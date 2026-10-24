import bpy,json,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];out=R/'review/unity-integration-20261018/assets/S01/bvh-r03';bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-integration/bvh-r03/S01.blend'));s=json.loads((out/'review-settings.json').read_text());sc=bpy.context.scene;sc.render.threads=2
for ob in sc.objects:
 if ob.get('production'):ob.hide_render=True
 if ob.get('input_object'):ob.hide_render=False
v=Vector((0,-.001,1)).normalized();target=Vector(s['target']);sc.camera.location=target+v*30;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=s['ortho_scale'];sc.render.filepath=str(out/'original-material-top.png');bpy.ops.render.render(write_still=True)
spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H);gray=H.material('Original source gray',(.38,.38,.38),.85)
for ob in sc.objects:
 if ob.get('input_object'):ob.data.materials.clear();ob.data.materials.append(gray)
sc.render.filepath=str(out/'original-clay-top.png');bpy.ops.render.render(write_still=True)
