"""Four user Meshy seedlings ->14 explicit shared-family microedited derivatives. No native generator."""
import bpy,bmesh,json,math,sys,argparse,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018'
spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
p=argparse.ArgumentParser();p.add_argument('--crop',required=True);p.add_argument('--phase',choices=['build','review'],default='build');p.add_argument('--version',default='meshy-toon-r01');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);c=next(c for c in json.loads((O/'mapping.json').read_text()) if c['id']==a.crop);slug=c['id'];v=a.version;out=O/slug/v;out.mkdir(parents=True,exist_ok=True);source=R/f"assets-source/farm-assets/{c['batch']}/{v}/{slug}-seedling.blend";glb=R/f"public/models/farm-assets/{c['batch']}/{v}/{slug}-seedling.glb";original=R/'public'/c['input']['file'].lstrip('/')
def import_plant(path,height=None):
 bpy.ops.import_scene.gltf(filepath=str(path));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];lo,hi=H.bounds(obs);scale=height/(hi.z-lo.z) if height else 1;mid=(lo+hi)/2
 for ob in obs:
  world=ob.matrix_world.copy();ob.parent=None
  for x in ob.data.vertices:x.co=(world@x.co-Vector((mid.x,mid.y,lo.z)))*scale
  ob.matrix_world=Matrix.Identity(4);ob['production']=True
 return obs

def frame(target,height,view='quarter',farm=False):
 s=bpy.context.scene;t=Vector(target);d=Vector((math.cos(math.radians(50))/2**.5,-math.cos(math.radians(50))/2**.5,math.sin(math.radians(50)))) if farm else Vector(H.VIEWS[view]).normalized();s.camera.data.ortho_scale=height*(1280/720 if farm else 1);s.camera.location=t+d*30;s.camera.rotation_euler=(t-s.camera.location).to_track_quat('-Z','Y').to_euler()
def picture(path,target,height,view='quarter',farm=False):
 frame(target,height,view,farm);bpy.context.scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
def topo(obs):
 rows=[]
 for ob in obs:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update();rows.append({'name':ob.name,'welded_boundary':sum(e.is_boundary for e in bm.edges),'welded_nonmanifold':sum(not e.is_manifold for e in bm.edges),'zero_area_1e14':sum(f.calc_area()<1e-14 for f in bm.faces),'finite_normals':all(all(math.isfinite(x) for x in vert.normal) for vert in bm.verts)});bm.free()
 return rows
