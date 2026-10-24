"""polish-r01: muzzle colour edge, mouth line, crown fruit seat. Base: eye-r01 (read-only).

Edits:
  * muzzle orange reaches just under the eyes (ry_up .126 -> .150) -> head COLOR_0 + face base colour
  * mouth line lower / slightly wider, right end a touch higher (face texture only)
  * head crown plateau (flat low-poly cap with a folded, dark rim) refilled as a smooth dome; topology unchanged
  * crown fruit: narrower, slightly taller, seated so its open rim is hidden; leaf gathered into a short stem
Everything else (body, arms, legs, shorts, neck, eye patches, transforms) byte-identical.
"""
from pathlib import Path
import copy, hashlib, json, struct, sys, importlib.util
import numpy as np

R = Path(__file__).resolve().parents[1]
D = R / 'review/lulu-hybrid-color-20261023'
O = D / 'polish-r01'
spec = importlib.util.spec_from_file_location('clh', R / 'tools/color_lulu_hybrid.py')
clh = importlib.util.module_from_spec(spec); spec.loader.exec_module(clh)
BASE_SHA = '164deed1f1572673dfdc716238e864361dcdb4f17906103b5562e13e251b0a1f'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def skincolor2(p, ry_up):
    col = np.tile(clh.SKIN, (len(p), 1)); x, y, z = p.T
    ry = np.where(y > .627, ry_up, .161)
    radius = np.sqrt((x / .315) ** 2 + ((y - .627) / ry) ** 2 + ((z - .255) / .65) ** 2)
    a = (1 - clh.smooth(.89, 1.105, radius)) * clh.smooth(.015, .075, z)
    orange = clh.MUZZLE[None, :] + np.c_[np.zeros(len(p)), np.clip((y - .60) * .21, 0, .03), np.zeros(len(p))]
    return np.clip(col * (1 - a[:, None]) + orange * a[:, None], 0, 1)


def write_glb(path, g, b):
    b = bytearray(b); b += b'\0' * ((-len(b)) % 4); g['buffers'][0]['byteLength'] = len(b)
    js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(js) + len(b)) + struct.pack('<II', len(js), 0x4e4f534a) + js + struct.pack('<II', len(b), 0x004e4942) + b)


