"""Rigidly orient the independent head using its symmetry plane and fruit axis.

No sculpting or anatomical deletion. Preserve r04 and save a new native/GLB copy.
The tiny residual fruit tilt is corrected as a separate rigid object rotation.
"""
from pathlib import Path
import bpy, numpy as np, json, hashlib
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-head-mirror-20261021';O=D/'head-r05'
if O.exists():raise RuntimeError('Preserve revisions; output already exists')
O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={s:sha(D/'head-r04'/s) for s in ['lulu-head-mirrored.blend','lulu-head-mirrored.glb','lulu-head-only.glb']}
a=np.load(D/'baseline/welded-source.npz');p=a['p'].astype(float);B=a['head_basis'];c=a['head_center'];h=np.einsum('ij,kj->ik',p-c,B);h[:,1]+=.72
fruit=p[(h[:,1]>.933)&(h[:,1]<1.007)&(np.abs(h[:,0])<.12)&(np.abs(h[:,2])<.12)]
origin=fruit.mean(0);q=fruit-origin
A=np.c_[q[:,0]**2,q[:,1]**2,q[:,2]**2,2*q[:,0]*q[:,1],2*q[:,0]*q[:,2],2*q[:,1]*q[:,2],q[:,0],q[:,1],q[:,2]]
r=np.linalg.lstsq(A,np.ones(len(q)),rcond=None)[0]
M=np.array([[r[0],r[3],r[4]],[r[3],r[1],r[5]],[r[4],r[5],r[2]]])
e,axes=np.linalg.eigh(M);fruit_axis=axes[:,np.argmax(e)]
if fruit_axis[1]<0:fruit_axis=-fruit_axis
fruit_center=origin-np.linalg.solve(2*M,r[6:])
right=B[0].copy();up=fruit_axis-right*np.dot(fruit_axis,right);up/=np.linalg.norm(up);front=np.cross(right,up)
newbasis=np.array([right,up,front]);T=np.eye(4);T[:3,:3]=newbasis;T[:3,3]=np.array([0,.72,0])-np.einsum('ij,j->i',newbasis,c)
mapped_axis=np.einsum('ij,j->i',newbasis,fruit_axis);mapped_center=np.einsum('ij,j->i',newbasis,fruit_center)+T[:3,3]
extra=Vector(mapped_axis).rotation_difference(Vector((0,1,0))).to_matrix().to_4x4()
extra=Matrix.Translation(Vector(mapped_center))@extra@Matrix.Translation(-Vector(mapped_center))
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)));head_transform=C@Matrix(T.tolist())@C.inverted();fruit_transform=C@extra@Matrix(T.tolist())@C.inverted()
bpy.ops.wm.open_mainfile(filepath=str(D/'head-r04/lulu-head-mirrored.blend'))
head=bpy.data.objects['Lulu_Head_Mirrored'];ornament=bpy.data.objects['Original_Crown_Ornament'];ref=bpy.data.objects['Original_Source_Unmodified']
original_head_positions=np.array([v.co[:] for v in head.data.vertices]);head.matrix_world=head_transform;ornament.matrix_world=fruit_transform;ref.matrix_world=head_transform
head['orientation_note']='Rigid orientation only from r04; head symmetry plane is vertical. No head vertex shape edits.'
ornament['orientation_note']='Fruit body axis upright, leaf curvature retained; additional rigid tilt correction below one degree.'
bpy.context.scene['stage']='Head-r05 upright symmetry inspection. Head/body/arm/rig approval still pending.'
for obj in bpy.context.scene.objects:obj.select_set(False)
head.select_set(True);ornament.select_set(True);bpy.context.view_layer.objects.active=head
bpy.ops.export_scene.gltf(filepath=str(O/'lulu-head-mirrored.glb'),export_format='GLB',use_selection=True,export_yup=True,export_extras=True)
ornament.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(O/'lulu-head-only.glb'),export_format='GLB',use_selection=True,export_yup=True,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'lulu-head-mirrored.blend'))
bpy.ops.wm.open_mainfile(filepath=str(O/'lulu-head-mirrored.blend'))
head=bpy.data.objects['Lulu_Head_Mirrored']
assert np.array_equal(original_head_positions,np.array([v.co[:] for v in head.data.vertices]))
for s,digest in before.items():assert sha(D/'head-r04'/s)==digest
assert sha(Path('/Users/haowen/Downloads/a5747f74f0034470a2029a85f6e9c11d.glb'))=='13c234b586876b53cc5bd435b55ffd8612cb3994accb83648c5ba9f5fd0a037b'
report={'revision':'head-r05','base':'head-r04','method':'Rigid rotation and translation only; no resculpt or scale. Vertical head symmetry plane, fruit body up axis aligned with world Y.','source_to_upright_column_major':T.T.flatten().tolist(),'source_to_upright_rows':T.tolist(),'fruit_original_axis':fruit_axis.tolist(),'fruit_axis_after_head_rotation':mapped_axis.tolist(),'fruit_residual_correction_degrees':float(np.degrees(np.arccos(mapped_axis[1]))),'fruit_center':fruit_center.tolist(),'fit_rms':float(np.sqrt(np.mean((np.einsum('ij,j->i',A,r)-1)**2))),'head_vertex_positions_identical_to_r04':True,'r04_hashes':before,'original_unchanged':True,'native_reopened':True,'armatures':len([o for o in bpy.data.objects if o.type=='ARMATURE']),'remaining':'Existing lower neck closure lip unchanged; inspect upright before any local geometry edits. Original reference intentionally retains raised hand, candidate does not contain that hand geometry.'}
(O/'alignment.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
