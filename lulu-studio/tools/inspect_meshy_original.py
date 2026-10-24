"""Import and inspect supplied GLB without modifying its geometry or material."""
import bpy,bmesh,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
p=R/'assets-source/meshy-original/Meshy_AI_Sunny_Sprout_1014132159_texture.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
report={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'meshes':[],'images':[]}
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
 raw_vertices=len(bm.verts);raw_boundary=sum(e.is_boundary for e in bm.edges)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
 bm.verts.ensure_lookup_table();bm.verts.index_update()
 visited=set();islands=[]
 for v in bm.verts:
  if v.index in visited:continue
  pending=[v];ids=[];visited.add(v.index)
  while pending:
   cur=pending.pop();ids.append(cur.index)
   for e in cur.link_edges:
    q=e.other_vert(cur)
    if q.index not in visited:visited.add(q.index);pending.append(q)
  vs=[bm.verts[i].co for i in ids];lo=[min(v[a] for v in vs) for a in range(3)];hi=[max(v[a] for v in vs) for a in range(3)]
  islands.append({'vertices':len(ids),'bounds_min':lo,'bounds_max':hi})
 report['meshes'].append({'name':ob.name,'vertices':len(ob.data.vertices),'analysis_only_welded_vertices':len(bm.verts),'raw_uv_split_boundary_edges':raw_boundary,'faces':len(ob.data.polygons),'connected_islands':sorted(islands,key=lambda d:-d['vertices']),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'modifiers':[m.type for m in ob.modifiers]});bm.free()
for im in bpy.data.images:
 report['images'].append({'name':im.name,'size':list(im.size),'packed':bool(im.packed_file)})
report['armatures']=sum(o.type=='ARMATURE' for o in bpy.context.scene.objects)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets-source/lulu-meshy-original.blend'))
(R/'review/meshy-original-inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2)[:2000])
