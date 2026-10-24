"""Sky-island concept mock (Blender/bpy 4.5). Uses the real farm GLTF assets at their Builder positions.
Unity (x,y,z) -> Blender (-x,-z,y). Run: python island_mock.py <variant A|B> <outdir>"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, noise
VAR, OUT = sys.argv[sys.argv.index('--') + 1], sys.argv[sys.argv.index('--') + 2]
ART = '/home/user/lulu-farm/lulu-farm-unity/Assets/Farm/Art'
WH = {'S01': 4.9, 'E08': 3.2, 'E09': 3.4, 'E10': .75, 'E11': .45, 'cow': 1.02, 'sheep': .72, 'duck': .48, 'chicken': .5, 'pig': .66}
os.makedirs(OUT, exist_ok=True); random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x, sc.render.resolution_y = 1600, 900; sc.view_settings.view_transform = 'Standard'
sc.eevee.taa_render_samples = 32
U = lambda x, z, y=0: Vector((-x, -z, y))

def mat(name, col, rough=.85, emit=0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*col, 1); b.inputs['Emission Strength'].default_value = emit
    return m

def hexc(h): h = h.lstrip('#'); return tuple((int(h[i:i+2], 16) / 255) ** 2.2 for i in (0, 2, 4))

# ---------------- island outline (rounded rectangle + soft lobes), playable 34x24 inside
def radius(a):
    c, s = math.cos(a), math.sin(a); n = 3.2
    base = 1 / ((abs(c) / 23.0) ** n + (abs(s) / 17.5) ** n) ** (1 / n)
    return base + 1.6 * math.sin(3 * a + .7) + 1.0 * math.sin(5 * a + 2.1) + .6 * math.sin(9 * a)

def island(style):
    bm = bmesh.new(); N = 160; rings = []
    # top: flat grass with a soft rolled lip over the last 1.2 m
    prof_top = [(0, 0), (.55, 0), (.8, -.05), (.93, -.18), (1.0, -.45)]
    if style == 'A':   # soft "cake": layered rounded strata tapering to a gentle point
        prof = [(1.0, -.45), (1.01, -1.4), (.97, -2.6), (.99, -3.4), (.93, -4.6), (.88, -5.6), (.78, -7.4), (.62, -9.6), (.42, -12.0), (.22, -14.0), (.06, -15.4)]
    else:              # rocky: deeper, irregular, with a long rocky keel
        prof = [(1.0, -.45), (1.02, -1.8), (.95, -3.2), (.86, -5.4), (.80, -6.6), (.66, -9.6), (.50, -13.0), (.34, -16.5), (.18, -20.0), (.05, -23.0)]
    profile = prof_top + prof[1:]
    verts = []
    for k, (f, y) in enumerate(profile):
        ring = []
        for i in range(N):
            a = i / N * 2 * math.pi; r = radius(a) * f
            if style == 'B' and y < -1: r *= 1 + .12 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, y * .35)))
            x, z = math.cos(a) * r, math.sin(a) * r
            ring.append(bm.verts.new(U(x, z, y)))
        rings.append(ring)
    centre = bm.verts.new(U(0, 0, 0))
    for i in range(N): bm.faces.new((centre, rings[0][(i + 1) % N], rings[0][i]))
    for k in range(len(rings) - 1):
        for i in range(N):
            bm.faces.new((rings[k][i], rings[k][(i + 1) % N], rings[k + 1][(i + 1) % N], rings[k + 1][i]))
    tip = bm.verts.new(U(0, 0, profile[-1][1] - 1.2))
    for i in range(N): bm.faces.new((rings[-1][i], rings[-1][(i + 1) % N], tip))
    me = bpy.data.meshes.new('Island'); bm.to_mesh(me); ob = bpy.data.objects.new('Island', me); sc.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = sum(me.vertices[v].co.z for v in p.vertices) / len(p.vertices) < -.03
    # height-banded material: grass top, grass lip, then soil strata
    grass, lip = mat('grass', hexc('#9FCB4E')), mat('lip', hexc('#7DB43F'))
    strata = [mat('s1', hexc('#C98A55')), mat('s2', hexc('#B4744A')), mat('s3', hexc('#D9A56B')), mat('s4', hexc('#9C6A4A')), mat('rock', hexc('#8F8578') if style == 'B' else hexc('#A77B5B'))]
    for m in [grass, lip] + strata: me.materials.append(m)
    for p in me.polygons:
        zc = sum(me.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if zc > -.02: p.material_index = 0
        elif zc > -.5: p.material_index = 1
        else:
            band = int((-zc) / (1.6 if style == 'A' else 2.4)); p.material_index = 2 + min(band % 4 if zc > -9 else 4, 4)
    return ob

def cloud(center, size, seed, tint=(1, 1, 1)):
    rnd = random.Random(seed); m = bpy.data.materials.get('cloud') or mat('cloud', (1, .99, .97), 1, .12)
    for k in range(rnd.randint(5, 9)):
        off = Vector((rnd.uniform(-1, 1) * size, rnd.uniform(-1, 1) * size * .6, rnd.uniform(-.2, .5) * size * .5))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=size * rnd.uniform(.45, .8), location=center + off)
        o = bpy.context.object; o.scale.z = .55; o.data.materials.append(m); bpy.ops.object.shade_smooth()

def place(id_, x, z, yaw=0, s=1.0, y=0):
    path = f'{ART}/{id_}/model.gltf'
    before = set(sc.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in sc.objects if o not in before]
    root = bpy.data.objects.new(id_, None); sc.collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in new if o.type == 'MESH' for c in o.bound_box]
    lo = min(p.z for p in pts); hi = max(p.z for p in pts); cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
    k = (WH.get(id_) or 0) / (hi - lo) if WH.get(id_) else 1
    for o in new:
        if o.parent == root: o.location -= Vector((cx, cy, lo))
    root.scale = (k * s,) * 3; root.rotation_euler.z = math.radians(-yaw); root.location = U(x, z, y)
    return root

def flat(name, pts, col, y=.012):
    bm = bmesh.new(); vs = [bm.verts.new(U(x, z, y)) for x, z in pts]; bm.faces.new(vs)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(mat(name, col, .9)); return o

def rect(name, x0, z0, x1, z1, col, y=.012): return flat(name, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], col, y)

# ---------------- build
island(VAR)
road = hexc('#E3B979')
for r in [(-6.1, 2.25, 7.4, 4.05), (-6.1, -8.4, -4.3, 4.05), (-6.1, -8.4, 7.4, -6.6), (5.6, -8.4, 7.4, 4.05), (-.9, 4.05, .9, 5.2)]: rect('road', *r, road)
rect('fieldsoil', -11.5, -2.5, -5.5, 5.9, hexc('#8A5A3A'), .02)
for i in range(5):
    for j in range(4): rect('plot', -11.3 + j * 1.45, -2.3 + i * 1.6, -10.0 + j * 1.45, -.9 + i * 1.6, hexc('#6E432A'), .03)
pond = [(8.6 + 3.4 + 3.4 * math.cos(t / 24 * 6.283) * (1 + .08 * math.sin(3 * t)), 1.3 + 4.6 * math.sin(t / 24 * 6.283)) for t in range(24)]
flat('pond', pond, hexc('#46B6E6'), .02)
if VAR == 'B':  # stream from the pond to the east rim and a waterfall into the clouds
    flat('stream', [(15.2, .6), (22.5, .2), (22.5, 1.9), (15.2, 2.2)], hexc('#46B6E6'), .021)
    bm = bmesh.new(); vs = [bm.verts.new(U(22.3, z, y)) for z, y in [(.2, 0), (1.9, 0), (1.9, -14), (.2, -14)]]; bm.faces.new(vs)
    me = bpy.data.meshes.new('fall'); bm.to_mesh(me); o = bpy.data.objects.new('fall', me); sc.collection.objects.link(o); o.data.materials.append(mat('fall', hexc('#BDEBFF'), .2, .25))
house = place('S01', 0, 6.3, 180)
for x in range(-3, 6):  # pasture fence north/south
    place('S05', x * 1.2 - .6, 1.9, 0); place('S05', x * 1.2 - .6, -6.5, 0)
for z in range(-5, 2): place('S05', -3.6, z * 1.2 + .1, 90); place('S05', 6, z * 1.2 + .1, 90)
for a, (x, z) in zip(['cow', 'sheep', 'chicken', 'pig', 'duck'], [(-1.7, -.3), (1, -1.5), (-2.2, -4.2), (.7, -4.3), (3.8, -4.4)]): place(a, x, z, random.uniform(0, 360))
# rim planting: bushes/flowers along the lip, clustered trees on the rim (no far scattered trees)
for i in range(90):
    a = i / 90 * 2 * math.pi; r = radius(a) - random.uniform(1.2, 2.6)
    x, z = math.cos(a) * r, math.sin(a) * r
    if abs(x) < 17.5 and abs(z) < 12.5: continue
    place(random.choice(['E10', 'E11', 'E11']), x, z, random.uniform(0, 360), random.uniform(.85, 1.2))
for i in range(16):
    a = i / 16 * 2 * math.pi + random.uniform(-.1, .1)
    if -1.1 < a < -.2: continue  # keep the south-east view to the clouds open
    r = radius(a) - random.uniform(2.6, 4.2); x, z = math.cos(a) * r, math.sin(a) * r
    if abs(x) < 17.5 and abs(z) < 12.5: continue
    for t in range(random.randint(1, 3)):
        place('E08' if random.random() < .75 else 'E09', x + random.uniform(-1.6, 1.6), z + random.uniform(-1.2, 1.2), random.uniform(0, 360), random.uniform(.75, 1.15))
for (x, z) in [(-14, -9.5), (-10.8, -10), (6, -10), (12.6, -10), (15.7, 8), (4, 10), (-9, 8.6), (-14.5, .5)]: place('E08', x, z, random.uniform(0, 360), .9)
# cloud sea below and around; a few distant islets
for i in range(70):
    a = random.uniform(0, 2 * math.pi); d = random.uniform(24, 95)
    cloud(U(math.cos(a) * d * 1.2, math.sin(a) * d, random.uniform(-16, -9)), random.uniform(3.5, 8), i)
for i, (x, z, y, s) in enumerate([(62, 40, -2, .35), (-70, 30, 3, .25), (55, -55, -5, .3)]):
    ob = island('A'); ob.scale = (s, s, s); ob.location = U(x, z, y)
    place('E08', x, z, 0, s * 1.6, y)
# sky
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree
tex = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ramp = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(tex.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], ramp.inputs[0])
ramp.color_ramp.elements[0].position = .0; ramp.color_ramp.elements[0].color = (*hexc('#F4EEE4'), 1)
ramp.color_ramp.elements[1].position = .32; ramp.color_ramp.elements[1].color = (*hexc('#8CC3EC'), 1)
nt.links.new(ramp.outputs[0], nt.nodes['Background'].inputs[0]); nt.nodes['Background'].inputs[1].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.2; sun.data.color = hexc('#FFF0DA'); sun.data.angle = math.radians(6)
sun.rotation_euler = (math.radians(42), 0, math.radians(35)); sc.collection.objects.link(sun)
sc.eevee.use_shadows = True if hasattr(sc.eevee, 'use_shadows') else None
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
def shoot(name, pos, target, lens):
    cam.location = pos; cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens; cam.data.clip_end = 600
    sc.render.filepath = f'{OUT}/{name}.png'; bpy.ops.render.render(write_still=True)
shoot('hero', U(34, -42, 15), U(0, 0, -5), 30)
shoot('edge', U(14, -8, 2.8), U(30, -17, -4), 24)
shoot('rim-north', U(-6, 4, 3.2), U(-14, 22, -1), 24)
shoot('play', U(0, -6.5, 4.2), U(0, 4, .6), 24)
