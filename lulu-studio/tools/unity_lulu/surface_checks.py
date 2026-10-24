import bpy,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];REP=R/'review/unity-integration-20261018/lulu/locomotion-r02';SRC=R/'assets-source/unity-lulu/locomotion-r02'
bpy.ops.wm.open_mainfile(filepath=str(SRC/'lulu-locomotion-master.blend'));trees={};srcbounds={}
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  p=[v.co.copy() for v in o.data.vertices];trees[o.name]=BVHTree.FromPolygons(p,[list(f.vertices) for f in o.data.polygons],all_triangles=False);srcbounds[o.name]=[np.array(p).min(0).tolist(),np.array(p).max(0).tolist()]
bpy.ops.wm.open_mainfile(filepath=str(SRC/'lulu-game-lod0.blend'));result={}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 dist=np.array([trees[o.name].find_nearest(v.co)[3] for v in o.data.vertices]);uv=o.data.uv_layers
 result[o.name]={'low_vertex_to_high_surface_distance_max':float(dist.max()),'distance_p95':float(np.percentile(dist,95)),'distance_mean':float(dist.mean()),'triangle_count':sum(len(f.vertices)-2 for f in o.data.polygons),'UV_finite':all(np.isfinite([list(x.uv) for x in u.data]).all() for u in uv),'material_slots':len(o.data.materials)}
(REP/'surface-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
