import numpy as np
from remove_meshy_tail import triangulate_polygon,cross2
from refine_meshy_eye_natural import R
m=np.load(R/'review/meshy-eye-bridge-analysis.npz');p=m['p'];c=m['c'];t=m['t'];inv=m['inv'];U=p[m['first']];ut=inv[t]
P=p[t].mean(1);x,y,z=P.T;q=np.sqrt(((abs(x)-.232)/.079)**2+((y-.525)/.07)**2)
vertex_eye=(abs(p[:,0])>.10)&(abs(p[:,0])<.37)&(p[:,1]>.43)&(p[:,1]<.62)&(p[:,2]>.14)&(((c[:,2]>c[:,0]*.85)&(c[:,2]>c[:,1]*.85))| (c.mean(1)<110))
for ri in [.99,1.015,1.045,1.07,1.10]:
 rm=(q>ri)&(q<1.66)&((y-.525)/.07<.4)&(z>.14)&~np.any(vertex_eye[t],axis=1)
 E=np.sort(np.concatenate([ut[rm][:,[0,1]],ut[rm][:,[1,2]],ut[rm][:,[2,0]]]),axis=1);E,n=np.unique(E,axis=0,return_counts=True);be=E[n==1];ids,deg=np.unique(be,return_counts=True)
 if np.any(deg!=2):print(ri,'bad degree',dict(zip(*np.unique(deg,return_counts=True))));continue
 adj={int(i):[] for i in ids}
 for a,b in be:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
 unseen=set(map(int,ids));loops=[]
 while unseen:
  s=next(iter(unseen));loop=[s];last=-1;i=s
  while True:
   j=next(v for v in adj[i] if v!=last)
   if j==s:break
   loop.append(j);last,i=i,j
  unseen-=set(loop);loops.append(loop)
 results=[]
 for loop in loops:
  b=U[loop];area=sum(cross2(a[:2],v[:2]) for a,v in zip(b,np.roll(b,-1,axis=0)))
  if area>0:b=b[::-1]
  try:tri=triangulate_polygon(b[:,:2]);ear=True
  except AssertionError:ear=False
  results.append((len(loop),bool(ear),[round(v,4) for v in b.mean(0)]))
 print(ri,'faces',int(rm.sum()),'loops',results)
