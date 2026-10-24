import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];out=R/'review/unity-integration-20261018/assets/E05-corner/interface-r01';out.mkdir(parents=True,exist_ok=True);dest=R/'public/models/unity-integration/interface-r01/E05-corner.glb';blend=R/'assets-source/unity-integration/interface-r01/E05-corner.blend';source=R/'public/models/farm-assets/B03/e05-r03.glb';radius=1.2/(math.pi/2)
spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
for ob in obs:
 world=ob.matrix_world.copy();ob.parent=None
 for v in ob.data.vertices:v.co=world@v.co
 ob.matrix_world.identity();ob['production']=True
 if 'stone' in ob.name.lower():
  # Stones move rigidly; no rubber bending across the circular frame.
  center=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices);angle=(center.x+.6)/radius;new=Vector(((radius+center.y)*math.sin(angle),(radius+center.y)*math.cos(angle),center.z))
  for v in ob.data.vertices:
   d=v.co-center;v.co=new+Vector((d.x*math.cos(angle)+d.y*math.sin(angle),-d.x*math.sin(angle)+d.y*math.cos(angle),d.z))
 else:
  for v in ob.data.vertices:
   x,y,z=v.co;angle=(x+.6)/radius;v.co=((radius+y)*math.sin(angle),(radius+y)*math.cos(angle),z)
 ob.name='E05 curved '+ob.name;ob.data.update()
bpy.ops.object.select_all(action='DESELECT')
for ob in obs:ob.select_set(True)
bpy.context.view_layer.objects.active=obs[0];bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_apply=True);H.inspection_setup();sc=bpy.context.scene;sc.cycles.samples=8;sc.render.threads_mode='FIXED';sc.render.threads=4
for ob in sc.objects:
 if ob.name.startswith('QA ground'):ob.location.z=-.30
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True);bpy.ops.wm.open_mainfile(filepath=str(blend));obs=[o for o in bpy.context.scene.objects if o.get('production')];sc=bpy.context.scene;target=Vector((.65,.65,-.10));scale=2.10
for mode in ['material','clay']:
 if mode=='clay':
  mat=H.material('Neutral gray',(.38,.38,.38),.85)
  for ob in obs:ob.data.materials.clear();ob.data.materials.append(mat)
 for view in H.VIEWS:
  d=Vector(H.VIEWS[view]).normalized();sc.camera.location=target+d*30;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale;sc.render.filepath=str(out/(mode+'-'+view+'.png'));bpy.ops.render.render(write_still=True)
metrics=H.check_glb(dest);metrics.update({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'file':str(dest),'editable_source':str(blend),'source_reopened':True,'export_reimported':True,'radius_centerline':radius,'angle_degrees':90,'arc_length':1.2,'land_height':0,'water_height':-.105,'start_connector_gltf':[0,0,-radius],'end_connector_gltf':[radius,0,0],'start_tangent_gltf':[1,0,0],'end_tangent_gltf':[0,0,1],'land_side':'outside circle','water_side':'inside circle','cross_section_y_source':[-.38,.60],'underwater_floor':-.28,'notes':'Geometry starts/ends at exact E05 section profiles. Five source stones moved rigidly around arc. Do not normalize/ground to bounding minimum: land datum stays0.'});(out/'metrics.json').write_text(json.dumps(metrics,indent=2));print('CORNER_COMPLETE',radius,flush=True)
