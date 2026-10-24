import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets'
plan=[('cabbage',6500),('tomato',11000),('corn',7500),('cucumber',9000),('sunflower',8500),('wheat',6500),('bokchoy',6500),('watermelon',6500),('tulip',5000),('rose',16000),('lettuce',18000),('cauliflower',20000),('strawberry',24000),('pumpkin',6500)]
for species,target in plan:
 key=species+'-mature';v='atlas-local-lod1-r01' if species=='pumpkin' else 'atlas-lod1-r01'
 if (O/key/v/'metrics.json').exists():continue
 res=1024
 with (O/(key+'-'+v+'.log')).open('w') as log:rc=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_assets/process_bvh.py'),'--','--id',key,'--version',v,'--target',str(target),'--resolution',str(res),'--review','all'],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 print('MATURE_LOD',key,rc,flush=True)
