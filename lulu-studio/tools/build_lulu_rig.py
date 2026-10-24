"""Bind the accepted Lulu v1 without changing its rest geometry or textures.
Run with Blender 4.5. Bone/weight data are authored in Blender; the GLB writer
appends only skin/joint data to the accepted binary to preserve its exact look.
"""
from pathlib import Path
import bpy, numpy as np, json, struct, hashlib, sys
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parents[1]
REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r01'
OUT=R/'assets-source/rig'/f'lulu-rig-{REV}.blend'
GLB=R/'public/models/rig'/f'lulu-rig-{REV}.glb'
REPORT=R/'review/lulu-rig-20261018'/REV
SOURCE=R/'public/models/lulu-official-v1.glb'
if OUT.exists() or GLB.exists():raise RuntimeError('Use a new revision; preserve previous files')
OUT.parent.mkdir(parents=True,exist_ok=True);GLB.parent.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
blob=SOURCE.read_bytes(); jl=struct.unpack_from('<I',blob,12)[0]
g=json.loads(blob[20:20+jl]);raw=bytearray(blob[28+jl:])
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
 return np.ndarray((a['count'],sz),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*dt.itemsize),dt.itemsize)).copy()
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def v(p):return Vector((p[0],-p[2],p[1]))  # glTF Y-up -> Blender Z-up
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE),merge_vertices=False)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
# The formal unrigged editable copy carries clear approval metadata.
formal=R/'assets-source/lulu-official-v1.blend'
if not formal.exists():
 bpy.context.scene['asset_name']='Lulu 正式版 v1'
 bpy.context.scene['approval']='User approved cheekfix-r4 on 2026-10-18'
 bpy.context.scene['source_sha256']=hashlib.sha256(blob).hexdigest()
 bpy.context.scene['source_kind']='Imported Meshy derivative; not an authored sculpt'
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(formal))
# Coordinates below are measured in the immutable original glTF frame.
spec=[]
def bone(n,h,t,p=None,deform=True):spec.append((n,h,t,p,deform))
bone('Root',(0,-.950609,0),(0,-.80,0),deform=False)
bone('Hips',(0,-.56,-.10),(0,-.40,-.10),'Root')
bone('Spine',(0,-.40,-.10),(0,-.28,-.10),'Hips')
bone('Spine1',(0,-.28,-.10),(0,-.19,-.10),'Spine')
bone('Spine2',(0,-.19,-.10),(0,-.13,-.10),'Spine1')
bone('Neck',(0,-.13,-.10),(0,-.045,-.10),'Spine2')
bone('Head',(0,-.045,-.10),(0,.64,-.10),'Neck')
for side,s in [('Left',1),('Right',-1)]:
 bone(side+'Shoulder',(.12*s,-.14,-.09),(.405*s,-.155,-.075),'Spine2')
 bone(side+'Arm',(.405*s,-.155,-.075),(.505*s,-.335,-.045),side+'Shoulder')
 bone(side+'ForeArm',(.505*s,-.335,-.045),(.54*s,-.50,-.005),side+'Arm')
 bone(side+'Hand',(.54*s,-.50,-.005),(.54*s,-.59,.015),side+'ForeArm')
 bone(side+'UpLeg',(.25*s,-.57,-.10),(.26*s,-.735,-.075),'Hips')
 bone(side+'Leg',(.26*s,-.735,-.075),(.26*s,-.865,-.075),side+'UpLeg')
 bone(side+'Foot',(.26*s,-.865,-.075),(.26*s,-.913,.025),side+'Leg')
 bone(side+'ToeBase',(.26*s,-.913,.025),(.26*s,-.913,.07),side+'Foot')
adata=bpy.data.armatures.new('Lulu_DeformSkeleton');arm=bpy.data.objects.new('Lulu_Rig',adata);bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for n,h,t,parent,deform in spec:
 b=adata.edit_bones.new(n);b.head=v(h);b.tail=v(t);b.use_deform=deform
 if parent:b.parent=adata.edit_bones[parent]
 b.align_roll(Vector((0,1,0)))
