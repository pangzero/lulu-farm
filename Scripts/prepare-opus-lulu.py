#!/usr/bin/env python3
"""Prepare an independent working copy of the existing Opus O1 tools and inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path,
                        help='New, empty working directory; preserved sources are never edited.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = args.workspace.expanduser().resolve()
    preserved = [root / 'lulu-studio/review', root / 'lulu-studio/public',
                 root / 'lulu-farm-unity/Assets', root / 'lulu-farm-unity/Delivery']
    if any(work == p or p in work.parents for p in preserved):
        parser.error('Use an independent working directory outside preserved asset folders.')
    if work.exists() and any(work.iterdir()):
        parser.error('Workspace must be empty or nonexistent.')
    manifest = json.loads((root / 'lulu-farm-unity/Docs/R07-LULU-WIP-REMOTE-MANIFEST.json').read_text())
    for entry in manifest['files']:
        p = root / entry['path']
        if not p.is_file():
            parser.error(f'Missing input: {p}; run git lfs pull.')
        if hashlib.sha256(p.read_bytes()).hexdigest() != entry['sha256']:
            parser.error(f'Hash mismatch: {p}; preserve local edits and check Git/LFS state.')
    missing = [name for name in ('numpy', 'scipy', 'PIL') if importlib.util.find_spec(name) is None]
    if missing:
        parser.error('Install Scripts/requirements-opus-lulu.txt in a Python environment: ' + ', '.join(missing))
    compiler = shutil.which('c++') or shutil.which('g++') or shutil.which('clang++')
    if not compiler:
        parser.error('A C++ compiler is required to build the preserved QEM source.')
    work.mkdir(parents=True, exist_ok=True)
    tools = root / 'lulu-studio/review/lulu-game-r01/tools'
    for source in sorted(tools.iterdir()):
        if source.suffix in ('.py', '.cpp', '.h'):
            shutil.copy2(source, work / source.name)
    # The archived render script has this workstation's old absolute path.
    # Adapt only the disposable copy, keeping the archived source byte-identical.
    render = work / 'render_lulu.py'
    text = render.read_text()
    text = text.replace("STUDIO = '/Users/haowen/IdeaProjects/farm-game/lulu-studio/public'",
                        'STUDIO = ' + repr(str(root / 'lulu-studio/public')))
    render.write_text(text)
    inputs = {
        'new.glb': root / 'lulu-studio/review/lulu-hybrid-color-20261023/shorts-r01/lulu-colored.glb',
        'master.glb': root / 'lulu-studio/public/models/unity-lulu/locomotion-r08/lulu-locomotion-master.glb',
        'body-wrap-basecolor.png': root / 'lulu-studio/review/lulu-hybrid-color-20261023/shorts-r01/body-wrap-basecolor.png',
    }
    for name, source in inputs.items():
        shutil.copy2(source, work / name)
    (work / 'qem').mkdir(exist_ok=True)
    subprocess.run([compiler, '-std=c++17', '-O2', str(work / 'qem.cpp'),
                    '-o', str(work / 'qem/qem')], check=True, cwd=work)
    result = {'workspace': str(work), 'root': str(root), 'verifiedFiles': len(manifest['files']),
              'compiledQem': True, 'sourceFilesModified': False,
              'note': 'Preparation only. No new model built and no art/animation acceptance implied.'}
    (work / 'preparation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print('Continue from HANDOFF.md and the existing lulu-game-lod0-wip.glb; avoid regenerating completed work.')


if __name__ == '__main__':
    main()
