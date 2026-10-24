import bpy,sys,json,math,hashlib,struct
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'review/farm-assets/B01';SRC=ROOT/'assets-source/farm-assets/B01';OUT=ROOT/'public/models/farm-assets/B01'
REV='r03';VIEWS={'front':(0,-1,.025),'side':(1,0,.025),'back':(0,1,.025),'quarter':(1.35,-4,2.25),'top':(0,-.001,1)}
settings={'revision':REV,'blender':'4.5.3 LTS','native_renderer':'Cycles CPU, 16 samples, denoising','native_color':{'view':'Standard','look':'None','exposure':0,'gamma':1},'lights':{'world':.32,'area_key':{'location':[-3,-4,6],'power':280,'size':4},'fill':{'location':[4,-1,3],'power':140,'size':3},'rim':{'location':[0,4,5],'power':230,'size':3}},'views':VIEWS,'close_image':[768,768],'cell':1.2,'crop_scale':1,'cameras':{'cabbage':{'target':[0,0,.32],'ortho_scale':1.32},'tomato':{'target':[0,0,.72],'ortho_scale':1.96},'corn':{'target':[0,0,.72],'ortho_scale':1.96}},'farm':{'size':[1280,720],'orthographic_width':14.1*1280/720,'orthographic_height':14.1,'azimuth_degrees':45,'elevation_degrees':50,'cells':[12,8],'normalization':False},'web':{'tone_mapping':'NoToneMapping','output':'sRGB','pixel_ratio':1,'hemisphere':.85,'key':2,'fill':.5,'exposure':1,'shadow_normal_bias':.02},'note':'Initial r01 beauty renders are not controlled A/B evidence; rerendered r01-baseline and v1/v2-baseline use these final fixed settings.'}

def camera(sc,crop,view):
 cfg=settings['cameras'][crop];target=Vector(cfg['target']);d=Vector(VIEWS[view]).normalized();sc.camera.location=target+d*6;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=cfg['ortho_scale'];sc.render.resolution_x=sc.render.resolution_y=768;sc.cycles.samples=16

def render(sc,path):sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
def glb_stats(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update();obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];vs=[o.matrix_world@v.co for o in obs for v in o.data.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
 zero=sum(p.area<1e-12 for o in obs for p in o.data.polygons);nan=sum(not all(math.isfinite(c) for c in v) for v in vs);dups=0
 for o in obs:
  faces=[tuple(sorted(p.vertices)) for p in o.data.polygons];dups+=len(faces)-len(set(faces))
 raw=path.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]]);tris=sum(g['accessors'][p['indices']]['count']//3 for m in g.get('meshes',[]) for p in m['primitives']);mats=g.get('materials',[])
 return {'file':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':tris,'vertices_imported':len(vs),'mesh_nodes':len(obs),'primitives':sum(len(m['primitives']) for m in g['meshes']),'materials':len(mats),'textures':len(g.get('images',[])),'external_uris':[i['uri'] for i in g.get('images',[]) if 'uri' in i and not i['uri'].startswith('data:')],'bbox_blender_z_up':[lo,hi],'size':[b-a for a,b in zip(lo,hi)],'zero_area_faces':zero,'nonfinite_vertices':nan,'duplicate_index_faces':dups,'negative_transform_objects':[o.name for o in obs if o.matrix_world.determinant()<0],'material_double_sided':sum(m.get('doubleSided',False) for m in mats),'normal_check':'smooth shading, normals imported; visual front/back review additionally required','readback':'success'}
metrics={};manifest=[]
for c in ['cabbage','tomato','corn']:
 metrics[c]=glb_stats(OUT/f'{c}-mature-{REV}.glb')
 metrics[c]['source']=str((SRC/f'{c}-mature-{REV}.blend').relative_to(ROOT))
 metrics[c]['source_sha256']=hashlib.sha256((SRC/f'{c}-mature-{REV}.blend').read_bytes()).hexdigest()
 metrics[c]['baseline']=glb_stats(ROOT/f'public/models/crops/{c}-mature.glb')
 manifest.append({'id':c,'name':{'cabbage':'卷心菜','tomato':'番茄','corn':'玉米'}[c],'revision':REV,'stage':'mature','status':'待用户验收','file':f'/models/farm-assets/B01/{c}-mature-{REV}.glb','triangles':metrics[c]['triangles'],'bytes':metrics[c]['bytes']})
metrics['lulu']=glb_stats(ROOT/'public/models/lulu-meshy-notail.glb');h=metrics['lulu']['size'][2];settings['lulu']={'original_height':h,'display_height':1.2,'instance_scale':1.2/h,'geometry_changed':False,'reason':'Provisional art scale: Lulu is one 1.2-unit cell tall; crops retain authored size. Pending user review.'}
(QA/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2));(QA/'review-settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2));(OUT/'manifest.json').write_text(json.dumps({'batch':'B01','revision':REV,'lulu_scale':1.2/h,'crops':manifest},ensure_ascii=False,indent=2))
for c in ['cabbage','tomato','corn']:
 bpy.ops.wm.open_mainfile(filepath=str(SRC/f'{c}-mature-{REV}.blend'));sc=bpy.context.scene
 prod=[o for o in sc.objects if o.type in ['MESH','CURVE'] and not o.name.startswith('QA ground')]
 for view in VIEWS:
  camera(sc,c,view);render(sc,QA/f'{c}-{REV}-material-{view}.png')
 clay=bpy.data.materials.new('Neutral diagnostic clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.38,.38,.38,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
 originals={o.name:list(o.data.materials) for o in prod}
 for o in prod:o.data.materials.clear();o.data.materials.append(clay)
 for view in VIEWS:
  camera(sc,c,view);render(sc,QA/f'{c}-{REV}-clay-{view}.png')
 for o in prod:
  o.data.materials.clear()
  for m in originals[o.name]:o.data.materials.append(m)
 camera(sc,c,'quarter');sc.camera.data.ortho_scale*=.68;render(sc,QA/f'{c}-{REV}-detail.png')
 # Source reopened and rendered above; baseline exported GLBs use identical camera/light.
 for o in prod:o.hide_render=True
 for tag,path in [('v1',ROOT/f'public/models/crops/{c}-mature.glb'),('r01',OUT/f'{c}-mature-r01.glb'),('r02',OUT/f'{c}-mature-r02.glb')]+([('v2',ROOT/'public/models/crop-studies/cabbage-v2.glb')] if c=='cabbage' else []):
  before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));added=set(bpy.data.objects)-before;camera(sc,c,'quarter');render(sc,QA/f'{c}-{tag}-baseline.png')
  for o in added:bpy.data.objects.remove(o,do_unlink=True)
 # Reimport candidate, so field images validate the exported artifact, not only the source.
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(OUT/f'{c}-mature-{REV}.glb'));new=[o for o in set(bpy.data.objects)-before if o.type=='MESH'];copies=[]
 for x in [-1.2,0,1.2]:
  for y in [-1.2,0,1.2]:
   for o in new:
    q=o.copy();q.data=o.data;sc.collection.objects.link(q);q.location+=Vector((x,y,0));copies.append(q)
 for o in new:o.hide_render=True
 camera(sc,c,'quarter');target=Vector((0,0,.35));sc.camera.location=target+Vector((4,-6,6));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=5.3;sc.render.resolution_x=1280;sc.render.resolution_y=720
 render(sc,QA/f'{c}-{REV}-field.png')
 print('REVIEW DONE',c,flush=True)
print('B01 REVIEW COMPLETE',flush=True)
