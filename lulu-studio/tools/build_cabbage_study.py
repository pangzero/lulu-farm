"""Isolated art-quality study. Keeps all v1 crops untouched; creates a review candidate."""
import bpy, math, sys, json, struct
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets-source/crop-studies'
OUT=ROOT/'public/models/crop-studies'
REVIEW=ROOT/'review/crop-studies'
for p in (SOURCE,OUT,REVIEW):p.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0

def rgb(h):
    vals=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in vals)

def mix(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))
def smooth(a,b,v):
    t=max(0,min(1,(v-a)/(b-a)))
    return t*t*(3-2*t)

def surface_material(name,roughness=.57):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(1,1,1,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Specular IOR Level'].default_value=.28
    # Vertex paint is retained in Blender and travels to glTF COLOR_0.
    c=m.node_tree.nodes.new('ShaderNodeVertexColor');c.layer_name='LeafColor'
    m.node_tree.links.new(c.outputs['Color'],p.inputs['Base Color'])
    m.diffuse_color=(*rgb('#8CC954'),1)
    return m

leafmat=surface_material('Painted cabbage / soft matte')
rootmat=bpy.data.materials.new('Fresh cut green stalk');rootmat.diffuse_color=(*rgb('#88B65A'),1);rootmat.use_nodes=True
rootmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rootmat.diffuse_color
rootmat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.67
plant=bpy.data.collections.new('Cabbage_v2_editable');bpy.context.scene.collection.children.link(plant)
parts=[]

def add_mesh(name,verts,faces,colors):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);plant.objects.link(o);data.materials.append(leafmat)
    attr=data.color_attributes.new(name='LeafColor',type='FLOAT_COLOR',domain='POINT')
    for i,c in enumerate(colors):attr.data[i].color=(*c,1)
    data.color_attributes.active_color=attr
    for p in data.polygons:p.use_smooth=True
    solid=o.modifiers.new('Fleshy leaf edge / editable','SOLIDIFY');solid.thickness=.010;solid.offset=-.45;solid.use_even_offset=True
    parts.append(o)
    return o

def vein_amount(t,u):
    # Main vein and curved feathering are painted into the leaf surface, with restrained relief.
    center=math.exp(-(u/.045)**2)*(.55+.45*(1-t))
    branch=0
    for k in range(5):
        base=.20+k*.125
        line=base+.12*abs(u)+.10*u*u
        branch=max(branch,math.exp(-((t-line)/.012)**2)*smooth(.01,.15,abs(u))*(1-smooth(.68,.95,abs(u))))
    return center*.15

def painted(t,u,outer,index):
    if outer:
        base=rgb('#438F37');mid=rgb('#70B844');tip=rgb('#A0D45D');vein=rgb('#C1DB88')
    else:
        base=rgb('#7CBA45');mid=rgb('#A6D75B');tip=rgb('#D3EA8A');vein=rgb('#E3F1AE')
    c=mix(base,mid,smooth(.03,.58,t));c=mix(c,tip,smooth(.55,1,t)*.63)
    edge=smooth(.55,1,abs(u))*.10
    c=mix(c,tip,edge)
    c=mix(c,vein,vein_amount(t,u)*(.52 if outer else .40))
    shade=.96+.035*math.sin(index*2.3)+.025*math.sin(t*9+u*3)
    return tuple(min(1,v*shade) for v in c)

veinmat=bpy.data.materials.new('Leaf veins / embedded pale relief');veinmat.use_nodes=True
veinmat.diffuse_color=(*rgb('#BCD782'),1)
veinmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=veinmat.diffuse_color
veinmat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.68

def vein_mesh(name,points,radius):
    verts=[];faces=[];sides=5
    points=[Vector(p) for p in points]
    for i,p in enumerate(points):
        tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        guide=Vector((0,0,1)) if abs(tangent.z)<.85 else Vector((1,0,0))
        a=tangent.cross(guide).normalized();b=tangent.cross(a)
        rr=radius*(1-.75*i/(len(points)-1))
        for j in range(sides):
            angle=j*2*math.pi/sides;verts.append(p+(a*math.cos(angle)+b*math.sin(angle))*rr)
    for i in range(len(points)-1):
        for j in range(sides):q=i*sides+j;r=i*sides+(j+1)%sides;faces.append((q,r,r+sides,q+sides))
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    o=bpy.data.objects.new(name,data);plant.objects.link(o);data.materials.append(veinmat)
    for p in data.polygons:p.use_smooth=True
    parts.append(o)

