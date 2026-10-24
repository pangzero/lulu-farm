"""Eye-patch fit check: are the flush eye patches in front of the (decimated) head surface?
For every eye vertex and triangle centroid: signed distance to the head surface along the head's interpolated normal (+ = in front).
For every head vertex under an eye: signed distance to the eye patch along the eye normal (+ = head pokes through the eye).
Units are rig-local (x0.6314 for world metres at 1.2 height). Usage: check_eyes.py game.glb [game2.glb ...] [--source new.glb]
"""
import sys, json, numpy as np
from pathlib import Path
import clh, geo
from newparts import load_new

def surf_from_glb(g, b, name):
    m = next(m for m in g['meshes'] if m['name'] == name); Ps, Ns, Is = [], [], []; o = 0
    for p in m['primitives']:
        P = clh.accessor(g, b, p['attributes']['POSITION']); N = clh.accessor(g, b, p['attributes']['NORMAL'])
        Is.append(clh.accessor(g, b, p['indices']).reshape(-1, 3).astype(np.int64) + o); Ps.append(P); Ns.append(N); o += len(P)
    return np.vstack(Ps), np.vstack(Ns), np.vstack(Is)

def surf_from_source(parts, key):
    Ps, Ns, Is = [], [], []; o = 0
    for p in parts[key]:
        Ps.append(p['P']); Ns.append(p['N']); Is.append(p['I'].astype(np.int64) + o); o += len(p['P'])
    return np.vstack(Ps), np.vstack(Ns), np.vstack(Is)

def signed(Q, P, N, I):
    s = geo.Surf(P, I); F, B, D = s.query(Q); foot = s.interp(F, B, P); n = s.interp(F, B, N)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20); return ((Q - foot) * n).sum(1), D

def check(head, eyes):
    HP, HN, HI = head; out = {}
    for nm, (EP, EN, EI) in eyes.items():
        Q = np.vstack([EP, EP[EI].mean(1), (EP[EI[:, [0, 1, 1, 2, 2, 0]]].reshape(-1, 2, 3).mean(1))])
        sd, _ = signed(Q, HP, HN, HI)
        # head vertices under this eye (closest eye point is interior, within 1.5 mm)
        c = EP.mean(0); r = np.linalg.norm(EP - c, axis=1).max()
        hv = np.where(np.linalg.norm(HP - c, axis=1) < r * 1.05)[0]
        hs, hd = signed(HP[hv], EP, EN, EI) if len(hv) else (np.zeros(0), np.zeros(0))
        poke = hs[(hd < .0015) & (hs > 0)] if len(hv) else np.zeros(0)
        out[nm] = dict(eye_samples=int(len(Q)), eye_min_offset=float(sd.min()), eye_p01_offset=float(np.percentile(sd, 1)), eye_median_offset=float(np.median(sd)),
                       eye_samples_behind_head=int((sd < 0).sum()), eye_samples_below_2e4=int((sd < 2e-4).sum()),
                       head_verts_near=int(len(hv)), head_verts_poking_through=int(len(poke)), head_poke_max=float(poke.max()) if len(poke) else 0.0)
    return out

if __name__ == '__main__':
    args = sys.argv[1:]; res = {}
    if '--source' in args:
        i = args.index('--source'); src = args[i + 1]; del args[i:i + 2]
        _, _, parts, _ = load_new(src)
        res['source'] = check(surf_from_source(parts, 'Lulu_Head_Mirrored'), {k: surf_from_source(parts, 'Lulu_' + k) for k in ('Eye_ScreenLeft', 'Eye_ScreenRight')})
    for a in args:
        g, b = clh.load(Path(a))
        res[Path(a).name] = check(surf_from_glb(g, b, 'Head'), {k: surf_from_glb(g, b, k) for k in ('Eye_ScreenLeft', 'Eye_ScreenRight')})
    print(json.dumps(res, indent=1))
