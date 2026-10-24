"""Independent multi-part rig. Append skin data; keep source geometry/images exact."""
from pathlib import Path
import sys,json,struct,hashlib,copy,numpy as np,bpy
from mathutils import Vector,Matrix,Quaternion
R=Path(__file__).resolve().parents[1];rev=sys.argv[sys.argv.index('--')+1];full=rev.startswith('full-');root=R/'review/lulu-wardrobe-rig-20261018';report=root/rev
out=R/'public/models/wardrobe-rig'/rev;native=R/'assets-source/wardrobe-rig'/rev/'lulu-rig.blend';source=R/'public/models/modular'/('arm-trim-volume-r01' if rev=='arm-r03' or full else 'arm-inner-volume-r01' if rev=='arm-r02' else 'right-junction-r04')/'lulu-assembled.glb'
if full:assert json.loads((root/'arm-gate.json').read_text())['status']=='PASS_LIMITED'
assert not native.exists() and not (out/'lulu-rig.glb').exists();out.mkdir(parents=True,exist_ok=True);native.parent.mkdir(parents=True,exist_ok=True);report.mkdir(parents=True,exist_ok=True)
blob=source.read_bytes();jl=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+jl]);raw=bytearray(blob[28+jl:]);original_len=len(raw)
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);return np.ndarray((a['count'],sz),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*dt.itemsize),dt.itemsize)).copy()
def ss(a,b,x):q=np.clip((x-a)/(b-a),0,1);return q*q*(3-2*q)
def V(p):return Vector((p[0],-p[2],p[1]))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source),merge_vertices=False);objects={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'};spec=[]
def bone(n,h,t,p=None,deform=True):spec.append((n,h,t,p,deform))
bone('Root',(0,-.950609,0),(0,-.80,0),deform=False);bone('Hips',(0,-.56,-.10),(0,-.40,-.10),'Root');bone('Spine',(0,-.40,-.10),(0,-.28,-.10),'Hips');bone('Spine1',(0,-.28,-.10),(0,-.19,-.10),'Spine');bone('Spine2',(0,-.19,-.10),(0,-.13,-.10),'Spine1');bone('Neck',(0,-.13,-.10),(0,-.045,-.10),'Spine2');bone('Head',(0,-.045,-.10),(0,.64,-.10),'Neck')
for side,s in [('Left',1),('Right',-1)]:
 bone(side+'Shoulder',(.13*s,-.14,-.10),(.435*s,-.17,-.09),'Spine2');bone(side+'Arm',(.435*s,-.17,-.09),(.515*s,-.345,-.055),side+'Shoulder');bone(side+'ForeArm',(.515*s,-.345,-.055),(.55*s,-.51,-.015),side+'Arm');bone(side+'Hand',(.55*s,-.51,-.015),(.55*s,-.59,.015),side+'ForeArm');bone(side+'UpLeg',(.25*s,-.57,-.10),(.26*s,-.735,-.075),'Hips');bone(side+'Leg',(.26*s,-.735,-.075),(.26*s,-.865,-.075),side+'UpLeg');bone(side+'Foot',(.26*s,-.865,-.075),(.26*s,-.913,.025),side+'Leg');bone(side+'ToeBase',(.26*s,-.913,.025),(.26*s,-.913,.07),side+'Foot')
adata=bpy.data.armatures.new('Lulu_Modular_DeformSkeleton');arm=bpy.data.objects.new('Lulu_Modular_Rig',adata);bpy.context.collection.objects.link(arm);bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for n,h,t,parent,deform in spec:
 b=adata.edit_bones.new(n);b.head=V(h);b.tail=V(t);b.use_deform=deform
 if parent:b.parent=adata.edit_bones[parent]
 b.align_roll(Vector((0,1,0)))
bpy.ops.object.mode_set(mode='OBJECT');arm.show_in_front=True;adata.display_type='OCTAHEDRAL';names=[s[0] for s in spec];ix={n:i for i,n in enumerate(names)}
def weights(name,p):
 x,y,z=p.T;w=np.zeros((len(p),len(names)),dtype=np.float32)
 if name in ['Head','Orange']:w[:,ix['Head']]=1
 elif name=='Body':
  a=ss(-.49,-.32,y);b=ss(-.34,-.23,y);c=ss(-.24,-.15,y);w[:,ix['Hips']]=1-a;w[:,ix['Spine']]=a*(1-b);w[:,ix['Spine1']]=a*b*(1-c);w[:,ix['Spine2']]=a*b*c
 elif name.startswith('Arm_'):
  side='Right' if name=='Arm_R' else 'Left'
  if not full and side=='Left':w[:,ix['Spine2']]=1
  else:
   root=ss(-.245,-.15,y);hand=1-ss(-.55,-.49,y);fore=(1-ss(-.39,-.30,y))*(1-hand);upper=1-hand-fore
   w[:,ix[side+'Shoulder']]=root;w[:,ix[side+'Arm']]=(1-root)*upper;w[:,ix[side+'ForeArm']]=(1-root)*fore;w[:,ix[side+'Hand']]=(1-root)*hand
 elif not full:w[:,ix['Hips']]=1
 elif name=='Shorts':
  leg=(1-ss(-.74,-.55,y))*ss(.035,.13,np.abs(x));left=ss(-.09,.09,x);knee=(1-ss(-.82,-.735,y))*.35;w[:,ix['Hips']]=1-leg
  for side,s in [('Left',left),('Right',1-left)]:w[:,ix[side+'UpLeg']]=leg*s*(1-knee);w[:,ix[side+'Leg']]=leg*s*knee
 elif name.startswith('Leg_'):
  side='Right' if name=='Leg_R' else 'Left';hip=ss(-.73,-.61,y);knee=1-ss(-.79,-.71,y);foot=1-ss(-.87,-.82,y);w[:,ix['Hips']]=hip;w[:,ix[side+'UpLeg']]=(1-hip)*(1-knee);w[:,ix[side+'Leg']]=(1-hip)*knee*(1-foot);w[:,ix[side+'Foot']]=(1-hip)*knee*foot
 else:raise ValueError(name)
 ind=np.argsort(-w,axis=1)[:,:4];val=np.take_along_axis(w,ind,axis=1);assert np.all(val.sum(1)>.99);val/=val.sum(1,keepdims=True);w[:]=0;np.put_along_axis(w,ind,val,axis=1);return w
rest=[];checks=[]
for name,o in objects.items():
 p=np.array([o.matrix_world@v.co for v in o.data.vertices]);p=p[:,[0,2,1]];p[:,2]*=-1;w=weights(name,p);rest.append((o,p,w))
 for j,n in enumerate(names):
  ids=np.flatnonzero(w[:,j]>0)
  if not len(ids):continue
  vg=o.vertex_groups.new(name=n)
  for k in ids:vg.add([int(k)],float(w[k,j]),'REPLACE')
 o.parent=arm;mod=o.modifiers.new('Lulu explicit part weights','ARMATURE');mod.object=arm;mod.use_deform_preserve_volume=False;o['base_revision']='right-junction-r04';o['weight_method']='explicit part isolation; original geometry fixed'
 checks.append({'part':name,'vertices':len(p),'arm_bone_influence_max':float(w[:,[ix[n] for n in names if n.endswith(('Arm','ForeArm','Hand','Shoulder'))]].sum(1).max()),'all_head_rigid':bool(np.all(w[:,ix['Head']]==1)) if name in ['Head','Orange'] else None})
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();rest_delta=0
for o,p,w in rest:
 ev=o.evaluated_get(dg);q=np.array([ev.matrix_world@v.co for v in ev.data.vertices]);q=q[:,[0,2,1]];q[:,2]*=-1;rest_delta=max(rest_delta,float(np.abs(q-p).max()))
assert rest_delta<1e-5
# Save genuine native diagnostic clips. They are small-motion tests, not walks.
tests={'RightArm_Abduct15':{'RightArm':([0,0,1],-15)},'RightArm_Swing10':{'RightArm':([1,0,0],-10),'RightForeArm':([1,0,0],-2)}}
if full:tests.update({'LeftLeg_Lift8':{'LeftUpLeg':([1,0,0],-8),'LeftLeg':([1,0,0],12),'LeftFoot':([1,0,0],-4)},'RightLeg_Lift8':{'RightUpLeg':([1,0,0],-8),'RightLeg':([1,0,0],12),'RightFoot':([1,0,0],-4)},'Head_Turn10':{'Head':([0,1,0],10)}})
arm.animation_data_create();native_clips=[]
for label,turns in tests.items():
 action=bpy.data.actions.new(label);action.use_fake_user=True;arm.animation_data.action=action
 for f,mult in [(1,0),(25,1),(49,0)]:
  for n,(axis,degrees) in turns.items():
   pb=arm.pose.bones[n];a=adata.bones[n].matrix_local.to_quaternion().inverted()@V(axis);pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(a,np.deg2rad(degrees*mult));pb.keyframe_insert(data_path='rotation_quaternion',frame=f,group=n)
 native_clips.append(label)
arm.animation_data.action=None
for pb in arm.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion()
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();arm['phase']='full limited rig' if full else 'single right arm gate';arm['source_sha256']=hashlib.sha256(blob).hexdigest();bpy.context.scene['rig_status']='Limited diagnostic rig; no Mixamo; appearance and range acceptance pending'
wardrobe_path=R/'public/models/wardrobe-rig/wardrobe.json'
if wardrobe_path.exists():
 shorts=objects['Shorts'];uv=shorts.data.uv_layers.new(name='FabricUV');sourcep=np.array([[v.co.x,v.co.z,-v.co.y] for v in shorts.data.vertices]);sourceu=np.arctan2(sourcep[:,0],sourcep[:,2]+.08)/(2*np.pi)+.5;bins=128;top=np.array([sourcep[(sourceu>=i/bins)&(sourceu<(i+1)/bins),1].max() if np.any((sourceu>=i/bins)&(sourceu<(i+1)/bins)) else -.46 for i in range(bins)]);top=(np.roll(top,1)+top+np.roll(top,-1))/3
 def fabric_uv(p):
  u=np.arctan2(p[:,0],p[:,2]+.08)/(2*np.pi)+.5;waist=np.interp(u,(np.arange(bins)+.5)/bins,top,period=1);v=np.clip((waist-p[:,1])/(waist+.84),0,1);return np.c_[u,v]
 for poly in shorts.data.polygons:
  inds=list(poly.vertices);uvs=fabric_uv(sourcep[inds])
  if np.ptp(uvs[:,0])>.5:uvs[uvs[:,0]<.5,0]+=1
  for li,q in zip(poly.loop_indices,uvs):uv.data[li].uv=(float(q[0]),float(1-q[1]))
 shorts.data.uv_layers[0].active_render=True
 for preset in json.loads(wardrobe_path.read_text())['presets']:
  if preset['id']=='original':continue
  material=bpy.data.materials.new('Shorts_'+preset['id']);material.use_nodes=True;material.use_fake_user=True;bsdf=material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=preset['roughness'];tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'public'/preset['baseColor'].lstrip('/')));uvnode=material.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='FabricUV';material.node_tree.links.new(uvnode.outputs['UV'],tex.inputs['Vector']);material.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);material['wardrobe_slot']='Shorts';material['same_template_geometry']=True
 bpy.context.scene['wardrobe_presets']='original, blue-stars, watermelon; same Shorts mesh/UV/weights; alternate materials saved with fake users'
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
# Append-only glTF skin writer. Original buffer views, attributes and images stay.
def add(a,typ,component):
 raw.extend(b'\0'*((-len(raw))%4));off=len(raw);raw.extend(a.tobytes());vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':a.nbytes});ai=len(g['accessors']);q={'bufferView':vi,'componentType':component,'count':len(a),'type':typ}
 if typ in ['SCALAR','VEC3']:q.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 g['accessors'].append(q);return ai
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));M={n:C@adata.bones[n].matrix_local@C.inverted() for n in names};nodeids={n:len(g['nodes'])+i for i,n in enumerate(names)};localqs={}
for n,h,t,parent,deform in spec:
 local=M[parent].inverted()@M[n] if parent else M[n];loc,rot,sca=local.decompose();localqs[n]=rot;node={'name':n,'translation':list(loc),'rotation':[rot.x,rot.y,rot.z,rot.w],'scale':list(sca),'extras':{'boneTail':list(t),'deform':deform}};kids=[nodeids[s[0]] for s in spec if s[3]==n]
 if kids:node['children']=kids
 g['nodes'].append(node)
