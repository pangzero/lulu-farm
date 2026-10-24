"""B01 species-specific editable surfaces. Existing assets are read-only."""
import bpy, math, json, sys, hashlib
from mathutils import Vector
from pathlib import Path
from math import sin,cos,pi,sqrt,exp
ROOT=Path(__file__).resolve().parents[1]; REV='r03'
SRC=ROOT/'assets-source/farm-assets/B01'; OUT=ROOT/'public/models/farm-assets/B01'; QA=ROOT/'review/farm-assets/B01'
for p in [SRC,OUT,QA]:p.mkdir(parents=True,exist_ok=True)
parts=[]
def linear(h):
 v=[int(h[i:i+2],16)/255 for i in (1,3,5)];return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
def mix(a,b,t):return tuple(x*(1-t)+y*t for x,y in zip(a,b))
def mat(name,color,rough=.65,paint=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*linear(color),1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.28
 if paint:
  n=m.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Color';m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
 return m

def mesh(name,vs,fs,material,colors=None):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(material)
 for f in d.polygons:f.use_smooth=True
 if colors:
  a=d.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT');d.color_attributes.active_color=a
  for v,c in zip(a.data,colors):v.color=(*c,1)
 parts.append(o);return o

def tube(name,pts,r,material):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=12;d.bevel_depth=r;d.bevel_resolution=3;d.use_fill_caps=True
 s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
 for i,(p,co) in enumerate(zip(s.bezier_points,pts)):
  p.co=co;p.handle_left_type=p.handle_right_type='AUTO';p.radius=1-.65*i/max(1,len(pts)-1)
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(material);parts.append(o);return o

def sphere(name,loc,scale,material,segments=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
 for f in o.data.polygons:f.use_smooth=True
 parts.append(o);return o

def leaf(name,point,colors,thick=.014,nu=24,nv=16,veins=False):
 # Square-to-disc parameterization avoids collapsed zero-area rows at leaf tips.
 vs=[];cs=[];fs=[]
 for i in range(nu+1):
  for j in range(nv+1):
   a=j/nv*2-1;b=i/nu*2-1;x=a*sqrt(1-b*b/2);y=b*sqrt(1-a*a/2);t=(y+1)/2;u=x/sqrt(max(1e-9,1-y*y))
   vs.append(point(t,u));c=mix(linear(colors[0]),linear(colors[1]),.18+.65*t)
   rib=exp(-(u/.095)**2)*.24
   if veins:
    for k in range(5):rib=max(rib,exp(-((t-(.22+k*.13+.20*abs(u)))/.026)**2)*.20*(1-abs(u)))
   cs.append(mix(c,linear(colors[2]),rib))
 for i in range(nu):
  for j in range(nv):
   a=i*(nv+1)+j;fs.append((a,a+1,a+nv+2,a+nv+1))
 o=mesh(name,vs,fs,paint,cs)
 sol=o.modifiers.new('Fleshy thickness','SOLIDIFY');sol.thickness=thick;sol.offset=0
 sub=o.modifiers.new('Rounded edge and surface','SUBSURF');sub.levels=1;sub.render_levels=1
 if False: # r03 uses integrated vertex-painted veins; removes interrupted bright filaments
  vm=mat(name+' soft veins',colors[2],.8)
  def lift(t,u):
   p=point(t,u);dt=point(min(.999,t+.002),u)-point(max(.001,t-.002),u);du=point(t,min(.999,u+.002))-point(t,max(-.999,u-.002));n=du.cross(dt).normalized()
   return p+n*(thick*.5-.001)
  tube(name+' embedded midrib',[lift(.08+i*.83/20,0) for i in range(21)],.003 if 'Cabbage' in name else .0017,vm)
  for k in range(4):
   for side in [-1,1]:
    tube(name+' embedded branching vein',[lift(.22+k*.135+.19*j/12,side*.84*j/12) for j in range(13)],.0014,vm)
 return o

def cabbage():
 # Broad cupped outer leaves rise at the back and fold outward at the front.
 for i in range(9):
  a=2*pi*i/9+.16;d=Vector((cos(a),sin(a),0));s=Vector((-sin(a),cos(a),0));back=(sin(a)+1)/2
  reach=.37+.025*sin(i*2);height=.19+.28*back;wid=.235+.015*cos(i*3)
  def pt(t,u,d=d,s=s,i=i,reach=reach,height=height,wid=wid):
   e=sin(pi*t)**.65;r=.035+reach*sin(t*pi*.67);z=.026+height*t+.05*sin(pi*t)
   p=d*(r-.09*u*u*e)+s*(u*wid*e)
   p.z=z+.075*u*u*e+.013*sin(t*15+i+u*2)*abs(u)**4*e
   return p
  leaf(f'Cabbage outer cupped leaf {i+1}',pt,('#438F32','#98C958','#BFD887'),.018,veins=True)
 # Each inner leaf crosses the crown, overlaps its neighbour and curls back in.
 for i in range(10):
  a=i*2.39996+.45;r=.245+.0035*i;top=-.18+.045*(i%3)
  def pt(t,u,a=a,r=r,top=top,i=i):
   polar=2.65-(2.65-top)*t;env=sin(pi*t)**.48
   az=a+u*env*1.40+.16*sin(t*pi)
   rad=r+.023*cos(u*4+t*5+i)*sin(pi*t)**2+.012*abs(u)**5*sin(pi*t)
   polar+=.028*sin(u*4+i)*abs(u)**3*sin(pi*t)
   return Vector((rad*sin(polar)*cos(az),rad*.96*sin(polar)*sin(az),.30+rad*cos(polar)))
  leaf(f'Cabbage overlapping heart leaf {i+1}',pt,('#7EB543','#C4DD73','#E3ECB2'),.008,40,28,True)
 # Small folded central leaves close the crown, no exposed spherical core.
 for i in range(3):
  a=i*2.1
  def pt(t,u,a=a):
   p=Vector((cos(a),sin(a),0))*(.02+.11*sin(pi*t));p+=Vector((-sin(a),cos(a),0))*u*.095*sin(pi*t)**.6;p.z=.43+.10*t+.025*u*u*sin(pi*t);return p
  leaf('Cabbage tender folded tip',pt,('#A3CE59','#D3E58A','#EAF0BD'),.012)
 sphere('Cabbage grounded stalk',(0,0,.045),(.065,.06,.048),green)

def tomato_leaf(name,start,end,width,phase=0):
 start=Vector(start);end=Vector(end);delta=end-start;side=Vector((-delta.y,delta.x,0)).normalized()
 def pt(t,u):
  env=sin(pi*t)**.72;serr=1+.055*sin(t*pi*12+phase)*abs(u)**4
  p=start+delta*t+side*(u*width*env*serr);p.z+=.065*sin(pi*t)+.032*u*u*env-.035*t*t;return p
 leaf(name,pt,('#2C7D32','#6CAF43','#B4D579'),.012,24,14,True)

def tomato_fruit(name,center,radius):
 # Tomato-specific broad shoulders, five subtle lobes, recessed stem and flattened bottom.
 vs=[];fs=[];cs=[];n=48;m=30;center=Vector(center)
 vs.append(center+Vector((0,0,radius*.79)));cs.append(linear('#D84922'))
 for i in range(1,m):
  th=pi*i/m
  for j in range(n):
   a=2*pi*j/n;rad=radius*sin(th)*(1+.033*cos(5*a)*sin(th)**.5)
   z=radius*(.91*cos(th)-.12*exp(-(th/.32)**2)+.035*exp(-((th-pi)/.3)**2))
   vs.append(center+Vector((rad*cos(a),rad*sin(a),z)));cs.append(mix(linear('#D93617'),linear('#FF6A2D'),.28+.35*(cos(th)+1)/2))
 bot=len(vs);vs.append(center+Vector((0,0,-radius*.875)));cs.append(linear('#DC3D1A'))
 for j in range(n):fs.append((0,1+j,1+(j+1)%n));fs.append((bot,1+(m-2)*n+(j+1)%n,1+(m-2)*n+j))
 for i in range(m-2):
  for j in range(n):a=1+i*n+j;b=1+i*n+(j+1)%n;fs.append((a,a+n,b+n,b))
 mesh(name,vs,fs,fruitpaint,cs)
 top=center+Vector((0,0,radius*.81))
 for k in range(5):
  a=k*2*pi/5;d=Vector((cos(a),sin(a),0));s=Vector((-sin(a),cos(a),0))
  def pt(t,u,d=d,s=s,top=top):return top+d*(.012+.112*t)+s*(.035*u*sin(pi*t)) + Vector((0,0,.02*sin(pi*t)-.024*t*t))
  leaf(name+' pointed calyx',pt,('#267D2C','#539B35','#89BB49'),.009,16,8)
 return top

def tomato():
 tube('Tomato main organic stem',[(0,0,0),(.01,0,.32),(-.025,.015,.68),(.035,.025,1.05),(.015,.02,1.16)],.032,green)
 for k,(center,r) in enumerate([((-.225,-.08,.36),.20),((.225,-.10,.31),.21),((.13,.12,.75),.135)]):
  tip=tomato_fruit('Tomato fruit '+str(k+1),center,r);tube('Fruit-bearing curved branch',[(0,.01,tip.z+.18),(tip.x*.78,tip.y,tip.z+.12),tip],.021,green)
 # Asymmetric compound foliage with terminal and paired leaflets.
 for idx,(root,tip,w) in enumerate([((0,0,.66),(-.40,.07,.84),.11),((.01,0,.86),(.38,.10,1.0),.105),((0,0,1.07),(-.23,.025,1.28),.105),((0,.02,.47),(.25,.26,.65),.10)]):
  a=Vector(root);b=Vector(tip);tube('Compound rachis '+str(idx),[a,(a+b)*.5+Vector((0,0,.04)),b],.016,green)
  delta=b-a;side=Vector((-delta.y,delta.x,0)).normalized()
  tomato_leaf('Terminal tomato leaflet',a+delta*.5,b+delta*.25,w,idx)
  for q in [-1,1]:
   start=a+delta*.43;end=start+delta*.35+side*q*.14
   tomato_leaf('Paired tomato leaflet',start,end,w*.78,idx+q)
 tomato_leaf('Tender terminal crown',(.015,.02,1.12),(-.08,-.16,1.32),.085)
 # A small five-petal flower on an open branch.
 c=Vector((-.19,-.02,.96));tube('Flower stem',[(0,0,.86),(-.10,0,.96),c],.012,green)
 for k in range(5):
  a=k*2*pi/5;sphere('Tomato yellow flower petal',c+Vector((.043*cos(a),-.008,.043*sin(a))),(.033,.018,.032),gold,20,12)
 sphere('Tomato flower centre',c+Vector((0,-.024,0)),(.025,.015,.025),pollen,20,12)

def corn_leaf(name,base,angle,length,width,rise,fall,colors=('#3A8E32','#8BBE43','#CAE28B')):
 d=Vector((cos(angle),sin(angle),0));s=Vector((-sin(angle),cos(angle),0));base=Vector(base)
 def pt(t,u):
  env=sin(pi*t)**.68;p=base+d*(length*t)+s*(u*width*env)
  p.z+=rise*sin(t*pi*.7)-fall*t*t+.025*u*u*env+.006*cos(t*12)*abs(u)**3*env
  return p
 return leaf(name,pt,colors,.012,32,14,True)

def corn():
 tube('Corn thick jointed stalk',[(0,0,0),(0,0,.38),(.015,.005,.8),(-.018,.015,1.2),(-.005,.03,1.30)],.032,green)
 for i,(z,a,L,w,rise,fall) in enumerate([(.15,3.35,.48,.115,.36,.20),(.32,.1,.46,.12,.28,.22),(.64,2.8,.40,.11,.30,.14),(.92,.35,.42,.13,.27,.08),(1.13,3.1,.30,.075,.32,.02)]):corn_leaf('Corn arching blade '+str(i),(0,0,z),a,L,w,rise,fall)
 # Main ear axis inclines right; front faces -Y, exposed cob has packed rounded kernel cells.
 origin=Vector((.055,-.025,.48));axis=Vector((.30,0,.954)).normalized();side=Vector((axis.z,0,-axis.x));front=Vector((0,-1,0));H=.55
 def ep(z,r,a):return origin+axis*z+(side*cos(a)+front*sin(a))*r
 # tapered core visible only between rows
 o=sphere('Corn cob under kernel rows',origin+axis*(H*.49),(.092,.092,H*.51),pollen);o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(axis)
 for row in range(11):
  t=(row+.5)/11;r=.082*(sin(pi*(.10+.85*t))**.60)
  for j in range(10):
   a=2*pi*j/10+.025*(row%2);loc=ep(H*t,r,a)
   o=sphere('Corn kernel row %02d cell %02d'%(row,j),loc,(.027,.025,.029),gold if (row+j)%3 else lightgold,16,10)
   for v in o.data.vertices:
    for dim in range(3):
     x=v.co[dim];v.co[dim]=math.copysign(abs(x)**.65,x)
   # Kernel local Z follows ear.
   normal=(side*cos(a)+front*sin(a));o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(axis)
 # Three broad husks clasp the lower ear and peel away at their tips.
 for idx,a in enumerate([.10,pi-.10,3*pi/2]):
  d=side*cos(a)+front*sin(a);s=axis.cross(d).normalized()
  def pt(t,u,d=d,s=s,idx=idx):
   env=sin(pi*t)**.65;rad=.112+.024*sin(t*pi*.9)+.13*t**5
   p=origin+axis*(H*t*1.05)+d*(rad-.018*u*u*env)+s*(u*.12*env)
   return p
  leaf('Corn clasping husk '+str(idx),pt,('#438D29','#A7CE55','#DBE89A'),.014,32,18,True)
 corn_leaf('Corn high flag leaf',(-.005,.03,1.30),.30,.31,.085,.26,.02)


def studio():
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.resolution_x=sc.render.resolution_y=900;sc.render.resolution_percentage=100
 sc.world=bpy.data.worlds.new('Neutral studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.80,.75,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.32
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 for name,loc,power,size in [('Key',(-3,-4,6),280,4),('Fill',(4,-1,3),140,3),('Rim',(0,4,5),230,3)]:
  d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.shape='DISK';d.size=size
 floor=mat('Review ground','#F4F2E8',1);bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));o=bpy.context.object;o.name='QA ground not exported';o.data.materials.append(floor)
 d=bpy.data.cameras.new('Fixed review camera');o=bpy.data.objects.new('Fixed review camera',d);sc.collection.objects.link(o);sc.camera=o;d.type='ORTHO';return sc

def bounds(obs):
 pts=[o.matrix_world@Vector(c) for o in obs if o.type=='MESH' for c in o.bound_box];return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]

