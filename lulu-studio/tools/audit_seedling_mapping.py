from pathlib import Path
import json,hashlib,struct,io
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(R/'public/models/crop-two-stage/manifest.json');before=read(O/'manifest-before.json');rows=[]
for c in manifest['crops']:
 old=next(x for x in before['crops'] if x['id']==c['id']);assert c['mature']==old['mature'],c['id']
for row in read(O/'mapping.json'):
 s=row['id'];version=row.get('current_version','meshy-toon-r01');m=read(O/s/version/'metrics.json');file=R/m['glb'];source=R/m['source'];assert sha(file)==m['sha256'] and sha(source)==m['source_sha256'];assert m['nonfinite_vertices']==m['zero_area_faces']==0;assert not m['external_uris'];assert all(t['welded_boundary']==t['welded_nonmanifold']==t['zero_area_1e14']==0 and t['finite_normals'] for t in m['topology']);assert read(O/s/version/'source-reopen.json')['source_reopened'];assert abs(m['size'][2]-row['height'])<.0001
 raw=file.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);assert not d.get('cameras');assert len(d['meshes'])==1
 for mat in d['materials']:assert abs(mat.get('normalTexture',{}).get('scale',1)-.14)<1e-6
 assert all(max(x)<=1024 for x in m['texture_sizes'])
 expected=[O/s/v/f'{mode}-{view}.png' for v in ['original',version] for mode in ['material','clay'] for view in ['front','side','back','quarter','top']]+[O/s/version/f'{v}.png' for v in ['planting-3x3-lulu','farm-distance']]+[O/s/'stage-pair.png']+[O/s/v/f'{mode}-detail.png' for v in ['original',version] for mode in ['material','clay']];missing=[]
 for p in expected:
  if not p.exists():missing.append(str(p.relative_to(O)));continue
  im=Image.open(p);assert im.size==((1280,720) if p.stem=='farm-distance' else (768,768)),p;im.verify()
 rows.append({'crop':s,'payload':'passed','source_reopen':'passed','embedded_textures':'passed','world_scale':'passed','evidence_count':len(expected)-len(missing),'missing':missing})
preserved=read(O/'preservation-before.json');changed=[p for p,h in preserved.items() if sha(R/p)!=h];assert not changed,changed
inputs=read(O/'inputs-manifest.json')
for x in inputs:assert sha(R/'public'/x['file'].lstrip('/'))==x['sha256']==sha(Path(x['original_download']))
(O/'preservation-check.json').write_text(json.dumps({'protected_files':len(preserved),'mature_manifest_unchanged':True,'protected_unchanged':not changed,'four_downloads_and_project_copies_identical':True},indent=2));(O/'technical-validation.json').write_text(json.dumps(rows,indent=2))
checks=read(O/'browser/checks.json');assert len(checks)==162
for x in checks:assert x['canvas']['stage']=='seedling' and x['canvas']['file']==x['download'];assert json.loads(x['canvas']['camera'])['dpr']==1
single=[x for x in checks if 'layout=single' in x['url']];assert all(int(x['canvas']['geometries'])==3 for x in single)
dl=read(O/'browser/downloads.json');tulip=next(x for x in read(O/'metrics.json') if x['crop']=='tulip');assert sha(Path(dl['glb']))==tulip['sha256'];assert sha(Path(dl['blend']))==tulip['source_sha256'];(O/'browser/download-validation.json').write_text(json.dumps({'glb':dl['glb'],'glb_sha256':tulip['sha256'],'blend':dl['blend'],'blend_sha256':tulip['source_sha256'],'both_match_current_entry':True},indent=2))
print('Validated14models; missingimages',sum(len(x['missing']) for x in rows),'preserved',len(preserved),'browserstates',len(checks))
