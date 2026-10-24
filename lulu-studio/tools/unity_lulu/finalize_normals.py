import bpy,json
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[2];rev='locomotion-r04';OUT=R/'public/models/unity-lulu'/rev;SRC=R/'assets-source/unity-lulu'/rev;REP=R/'review/unity-integration-20261018/lulu'/rev
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu/locomotion-r03/lulu-game-lod0.blend'));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];head=next(o for o in meshes if o.name=='Head');bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head;bpy.ops.mesh.customdata_custom_splitnormals_clear()
arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'lulu-game-lod0.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'lulu-game-lod0.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
m=json.loads((R/'public/models/unity-lulu/locomotion-r03/manifest.json').read_text());m['revision']=rev
for k in ['model','fbx','native']:m[k]=m[k].replace('locomotion-r03',rev)
m['normal_revision']='Original part normals except Head uses its smooth normals to avoid projection from folded underside; source geometry same as r02.';(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
