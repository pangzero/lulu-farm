import subprocess,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';animals=[a['id'] for a in json.loads((R/'public/models/unity-integration/manifest.json').read_text())['assets'] if a['type']=='animal'];progress=R/'review/unity-integration-20261018/animals/batch-progress.json';done=[]
for aid in animals:
 for variant in ['lod0','lod1']:
  expected=R/'public/models/unity-animals/game-r03'/aid/(variant+'-manifest.json')
  tasks=[]
  if not expected.exists():tasks.append(('build.py',[aid,variant]))
  tasks.extend([('readback.py',[aid,variant]),('review.py',[aid,variant,'full'])])
  if variant=='lod0':tasks.append(('review.py',[aid,'source','full']))
  for script,args in tasks:
   log=R/'review/unity-integration-20261018/animals'/('r03-'+aid+'-'+variant+'-'+script+'-'+args[1]+'.log')
   with log.open('w') as f:result=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_animals'/script),'--',*args],cwd=R,stdout=f,stderr=subprocess.STDOUT)
   data=log.read_text()
   if result.returncode or 'Traceback (most recent call last)' in data:raise SystemExit('FAILED '+str((aid,script,args)))
   done.append({'asset':aid,'variant':variant,'task':script,'args':args});progress.write_text(json.dumps({'done':done,'current':aid,'time':time.time()},indent=2));print('DONE',aid,variant,script,args,flush=True)
