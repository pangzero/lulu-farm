import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'public/models/unity-integration/manifest.json';d=json.loads(P.read_text());old=json.loads((R/'public/models/crop-two-stage/manifest.json').read_text());raw=json.loads((R/'public/models/crops-meshy/manifest.json').read_text());fac=json.loads((R/'public/models/facilities-meshy/manifest.json').read_text())
def absolute(p):return R/'public'/p.lstrip('/') if p.startswith('/models/') else R/p
cache={}
def file_record(p,role,name=None):
 p=Path(p);assert p.exists(),p
 if str(p) not in cache:cache[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return {'role':role,'file':str(p),'name':name or p.name,'sha256':cache[str(p)],'bytes':p.stat().st_size}
for r in d['assets']:
 if r['type']=='animal':continue
 chain=[]
 if r['type']=='crop':
  c=next(x for x in old['crops'] if x['id']==r['species'])
  if r['stage']=='seedling':
   b=c['seedling']['meshy-original'];p=absolute(b['originalFile']);chain.append(file_record(p,'user_meshy_original'));r['shared_family']=b['family'];r['shared_mapping_note']=b['mappingNote']
  else:
   b=next(x for x in raw['crops'] if x['id']==r['species']);p=absolute(b['file']);q=file_record(p,'user_meshy_original',b['original_name']);assert q['sha256']==b['sha256'];chain.append(q)
  version=next((v for v in c[r['stage']].values() if str(absolute(v['file']))==r['source']),None)
  if version and version.get('source'):
   p=absolute(version['source'])
   if p.exists():chain.append(file_record(p,'pre_unity_editable_import'))
 elif any(x['id']==r['id'] for x in fac['assets']):
  b=next(x for x in fac['assets'] if x['id']==r['id']);p=absolute(b['file']);q=file_record(p,'user_meshy_original',b['source_name']);assert q['sha256']==b['sha256'];chain.append(q)
 chain.append(file_record(r['source'],'immediate_input',r['source_name']));r['provenance_chain']=chain
 if r.get('metrics_file'):
  r['lods']=[{'level':0,'model':r['file'],'triangles':r['triangles'],'sha256':r['sha256'],'editable_source':r['editable_source'],'metrics':r['metrics_file'],'status':'local source/readback/fixed-view review; Unity pending'}]+[x for x in r.get('lods',[]) if x.get('level')!=0]
  for lod in r['lods']:
   if not lod.get('sha256'):lod['sha256']=file_record(lod['model'],'candidate')['sha256']
P.write_text(json.dumps(d,ensure_ascii=False,indent=2));print('PROVENANCE_UPDATED',sum(r['type']!='animal' for r in d['assets']))