def lay_veins(name,point,head=False):
    def lifted(t,u):
        p=point(t,u)
        dt=point(min(.999,t+.002),u)-point(max(.001,t-.002),u)
        du=point(t,min(.999,u+.002))-point(t,max(-.999,u-.002))
        normal=du.cross(dt).normalized() if head else dt.cross(du).normalized()
        return p+normal*.0015
    vein_mesh(name+' / midrib',[lifted(.07+.86*i/25,0) for i in range(26)],.0025 if head else .0028)
    for k in range(4):
        start=.22+k*.14
        for side in (-1,1):
            vein_mesh(name+' / branching vein',[lifted(start+.15*(i/15)+.055*(i/15)**2,side*.88*(i/15)) for i in range(16)],.00145)

def crown_leaf(index,angle,top,reach,width):
    d=Vector((math.cos(angle),math.sin(angle),0));s=Vector((-d.y,d.x,0));verts=[];colors=[];faces=[]
    nv=28;nu=26
    def point(t,u):
        r=.028+reach*math.sin(t*math.pi*.59);z=.015+top*t-.073*math.sin(math.pi*t)
        envelope=math.sqrt(max(0,1-(2*t-1)**2))
        breadth=envelope*width
        curl=.060*u*u*math.sin(math.pi*t)
        lip=.009*smooth(.75,1,abs(u))*math.sin(math.pi*t)
        wave=.006*math.sin(t*math.pi*5+index)*abs(u)**5*math.sin(math.pi*t)
        p=d*(r-.055*u*u*math.sin(math.pi*t))+s*(u*breadth+.017*math.sin(math.pi*t)*math.sin(index))
        p.z=z+curl+lip+wave
        return p
    for i in range(nv+1):
        for j in range(nu+1):
            a=j/nu*2-1;b=i/nv*2-1
            x=a*math.sqrt(1-b*b/2);y=b*math.sqrt(1-a*a/2)
            t=(y+1)/2;envelope=math.sqrt(max(1e-8,1-y*y));u=x/envelope
            verts.append(point(t,u));colors.append(painted(t,u,True,index))
    for i in range(nv):
        for j in range(nu):a=i*(nu+1)+j;faces.append((a,a+nu+1,a+nu+2,a+1))
    o=add_mesh(f'Crown leaf {index+1:02d} / broad rounded rim',verts,faces,colors)
    lay_veins(f'Crown leaf {index+1:02d}',point)
    return o

def wrap_leaf(index,angle,radius,polar_top,spread):
    verts=[];colors=[];faces=[];nv=32;nu=26
    def point(t,u):
        polar=2.58-(2.58-polar_top)*t
        envelope=math.sqrt(max(0,1-(2*t-1)**2))
        theta=angle+u*envelope*spread+.075*math.sin(t*math.pi)
        rr=radius+.008*math.sin(t*math.pi)+.006*smooth(.8,1,abs(u))*math.sin(t*math.pi)
        rpol=polar+.015*math.sin(theta*3+index)*abs(u)**3
        return Vector((rr*math.sin(rpol)*math.cos(theta),rr*.94*math.sin(rpol)*math.sin(theta),.303+rr*.98*math.cos(rpol)))
    for i in range(nv+1):
        for j in range(nu+1):
            a=j/nu*2-1;b=i/nv*2-1;x=a*math.sqrt(1-b*b/2);y=b*math.sqrt(1-a*a/2)
            t=(y+1)/2;u=x/math.sqrt(max(1e-8,1-y*y))
            verts.append(point(t,u));colors.append(painted(t,u,False,index))
    for i in range(nv):
        for j in range(nu):a=i*(nu+1)+j;faces.append((a,a+1,a+nu+2,a+nu+1))
    o=add_mesh(f'Heart wrap {index+1:02d} / painted branching veins',verts,faces,colors)
    lay_veins(f'Heart wrap {index+1:02d}',point,True)
    return o

# A subtly asymmetrical heart, enclosed by leaves; no exposed plain sphere is the main read.
bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=(0,0,.303))
heart=bpy.context.object;heart.name='Tender inner heart';heart.scale=(.242,.226,.245)
for c in list(heart.users_collection):c.objects.unlink(heart)
plant.objects.link(heart);heart.data.materials.append(leafmat)
attr=heart.data.color_attributes.new(name='LeafColor',type='FLOAT_COLOR',domain='POINT')
for i,v in enumerate(heart.data.vertices):
    attr.data[i].color=(*mix(rgb('#93CA55'),rgb('#D1E78C'),(v.co.z+1)*.5),1)
