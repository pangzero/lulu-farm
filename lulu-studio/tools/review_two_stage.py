"""Actual GLB readback, controlled original renders and fixed planting evidence."""
import bpy,bmesh,json,sys,math,importlib.util,argparse
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'review/crop-two-stage-20261018'
spec=importlib.util.spec_from_file_location('qa_helpers',ROOT/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
p=argparse.ArgumentParser();p.add_argument('--crop',required=True);p.add_argument('--mode',choices=['original','planting','farm-only','detail-pair'],required=True);p.add_argument('--optimized',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);slug=a.crop
MATURE_REV='game-r02' if a.optimized else ('r03' if slug=='tomato' else 'r02')
entry=next(c for c in json.loads((ROOT/'public/models/crops-meshy/manifest.json').read_text())['crops'] if c['id']==slug)

def import_model(path,scale=1):
 before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(path));allobjs=[o for o in bpy.context.scene.objects if o not in before];roots=[o for o in allobjs if o.parent is None]
 for o in roots:o.scale*=scale
 meshes=[o for o in allobjs if o.type=='MESH'];lo,hi=H.bounds(meshes);offset=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
 for o in roots:o.location+=offset
 return roots,meshes

def cam(target,height,view='quarter',farm=False):
 s=bpy.context.scene;direction=Vector((math.cos(math.radians(50))/math.sqrt(2),-math.cos(math.radians(50))/math.sqrt(2),math.sin(math.radians(50)))) if farm else Vector(H.VIEWS[view]).normalized()
 s.camera.data.ortho_scale=height*(1280/720 if farm else 1);s.camera.location=Vector(target)+direction*30;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler()

def soil(nx,ny):
 mat=H.material('Separate QA soil cells',(.33,.20,.10),1)
 for y in range(ny):
  for x in range(nx):
   bpy.ops.mesh.primitive_cube_add(size=1,location=((x-(nx-1)/2)*1.2,(y-(ny-1)/2)*1.2,-.035));o=bpy.context.object;o.name='QA soil - not production';o.dimensions=(1.14,1.14,.07);o.data.materials.append(mat);o['qa_soil']=True
 # Put the existing inspection plane below the soil tops.
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and o.name.startswith('Plane'):o.location.z=-.071

if a.mode=='detail-pair':
 for stage,rev,batch in [('seedling','r03','B08'),('mature',MATURE_REV,entry['batch'])]:
  out=REVIEW/slug/stage/rev;bpy.ops.wm.read_factory_settings(use_empty=True);version=('native-' if stage=='seedling' else 'toon-')+rev
  roots,objects=import_model(ROOT/f'public/models/farm-assets/{batch}/{version}/{slug}-{stage}.glb');H.inspection_setup()
  lo,hi=H.bounds(objects);target=(lo+hi)/2
  if stage=='seedling':target=Vector((0,0,.10));height=.23
  else:height=max(hi-lo)*.65
  cam(target,height);bpy.context.scene.render.filepath=str(out/'structure-detail.png');bpy.ops.render.render(write_still=True)
 bpy.ops.wm.read_factory_settings(use_empty=True)
 r1,o1=import_model(ROOT/f'public/models/farm-assets/B08/native-r03/{slug}-seedling.glb');r2,o2=import_model(ROOT/f'public/models/farm-assets/{entry["batch"]}/toon-{MATURE_REV}/{slug}-mature.glb')
 for o in r1:o.location.x-=.7
 for o in r2:o.location.x+=.7
 H.inspection_setup();cam((0,0,.45),2.5)
 for material in ['material','clay']:
  if material=='clay':
   gray=H.material('Neutral pair clay',(.38,.38,.38),.85)
   for o in o1+o2:o.data.materials.clear();o.data.materials.append(gray)
  bpy.context.scene.render.filepath=str(REVIEW/slug/f'pair-{material}-quarter.png');bpy.ops.render.render(write_still=True)
