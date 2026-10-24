"""Complete source-fitted components; no rejected face labels or guard patches.
Accepted head objects are copied unchanged. Torso and arms have complete closed
control surfaces. The clear lower-body half retains original sculpture detail.
Raw working coordinates are Y up, +Z front; Blender conversion is explicit.
"""
from pathlib import Path
import argparse,sys,json,math,hashlib
import bpy,bmesh,numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-body-parts-20261021'
ap=argparse.ArgumentParser();ap.add_argument('--revision',default='body-r01');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
O=D/args.revision
if O.exists():raise RuntimeError('Use a new revision')
O.mkdir()
A=np.load(D/'source-body-frame.npz');p=A['p'];f=A['f']
bpy.ops.wm.open_mainfile(filepath=str(D/'baseline/lulu-head.blend'))
head=bpy.data.objects['Lulu_Head_Mirrored'];crown=bpy.data.objects['Original_Crown_Ornament']
head_before=np.array([v.co[:] for v in head.data.vertices]);hm=np.array(head.matrix_world);gray=head.data.materials[0]
for ob in bpy.context.scene.objects:
 ob.select_set(False)
 if ob not in [head,crown]:ob.hide_render=True;ob.hide_set(True)
head.hide_set(False);crown.hide_set(False)
collection=bpy.data.collections.new('Independent body and arms');bpy.context.scene.collection.children.link(collection)

def make(name,v,fa):
 v=np.asarray(v);xyz=np.c_[v[:,0],-v[:,2],v[:,1]]
 me=bpy.data.meshes.new(name+'_Control');me.from_pydata(xyz.tolist(),[],fa);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(name,me);collection.objects.link(ob);me.materials.append(gray)
 for pp in me.polygons:pp.use_smooth=True
 return ob

def subdiv(ob,level=2):
 m=ob.modifiers.new('Continuous subdivision','SUBSURF');m.levels=level;m.render_levels=level

def loft(name,rings,segments=48,sub=2):
 # Rings contain cx,y,cz,rx,rz; poles at first/last zero-radius entries.
 v=[];fa=[];actual=rings[1:-1]
 for cx,y,cz,rx,rz in actual:
  for j in range(segments):
   t=j*2*math.pi/segments;v.append((cx+rx*math.cos(t),y,cz+rz*math.sin(t)))
 for i in range(len(actual)-1):
  for j in range(segments):a=i*segments+j;b=i*segments+(j+1)%segments;fa.append((a,b,b+segments,a+segments))
 for k,ring in enumerate([rings[0],rings[-1]]):
  tip=len(v);v.append(ring[:3]);base=0 if k==0 else (len(actual)-1)*segments
  for j in range(segments):fa.append((tip,base+j,base+(j+1)%segments))
 ob=make(name,v,fa)
 if sub:subdiv(ob,sub)
 return ob

# Fit smooth oval rings to unoccluded source torso; arm sector excluded above .39.
yvals=np.arange(.306,.4701,.012);measure=[]
for y in yvals:
 q=p[(abs(p[:,1]-y)<.0022)&(p[:,0]>.003)]
 if y>.39:q=q[~((q[:,0]>.12)&(q[:,2]>-.10))]
 # Symmetric conic: a*x²+b*z²+c*z = 1. Iteratively trim source bumps.
 X=np.c_[q[:,0]**2,q[:,2]**2,q[:,2]];coeff=np.linalg.lstsq(X,np.ones(len(q)),rcond=None)[0]
 for _ in range(3):
  res=abs(np.einsum('ij,j->i',X,coeff)-1);sel=res<np.quantile(res,.90);coeff=np.linalg.lstsq(X[sel],np.ones(sel.sum()),rcond=None)[0]
 a,b,c=coeff;zc=-c/(2*b);k=1+c*c/(4*b);rx=np.sqrt(k/a);rz=np.sqrt(k/b)
 measure.append([float(y),float(rx),float(rz),float(zc)])
measure=np.array(measure)
# Smooth fit over entire torso rather than patching holes in a cut boundary.
coefs=[np.polyfit(measure[:,0]-.38,measure[:,j],3) for j in [1,2,3]]
rings=[(0,.252,-.021,0,0),(0,.257,-.021,.242,.196),(0,.267,-.022,.267,.213)]
for y in np.linspace(.284,.455,18):
 rx,rz,zc=[float(np.polyval(c,y-.38)) for c in coefs]
 rings.append((0,float(y),zc,rx,rz))
