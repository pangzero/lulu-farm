"""Independent mature Meshy editing, resource derivatives, and actual GLB review.
No seedling or historical crop generator is executed. All writes are revisioned.
"""
import bpy,bmesh,json,sys,math,importlib.util,argparse
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018'
spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
p=argparse.ArgumentParser();p.add_argument('--crop',required=True);p.add_argument('--mode',choices=['toon','game','original','inspect','plant'],required=True);p.add_argument('--version',default='toon-r01');p.add_argument('--parent-version',default='toon-r01');p.add_argument('--render',choices=['quick','all','detail','none'],default='quick');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
e=next(x for x in json.loads((O/'scope.json').read_text()) if x['id']==a.crop);slug=a.crop;batch=e['batch'];v='original' if a.mode=='original' else a.version
out=O/slug/v;out.mkdir(parents=True,exist_ok=True)
source=R/f'assets-source/farm-assets/{batch}/{v}/{slug}-mature.blend';glb=R/f'public/models/farm-assets/{batch}/{v}/{slug}-mature.glb';original=R/'public'/e['file'].lstrip('/')
profile=json.loads((O/'profiles.json').read_text())[slug]

def import_model(path,scale=1):
 before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(path));obs=[o for o in bpy.context.scene.objects if o not in before];roots=[o for o in obs if o.parent is None]
 for o in roots:o.scale*=scale
 meshes=[o for o in obs if o.type=='MESH'];lo,hi=H.bounds(meshes);shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
 for o in roots:o.location+=shift
 bpy.context.view_layer.update()
 return roots,meshes

def cam(target,height,view='quarter',farm=False):
 s=bpy.context.scene;target=Vector(target);d=Vector((math.cos(math.radians(50))/2**.5,-math.cos(math.radians(50))/2**.5,math.sin(math.radians(50)))) if farm else Vector(H.VIEWS[view]).normalized()
 s.camera.data.ortho_scale=height*(1280/720 if farm else 1);s.camera.location=target+d*30;s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()

def picture(name,target,height,view='quarter',farm=False):
 cam(target,height,view,farm);bpy.context.scene.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)

def audit_objects(objects):
 result=[]
 for o in objects:
  bm=bmesh.new();bm.from_mesh(o.data);raw=sum(x.is_boundary for x in bm.edges);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update()
  result.append({'mesh':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'raw_uv_split_boundaries':raw,'welded_boundary_edges':sum(x.is_boundary for x in bm.edges),'welded_nonmanifold_edges':sum(not x.is_manifold for x in bm.edges),'zero_area_faces_1e12':sum(f.calc_area()<1e-12 for f in bm.faces),'finite_normals':all(all(math.isfinite(c) for c in vert.normal) for vert in o.data.vertices),'duplicate_faces_after_weld':len(bm.faces)-len({tuple(sorted(x.index for x in f.verts)) for f in bm.faces})});bm.free()
 return result

def material_edit(objects):
 for mat in {m for o in objects for m in o.data.materials if m}:
  if not mat.use_nodes:continue
  nt=mat.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
  for socket,value in [('Metallic',0),('Roughness',profile['leaf_roughness']),('Specular IOR Level',.28)]:
   for link in list(p.inputs[socket].links):nt.links.remove(link)
   p.inputs[socket].default_value=value
  for n in nt.nodes:
   if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=profile['normal_strength']
   if n.type=='TEX_IMAGE' and n.image and any(l.to_node==p and l.to_socket.name=='Base Color' for l in n.outputs['Color'].links):
    img=bpy.data.images.load(str(out/'basecolor.png'),check_existing=True);img.pack();n.image=img
  img=bpy.data.images.load(str(out/'roughness.png'),check_existing=True);img.colorspace_settings.name='Non-Color';img.pack();n=nt.nodes.new('ShaderNodeTexImage');n.name='Species organ roughness';n.image=img;nt.links.new(n.outputs['Color'],p.inputs['Roughness']);mat.name=f'{slug} softened leaves and distinct organ surface'

