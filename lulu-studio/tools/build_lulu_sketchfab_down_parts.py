"""Reversible pose: retain each source triangle once; add separate inner guard shells.
No source vertex/normal/UV is edited. Source anatomy is partitioned at existing
surface seams; each arm is rigidly posed with a bone and body is fixed.
"""
from pathlib import Path
import numpy as np, json, struct, hashlib, argparse, copy, math
from pose_lulu_sketchfab_arm import read,accessor,quaternion,matrix,D,SOURCE
from color_lulu_sketchfab import colour,srgb_to_linear,SKIN
R=Path(__file__).resolve().parents[1]
PIVOTS=[np.array([.242,.445,.012]),np.array([-.242,.433,-.065])]
HANDS=[np.array([.191,.527,.225]),np.array([-.246,.217,-.175])]
TARGETS=[np.array([.29,.20,.015]),np.array([-.282,.19,-.043])]


def boundary_loops(f):
 e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ue,iv,counts=np.unique(np.sort(e,1),axis=0,return_inverse=True,return_counts=True)
 ed=e[counts[iv]==1];adj={}
 for a,b in ed:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
 if any(len(v)!=2 for v in adj.values()):raise ValueError('Branched boundary')
 loops=[]
 while adj:
  s=next(iter(adj));loop=[s];prev=-1;cur=s
  while True:
   choices=adj[cur];nxt=choices[0] if choices[0]!=prev else choices[1]
   if nxt==s:break
   loop.append(nxt);prev,cur=cur,nxt
  for a in loop:del adj[a]
  loops.append(np.array(loop,int))
 return loops


def cap(loop,p,n,part,envelope):
 B=p[loop].astype(float);N=n[loop].astype(float);center=B.mean(0)
 # The body guard follows the intact body's neighboring curvature; arm guards
 # close only the newly exposed inner side, never flatten the visible arm.
 direction=np.array([1 if center[0]>0 else -1,0,0.])
 if part>0:direction=-direction
 # Solve a smooth biharmonic disk from the complete boundary, rather than
 # a radial fan to one point. Arc-length sampling avoids dense seam jitter.
 seg=np.linalg.norm(np.roll(B,-1,axis=0)-B,axis=1);arc=np.r_[0,np.cumsum(seg)];theta=arc[:-1]/arc[-1]*2*np.pi
 M=512;tt=np.arange(M)/M*2*np.pi
 BB=np.stack([np.interp(tt,np.r_[theta,2*np.pi],np.r_[B[:,j],B[0,j]]) for j in range(3)],1)
 NN0=np.stack([np.interp(tt,np.r_[theta,2*np.pi],np.r_[N[:,j],N[0,j]]) for j in range(3)],1)
 # A fixed orientation across the loop prevents alternating inward/outward
 # tangents. Geometry around the seam is not altered.
 T=np.roll(BB,-2,axis=0)-np.roll(BB,2,axis=0);T/=np.maximum(np.linalg.norm(T,axis=1),1e-12)[:,None]
 tangent=np.cross(NN0,T)
 if np.sum(tangent*(center-BB))<0:tangent=-tangent
 tangent/=np.maximum(np.linalg.norm(tangent,axis=1),1e-12)[:,None]
 span=np.linalg.norm(center-BB,axis=1)
 deriv=-tangent*span[:,None]*.25
 fb=np.fft.rfft(BB,axis=0)/M;fd=np.fft.rfft(deriv,axis=0)/M
 freq=np.arange(len(fb));freqmat=freq[:,None]
 beta=(fd-freqmat*fb)/2;alpha=fb-beta
 phase=np.exp(1j*theta[:,None]*freq[None,:]);factor=np.ones(len(freq))*2;factor[0]=1;factor[-1]=1
 rings=24;pp=[B];K=len(B)
 for j in range(1,rings):
  r=1-j/rings
  coeff=alpha*r**freqmat+beta*r**(freqmat+2)
  Q=np.real(phase@(coeff*factor[:,None]))
  pp.append(Q)
 center=np.real(alpha[0])
 P=np.concatenate(pp+[center[None,:]])
 if part==0:
  # Guard uses the intact opposite half, without editing original body vertices.
  sign=1 if B[:,0].mean()>0 else -1
  yy,zz=p[:,1],p[:,2];ey,ez=B[:,1].mean(),B[:,2].mean()
  good=np.isfinite(envelope)&(p[:,0]*sign>.06)&(yy>B[:,1].min()-.04)&(yy<B[:,1].max()+.04)&(zz>B[:,2].min()-.04)&(zz<B[:,2].max()+.04)
  def design(Y,Z):
   Y=(Y-ey)/.15;Z=(Z-ez)/.15
   return np.stack([np.ones_like(Y),Y,Z,Y*Y,Y*Z,Z*Z,Y**3,Y*Y*Z,Y*Z*Z,Z**3],1)
  ids=np.where(good)[0][::3];A=design(yy[ids],zz[ids]);coeff=np.linalg.lstsq(A,np.abs(envelope[ids]),rcond=1e-6)[0]
  fitted=design(P[:,1],P[:,2])@coeff;fitted=np.clip(fitted,.07,.32)*sign
  rimfit=design(B[:,1],B[:,2])@coeff*sign;delta=B[:,0]-rimfit
  for j in range(rings):
   r=1-j/rings;P[j*K:(j+1)*K,0]=fitted[j*K:(j+1)*K]+delta*r**8
  P[-1,0]=fitted[-1];P[:K]=B
 else:
  for j in range(1,rings):
   s=j/rings
   P[j*K:(j+1)*K,0]+=(1 if B[:,0].mean()<0 else -1)*.009*np.sin(np.pi*s)

 faces=[]
 for j in range(rings-1):
  for i in range(K):
   a=j*K+i;b=j*K+(i+1)%K;c=(j+1)*K+i;d=(j+1)*K+(i+1)%K;faces.extend([[a,b,c],[b,d,c]])
 for i in range(K):faces.append([(rings-1)*K+i,(rings-1)*K+(i+1)%K,rings*K])
 F=np.array(faces,int);fn=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]])
 # Align with original rim normal rather than assume projection direction.
 idx=np.arange(min(K*2,len(F)));mean=np.mean(np.einsum('ij,ij->i',fn[idx],N[F[idx,0]%K]))
 if mean<0:F=F[:,[0,2,1]];fn=-fn
 NN=np.zeros_like(P)
 for a in range(3):np.add.at(NN,F[:,a],fn)
 NN/=np.maximum(np.linalg.norm(NN,axis=1),1e-12)[:,None];NN[:K]=N
 C=colour(P,head_only=True) if part==0 and center[1]>.4 else colour(P)
 if part>0:C[:]=SKIN
 return P.astype('<f4'),NN.astype('<f4'),F.astype('<u4'),srgb_to_linear(C).astype('<f4')


