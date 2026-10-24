import bpy,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];REP=R/'review/unity-integration-20261018/lulu/locomotion-r04';result={}
for rev,label in [('locomotion-r02','locomotion-master'),('locomotion-r04','game-lod0'),('locomotion-r04','game-lod1')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu'/rev/f'lulu-{label}.blend'));row={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.normal_update();row[o.name]={'boundary_edges':sum(e.is_boundary for e in bm.edges),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)};bm.free()
 result[label]=row
(REP/'topology.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
