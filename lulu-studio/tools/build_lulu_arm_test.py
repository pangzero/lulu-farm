"""Small-range arm rig study; source clay stays untouched."""
import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets-source/lulu-head-study.blend'))
head=bpy.data.objects['Source_HeadStudy_ContinuousCage'];head.hide_set(False)
body_tree=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
clay=head.data.materials[0]
bpy.data.objects.remove(bpy.data.objects['Lulu_ContinuousShoulderSkin'],do_unlink=True)
# Reshape only shoulder/upper-arm cage rings. All pad-palm rings stay intact.
rows=[(1.045,.435,-.025,.070,.096,.432,-.025,.075,.103),
 (.990,.480,-.032,.092,.109,.475,-.028,.104,.117),
 (.925,.525,-.012,.102,.118,.515,-.025,.108,.123),
 (.850,.567,.008,.104,.122,.555,-.018,.108,.122),
 (.770,.610,.005,.098,.120,.596,-.020,.101,.120),
 (.690,.626,-.015,.090,.116,.617,-.032,.094,.116)]
for side in [-1,1]:
 source=bpy.data.objects['Source_Arm_'+str(side)]
 for v in source.data.vertices:
  for z,cx,cy,rx,ry,nx,ny,nrx,nry in rows:
   if abs(v.co.z-z)<1e-5:
    v.co.x=side*(nx+(side*v.co.x-cx)*nrx/rx)
    v.co.y=ny+(v.co.y-cy)*nry/ry
    break
 source.data.update()
parts=[]
for name in ['Source_HeadStudy_ContinuousCage','Source_Arm_-1','Source_Arm_1']:
 src=bpy.data.objects[name];src.hide_set(False)
 data=bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
 o=bpy.data.objects.new('Test_'+name,data);bpy.context.collection.objects.link(o);parts.append(o)
 if 'Arm_' in name:
  side=-1 if name.endswith('-1') else 1
  for v in data.vertices:
   x,y,z=v.co
   if z>=.94:continue
   hit=body_tree.ray_cast((side*1.5,y,z),(-side,0,0),2)[0]
   if hit is not None:
    t=min(1,max(0,(.94-z)/.12));t=t*t*(3-2*t)
    gap=.020 if z<=.615 else .018
    edge=abs(hit.x)+gap*t
    if abs(x)<edge:v.co.x=side*(abs(x)*(1-t)+edge*t)
 src.hide_set(True)
bpy.context.view_layer.update()
refs=[BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get()) for o in parts]
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();skin=parts[0];skin.name='Lulu_ArmTestSkin'
r=skin.modifiers.new('Shoulder-only attachment','REMESH');r.mode='VOXEL';r.voxel_size=.0055;r.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=r.name)
g=skin.vertex_groups.new(name='RootBlend')
for v in skin.data.vertices:
 x,y,z=v.co
 w=math.exp(-((abs(x)-.49)/.105)**4-((z-.95)/.12)**4)
 if w>.001:g.add([v.index],w,'REPLACE')
s=skin.modifiers.new('Shoulder root relaxation','SMOOTH');s.vertex_group=g.name;s.factor=.65;s.iterations=65;bpy.ops.object.modifier_apply(modifier=s.name)
for v in skin.data.vertices:
 x,y,z=v.co;w=math.exp(-((abs(x)-.49)/.105)**4-((z-.95)/.12)**4)
 if w<.2:
  hit=min((t.find_nearest(v.co) for t in refs),key=lambda h:h[3]);blend=min(1,w/.2);blend=blend*blend*(3-2*blend);v.co=v.co*blend+hit[0]*(1-blend)
for p in skin.data.polygons:p.use_smooth=True
skin.data.materials.clear();skin.data.materials.append(clay)
armdata=bpy.data.armatures.new('Lulu_ArmInspectionRig');rig=bpy.data.objects.new('Lulu_ArmInspectionRig',armdata);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
root=armdata.edit_bones.new('Root');root.head=(0,0,.4);root.tail=(0,0,1.1)
for side in [-1,1]:
 upper=armdata.edit_bones.new('UpperArm_'+str(side));upper.head=(side*.49,-.03,.975);upper.tail=(side*.608,-.044,.735);upper.parent=root
 fore=armdata.edit_bones.new('Forearm_'+str(side));fore.head=upper.tail;fore.tail=(side*.615,-.06,.46);fore.parent=upper;fore.use_connect=True
