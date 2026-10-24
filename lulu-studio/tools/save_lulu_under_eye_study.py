from pathlib import Path
import bpy,json

root=Path(__file__).resolve().parents[1]/'review/lulu-under-eye-20261018/r06'
out=root/'lulu-under-eye-study.blend'
if out.exists():raise RuntimeError('Do not overwrite a saved study')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root/'lulu-under-eye.glb'))
bpy.context.scene['status']='REJECTED STUDY: under-eye improvement insufficient; new inner-corner bump/line. Do not promote.'
bpy.context.scene['source']='Independent modular right-junction-r04 copy; only one under-eye skin patch replaced.'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out))
(root/'native-readback.json').write_text(json.dumps({'opened':True,'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons)} for o in bpy.data.objects if o.type=='MESH'],'art_status':'rejected'},indent=2))