def build(rev):
 out=D/rev;out.mkdir(exist_ok=False)
 g,b=read(SOURCE);original=copy.deepcopy(g);v=np.load(R/'review/lulu-sketchfab-color-20261019/baseline/geometry.npz');a=np.load(D/'baseline/arm-labels-union-r01.npz');u,inv=a['u'],a['inv'];F=inv[v['f']];fl=a['face_labels'].copy();n=a['n']
 # Resolve isolated diagonal face-label contacts, without touching geometry.
 for iteration in range(12):
  bad=[]
  for part in [1,2]:
   ff=F[fl==part];ee=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);uu,cc=np.unique(np.sort(ee,1),axis=0,return_counts=True);bd=uu[cc==1];verts,num=np.unique(bd,return_counts=True);bad.extend(verts[num!=2])
  if not bad:break
  for vi in set(bad):
   ids=np.where((F==vi).any(1))[0];lab=np.bincount(fl[ids],minlength=3).argmax();fl[ids]=lab
 else:raise RuntimeError('Face-label boundary not regular')
 np.savez_compressed(out/'face-labels.npz',face_labels=fl)
 def buf(data):
  b.extend(b'\0'*((-len(b))%4));i=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data);return i
 def acc(a,typ,component=5126,bounds=False):
  i=len(g['accessors']);v={'bufferView':buf(a.tobytes()),'componentType':component,'count':len(a),'type':typ}
  if bounds:v.update(min=np.min(a,axis=0).tolist(),max=np.max(a,axis=0).tolist())
  g['accessors'].append(v);return i
 def skinattrs(count,part):
  jj=np.zeros((count,4),'<u2');jj[:,0]=part;ww=np.zeros((count,4),'<f4');ww[:,0]=1
  return {'JOINTS_0':acc(jj,'VEC4',5123),'WEIGHTS_0':acc(ww,'VEC4')}
 # Face lookup from the original triangle order, material groups may reorder.
 lookup={tuple(f):int(lab) for f,lab in zip(v['f'],fl)}
 meshes=[{'name':name,'primitives':[]} for name in ['Body_Preserved','LeftArm_OriginalSurface','RightArm_OriginalSurface']];offset=0;counts=[0,0,0]
 for m in original['meshes']:
  N=original['accessors'][m['primitives'][0]['attributes']['POSITION']]['count'];sk=[skinattrs(N,i) for i in range(3)]
  for pr in m['primitives']:
   f=accessor(g,b,pr['indices']).reshape(-1,3);labs=np.array([lookup[tuple(fi+offset)] for fi in f])
   for part in range(3):
    sub=f[labs==part]
    if not len(sub):continue
    new=copy.deepcopy(pr);new['indices']=acc(sub.astype('<u4').reshape(-1,1),'SCALAR',5125);new['attributes'].update(sk[part]);meshes[part]['primitives'].append(new);counts[part]+=len(sub)
  offset+=N
 # Separate added guard shells. They can be hidden in the inspector.
 caps=[]
 for part in range(3):
  loops=boundary_loops(F[fl==part])
  for li,loop in enumerate(loops):
   env=a['left_envelope'] if u[loop,0].mean()>0 else a['right_envelope'];p,nn,f,co=cap(loop,u,n,part,env)
   attrs={'POSITION':acc(p,'VEC3',bounds=True),'NORMAL':acc(nn,'VEC3'),'COLOR_0':acc(co,'VEC3')};attrs.update(skinattrs(len(p),part))
   meshes.append({'name':f'GuardShell_{part}_{li}','primitives':[{'attributes':attrs,'indices':acc(f.reshape(-1,1),'SCALAR',5125),'material':0,'mode':4}]});caps.append({'part':part,'boundary_vertices':len(loop),'triangles':len(f),'center':u[loop].mean(0).tolist()})
 g['meshes']=meshes
 # Simplified hierarchy keeps the source top transform verbatim.
 g['nodes']=[copy.deepcopy(original['nodes'][0]),{'name':'Lulu_Pose_Copy','children':[]}];g['nodes'][0]['children']=[1]
 mesh_nodes=[]
 for mi,m in enumerate(meshes):
  mesh_nodes.append(len(g['nodes']));g['nodes'].append({'name':m['name'],'mesh':mi,'skin':0})
 body=len(g['nodes']);left=body+1;right=body+2
 qs=[quaternion(h-p,t-p) for p,h,t in zip(PIVOTS,HANDS,TARGETS)]
 g['nodes'].append({'name':'Body_Fixed','children':[left,right]})
 for name,p,q in zip(['LeftArm_Pose','RightArm_Pose'],PIVOTS,qs):g['nodes'].append({'name':name,'translation':p.tolist(),'rotation':q.tolist()})
 g['nodes'][1]['children']=mesh_nodes+[body]
 ib=np.tile(np.eye(4,dtype='<f4'),(3,1,1));ib[1,:3,3]=-PIVOTS[0];ib[2,:3,3]=-PIVOTS[1]
 g['skins']=[{'name':'Lulu_Arms_Pose','joints':[body,left,right],'skeleton':body,'inverseBindMatrices':acc(ib.transpose(0,2,1).reshape(3,16).copy(),'MAT4')}]
 ti=acc(np.array([[0],[1]],'<f4'),'SCALAR',bounds=True);g['animations']=[]
 for name,mode in [('Original_Pose','up'),('Arms_Down','down'),('Arms_Lowering','move')]:
  ani={'name':name,'samplers':[],'channels':[]}
  for j,q in enumerate(qs):
   vals=[[0,0,0,1]]*2 if mode=='up' else [q.tolist()]*2 if mode=='down' else [[0,0,0,1],q.tolist()]
   ani['samplers'].append({'input':ti,'output':acc(np.array(vals,'<f4'),'VEC4'),'interpolation':'LINEAR'});ani['channels'].append({'sampler':j,'target':{'node':[left,right][j],'path':'rotation'}})
  g['animations'].append(ani)
 g['extras']['arm_pose']={'revision':rev,'source':'color-r08','original_triangles_retained_once':True,'added_separate_guard_shells':True,'scope':'two rigid arm poses, fixed body; native bind vertices untouched; not walk/run approval'}
 g['buffers'][0]['byteLength']=len(b);j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4)
 outglb=out/'lulu-arm-down.glb';outglb.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
 assert sum(counts)==499926
 _,bb=read(outglb);_,src=read(SOURCE);assert bb[:len(src)]==src
 meta={'revision':rev,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(outglb.read_bytes()).hexdigest(),'source_buffer_prefix_bit_exact':True,'original_triangle_counts':counts,'original_triangles_retained_once':sum(counts),'source_position_normals_uv_colours_unchanged':True,'body_vertices_no_motion':True,'parts':{'0':'fixed body','1':'left arm raised at face','2':'right arm at buttocks'},'pivots':[p.tolist() for p in PIVOTS],'hand_centers':[h.tolist() for h in HANDS],'target_centers':[((h-p)@matrix(q).T+p).tolist() for p,h,q in zip(PIVOTS,HANDS,qs)],'quaternions':[q.tolist() for q in qs],'angles':[2*math.degrees(math.acos(q[3])) for q in qs],'guard_shells':caps,'status':'INTERNAL_VISUAL_CHECK'}
 (out/'build.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--revision',required=True);args=ap.parse_args();build(args.revision)