# Complete neck volume tucks inside accepted closed head; no edit to head.
rings.extend([(0,.475,-.022,.205,.170),(0,.496,-.020,.199,.160),(0,.516,-.018,.172,.137),(0,.530,-.018,.10,.085),(0,.536,-.018,0,0)])
# Exact shared interface: reproduce the accepted head's boundary coordinates.
# Head shape/topology remains unchanged; only boundary shading normals are shared.
N=np.load(D/'head-neck.npz');hp=N['p'];ids=N['neck_boundary'];nb=hp[ids];zc=.009
angles=np.arctan2(nb[:,2]-zc,nb[:,0]);order=np.argsort(angles);ids=ids[order];nb=nb[order];t=angles[order];seg=len(t);C,S=np.cos(t),np.sin(t)
# Exterior-only head normals exclude the provisional hidden bottom cap.
closure=N['closure'];hn=np.zeros_like(hp)
for face in head.data.polygons:
 inds=np.array(face.vertices,dtype=int)
 if closure[inds].any():continue
 xyz=hp[inds];normal=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])
 np.add.at(hn,inds,normal)
hn/=np.maximum(np.linalg.norm(hn,axis=1),1e-12)[:,None]
endnorm=hn[ids];radnorm=endnorm[:,0]*C+endnorm[:,2]*S
slope=np.clip(-endnorm[:,1]/np.maximum(radnorm,.1),-1.5,1.5)
# Source triangulation normals are noisy; use a broad angular tangent field.
H=np.stack([np.ones_like(t)]+[fun(k*t) for k in range(1,7) for fun in (np.cos,np.sin)],axis=1)
slope=np.einsum('ij,j->i',H,np.linalg.lstsq(H,slope,rcond=None)[0])
endnorm=np.c_[C,-slope,S];endnorm/=np.linalg.norm(endnorm,axis=1)[:,None]
vertices=[];y0=.37
for cx,y,cz,rx,rz in rings[1:]:
 if y>y0:break
 vertices.extend(np.c_[rx*C,np.full(seg,y),cz+rz*S].tolist())
rx,rz,cz=[float(np.polyval(c,y0-.38)) for c in coefs]
start=np.c_[rx*C,np.full(seg,y0),cz+rz*S]
rxp,rzp,czp=[float(np.polyval(np.polyder(c),y0-.38)) for c in coefs]
tan0=np.c_[rxp*C,np.ones(seg),czp+rzp*S];tan1=np.c_[slope*C,np.ones(seg),slope*S];length=nb[:,1]-y0
for u in np.linspace(0,1,24):
 q=(2*u**3-3*u*u+1)*start+(u**3-2*u*u+u)*length[:,None]*tan0+(-2*u**3+3*u*u)*nb+(u**3-u*u)*length[:,None]*tan1
 vertices.extend(q.tolist())
bound_start=len(vertices)-seg
# Continue inside the existing head closure, forming a complete torso object.
for rise,shrink in [(.004,.008),(.012,.025),(.022,.065),(.030,.12)]:
 q=nb.copy();q[:,1]+=rise;q[:,0]-=shrink*C;q[:,2]-=shrink*S;vertices.extend(q.tolist())
rn=len(vertices)//seg;faces=[]
for i in range(rn-1):
 for j in range(seg):aa=i*seg+j;bb=i*seg+(j+1)%seg;faces.append((aa,bb,bb+seg,aa+seg))
for base,y in [(0,.253),((rn-1)*seg,.51)]:
 tip=len(vertices);vertices.append((0,y,-.01))
 for j in range(seg):faces.append((tip,base+j,base+(j+1)%seg))
torso=make('Lulu_Torso',vertices,faces)
# Match normals on the exact seam; geometry is unchanged on the accepted head.
# Convert raw Y-up normal to Blender Z-up and then the head's local frame.
world_to_head=head.matrix_world.to_3x3().inverted();custom={}
for vi,n in zip(ids,endnorm):custom[int(vi)]=world_to_head@Vector((float(n[0]),float(-n[2]),float(n[1])))
head.data.normals_split_custom_set([custom.get(loop.vertex_index,head.data.corner_normals[loop.index].vector) for loop in head.data.loops])
torso.data.update();normals=[]
for loop in torso.data.loops:
 vi=loop.vertex_index
 if bound_start<=vi<bound_start+seg:
  n=endnorm[vi-bound_start];normals.append((float(n[0]),float(-n[2]),float(n[1])))
 else:normals.append(tuple(torso.data.corner_normals[loop.index].vector))
torso.data.normals_split_custom_set(normals)
torso['method']='Complete torso with source-fitted lower rings and exact shared head-neck boundary; matching boundary shading normals. No head vertex/face edits.'
head['assembly_note']='Accepted vertices, faces and transform unchanged. Boundary shading normals exclude hidden NeckClosure cap for continuous torso interface.'

