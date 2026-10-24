import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets'
for key,target,version in [('pumpkin-mature',10000,'atlas-local-r01'),('lettuce-mature',30000,'atlas-detail-r01'),('cauliflower-mature',32000,'atlas-detail-r01'),('strawberry-mature',36000,'atlas-detail-r01')]:
 with (O/(key+'-'+version+'.log')).open('w') as log:r=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_assets/process_bvh.py'),'--','--id',key,'--version',version,'--target',str(target),'--review','all'],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 print('DETAIL',key,r.returncode,flush=True)
