import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];rev='locomotion-r07';OUT=R/'public/models/unity-lulu'/rev;SRC=R/'assets-source/unity-lulu'/rev;REP=R/'review/unity-integration-20261018/lulu'/rev
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'game-lod0';base='locomotion-r02' if label=='locomotion-master' else 'locomotion-r04'
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu'/base/f'lulu-{label}.blend'));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
for o in meshes:
 if not o.name.startswith('Leg_'):continue
 side='Left' if o.name=='Leg_L' else 'Right';footname=side+'Foot'
 for vg in o.vertex_groups:vg.remove(list(range(len(o.data.vertices))))
 o.vertex_groups[footname].add(list(range(len(o.data.vertices))),1,'REPLACE')
body=bpy.data.objects['Body'];body.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(f.vertices) for f in body.data.loop_triangles],all_triangles=True)
patches=[]
for s in [-1,1]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=(s*.443,-.045,-.416));o=bpy.context.object;o.name='ConcealedWaistSideClosure';o.scale=(.022,.055,.034);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(body.data.materials[0]);o.vertex_groups.new(name='Hips').add(list(range(len(o.data.vertices))),1,'REPLACE')
 o.data.uv_layers[0].name=body.data.uv_layers[0].name
 for f in o.data.polygons:f.use_smooth=True
 for li,l in enumerate(o.data.loops):
  near=tree.find_nearest(Vector((0,-.27,-.4)));tri=body.data.loop_triangles[near[2]];co=[body.data.vertices[k].co for k in tri.vertices];uvs=[Vector((*body.data.uv_layers[0].data[k].uv,0)) for k in tri.loops];uv=barycentric_transform(near[0],*co,*uvs);o.data.uv_layers[0].data[li].uv=(uv.x,uv.y)
 patches.append(o)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in patches:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'lulu-{label}.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
if label=='game-lod0':
 bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
 m=json.loads((R/'public/models/unity-lulu/locomotion-r04/manifest.json').read_text());m['revision']=rev
 for k in ['model','fbx','native']:m[k]=m[k].replace('locomotion-r04',rev)
 m['status']={'technical':'pending_readback','visual':'pending_actual_inspection','user_art':'pending','optimization':'candidate','device':'unverified'};m['locomotion_repair']='Visible stub legs rigid to Foot; 2 small concealed skin-material closures under existing side waist. Original coordinates and FabricUV unchanged.';(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
