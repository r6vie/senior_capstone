"""Smooth scene for pixelation: blender -b --factory-startup -P smooth.py -- beauty.png id.png [samples]

Renders the reference's composition as smooth, softly lit forms (orthographic, tilted down), then a flat material-id
image. pixelate.py turns the pair into wide slabs per material."""

import math
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
BEAUTY, IDOUT = argv[0], argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
W, H = 1744, 690
T = math.radians(20)
CT, ST = math.cos(T), math.sin(T)
rng = np.random.default_rng(4)


def lin(h):
    h = h.lstrip("#")
    c = np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)])
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


PAPER = lin("#F6F7F2")
IDS = {"blue": "#FF0000", "cream": "#00FF00", "coral": "#0000FF", "terrace": "#FFFF00", "water": "#00FFFF",
       "trunk": "#FF00FF", "leaf": "#FFFFFF", "blue2": "#FF0000", "cream2": "#00FF00", "cream3": "#00FF00"}
mats = {}


def material(name, color, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rough
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    except KeyError:
        pass
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    # tint per object (trees) and fade to paper by a 'fade' attribute (mist at the feet of forms)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*color[0], 1)
    ramp.color_ramp.elements[1].color = (*color[-1], 1)
    nt.links.new(oi.outputs["Random"], ramp.inputs["Fac"])
    bmix = nt.nodes.new("ShaderNodeMix")
    bmix.data_type = "RGBA"
    bmix.inputs["B"].default_value = (*lin("#CF7966"), 1)
    nt.links.new(ramp.outputs["Color"], bmix.inputs["A"])
    nt.links.new(bmix.outputs["Result"], bsdf.inputs["Base Color"])
    fade = nt.nodes.new("ShaderNodeAttribute")
    fade.attribute_name = "fade"
    em = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    # band and mist from world height, per object: zb (base), zh (height), mist, blo/bhi (coral band as fractions)
    def objattr(key):
        a_ = nt.nodes.new("ShaderNodeAttribute")
        a_.attribute_type = "OBJECT"
        a_.attribute_name = key
        return a_.outputs["Fac"]

    def math(op, a_, b_):
        n_ = nt.nodes.new("ShaderNodeMath")
        n_.operation = op
        for i_, v_ in enumerate((a_, b_)):
            if isinstance(v_, (int, float)):
                n_.inputs[i_].default_value = v_
            else:
                nt.links.new(v_, n_.inputs[i_])
        return n_.outputs["Value"]

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sxyz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sxyz.inputs[0])
    Zp = math("MULTIPLY", math("FLOOR", math("DIVIDE", sxyz.outputs["Z"], 9.0), 0.0), 9.0)
    Xp = math("MULTIPLY", math("FLOOR", math("DIVIDE", sxyz.outputs["X"], 26.0), 0.0), 26.0)
    rel = math("SUBTRACT", Zp, objattr("zb"))
    t = math("DIVIDE", rel, objattr("zh"))
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.012
    nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
    wob = math("MULTIPLY", math("SUBTRACT", noise.outputs["Fac"], 0.5), 0.5)
    tw = math("ADD", t, wob)
    band_v = math("MULTIPLY", math("GREATER_THAN", tw, objattr("blo")), math("LESS_THAN", tw, objattr("bhi")))
    nt.links.new(band_v, bmix.inputs["Factor"])
    fade_h = math("MAXIMUM", math("SUBTRACT", 1.0, math("DIVIDE", rel, objattr("mist"))), 0.0)
    edge = math("MINIMUM", Xp, math("SUBTRACT", 1744.0, Xp))
    fade_x = math("MULTIPLY", math("MULTIPLY", math("MAXIMUM", math("SUBTRACT", 1.0, math("DIVIDE", edge, 140.0)), 0.0), 0.9), objattr("edge"))
    fade_g = math("MINIMUM", math("MAXIMUM", math("MAXIMUM", fade_h, fade_x), fade.outputs["Fac"]), 1.0)
    stepped = math("ADD", math("MULTIPLY", math("GREATER_THAN", fade_g, 0.35), 0.0),
                   math("GREATER_THAN", fade_g, 0.7))
    nt.links.new(stepped, mix.inputs["Fac"])
    pale = nt.nodes.new("ShaderNodeMix")
    pale.data_type = "RGBA"
    pale.inputs["B"].default_value = (*lin("#EDEDE6"), 1)
    nt.links.new(math("MULTIPLY", math("GREATER_THAN", fade_g, 0.35), 0.75), pale.inputs["Factor"])
    nt.links.new(bmix.outputs["Result"], pale.inputs["A"])
    nt.links.new(pale.outputs["Result"], bsdf.inputs["Base Color"])
    mats[name] = m
    return m


