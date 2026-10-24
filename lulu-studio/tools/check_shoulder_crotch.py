import bpy,bmesh,json,hashlib,struct
from mathutils.bvhtree import BVHTree
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'assets-source/lulu-head-study.blend'))
report={'user_accepted':False,'geometry':{},'preserved':{}}
for name in ['Lulu_ContinuousShoulderSkin','Ear_-1','Ear_1','Shorts_Tailored']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 report['geometry'][name]={'vertices':len(bm.verts),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)};bm.free()
head=bpy.data.objects['Source_HeadStudy_ContinuousCage']
head.hide_set(False);tree=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
errors=[tree.find_nearest(v.co)[3] for v in bpy.data.objects['Lulu_ContinuousShoulderSkin'].data.vertices if v.co.z>1.20]
report['upper_head_max_distance_to_original_surface']=max(errors)
base=root/'review/shoulder-crotch-baseline/lulu-head-study.blend'
with bpy.data.libraries.load(str(base),link=False) as (a,b):b.objects=[n for n in a.objects if n in ['Source_HeadStudy_ContinuousCage','Foot_-1','Foot_1','Ear_-1','Ear_1','Source_Arm_-1','Source_Arm_1','Shorts_Tailored']]
for old in b.objects:
 name=old.name.split('.')[0];current=head if name=='Source_HeadStudy_ContinuousCage' else bpy.data.objects[name]
 pairs=list(zip(old.data.vertices,current.data.vertices))
 if name.startswith('Source_Arm_'):
  report['preserved'][name+'_palm_below_0.615']=all((a.co-b.co).length<1e-7 for a,b in pairs if a.co.z<=.615)
 elif name=='Shorts_Tailored':
  report['cloth_max_displacement']=max((a.co-b.co).length for a,b in pairs)
  report['preserved']['cloth_back']=all((a.co-b.co).length<1e-7 for a,b in pairs if a.co.y>=-.10)
  report['preserved']['cloth_xz_outline']=all(abs(a.co.x-b.co.x)<1e-7 and abs(a.co.z-b.co.z)<1e-7 for a,b in pairs)
 else:
  report['preserved'][name]=len(old.data.vertices)==len(current.data.vertices) and all((a.co-b.co).length<1e-7 for a,b in pairs)
p=root/'public/models/lulu-head-study.glb';data=p.read_bytes();length=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+length])
report.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),images=len(g.get('images',[])),textures=len(g.get('textures',[])),materials=[m['name'] for m in g.get('materials',[])],exported_source_nodes=[n.get('name') for n in g.get('nodes',[]) if n.get('name','').startswith('Source_')])
(root/'review/shoulder-crotch-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
