"""Read-only payload checks, preservation and explicit evidence completeness."""
from pathlib import Path
import json,hashlib,struct,io
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018';entries=json.loads((O/'scope.json').read_text());rows=[]
for e in entries:
 slug=e['id'];versions=['toon-r03','game-r02'] if slug=='rose' else ['toon-r01','game-r01'];stats=[]
 for v in versions:
  m=json.loads((O/slug/v/'metrics.json').read_text());p=R/m['glb'];raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);normals=[mat.get('normalTexture',{}).get('scale',1) for mat in doc.get('materials',[])];assert all(abs(x-m['profile']['normal_strength'])<1e-6 for x in normals),(slug,normals)
  assert all(x['welded_boundary_edges']==x['welded_nonmanifold_edges']==x['zero_area_faces_1e12']==x['duplicate_faces_after_weld']==0 and x['finite_normals'] for x in m['roundtrip_topology'])
  assert m['nonfinite_vertices']==m['zero_area_faces']==0 and not m['external_uris'];assert m['sha256']==hashlib.sha256(raw).hexdigest();assert m['source_sha256']==hashlib.sha256((R/m['source']).read_bytes()).hexdigest()
  images=[];missing=[]
  for mode in ['material','clay']:
   for view in ['front','side','back','quarter','top','detail']:
    file=O/slug/v/f'{mode}-{view}.png'
    if not file.exists():missing.append(str(file.relative_to(O)));continue
    im=Image.open(file);assert min(im.size)>=768;im.verify();images.append(str(file.relative_to(O)))
  for view in ['planting-3x3-lulu','farm-distance']:
   file=O/slug/v/f'{view}.png'
   if file.exists():
    im=Image.open(file);assert im.size==((1280,720) if view=='farm-distance' else (768,768));im.verify();images.append(str(file.relative_to(O)))
   else:missing.append(str(file.relative_to(O)))
  stats.append({'version':v,'payload_check':'passed','normal_scale':normals,'images_checked':len(images),'missing':missing,'evidence':images,'inspection_source_reopened':(O/slug/v/'inspection-source.json').exists()})
 rows.append({'crop':slug,'versions':stats})
(O/'technical-validation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
before=json.loads((O/'preservation-before.json').read_text());preservation={p:{'before':sha,'after':hashlib.sha256((R/p).read_bytes()).hexdigest()} for p,sha in before.items()};changed=[p for p,x in preservation.items() if x['before']!=x['after']];assert not changed,changed
(O/'preservation-check.json').write_text(json.dumps({'protected_count':len(before),'unchanged':True,'files':preservation},indent=2))
print('Validated payloads:',len(rows)*2,'missing images:',sum(len(v['missing']) for r in rows for v in r['versions']),'protected originals:',len(before))
