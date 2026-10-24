import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];REV='game-r04';OUT=R/'review/unity-integration-20261018/animals'/REV/'scale';OUT.mkdir(exist_ok=True);items=[a for a in json.loads((R/'public/models/unity-integration/manifest.json').read_text())['assets'] if a['type']=='animal'];variant=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'lod0'
for group in range(3):
 
 if (OUT/(variant+'-group-'+str(group+1)+'.png')).exists():continue
 if any(not (R/'public/models/unity-animals'/REV/a['id']/(variant+'.glb')).exists() for a in items[group*5:(group+1)*5]):continue
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;bpy.ops.import_scene.gltf(filepath=str(R/'public/models/unity-lulu/locomotion-r08/lulu-game-lod0.glb'));lulu=list(scene.objects)
 for o in lulu:
  if o.animation_data:o.animation_data_clear()
  if o.type=='ARMATURE':
   for p in o.pose.bones:p.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();root=bpy.data.objects.new('Lulu_readonly_1_2',None);scene.collection.objects.link(root)
 for o in lulu:
  if o.parent is None:o.parent=root
 root.scale=(.6313689341,)*3;root.location=(-3.75,0,.950609*.6313689341)
 selected=items[group*5:(group+1)*5];sizes=[]
 for i,a in enumerate(selected):
  before=set(scene.objects);file=R/'public/models/unity-animals'/REV/a['id']/(variant+'.glb');bpy.ops.import_scene.gltf(filepath=str(file));new=[o for o in scene.objects if o not in before];meshes=[o for o in new if o.type=='MESH'];pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];mi=Vector([min(p[j] for p in pts) for j in range(3)]);ma=Vector([max(p[j] for p in pts) for j in range(3)]);height=a['suggested_world_height'];metric=json.loads((R/'public/models/unity-animals'/REV/a['id']/'lod0-manifest.json').read_text());mi,ma=[Vector(x) for x in metric['bounds_blender']];scale=height/(ma.z-mi.z);root=bpy.data.objects.new(a['id']+'_scale',None);scene.collection.objects.link(root)
  for o in new:
   if o.parent is None:o.parent=root
  root.scale=(scale,)*3;root.location=(-2.25+i*1.5-(ma.x+mi.x)/2*scale,-(ma.y+mi.y)/2*scale,-mi.z*scale);sizes.append({'id':a['id'],'world_height':height,'scale':scale,'ground_offset_z':-mi.z*scale})
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8;scene.cycles.use_denoising=True;scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
 world=bpy.data.worlds.new('Review World');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.83,.9,1);world.node_tree.nodes['Background'].inputs[1].default_value=.32;scene.world=world;target=Vector((0,0,.55))
 for name,loc,power,size in [('Key',(-3,-4,6),280,4),('Fill',(4,-1,3),140,3),('Rim',(0,4,5),230,3)]:
  d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.003));m=bpy.data.materials.new('ReviewGround');m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.76,.8,.77,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9;bpy.context.object.data.materials.append(m)
 d=bpy.data.cameras.new('ScaleCamera');cam=bpy.data.objects.new('ScaleCamera',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=9.7;cam.location=target+Vector((0,-4,1.8)).normalized()*10;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(variant+'-group-'+str(group+1)+'.png'));bpy.ops.render.render(write_still=True);(OUT/(variant+'-group-'+str(group+1)+'.json')).write_text(json.dumps({'lulu_height':1.2,'left_to_right':['lulu']+[a['id'] for a in selected],'animals':sizes,'pixel_size':[1280,720],'all_rooted_at_z':0,'source_originals_unchanged':True},indent=2))
