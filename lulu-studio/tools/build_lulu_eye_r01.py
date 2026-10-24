"""eye-r01: replace sculpted eye sockets with smooth skin + separate flush eye patches.

Base: color-r03 (unchanged, read-only). Writes review/lulu-hybrid-color-20261023/eye-r01/.
Edits are limited to:
  * Lulu_Head_Mirrored POSITION/NORMAL inside the two eye-socket regions (topology/indices unchanged)
  * head face UV (same front-planar formula, recomputed from the new positions) and head COLOR_0
  * face base-colour / metal-rough textures (painted eyes removed, pixels outside eye areas identical)
  * two new mesh nodes Lulu_Eye_ScreenLeft / Lulu_Eye_ScreenRight with their own textures
All other nodes, meshes, accessors and transforms are left byte-identical; build.json records the checks.
"""
from pathlib import Path
import copy, hashlib, json, struct, sys, importlib.util
import numpy as np

R = Path(__file__).resolve().parents[1]
D = R / 'review/lulu-hybrid-color-20261023'
O = D / 'eye-r01'
spec = importlib.util.spec_from_file_location('clh', R / 'tools/color_lulu_hybrid.py')
clh = importlib.util.module_from_spec(spec); spec.loader.exec_module(clh)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_glb(path, g, b):
    js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
    b = bytearray(b); b += b'\0' * ((-len(b)) % 4)
    g['buffers'][0]['byteLength'] = len(b)
    js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(js) + len(b)) + struct.pack('<II', len(js), 0x4e4f534a) + js + struct.pack('<II', len(b), 0x004e4942) + b)


