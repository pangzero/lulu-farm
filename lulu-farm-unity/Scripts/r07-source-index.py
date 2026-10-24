#!/usr/bin/env python3
"""Index this execution lane for review; no edits to source or accepted inputs."""
import datetime
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'Evidence/r07/D7'
out.mkdir(parents=True, exist_ok=True)
edited = [
    'Assets/Farm/Editor/FarmProjectBuilder.cs',
    'Assets/Farm/Editor/FarmLandscapePolish.cs',
]
patterns = [
    'Assets/Farm/Editor/*R07.cs',
    'Assets/Farm/Editor/FarmDecorScatter.cs',
    'Assets/Farm/Scripts/Runtime/*R07.cs',
    'Assets/Farm/Shaders/FarmGround-r03.shader',
    'Assets/Farm/Shaders/FarmLivingSurface-r07.shader',
    'Assets/Farm/Audio/R07/*',
    'Scripts/r07-*',
]
paths = {root / p for p in edited}
for pattern in patterns:
    paths.update(p for p in root.glob(pattern) if p.is_file())
for p in tuple(paths):
    meta = p.with_name(p.name + '.meta')
    if meta.is_file():
        paths.add(meta)
records = []
for p in sorted(paths):
    rel = str(p.relative_to(root))
    records.append({
        'file': rel,
        'classification': 'edited_existing_builder' if rel in edited else 'new_r07_file_or_meta',
        'bytes': p.stat().st_size,
        'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    })
record = {
    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'DeepSeek continuation D5-D6; inherited D1 has its own changed-files list',
    'defaultBuilderTask': 'D6',
    'sceneRevision': 'integration-r07-D6',
    'generatedOutputs': [
        'Assets/Farm/Scenes/FarmWorld.unity',
        'Assets/Farm/Settings/',
        'Assets/Farm/GeneratedR07/',
    ],
    'note': 'Generated scene/settings/assets are Builder outputs. Do not hand-edit the scene. All reports and evidence remain under Evidence/r07; no acceptance claim.',
    'files': records,
}
(out / 'source-files.json').write_text(json.dumps(record, indent=2))
print(len(records), 'authored files and metadata indexed')
