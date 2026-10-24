from pathlib import Path
import json,urllib.request
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018';m=json.loads((R/'public/models/crop-two-stage/manifest.json').read_text());checks=[];seen=set()
for c in m['crops']:
 for v in ['meshy-original',c['defaultSeedlingVersion']]:
  for k in ['file','source']:
   url=c['seedling'][v].get(k)
   if not url or url in seen:continue
   seen.add(url);p=R/'public'/url.lstrip('/');req=urllib.request.Request('http://127.0.0.1:5173'+urllib.parse.quote(url),method='HEAD')
   with urllib.request.urlopen(req,timeout=20) as r:status=r.status;size=int(r.headers['Content-Length'])
   assert status==200 and size==p.stat().st_size;checks.append({'url':url,'status':status,'bytes':size,'size_matches':True})
(O/'browser/http-links.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print('Unique model/source URLs passed',len(checks))
