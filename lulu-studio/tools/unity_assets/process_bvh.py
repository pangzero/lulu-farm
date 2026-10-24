"""Revisioned geometry/texture candidates, species-specific targets and baked broad-leaf normals.
No historical production generator runs; every input is an explicit preserved source GLB.
"""
import bpy,bmesh,json,sys,math,argparse,hashlib,importlib.util,time
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent));from bvh_bake import bake as bvh_bake
R=Path(__file__).resolve().parents[2];P=R/'public/models/unity-integration';O=R/'review/unity-integration-20261018/assets';S=R/'assets-source/unity-integration'
ap=argparse.ArgumentParser();ap.add_argument('--id',required=True);ap.add_argument('--version',default='bvh-r01');ap.add_argument('--target',type=int);ap.add_argument('--resolution',type=int);ap.add_argument('--review',default='quick',choices=['none','quick','all']);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);row=next(x for x in json.loads((P/'manifest.json').read_text())['assets'] if x['id']==a.id);out=O/a.id/a.version;out.mkdir(parents=True,exist_ok=True);dest=P/a.version/(a.id+'.glb');blend=S/a.version/(a.id+'.blend');dest.parent.mkdir(parents=True,exist_ok=True);blend.parent.mkdir(parents=True,exist_ok=True)
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
assert a.version!='atlas-local-lod1-r01', 'Zero-weight geometry lock route stopped after silhouette-collapse gate.'
assert sha(row['source'])==row['source_sha256'];assert not dest.exists(),f'Revision exists: {dest}'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=row['source']);orig=[o for o in bpy.context.scene.objects if o.type=='MESH']
for ob in orig:
 world=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=world;select([ob]);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob['input_object']=True
if row.get('source_scale'):
 for ob in orig:
  for vert in ob.data.vertices:vert.co*=row['source_scale']
  ob.data.update()
 bpy.context.view_layer.update()
if row.get('source_center_ground'):
 blo,bhi=bounds(orig);offset=Vector(((blo.x+bhi.x)/2,(blo.y+bhi.y)/2,blo.z))
 for ob in orig:
  for vert in ob.data.vertices:vert.co-=offset
  ob.data.update()
 bpy.context.view_layer.update()
