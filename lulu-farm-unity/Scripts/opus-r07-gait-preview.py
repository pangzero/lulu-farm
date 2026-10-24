"""Preview of the O7 procedural gait (same formula as LivingSurface-r10 Gait()) on the real animal meshes.
Renders side views over one gait cycle with bpy 4.5. Run:
python -c "import sys;sys.argv=['x','--','<outdir>'];exec(open('Scripts/opus-r07-gait-preview.py').read())"
"""
import bpy, json, math, sys, os, numpy as np
OUT = sys.argv[sys.argv.index('--') + 1]; os.makedirs(OUT, exist_ok=True)
ART = '/home/user/lulu-farm/lulu-farm-unity/Assets/Farm/Art'
# Measured from the LOD0 meshes (object space, metres before the prefab's worldHeight scale): leg top band,
# front/back split, stride half-amplitude, foot lift, body bob, biped flag, waddle roll. Kept in sync with
# FarmAnimalWalkR10.GaitTable.
GAIT = {
    'cow':     dict(top0=.15, top1=.28, midz=-.11, stride=.10, lift=.06, bob=.012, biped=0, roll=0),
    'sheep':   dict(top0=.08, top1=.21, midz=-.08, stride=.09, lift=.05, bob=.012, biped=0, roll=0),
    'pig':     dict(top0=.05, top1=.15, midz=-.11, stride=.09, lift=.05, bob=.010, biped=0, roll=0),
    'chicken': dict(top0=.06, top1=.19, midz=0,    stride=.10, lift=.07, bob=.030, biped=1, roll=.03),
    'duck':    dict(top0=.10, top1=.21, midz=0,    stride=.09, lift=.05, bob=.020, biped=1, roll=.07),
}
def smooth(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def foot(s, A, L):
    """s in [0,1): first half stance (foot slides back, planted), second half swing (lifts, returns forward)."""
    st = s < .5; u = np.where(st, s * 2, (s - .5) * 2)
    dz = np.where(st, A * (1 - 2 * u), A * (-1 + 2 * smooth(0, 1, u)))
    dy = np.where(st, 0, L * np.sin(np.pi * u)); return dz, dy
def gait(P, floor, g, phase, amount=1.0):
    p = P.copy(); y = p[:, 1] - floor
    w = 1 - smooth(g['top0'], g['top1'], y)                     # 1 on the legs, 0 on the body
    side = np.sign(p[:, 0] + 1e-6); front = np.sign(p[:, 2] - g['midz'] + 1e-6)
    off = np.where(g['biped'] > .5, (side > 0) * .5, ((side * front) > 0) * .5)   # diagonal pairs / alternate feet
    s = (phase / (2 * np.pi) + off) % 1
    dz, dy = foot(s, g['stride'], g['lift'])
    p[:, 2] += dz * w * amount; p[:, 1] += dy * w * amount
    body = 1 - w
    p[:, 1] += g['bob'] * np.cos(2 * phase) * body * amount       # two bobs per cycle
    r = g['roll'] * np.sin(phase) * amount * body                  # waddle about the forward axis at the feet
    c, sn = np.cos(r), np.sin(r); yy = p[:, 1] - floor; xx = p[:, 0]
    p[:, 0] = c * xx - sn * yy; p[:, 1] = floor + sn * xx + c * yy
    return p
sys.path.insert(0, '/tmp/claude-0'); from animal_load import load
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x, sc.render.resolution_y = 360, 300; sc.eevee.taa_render_samples = 8
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.85, .9, .95, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sc.collection.objects.link(sun)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.3
m = bpy.data.materials.new('m'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.8, .7, .6, 1)
gm = bpy.data.materials.new('g'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.35, .55, .3, 1)
for a, g in GAIT.items():
    P, T = load(a); floor = P[:, 1].min()
    me = bpy.data.meshes.new(a); me.from_pydata([(-x, z, y) for x, y, z in P], [], [tuple(t) for t in T]); me.materials.append(m)
    ob = bpy.data.objects.new(a, me); sc.collection.objects.link(ob)
    gr = bpy.data.meshes.new('gr'); gr.from_pydata([(-3, -3, floor), (3, -3, floor), (3, 3, floor), (-3, 3, floor)], [], [(0, 1, 2, 3)]); gr.materials.append(gm)
    gro = bpy.data.objects.new('gr', gr); sc.collection.objects.link(gro)
    cam.location = (3, 0, 0); cam.rotation_euler = (math.radians(90), 0, math.radians(90))    # side view (+x), head toward +y
    for k in range(8):
        ph = k / 8 * 2 * math.pi; D = gait(P, floor, g, ph)
        me.vertices.foreach_set('co', np.array([(-x, z, y) for x, y, z in D]).ravel()); me.update()
        sc.render.filepath = f'{OUT}/{a}-{k}.png'; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ob); bpy.data.objects.remove(gro)
