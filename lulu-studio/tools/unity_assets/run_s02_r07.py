"""r07 D1: S02 pasture barn game derivatives.

Same route as run_atlas.py / run_facility_lods.py (both delegate to process_bvh.py),
but written as a separate runner so the S01-era runners keep their original asset
plans. S02 only: atlas-r01 (LOD0) and atlas-lod1-r01 (LOD1).

Texture budget: task cap is 2K, so LOD0 uses 2048 and LOD1 uses 1024 (S01 atlas used
2048/1024 through the same --resolution argument).
"""
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[2]
B = '/Users/haowen/.codex/runtimes/blender/Blender.app/Contents/MacOS/Blender'
O = R / 'review/unity-integration-20261018/assets'
E = R.parent / 'lulu-farm-unity/Evidence/r07/D1'

JOBS = [
    ('atlas-r01', 38000, 2048),
    ('atlas-lod1-r01', 11500, 1024),
]

E.mkdir(parents=True, exist_ok=True)
for version, target, resolution in JOBS:
    if (O / 'S02' / version / 'metrics.json').exists():
        print('SKIP', version, 'metrics exist', flush=True)
        continue
    log = E / ('S02-' + version + '.log')
    with log.open('w') as fh:
        rc = subprocess.run(
            [B, '-b', '-t', '3', '--python',
             str(R / 'tools/unity_assets/process_bvh.py'), '--',
             '--id', 'S02', '--version', version,
             '--target', str(target), '--resolution', str(resolution),
             '--review', 'all'],
            cwd=R, stdout=fh, stderr=subprocess.STDOUT).returncode
    ok = (O / 'S02' / version / 'metrics.json').exists()
    print('S02', version, 'complete' if ok else 'FAILED rc=%s' % rc, flush=True)