ib=np.array([[a for col in M[n].inverted().transposed() for a in col] for n in names],dtype='<f4');g['skins']=[{'name':'Lulu_Modular_Rig','inverseBindMatrices':add(ib,'MAT4',5126),'skeleton':nodeids['Root'],'joints':[nodeids[n] for n in names]}];g['scenes'][g.get('scene',0)]['nodes'].append(nodeids['Root'])
for ni,node in enumerate(g['nodes']):
 if 'mesh' not in node:continue
 mesh=g['meshes'][node['mesh']];name=mesh['name'];node['skin']=0
 for prim in mesh['primitives']:
  p=acc(prim['attributes']['POSITION']);w=weights(name,p);idx=np.argsort(-w,axis=1)[:,:4].astype('<u2');val=np.take_along_axis(w,idx,axis=1).astype('<f4');prim['attributes']['JOINTS_0']=add(idx,'VEC4',5123);prim['attributes']['WEIGHTS_0']=add(val,'VEC4',5126)
  if name=='Shorts' and full:
   oldattrs=prim['attributes'].copy();f=acc(prim['indices']).reshape(-1,3);uvs=fabric_uv(p)[f];cross=np.ptp(uvs[:,:,0],axis=1)>.5;uvs[:,:,0]+=cross[:,None]&(uvs[:,:,0]<.5);columns=[];fields=[];offset=0
   for key,ai in oldattrs.items():
    a=acc(ai);columns.append(a[f].reshape(-1,a.shape[1]));fields.append((key,offset,a.shape[1],g['accessors'][ai]['type'],g['accessors'][ai]['componentType']));offset+=a.shape[1]
   columns.append(uvs.reshape(-1,2));fields.append(('TEXCOORD_1',offset,2,'VEC2',5126));data=np.concatenate(columns,axis=1).astype('<f4');unique,inverse=np.unique(data,axis=0,return_inverse=True);attrs={}
   for key,start,width,typ,ct in fields:attrs[key]=add(unique[:,start:start+width].astype('<u2' if ct==5123 else '<f4'),typ,ct)
   prim['attributes']=attrs;prim['indices']=add(inverse.astype('<u4').reshape(-1,1),'SCALAR',5125)