for p in heart.data.polygons:p.use_smooth=True
parts.append(heart)

# Golden-angle staggering keeps overlaps off a mechanical radial pattern.
for i in range(5):wrap_leaf(i,i*2.399+.35,.249+i*.004,.18+.025*(i%3),1.02)
for i in range(7):
    a=i*2*math.pi/7+.16
    back=(math.sin(a)+1)/2
    crown_leaf(i,a,.31+.27*back,.34+.025*math.sin(i*1.7),.175+.018*math.sin(i*2.1))
# One broad, low front leaf folds across the bottom of the heart.
crown_leaf(8,-math.pi/2,.24,.37,.23)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=(0,0,.055))
stalk=bpy.context.object;stalk.name='Grounded fleshy stalk';stalk.scale=(.065,.06,.065);stalk.data.materials.append(rootmat)
for c in list(stalk.users_collection):c.objects.unlink(stalk)
plant.objects.link(stalk);parts.append(stalk)
for p in stalk.data.polygons:p.use_smooth=True

# Export candidate only. The source keeps all painted leaf objects and modifiers.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=heart
bpy.ops.export_scene.gltf(filepath=str(OUT/'cabbage-v2.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)

# Import v1 unchanged for a controlled comparison; exactly the same scale/camera/material lighting.
oldcol=bpy.data.collections.new('Cabbage_v1_reference');bpy.context.scene.collection.children.link(oldcol)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/models/crops/cabbage-mature.glb'))
old=[o for o in bpy.data.objects if o not in before]
root=bpy.data.objects.new('V1 reference / coordinate conversion',None);oldcol.objects.link(root);root.rotation_euler.x=math.pi/2
for o in old:
    if o.parent is None:o.parent=root
    for c in list(o.users_collection):c.objects.unlink(o)
    oldcol.objects.link(o)
# Blender's glTF importer already restores Z-up. Keep native import orientation.
root.rotation_euler.x=0
for o in parts:o.location.x+=.64
root.location.x=-.64

sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True
sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.55
sc.world=bpy.data.worlds.new('Warm daylight');sc.world.use_nodes=True
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.85,.89,.78,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
floor_mat=bpy.data.materials.new('Warm cream ground');floor_mat.diffuse_color=(*rgb('#F3F1E7'),1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));floor=bpy.context.object;floor.name='Review floor';floor.data.materials.append(floor_mat)
for name,loc,power,size in [('Key',(-2.5,-3.8,4.5),320,3.5),('Fill',(3,-1,3.2),100,3),('Rim',(0,3,4),180,3)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Same camera');camera=bpy.data.objects.new('Same camera',data);sc.collection.objects.link(camera)
camera.location=(.0,-4,2.1);camera.rotation_euler=(Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=2.65;sc.camera=camera
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=heart
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'cabbage-v2.blend'))
sc.render.filepath=str(REVIEW/'cabbage-v1-v2.png');bpy.ops.render.render(write_still=True)
# Also render a close 3/4 of the candidate with the old model hidden.
oldcol.hide_render=True
camera.location=(1.65,-2.6,1.65);camera.rotation_euler=(Vector((.64,0,.29))-camera.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=1.25
sc.render.resolution_x=1200;sc.render.resolution_y=1200
sc.render.filepath=str(REVIEW/'cabbage-v2-close.png');bpy.ops.render.render(write_still=True)
raw=(OUT/'cabbage-v2.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);tri=sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
record={'status':'art-quality-study-not-accepted','bytes':len(raw),'triangles':tri,'source':'assets-source/crop-studies/cabbage-v2.blend','glb':'public/models/crop-studies/cabbage-v2.glb','file':'/models/crop-studies/cabbage-v2.glb','stage':'mature','meshes':len(g['meshes']),'materials':len(g.get('materials',[])),'name':'试改 v2'}
(REVIEW/'cabbage-v2.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
manifest_path=OUT/'manifest.json'
studies=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
studies['cabbage']=record
manifest_path.write_text(json.dumps(studies,ensure_ascii=False,indent=2)+'\n')
print('STUDY_COMPLETE',tri,len(raw),flush=True)
