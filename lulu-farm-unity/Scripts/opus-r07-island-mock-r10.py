"""O7 sky-island preview r10 (r09 + horizon cloud towers, nearer islets with life, meadow patches, richer sky).
Original r09 docstring follows.
O7 sky-island preview (bpy 4.5) using the SAME outline/cliff/cloud rules as Assets/Farm/Editor/FarmSkyIslandR09.cs
and the real farm glTF assets. Unity (x,y,z) -> Blender (-x,-z,y). Preview only; Unity output is the reference.
Run: python -c "import sys;sys.argv=['x','--','<outdir>'];exec(open('Scripts/opus-r07-island-mock-r09.py').read())"
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector
OUT = sys.argv[sys.argv.index('--') + 1]
ART = '/home/user/lulu-farm/lulu-farm-unity/Assets/Farm/Art'
WH = {'deer': 1.08, 'alpaca': 1.15, 'E12': 1.1, 'E15': .65, 'S10': 2.1, 'S01': 4.9, 'S02': 3.0, 'E08': 3.2, 'E09': 3.4, 'E10': .75, 'E11': .45, 'cow': 1.02, 'sheep': .72, 'duck': .48, 'chicken': .5, 'pig': .66, 'Lulu': .95}
os.makedirs(OUT, exist_ok=True); rnd = random.Random(91024)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x, sc.render.resolution_y = 1280, 720; sc.view_settings.view_transform = 'Standard'
sc.eevee.taa_render_samples = 32
U = lambda x, z, y=0: Vector((-x, -z, y))
def hexc(h): h = h.lstrip('#'); return tuple((int(h[i:i+2], 16) / 255) ** 2.2 for i in (0, 2, 4))
FOG = hexc('#C9E0E6')

def mat(name, col, rough=.85, emit=0, fog=False, fog_range=(32, 80), fog_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    if fog:   # Unity linear fog 32..80 m, colour #C9E0E6
        cam = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value, mr.inputs[2].default_value = fog_range
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (*(fog_col or FOG), 1); mix = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes['Material Output']
        nt.links.new(cam.outputs['View Distance'], mr.inputs[0]); nt.links.new(mr.outputs[0], mix.inputs[0])
        nt.links.new(b.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])
    return m

def mesh_obj(name, verts, faces, mats, face_mats=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata([U(v[0], v[2], v[1]) for v in verts], [], faces); me.update()
    for m in mats: me.materials.append(m)
    if face_mats: 
        for p, k in zip(me.polygons, face_mats): p.material_index = k
    for p in me.polygons: p.use_smooth = smooth
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o

def place(id_, x, z, yaw=0, s=1.0, y=0):
    before = set(sc.objects); bpy.ops.import_scene.gltf(filepath=f'{ART}/{id_}/model.gltf'); new = [o for o in sc.objects if o not in before]
    root = bpy.data.objects.new(id_, None); sc.collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in new if o.type == 'MESH' for c in o.bound_box]
    lo = min(p.z for p in pts); hi = max(p.z for p in pts); cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    k = WH[id_] / (hi - lo) if id_ in WH else 1
    for o in new:
        if o.parent == root: o.location -= Vector((cx, cy, lo))
    root.scale = (k * s,) * 3; root.rotation_euler.z = math.radians(-yaw); root.location = U(x, z, y); return root

# ---- outline: identical to FarmSkyIslandR09.cs
WX, WZ, WF = 17.0, 12.0, .089
def margin(a):
    m = 2.7 + .8 * math.sin(3 * a + .7) + .5 * math.sin(5 * a + 2.1) + .3 * math.sin(11 * a)
    d = math.atan2(math.sin(a - WF), math.cos(a - WF)); G = lambda x, w: math.exp(-x * x / (2 * w * w))
    return max(1.5, m - 1.8 * G(d, .06) + 1.5 * (G(d - .21, .07) + G(d + .21, .07)))
def wall_dist(x, z): return math.hypot(max(abs(x) - WX, 0), max(abs(z) - WZ, 0))
def ipoint(a, inset=0):
    c, s = math.cos(a), math.sin(a); lo, hi, tg = 0, 80, margin(a) - inset
    for _ in range(48):
        t = (lo + hi) / 2
        if wall_dist(c * t, s * t) < tg: lo = t
        else: hi = t
    return c * lo, s * lo
angles = sorted(set([-math.pi + i * 2 * math.pi / 288 for i in range(288)] + [math.atan2(sz * WZ, sx * WX) for sx in (1, -1) for sz in (1, -1)]))
N = len(angles); rim = [ipoint(a) for a in angles]

grass = mat('grass', hexc('#97C24F')); road = mat('road', hexc('#E3B979'))
strata = [grass, mat('soil', hexc('#8E5E3C')), mat('cream', hexc('#E6C38C')), mat('clay', hexc('#A26E46')), mat('keel', hexc('#7D5E4C'))]
def build_island(name, cx, cz, cy, s, fogged=False):
    sm = [mat(m.name + '-f', tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)[:3], fog=True) for m in strata] if fogged else strata
    verts = [(cx, cy, cz)] + [(cx + x * s, cy, cz + z * s) for x, z in rim]; faces = [(0, 1 + (i + 1) % N, 1 + i) for i in range(N)]; fm = [0] * N
    bands = [[(1, 0), (1.004, -.07), (1.004, -.16)], [(1.004, -.16), (1.008, -.6), (1.0, -1.0)], [(1.0, -1.0), (1.006, -1.3), (.996, -1.6)],
             [(.996, -1.6), (.985, -2.5), (.955, -3.4)], [(.955, -3.4), (.89, -5.2), (.77, -7.6), (.58, -10.2), (.36, -12.6), (.14, -14.6), (.02, -15.6)]]
    for k, band in enumerate(bands):
        b0 = len(verts)
        for f, y in band: verts += [(cx + x * f * s, cy + y * s, cz + z * f * s) for x, z in rim]
        for r in range(len(band) - 1):
            for i in range(N): faces.append((b0 + r * N + i, b0 + r * N + (i + 1) % N, b0 + (r + 1) * N + (i + 1) % N, b0 + (r + 1) * N + i)); fm.append(k)
    return mesh_obj(name, verts, faces, sm, fm)
build_island('Island', 0, 0, 0, 1)

# ---- farm (real layout, simplified roads)
for r in [(-14, -8.3, 15.5, -8.3), (-5, -8.3, -5, 3.2), (-5, 3.2, 5.5, 3.2), (6.5, -8.3, 6.5, 3.2), (2.4, -8.3, 2.4, -6.2), (6.5, -4.3, 11, -4.3), (0, 3.2, 0, 4.7)]:
    x0, z0, x1, z1 = r; dx, dz = x1 - x0, z1 - z0; L = math.hypot(dx, dz); nx, nz = -dz / L * .9, dx / L * .9
    mesh_obj('road', [(x0 + nx, .006, z0 + nz), (x1 + nx, .006, z1 + nz), (x1 - nx, .006, z1 - nz), (x0 - nx, .006, z0 - nz)], [(0, 1, 2, 3)], [road])
mesh_obj('field', [(-11.5, .01, -2.5), (-5.5, .01, -2.5), (-5.5, .01, 5.9), (-11.5, .01, 5.9)], [(0, 1, 2, 3)], [mat('soil-f', hexc('#7A4B30'))])
water = mat('water', hexc('#3FA9D6'), .15)
br = 1.2 / (math.pi / 2); px0, px1, pz0, pz1 = 7.4, 7.4 + 6 + 2 * br, -2.7, -2.7 + 7.2 + 2 * br
mesh_obj('pond', [(px0, .01, pz0), (px1, .01, pz0), (px1, .01, pz1), (px0, .01, pz1)], [(0, 1, 2, 3)], [water])
place('S01', 0, 6.3, 180)
b = place('S02', 3.6, .35, 180, .8); b.scale.x *= -1
for a, (x, z) in zip(['cow', 'sheep', 'chicken', 'pig', 'duck'], [(-1.7, -.3), (1, -1.5), (-2.2, -4.2), (.7, -4.3), (3.8, -4.4)]): place(a, x, z, 150 + 35 * ['cow', 'sheep', 'chicken', 'pig', 'duck'].index(a))
for x in range(-3, 6): place('S05', x * 1.2 - .6, 1.9, 0); place('S05', x * 1.2 - .6, -6.5, 0)
for z in range(-5, 2): place('S05', -3.6, z * 1.2 + .1, 90); place('S05', 6, z * 1.2 + .1, 90)
for i, (x, z) in enumerate([(-14, -9.5), (-10.8, -10), (-5.8, -10.4), (6, -10), (12.6, -10), (15.7, -6), (15.7, 8), (9, 9.5), (4, 10), (-4.2, 9.2), (-9, 8.6), (-14.1, 6), (-14.5, .5), (-4, 1.2)]):
    place('E09' if i % 4 == 1 else 'E08', x, z, i * 39, .85 + (i % 3) * .08)

# ---- rim planting (same rules as the Builder)
near_cove = lambda a: abs(math.degrees(math.atan2(math.sin(a - WF), math.cos(a - WF)))) < 9
arc = 0
while arc < 2 * math.pi:
    a = arc - math.pi; arc += rnd.uniform(.08, .13)
    if near_cove(a): continue
    x, z = ipoint(a, rnd.uniform(.6, min(1.2, margin(a) - .3))); fl = rnd.random() < .45
    place('E11' if fl else 'E10', x, z, rnd.uniform(0, 360), rnd.uniform(.55, .8) if fl else rnd.uniform(.8, 1.1))
for deg in [22, 58, 128, 162, 205, 232]:
    a = math.radians(deg)
    if margin(a) < 3.1: continue
    for i in range(2 + rnd.randrange(2)):
        b2 = a + rnd.uniform(-.04, .04); x, z = ipoint(b2, margin(b2) * rnd.uniform(.45, .6))
        place('E08' if rnd.random() < .7 else 'E09', x, z, rnd.uniform(0, 360), rnd.uniform(.8, 1.05))

# ---- stream + waterfall
lx, lz = ipoint(WF); ol = math.hypot(lx, lz); ox, oz = lx / ol, lz / ol; tx, tz = -math.sin(WF), math.cos(WF)
sx, sz = px1 + .45, lz; vs, fs = [], []
for i in range(11):
    s = i / 10; cx = sx + (lx + ox * .04 - sx) * s + tx * math.sin(s * math.pi) * .35; cz = sz + (lz + oz * .04 - sz) * s + tz * math.sin(s * math.pi) * .35; w = .55 + .15 * s
    vs += [(cx - tx * w, .014, cz - tz * w), (cx + tx * w, .014, cz + tz * w)]
    if i: k = len(vs) - 4; fs.append((k, k + 1, k + 3, k + 2))
mesh_obj('stream', vs, fs, [water])
vs, fs = [], []
for j in range(17):
    d = j * .6; off = 2.0 * math.sqrt(d / 9.81 * 2); cx, cz = lx + ox * off, lz + oz * off; w = .7 + d * .03
    vs += [(cx - tx * w, .014 - d, cz - tz * w), (cx + tx * w, .014 - d, cz + tz * w)]
    if j: k = len(vs) - 4; fs.append((k, k + 1, k + 3, k + 2))
mesh_obj('fall', vs, fs, [mat('fall', hexc('#BFE9F7'), .3, .35)])

# ---- clouds (flattened ellipsoids, same counts/ranges as the Builder)
cv, cf = [], []; tv, tf = [], []
def ellipsoid(c, r, V=None, F=None, flat=.45):
    V = cv if V is None else V; F = cf if F is None else F; k = len(V)
    for i in range(7):
        th = math.pi * i / 6
        for j in range(10):
            ph = 2 * math.pi * j / 10; y = math.cos(th); y = y * flat if y < 0 else y
            V.append((c[0] + math.sin(th) * math.cos(ph) * r[0], c[1] + y * r[1], c[2] + math.sin(th) * math.sin(ph) * r[2]))
    for i in range(6):
        for j in range(10):
            a = k + i * 10 + j; b_ = k + i * 10 + (j + 1) % 10; F.append((a, b_, b_ + 10, a + 10))
def puff(c, size):
    for _ in range(3 + rnd.randrange(3)):
        ellipsoid((c[0] + rnd.uniform(-1, 1) * size * .8, c[1] + rnd.uniform(-.15, .25) * size, c[2] + rnd.uniform(-1, 1) * size * .8),
                  (size * rnd.uniform(.7, 1.1), size * rnd.uniform(.45, .6), size * rnd.uniform(.7, 1.1)))
arc = 0
while arc < 2 * math.pi:
    a = arc - math.pi; arc += rnd.uniform(.07, .11); x, z = ipoint(a); l = math.hypot(x, z); d = rnd.uniform(1.2, 4.5)
    puff((x + x / l * d, rnd.uniform(-3.4, -2.6), z + z / l * d), rnd.uniform(1.6, 2.8))
puff((lx + ox * 2.6, -4.6, lz + oz * 2.6), 2.4); puff((lx + ox * 2.2, -1.6, lz + oz * 2.2), 1.5)
for _ in range(170):
    a = rnd.uniform(-math.pi, math.pi); d = rnd.uniform(28, 112); puff((math.cos(a) * d, rnd.uniform(-10, -5), math.sin(a) * d), rnd.uniform(3, 7.5))
cloudm = mat('cloud', hexc('#FFF8EE'), 1, .06, fog=True); floorm = mat('cloudfloor', hexc('#C9DDEE'), 1, .12, fog=True)
# r10: towering cumulus on the horizon (85–112 m), with their own long fog so they keep their shape
HZ = hexc('#DDEDF2')
for i in range(13):
    a = -math.pi + i * 2 * math.pi / 13 + rnd.uniform(-.12, .12); d = rnd.uniform(86, 112); cx, cz = math.cos(a) * d, math.sin(a) * d
    tx_, tz_ = -math.sin(a), math.cos(a); h = rnd.uniform(.6, 1.0)
    for layer, (n, lo, hi, y0, y1) in enumerate([(5, 8, 11, -4, 0), (3, 6, 8.5, 5, 9), (2, 4, 6, 12, 18)]):
        for _ in range(n if layer < 2 or h > .75 else 1):
            o = rnd.uniform(-1, 1) * (16 - layer * 5); sz = rnd.uniform(lo, hi)
            ellipsoid((cx + tx_ * o, rnd.uniform(y0, y1) * h, cz + tz_ * o), (sz, sz * rnd.uniform(.65, .8), sz), tv, tf, .3)
mesh_obj('towers', tv, tf, [mat('tower', hexc('#FFF8EE'), 1, .08, fog=True, fog_range=(70, 190), fog_col=HZ)], smooth=True)
mesh_obj('clouds', cv, cf, [cloudm], smooth=True)
mesh_obj('cloudfloor', [(0, -9, 0)] + [(math.cos(i * math.pi / 24) * 170, -9, math.sin(i * math.pi / 24) * 170) for i in range(48)], [(0, 1 + (i + 1) % 48, 1 + i) for i in range(48)], [floorm])
# r10: nearer islets at mixed heights (one above eye level shows its keel), some with a little life on top
ISLETS = [((34, 18), -2.0, .30, [('E08', -2.5, 1.0, 1.0), ('E09', 2.6, -.4, .9), ('deer', .3, .6, 1.0), ('E10', -.8, -2.2, 1), ('E11', 1.4, 2.0, .8), ('E11', -3.6, -1.0, .7)]),
          ((-30, 26), 7.0, .26, [('E09', 0, .4, 1.0), ('E11', -1.6, -1.4, .8), ('E10', 2.0, -.8, .9)]),
          ((8, -36), -4.0, .22, [('S10', -1.0, .2, 1.0), ('E15', 1.6, -.6, 1.0), ('E11', .4, 1.6, .8), ('E08', 2.2, 1.4, .8)]),
          ((-38, -20), 1.0, .20, [('alpaca', .5, .2, 1.0), ('E08', -1.8, .6, .85), ('E11', 1.6, -1.2, .7)]),
          ((55, -10), 10.0, .14, [('E08', 0, 0, .9)]), ((-60, 40), -2.0, .16, [('E08', 0, 0, 1.0)]), ((20, 52), 4.0, .15, [('E09', 0, 0, 1.0)])]
for (x, z), y, s, props in ISLETS:
    build_island('islet', x, z, y, s, fogged=True)
    for pid, ox_, oz_, k in props: place(pid, x + ox_, z + oz_, rnd.uniform(0, 360), k, y)
    for _ in range(3): puff((x + rnd.uniform(-1, 1) * 12 * s, y - 15 * s * rnd.uniform(.5, .9), z + rnd.uniform(-1, 1) * 9 * s), 9 * s)
for (x, z), y, s in [((24, -20), 3.0, .05), ((-26, -9), -1.0, .06), ((-12, 22), 5.0, .045), ((27, 4), 1.5, .04)]:   # floating rocks
    build_island('rock', x, z, y, s, fogged=True)
# r10: meadow patches in the rim band (clusters, not a hedge); reeds by the cove
for deg in [-150, -120, -95, -60, -35, 40, 75, 100, 140, 185]:
    a = math.radians(deg)
    for _ in range(6):
        b2 = a + rnd.uniform(-.05, .05); x, z = ipoint(b2, rnd.uniform(.5, max(.6, margin(b2) - .4)))
        place('E11', x, z, rnd.uniform(0, 360), rnd.uniform(.6, .95))
for k in range(5):
    b2 = WF + (.11 if k % 2 else -.11) + rnd.uniform(-.03, .03); x, z = ipoint(b2, rnd.uniform(.4, 1.0)); place('E12', x, z, rnd.uniform(0, 360), rnd.uniform(.7, .9))

# ---- sky like FarmSky-r08 (horizon = fog colour), sun like Lighting()
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree
tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); rp = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(tc.outputs['Generated'], sp.inputs[0]); nt.links.new(sp.outputs['Z'], rp.inputs[0])
rp.color_ramp.elements[0].position = .5; rp.color_ramp.elements[0].color = (*HZ, 1); rp.color_ramp.elements[1].position = 1; rp.color_ramp.elements[1].color = (*hexc('#4C97D6'), 1)
mid = rp.color_ramp.elements.new(.55); mid.color = (*hexc('#9CCDEB'), 1)
nt.links.new(rp.outputs[0], nt.nodes['Background'].inputs[0])
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.4; sun.data.color = hexc('#FFF0DA'); sun.data.angle = math.radians(6)
sun.rotation_euler = (math.radians(42), 0, math.radians(35)); sc.collection.objects.link(sun)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(52); cam.data.clip_end = 120
lulu = None
def game(name, tx_, tz_, yaw_deg, pitch=35, dist=5.1):
    global lulu
    if lulu is None: lulu = place('Lulu', 0, 0)
    lulu.location = U(tx_, tz_, 0); lulu.rotation_euler.z = math.radians(-yaw_deg)
    yaw, p = math.radians(yaw_deg), math.radians(pitch); fx, fz = math.sin(yaw), math.cos(yaw)
    cam.location = U(tx_ - fx * math.cos(p) * dist, tz_ - fz * math.cos(p) * dist, .8 + math.sin(p) * dist)
    cam.rotation_euler = (U(tx_, tz_, .8) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}/{name}.png'; bpy.ops.render.render(write_still=True)
game('g1-east-out', 16.3, -3.5, 75)            # walking to the east wall, south of the cove
game('g2-cove', 16.0, 5.6, 150)                 # north-east corner of the play area, looking at the cove
game('g3-south-out', 3, -11.3, 180)             # south wall, looking out over the clouds
game('g4-north-far', -6, 11.3, 0, 15, 8.6)       # north wall, flattest pitch, furthest zoom
game('g5-west-out', -16.3, 2, -90, 25, 6.5)      # west wall
cam.data.sensor_fit = 'AUTO'; cam.data.lens = 30; cam.location = U(34, -42, 15); cam.rotation_euler = (U(0, 0, -5) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = f'{OUT}/overview.png'; bpy.ops.render.render(write_still=True)
