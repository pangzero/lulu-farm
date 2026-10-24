# Shared Blender helpers retained for historical Lulu scripts. No farm builders.
# -*- coding: utf-8 -*-
import bpy, math, random, json, os
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/models'; SRC=ROOT/'assets-source'; REVIEW=ROOT/'review'
for p in [OUT,SRC,REVIEW]:p.mkdir(exist_ok=True,parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(43)
MATS={}
def rgb(h):
 h=h.lstrip('#');v=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in v)+(1,)
def material(name,c,rough=.65,metal=0,emit=0):
 m=bpy.data.materials.new(name);m.diffuse_color=rgb(c);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=rgb(c);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 if emit:bs.inputs['Emission Color'].default_value=rgb(c);bs.inputs['Emission Strength'].default_value=emit
 MATS[name]=m;return m
bodymat=material('Lulu_SoftMango','#F5CE63',.74);pantsmat=material('Lulu_TerracottaShorts','#F18038',.82)
orange=material('OrangeFruit','#F59A1E',.6);iris=material('Iris_Blue','#5C8DC9',.28);pupil=material('Pupil','#10141C',.22);white=material('Eye_White','#FFFEEC',.33);mouth=material('Smile','#633F25',.8)
leafmat=material('Leaf','#779C48',.72);wood=material('Wood_Honey','#A8783F',.8);woodlight=material('Wood_Light','#C59A5C',.8);plaster=material('Cream_Plaster','#EEDCC0',.9);roofmat=material('Terracotta_Tiles','#BF6349',.87);rooflight=material('Tile_Light','#D97D5A',.86);stone=material('Foundation_Stone','#ACA28B',.85);teal=material('Awning_Green','#648D75',.87);ivory=material('Awning_Cream','#EFE9CA',.86);glass=material('Window_Amber','#FFD383',.25,emit=.5);soil=material('Soil','#69513A',.95);green=[material('Leaf_'+str(i),c,.8) for i,c in enumerate(['#6E923D','#85AC49','#A1C45A','#B3D46C'])];red=material('Tomato','#D84B30',.37);pot=material('Pot','#B7774F',.86);metal=material('Metal_Dark','#43584D',.45,.35);watermat=material('Watering_Blue','#6D9ABD',.5)

def assign(o,m):o.data.materials.append(m);return o
def smooth(o):
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
 return o
def box(name,loc,scale,m,bevel=.04):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m)
 if bevel:
  mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=bevel;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)
  smooth(o);mod=o.modifiers.new('Weighted corners','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def sphere(name,loc,scale,m,segments=24,rings=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m);smooth(o);return o
def mesh(name,verts,faces,m):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);assign(o,m);return o
def curve(name,pts,r,m):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=16;cu.bevel_depth=r;cu.bevel_resolution=3;sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);assign(o,m);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return o
def cylinder(name,loc,r,h,m,verts=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=h,location=loc);o=bpy.context.object;o.name=name;assign(o,m);smooth(o);return o
def leaf(name,origin,length,width,angle,tilt,m):
 # Curved blade with folded central rib; solid thickness is visible from sides.
 vs=[];fs=[]
 for i in range(9):
  t=i/8;spread=width*math.sin(math.pi*t)**.7;center=length*t;z=.10*math.sin(t*math.pi)+tilt*t*t
  for k in range(3):
   x=(k-1)*spread;y=center;zz=z+(0.055 if k==1 else 0)+.028*math.sin(t*5*math.pi)*(abs(k-1))
   vs.append((origin[0]+x*math.cos(angle)-y*math.sin(angle),origin[1]+x*math.sin(angle)+y*math.cos(angle),origin[2]+zz))
 for i in range(8):
  for k in range(2):a=i*3+k;fs.append((a,a+1,a+4,a+3))
 o=mesh(name,vs,fs,m);smooth(o);mod=o.modifiers.new('Leaf thickness','SOLIDIFY');mod.thickness=.014;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);return o

def export(name,objects,animations=False):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_animations=animations,export_animation_mode='ACTIONS',export_yup=True)
 print('EXPORTED',name,len(objects))
def combine(objects):
 # Join static geometry by material, retain names for loading model instances.
 groups={}
 for o in objects:
  if o.type=='MESH':groups.setdefault(o.data.materials[0].name,[]).append(o)
 result=[]
 for name,items in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in items:o.select_set(True)
  bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();items[0].name=name;result.append(items[0])
 return result

