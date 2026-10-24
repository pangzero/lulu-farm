from pathlib import Path
import json,urllib.request
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018'
ids={e['id'] for e in json.loads((O/'scope.json').read_text())};m=json.loads((R/'public/models/crop-two-stage/manifest.json').read_text());checks=[]
for c in m['crops']:
 if c['id'] not in ids:continue
 for v in (['toon-r03','game-r02'] if c['id']=='rose' else ['toon-r01','game-r01']):
  for kind in ['file','source']:
   url=c['mature'][v][kind];p=R/'public'/url.lstrip('/');req=urllib.request.Request('http://127.0.0.1:5173'+url,method='HEAD')
   with urllib.request.urlopen(req,timeout=20) as r:status=r.status;size=int(r.headers['Content-Length'])
   assert status==200 and size==p.stat().st_size,(url,status,size)
   checks.append({'crop':c['id'],'version':v,'kind':kind,'url':url,'http_status':status,'bytes':size,'local_size_match':True})
 for url in [c['matureConcept']]:
  with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:5173'+url,method='HEAD'),timeout=20) as r:assert r.status==200;checks.append({'crop':c['id'],'kind':'concept','url':url,'http_status':r.status})
(O/'browser/http-links.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print('HTTP links passed',len(checks))
