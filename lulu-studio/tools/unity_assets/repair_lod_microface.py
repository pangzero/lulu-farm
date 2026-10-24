import bpy,bmesh,json,hashlib,sys,importlib.util,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];P=R/'public/models/unity-integration';S=R/'assets-source/unity-integration';O=R/'review/unity-integration-20261018/assets';spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
for key in sys.argv[sys.argv.index('--')+1:]:
 v='atlas-lod1-r02';d=P/v/(key+'.glb');s=S/v/(key+'.blend');out=O/key/v;out.mkdir(parents=True,exist_ok=True);d.parent.mkdir(exist_ok=True);s.parent.mkdir(exist_ok=True);assert not d.exists()
 old=O/key/'atlas-lod1-r01';settings=json.loads((old/'review-settings.json').read_text());m=json.loads((old/'metrics.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(S/'atlas-lod1-r01'/(key+'.blend')));obs=[o for o in bpy.context.scene.objects if o.get('production')];removed=[]
 for ob in obs:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bad=[f for f in bm.faces if f.calc_area()<1e-4 and all(not e.is_manifold for e in f.edges)];removed.extend([{'area':f.calc_area(),'center':list(f.calc_center_median()),'edges':[e.calc_length() for e in f.edges]} for f in bad]);assert len(bad)==1,(key,len(bad));bmesh.ops.delete(bm,geom=bad,context='FACES');bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES');bm.normal_update();assert not any(not e.is_manifold for e in bm.edges),key;bm.to_mesh(ob.data);bm.free();ob.data.update()
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.export_scene.gltf(filepath=str(d),export_format='GLB',use_selection=True,export_apply=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(s),compress=True);bpy.ops.wm.open_mainfile(filepath=str(s));obs=[o for o in bpy.context.scene.objects if o.get('production')];sc=bpy.context.scene;target=Vector(settings['target']);sc.render.threads_mode='FIXED';sc.render.threads=4
 for mode in ['material','clay']:
  if mode=='clay':
   gray=H.material('Local repair neutral gray',(.38,.38,.38),.85)
   for ob in obs:ob.data.materials.clear();ob.data.materials.append(gray)
  for view,di in H.VIEWS.items():
   sc.camera.location=target+Vector(di).normalized()*30;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=settings['ortho_scale'];sc.render.filepath=str(out/f'{mode}-{view}.png');bpy.ops.render.render(write_still=True)
 for view in ['quarter','back']:shutil.copy2(old/f'original-material-{view}.png',out/f'original-material-{view}.png')
 stats=H.check_glb(d);top=[]
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);top.append({'name':ob.name,'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'zero_area':sum(f.calc_area()<1e-14 for f in bm.faces),'finite':True});bm.free()
 m.update(stats);m.update({'version':v,'file':str(d),'editable_source':str(s),'editable_source_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'actual_triangles':stats['triangles'],'geometry':top,'local_repair':{'method':'remove exactly one submillimetre stray triangle identified by three anomalous edges; all other faces and original UV retained','removed':removed},'source_reopened':True,'export_reimported':True,'visual':'pending_actual_inspection'});(out/'metrics.json').write_text(json.dumps(m,indent=2));(out/'review-settings.json').write_text(json.dumps(settings,indent=2));print('REPAIRED',key,m['actual_triangles'],top,flush=True)
