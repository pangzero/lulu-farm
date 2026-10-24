"""Protection gates for the current eye-corner-only candidate."""
import json,hashlib
import numpy as np
from refine_meshy_eye_natural import R,BASE,read_glb,accessor,scope_and_core

d0,g0,b0=read_glb(BASE);d,g,b=read_glb(R/'public/models/lulu-meshy-natural.glb')
pr=g0['meshes'][0]['primitives'][0]
p0=accessor(g0,b0,pr['attributes']['POSITION']);p=accessor(g,b,pr['attributes']['POSITION'])
n0=accessor(g0,b0,pr['attributes']['NORMAL']);n=accessor(g,b,pr['attributes']['NORMAL'])
t0=accessor(g0,b0,pr['indices']).reshape(-1,3);t=accessor(g,b,pr['indices']).reshape(-1,3)
scope,core,*_=scope_and_core(p0)
delta=p-p0
f0=np.cross(p0[t0[:,1]]-p0[t0[:,0]],p0[t0[:,2]]-p0[t0[:,0]])
f=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]])
a0=np.linalg.norm(f0,axis=1);a=np.linalg.norm(f,axis=1)
valid=a0>1e-12
cos=(f*f0).sum(1)/np.maximum(a*a0,1e-20)
def image(g,b,i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return b[v['byteOffset']:v['byteOffset']+v['byteLength']]
r={'baseline_sha256':hashlib.sha256(d0).hexdigest(),'output_sha256':hashlib.sha256(d).hexdigest(),
 'finite_geometry_normals':bool(np.isfinite(p).all() and np.isfinite(n).all()),
 'all_XY_coordinates_exact':bool(np.array_equal(p[:,:2],p0[:,:2])),
 'outside_eye_scope_coordinates_exact':bool(np.array_equal(p[~scope],p0[~scope])),
 'outside_eye_scope_normals_exact':bool(np.array_equal(n[~scope],n0[~scope])),
 'eye_core_coordinates_exact':bool(np.array_equal(p[core],p0[core])),
 'eye_core_normals_exact':bool(np.array_equal(n[core],n0[core])),
 'UV_exact':bool(np.array_equal(accessor(g,b,pr['attributes']['TEXCOORD_0']),accessor(g0,b0,pr['attributes']['TEXCOORD_0']))),
 'topology_exact':bool(np.array_equal(t,t0)),
 'all_textures_exact':all(image(g,b,i)==image(g0,b0,i) for i in range(len(g0['images']))),
 'materials_exact':g['materials']==g0['materials'],'nodes_transforms_exact':g['nodes']==g0['nodes'],
 'bounds_exact':bool(np.array_equal(p.min(0),p0.min(0)) and np.array_equal(p.max(0),p0.max(0))),
 'new_near_zero_area_triangles':int(((a<1e-12)&valid).sum()),
 'new_face_reversals_over_90deg':int(((cos<0)&valid).sum()),
 'minimum_face_area_ratio':float((a[valid]/a0[valid]).min()),
 'max_axis_delta':np.abs(delta).max(0).tolist(),'changed_vertices':int(np.any(delta!=0,axis=1).sum())}
r['passed']=all(v for v in r.values() if isinstance(v,bool)) and r['new_near_zero_area_triangles']==0 and r['new_face_reversals_over_90deg']==0
(R/'review/meshy-eye-natural-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert r['passed']
