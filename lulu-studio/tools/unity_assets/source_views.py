import bpy,sys,json,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];key,version=sys.argv[sys.argv.index('--')+1:];out=R/'review/unity-integration-20261018/assets'/key/version
s=json.loads((out/'review-settings.json').read_text());spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-integration'/version/(key+'.blend')))
orig=[o for o in bpy.context.scene.objects if o.get('input_object')]
for o in bpy.context.scene.objects:
 if o.get('production'):o.hide_render=True
for o in orig:o.hide_render=False
sc=bpy.context.scene
for mode in ['material','clay']:
 if mode=='clay':
  gray=H.material('Source neutral gray',(.38,.38,.38),.85)
  for o in orig:o.data.materials.clear();o.data.materials.append(gray)
 for v,d in s['views'].items():
  p=out/f'original-{mode}-{v}.png'
  if p.exists():continue
  t=Vector(s['target']);sc.camera.location=t+Vector(d).normalized()*30;sc.camera.rotation_euler=(t-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=s['ortho_scale'];sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
print('SOURCE_VIEWS_COMPLETE',key,version,flush=True)
