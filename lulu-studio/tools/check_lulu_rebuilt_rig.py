"""Read back Blender rig + GLB. No asset mutation."""
import bpy,json,sys,struct,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1];rev=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r02';folder=R/'review/lulu-rig-separation-20261018'/rev
bpy.ops.wm.open_mainfile(filepath=str(R/f'assets-source/rig/lulu-rig-{rev}.blend'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
def coords(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());return np.array([ev.matrix_world@v.co for v in ev.data.vertices])
for b in arm.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion.identity()
bpy.context.view_layer.update();base=[coords(o) for o in meshes]
report={'revision':rev,'blender_reopened':True,'armatures':1,'bones':len(arm.data.bones),'vertices':sum(len(o.data.vertices) for o in meshes),'packed_images':sum(bool(i.packed_file) for i in bpy.data.images if i.source=='FILE'),'no_unweighted_vertices':all(len(v.groups)>0 for o in meshes for v in o.data.vertices),'weight_sum_max_error':max(abs(sum(g.weight for g in v.groups)-1) for o in meshes for v in o.data.vertices),'max_influences':max(len(v.groups) for o in meshes for v in o.data.vertices),'poses':{}}
for mode in ['head','arms','legs']:
 for b in arm.pose.bones:b.rotation_quaternion.identity()
 bpy.context.view_layer.update()
 bn=['Head'] if mode=='head' else ['LeftArm','RightArm'] if mode=='arms' else ['LeftUpLeg','LeftLeg']
 angles=[12] if mode=='head' else [-20,-20] if mode=='arms' else [-12,20]
 world_axis=Vector((0,0,1)) if mode=='head' else Vector((1,0,0))
 for name,deg in zip(bn,angles):
  b=arm.pose.bones[name];axis=b.bone.matrix_local.to_quaternion().inverted()@world_axis;b.rotation_quaternion=Quaternion(axis,np.radians(deg))
 bpy.context.view_layer.update();errs=[];deltas=[]
 for obj,p in zip(meshes,base):
  q=coords(obj);mask=p[:,2]>=-.055
  if mode=='head':
   M=arm.pose.bones['Head'].matrix@arm.data.bones['Head'].matrix_local.inverted();expected=np.array([M@Vector(co) for co in p[mask]]);errs.append(float(np.abs(q[mask]-expected).max()))
  else:errs.append(float(np.abs(q[mask]-p[mask]).max()))
  deltas.append(float(np.linalg.norm(q-p,axis=1).max()))
 report['poses'][mode]={'max_movement':max(deltas),'head_rigid_error' if mode=='head' else 'head_unchanged_error':max(errs)}
def read(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
g0,b0=read(R/'public/models/lulu-official-v1.glb');g,b=read(R/f'public/models/rig/lulu-rig-{rev}.glb')
report['original_binary_prefix_identical']=b[:len(b0)]==b0
report['materials_identical']=g['materials']==g0['materials'];report['images_identical']=g['images']==g0['images'];report['skin_count']=len(g['skins']);report['animations']=len(g.get('animations',[]))
report['original_attributes_identical']=all(all(p['attributes'][k]==v for k,v in s['attributes'].items()) and p['indices']==s['indices'] for p,s in zip(g['meshes'][0]['primitives'],g0['meshes'][0]['primitives']))
report['formal_equals_approved_r4']=(R/'public/models/lulu-official-v1.glb').read_bytes()==(R/'public/models/lulu-meshy-cheekfix.glb').read_bytes()
# Reimport final preview GLB into Blender to catch inverse-bind/axis/export errors.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/f'public/models/rig/lulu-rig-{rev}.glb'))
a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mm=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)];bpy.context.view_layer.update()
err=0
for obj in mm:
 p=np.array([obj.matrix_world@v.co for v in obj.data.vertices]);q=coords(obj);err=max(err,float(abs(q-p).max()))
report['glb_reimport']={'armatures':sum(o.type=='ARMATURE' for o in bpy.context.scene.objects),'bones':len(a.data.bones),'rest_max_coordinate_delta':err,'skinned_meshes':sum(any(m.type=='ARMATURE' for m in o.modifiers) for o in mm)}
print(json.dumps(report,indent=2),flush=True)
assert report['original_binary_prefix_identical'] and report['formal_equals_approved_r4']
assert report['no_unweighted_vertices'] and report['max_influences']<=4 and report['weight_sum_max_error']<1e-5
assert max(report['poses'][m].get('head_rigid_error',report['poses'][m].get('head_unchanged_error',1)) for m in report['poses'])<1e-5
assert err<1e-5
(folder/'blender-readback.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