def mesh_obj(name, verts, faces, mat, fade=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    if fade is not None:
        a = me.attributes.new("fade", "FLOAT", "POINT")
        a.data.foreach_set("value", np.asarray(fade, np.float32))
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def z_for(screen_y, depth):
    return ((H - screen_y) - depth * ST) / CT


def relief(name, peaks, base_y, depth, mat, bulge=110, q=1.2, mist=60, step=46, band=None, fine=6):
    """A faceted mountain, like folded paper. Its depth comes from a coarse grid (big flat planes for the light to
    break across); its outline comes from a fine grid, so silhouettes stay crisp. band paints coral strata."""
    zb = z_for(base_y, depth)
    zt = z_for(min(p[1] for p in peaks), depth) + 20

    def field(Xg, Zg):
        f = np.zeros_like(Xg)
        fb = np.zeros_like(Xg)
        for cx, ty, rx in peaks:
            hz = z_for(ty, depth) - zb
            d = (np.abs((Xg - cx) / rx) ** q + np.abs((Zg - zb) / hz) ** q) ** (1 / q)
            g = np.clip(1 - d, 0, 1)
            if band:
                # a wedge on the lower right flank: its top edge climbs toward the summit, its left edge leans
                t = (Zg - zb) / hz + 0.35 * (Xg - cx) / rx
                wob = 0.08 * np.sin(Xg / 23.0 + cx) + 0.06 * np.sin(Zg / 13.0)
                right = (Xg - cx) > -0.35 * rx + (Zg - zb) * 0.15
                fb = np.maximum(fb, ((t > band[0] + wob) & (t < band[1] + wob) & right & (g > 0.03)).astype(float))
            f = np.maximum(f, g)
        return f, fb

    r = np.random.default_rng(int(depth))
    cxs = np.arange(-160, W + 200, step)
    czs = np.arange(zb - 40, zt + 60, step * 0.8)
    CX, CZ = np.meshgrid(cxs, czs, indexing="ij")
    cf, _ = field(CX, CZ)
    cY = bulge * np.clip(cf, 0, None) ** 0.7
    xs = np.arange(-60, W + 60, fine)
    zs = np.arange(zb - 6, zt, fine)
    Xg, Zg = np.meshgrid(xs, zs, indexing="ij")
    f, fb = field(Xg, Zg)
    # bilinear lookup of the coarse surface
    ix = np.clip((Xg - cxs[0]) / step, 0, len(cxs) - 1.001)
    iz = np.clip((Zg - czs[0]) / (step * 0.8), 0, len(czs) - 1.001)
    i0, k0 = ix.astype(int), iz.astype(int)
    fx, fz = ix - i0, iz - k0
    Yb = (cY[i0, k0] * (1 - fx) * (1 - fz) + cY[i0 + 1, k0] * fx * (1 - fz) + cY[i0, k0 + 1] * (1 - fx) * fz
          + cY[i0 + 1, k0 + 1] * fx * fz)
    Yd = depth - Yb
    nx, nz = Xg.shape
    verts = np.stack([Xg.ravel(), Yd.ravel(), Zg.ravel()], 1)
    edge = np.clip(np.minimum(Xg, W - Xg) / 140.0, 0, 1)
    fadev = np.maximum(np.clip(1 - (Zg - zb) / mist, 0, 1) ** 1.2, (1 - edge) * 0.9).ravel()
    inside = f > 0.0
    faces = []
    for i in range(nx - 1):
        for k in range(nz - 1):
            if inside[i, k] and inside[i + 1, k] and inside[i, k + 1] and inside[i + 1, k + 1] and Zg[i, k] >= zb:
                a = i * nz + k
                faces.append((a, a + nz, a + nz + 1, a + 1))
    ob = mesh_obj(name, verts, faces, mat, fadev)
    for p in ob.data.polygons:
        p.use_smooth = False
    ob["zb"], ob["zh"], ob["mist"] = float(zb), float(zt - zb), float(mist)
    ob["blo"], ob["bhi"] = (float(band[0]), float(band[1])) if band else (5.0, 6.0)
    ob["edge"] = 1.0
    return ob


def terraces(name, cx, cy_screen, rx, rdepth, depth, levels, mat, step_h=9):
    """Stacked plates with vertical risers: each level a flat-topped prism, inset from the one below."""
    zb = z_for(cy_screen, depth)
    r = np.random.default_rng(int(cx))
    n = 56
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    wob = 1 + 0.10 * np.sin(ang * 3 + r.uniform(0, 6)) + 0.07 * np.sin(ang * 7 + r.uniform(0, 6))
    for lv in range(levels):
        s_ = 1 - lv / (levels + 1.2)
        ox, od = r.uniform(-0.06, 0.06) * rx, r.uniform(-0.08, 0.08) * rdepth
        w2 = wob * (1 + r.uniform(-0.04, 0.04, n))
        xs = cx + ox + np.cos(ang) * rx * s_ * w2
        ds = depth + od + np.sin(ang) * rdepth * s_ * w2
        z0, z1 = zb + lv * step_h, zb + (lv + 1) * step_h
        verts = [(x, d, z0) for x, d in zip(xs, ds)] + [(x, d, z1) for x, d in zip(xs, ds)]
        faces = [tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        ob = mesh_obj(f"{name}{lv}", verts, faces, mat)
        for p in ob.data.polygons:
            p.use_smooth = False
        ob["zb"], ob["zh"], ob["mist"], ob["blo"], ob["bhi"], ob["edge"] = float(zb), 1.0, float(step_h * 2.6), 5.0, 6.0, 0.0
    return lambda x, d: zb + step_h * max(1, min(levels, int((1 - (((x - cx) / rx) ** 2 + ((d - depth) / rdepth) ** 2) ** 0.5) * (levels + 1.2)) + 1))


for _o in list(bpy.data.objects):
    bpy.data.objects.remove(_o)

# ---------- materials (sampled from the reference) ----------
m_blue = material("blue", [lin("#3A7A93"), lin("#41809A")])
m_blue2 = material("blue2", [lin("#2E708B"), lin("#367892")])
m_cream = material("cream", [lin("#F5F0E6"), lin("#FBF8F1")])
m_cream2 = material("cream2", [lin("#F4EEE3"), lin("#FAF6EE")])
m_cream3 = material("cream3", [lin("#F3ECE0"), lin("#F9F4EB")])
m_coral = material("coral", [lin("#D27A66"), lin("#D98470")])
m_terr = material("terrace", [lin("#8E9C6E"), lin("#A2A77A")])
_nt = m_terr.node_tree
_bsdf = next(n for n in _nt.nodes if n.type == "BSDF_PRINCIPLED")
_geo = _nt.nodes.new("ShaderNodeNewGeometry")
_sep = _nt.nodes.new("ShaderNodeSeparateXYZ")
_nt.links.new(_geo.outputs["Normal"], _sep.inputs[0])
_mr = _nt.nodes.new("ShaderNodeMapRange")
_mr.inputs["From Min"].default_value, _mr.inputs["From Max"].default_value = 0.3, 0.45
_nt.links.new(_sep.outputs["Z"], _mr.inputs["Value"])
_mx = _nt.nodes.new("ShaderNodeMix")
_mx.data_type = "RGBA"
_mx.inputs["A"].default_value = (*lin("#A58C68"), 1)
_mx.inputs["B"].default_value = (*lin("#8FA06C"), 1)
_nt.links.new(_mr.outputs["Result"], _mx.inputs["Factor"])
_nt.links.new(_mx.outputs["Result"], _bsdf.inputs["Base Color"])
m_water = material("water", [lin("#2E7A98"), lin("#3A86A3")], rough=0.8)
_nt = m_water.node_tree
_bsdf = next(n for n in _nt.nodes if n.type == "BSDF_PRINCIPLED")
_tex = _nt.nodes.new("ShaderNodeTexNoise")
_tex.inputs["Scale"].default_value = 0.035
_cr = _nt.nodes.new("ShaderNodeValToRGB")
_cr.color_ramp.elements[0].position = 0.35
_cr.color_ramp.elements[0].color = (*lin("#21607D"), 1)
_cr.color_ramp.elements[1].position = 0.7
_cr.color_ramp.elements[1].color = (*lin("#5A9DB8"), 1)
_e = _cr.color_ramp.elements.new(0.85)
_e.color = (*lin("#B6D2DD"), 1)
_nt.links.new(_tex.outputs["Fac"], _cr.inputs["Fac"])
_nt.links.new(_cr.outputs["Color"], _bsdf.inputs["Base Color"])
m_trunk = material("trunk", [lin("#5A4537"), lin("#7A5A45")])
m_leaf = material("leaf", [lin("#47603E"), lin("#6E8A58")])
ID_OF = {m_blue: "blue", m_blue2: "blue2", m_cream: "cream", m_cream2: "cream2", m_cream3: "cream3", m_coral: "coral",
         m_terr: "terrace", m_water: "water", m_trunk: "trunk", m_leaf: "leaf"}

# ---------- the scene ----------
relief("blueA", [(1240, 40, 440), (985, 110, 120), (1730, 222, 150), (1460, 120, 170)], 340, 900, m_blue, mist=45)
relief("blueB", [(360, 150, 240), (180, 250, 230), (620, 250, 160)], 340, 860, m_blue2, mist=45)
relief("creamA", [(965, 110, 150), (1310, 135, 250), (330, 222, 200)], 350, 700, m_cream, mist=70, band=(0.22, 0.46))
relief("creamM", [(760, 250, 230), (900, 300, 190)], 450, 470, m_cream2, mist=70, band=(0.24, 0.44))
relief("creamB", [(250, 262, 220), (1060, 225, 210), (1640, 300, 210)], 430, 520, m_cream2, mist=60, band=(0.24, 0.44))
relief("creamC", [(1185, 290, 240), (1590, 340, 240), (840, 300, 140), (110, 330, 170)], 470, 400, m_cream3, mist=70)

left = terraces("islandL", 420, 615, 500, 240, 240, 9, m_terr, step_h=6)
right = terraces("islandR", 1360, 615, 460, 170, 260, 8, m_terr, step_h=6)
mid = terraces("islandM", 600, 455, 170, 70, 420, 4, m_terr)

# river: a strip winding toward the viewer, widening
pts = [(780, -40, 170), (900, 40, 140), (800, 120, 110), (940, 200, 90), (850, 290, 70), (960, 380, 55), (900, 470, 42), (980, 560, 34)]
dd = np.linspace(-40, 560, 160)
from numpy import convolve, ones
cx = 880 + 110 * np.sin((dd + 40) / 85.0) * (1 - dd / 900) + dd * 0.12
hw = 46 + (560 - dd) * 0.22
zr = z_for(600, 200) - 4
verts = [(x - w, d, zr) for x, w, d in zip(cx, hw, dd)] + [(x + w, d, zr) for x, w, d in zip(cx, hw, dd)]
n = len(dd)
faces = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
fadev = [max(0.0, min(1.0, (60 - d) / 100)) for d in dd] * 2
mesh_obj("river", verts, faces, m_water, fadev)

# trees: one shared trunk and canopy mesh, linked many times
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1, depth=1)
trunk_mesh = bpy.context.object.data
bpy.data.objects.remove(bpy.context.object)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1)
pad_mesh = bpy.context.object.data
bpy.data.objects.remove(bpy.context.object)
trunk_mesh.materials.append(m_trunk)
pad_mesh.materials.append(m_leaf)
for p in pad_mesh.polygons:
    p.use_smooth = True


