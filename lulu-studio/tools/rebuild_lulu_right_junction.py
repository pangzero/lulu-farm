"""Only anatomical right shoulder/inner-arm fair patches; source exterior fixed."""
from pathlib import Path
import sys,json,hashlib,shutil,numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
sys.path.insert(0,str(Path(__file__).parent))
from lulu_patch_io import read_glb,triangles,write_glb
R=Path(__file__).resolve().parents[1];rev=sys.argv[sys.argv.index('--')+1];arm_only='--arm-only' in sys.argv;src=R/'public/models/modular'/('right-junction-r04' if arm_only else 'parts-v2');out=R/'public/models/modular'/rev;rep=R/'review/lulu-right-junction-20261018'/rev;out.mkdir(parents=True,exist_ok=True);rep.mkdir(parents=True,exist_ok=True);assert not (out/'lulu-assembled.glb').exists()
g,raw=read_glb(src/'lulu-assembled.glb')
def key(p):return tuple(np.round(p.astype(float),6))
def loops(ts):
 ed={};verts={}
 for t in ts:
  ks=[key(v[:3]) for v in t]
  if len(set(ks))<3:continue
  for k,v in zip(ks,t):verts[k]=v
  for i in range(3):ed.setdefault(tuple(sorted([ks[i],ks[(i+1)%3]])),[]).append((ks[i],ks[(i+1)%3]))
 nxt={a:b for ee in ed.values() if len(ee)==1 for a,b in ee};ls=[]
 while nxt:
  start=next(iter(nxt));cur=start;ids=[]
  while cur in nxt:
   ids.append(cur);cur=nxt.pop(cur)
   if cur==start:break
  assert cur==start,('open boundary',len(ids))
  if len(ids)>2:ls.append(np.array([verts[k] for k in ids]))
 return ls

def smooth_interp(x,xs,ys):
 xs=np.asarray(xs);ys=np.asarray(ys);m=np.gradient(ys,xs);x=np.clip(x,xs[0],xs[-1]);i=np.clip(np.searchsorted(xs,x)-1,0,len(xs)-2);h=xs[i+1]-xs[i];t=(x-xs[i])/h
 return (2*t**3-3*t*t+1)*ys[i]+(t**3-2*t*t+t)*h*m[i]+(-2*t**3+3*t*t)*ys[i+1]+(t**3-t*t)*h*m[i+1]
def body_surface(y,z):
 yc=np.array([-.65,-.54,-.48,-.40,-.32,-.25,-.20,-.13,-.09]);width=smooth_interp(y,yc,[.47,.49,.475,.457,.445,.435,.43,.44,.45]);front=smooth_interp(y,yc,[.23,.295,.302,.292,.27,.242,.22,.216,.23]);back=smooth_interp(y,yc,[-.41,-.45,-.447,-.431,-.41,-.39,-.38,-.366,-.36]);q=np.clip(np.abs((z-(front+back)/2)/((front-back)/2)),0,.9999)
 return width*np.power(1-np.power(q,2.5),1/2.5)

