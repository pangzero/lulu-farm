import bpy,json,math,sys,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];O=R/'review/unity-integration-20261018/assets';P=R/'public/models/unity-integration';spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H);registry=json.loads((P/'manifest.json').read_text());stage=sys.argv[sys.argv.index('--')+1];keys=sys.argv[sys.argv.index('--')+2:];lod1='--lod1' in keys;keys=[k for k in keys if k!='--lod1'];lp=R/'public/models/wardrobe-rig/full-r02/lulu-rig.glb';lsha=hashlib.sha256(lp.read_bytes()).hexdigest()
def import_flat(path):
 before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(path));allobs=[o for o in bpy.context.scene.objects if o not in before];meshes=[o for o in allobs if o.type=='MESH'];bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 for ob in meshes:
  mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(dg));world=ob.matrix_world.copy();ob.modifiers.clear();ob.data=mesh;ob.parent=None;ob.matrix_world=world
 for ob in allobs:
  if ob.type!='MESH':bpy.data.objects.remove(ob,do_unlink=True)
 return meshes
for row in registry['assets']:
 if row['stage']!=stage or (keys and row['id'] not in keys):continue
 key=row['id'];v=row['selected_version'];glb=Path(row['file'])
 if lod1:
  lod=next(x for x in row['lods'] if x['level']==1);glb=Path(lod['model']);v=glb.parent.name
 out=O/key/v;assert glb.exists();assert v.startswith(('bvh','semantic','atlas','surface','lod1')),(key,v)
 if (out/'planting-settings.json').exists():continue
 bpy.ops.wm.read_factory_settings(use_empty=True);plants=import_flat(glb);bpy.context.view_layer.update();lo,hi=H.bounds(plants);offset=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
 for ob in plants:ob.location+=offset
 copies=[]
 for ob in plants:
  for y in [-1,0,1]:
   for x in [-1,0,1]:
    if x==0 and y==0:continue
    cp=ob.copy();cp.data=ob.data;bpy.context.collection.objects.link(cp);cp.location+=Vector((x*1.2,y*1.2,0));copies.append(cp)
 lulu=import_flat(lp);bpy.context.view_layer.update();llo,lhi=H.bounds(lulu);lscale=1.2/(lhi.z-llo.z);lshift=Vector((-(llo.x+lhi.x)/2,-(llo.y+lhi.y)/2,-llo.z))
 for ob in lulu:
  ob.matrix_world.translation=(ob.matrix_world.translation+lshift)*lscale+Vector((2.5,0,0));ob.scale*=lscale
 H.inspection_setup();sc=bpy.context.scene;sc.cycles.samples=8;sc.render.threads=3;soilmat=H.material('Separate 1.2 cell QA soil',(.33,.20,.10),1)
 def soil(nx,ny):
  for ob in list(sc.objects):
   if ob.get('qa_soil'):bpy.data.objects.remove(ob,do_unlink=True)
  for y in range(ny):
   for x in range(nx):
    bpy.ops.mesh.primitive_cube_add(size=1,location=((x-(nx-1)/2)*1.2,(y-(ny-1)/2)*1.2,-.035));ob=bpy.context.object;ob.name='QA soil, never included in plant GLB';ob.dimensions=(1.14,1.14,.07);ob.data.materials.append(soilmat);ob['qa_soil']=True
  for ob in sc.objects:
   if ob.name.startswith('QA ground'):ob.location.z=-.071
 def picture(name,target,ortho,farm=False):
  target=Vector(target);di=Vector((math.cos(math.radians(50))/2**.5,-math.cos(math.radians(50))/2**.5,math.sin(math.radians(50)))) if farm else Vector(H.VIEWS['quarter']).normalized();sc.camera.location=target+di*30;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=ortho*(1280/720 if farm else 1);sc.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
 soil(3,3);picture('planting-3x3-lulu.png',(.45,0,.5),6.2);soil(12,8)
 for ob in plants+copies:ob.location+=Vector((.6,.6,0))
 sc.render.resolution_x=1280;sc.render.resolution_y=720;picture('farm-distance.png',(0,0,0),14.1,True)
 (out/'planting-settings.json').write_text(json.dumps({'model':str(glb),'lod_level':1 if lod1 else 0,'same_condition_lod0':str(O/key/row['selected_version']/'planting-settings.json'),'sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'plant_scale':1,'cell':[1.2,1.2],'plant_count':9,'near_resolution':[768,768],'near_ortho_height':6.2,'farm_resolution':[1280,720],'farm_ortho_height':14.1,'farm_ortho_width':14.1*1280/720,'farm_azimuth':45,'farm_elevation':50,'farm_cells':[12,8],'lulu_source':str(lp),'lulu_sha256':lsha,'lulu_read_only':True,'lulu_height':1.2,'lulu_scale':lscale,'soil_qa_only':True,'actual_visual_inspection':'pending','unity_actual':'pending'},indent=2));assert hashlib.sha256(lp.read_bytes()).hexdigest()==lsha;print('PLANTING_RENDERED',key,v,flush=True)