def build():
    src = D / 'eye-r01/lulu-colored.glb'; assert sha(src) == BASE_SHA, 'eye-r01 changed'
    g, b = clh.load(src); orig = copy.deepcopy(g); b0 = bytes(b)
    patch = np.load(O / 'polish-patch.npz'); prm = json.loads((O / 'polish-params.json').read_text())
    W = clh.worlds(g)

    def buf(raw):
        b.extend(b'\0' * ((-len(b)) % 4)); i = len(g['bufferViews'])
        g['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(raw)}); b.extend(raw); return i

    def acc(a, typ, minmax=False):
        a = np.ascontiguousarray(a, dtype='<f4'); i = len(g['accessors'])
        d = {'bufferView': buf(a.tobytes()), 'componentType': 5126, 'count': len(a), 'type': typ}
        if minmax: d['min'] = a.min(0).tolist(); d['max'] = a.max(0).tolist()
        g['accessors'].append(d); return i

    def replace(node_name, key_base, key_new, key_n):
        ni = next(i for i, n in enumerate(g['nodes']) if n.get('name') == node_name)
        M = W[ni]; Rm = M[:3, :3]; t = M[:3, 3]; Ri = np.linalg.inv(Rm)
        mesh = g['meshes'][g['nodes'][ni]['mesh']]; pr0 = mesh['primitives'][0]
        Pl = clh.accessor(g, b, pr0['attributes']['POSITION']); Nl_old = clh.accessor(g, b, pr0['attributes']['NORMAL'])
        Pw = Pl @ Rm.T + t
        assert np.abs(Pw - patch[key_base]).max() < 2e-6, f'{node_name}: patch made for a different base'
        Qw = patch[key_new].astype(float); Ql = (Qw - t) @ Ri.T
        # world normal = M^-T n_local  ->  n_local ∝ M^T n_world  (row vectors: n_world @ M)
        Nl = patch[key_n].astype(float) @ Rm
        Nl /= np.linalg.norm(Nl, axis=1, keepdims=True)
        moved = np.abs(Qw - Pw).max(1) > 1e-7
        Ql[~moved] = Pl[~moved]; Nl[~moved] = Nl_old[~moved]
        pa = acc(Ql, 'VEC3', True); na = acc(Nl, 'VEC3')
        for pr in mesh['primitives']:
            pr['attributes']['POSITION'] = pa; pr['attributes']['NORMAL'] = na
        return ni, mesh, Ql @ Rm.T + t, moved

    hi, hmesh, Hw, hmoved = replace('Lulu_Head_Mirrored', 'head_p_world_base', 'head_p_world', 'head_n_world')
    col = clh.linear(skincolor2(Hw, prm['muzzle']['ry_up'])); ca = acc(col, 'VEC3')
    uv = np.c_[(Hw[:, 0] + .34) / .68, (.945 - Hw[:, 1]) / .45]; ua = acc(uv, 'VEC2')
    for pr in hmesh['primitives']:
        if 'COLOR_0' in pr['attributes']: pr['attributes']['COLOR_0'] = ca
        if 'TEXCOORD_0' in pr['attributes']: pr['attributes']['TEXCOORD_0'] = ua
    oi, omesh, Ow, omoved = replace('Original_Crown_Ornament', 'orn_p_world_base', 'orn_p_world', 'orn_n_world')
    for img in g['images']:
        if img.get('name') in ('face-basecolor.png', 'face-metalrough.png'):
            img['bufferView'] = buf((O / img['name']).read_bytes())
    g.setdefault('extras', {})['polish_r01'] = {'base': 'eye-r01', 'params': prm}
    out = O / 'lulu-colored.glb'; write_glb(out, g, b)

    g2, b2 = clh.load(out); ck = {}
    ck['base_buffer_prefix_identical'] = bytes(b2[:len(b0)]) == b0
    ck['nodes_identical'] = g2['nodes'] == orig['nodes']
    ck['source_accessors_identical'] = g2['accessors'][:len(orig['accessors'])] == orig['accessors']
    touched = {g['nodes'][hi]['mesh'], g['nodes'][oi]['mesh']}
    ck['other_meshes_identical'] = all(g2['meshes'][i] == orig['meshes'][i] for i in range(len(orig['meshes'])) if i not in touched)
    ck['indices_unchanged'] = all([p['indices'] for p in g2['meshes'][i]['primitives']] == [p['indices'] for p in orig['meshes'][i]['primitives']] for i in touched)
    ck['head_vertices_moved'] = int(hmoved.sum()); ck['fruit_vertices_moved'] = int(omoved.sum())
    hm = g2['meshes'][g['nodes'][hi]['mesh']]
    P2 = clh.accessor(g2, b2, hm['primitives'][0]['attributes']['POSITION']); M = clh.worlds(g2)[hi]; W2 = P2 @ M[:3, :3].T + M[:3, 3]
    F = np.vstack([clh.accessor(g2, b2, p['indices']).reshape(-1, 3) for p in hm['primitives']])
    fn = np.cross(W2[F[:, 1]] - W2[F[:, 0]], W2[F[:, 2]] - W2[F[:, 0]]); crown = hmoved[F].any(1)
    ck['crown_faces_edited'] = int(crown.sum()); ck['crown_faces_facing_down'] = int(((fn[:, 1] < 0) & crown).sum())
    ck['crown_faces_facing_down_area_max'] = float(np.linalg.norm(fn[(fn[:, 1] < 0) & crown], axis=1).max(initial=0) / 2)
    ck['base_unchanged'] = sha(src) == BASE_SHA
    ok = all(ck[k] for k in ['base_buffer_prefix_identical', 'nodes_identical', 'source_accessors_identical', 'other_meshes_identical', 'indices_unchanged', 'base_unchanged'])

    gg = copy.deepcopy(g2); gi = len(gg['materials'])
    gg['materials'].append({'name': 'Neutral gray inspection', 'pbrMetallicRoughness': {'baseColorFactor': [0.462, 0.469, 0.434, 1], 'roughnessFactor': .87, 'metallicFactor': 0}})
    for m in gg['meshes']:
        for p in m['primitives']: p['material'] = gi; p['attributes'].pop('COLOR_0', None)
    gray = O / 'lulu-polish-r01-neutral-gray.glb'; write_glb(gray, gg, b2)
    rep = {'revision': 'polish-r01', 'base': 'eye-r01', 'base_sha256': BASE_SHA, 'output_sha256': sha(out), 'gray_sha256': sha(gray), 'checks': ck,
           'all_checks_pass': bool(ok), 'status': 'POLISH_CANDIDATE_USER_REVIEW_PENDING', 'blender_copy': 'NOT MADE (no Blender here)'}
    (O / 'build.json').write_text(json.dumps(rep, indent=2, ensure_ascii=False)); print(json.dumps(rep, indent=2, ensure_ascii=False)); return ok


if __name__ == '__main__':
    sys.exit(0 if build() else 1)
