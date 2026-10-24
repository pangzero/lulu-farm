import bpy,json,sys,math,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parents[2];REV='locomotion-r08';REP=R/'review/unity-integration-20261018/lulu'/REV
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []; mode=args[0] if args else 'quick'; label=args[1] if len(args)>1 else 'game-lod0'
source=R/'assets-source/unity-lulu'/REV/('lulu-'+label+'.blend');bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
world=bpy.data.worlds.new('Review World');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.83,.9,1);world.node_tree.nodes['Background'].inputs[1].default_value=.32;scene.world=world
for name,loc,power,size in [('Key',(-3,-4,6),280,4),('Fill',(4,-1,3),140,3),('Rim',(0,4,5),230,3)]:
 d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.951));floor=bpy.context.object;floor.name='ReviewFloor';m=bpy.data.materials.new('ReviewGround');m.diffuse_color=(.76,.8,.77,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.76,.8,.77,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9;floor.data.materials.append(m)
d=bpy.data.cameras.new('FixedReviewCamera');cam=bpy.data.objects.new('FixedReviewCamera',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=2.35;d.lens=50
views={'front':(0,-1,.025),'side':(1,0,.025),'back':(0,1,.025),'quarter':(1.35,-4,2.25),'top':(0,-.001,1)}
gray=bpy.data.materials.new('NeutralClay');gray.diffuse_color=(.5,.5,.5,1);gray.use_nodes=True;gray.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.5,.5,.5,1);gray.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.84
out=REP/label;out.mkdir(exist_ok=True)
def render(view,clip=None,frame=1,clay=False):
 arm.animation_data.action=bpy.data.actions.get(clip) if clip else None
 if not clip:
  for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
 scene.frame_set(frame);bpy.context.view_layer.update();target=Vector((0,0,0));cam.location=target+Vector(views[view]).normalized()*5;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.view_layers[0].material_override=gray if clay else None
 scene.render.filepath=str(out/f'{clip or "Rest"}-{frame:03d}-{view}-{"clay" if clay else "color"}.png');bpy.ops.render.render(write_still=True)
# Explicit same-cut UV1 outfit checks; geometry and skin unchanged.
shorts=next(o for o in meshes if o.name=='Shorts')
for preset in ['blue-stars','watermelon']:
 out=REP/'wardrobe'/preset;out.mkdir(parents=True,exist_ok=True)
 mat=bpy.data.materials.new(preset+'FabricUV1');mat.use_nodes=True;bsdf=mat.node_tree.nodes['Principled BSDF'];bsdf.inputs['Roughness'].default_value=.86
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'public/models/wardrobe-rig/materials-v2'/f'{preset}.png'));uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='FabricUV';mat.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector']);mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
 shorts.data.materials.clear();shorts.data.materials.append(mat)
 for p in shorts.data.polygons:p.material_index=0
 render('front');render('back');render('quarter','Run',4)
