"""Audit delivery files; actual image inspections are recorded separately by reviewer."""
import json, hashlib
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[2]
P=R/'public/models/unity-animals'; V=R/'review/unity-integration-20261018/animals/game-r04'
m=json.loads((P/'manifest.json').read_text()); checks=json.loads((V/'actual-inspections.json').read_text()); scales=json.loads((V/'scale/actual-inspections.json').read_text()); rows=[]
for a in m['assets']:
 aid=a['id']; d=V/aid; issues=[]; view_count=0
 for variant in ['source','lod0','lod1']:
  for view in ['front','side','back','quarter','top']:
   for material in ['color','clay']:
    f=d/variant/(view+'-'+material+'.png')
    if not f.exists():issues.append('Missing '+str(f.relative_to(V)));continue
    with Image.open(f) as im:
     if im.width<768 or im.height<768:issues.append('Under-resolution '+str(f.relative_to(V)))
    view_count+=1
 for variant in ['lod0','lod1']:
  f=d/(variant+'-readback.json')
  if not f.exists() or not json.loads(f.read_text()).get('pass'):issues.append('Readback incomplete '+variant)
 for lod in a['lods']:
  for key,hkey in [('source','source_sha256'),('native','native_sha256'),('source_import','source_import_sha256'),('file','sha256')]:
   f=Path(lod[key]);f=f if f.is_absolute() else R/f
   if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=lod[hkey]:issues.append('Missing/hash mismatch '+key+' '+lod['variant'])
 f=d/'topology.json'
 if not f.exists():issues.append('Missing topology diagnostics')
 else:
  topo=json.loads(f.read_text())
  for variant,objects in topo['models'].items():
   for o in objects:
    if any(o[k] for k in ['boundary_edges','nonmanifold_edges','zero_area_faces']):issues.append('Topology flags '+variant)
 if aid not in checks:issues.append('No actual visual inspection recorded')
 if not (d/'review-settings.json').exists():issues.append('Missing review settings')
 rows.append({'id':aid,'technical_and_evidence_file_audit':'pass' if not issues else 'incomplete','issues':issues,'full_views':view_count,'visual_initial_review':checks.get(aid,{}).get('visual_initial_review','not_reviewed'),'user_art':'pending','optimization':'LOD_candidates_only','unity_runtime':'separate_root_integration','device':'not_tested'})
scale_issues=[]
for lod in ['lod0','lod1']:
 for n in [1,2,3]:
  k=lod+'-group-'+str(n)
  if not (V/'scale'/(k+'.png')).exists() or not (V/'scale'/(k+'.json')).exists():scale_issues.append('Missing '+k)
  if not scales.get(k,{}).get('actually_viewed'):scale_issues.append('Not inspected '+k)
report={'revision':'game-r04','scope':'15 static animals, independent derived assets, no animal animation','resource_and_native_review_complete':len(rows)==15 and not m['pending'] and all(not r['issues'] for r in rows) and not scale_issues,'asset_count':len(rows),'assets':rows,'scale_issues':scale_issues,'source_preservation':m['source_preservation'],'totals':m['totals'],'actual_visual_evidence':'actual-inspections.json; scale/actual-inspections.json','limitations':['Blender evidence does not verify Unity rendering, LOD transitions or installed builds.','Phone performance has not been tested.','User art approval is pending.','Inherited source seams, texture relief and occasional lower-poly close-up eye reflections are recorded per animal.']}
(V/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'complete':report['resource_and_native_review_complete'],'assets':len(rows),'issues':[(r['id'],r['issues']) for r in rows if r['issues']],'scale_issues':scale_issues},ensure_ascii=False))
