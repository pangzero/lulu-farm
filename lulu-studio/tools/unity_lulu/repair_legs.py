import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[2];rev='locomotion-r05';OUT=R/'public/models/unity-lulu'/rev;SRC=R/'assets-source/unity-lulu'/rev;REP=R/'review/unity-integration-20261018/lulu'/rev
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'game-lod0';base='locomotion-r02' if label=='locomotion-master' else 'locomotion-r04'
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu'/base/f'lulu-{label}.blend'));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
report=[]
for o in meshes:
 if not o.name.startswith('Leg_'):continue
 side='Left' if o.name=='Leg_L' else 'Right';footname=side+'Foot';groups={g.index:g.name for g in o.vertex_groups};count=0
 for v in o.data.vertices:
  z=v.co.z;t=max(0,min(1,(z+.805)/.05));foot=1-t*t*(3-2*t)
  if foot<=0:continue
  old={groups[g.group]:g.weight for g in v.groups};other={k:w for k,w in old.items() if k!=footname};s=sum(other.values())
  for vg in o.vertex_groups:vg.remove([v.index])
  if s>1e-8:
   for k,w in other.items():o.vertex_groups[k].add([v.index],w/s*(1-foot),'REPLACE')
  else:foot=1
  o.vertex_groups[footname].add([v.index],foot,'REPLACE');count+=1
 report.append({'part':o.name,'edited_vertices':count,'rigid_visible_foot_below_z':-.805,'transition_hidden_between_z':[-.805,-.755]})
 bpy.context.view_layer.objects.active=o
 # Preserve weight normalization and four maximum influences after targeted blend.
 o.select_set(True)
 bpy.ops.object.vertex_group_limit_total(limit=4)
 bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'lulu-{label}.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
if label=='game-lod0':
 bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
 m=json.loads((R/'public/models/unity-lulu/locomotion-r04/manifest.json').read_text());m['revision']=rev
 for k in ['model','fbx','native']:m[k]=m[k].replace('locomotion-r04',rev)
 m['leg_revision']=report;(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(REP/f'{label}-weight-repair.json').write_text(json.dumps(report,indent=2))
