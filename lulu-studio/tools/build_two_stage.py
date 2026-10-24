"""Native authored seedling surfaces and independently saved Meshy derivatives.
No historical production builder is executed. Review helpers are read from the
guarded, independent route-study module; all new outputs have distinct paths.
"""
import bpy,bmesh,sys,math,json,hashlib,importlib.util,argparse
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'review/crop-two-stage-20261018'
spec=importlib.util.spec_from_file_location('study_helpers',ROOT/'tools/build_seedling_study.py')
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
CAT=json.loads((ROOT/'public/models/crops-meshy/manifest.json').read_text())
CROPS={x['id']:x for x in CAT['crops'] if x.get('file')}
args=argparse.ArgumentParser();args.add_argument('--crop',required=True);args.add_argument('--stage',choices=['seedling','mature'],required=True);args.add_argument('--revision',default='r01');args.add_argument('--render',choices=['quick','all','none'],default='quick');args.add_argument('--review-only',action='store_true')
A=args.parse_args(sys.argv[sys.argv.index('--')+1:]);slug=A.crop;stage=A.stage;rev=A.revision
batch=('B08' if int(CROPS[slug]['code'][1:])<=8 else 'B09') if stage=='seedling' else CROPS[slug]['batch']
version=('native-' if stage=='seedling' else 'toon-')+rev
SOURCE=ROOT/f'assets-source/farm-assets/{batch}/{version}/{slug}-{stage}.blend'
GLB=ROOT/f'public/models/farm-assets/{batch}/{version}/{slug}-{stage}.glb'
OUT=REVIEW/f'{slug}/{stage}/{rev}'
for p in [SOURCE.parent,GLB.parent,OUT]:p.mkdir(parents=True,exist_ok=True)

def tube(name,points,radius,mat):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=16;c.bevel_depth=radius;c.bevel_resolution=3;c.use_fill_caps=True
 s=c.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for i,(b,p) in enumerate(zip(s.bezier_points,points)):
  b.co=p;b.handle_left_type=b.handle_right_type='AUTO';b.radius=1-.78*(i/max(1,len(points)-1))**3
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);o['production']=True;return o

def leaf(name,start,end,width,kind='round',color=(.22,.46,.065),curl=.012,twist=0):
 """Swept broad surface in a local blade plane, with integrated shallow veins.
 Width, surface bulge, petiole transition and edge contour are separately authored.
 """
 start,end=Vector(start),Vector(end);axis=end-start
 side=Vector((1,twist,0));side=(side-axis.normalized()*side.dot(axis.normalized())).normalized()
 if side.length<.1:side=Vector((0,1,0))
 normal=axis.normalized().cross(side).normalized()
 if normal.y>0:normal=-normal
 vs=[];cols=[];nu,nv=32,16
 pet=.16 if kind not in ['strap','tulip'] else 0
 for i in range(nu+1):
  t=i/nu;s=max(0,(t-pet)/(1-pet));blade=math.sin(math.pi*s)
  profile=max(.006,blade**(.57 if kind=='round' else .8))
  if kind=='lobed':profile*=.88+.12*math.cos(s*math.pi*5.3+.3)
  if kind=='round':profile*=1+.045*math.sin(s*math.pi*7)
  if kind=='heart':profile*=1.18-.45*s
  if kind=='ruffle':profile*=1+.12*math.sin(s*math.pi*5)
  if kind=='strap':profile=math.sin(math.pi*t)**.65
  if kind=='tulip':profile=math.sin(math.pi*t)**.7
  w=(.0025*(1-t/pet)+.003*t/pet) if t<pet else max(.0004,width*profile)
  center=start+axis*t
  center+=normal*(curl*math.sin(math.pi*t)-curl*.65*t*t)
  center+=side*(.008*math.sin(math.pi*t)*math.sin(t*math.pi*.7))
  for j in range(nv+1):
   v=-1+2*j/nv
   # Low shallow grooves, never floating vein meshes. Branches fan from midrib.
   vein=math.exp(-(v/.075)**2)
   if kind not in ['strap','tulip']:
    for origin in [.22,.38,.54,.7]:
     d=s-origin-.24*abs(v)
     vein+=.55*math.exp(-(d/.018)**2)*(1-abs(v))
   else:vein+=.25*math.exp(-((abs(v)-.54)/.05)**2)
   swell=.028*blade*(1-v*v)
   wave=(.006 if kind in ['round','ruffle'] else .003)*math.sin(s*math.pi*5+v)*blade*v*v
   pos=center+side*(w*v)+normal*(swell+wave+.0014*min(1,vein)*blade)
   vs.append(tuple(pos));shade=(.74+.14*blade+.14*(1-v*v))
   cols.append(tuple(min(1,c*shade+.055*min(1,vein)*blade) for c in color)+(1,))
 faces=[]
 for i in range(nu):
  for j in range(nv):
   p=i*(nv+1)+j;faces.append((p,p+nv+1,p+nv+2,p+1))
 o=H.mesh_object(name,vs,faces,LEAFMAT);o['production']=True
 attr=o.data.color_attributes.new(name='LeafColor',type='FLOAT_COLOR',domain='POINT')
 for d,c in zip(attr.data,cols):d.color=c
 sub=o.modifiers.new('Rounded authored leaf contour','SUBSURF');sub.levels=1
 solid=o.modifiers.new('Editable substantial rounded leaf thickness','SOLIDIFY');solid.thickness=.005 if kind not in ['strap','tulip'] else .003;solid.offset=0
 bevel=o.modifiers.new('Soft leaf rim','BEVEL');bevel.width=.0014;bevel.segments=3;bevel.limit_method='ANGLE'
 o['leaf_kind']=kind;o['integrated_veins']=True
 return o

