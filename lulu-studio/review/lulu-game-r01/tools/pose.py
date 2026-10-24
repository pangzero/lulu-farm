"""Evaluate a skinned game GLB at an animation time (linear / slerp sampling, glTF LBS) and measure leg exposure from the shorts.
Usage: pose.py game.glb [Run|Walk|Idle]  -> per-frame count of should-be-covered leg vertices visible from five views.
"""
import sys, json, numpy as np
from pathlib import Path
import clh, geo

def slerp(a, b, t):
    d = (a * b).sum()
    if d < 0: b, d = -b, -d
    if d > .9995: q = a + t * (b - a)
    else:
        th = np.arccos(d); q = (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)
    return q / np.linalg.norm(q)

class Rig:
    def __init__(s, path):
        s.g, s.b = clh.load(Path(path)); g, b = s.g, s.b
        s.anims = {}
        for an in g['animations']:
            ch = []
            for c in an['channels']:
                sm = an['samplers'][c['sampler']]; ch.append((c['target']['node'], c['target']['path'], clh.accessor(g, b, sm['input'])[:, 0], clh.accessor(g, b, sm['output']), sm.get('interpolation', 'LINEAR')))
            s.anims[an['name']] = ch
        sk = g['skins'][0]; s.joints = sk['joints']; s.ibm = clh.accessor(g, b, sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        s.meshes = {}
        for m in g['meshes']:
            for p in m['primitives']:
                a = p['attributes']
                s.meshes.setdefault(m['name'], []).append(dict(P=clh.accessor(g, b, a['POSITION']), N=clh.accessor(g, b, a['NORMAL']), J=clh.accessor(g, b, a['JOINTS_0']).astype(int),
                                                              W=clh.accessor(g, b, a['WEIGHTS_0']), I=clh.accessor(g, b, p['indices']).reshape(-1, 3).astype(np.int64)))
    def duration(s, name): return max(c[2][-1] for c in s.anims[name])
    def joint_mats(s, name=None, t=0.):
        W = s.worlds(name, t); return np.stack([W[j] @ s.ibm[i] for i, j in enumerate(s.joints)])
    def worlds(s, name=None, t=0.):
        nodes = [dict(n) for n in s.g['nodes']]
        if name:
            for ni, path, tin, out, interp in s.anims[name]:
                k = int(np.clip(np.searchsorted(tin, t, 'right') - 1, 0, len(tin) - 1)); k2 = min(k + 1, len(tin) - 1)
                u = 0. if k2 == k or interp == 'STEP' else float(np.clip((t - tin[k]) / (tin[k2] - tin[k]), 0, 1))
                v = slerp(out[k], out[k2], u) if path == 'rotation' else out[k] * (1 - u) + out[k2] * u
                nodes[ni][path] = v.tolist(); nodes[ni].pop('matrix', None)
        return clh.worlds({**s.g, 'nodes': nodes})
    def posed(s, mesh, M):
        out = []
        for p in s.meshes[mesh]:
            S = np.einsum('vk,vkij->vij', p['W'], M[p['J']]); P = np.einsum('vij,vj->vi', S[:, :3, :3], p['P']) + S[:, :3, 3]
            N = np.einsum('vij,vj->vi', S[:, :3, :3], p['N']); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-20); out.append((P, N, p['I']))
        return out

def merge(prims):
    o = 0; Ps, Ns, Is = [], [], []
    for P, N, I in prims: Ps.append(P); Ns.append(N); Is.append(I + o); o += len(P)
    return np.vstack(Ps), np.vstack(Ns), np.vstack(Is)

VIEWS = {f'{n}': np.array([np.sin(np.radians(a)) * np.cos(np.radians(15)), np.sin(np.radians(15)), np.cos(np.radians(a)) * np.cos(np.radians(15))])
         for n, a in (('front', 0), ('front_l45', 45), ('front_r45', -45), ('side_l', 90), ('side_r', -90))}

def occluded(Q, d, P, I, eps=1e-4, chunk=64):
    """Moller-Trumbore: does the ray Q + t*d (t > eps) hit any triangle?"""
    a, b, c = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]; e1, e2 = b - a, c - a; h = np.cross(d, e2); det = (e1 * h).sum(1); ok = np.abs(det) > 1e-12
    a, e1, e2, h, det = a[ok], e1[ok], e2[ok], h[ok], det[ok]; inv = 1 / det; hit = np.zeros(len(Q), bool)
    for o in range(0, len(Q), chunk):
        s = Q[o:o + chunk, None, :] - a[None]; u = (s * h).sum(-1) * inv; qv = np.cross(s, e1); v = (qv * d).sum(-1) * inv; t = (qv * e2).sum(-1) * inv
        hit[o:o + chunk] = ((u >= 0) & (v >= 0) & (u + v <= 1) & (t > eps)).any(1)
    return hit

def exposure(rig, M, rest_hem=-.80):
    """Leg points that are above the shorts hem at rest (should be covered) and are visible (unoccluded) from each view."""
    occ = merge(sum((rig.posed(m, M) for m in ('Shorts', 'Body', 'Arm_L', 'Arm_R')), []))
    res = {}
    for leg in ('Leg_L', 'Leg_R'):
        LP, _, _ = merge(rig.posed(leg, M)); rest = np.vstack([p['P'] for p in rig.meshes[leg]]); Q = LP[rest[:, 1] > rest_hem]
        res[leg] = {v: int((~occluded(Q, d, occ[0], occ[2])).sum()) for v, d in VIEWS.items()}
        res[leg]['covered'] = int(len(Q))
    return res

if __name__ == '__main__':
    rig = Rig(sys.argv[1]); clip = sys.argv[2] if len(sys.argv) > 2 else 'Run'; n = 12 if clip == 'Run' else 18
    rows = []
    for f in range(n):
        t = rig.duration(clip) * f / n; e = exposure(rig, rig.joint_mats(clip, t)); vis = sum(v[k] for v in e.values() for k in VIEWS)
        rows.append(dict(frame=f, visible=vis, **{k: [v[x] for x in VIEWS] for k, v in e.items()}))
    rest = exposure(rig, rig.joint_mats(None))
    print(json.dumps(dict(views=list(VIEWS), rest=rest, total_visible=sum(r['visible'] for r in rows), worst=max(r['visible'] for r in rows), frames=rows)))
