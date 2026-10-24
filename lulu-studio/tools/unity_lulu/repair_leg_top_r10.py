import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];rev='locomotion-r10';OUT=R/'public/models/unity-lulu'/rev;SRC=R/'assets-source/unity-lulu'/rev;REP=R/'review/unity-integration-20261018/lulu'/rev
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'game-lod0';bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu/locomotion-r08'/f'lulu-{label}.blend'));arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
report=[]
for o in [bpy.data.objects['Leg_L'],bpy.data.objects['Leg_R']]:
 side='Left' if o.name=='Leg_L' else 'Right';sign=1 if side=='Left' else -1;originalverts=len(o.data.vertices);o.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.loop_triangles],all_triangles=True);near=tree.find_nearest(Vector((sign*.26,-.05,-.90)));tri=o.data.loop_triangles[near[2]];co=[o.data.vertices[k].co for k in tri.vertices];uvs=[Vector((*o.data.uv_layers[0].data[k].uv,0)) for k in tri.loops];sample=barycentric_transform(near[0],*co,*uvs);orig_tri=[([o.data.vertices[k].co.copy() for k in t.vertices],[o.data.corner_normals[k].vector.copy() for k in t.loops]) for t in o.data.loop_triangles]
 bm=bmesh.new();bm.from_mesh(o.data);result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,-.835),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
 edges=[e for e in bm.edges if e.is_boundary];unused=set(edges);rings=[]
 while unused:
  e=next(iter(unused));unused.remove(e);vs=[e.verts[0],e.verts[1]];current=vs[-1]
  while current!=vs[0]:
   found=next((k for k in current.link_edges if k in unused),None)
   if found is None:break
   unused.remove(found);current=found.other_vert(current)
   if current!=vs[0]:vs.append(current)
  if len(vs)>2:rings.append(vs)
 capfaces=[];newverts=[]
 for ring in rings:
  
  for _ in range(5):
   smooth=[(ring[(i-1)%len(ring)].co+2*v.co+ring[(i+1)%len(ring)].co)/4 for i,v in enumerate(ring)]
   for v,p in zip(ring,smooth):v.co=p
  center=sum((v.co for v in ring),Vector())/len(ring);prev=ring
  for fraction,zlift in [(math.cos(a),.067*math.sin(a)) for a in [math.radians(x) for x in [15,30,45,60,75,85]]]:
   new=[bm.verts.new((center.x+(v.co.x-center.x)*fraction,center.y+(v.co.y-center.y)*fraction,-.835+zlift)) for v in ring];newverts.extend(new)
   for i in range(len(ring)):
    j=(i+1)%len(ring);capfaces.append(bm.faces.new((prev[i],prev[j],new[j],new[i])))
   prev=new
  top=bm.verts.new((center.x,center.y,-.768));newverts.append(top)
  for i in range(len(ring)):capfaces.append(bm.faces.new((prev[i],prev[(i+1)%len(ring)],top)))
 uv=bm.loops.layers.uv.active
 for f in capfaces:
  f.smooth=True
  for l in f.loops:l[uv].uv=(sample.x,sample.y)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 for f in o.data.polygons:f.use_smooth=True
 normals=[]
 for l in o.data.loops:
  v=o.data.vertices[l.vertex_index];default=v.normal.copy()
  if v.co.z<=-.835001:
   hit=tree.find_nearest(v.co);co,no=orig_tri[hit[2]];normal=barycentric_transform(hit[0],*co,*no).normalized();normals.append(tuple(normal))
  else:normals.append(tuple(default))
 o.data.normals_split_custom_set(normals)
 for vg in o.vertex_groups:vg.remove(list(range(len(o.data.vertices))))
 o.vertex_groups[side+'Foot'].add(list(range(len(o.data.vertices))),1,'REPLACE');report.append({'part':o.name,'original_vertices':originalverts,'vertices':len(o.data.vertices),'retained_original_below_z':-.835,'closure_top_z':-.768,'boundary_loops':[len(x) for x in rings],'new_cap_faces':len(capfaces),'uv0_sample':[sample.x,sample.y]})
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=arm;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'lulu-{label}.blend'),compress=True);bpy.ops.export_scene.gltf(filepath=str(OUT/f'lulu-{label}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_anim_slide_to_zero=True,export_skins=True,export_all_influences=False,export_yup=True,export_apply=False)
if label=='game-lod0':
 bpy.ops.export_scene.fbx(filepath=str(OUT/'lulu-game-lod0.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
 m=json.loads((R/'public/models/unity-lulu/locomotion-r08/manifest.json').read_text());m['revision']=rev
 for k in ['model','fbx','native']:m[k]=m[k].replace('locomotion-r08',rev)
 m['status']['technical']='pending_reopen';m['status']['visual']='pending_leg_top_gate_waist_unresolved';m['leg_top_repair']=report;(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(REP/(label+'-leg-top-repair.json')).write_text(json.dumps(report,indent=2));print('REPAIRED',report)
