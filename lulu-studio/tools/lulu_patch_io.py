"""GLB triangle-corner IO; preserve source images/materials and mesh attributes."""
from pathlib import Path
import json,struct,copy,numpy as np

def read_glb(path):
 b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def accessor(g,raw,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];s={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]);return np.ndarray((a['count'],s),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',s*dt.itemsize),dt.itemsize)).copy()
def triangles(g,raw,mesh):
 ts=[];ms=[]
 for pr in mesh['primitives']:
  at=pr['attributes'];p=accessor(g,raw,at['POSITION']);no=accessor(g,raw,at['NORMAL']);uv=accessor(g,raw,at['TEXCOORD_0']);co=accessor(g,raw,at['COLOR_0']) if 'COLOR_0' in at else np.ones_like(p);f=accessor(g,raw,pr['indices']).reshape(-1,3);ts.append(np.concatenate([p,no,uv,co],axis=1)[f]);ms.extend([pr.get('material',0)]*len(f))
 return np.concatenate(ts),np.array(ms)
def write_glb(path,g,raw,parts,revision):
 doc={k:copy.deepcopy(g[k]) for k in ['asset','materials','textures','samplers','extensionsUsed','extensionsRequired'] if k in g};data=bytearray();doc.update(bufferViews=[],accessors=[],images=[],meshes=[],nodes=[],scenes=[{'nodes':[]}],scene=0,buffers=[{}])
 def buf(bb):
  data.extend(b'\0'*((-len(data))%4));i=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(bb)});data.extend(bb);return i
 for img in g['images']:
  v=g['bufferViews'][img['bufferView']];q=copy.deepcopy(img);q['bufferView']=buf(raw[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);doc['images'].append(q)
 def add(a,typ,component):
  i=len(doc['accessors']);q={'bufferView':buf(a.tobytes()),'componentType':component,'count':len(a),'type':typ}
  if typ=='VEC3':q.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  doc['accessors'].append(q);return i
 for name,t,ms in parts:
  prim=[]
  for mi in np.unique(ms):
   a=t[ms==mi].reshape(-1,11).astype('<f4');a,inv=np.unique(a,axis=0,return_inverse=True);at={}
   for label,sl,typ in [('POSITION',slice(0,3),'VEC3'),('NORMAL',slice(3,6),'VEC3'),('TEXCOORD_0',slice(6,8),'VEC2')]:at[label]=add(a[:,sl].copy(),typ,5126)
   if mi==2:at['COLOR_0']=add(a[:,8:11].copy(),'VEC3',5126)
   prim.append({'attributes':at,'indices':add(inv.astype('<u4').reshape(-1,1),'SCALAR',5125),'material':int(mi),'mode':4})
  i=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':prim});doc['nodes'].append({'name':name,'mesh':i,'extras':{'part':name,'static_only':True}});doc['scenes'][0]['nodes'].append(i)
 doc['buffers'][0]['byteLength']=len(data);doc['extras']=copy.deepcopy(g.get('extras',{}));doc['extras']['lulu']['revision']=revision;j=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data+=b'\0'*((-len(data))%4);Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(data))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data)