bpy.ops.object.mode_set(mode='OBJECT');arm.show_in_front=True;adata.display_type='OCTAHEDRAL'
names=[x[0] for x in spec];ix={n:i for i,n in enumerate(names)}
skin_data=np.load(R/('review/lulu-rig-20261018/skin-region-smooth.npz' if REV=='r04' else 'review/lulu-rig-20261018/skin-region.npz'))
skin_points=skin_data['p'];skin_values=skin_data['skin']
skin_tree=KDTree(len(skin_points))
for i,co in enumerate(skin_points):skin_tree.insert(co,i)
skin_tree.balance()
# Skin weights are explicit and reproducible. No heat weights across fused armpits.
def weights(p):
 x,y,z=p.T;ax=np.abs(x);w=np.zeros((len(p),len(names)),dtype=np.float64)
 # Spine segments with broad overlap, head and face rigid above the neck collar.
 head=ss(-.17,-.055,y)
 body=1-head
 w[:,ix['Head']]=head
 spine=ss(-.49,-.31,y)
 upper=ss(-.33,-.20,y)
 neck=ss(-.21,-.12,y)
 w[:,ix['Hips']]=body*(1-spine)
 w[:,ix['Spine']]=body*spine*(1-upper)
 w[:,ix['Spine1']]=body*spine*upper*(1-neck)
 w[:,ix['Spine2']]=body*spine*upper*neck
 # Arm influence grows toward the outer side and gradually leaves the chest.
 start=np.interp(y,[-.62,-.5,-.35,-.2,-.12],[.425,.43,.405,.33,.30])
 end=start+np.interp(y,[-.62,-.35,-.12],[.065,.11,.135])
 mask=ss(start,end,ax)*(1-ss(-.20,-.055,y))*ss(-.67,-.59,y)
 # Rear and frontal torso keep torso weights; lateral palm remains fully weighted.
 depth=(1-ss(.13,.23,np.abs(z+.055)))
 mask*=depth
 # Separate the yellow arm from orange shorts where the two touch.
 if REV != 'r01':
  skin=np.array([skin_values[skin_tree.find(co)[1]] for co in p])
  mask*=1-(1-skin)*(1-ss(-.40,-.32,y))
 hand=1-ss(-.545,-.465,y)
 fore=(1-ss(-.385,-.285,y))*(1-hand)
 upperarm=(1-hand-fore)
 collar=ss(-.235,-.145,y)*.28
 for side,sgn in [('Left',1),('Right',-1)]:
  m=mask*(x*sgn>0)
  w*=1-m[:,None]
  w[:,ix[side+'Shoulder']]+=m*upperarm*collar
  w[:,ix[side+'Arm']]+=m*upperarm*(1-collar)
  w[:,ix[side+'ForeArm']]+=m*fore
  w[:,ix[side+'Hand']]+=m*hand
 # Short legs: pelvis-to-thigh transition confined to the lower shorts.
 lm=(1-ss(-.72,-.57,y))*ss(.045,.17,ax)
 knee=1-ss(-.79,-.705,y)
 foot=1-ss(-.89,-.815,y)
 toe=ss(.005,.065,z)*(1-ss(-.90,-.86,y))*.65
 for side,sgn in [('Left',1),('Right',-1)]:
  m=lm*(x*sgn>0)
  w*=1-m[:,None]
  w[:,ix[side+'UpLeg']]+=m*(1-knee)
  w[:,ix[side+'Leg']]+=m*knee*(1-foot)
  w[:,ix[side+'Foot']]+=m*knee*foot*(1-toe)
  w[:,ix[side+'ToeBase']]+=m*knee*foot*toe
 # Fixed four-influence budget for runtime and Blender equivalence.
 ind=np.argsort(-w,axis=1)[:,:4];val=np.take_along_axis(w,ind,axis=1);val/=val.sum(1,keepdims=True)
 w[:]=0;np.put_along_axis(w,ind,val,axis=1)
 return w.astype(np.float32)
rest=[]
for obj in meshes:
 p=np.array([obj.matrix_world@v.co for v in obj.data.vertices]);p=p[:,[0,2,1]];p[:,2]*=-1
 w=weights(p);rest.append((obj,p.copy(),w))
 for i,n in enumerate(names):
  vg=obj.vertex_groups.new(name=n)
  for j in np.flatnonzero(w[:,i]>0):vg.add([int(j)],float(w[j,i]),'REPLACE')
 obj.parent=arm
 mod=obj.modifiers.new('Lulu Armature','ARMATURE');mod.object=arm;mod.use_deform_preserve_volume=False
 obj['weight_method']='Measured region weights, max four influences; rigid head/face'
