"""Imported native inspection/edit copy of the new coloured Sketchfab asset."""
from pathlib import Path
import bpy, json, math, sys, argparse
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='color-r06');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
D=R/'review/lulu-sketchfab-color-20261019'/args.revision
out=D/'lulu-sketchfab-colour.blend'
if out.exists():raise RuntimeError('Source exists; preserve candidate history')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(D/'lulu-sketchfab-colour.glb'))
roots=[o for o in bpy.context.scene.objects if o.parent is None]
upright=bpy.data.objects.new('Upright_Display_Root',None)
bpy.context.collection.objects.link(upright)
for obj in roots:obj.parent=upright
upright.rotation_euler.x=math.pi/2
upright['note']='Presentation-only upright rotation. Imported source mesh geometry unchanged.'
for name in ['front','side','back']:
    image=bpy.data.images.load(str(R/f'public/reference/{name}.png'),check_existing=True)
    image.name=f'Original_Lulu_Reference_{name}'
    image.use_fake_user=True
for obj in bpy.data.objects:
    if obj.type=='MESH':
        obj['status']='Imported unchanged sculpt; colour/UV material candidate, not rigged.'
bpy.context.scene['provenance']='Spencer0131, Sketchfab a5747f74f0034470a2029a85f6e9c11d, CC BY 4.0; independent colour study. Native file is an imported inspection/edit copy, not a newly authored sculpt.'
bpy.context.scene['scope']='Reference colours and face UV only. Raised left arm/head/body/shoulder remain source geometry.'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.wm.open_mainfile(filepath=str(out))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
report={'source_reopened':True,'mesh_objects':len(meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'packed_images':len([i for i in bpy.data.images if i.packed_file]),'armatures':len([o for o in bpy.data.objects if o.type=='ARMATURE']),'has_face_uv':any(len(o.data.uv_layers)>0 for o in meshes),'has_vertex_colours':any(len(o.data.color_attributes)>0 for o in meshes),'native_source_type':'Imported GLB with editable vertex colours and face UV image; display root upright only.'}
(D/'native-readback.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