def build(crop):
 global parts,paint,fruitpaint,green,gold,lightgold,pollen
 if (SRC/f'{crop}-mature-{REV}.blend').exists() or (OUT/f'{crop}-mature-{REV}.glb').exists():raise RuntimeError('Candidate already exists. Select a NEW revision before building.')
 bpy.ops.wm.read_factory_settings(use_empty=True);parts=[];bpy.context.preferences.filepaths.save_version=0
 paint=mat('Leaf vertex colors','#FFFFFF',.68,True);fruitpaint=mat('Tomato fruit vertex colors','#FFFFFF',.48,True);green=mat('Living stems','#428B31',.65);gold=mat('Golden kernels and petals','#F8C62E',.55);lightgold=mat('Warm golden variation','#F2B626',.57);pollen=mat('Flower and cob heart','#C89020',.73)
 globals()[crop]()
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0]
 # Apply geometry only on temporary export copies, join by material to control draw calls.
 originals=list(parts);bpy.ops.object.duplicate();copies=list(bpy.context.selected_objects)
 bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.ops.object.join();merged=bpy.context.object;merged.name=crop+'_mature_'+REV
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.export_scene.gltf(filepath=str(OUT/f'{crop}-mature-{REV}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
 bpy.data.objects.remove(merged,do_unlink=True)
 sc=studio();target=Vector((0,0,.32 if crop=='cabbage' else .72));sc.camera.location=target+Vector((1.35,-4,2.25));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=1.32 if crop=='cabbage' else 1.96
 bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'{crop}-mature-{REV}.blend'))
 sc.render.filepath=str(QA/f'{crop}-{REV}-initial.png');bpy.ops.render.render(write_still=True)
 print('B01 BUILT',crop,flush=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['cabbage','tomato','corn']
for crop in args:build(crop)
