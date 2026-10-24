from pathlib import Path
import bpy
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'public/models/lulu-meshy-notail.glb'))
bpy.context.scene['lulu_revision']='no-tail-2'
bpy.context.scene['source']='natural-6; local tail deletion; eyes unchanged'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets-source/lulu-meshy-notail.blend'))
