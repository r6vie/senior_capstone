"""Voxel landscape covers for Trove, rendered in Blender (run: blender -b -P voxel.py -- <scene> <out.png> [scale]).

A scene is a voxel grid (occupied + colour per cell) built with numpy, turned into one mesh of slightly
shrunk cubes (only cells with an open neighbour), lit by a soft sun and a white sky, and rendered in Cycles
through a portrait camera that leaves the top of the frame empty for the title.
"""

import math
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
SCENE = argv[0] if argv else "valley"
OUT = argv[1] if len(argv) > 1 else "/tmp/voxel.png"
SCALE = float(argv[2]) if len(argv) > 2 else 1.0
SAMPLES = int(argv[3]) if len(argv) > 3 else 96


def srgb(h):
    h = h.lstrip("#")
    c = np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


rng = np.random.default_rng(7)


# ---------------- noise ----------------
def value_noise(shape, cell, seed):
    r = np.random.default_rng(seed)
    gx, gy = shape[0] // cell + 2, shape[1] // cell + 2
    g = r.random((gx, gy))
    xs = np.arange(shape[0]) / cell
    ys = np.arange(shape[1]) / cell
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = g[x0][:, y0]
    b = g[x0 + 1][:, y0]
    c = g[x0][:, y0 + 1]
    d = g[x0 + 1][:, y0 + 1]
    fx, fy = fx[:, None], fy[None, :]
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def fbm(shape, cell, seed, octaves=4):
    out = np.zeros(shape)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out += amp * value_noise(shape, max(2, cell >> o), seed + o)
        tot += amp
        amp *= 0.5
    return out / tot


# ---------------- scenes ----------------
def palette(name):
    return {k: srgb(v) for k, v in name.items()}


P = palette(
    {
        "blue": "#0E5C93",
        "blue2": "#1B74B0",
        "blue3": "#0A4A78",
        "cream": "#EEE8DD",
        "cream2": "#DCD3C4",
        "cream3": "#C3B8A6",
        "coral": "#E6785B",
        "coral2": "#D2664B",
        "grass": "#86A85A",
        "grass2": "#6E9147",
        "earth": "#A88C68",
        "leaf": "#5C8E3E",
        "leaf2": "#3F6F2D",
        "leaf3": "#2B5220",
        "leaf4": "#8BB65C",
        "trunk": "#6A4631",
        "water": "#2C7DB2",
        "water2": "#4C9ACB",
        "foam": "#E9F0F3",
        "cloud": "#F4F1EC",
        "cloud2": "#E2DDD4",
        "teal": "#2F5E5C",
        "teal2": "#1B3C3A",
    }
)


def peaks_height(X, Y, peaks, seed):
    h = np.zeros(X.shape)
    for cx, cy, ht, rx, ry, p in peaks:
        d = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2)
        h = np.maximum(h, ht * np.clip(1 - d, 0, None) ** p)
    n = fbm(X.shape, 16, seed)
    return h * (0.82 + 0.36 * n)


def pick(j, *pairs):
    """pairs: (threshold, colour) ... pick the first whose threshold exceeds j."""
    out = np.zeros(j.shape + (3,), np.float32)
    done = np.zeros(j.shape, bool)
    for th, c in pairs:
        m = (j < th) & ~done
        out[m] = c
        done |= m
    return out


