from pathlib import Path
import sys,json,hashlib
import bpy,bmesh,numpy as np
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-body-source-20261023'
rev=sys.argv[sys.argv.index('--')+1];O=D/rev
checks=[]
for row in json.loads((D/'backup.json').read_text()):
 orig=hashlib.sha256(Path(row['source']).read_bytes()).hexdigest();backup=hashlib.sha256(Path(row['backup']).read_bytes()).hexdigest()
 checks.append({'source':row['source'],'unchanged':orig==backup==row['sha256']})
 assert checks[-1]['unchanged']
a=np.load(O/'geometry-proof.npz',allow_pickle=True);s=np.load(R/'review/lulu-body-parts-20261021/source-body-frame.npz');p=a['p'];ids=a['source_id'];ret=ids>=0
err=np.linalg.norm(p[ret]-s['p'][ids[ret]],axis=1)
sourcefaces={tuple(sorted(f)) for f in s['f']};face_exact=0;retained_missing=0
for ff,reg in zip(a['faces'],a['regions']):
 if reg!=0:continue
 ff=np.array(ff,int);si=ids[ff]
 if np.all(si>=0):
  if tuple(sorted(si)) in sourcefaces:face_exact+=1
  else:retained_missing+=1
assert retained_missing==0
bpy.ops.wm.open_mainfile(filepath=str(O/'lulu-body.blend'))
obj=bpy.data.objects['Lulu_Body_FromOriginal'];bm=bmesh.new();bm.from_mesh(obj.data)
nonmanifold=sum(not e.is_manifold for e in bm.edges);boundary=sum(e.is_boundary for e in bm.edges)
assert nonmanifold==0 and boundary==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
native={'vertices':len(bm.verts),'faces':len(bm.faces),'nonmanifold_edges':nonmanifold,'boundary_edges':boundary,'reopened':True};bm.free()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'lulu-body.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];allv=[]
for o in meshes:
 for v in o.data.vertices:
  q=o.matrix_world@v.co;allv.append([q.x,q.z,-q.y])
allv=np.array(allv);assert np.isfinite(allv).all()
report={'revision':rev,'original_and_accepted_head_preserved':checks,'retained_source_vertices':int(ret.sum()),'retained_source_vertex_max_error':float(err.max()),'retained_original_faces':face_exact,'retained_face_mismatch':retained_missing,'native':native,'glb_reopened':True,'glb_meshes':len(meshes),'glb_bounds':[allv.min(0).tolist(),allv.max(0).tolist()],'art_acceptance':'PENDING_USER_REVIEW','note':'Technical preservation/manifold checks are not visual acceptance. Local patch borders need visual review.'}
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
