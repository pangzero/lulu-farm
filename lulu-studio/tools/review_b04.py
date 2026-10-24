"""B04 source reopen, GLB readback and controlled visual evidence (no asset writes)."""
import bpy,bmesh,sys,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_b04 import studio,CAMERAS
ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'review/farm-assets/B04';SRC=ROOT/'assets-source/farm-assets/B04';OUT=ROOT/'public/models/farm-assets/B04';REV='r02';CROPS=['bokchoy','lettuce','cauliflower']
VIEWS={'front':(0,-1,.025),'side':(1,0,.025),'back':(0,1,.025),'quarter':(1.35,-4,2.25),'top':(0,-.001,1)}

def import_glb(path,offset=(0,0,0)):
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));added=set(bpy.data.objects)-before
    for o in added:
        if o.parent not in added:o.location+=Vector(offset)
    bpy.context.view_layer.update();return list(added)
def remove(obs):
    for o in obs:bpy.data.objects.remove(o,do_unlink=True)
def prod():return [o for o in bpy.context.scene.objects if o.type in ['MESH','CURVE'] and not o.name.startswith('QA ')]
def render(s,path):s.render.filepath=str(QA/path);bpy.ops.render.render(write_still=True)
def camera(s,target,scale,view='quarter',size=(768,768)):
    t=Vector(target);s.camera.location=t+Vector(VIEWS[view]).normalized()*10;s.camera.rotation_euler=(t-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=scale*size[0]/size[1];s.render.resolution_x,s.render.resolution_y=size;s.cycles.samples=16

def stats(path):
    bpy.ops.wm.read_factory_settings(use_empty=True);added=import_glb(path);obs=[o for o in added if o.type=='MESH'];pts=[o.matrix_world@v.co for o in obs for v in o.data.vertices]
    lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
    zero=dups=badverts=badnorm=boundaries=nonman=0;negative=[]
    for o in obs:
        fs=[tuple(sorted(p.vertices)) for p in o.data.polygons];dups+=len(fs)-len(set(fs));zero+=sum(p.area<1e-12 for p in o.data.polygons)
        badverts+=sum(not all(math.isfinite(c) for c in v.co) for v in o.data.vertices);badnorm+=sum(not all(math.isfinite(c) for c in p.normal) or p.normal.length<.5 for p in o.data.polygons)
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);boundaries+=sum(e.is_boundary for e in bm.edges);nonman+=sum(not e.is_manifold for e in bm.edges)
        if bm.calc_volume(signed=True)<-1e-8:negative.append(o.name)
        bm.free()
    raw=path.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    return {'file':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':sum(g['accessors'][p['indices']]['count']//3 for m in g.get('meshes',[]) for p in m['primitives']),'vertices_imported':len(pts),'mesh_nodes':len(obs),'primitives':sum(len(m['primitives']) for m in g.get('meshes',[])),'materials':len(g.get('materials',[])),'textures':len(g.get('images',[])),'texture_dimensions':[],'external_uris':[im['uri'] for im in g.get('images',[]) if 'uri' in im and not im['uri'].startswith('data:')],'bbox_blender_z_up':[lo,hi],'size':[b-a for a,b in zip(lo,hi)],'zero_area_faces':zero,'duplicate_index_faces':dups,'nonfinite_vertices':badverts,'invalid_face_normals':badnorm,'welded_boundary_edges':boundaries,'welded_nonmanifold_edges':nonman,'negative_signed_volume_meshes':negative,'negative_transform_objects':[o.name for o in obs if o.matrix_world.determinant()<0],'exported_cameras':len(g.get('cameras',[])),'exported_lights':len(g.get('extensions',{}).get('KHR_lights_punctual',{}).get('lights',[])),'vertex_color_primitives':sum('COLOR_0' in p['attributes'] for m in g.get('meshes',[]) for p in m['primitives']),'readback':'success','origin':'Root ground centre, Blender Z-up converted to glTF Y-up; no height normalization','normal_check':'Finite face normals + temporary welded topology/volume diagnostics + actual front/back views; visual defects recorded separately.'}

settings=json.loads((ROOT/'review/farm-assets/B01/review-settings.json').read_text());settings.update({'batch':'B04','revision':REV,'baseline':'User accepted B01 r03','cameras':CAMERAS,'detail':{'bokchoy':{'target':[0,-.10,.30],'ortho_scale':.90},'lettuce':{'target':[0,0,.36],'ortho_scale':1.05},'cauliflower':{'target':[0,0,.42],'ortho_scale':.95}},'native_field':{'size':[1280,720],'spacing':1.2,'target':[0,0,.35],'orthographic_height':4.3,'orthographic_width':4.3*1280/720,'ortho_scale':4.3*1280/720,'direction':[4,-6,6]},'types':{'size':[1280,720],'asset_positions_x':[-1.2,0,1.2],'orthographic_height':2.6,'target':[0,0,.43],'labels_in_image':False,'scale':1},'scope':'Only bokchoy/lettuce/cauliflower mature. Test cells are QA, not E01 assets.','note':'r01/r02/v1 comparisons share camera/light/exposure and authored scale; all three r02 crops remain visual failures, not art accepted.'})
(QA/'review-settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2))
metrics={'batch':'B04','revision':REV,'assets':{}}
for c in CROPS:
    metrics['assets'][c]=stats(OUT/f'{c}-mature-{REV}.glb')
    metrics['assets'][c]['baseline_v1']=stats(ROOT/f'public/models/crops/{c}-mature.glb')
    metrics['assets'][c]['previous_r01']=stats(OUT/f'{c}-mature-r01.glb')
    p=SRC/f'{c}-mature-{REV}.blend';metrics['assets'][c]['source']=str(p.relative_to(ROOT));metrics['assets'][c]['source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
(QA/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
for c in CROPS:
    bpy.ops.wm.open_mainfile(filepath=str(SRC/f'{c}-mature-{REV}.blend'));s=bpy.context.scene;obs=prod();cfg=CAMERAS[c]
    metrics['assets'][c]['source_reopened']=True;metrics['assets'][c]['editable_components']=[o.name for o in obs];metrics['assets'][c]['modifiers']={o.name:[m.type for m in o.modifiers] for o in obs};metrics['assets'][c]['ground_alignment_offset']=s.get('ground_alignment_offset',0)
    for view in VIEWS:camera(s,cfg['target'],cfg['ortho_scale'],view);render(s,f'{c}-{REV}-material-{view}.png')
    clay=bpy.data.materials.new('B04 neutral diagnostic clay');clay.use_nodes=True;p=clay.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.38,.38,.38,1);p.inputs['Roughness'].default_value=.85;p.inputs['Specular IOR Level'].default_value=.28
    original={o.name:list(o.data.materials) for o in obs}
    for o in obs:o.data.materials.clear();o.data.materials.append(clay)
    for view in VIEWS:camera(s,cfg['target'],cfg['ortho_scale'],view);render(s,f'{c}-{REV}-clay-{view}.png')
    for o in obs:
        o.data.materials.clear()
        for m in original[o.name]:o.data.materials.append(m)
    d=settings['detail'][c];camera(s,d['target'],d['ortho_scale']);render(s,f'{c}-{REV}-detail.png');remove(obs)
    # Actual exported candidates, including previous failure and v1, not a fake beauty proxy.
    for tag,path in [(REV,OUT/f'{c}-mature-{REV}.glb'),('r01',OUT/f'{c}-mature-r01.glb'),('v1',ROOT/f'public/models/crops/{c}-mature.glb')]:
        added=import_glb(path);camera(s,cfg['target'],cfg['ortho_scale']);render(s,f'{c}-{tag}-glb-quarter.png');remove(added)
    imported=import_glb(OUT/f'{c}-mature-{REV}.glb');meshes=[o for o in imported if o.type=='MESH'];copies=[]
    for x in [-1.2,0,1.2]:
        for y in [-1.2,0,1.2]:
            for o in meshes:
                q=o.copy();q.data=o.data;q.parent=None;q.matrix_world=o.matrix_world.copy();q.location+=Vector((x,y,0));s.collection.objects.link(q);copies.append(q)
    remove(imported);camera(s,[0,0,.35],4.3,size=(1280,720));t=Vector((0,0,.35));s.camera.location=t+Vector((4,-6,6));s.camera.rotation_euler=(t-s.camera.location).to_track_quat('-Z','Y').to_euler();render(s,f'{c}-{REV}-field.png')
    metrics['assets'][c]['native_review_completed']=True;(QA/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2));print('B04 REVIEWED',c,flush=True)
# Unlabelled three-type diagnostic in one world scale; no acceptance claim.
bpy.ops.wm.read_factory_settings(use_empty=True);s=studio()
for c,x in zip(CROPS,[-1.2,0,1.2]):import_glb(OUT/f'{c}-mature-{REV}.glb',(x,0,0))
camera(s,[0,0,.43],2.6,size=(1280,720));render(s,f'B04-{REV}-types.png')
clay=bpy.data.materials.new('B04 types clay');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.38,.38,.38,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
for o in prod():o.data.materials.clear();o.data.materials.append(clay)
render(s,f'B04-{REV}-types-clay.png')
(QA/f'metrics-{REV}.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
print('B04 REVIEW COMPLETE',flush=True)
