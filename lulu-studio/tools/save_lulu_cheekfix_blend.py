from pathlib import Path
import bpy

R = Path(__file__).resolve().parents[1]
output = R / 'assets-source/lulu-meshy-cheekfix.blend'
if output.exists():
    raise RuntimeError('Preserve existing revision; do not overwrite.')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R / 'public/models/lulu-meshy-cheekfix.glb'))
bpy.context.scene['lulu_revision'] = 'cheekfix-r4'
bpy.context.scene['source'] = 'Imported corrected GLB; based on leftfix-r3, user red-box cheek only'
bpy.context.scene['art_status'] = 'Pending review; small improvement; longer lower-eye line remains'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(output))
