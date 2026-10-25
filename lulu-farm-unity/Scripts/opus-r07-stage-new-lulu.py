#!/usr/bin/env python3
"""O9: copy the new Lulu (lulu-game-r01 LOD0 WIP) into the Unity project for the O9 stage, without touching the
registered Lulu (locomotion-r08) or running ConfigureAndImport.

Writes Assets/Farm/Art/Lulu-game-r01/model.glb (+ .meta with the same glTFast import settings as Art/Lulu/model.gltf:
node names kept, Mecanim clips). Run once before `r07-run-editor.py O9 generate`. Idempotent; refuses to overwrite a
different file. The copy is a generated input (the source stays in lulu-studio/review and is the reference).
"""
import hashlib, json, pathlib, shutil, sys

root = pathlib.Path(__file__).resolve().parents[1]
source = root.parent / 'lulu-studio/review/lulu-game-r01/lulu-game-lod0-wip.glb'
expected = '50f4a16bbf394f2c1320afb005f9f2a5e2da0b4466d1ea2f8ef2ed02677c1acc'
folder = root / 'Assets/Farm/Art/Lulu-game-r01'
target = folder / 'model.glb'
FOLDER_META = 'fileFormatVersion: 2\nguid: 7c1e2a90b4d34f6e9a51c0d8e2f4b613\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n'
GLB_META = '''fileFormatVersion: 2
guid: 3b8f0d6c2a5e4f1d9c7b6a5e4d3c2b10
ScriptedImporter:
  internalIDToNameTable: []
  externalObjects: {}
  serializedVersion: 2
  userData: 
  assetBundleName: 
  assetBundleVariant: 
  script: {fileID: 11500000, guid: 715df9372183c47e389bb6e19fbc3b52, type: 3}
  editorImportSettings:
    generateSecondaryUVSet: 0
  importSettings:
    nodeNameMethod: 1
    animationMethod: 2
    generateMipMaps: 1
    texturesReadable: 0
    defaultMinFilterMode: 9729
    defaultMagFilterMode: 9729
    anisotropicFilterLevel: 1
  instantiationSettings:
    mask: -1
    layer: 0
    skinUpdateWhenOffscreen: 1
    lightIntensityFactor: 1
    sceneObjectCreation: 2
'''
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

if not source.exists() or source.read_bytes()[:4] != b'glTF':
    sys.exit('Source missing or still an LFS pointer (run git lfs pull): ' + str(source))
if sha(source) != expected:
    sys.exit('Source SHA256 differs from the reviewed WIP: ' + sha(source))
folder.mkdir(parents=True, exist_ok=True)
if target.exists() and sha(target) != expected:
    sys.exit('Refusing to overwrite a different ' + str(target))
if not target.exists(): shutil.copy2(source, target)
for path, text in [(folder.with_suffix('.meta'), FOLDER_META), (target.with_name('model.glb.meta'), GLB_META)]:
    if path.exists() and path.read_text() != text: sys.exit('Refusing to overwrite a different ' + str(path))
    path.write_text(text)
out = root / 'Evidence/r07/O9'; out.mkdir(parents=True, exist_ok=True)
(out / 'new-lulu-staging.json').write_text(json.dumps({'source': str(source.relative_to(root.parent)), 'sha256': expected,
    'target': str(target.relative_to(root)), 'note': 'Copy of lulu-game-r01 LOD0 WIP for O9; registered Lulu (locomotion-r08) unchanged'}, indent=2))
print('Staged', target, expected)
