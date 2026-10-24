"""Make a neutral display derivative of color-r03; never alter source geometry."""
from pathlib import Path
import copy
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'review/lulu-hybrid-color-20261023'
OUT = STUDY / 'handoff'
OUT.mkdir(exist_ok=True)
SOURCE = STUDY / 'color-r03/lulu-colored.glb'
data = SOURCE.read_bytes()
source_sha = hashlib.sha256(data).hexdigest()
json_len, chunk_type = struct.unpack_from('<II', data, 12)
assert chunk_type == 0x4E4F534A
original = json.loads(data[20:20 + json_len])
doc = copy.deepcopy(original)
gray_index = len(doc['materials'])
doc['materials'].append({
    'name': 'Handoff neutral gray - no texture or normal map',
    'pbrMetallicRoughness': {
        'baseColorFactor': [.47, .47, .47, 1],
        'metallicFactor': 0,
        'roughnessFactor': .85,
    },
    'doubleSided': True,
})
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        prim['material'] = gray_index
        # glTF multiplies COLOR_0 into every base color. Disable only its use;
        # the original data remains untouched in the embedded buffer.
        prim['attributes'].pop('COLOR_0', None)
assert doc['nodes'] == original['nodes']
for old_mesh, new_mesh in zip(original['meshes'], doc['meshes']):
    assert len(old_mesh['primitives']) == len(new_mesh['primitives'])
    for old, new in zip(old_mesh['primitives'], new_mesh['primitives']):
        expected = copy.deepcopy(old)
        expected['material'] = gray_index
        expected['attributes'].pop('COLOR_0', None)
        assert new == expected
j = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
j += b' ' * (-len(j) % 4)
remaining_chunks = data[20 + json_len:]
packed = struct.pack('<III', 0x46546C67, 2, 20 + len(j) + len(remaining_chunks))
packed += struct.pack('<II', len(j), 0x4E4F534A) + j + remaining_chunks
target = OUT / 'lulu-color-r03-neutral-gray.glb'
target.write_bytes(packed)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha
record = {
    'source': str(SOURCE),
    'source_sha256': source_sha,
    'gray_glb': str(target),
    'gray_sha256': hashlib.sha256(packed).hexdigest(),
    'original_binary_chunks_identical': True,
    'all_mesh_indices_positions_normals_uvs_transforms_identical': True,
    'change': 'Assign neutral material, disable vertex color use; no mesh edit',
    'mesh_objects': len(doc['meshes']),
    'triangles': sum(doc['accessors'][p['indices']]['count'] // 3
                     for m in doc['meshes'] for p in m['primitives']),
}
(OUT / 'gray-preservation.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(record, ensure_ascii=False, indent=2))
