"""Lulu game-r01: game derivative of shorts-r01 on the existing 23-bone locomotion rig (Idle/Walk/Run).
Rig-local units = the old full-r02 modular coordinates (same as locomotion-r08); feet at y=-0.9506.
"""
import numpy as np, json, struct, sys, hashlib, io
from pathlib import Path
from scipy.spatial import cKDTree
import clh, geo, decim
from newparts import load_new

TARGETS = {'lod0': {'Lulu_Head_Mirrored': 9000, 'Neck_Transition': 900, 'Original_Crown_Ornament': 1400, 'Lulu_Eye_ScreenLeft': 600,
                    'Lulu_Eye_ScreenRight': 600, 'Body': 4500, 'Shorts': 5000, 'Arm_L': 1800, 'Arm_R': 1800, 'Leg_L': 1500, 'Leg_R': 1500},
           # lod1: Body below 2000 collapses (20 mm at 1800); Head below ~3800 leaves <0.2 mm under the eye patches; Neck is border-locked at ~1480
           'lod1': {'Lulu_Head_Mirrored': 3800, 'Neck_Transition': 500, 'Original_Crown_Ornament': 500, 'Lulu_Eye_ScreenLeft': 250,
                    'Lulu_Eye_ScreenRight': 250, 'Body': 2000, 'Shorts': 2200, 'Arm_L': 700, 'Arm_R': 700, 'Leg_L': 600, 'Leg_R': 600}}
OUTNAME = {'Lulu_Head_Mirrored': 'Head', 'Neck_Transition': 'Neck', 'Original_Crown_Ornament': 'Orange', 'Lulu_Eye_ScreenLeft': 'Eye_ScreenLeft',
           'Lulu_Eye_ScreenRight': 'Eye_ScreenRight', 'Body': 'Body', 'Shorts': 'Shorts', 'Arm_L': 'Arm_L', 'Arm_R': 'Arm_R', 'Leg_L': 'Leg_L', 'Leg_R': 'Leg_R'}
HEAD_J = 6; SPINE2_J = 4; NECK_J = 5
JN = ['Root','Hips','Spine','Spine1','Spine2','Neck','Head','LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase']
MIRROR = [JN.index(n.replace('Left','#').replace('Right','Left').replace('#','Right')) for n in JN]

# shorts leg tubes follow the thigh (UpLeg) more closely so the hem does not lag behind a striding leg
THIGH = dict(top=-.60, span=.14, x0=.06, xspan=.08, amount=.55)

def thigh_blend(V, Wd, k=THIGH):
    side = np.where(V[:, 0] > 0, JN.index('LeftUpLeg'), JN.index('RightUpLeg'))
    bt = np.clip((k['top'] - V[:, 1]) / k['span'], 0, 1) * np.clip((np.abs(V[:, 0]) - k['x0']) / k['xspan'], 0, 1); bt = (bt * bt * (3 - 2 * bt)) * k['amount']
    tgt = np.zeros_like(Wd); tgt[np.arange(len(V)), side] = 1
    lg = Wd[:, [JN.index('LeftLeg'), JN.index('RightLeg')]].sum(1)  # keep existing knee share
    tgt *= (1 - lg)[:, None]; tgt[:, JN.index('LeftLeg')] += Wd[:, JN.index('LeftLeg')]; tgt[:, JN.index('RightLeg')] += Wd[:, JN.index('RightLeg')]
    return (1 - bt[:, None]) * Wd + bt[:, None] * tgt

def lin2srgb(c): return np.where(c <= .0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, 1), 1 / 2.4) - .055)

