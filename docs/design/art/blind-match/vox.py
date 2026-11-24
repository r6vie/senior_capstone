"""Hand-built voxels: blender -b --factory-startup -P vox.py -- out.png [samples]

Every form is a set of boxes on its own grid, each box carrying its own colour (top and side), so block size and
colour are chosen per material: big blocks for the mountains, coral on the faces that turn right, small cubes for
trees, long thin strokes for water, coloured terraces for the banks. Orthographic camera tilted down 20 degrees."""

import math
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
OUT = argv[0]
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
W, H = 1744, 690
T = math.radians(20)
CT, ST = math.cos(T), math.sin(T)
rng = np.random.default_rng(4)


def lin(h):
    h = h.lstrip("#")
    c = np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


PAPER = lin("#F6F7F2")


def z_for(screen_y, depth):
    return ((H - screen_y) - depth * ST) / CT


def vnoise(x, y, scale, seed):
    """Smooth value noise at arbitrary points."""
    g = np.random.default_rng(seed).random((64, 64))
    gx, gy = np.asarray(x) / scale + 7, np.asarray(y) / scale + 7
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    x0, y0 = x0 % 63, y0 % 63
    a, b, c, d = g[y0, x0], g[y0, x0 + 1], g[y0 + 1, x0], g[y0 + 1, x0 + 1]
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


