import bpy,bmesh,json,hashlib,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'assets-source/lulu-head-study.blend'))
report={'user_accepted':False,'geometry':{},'preserved':{}}
for name in ['Ear_-1','Ear_1','HeadStudy_ContinuousCage','Arm_-1','Arm_1']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 report['geometry'][name]={'control_vertices':len(bm.verts),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)};bm.free()
base=root/'review/ear-shell-baseline/lulu-head-study.blend'
with bpy.data.libraries.load(str(base),link=False) as (a,b):
 b.objects=[n for n in a.objects if n in ['HeadStudy_ContinuousCage','Arm_-1','Arm_1','Foot_-1','Foot_1']]
for old in b.objects:
 name=old.name.rsplit('.',1)[0];current=bpy.data.objects[name]
 report['preserved'][name]=len(old.data.vertices)==len(current.data.vertices) and all((a.co-b.co).length<1e-7 for a,b in zip(old.data.vertices,current.data.vertices))
p=root/'public/models/lulu-head-study.glb';data=p.read_bytes();length=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+length])
report.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),images=len(g.get('images',[])),textures=len(g.get('textures',[])),materials=[m['name'] for m in g.get('materials',[])])
(root/'review/ear-shell-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
