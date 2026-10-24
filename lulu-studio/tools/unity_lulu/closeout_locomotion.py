import bpy,bmesh,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];rev='locomotion-r06';OUT=R/'public/models/unity-lulu'/rev;SRC=R/'assets-source/unity-lulu'/rev;REP=R/'review/unity-integration-20261018/lulu'/rev
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'game-lod0';base='locomotion-r02' if label=='locomotion-master' else 'locomotion-r04'
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu'/base/f'lulu-{label}.blend'));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
for o in meshes:
 if not o.name.startswith('Leg_'):continue
 side='Left' if o.name=='Leg_L' else 'Right';footname=side+'Foot'
 for vg in o.vertex_groups:vg.remove(list(range(len(o.data.vertices))))
 o.vertex_groups[footname].add(list(range(len(o.data.vertices))),1,'REPLACE')
shorts=next(o for o in meshes if o.name=='Shorts');p=np.array([v.co[:] for v in shorts.data.vertices]);cx=0;cy=.075;theta=np.mod(np.arctan2(p[:,0],p[:,1]-cy),math.tau);radius=np.sqrt(p[:,0]**2+(p[:,1]-cy)**2);N=128;tops=[];rads=[]
for i in range(N):
 sel=np.abs(np.angle(np.exp(1j*(theta-math.tau*i/N))))<math.tau/N
 q=p[sel];rr=radius[sel];z=float(q[:,2].max());tops.append(z);rads.append(float(np.percentile(rr[q[:,2]>z-.02],75)))
tops=np.array(tops);rads=np.array(rads)
for _ in range(2):tops=(np.roll(tops,1)+2*tops+np.roll(tops,-1))/4;rads=(np.roll(rads,1)+2*rads+np.roll(rads,-1))/4
verts=[]
for layer in range(4):
 for i in range(N):
  a=math.tau*i/N;rad=rads[i]+(.001 if layer in [0,1] else -.009);z=tops[i]+(-.014 if layer in [0,3] else .025)
  verts.append((math.sin(a)*rad,cy+math.cos(a)*rad,z))
faces=[]
for l in range(4):
 for i in range(N):j=(i+1)%N;faces.append((l*N+i,l*N+j,((l+1)%4)*N+j,((l+1)%4)*N+i))
me=bpy.data.meshes.new('ShortsInnerWaistClosure');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();ob=bpy.data.objects.new('ShortsInnerWaistClosure',me);bpy.context.scene.collection.objects.link(ob);ob.data.materials.append(shorts.data.materials[0]);vg=ob.vertex_groups.new(name='Hips');vg.add(list(range(len(verts))),1,'REPLACE')
# Constant UV0 samples the original front waistband orange; UV1 follows existing fabric top edge.
shorts.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in shorts.data.vertices],[list(f.vertices) for f in shorts.data.loop_triangles],all_triangles=True);near=tree.find_nearest(Vector((0,-.29,-.53)));tri=shorts.data.loop_triangles[near[2]];co=[shorts.data.vertices[k].co for k in tri.vertices];uvs=[Vector((*shorts.data.uv_layers[0].data[k].uv,0)) for k in tri.loops];sample=barycentric_transform(near[0],*co,*uvs)
for u in shorts.data.uv_layers:me.uv_layers.new(name=u.name)
for f in me.polygons:
 f.use_smooth=True
 for li in f.loop_indices:
  vi=me.loops[li].vertex_index;v=Vector(verts[vi]);me.uv_layers[0].data[li].uv=(sample.x,sample.y)
  if len(me.uv_layers)>1:me.uv_layers[1].data[li].uv=(math.atan2(v.x,-v.y+.08)/math.tau+.5,.995)
# Join only the concealed/overlap waist strip; all existing vertices remain in place.
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);shorts.select_set(True);bpy.context.view_layer.objects.active=shorts;bpy.ops.object.join()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'lulu-{label}.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
if label=='game-lod0':
 bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
 m=json.loads((R/'public/models/unity-lulu/locomotion-r04/manifest.json').read_text());m['revision']=rev
 for k in ['model','fbx','native']:m[k]=m[k].replace('locomotion-r04',rev)
 m['locomotion_repair']='Visible stub legs rigid to Foot; knee/upper-leg mechanism remains under pants; original mesh vertices unchanged. Shorts adds thin inner waist overlap strip, original external vertices unchanged.';(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(REP/f'{label}-repair.json').write_text(json.dumps({'legs':'rigid Foot, original coordinates/UV/normals untouched','waist_strip_vertices':len(verts),'waist_strip_faces':len(faces),'overlap_height':.025,'original_vertices_unchanged':True,'UV0_sample':list(sample)[:2]},indent=2))