# ---------- mesh emission ----------
DIRS = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)])
CORN = np.array([
    [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
    [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
    [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
    [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
    [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)],
], float)
MAT = None


def build(name, verts, cols, lines):
    n = len(verts) // 4
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.add(len(verts))
    me.loops.foreach_set("vertex_index", np.arange(len(verts), dtype=np.int32))
    me.polygons.add(n)
    me.polygons.foreach_set("loop_start", np.arange(0, len(verts), 4, dtype=np.int32))
    me.update(calc_edges=True)
    ca = me.color_attributes.new("col", "FLOAT_COLOR", "POINT")
    rgba = np.concatenate([cols, np.ones((len(cols), 1))], 1)
    ca.data.foreach_set("color", rgba.astype(np.float32).ravel())
    la = me.attributes.new("lines", "FLOAT", "POINT")
    la.data.foreach_set("value", np.asarray(lines, np.float32))
    me.materials.append(MAT)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def emit(name, cells, top, side, size, origin, lines=0.0):
    """cells: (N,3) int grid coords; top/side: (N,3) linear colours. Only faces with no neighbour are drawn."""
    cells = np.asarray(cells, np.int64)
    cells, ui = np.unique(cells, axis=0, return_index=True)
    top, side = np.asarray(top)[ui], np.asarray(side)[ui]
    off = cells.min(0) - 2
    c = cells - off
    dims = c.max(0) + 3
    enc = lambda a: (a[:, 0] * dims[1] + a[:, 1]) * dims[2] + a[:, 2]
    keys = np.sort(enc(c))
    V, C = [], []
    for d in range(6):
        nb = enc(c + DIRS[d])
        pos = np.searchsorted(keys, nb)
        pos = np.clip(pos, 0, len(keys) - 1)
        exposed = keys[pos] != nb
        if not exposed.any():
            continue
        cc = cells[exposed]
        v = (cc[:, None, :] + CORN[d][None]) * np.asarray(size) + np.asarray(origin)
        V.append(v.reshape(-1, 3))
        col = (top if d == 4 else side)[exposed]
        C.append(np.repeat(col, 4, 0))
    verts, cols = np.concatenate(V), np.concatenate(C)
    return build(name, verts, cols, np.full(len(verts), lines))


def boxes(name, mins, maxs, cols, lines=0.0):
    mins, maxs = np.asarray(mins, float), np.asarray(maxs, float)
    V, C = [], []
    for d in range(6):
        v = mins[:, None, :] + CORN[d][None] * (maxs - mins)[:, None, :]
        V.append(v.reshape(-1, 3))
        C.append(np.repeat(np.asarray(cols), 4, 0))
    verts, cols_ = np.concatenate(V), np.concatenate(C)
    return build(name, verts, cols_, np.full(len(verts), lines))


def mixp(col, t):
    t = np.asarray(t)[..., None]
    return col * (1 - t) + PAPER * t


# ---------- material: colour from the boxes, faint courses on faces that ask for them ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
MAT = bpy.data.materials.new("vox")
MAT.use_nodes = True
nt = MAT.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Roughness"].default_value = 1.0
try:
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
except KeyError:
    pass
att = nt.nodes.new("ShaderNodeAttribute")
att.attribute_name = "col"
lat = nt.nodes.new("ShaderNodeAttribute")
lat.attribute_name = "lines"
geo = nt.nodes.new("ShaderNodeNewGeometry")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Position"], sep.inputs[0])


def mth(op, a, b):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs["Value"]


# a thin darker line every 4 units of height: the courses inside each big block
stripe = mth("LESS_THAN", mth("FRACT", mth("DIVIDE", sep.outputs["Z"], 4.0), 0), 0.28)
k = mth("SUBTRACT", 1.0, mth("MULTIPLY", stripe, lat.outputs["Fac"]))
mul = nt.nodes.new("ShaderNodeMix")
mul.data_type = "RGBA"
mul.blend_type = "MULTIPLY"
mul.inputs["Factor"].default_value = 1.0
nt.links.new(att.outputs["Color"], mul.inputs["A"])
cval = nt.nodes.new("ShaderNodeCombineColor")
for ch in ("Red", "Green", "Blue"):
    nt.links.new(k, cval.inputs[ch])
nt.links.new(cval.outputs["Color"], mul.inputs["B"])
nt.links.new(mul.outputs["Result"], bsdf.inputs["Base Color"])


# ---------- mountains ----------
def mountain(name, peaks, base_y, depth, kind, mist=60, cell=(20, 12, 12), bulge=140, q=1.2, step=90, seed=0,
             edge=True):
    """Columns of big blocks. Depth comes from a coarse, faceted surface; each column is toned by how that surface
    meets the light, and on cream ranges the faces that turn right are coral (the snow sits on the left faces)."""
    SX, SY, SZ = cell
    zb = z_for(base_y, depth)
    zt = z_for(min(p[1] for p in peaks), depth) + 20

    def field(Xg, Zg):
        f = np.zeros_like(Xg, float)
        for cx, ty, rx in peaks:
            hz = z_for(ty, depth) - zb
            d = (np.abs((Xg - cx) / rx) ** q + np.abs((Zg - zb) / hz) ** q) ** (1 / q)
            f = np.maximum(f, np.clip(1 - d, 0, 1))
        return f

    cxs = np.arange(-200, W + 240, step)
    czs = np.arange(zb - 60, zt + 80, step * 0.8)
    CX, CZ = np.meshgrid(cxs, czs, indexing="ij")
    r = np.random.default_rng(seed)
    cY = bulge * field(CX, CZ) ** 0.7 * (1 + r.uniform(-0.12, 0.12, CX.shape))

    def surf(X, Z):
        ix = np.clip((X - cxs[0]) / step, 0, len(cxs) - 1.001)
        iz = np.clip((Z - czs[0]) / (step * 0.8), 0, len(czs) - 1.001)
        i0, k0 = ix.astype(int), iz.astype(int)
        fx, fz = ix - i0, iz - k0
        return (cY[i0, k0] * (1 - fx) * (1 - fz) + cY[i0 + 1, k0] * fx * (1 - fz) + cY[i0, k0 + 1] * (1 - fx) * fz
                + cY[i0 + 1, k0 + 1] * fx * fz)

    ii = np.arange(int(-40 // SX), int((W + 40) // SX) + 1)
    kk = np.arange(0, int((zt - zb) // SZ) + 2)
    I, K = np.meshgrid(ii, kk, indexing="ij")
    # bricks: odd courses shift half a block, so the blocks never line up into columns
    X, Z = (I + 0.5 + 0.5 * (K % 2)) * SX, zb + (K + 0.5) * SZ
    # a ragged outline: the threshold wanders a little so edges step unevenly
    inside = field(X, Z) > 0.05 + 0.04 * (vnoise(X, Z, 60, seed + 1) - 0.5)
    X, Z, I, K = X[inside], Z[inside], I[inside], K[inside]
    Yb = surf(X, Z)
    gx = (surf(X + 6, Z) - surf(X - 6, Z)) / 12
    gz = (surf(X, Z + 6) - surf(X, Z - 6)) / 12
    n = np.stack([-gx, -np.ones_like(gx), -gz], 1)  # outward, toward the camera
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    L = np.array([-0.55, -0.55, 0.62])
    L /= np.linalg.norm(L)
    lam = np.clip((n * L).sum(1), 0, 1)
    lam = np.clip((lam - 0.62) * 2.2 + 0.55 + 0.25 * (vnoise(X, Z, 55, seed + 7) - 0.5), 0, 1)
    lam = np.round(lam * 5) / 5  # a few flat tones, like folded paper
    t = (Z - zb) / (zt - zb)
    if kind == "blue":
        base = np.array([lin("#1E5F7A"), lin("#2B6E8A"), lin("#3A7A93"), lin("#407990")])
        col = base[np.clip((lam * 4 - 0.4 + r.normal(0, 0.3, len(lam))).round().astype(int), 0, 3)]
    else:
        cream = np.array([lin("#A39D96"), lin("#C2BBB2"), lin("#DDD7CD"), lin("#EEEAE2"), lin("#FAF8F3")])
        col = cream[np.clip((lam * 4.4 + 0.3 + r.normal(0, 0.25, len(lam))).round().astype(int), 0, 4)]
        # right-facing flanks are coral; a little noise lets the border step
        slope = n[:, 0] + 0.22 * (vnoise(X, Z, 110, seed + 2) - 0.5)
        foot = np.clip(1 - (Z - zb) / mist, 0, 1)
        # strata: a band partway up each mass, showing where the face turns right
        tb = t + 0.12 * (vnoise(X, Z, 90, seed + 4) - 0.5) - 0.25 * np.clip(n[:, 0], -1, 1)
        coral = (slope > 0.02) & (tb > 0.12) & (tb < 0.5) & (foot < 0.3)
        cor = np.array([lin("#D98A74"), lin("#E3957D"), lin("#EBA088")])
        col[coral] = cor[np.clip((lam[coral] * 2.4 + r.normal(0, 0.3, coral.sum())).round().astype(int), 0, 2)]
    col = col * (1 + r.normal(0, 0.02, (len(col), 1)))
    # mist at the foot, in steps
    fade = np.clip(1 - (Z - zb) / mist, 0, 1) + 0.25 * (vnoise(X, Z, 30, seed + 3) - 0.5)
    if edge:
        fade = np.maximum(fade, np.clip(1 - np.minimum(X, W - X) / 150, 0, 1) * 0.95)
    fade = np.clip(np.round(fade * 4) / 4, 0, 1)
    keep = fade < 0.8
    col = mixp(col, fade * 0.95)
    X, Z, I, K, Yb, col = X[keep], Z[keep], I[keep], K[keep], Yb[keep], col[keep]
    jf = np.round((depth - Yb) / SY).astype(int)
    jb = int(round(depth / SY))
    cells, cs = [], []
    for i_, k_, j0, c_ in zip(I, K, jf, col):
        h0 = 2 * i_ + k_ % 2
        for j in range(j0, min(jb, j0 + 3) + 1):
            for h in (h0, h0 + 1):
                cells.append((h, j, k_))
                cs.append(c_)
    cs = np.array(cs)
    return emit(name, cells, cs, cs, (SX / 2, SY, SZ), (0, 0, zb), lines=0.10)


mountain("blueA", [(1240, 40, 440), (985, 110, 120), (1730, 222, 150), (1460, 120, 170)], 340, 900, "blue", mist=45,
         seed=1, cell=(14, 10, 10))
mountain("blueB", [(360, 150, 240), (180, 250, 230), (620, 250, 160)], 340, 860, "blue", mist=45, seed=2,
         cell=(14, 10, 10))
mountain("creamA", [(965, 110, 150), (1310, 135, 250), (330, 222, 200)], 350, 700, "cream", mist=70, seed=3, q=1.7,
         cell=(18, 11, 11))
mountain("creamM", [(760, 250, 230), (900, 300, 190)], 450, 470, "cream", mist=70, seed=4, q=1.8, cell=(22, 12, 12))
mountain("creamB", [(250, 262, 220), (1060, 225, 210), (1640, 300, 210)], 430, 520, "cream", mist=60, seed=5, q=1.8,
         cell=(20, 12, 12))
mountain("creamC", [(1185, 290, 240), (1590, 340, 240), (840, 300, 140), (110, 330, 170)], 470, 400, "cream", mist=70,
         seed=6, q=1.9, cell=(24, 13, 13))

# ---------- terraced islands ----------
GRASS = np.array([lin(h) for h in ("#6F8A57", "#7F9467", "#8E9C6E", "#999D71", "#A2A77A", "#B3AE80", "#838F7D")])
EARTH = np.array([lin(h) for h in ("#9C8A66", "#A99A72", "#B8AC84", "#8E8C66", "#C9BF9C")])


def island(name, cx, cy_screen, rx, rdepth, depth, levels, step_h=6, cell=(10, 10)):
    SX, SY = cell
    zb = z_for(cy_screen, depth)
    r = np.random.default_rng(int(cx))
    ii = np.arange(int((cx - rx * 1.2) // SX), int((cx + rx * 1.2) // SX) + 1)
    jj = np.arange(int((depth - rdepth * 1.2) // SY), int((depth + rdepth * 1.2) // SY) + 1)
    I, J = np.meshgrid(ii, jj, indexing="ij")
    X, D = (I + 0.5) * SX, (J + 0.5) * SY
    ang = np.arctan2((D - depth) / rdepth, (X - cx) / rx)
    wob = 1 + 0.10 * np.sin(ang * 3 + r.uniform(0, 6)) + 0.07 * np.sin(ang * 7 + r.uniform(0, 6))
    rr = np.sqrt(((X - cx) / rx) ** 2 + ((D - depth) / rdepth) ** 2) / wob
    rr = rr + 0.10 * (vnoise(X, D, 35, int(cx) + 5) - 0.5)
    lev = np.clip(((1 - rr) * (levels + 1.2)).astype(int) + 1, 0, levels)
    on = rr < 1
    I, J, X, D, lev = I[on], J[on], X[on], D[on], lev[on]
    cells, tops, sides = [], [], []
    for i_, j_, x_, d_, L_ in zip(I, J, X, D, lev):
        # each terrace ring has its own tone, drifting along the ring
        g = int((L_ * 2.3 + vnoise(x_, d_, 90, int(cx)) * 4 + r.normal(0, 0.5)) % len(GRASS))
        e = int((L_ + vnoise(x_, d_, 60, int(cx) + 9) * 3) % len(EARTH))
        for k_ in range(L_):
            cells.append((i_, j_, k_))
            fade = max(0.0, 1 - k_ / 1.8) * 0.75 if k_ < 2 else 0.0
            tops.append(mixp(GRASS[g] * (1 + r.normal(0, 0.03)), fade))
            sides.append(mixp(EARTH[e] * (1 + r.normal(0, 0.04)), fade))
    emit(name, cells, tops, sides, (SX, SY, step_h), (0, 0, zb), lines=0.0)

    def ground(x, d):
        rr_ = math.sqrt(((x - cx) / rx) ** 2 + ((d - depth) / rdepth) ** 2)
        return zb + step_h * max(1, min(levels, int((1 - rr_) * (levels + 1.2)) + 1))

    return ground


left = island("islandL", 420, 615, 500, 240, 240, 8, step_h=8)
right = island("islandR", 1360, 615, 460, 170, 260, 7, step_h=8)
mid = island("islandM", 600, 455, 170, 70, 420, 4, step_h=8)
mid2 = island("islandC", 1010, 470, 120, 45, 470, 5, step_h=8)

# ---------- river: long strokes of many blues, paler and broken with distance ----------
WATER = np.array([lin(h) for h in ("#1E5F7A", "#21607D", "#2E7A98", "#327E9B", "#35738F", "#3A86A3", "#5A9DB8",
                                   "#8DBACB", "#B6D2DD", "#E3EDF0")])
zr = z_for(600, 200) - 2
mins, maxs, wc = [], [], []
dstep = 11
for d in np.arange(-40, 560, dstep):
    c = 860 + 190 * np.sin((d + 40) / 110.0) * (1 - d / 800) + d * 0.1
    hw = 40 + (560 - d) * 0.3
    x = c - hw + rng.uniform(-14, 14)
    far = np.clip((d + 40) / 600, 0, 1)
    while x < c + hw:
        Ls = rng.uniform(60, 220)
        x2 = min(c + hw + rng.uniform(-10, 20), x + Ls)
        shade = 0.25 + 0.5 * vnoise(x, d, 120, 3) + rng.normal(0, 0.18) + far * 0.55
        idx = int(np.clip(round(shade * 9), 0, 9))
        col = WATER[idx]
        if rng.random() < 0.06 + 0.12 * (vnoise(x, d, 60, 8) > 0.62):
            col = WATER[rng.integers(7, 10)]  # pale glints gather in bands
        if far > 0.75 and rng.random() < far - 0.55:
            col = mixp(col, 0.7)
        mins.append((x, d, zr))
        maxs.append((x2, d + dstep, zr + 2))
        wc.append(col)
        x = x2 + (rng.uniform(10, 70) if rng.random() < 0.18 else 0)
boxes("river", mins, maxs, wc)

# ---------- trees: trunk, a few branches, and lumpy pads of small cubes ----------
VS = 4.2
LEAF = np.array([lin(h) for h in ("#253224", "#2F3F2C", "#3A4E34", "#46603C", "#527047", "#5F7D4F", "#6E8A58",
                                  "#7E9B60", "#90AD6C", "#A6BF7E")])
BARK = np.array([lin(h) for h in ("#4A3428", "#5A4537", "#6B4B3A", "#7A5A45", "#8A5E48")])
T_cells, T_col = [], []
L_cells, L_top, L_side = [], [], []


def tree(x, d, zg, s):
    r = np.random.default_rng(int(x * 13 + d * 7))
    h = s * r.uniform(1.0, 1.9)
    lean = r.uniform(-0.25, 0.25)
    i0, j0, k0 = round(x / VS), round(d / VS), int(zg // VS)
    nk = max(3, int(h / VS))
    bark = BARK[r.integers(0, len(BARK))]
    tw = 1 if s < 45 else 2
    top = None
    for k in range(nk):
        i = i0 + round(lean * k)
        for a in range(tw):
            T_cells.append((i + a, j0, k0 + k))
            T_col.append(bark * (0.85 + 0.25 * k / nk))
        top = (i, j0, k0 + k)
    # pads: one on top, two to four on branches
    pads = [(top[0], top[1], top[2] + 1, s * r.uniform(0.45, 0.6))]
    for _ in range(int(r.integers(2, 5))):
        bk = int(nk * r.uniform(0.45, 0.85))
        side = r.choice([-1, 1])
        length = s * r.uniform(0.35, 0.7) / VS
        rise = r.uniform(0.2, 0.7)
        bi = i0 + round(lean * bk)
        for t in range(int(length)):
            T_cells.append((bi + side * t, j0 + round(r.uniform(-0.4, 0.4)), k0 + bk + round(t * rise)))
            T_col.append(bark * 0.9)
        pads.append((bi + side * int(length), j0 + int(r.integers(-1, 2)), k0 + bk + round(length * rise) + 1,
                     s * r.uniform(0.3, 0.48)))
    for pi, pj, pk, pr in pads:
        R = pr / VS
        Rz = R * r.uniform(0.38, 0.55)
        n = int(R) + 2
        di, dj, dk = np.meshgrid(np.arange(-n, n + 1), np.arange(-n, n + 1), np.arange(-int(Rz) - 1, int(Rz) + 2),
                                 indexing="ij")
        # several lumps make a cloud, not an oval
        lumps = [(0, 0, 0, 1.0)] + [(r.uniform(-0.6, 0.6) * R, r.uniform(-0.5, 0.5) * R, r.uniform(-0.2, 0.5) * Rz,
                                     r.uniform(0.45, 0.7)) for _ in range(4)]
        inside = np.zeros(di.shape, bool)
        for lx, ly, lz, ls in lumps:
            dd = ((di - lx) / (R * ls)) ** 2 + ((dj - ly) / (R * ls)) ** 2 + ((dk - lz) / (Rz * ls + 0.6)) ** 2
            inside |= dd < 1 + r.uniform(-0.15, 0.15, di.shape)
        inside &= dk >= -Rz * 0.5  # flat underside
        for a, b, c_ in zip(di[inside], dj[inside], dk[inside]):
            L_cells.append((pi + a, pj + b, pk + c_))
            hgt = (c_ + Rz) / (2 * Rz + 1e-6)
            g = np.clip(1 + hgt * 8 + r.normal(0, 1.0), 0, 9)
            L_top.append(LEAF[int(round(g))])
            L_side.append(LEAF[int(round(max(0, g - 2.2)))])


placed = []


def plant(x, d, z, s):
    for px, pd, ps in placed:
        if (x - px) ** 2 + ((d - pd) * 1.3) ** 2 < (1.05 * (s + ps) / 2) ** 2:
            return
    placed.append((x, d, s))
    tree(x, d, z, s)


for _ in range(700):
    x, d = rng.uniform(-60, 820), rng.uniform(20, 440)
    if ((x - 420) / 500) ** 2 + ((d - 240) / 240) ** 2 < 0.62:
        plant(x, d, left(x, d), rng.choice([0.55, 0.8, 1.0, 1.3]) * rng.uniform(55, 85) * (1.15 - d / 900))
for _ in range(700):
    x, d = rng.uniform(1000, 1800), rng.uniform(100, 420)
    if ((x - 1360) / 460) ** 2 + ((d - 260) / 170) ** 2 < 0.62:
        plant(x, d, right(x, d), rng.choice([0.55, 0.8, 1.0, 1.3]) * rng.uniform(50, 80) * (1.1 - d / 1000))
for _ in range(18):
    x, d = rng.uniform(910, 1110), rng.uniform(440, 500)
    plant(x, d, mid2(x, d), rng.uniform(18, 28))
for _ in range(50):
    x, d = rng.uniform(460, 760), rng.uniform(380, 470)
    if ((x - 600) / 170) ** 2 + ((d - 420) / 70) ** 2 < 0.62:
        plant(x, d, mid(x, d), rng.uniform(20, 32))
print("trees", len(placed), "leaf cells", len(L_cells))
emit("trunks", T_cells, T_col, T_col, (VS, VS, VS), (0, 0, 0))
emit("leaves", L_cells, L_top, L_side, (VS, VS, VS), (0, 0, 0))

# ---------- light, camera ----------
sc = bpy.context.scene
sc.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for dv in prefs.devices:
        dv.use = True
    sc.cycles.device = "GPU"
except Exception as e:
    print("gpu", e)
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (*PAPER, 1)
bg.inputs[1].default_value = 0.68
sun = bpy.data.lights.new("sun", "SUN")
sun.energy = 1.6
sun.angle = math.radians(20)
sun.use_shadow = False
so = bpy.data.objects.new("sun", sun)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(55), math.radians(-40), math.radians(-25))
cam = bpy.data.cameras.new("cam")
cam.type = "ORTHO"
cam.ortho_scale = W
cam.clip_start, cam.clip_end = 1, 20000
co = bpy.data.objects.new("cam", cam)
sc.collection.objects.link(co)
up = np.array([0, ST, CT])
fwd = np.array([0, CT, -ST])
co.location = tuple(np.array([W / 2, 0, 0]) - fwd * 3000 + up * (H / 2))
co.rotation_euler = (math.pi / 2 - T, 0, 0)
sc.camera = co
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("done")
