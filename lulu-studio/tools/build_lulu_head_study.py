"""Head clay study: one subdivision cage fitted jointly to three silhouettes.
No eye beds, surface displacement, painted features, or view-dependent geometry.
"""
import bpy, math, json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'review/head-study-baseline/lulu.blend'))
for o in list(bpy.data.objects):
 if o.type=='ARMATURE' or o.name.startswith(('Lulu_ContinuousBody','Smile','Can')):
  bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.objects:
 o.parent=None
 for mod in list(o.modifiers):
  if mod.type=='ARMATURE':o.modifiers.remove(mod)
 o.animation_data_clear()
clay=bpy.data.materials.new('Neutral_Clay_Inspection');clay.use_nodes=True
bs=clay.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.52,.52,.52,1);bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=.15
for o in bpy.data.objects:
 if o.type=='MESH':o.data.materials.clear();o.data.materials.append(clay)
# Measured full-image silhouettes. Width is averaged across front and back.
# Ear-occluded upper skull bounds are explicitly estimated, not treated as observations.
# z, half-width, side-left, side-right
head=np.array([
 [1.05,.545,-.391,.518],[1.15,.614,-.440,.633],
 [1.25,.670,-.505,.683],[1.35,.696,-.541,.695],
 [1.45,.688,-.556,.705],[1.55,.652,-.549,.688],
 [1.65,.606,-.522,.650],[1.75,.554,-.470,.506],
 [1.85,.488,-.407,.431],[1.95,.385,-.285,.320],[1.98,.327,-.240,.270],
 [2.012,.235,-.173,.185],[2.045,.008,-.008,.008]])
angle=math.atan2(2.6,10);c=math.cos(angle);s=math.sin(angle)
center=-(head[:,3]+head[:,2])/(2*c)
depth=np.sqrt(np.maximum(.00001,((head[:,3]-head[:,2])/2)**2-(head[:,1]*s)**2))/c
# Body only gives context. Fit head and neck in the same continuous cage.
lower=np.array([[.35,.10,-.02,.08],[.42,.30,-.015,.22],[.56,.558,-.045,.435],[.75,.52,-.015,.39],[.90,.521,-.010,.367],[.95,.529,-.014,.380]])
target=np.concatenate([lower,np.stack([head[:,0],head[:,1],center,depth],axis=1)])
zc=np.array([.32,.35,.43,.57,.74,.91,1.04,1.17,1.30,1.43,1.56,1.69,1.79,1.89,1.99,2.075,2.09])
n=len(zc)
# Uniform cubic B-spline basis is the longitudinal limit of this quad cage.
def basis(u):
 j=min(n-4,int(u));t=u-j
 out=np.zeros(n);out[j:j+4]=[(1-t)**3/6,(3*t**3-6*t*t+4)/6,(-3*t**3+3*t*t+3*t+1)/6,t**3/6]
 return out
us=np.linspace(0,n-3-1e-8,1600);B=np.array([basis(u) for u in us]);zs=B@zc
A=np.array([basis(float(np.interp(z,zs,us))) for z in target[:,0]])
D=np.diff(np.eye(n),n=2,axis=0)
# Joint global regularized fit; all control rings participate together.
weight=np.ones(len(target));weight[-2:]=2
values=[]
for col in [1,2,3]:
 lhs=np.vstack([A*weight[:,None],D*.18])
 rhs=np.concatenate([target[:,col]*weight,np.zeros(n-2)])
 values.append(np.linalg.lstsq(lhs,rhs,rcond=None)[0])
rx,cy,ry=values
# Preserve the approved head cage. Adjust the lower torso control rings as one arc.
ry[2]=.355
cy[3],ry[3]=-.010,.430
cy[4],ry[4]=-.025,.415
cy[5],ry[5]=-.005,.355
rx=np.maximum(rx,.003);ry=np.maximum(ry,.003)
segments=24
# Compensation for the angular shrink of the subdivision limit, common to all rings.
angular=(2+math.cos(2*math.pi/segments))/3
verts=[]
for j,z in enumerate(zc):
 for k in range(segments):
  a=2*math.pi*k/segments
  # Broad lower face and rounded rear skull share one closed cross-section.
  # The angular field varies smoothly over the entire head, not a glued-on muzzle.
  # cos^2 has zero slope at the lateral seam, preserving tangent continuity.
  face_weight=math.exp(-((z-1.40)/.31)**4)
  front=math.sin(a)<0
  fullness=.21*face_weight if front else .025*face_weight
  y=math.sin(a)*(1+fullness*math.cos(a)**2)
  verts.append((float(rx[j]/angular*math.cos(a)),float(cy[j]+ry[j]/angular*y),float(z)))
faces=[]
for j in range(n-1):
 for k in range(segments):
  a=j*segments+k;b=j*segments+(k+1)%segments;faces.append((a,b,b+segments,a+segments))
faces.extend([tuple(reversed(range(segments))),tuple((n-1)*segments+k for k in range(segments))])
me=bpy.data.meshes.new('HeadBody_QuadCage');me.from_pydata(verts,[],faces);me.update()
obj=bpy.data.objects.new('HeadStudy_ContinuousCage',me);bpy.context.collection.objects.link(obj);obj.data.materials.append(clay)
for p in me.polygons:p.use_smooth=True
sub=obj.modifiers.new('Whole form subdivision','SUBSURF');sub.subdivision_type='CATMULL_CLARK';sub.levels=3;sub.render_levels=3
import sys
sys.path.insert(0,str(ROOT/'tools'))
from refine_lulu_clay import refine
def torso_profile(z):
 b=basis(float(np.interp(z,zs,us)))
 return float(b@rx),float(b@cy),float(b@ry)
refine(clay,np,torso_profile)
# Keep the full editable cage and modifier in the .blend.
bpy.ops.object.select_all(action='DESELECT')
for export_obj in bpy.context.scene.objects:
 if export_obj.type=='MESH' and not export_obj.name.startswith('Source_'):export_obj.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects.get('Lulu_ContinuousShoulderSkin',obj)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets-source/lulu-head-study.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/lulu-head-study.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_skins=False)
report={'method':'single Catmull-Clark quad cage; joint silhouette fit and smooth broad-face cross sections','control_vertices':len(verts),'head_targets':head.tolist(),'upper_occluded_estimates_z':[1.85,1.95,2.012],'side_camera':[-10,1.75,2.6],'textures':0,'eyes':0,'mouth':0,'control_rings':[list(map(float,row)) for row in zip(zc,rx,cy,ry)]}
(ROOT/'review/head-study-fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('HEAD_STUDY_EXPORTED')
