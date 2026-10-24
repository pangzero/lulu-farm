"""Reopen the native rig and glTF roundtrip; test the known body/head risks."""
from pathlib import Path
import sys,json,numpy as np,bpy,hashlib
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1];rep=R/'review/lulu-wardrobe-rig-20261018/full-r02';native=R/'assets-source/wardrobe-rig/full-r02/lulu-rig.blend';bpy.ops.wm.open_mainfile(filepath=str(native));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');objects={o.name:o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)}
def reset():
 for p in arm.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion()
 bpy.context.view_layer.update()
def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());p=np.empty(len(ev.data.vertices)*3);ev.data.vertices.foreach_get('co',p);p=p.reshape(-1,3);M=np.array(ev.matrix_world);return np.einsum('ij,kj->ik',p,M[:3,:3])+M[:3,3]
def turn(name,axis,deg):
 ax=Vector((axis[0],-axis[2],axis[1]));local=arm.data.bones[name].matrix_local.to_quaternion().inverted()@ax;arm.pose.bones[name].rotation_quaternion=Quaternion(local,np.deg2rad(deg));bpy.context.view_layer.update()
reset();rest={n:points(o) for n,o in objects.items()};turn('RightArm',[0,0,1],-15);delta={n:float(np.max(np.abs(points(o)-rest[n]))) for n,o in objects.items()};assert max(delta[n] for n in ['Head','Orange','Body','Shorts','Leg_R','Leg_L','Arm_L'])<1e-5;assert delta['Arm_R']>.03
reset();turn('Head',[0,1,0],10);D=np.array(arm.pose.bones['Head'].matrix@arm.data.bones['Head'].matrix_local.inverted());head_error={}
for n in ['Head','Orange']:
 expected=np.einsum('ij,kj->ik',rest[n],D[:3,:3])+D[:3,3];head_error[n]=float(np.max(np.abs(points(objects[n])-expected)));assert head_error[n]<1e-5
legs={}
for side,parts in [('Left',['Leg_L']),('Right',['Leg_R'])]:
 reset();turn(side+'UpLeg',[1,0,0],-8);turn(side+'Leg',[1,0,0],12);turn(side+'Foot',[1,0,0],-4);legs[side]={n:float(np.max(np.abs(points(objects[n])-rest[n]))) for n in ['Body','Head','Shorts',*parts]};assert legs[side]['Body']<1e-5 and legs[side]['Head']<1e-5 and legs[side]['Shorts']>.001
reset();images=[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file or i.packed_files)} for i in bpy.data.images if i.source=='FILE'];uv=[u.name for u in objects['Shorts'].data.uv_layers];assert 'FabricUV' in uv and len(images)==7 and all(i['packed'] for i in images);actions=[a.name for a in bpy.data.actions];bone_count=len(arm.data.bones)
# Reimport the exported skin, evaluate true bind matrices in Blender.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'public/models/wardrobe-rig/full-r02/lulu-rig.glb'),merge_vertices=False);rt=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)];roundtrip={}
for obj in bpy.context.scene.objects:
 if obj.animation_data:obj.animation_data_clear()
 if obj.type=='ARMATURE':
  for pb in obj.pose.bones:pb.location=(0,0,0);pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion();pb.scale=(1,1,1)
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
for o in rt:
 raw=np.empty(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',raw);p=raw.reshape(-1,3);M=np.array(o.matrix_world);p=np.einsum('ij,kj->ik',p,M[:3,:3])+M[:3,3];q=points(o);roundtrip[o.name]=float(np.abs(q-p).max());print('roundtrip rest',o.name,roundtrip[o.name],flush=True);assert roundtrip[o.name]<1e-5
result={'native_meshes':len(objects),'bones':bone_count,'arm15_max_coordinate_changes':delta,'head_rigid_transform_error':head_error,'leg_tests':legs,'shorts_uv_layers':uv,'packed_images':images,'native_actions':actions,'gltf_roundtrip_rest_errors':roundtrip,'visual_review_separate':True}
(rep/'native-readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
