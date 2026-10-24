"""Retain original body triangles; reconstruct only two documented arm contacts.

No oval loft, whole-body remesh, or accepted-head asset is used for generation.
Skin holes are constrained by adjacent retained skin. The cloth contact borrows
opposite original cloth topology. The body stays in its original pose.
"""
from pathlib import Path
import argparse, sys, json, math, hashlib
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

R=Path(__file__).resolve().parents[1]; D=R/'review/lulu-body-source-20261023'
ap=argparse.ArgumentParser();ap.add_argument('--revision',default='source-r01')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
O=D/args.revision;O.mkdir(exist_ok=False)
A=np.load(R/'review/lulu-body-parts-20261021/source-body-frame.npz');P=A['p'];F=A['f']
FIT=json.loads((R/'review/lulu-body-parts-20261021/body-fit.json').read_text())
H=np.load(R/'review/lulu-head-mirror-20261021/baseline/welded-source.npz')
bpy.ops.wm.read_factory_settings(use_empty=True)

def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.83
 return m
materials=[material('Original retained surface',(.48,.49,.46)),material('Left contact reconstruction',(.27,.49,.40)),material('Right contact reconstruction',(.62,.40,.25)),material('Temporary neck closure',(.35,.42,.59))]

me=bpy.data.meshes.new('Original welded topology');me.from_pydata(P.tolist(),[],F.tolist());me.update()
bm=bmesh.new();bm.from_mesh(me);bpy.data.meshes.remove(me)
sid=bm.verts.layers.int.new('source_vertex_id');patch=bm.faces.layers.int.new('repair_region')
for i,v in enumerate(bm.verts):v[sid]=i+1
source_bvh=BVHTree.FromPolygons([Vector(q) for q in P],F.tolist(),all_triangles=True)

def coords(points,side):
 return np.c_[np.arctan2(points[:,2]+.02,points[:,0]*side)*.22,points[:,1]]
def inside(q,poly):
 yes=np.zeros(len(q),bool)
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  yes^=((a[1]>q[:,1])!=(b[1]>q[:,1]))&(q[:,0]<(b[0]-a[0])*(q[:,1]-a[1])/(b[1]-a[1]+1e-30)+a[0])
 return yes
def boundary_loops():
 edges={e for e in bm.edges if e.is_boundary};loops=[]
 while edges:
  e=next(iter(edges));start=e.verts[0];cur=start;loop=[]
  while True:
   loop.append(cur);opts=[ee for ee in cur.link_edges if ee in edges]
   if not opts:break
   ee=opts[0];edges.remove(ee);cur=ee.other_vert(cur)
   if cur==start:break
  loops.append(loop)
 return loops
def donor(q,side):
 out=[]
 for u,y in q:
  th=u/.22;dr=Vector((-side*math.cos(th),0,math.sin(th)))
  hit,n,i,dist=source_bvh.ray_cast(Vector((0,float(y),-.02)),dr,1.0)
  if hit is None:raise RuntimeError(f'Missing donor {u,y,side}')
  out.append(dist)
 return np.array(out)
