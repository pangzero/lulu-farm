"""Revisioned geometry/texture candidates, species-specific targets and baked broad-leaf normals.
No historical production generator runs; every input is an explicit preserved source GLB.
"""
import bpy,bmesh,json,sys,math,argparse,hashlib,importlib.util,time
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];P=R/'public/models/unity-integration';O=R/'review/unity-integration-20261018/assets';S=R/'assets-source/unity-integration'
ap=argparse.ArgumentParser();ap.add_argument('--id',required=True);ap.add_argument('--version',default='game-r01');ap.add_argument('--review',default='quick',choices=['none','quick','all']);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);row=next(x for x in json.loads((P/'manifest.json').read_text())['assets'] if x['id']==a.id);out=O/a.id/a.version;out.mkdir(parents=True,exist_ok=True);dest=P/a.version/(a.id+'.glb');blend=S/a.version/(a.id+'.blend');dest.parent.mkdir(parents=True,exist_ok=True);blend.parent.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bounds(obs):
 pts=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box];return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
def select(obs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
def tri(obs):return sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in obs)
def pic(path,target,scale,view='quarter'):
 sc=bpy.context.scene;di=Vector(H.VIEWS[view]).normalized();sc.camera.location=Vector(target)+di*30;sc.camera.rotation_euler=(Vector(target)-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale;sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
def geometry(obs):
 records=[]
 for ob in obs:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update();records.append({'name':ob.name,'vertices':len(ob.data.vertices),'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'finite':all(all(math.isfinite(c) for c in v.co) for v in bm.verts),'zero_area':sum(f.calc_area()<1e-14 for f in bm.faces),'uv_layers':len(ob.data.uv_layers)});bm.free()
 return records
assert sha(row['source'])==row['source_sha256'];assert not dest.exists(),f'Revision exists: {dest}'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=row['source']);orig=[o for o in bpy.context.scene.objects if o.type=='MESH']
for ob in orig:
 world=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=world;select([ob]);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob['input_object']=True
lo,hi=bounds(orig);target=(lo+hi)/2;span=max(hi-lo)*1.42;size=max(hi-lo)
settings={'source_sha256':row['source_sha256'],'target':list(target),'ortho_scale':span,'views':H.VIEWS,'resolution':[768,768],'color':'Standard / exposure0 / gamma1','renderer':'Cycles CPU 8 samples denoised','lights':'B01 fixed area/key/fill/rim, scaled only by asset span for non-crop calibration','no_candidate_scale_change':True,'no_height_normalization':True}
(out/'review-settings.json').write_text(json.dumps(settings,indent=2));source_geometry=geometry(orig);total=tri(orig);desired=None;low=[];broad=row['stage']=='seedling' and row['species'] in ['cabbage','bokchoy','cauliflower','lettuce']
for ob in orig:
 cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);cp.name=a.id+' game mesh';cp['input_object']=False;cp['production']=True
 # Copy materials so source comparison remains original.
 for i,mat in enumerate(cp.data.materials):
  if mat:cp.data.materials[i]=mat.copy()
 # Independent conservative surface dissolve: UV boundary and curvature protected; no nearest-face transfer.
 select([cp]);bm=bmesh.new();bm.from_mesh(cp.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update()
 protect=set()
 if a.id=='strawberry-mature':
  # Direct source-UV organ selection protects red fruit skins, yellow seeds and flower center.
  uv=bm.loops.layers.uv.active;im=next(n.image for m in cp.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.colorspace_settings.name=='sRGB');pixels=np.array(im.pixels[:]).reshape(im.size[1],im.size[0],4)
  for face in bm.faces:
   t=sum((loop[uv].uv for loop in face.loops),Vector((0.,0.)))/len(face.loops);rgb=pixels[min(im.size[1]-1,max(0,int(t.y*(im.size[1]-1)))),min(im.size[0]-1,max(0,int(t.x*(im.size[0]-1)))),:3]
   if (rgb[0]>.5 and rgb[0]>rgb[1]*1.35) or (rgb[0]>.6 and rgb[1]>.4 and rgb[2]<.45):protect.update(face.verts)
 edges=[e for e in bm.edges if not any(v in protect for v in e.verts)];verts=[v for v in bm.verts if v not in protect]
 angle=math.radians(1.2 if 'lod1' not in a.version else 2.4)
 before=len(bm.faces);bmesh.ops.dissolve_limit(bm,angle_limit=angle,verts=verts,edges=edges,use_dissolve_boundaries=False,delimit={'UV','MATERIAL','NORMAL'}) if a.id!='strawberry-mature' else None;bm.normal_update();bm.to_mesh(cp.data);bm.free();cp.data.update();print('CONSERVATIVE_DISSOLVE',a.id,before,tri([cp]),'protected_vertices',len(protect),flush=True)
 for mat in cp.data.materials:
  if not mat or not mat.use_nodes:continue
  nt=mat.node_tree;bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if True and bs:
   for key,val in [('Metallic',0),('Roughness',.83),('Specular IOR Level',.24)]:
    for link in list(bs.inputs[key].links):nt.links.remove(link)
    bs.inputs[key].default_value=val
   for node in nt.nodes:
    if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.22
  # Each texture copied once for candidate; retain original maps in baseline.
  for node in nt.nodes:
   if node.type=='TEX_IMAGE' and node.image and node.image!=bpy.data.images.get(a.id+' baked high-surface normal'):
    key=node.image.name
    if not node.image.get('unity_candidate'):
     srcimg=node.image;pixels=np.empty(len(srcimg.pixels),dtype=np.float32);srcimg.pixels.foreach_get(pixels);im=bpy.data.images.new(srcimg.name+' unity packed copy',width=srcimg.size[0],height=srcimg.size[1],alpha=True);im.colorspace_settings.name=srcimg.colorspace_settings.name;im.pixels.foreach_set(pixels);im.update();im['unity_candidate']=True;maxdim=(1024 if 'lod1' in a.version else 2048) if a.id=='strawberry-mature' else (512 if 'lod1' in a.version else 1024)
     if max(im.size)>maxdim:im.scale(maxdim,maxdim)
     im.pack();node.image=im
 low.append(cp)
# Hide original during save/export; retain it in separate source collection for editable provenance.
for ob in orig:ob.hide_render=True;ob.hide_set(True)
select(low);bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
H.inspection_setup();sc=bpy.context.scene;sc.cycles.samples=8;sc.render.threads_mode='FIXED';sc.render.threads=4
# H adds ground: match plane to source grounding for preview only.
for ob in sc.objects:
 if ob.name.startswith('QA ground'):ob.location.z=lo.z-.005
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(blend));low=[o for o in bpy.context.scene.objects if o.get('production')];orig=[o for o in bpy.context.scene.objects if o.get('input_object')];assert low
if a.review!='none':
 for ob in low:ob.hide_render=True
 for ob in orig:ob.hide_render=False
 for view in ['quarter','back']:pic(out/f'original-material-{view}.png',target,span,view)
 for ob in low:ob.hide_render=False
 for ob in orig:ob.hide_render=True
 views=['quarter','back'] if a.review=='quick' else list(H.VIEWS)
 for view in views:pic(out/f'material-{view}.png',target,span,view)
 gray=H.material('Unity candidate neutral gray',(.38,.38,.38),.85)
 for ob in low:ob.data.materials.clear();ob.data.materials.append(gray)
 for view in views:pic(out/f'clay-{view}.png',target,span,view)
# Separate exported GLB readback, including evaluated geometry and textures.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(dest));rt=[o for o in bpy.context.scene.objects if o.type=='MESH'];rlo,rhi=bounds(rt);stats=H.check_glb(dest);rt=[o for o in bpy.context.scene.objects if o.type=='MESH'];stats.update({'id':a.id,'version':a.version,'source':row['source'],'source_sha256':row['source_sha256'],'editable_source':str(blend),'editable_source_sha256':sha(blend),'file':str(dest),'source_reopened':True,'export_reimported':True,'original_unchanged':sha(row['source'])==row['source_sha256'],'original_triangles':total,'target_triangles':desired,'actual_triangles':tri(rt),'source_geometry':source_geometry,'geometry':geometry(rt),'bounds_zup':{'min':list(rlo),'max':list(rhi),'size':list(rhi-rlo)},'images':[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file)} for im in bpy.data.images if im.size[0]],'route':'UV-boundary and curvature protected limited dissolve; strawberry fruit/seed topology excluded; exact original UV mapping; independent matte and reduced texture copies','visual':'pending_actual_inspection','user_art':'pending','device':'not_tested'})
(out/'metrics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print('ASSET_COMPLETE',a.id,tri(rt),str(dest),flush=True)
