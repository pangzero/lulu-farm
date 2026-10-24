"""Continuous subdivision limbs and closed shallow triangular ear shells."""
import bpy,math,bmesh
from pathlib import Path
from mathutils import Vector

def refine(clay,np,torso_profile):
 def mesh(name,v,f,mat=clay,sub=2):
  m=bpy.data.meshes.new(name);m.from_pydata(v,[],f);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(mat)
  bm=bmesh.new();bm.from_mesh(m);bmesh.ops.dissolve_degenerate(bm,dist=0.00001,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(m);bm.free()
  for p in m.polygons:p.use_smooth=True
  if sub:
   s=o.modifiers.new('Continuous soft surface','SUBSURF');s.levels=sub;s.render_levels=sub
  return o
 def loft(name,rings,fn,N=32):
  v=[fn(row,2*math.pi*k/N) for row in rings for k in range(N)];f=[]
  for j in range(len(rings)-1):
   for k in range(N):a=j*N+k;b=j*N+(k+1)%N;f.append((a,b,b+N,a+N))
  f += [tuple(reversed(range(N))),tuple((len(rings)-1)*N+k for k in range(N))]
  return mesh(name,v,f)
 for o in list(bpy.data.objects):
  if o.name.startswith(('Arm_','Foot_','Ear_','Shorts_')):bpy.data.objects.remove(o,do_unlink=True)
 for side in [-1,1]:
  # Simplified hand and forearm share a single smooth control cage, without digits.
  # Short shoulder attachment, bowed upper arm and a short flattened pad palm.
  # Palm radii taper monotonically: no pinched wrist followed by a ball end.
  rings=[(1.085,.395,-.010,.025,.040),(1.045,.435,-.025,.070,.096),
   (.990,.480,-.032,.092,.109),(.925,.525,-.012,.102,.118),
   (.850,.567,.008,.104,.122),(.770,.610,.005,.098,.120),
   (.690,.626,-.015,.090,.116),(.615,.627,-.045,.085,.108),
   (.550,.622,-.064,.081,.098),(.495,.618,-.068,.078,.092),
   (.450,.615,-.062,.067,.080),(.425,.613,-.053,.042,.051),(.413,.612,-.048,.008,.012)]
  loft('Arm_'+str(side),rings,lambda r,a:(side*(r[1]+r[3]*math.cos(a)),r[2]+r[4]*math.sin(a),r[0]))
  rings=[(.003,.099,.125,-.075),(.009,.128,.160,-.075),(.034,.146,.182,-.075),(.090,.150,.177,-.065),(.160,.145,.153,-.038),(.225,.132,.120,-.016),(.290,.117,.103,-.008),(.31,.075,.065,-.008)]
  loft('Foot_'+str(side),rings,lambda r,a:(side*.30+r[1]*math.cos(a),r[3]+r[2]*math.sin(a),r[0]))
  # A solid rounded triangular volume is established before its shallow inset.
  # Positions are shared by front / side / back; the lower two corners bury
  # a broad root into the existing head rather than hanging from a narrow tip.
  import os
  cavity=float(os.environ.get('LULU_EAR_CAVITY','.073'))
  corners=[(-.155,-.120),(.110,-.060),(.088,.160)];boundary=[]
  for i,c in enumerate(corners):
   prev=corners[(i-1)%3];nxt=corners[(i+1)%3]
   p=np.array(c)*.60+np.array(prev)*.40;q=np.array(c)*.60+np.array(nxt)*.40
   for k in range(12):
    t=k/12;boundary.append((1-t)**2*p+2*t*(1-t)*np.array(c)+t*t*q)
  ev=[];angle=side*math.radians(50)
  # Latitude rings make a closed, fleshy lens with a convex ear back.
  latitudes=np.linspace(-math.pi/2+.012,math.pi/2-.012,23)
  for latitude in latitudes:
   scale=math.cos(latitude)
   front=latitude<0
   depth=(.083 if front else .100)*math.sin(latitude)
   # Inset stays within the central half; it fades before reaching the root/rim.
   for x,z in boundary:
    xx=side*x*scale;zz=z*scale
    d=depth+(cavity*math.exp(-((scale/.54)**4))*(.80+.20*math.tanh((zz+.015)/.040)) if front else 0)
    ev.append((side*.535+xx*math.cos(angle)-d*math.sin(angle),
      .115+xx*math.sin(angle)+d*math.cos(angle),1.850+zz))

  N=len(boundary);ef=[]
  for j in range(len(latitudes)-1):
   for k in range(N):
    a=j*N+k;b=j*N+(k+1)%N;ef.append((a,b,b+N,a+N))
  ef += [tuple(reversed(range(N))),tuple((len(latitudes)-1)*N+k for k in range(N))]
  mesh('Ear_'+str(side),ev,ef)
 # Use a finer continuous garment field with fuller thighs blended into the seat.
 import sys
 sys.path.insert(0,str(Path(__file__).parent))
 from lulu_clay_garment import build_garment
 garment=build_garment(lambda name,v,f,mat:mesh(name,v,f,mat,0),clay,bpy,np)
 sm=garment.modifiers.new('Cloth curvature relaxation','SMOOTH');sm.factor=.65;sm.iterations=10
 bpy.context.view_layer.objects.active=garment
 bpy.ops.object.modifier_apply(modifier=sm.name)
 # Remove only the hidden upper cap before fitting the outer cloth surface.
 bm=bmesh.new();bm.from_mesh(garment.data)
 caps=[f for f in bm.faces if f.normal.z>.7 and min(v.co.z for v in f.verts)>.565]
 bmesh.ops.delete(bm,geom=caps,context='FACES');bm.to_mesh(garment.data);bm.free()
 # A single Hermite profile connects the seat to the torso waist tangent.
 # It replaces the old blended belt region, whose radial slope reversed twice.
 from mathutils.bvhtree import BVHTree
 head_tree=BVHTree.FromObject(bpy.data.objects['HeadStudy_ContinuousCage'],bpy.context.evaluated_depsgraph_get())
 cloth_tree=BVHTree.FromObject(garment,bpy.context.evaluated_depsgraph_get())
 samples=128;profiles=[]
 for tree,height,center in [(cloth_tree,.33,-.035),(cloth_tree,.345,-.035),
                            (head_tree,.585,torso_profile(.585)[1]),(head_tree,.605,torso_profile(.605)[1])]:
  radii=[]
  for k in range(samples):
   angle=2*math.pi*k/samples;direction=Vector((math.cos(angle),math.sin(angle),0))
   origin=Vector((0,center,height));hit=tree.ray_cast(origin,direction,2)[0]
   radii.append((hit-origin).length)
  profiles.append(radii)
 z0,z1=.33,.585;span=z1-z0
 for v in garment.data.vertices:
  z=v.co.z
  if z<z0:continue
  t=min(1,max(0,(z-z0)/span));h=t*t*(3-2*t)
  angle=math.atan2(v.co.y+.035,v.co.x)%(2*math.pi);u=angle/(2*math.pi)*samples;j=int(u);f=u-j
  r=[p[j]*(1-f)+p[(j+1)%samples]*f for p in profiles]
  end=r[2]+.003;delta=(end-r[0])/span
  m0=(r[1]-r[0])/.015;m1=(r[3]-r[2])/.020
  if delta>0:m0=min(max(m0,0),3*delta);m1=min(max(m1,0),3*delta)
  radius=(2*t**3-3*t*t+1)*r[0]+(t**3-2*t*t+t)*span*m0+(-2*t**3+3*t*t)*end+(t**3-t*t)*span*m1
  center=-.035*(1-h)+torso_profile(.585)[1]*h
  v.co.x=radius*math.cos(angle);v.co.y=center+radius*math.sin(angle)
 # Restrained front-only cloth relaxation: reduce the puff above the crotch.
 # Preserve waist, U opening, hem heights and the back/seat volume.
 for v in garment.data.vertices:
  x,y,z=v.co
  if .20<z<.58 and y<-.10:
   edge=math.sin(math.pi*(z-.20)/(.58-.20))**2
   across=math.exp(-((x/.46)**4))
   front=min(1,max(0,(-y-.10)/.16));front=front*front*(3-2*front)
   v.co.y += .010*edge*across*front
 garment.data.update()
 bm=bmesh.new();bm.from_mesh(garment.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(garment.data);bm.free()
 # Round the tail end without changing its attachment.
 tail=bpy.data.objects.get('Waist_BackTeardrop')
 if tail:
  sm=tail.modifiers.new('Soft tail tip','SMOOTH');sm.factor=.5;sm.iterations=5

 # Sculpt-style unified skin at shoulder roots. Retain editable cages as sources.
 # Project the remeshed surface back outside the shoulder blend zone so the
 # approved head shape does not get relaxed along with the shoulder junctions.
 head=bpy.data.objects['HeadStudy_ContinuousCage']
 sources=[head,bpy.data.objects['Arm_-1'],bpy.data.objects['Arm_1']]
 deps=bpy.context.evaluated_depsgraph_get()
 reference_trees=[BVHTree.FromObject(o,deps) for o in sources]
 pieces=[]
 bpy.ops.object.select_all(action='DESELECT')
 for src in sources:
  data=bpy.data.meshes.new_from_object(src.evaluated_get(deps))
  part=bpy.data.objects.new('Skin work',data);bpy.context.collection.objects.link(part);part.select_set(True);pieces.append(part)
 bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();skin=pieces[0];skin.name='Lulu_ContinuousShoulderSkin'
 rem=skin.modifiers.new('Unified shoulder volume','REMESH');rem.mode='VOXEL';rem.voxel_size=.009;rem.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=rem.name)
 group=skin.vertex_groups.new(name='Shoulder junction smoothing')
 def weight(co):
  x,y,z=co
  return math.exp(-((abs(x)-.52)/.17)**4-((z-.845)/.245)**4)*max(0,min(1,(1.13-z)/.07))
 for v in skin.data.vertices:
  w=weight(v.co)
  if w>.001:group.add([v.index],w,'REPLACE')
 smooth=skin.modifiers.new('Broad shoulder blend','SMOOTH');smooth.vertex_group=group.name;smooth.factor=.8;smooth.iterations=100
 bpy.ops.object.modifier_apply(modifier=smooth.name)
 for v in skin.data.vertices:
  w=weight(v.co)
  if w<.2:
   hits=[t.find_nearest(v.co) for t in reference_trees];hit=min((h for h in hits if h[0] is not None),key=lambda h:h[3])
   blend=min(1,max(0,w/.2));blend=blend*blend*(3-2*blend)
   v.co=v.co*blend+hit[0]*(1-blend)
 # Soften the lower end of the chest-side groove locally, without extending
 # shoulder fusion toward the neck or changing the preserved pad palm.
 g=skin.vertex_groups.new(name='Short chest groove termination')
 for v in skin.data.vertices:
  x,y,z=v.co
  w=math.exp(-((abs(x)-.535)/.075)**4-((z-.82)/.115)**4-((y+.105)/.11)**4)
  if w>.001:g.add([v.index],w,'REPLACE')
 sm=skin.modifiers.new('Soft groove termination','SMOOTH');sm.vertex_group=g.name;sm.factor=.65;sm.iterations=110
 bpy.context.view_layer.objects.active=skin;bpy.ops.object.modifier_apply(modifier=sm.name)
 for face in skin.data.polygons:face.use_smooth=True
 skin.data.materials.clear();skin.data.materials.append(clay)
 for src in sources:
  src.name='Source_'+src.name;src.hide_render=True;src.hide_set(True)