PAD_V = np.array([v.co[:] for v in pad_mesh.vertices])
PAD_F = [tuple(p.vertices) for p in pad_mesh.polygons]
TR_V = np.array([v.co[:] for v in trunk_mesh.vertices])
TR_F = [tuple(p.vertices) for p in trunk_mesh.polygons]
canopy_v, canopy_f, trunk_v, trunk_f = [], [], [], []


def _add(vs, fs, V, F, scale, loc):
    base = sum(len(a) for a in vs)
    vs.append(V * np.array(scale) + np.array(loc))
    fs.extend(tuple(i + base for i in f) for f in F)


def tree(x, d, zg, s):
    r = np.random.default_rng(int(x * 13 + d * 7))
    h = s * r.uniform(1.4, 2.5)
    lean = r.uniform(-0.15, 0.15)
    _add(trunk_v, trunk_f, TR_V, TR_F, (s * 0.12, s * 0.12, h / 2 + 2), (x + lean * h / 2, d, zg + h / 2))
    for _ in range(int(r.integers(3, 6))):
        rr = s * r.uniform(0.4, 0.7)
        _add(canopy_v, canopy_f, PAD_V, PAD_F, (rr, rr * 0.9, rr * 0.48),
             (x + lean * h + r.uniform(-0.8, 0.8) * s * 0.9, d + r.uniform(-0.5, 0.5) * s, zg + h + r.uniform(-0.35, 0.35) * s))


