"""B14 S01 complete exterior. Independent native editable parts, B02 r04 language.

Only creates a new immutable revision. B02 helpers are imported without executing
their guarded batch entry point. No interiors, vegetation, props or gameplay.
"""
import bpy, bmesh, math, json, sys, hashlib, shutil
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_b02 as B
ROOT=Path(__file__).resolve().parents[1]
REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r01'
SRC=ROOT/f'assets-source/farm-assets/B14/{REV}'
OUT=ROOT/f'public/models/farm-assets/B14/{REV}'
QA=ROOT/f'review/farm-assets/B14/{REV}'
GROUPS={}; CURRENT='walls'

def group(name):
    global CURRENT
    CURRENT=name;GROUPS.setdefault(name,[])
def register(fn,*a,**kw):
    before=set(B.PARTS);o=fn(*a,**kw)
    GROUPS[CURRENT].extend(x for x in B.PARTS if x not in before)
    return o
def box(*a,**kw):return register(B.box,*a,**kw)
def mesh(*a,**kw):return register(B.mesh,*a,**kw)
def extr(*a,**kw):return register(B.extrusion,*a,**kw)
def ring(*a,**kw):return register(B.arch_ring,*a,**kw)
def curve(*a,**kw):return register(B.curve,*a,**kw)
def plug(*a,**kw):return register(B.plug,*a,**kw)
def transform(parts,angle,origin):
    T=Matrix.Translation(Vector(origin))@Matrix.Rotation(angle,4,'Z')
    for o in parts:o.matrix_world=T@o.matrix_world
    bpy.context.view_layer.update()
def applycut(wall,cutter):
    for members in GROUPS.values():
        if cutter in members:members.remove(cutter)
    B.cut(wall,cutter)
def rz(x):return 4.67-1.53*(abs(x)/2.68)**1.65

def surface(name,xa,xb,ya,yb,thickness,mat,lift=0,n=8,bev=.012):
    vs=[]
    for dz in [0,thickness]:
        for y in [ya,yb]:
            for i in range(n+1):
                x=xa+(xb-xa)*i/n;vs.append((x,y,rz(x)+dz+lift))
    N=n+1;fs=[]
    for i in range(n):
        fs.extend([(i,i+1,N+i+1,N+i),(2*N+i,3*N+i,3*N+i+1,2*N+i+1),
                   (i,2*N+i,2*N+i+1,i+1),(N+i,N+i+1,3*N+i+1,3*N+i)])
    fs.extend([(0,N,3*N,2*N),(n,2*N+n,3*N+n,N+n)])
    return B.bevel(mesh(name,vs,fs,mat),bev,3)

def window(wall,origin,angle,width=.86,base=.96,spring=1.60,planter=False,label='window'):
    group('windows');before=set(B.PARTS);r=width/2
    cutter=extr(label+' actual opening',B.profile(r+.026,base-.025,spring),0,-.65,.65,None)
    transform([cutter],angle,origin);applycut(wall,cutter)
    ring(label+' full depth reveal',0,r-.026,r+.027,base,spring,-.13,.17,oak)
    ring(label+' rounded arch casing',0,r-.012,r+.128,base,spring,-.30,-.112,oak)
    extr(label+' inset opaque blue pane',B.profile(r-.027,base+.018,spring),0,-.038,.018,glass,.005)
    box(label+' vertical mullion',(0,-.17,(base+spring+r-.035)/2),(.065,.095,spring+r-.035-base),oak,.014)
    cross=spring-.06;half=(width-.065)/2
    for sign in [-1,1]:box(label+' split horizontal transom',(sign*(.0325+half/2),-.17,cross),(half,.095,.065),oak,.012)
    box(label+' thick sill',(0,-.25,base-.055),(width+.37,.50,.13),lightwood,.026)
    for x in [-width*.35,width*.35]:box(label+' sill corbel',(x,-.20,base-.17),(.12,.29,.18),oak,.022)
    new=[o for o in B.PARTS if o not in before];transform(new,angle,origin)
    if planter:
        # Empty architectural window box; no unrequested E-class flower asset.
        group('window_box');before=set(B.PARTS)
        w=width+.52
        box(label+' planter bottom',(0,-.48,base-.32),(w,.45,.10),oak,.022)
        box(label+' planter front',(0,-.705,base-.18),(w,.09,.26),lightwood,.023)
        box(label+' planter back',(0,-.255,base-.18),(w,.08,.26),oak,.020)
        for sign in [-1,1]:
            box(label+' planter end',(sign*(w/2-.045),-.48,base-.18),(.09,.38,.26),lightwood,.022)
            box(label+' box support',(sign*width*.36,-.36,base-.43),(.12,.28,.19),oak,.024)
        transform([o for o in B.PARTS if o not in before],angle,origin)