def disk_patch(ring,bulge,body=False):
 # Input orientation matches the removed surface. Circle parameterization
 # avoids projecting nonplanar concave seams onto a folded world-space fan.
 xyz=ring[:,:3].astype(float);length=np.linalg.norm(np.roll(xyz,-1,axis=0)-xyz,axis=1);ang=2*np.pi*np.r_[0,np.cumsum(length[:-1])]/length.sum();uv=np.c_[np.cos(ang),np.sin(ang)];N=len(ring)
 grid=np.array([(x,y) for x in np.arange(-.96,.961,.045) for y in np.arange(-.96,.961,.045) if x*x+y*y<.94**2]);domain=np.concatenate([uv,grid]);e=[(i,(i+1)%N) for i in range(N)];v,edges,faces,orig,_,_=delaunay_2d_cdt([Vector(q) for q in domain],e,[list(range(N))],1,1e-10,True);v=np.array(v);f=np.array(faces);assert f.shape[1]==3
 p=np.zeros((len(v),3));fixed=np.zeros(len(v),bool);bound={}
 for i,ids in enumerate(orig):
  ids=[j for j in ids if j<N]
  if ids:
   assert len(ids)==1,('merged boundary points',ids);j=ids[0];fixed[i]=True;p[i]=xyz[j];bound[i]=j
 assert fixed.sum()==N,(fixed.sum(),N)
 if body:p[fixed,0]+=body_surface(p[fixed,1],p[fixed,2])
 # Positive cotangent FEM weights on a well-spaced planar disk.
 edgeweights={}
 for t in f:
  for j in range(3):
   a,b,c=t[j],t[(j+1)%3],t[(j+2)%3];da=v[a]-v[c];db=v[b]-v[c];cot=np.dot(da,db)/max(abs(da[0]*db[1]-da[1]*db[0]),1e-14);k=tuple(sorted([int(a),int(b)]));edgeweights[k]=edgeweights.get(k,0)+cot*.5
 e=np.array(list(edgeweights));w=np.maximum(np.array(list(edgeweights.values())),1e-8);diag=np.bincount(e.reshape(-1),weights=np.repeat(w,2),minlength=len(v));ii=np.flatnonzero(~fixed);unknown=np.full(len(v),-1);unknown[ii]=np.arange(len(ii));inside=(~fixed[e]).all(1);ie=unknown[e[inside]];iw=w[inside];dd=diag[ii]
 def mat(x):return dd*x-np.bincount(ie[:,0],weights=iw*x[ie[:,1]],minlength=len(ii))-np.bincount(ie[:,1],weights=iw*x[ie[:,0]],minlength=len(ii))
 residuals=[]
 for axis in range(3):
  rhs=np.bincount(e[:,0],weights=w*p[e[:,1],axis],minlength=len(v))+np.bincount(e[:,1],weights=w*p[e[:,0],axis],minlength=len(v));rhs=rhs[ii];x=np.full(len(ii),xyz[:,axis].mean());r=rhs-mat(x);z=r/dd;d=z.copy();rz=np.dot(r,z)
  for it in range(3000):
   ad=mat(d);alpha=rz/max(np.dot(d,ad),1e-30);x+=alpha*d;r-=alpha*ad
   if np.linalg.norm(r)<1e-9:break
   z=r/dd;nrz=np.dot(r,z);d=z+(nrz/rz)*d;rz=nrz
  p[ii,axis]=x;residuals.append({'axis':axis,'iterations':it,'residual':float(np.linalg.norm(r))})
 if body:p[:,0]-=body_surface(p[:,1],p[:,2])
 else:
  rr=np.sum(v*v,axis=1);p[ii,0]+=bulge*np.maximum(0,1-rr[ii])
 # Use area-weighted geometry normals, preserve source normals at the seam.
 nn=np.zeros_like(p);face=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
 for j in range(3):np.add.at(nn,f[:,j],face)
 nn/=np.maximum(np.linalg.norm(nn,axis=1,keepdims=True),1e-12)
 rgb=np.array([1,.91,.34]);color=((rgb+.055)/1.055)**2.4;attrs=np.c_[p,nn,np.zeros((len(p),2)),np.tile(color,(len(p),1))]
 for i,j in bound.items():attrs[i,:]=ring[j]
 attrs[:,8:11]=color
 return attrs[f],{'boundary':N,'new_vertices':len(v),'new_triangles':len(f),'cg':residuals,'bulge':bulge,'boundary_max_position_delta':float(np.max(np.abs(attrs[list(bound),:3]-ring[list(bound.values()),:3])))}
