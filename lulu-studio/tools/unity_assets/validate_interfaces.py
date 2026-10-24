import bpy,bmesh,json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
for folder,key,files in [('interface-r04','S06',['S06-open-gate','S06-left-post','S06-right-post','S06-gate-leaf']),('interface-r01','E05-corner',['E05-corner'])]:
 rows=[]
 for f in files:
  p=R/'public/models/unity-integration'/folder/(f+'.glb');m=H.check_glb(p);m['file']=str(p);top=[]
  for o in bpy.context.scene.objects:
   if o.type!='MESH':continue
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);top.append({'name':o.name,'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges)});bm.free()
  m['welded_topology']=top;rows.append(m)
 out=R/'review/unity-integration-20261018/assets'/key/folder;(out/'roundtrip.json').write_text(json.dumps(rows,indent=2));print('ROUNDTRIP',key,rows[0]['triangles'],rows[0]['welded_topology'],flush=True)
