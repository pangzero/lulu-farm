import bpy,bmesh,json,math,sys,hashlib,importlib.util,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];P=R/'public/models/unity-integration';O=R/'review/unity-integration-20261018/assets';S=R/'assets-source/unity-integration';kind=sys.argv[-1];row=next(x for x in json.loads((P/'manifest.json').read_text())['assets'] if x['id']==kind);out=O/kind/'interface-r04';out.mkdir(parents=True,exist_ok=True);dest=P/'interface-r04';dest.mkdir(exist_ok=True);src=S/'interface-r04';src.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
def bounds(obs):
 pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box];return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
def select(obs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
def export(obs,name):
 select(obs);bpy.ops.export_scene.gltf(filepath=str(dest/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=row['source']);obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];
for ob in obs:
 world=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=world;select([ob]);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
ob=obs[0];lo,hi=bounds(obs);metrics={'input':row['source'],'source_sha256':row['source_sha256'],'original_bounds_zup':{'min':list(lo),'max':list(hi)}}
if kind=='S06':
 # Partition exactly at the two post/gate interfaces, with capped cut planes.
 left=lo.x+(hi.x-lo.x)*.185;right=lo.x+(hi.x-lo.x)*.825;parts=[]
 for name,xlo,xhi in [('left-post',None,left),('gate-leaf',left,right),('right-post',right,None)]:
  cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);cp.name='S06 '+name;bm=bmesh.new();bm.from_mesh(cp.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
  if xlo is not None:bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(xlo,0,0),plane_no=(1,0,0),clear_inner=True)
  if xhi is not None:bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(xhi,0,0),plane_no=(-1,0,0),clear_inner=True)
  boundary=[e for e in bm.edges if e.is_boundary]
  cap=bpy.data.materials.new('S06 warm wood cut cap');cap.diffuse_color=(.55,.245,.095,1);cap.use_nodes=True;bs=next(n for n in cap.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.55,.245,.095,1);bs.inputs['Roughness'].default_value=.86;cp.data.materials.append(cap);filled=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
  for face in filled.get('faces',[]):face.material_index=len(cp.data.materials)-1
  bm.to_mesh(cp.data);bm.free();cp['production']=True
  for v in cp.data.vertices:v.co.z-=lo.z
  if name=='gate-leaf':
   for v in cp.data.vertices:v.co-=Vector((left,0,0))
   cp.location.x=left
  parts.append(cp);export([cp],'S06-'+name)
 bpy.data.objects.remove(ob,do_unlink=True);parts[1].rotation_mode='XYZ';parts[1].rotation_euler.z=math.radians(88);bpy.context.view_layer.update();export(parts,'S06-open-gate');metrics.update({'gate_hinge_zup':[left,0,0],'opening_x':[left,right],'clear_opening_source_units':right-left,'source_height':hi.z-lo.z,'open_angle_degrees':88,'world_scale_for_height_082':.82/(hi.z-lo.z),'clear_opening_at_height_082':(right-left)*.82/(hi.z-lo.z),'note':'Three source-derived capped pieces; static 88-degree open leaf. X = opening width, Blender -Y / glTF +Z = front.'});obs=parts
else:
 # Label source water faces by the visible turquoise surface, not by a fixed height that would remove stones.
 mat=ob.data.materials[0];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=bs.inputs['Base Color'].links[0].from_node;im=tex.image;w,h=im.size;pixels=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4);uv=ob.data.uv_layers.active.data;remove=[]
 for poly in ob.data.polygons:
  q=sum((uv[i].uv for i in poly.loop_indices),Vector((0,0)))/len(poly.loop_indices);r,g,b,_=pixels[min(h-1,int(q.y*h)),min(w-1,int(q.x*w))];
  if b>r*1.5 and g>r*1.5 and b>.16:remove.append(poly.index)
 bm=bmesh.new();bm.from_mesh(ob.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES');bm.to_mesh(ob.data);bm.free();ob.name='E06 source bank without integrated water';ob['production']=True
 # Keep native position and report it, because only scene adapters own vertical plane alignment.
 export([ob],'E06-bank-no-water');metrics.update({'removed_water_faces':len(remove),'remaining_faces':len(ob.data.polygons),'alignment':'Native GLB preserved in this derivative. Preview front is glTF +Z; concave water edge is +Z; grassy rear is -Z. Model is a curved bank wedge, not a parameterized 90-degree grid corner. Requires adapter/soil backing, not blind 1.2-grid corner tiling.','collision':'Use simplified solid bank strips; never high-mesh collider or removed-water bounding box.'})
H.inspection_setup();sc=bpy.context.scene;sc.cycles.samples=8;sc.render.threads_mode='FIXED';sc.render.threads=4;lo,hi=bounds(obs);target=(lo+hi)/2;span=max(hi-lo)*1.45
for g in sc.objects:
 if g.name.startswith('QA ground'):g.location.z=lo.z-.01
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(src/(kind+'.blend')),compress=True);bpy.ops.wm.open_mainfile(filepath=str(src/(kind+'.blend')));obs=[o for o in bpy.context.scene.objects if o.get('production')];sc=bpy.context.scene
for mode in ['material','clay']:
 if mode=='clay':
  gray=H.material('Neutral gray',(.38,.38,.38),.85)
  for ob in obs:ob.data.materials.clear();ob.data.materials.append(gray)
 for view in H.VIEWS:
  d=Vector(H.VIEWS[view]).normalized();sc.camera.location=target+d*30;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=span;sc.render.filepath=str(out/(mode+'-'+view+'.png'));bpy.ops.render.render(write_still=True)
metrics['source_reopened']=True;metrics['user_art']='pending';metrics['visual']='pending_actual_inspection';(out/'metrics.json').write_text(json.dumps(metrics,indent=2));print('INTERFACE_COMPLETE',kind,flush=True)
