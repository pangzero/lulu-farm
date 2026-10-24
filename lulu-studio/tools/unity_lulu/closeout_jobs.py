import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';jobs=[('legs_only_closeout.py',['game-lod1']),('legs_only_closeout.py',['locomotion-master']),('readback_r08.py',[]),('review_r08.py',['full','game-lod0']),('review_r08.py',['full','game-lod1']),('review_r08.py',['full','locomotion-master']),('wardrobe_review_r08.py',[]),('motion_preview_r08.py',[])]
for script,args in jobs:
 with (R/'review/unity-integration-20261018/lulu'/('r08-'+script+'-'+('-'.join(args) or 'default')+'.log')).open('w') as f:
  result=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_lulu'/script),'--',*args],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 if result.returncode:raise SystemExit(str((script,args,result.returncode)))
 print('DONE',script,args,flush=True)
