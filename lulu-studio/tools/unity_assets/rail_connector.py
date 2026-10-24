import bpy,json,hashlib,bmesh,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];src=R/'assets-source/farm-assets/B02/s05-fence-r04.blend';out=R/'review/unity-integration-20261018/assets/S05-rail-connector/interface-r01';dest=R/'public/models/unity-integration/interface-r01/S05-rail-connector.glb';blend=R/'assets-source/unity-integration/interface-r01/S05-rail-connector.blend';out.mkdir(parents=True,exist_ok=True);spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H);oldhash=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src));rails=[o for o in bpy.context.scene.objects if o.name in ['S05 continuous rounded rail 1','S05 continuous rounded rail 2']];assert len(rails)==2
for o in list(bpy.context.scene.objects):
 if o not in rails:bpy.data.objects.remove(o,do_unlink=True)
for o in rails:
 o.hide_set(False);o.hide_render=False;o.parent=None
 for v in o.data.vertices:v.co.x=(v.co.x-.11)/.98*1.2-.6
 o.data.update()
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=rails[0];bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_apply=True);H.inspection_setup();sc=bpy.context.scene;sc.cycles.samples=8;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.camera.data.ortho_scale=1.65;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True);bpy.ops.wm.open_mainfile(filepath=str(blend));sc=bpy.context.scene;rails=[o for o in sc.objects if o.name.startswith('S05 continuous')]
for mode in ['material','clay']:
 if mode=='clay':
  mat=H.material('Connector neutral gray',(.38,.38,.38),.85)
  for o in rails:o.data.materials.clear();o.data.materials.append(mat)
 for view,di in H.VIEWS.items():
  target=Vector((0,0,.495));sc.camera.location=target+Vector(di).normalized()*30;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/f'{mode}-{view}.png');bpy.ops.render.render(write_still=True)
m=H.check_glb(dest);tops=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);tops.append({'name':o.name,'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges)});bm.free()
m.update({'file':str(dest),'editable_source':str(blend),'source':str(src),'source_sha256':oldhash,'original_unchanged':hashlib.sha256(src.read_bytes()).hexdigest()==oldhash,'source_reopened':True,'export_reimported':True,'welded_topology':tops,'interface':{'axis':'glTF X','endpoints_x':[-.6,.6],'span':1.2,'rail_centers_y':[.32,.67],'width_z':.11,'rail_height_y':.15,'application':'Scale X only to clear distance between post surfaces; keep fixed YZ profile. No posts included.'}});(out/'metrics.json').write_text(json.dumps(m,indent=2));(out/'review-settings.json').write_text(json.dumps({'target':[0,0,.495],'ortho_scale':1.65,'views':H.VIEWS,'resolution':[768,768],'same_B02_materials':True},indent=2));print('RAIL_CONNECTOR',json.dumps(m),flush=True)