clips=[]
for label,turns in tests.items():
 times=add(np.array([[0],[1],[2]],dtype='<f4'),'SCALAR',5126);samplers=[];channels=[]
 for n,(axis,degrees) in turns.items():
  qs=[]
  for mult in [0,1,0]:
   # Premultiply a parent-space world-axis rotation onto the rest local joint.
   parent=next(s[3] for s in spec if s[0]==n);pa=M[parent].to_quaternion() if parent else Quaternion();axisparent=pa.inverted()@Vector(axis);q=Quaternion(axisparent,np.deg2rad(degrees*mult))@localqs[n];qs.append([q.x,q.y,q.z,q.w])
  oi=add(np.array(qs,dtype='<f4'),'VEC4',5126);samplers.append({'input':times,'output':oi,'interpolation':'LINEAR'});channels.append({'sampler':len(samplers)-1,'target':{'node':nodeids[n],'path':'rotation'}})
 clips.append({'name':label,'samplers':samplers,'channels':channels})
g['animations']=clips;g['buffers'][0]['byteLength']=len(raw);g.setdefault('extras',{})['lulu']['modular_rig']={'revision':rev,'phase':'full' if full else 'right-arm-only','base':'right-junction-r04','original_buffer_bytes_preserved':original_len,'clothing_slot':'Shorts','wardrobe':'same mesh/UV/skin; material presets'}
def save(path,doc):
 j=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);rr=raw+b'\0'*((-len(raw))%4);path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(rr))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(rr),0x004e4942)+rr)