if a.mode in ['toon','game']:
 assert not source.exists() and not glb.exists(),'Never overwrite a revision'
 for x in [source.parent,glb.parent]:x.mkdir(parents=True,exist_ok=True)
 if a.mode=='toon':
  assert H.sha(original)==e['sha256'];bpy.ops.wm.read_factory_settings(use_empty=True);roots,objects=import_model(original,.47);material_edit(objects)
  for o in objects:o['production']=True;o['source_sha256']=e['sha256'];o.name=slug+' mature Meshy editable import'
  H.inspection_setup();lo,hi=H.bounds(objects);settings={'camera_target':list((lo+hi)/2),'ortho_scale':max(hi-lo)*1.35,'common_import_scale':.47,'lights':'B01 fixed','exposure':0,'resolution':[768,768]};(O/slug/'review-settings.json').write_text(json.dumps(settings,indent=2))
 else:
  parent=R/f'assets-source/farm-assets/{batch}/{a.parent_version}/{slug}-mature.blend';bpy.ops.wm.open_mainfile(filepath=str(parent));objects=[o for o in bpy.context.scene.objects if o.get('production')]
  for o in objects:
   weld=o.modifiers.new('Weld coincident positions before collapse - retain UV loops','WELD');weld.merge_threshold=1e-7
   dec=o.modifiers.new('Species-specific silhouette-preserving resource candidate','DECIMATE');dec.ratio=profile['optimization_ratio'];dec.use_collapse_triangulate=True
  for img in bpy.data.images:
   if img.size[0]>2048 or img.size[1]>2048:img.scale(2048,2048);img.pack()
 for o in bpy.context.scene.objects:o.select_set(False)
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
 m=H.check_glb(glb);m.update({'crop':slug,'name':e['name'],'batch':batch,'stage':'mature','version':v,'source':str(source.relative_to(R)),'source_sha256':H.sha(source),'glb':str(glb.relative_to(R)),'source_kind':'Meshy editable imported derivative','original_source_name':e.get('original_name',e.get('source_name')),'input_glb':e['file'],'input_sha256':e['sha256'],'profile':profile,'geometry_changed':a.mode=='game','user_art_status':'pending','target_device':'not_tested','roundtrip_topology':audit_objects([o for o in bpy.context.scene.objects if o.type=='MESH'])})
 (out/'metrics.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))

if a.mode in ['toon','game','inspect']:
 bpy.ops.wm.open_mainfile(filepath=str(source));objects=[o for o in bpy.context.scene.objects if o.get('production')];settings=json.loads((O/slug/'review-settings.json').read_text());assert objects
 (out/'source-reopen.json').write_text(json.dumps({'source_reopened':True,'source_sha256':H.sha(source),'production_objects':len(objects),'editable_modifiers':{o.name:[m.type for m in o.modifiers] for o in objects},'settings':settings},indent=2))
elif a.mode=='original':
 bpy.ops.wm.read_factory_settings(use_empty=True);roots,objects=import_model(original,.47);H.inspection_setup();settings=json.loads((O/slug/'review-settings.json').read_text())
 (out/'provenance.json').write_text(json.dumps({'source_file':e['file'],'original_sha256':H.sha(original),'scale':.47,'settings':settings},indent=2))

if a.mode!='plant' and a.render!='none':
 modes=['material'] if a.render=='quick' else ['material','clay'];views=[] if a.render=='detail' else ['quarter'] if a.render=='quick' else list(H.VIEWS)
 for mode in modes:
  if mode=='clay':
   gray=H.material('Neutral geometry inspection gray',(.38,.38,.38),.85)
   for o in objects:o.data.materials.clear();o.data.materials.append(gray)
  for view in views:picture(f'{mode}-{view}.png',settings['camera_target'],settings['ortho_scale'],view)
  if a.render in ['all','detail']:
   detail=list(settings['camera_target']);detail[2]*={'sunflower':1.5,'wheat':1.5,'rose':1.65,'cauliflower':1.25,'tulip':1.55,'lettuce':1.15}.get(slug,1)
   picture(f'{mode}-detail.png',detail,settings['ortho_scale']*.48)

if a.mode=='plant':
 bpy.ops.wm.read_factory_settings(use_empty=True);roots,objects=import_model(glb)
 copies=[]
 for o in objects:
  world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
  for y in [-1,0,1]:
   for x in [-1,0,1]:
    if x==0 and y==0:continue
    d=o.copy();d.data=o.data;bpy.context.collection.objects.link(d);d.location+=Vector((x*1.2,y*1.2,0));copies.append(d)
 H.inspection_setup();soilmat=H.material('QA soil separate from plant',(.33,.20,.10),1)
 def soil(nx,ny):
  for o in list(bpy.context.scene.objects):
   if o.get('qa_soil'):bpy.data.objects.remove(o,do_unlink=True)
  for y in range(ny):
   for x in range(nx):
    bpy.ops.mesh.primitive_cube_add(size=1,location=((x-(nx-1)/2)*1.2,(y-(ny-1)/2)*1.2,-.035));o=bpy.context.object;o.name='QA soil only';o.dimensions=(1.14,1.14,.07);o.data.materials.append(soilmat);o['qa_soil']=True
  for o in bpy.context.scene.objects:
   if o.type=='MESH' and o.name.startswith('QA ground'):o.location.z=-.071
 soil(3,3);lp=R/'public/models/lulu-official-v1.glb';lroots,lmeshes=import_model(lp,.6313689262131015)
 for o in lroots:o.location.x+=2.5
 picture('planting-3x3-lulu.png',(.45,0,.5),6.2)
 soil(12,8)
 for o in objects+copies:o.location+=Vector((.6,.6,0))
 bpy.context.scene.render.resolution_x=1280;bpy.context.scene.render.resolution_y=720;picture('farm-distance.png',(0,0,0),14.1,farm=True)
 (out/'planting-settings.json').write_text(json.dumps({'input_exported_glb_sha256':H.sha(glb),'plant_scale':1,'plants':9,'grid_cell':1.2,'near_resolution':[768,768],'near_ortho_height':6.2,'farm_resolution':[1280,720],'farm_ortho_height':14.1,'farm_ortho_width':14.1*1280/720,'farm_azimuth':45,'farm_elevation':50,'farm_cells':[12,8],'lulu_file':str(lp.relative_to(R)),'lulu_sha256':H.sha(lp),'lulu_instance_scale':.6313689262131015,'soil_exported':False},indent=2))
print('COMPLETE',slug,a.mode,v,flush=True)