def arched(name,angle,height,reach,width,color):
 """Three-dimensional monocot blade with a smoothly changing local frame."""
 az=math.radians(angle);radial=Vector((math.cos(az),math.sin(az),0));side=Vector((-math.sin(az),math.cos(az),0));vs=[];colors=[];nu,nv=64,16
 for i in range(nu+1):
  t=i/nu;w=max(.0003,width*math.sin(math.pi*t)**.65)
  center=radial*(reach*t*t);center.z=.012+height*math.sin(t*math.pi*.78)
  tangent=radial*(2*reach*t)+Vector((0,0,height*math.pi*.78*math.cos(t*math.pi*.78)));normal=side.cross(tangent).normalized()
  for j in range(nv+1):
   v=2*j/nv-1;pos=center+side*w*v+normal*(.009*math.sin(math.pi*t)*(v*v-.2)+.001*math.exp(-(v/.1)**2))
   vs.append(tuple(pos));colors.append(tuple(c*(.95+.07*(1-v*v))+.012*math.exp(-(v/.12)**2) for c in color)+(1,))
 faces=[(i*(nv+1)+j,i*(nv+1)+j+1,(i+1)*(nv+1)+j+1,(i+1)*(nv+1)+j) for i in range(nu) for j in range(nv)]
 o=H.mesh_object(name,vs,faces,LEAFMAT);o['production']=True
 at=o.data.color_attributes.new(name='LeafColor',type='FLOAT_COLOR',domain='POINT')
 for d,c in zip(at.data,colors):d.color=c
 sol=o.modifiers.new('Leaf sheath thickness','SOLIDIFY');sol.thickness=.004;sol.offset=0
 be=o.modifiers.new('Rounded strap edges','BEVEL');be.width=.0012;be.segments=3;be.limit_method='ANGLE'

