import bpy,bmesh,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];d=json.loads((R/'public/models/unity-integration/manifest.json').read_text());key=sys.argv[-1];r=next(x for x in d['assets'] if x['id']==key);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=r['source']);records=[]
for ob in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);seen=set()
 for v in bm.verts:
  if v in seen:continue
  todo=[v];part=[];seen.add(v)
  while todo:
   a=todo.pop();part.append(a)
   for e in a.link_edges:
    b=e.other_vert(a)
    if b not in seen:seen.add(b);todo.append(b)
  if len(part)>5:
   pts=[ob.matrix_world@x.co for x in part];faces={f for x in part for f in x.link_faces};records.append({'verts':len(part),'tris':sum(len(f.verts)-2 for f in faces),'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]})
 bm.free()
records.sort(key=lambda x:x['tris'],reverse=True);p=R/'review/unity-integration-20261018/assets'/key/'components.json';p.write_text(json.dumps(records,indent=2));print('COMPONENTS',key,len(records),records[:25],flush=True)
