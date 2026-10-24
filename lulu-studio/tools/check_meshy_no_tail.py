"""Protection and topology checks for the local tail deletion."""
import json,hashlib
import numpy as np
from refine_meshy_eye_natural import R,read_glb,accessor
base=R/'review/meshy-no-tail-baseline/lulu-meshy-natural.glb'
d0,g0,b0=read_glb(base);d,g,b=read_glb(R/'public/models/lulu-meshy-notail.glb')
m=np.load(R/'review/meshy-no-tail-map.npz');keep=m['retained'];border=m['border']
pr0=g0['meshes'][0]['primitives'][0];pr=g['meshes'][0]['primitives']
p0=accessor(g0,b0,pr0['attributes']['POSITION']);n0=accessor(g0,b0,pr0['attributes']['NORMAL']);uv0=accessor(g0,b0,pr0['attributes']['TEXCOORD_0']);t0=accessor(g0,b0,pr0['indices']).reshape(-1,3)
p=accessor(g,b,pr[0]['attributes']['POSITION']);n=accessor(g,b,pr[0]['attributes']['NORMAL']);uv=accessor(g,b,pr[0]['attributes']['TEXCOORD_0'])
t=np.concatenate([accessor(g,b,q['indices']).reshape(-1,3) for q in pr]);_,weld=np.unique(np.round(p,6),axis=0,return_inverse=True);wt=weld[t]
e=np.sort(np.concatenate([wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]]),axis=1);edges,counts=np.unique(e,axis=0,return_counts=True)
parent=np.arange(weld.max()+1)
def root(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
for a,z in edges:
 a=root(a);z=root(z)
 if a!=z:parent[z]=a
areas=np.linalg.norm(np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]),axis=1)
patch=t[len(t0)-m['removed_faces'].sum():];patch_normal=np.cross(p[patch[:,1]]-p[patch[:,0]],p[patch[:,2]]-p[patch[:,0]])
def image(g,b,i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return b[v['byteOffset']:v['byteOffset']+v['byteLength']]
body_indices=accessor(g,b,pr[0]['indices']).reshape(-1,3)
r={'source_sha256':hashlib.sha256(d0).hexdigest(),'output_sha256':hashlib.sha256(d).hexdigest(),'triangles':len(t),'retained_original_positions_exact':bool(np.array_equal(p[:len(keep)],p0[keep])),'retained_original_UV_exact':bool(np.array_equal(uv[:len(keep)],uv0[keep])),'retained_normals_outside_cut_border_exact':bool(np.array_equal(n[:len(keep)][~border],n0[keep][~border])),'retained_original_triangles_exact':bool(np.array_equal(keep[body_indices],t0[~m['removed_faces']])),'original_textures_exact':all(image(g,b,i)==image(g0,b0,i) for i in range(len(g0['images']))),'original_material_exact':g['materials'][:len(g0['materials'])]==g0['materials'],'nodes_exact':g['nodes']==g0['nodes'],'bounds_exact':bool(np.array_equal(p.min(0),p0.min(0)) and np.array_equal(p.max(0),p0.max(0))),'finite_attributes':bool(np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()),'indices_valid':bool(t.min()>=0 and t.max()<len(p)),'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),'connected_components':len(set(root(int(i)) for i in np.unique(wt))),'zero_area_triangles':int((areas<1e-12).sum()),'patch_back_facing':bool(np.all(patch_normal[:,2]<0)),'minimum_patch_twice_area':float(np.linalg.norm(patch_normal,axis=1).min())}
r['passed']=all(v for v in r.values() if isinstance(v,bool)) and r['boundary_edges']==0 and r['nonmanifold_edges']==0 and r['connected_components']==1 and r['zero_area_triangles']==0
(R/'review/meshy-no-tail-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert r['passed']
