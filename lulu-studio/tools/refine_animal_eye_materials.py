"""Create a reversible cow-eye material study; preserve vertices and texture bytes.

Image files are decoded only for classification. No texture is painted,
resampled or re-encoded. Existing triangles get a separate eye material.
"""
from pathlib import Path
import copy
import hashlib
import io
import json
import shutil
import struct
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT/'review/animal-eye-materials-20261017'
OUTPUT = ROOT/'public/models/animal-studies'


def hull_2d(points):
    points = sorted(set(map(tuple, points.tolist())))
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower, upper = [], []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return np.asarray(lower[:-1]+upper[:-1])


def inside_hull(points, hull):
    result = np.ones(len(points), dtype=bool)
    for a, b in zip(hull, np.roll(hull, -1, axis=0)):
        result &= (b[0]-a[0])*(points[:, 1]-a[1])-(b[1]-a[1])*(points[:, 0]-a[0]) >= -1e-9
    return result


def main():
    source = ROOT/'public/models/animals/cow.glb'
    raw = source.read_bytes()
    source_hash = hashlib.sha256(raw).hexdigest()
    expected = next(m for m in json.loads((ROOT/'public/models/animals/manifest.json').read_text())['models'] if m['id']=='cow')
    assert source_hash == expected['sha256']
    REVIEW.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for relative in ('public/models/animals/cow.glb', 'src/gallery.ts', 'gallery.html', 'src/gallery.css'):
        src, dst = ROOT/relative, REVIEW/'baseline'/relative
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    json_length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+json_length])
    binary_length = struct.unpack_from('<I', raw, 20+json_length)[0]
    binary = raw[28+json_length:28+json_length+binary_length]
    original_doc = copy.deepcopy(doc)
    def accessor(index):
        a = doc['accessors'][index]
        v = doc['bufferViews'][a['bufferView']]
        dtype = {5126:'<f4', 5125:'<u4', 5123:'<u2'}[a['componentType']]
        width = {'VEC3':3, 'VEC2':2, 'SCALAR':1}[a['type']]
        step = np.dtype(dtype).itemsize
        return np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
                          offset=v.get('byteOffset', 0)+a.get('byteOffset', 0),
                          strides=(v.get('byteStride', step*width), step))
    primitive = doc['meshes'][0]['primitives'][0]
    positions = accessor(primitive['attributes']['POSITION'])
    uv = accessor(primitive['attributes']['TEXCOORD_0'])
    indices = accessor(primitive['indices']).reshape(-1, 3)
    material = doc['materials'][primitive['material']]
    image_index = doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    image_view = doc['bufferViews'][doc['images'][image_index]['bufferView']]
    offset = image_view.get('byteOffset', 0)
    colors = np.asarray(Image.open(io.BytesIO(binary[offset:offset+image_view['byteLength']])).convert('RGB'))
    height, width = colors.shape[:2]
    texels = colors[np.clip((uv[:, 1]*height).astype(int), 0, height-1), np.clip((uv[:, 0]*width).astype(int), 0, width-1)].astype(int)
    blue = (texels[:, 2]>texels[:, 0]+25)&(texels[:, 2]>texels[:, 1]+5)&(texels[:, 2]>80)&(texels[:, 0]<150)
    centroids = positions[indices].mean(axis=1)
    eye_faces = np.zeros(len(indices), dtype=bool)
    eyes = []
    for sign in (-1, 1):
        seeds = positions[blue & (positions[:, 0]*sign>0)]
        assert len(seeds)>100
        center = seeds.mean(axis=0)
        _, _, basis = np.linalg.svd(seeds-center, full_matrices=False)
        local_seeds = (seeds-center)@basis[:2].T
        hull = hull_2d(local_seeds)
        # The blue iris surrounds the pupil. Its convex footprint includes the
        # pupil and painted catchlight; a small border margin covers sampling.
        hull_center = (hull.min(axis=0)+hull.max(axis=0))/2
        hull = hull_center+(hull-hull_center)*1.055
        projected = (centroids-center)@basis[:2].T
        plane_distance = np.abs((centroids-center)@basis[2])
        selected = inside_hull(projected, hull)&(plane_distance<.014)
        eye_faces |= selected
        eyes.append(dict(side=sign, triangles=int(selected.sum()), center=center.tolist(), min=centroids[selected].min(axis=0).tolist(), max=centroids[selected].max(axis=0).tolist()))
    assert 300 < eye_faces.sum() < 6000
    body_indices = indices[~eye_faces]
    eye_indices = indices[eye_faces]
    # A disjoint partition of the exact original triangle list.
    assert len(body_indices)+len(eye_indices)==len(indices)
    assert all(eye['triangles']>100 for eye in eyes)
    assert np.array_equal(indices[~eye_faces], body_indices)
    assert np.array_equal(indices[eye_faces], eye_indices)
    eye_material = copy.deepcopy(material)
    eye_material['name'] = 'Cow_Eyes_SoftGloss_Study_v1'
    pbr = eye_material['pbrMetallicRoughness']
    pbr.pop('metallicRoughnessTexture', None)
    pbr['metallicFactor'] = 0.0
    pbr['roughnessFactor'] = 0.24
    eye_material['normalTexture']['scale'] = 0.08
    # The painted primary catchlight stays intact. Restrain additional real
    # light reflections instead of replacing the pupil with a broad gray glow.
    eye_material.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor':0.20}
    used = doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_specular' not in used:
        used.append('KHR_materials_specular')
    eye_material_index = len(doc['materials'])
    doc['materials'].append(eye_material)
    payload = bytearray(binary)
    def add_indices(values):
        payload.extend(b'\x00'*((-len(payload))%4))
        start = len(payload)
        encoded = values.astype('<u4').tobytes()
        payload.extend(encoded)
        view_index = len(doc['bufferViews'])
        doc['bufferViews'].append(dict(buffer=0, byteOffset=start, byteLength=len(encoded), target=34963))
        accessor_index = len(doc['accessors'])
        doc['accessors'].append(dict(bufferView=view_index, byteOffset=0, componentType=5125, count=int(values.size), type='SCALAR', min=[int(values.min())], max=[int(values.max())]))
        return accessor_index
    body_primitive, eyes_primitive = copy.deepcopy(primitive), copy.deepcopy(primitive)
    body_primitive['indices'] = add_indices(body_indices)
    eyes_primitive['indices'] = add_indices(eye_indices)
    eyes_primitive['material'] = eye_material_index
    doc['meshes'][0]['primitives'] = [body_primitive, eyes_primitive]
    doc['buffers'][0]['byteLength'] = len(payload)
    doc.setdefault('extras', {})['materialStudy'] = dict(source='cow.glb', sourceSha256=source_hash, scope='iris-pupil material assignment only; unchanged vertices, normals, UVs and texture data')
    assert doc['materials'][0]==original_doc['materials'][0]
    assert doc['images']==original_doc['images'] and doc['textures']==original_doc['textures']
    assert doc['nodes']==original_doc['nodes']
    assert bytes(payload[:len(binary)])==binary
    json_bytes = json.dumps(doc, separators=(',', ':')).encode()
    json_bytes += b' '*((-len(json_bytes))%4)
    payload.extend(b'\x00'*((-len(payload))%4))
    output = struct.pack('<4sII', b'glTF', 2, 12+8+len(json_bytes)+8+len(payload))
    output += struct.pack('<II', len(json_bytes), 0x4E4F534A)+json_bytes
    output += struct.pack('<II', len(payload), 0x004E4942)+payload
    destination = OUTPUT/'cow-eyes-v1.glb'
    initial = REVIEW/'candidates/cow-roughness-only.glb'
    if destination.exists() and not initial.exists():
        initial.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, initial)
    destination.write_bytes(output)
    assert source.read_bytes()==raw
    scale = 2.2/float(positions[:, 1].max()-positions[:, 1].min())
    center_xz = (positions.max(axis=0)+positions.min(axis=0))/2
    def normalized(point):
        return [(point[0]-center_xz[0])*scale, (point[1]-positions[:, 1].min())*scale, (point[2]-center_xz[2])*scale]
    low = np.min([e['min'] for e in eyes], axis=0)
    high = np.max([e['max'] for e in eyes], axis=0)
    focus_low = normalized(low-np.array([.08, .09, .10]))
    focus_high = normalized(high+np.array([.08, .09, .06]))
    record = dict(id='cow-eyes-v1', source='public/models/animals/cow.glb', source_sha256=source_hash,
                  file=str(destination.relative_to(ROOT)), url='/models/animal-studies/cow-eyes-v1.glb',
                  bytes=len(output), version=hashlib.sha256(output).hexdigest()[:8], sha256=hashlib.sha256(output).hexdigest(),
                  eye_roughness=.24, eye_normal_scale=.08, eye_specular_factor=.20, triangles=int(len(indices)), eye_triangles=int(eye_faces.sum()),
                  vertices_unchanged=True, original_binary_prefix_unchanged=True, texture_bytes_unchanged=True,
                  body_material_unchanged=True, eyes=eyes, focus_box=[focus_low,focus_high], status='material-study-pending-user-review')
    (OUTPUT/'manifest.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    (ROOT/'src/animal-eye-study.ts').write_text('// Generated by tools/refine_animal_eye_materials.py.\nexport const cowEyeStudy = '+json.dumps(record, ensure_ascii=False, indent=2)+';\n')
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