placed = []


def plant(x, d, z, s):
    for (px, pd, ps) in placed:
        if (x - px) ** 2 + ((d - pd) * 1.3) ** 2 < (1.2 * (s + ps) / 2) ** 2:
            return
    placed.append((x, d, s))
    tree(x, d, z, s)


for _ in range(260):
    x, d = rng.uniform(-60, 820), rng.uniform(20, 440)
    if ((x - 420) / 500) ** 2 + ((d - 240) / 240) ** 2 < 0.6:
        plant(x, d, left(x, d), rng.uniform(36, 70) * (1.15 - d / 900))
for _ in range(240):
    x, d = rng.uniform(1000, 1800), rng.uniform(100, 420)
    if ((x - 1360) / 460) ** 2 + ((d - 260) / 170) ** 2 < 0.6:
        plant(x, d, right(x, d), rng.uniform(34, 64) * (1.1 - d / 1000))
mid2 = terraces("islandC", 1010, 470, 120, 45, 470, 5, m_terr)
for _ in range(14):
    x, d = rng.uniform(910, 1110), rng.uniform(440, 500)
    plant(x, d, mid2(x, d), rng.uniform(18, 26))
for _ in range(40):
    x, d = rng.uniform(460, 760), rng.uniform(380, 470)
    if ((x - 600) / 170) ** 2 + ((d - 420) / 70) ** 2 < 0.6:
        plant(x, d, mid(x, d), rng.uniform(20, 30))