def make_seedling():
 global LEAFMAT
 bpy.ops.wm.read_factory_settings(use_empty=True)
 LEAFMAT=H.material('Juvenile leaf - portable vertex colour',(.22,.46,.07),.78)
 nodes=LEAFMAT.node_tree.nodes;v=nodes.new('ShaderNodeVertexColor');v.layer_name='LeafColor';LEAFMAT.node_tree.links.new(v.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
 stemmat=H.material('Soft green attached crown',(.27,.44,.075),.8)
 g=(.22,.46,.06);light=(.33,.53,.095)
 if slug=='cabbage':
  tube('Short cabbage crown',[(0,0,0),(0,0,.04),(.005,.006,.083)],.012,stemmat)
  leaf('Low round cotyledon left',(-.002,0,.025),(-.09,-.055,.055),.033,'oval',color=light,twist=.8)
  leaf('Low round cotyledon right',(.002,0,.028),(.095,.025,.063),.035,'oval',color=light,twist=-.7)
  leaf('Broad true leaf left',(0,0,.05),(-.11,-.02,.195),.067,color=g,curl=.043,twist=1.2)
  leaf('Broad upright true leaf right',(0,.005,.055),(.085,.073,.265),.08,color=g,curl=.037,twist=-.8)
  leaf('Small emerging centre',(.002,-.006,.064),(.01,-.052,.145),.029,color=light,curl=.014,twist=.7)
 elif slug=='tomato':
  tube('Branched juvenile stem',[(0,0,0),(.002,0,.11),(-.005,.003,.2)],.009,stemmat)
  leaf('Narrow cotyledon left',(0,0,.035),(-.10,-.042,.072),.018,'oval',color=light,twist=.7)
  leaf('Narrow cotyledon right',(0,0,.04),(.09,.035,.078),.017,'oval',color=light,twist=-.6)
  leaf('Rounded lobed true leaf left',(.001,0,.115),(-.13,.055,.255),.054,'lobed',g,.034,1.1)
  leaf('Rounded lobed true leaf right',(0,0,.13),(.13,-.04,.235),.052,'lobed',g,.036,-1.3)
  leaf('Upright lobed new leaf',(0,.004,.19),(.025,.065,.35),.033,'lobed',light,.025,.8)
 elif slug=='corn':
  tube('Young overlapping sheath',[(0,0,0),(.002,0,.06),(0,.004,.14)],.013,stemmat)
  arched('First arched corn blade',167,.35,.18,.044,g)
  arched('Second arched corn blade',25,.27,.16,.041,light)
  vs=[];fs=[]
  for i in range(33):
   t=i/32;r=(.013+.008*math.sin(math.pi*t))*(1-.96*t**5);opening=2.4-1.65*t*t
   for j in range(17):
    a=(j/16*2-1)*opening
    vs.append((r*math.sin(a)+.025*t*t,r*(1-math.cos(a))+.004,.06+.34*t))
  fs=[(i*17+j,i*17+j+1,(i+1)*17+j+1,(i+1)*17+j) for i in range(32) for j in range(16)]
  o=H.mesh_object('Curled emerging corn sheath',vs,fs,stemmat);o['production']=True
  sol=o.modifiers.new('Rolled leaf thickness','SOLIDIFY');sol.thickness=.003;sol.offset=0
 else:raise ValueError('Gate first: other species not authorized for build until inspected')
 return [o for o in bpy.context.scene.objects if o.get('production')]

def make_mature():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 original=ROOT/'public'/CROPS[slug]['file'].lstrip('/')
 assert H.sha(original)==CROPS[slug]['sha256']
 bpy.ops.import_scene.gltf(filepath=str(original));objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
 # Keep mature geometry and UVs; modify a separate packed colour map and PBR inputs.
 strength={'cabbage':.42,'tomato':.22,'corn':.28}.get(slug,.25)
 for mat in list(bpy.data.materials):
  if not mat.use_nodes:continue
  p=mat.node_tree.nodes.get('Principled BSDF')
  if not p:continue
  for socket,value in [('Metallic',0),('Roughness',.82),('Specular IOR Level',.22)]:
   for link in list(p.inputs[socket].links):mat.node_tree.links.remove(link)
   p.inputs[socket].default_value=value
  for n in mat.node_tree.nodes:
   if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.28
  for n in mat.node_tree.nodes:
   if n.type!='TEX_IMAGE' or not n.image:continue
   if not any(l.to_node==p and l.to_socket.name=='Base Color' for l in n.outputs['Color'].links):continue
   old=n.image;w,h=old.size;pix=np.empty(w*h*4,dtype=np.float32);old.pixels.foreach_get(pix);pix=pix.reshape(h,w,4)
   rgb=pix[:,:,:3];green=(rgb[:,:,1]>rgb[:,:,0]*1.035)&(rgb[:,:,1]>rgb[:,:,2]*1.3)
   lum=rgb.max(axis=2);green_level=np.percentile(lum[green],45) if green.any() else .4
   # Reduce contrast of bright veins only within greens; hue and boundary retained.
   factor=1-strength*np.clip((lum-green_level)/max(.1,1-green_level),0,1)
   rgb[green]*=factor[green,None]
   rgb[:]=np.clip(rgb*.98+.012,0,1)
   prepared=OUT/f'{slug}-cartoon-basecolor.png'
   if rev!='r01' and prepared.exists():
    img=bpy.data.images.load(str(prepared));img.pack();n.image=img
   else:
    img=bpy.data.images.new(f'{slug} cartoon basecolour {rev}',width=w,height=h,alpha=True)
    img.pixels.foreach_set(pix.ravel());img.filepath_raw=str(prepared);img.file_format='PNG';img.save();img.pack();n.image=img
  roughmap=OUT/f'{slug}-roughness.png'
  if roughmap.exists():
   rough=bpy.data.images.load(str(roughmap));rough.colorspace_settings.name='Non-Color';rough.pack();node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=rough
   mat.node_tree.links.new(node.outputs['Color'],p.inputs['Roughness']);p.inputs['Specular IOR Level'].default_value=.28
  mat.name=f'{slug} cartoon matte {rev}'
 for o in objects:o['production']=True
 return objects

def normalize(objects):
 if stage=='mature':
  # Scale the complete imported hierarchy once, matching current preview .47.
  roots=[o for o in bpy.context.scene.objects if o.parent is None]
  for o in roots:o.scale*=.47
 lo,hi=H.bounds(objects);offset=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
 for o in [o for o in bpy.context.scene.objects if o.parent is None]:o.location+=offset

def camera(view,target,scale):
 s=bpy.context.scene;s.camera.data.ortho_scale=scale;s.camera.location=target+Vector(H.VIEWS[view]).normalized()*7;s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()

def export_native_clean(objects):
 # Bake only temporary export copies. Keep all authored editable surfaces in source.
 copies=[];report=[];dep=bpy.context.evaluated_depsgraph_get()
 for source in objects:
  mesh=bpy.data.meshes.new_from_object(source.evaluated_get(dep),preserve_all_data_layers=True,depsgraph=dep)
  bm=bmesh.new();bm.from_mesh(mesh)
  before=[len(bm.verts),len(bm.faces)]
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
  bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-5)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY')
  bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-6)
  report.append({'object':source.name,'before_vertices_faces':before,'after_vertices_faces':[len(bm.verts),len(bm.faces)],'boundary_edges':sum(e.is_boundary for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)})
  bm.to_mesh(mesh);bm.free();mesh.update()
  copy=bpy.data.objects.new(source.name+' export',mesh);bpy.context.collection.objects.link(copy);copy.matrix_world=source.matrix_world;copies.append(copy)
 for o in bpy.context.scene.objects:o.select_set(False)
 for o in copies:o.select_set(True)
 bpy.context.view_layer.objects.active=copies[0]
 bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
 for o in copies:bpy.data.objects.remove(o,do_unlink=True)
 (OUT/'export-cleanup.json').write_text(json.dumps({'distance_thresholds':[1e-7,1e-5,1e-6],'source_editable_modifiers_preserved':True,'objects':report},indent=2))

