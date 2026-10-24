from pathlib import Path
import bpy

R=Path(__file__).resolve().parents[1]
output=R/'assets-source/lulu-meshy-leftfix.blend'
if output.exists():
    raise RuntimeError('Preserve existing source; choose a new revision filename.')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'public/models/lulu-meshy-leftfix.glb'))
bpy.context.scene['lulu_revision']='leftfix-r3'
bpy.context.scene['source']='crease-3; screen-left eye skin only; eye positions/normals/UV fixed'
bpy.context.scene['art_status']='candidate pending user review; shallow lower-eye seam remains'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(output))
