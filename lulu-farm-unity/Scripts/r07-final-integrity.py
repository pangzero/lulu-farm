#!/usr/bin/env python3
"""Read-only verification of protected inputs; run after performance capture, not during it."""
import datetime, hashlib, json, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
import sys
# Default keeps the delivered D7 location; O6 passes its own folder so D7 evidence is not overwritten.
out=root/'Evidence/r07'/(sys.argv[1] if len(sys.argv)>1 else 'D7')
out.mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
baseline=load(root/'Evidence/r07/preflight-20261024/preservation.json')
records=[]
def verify(path,expected,category):
    p=pathlib.Path(path);actual=sha(p) if p.is_file() else None
    records.append({'file':str(p),'category':category,'expected':expected,'actual':actual,'identical':actual==expected})
for entry in baseline['delivery']:
    verify(root/'Delivery/r06-20261023'/entry['file'],entry['expected'],'r06-delivery')
verify(baseline['barn']['path'],baseline['barn']['expected'],'S02-original')
for file,expected in baseline['locks'].items():verify(file,expected,'locked-packages')
for file,expected in load(root/'Evidence/r07/D5/before/protected-lulu.json').items():verify(root/file,expected,'frozen-Lulu')
for entry in load(root/'Evidence/r07/D3/before/road-and-ground-hashes.json'):
    verify(root/entry['file'],entry['sha256'],'retained-road-ground-geometry')
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'actual SHA256 of protected local files; no writes to inputs','checkedFiles':len(records),'changedFiles':[r['file'] for r in records if not r['identical']],'records':records}
(out/'final-integrity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print({'checkedFiles':len(records),'changedFiles':report['changedFiles']})
raise SystemExit(bool(report['changedFiles']))
