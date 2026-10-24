"""shorts-r01: repair of the shorts back tail-removal fan crease. Base: polish-r01 (read-only).

Edits (Shorts mesh only):
  * outer layer of the back repair patch (Shorts primitive 1, outer component) is replaced by a new,
    evenly triangulated surface that fills the same hole plus a 1 cm margin of the main Shorts surface
    (181 main-mesh outer faces removed, primitive 0 index list only). New boundary welds exactly to the
    remaining main-mesh edges. Height from a thin-plate fit to the surrounding shorts surface; the waistband
    step is continued across the former gap. The long radial slivers that caused the fan crease are gone.
  * inner layer of the patch (hidden backing surface) is kept unchanged.
Everything else (all other meshes, nodes, transforms, materials, textures, head/eyes/fruit) byte-identical.
Patch data: review/lulu-hybrid-color-20261023/shorts-r01/shorts-patch.npz (computed offline, see params json).
"""
from pathlib import Path
import copy, hashlib, json, struct, sys, importlib.util
from collections import Counter
import numpy as np

R = Path(__file__).resolve().parents[1]
D = R / 'review/lulu-hybrid-color-20261023'
O = D / 'shorts-r01'
spec = importlib.util.spec_from_file_location('clh', R / 'tools/color_lulu_hybrid.py')
clh = importlib.util.module_from_spec(spec); spec.loader.exec_module(clh)
BASE_SHA = 'a9bc5557684ca97365931b8ac3bcfb4784097e1aa47e35516c3f7733160c1473'  # polish-r01/lulu-colored.glb


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_glb(path, g, b):
    b = bytearray(b); b += b'\0' * ((-len(b)) % 4); g['buffers'][0]['byteLength'] = len(b)
    js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(js) + len(b)) + struct.pack('<II', len(js), 0x4e4f534a) + js + struct.pack('<II', len(b), 0x004e4942) + b)


