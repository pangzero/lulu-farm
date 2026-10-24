from pathlib import Path
import bpy
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'public/models/lulu-meshy-crease.glb'))
bpy.context.scene['lulu_revision']='crease-3'
bpy.context.scene['source']='no-tail-2; local inner/lower eye transition only'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets-source/lulu-meshy-crease.blend'))
