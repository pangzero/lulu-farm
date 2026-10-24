"""Import and save the exact neutral GLB as an independent inspection copy."""
from pathlib import Path
import bpy
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review/lulu-hybrid-color-20261023/handoff'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT / 'lulu-color-r03-neutral-gray.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
assert len(meshes) == 9
assert not any(o.type == 'ARMATURE' for o in bpy.data.objects)
for view in bpy.data.screens:
    for area in view.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'lulu-color-r03-neutral-gray.blend'))
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'lulu-color-r03-neutral-gray.blend'))
assert len([o for o in bpy.data.objects if o.type == 'MESH']) == 9
print(json.dumps({'import_save_reopen': True, 'meshes': 9, 'armatures': 0}))
