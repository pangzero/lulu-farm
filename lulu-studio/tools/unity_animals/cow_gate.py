import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender'
for variant in ['source','lod0']:
 log=R/'review/unity-integration-20261018/animals'/('cow-'+variant+'-gate.log')
 with log.open('w') as f:subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_animals/review.py'),'--','cow',variant,'quick'],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
 print('DONE',variant,flush=True)
