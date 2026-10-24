"""Blender render of a game GLB. Run: Blender -b --factory-startup -P render_lulu.py -- game.glb outdir job [frames]
jobs: views (front/quarter/side/back/clay-quarter), run (front + front-l45 for every Run frame), walk, wardrobe (original/blue-stars/watermelon),
      eyes (close-up front/quarter + rake), crotch (low front close-up of shorts for every Run frame).
"""
import bpy, sys, math, os
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]; GLB, OUT, JOB = argv[0], argv[1], argv[2]; os.makedirs(OUT, exist_ok=True)
STUDIO = '/Users/haowen/IdeaProjects/farm-game/lulu-studio/public'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); meshes = [o for o in sc.objects if o.type == 'MESH']
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.render.resolution_x = sc.render.resolution_y = 800; sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.93, .93, .9, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .65
for name, rot, energy in (('key', (50, 0, -35), 2.4), ('fill', (60, 0, 140), 1.2), ('top', (0, 0, 0), .8)):
    l = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN')); l.data.energy = energy; l.data.angle = math.radians(8)
    l.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(l)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam

def action(name):
    acts = [a for a in bpy.data.actions if a.name == name or a.name.startswith(name + '_') or a.name.startswith(name)]
    arm.animation_data_create(); arm.animation_data.action = acts[0] if acts else None
    if acts and arm.animation_data.action_slot is None and acts[0].slots: arm.animation_data.action_slot = acts[0].slots[0]
    return acts[0] if acts else None

def bounds():
    dg = bpy.context.evaluated_depsgraph_get(); lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in meshes:
        e = o.evaluated_get(dg)
        for c in e.bound_box:
            v = e.matrix_world @ Vector(c); lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    return lo, hi

def shoot(path, yaw, pitch=8, target=None, dist=None, lens=50, ortho=None):
    lo, hi = bounds(); ctr = target if target is not None else (lo + hi) / 2; d = dist or (hi - lo).length * 1.15
    y, p = math.radians(yaw), math.radians(pitch); off = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * d
    cam.location = ctr + off; cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens; cam.data.clip_start = .01
    if ortho: cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else: cam.data.type = 'PERSP'
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)

def clay(on):
    for o in meshes:
        if on:
            o['_mats'] = [s.material.name if s.material else '' for s in o.material_slots]
            m = bpy.data.materials.get('clay') or bpy.data.materials.new('clay'); m.use_nodes = True; m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.72, .72, .69, 1)
            m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .8
            for s in o.material_slots: s.material = m
        else:
            for s, n in zip(o.material_slots, o['_mats']): s.material = bpy.data.materials.get(n)

def fabric(preset):
    sh = next(o for o in meshes if o.name.startswith('Shorts')); orig = bpy.data.materials.get('Lulu_Shorts_Original')
    if preset == 'original':
        for s in sh.material_slots: s.material = orig
        return
    m = bpy.data.materials.new('Shorts_' + preset); m.use_nodes = True; nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value = .86
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(f'{STUDIO}/models/wardrobe-rig/materials-v2/{preset}.png')
    uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = sh.data.uv_layers[1].name
    nt.links.new(uv.outputs['UV'], tex.inputs['Vector']); nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    for s in sh.material_slots: s.material = m

lo, hi = bounds(); H = hi.z - lo.z; mid = (lo + hi) / 2
if JOB == 'views':
    action('Idle'); sc.frame_set(0)
    for n, yaw in (('front', 0), ('quarter', 35), ('side', 90), ('back', 180)): shoot(f'{OUT}/{n}.png', yaw)
    clay(True); shoot(f'{OUT}/clay-quarter.png', 35); shoot(f'{OUT}/clay-back.png', 180); clay(False)
elif JOB in ('run', 'walk', 'crotch'):
    a = action('Run' if JOB != 'walk' else 'Walk'); f0, f1 = map(int, a.frame_range)
    frames = [int(x) for x in argv[3].split(',')] if len(argv) > 3 else list(range(f0, f1))
    for f in frames:
        sc.frame_set(f)
        if JOB == 'crotch':
            t = Vector((mid.x, mid.y, lo.z + H * .2)); sc.render.resolution_x, sc.render.resolution_y = 800, 500
            shoot(f'{OUT}/f{f:02d}-front.png', 0, 5, t, H * 1.1); shoot(f'{OUT}/f{f:02d}-l45.png', 45, 5, t, H * 1.1)
        else:
            shoot(f'{OUT}/f{f:02d}-front.png', 0); shoot(f'{OUT}/f{f:02d}-side.png', 90)
elif JOB == 'wardrobe':
    action('Idle'); sc.frame_set(0)
    for p in ('original', 'blue-stars', 'watermelon'):
        fabric(p); shoot(f'{OUT}/{p}-front.png', 0); shoot(f'{OUT}/{p}-back.png', 160)
    fabric('original')
elif JOB == 'eyes':
    action('Idle'); sc.frame_set(0); t = Vector((mid.x, lo.y, lo.z + H * .82))
    shoot(f'{OUT}/eyes-front.png', 0, 4, t, H * .9, 85); shoot(f'{OUT}/eyes-quarter.png', 40, 10, t, H * .9, 85); shoot(f'{OUT}/eyes-rake.png', 70, 25, t, H * .9, 85)
