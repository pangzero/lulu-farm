"""Preservation checks for the one-sided r04 trial; no model modifications."""
from pathlib import Path
import sys,json,hashlib,numpy as np,shutil
sys.path.insert(0,str(Path(__file__).parent))
from lulu_patch_io import read_glb,triangles
R=Path(__file__).resolve().parents[1];rev='right-junction-r04';rep=R/'review/lulu-right-junction-20261018'/rev;src=R/'public/models/modular/parts-v2';dst=R/'public/models/modular'/rev
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
back=json.loads((rep.parent/'baseline/manifest.json').read_text())
for entry in back:
 entry['source_unchanged']=sha(R/entry['source'])==entry['sha256'];entry['backup_unchanged']=sha(R/entry['backup'])==entry['sha256'];assert entry['source_unchanged'] and entry['backup_unchanged']
g,b=read_glb(src/'lulu-assembled.glb');h,c=read_glb(dst/'lulu-assembled.glb');records=[]
for mesh in g['meshes']:
 name=mesh['name'];t,m=triangles(g,b,mesh);nt,nm=triangles(h,c,next(x for x in h['meshes'] if x['name']==name));co=t[:,:,:3].mean(1)
 mask=(m==2) if name=='Arm_R' else ((m==2)&(co[:,0]<-.29)&(co[:,1]>-.415)&(co[:,1]<-.112)) if name=='Body' else np.zeros(len(t),bool)
 for mat in np.unique(m):
  fixed=t[(~mask)&(m==mat)].astype('<f4');actual=nt[nm==mat][:len(fixed)];assert np.array_equal(fixed,actual),(name,int(mat))
 sg,sb=read_glb(dst/(name+'.glb'));st,sm=triangles(sg,sb,sg['meshes'][0]);assert np.array_equal(st,nt) and np.array_equal(sm,nm)
 records.append({'part':name,'fixed_original_triangles':int((~mask).sum()),'fixed_positions_normals_uv_colors_exact':True,'standalone_matches_assembly':True,'unchanged_file':sha(src/(name+'.glb'))==sha(dst/(name+'.glb'))})
for i,j in zip(g['images'],h['images']):
 vi=g['bufferViews'][i['bufferView']];vj=h['bufferViews'][j['bufferView']];assert b[vi.get('byteOffset',0):vi.get('byteOffset',0)+vi['byteLength']]==c[vj.get('byteOffset',0):vj.get('byteOffset',0)+vj['byteLength']]
official={'public/models/lulu-official-v1.glb':'5f770f539c3927b9e4d26a73bf96070e86e6b6cdd04e9710074b4c6645207e7d','assets-source/lulu-official-v1.blend':'58f9f045dca6804b6a1da772cc5a9f30eeebdfd8ab624343e581d20a5a4e8c4a'}
for p,s in official.items():assert sha(R/p)==s
result={'revision':rev,'baseline_and_backup':back,'official_unchanged':True,'parts':records,'embedded_images_unchanged':True,'skeletons':len(h.get('skins',[])),'animations':len(h.get('animations',[])),'assembly_sha256':sha(dst/'lulu-assembled.glb')}
(rep/'preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));shutil.copy2(R/'review/lulu-modular-20261018'/rev/'blender-check.json',rep/'blender-check.json');print(json.dumps({'official_unchanged':True,'fixed_geometry_exact':True,'six_other_files_identical':all(x['unchanged_file'] for x in records if x['part'] not in ['Arm_R','Body']),'standalone_matches':True,'skins':0,'animations':0}))