def valley():
    NX, NY, NZ = 200, 230, 110
    X, Y = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
    n1 = fbm(X.shape, 32, 1)
    # far range: broad blue domes
    far = peaks_height(X, Y, [(30, 205, 58, 50, 26, 0.75), (95, 212, 72, 60, 28, 0.7), (165, 205, 62, 50, 26, 0.75),
                               (200, 200, 48, 34, 22, 0.8)], 3)
    # middle: rounded cream mounds
    mid = peaks_height(X, Y, [(28, 160, 40, 36, 22, 0.65), (78, 168, 50, 40, 24, 0.6), (128, 158, 44, 34, 22, 0.65),
                               (176, 165, 40, 32, 22, 0.65), (55, 140, 26, 26, 16, 0.7), (150, 140, 24, 24, 14, 0.7)], 5)
    # the island: two wooded banks either side of the river, ragged at the edges
    river_x = 100 + 22 * np.sin(Y / 26.0) + 7 * np.sin(Y / 9.0)
    dist = np.abs(X - river_x)
    river_w = 5 + Y / 30
    island = (fbm(X.shape, 20, 21) * 1.1 - ((X - 100) / 125) ** 2 - ((Y - 82) / 78) ** 2) > 0.18
    ground = np.where(island, 2 + np.floor(4 * fbm(X.shape, 18, 9)), 0)
    in_river = (dist < river_w) & (Y < 150) & (island | (Y > 110) | ((fbm(X.shape, 6, 31) > 0.45) & (Y > 4)))
    far, mid = far * 1.3, mid * 1.3
    terrain = np.maximum(ground, np.maximum(far, mid))
    H = np.where(in_river & (mid < 3) & (far < 3), 1, np.round(terrain)).astype(int)
    H = np.clip(H, 0, NZ - 1)

    Z = np.arange(NZ)[None, None, :]
    occ = Z < H[:, :, None]
    j = rng.random((NX, NY, NZ)).astype(np.float32)
    col = np.zeros((NX, NY, NZ, 3), np.float32)

    src_far = (far >= np.maximum(mid, ground)) & (far > 3)
    src_mid = ~src_far & (mid >= ground) & (mid > 3)
    src_ground = ~src_far & ~src_mid
    zf = Z / np.maximum(1, H[:, :, None])

    c_far = pick(j, (0.3, P["blue2"]), (0.88, P["blue"]), (1.1, P["blue3"]))
    c_cream = pick(j, (0.55, P["cream"]), (0.88, P["cream2"]), (1.1, P["cream3"]))
    c_coral = pick(j, (0.68, P["coral"]), (1.1, P["coral2"]))
    patch = fbm(X.shape, 14, 17)[:, :, None]
    gx_, gy_ = np.gradient(H.astype(float))
    steep = (np.hypot(gx_, gy_) > 0.9)[:, :, None]
    band = (Z < 15 + 11 * n1[:, :, None]) & (Z > 5) & steep & (patch + 0.12 * j > 0.42)
    c_mid = np.where(band[..., None], c_coral, c_cream)
    top = Z == (H[:, :, None] - 1)
    c_ground = np.where(top[..., None], pick(j, (0.55, P["grass"]), (0.9, P["grass2"]), (1.1, P["earth"])),
                        pick(j, (0.55, P["earth"]), (1.1, P["grass2"])))
    c_water = pick(j, (0.1, P["foam"]), (0.45, P["water2"]), (1.1, P["water"]))
    col[:] = c_ground
    col[src_far] = c_far[src_far]
    col[src_mid] = c_mid[src_mid]
    rv = in_river & (H <= 1)
    col[rv] = c_water[rv]

    # trees: dense groves on the banks, round crowns lit from the upper left
    r = np.random.default_rng(11)
    for _ in range(300):
        x, y = int(r.integers(3, NX - 3)), int(r.integers(4, 140))
        if not island[x, y] or dist[x, y] < river_w[x, y] + 3 or mid[x, y] > 3 or far[x, y] > 3:
            continue
        base = H[x, y]
        th = int(r.integers(4, 8))
        cr = r.uniform(2.4, 4.2)
        occ[x, y, base : base + th] = True
        col[x, y, base : base + th] = P["trunk"]
        cz = base + th + cr * 0.3
        R = int(cr) + 2
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                for dz in range(-R, R + 1):
                    xx, yy, zz = x + dx, y + dy, int(cz + dz)
                    if not (0 <= xx < NX and 0 <= yy < NY and 0 <= zz < NZ):
                        continue
                    d = math.sqrt(dx * dx + dy * dy + (dz * 1.4) ** 2)
                    if d <= cr + r.uniform(-0.6, 0.3):
                        occ[xx, yy, zz] = True
                        k = (dz / R) * 0.55 - (dx / R) * 0.3 + (dy / R) * 0.1 + r.uniform(-0.25, 0.25)
                        col[xx, yy, zz] = (P["leaf4"] if k > 0.35 else P["leaf"] if k > 0.0
                                           else P["leaf2"] if k > -0.35 else P["leaf3"])

    # cumulus banks between the ranges: several round lobes on a flat base, lit from the upper left
    cr_ = np.random.default_rng(23)
    for cx, cy, cz, w in [(16, 182, 34, 34), (92, 194, 40, 40), (168, 184, 34, 36), (112, 150, 24, 26), (40, 134, 16, 18)]:
        lobes = [(cx + cr_.uniform(-w / 2, w / 2), cy + cr_.uniform(-4, 4), cz + cr_.uniform(0, 3), cr_.uniform(4.5, 8.5))
                 for _ in range(7)]
        x0, x1 = int(max(0, cx - w / 2 - 10)), int(min(NX, cx + w / 2 + 10))
        y0, y1 = int(max(0, cy - 14)), int(min(NY, cy + 14))
        z0, z1 = int(max(0, cz - 2)), int(min(NZ, cz + 14))
        gx, gy, gz = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1), np.arange(z0, z1), indexing="ij")
        m = np.zeros(gx.shape, bool)
        lit = np.full(gx.shape, -9.0)
        for lx, ly, lz, lr in lobes:
            d = np.sqrt((gx - lx) ** 2 + ((gy - ly) * 1.2) ** 2 + ((gz - lz) * 1.25) ** 2)
            inside = d < lr - 0.6 * rng.random(d.shape)
            m |= inside
            lit = np.maximum(lit, np.where(inside, ((gz - lz) - (gx - lx) * 0.5) / lr, -9))
        m &= gz >= cz  # flat base
        sl = np.s_[x0:x1, y0:y1, z0:z1]
        occ[sl] |= m
        cc = np.where((lit + 0.25 * rng.random(lit.shape) > -0.05)[..., None], P["cloud"], P["cloud2"])
        col[sl] = np.where(m[..., None], cc, col[sl])

    # distance haze toward paper: far things pale out (the reference's soft depth)
    haze = np.clip((np.arange(NY) - 150) / 300, 0, 0.05)[None, :, None, None]
    col = col * (1 - haze) + srgb("#FAFAF7")[None, None, None, :] * haze
    cam = dict(loc=(100.5, -300, 140), target=(100.5, 112, 30), lens=82)
    return occ, col.astype(np.float32), cam


