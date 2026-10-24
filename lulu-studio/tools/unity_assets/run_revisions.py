import subprocess,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets'
for key,v in [('S01','bvh-r03'),('cabbage-mature','bvh-r02'),('tomato-mature','bvh-r02')]:
 with (O/(key+'-'+v+'.log')).open('w') as log:rc=subprocess.run([B,'-b','-t','4','--python',str(R/'tools/unity_assets/process_bvh.py'),'--','--id',key,'--version',v,'--review','all'],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 p=O/key/v/'metrics.json';print('REVISION',key,v,'complete' if p.exists() else rc,flush=True)
