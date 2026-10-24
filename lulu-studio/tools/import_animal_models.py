"""Copy the user's Meshy animal downloads without rewriting their GLBs."""
from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import json
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
# Stable game asset IDs; original download names remain in the manifest.
ASSETS = [
    ('cow', 'A06', '牛', '牛', '#e4e6e0', '#70796a', 'Meshy_AI_stylized_cow_model_1016172107_image-to-3d-texture.glb'),
    ('sheep', 'A03', '绵羊', '羊', '#f0e6d4', '#a59571', 'Meshy_AI_stylized_sheep_model_1016172124_image-to-3d-texture.glb'),
    ('duck', 'A07', '小鸭', '鸭', '#faecc1', '#c59b33', 'Meshy_AI_stylized_duck_model_1016172118_image-to-3d-texture.glb'),
    ('chicken', 'A01', '鸡', '鸡', '#f8dfbc', '#c98739', 'Meshy_AI_Chicken_1016182344_image-to-3d-texture.glb'),
    ('pig', 'A02', '粉猪', '猪', '#f7d9d7', '#bf817d', 'Meshy_AI_Pig_1016182334_image-to-3d-texture.glb'),
    ('alpaca', 'A04', '羊驼', '驼', '#f0e5d1', '#a28e69', 'Meshy_AI_Alpaca_1016182352_image-to-3d-texture.glb'),
    ('hamster', 'A05', '仓鼠', '鼠', '#f4dfba', '#b78e4c', 'Meshy_AI_Hamster_1016182402_image-to-3d-texture.glb'),
    ('donkey', 'A09', '驴', '驴', '#e0e1df', '#81867b', 'Meshy_AI_Donkey_1016183357_image-to-3d-texture.glb'),
    ('capybara', 'A10', '普通水豚', '豚', '#edd7b9', '#ac8451', 'Meshy_AI_Capybara_1016183318_image-to-3d-texture.glb'),
    ('ostrich', 'A11', '鸵鸟', '鸵', '#e9dfdf', '#917b7b', 'Meshy_AI_Ostrich_1016183344_image-to-3d-texture.glb'),
    ('pony', 'A12', '小马', '马', '#e9d2bc', '#a57c55', 'Meshy_AI_Horse_1016183350_image-to-3d-texture.glb'),
    ('goat', 'A14', '山羊', '羊', '#e4e2da', '#89826d', 'Meshy_AI_Goat_1017004011_image-to-3d-texture.glb'),
    ('goose', 'A13', '白鹅', '鹅', '#f1ebda', '#a59a72', 'Meshy_AI_Duck_1017004003_image-to-3d-texture.glb'),
    ('black-pig', 'A16', '黑猪', '猪', '#dddedf', '#74777d', 'Meshy_AI_Pig_1017003928_image-to-3d-texture.glb'),
    ('deer', 'A15', '小鹿', '鹿', '#f0d9bf', '#b18656', 'Meshy_AI_Deer_1017003854_image-to-3d-texture.glb'),
]


def inspect_glb(data):
    magic, version, length = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or length != len(data):
        raise ValueError('Invalid GLB header or length')
    offset, doc, binary_length = 12, None, 0
    while offset < len(data):
        size, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if offset + size > len(data):
            raise ValueError('GLB chunk exceeds file')
        if kind == 0x4E4F534A:
            doc = json.loads(data[offset:offset+size])
        elif kind == 0x004E4942:
            binary_length += size
        offset += size
    if doc is None:
        raise ValueError('No glTF JSON')
    if any('uri' in value and not value['uri'].startswith('data:') for key in ('images', 'buffers') for value in doc.get(key, [])):
        raise ValueError('External resources need separate import')
    for view in doc.get('bufferViews', []):
        if view.get('byteOffset', 0) + view['byteLength'] > binary_length:
            raise ValueError('Buffer view exceeds embedded data')
    triangles = 0
    for mesh in doc.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            accessor = primitive.get('indices', primitive['attributes']['POSITION'])
            count = doc['accessors'][accessor]['count']
            mode = primitive.get('mode', 4)
            triangles += count // 3 if mode == 4 else max(0, count - 2) if mode in (5, 6) else 0
    return dict(triangles=triangles, mesh_definitions=len(doc.get('meshes', [])), images=len(doc.get('images', [])), skins=len(doc.get('skins', [])), animations=len(doc.get('animations', [])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', type=Path, default=Path.home()/'Downloads')
    args = parser.parse_args()
    destination = ROOT/'public/models/animals'
    destination.mkdir(parents=True, exist_ok=True)
    # Validate every input and every collision before copying any model.
    prepared = []
    for identity, board_id, name, icon, tint, ink, filename in ASSETS:
        source = args.downloads/filename
        data = source.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        stats = inspect_glb(data)
        target = destination/f'{identity}.glb'
        exists = target.exists()
        if exists and hashlib.sha256(target.read_bytes()).hexdigest() != sha:
            raise ValueError(f'Refusing to replace different existing asset: {target}')
        record = dict(id=identity, board_id=board_id, name=name, icon=icon, tint=tint, ink=ink,
                      file=str(target.relative_to(ROOT)), source_download=str(source), bytes=len(data), sha256=sha,
                      **stats, status='original-unmodified')
        prepared.append((source, target, record, exists))
    backup = ROOT/'review/gallery-import-20261017'
    for relative in ('src/gallery.ts', 'src/gallery.css', 'gallery.html', 'public/models/animals/manifest.json', 'assets-manifest.json'):
        src = ROOT/relative
        dst = backup/relative
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    records, viewer = [], []
    for source, target, record, exists in prepared:
        if not exists:
            shutil.copy2(source, target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Copy verification failed: {target}')
        records.append(record)
        note = 'Meshy 下载原件'
        if record['id'] == 'goose':
            note += ' · 下载名 Duck'
        if record['id'] == 'black-pig':
            note += ' · 独立生成版本'
        viewer.append({key:record[key] for key in ('id', 'name', 'icon', 'tint', 'ink', 'bytes')} | dict(url='/'+str(target.relative_to(ROOT/'public')), version=record['sha256'][:8], source=source.name, note=note))
        print(('verified existing' if exists else 'copied new'), record['id'], record['bytes'], record['sha256'][:12])
    manifest = dict(imported_on=datetime.now().date().isoformat(), viewer='gallery.html', models=records)
    (destination/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    main_manifest_path = ROOT/'assets-manifest.json'
    main_manifest = json.loads(main_manifest_path.read_text())
    main_manifest['animal_models'] = records
    main_manifest_path.write_text(json.dumps(main_manifest, ensure_ascii=False, indent=2)+'\n')
    (ROOT/'src/animal-catalog.ts').write_text('// Generated by tools/import_animal_models.py from the imported asset manifest.\nexport const animalCatalog = '+json.dumps(viewer, ensure_ascii=False, indent=2)+';\n')
    print(f"Imported {sum(not row[3] for row in prepared)} new; verified {sum(row[3] for row in prepared)} existing; total {len(records)} animal models.")


if __name__ == '__main__':
    main()
