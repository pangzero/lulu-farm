from pathlib import Path
import bpy
R=Path(__file__).resolve().parents[1]
for name in ['fold','surface','tail','polish']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(R/f'public/models/lulu-meshy-{name}.glb'))
 bpy.ops.wm.save_as_mainfile(filepath=str(R/f'assets-source/lulu-meshy-{name}.blend'))
 print('Saved',name)