elif a.mode=='original':
 out=REVIEW/slug/'mature/original';out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True)
 roots,objects=import_model(ROOT/'public'/entry['file'].lstrip('/'),.47);H.inspection_setup()
 settings=json.loads((REVIEW/slug/'mature/r02/source-reopen.json').read_text());target=settings['camera_target'];height=settings['ortho_scale']
 for mode in ['material','clay']:
  if mode=='clay':
   gray=H.material('Neutral clay',(.38,.38,.38),.85)
   for o in objects:o.data.materials.clear();o.data.materials.append(gray)
  for view in H.VIEWS:
   cam(target,height,view);bpy.context.scene.render.filepath=str(out/f'{mode}-{view}.png');bpy.ops.render.render(write_still=True)
 (out/'review-settings.json').write_text(json.dumps({'original_file':entry['file'],'original_sha256':H.sha(ROOT/'public'/entry['file'].lstrip('/')),'scale':.47,'camera_target':target,'ortho_scale':height,'lights':'unchanged B01','exposure':0,'resolution':[768,768]},indent=2))
else:
 for stage,rev,batch in [('seedling','r03','B08'),('mature',MATURE_REV,entry['batch'])]:
  if stage=='seedling' and a.optimized:continue
  out=REVIEW/slug/stage/rev;bpy.ops.wm.read_factory_settings(use_empty=True)
  version=rev if rev.startswith('game-') else ('native-' if stage=='seedling' else 'toon-')+rev
  roots,objects=import_model(ROOT/f'public/models/farm-assets/{batch}/{version}/{slug}-{stage}.glb')
  audit=[]
  for o in objects:
   bm=bmesh.new();bm.from_mesh(o.data);before=sum(e.is_boundary for e in bm.edges);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
   audit.append({'mesh':o.name,'raw_split_boundary_edges':before,'welded_boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'vertices':len(o.data.vertices),'finite_normals':all(all(math.isfinite(c) for c in v.normal) for v in o.data.vertices)})
   bm.free()
  (out/'roundtrip-topology.json').write_text(json.dumps(audit,indent=2))
  # Bake transforms on render-only mesh copies; linked duplicates share mesh data.
  bpy.context.view_layer.update()
  copies=[]
  for o in objects:
   world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
   for y in [-1,0,1]:
    for x in [-1,0,1]:
     if x==0 and y==0:continue
     dup=o.copy();dup.data=o.data;bpy.context.collection.objects.link(dup);dup.location+=Vector((x*1.2,y*1.2,0));copies.append(dup)
  H.inspection_setup();soil(3,3)
  lulu_roots,lulu_mesh=import_model(ROOT/'public/models/lulu-meshy-notail.glb',.6313689262131015)
  for o in lulu_roots:o.location.x+=2.5
  if a.mode!='farm-only':
   cam((.45,0,.5),6.2);bpy.context.scene.render.filepath=str(out/'planting-3x3-lulu.png');bpy.ops.render.render(write_still=True)
  for o in list(bpy.context.scene.objects):
   if o.get('qa_soil'):bpy.data.objects.remove(o,do_unlink=True)
  for o in objects+copies:o.location+=Vector((.6,.6,0))
  soil(12,8);s=bpy.context.scene;s.render.resolution_x=1280;s.render.resolution_y=720
  cam((0,0,0),14.1,farm=True);s.render.filepath=str(out/'farm-distance.png');bpy.ops.render.render(write_still=True)
  (out/'planting-settings.json').write_text(json.dumps({'rendered_from':'Exported GLB readback','grid_cell':1.2,'plants':9,'lulu_scale':.6313689262131015,'lulu_unchanged':True,'near_resolution':[768,768],'near_ortho':6.2,'farm_resolution':[1280,720],'farm_orthographic_height':14.1,'farm_orthographic_width':14.1*1280/720,'farm_azimuth':45,'farm_elevation':50,'field_cells':[12,8],'plant_scale':1},indent=2))
print('COMPLETE',slug,a.mode,flush=True)
