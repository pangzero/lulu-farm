"""Run-clip edit for the shorts. The forward thigh swing (UpLeg flexes up to ~67 deg) turns the short shorts tube so its opening faces
forward and the leg shows under the front hem. Knee damping makes it worse and sinks the foot; plain hip damping lifts the planted foot
(up to 44 mm) and makes it skate. So the stride itself is shortened with two-bone IK:
each ankle's forward (Z) offset from its hip joint is scaled by STRIDE, its height is kept (ground contact unchanged), hip/knee are solved
in the original bend plane, and the foot keeps its world orientation. The stance foot still slides back at a constant STRIDE x source speed,
so the controller reference speed scales by STRIDE.
Usage: run_edit.py in.glb out.glb [stride=0.6] [swing_hip=0.5] [--ref ref.glb]   (ref = glb whose legs are measured, default in.glb; use LOD0 for LOD1)
"""
import sys, json, struct, numpy as np
from pathlib import Path
import clh, pose, gait

LEGS = (('LeftUpLeg', 'LeftLeg', 'LeftFoot'), ('RightUpLeg', 'RightLeg', 'RightFoot'))

def ortho(M):
    u, _, vt = np.linalg.svd(M[:3, :3]); return u @ vt

def frame(d, n):
    e1 = d / np.linalg.norm(d); e2 = n - (n @ e1) * e1; e2 /= np.linalg.norm(e2); return np.c_[e1, e2, np.cross(e1, e2)]