save(out/'lulu-rig.glb',g)
base=copy.deepcopy(g);shorts_nodes={i for i,n in enumerate(base['nodes']) if 'mesh' in n and base['meshes'][n['mesh']]['name']=='Shorts'};base['scenes'][base.get('scene',0)]['nodes']=[i for i in base['scenes'][base.get('scene',0)]['nodes'] if i not in shorts_nodes];base['extras']['lulu']['modular_rig']['wardrobe']='Shorts slot omitted from active scene; covered lower-body inspection base, not an approved nude body';save(out/'lulu-base.glb',base)
result={'revision':rev,'phase':'full' if full else 'right-arm-only','source':str(source.relative_to(R)),'source_sha256':hashlib.sha256(blob).hexdigest(),'rig_sha256':hashlib.sha256((out/'lulu-rig.glb').read_bytes()).hexdigest(),'bones':len(names),'parts':checks,'rest_max_delta':rest_delta,'original_raw_prefix_unchanged':bytes(raw[:original_len])==blob[28+jl:],'native_clips':native_clips,'glb_clips':[c['name'] for c in clips],'blend':str(native.relative_to(R)),'weight_max_influences':4,'art_status':'requires actual motion review; small angles only'}
assert result['original_raw_prefix_unchanged'];(report/'build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
