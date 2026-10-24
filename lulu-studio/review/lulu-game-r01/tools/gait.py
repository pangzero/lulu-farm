"""Run-clip damping: blend leg-joint rotations toward the bind pose and measure exposure, ground contact and stride.
damp(rig, 'Run', {'LeftLeg': k, ...}) edits the rig's sampled rotations in place (slerp(bind, anim, k)); build_game applies the same to the GLB.
"""
import sys, json, numpy as np
import pose
from build_game import JN

def damp_rotations(rest_q, out, k):
    return np.array([pose.slerp(np.asarray(rest_q, float), q.astype(float), k) for q in out], np.float32)

def damp(rig, clip, factors):
    ch = []
    for ni, path, tin, out, interp in rig.anims[clip]:
        nm = rig.g['nodes'][ni].get('name')
        if path == 'rotation' and nm in factors: out = damp_rotations(rig.g['nodes'][ni].get('rotation', [0, 0, 0, 1]), out, factors[nm])
        ch.append((ni, path, tin, out, interp))
    rig.anims[clip] = ch

def gait(rig, clip='Run', n=48):
    """Per-foot lowest point per frame; stride speed = mean |dz/dt| of the support foot while it is within 3 mm of the ground."""
    feet = {}
    for leg in ('Leg_L', 'Leg_R'):
        ys, zs = [], []
        for f in range(n):
            M = rig.joint_mats(clip, rig.duration(clip) * f / n); P, _, _ = pose.merge(rig.posed(leg, M)); i = P[:, 1].argmin(); ys.append(P[i, 1]); zs.append(P[:, 2][P[:, 1] < P[i, 1] + .01].mean())
        feet[leg] = (np.array(ys), np.array(zs))
    ground = min(v[0].min() for v in feet.values()); dt = rig.duration(clip) / n; sp = []
    for ys, zs in feet.values():
        c = ys < ground + .003; v = (np.roll(zs, -1) - zs) / dt; sp += list(np.abs(v[c & np.roll(c, -1)]))
    lift = max(v[0].max() for v in feet.values()) - ground
    return dict(ground=float(ground), max_lift=float(lift), support_speed=float(np.median(sp)) if sp else None, support_frames=len(sp))

if __name__ == '__main__':
    glb = sys.argv[1]; out = []
    for knee, hip in [(1, 1), (.75, 1), (.6, 1), (.5, 1), (.6, .85), (.5, .8)]:
        r = pose.Rig(glb); damp(r, 'Run', {'LeftLeg': knee, 'RightLeg': knee, 'LeftUpLeg': hip, 'RightUpLeg': hip})
        rows = [sum(v[k] for v in pose.exposure(r, r.joint_mats('Run', r.duration('Run') * f / 12)).values() for k in pose.VIEWS) for f in range(12)]
        out.append(dict(knee=knee, hip=hip, total=sum(rows), worst=max(rows), **gait(r))); print(json.dumps(out[-1]), flush=True)

def plants(rig, ref_rig, clip='Run', n=60, tol=.006):
    """Foot-plant check inside the reference clip's contact windows: lowest-20-vertex height above ground (mm) and backward foot speed."""
    def track(r):
        T = r.duration(clip); o = {}
        for leg in ('Leg_L', 'Leg_R'):
            Y, Z = [], []
            for f in range(n):
                P, _, _ = pose.merge(r.posed(leg, r.joint_mats(clip, T * f / n))); i = np.argsort(P[:, 1])[:20]; Y.append(P[i, 1].mean()); Z.append(P[i, 2].mean())
            o[leg] = np.array(Y), np.array(Z)
        return o, T / n
    O, dt = track(ref_rig); N, _ = track(rig); g = min(O[l][0].min() for l in O); res = {}
    for leg in O:
        c = O[leg][0] < g + tol; cc = c & np.roll(c, -1); v = -(np.roll(N[leg][1], -1) - N[leg][1])[cc] / dt; y = (N[leg][0][c] - g) * 1000
        res[leg] = dict(contact_keys=int(c.sum()), height_mm=[round(float(y.min()), 1), round(float(y.max()), 1)], speed_median=round(float(np.median(v)), 4), speed_p10_p90=np.percentile(v, [10, 90]).round(3).tolist())
    return res
