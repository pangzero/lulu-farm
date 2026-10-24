import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets'
for k in ['strawberry-mature','pumpkin-mature','E16']:
 with (O/(k+'-surface-lod1.log')).open('w') as log:r=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_assets/process_conservative.py'),'--','--id',k,'--version','surface-lod1-r01','--review','all'],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 print(k,r.returncode,flush=True)
