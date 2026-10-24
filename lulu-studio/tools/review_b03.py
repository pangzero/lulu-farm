"""Reopen sources, import real GLBs, measure interfaces and render B03 evidence."""
import bpy,bmesh,json,hashlib,struct,math,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_b03 as build
ROOT=build.ROOT;QA=build.QA;SRC=build.SRC;OUT=build.OUT;REV='r03'
VIEWS={'front':(0,-1,.025),'side':(1,0,.025),'back':(0,1,.025),'quarter':(1.35,-4,2.25),'top':(0,-.001,1)}
SETTINGS=json.loads((ROOT/'review/farm-assets/B01/review-settings.json').read_text())
SETTINGS.update({'batch':'B03','revision':REV,'cell':1.2,'land_z':0,'water_z':-.105,'views':VIEWS,'cameras':{a:{'target':[0,0,.15 if a=='e13' else -.03],'ortho_scale':1.8} for a in build.ASSETS},'qa_ground_top':{'e01':-.19,'e05':-.29,'e07':-.14,'e13':-.01},'reuse':'B01 lights/color/scale/farm camera. Near camera framing adapted to terrain; no asset scaling.', 'water':{'mesh':'Flat open sheet, z=-0.105; no thickness/displacement','glb':'Opaque roughness 0.35; embedded 512px seamless image','web':'Optional world-space sine color modulation +/-5.5%; geometry stays fixed; no transparency/underwater visibility'}})
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def import_glb(p):
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p));bpy.context.view_layer.update();return [o for o in set(bpy.data.objects)-before if o.type=='MESH']
def stats(a,rev=REV):
    bpy.ops.wm.read_factory_settings(use_empty=True);path=OUT/f'{a}-{rev}.glb';obs=import_glb(path)
    vs=[o.matrix_world@v.co for o in obs for v in o.data.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
    boundaries={};raw_boundaries={};vol={};dups=0
    for o in obs:
        bm=bmesh.new();bm.from_mesh(o.data);raw_boundaries[o.name]=sum(e.is_boundary for e in bm.edges)
        # glTF legitimately splits vertices at UV/normal/color seams. Weld only a diagnostic copy.
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        boundaries[o.name]=sum(e.is_boundary for e in bm.edges);vol[o.name]=bm.calc_volume(signed=True) if not boundaries[o.name] else None;bm.free()
        faces=[tuple(sorted(p.vertices)) for p in o.data.polygons];dups+=len(faces)-len(set(faces))
    raw=path.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    triangles=sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
    result={'asset':a,'revision':rev,'file':str(path.relative_to(ROOT)),'source':str((SRC/f'{a}-{rev}.blend').relative_to(ROOT)),'sha256':sha(path),'source_sha256':sha(SRC/f'{a}-{rev}.blend'),'bytes':len(raw),'triangles':triangles,'vertices_imported':len(vs),'mesh_nodes':len(obs),'materials':len(g.get('materials',[])),'textures':[{'name':im.name,'size':list(im.size)} for im in bpy.data.images if im.size[0]>0],'external_uris':[x['uri'] for typ in ['images','buffers'] for x in g.get(typ,[]) if 'uri'in x and not x['uri'].startswith('data:')],'bbox_blender_z_up':[lo,hi],'dimensions':[hi[i]-lo[i] for i in range(3)],'zero_area_faces':sum(p.area<1e-12 for o in obs for p in o.data.polygons),'duplicate_index_faces':dups,'nonfinite_vertices':sum(not all(math.isfinite(c) for c in v) for v in vs),'boundary_edges':boundaries,'signed_mesh_volumes':vol,'negative_transform_objects':[o.name for o in obs if o.matrix_world.determinant()<0],'import_status':'success','export_contains_qa':any('QA' in o.name for o in obs),'glb_origin':'scene origin (0,0,0), Blender Z up exported to glTF Y up; source component pivots retained'}
    result['raw_index_boundary_edges']=raw_boundaries
    result['boundary_method']='Geometric diagnostic copy welded at 1e-6; exported mesh left unchanged. E07 open perimeter is intentional.'
    if a in ['e01','e05','e07']:
        target='foundation' if a=='e01' else 'bank core' if a=='e05' else 'water sheet'
        ob=next(o for o in obs if target in o.name);pvs=[ob.matrix_world@v.co for v in ob.data.vertices]
        left=sorted(set((round(v.y,6),round(v.z,6)) for v in pvs if abs(v.x+.6)<1e-5));right=sorted(set((round(v.y,6),round(v.z,6)) for v in pvs if abs(v.x-.6)<1e-5))
        xmin=min(v.x for v in pvs);xmax=max(v.x for v in pvs)
        result['interface']={'pitch':1.2,'x_repeat_gap':1.2+xmin-xmax,'left_profile':left,'right_profile':right,'matching_end_profile':left==right}
        if a=='e01':
            ob=next(o for o in obs if 'continuous soil' in o.name);v=min(ob.data.vertices,key=lambda v:v.co.x*v.co.x+v.co.y*v.co.y if v.co.z>-.1 else 100);result['soil_center_z']=v.co.z
        if a=='e07':result['water_z_range']=[min(v.z for v in pvs),max(v.z for v in pvs)]
    return result

def near_camera(sc,a,view='quarter',scale=None):
    cfg=SETTINGS['cameras'][a];build.aim(sc,cfg['target'],VIEWS[view],scale or cfg['ortho_scale']);sc.render.resolution_x=sc.render.resolution_y=768
def image(sc,name):build.render(sc,QA/name)

def render_asset(a):
    bpy.ops.wm.open_mainfile(filepath=str(SRC/f'{a}-{REV}.blend'));sc=bpy.context.scene
    prod=[o for o in sc.objects if o.type=='MESH' and o.name!='QA ground']
    for view in VIEWS:near_camera(sc,a,view);image(sc,f'{a}-{REV}-material-{view}.png')
    original={o.name:list(o.data.materials) for o in prod};clay=build.material('B03 neutral diagnostic gray','#A3A3A3',.85)
    for o in prod:
        for i in range(len(o.data.materials)):o.data.materials[i]=clay
    for view in VIEWS:near_camera(sc,a,view);image(sc,f'{a}-{REV}-clay-{view}.png')
    for o in prod:
        for i,m in enumerate(original[o.name]):o.data.materials[i]=m
    detail={'e01':((.46,-.46,.015),.50),'e05':((.30,-.10,-.015),.70),'e07':((0,0,-.105),.86),'e13':((-.12,.04,.20),.85)}[a]
    build.aim(sc,detail[0],VIEWS['quarter'],detail[1]);image(sc,f'{a}-{REV}-detail.png')
    # Same-light same-scale exported r01/r02/r03 evidence, no source substitution.
    for o in prod:o.hide_render=True
    for rev in ['r01','r02','r03']:
        obs=import_glb(OUT/f'{a}-{rev}.glb');near_camera(sc,a);image(sc,f'{a}-{rev}-glb-controlled.png')
        for o in obs:bpy.data.objects.remove(o,do_unlink=True)
    print('B03 FIVE VIEWS AND READBACK',a,flush=True)

def assemble(mode):
    bpy.ops.wm.read_factory_settings(use_empty=True);build.PARTS.clear();sc=build.setup()
    cache={}
    def asset(path,x=0,y=0,scale=1):
        if path not in cache:
            cache[path]=import_glb(ROOT/path)
            for o in cache[path]:o.hide_render=True
        copies=[]
        for base in cache[path]:
            o=base.copy();o.data=base.data;sc.collection.objects.link(o);o.hide_render=False;o.location=base.location*scale+Vector((x,y,0));o.scale=base.scale*scale;copies.append(o)
        return copies
    def env(a,x=0,y=0):return asset(f'public/models/farm-assets/B03/{a}-{REV}.glb',x,y)
    def crop(c,x,y):return asset(f'public/models/farm-assets/B01/{c}-mature-r03.glb',x,y)
    if mode in ['tiles','empty-tiles']:
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                env('e01',x*1.2,y*1.2)
                if mode=='tiles' and y!=-1:crop(['cabbage','tomato','corn'][x+1],x*1.2,y*1.2)
        target=(0,0,.35);height=5.0;d=VIEWS['quarter'];sc.objects['QA ground'].location.z=-.20
    elif mode=='shore':
        for x in [-1,0,1]:
            env('e05',x*1.2,0);env('e01',x*1.2,1.2)
            for y in range(3):env('e07',x*1.2,-y*1.2)
        env('e13',-1.2,1.2);target=(0,-.6,-.03);height=5.4;d=VIEWS['quarter']
    else:
        neutral=build.material('QA flat bench only','#D4D8B8',1)
        build.box('QA 12x8 extent',(0,0,-.31),(14.4,9.6,.05),neutral,0)
        for x,y,w,l in [(-3.6,0,7.2,9.6),(3.6,3.3,7.2,3)]:build.box('QA level land support',(x,y,-.15),(w,l,.27),neutral,0)
        for x in range(3):
            for y in range(3):env('e01',(x-4)*1.2,-(y-1)*1.2);crop(['cabbage','tomato','corn'][x],(x-4)*1.2,-(y-1)*1.2)
        for x in range(4):
            env('e05',(x+.6)*1.2,1.2)
            for y in range(4):env('e07',(x+.6)*1.2,-(y-1)*1.2)
        env('e13',1.5,2.2);env('e13',4.2,2.4)
        lu=asset('public/models/lulu-meshy-notail.glb',-.45,-1,.6313689262131015)
        bpy.context.view_layer.update();lowest=min((o.matrix_world@Vector(v))[2] for o in lu for v in o.bound_box)
        for o in lu:o.location.z-=lowest
        el=math.radians(50);d=(cos(el)/math.sqrt(2),-cos(el)/math.sqrt(2),sin(el));target=(0,0,0);height=14.1
    # Blender ortho_scale is horizontal for a landscape frame; B01 web height * aspect.
    sc.render.resolution_x=1280;sc.render.resolution_y=720;build.aim(sc,target,d,height*1280/720)
    bpy.ops.wm.save_as_mainfile(filepath=str(QA/f'check-{mode}-{REV}.blend'));image(sc,f'{mode}-{REV}-1280x720.png')
    if mode=='shore':
        build.aim(sc,(0,-.05,-.06),(1,0,.035),2.2);image(sc,f'shore-{REV}-section.png')
        build.aim(sc,(.6,-.18,-.08),VIEWS['quarter'],.90);sc.render.resolution_x=sc.render.resolution_y=768;image(sc,f'shore-{REV}-seam-detail.png')
    print('B03 ASSEMBLY',mode,flush=True)

def main():
    metrics={a:stats(a) for a in build.ASSETS};dump(QA/'metrics.json',metrics);dump(QA/'review-settings.json',SETTINGS)
    dump(OUT/'manifest.json',{'batch':'B03','revision':REV,'revisions':['r03','r02','r01'],'status':'待用户验收','phase':'静态环境样板','cell':1.2,'land_z':0,'water_z':-.105,'metrics':metrics,'assets':[{'id':a,'name':n,'source':f'assets-source/farm-assets/B03/{a}-{REV}.blend','file':f'/models/farm-assets/B03/{a}-{REV}.glb'} for a,n in build.ASSETS.items()]})
    for a in build.ASSETS:render_asset(a)
    for mode in ['empty-tiles','tiles','shore','farm']:assemble(mode)
    print('B03 REVIEW COMPLETE',flush=True)

if __name__=='__main__':
    from math import sin,cos
    main()
