from pathlib import Path
import bpy,numpy as np,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-body-parts-20261021';O=D/'body-r07'
if O.exists():raise RuntimeError('Preserve existing candidate')
O.mkdir();bpy.ops.wm.open_mainfile(filepath=str(D/'body-r06/lulu-independent-parts.blend'))
torso=bpy.data.objects['Lulu_Torso'];head=bpy.data.objects['Lulu_Head_Mirrored'];orn=bpy.data.objects['Original_Crown_Ornament'];parts=[head,orn,torso,bpy.data.objects['Lulu_LowerBody_SourceMirror'],bpy.data.objects['Lulu_Arm_L'],bpy.data.objects['Lulu_Arm_R']]
bvh=BVHTree.FromObject(torso,bpy.context.evaluated_depsgraph_get())
for ob in parts[-2:]:
 vg=ob.vertex_groups.new(name='ShoulderContactNormals')
 for v in ob.data.vertices:
  y=v.co.z
  if y<.38:continue
  loc,n,idx,dist=bvh.find_nearest(v.co)
  fade=max(0,min(1,(y-.38)/.043));fade=fade*fade*(3-2*fade)
  w=fade*math.exp(-(dist/.020)**2)
  if w>.001:vg.add([v.index],w,'REPLACE')
 mod=ob.modifiers.new('Shoulder contact shading','DATA_TRANSFER');mod.object=torso;mod.use_loop_data=True;mod.data_types_loops={'CUSTOM_NORMAL'};mod.loop_mapping='POLYINTERP_NEAREST';mod.vertex_group=vg.name;mod.mix_mode='REPLACE';mod.mix_factor=1.
 ob['junction_note']='Only contact shading normals matched to torso in narrow upper-arm band. No torso or arm vertex position changed from body-r06.'
for o in bpy.context.scene.objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=torso
bpy.ops.export_scene.gltf(filepath=str(O/'lulu-assembled.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True)
for ob,fn in [(torso,'torso'),(parts[3],'lower-body'),(parts[4],'arm-left'),(parts[5],'arm-right')]:
 for o in parts:o.select_set(False)
 ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.gltf(filepath=str(O/f'lulu-{fn}.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=torso;bpy.ops.wm.save_as_mainfile(filepath=str(O/'lulu-independent-parts.blend'))
report=json.loads((D/'body-r06/build.json').read_text());report.update(revision='body-r07',base='body-r06',change='Only upper-arm contact normals; all object vertex positions and transforms unchanged from r06.')
(O/'build.json').write_text(json.dumps(report,indent=2))
