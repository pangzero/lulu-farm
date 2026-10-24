import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];rev='locomotion-r08';OUT=R/'public/models/unity-lulu'/rev;SRC=R/'assets-source/unity-lulu'/rev;REP=R/'review/unity-integration-20261018/lulu'/rev
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'game-lod0';base='locomotion-r02' if label=='locomotion-master' else 'locomotion-r04'
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu'/base/f'lulu-{label}.blend'));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
for o in meshes:
 if not o.name.startswith('Leg_'):continue
 side='Left' if o.name=='Leg_L' else 'Right';footname=side+'Foot'
 for vg in o.vertex_groups:vg.remove(list(range(len(o.data.vertices))))
 o.vertex_groups[footname].add(list(range(len(o.data.vertices))),1,'REPLACE')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'lulu-{label}.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
if label=='game-lod0':
 bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
 m=json.loads((R/'public/models/unity-lulu/locomotion-r04/manifest.json').read_text());m['revision']=rev
 for k in ['model','fbx','native']:m[k]=m[k].replace('locomotion-r04',rev)
 m['status']={'technical':'pending_readback','visual':'waist_seam_unresolved_pending_multiphase','user_art':'pending','optimization':'candidate','device':'unverified'};m['locomotion_repair']='Visible short legs rigid to Foot; original coordinates, normals, UV0 and FabricUV unchanged. No waist patch used; original waist seam remains unresolved.';(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