SCENES = {"valley": valley}


# ---------------- mesh ----------------
def build_mesh(occ, col, shrink=0.955, zscale=0.62):
    pad = np.pad(occ, 1)
    exposed = occ & ~(
        pad[2:, 1:-1, 1:-1] & pad[:-2, 1:-1, 1:-1] & pad[1:-1, 2:, 1:-1] & pad[1:-1, :-2, 1:-1]
        & pad[1:-1, 1:-1, 2:] & pad[1:-1, 1:-1, :-2]
    )
    idx = np.argwhere(exposed)
    n = len(idx)
    print("cubes", n)
    s = shrink / 2
    corners = np.array([[-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s], [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]])
    faces = np.array([[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    centers = idx.astype(np.float32) + 0.5
    verts = (centers[:, None, :] + corners[None, :, :]).reshape(-1, 3)
    verts[:, 2] *= zscale
    f = (faces[None, :, :] + (np.arange(n) * 8)[:, None, None]).reshape(-1, 4)
    me = bpy.data.meshes.new("vox")
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(len(f) * 4)
    me.loops.foreach_set("vertex_index", f.ravel())
    me.polygons.add(len(f))
    me.polygons.foreach_set("loop_start", np.arange(0, len(f) * 4, 4))
    me.polygons.foreach_set("loop_total", np.full(len(f), 4))
    me.update()
    cols = col[tuple(idx.T)]
    face_cols = np.repeat(cols, 6, axis=0)
    rgba = np.concatenate([face_cols, np.ones((len(face_cols), 1))], axis=1).astype(np.float32)
    attr = me.color_attributes.new("Col", "FLOAT_COLOR", "FACE")
    attr.data.foreach_set("color", rgba.ravel())
    ob = bpy.data.objects.new("vox", me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new("vox")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.85
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = "Col"
    nt.links.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    me.materials.append(mat)
    return ob


def setup(cam, w, h):
    sc = bpy.context.scene
    try:
        sc.render.engine = "CYCLES"
    except TypeError as e:
        print(e)
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:  # CPU is fine
        print("gpu", e)
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    bg = next(nd for nd in world.node_tree.nodes if nd.type == "BACKGROUND")
    bg.inputs[0].default_value = (*srgb("#FAFAF7"), 1)
    bg.inputs[1].default_value = 0.75
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 3.6
    sun.angle = math.radians(12)
    so = bpy.data.objects.new("sun", sun)
    sc.collection.objects.link(so)
    so.location = (-160, -60, 120)
    st = bpy.data.objects.new("sun_t", None)
    st.location = (100, 120, 0)
    sc.collection.objects.link(st)
    kk = so.constraints.new("TRACK_TO")
    kk.target = st
    kk.track_axis = "TRACK_NEGATIVE_Z"
    kk.up_axis = "UP_Y"
    c = bpy.data.cameras.new("cam")
    c.lens = cam["lens"]
    co = bpy.data.objects.new("cam", c)
    sc.collection.objects.link(co)
    co.location = cam["loc"]
    t = bpy.data.objects.new("t", None)
    t.location = cam["target"]
    sc.collection.objects.link(t)
    k = co.constraints.new("TRACK_TO")
    k.target = t
    k.track_axis = "TRACK_NEGATIVE_Z"
    k.up_axis = "UP_Y"
    sc.camera = co


for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
occ, col, cam = SCENES[SCENE]()
build_mesh(occ, col)
setup(cam, int(472 * SCALE), int(688 * SCALE))
bpy.context.scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
