"""Fresh saved-source and GLB readback checks. Does not write production files."""
import bpy,bmesh,json,math,struct,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_b02 as B
ROOT=Path(__file__).resolve().parents[1];REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r02'
QA=ROOT/f'review/farm-assets/B14/{REV}';QA.mkdir(parents=True,exist_ok=True)
SRC=ROOT/f'assets-source/farm-assets/B14/{REV}/s01-main-house.blend';GLB=ROOT/f'public/models/farm-assets/B14/{REV}/s01-main-house.glb'
VIEWS={'front':(0,-1,.025),'side':(1,0,.025),'back':(0,1,.025),'quarter':(1.35,-4,2.25),'top':(0,-.001,1),'left':(-1,0,.025)}
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def import_glb(path):
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update();return list(set(bpy.data.objects)-before)
def bbox(obs):
    v=[o.matrix_world@v.co for o in obs if o.type=='MESH' for v in o.data.vertices]
    return [[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]
def stats(path):
    bpy.ops.wm.read_factory_settings(use_empty=True);obs=[o for o in import_glb(path) if o.type=='MESH']
    raw=path.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    details=[]
    for o in obs:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        fs=[tuple(sorted(p.vertices)) for p in o.data.polygons]
        d={'name':o.name,'triangles':len(o.data.polygons),'zero_area':sum(p.area<1e-12 for p in o.data.polygons),
           'duplicate_index_faces':len(fs)-len(set(fs)),'invalid_vertices':sum(not all(math.isfinite(x) for x in v.co) for v in o.data.vertices),
           'invalid_normals':sum(p.normal.length<.9 or not all(math.isfinite(x) for x in p.normal) for p in o.data.polygons),
           'welded_boundary_edges':sum(e.is_boundary for e in bm.edges),'welded_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
           'signed_volume':bm.calc_volume(signed=True),'bbox_z_up':bbox([o]),'materials':[m.name for m in o.data.materials]}
        bm.free();details.append(d)
    bounds=bbox(obs)
    return {'file':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':len(raw),'bbox_z_up':bounds,'size':[b-a for a,b in zip(*bounds)],
       'triangles':sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives']),
       'mesh_nodes':len(obs),'primitives':sum(len(m['primitives']) for m in g['meshes']),'materials':len(g.get('materials',[])),
       'texture_count':len(g.get('images',[])),'texture_dimensions':[],'external_uris':[im.get('uri') for im in g.get('images',[]) if im.get('uri')],
       'cameras':len(g.get('cameras',[])),'lights':len(g.get('extensions',{}).get('KHR_lights_punctual',{}).get('lights',[])),
       'modules':details,'readback':'passed','negative_transforms':[o.name for o in obs if o.matrix_world.determinant()<0]}
def image(s,name,target=(0,0,2.5),scale=7.3,view='quarter',size=(768,768)):
    B.camera(s,target,scale,VIEWS.get(view,view));s.render.resolution_x,s.render.resolution_y=size
    s.render.filepath=str(QA/(name+'.png'));bpy.ops.render.render(write_still=True)
def lulu(location):
    added=import_glb(ROOT/'public/models/lulu-official-v1.glb');root=bpy.data.objects.new('QA readonly Lulu official v1',None);bpy.context.scene.collection.objects.link(root)
    aset=set(added)
    for o in added:
        if o.parent not in aset:o.parent=root
    root.scale=(.6313689262131015,)*3;bpy.context.view_layer.update()
    bounds=bbox(added);root.location=(location[0],location[1],-bounds[0][2]);bpy.context.view_layer.update();return added,root

metrics={'revision':REV,'glb':stats(GLB)}
bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=3
prod=[o for o in s.objects if o.type in ['MESH','CURVE'] and not o.name.startswith('QA ground')]
metrics['source']={'file':str(SRC.relative_to(ROOT)),'sha256':sha(SRC),'reopened':True,'editable_components':len(prod),
 'components':[{'name':o.name,'type':o.type,'modifiers':[m.type for m in o.modifiers]} for o in prod],
 'collections':[c.name for c in bpy.data.collections if c.name.startswith('S01 editable')],
 'scope':s.get('asset_scope'),'entrance':s.get('entrance'),'axes':'Z up; front -Y; origin ground centre'}
dump(QA/'metrics.json',metrics)
settings=json.loads((ROOT/'review/farm-assets/B02/review-settings.json').read_text())
settings.update({'batch':'B14','revision':REV,'scope':'S01 complete house exterior; no interior/gameplay',
 'cameras':{'house':{'target':[0,0,2.5],'ortho_scale':7.3}},'views':VIEWS,'near_pixels':[768,768],
 'detail':{'door':{'target':[0,-1.75,1.3],'ortho_scale':2.8},'window':{'target':[1.52,-1.7,1.45],'ortho_scale':1.7},
 'chimney':{'target':[1.22,.66,4.72],'ortho_scale':1.8},'corner':{'target':[2.25,1.4,1.8],'ortho_scale':2.8}},
 'lulu':{'source':'public/models/lulu-official-v1.glb','sha256':sha(ROOT/'public/models/lulu-official-v1.glb'),'scale':.6313689262131015,'display_height':1.2,'geometry_modified':False},
 'style_inference':'Full gables, sides/back, window placement and chimney derived from S01 concept; B02 accepted warm plaster/oak/terracotta/blue-glass palette retained.',
 'comparisons':'r01/r02 same camera, inherited B01 light/colour and world scale; B02 sample NOT a full house predecessor.'})
dump(QA/'review-settings.json',settings)
for view in VIEWS:image(s,'material-'+view,view=view)
clay=B.material('B14 diagnostic clay','#A3A3A3',.85);original={o.name:list(o.data.materials) for o in prod}
for o in prod:
    for i in range(len(o.data.materials)):o.data.materials[i]=clay
for view in VIEWS:image(s,'clay-'+view,view=view)
for o in prod:
    for i,m in enumerate(original[o.name]):o.data.materials[i]=m
for name,c in settings['detail'].items():
    direction='quarter' if name!='corner' else (4,2,1.4)
    image(s,'detail-'+name,c['target'],c['ortho_scale'],direction)
for o in prod:bpy.data.objects.remove(o,do_unlink=True)
imported=import_glb(GLB)
for view in ['quarter','back','side']:image(s,'glb-'+view,view=view)
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
older=ROOT/'public/models/farm-assets/B14/r01/s01-main-house.glb'
if REV!='r01' and older.exists():
    old=import_glb(older)
    for view in ['quarter','side','back']:image(s,'r01-controlled-'+view,view=view)
    for o in old:bpy.data.objects.remove(o,do_unlink=True)
current=import_glb(GLB);luluObjects,luluRoot=lulu((1.06,-2.4))
image(s,'lulu-entrance',(0,-1.3,1.65),4.5,'front')
luluRoot.location.x=3.3;luluRoot.location.y=-2.4
image(s,'lulu-scale',(0,0,2.25),8.5)
# Neutral 1.2-grid QA plane only. No E03/E04 deliverable is manufactured here.
qaMat=B.material('QA neutral cells','#DDDCCF',1)
for x in range(12):
    for y in range(8):B.box('QA field spacing cell',((x-5.5)*1.2,(y-3.5)*1.2,-.024),(1.17,1.17,.03),qaMat,0)
for o in s.objects:
    if o.name.startswith('QA ground'):o.location.z=-.05
e=math.radians(50);direction=(math.cos(e)/math.sqrt(2),-math.cos(e)/math.sqrt(2),math.sin(e))
# Blender ortho_scale is width for landscape; preserve the specified 14.1 height.
image(s,'farm-distance',(0,0,0),14.1*1280/720,direction,(1280,720))
dump(QA/'source-reopen.json',metrics['source']);print('B14 REVIEW COMPLETE',REV,flush=True)
