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
(out/'review-settings.json').write_text(json.dumps(settings,indent=2));source_geometry=geometry(orig);total=tri(orig);desired=row['candidate_target_triangles'];low=[];broad=row['stage']=='seedling' and row['species'] in ['cabbage','bokchoy','cauliflower','lettuce']
for ob in orig:
 cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);cp.name=a.id+' game mesh';cp['input_object']=False;cp['production']=True
 # Copy materials so source comparison remains original.
 for i,mat in enumerate(cp.data.materials):
  if mat:cp.data.materials[i]=mat.copy()
 select([cp]);w=cp.modifiers.new('Weld coincident seams before simplification','WELD');w.merge_threshold=max(size*1e-8,1e-8);bpy.ops.object.modifier_apply(modifier=w.name)
 if desired and tri([cp])>desired*tri([ob])/total:
  # Budget is explicit per-asset, not a global percentage. Seam UV loops remain.
  dec=cp.modifiers.new('Per-asset curvature aware LOD candidate','DECIMATE');dec.ratio=min(1,desired/total);dec.use_collapse_triangulate=True
  if not broad and cp.data.uv_layers:
   uv=cp.data.uv_layers.active.data;vertex_uv={}
   for lp in cp.data.loops:vertex_uv.setdefault(lp.vertex_index,set()).add(tuple(round(v,5) for v in uv[lp.index].uv))
   vg=cp.vertex_groups.new(name='UV seam retention')
   seam=[i for i,values in vertex_uv.items() if len(values)>1]
   if seam:vg.add(seam,1.0,'REPLACE');dec.vertex_group=vg.name;dec.vertex_group_factor=100
  if broad:
   bm=bmesh.new();bm.from_mesh(cp.data);bm.verts.ensure_lookup_table();bm.normal_update();vg=cp.vertex_groups.new(name='Vein-curvature-retention')
   for v in bm.verts:
    bend=max((1-v.normal.dot(f.normal) for f in v.link_faces),default=0);weight=min(1,bend*8)
    if weight>.02:vg.add([v.index],weight,'REPLACE')
   bm.free();dec.vertex_group=vg.name;dec.vertex_group_factor=8
  bpy.ops.object.modifier_apply(modifier=dec.name)
 # Preserve high frequency surface response through tangent-normal baking on broad leaves.
 if broad:
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=1;sc.render.threads_mode='FIXED';sc.render.threads=4
  image=bpy.data.images.new(a.id+' baked high-surface normal',1024,1024,alpha=False);image.colorspace_settings.name='Non-Color';image.generated_color=(.5,.5,1,1)
  for mat in cp.data.materials:
   node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.select=True;mat.node_tree.nodes.active=node
  select([ob,cp]);bpy.context.view_layer.objects.active=cp;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=size*.025;sc.render.bake.max_ray_distance=size*.05;sc.render.bake.margin=12
  bpy.ops.object.bake(type='NORMAL');image.filepath_raw=str(out/'baked-normal.png');image.file_format='PNG';image.save();image.pack()
  for mat in cp.data.materials:
   nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');n=nt.nodes.new('ShaderNodeNormalMap');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;nt.links.new(tex.outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal']);n.inputs['Strength'].default_value=.55
 for mat in cp.data.materials:
  if not mat or not mat.use_nodes:continue
  nt=mat.node_tree;bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if row['type'] in ['facility','environment'] and bs:
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
     srcimg=node.image;pixels=np.empty(len(srcimg.pixels),dtype=np.float32);srcimg.pixels.foreach_get(pixels);im=bpy.data.images.new(srcimg.name+' unity packed copy',width=srcimg.size[0],height=srcimg.size[1],alpha=True);im.colorspace_settings.name=srcimg.colorspace_settings.name;im.pixels.foreach_set(pixels);im.update();im['unity_candidate']=True;maxdim=2048 if a.id=='S01' else 1024
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
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(dest));rt=[o for o in bpy.context.scene.objects if o.type=='MESH'];rlo,rhi=bounds(rt);stats=H.check_glb(dest);rt=[o for o in bpy.context.scene.objects if o.type=='MESH'];stats.update({'id':a.id,'version':a.version,'source':row['source'],'source_sha256':row['source_sha256'],'editable_source':str(blend),'editable_source_sha256':sha(blend),'file':str(dest),'source_reopened':True,'export_reimported':True,'original_unchanged':sha(row['source'])==row['source_sha256'],'original_triangles':total,'target_triangles':desired,'actual_triangles':tri(rt),'source_geometry':source_geometry,'geometry':geometry(rt),'bounds_zup':{'min':list(rlo),'max':list(rhi),'size':list(rhi-rlo)},'images':[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file)} for im in bpy.data.images if im.size[0]],'broad_route':'curvature-weighted decimation plus selected-to-active normal bake; source high mesh retained' if broad else None,'visual':'pending_actual_inspection','user_art':'pending','device':'not_tested'})
(out/'metrics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print('ASSET_COMPLETE',a.id,tri(rt),str(dest),flush=True)