def tps_fit(c,z):
 # Smooth residual field retains the source shape on both sides of the join.
 ds=np.sqrt(np.sum((c[:,None,:]-c[None,:,:])**2,axis=2));K=ds*ds*np.log(np.maximum(ds,1e-10));poly=np.c_[np.ones(len(c)),c]
 L=np.block([[K+np.eye(len(c))*2e-8,poly],[poly.T,np.zeros((3,3))]])
 w=np.linalg.solve(L,np.r_[z,np.zeros(3)])
 def fn(q):
  outs=[]
  for chunk in np.array_split(q,max(1,len(q)//600)):
   ds=np.sqrt(np.sum((chunk[:,None,:]-c[None,:,:])**2,axis=2));k=ds*ds*np.log(np.maximum(ds,1e-10))
   outs.append(np.einsum('ij,j->i',k,w[:-3])+np.einsum('ij,j->i',np.c_[np.ones(len(chunk)),chunk],w[-3:]))
  return np.concatenate(outs)
 return fn

# Anatomical contact footprints, explicitly reviewed against source cross sections.
# Angles are measured from each outer side toward the front (+Z).
regions=[
 ('buttock_cloth',-1,[(-43,.150),(-66,.178),(-69,.242),(-62,.330),(32,.330),(28,.283),(-1,.215),(-20,.168)],2),
 ('raised_left_skin',1,[(24,.375),(-14,.395),(-29,.445),(-28,.54),(2,.603),(55,.608),(79,.54),(70,.43),(53,.393)],1),
 ('right_shoulder_skin',-1,[(-60,.307),(-50,.365),(-35,.41),(-28,.445),(4,.48),(37,.435),(45,.36),(40,.307)],2)]
reports=[]
for name,side,poly0,region_id in regions:
 poly=np.array(poly0,float);poly[:,0]*=math.pi/180*.22
 # Face-centre selection preserves every retained source triangle exactly.
 faces=list(bm.faces);cent=np.array([f.calc_center_median()[:] for f in faces]);uv=coords(cent,side)
 remove=inside(uv,poly)&(cent[:,0]*side>0)
 doomed=[f for f,m in zip(faces,remove) if m]
 bmesh.ops.delete(bm,geom=doomed,context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 loops=[l for l in boundary_loops() if len(l)>40 and np.mean([v.co.x for v in l])*side>0]
 if len(loops)!=1:raise RuntimeError(f'{name}: expected single contact boundary, got {[(len(l),list(l[0].co)) for l in loops]}')
 loop=loops[0];bp=np.array([v.co[:] for v in loop]);buv=coords(bp,side)
 area=np.sum(buv[:,0]*np.roll(buv[:,1],-1)-buv[:,1]*np.roll(buv[:,0],-1))
 if area<0:loop=loop[::-1];bp=bp[::-1];buv=buv[::-1]
 if 'skin' in name:
  # Local skin-only reconstruction; sample intact neighboring source skin.
  # Every exterior vertex stays fixed. The cloth fold is handled separately.
  outer=set(loop)
  for _ in range(16):outer|={e.other_vert(v) for v in list(outer) for e in v.link_edges}
  op=np.array([v.co[:] for v in outer if v[sid]>0]);ou=coords(op,side)
  # Restrict controls to actual body/shoulder skin, excluding the upper hand/head.
  lim=.4728+.151*(op[:,0]+.01575)-.0143*op[:,2]
  good=(op[:,0]*side>0)&~inside(ou,poly)&(op[:,1]<lim+.012)&(op[:,1]>.304)
  op=op[good];ou=ou[good]
  cells=np.floor(ou/.004).astype(int);_,ind=np.unique(cells,axis=0,return_index=True);op=op[ind];ou=ou[ind]
  rad=np.sqrt(op[:,0]**2+(op[:,2]+.02)**2)
  center=ou.mean(0);scale=np.array([.12,.10])
  def basis(uv):
   u,v=((uv-center)/scale).T
   return np.c_[np.ones(len(uv)),u,v,u*u,u*v,v*v,u*u*u,u*u*v,u*v*v,v*v*v]
  B=basis(ou);coef=np.linalg.lstsq(B,rad,rcond=None)[0]
  # Small residual interpolation matches retained skin without copying arm roots.
  residual=rad-np.einsum('ij,j->i',B,coef)
  field=tps_fit(ou,residual)
  uu=np.arange(buv[:,0].min(),buv[:,0].max(),.0035);yy=np.arange(buv[:,1].min(),buv[:,1].max(),.0035)
  grid=np.stack(np.meshgrid(uu,yy),-1).reshape(-1,2);grid=grid[inside(grid,buv)]
  grid=grid[np.min(np.sum((grid[:,None,:]-buv[None,:,:])**2,axis=2),axis=1)>.0018**2]
  inp=np.concatenate([buv,grid]);N=len(loop)
  vs,es,fs,vid,eid,fid=delaunay_2d_cdt([Vector(q) for q in inp],[],[list(range(N))],1,1e-9,True)
  q=np.array([v[:] for v in vs]);r=np.einsum('ij,j->i',basis(q),coef)+field(q)
  th=q[:,0]/.22;xyz=np.c_[side*r*np.cos(th),q[:,1],-.02+r*np.sin(th)]
  made=[];new=[]
  for i,ids in enumerate(vid):
   existing=[j for j in ids if j<N]
   if existing:made.append(loop[existing[0]])
   else:v=bm.verts.new(xyz[i].tolist());v[sid]=0;made.append(v);new.append(v)
  for ff in fs:
   face=bm.faces.new([made[j] for j in ff]);face[patch]=region_id;face.material_index=region_id
  reports.append({'region':name,'method':'local skin patch constrained by original neighboring skin','deleted_source_faces':len(doomed),'rim_vertices':N,'new_vertices':len(new),'control_count':len(ou),'fit_residual_max':float(abs(residual).max())})
  print(name,reports[-1],flush=True)
  continue
 # Borrow a real opposite-side surface patch, including its original cloth folds.
 # Only its border collar is new topology; no radial or oval reconstruction.
 inner=poly.mean(0)+(poly-poly.mean(0))*.84
 donor_p=P.copy()
 # The original neck/shoulder line rises toward the raised arm. Align only the
 # borrowed patch to that original pose; never move the retained body surface.
 bend=np.clip((P[:,1]-.30)/.15,0,1);bend=bend*bend*(3-2*bend)
 donor_p[:,1]-=.30*P[:,0]*bend
 donor_p[:,0]*=-1
 dc=donor_p[F].mean(1);keep=inside(coords(dc,side),inner)&(dc[:,0]*side>0)
 df=F[keep][:,::-1];used,inv=np.unique(df,return_inverse=True)
 dm=bpy.data.meshes.new('opposite_original_patch');dm.from_pydata(donor_p[used].tolist(),[],inv.reshape(-1,3).tolist())
 db=bmesh.new();db.from_mesh(dm);bpy.data.meshes.remove(dm)
 # Retain the main connected donor surface only.
 todo=set(db.faces);groups=[]
 while todo:
  seed=todo.pop();group={seed};queue=[seed]
  while queue:
   f0=queue.pop()
   for e in f0.edges:
    for ff in e.link_faces:
     if ff in todo:todo.remove(ff);group.add(ff);queue.append(ff)
  groups.append(group)
 large=max(groups,key=len);bmesh.ops.delete(db,geom=[f0 for g in groups if g is not large for f0 in g],context='FACES')
 bmesh.ops.delete(db,geom=[v for v in db.verts if not v.link_faces],context='VERTS')
 edges={e for e in db.edges if e.is_boundary};dl=[]
 e=next(iter(edges));v=e.verts[0];first=v
 while True:
  dl.append(v);opts=[e for e in v.link_edges if e in edges]
  if not opts:break
  e=opts[0];edges.remove(e);v=e.other_vert(v)
  if v==first:break
 if edges:raise RuntimeError(f'Donor patch has extra boundary edges: {len(edges)}')
 # Match the borrowed cloth to this side's original waist/hip asymmetry.
 # A local vector field acts only on new donor vertices; retained source is fixed.
 dvh=BVHTree.FromPolygons([Vector(q) for q in donor_p],F[:,::-1].tolist(),all_triangles=True)
 controls=[];offsets=[]
 for q0 in bp[::3]:
  hit,nn,ii,dd=dvh.find_nearest(Vector(q0))
  if hit is not None and dd<.045:controls.append(hit[:]);offsets.append(q0-np.array(hit[:]))
 controls=np.array(controls);offsets=np.array(offsets)
 for v in db.verts:
  if v.co.y>=.298:continue
  dd=np.sum((controls-np.array(v.co[:]))**2,axis=1)
  weights=np.exp(-dd/.025**2)
  delta=np.einsum('i,ij->j',weights,offsets)/(weights.sum()+.02)
  fade=float(np.clip((.298-v.co.y)/.028,0,1));fade=fade*fade*(3-2*fade)
  v.co+=Vector(delta*fade)
 dp=np.array([v.co[:] for v in dl]);duv=coords(dp,side)
 if np.sum(duv[:,0]*np.roll(duv[:,1],-1)-duv[:,1]*np.roll(duv[:,0],-1))<0:dl=dl[::-1];dp=dp[::-1];duv=duv[::-1]
 # Anchor the two loops at their bottom; monotone correspondence preserves folds.
 j=int(np.argmin(duv[:,1]));dl=dl[j:]+dl[:j];dp=np.roll(dp,-j,axis=0);duv=np.roll(duv,-j,axis=0)
 i=int(np.argmin(np.sum((buv-duv[0])**2,axis=1)));loop=loop[i:]+loop[:i];bp=np.roll(bp,-i,axis=0);buv=np.roll(buv,-i,axis=0)
 n,m=len(loop),len(dl);cost=np.sum((buv[:,None,:]-duv[None,:,:])**2,axis=2)
 dist=np.full((n,m),np.inf);prev=np.zeros((n,m),np.uint8);dist[0,0]=cost[0,0]
 for i in range(n):
  for j in range(m):
   if not(i or j):continue
   opts=[dist[i-1,j] if i else np.inf,dist[i,j-1] if j else np.inf,dist[i-1,j-1] if i and j else np.inf]
   k=int(np.argmin(opts));prev[i,j]=k;dist[i,j]=cost[i,j]+opts[k]
 path=[];i=n-1;j=m-1
 while True:
  path.append((i,j))
  if i==0 and j==0:break
  k=prev[i,j]
  if k in [0,2]:i-=1
  if k in [1,2]:j-=1
 path=path[::-1];match=[[] for _ in range(n)]
 for i,j in path:match[i].append(j)
 target=np.array([dp[js].mean(0) for js in match])
 bm.normal_update();db.normal_update()
 source_norm=np.array([v.normal[:] for v in loop]);donor_norm=np.array([v.normal[:] for v in dl])
 target_norm=np.array([donor_norm[js].mean(0) for js in match]);target_norm/=np.maximum(np.linalg.norm(target_norm,axis=1)[:,None],1e-10)
 delta=target-bp
 tangent0=delta-source_norm*np.sum(delta*source_norm,axis=1)[:,None]
 tangent1=delta-target_norm*np.sum(delta*target_norm,axis=1)[:,None]
 mapping={};new=[]
 for v in db.verts:
  nv=bm.verts.new(v.co);nv[sid]=0;mapping[v]=nv;new.append(nv)
 for f0 in db.faces:
  ff=bm.faces.new([mapping[v] for v in f0.verts]);ff[patch]=region_id;ff.material_index=region_id
 dlout=[mapping[v] for v in dl]
 old=loop;collar=[]
 for t0 in [.20,.40,.60,.80]:
  vv=(2*t0**3-3*t0*t0+1)*bp+(t0**3-2*t0*t0+t0)*tangent0+(-2*t0**3+3*t0*t0)*target+(t0**3-t0*t0)*tangent1
  row=[]
  for q0 in vv:
   v=bm.verts.new(q0.tolist());v[sid]=0;row.append(v);collar.append(v)
  for i in range(n):
   ff=bm.faces.new((old[i],old[(i+1)%n],row[(i+1)%n],row[i]));ff[patch]=region_id;ff.material_index=region_id
  old=row
 # Close the last narrow strip with unequal original edge counts.
 for (i,j),(ii,jj) in zip(path,path[1:]+[(0,0)]):
  vv=[old[i]]
  if ii!=i:vv.append(old[ii])
  if jj!=j:vv.append(dlout[jj])
  vv.append(dlout[j])
  if len(set(vv))<3:continue
  ff=bm.faces.new(vv);ff[patch]=region_id;ff.material_index=region_id
 # Only the newly created transition collar is faired. Both source borders fixed.
 for step in range(48):
  edits={}
  for v in collar:
   if step>=4 and v.co.y>=.298:continue
   avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
   edits[v]=v.co.lerp(avg,.20)
  for v,q0 in edits.items():v.co=q0
 reports.append({'region':name,'deleted_source_faces':len(doomed),'rim_vertices':n,'donor_original_vertices':len(new),'collar_vertices':len(collar),'donor_rim_vertices':m,'footprint_angle_y':poly0})
 db.free()
 print(name,reports[-1],flush=True)

# Separate only at the original head/neck interface; preserve body pose and tilt.
# Map the accepted extraction plane (not the upright head shape) into body frame.
angle=math.radians(FIT['yaw_degrees']);rot=np.array([[math.cos(angle),0,math.sin(angle)],[0,1,0],[-math.sin(angle),0,math.cos(angle)]])
normal=np.einsum('ij,j->i',rot,H['head_basis'][1])
point_raw=H['head_center']+H['head_basis'][1]*(.470-.72)
point=np.einsum('ij,j->i',rot,point_raw-np.array([FIT['center_x'],0,0]))
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=point,plane_no=normal,clear_outer=True,clear_inner=False)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
# One short, flat temporary closure strictly inside the cut. No flared collar.
loops=boundary_loops();assert len(loops)==1,[(len(v),v[0].co[:]) for v in loops]
closed=bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)['faces']
for f in closed:f[patch]=3;f.material_index=3
bmesh.ops.triangulate(bm,faces=closed)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.verts.index_update();bm.faces.index_update()
original_ids=[];delta=[]
for v in bm.verts:
 i=v[sid]-1
 if i>=0:
  dd=float(np.linalg.norm(np.array(v.co[:])-P[i]));delta.append(dd)
  if dd<1e-7:original_ids.append(i)
  else:v[sid]=0 # bisect-generated interpolated source id does not mean provenance
raw=np.array([v.co[:] for v in bm.verts]);facearr=[list(v.index for v in f.verts) for f in bm.faces]
region_ids=[f[patch] for f in bm.faces]
np.savez_compressed(O/'geometry-proof.npz',p=raw,faces=np.array(facearr,dtype=object),source_id=np.array([v[sid]-1 for v in bm.verts]),regions=region_ids)
for v in bm.verts:x,y,z=v.co;v.co=(x,-z,y)
mesh=bpy.data.meshes.new('Original retained body with local contact repairs');bm.to_mesh(mesh)
ob=bpy.data.objects.new('Lulu_Body_FromOriginal',mesh);bpy.context.collection.objects.link(ob)
for m in materials:mesh.materials.append(m)
for f in mesh.polygons:f.use_smooth=f.material_index!=3
for n,ix in [('Original_Retained',0),('Left_Contact_Repair',1),('Right_Contact_Repair',2),('Temporary_Neck_Cap',3)]:
 ids=set()
 for f in mesh.polygons:
  if f.material_index==ix:ids.update(f.vertices)
 if ids:ob.vertex_groups.new(name=n).add(list(ids),1,'REPLACE')
ob['scope']='Original body; only two arm-contact patches reconstructed. Head and arms absent. No rig.'
ob.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(O/'lulu-body.glb'),export_format='GLB',use_selection=True,export_yup=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'lulu-body.blend'))
report={'revision':args.revision,'status':'VISUAL_REVIEW_REQUIRED','source_vertices_retained':len(original_ids),'body_vertices':len(bm.verts),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'regions':reports,'head_asset_loaded_or_changed':False,'armature_count':0,'neck_cut_point':point.tolist(),'neck_cut_normal':normal.tolist()}
bm.free();(O/'build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