def door(wall):
    group('door');origin=(0,-1.63,.18);before=set(B.PARTS)
    cutter=extr('Entrance true arched opening',B.profile(.59,.11,1.39),0,-.65,.65,None)
    transform([cutter],0,origin);applycut(wall,cutter)
    ring('Entrance full depth jamb',0,.555,.592,.13,1.39,-.13,.17,dark)
    ring('Entrance round honey oak casing',0,.57,.72,.13,1.39,-.285,-.12,oak)
    extr('Closed door solid backing',B.profile(.582,.135,1.39),0,.044,.105,dark,.005)
    r=.552
    for k in range(6):
        a=-r+k*2*r/6+.005;b=-r+(k+1)*2*r/6-.005
        poly=[(a,.145),(b,.145)]+[(b+(a-b)*j/8,1.39+math.sqrt(max(0,r*r-(b+(a-b)*j/8)**2))) for j in range(9)]
        extr('Door '+('left' if k<3 else 'right')+' leaf plank '+str(k),poly,0,-.065,.045,wood if k%3 else lightwood,.009)
        if k in [0,2,4]:
            x=(a+b)*.5
            curve('Sparse recessed-colour door grain '+str(k),[(x,-.068,.35),(x+.007,-.068,.65),(x-.006,-.068,1.05)],.0023,dark)
    for x in [-.21,.21]:box('Upper dark timber inlay',(x,-.071,1.47),(.06,.016,.25),dark,.006)
    for x in [-.12,.12]:
        plug('Brass handle rose',(x,-.091,.88),.044,.025,gold)
        plug('Round brass knob',(x,-.121,.88),.026,.046,gold)
    transform([o for o in B.PARTS if o not in before],0,origin)
    group('foundation')
    box('Entrance broad first step',(0,-2.18,.055),(1.76,.88,.11),stone,.025)
    box('Entrance second step',(0,-2.01,.145),(1.60,.59,.09),stone,.022)
    box('Door final threshold',(0,-1.86,.245),(1.37,.51,.11),stone,.022)

def export_groups():
    copies=[];bpy.ops.object.select_all(action='DESELECT')
    for name,parts in GROUPS.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:o.select_set(True)
        bpy.context.view_layer.objects.active=parts[0]
        bpy.ops.object.duplicate();bpy.ops.object.convert(target='MESH');bpy.ops.object.join()
        o=bpy.context.object;o.parent=None;o.name='S01_'+name
        bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        o.data.calc_loop_triangles()
        bad=sum(t.area<1e-12 for t in o.data.loop_triangles)
        if bad:
            print('DEGENERATE',name,[[list(o.data.vertices[i].co) for i in t.vertices] for t in o.data.loop_triangles if t.area<1e-12],flush=True)
            raise RuntimeError(f'{name}: {bad} zero-area triangles')
        copies.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in copies:o.select_set(True)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/'s01-main-house.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
    for o in copies:bpy.data.objects.remove(o,do_unlink=True)