mesh_obj("canopy", np.concatenate(canopy_v), canopy_f, m_leaf)
mesh_obj("trunks", np.concatenate(trunk_v), trunk_f, m_trunk)
for ob in bpy.context.scene.objects:
    if "zb" not in ob.keys():
        ob["zb"], ob["zh"], ob["mist"], ob["blo"], ob["bhi"], ob["edge"] = -100000.0, 1.0, 0.001, 5.0, 6.0, 0.0

# ---------- voxelize the terrain into wide blocks ----------
SQUASH = 1.8
CELL = {"blue": 8, "cream": 8, "island": 5, "canopy": 3.6, "trunks": 3.6}
for ob in [o for o in bpy.context.scene.objects]:
    if ob.type != "MESH" or ob.data in (trunk_mesh, pad_mesh) or ob.name.startswith("river"):
        continue
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co[:, 0] /= SQUASH
    me.vertices.foreach_set("co", co.ravel())
    me.update()
    ob.scale = (SQUASH, 1, 1)
    span = max(np.ptp(co[:, 0]), np.ptp(co[:, 1]), np.ptp(co[:, 2]))
    cell = next((v for k, v in CELL.items() if ob.name.startswith(k)), 6)
    depth = int(np.clip(round(np.log2(span / cell)), 4, 10))
    mod = ob.modifiers.new("blocks", "REMESH")
    mod.mode = "BLOCKS"
    mod.octree_depth = depth
    mod.scale = 0.99
    mod.use_remove_disconnected = False
    mod.use_smooth_shade = False
    print(ob.name, "span", round(span), "depth", depth)

# ---------- light, camera ----------
sc = bpy.context.scene
for ob in list(sc.objects):
    if ob.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(ob)
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
bg.inputs[1].default_value = 0.55
sun = bpy.data.lights.new("sun", "SUN")
sun.energy = 2.3
sun.angle = math.radians(25)
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

# beauty
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.filepath = BEAUTY
bpy.ops.render.render(write_still=True)

# material ids: flat emission, no filtering
for m, key in ID_OF.items():
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    h = IDS[key].lstrip("#")
    em.inputs["Color"].default_value = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1,)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
sc.cycles.samples = 1
sc.cycles.use_denoising = False
sc.cycles.filter_width = 0.01
sc.render.filepath = IDOUT
bpy.ops.render.render(write_still=True)
print("done")
