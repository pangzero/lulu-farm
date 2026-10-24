import bpy,json,sys,importlib.util
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];o=R/'review/unity-integration-20261018/assets/rose-mature/atlas-semantic-r04';d=json.loads((R/'public/models/unity-integration/manifest.json').read_text());a=next(x for x in d['assets'] if x['id']=='rose-mature');bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a['source']);obs=[x for x in bpy.context.scene.objects if x.type=='MESH'];pts=[x.matrix_world@v.co for x in obs for v in x.data.vertices];lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));off=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))*.47
print('SOURCE_TRANSFORM',{'scale':.47,'subtract_offset_blender_zup':list(off),'source_bounds':[list(lo),list(hi)]},flush=True)
records=[];bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-integration/atlas-semantic-r04/rose-mature.blend'));high=[x for x in bpy.context.scene.objects if x.get('input_object')][0];high.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in high.data.vertices],[t.vertices for t in high.data.loop_triangles],all_triangles=True);s=json.loads((o/'review-settings.json').read_text());target=Vector(s['target']);scale=s['ortho_scale']
for view,pixels in [('top',[(481,357),(475,352),(489,361)])]:
 di=Vector(s['views'][view]).normalized();quat=(-di).to_track_quat('-Z','Y');right=quat@Vector((1,0,0));up=quat@Vector((0,1,0))
 for x,y in pixels:
  origin=target+di*30+right*((x/768-.5)*scale)+up*((.5-y/768)*scale);hit=tree.ray_cast(origin,-di);records.append({'view':view,'pixel':[x,y],'point':list(hit[0]) if hit[0] is not None else None,'normal':list(hit[1]) if hit[1] is not None else None})
print('PATCH_PROBE',records,flush=True);(o/'local-patch-probe.json').write_text(json.dumps({'source_scale':.47,'source_subtract_offset_blender_zup':list(off),'points':records},indent=2))
