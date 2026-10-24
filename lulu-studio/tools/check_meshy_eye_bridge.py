import json,hashlib
import numpy as np
from refine_meshy_eye_natural import R,read_glb,accessor
base=R/'review/meshy-eye-bridge-baseline/lulu-meshy-notail.glb';d0,g0,b0=read_glb(base);d,g,b=read_glb(R/'public/models/lulu-meshy-bridge.glb');pr0=g0['meshes'][0]['primitives'];pr=g['meshes'][0]['primitives'];a0=pr0[0]['attributes'];a=pr[0]['attributes']
p0=accessor(g0,b0,a0['POSITION']);n0=accessor(g0,b0,a0['NORMAL']);uv0=accessor(g0,b0,a0['TEXCOORD_0']);p=accessor(g,b,a['POSITION']);n=accessor(g,b,a['NORMAL']);uv=accessor(g,b,a['TEXCOORD_0'])
m=np.load(R/'review/meshy-eye-bridge-map.npz');keep=m['retained'];border=m['border'];eye=m['eye'];tri=[accessor(g,b,q['indices']).reshape(-1,3) for q in pr];t=np.concatenate(tri);_,weld=np.unique(np.round(p,6),axis=0,return_inverse=True);wt=weld[t];e=np.sort(np.concatenate([wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]]),axis=1);edges,count=np.unique(e,axis=0,return_counts=True);area=np.linalg.norm(np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]),axis=1)
parent=np.arange(weld.max()+1)
def root(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
for a,z in edges:
 a=root(a);z=root(z)
 if a!=z:parent[z]=a
all_eye_kept=np.isin(np.flatnonzero(eye),keep).all();pin=np.isin(keep,np.flatnonzero(eye))
def image(g,b,i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return b[v['byteOffset']:v['byteOffset']+v['byteLength']]
f=np.cross(p[tri[-1][:,1]]-p[tri[-1][:,0]],p[tri[-1][:,2]]-p[tri[-1][:,0]])
r={'source_sha256':hashlib.sha256(d0).hexdigest(),'output_sha256':hashlib.sha256(d).hexdigest(),'retained_positions_exact':bool(np.array_equal(p[:len(keep)],p0[keep])),'retained_UV_exact':bool(np.array_equal(uv[:len(keep)],uv0[keep])),'retained_normals_outside_cut_border_exact':bool(np.array_equal(n[:len(keep)][~border],n0[keep][~border])),'all_painted_eye_vertices_kept':bool(all_eye_kept),'painted_eye_positions_exact':bool(all_eye_kept and np.array_equal(p[:len(keep)][pin],p0[keep][pin])),'painted_eye_normals_exact':bool(np.array_equal(n[:len(keep)][pin],n0[keep][pin])),'retained_body_triangles_exact':bool(np.array_equal(keep[tri[0]],accessor(g0,b0,pr0[0]['indices']).reshape(-1,3)[~m['removed']])),'tail_patch_triangles_exact':bool(np.array_equal(keep[tri[1]],accessor(g0,b0,pr0[1]['indices']).reshape(-1,3))),'original_images_exact':all(image(g,b,i)==image(g0,b0,i) for i in range(len(g0['images']))),'original_materials_exact':g['materials'][:len(g0['materials'])]==g0['materials'],'nodes_exact':g['nodes']==g0['nodes'],'bounds_exact':bool(np.array_equal(p.min(0),p0.min(0)) and np.array_equal(p.max(0),p0.max(0))),'finite':bool(np.isfinite(p).all() and np.isfinite(n).all()),'patch_front_facing':bool(np.all(f[:,2]>0)),'boundary_edges':int((count==1).sum()),'nonmanifold_edges':int((count>2).sum()),'connected_components':len(set(root(int(i)) for i in np.unique(wt))),'degenerate_triangles':int((area<1e-12).sum()),'triangle_count':len(t),'patch_min_twice_area':float(np.linalg.norm(f,axis=1).min())}
r['passed']=all(v for v in r.values() if isinstance(v,bool)) and r['boundary_edges']==0 and r['nonmanifold_edges']==0 and r['connected_components']==1 and r['degenerate_triangles']==0
(R/'review/meshy-eye-bridge-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert r['passed']