if not A.review_only:
 assert not SOURCE.exists() and not GLB.exists(),'Revision exists; save a new revision'
 objects=make_seedling() if stage=='seedling' else make_mature();normalize(objects)
 for o in bpy.context.scene.objects:o.select_set(False)
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 if stage=='seedling' and rev=='r03':export_native_clean(objects)
 else:bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
 H.inspection_setup();bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE),compress=True)
 m=H.check_glb(GLB);m.update({'crop':slug,'stage':stage,'batch':batch,'version':version,'source':str(SOURCE.relative_to(ROOT)),'source_sha256':H.sha(SOURCE),'glb':str(GLB.relative_to(ROOT)),'input_sha256':CROPS[slug]['sha256'] if stage=='mature' else None,'source_kind':'native_authored' if stage=='seedling' else 'meshy_cartoon_derivative','user_art_status':'pending','target_device':'not_tested','geometry_changed':stage=='seedling'})
 (OUT/'metrics.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));objects=[o for o in bpy.context.scene.objects if o.get('production')];assert objects
lo,hi=H.bounds(objects);target=(lo+hi)/2;scale=max(hi.z-lo.z,hi.x-lo.x,hi.y-lo.y)*1.35
if stage=='seedling':scale=.55;target=Vector((0,0,.2))
if A.render!='none':
 views=['quarter'] if A.render=='quick' else list(H.VIEWS)
 for mode in (['material'] if A.render=='quick' else ['material','clay']):
  if mode=='clay':
   gray=H.material('Neutral clay',(.38,.38,.38),.85)
   for o in objects:o.data.materials.clear();o.data.materials.append(gray)
  for view in views:
   camera(view,target,scale);bpy.context.scene.render.filepath=str(OUT/f'{mode}-{view}.png');bpy.ops.render.render(write_still=True)
(OUT/'source-reopen.json').write_text(json.dumps({'source_reopened':True,'objects':len(objects),'camera_target':list(target),'ortho_scale':scale,'source_preserved':H.sha(SOURCE)},indent=2))
print('COMPLETE',slug,stage,version,flush=True)
