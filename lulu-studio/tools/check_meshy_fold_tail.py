from pathlib import Path
import json,struct,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1]
base=R/'review/meshy-fold-tail-baseline/lulu-meshy-eyes.glb'
def read(p):
 d=p.read_bytes();n=struct.unpack_from('<I',d,12)[0];return json.loads(d[20:20+n]),d[28+n:]
def arr(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];return np.ndarray((a['count'],sz),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*np.dtype(dt).itemsize),np.dtype(dt).itemsize))
def image(g,b,i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return b[v['byteOffset']:v['byteOffset']+v['byteLength']]
g0,b0=read(base);pr=g0['meshes'][0]['primitives'][0];p0=arr(g0,b0,pr['attributes']['POSITION']);n0=arr(g0,b0,pr['attributes']['NORMAL']);uv0=arr(g0,b0,pr['attributes']['TEXCOORD_0']);t0=arr(g0,b0,pr['indices']).reshape(-1,3)
x,y,z=p0.T
fold_scope=(np.sqrt(((abs(x)-.265)/.135)**2+((y-.456)/.042)**2)<1.201)&(z>.179)
eye_scope=(np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.070)**2)<1.221)&(z>.129)
tail_scope=(y<-.475)&(y>-.62)&(abs(x-.0015)<.0671)&(z<-.4459)
scopes={'fold':fold_scope,'surface':eye_scope,'tail':tail_scope,'polish':fold_scope|eye_scope|tail_scope}
report={'baseline_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'variants':{}}
for name,scope in scopes.items():
 g,b=read(R/f'public/models/lulu-meshy-{name}.glb');p=arr(g,b,pr['attributes']['POSITION']);n=arr(g,b,pr['attributes']['NORMAL']);t=arr(g,b,pr['indices']).reshape(-1,3);delta=p-p0;changed=np.any(delta!=0,axis=1)
 face=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]);face0=np.cross(p0[t0[:,1]]-p0[t0[:,0]],p0[t0[:,2]]-p0[t0[:,0]])
 area=np.linalg.norm(face,axis=1);area0=np.linalg.norm(face0,axis=1)
 r={'finite_geometry_and_normals':bool(np.isfinite(p).all() and np.isfinite(n).all()),'coordinates_outside_scope_exact':bool(np.array_equal(p0[~scope],p[~scope])),'normals_outside_scope_exact':bool(np.array_equal(n0[~scope],n[~scope])),'changed_vertices':int(changed.sum()),'max_axis_delta':np.abs(delta).max(0).tolist(),'UV_exact':bool(np.array_equal(uv0,arr(g,b,pr['attributes']['TEXCOORD_0']))),'topology_exact':bool(np.array_equal(t,t0)),'all_texture_bytes_exact':all(image(g0,b0,i)==image(g,b,i) for i in range(len(g0['images']))),'materials_exact':g['materials']==g0['materials'],'nodes_transforms_exact':g['nodes']==g0['nodes'],'bounds_exact':bool(np.array_equal(p.min(0),p0.min(0)) and np.array_equal(p.max(0),p0.max(0))),'new_near_zero_area_triangles':int(((area<1e-12)&(area0>=1e-12)).sum()),'horizontal_vertical_eye_positions_exact':bool(np.array_equal(p0[eye_scope&~fold_scope,:2],p[eye_scope&~fold_scope,:2]))}
 r['passed']=all(v for v in r.values() if isinstance(v,bool)) and r['new_near_zero_area_triangles']==0;report['variants'][name]=r
report['passed']=all(r['passed'] for r in report['variants'].values());(R/'review/meshy-fold-tail-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert report['passed']