def build():
    src = D / 'polish-r01/lulu-colored.glb'; assert sha(src) == BASE_SHA, 'polish-r01 changed'
    g, b = clh.load(src); orig = copy.deepcopy(g); b0 = bytes(b)
    z = np.load(O / 'shorts-patch.npz'); prm = json.loads((O / 'shorts-params.json').read_text())

    def add(a, typ, ct=5126, minmax=False):
        a = np.ascontiguousarray(a, dtype='<f4' if ct == 5126 else '<u4'); b.extend(b'\0' * ((-len(b)) % 4))
        g['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': a.nbytes}); b.extend(a.tobytes())
        d = {'bufferView': len(g['bufferViews']) - 1, 'componentType': ct, 'count': len(a) if a.ndim > 1 else a.size, 'type': typ}
        if minmax: d['min'] = a.min(0).tolist(); d['max'] = a.max(0).tolist()
        g['accessors'].append(d); return len(g['accessors']) - 1

    si = next(i for i, n in enumerate(g['nodes']) if n.get('name') == 'Shorts'); mi = g['nodes'][si]['mesh']
    pr = g['meshes'][mi]['primitives']; p0, p1 = pr[0], pr[1]
    A = {k: clh.accessor(g, b, v) for k, v in p1['attributes'].items()}
    I1 = clh.accessor(g, b, p1['indices']).reshape(-1, 3); I0 = clh.accessor(g, b, p0['indices']).reshape(-1, 3)
    inner = z['inner_vertices'].astype(int); src_i = z['attr_src'].astype(int)
    V, NN, T = z['outer_P'], z['outer_N'], z['outer_T'].astype(int); nv = len(V)
    remap = -np.ones(len(A['POSITION']), int); remap[inner] = np.arange(len(inner)) + nv
    inner_faces = I1[np.isin(I1[:, 0], inner)]; Ti = remap[inner_faces]; assert (Ti >= 0).all()
    newP = np.vstack([V, A['POSITION'][inner]]); newN = np.vstack([NN, A['NORMAL'][inner]])
    newUV = np.vstack([A['TEXCOORD_0'][src_i], A['TEXCOORD_0'][inner]]); newC = np.vstack([A['COLOR_0'][src_i], A['COLOR_0'][inner]])
    keep0 = np.ones(len(I0), bool); keep0[z['main_faces_removed'].astype(int)] = False
    p1['attributes'] = {'POSITION': add(newP, 'VEC3', minmax=True), 'NORMAL': add(newN, 'VEC3'),
                        'TEXCOORD_0': add(newUV, 'VEC2'), 'COLOR_0': add(newC, 'VEC3')}
    p1['indices'] = add(np.vstack([T, Ti]).ravel(), 'SCALAR', ct=5125)
    p0['indices'] = add(I0[keep0].ravel(), 'SCALAR', ct=5125)
    g.setdefault('extras', {})['shorts_r01'] = {'base': 'polish-r01', 'params': prm}
    out = O / 'lulu-colored.glb'; write_glb(out, g, b)

    # ---- readback checks
    g2, b2 = clh.load(out); ck = {}
    ck['base_buffer_prefix_identical'] = bytes(b2[:len(b0)]) == b0
    ck['nodes_identical'] = g2['nodes'] == orig['nodes']
    ck['materials_images_identical'] = g2['materials'] == orig['materials'] and g2['images'] == orig['images']
    ck['source_accessors_identical'] = g2['accessors'][:len(orig['accessors'])] == orig['accessors']
    ck['other_meshes_identical'] = all(g2['meshes'][i] == orig['meshes'][i] for i in range(len(orig['meshes'])) if i != mi)
    ck['shorts_primitive2_identical'] = g2['meshes'][mi]['primitives'][2] == orig['meshes'][mi]['primitives'][2]
    q = g2['meshes'][mi]['primitives']
    P0 = clh.accessor(g2, b2, q[0]['attributes']['POSITION']); J0 = clh.accessor(g2, b2, q[0]['indices']).reshape(-1, 3)
    P1 = clh.accessor(g2, b2, q[1]['attributes']['POSITION']); J1 = clh.accessor(g2, b2, q[1]['indices']).reshape(-1, 3)
    key = lambda p: tuple(np.round(p * 1e6).astype(np.int64))
    mainE = Counter(tuple(sorted((key(P0[t[a]]), key(P0[t[(a + 1) % 3]])))) for t in J0 for a in range(3))
    To = J1[(J1 < nv).all(1)]
    EC = Counter(tuple(sorted((t[a], t[(a + 1) % 3]))) for t in To for a in range(3))
    bd = [e for e, c in EC.items() if c == 1]
    ck['patch_outer_triangles'] = int(len(To)); ck['patch_outer_vertices'] = int(nv)
    ck['patch_outer_edges_manifold'] = all(c <= 2 for c in EC.values())
    ck['patch_boundary_edges'] = len(bd)
    ck['patch_boundary_welded_to_main'] = all(mainE.get(tuple(sorted((key(P1[a]), key(P1[c])))), 0) == 1 for a, c in bd)
    F = np.cross(P1[To[:, 1]] - P1[To[:, 0]], P1[To[:, 2]] - P1[To[:, 0]])
    ck['patch_outer_faces_outward'] = bool((F[:, 2] < 0).all())
    ck['patch_outer_degenerate_faces'] = int((np.linalg.norm(F, axis=1) < 2e-10).sum())
    ck['main_faces_removed'] = int((~keep0).sum()); ck['patch_inner_faces_kept'] = int(len(Ti))
    # hidden inner layer must stay behind the new outer surface
    Po = P1[:nv]; Pi = P1[nv:]
    nn_ = np.array([np.argmin(((Po[:, :2] - p[:2]) ** 2).sum(1)) for p in Pi[::4]])
    gap = Pi[::4, 2] - Po[nn_, 2]; ck['inner_gap_min_local'] = float(gap.min()); ck['inner_behind_outer'] = bool(gap.min() > 0.003)
    ck['base_unchanged'] = sha(src) == BASE_SHA
    must = ['base_buffer_prefix_identical', 'nodes_identical', 'materials_images_identical', 'source_accessors_identical', 'other_meshes_identical',
            'shorts_primitive2_identical', 'patch_outer_edges_manifold', 'patch_boundary_welded_to_main', 'patch_outer_faces_outward', 'inner_behind_outer', 'base_unchanged']
    ok = all(ck[k] for k in must) and ck['patch_outer_degenerate_faces'] == 0

    gg = copy.deepcopy(g2); gi = len(gg['materials'])
    gg['materials'].append({'name': 'Neutral gray inspection', 'pbrMetallicRoughness': {'baseColorFactor': [0.462, 0.469, 0.434, 1], 'roughnessFactor': .87, 'metallicFactor': 0}})
    for m in gg['meshes']:
        for p in m['primitives']: p['material'] = gi; p['attributes'].pop('COLOR_0', None)
    gray = O / 'lulu-shorts-r01-neutral-gray.glb'; write_glb(gray, gg, b2)
    rep = {'revision': 'shorts-r01', 'base': 'polish-r01', 'base_sha256': BASE_SHA, 'output_sha256': sha(out), 'gray_sha256': sha(gray), 'checks': ck,
           'all_checks_pass': bool(ok), 'status': 'SHORTS_REPAIR_CANDIDATE_USER_REVIEW_PENDING', 'blender_copy': 'NOT MADE'}
    (O / 'build.json').write_text(json.dumps(rep, indent=2, ensure_ascii=False)); print(json.dumps(rep, indent=2, ensure_ascii=False)); return ok


if __name__ == '__main__':
    sys.exit(0 if build() else 1)
