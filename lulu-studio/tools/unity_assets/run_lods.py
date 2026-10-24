import subprocess,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';O=R/'review/unity-integration-20261018/assets';registry=json.loads((R/'public/models/unity-integration/manifest.json').read_text())
for row in registry['assets']:
 if row['stage']!='seedling':continue
 key=row['id'];v='lod1-r01';target=6000 if row['species'] in ['cabbage','bokchoy','cauliflower','lettuce'] else 2300
 if (O/key/v/'metrics.json').exists():continue
 with (O/(key+'-'+v+'.log')).open('w') as log:rc=subprocess.run([B,'-b','-t','3','--python',str(R/'tools/unity_assets/process_bvh.py'),'--','--id',key,'--version',v,'--target',str(target),'--resolution','1024','--review','all'],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 p=O/key/v/'metrics.json';print('LOD',key,'complete' if p.exists() else rc,flush=True)
