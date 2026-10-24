import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
R=Path(__file__).resolve().parents[2]; REV='locomotion-r02'; OUT=R/'public/models/unity-lulu'/REV; SRC=R/'assets-source/unity-lulu'/REV; REP=R/'review/unity-integration-20261018/lulu'/REV
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
source=R/'assets-source/wardrobe-rig/full-r02/lulu-rig.blend'; sourceglb=R/'public/models/wardrobe-rig/full-r02/lulu-rig.glb'
bpy.ops.wm.open_mainfile(filepath=str(source)); scene=bpy.context.scene
arm=next(o for o in scene.objects if o.type=='ARMATURE'); meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
arm.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
scene.render.fps=30
bpy.context.preferences.edit.keyframe_new_interpolation_type='LINEAR'
rest={b.name:b.matrix_local.copy() for b in arm.data.bones}
for p in arm.pose.bones:p.rotation_mode='QUATERNION'
def reset():
 for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def rotate(n,axis,degrees):
 p=arm.pose.bones[n];p.rotation_quaternion=Quaternion(rest[n].to_quaternion().inverted()@Vector(axis),math.radians(degrees))
def shift(n,world):
 arm.pose.bones[n].location=rest[n].to_3x3().inverted()@Vector(world)
def segment(n,head,tail):
 mat=rest[n].copy();orig=mat.to_quaternion();origdir=orig@Vector((0,1,0));rot=origdir.rotation_difference((tail-head).normalized())@orig
 arm.pose.bones[n].matrix=Matrix.Translation(head)@rot.to_matrix().to_4x4()
 bpy.context.view_layer.update()
def pose(kind,t):
 reset();tau=math.tau*t
 if kind=='Idle':
  rotate('Spine1',(1,0,0),.45*math.sin(tau));rotate('Neck',(1,0,0),-.3*math.sin(tau));rotate('Head',(0,0,1),.6*math.sin(tau));return
 run=kind=='Run';sway=(.008 if run else .006)*math.sin(tau);lower=(-.075 if run else -.045);bob=(.006 if run else .003)*(1-math.cos(2*tau))
 shift('Hips',(sway,0,lower+bob));rotate('Spine1',(1,0,0),-2.8 if run else -.7);rotate('Spine2',(0,0,1),(1.0 if run else .6)*math.sin(tau));rotate('Neck',(1,0,0),1.3 if run else .4)
 bpy.context.view_layer.update()
 for side,phase in [('Left',0),('Right',.5)]:
  u=(t+phase)%1; s=1 if side=='Left' else -1; stride=.34 if run else .26; lift=.085 if run else .055; stance=.42 if run else .5
  if u<stance:q=u/stance;y=-stride/2+stride*q;z=0
  else:q=(u-stance)/(1-stance);y=stride/2-stride*(q*q*(3-2*q));z=lift*math.sin(math.pi*q)**1.3
  pb=arm.pose.bones[side+'UpLeg'];hip=pb.head.copy();ankle=Vector((s*.26,.075+y,-.865+z));A=arm.data.bones[side+'UpLeg'].length;B=arm.data.bones[side+'Leg'].length;D=ankle-hip;d=min(D.length,A+B-.0001);e=D.normalized();pole=Vector((0,-1,0));pole=(pole-e*pole.dot(e)).normalized();along=(A*A-B*B+d*d)/(2*d);h=math.sqrt(max(0,A*A-along*along));knee=hip+e*along+pole*h
  segment(side+'UpLeg',hip,knee);segment(side+'Leg',knee,ankle)
  # Keep flat sole orientation during stance; slight toe-off only in swing.
  foot=rest[side+'Foot'].copy();foot.translation=ankle;arm.pose.bones[side+'Foot'].matrix=foot
  angle=(14 if run else 8)*math.cos(tau+phase*math.tau);rotate(side+'Arm',(1,0,0),-angle);rotate(side+'ForeArm',(1,0,0),-(9 if run else 3));rotate(side+'Hand',(1,0,0),1)
 bpy.context.view_layer.update()
clips=[{'name':'Idle','frames':90,'duration':3.0,'source_speed':0.0},{'name':'Walk','frames':18,'duration':.6,'source_speed':.26/(.5*.6)},{'name':'Run','frames':12,'duration':.4,'source_speed':.34/(.42*.4)}]
arm.animation_data_create()
for c in clips:
 a=bpy.data.actions.new(c['name']);a.use_fake_user=True;arm.animation_data.action=a
 for f in range(c['frames']+1):
  pose(c['name'],f/c['frames'])
  for pb in arm.pose.bones:
   pb.keyframe_insert(data_path='location',frame=f+1,group=pb.name);pb.keyframe_insert(data_path='rotation_quaternion',frame=f+1,group=pb.name);pb.keyframe_insert(data_path='scale',frame=f+1,group=pb.name)
 c['world_speed_at_height_1_2']=c['source_speed']*1.2/1.900632
