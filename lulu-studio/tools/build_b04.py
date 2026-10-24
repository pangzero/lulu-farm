"""B04 mature bokchoy/lettuce/cauliflower only. Immutable per-revision outputs."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import b04_common as C
from b04_common import mesh,leaf,sphere,mat,linear,mix,smooth
from b04_cauliflower import build_cauliflower
from math import sin,cos,pi,exp
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'assets-source/farm-assets/B04';OUT=ROOT/'public/models/farm-assets/B04';QA=ROOT/'review/farm-assets/B04';REV='r02'
CAMERAS={'bokchoy':{'target':[0,0,.46],'ortho_scale':1.65},'lettuce':{'target':[0,0,.30],'ortho_scale':1.65},'cauliflower':{'target':[0,0,.32],'ortho_scale':1.65}}

def bokchoy():
    stalk=mat('Bokchoy tender basal crown','#DFE7BA',.81)
    sphere('Bokchoy grounded basal crown',(0,0,.045),(.085,.08,.045),stalk)
    paint=mat('Bokchoy ivory spoon to green blade','#FFFFFF',.76,True)
    specs=[]
    for i in range(6):specs.append((i*2*pi/6+.22,.33+.02*sin(i*1.7),.77+.025*cos(i*2),.182+.01*cos(i*3),i))
    for i in range(3):specs.append((i*2*pi/3+.87,.18,.92+.012*sin(i*2),.157,6+i))
    def interp(knots,t):
        for (x,a),(y,b) in zip(knots,knots[1:]):
            if x<=t<=y:return a+(b-a)*smooth(x,y,t)
        return knots[-1][1]
    for angle,reach,height,width,index in specs:
        d=Vector((cos(angle),sin(angle),0));side=Vector((-sin(angle),cos(angle),0))
        def center(t):return d*(.048+reach*sin(t*pi*.54))+Vector((0,0,.03+height*t-.052*t**4))
        vs=[];colors=[];faces=[];nt=44;nr=24
        # A closed elliptical spoon stalk fattens near the root, narrows at the
        # neck, and flares into a curved blade in the SAME continuous mesh.
        for i in range(nt):
            t=i/nt;p=center(t);tangent=center(min(1,t+.001))-center(max(0,t-.001))
            normal=side.cross(tangent).normalized()
            w=interp([(0,.044),(.14,.106),(.31,.089),(.43,.074),(.59,width),(.76,width*.92),(1,0)],t)
            depth=interp([(0,.036),(.14,.072),(.31,.055),(.45,.020),(.59,.010),(1,.003)],t)
            green=smooth(.38,.59,t)
            for j in range(nr):
                aa=2*pi*j/nr;u=cos(aa)
                q=p+side*(w*u)+normal*(depth*sin(aa)+.028*u*u*sin(pi*t)*green)
                q.z+=.009*sin(8*t+index)*abs(u)**4*sin(pi*t)*green
                vs.append(q)
                pale=mix(linear('#F0F1D3'),linear('#D0DEAA'),.22+.22*t)
                blade=mix(linear('#2E8537'),linear('#69AD42'),.18+.62*t)
                blade=mix(blade,linear('#B7D37A'),exp(-(u/.14)**2)*.30)
                colors.append(mix(pale,blade,green))
        tip=len(vs);vs.append(center(1));colors.append(linear('#78B94E'))
        bottom=len(vs);vs.append(center(0));colors.append(linear('#E9EEC9'))
        for j in range(nr):
            k=(j+1)%nr;faces.append((bottom,k,j));faces.append((tip,(nt-1)*nr+j,(nt-1)*nr+k))
        for i in range(nt-1):
            for j in range(nr):
                k=(j+1)%nr;faces.append((i*nr+j,i*nr+k,(i+1)*nr+k,(i+1)*nr+j))
        o=mesh('Bokchoy solid swollen spoon stalk continuous blade %02d'%(index+1),vs,faces,paint,colors)
        m=o.modifiers.new('Rounded fleshy petiole and soft blade','SUBSURF');m.levels=m.render_levels=1

def lettuce():
    rootmat=mat('Lettuce tender low root','#92B55B',.84)
    sphere('Lettuce grounded short crown',(0,0,.04),(.055,.052,.04),rootmat)
    for row,n in enumerate([7,6,4]):
        for i in range(n):
            angle=i*2*pi/n+row*.67+.075*sin(i*2.1);d=Vector((cos(angle),sin(angle),0));side=Vector((-sin(angle),cos(angle),0))
            reach=[.43,.29,.14][row]*(1+.055*sin(i*2.3+row));height=[.39,.54,.55][row];width=[.225,.20,.135][row];phase=i*.94+row*.7
            def point(t,u,d=d,side=side,reach=reach,height=height,width=width,row=row,phase=phase):
                env=sin(pi*t)**.62
                r=.019+reach*sin(t*pi*[.66,.62,.85][row])-.070*u*u*env
                # Broad accordion folds and rolled margins, not a spherical heart.
                edge=abs(u)**3.5
                r+=.032*sin(6*pi*t+phase)*edge*env
                p=d*r+side*(u*width*env*(1+.12*sin(5*pi*t+phase)*edge))
                p.z=.025+height*t-[.17,.085,.045][row]*t**4+.067*u*u*env
                p.z+=.050*sin(6*pi*t+phase+u*.8)*edge*env+.018*cos(3*pi*u+phase)*sin(pi*t)**2
                p.z+=.012*exp(-(u/.16)**2)*env
                return p
            colors=[('#3E942C','#A3CD4B','#CCDE86'),('#559D2E','#B5D65B','#D5E69A'),('#79B03B','#C8DC70','#E0EAA8')][row]
            leaf('Lettuce loose rolled ruffled blade row%d leaf%02d'%(row+1,i+1),point,colors,.017,40,26,True)

def studio():
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=s.render.resolution_y=768;s.render.resolution_percentage=100
    s.world=bpy.data.worlds.new('B01 neutral studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.80,.75,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.32
    s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
    for name,loc,power,size in [('Key',(-3,-4,6),280,4),('Fill',(4,-1,3),140,3),('Rim',(0,4,5),230,3)]:
        d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.shape='DISK';d.size=size
    ground=mat('QA ground only','#F4F2E8',1);bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));o=bpy.context.object;o.name='QA ground not exported';o.data.materials.append(ground)
    d=bpy.data.cameras.new('B04 fixed camera');o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);s.camera=o;d.type='ORTHO';return s

def evaluated_min_z(parts):
    deps=bpy.context.evaluated_depsgraph_get();values=[]
    for o in parts:
        e=o.evaluated_get(deps);me=e.to_mesh();values.extend((o.matrix_world@v.co).z for v in me.vertices);e.to_mesh_clear()
    return min(values)

def build(crop):
    source=SRC/f'{crop}-mature-{REV}.blend';export=OUT/f'{crop}-mature-{REV}.glb'
    if source.exists() or export.exists():raise RuntimeError('Existing candidate is immutable. Use a new REV.')
    bpy.ops.wm.read_factory_settings(use_empty=True);C.PARTS.clear();bpy.context.preferences.filepaths.save_version=0
    {'bokchoy':bokchoy,'lettuce':lettuce,'cauliflower':build_cauliflower}[crop]();parts=list(C.PARTS)
    bpy.context.view_layer.update();offset=-evaluated_min_z(parts)
    for o in parts:o.location.z+=offset
    col=bpy.data.collections.new('PRODUCTION B04 '+crop+' mature');bpy.context.scene.collection.children.link(col)
    for o in parts:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.duplicate();bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.ops.object.join();o=bpy.context.object;o.name=f'{crop}_mature_{REV}'
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');o.data.calc_loop_triangles()
    bad=sum(t.area<1e-12 for t in o.data.loop_triangles)
    if bad:raise RuntimeError(f'{crop}: {bad} degenerate export triangles')
    bpy.ops.export_scene.gltf(filepath=str(export),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
    bpy.data.objects.remove(o,do_unlink=True)
    s=studio();cfg=CAMERAS[crop];t=Vector(cfg['target']);s.camera.location=t+Vector((1.35,-4,2.25)).normalized()*6;s.camera.rotation_euler=(t-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=cfg['ortho_scale']
    s['scope']='B04 '+crop+' mature only; no other growth stages';s['ground_alignment_offset']=offset;s['unit_cell']=1.2
    bpy.ops.wm.save_as_mainfile(filepath=str(source));s.render.filepath=str(QA/f'{crop}-{REV}-initial.png');bpy.ops.render.render(write_still=True)
    print('B04 BUILT',crop,flush=True)

if __name__=='__main__':
    for p in [SRC,OUT,QA]:p.mkdir(parents=True,exist_ok=True)
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['bokchoy','lettuce','cauliflower']
    for crop in args:build(crop)
    if set(args)=={'bokchoy','lettuce','cauliflower'}:
        (OUT/'manifest.json').write_text(json.dumps({'batch':'B04','revision':REV,'stage':'mature','status':'待用户验收','cell':1.2,'lulu_scale':.6313689262131015,'crops':[{'id':c,'revision':REV,'stage':'mature','status':'待用户验收','file':f'/models/farm-assets/B04/{c}-mature-{REV}.glb','source':f'assets-source/farm-assets/B04/{c}-mature-{REV}.blend'} for c in args]},ensure_ascii=False,indent=2))
