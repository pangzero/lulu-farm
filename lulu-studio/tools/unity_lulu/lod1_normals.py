import bpy,json,sys
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[2];old='locomotion-r02';rev='locomotion-r04';OUT=R/'public/models/unity-lulu'/rev;SRC=R/'assets-source/unity-lulu'/rev;REP=R/'review/unity-integration-20261018/lulu'/rev
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'game-lod0'
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu'/old/f'lulu-{label}.blend'));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');low={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'};arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
with bpy.data.libraries.load(str(R/'assets-source/unity-lulu'/old/'lulu-locomotion-master.blend'),link=False) as (a,b):b.objects=[x for x in a.objects if x in low]
for high in b.objects:
 if high is None:continue
 name=high.name.split('.')[0];bpy.context.scene.collection.objects.link(high);high.parent=None;high.matrix_world=Matrix.Identity(4)
 for mod in list(high.modifiers):high.modifiers.remove(mod)
 o=low[name]
 if name=='Head':
  bpy.data.objects.remove(high,do_unlink=True);continue
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 dt=o.modifiers.new('Original surface normal transfer','DATA_TRANSFER');dt.object=high;dt.use_loop_data=True;dt.data_types_loops={'CUSTOM_NORMAL'};dt.loop_mapping='POLYINTERP_NEAREST';dt.mix_mode='REPLACE';dt.mix_factor=1
 while list(o.modifiers).index(dt)>0:bpy.ops.object.modifier_move_up(modifier=dt.name)
 bpy.ops.object.modifier_apply(modifier=dt.name);bpy.data.objects.remove(high,do_unlink=True)
for o in list(bpy.context.scene.objects):
 if o not in low.values() and o!=arm:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in low.values():o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'lulu-{label}.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
if label=='game-lod0':
 bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
 m=json.loads((R/'public/models/unity-lulu'/old/'manifest.json').read_text());m['revision']=rev
 for k in ['model','fbx','native']:m[k]=m[k].replace(old,rev)
 m['normal_revision']='Original full-r02 per-loop normal projection; geometry and UVs unchanged from r02 game derivative.';(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
print('TRANSFER COMPLETE',label)
