import subprocess,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets'
for key in sys.argv[1:]:
 v='atlas-r01'
 if (O/key/v/'metrics.json').exists():continue
 with (O/(key+'-'+v+'.log')).open('w') as log:rc=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_assets/process_bvh.py'),'--','--id',key,'--version',v,'--review','all'],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 p=O/key/v/'metrics.json';print('ATLAS',key,'complete' if p.exists() else rc,flush=True)