arm.animation_data.action=None;reset();scene.frame_set(1);scene.frame_end=91
scene['lulu_status']='Independent real in-place locomotion; source 23-bone full-r02. Controller speed must match manifest gait speed.'
scene['original_source']=str(source);scene['root_motion']='in-place; Root stationary. Apply controller translation.'
for o in meshes:o['source_revision']='wardrobe/full-r02';o['derivative']='unity locomotion-r01; original shorts/FabricUV retained'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'lulu-locomotion-master.blend'),compress=True)
# Export only model objects with real clips.
def select():
 bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
 for o in meshes:o.select_set(True)
 bpy.context.view_layer.objects.active=arm

def export(label):
 select();arm.animation_data.action=None;reset()
 bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
 print('EXPORTED',label,flush=True)
export('locomotion-master')
# Independent rebaked game derivative: each part projects only from its matching source.
budgets={'Head':32000,'Orange':2200,'Body':9000,'Shorts':11000,'Arm_L':3500,'Arm_R':3500,'Leg_L':4500,'Leg_R':4500}
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
 size=2048 if o.name=='Head' else 1024 if o.name in ['Body','Shorts'] else 512
 im=bpy.data.images.new(o.name+'_Game_BaseColor',width=size,height=size,alpha=False);im.colorspace_settings.name='sRGB'
 mat=bpy.data.materials.new(o.name+'_Game_Matte');mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.86;bsdf.inputs['Specular IOR Level'].default_value=.16
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.select=True;mat.node_tree.nodes.active=tex;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
 o.data.materials.clear();o.data.materials.append(mat)
 for f in o.data.polygons:f.material_index=0
 high.hide_render=False;high.hide_set(False);high.select_set(True);o.select_set(True);bpy.context.view_layer.objects.active=o
 scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.012;scene.render.bake.max_ray_distance=.035;scene.render.bake.margin=16;scene.render.bake.use_clear=True
 bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR'},use_selected_to_active=True)
 (OUT/'textures').mkdir(exist_ok=True);im.filepath_raw=str(OUT/'textures'/f'{o.name}-basecolor.png');im.file_format='PNG';im.save();im.pack();high.hide_render=True;high.hide_set(True)
 metrics.append({'part':o.name,'original_triangles':before,'game_triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'uv_layers':[u.name for u in o.data.uv_layers],'texture_size':size,'bake':'matching original full-r02 part only, DIFFUSE COLOR, no lighting'})
 print('BAKED',o.name,flush=True)
for o in highs:bpy.data.objects.remove(o,do_unlink=True)
select();reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'lulu-game-lod0.blend'),compress=True)
export('game-lod0')
bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
manifest={'revision':REV,'source':str(sourceglb),'source_sha256':hashlib.sha256(sourceglb.read_bytes()).hexdigest(),'source_blend':str(source),'source_blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'model':str(OUT/'lulu-game-lod0.glb'),'fbx':str(OUT/'lulu-game-lod0.fbx'),'native':str(SRC/'lulu-game-lod0.blend'),'master':str(SRC/'lulu-locomotion-master.blend'),'clips':clips,'geometry':metrics,'triangles':sum(m['game_triangles'] for m in metrics),'bones':23,'parts':8,'coordinates':{'blender_up':'+Z','blender_forward':'-Y','gltf_up':'+Y','gltf_forward':'+Z','raw_height':1.900632,'unity_scale_for_height_1_2':1.2/1.900632,'ground_origin_offset_y':.950609,'root_motion':'in place; Root does not translate; only Hips move locally'},'wardrobe':{'part':'Shorts','texCoord':1,'uv_layer':'FabricUV','registry':str(R/'public/models/wardrobe-rig/wardrobe.json')},'runtime':{'animator':'Generic or glTFast legacy Animation','crossfade_seconds':.12,'speed_multiplier':'clip playback rate scales with actual controller speed divided by world_speed_at_height_1_2'},'status':{'technical':'awaiting readback','visual':'awaiting image inspection','user_art':'pending','optimization':'candidate','device':'unverified'}}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(REP/'metrics.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('DONE',manifest['triangles'],flush=True)
