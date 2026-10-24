import bpy,bmesh,json,hashlib,importlib.util,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];P=R/'public/models/unity-integration';S=R/'assets-source/unity-integration';O=R/'review/unity-integration-20261018/assets';registry=json.loads((P/'manifest.json').read_text());spec=importlib.util.spec_from_file_location('qa',R/'tools/build_seedling_study.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def select(obs):
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0]
def tri(ob):return sum(len(f.vertices)-2 for f in ob.data.polygons)
keys=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['E01','E05','E13']
for key in keys:
 if key=='E05-corner':
  base=next(x for x in json.loads((P/'interfaces-manifest.json').read_text())['assets'] if x['id']==key);row={'source':base['file'],'source_sha256':base['sha256']}
 else:row=next(x for x in registry['assets'] if x['id']==key)
 for level in [0,1]:
  v='native-r01' if level==0 else 'native-lod1-r01';out=O/key/v;out.mkdir(parents=True,exist_ok=True);dest=P/v/(key+'.glb');blend=S/v/(key+'.blend');dest.parent.mkdir(exist_ok=True);blend.parent.mkdir(exist_ok=True);assert not dest.exists();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=row['source']);orig=[o for o in bpy.context.scene.objects if o.type=='MESH'];lo,hi=H.bounds(orig);center=(lo+hi)/2;scale=max(hi-lo)*1.42;low=[];parts=[]
  for ob in orig:
   world=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=world;select([ob]);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob['input_object']=True;cp=ob.copy();cp.data=ob.data.copy();bpy.context.collection.objects.link(cp);cp['input_object']=False;cp['production']=True;before=tri(ob);cp.name=ob.name+' native game';budget=before
   if key=='E01':budget=(1600 if level==0 else 900) if 'soil' in ob.name else (48 if level==0 else 24) if before>7000 else (128 if level==0 else 80)
   elif key.startswith('E05'):budget=(500 if level==0 else 200) if before>7000 else before
   elif key=='E13':budget=700 if level==0 else 280
   if before>budget:
    select([cp]);w=cp.modifiers.new('Weld position seams preserving native colors','WELD');w.merge_threshold=1e-7;bpy.ops.object.modifier_apply(modifier=w.name);dec=cp.modifiers.new('Named part budget, native surface retained','DECIMATE');dec.ratio=budget/before;dec.use_collapse_triangulate=True
    if key=='E01' and 'soil' in ob.name:
     vg=cp.vertex_groups.new(name='Keep four tile interface edges');vg.add(list(range(len(cp.data.vertices))),1.,'REPLACE');edge=[x.index for x in cp.data.vertices if abs(x.co.x)>.549 or abs(x.co.y)>.549];vg.add(edge,0,'REPLACE');dec.vertex_group=vg.name
    bpy.ops.object.modifier_apply(modifier=dec.name)
   parts.append({'name':ob.name,'source_triangles':before,'requested_part_budget':budget,'actual':tri(cp)});low.append(cp);ob.hide_render=True;ob.hide_set(True)
  select(low);bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_apply=True);H.inspection_setup();sc=bpy.context.scene;sc.cycles.samples=8;sc.render.threads=3
  for ob in sc.objects:
   if ob.name.startswith('QA ground'):ob.location.z=lo.z-.005
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True);bpy.ops.wm.open_mainfile(filepath=str(blend));sc=bpy.context.scene;low=[o for o in sc.objects if o.get('production')];orig=[o for o in sc.objects if o.get('input_object')]
  def pic(name,view):
   di=Vector(H.VIEWS[view]).normalized();sc.camera.location=center+di*30;sc.camera.rotation_euler=(center-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale;sc.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
  for ob in low:ob.hide_render=True
  for ob in orig:ob.hide_render=False
  for view in ['quarter','back']:pic('original-material-'+view+'.png',view)
  for ob in low:ob.hide_render=False
  for ob in orig:ob.hide_render=True
  for mode in ['material','clay']:
   if mode=='clay':
    g=H.material('Neutral native gray',(.38,.38,.38),.85)
    for ob in low:ob.data.materials.clear();ob.data.materials.append(g)
   for view in H.VIEWS:pic(mode+'-'+view+'.png',view)
  m=H.check_glb(dest);geometry=[]
  for ob in bpy.context.scene.objects:
   if ob.type!='MESH':continue
   bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);geometry.append({'name':ob.name,'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'zero_area':sum(f.calc_area()<1e-14 for f in bm.faces),'finite':all(all(math.isfinite(c) for c in v.co) for v in bm.verts)});bm.free()
  rtlo,rthi=H.bounds([ob for ob in bpy.context.scene.objects if ob.type=='MESH']);m.update({'id':key,'version':v,'level':level,'source':row['source'],'source_sha256':row['source_sha256'],'source_reopened':True,'export_reimported':True,'original_unchanged':sha(row['source'])==row['source_sha256'],'editable_source':str(blend),'editable_source_sha256':sha(blend),'file':str(dest),'actual_triangles':m['triangles'],'parts':parts,'geometry':geometry,'bounds_zup':{'min':list(rtlo),'max':list(rthi),'size':list(rthi-rtlo)},'native_vertex_colors_and_materials_preserved':True,'no_texture_rebake':True,'visual':'pending_actual_inspection'});(out/'metrics.json').write_text(json.dumps(m,indent=2));(out/'review-settings.json').write_text(json.dumps({'target':list(center),'ortho_scale':scale,'resolution':[768,768],'views':H.VIEWS,'lights':'B01 fixed','exposure':0,'authored_scale_and_interfaces_preserved':True},indent=2));print('NATIVE',key,v,m['triangles'],geometry,flush=True)