if a.phase=='build':
 assert not source.exists() and not glb.exists(),'Protect existing revision';bpy.ops.wm.read_factory_settings(use_empty=True);obs=import_plant(original,c['height']);original_bounds=H.bounds(obs)
 for ob in obs:
  for vert in ob.data.vertices:
   x,y,z=vert.co;t=max(0,min(1,z/c['height']));w=t*t*(3-2*t);angle=c['twist']*w
   xx=x*(1+(c['width']-1)*w);yy=y*(1+(c['depth']-1)*w)
   vert.co=(xx*math.cos(angle)-yy*math.sin(angle),xx*math.sin(angle)+yy*math.cos(angle),z)
  ob.data.update();ob.name=f"{slug} shared {c['family']} Meshy microedit";ob['mapped_family']=c['family'];ob['mapping_note']=c['mapping_note'];ob['original_sha256']=c['input']['sha256']
  for mat in ob.data.materials:
   if not mat or not mat.use_nodes:continue
   nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
   for socket,value in [('Metallic',0),('Roughness',.84),('Specular IOR Level',.25)]:
    for link in list(bs.inputs[socket].links):nt.links.remove(link)
    bs.inputs[socket].default_value=value
   for n in nt.nodes:
    if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.14
    if n.type=='TEX_IMAGE' and n.image and any(l.to_node==bs and l.to_socket.name=='Base Color' for l in n.outputs['Color'].links):img=bpy.data.images.load(str(out/'basecolor.png'),check_existing=True);img.pack();n.image=img
  weld=ob.modifiers.new('Weld coincident positions, preserve UV loops','WELD');weld.merge_threshold=1e-7
  if v=='meshy-toon-r01':
   dec=ob.modifiers.new('Seedling resource reduction - inspect silhouette','DECIMATE');dec.ratio=min(1,35000/c['input']['triangles']);dec.use_collapse_triangulate=True
 for img in bpy.data.images:
  if img.size[0]>1024 or img.size[1]>1024:img.scale(1024,1024);img.pack()
 lo,hi=H.bounds(obs);lo=Vector(tuple(min(lo[i],original_bounds[0][i]) for i in range(3)));hi=Vector(tuple(max(hi[i],original_bounds[1][i]) for i in range(3)));settings={'target':list((lo+hi)/2),'height':max(hi-lo)*1.4,'world_height':c['height'],'no_per_plant_height_normalization':True};(O/slug/'review-settings.json').write_text(json.dumps(settings,indent=2))
 H.inspection_setup();frame(settings['target'],settings['height']);source.parent.mkdir(parents=True,exist_ok=True);glb.parent.mkdir(parents=True,exist_ok=True)
 for ob in bpy.context.scene.objects:ob.select_set(False)
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
 m=H.check_glb(glb);m.update({'crop':slug,'name':c['name'],'code':c['code'],'batch':c['batch'],'family':c['family'],'version':v,'source':str(source.relative_to(R)),'source_sha256':H.sha(source),'glb':str(glb.relative_to(R)),'original_filename':c['input']['original_filename'],'original_sha256':c['input']['sha256'],'mapping_note':c['mapping_note'],'topology':topo([o for o in bpy.context.scene.objects if o.type=='MESH']),'user_art':'pending','device':'not_tested'});(out/'metrics.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
 bpy.ops.wm.open_mainfile(filepath=str(source));obs=[o for o in bpy.context.scene.objects if o.get('production')];assert obs;(out/'source-reopen.json').write_text(json.dumps({'source_reopened':True,'sha256':H.sha(source),'objects':len(obs),'modifiers':[[x.type for x in ob.modifiers] for ob in obs]},indent=2));picture(out/'material-quarter.png',settings['target'],settings['height']);print('COMPLETE_BUILD',slug,flush=True)
else:
 settings=json.loads((O/slug/'review-settings.json').read_text())
 for original_mode in [True,False]:
  folder=O/slug/('original' if original_mode else v);folder.mkdir(parents=True,exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True);obs=import_plant(original,c['height']) if original_mode else import_plant(glb);H.inspection_setup()
  for mode in ['material','clay']:
   if mode=='clay':
    gray=H.material('Neutral geometry gray',(.38,.38,.38),.85)
    for ob in obs:ob.data.materials.clear();ob.data.materials.append(gray)
   for view in H.VIEWS:picture(folder/f'{mode}-{view}.png',settings['target'],settings['height'],view)
 # Planting from actual exported candidate, readonly official Lulu.
 bpy.ops.wm.read_factory_settings(use_empty=True);obs=import_plant(glb);plants=list(obs)
 for ob in obs:
  for y in [-1,0,1]:
   for x in [-1,0,1]:
    if not(x or y):continue
    cp=ob.copy();cp.data=ob.data;bpy.context.collection.objects.link(cp);cp.location+=Vector((x*1.2,y*1.2,0));plants.append(cp)
 H.inspection_setup();soilmat=H.material('Separate QA soil',(.33,.20,.10),1)
 def soil(nx,ny):
  for ob in list(bpy.context.scene.objects):
   if ob.get('qa_soil'):bpy.data.objects.remove(ob,do_unlink=True)
  for y in range(ny):
   for x in range(nx):
    bpy.ops.mesh.primitive_cube_add(size=1,location=((x-(nx-1)/2)*1.2,(y-(ny-1)/2)*1.2,-.035));ob=bpy.context.object;ob.dimensions=(1.14,1.14,.07);ob.data.materials.append(soilmat);ob['qa_soil']=True
  for ob in bpy.context.scene.objects:
   if ob.name.startswith('QA ground'):ob.location.z=-.071
 soil(3,3);before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(R/'public/models/lulu-official-v1.glb'));lroots=[o for o in bpy.context.scene.objects if o not in before and o.parent is None]
 for ob in lroots:ob.scale*=.6313689262131015
 bpy.context.view_layer.update();lm=[o for o in bpy.context.scene.objects if o not in before and o.type=='MESH'];lo,hi=H.bounds(lm)
 for ob in lroots:ob.location+=Vector((2.5-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
 picture(out/'planting-3x3-lulu.png',(.45,0,.5),6.2)
 soil(12,8)
 for ob in plants:ob.location+=Vector((.6,.6,0))
 bpy.context.scene.render.resolution_x=1280;bpy.context.scene.render.resolution_y=720;picture(out/'farm-distance.png',(0,0,0),14.1,farm=True)
 print('COMPLETE_REVIEW',slug,flush=True)
