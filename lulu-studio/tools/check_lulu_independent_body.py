from pathlib import Path
import bpy,bmesh,numpy as np,json,hashlib,struct
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-body-parts-20261021';O=D/'body-r06'
def capture(ob):
 return (np.array([v.co[:] for v in ob.data.vertices]),np.array(ob.matrix_world),[tuple(p.vertices) for p in ob.data.polygons])
bpy.ops.wm.open_mainfile(filepath=str(D/'baseline/lulu-head.blend'));original={n:capture(bpy.data.objects[n]) for n in ['Lulu_Head_Mirrored','Original_Crown_Ornament']}
bpy.ops.wm.open_mainfile(filepath=str(O/'lulu-independent-parts.blend'));headchecks={}
for n,old in original.items():
 new=capture(bpy.data.objects[n]);checks={'vertices_identical':bool(np.array_equal(old[0],new[0])),'transform_identical':bool(np.array_equal(old[1],new[1])),'faces_identical':old[2]==new[2]};assert all(checks.values());headchecks[n]=checks
parts=[];deps=bpy.context.evaluated_depsgraph_get()
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 ev=ob.evaluated_get(deps);me=ev.to_mesh();v=np.array([v.co[:] for v in me.vertices]);assert np.isfinite(v).all();bm=bmesh.new();bm.from_mesh(me);boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);assert boundary==0 and nonmanifold==0
 parts.append({'name':ob.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'volume':bm.calc_volume()});bm.free();ev.to_mesh_clear()
assert len(parts)==6;assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();backups=json.loads((D/'backup.json').read_text())
for b in backups:assert sha(R/b['source'])==b['sha256']==sha(R/b['backup'])
exports=[]
for path in sorted(O.glob('*.glb')):
 blob=path.read_bytes();magic,version,length=struct.unpack_from('<III',blob);assert magic==0x46546c67 and version==2 and length==len(blob)
 size,kind=struct.unpack_from('<II',blob,12);g=json.loads(blob[20:20+size]);assert not g.get('skins') and not g.get('animations');exports.append({'file':path.name,'bytes':len(blob),'meshes':len(g['meshes']),'sha256':sha(path)})
# Reimport exported assembly into an empty scene to prove independent meshes load.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'lulu-assembled.glb'))
imported=[o.name for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==6
report={'revision':'body-r06','native_reopened':True,'glb_reimported':True,'imported_parts':imported,'head_and_ornament_geometry':headchecks,'head_boundary_shading_note':'Only neck boundary custom normals differ in assembly; accepted canonical head files untouched.','parts':parts,'exports':exports,'all_backups_and_originals_hash_verified':True,'armatures':0,'animations':0,'acceptance':'Technical checks passed; static body/arm appearance awaits user acceptance.'}
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'parts':len(parts),'head_geometry_unchanged':True,'backups_unchanged':True,'native_and_glb_reopened':True},indent=2))
