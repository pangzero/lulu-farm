"""Check locality and closed patch attachment without asserting art quality."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from lulu_patch_io import read_glb,accessor

R=Path(__file__).resolve().parents[1];D=R/'review/lulu-eye-ring-20261018';O=D/'orbit-r03'
g,b=read_glb(D/'baseline/modular-r04.glb');h,c=read_glb(O/'lulu-eye-ring.glb')
checks=[]
for i in range(1,len(g['meshes'])):
    a=g['meshes'][i];d=h['meshes'][i];ok=True
    for p,q in zip(a['primitives'],d['primitives']):
        ok&=p==q
        for k,v in p['attributes'].items():ok&=np.array_equal(accessor(g,b,v),accessor(h,c,q['attributes'][k]))
        ok&=np.array_equal(accessor(g,b,p['indices']),accessor(h,c,q['indices']))
    assert ok;checks.append({'part':a['name'],'exact':True})
pr=g['meshes'][0]['primitives'][0];P=accessor(g,b,pr['attributes']['POSITION']);V=accessor(h,c,h['meshes'][0]['primitives'][0]['attributes']['POSITION']);assert np.array_equal(P,V)
pack=np.load(O/'patch.npz');sel=pack['removed'];T=accessor(g,b,pr['indices']).reshape(-1,3);newp=pack['P'].astype('float32');newt=pack['T']
assert np.array_equal(accessor(h,c,h['meshes'][0]['primitives'][0]['indices']).reshape(-1,3),T[~sel])
assert np.all(P[T[sel],0]<0)
U,inv=np.unique(P,axis=0,return_inverse=True);bd=pack['boundary_ids'];old=U[bd]
assert all(np.any(np.all(newp==p,axis=1)) for p in old)
def edge_counts(tri):
    _,ii=np.unique(np.round(tri.reshape(-1,3),6),axis=0,return_inverse=True);f=ii.reshape(-1,3);e=np.sort(np.r_[f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]],axis=1);_,cnt=np.unique(e,axis=0,return_counts=True)
    return {'open_edges':int((cnt==1).sum()),'nonmanifold_edges':int((cnt>2).sum())}
old_top=edge_counts(P[T]);new_top=edge_counts(np.r_[P[T[~sel]],newp[newt]])
assert new_top==old_top,(old_top,new_top)
assert np.allclose(np.r_[P[T[~sel]],newp[newt]].min((0,1)),P[T].min((0,1)),atol=1e-7)
assert np.allclose(np.r_[P[T[~sel]],newp[newt]].max((0,1)),P[T].max((0,1)),atol=1e-7)
images=[]
for a,d in zip(g['images'],h['images']):
    v=g['bufferViews'][a['bufferView']];w=h['bufferViews'][d['bufferView']];s=v.get('byteOffset',0);t=w.get('byteOffset',0);assert b[s:s+v['byteLength']]==c[t:t+w['byteLength']];images.append(True)
backups=json.loads((D/'backup.json').read_text())
for v in backups:assert hashlib.sha256((R/v['source']).read_bytes()).hexdigest()==v['sha256']
report={'source_backups_unchanged':True,'other_seven_parts':checks,'retained_head_attributes_exact':True,'untouched_head_triangles_exact':True,'opposite_eye_untouched':True,'outer_boundary_vertices_exact':len(bd),'head_bounds_exact':True,'source_head_topology':old_top,'candidate_head_topology':new_top,'original_images_exact':len(images),'scope':'One whole eye/skin transition, character right / screen left. Eye depth allowed to change; front painted silhouette reprojected.','art_acceptance':'separate visual review; not established by these checks'}
(O/'preservation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
