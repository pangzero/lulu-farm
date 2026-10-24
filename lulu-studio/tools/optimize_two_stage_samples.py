"""Separate first-three mature resource candidates, never changes Meshy/toon inputs."""
import bpy,bmesh,json,sys,importlib.util
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT/'review/crop-two-stage-20261018'
spec=importlib.util.spec_from_file_location('qa',ROOT/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
slug=sys.argv[sys.argv.index('--')+1];rev='r03' if slug=='tomato' else 'r02';game_version=sys.argv[sys.argv.index('--')+2] if len(sys.argv)>sys.argv.index('--')+2 else 'game-r01'
ratios={'cabbage':.16,'tomato':.22,'corn':.20};ratio=ratios[slug]
src=ROOT/f'assets-source/farm-assets/B01/toon-{rev}/{slug}-mature.blend';dest=ROOT/f'assets-source/farm-assets/B01/{game_version}/{slug}-mature.blend';glb=ROOT/f'public/models/farm-assets/B01/{game_version}/{slug}-mature.glb';out=REVIEW/slug/'mature'/game_version
for p in [dest.parent,glb.parent,out]:p.mkdir(parents=True,exist_ok=True)
assert not dest.exists() and not glb.exists()
bpy.ops.wm.open_mainfile(filepath=str(src));objects=[o for o in bpy.context.scene.objects if o.get('production')]
for o in objects:
 if game_version=='game-r02':
  weld=o.modifiers.new('Join coincident geometry before simplification - preserve UV loops','WELD');weld.merge_threshold=1e-7
 m=o.modifiers.new('Resource candidate - preserve major silhouette','DECIMATE');m.ratio=ratio;m.use_collapse_triangulate=True
for img in bpy.data.images:
 if img.size[0]>2048 or img.size[1]>2048:img.scale(2048,2048);img.pack()
for o in bpy.context.scene.objects:o.select_set(False)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
m=H.check_glb(glb);m.update({'crop':slug,'stage':'mature','batch':'B01','version':game_version,'source':str(dest.relative_to(ROOT)),'source_sha256':H.sha(dest),'glb':str(glb.relative_to(ROOT)),'source_kind':'meshy_cartoon_resource_derivative','parent_source':str(src.relative_to(ROOT)),'parent_sha256':H.sha(src),'optimization_ratio':ratio,'texture_max':2048,'geometry_changed':True,'user_art_status':'pending','target_device':'not_tested'})
audit=[]
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);audit.append({'name':o.name,'boundary_edges_after_weld':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)});bm.free()
m['topology']=audit;(out/'metrics.json').write_text(json.dumps(m,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(dest));objects=[o for o in bpy.context.scene.objects if o.get('production')]
settings=json.loads((REVIEW/slug/'mature'/rev/'source-reopen.json').read_text());target=Vector(settings['camera_target']);height=settings['ortho_scale']
for mode in ['material','clay']:
 if mode=='clay':
  gray=H.material('Neutral clay',(.38,.38,.38),.85)
  for o in objects:o.data.materials.clear();o.data.materials.append(gray)
 for view,direction in H.VIEWS.items():
  s=bpy.context.scene;s.camera.data.ortho_scale=height;s.camera.location=target+Vector(direction).normalized()*7;s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/f'{mode}-{view}.png');bpy.ops.render.render(write_still=True)
(out/'source-reopen.json').write_text(json.dumps({'source_reopened':True,'source_preserved':H.sha(dest),'camera_target':list(target),'ortho_scale':height,'same_as_parent':True},indent=2))
print('COMPLETE',slug,game_version,flush=True)
