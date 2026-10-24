import subprocess,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets'
plan={'S01':35000,'S03':18000,'S04':18000,'S06':4500,'S07':6000,'S08':6500,'S09':4000,'S10':4000,'S11':6500,'S12':3000,'E03':1800,'E04':1500,'E08':3500,'E09':4500,'E10':2500,'E11':4500,'E12':3500,'E14':2800,'E15':3000,'E16':3000}
for key,target in plan.items():
 v='atlas-lod1-r01'
 if (O/key/v/'metrics.json').exists():continue
 with (O/(key+'-'+v+'.log')).open('w') as log:rc=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_assets/process_bvh.py'),'--','--id',key,'--version',v,'--target',str(target),'--resolution','1024' if key in ['S01','S03','S04','S11'] else '512','--review','all'],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 p=O/key/v/'metrics.json';print('FACILITY_LOD',key,'complete' if p.exists() else rc,flush=True)