lo,hi=bounds(orig);target=(lo+hi)/2;span=max(hi-lo)*1.42;size=max(hi-lo)
settings={'source_sha256':row['source_sha256'],'target':list(target),'ortho_scale':span,'views':H.VIEWS,'resolution':[768,768],'color':'Standard / exposure0 / gamma1','renderer':'Cycles CPU 8 samples denoised','lights':'B01 fixed area/key/fill/rim, scaled only by asset span for non-crop calibration','no_candidate_scale_change':True,'no_height_normalization':True}
(out/'review-settings.json').write_text(json.dumps(settings,indent=2));source_geometry=geometry(orig);total=tri(orig);desired=a.target if a.target else row['candidate_target_triangles'];low=[];broad=row['stage']=='seedling' and row['species'] in ['cabbage','bokchoy','cauliflower','lettuce']
for ob in orig:
 cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);cp.name=a.id+' game mesh';cp['input_object']=False;cp['production']=True
 # Copy materials so source comparison remains original.
 for i,mat in enumerate(cp.data.materials):
  if mat:cp.data.materials[i]=mat.copy()
 select([cp]);w=cp.modifiers.new('Weld coincident seams before simplification','WELD');w.merge_threshold=max(size*1e-6,1e-7);bpy.ops.object.modifier_apply(modifier=w.name)
 if desired and tri([cp])>desired*tri([ob])/total:
  # Budget is explicit per-asset, not a global percentage. Seam UV loops remain.
  dec=cp.modifiers.new('Per-asset curvature aware LOD candidate','DECIMATE');dec.ratio=min(1,desired/total);dec.use_collapse_triangulate=True
  if a.id=='S01' and a.version not in ['bvh-r01','bvh-r02']:
   # Redistribute the same triangle budget to the roof crest and joinery.
   vg=cp.vertex_groups.new(name='House ridge and window local protection');vg.add(list(range(len(cp.data.vertices))),1.0,'REPLACE');keep=[]
   for v in cp.data.vertices:
    x,y,z=v.co
    if (abs(x)<.19 and z>.46) or (y<-.44 and -.32<x<.33 and -.15<z<.40) or (x>.57 and -.55<z<.13):keep.append(v.index)
   vg.add(keep,.12,'REPLACE');dec.vertex_group=vg.name;dec.vertex_group_factor=.002
  if a.id=='E16' and a.version=='atlas-local-r01':
   vg=cp.vertex_groups.new(name='Blue fish smile local exact geometry lock');vg.add(list(range(len(cp.data.vertices))),1.0,'REPLACE');keep=[v.index for v in cp.data.vertices if v.co.y<-.65 and -.30<v.co.z<.05 and abs(v.co.x)<.32];vg.add(keep,0.0,'REPLACE');dec.vertex_group=vg.name
  if a.id=='rose-mature' and a.version.startswith('atlas'):
   vg=cp.vertex_groups.new(name='Explicit three flower petal curvature allocation');vg.add(list(range(len(cp.data.vertices))),1.0,'REPLACE');keep=[]
   for v in cp.data.vertices:
    for c,r,zmin in [((-.069,-.081,.777),(.23,.22,.18),.62),((-.236,-.132,.505),(.16,.17,.14),.382),((.223,.036,.684),(.1,.11,.14),.574)]:
     if v.co.z>zmin and sum(((v.co[i]-c[i])/r[i])**2 for i in range(3))<1:keep.append(v.index);break
   vg.add(keep,.08,'REPLACE');dec.vertex_group=vg.name;dec.vertex_group_factor=.001
  if a.id=='pumpkin-mature' and a.version!='bvh-r01':
   # Keep the thin near-right foreground leaf clear of the orange fruit shell.
   vg=cp.vertex_groups.new(name='Pumpkin foreground leaf local protection');vg.add(list(range(len(cp.data.vertices))),1.0,'REPLACE');keep=[v.index for v in cp.data.vertices if v.co.x>.10 and v.co.y<-.12 and .05<v.co.z<.44];vg.add(keep,0.0 if a.version=='atlas-local-r01' else .03,'REPLACE');dec.vertex_group=vg.name;dec.vertex_group_factor=.004
  if a.id=='lettuce-mature' and a.version.startswith('atlas'):
   vg=cp.vertex_groups.new(name='Lettuce rolled lip tangent protection');vg.add(list(range(len(cp.data.vertices))),1.0,'REPLACE');keep=[v.index for v in cp.data.vertices if abs(v.normal.z)<.38];vg.add(keep,.15,'REPLACE');dec.vertex_group=vg.name;dec.vertex_group_factor=.001
  if a.id=='cauliflower-mature' and a.version.startswith('atlas'):
   vg=cp.vertex_groups.new(name='Cauliflower upper floret allocation');vg.add(list(range(len(cp.data.vertices))),1.0,'REPLACE');keep=[v.index for v in cp.data.vertices if v.co.z>lo.z+(hi.z-lo.z)*.52];vg.add(keep,.15,'REPLACE');dec.vertex_group=vg.name;dec.vertex_group_factor=.001
  bpy.ops.object.modifier_apply(modifier=dec.name)
 if a.id in ['S03','S09'] and a.version.startswith('atlas'):
  bm=bmesh.new();bm.from_mesh(cp.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bad=[f for f in bm.faces if f.calc_area()<1e-6 and all(not e.is_manifold for e in f.edges)]
  if len(bad)==1:bmesh.ops.delete(bm,geom=bad,context='FACES');bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
  bm.normal_update();bm.to_mesh(cp.data);bm.free();cp.data.update()
 # New route: a fresh UV atlas and selected-to-active surface transfer avoid retained-UV collapse artifacts.
 if a.version.startswith('atlas-hybrid'):
  cp.data.uv_layers.active.name='SourceUV';newuv=cp.data.uv_layers.new(name='GameUV');cp.data.uv_layers.active=newuv
 select([cp]);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(75),island_margin=.0025 if a.version.startswith('atlas') else .015,area_weight=.1);bpy.ops.object.mode_set(mode='OBJECT')
 cp.data.materials.clear();mat=bpy.data.materials.new(a.id+' baked matte surface');mat.use_nodes=True;cp.data.materials.append(mat)
 for face in cp.data.polygons:face.material_index=0
 nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.84;bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.24
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=1;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=size*.014;sc.render.bake.max_ray_distance=size*.028;sc.render.bake.margin=12
 texsize=a.resolution or (2048 if a.id in ['S01','S03','strawberry-mature'] else 1024)
 color,normal,bake_stats=bvh_bake(ob,cp,texsize,out,semantic=(('rose-clean2' if a.version in ['atlas-semantic-r06','atlas-lod1-r04'] else 'rose-clean' if a.version in ['atlas-semantic-r05','atlas-lod1-r03'] else 'rose-blended' if a.version.startswith('atlas-semantic-r04') or a.version.startswith('atlas-lod1-r02') else 'rose-local') if a.version.startswith('atlas') else 'rose') if a.id=='rose-mature' else ('pumpkin-uv' if a.id=='pumpkin-mature' else 'fish-uv') if a.version.startswith('atlas-hybrid') else None,supersample=2 if a.version.endswith('r02') and a.id in ['tomato-mature','cucumber-mature','pumpkin-mature'] else 1,normal_match=a.version.startswith('oriented'))
 cn=nt.nodes.new('ShaderNodeTexImage');cn.image=color;nt.links.new(cn.outputs['Color'],bs.inputs['Base Color']);nn=nt.nodes.new('ShaderNodeTexImage');nn.image=normal;nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.55 if broad else .25;nt.links.new(nn.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 if a.version.startswith('atlas-hybrid'):
  cp.data.uv_layers.remove(cp.data.uv_layers.get('SourceUV'));cp.data.uv_layers.active=cp.data.uv_layers.get('GameUV');cp.data.uv_layers.active.active_render=True
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
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(dest));rt=[o for o in bpy.context.scene.objects if o.type=='MESH'];rlo,rhi=bounds(rt);stats=H.check_glb(dest);rt=[o for o in bpy.context.scene.objects if o.type=='MESH'];stats.update({'id':a.id,'version':a.version,'source':row['source'],'source_sha256':row['source_sha256'],'editable_source':str(blend),'editable_source_sha256':sha(blend),'file':str(dest),'source_reopened':True,'export_reimported':True,'original_unchanged':sha(row['source'])==row['source_sha256'],'original_triangles':total,'target_triangles':desired,'actual_triangles':tri(rt),'source_geometry':source_geometry,'geometry':geometry(rt),'bounds_zup':{'min':list(rlo),'max':list(rhi),'size':list(rhi-rlo)},'images':[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file)} for im in bpy.data.images if im.size[0]],'broad_route':'fresh UV + BVH nearest-surface barycentric color/normal transfer; source high mesh retained','visual':'pending_actual_inspection','user_art':'pending','device':'not_tested'})
(out/'metrics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));print('ASSET_COMPLETE',a.id,tri(rt),str(dest),flush=True)
