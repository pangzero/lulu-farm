import json,hashlib
import numpy as np
from refine_meshy_eye_natural import R,read_glb,accessor
base=R/'review/meshy-eye-retopo-baseline/lulu-meshy-notail.glb';d0,g0,b0=read_glb(base);d,g,b=read_glb(R/'public/models/lulu-meshy-retopo.glb');pr0=g0['meshes'][0]['primitives'];pr=g['meshes'][0]['primitives'];a=pr[0]['attributes'];a0=pr0[0]['attributes'];p0=accessor(g0,b0,a0['POSITION']);n0=accessor(g0,b0,a0['NORMAL']);uv0=accessor(g0,b0,a0['TEXCOORD_0']);p=accessor(g,b,a['POSITION']);n=accessor(g,b,a['NORMAL']);uv=accessor(g,b,a['TEXCOORD_0']);m=np.load(R/'review/meshy-eye-retopo-map.npz');keep=m['retained'];tris=[accessor(g,b,q['indices']).reshape(-1,3) for q in pr];t=np.concatenate(tris)
_,inv=np.unique(np.round(p,6),axis=0,return_inverse=True);wt=inv[t];edges=np.sort(np.concatenate([wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]]),axis=1);edges,count=np.unique(edges,axis=0,return_counts=True)
parent=np.arange(inv.max()+1)
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for aa,bb in edges:
 aa=root(aa);bb=root(bb)
 if aa!=bb:parent[bb]=aa
f=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]);area=np.linalg.norm(f,axis=1);pf=np.cross(p[tris[-1][:,1]]-p[tris[-1][:,0]],p[tris[-1][:,2]]-p[tris[-1][:,0]])
q0=np.sqrt(((abs(p0[:,0])-.232)/.079)**2+((p0[:,1]-.525)/.07)**2);eye_core=(q0<.50)&(p0[:,2]>.08)
def img(g,b,i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return b[v['byteOffset']:v['byteOffset']+v['byteLength']]
edit=json.loads((R/'review/meshy-eye-retopo-edit.json').read_text());start=0;positive=True
for part in edit['patches']:
 part_count=part['new_triangles'];axis=np.array(part['graph_axis'])
 positive &= bool(np.all(pf[start:start+part_count]@axis>0));start+=part_count
r={'source_sha256':hashlib.sha256(d0).hexdigest(),'output_sha256':hashlib.sha256(d).hexdigest(),'retained_positions_exact':bool(np.array_equal(p[:len(keep)],p0[keep])),'retained_normals_exact':bool(np.array_equal(n[:len(keep)],n0[keep])),'retained_UV_exact':bool(np.array_equal(uv[:len(keep)],uv0[keep])),'eye_center_core_fully_retained':bool(np.isin(np.flatnonzero(eye_core),keep).all()),'retained_body_faces_exact':bool(np.array_equal(keep[tris[0]],accessor(g0,b0,pr0[0]['indices']).reshape(-1,3)[~m['removed']])),'shorts_back_faces_exact':bool(np.array_equal(keep[tris[1]],accessor(g0,b0,pr0[1]['indices']).reshape(-1,3))),'original_images_exact':all(img(g,b,i)==img(g0,b0,i) for i in range(len(g0['images']))),'original_materials_exact':g['materials'][:len(g0['materials'])]==g0['materials'],'nodes_exact':g['nodes']==g0['nodes'],'bounds_exact':bool(np.array_equal(p.min(0),p0.min(0)) and np.array_equal(p.max(0),p0.max(0))),'finite_attributes':bool(np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all()),'new_patch_positive_in_eye_tangent_projection':positive,'boundary_edges':int((count==1).sum()),'nonmanifold_edges':int((count>2).sum()),'connected_components':len(set(root(int(i)) for i in np.unique(wt))),'degenerate_triangles':int((area<1e-12).sum()),'total_triangles':len(t),'retained_vertices':len(keep),'new_vertices':len(p)-len(keep),'old_removed_faces':int(m['removed'].sum()),'new_patch_faces':len(tris[-1])}
r['protection_and_topology_passed']=all(v for v in r.values() if isinstance(v,bool)) and r['boundary_edges']==0 and r['nonmanifold_edges']==0 and r['connected_components']==1 and r['degenerate_triangles']==0
(R/'review/meshy-eye-retopo-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert r['protection_and_topology_passed']
