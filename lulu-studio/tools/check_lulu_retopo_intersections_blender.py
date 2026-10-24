import sys,json
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import struct
R=Path(__file__).resolve().parents[1]
def read_glb(path):
 data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0]
 return data,json.loads(data[20:20+size]),data[28+size:]
def accessor(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];size={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
 return np.ndarray((a['count'],size),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*dt.itemsize),dt.itemsize))
stats={}
for name,path in [('baseline',R/'review/meshy-eye-retopo-baseline/lulu-meshy-notail.glb'),('candidate',R/'public/models/lulu-meshy-retopo.glb')]:
 _,g,b=read_glb(path);pr=g['meshes'][0]['primitives'];p=accessor(g,b,pr[0]['attributes']['POSITION']);parts=[accessor(g,b,q['indices']).reshape(-1,3) for q in pr];t=np.concatenate(parts)
 cent=p[t].mean(1);local=(abs(cent[:,0])<.43)&(cent[:,1]>.36)&(cent[:,1]<.68)&(cent[:,2]>.07);tl=t[local];globalids=np.flatnonzero(local)
 _,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);wt=inv[tl]
 tree=BVHTree.FromPolygons(p.tolist(),tl.tolist(),all_triangles=True,epsilon=0)
 pairs=[]
 for a,z in tree.overlap(tree):
  if a>=z or np.intersect1d(wt[a],wt[z]).size:continue
  pairs.append([int(globalids[a]),int(globalids[z])])
 new_start=sum(map(len,parts[:-1])) if name=='candidate' else len(t)
 stats[name]={'local_triangles':int(local.sum()),'nonadjacent_intersection_pairs':len(pairs),'new_patch_involved_pairs':sum(a>=new_start or z>=new_start for a,z in pairs),'pairs':pairs}
 print(name,{k:v for k,v in stats[name].items() if k!='pairs'},flush=True)
(R/'review/meshy-eye-retopo-intersections.json').write_text(json.dumps(stats,indent=2))
