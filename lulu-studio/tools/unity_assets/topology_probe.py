import bpy,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];out=[]
for key in ['S03','S09']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-integration/bvh-r01'/f'{key}.blend'))
 ob=next(o for o in bpy.context.scene.objects if o.get('production'));bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update();bad=[e for e in bm.edges if not e.is_manifold]
 row={'id':key,'bad_edges':[{'length':e.calc_length(),'faces':len(e.link_faces),'verts':[list(v.co) for v in e.verts],'face_areas':[f.calc_area() for f in e.link_faces]} for e in bad]};out.append(row);bm.free()
print(json.dumps(out,indent=2));(R/'review/unity-integration-20261018/assets/topology-probe.json').write_text(json.dumps(out,indent=2))
