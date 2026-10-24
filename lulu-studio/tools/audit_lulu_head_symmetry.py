"""Fit the new sculpture's tilted head plane; read-only source analysis."""
from pathlib import Path
import math, json
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=Path(__file__).resolve().parents[1]
D=R/'review/lulu-head-mirror-20261021'
a=np.load(R/'review/lulu-sketchfab-color-20261019/baseline/geometry.npz')
p,inv=np.unique(a['p'],axis=0,return_inverse=True)
f=inv[a['f']]
t=math.radians(8.7)
h=p.copy(); h[:,0]=np.cos(t)*p[:,0]+np.sin(t)*(p[:,1]-.72)
h[:,1]=-np.sin(t)*p[:,0]+np.cos(t)*(p[:,1]-.72)+.72
mask=(h[:,1]>.625)&(h[:,1]<.88)
ff=f[np.all(mask[f],axis=1)]
bvh=BVHTree.FromPolygons(p.tolist(),ff.tolist(),all_triangles=True)
keep=mask&(h[:,0]<-.035)&(h[:,0]>-.245)
# Avoid the circular relief eyes and ears; fit broad skin on front/back/top.
keep &= ~((p[:,2]>.10)&(h[:,1]>.755))
sample=p[keep][::max(1,int(keep.sum()/2200))]
def normal(v):
    roll,yaw,offset=v
    rr,yy=math.radians(roll),math.radians(yaw)
    return np.array([math.cos(rr)*math.cos(yy),math.sin(rr)*math.cos(yy),math.sin(yy)])
def score(v):
    n=normal(v); c=np.array([v[2],.72,0.])
    pp=sample-2*np.einsum('ij,j->i',sample-c,n)[:,None]*n
    ds=np.array([bvh.find_nearest(Vector(q))[3] for q in pp])
    ds=np.sort(ds); return float(np.mean(ds[:int(len(ds)*.85)]**2))
v=np.array([8.7,0.,0.]); best=score(v)
for step in [(2.,2.,.006),(.7,.7,.002),(.2,.2,.0007),(.06,.06,.0002)]:
    for repeat in range(12):
        changed=False
        for axis,delta in enumerate(step):
            opts=[]
            for sign in [-1,1]:
                q=v.copy();q[axis]+=sign*delta
                opts.append((score(q),q))
            value,q=min(opts,key=lambda item:item[0])
            if value<best:best=value;v=q;changed=True
        if not changed:break
    print('fit',v.tolist(),'rms',math.sqrt(best),flush=True)
n=normal(v); up=np.array([0.,1.,0.]); up-=np.dot(up,n)*n;up/=np.linalg.norm(up)
front=np.cross(n,up); basis=np.array([n,up,front]); center=np.array([v[2],.72,0.])
hh=np.einsum('ij,kj->ik',p-center,basis)
slices=[]
for y in np.arange(.43,.901,.02):
    band=p[(np.abs(hh[:,1]+.72-y)<.002)&(hh[:,0]<-.01)]
    if len(band):slices.append({'local_y':round(float(y),3),'min':band.min(0).tolist(),'max':band.max(0).tolist(),'count':len(band)})
report={'roll_degrees':v[0],'yaw_degrees':v[1],'plane_x_at_y_072':v[2],'basis_rows':basis.tolist(),'center':center.tolist(),'trimmed_rms':math.sqrt(best),'fit_samples':len(sample),'slices':slices,'note':'Fit broad unaffected skin, excluding eyes, ears and hand contact. Symmetry is approximate.'}
(D/'symmetry-fit.json').write_text(json.dumps(report,indent=2))
np.savez_compressed(D/'baseline/welded-source.npz',p=p,f=f,head_basis=basis,head_center=center)
print(json.dumps(report,indent=2),flush=True)
