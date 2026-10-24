#!/usr/bin/env python3
"""Compare staged glTF payloads against selected GLBs; this is not Unity import acceptance."""
import datetime
import hashlib
import json
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_glb(path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    assert magic == 0x46546C67 and version == 2 and length == len(raw), 'Invalid GLB header'
    chunks = {}
    cursor = 12
    while cursor < len(raw):
        size, kind = struct.unpack_from('<II', raw, cursor)
        cursor += 8
        chunks[kind] = raw[cursor:cursor + size]
        cursor += size
    return json.loads(chunks[0x4E4F534A]), chunks[0x004E4942], raw


def view_bytes(doc, blob, index):
    view = doc['bufferViews'][index]
    start = view.get('byteOffset', 0)
    end = start + view['byteLength']
    assert view.get('buffer', 0) == 0 and end <= len(blob), 'Invalid buffer view'
    return blob[start:end]


def audit(record):
    source = pathlib.Path(record['source'])
    assert digest(source.read_bytes()) == record['sourceSHA256'], 'Protected source hash changed'
    original, original_bin, original_raw = read_glb(pathlib.Path(record['importSource']))
    assert digest(original_raw) == record['importSHA256'], 'Selected import hash changed'
    staged_path = ROOT / record['path']
    staged = json.loads(staged_path.read_text())
    staged_bin = (staged_path.parent / staged['buffers'][0]['uri']).read_bytes()
    image_views = {image['bufferView'] for image in original.get('images', [])}
    assert len(original.get('bufferViews', [])) == len(staged.get('bufferViews', [])), 'Buffer view count changed'
    geometry_bytes = 0
    for index, _ in enumerate(original.get('bufferViews', [])):
        if index in image_views:
            continue
        expected = view_bytes(original, original_bin, index)
        actual = view_bytes(staged, staged_bin, index)
        assert actual == expected, 'Geometry/animation payload changed at buffer view ' + str(index)
        geometry_bytes += len(actual)
    image_hashes = []
    for index, image in enumerate(original.get('images', [])):
        expected = view_bytes(original, original_bin, image['bufferView'])
        actual = (staged_path.parent / staged['images'][index]['uri']).read_bytes()
        assert expected == actual, 'Image payload changed at index ' + str(index)
        image_hashes.append(digest(actual))
    for key in set(original) | set(staged):
        if key not in ('buffers', 'bufferViews', 'images'):
            assert original.get(key) == staged.get(key), 'Scene/material/skin/animation metadata changed: ' + key
    return {'id': record['id'], 'status': 'exact_payload_preserved',
            'selectedVersion': record['version'], 'sourceSHA256': record['sourceSHA256'],
            'importSHA256': record['importSHA256'], 'geometryAnimationBytes': geometry_bytes,
            'imageSHA256': image_hashes, 'meshCount': len(original.get('meshes', [])),
            'skinCount': len(original.get('skins', [])),
            'animations': [a.get('name', '') for a in original.get('animations', [])],
            'visual': record['visual'], 'unityImport': 'not_verified_by_this_audit'}


def main():
    registry_path = ROOT / 'Assets/Farm/Data/asset-registry.json'
    raw = registry_path.read_bytes()
    registry = json.loads(raw)
    results = []
    for record in registry['assets']:
        try:
            results.append(audit(record))
            for index,lod in enumerate(record.get('lodImports',[])):
                lod_record=dict(record)
                lod_record.update(lod)
                lod_record['id']=record['id']+'/LOD'+str(index+1)
                results.append(audit(lod_record))
        except Exception as error:
            results.append({'id': record['id'], 'status': 'failed', 'reason': str(error)})
    ids = [record['id'] for record in registry['assets']]
    checks = {'uniqueIds': len(ids) == len(set(ids)),
              'deferredAbsent': all(item not in ids for item in ('S02', 'C12', 'C16', 'zucchini-mature', 'zucchini-seedling', 'scallion-mature', 'scallion-seedling'))}
    success = all(r['status'] == 'exact_payload_preserved' for r in results) and all(checks.values())
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'registrySHA256': digest(raw), 'status': 'staging_payload_pass' if success else 'staging_payload_failure',
              'scope': 'GLB-to-glTF conversion only; no Unity import, rendering, runtime or device acceptance',
              'checks': checks, 'assets': results}
    output = ROOT / 'Preflight/staging-audit.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(report['status'], len(results), 'assets;', output)
    for result in results:
        if result['status'] == 'failed':
            print(result['id'], result['reason'])
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