bpy.ops.object.mode_set(mode='OBJECT')
groups={n:skin.vertex_groups.new(name=n) for n in ['Root','UpperArm_-1','UpperArm_1','Forearm_-1','Forearm_1']}
weights=[];membership_weights=[]
for v in skin.data.vertices:
 x,y,z=v.co;side=-1 if x<0 else 1
 db=refs[0].find_nearest(v.co)[3];da=refs[1 if side<0 else 2].find_nearest(v.co)[3]
 membership=(db**4)/(db**4+da**4+1e-16)
 top=min(1,max(0,(1.09-z)/.13));top=top*top*(3-2*top)
 lateral=min(1,max(0,(abs(x)-.39)/.11));lateral=lateral*lateral*(3-2*lateral)
 membership_weights.append(membership*top*lateral if z<1.09 else 0)
# Diffuse weights over the actual joined shoulder surface to avoid a rigid
# moving arm meeting a completely fixed patch of chest at a single seam.
w=np.array(membership_weights);edges=np.array([e.vertices[:] for e in skin.data.edges]);a=edges[:,0];b=edges[:,1]
degree=np.bincount(edges.ravel(),minlength=len(w))
coords=np.array([v.co[:] for v in skin.data.vertices]);zone=np.exp(-((coords[:,2]-.97)/.14)**4)*np.clip((np.abs(coords[:,0])-.32)/.14,0,1)
for _ in range(65):
 total=np.bincount(a,weights=w[b],minlength=len(w))+np.bincount(b,weights=w[a],minlength=len(w))
 w=w*(1-.55*zone)+total/np.maximum(degree,1)*(.55*zone)
w[coords[:,2]>1.12]=0
for v,weight in zip(skin.data.vertices,w):
 x,y,z=v.co;side=-1 if x<0 else 1
 elbow=min(1,max(0,(.82-z)/.17));elbow=elbow*elbow*(3-2*elbow)
 vals={'Root':1-weight,'UpperArm_'+str(side):weight*(1-elbow),'Forearm_'+str(side):weight*elbow}
 for n,val in vals.items():
  if val>1e-7:groups[n].add([v.index],float(val),'REPLACE')
 weights.append((z,float(weight)))
# Fit the medial upper-arm surface close to the torso after remeshing.
# This retains a real opening without the voxel-sized bright slit; palm unchanged.
for v,weight in zip(skin.data.vertices,w):
 x,y,z=v.co
 if not (.615<z<.93) or weight<.55:continue
 side=-1 if x<0 else 1
 hit=body_tree.ray_cast((side*1.5,y,z),(-side,0,0),2)[0]
 if hit is None:continue
 gap=abs(x)-abs(hit.x)
 if .004<gap<.065:
  taper=min(1,(z-.615)/.065,(.93-z)/.055);taper=taper*taper*(3-2*taper)
  radial=math.exp(-((gap-.018)/.030)**4)
  shift=min(.012,max(0,gap-.004))*taper*radial
  v.co.x-=side*shift
skin.data.update()
# A bounded corrective preserves shoulder-front volume only during backward swing.
skin.shape_key_add(name='Basis')
corrective=skin.shape_key_add(name='BackShoulderSupport')
for v,k in zip(skin.data.vertices,corrective.data):
 x,y,z=v.co;side=-1 if x<0 else 1
 weight=math.exp(-((abs(x)-.525)/.075)**4-((y+.105)/.090)**4-((z-.955)/.065)**4)
 k.co.y-=.020*weight;k.co.x+=side*.004*weight
mod=skin.modifiers.new('Arm inspection skinning','ARMATURE');mod.object=rig;skin.parent=rig
bpy.context.scene.frame_set(1)
# Pose is driven by bone quaternions in the viewer; retain rig, not a baked clip.
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
 if o==rig or (o.type=='MESH' and not o.name.startswith('Source_')):o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets-source/lulu-arm-test.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/lulu-arm-test.glb'),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_skins=True)
(ROOT/'review/arm-motion-rig.json').write_text(json.dumps({'bones':[b.name for b in armdata.bones],'skin_vertices':len(skin.data.vertices),'head_weight_max':max(w for z,w in weights if z>1.2),'source':'lulu-head-study.blend','preserve_static_source':True},indent=2))