def quat(R):
    w = np.sqrt(max(0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2; x = np.sqrt(max(0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2
    y = np.sqrt(max(0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2; z = np.sqrt(max(0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2
    x = np.copysign(x, R[2, 1] - R[1, 2]); y = np.copysign(y, R[0, 2] - R[2, 0]); z = np.copysign(z, R[1, 0] - R[0, 1]); q = np.array([x, y, z, w]); return q / np.linalg.norm(q)

def solve_leg(W, ids, stride):
    """New global rotations (thigh, shin, foot) for one leg at one pose."""
    up, kn, ft = ids; H, K0, A0 = W[up][:3, 3], W[kn][:3, 3], W[ft][:3, 3]; L1, L2 = np.linalg.norm(K0 - H), np.linalg.norm(A0 - K0)
    n = np.cross(K0 - H, A0 - K0); n = n / np.linalg.norm(n) if np.linalg.norm(n) > 1e-9 else frame(K0 - H, np.array([1., 0, 0]))[:, 1]
    A = H + (A0 - H) * [1, 1, stride]; D = min(np.linalg.norm(A - H), (L1 + L2) * .9999); u = (A - H) / np.linalg.norm(A - H); A = H + u * D
    v = np.cross(n, u); v /= np.linalg.norm(v); a = (L1 * L1 - L2 * L2 + D * D) / (2 * D); h = np.sqrt(max(L1 * L1 - a * a, 0))
    v0 = np.cross(n, (A0 - H) / np.linalg.norm(A0 - H)); side = np.sign((K0 - H) @ v0) or 1.; K = H + u * a + side * h * v
    Rt = frame(K - H, n) @ frame(K0 - H, n).T @ ortho(W[up]); Rs = frame(A - K, n) @ frame(A0 - K0, n).T @ ortho(W[kn])
    return Rt, Rs, ortho(W[ft])

def edited_run(ref, stride, swing_hip=1., foot=1., clip='Run'):
    orig = pose.Rig(ref); new = pose.Rig(ref); idx = {n.get('name'): i for i, n in enumerate(new.g['nodes'])}
    parent = {c: i for i, n in enumerate(new.g['nodes']) for c in n.get('children', [])}
    ch = []
    for ni, path, tin, out, interp in new.anims[clip]:
        nm = new.g['nodes'][ni].get('name'); leg = next((l for l in LEGS if nm in l), None)
        if leg and path == 'rotation':
            out = out.copy()
            for k, t in enumerate(tin):
                W = orig.worlds(clip, float(t)); R = dict(zip(leg, solve_leg(W, [idx[x] for x in leg], stride)))
                Rp = R.get(new.g['nodes'][parent[ni]].get('name')); Rp = ortho(W[parent[ni]]) if Rp is None else Rp
                q = quat(Rp.T @ R[nm]); out[k] = q if q @ out[k] >= 0 else -q
        ch.append((ni, path, tin, out, interp))
    new.anims[clip] = ch
    # the visible leg stump is skinned to Foot and the ankle sits at the hem, so heel-strike dorsiflexion tips the stump rim out of the hem
    if foot < 1: gait.damp(new, clip, {'LeftFoot': foot, 'RightFoot': foot})
    if swing_hip < 1: swing_damp(new, clip, swing_hip)
    # IK keeps ankle height, so the shortened stride leaves the feet a few mm high: shift Hips down by one constant (plants unchanged)
    T = orig.duration(clip); ts = np.linspace(0, T, 49); d = min(lowest(orig, clip, t) for t in ts) - min(lowest(new, clip, t) for t in ts)
    hips = idx['Hips']; up = np.linalg.solve(ortho(clh.worlds(new.g)[parent[hips]]), [0, 1, 0])
    new.anims[clip] = [(ni, path, tin, out + (up * d).astype(np.float32) if ni == hips and path == 'translation' else out, interp) for ni, path, tin, out, interp in new.anims[clip]]
    return orig, new

def lowest(rig, clip, t):
    M = rig.joint_mats(clip, t); return min(pose.merge(rig.posed(l, M))[0][:, 1].min() for l in ('Leg_L', 'Leg_R'))

def swing_damp(rig, clip, hip, lo=.004, hi=.03, clear=.005):
    """Damp each UpLeg toward bind (down to `hip`) only while its own foot is in the air (smoothstep lo..hi above ground); stance keys
    untouched. Per key the damping is relaxed (bisection) until that foot stays >= `clear` above the ground, so the Hips never move
    and the planted foot is exactly the IK result."""
    before = pose.Rig.__new__(pose.Rig); before.__dict__.update(rig.__dict__); before.anims = dict(rig.anims)
    fh = lambda r, leg, t: pose.merge(r.posed(leg, r.joint_mats(clip, t)))[0][:, 1].min()
    ground = min(fh(before, l, t) for l in ('Leg_L', 'Leg_R') for t in np.linspace(0, before.duration(clip), 49))
    probe = pose.Rig.__new__(pose.Rig); probe.__dict__.update(rig.__dict__); ch = []
    for ci, (ni, path, tin, out, interp) in enumerate(rig.anims[clip]):
        leg = {'LeftUpLeg': 'Leg_L', 'RightUpLeg': 'Leg_R'}.get(rig.g['nodes'][ni].get('name'))
        if leg and path == 'rotation':
            rest = np.asarray(rig.g['nodes'][ni].get('rotation', [0, 0, 0, 1]), float); out = out.copy()
            for k, t in enumerate(tin):
                a = np.clip((fh(before, leg, float(t)) - ground - lo) / (hi - lo), 0, 1); a = a * a * (3 - 2 * a)
                if a == 0: continue
                def at(f):
                    o2 = out.copy(); o2[k] = pose.slerp(rest, out[k].astype(float), f); probe.anims = {**before.anims, clip: [c if c[0] != ni or c[1] != path else (ni, path, tin, o2, interp) for c in before.anims[clip]]}
                    return o2[k], fh(probe, leg, float(t)) - ground
                f0 = 1 - a * (1 - hip); q, h = at(f0)
                if h < clear:
                    a_, b_ = f0, 1.
                    for _ in range(12):
                        m = (a_ + b_) / 2; q, h = at(m)
                        if h < clear: a_ = m
                        else: b_ = m
                    q, _ = at(b_)
                out[k] = q
        ch.append((ni, path, tin, out, interp))
    rig.anims[clip] = ch

def patch(src, dst, new, clip='Run', note=None):
    g, b = clh.load(Path(src)); an = next(a for a in g['animations'] if a['name'] == clip); outs = {(ni, p): o for ni, p, _, o, _ in new.anims[clip]}
    for c in an['channels']:
        o = outs[(c['target']['node'], c['target']['path'])]; a = g['accessors'][an['samplers'][c['sampler']]['output']]; v = g['bufferViews'][a['bufferView']]
        raw = np.ascontiguousarray(o, '<f4').tobytes(); off = v.get('byteOffset', 0) + a.get('byteOffset', 0); assert len(raw) == a['count'] * o.shape[1] * 4 and 'byteStride' not in v
        b[off:off + len(raw)] = raw
    if note: g.setdefault('extras', {}).setdefault('lulu_game', {})['run_edit'] = note
    js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4); b = bytes(b) + b'\0' * ((-len(b)) % 4)
    Path(dst).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(js) + len(b)) + struct.pack('<II', len(js), 0x4e4f534a) + js + struct.pack('<II', len(b), 0x004e4942) + b)

if __name__ == '__main__':
    a = sys.argv[1:]; ref = a[a.index('--ref') + 1] if '--ref' in a else a[0]; a = [x for x in a if x not in ('--ref', ref)] if '--ref' in a else a
    src, dst = a[0], a[1]; stride = float(a[2]) if len(a) > 2 else .6; swing = float(a[3]) if len(a) > 3 else .5; foot = float(a[4]) if len(a) > 4 else 1.
    orig, new = edited_run(ref, stride, swing, foot)
    rows = [sum(v[k] for v in pose.exposure(new, new.joint_mats('Run', new.duration('Run') * f / 12)).values() for k in pose.VIEWS) for f in range(12)]
    gn, go = dict(gait.gait(new), plants=gait.plants(new, orig)), gait.gait(orig)
    note = dict(stride=stride, swing_hip=swing, foot=foot, method='two-bone IK stride (ankle fwd offset x stride, height kept, bend plane kept, foot world rotation kept) + swing-only UpLeg damping with 5 mm foot clearance + constant Hips offset to original ground', exposure_rows=rows, gait_new=gn, gait_orig=go)
    patch(src, dst, new, note=note); print(json.dumps(note))