def build(lod, out_path, src='new.glb', master='master.glb', wrap_png='body-wrap-basecolor.png'):
    g, b, parts, A = load_new(src); Ainv = np.linalg.inv(A)
    gm, bm = clh.load(Path(master)); J = gm['skins'][0]['joints']
    world = lambda P: P @ A[:3, :3].T + A[:3, 3]
    # ---- wrap-UV parameters (identical to tools/make_portable_glb.py on the same model)
    wp = [world(p['P']) for k in ('Lulu_Head_Mirrored', 'Neck_Transition') for p in parts[k] if 'COLOR_0' in p['A']]
    allP = np.vstack(wp); cz = float(np.median(allP[:, 2])); y0, y1 = float(allP[:, 1].min()) - .01, float(allP[:, 1].max()) + .01
    def wrap_uv(Pw): th = np.arctan2(Pw[:, 0], Pw[:, 2] - cz); return np.c_[(th + np.pi) / (2 * np.pi), (y1 - Pw[:, 1]) / (y1 - y0)]
    def face_uv(Pw): return np.c_[(Pw[:, 0] + .34) / .68, (.945 - Pw[:, 1]) / .45]
    # ---- master skin surfaces per part (dense weights)
    msurf = {}
    for m in gm['meshes']:
        Ps, Is, Ws = [], [], []; o = 0
        for p in m['primitives']:
            P = clh.accessor(gm, bm, p['attributes']['POSITION']); I = clh.accessor(gm, bm, p['indices']).reshape(-1, 3).astype(np.int64)
            jw = clh.accessor(gm, bm, p['attributes']['JOINTS_0']).astype(int); w = clh.accessor(gm, bm, p['attributes']['WEIGHTS_0'])
            D = np.zeros((len(P), len(J))); np.add.at(D, (np.repeat(np.arange(len(P)), 4), jw.ravel()), w.ravel())
            uv1 = clh.accessor(gm, bm, p['attributes']['TEXCOORD_1']) if 'TEXCOORD_1' in p['attributes'] else None
            Ps.append(P); Is.append(I + o); Ws.append((D, uv1)); o += len(P)
        P = np.vstack(Ps); I = np.vstack(Is); D = np.vstack([w[0] for w in Ws])
        uv1 = np.vstack([w[1] for w in Ws]) if Ws[0][1] is not None else None
        msurf[m['name']] = (geo.Surf(P, I), D, uv1, P, I)

    meshes = []; report = {'lod': lod, 'parts': {}}
    for key, target in TARGETS[lod].items():
        prims = parts[key]; P, I, pid, off = decim.part_mesh(prims); I = I.astype(np.int64)
        # eye patches vs decimated head: verified by check_eyes.py (no lock needed)
        V, T, Wo, Fo, fixed = decim.decimate(P, I, target, tol=2e-4)
        # original welded surface + attribute arrays (positions identical within a part, so the first matching vertex is used)
        key6 = np.round(P / 1e-6).astype(np.int64); _, first = np.unique(key6, axis=0, return_index=True)
        surf = geo.Surf(Wo, Fo); Fi, B, Dd = surf.query(V)
        # normals: decimated geometry; border vertices keep the authored source normal
        Nn = geo.vnormals(V, T)
        Norig = np.vstack([p['N'] for p in prims])[first]
        _, nearest = cKDTree(Wo).query(V); bmask = fixed[nearest] & (np.linalg.norm(Wo[nearest] - V, axis=1) < 1e-6)
        Nn[bmask] = Norig[nearest[bmask]]
        # primitive id per new face (closest original face to the face centroid)
        oc = surf.query(V[T].mean(1))[0]
        allI = I; face_pid = pid  # original faces before weld; map through centroid query on raw faces
        raw = geo.Surf(P, I); fpid = pid[raw.query(V[T].mean(1))[0]]
        Pw = world(V)
        cols = np.vstack([p['A']['COLOR_0'][:, :3] if 'COLOR_0' in p['A'] else np.ones((len(p['P']), 3)) for p in prims])[first]
        C = surf.interp(Fi, B, cols)
        # ---- skin weights
        nm = OUTNAME[key]
        if nm in ('Head', 'Orange', 'Eye_ScreenLeft', 'Eye_ScreenRight'):
            Wd = np.zeros((len(V), len(J))); Wd[:, HEAD_J] = 1
        elif nm == 'Neck':
            a = np.clip((V[:, 1] + .123) / (.083), 0, 1); a = a * a * (3 - 2 * a); Wd = np.zeros((len(V), len(J)))
            Wd[:, SPINE2_J] = (1 - a) ** 2; Wd[:, NECK_J] = 2 * a * (1 - a); Wd[:, HEAD_J] = a ** 2
        else:
            src = 'Arm_L' if nm == 'Arm_R' else nm; Q = V * ([-1, 1, 1] if nm == 'Arm_R' else 1)
            ms, D, _, _, _ = msurf[src]; mf, mb, md = ms.query(Q); Wd = ms.interp(mf, mb, D); report.setdefault('weight_src_dist_max', {})[nm] = float(md.max())
            if nm == 'Arm_R': Wd = Wd[:, MIRROR]
            if nm == 'Shorts': Wd = thigh_blend(V, Wd)
            if nm.startswith('Leg'):
                # r08 legs were rigid on the Foot bone, so the leg top slid out of the shorts while striding.
                # Above the hem the leg follows exactly the same (thigh-blended) weights as the surrounding game shorts tube;
                # using the unblended master shorts weights here let the thigh underside slip out under the front hem when running.
                ss_, Ds, _, _, _ = msurf['Shorts']; sf, sb, _ = ss_.query(V); Wsh = thigh_blend(V, ss_.interp(sf, sb, Ds))
                a = np.clip((V[:, 1] + .87) / .06, 0, 1); a = (a * a * (3 - 2 * a))[:, None]; Wd = a * Wsh + (1 - a) * Wd
        top = np.argsort(-Wd, 1)[:, :4]; wt = np.take_along_axis(Wd, top, 1); wt[wt < 1e-4] = 0; wt /= wt.sum(1, keepdims=True)
        jt = np.where(wt > 0, top, 0)
        base = dict(P=V, N=Nn, J=jt, W=wt)
        # ---- primitives / materials
        out = []
        if nm == 'Head':
            facem = np.array([prims[0]['prim'] != q for q in fpid])  # prim 1 = face texture
            facem = fpid == 1
            out.append(('wrap', T[~facem])); out.append(('face', T[facem]))
        elif nm == 'Neck': out.append(('wrap', T))
        elif nm == 'Orange':
            green = C[:, 1] > C[:, 0]; leaf = green[T].sum(1) >= 2
            out.append(('fruit_orange', T[~leaf])); out.append(('fruit_leaf', T[leaf]))
            report['parts'].setdefault('colors', {})['fruit_orange'] = C[~green].mean(0).tolist(); report['parts']['colors']['fruit_leaf'] = C[green].mean(0).tolist()
        elif nm.startswith('Eye'): out.append((nm, T))
        else:
            out.append((nm, T)); report['parts'].setdefault('colors', {})[nm] = C.mean(0).tolist(); report['parts'].setdefault('color_spread', {})[nm] = float(np.abs(C - C.mean(0)).max())
        prim_out = []
        for mat, TT in out:
            if len(TT) == 0: continue
            used = np.unique(TT); rm = -np.ones(len(V), int); rm[used] = np.arange(len(used)); TT2 = rm[TT]
            attr = {k: v[used] for k, v in base.items()}; Pw_u = Pw[used]
            if mat == 'wrap':
                uv = wrap_uv(Pw_u); span = uv[TT2, 0].max(1) - uv[TT2, 0].min(1); cross = span > .5; dup = {}
                for fi in np.where(cross)[0]:
                    for j in range(3):
                        v = TT2[fi, j]
                        if uv[v, 0] < .5:
                            if v not in dup: dup[v] = len(uv) + len(dup)
                            TT2[fi, j] = dup[v]
                if dup:
                    ids = np.array(list(dup.keys())); uv = np.vstack([uv, uv[ids] + [1, 0]])
                    attr = {k: np.concatenate([v, v[ids]]) for k, v in attr.items()}
                attr['UV0'] = uv
            elif mat == 'face': attr['UV0'] = face_uv(Pw_u)
            elif mat.startswith('Eye'):
                uvo = prims[0]['A']['TEXCOORD_0'][first]; attr['UV0'] = surf.interp(Fi[used], B[used], uvo)
            elif mat == 'Shorts':
                # per-corner FabricUV from one consistent master triangle per face (no smearing across UV seams)
                ms, D, uv1, mP, mI = msurf['Shorts']
                c = attr['P'][TT2].mean(1); mf, _, _ = ms.query(c)
                tri = mP[mI[mf]]; corners = attr['P'][TT2]
                e0 = tri[:, 1] - tri[:, 0]; e1 = tri[:, 2] - tri[:, 0]; n = np.cross(e0, e1)
                def bary(p):
                    d = p - tri[:, 0]; d00 = (e0 * e0).sum(1); d01 = (e0 * e1).sum(1); d11 = (e1 * e1).sum(1); d20 = (d * e0).sum(1); d21 = (d * e1).sum(1)
                    den = d00 * d11 - d01 * d01; bad = np.abs(den) < 1e-18; den = np.where(bad, 1, den); v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den; v[bad] = 1/3; w[bad] = 1/3; return np.c_[1 - v - w, v, w]
                tuv = uv1[mI[mf]]
                cuv = np.stack([(bary(corners[:, k])[:, :, None] * tuv).sum(1) for k in range(3)], 1)  # (nf,3,2)
                # split vertices per (vertex, uv1)
                flat_v = TT2.ravel(); flat_uv = cuv.reshape(-1, 2).copy()
                # unify corner UVs of a vertex that agree within 0.02 (same island); keep real seams split
                order = np.argsort(flat_v, kind='stable'); fv = flat_v[order]; fu = flat_uv[order]; starts = np.r_[0, np.where(np.diff(fv))[0] + 1, len(fv)]
                lab = np.zeros(len(fv), np.int64)
                for a_, b_ in zip(starts[:-1], starts[1:]):
                    grp = fu[a_:b_]; ids = -np.ones(b_ - a_, int); reps = []
                    for q in range(b_ - a_):
                        for r_, rep in enumerate(reps):
                            if np.abs(grp[q] - rep[0]).max() < .02: ids[q] = r_; rep[1].append(q); break
                        else: reps.append([grp[q], [q]]); ids[q] = len(reps) - 1
                    for r_, rep in enumerate(reps): fu[a_ + np.array(rep[1])] = grp[np.array(rep[1])].mean(0)
                    lab[a_:b_] = ids
                flat_uv[order] = fu; sub = np.zeros(len(fv), np.int64); sub[order] = lab
                kk = np.c_[flat_v, sub]
                _, firsti, inv = np.unique(kk, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
                attr = {k: v[flat_v[firsti]] for k, v in attr.items()}; attr['UV1'] = flat_uv[firsti]; TT2 = inv.reshape(-1, 3)
                report.setdefault('shorts_uv1_split', [len(used), len(firsti)])
            prim_out.append((mat, attr, TT2))
        meshes.append((nm, prim_out))
        report['parts'][nm] = dict(src_tris=int(len(Fo)), tris=int(len(T)), verts=int(len(V)), max_dev_local=float(Dd.max()), p99_dev_local=float(np.percentile(Dd, 99)))
    return write(gm, bm, g, b, meshes, report, out_path, wrap_png)

def write(gm, bm, g, b, meshes, report, out_path, wrap_png):
    out = {'asset': {'version': '2.0', 'generator': 'lulu game-r01 builder'}, 'scene': 0, 'scenes': [], 'nodes': [], 'meshes': [], 'materials': [], 'textures': [], 'images': [], 'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071}, {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 33071}],
           'accessors': [], 'bufferViews': [], 'buffers': [{}], 'skins': [], 'animations': []}
    buf = bytearray()
    def bv(raw, target=None):
        buf.extend(b'\0' * ((-len(buf)) % 4)); d = {'buffer': 0, 'byteOffset': len(buf), 'byteLength': len(raw)}
        if target: d['target'] = target
        out['bufferViews'].append(d); buf.extend(raw); return len(out['bufferViews']) - 1
    def acc(a, typ, comp=5126, minmax=False, target=None, normalized=False):
        dt = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[comp]; a = np.ascontiguousarray(a, dtype=dt)
        d = {'bufferView': bv(a.tobytes(), target), 'componentType': comp, 'count': int(a.shape[0]), 'type': typ}
        if minmax: d['min'] = a.reshape(a.shape[0], -1).min(0).tolist(); d['max'] = a.reshape(a.shape[0], -1).max(0).tolist()
        if normalized: d['normalized'] = True
        out['accessors'].append(d); return len(out['accessors']) - 1
    # images
    def img(name, data, mime='image/png'):
        out['images'].append({'name': name, 'mimeType': mime, 'bufferView': bv(data)}); return len(out['images']) - 1
    def tex(i, s=0): out['textures'].append({'source': i, 'sampler': s}); return len(out['textures']) - 1
    srcimg = {im.get('name'): bytes(b[g['bufferViews'][im['bufferView']]['byteOffset']:g['bufferViews'][im['bufferView']]['byteOffset'] + g['bufferViews'][im['bufferView']]['byteLength']]) for im in g['images'] if im.get('name')}
    t_face = tex(img('face-basecolor.png', srcimg['face-basecolor.png'])); t_wrap = tex(img('body-wrap-basecolor.png', Path(wrap_png).read_bytes()), 1)
    t_el = tex(img('eye-screen-left.png', srcimg['eye-screen-left.png'])); t_er = tex(img('eye-screen-right.png', srcimg['eye-screen-right.png']))
    cols = report['parts']['colors']; mats = {}
    def mat(name, col=None, t=None, rough=.87):
        p = {'metallicFactor': 0, 'roughnessFactor': rough, 'baseColorFactor': [float(x) for x in (col if col is not None else [1, 1, 1])] + [1]}
        if t is not None: p['baseColorTexture'] = {'index': t}
        out['materials'].append({'name': name, 'pbrMetallicRoughness': p}); mats[name] = len(out['materials']) - 1
    mat('Lulu_Skin_Wrap', t=t_wrap); mat('Lulu_Face', t=t_face); mat('Lulu_Eye_ScreenLeft', t=t_el, rough=.45); mat('Lulu_Eye_ScreenRight', t=t_er, rough=.45)
    mat('Lulu_Fruit_Orange', cols['fruit_orange']); mat('Lulu_Fruit_Leaf', cols['fruit_leaf'])
    for p in ('Body', 'Arm_L', 'Arm_R', 'Leg_L', 'Leg_R'): mat('Lulu_' + p, cols[p])
    mat('Lulu_Shorts_Original', cols['Shorts'])
    matof = {'wrap': 'Lulu_Skin_Wrap', 'face': 'Lulu_Face', 'Eye_ScreenLeft': 'Lulu_Eye_ScreenLeft', 'Eye_ScreenRight': 'Lulu_Eye_ScreenRight', 'fruit_orange': 'Lulu_Fruit_Orange',
             'fruit_leaf': 'Lulu_Fruit_Leaf', 'Shorts': 'Lulu_Shorts_Original'}
    # joints: copy master nodes 0..22 verbatim
    for n in gm['nodes'][:23]: out['nodes'].append({k: v for k, v in n.items()})
    skin = gm['skins'][0]; ibm = clh.accessor(gm, bm, skin['inverseBindMatrices']).reshape(-1, 16)
    out['skins'].append({'name': 'Lulu_Game_Skin', 'joints': skin['joints'], 'inverseBindMatrices': acc(ibm, 'MAT4')})
    child = []
    for nm, prims in meshes:
        mp = []
        for m, a, T in prims:
            at = {'POSITION': acc(a['P'], 'VEC3', minmax=True, target=34962), 'NORMAL': acc(a['N'], 'VEC3', target=34962)}
            if 'UV0' in a: at['TEXCOORD_0'] = acc(a['UV0'], 'VEC2', target=34962)
            if 'UV1' in a: at['TEXCOORD_0'] = acc(a['UV1'] * 0 + a['UV1'], 'VEC2', target=34962) if 'UV0' not in a else at.get('TEXCOORD_0'); at['TEXCOORD_1'] = acc(a['UV1'], 'VEC2', target=34962)
            at['JOINTS_0'] = acc(a['J'], 'VEC4', 5123, target=34962); at['WEIGHTS_0'] = acc(a['W'], 'VEC4', target=34962)
            mp.append({'attributes': at, 'indices': acc(T.ravel(), 'SCALAR', 5125, target=34963), 'material': mats[matof.get(m, 'Lulu_' + m)]})
        out['meshes'].append({'name': nm, 'primitives': mp}); out['nodes'].append({'name': nm, 'mesh': len(out['meshes']) - 1, 'skin': 0}); child.append(len(out['nodes']) - 1)
    out['nodes'].append({'name': 'Lulu_Game_Rig', 'children': child + [22]}); out['scenes'].append({'name': 'Scene', 'nodes': [len(out['nodes']) - 1]})
    # animations copied verbatim (joint node indices are identical)
    for an in gm['animations']:
        smp = []
        for s in an['samplers']:
            i = clh.accessor(gm, bm, s['input']); o = clh.accessor(gm, bm, s['output'])
            typ = gm['accessors'][s['output']]['type']; ia = acc(i, 'SCALAR', minmax=True)
            smp.append({'input': ia, 'output': acc(o, typ), 'interpolation': s.get('interpolation', 'LINEAR')})
        out['animations'].append({'name': an['name'], 'channels': an['channels'], 'samplers': smp})
    out['buffers'][0]['byteLength'] = len(buf)
    out['extras'] = {'lulu_game': {k: v for k, v in report.items() if k != 'parts'} | {'parts': {k: v for k, v in report['parts'].items() if k not in ('colors',)}}}
    js = json.dumps(out, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4); buf.extend(b'\0' * ((-len(buf)) % 4))
    Path(out_path).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(js) + len(buf)) + struct.pack('<II', len(js), 0x4e4f534a) + js + struct.pack('<II', len(buf), 0x004e4942) + buf)
    tris = sum(v['tris'] for k, v in report['parts'].items() if isinstance(v, dict) and 'tris' in v)
    report['total_tris'] = tris; return report

if __name__ == '__main__':
    lod = sys.argv[1]; r = build(lod, sys.argv[2]); print(json.dumps(r, indent=1, default=float))
