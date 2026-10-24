import bpy
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-integration/bvh-r01/S01.blend'))
for o in bpy.context.scene.objects:
 if o.get('production'):
  for m in o.data.materials:
   if m and m.use_nodes:
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    for l in list(b.inputs['Normal'].links):m.node_tree.links.remove(l)
from mathutils import Vector
import json
q=json.loads((R/'review/unity-integration-20261018/assets/S01/bvh-r01/review-settings.json').read_text());t=Vector(q['target']);sc=bpy.context.scene;sc.camera.location=t+Vector((1.35,-4,2.25)).normalized()*30;sc.camera.rotation_euler=(t-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=q['ortho_scale'];sc.render.filepath=str(R/'review/unity-integration-20261018/assets/S01/bvh-r01/no-normal-quarter.png');bpy.ops.render.render(write_still=True)