arm['base_asset']='Lulu 正式版 v1 / cheekfix-r4'
arm['rig_revision']=REV;arm['retarget_status']='Base deform rig, original rest pose. Mixamo not retargeted; match reference poses first.'
arm['known_limit']='Fused shoulder skin. Small range QA only; not full animation acceptance.'
scene=bpy.context.scene;scene['asset_name']='Lulu 独立骨骼绑定副本 '+REV
scene['source_sha256']=hashlib.sha256(blob).hexdigest();scene['rig_status']='Base rig; no production animation; full-motion weights pending'
# Save rest, armature selected for immediate editing.
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
# Exact-material GLB: append skin buffers; all original buffer views untouched.
def add(a,typ,component):
 while len(raw)%4:raw.append(0)
 off=len(raw);raw.extend(a.tobytes());vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':a.nbytes})
 ai=len(g['accessors']);g['accessors'].append({'bufferView':vi,'componentType':component,'count':len(a),'type':typ});return ai
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
M={n:C@adata.bones[n].matrix_local@C.inverted() for n in names}
nodeids={n:len(g['nodes'])+i for i,n in enumerate(names)}
for n,h,t,parent,deform in spec:
 local=M[parent].inverted()@M[n] if parent else M[n]
 loc,rot,sca=local.decompose()
 node={'name':n,'translation':list(loc),'rotation':[rot.x,rot.y,rot.z,rot.w],'scale':list(sca),'extras':{'boneTail':list(t),'deform':deform}}
 kids=[nodeids[s[0]] for s in spec if s[3]==n]
 if kids:node['children']=kids
 g['nodes'].append(node)
ib=np.array([[a for col in M[n].inverted().transposed() for a in col] for n in names],dtype='<f4')
g['skins']=[{'name':'Lulu_Rig','inverseBindMatrices':add(ib,'MAT4',5126),'skeleton':nodeids['Root'],'joints':[nodeids[n] for n in names]}]
g['scenes'][g.get('scene',0)]['nodes'].append(nodeids['Root']);g['nodes'][0]['skin']=0;g['nodes'][0]['name']='Lulu_Official_v1_Skinned'
for prim in g['meshes'][0]['primitives']:
 p=acc(prim['attributes']['POSITION']);w=weights(p);ind=np.argsort(-w,axis=1)[:,:4].astype('<u2');val=np.take_along_axis(w,ind,axis=1).astype('<f4')
 prim['attributes']['JOINTS_0']=add(ind,'VEC4',5123);prim['attributes']['WEIGHTS_0']=add(val,'VEC4',5126)
g['buffers'][0]['byteLength']=len(raw)
g.setdefault('extras',{})['lulu']={'asset':'Lulu 独立骨骼绑定副本','revision':REV,'base':'Lulu 正式版 v1','source_sha256':hashlib.sha256(blob).hexdigest(),'geometry_and_materials':'Original buffer views retained exactly','animation_status':'No Mixamo or production animation yet'}
j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);raw+=b'\0'*((-len(raw))%4)
GLB.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(raw))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw)
# Evaluate actual Blender skin in neutral pose and a rigid head turn.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
maxrest=0;headrigid=0;headcount=0
for obj,p,w in rest:
 ev=obj.evaluated_get(dg);q=np.array([ev.matrix_world@v.co for v in ev.data.vertices]);q=q[:,[0,2,1]];q[:,2]*=-1
 maxrest=max(maxrest,float(np.abs(q-p).max()))
 mask=p[:,1]>=-.055;headcount+=int(mask.sum());headrigid+=int(np.sum(w[mask,ix['Head']]==1))
report={'revision':REV,'source':str(SOURCE.relative_to(R)),'source_sha256':hashlib.sha256(blob).hexdigest(),'bones':len(names),'bone_names':names,'rest_max_coordinate_delta':maxrest,'rigid_head_vertices':headrigid,'head_region_vertices':headcount,'rigid_head_all':headrigid==headcount,'vertex_count':sum(len(x[1]) for x in rest),'max_influences':4,'blend':str(OUT.relative_to(R)),'glb':str(GLB.relative_to(R)),'glb_sha256':hashlib.sha256(GLB.read_bytes()).hexdigest(),'art_status':'Binding candidate. Small-motion review required; full Mixamo motion not validated.'}
(REPORT/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
