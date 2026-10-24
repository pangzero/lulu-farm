"""Read-only local rig topology, preservation and pose checks."""
import json,struct,hashlib,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];REV=sys.argv[1] if len(sys.argv)>1 else 'r07';O=R/'review/lulu-rig-separation-20261018'/REV

def read(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);r=b[28+n:]
 def ac(i):
  a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
  return np.ndarray((a['count'],sz),dtype=dt,buffer=r,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*dt.itemsize),dt.itemsize)).copy()
 P=[];F=[];J=[];W=[];N=[]
 for pr in g['meshes'][0]['primitives']:
  p=ac(pr['attributes']['POSITION']);F.extend(ac(pr['indices']).reshape(-1,3)+len(P));P.extend(p);J.extend(ac(pr['attributes']['JOINTS_0']));W.extend(ac(pr['attributes']['WEIGHTS_0']));N.extend(ac(pr['attributes']['NORMAL']))
 return g,np.array(P),np.array(F),np.array(J),np.array(W),np.array(N),r
base=read(R/'public/models/rig/lulu-rig-r04.glb');new=read(R/f'public/models/rig/lulu-rig-{REV}.glb')
g,p,f,j,w,n,raw=new
u,idx,iv=np.unique(np.round(p,6),axis=0,return_index=True,return_inverse=True);uf=iv[f];uf=uf[(uf[:,0]!=uf[:,1])&(uf[:,1]!=uf[:,2])&(uf[:,0]!=uf[:,2])]
e=np.concatenate([uf[:,[0,1]],uf[:,[1,2]],uf[:,[2,0]]]);e=np.sort(e,axis=1);e=e[e[:,0]!=e[:,1]];ed,cnt=np.unique(e,axis=0,return_counts=True)
parent=np.arange(len(u))
def root(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
for a,b in ed:
 a=root(a);b=root(b)
 if a!=b:parent[b]=a
comps=len(set(root(i) for i in range(len(u))))
basehead={tuple(q) for q in np.round(base[1][base[1][:,1]>-.10],5)};newhead={tuple(q) for q in np.round(p[p[:,1]>-.10],5)}
head=p[:,1]>-.055;names=[g['nodes'][i]['name'] for i in g['skins'][0]['joints']];headid=names.index('Head')
report={'revision':REV,'position_weld_tolerance':1e-6,'connected_components':comps,'boundary_edges':int((cnt==1).sum()),'nonmanifold_edges':int((cnt>2).sum()),'head_positions_preserved_to_1e_5':basehead==newhead,'head_weights_rigid':bool(np.all(np.sum(w*(j==headid),axis=1)[head]>.99999)),'no_unweighted_vertices':bool(np.all(w.sum(1)>.99999)),'max_weight_sum_error':float(abs(w.sum(1)-1).max()),'original_embedded_binary_prefix_preserved':raw[:len(base[-1])]==base[-1],'materials_preserved':g['materials'][:2]==base[0]['materials'],'pose_checks':{}}

def pose(data,ang):
 gg,pp,ff,jj,ww,nn,rr=data;ns=[gg['nodes'][i]['name'] for i in gg['skins'][0]['joints']];out=pp.astype(float).copy()
 for sd,sgn in [('Left',1),('Right',-1)]:
  ids=[ns.index(sd+x) for x in ['Arm','ForeArm','Hand']];a=np.radians(ang*sgn);rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]]);pivot=np.array([.405*sgn,-.155,-.075]);delta=(pp-pivot)@rot.T+pivot-pp
  armw=np.sum(ww*np.isin(jj,ids),axis=1);out+=delta*armw[:,None]
 return out
for deg in [5,10,15]:
 row={}
 for tag,data in [('before',base),('after',new)]:
  gg,pp,ff,jj,ww,nn,rr=data;qq=pose(data,deg);ee=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);mid=pp[ee].mean(1);mask=(mid[:,1]<-.30)&(mid[:,1]>-.53)&(abs(mid[:,0])>.35);ee=ee[mask];l0=np.linalg.norm(pp[ee[:,0]]-pp[ee[:,1]],axis=1);l1=np.linalg.norm(qq[ee[:,0]]-qq[ee[:,1]],axis=1);good=l0>.001
  strain=l1[good]/l0[good];waist=(pp[:,1]<-.44)&(pp[:,1]>-.52)&(abs(pp[:,0])<.40)
  row[tag]={'edge_stretch_p99':float(np.quantile(strain,.99)),'edge_stretch_max':float(strain.max()),'central_waist_max_displacement':float(np.linalg.norm(qq[waist]-pp[waist],axis=1).max()),'head_max_displacement':float(np.linalg.norm(qq[pp[:,1]>-.055]-pp[pp[:,1]>-.055],axis=1).max())}
 report['pose_checks'][str(deg)]=row
# Horizontal contour counts below shoulders: torso + separate arm loops.
for y in [-.300347,-.400347,-.480347]:
 tr=u[uf];hit=(tr[:,:,1].min(1)<y)&(tr[:,:,1].max(1)>y);segments=[]
 for face,t in zip(uf[hit],tr[hit]):
  pts=[]
  for a,b in [(0,1),(1,2),(2,0)]:
   if (t[a,1]-y)*(t[b,1]-y)<0:pts.append(tuple(sorted([int(face[a]),int(face[b])])))
  if len(pts)==2:segments.append(pts)
 adj={}
 for a,b in segments:adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
 seen=set();lengths=[]
 for a in adj:
  if a in seen:continue
  stack=[a];component=[]
  while stack:
   q=stack.pop()
   if q in seen:continue
   seen.add(q);component.append(q);stack.extend(adj[q]-seen)
  if len(component)>10:lengths.append(len(component))
 report.setdefault('cross_sections',{})[str(y)]={'significant_loops':len(lengths),'samples':lengths}
for fn in ['lulu-official-v1.glb','rig/lulu-rig-r04.glb']:
 report.setdefault('protected_sha256',{})[fn]=hashlib.sha256((R/'public/models'/fn).read_bytes()).hexdigest()
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
