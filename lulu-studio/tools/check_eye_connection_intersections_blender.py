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
m=np.load(R/'review/meshy-eye-connection-map.npz');free=m['free'];stats={}
for name,path in [('baseline',R/'review/meshy-eye-bridge-baseline/lulu-meshy-notail.glb'),('candidate',R/'public/models/lulu-meshy-bridge.glb')]:
 _,g,b=read_glb(path);pr=g['meshes'][0]['primitives'][0];p=accessor(g,b,pr['attributes']['POSITION']);t=accessor(g,b,pr['indices']).reshape(-1,3)
 # Only local eye/skin geometry can intersect after this constrained edit.
 cent=p[t].mean(1);local=(abs(cent[:,0])<.48)&(cent[:,1]>.33)&(cent[:,1]<.65)&(cent[:,2]>.09);tl=t[local];affected=np.any(free[tl],axis=1)
 _,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);wt=inv[tl]
 tree=BVHTree.FromPolygons(p.tolist(),tl.tolist(),all_triangles=True,epsilon=0)
 overlaps=tree.overlap(tree);pairs=[];local_ids=np.flatnonzero(local)
 for a,z in overlaps:
  if a>=z or not(affected[a] or affected[z]):continue
  if np.intersect1d(wt[a],wt[z]).size:continue
  pairs.append([int(local_ids[a]),int(local_ids[z])])
 stats[name]={'local_triangles':int(local.sum()),'nonadjacent_intersection_pairs':len(pairs),'pairs':pairs}
 print(name,'pairs',len(pairs),flush=True)
stats['new_pairs']=[x for x in stats['candidate']['pairs'] if x not in stats['baseline']['pairs']]
stats['new_pair_count']=len(stats['new_pairs'])
(R/'review/meshy-eye-connection-intersections.json').write_text(json.dumps(stats,indent=2));print('new_pairs',stats['new_pair_count'])
