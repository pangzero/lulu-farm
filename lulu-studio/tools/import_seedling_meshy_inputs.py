import bpy,json,sys,importlib.util,shutil,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018';O.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
files={'broad':'Meshy_AI_Bok_Choy_Plant_1018082619_image-to-3d-texture.glb','sprout':'Meshy_AI_Sprout_Plant_1018082612_image-to-3d-texture.glb','triple':'Meshy_AI_Three_Leaf_Sprout_1018082607_image-to-3d-texture.glb','blade':'Meshy_AI_Tall_Leaf_Plant_1018082600_image-to-3d-texture.glb'}
manifest=[]
for family,name in files.items():
 orig=Path('/Users/haowen/Downloads')/name;dest=R/'public/models/seedling-meshy/originals'/name;dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert H.sha(dest)==H.sha(orig)
 else:shutil.copy2(orig,dest)
 m=H.check_glb(dest);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(dest));objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];lo,hi=H.bounds(objects);rawheight=hi.z-lo.z
 roots=[o for o in bpy.context.scene.objects if o.parent is None]
 for o in roots:o.scale*=.28/rawheight
 bpy.context.view_layer.update();lo,hi=H.bounds(objects);shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
 for o in roots:o.location+=shift
 bpy.context.view_layer.update();H.inspection_setup()
 source=R/f'assets-source/seedling-meshy/{family}/meshy-r01/{family}-import.blend';source.parent.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0;
 if not source.exists():bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
 folder=O/'inputs'/family;folder.mkdir(parents=True,exist_ok=True)
 for mode in ['material','clay']:
  if mode=='clay':
   gray=H.material('Neutral inspection',(.38,.38,.38),.85)
   for o in objects:o.data.materials.clear();o.data.materials.append(gray)
  for v in (['quarter','back','top'] if mode=='material' else ['side']):
   target=Vector((0,0,.14));bpy.context.scene.camera.location=target+Vector(H.VIEWS[v]).normalized()*6;bpy.context.scene.camera.rotation_euler=(target-bpy.context.scene.camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.camera.data.ortho_scale=max(H.bounds(objects)[1]-H.bounds(objects)[0])*1.4;bpy.context.scene.render.filepath=str(folder/f'{mode}-{v}.png');bpy.ops.render.render(write_still=True)
 m.update({'family':family,'original_filename':name,'original_download':str(orig),'file':'/'+str(dest.relative_to(R/'public')),'sha256':H.sha(dest),'source':str(source.relative_to(R)),'source_sha256':H.sha(source),'raw_height':rawheight,'inspection_height':.28});manifest.append(m);(O/'inputs-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('INPUT_COMPLETE',family,flush=True)
print('ALL_INPUTS_COMPLETE',flush=True)
