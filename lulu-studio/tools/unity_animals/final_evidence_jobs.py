import subprocess,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];B='/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender';animals=[a['id'] for a in json.loads((R/'public/models/unity-integration/manifest.json').read_text())['assets'] if a['type']=='animal']
for aid in animals:
 if (R/'review/unity-integration-20261018/animals/game-r04'/aid/'topology.json').exists():continue
 if not (R/'assets-source/unity-animals/game-r04'/aid/'lod1.blend').exists():continue
 log=R/'review/unity-integration-20261018/animals'/('r04-'+aid+'-topology.log')
 with log.open('w') as f:subprocess.run([B,'-b','-t','2','--python',str(R/'tools/unity_animals/topology.py'),'--',aid],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
 if 'Traceback (most recent call last)' in log.read_text():raise SystemExit('ERROR '+aid)
 print('TOPOLOGY',aid,flush=True)