# Preserve clear anatomical LEFT source shorts and foot, mirror to opposite side.
me=bpy.data.meshes.new('lowerworking');me.from_pydata(p.tolist(),[],f.tolist());bm=bmesh.new();bm.from_mesh(me);bpy.data.meshes.remove(me)
def cut(point,normal):
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=point,plane_no=normal,clear_outer=True,clear_inner=False)
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
cut((0,.285,0),(0,1,0));cut((0,0,0),(-1,0,0))
for v in bm.verts:
 if abs(v.co.x)<1e-6:v.co.x=0
bm.verts.index_update();v=np.array([v.co[:] for v in bm.verts]);fa=[[vv.index for vv in ff.verts] for ff in bm.faces];bm.free();nv=len(v);vv=v.copy();vv[:,0]*=-1
me=bpy.data.meshes.new('mirrorworking');me.from_pydata(np.concatenate([v,vv]).tolist(),[],fa+[[x+nv for x in reversed(ff)] for ff in fa]);bm=bmesh.new();bm.from_mesh(me);bpy.data.meshes.remove(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
# Weld only narrow midline. Lower-body half's pockets/cuffs/foot remain source geometry.
for _ in range(12):
 updates={}
 for v in bm.verts:
  if abs(v.co.x)<.008:
   w=(1-(abs(v.co.x)/.008)**2)**2;avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges);q=v.co.lerp(avg,.2*w)
   if abs(v.co.x)<1e-7:q.x=0
   updates[v]=q
 for v,q in updates.items():v.co=q
# Complete top inside torso. Flat fan is hidden; preserve all exposed source detail.
bound=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=bound,sides=0)
bm.verts.index_update();lower=make('Lulu_LowerBody_SourceMirror',[v.co[:] for v in bm.verts],[[v.index for v in ff.verts] for ff in bm.faces]);bm.free()
lower['method']='Clear LEFT lower-body half mirrored; original shorts, cuffs and foot surfaces retained outside narrow symmetry seam.'
lower['scope']='Shorts and feet retained together in this static body stage; garment separation/rig deferred.'

# Rebuild complete arm in a neutral hanging pose. Dimensions follow original
# upper-arm outer mass and hand envelope; no source skin connected to torso/face.
armrings=[
(.185,.470,-.020,0,0),(.215,.455,-.024,.032,.042),(.243,.438,-.027,.045,.055),
(.267,.413,-.028,.048,.060),(.280,.386,-.026,.047,.059),(.289,.358,-.020,.044,.056),
(.294,.329,-.013,.041,.052),(.295,.300,-.005,.039,.048),(.297,.272,.003,.039,.044),
(.300,.248,.008,.040,.043),(.300,.226,.010,.042,.044),(.299,.206,.010,.038,.040),
(.297,.191,.009,.028,.030),(.296,.181,.008,.014,.016),(.296,.177,.008,0,0)]
armrings=[(x-(.020 if y>.29 else .012),y,z,rx,rz) for x,y,z,rx,rz in armrings]
armL=loft('Lulu_Arm_L',armrings,40,2);armR=loft('Lulu_Arm_R',[(-x,y,z,rx,rz) for x,y,z,rx,rz in armrings],40,2)
for ob in [armL,armR]:ob['method']='Independent complete lofted arm, source-scale shoulder/forearm and simplified round palm. No fingers, no armature.'
parts=[head,crown,torso,lower,armL,armR]
# Explicit named part exports and assembly, with accepted head transforms unchanged.
for ob in bpy.context.scene.objects:ob.select_set(False)
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=torso
bpy.ops.export_scene.gltf(filepath=str(O/'lulu-assembled.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True)
for ob,fn in [(torso,'torso'),(lower,'lower-body'),(armL,'arm-left'),(armR,'arm-right')]:
 for o in parts:o.select_set(False)
 ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.gltf(filepath=str(O/f'lulu-{fn}.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=torso
bpy.context.scene['stage']='Independent torso and arms static candidate; head v1 is fixed/accepted. No rig or animation.'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'lulu-independent-parts.blend'))
assert np.array_equal(head_before,np.array([v.co[:] for v in head.data.vertices])) and np.array_equal(hm,np.array(head.matrix_world))
report={'revision':args.revision,'head_local_vertices_and_transform_unchanged':True,'body_ring_measurements':measure.tolist(),'parts':[],'armatures':0,'status':'INTERNAL_VISUAL_REVIEW'}
deps=bpy.context.evaluated_depsgraph_get()
for ob in parts:
 ev=ob.evaluated_get(deps);mesh=ev.to_mesh();bm=bmesh.new();bm.from_mesh(mesh)
 report['parts'].append({'name':ob.name,'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)})
 bm.free();ev.to_mesh_clear()
(O/'build.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='body_ring_measurements'},indent=2),flush=True)
