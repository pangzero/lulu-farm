import bpy,bmesh,json,sys,math,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/unity_animals'));from bvh_bake_color import bake
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['cow'];aid=args[0];variant=args[1] if len(args)>1 else 'lod0';REV='game-r03';OUT=R/'public/models/unity-animals'/REV/aid;SRC=R/'assets-source/unity-animals'/REV/aid;REP=R/'review/unity-integration-20261018/animals'/REV/aid
for p in [OUT,SRC,REP]:p.mkdir(parents=True,exist_ok=True)
item=next(a for a in json.loads((R/'public/models/unity-integration/manifest.json').read_text())['assets'] if a['type']=='animal' and a['id']==aid);source=Path(item['file']);sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha==item['source_sha256']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in objects:
 mw=o.matrix_world.copy();o.parent=None;o.matrix_world=mw;bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.select_set(False)
# Keep a separate native import, before editing the derived object.
if not (SRC/'source-import.blend').exists():bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'source-import.blend'),compress=True)
if len(objects)>1:
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
high=bpy.context.view_layer.objects.active if len(objects)>1 else objects[0];high.name=aid+'_source';low=high.copy();low.data=high.data.copy();bpy.context.collection.objects.link(low);low.name=aid+'_'+variant
bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low
bm=bmesh.new();bm.from_mesh(low.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=max(max(low.dimensions)*1e-6,1e-7));bm.to_mesh(low.data);bm.free();low.data.update()
tris=sum(len(p.vertices)-2 for p in low.data.polygons);budget={'cow':20000,'sheep':24000,'alpaca':24000,'ostrich':18000,'pony':20000,'deer':18000}.get(aid,16000);budget=budget if variant=='lod0' else int(budget*.55)
mod=low.modifiers.new('Independent silhouette candidate','DECIMATE');mod.ratio=min(1,budget/tris);bpy.ops.object.modifier_apply(modifier=mod.name)
# New atlas removes obsolete UV-island interpolation; transfer original custom surface normals.

for uv in list(low.data.uv_layers):low.data.uv_layers.remove(uv)
low.data.uv_layers.new(name='GameAtlas');bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.25);bpy.ops.object.mode_set(mode='OBJECT')
for p in low.data.polygons:p.use_smooth=True
mod=low.modifiers.new('Original surface normals','DATA_TRANSFER');mod.object=high;mod.use_loop_data=True;mod.data_types_loops={'CUSTOM_NORMAL'};mod.loop_mapping='POLYINTERP_NEAREST';bpy.ops.object.modifier_apply(modifier=mod.name)
folder=OUT/variant;folder.mkdir(exist_ok=True);res=2048 if variant=='lod0' else 1024;image,normal,breport=bake(high,low,res,folder)
# Keep original semantic material partitions; eye softness remains separately adjustable.
oldm=list(high.data.materials);low.data.materials.clear()
for mi,m in enumerate(oldm):
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');rough=float(bs.inputs['Roughness'].default_value);nm=bpy.data.materials.new(aid+'_'+variant+'_'+m.name);nm.use_nodes=True;n=nm.node_tree.nodes;pr=n.get('Principled BSDF');pr.inputs['Metallic'].default_value=0;pr.inputs['Roughness'].default_value=.24 if 'eye' in m.name.lower() else .9;pr.inputs['Specular IOR Level'].default_value=.2;tex=n.new('ShaderNodeTexImage');tex.image=image
 if m.name=='cow_black_head_interior_v4':pr.inputs['Base Color'].default_value=bs.inputs['Base Color'].default_value
 else:nm.node_tree.links.new(tex.outputs['Color'],pr.inputs['Base Color'])
 low.data.materials.append(nm)
high.hide_render=True;high.hide_viewport=True;bpy.data.objects.remove(high,do_unlink=True)
for o in list(bpy.context.scene.objects):
 if o!=low:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/(variant+'.blend')),compress=True);bpy.ops.export_scene.gltf(filepath=str(OUT/(variant+'.glb')),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_apply=True)
points=np.array([v.co[:] for v in low.data.vertices]);metric={'id':aid,'name':item['name'],'revision':REV,'variant':variant,'source':str(source),'source_name':source.name,'source_sha256':sha,'source_import':str(SRC/'source-import.blend'),'native':str(SRC/(variant+'.blend')),'file':str(OUT/(variant+'.glb')),'sha256':hashlib.sha256((OUT/(variant+'.glb')).read_bytes()).hexdigest(),'bytes':(OUT/(variant+'.glb')).stat().st_size,'triangles':sum(len(p.vertices)-2 for p in low.data.polygons),'meshes':1,'materials':len(low.data.materials),'texture_sizes':[[res,res]],'texture_count':1,'bounds_blender':[points.min(0).tolist(),points.max(0).tolist()],'suggested_world_height':item['suggested_world_height'],'bake':breport,'modifications':['UV seam weld only within 1e-6 of object size','independent silhouette decimation, new UV0','matching source nearest-surface color transfer; original part normals','source material segmentation preserved; metallic zero'],'status':{'technical':'pending_reopen_reimport','visual':'pending_actual_inspection','user_art':'pending','optimization':'candidate','device':'unverified'}};(REP/(variant+'-metrics.json')).write_text(json.dumps(metric,ensure_ascii=False,indent=2));(OUT/(variant+'-manifest.json')).write_text(json.dumps(metric,ensure_ascii=False,indent=2));print('FINISHED',aid,variant,metric['triangles'],metric['bytes'])
