from pathlib import Path
import sys,json,numpy as np,hashlib
sys.path.insert(0,str(Path(__file__).parent));from lulu_patch_io import read_glb,accessor,triangles
R=Path(__file__).resolve().parents[1];rep=R/'review/lulu-wardrobe-rig-20261018/full-r02';source=R/'public/models/modular/arm-trim-volume-r01/lulu-assembled.glb';g,b=read_glb(source);h,c=read_glb(R/'public/models/wardrobe-rig/full-r02/lulu-rig.glb');checks=[]
for sm,tm in zip(g['meshes'],h['meshes']):
 assert sm['name']==tm['name'];name=sm['name'];count=0
 for sp,tp in zip(sm['primitives'],tm['primitives']):
  sf=accessor(g,b,sp['indices']).ravel();tf=accessor(h,c,tp['indices']).ravel();assert len(sf)==len(tf)
  for label,ai in sp['attributes'].items():assert np.array_equal(accessor(g,b,ai)[sf],accessor(h,c,tp['attributes'][label])[tf]),(name,label)
  joints=accessor(h,c,tp['attributes']['JOINTS_0']);weights=accessor(h,c,tp['attributes']['WEIGHTS_0']);assert np.isfinite(weights).all() and np.abs(weights.sum(1)-1).max()<1e-6 and joints.max()<23
  if name=='Shorts':assert 'TEXCOORD_1' in tp['attributes'] and np.isfinite(accessor(h,c,tp['attributes']['TEXCOORD_1'])).all()
  count+=len(sf)//3
 checks.append({'part':name,'triangles':count,'positions_normals_original_uv_colors_exact_per_corner':True,'skin_weights_valid':True})
backup=json.loads((rep.parent/'baseline/manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for x in backup:assert sha(R/x['source'])==x['sha256'] and sha(R/x['backup'])==x['sha256']
base,bb=read_glb(R/'public/models/wardrobe-rig/full-r02/lulu-base.glb');pants,pb=read_glb(R/'public/models/wardrobe-rig/full-r02/shorts-template.glb');assert 'Shorts' not in [m['name'] for m in base['meshes']] and [m['name'] for m in pants['meshes']]==['Shorts']
# All seven non-arm parts remain exact copies of the original modular source.
source_dir=source.parent;original_dir=R/'public/models/modular/right-junction-r04';unchanged=[]
for p in original_dir.glob('*.glb'):
 if p.name in ['lulu-assembled.glb','Arm_R.glb']:continue
 assert sha(p)==sha(source_dir/p.name);unchanged.append(p.stem)
result={'source':str(source.relative_to(R)),'comparison':checks,'original_current_modular_and_backups_unchanged':True,'seven_other_static_parts_identical':unchanged,'shorts_geometry_normals_uv0_and_weights_preserved':True,'shorts_new_uv_channel':1,'base_active_parts':[m['name'] for m in base['meshes']],'template_active_parts':['Shorts'],'total_triangles':sum(x['triangles'] for x in checks),'scope_note':'Only Arm_R inner fringe/closure changed in rig working source. Original right-junction-r04 unchanged. Shorts UV1 requires seam vertex duplication but no shape changes.'};(rep/'preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'preserved':True,'seven_other_parts_identical':True,'uv1_present':True,'triangles':result['total_triangles']}))