def trim_inner(ts,ms):
 # Remove only the torso-side fringe carried by the arm partition. Never
 # touch Body; keep the rounded outside and palm below the narrow trim band.
 field=ts[:,:,0]-np.interp(ts[:,:,1],[-.65,-.56,-.50,-.40,-.30,-.20,-.12,-.10],[-.30,-.43,-.47,-.48,-.46,-.435,-.40,-.35]);out=[];mats=[];cache={};clipped=0
 for tri,mi,values in zip(ts,ms,field):
  if np.all(values<=0):out.append(tri);mats.append(mi);continue
  if np.all(values>0):clipped+=1;continue
  poly=[];clipped+=1
  for j in range(3):
   k=(j+1)%3;a,b=tri[j],tri[k];va,vb=values[j],values[k]
   if va<=0:poly.append(a)
   if (va<=0)!=(vb<=0):
    alpha=va/(va-vb);p=a+(b-a)*alpha;edge=tuple(sorted([key(a[:3]),key(b[:3])]));p[:3]=cache.setdefault(edge,p[:3].copy());p[3:6]/=max(np.linalg.norm(p[3:6]),1e-12);poly.append(p)
  for j in range(1,len(poly)-1):
   t=np.array([poly[0],poly[j],poly[j+1]])
   if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-14:out.append(t);mats.append(mi)
 return np.array(out),np.array(mats),clipped
parts=[];stats=[]
for mesh in g['meshes']:
 name=mesh['name'];t,m=triangles(g,raw,mesh)
 if name not in (['Arm_R'] if arm_only else ['Arm_R','Body']):parts.append((name,t,m));continue
 if name=='Arm_R' and '--trim-inner' in sys.argv:
  exterior,em,clipped=trim_inner(t[m!=2],m[m!=2]);ls=loops(exterior);print('trim inner loops',[(len(l),l[:,:3].min(0).tolist(),l[:,:3].max(0).tolist()) for l in ls],flush=True);assert 1<=len(ls)<=2
  added=[];infos=[]
  for ring in ls:
   new,info=disk_patch(ring[::-1],.095 if np.ptp(ring[:,1])>.1 else .003);added.append(new);infos.append(info)
  new=np.concatenate(added);parts.append((name,np.concatenate([exterior,new]),np.concatenate([em,np.full(len(new),2)])));stats.append(dict(part=name,trimmed_hidden_source_triangles=clipped,body_untouched=True,patches=infos));continue
 if name=='Arm_R':mask=m==2
 else:
  c=t[:,:,:3].mean(1);mask=(m==2)&(c[:,0]<-.29)&(c[:,1]>-.415)&(c[:,1]<-.112)
 patch=t[mask];ls=loops(patch);print(name,'boundaries',[(len(l),l[:,:3].min(0).tolist(),l[:,:3].max(0).tolist()) for l in ls],flush=True)
 assert len(ls)==1,'Need a single local patch; do not silently expand'
 ring=ls[0]
 # Join shading to preserved exterior normals, never the old fan normals.
 seamkeys={key(v[:3]) for v in ring};source_normals={}
 for v in t[~mask].reshape(-1,11):
  k=key(v[:3])
  if k in seamkeys:source_normals[k]=v[3:6]
 for v in ring:
  k=key(v[:3])
  if k in source_normals:v[3:6]=source_normals[k]
 new,info=disk_patch(ring,(.14 if arm_only else .058) if name=='Arm_R' else 0,body=name=='Body');nt=np.concatenate([t[~mask],new]);nm=np.concatenate([m[~mask],np.full(len(new),2)]);parts.append((name,nt,nm));info.update(part=name,removed_patch_triangles=int(mask.sum()),fixed_triangles=int((~mask).sum()));stats.append(info)
write_glb(out/'lulu-assembled.glb',g,raw,parts,rev)
for name,t,m in parts:
 if name in (['Arm_R'] if arm_only else ['Arm_R','Body']):write_glb(out/(name+'.glb'),g,raw,[(name,t,m)],rev)
 else:shutil.copy2(src/(name+'.glb'),out/(name+'.glb'))
(rep/'build.json').write_text(json.dumps({'revision':rev,'baseline':src.name,'scope':(['Arm_R inner source fringe and closure only' if '--trim-inner' in sys.argv else 'Arm_R additional inner closure only'] if arm_only else ['Arm_R additional inner surface','Body right-side additional surface only']),'parts':stats,'unchanged_standalone_files':[n for n,_,_ in parts if n not in (['Arm_R'] if arm_only else ['Body','Arm_R'])],'bones':0},indent=2));print(json.dumps(stats),flush=True)
