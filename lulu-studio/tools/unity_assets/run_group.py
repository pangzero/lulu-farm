import subprocess,sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets'
for key in sys.argv[1:]:
 version='bvh-r01';out=O/key/version
 if (out/'metrics.json').exists():print('EXISTING',key,flush=True);continue
 with (O/(key+'-bvh.log')).open('w') as log:
  cmd=[B,'-b','-t','4','--python',str(R/'tools/unity_assets/process_bvh.py'),'--','--id',key,'--review','all'];rc=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 if (out/'metrics.json').exists():
  m=json.loads((out/'metrics.json').read_text());print('FINISHED',key,m['actual_triangles'],m['geometry'],flush=True)
 else:print('FAILED',key,rc,flush=True)
