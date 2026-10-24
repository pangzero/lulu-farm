"""Remove opposite duplicate fin faces from r10; keep the visible surfaces/skin."""
from pathlib import Path
import bpy,numpy as np,json,struct,hashlib
R=Path(__file__).resolve().parents[1];src=R/'public/models/rig/lulu-rig-r10.glb';out=R/'public/models/rig/lulu-rig-r11.glb';blend=R/'assets-source/rig/lulu-rig-r11.blend';folder=R/'review/lulu-rig-separation-20261018/r11'
assert not out.exists() and not blend.exists()
folder.mkdir(parents=True,exist_ok=True)
b=src.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);raw=bytearray(b[28+n:])
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
 return np.ndarray((a['count'],sz),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*dt.itemsize),dt.itemsize)).copy()
prims=g['meshes'][0]['primitives'];positions=[];faces=[];lengths=[]
for pr in prims:
 p=acc(pr['attributes']['POSITION']);f=acc(pr['indices']).reshape(-1,3);faces.extend(f+len(positions));positions.extend(p);lengths.append(len(f))
p=np.array(positions);f=np.array(faces);u,iv=np.unique(p,axis=0,return_inverse=True);ff=iv[f];_,ids,c=np.unique(np.sort(ff,axis=1),axis=0,return_inverse=True,return_counts=True);remove=c[ids]>1
assert int(remove.sum())==26
for group in np.where(c>1)[0]:
 tri=p[f[ids==group]];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);assert len(tri)==2 and norm[0]@norm[1]<0
# Opposite coincident fins have no volume. Remove both sides, not just one.
def add(a,typ,comp):
 while len(raw)%4:raw.append(0)
 off=len(raw);raw.extend(a.tobytes());bi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':a.nbytes});ai=len(g['accessors']);v={'bufferView':bi,'componentType':comp,'count':len(a),'type':typ}
 if typ=='VEC3':v.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 g['accessors'].append(v);return ai
start=0
for pr,l in zip(prims,lengths):
 f=acc(pr['indices']).reshape(-1,3)[~remove[start:start+l]];start+=l;used,iv=np.unique(f,return_inverse=True)
 attrs={}
 for k,i in pr['attributes'].items():
  a=g['accessors'][i];attrs[k]=add(acc(i)[used],a['type'],a['componentType'])
 pr['attributes']=attrs;pr['indices']=add(iv.astype('<u4').reshape(-1,1),'SCALAR',5125)
g['buffers'][0]['byteLength']=len(raw);g['extras']['lulu']['revision']='r11';g['extras']['lulu']['cleanup']='26 opposite coincident fin triangles removed; outer rest surface preserved from r10'
j=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw+=b'\0'*((-len(raw))%4)
out.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(raw))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(out),merge_vertices=True)
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');arm.show_in_front=True
bpy.context.scene['asset_name']='Lulu 腋下分离绑定候选 r11';bpy.context.scene['base']='Lulu 正式版 v1; independent rig, local reconstructed inner arm and chest surfaces'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'revision':'r11','source':'r10','removed_opposite_duplicate_faces':26,'glb':str(out.relative_to(R)),'blend':str(blend.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'status':'Small-motion candidate; user visual acceptance pending'}
(folder/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
