from pathlib import Path
import json,subprocess,concurrent.futures,sys
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018';phase=sys.argv[1];ids=sys.argv[2:] or [c['id'] for c in json.loads((O/'mapping.json').read_text())]
def run(token):
 s,version=(token.split('@',1)+['meshy-toon-r01'])[:2] if '@' in token else (token,'meshy-toon-r01')
 log=O/s/f'{phase}-{version}.log';log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('w') as f:p=subprocess.run(['/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender','--background','--threads','4','--python',str(R/'tools/build_seedling_mapping.py'),'--','--crop',s,'--phase',phase,'--version',version],stdout=f,stderr=subprocess.STDOUT)
 ok=p.returncode==0 and f'COMPLETE_{phase.upper()} {s}' in log.read_text();print('DONE' if ok else 'FAILED',phase,s,flush=True);return ok
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:rs=list(ex.map(run,ids))
print('RESULT',phase,sum(rs),len(rs),flush=True)
if not all(rs):sys.exit(1)