def build():
    src = D / 'color-r03/lulu-colored.glb'
    src_sha = sha(src)
    assert src_sha == '04eb1816ebf2a7655364a1c5f58c5cd66ef0d7ab0e08f3e537332345d05f3a03', 'color-r03 changed'
    g, b = clh.load(src); orig = copy.deepcopy(g); b0 = bytes(b)
    patch = np.load(O / 'eye-patch.npz')

    def buf(raw):
        b.extend(b'\0' * ((-len(b)) % 4)); i = len(g['bufferViews'])
        g['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(raw)}); b.extend(raw); return i

    def acc(a, typ, component=5126, minmax=False):
        dt = {5126: '<f4', 5125: '<u4'}[component]; a = np.ascontiguousarray(a, dtype=dt); i = len(g['accessors'])
        d = {'bufferView': buf(a.tobytes()), 'componentType': component, 'count': len(a), 'type': typ}
        if minmax: d['min'] = a.min(0).tolist(); d['max'] = a.max(0).tolist()
        g['accessors'].append(d); return i

    hi = next(i for i, n in enumerate(g['nodes']) if n.get('name') == 'Lulu_Head_Mirrored')
    M = clh.worlds(g)[hi]; Rm = M[:3, :3]; t = M[:3, 3]
    mesh = g['meshes'][g['nodes'][hi]['mesh']]
    pa = mesh['primitives'][0]['attributes']['POSITION']; na = mesh['primitives'][0]['attributes']['NORMAL']
    P_local = clh.accessor(g, b, pa); P_world = np.einsum('ij,kj->ki', Rm, P_local) + t
    assert np.abs(P_world - patch['head_p_world_r03']).max() < 2e-6, 'patch was made for a different head'
    Qw = patch['head_p_world'].astype(float); Nw = patch['head_n_world'].astype(float)
    Ql = np.einsum('ji,kj->ki', Rm, Qw - t)          # R^T (q - t)  (rigid transform)
    Nl = np.einsum('ji,kj->ki', Rm, Nw); Nl /= np.linalg.norm(Nl, axis=1, keepdims=True)
    moved = np.abs(Ql - P_local).max(1) > 1e-7
    keep = ~moved
    Ql[keep] = P_local[keep]                           # bit-exact outside the edit region
    N_old = clh.accessor(g, b, na); Nl[keep] = N_old[keep]
    newpos = acc(Ql, 'VEC3', minmax=True); newnrm = acc(Nl, 'VEC3')
    Qw_final = np.einsum('ij,kj->ki', Rm, Ql) + t
    col = clh.linear(np.clip(clh.skincolor(Qw_final, True), 0, 1)); newcol = acc(col, 'VEC3')
    uv = np.c_[(Qw_final[:, 0] + .34) / .68, (.945 - Qw_final[:, 1]) / .45]; newuv = acc(uv, 'VEC2')
    for pr in mesh['primitives']:
        pr['attributes']['POSITION'] = newpos; pr['attributes']['NORMAL'] = newnrm
        if 'COLOR_0' in pr['attributes']: pr['attributes']['COLOR_0'] = newcol
        if 'TEXCOORD_0' in pr['attributes']: pr['attributes']['TEXCOORD_0'] = newuv

    # face textures: repoint the two existing images at new data
    for img in g['images']:
        if img.get('name') in ('face-basecolor.png', 'face-metalrough.png'):
            img['bufferView'] = buf((O / img['name']).read_bytes())

    # eye patches
    sampler = len(g['samplers']); g['samplers'].append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071})
    eye_nodes = []
    for name, tex in [('Lulu_Eye_ScreenLeft', 'eye-screen-left.png'), ('Lulu_Eye_ScreenRight', 'eye-screen-right.png')]:
        ii = len(g['images']); g['images'].append({'name': tex, 'mimeType': 'image/png', 'bufferView': buf((O / tex).read_bytes())})
        ti = len(g['textures']); g['textures'].append({'source': ii, 'sampler': sampler})
        mi = len(g['materials']); g['materials'].append({'name': f'{name} painted eye', 'extensions': {'KHR_materials_specular': {'specularFactor': .15}},
                                                        'pbrMetallicRoughness': {'baseColorTexture': {'index': ti}, 'roughnessFactor': .45, 'metallicFactor': 0}})
        p = patch[f'{name}_p']; prim = {'attributes': {'POSITION': acc(p, 'VEC3', minmax=True), 'NORMAL': acc(patch[f'{name}_n'], 'VEC3'),
                                                      'TEXCOORD_0': acc(patch[f'{name}_uv'], 'VEC2')},
                                       'indices': acc(patch[f'{name}_f'].reshape(-1, 1), 'SCALAR', 5125), 'material': mi, 'mode': 4}
        me = len(g['meshes']); g['meshes'].append({'name': name, 'primitives': [prim]})
        ni = len(g['nodes']); g['nodes'].append({'name': name, 'mesh': me, 'extras': {'eye_patch': 'eye-r01 separate flush eye patch, world-space vertices (identity transform)'}})
        g['scenes'][g.get('scene', 0)]['nodes'].append(ni); eye_nodes.append(ni)
    g.setdefault('extras', {})['eye_r01'] = {'base': 'color-r03', 'scope': 'Eye sockets filled smooth; painted eyes moved to two separate flush eye patches. Other geometry/transforms unchanged.',
                                             'params': json.loads((O / 'eye-params.json').read_text())}
    out = O / 'lulu-colored.glb'; write_glb(out, g, b)

    # ---- readback checks
    g2, b2 = clh.load(out)
    checks = {}
    checks['original_buffer_prefix_identical'] = bytes(b2[:len(b0)]) == b0
    checks['source_nodes_identical'] = g2['nodes'][:len(orig['nodes'])] == orig['nodes']
    checks['source_accessors_identical'] = g2['accessors'][:len(orig['accessors'])] == orig['accessors']
    other = [m for i, m in enumerate(orig['meshes']) if i != g['nodes'][hi]['mesh']]
    other2 = [m for i, m in enumerate(g2['meshes'][:len(orig['meshes'])]) if i != g['nodes'][hi]['mesh']]
    checks['other_meshes_identical'] = other == other2
    hm2 = g2['meshes'][g['nodes'][hi]['mesh']]
    checks['head_indices_unchanged'] = [p['indices'] for p in hm2['primitives']] == [p['indices'] for p in orig['meshes'][g['nodes'][hi]['mesh']]['primitives']]
    P2 = clh.accessor(g2, b2, hm2['primitives'][0]['attributes']['POSITION'])
    checks['head_vertices_moved'] = int(moved.sum()); checks['head_vertices_total'] = int(len(P2))
    checks['head_unmoved_vertices_bit_exact'] = bool((P2[keep] == P_local[keep]).all())
    F = np.vstack([clh.accessor(g2, b2, p['indices']).reshape(-1, 3) for p in hm2['primitives']])
    W2 = np.einsum('ij,kj->ki', Rm, P2) + t
    fn = np.cross(W2[F[:, 1]] - W2[F[:, 0]], W2[F[:, 2]] - W2[F[:, 0]])
    touched = moved[F].any(1)
    checks['edited_faces'] = int(touched.sum()); checks['edited_faces_backfacing'] = int(((fn[:, 2] < 0) & touched).sum())
    checks['max_world_displacement'] = float(np.abs(W2 - P_world).max())
    checks['eye_nodes'] = [g2['nodes'][i]['name'] for i in eye_nodes]
    checks['triangles_total'] = int(sum(g2['accessors'][p['indices']]['count'] // 3 for m in g2['meshes'] for p in m['primitives']))
    ok = all(checks[k] for k in ['original_buffer_prefix_identical', 'source_nodes_identical', 'source_accessors_identical', 'other_meshes_identical', 'head_indices_unchanged', 'head_unmoved_vertices_bit_exact']) and checks['edited_faces_backfacing'] == 0
    checks['source_sha256_after'] = sha(src); checks['source_unchanged'] = checks['source_sha256_after'] == src_sha

    # neutral gray copy (materials only; same accessors)
    gg = copy.deepcopy(g2); gi = len(gg['materials'])
    gg['materials'].append({'name': 'Neutral gray inspection', 'pbrMetallicRoughness': {'baseColorFactor': [0.462, 0.469, 0.434, 1], 'roughnessFactor': .87, 'metallicFactor': 0}})
    for m in gg['meshes']:
        for p in m['primitives']:
            p['material'] = gi; p['attributes'].pop('COLOR_0', None)
    gray = O / 'lulu-eye-r01-neutral-gray.glb'; write_glb(gray, gg, b2)

    build = {'revision': 'eye-r01', 'base': 'color-r03', 'source_sha256': src_sha, 'output_sha256': sha(out), 'gray_sha256': sha(gray),
             'checks': checks, 'all_checks_pass': bool(ok and checks['source_unchanged']), 'status': 'EYE_CANDIDATE_USER_REVIEW_PENDING',
             'blender_copy': 'NOT MADE (no Blender in this build environment); import lulu-colored.glb in Blender to make one.'}
    (O / 'build.json').write_text(json.dumps(build, indent=2, ensure_ascii=False))
    print(json.dumps(build, indent=2, ensure_ascii=False))
    return ok


if __name__ == '__main__':
    sys.exit(0 if build() else 1)
