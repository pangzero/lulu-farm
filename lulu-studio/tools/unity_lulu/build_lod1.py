import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
R=Path(__file__).resolve().parents[2];REV='locomotion-r02';OUT=R/'public/models/unity-lulu'/REV;SRC=R/'assets-source/unity-lulu'/REV;REP=R/'review/unity-integration-20261018/lulu'/REV
bpy.ops.wm.open_mainfile(filepath=str(SRC/'lulu-locomotion-master.blend'));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
def reset():
 for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
arm.animation_data.action=None;reset()
def select():
 bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
 for o in meshes:o.select_set(True)
 bpy.context.view_layer.objects.active=arm

def export(label):
 select();arm.animation_data.action=None;reset()
 bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
# Independent rebaked game derivative: each part projects only from its matching source.
budgets={'Head':18000,'Orange':1000,'Body':4200,'Shorts':6000,'Arm_L':1800,'Arm_R':1800,'Leg_L':2300,'Leg_R':2300}
metrics=[]; highs=[]
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
for o in meshes:
 high=o.copy();high.data=o.data.copy();high.name=o.name+'_BakeHigh';scene.collection.objects.link(high);high.hide_render=True;high.hide_set(True);highs.append(high)
for o,high in zip(meshes,highs):
 bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 before=sum(len(p.vertices)-2 for p in o.data.polygons)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.0000003);bpy.ops.object.mode_set(mode='OBJECT')
 dec=o.modifiers.new('Independent per-part game LOD','DECIMATE');dec.ratio=min(1,budgets[o.name]/max(1,before));dec.use_collapse_triangulate=True
 bpy.ops.object.modifier_move_up(modifier=dec.name);bpy.ops.object.modifier_apply(modifier=dec.name)
 for p in o.data.polygons:p.use_smooth=True
 # Keep FabricUV index1; replace UV0 only and bake original colour.
 o.data.uv_layers.active_index=0;o.data.uv_layers[0].name='GameAtlas'
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
 for ca in list(o.data.color_attributes):o.data.color_attributes.remove(ca)
 size=1024 if o.name in ['Head','Body','Shorts'] else 512
 im=bpy.data.images.new(o.name+'_Game_BaseColor',width=size,height=size,alpha=False);im.colorspace_settings.name='sRGB'
 mat=bpy.data.materials.new(o.name+'_Game_Matte');mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.86;bsdf.inputs['Specular IOR Level'].default_value=.16
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.select=True;mat.node_tree.nodes.active=tex;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
 o.data.materials.clear();o.data.materials.append(mat)
 for f in o.data.polygons:f.material_index=0
 high.hide_render=False;high.hide_set(False);high.select_set(True);o.select_set(True);bpy.context.view_layer.objects.active=o
 scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.012;scene.render.bake.max_ray_distance=.035;scene.render.bake.margin=16;scene.render.bake.use_clear=True
 bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR'},use_selected_to_active=True)
 (OUT/'textures-lod1').mkdir(exist_ok=True);im.filepath_raw=str(OUT/'textures-lod1'/f'{o.name}-basecolor.png');im.file_format='PNG';im.save();im.pack();high.hide_render=True;high.hide_set(True)
 metrics.append({'part':o.name,'original_triangles':before,'game_triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'uv_layers':[u.name for u in o.data.uv_layers],'texture_size':size,'bake':'matching original full-r02 part only, DIFFUSE COLOR, no lighting'})
 print('BAKED',o.name,flush=True)
for o in highs:bpy.data.objects.remove(o,do_unlink=True)
select();reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'lulu-game-lod1.blend'),compress=True)
export('game-lod1')

(REP/'lod1-metrics.json').write_text(json.dumps({'parts':metrics,'triangles':sum(x['game_triangles'] for x in metrics)},indent=2))
