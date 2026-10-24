#!/usr/bin/env python3
"""Archive the reproducible project, without caches or rendered evidence frames."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1]).resolve()
if output.exists():
    raise SystemExit('Refusing to overwrite an existing delivery')
output.parent.mkdir(parents=True, exist_ok=True)
members = []
for name in ['Assets', 'Packages', 'ProjectSettings', 'Tools', 'Scripts', 'Docs', 'Preflight']:
    members.extend(p for p in (root / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != '.DS_Store')
members.extend(root / name for name in ['README.md', 'AGENTS.md'])
manifest = []
with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(members):
        rel = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        manifest.append({'path': rel, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
        archive.write(path, 'lulu-farm-unity/' + rel)
    archive.writestr('lulu-farm-unity/SOURCE-SNAPSHOT.json', json.dumps(manifest, indent=2))
with zipfile.ZipFile(output) as archive:
    for row in manifest:
        payload = archive.read('lulu-farm-unity/' + row['path'])
        if hashlib.sha256(payload).hexdigest() != row['sha256']:
            raise SystemExit('Archived member mismatch: ' + row['path'])
result = {'archive': str(output), 'files': len(manifest), 'source_bytes': sum(x['bytes'] for x in manifest),
          'archive_bytes': output.stat().st_size, 'sha256': hashlib.file_digest(output.open('rb'), 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(output.read_bytes()).hexdigest(),
          'every_member_readback_sha256': 'pass', 'unity_reimport_from_extracted_archive': 'not_repeated; same source bytes as built project',
          'native_blender_sources': 'retained in sibling lulu-studio; see Docs/ASSET-INTEGRATION-STATUS-20261023.md',
          'evidence': 'separate delivery evidence archive; raw framebuffer sequences remain in workspace'}
output.with_suffix('.manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
