"""Fixed orthographic reference checks of the actual editable character."""
import bpy, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets-source/lulu.blend'))
scene=bpy.context.scene
for o in list(scene.objects):
 o.hide_set(False);o.hide_render=o.name.startswith('Can')
 if o.type=='ARMATURE':
  o.animation_data_clear()
  for b in o.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=600;scene.render.resolution_y=760;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.40
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;floor.name='CheckGround';floor.location.z=-.015
m=bpy.data.materials.new('CheckWhite');m.diffuse_color=(.93,.92,.88,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.93,.92,.88,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85;floor.data.materials.append(m)
for name,pos,power,size in [('Key',(-3,-4,6),170,5),('Fill',(4,-2,3),80,4),('Rim',(0,3,4),100,4)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('ReferenceCamera');data.type='ORTHO';data.ortho_scale=2.52
cam=bpy.data.objects.new('ReferenceCamera',data);scene.collection.objects.link(cam);scene.camera=cam
for name,pos in [('front',(0,-8,1.23)),('side',(-8,-3,1.23)),('back',(0,8,1.23)),('quarter',(6,-6,1.6))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,1.14))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(ROOT/'review'/('lulu-fit-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('REFERENCE_RENDERS_COMPLETE')
