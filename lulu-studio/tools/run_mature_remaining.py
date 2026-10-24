"""Bounded Blender processes; logs per crop, no source overwrite/retries."""
from pathlib import Path
import json,subprocess,sys,concurrent.futures,time,os
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018';B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender'
phase=sys.argv[1];slugs=sys.argv[2:] or [x['id'] for x in json.loads((O/'scope.json').read_text())]
def run(slug):
 if phase=='build':jobs=[('toon','toon-r01','quick'),('original','original','quick'),('game','game-r01','quick')]
 elif phase=='full':jobs=[('inspect','toon-r01','all'),('original','original','all'),('inspect','game-r01','all'),('plant','toon-r01','none'),('plant','game-r01','none')]
 elif phase=='detail':jobs=[('original','original','detail'),('inspect','toon-r01','detail'),('inspect','game-r01','detail')]
 else:raise ValueError(phase)
 for mode,v,render in jobs:
  folder=O/slug;folder.mkdir(exist_ok=True);log=folder/f'{phase}-{mode}-{v}.log'
  command=[B,'--background','--threads','4','--python',str(R/'tools/build_mature_remaining.py'),'--','--crop',slug,'--mode',mode,'--version',v,'--render',render]
  with log.open('w') as f:q=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
  if q.returncode or 'COMPLETE '+slug not in log.read_text():print('FAILED',slug,mode,q.returncode,str(log),flush=True);return False
  print('DONE',slug,mode,v,flush=True)
 return True
with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("MATURE_WORKERS",2))) as ex:
 results=list(ex.map(run,slugs))
print('PHASE_RESULT',phase,sum(results),len(results),flush=True)
if not all(results):sys.exit(1)