if __name__=='__main__':
    for p in [SRC,OUT,QA]:p.mkdir(parents=True,exist_ok=True)
    if (SRC/'s01-main-house.blend').exists() or (OUT/'s01-main-house.glb').exists():raise RuntimeError('Revision exists. Use a new revision.')
    B.reset()
    cream=B.material('Warm lime plaster','#F4E6C9',.87);stone=B.material('Limestone footing','#DBC9A7',.84)
    oak=B.material('Honey oak frames','#B97635');wood=B.material('Golden oak door','#C88A43')
    lightwood=B.material('Oak plank quiet variation','#D2944B');dark=B.material('Recessed oak end grain','#99602C',.85)
    gold=B.material('Aged brass handles','#DAB859',.58);glass=B.material('Opaque soft sky glass - no transparency','#60B9D2',.42)
    tiles=[B.material('Terracotta tile '+str(i),h,.78) for i,h in enumerate(['#E98436','#EE8D3B','#E68132','#F19743'])]
    soot=B.material('Chimney recessed unlit throat','#504235',.94)
    group('foundation')
    box('Continuous solid footing at ground',(0,0,.09),(4.91,3.71,.18),stone,.045)
    group('walls')
    outline=[(-2.4,.16),(2.4,.16)]+[(2.4-4.8*i/64,rz(2.4-4.8*i/64)+.035) for i in range(65)]
    shell=extr('Continuous 340mm exterior wall shell and shaped gables',outline,0,-1.8,1.8,cream)
    cavity=[(-2.06,.34),(2.06,.34)]+[(2.06-4.12*i/64,rz(2.06-4.12*i/64)-.28) for i in range(65)]
    cutter=extr('Structural thickness cavity - not an interior fitout',cavity,0,-1.46,1.46,None)
    applycut(shell,cutter)
    front=back=shell;sides=[shell,shell]
    door(front)
    for x in [-1.52,1.52]:window(front,(x,-1.63,0),0,.73,.98,1.48,label='Front lower '+str(x))
    window(front,(0,-1.63,0),0,1.08,2.73,3.40,True,'Front upper')
    for x in [-1.23,1.23]:window(back,(x,1.63,0),math.pi,.94,1.03,1.70,label='Rear '+str(x))
    window(back,(0,1.63,0),math.pi,.74,2.98,3.49,label='Rear upper')
    for wall,sign in zip(sides,[-1,1]):
        angle=sign*math.pi/2
        for y in [-.83,.83]:window(wall,(sign*2.23,y,0),angle,.86,1.13,1.82,label=('Left' if sign<0 else 'Right')+' side '+str(y))
    for wall in set([front,back,*sides]):
        B.bevel(wall,.025,3)
        # Boolean/bevel can leave coincident pairs at arc endpoints. Keep this
        # explicit editable cleanup after bevel; no visible-size decimation.
        weld=wall.modifiers.new('Weld coincident bevel endpoints 1 micron','WELD');weld.merge_threshold=.000001
    group('timber_eaves')
    for sign in [-1,1]:
        box('Side oak eave bearer '+str(sign),(sign*2.36,0,3.275),(.25,3.86,.17),oak,.032)
        for y in [-1.32,0,1.32]:
            box('Rounded eave corbel '+str((sign,y)),(sign*2.39,y,3.12),(.39,.17,.31),wood,.035)
    # One continuous deck seals gaps under individually editable roof tiles.
    group('roof')
    surface('Continuous curved terracotta roof deck',-2.68,2.68,-2.06,2.06,.14,tiles[0],n=64,bev=.018)
    for sign in [-1,1]:
        for row in range(6):
            xa=.055+row*(2.625/6)+.004;xb=.055+(row+1)*(2.625/6)-.004
            if sign<0:xa,xb=-xb,-xa
            for j in range(10):
                ya=-2.055+j*.411+.004;yb=-2.055+(j+1)*.411-.004
                surface('Roof tile %s slope %02d lane %02d'%(sign,row,j),xa,xb,ya,yb,.058,tiles[(row+j+int(sign>0))%4],lift=.136,n=4,bev=.012)
    # A softly rounded crest with actual thickness, not a line on the texture.
    for j in range(10):surface('Ridge terracotta cap '+str(j),-.14,.14,-2.08+j*.416+.003,-2.08+(j+1)*.416-.003,.082,tiles[1],lift=.164,n=10,bev=.02)
    group('chimney')
    cx,cy=1.22,.66;bottom=rz(cx)-.22;top=5.18
    box('Chimney front thick wall',(cx,cy-.205,(bottom+top)/2),(.56,.15,top-bottom),cream,.025)
    box('Chimney rear thick wall',(cx,cy+.205,(bottom+top)/2),(.56,.15,top-bottom),cream,.025)
    for sign in [-1,1]:box('Chimney side thick wall',(cx+sign*.205,cy,(bottom+top)/2),(.15,.26,top-bottom),cream,.022)
    box('Chimney dark recessed throat',(cx,cy,top-.20),(.28,.28,.08),soot,.01)
    # Four rim pieces surround the visible opening; no giant solid white plug.
    for y in [-.28,.28]:box('Chimney cap front back',(cx,cy+y,top+.025),(.72,.16,.15),stone,.025)
    for x in [-.28,.28]:box('Chimney cap sides',(cx+x,cy,top+.025),(.16,.40,.15),stone,.022)
    # Roof socket follows the roof slope, an intentional seated assembly.
    surface('Chimney terracotta flashing',cx-.34,cx+.34,cy-.34,cy+.34,.065,tiles[2],lift=.19,n=12,bev=.012)
    export_groups()
    for name,parts in GROUPS.items():B.organize(parts,'S01 editable '+name)
    s=B.studio();B.camera(s,(0,0,2.5),7.3)
    s['asset_scope']='B14 S01 complete CENTRAL HOUSE EXTERIOR. Native editable wall, door, windows, empty architectural window box, roof, timber, chimney and foundation modules. No interior/gameplay.'
    s['scale']='1.2 project cell; Lulu readonly reference height1.2; authored house not normalized.'
    s['entrance']='Clear arch width1.18; threshold .30; spring1.57; crown2.16. Closed door separate editable components. No collision/navigation claim.'
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'s01-main-house.blend'))
    s.render.filepath=str(QA/'initial-quarter.png');bpy.ops.render.render(write_still=True)
    for v,d in [('back',(0,1,.025)),('side',(1,0,.025)),('front',(0,-1,.025))]:
        B.camera(s,(0,0,2.5),7.3,d);s.render.filepath=str(QA/f'initial-{v}.png');bpy.ops.render.render(write_still=True)
    labels={'walls':'四面实体墙','foundation':'地基与入口台阶','door':'拱门与五金','windows':'全部深框窗','window_box':'空窗下木箱','timber_eaves':'木梁与托木','roof':'完整曲面屋顶与瓦片','chimney':'厚壁烟囱与收口'}
    (OUT/'source').mkdir(exist_ok=True);shutil.copy2(SRC/'s01-main-house.blend',OUT/'source/s01-main-house.blend')
    manifest={'batch':'B14','revision':REV,'status':'制作检查中；待用户验收','baseline':'B02 r04 accepted facade language; B01 r03 fixed studio','assets':[{'id':'S01','name':'中央主屋完整外观','file':f'/models/farm-assets/B14/{REV}/s01-main-house.glb','source':f'/models/farm-assets/B14/{REV}/source/s01-main-house.blend','source_kind':'native Blender editable modules','modules':[{'id':k,'name':labels[k],'nodes':['S01_'+k]} for k in GROUPS]}],'checks':{'technical':'待复核','visual':'待实际读图','user':'待验收','device':'未测试'}}
    (OUT.parent/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    (QA/'components.json').write_text(json.dumps({k:[o.name for o in v] for k,v in GROUPS.items()},ensure_ascii=False,indent=2))
    print('B14 NEW CANDIDATE SAVED',REV,flush=True)
