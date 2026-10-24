"""Local armpit reconstruction on the r04 rig copy; original files are immutable.
The cut volume removes fused inner-arm bridges. Its two independently curved
walls become new chest-side and inner-arm surfaces, rather than a torn skin.
Original outer triangles, UVs and normals are retained wherever unaffected.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,struct,sys,hashlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parents[1]
REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r05'
OUT=R/f'public/models/rig/lulu-rig-{REV}.glb'
BLEND=R/f'assets-source/rig/lulu-rig-{REV}.blend'
REPORT=R/'review/lulu-rig-separation-20261018'/REV
assert not OUT.exists() and not BLEND.exists(),'Use a fresh revision'
REPORT.mkdir(parents=True,exist_ok=True)
SOURCE=R/'public/models/rig/lulu-rig-r04.glb'
b=SOURCE.read_bytes();jl=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+jl]);raw=bytearray(b[28+jl:])
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
 return np.ndarray((a['count'],sz),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',sz*dt.itemsize),dt.itemsize)).copy()
P=[];N=[];UV=[];F=[];MAT=[];W=[];J=[]
for mi,pr in enumerate(g['meshes'][0]['primitives']):
 p=acc(pr['attributes']['POSITION']); f=acc(pr['indices']).reshape(-1,3)
 F.extend((f+len(P)).tolist());MAT.extend([pr.get('material',0)]*len(f))
 P.extend(p);N.extend(acc(pr['attributes']['NORMAL']));UV.extend(acc(pr['attributes']['TEXCOORD_0']));J.extend(acc(pr['attributes']['JOINTS_0']));W.extend(acc(pr['attributes']['WEIGHTS_0']))
P=np.array(P);N=np.array(N);UV=np.array(UV);F=np.array(F);J=np.array(J);W=np.array(W)
# Position welding preserves loop UV seams. The formal asset isn't changed.
unique,first,inv=np.unique(np.round(P,6),axis=0,return_index=True,return_inverse=True);up=P[first];uf=inv[F]
def key6(p):return tuple(np.rint(np.asarray(p)*1e6).astype(np.int64))
base_norm={key6(p):n for p,n in zip(P,N)}
base_corner_norm={(key6(p),key6(uv)):n for p,n,uv in zip(P,N,UV)}
base_weights={key6(p):(j,w) for p,j,w in zip(P,J,W)}
# Original texture lookup used exclusively by newly exposed inner surfaces.
bvh=BVHTree.FromPolygons([Vector(p) for p in P],F.tolist(),all_triangles=True)
def sampleuv(point):
 co,no,idx,dist=bvh.find_nearest(Vector(point)); ids=F[idx];a,c,d=P[ids]
 e=c-a;f=d-a;v=np.array(co)-a;ee=e@e;ff=f@f;ef=e@f;den=ee*ff-ef*ef
 s=(ff*(v@e)-ef*(v@f))/max(den,1e-20);t=(ee*(v@f)-ef*(v@e))/max(den,1e-20)
 return UV[ids[0]]*(1-s-t)+UV[ids[1]]*s+UV[ids[2]]*t
# Decode the existing embedded albedo using Blender, without replacing it.
bpy.ops.wm.read_factory_settings(use_empty=True)
imgid=g['textures'][0]['source'];vv=g['bufferViews'][g['images'][imgid]['bufferView']]
texfile=REPORT/'source-albedo.png';texfile.write_bytes(raw[vv.get('byteOffset',0):vv.get('byteOffset',0)+vv['byteLength']])
im=bpy.data.images.load(str(texfile));tw,th=im.size;pix=np.empty(tw*th*4,dtype=np.float32);im.pixels.foreach_get(pix);pix=pix.reshape(th,tw,4)
def color_at(p):
 uv=sampleuv(p);return pix[int(np.clip((1-uv[1])*(th-1),0,th-1)),int(np.clip(uv[0]*(tw-1),0,tw-1)),:3].copy()
mesh=bpy.data.meshes.new('Lulu_local_topology');mesh.from_pydata(up.tolist(),[],uf.tolist());mesh.update()
obj=bpy.data.objects.new('Lulu_local_topology',mesh);bpy.context.collection.objects.link(obj)
for k in range(3):mesh.materials.append(bpy.data.materials.new('slot'+str(k)))
uvlayer=mesh.uv_layers.new(name='UVMap')
for poly,mat,tri in zip(mesh.polygons,MAT,F):
 poly.material_index=int(mat);poly.use_smooth=True
 for li,vi in zip(poly.loop_indices,tri):uvlayer.data[li].uv=UV[vi]
# Measured separation channel. Front and rear surfaces of the arm stay in place.
ys=np.array([-.64,-.59,-.56,-.52,-.46,-.40,-.34,-.28,-.23,-.215])
body=np.array([.477,.477,.468,.456,.438,.422,.409,.401,.392,.390])
inner=np.array([.489,.487,.479,.470,.452,.434,.426,.420,.392,.390])
zc=np.array([-.055,-.055,-.057,-.065,-.065,-.069,-.079,-.085,-.090,-.09])
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def wall(y,z):
 u=1-ss(-.28,-.215,y)
 # Parabolic walls form a full rounded inner arm and a convex chest side.
 c=np.interp(y,ys,zc);q=(z-c)/.11
 xb=np.interp(y,ys,body)-.018*min(q*q,1.0)*u
 xa=np.interp(y,ys,inner)+.045*min(q*q,1.0)*u
 # Outside the actual palm depth, avoid shaving the central shorts/torso.
 return xb,xa
cutter_faces=0
for sign in [-1,1]:
 verts=[];faces=[];ny=85;nz=95
 yvals=np.linspace(-.635,-.215,ny);zvals=np.linspace(-.38,.23,nz)
 for side in [0,1]:
  for y in yvals:
   for z in zvals:
    lo,hi=wall(y,z)
    if y>-.218:hi=lo+.0002
    verts.append((sign*(lo if side==0 else hi),y,z))
 def idx(s,i,j):return s*ny*nz+i*nz+j
 for side in [0,1]:
  for i in range(ny-1):
   for j in range(nz-1):
    faces.append((idx(side,i,j),idx(side,i+1,j),idx(side,i+1,j+1),idx(side,i,j+1)))
 for i in range(ny-1):
  for j in [0,nz-1]:faces.append((idx(0,i,j),idx(1,i,j),idx(1,i+1,j),idx(0,i+1,j)))
 for i in [0,ny-1]:
  for j in range(nz-1):faces.append((idx(0,i,j),idx(0,i,j+1),idx(1,i,j+1),idx(1,i,j)))
 cm=bpy.data.meshes.new('curved_negative_space');cm.from_pydata(verts,[],faces);cm.update()
 bm=bmesh.new();bm.from_mesh(cm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cm);bm.free()
 for mat in mesh.materials:cm.materials.append(mat)
 for poly in cm.polygons:poly.material_index=2
 cutter=bpy.data.objects.new('Armpit_curve_tool',cm);bpy.context.collection.objects.link(cutter)
 bpy.context.view_layer.objects.active=obj;obj.select_set(True)
 mod=obj.modifiers.new('Rebuild inner arm and chest '+str(sign),'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 print('boolean',sign,len(obj.data.vertices),len(obj.data.polygons),flush=True)
mesh=obj.data
# Fair only the newly built junction and its immediate neighbours.
# This follows actual topology reconstruction and is not the old global smoothing.
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
patch=set(v for f in bm.faces if f.material_index==2 for v in f.verts)
seam=set(v for v in patch if any(f.material_index!=2 for f in v.link_faces))
seamKD=KDTree(len(seam))
for i,vv in enumerate(seam):seamKD.insert(vv.co,i)
seamKD.balance()
original_co={v:v.co.copy() for v in bm.verts}
zone={v for v in bm.verts if -.66<v.co.y<-.17 and abs(v.co.x)>.33 and seamKD.find(v.co)[2]<.026}
for _ in range(12):
 updates={}
 for v in zone:
  neigh=[e.other_vert(v).co for e in v.link_edges]
  if not neigh:continue
  d=seamKD.find(original_co[v])[2];a=.32*(1-ss(.008,.026,d))
  target=v.co.lerp(sum(neigh,Vector())/len(neigh),a)
  diff=target-original_co[v]
  if diff.length>.006:target=original_co[v]+diff.normalized()*.006
  updates[v]=target
 for v,co1 in updates.items():v.co=co1
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for poly in mesh.polygons:poly.use_smooth=True
mesh.update();mesh.calc_loop_triangles()
# Authored region weights after separation: body stays torso, full inner arm moves.
names=[g['nodes'][i]['name'] for i in g['skins'][0]['joints']];ix={n:i for i,n in enumerate(names)}
def weights(p,original):
 x,y,z=p;ax=abs(x)
 if y>=-.055:return np.array([ix['Head'],0,0,0],dtype='<u2'),np.array([1,0,0,0],dtype='<f4')
 if not (-.655<y<-.10 and ax>.29):return original
 w=np.zeros(len(names));sd='Left' if x>0 else 'Right'
 lo,hi=wall(y,z);mid=(lo+hi)/2
 # Below armpit, classify the two real surfaces rather than blending across them.
 if y<=-.275:
  arm=float(ax>mid and abs(z-np.interp(y,ys,zc))<.17 and ax>.39)
 elif y<-.16:
  start=np.interp(y,[-.275,-.215,-.16],[.393,.355,.32]);end=start+.10
  arm=float(ss(start,end,ax)*(1-ss(-.23,-.12,y)))
 else:arm=0.
 # The preserved free palm is completely assigned to hand/forearm.
 if -.625<y<-.53 and ax>.484 and -.17<z<.08:arm=1.
 if arm:
  hand=1-ss(-.545,-.465,y);fore=(1-ss(-.385,-.285,y))*(1-hand)
  w[ix[sd+'Hand']]=arm*hand;w[ix[sd+'ForeArm']]=arm*fore;w[ix[sd+'Arm']]=arm*(1-hand-fore)
 # Torso weights transferred independently, never inherited from r04 arm gradients.
 head=float(ss(-.17,-.055,y));sp=float(ss(-.49,-.31,y));upper=float(ss(-.33,-.20,y));neck=float(ss(-.21,-.12,y));bodyW=1-head
 w[ix['Head']]+=(1-arm)*head
 w[ix['Hips']]+=(1-arm)*bodyW*(1-sp)
 w[ix['Spine']]+=(1-arm)*bodyW*sp*(1-upper)
 w[ix['Spine1']]+=(1-arm)*bodyW*sp*upper*(1-neck)
 w[ix['Spine2']]+=(1-arm)*bodyW*sp*upper*neck
 inds=np.argsort(-w)[:4];vals=w[inds];vals/=vals.sum()
 return inds.astype('<u2'),vals.astype('<f4')
# Recompute only the rebuilt patch normals, retain all source exterior normals.
mesh.update();mesh.calc_loop_triangles();corner=np.array([n.vector[:] for n in mesh.corner_normals]);co=np.array([v.co[:] for v in mesh.vertices])
uvlayer=mesh.uv_layers.active
newuv={};newweight={};newnorm=0
for vi,p in enumerate(co):
 key=key6(p);orig=base_weights.get(key)
 if orig is None:
  _,_,ti,_=bvh.find_nearest(Vector(p));orig=(J[F[ti,0]],W[F[ti,0]])
 newweight[vi]=weights(p,orig)
 if key not in base_norm:newuv[vi]=sampleuv(p)
parts=[{'p':[],'n':[],'uv':[],'j':[],'w':[],'c':[],'f':[],'cache':{}} for _ in range(3)]
# Vertex colour on the missing surfaces avoids sampling across yellow/orange seams.
g['materials'].append({'name':'Lulu_rebuilt_inner_surfaces','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':.66},'doubleSided':True})
patch_triangles=0
for tri in mesh.loop_triangles:
 if len({tuple(np.asarray(co[vi],dtype=np.float32)) for vi in tri.vertices})<3:continue
 cap=mesh.polygons[tri.polygon_index].material_index==2
 part=parts[2 if cap else mesh.polygons[tri.polygon_index].material_index]
 out=[]
 for vi,li in zip(tri.vertices,tri.loops):
  p=co[vi];key=key6(p)
  uv=sampleuv(p) if cap else np.array(uvlayer.data[li].uv)
  n=base_corner_norm.get((key,key6(uv)),base_norm.get(key,corner[li]))
  d=seamKD.find(Vector(p))[2]
  normalmix=1-ss(.008,.03,d)
  n=n*(1-normalmix)+corner[li]*normalmix;n=n/max(np.linalg.norm(n),1e-10)
  col=np.ones(3)
  if cap:
   n=corner[li];x,y,z=p;lo,hi=wall(y,z);isarm=abs(x)>(lo+hi)*.5
   # Same-height exterior donor, chosen on the correct anatomical surface.
   if isarm:donor=(np.sign(x)*(.58 if y<-.33 else .53),y,-.07)
   else:donor=(np.sign(x)*.34,y,.17)
   col=color_at(donor)
   # At a true new/old boundary retain the original local colour.
   if d<.014:
    edgecol=color_at(p)
    # Do not inherit orange shorts onto a newly separated yellow inner arm.
    if not isarm or edgecol[1]>edgecol[0]*.70:
     a=ss(0,.014,d);col=edgecol*(1-a)+col*a

  ck=(int(vi),tuple(np.round(uv,7)),tuple(np.round(n,5)))
  if ck not in part['cache']:
   part['cache'][ck]=len(part['p']);part['p'].append(p);part['n'].append(n);part['uv'].append(uv);part['c'].append(np.where(col<=.04045,col/12.92,((col+.055)/1.055)**2.4));j,w=newweight[vi];part['j'].append(j);part['w'].append(w)
  out.append(part['cache'][ck])
 part['f'].append(out)
 if cap:patch_triangles+=1
# Append new attributes; textures, original binary, skeleton and original copy survive.
def add(a,typ,component):
 while len(raw)%4:raw.append(0)
 off=len(raw);raw.extend(a.tobytes());vi=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':a.nbytes});ai=len(g['accessors']);v={'bufferView':vi,'componentType':component,'count':len(a),'type':typ}
 if typ=='VEC3':v.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 g['accessors'].append(v);return ai
prims=[]
for mi,part in enumerate(parts):
 attrs={}
 for key,typ,comp,dt,outname in [('p','VEC3',5126,'<f4','POSITION'),('n','VEC3',5126,'<f4','NORMAL'),('uv','VEC2',5126,'<f4','TEXCOORD_0'),('j','VEC4',5123,'<u2','JOINTS_0'),('w','VEC4',5126,'<f4','WEIGHTS_0')]:attrs[outname]=add(np.array(part[key],dtype=dt),typ,comp)
 if mi==2:attrs['COLOR_0']=add(np.array(part['c'],dtype='<f4'),'VEC3',5126)
 prims.append({'attributes':attrs,'indices':add(np.array(part['f'],dtype='<u4').reshape(-1,1),'SCALAR',5125),'material':mi,'mode':4})
g['meshes'][0]['primitives']=prims;g['buffers'][0]['byteLength']=len(raw)
g.setdefault('extras',{})['lulu']['revision']=REV;g['extras']['lulu']['geometry_and_materials']='Local armpit/inner-arm surface reconstruction; source textures retained; independent skin weights';g['extras']['lulu']['animation_status']='Local separation candidate; small-motion visual review required'
j=json.dumps(g,ensure_ascii=False,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw+=b'\0'*((-len(raw))%4)
OUT.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(raw))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw)
# Native editable rig with actual new surfaces and original 23-bone armature.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT),merge_vertices=True)
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');arm.show_in_front=True
bpy.context.scene['asset_name']='Lulu 绑定副本 · 腋下与内臂重建 '+REV
bpy.context.scene['source']='r04; local topology correction, no Mixamo clips'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
report={'revision':REV,'source_sha256':hashlib.sha256(b).hexdigest(),'rebuilt_surface_triangles':patch_triangles,'vertices':sum(len(p['p']) for p in parts),'triangles':sum(len(p['f']) for p in parts),'static_official_unchanged':hashlib.sha256((R/'public/models/lulu-official-v1.glb').read_bytes()).hexdigest(),'native_source':str(BLEND.relative_to(R)),'glb':str(OUT.relative_to(R)),'status':'Candidate; needs visual validation'}
(REPORT/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
