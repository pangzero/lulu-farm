"""Anatomical surface labels for reversible part extraction. No position edits."""
from pathlib import Path
import numpy as np,heapq,json
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-sketchfab-arm-down-20261019'
v=np.load(R/'review/lulu-sketchfab-color-20261019/baseline/geometry.npz');p,n,f=v['p'],v['n'],v['f']
u,inv=np.unique(p,axis=0,return_inverse=True);count=np.bincount(inv)
nn=np.stack([np.bincount(inv,weights=n[:,a])/count for a in range(3)],axis=1);nn/=np.maximum(np.linalg.norm(nn,axis=1),1e-20)[:,None]
f=inv[f];e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);e=np.unique(np.sort(e,axis=1),axis=0)
x,y,z=u.T;labels=np.zeros(len(u),np.uint8)
seeds={
 'left':{'A':[[.307109,.465402,.046161],[.251280,.541385,.218122],[.187403,.531787,.260886],[.241791,.459803,.177891],[.167408,.481398,.186245],[.23,.51,.25],[.22,.55,.23],[.145812,.568579,.248059],[.185803,.566179,.260565],[.225794,.548583,.262579],[.117819,.538185,.232265]],'B':[[.241388,.541385,.082153],[.20,.4,.14],[.26,.41,-.06],[.25,.52,-.03],[.16,.63,.20],[.075,.53,.17]]},
 'right':{'A':[[-.264,.25,-.033],[-.251,.228,-.053],[-.262,.188,-.161],[-.202,.252,-.235],[-.214,.200,-.242],[-.23,.225,-.245],[-.27,.29,-.08],[-.268358,.225058,-.194131],[-.251780,.185685,-.205970],[-.2794,.217,-.1066],[-.29,.36,-.08],[-.29,.40,-.055]],'B':[[-.239174,.241636,-.015627],[-.22,.158,-.23],[-.154383,.202263,-.201256],[-.22,.38,.09],[-.22,.4,-.18],[-.25,.48,-.10]]}
}
for which,val in [('left',1),('right',2)]:
 if which=='left':roi=(x>.075)&(y>.31)&(y<.645)&(z>-.105);border=(y>.61)|(y<.32)|(x<.085)|(z<-.095)
 else:roi=(x<-.145)&(y>.14)&(y<.52);border=(x>-.153)|(y<.15)|(y>.50)
 ids=np.where(roi)[0];lookup=np.full(len(u),-1,int);lookup[ids]=np.arange(len(ids));q=u[ids]
 edge=e[roi[e].all(1)];delta=u[edge[:,1]]-u[edge[:,0]];length=np.linalg.norm(delta,axis=1)
 pr=np.einsum('ij,ij->i',nn[edge[:,1]]-nn[edge[:,0]],delta)/np.maximum(length,1e-10)
 ww=length*(1+2000*np.maximum(-pr,0)**2)
 adj=[[] for _ in ids]
 for (a,b),w in zip(lookup[edge],ww):adj[a].append((int(b),float(w)));adj[b].append((int(a),float(w)))
 def dist(points,extra):
  starts=np.unique(np.r_[[np.linalg.norm(q-s,axis=1).argmin() for s in points],extra]).astype(int)
  d=np.full(len(q),np.inf);d[starts]=0;heap=[(0,int(i)) for i in starts];heapq.heapify(heap)
  while heap:
   da,a=heapq.heappop(heap)
   if da!=d[a]:continue
   for b,w in adj[a]:
    v=da+w
    if v<d[b]:d[b]=v;heapq.heappush(heap,(v,b))
  return d
 da=dist(seeds[which]['A'],[]);db=dist(seeds[which]['B'],np.where(border[ids])[0])
 sel=da<db;labels[ids[sel]]=val
 print(which,int(sel.sum()),'bounds',q[sel].min(0),q[sel].max(0))
# A triangle belongs wholly to one part: unlike blended weights it cannot pull
# a distant cheek/body vertex with the arm. Shared coordinates are duplicated.
fl=labels[f];face=np.zeros(len(f),np.uint8)
for val in [1,2]:face[(fl==val).sum(1)>=2]=val
out=D/'baseline/arm-labels-r02.npz';assert not out.exists();np.savez_compressed(out,u=u,inv=inv,labels=labels,face_labels=face,n=nn)
(out.with_suffix('.json')).write_text(json.dumps({'method':'curvature-weighted surface distances, face-majority; labels only','seeds':seeds,'face_counts':np.bincount(face).tolist()},indent=2));print(np.bincount(face))
