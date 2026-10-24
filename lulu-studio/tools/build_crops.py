"""Native editable Blender crop library. Run with Blender --background --python ...

All authored plant geometry is generated here; no former farm assets are reused.
Z is up in .blend, glTF export converts to Y-up. One plant occupies one 1.2-unit cell.
"""
import bpy
import math
import json
import struct
import sys
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/models/crops'
SOURCE = ROOT / 'assets-source/crops'
REVIEW = ROOT / 'review/crops'
for folder in (OUT, SOURCE, REVIEW): folder.mkdir(parents=True, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = set(ARGS) - {'--render'}
RENDER = '--render' in ARGS
STAGES = ['sprout', 'growing', 'mature']
STAGE_NAMES = ['幼苗', '成长', '成熟']
PALETTE = {
    'leaf': '#65B944', 'leaf_light': '#8FD34D', 'leaf_deep': '#439538',
    'vein': '#AFDC6D', 'stem': '#4C9F3E', 'cabbage': '#B1DF63',
    'tomato': '#EE5536', 'tomato_light': '#FA6A3F', 'green_fruit': '#9DC64D',
    'yellow': '#F8C941', 'gold': '#EBAF30', 'corn_pale': '#FFE079',
    'white': '#EFF1D1', 'cream': '#FFF1C8', 'brown': '#95603A',
    'orange': '#F59C29', 'orange_light': '#FFB743', 'pink': '#EC81A2',
    'pink_light': '#F5A3B9', 'berry': '#EE4D48', 'melon': '#70B64B',
    'melon_dark': '#358D43', 'zucchini': '#499C43', 'bulb': '#F2EFD7',
}
MATS = {}
PARTS = []
COLLECTION = None

def linear(v): return v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4
def color(h): return tuple(linear(int(h[i:i+2], 16)/255) for i in (1, 3, 5))
def mat(key):
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new('Crop_' + key)
    m.diffuse_color = (*color(PALETTE[key]), 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = m.diffuse_color
    p.inputs['Roughness'].default_value = .78
    p.inputs['Specular IOR Level'].default_value = .22
    MATS[key] = m
    return m

def register(o, name, key, part='foliage'):
    o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    COLLECTION.objects.link(o)
    o.data.materials.append(mat(key))
    o['part'] = part
    if o.type == 'MESH':
        for f in o.data.polygons: f.use_smooth = True
    PARTS.append(o)
    return o

def mesh(name, vertices, faces, key, part='foliage'):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    o = bpy.data.objects.new(name, data)
    COLLECTION.objects.link(o)
    data.materials.append(mat(key))
    for f in data.polygons: f.use_smooth = True
    o['part'] = part
    PARTS.append(o)
    return o

def sphere(name, center, scale, key, part='produce', seg=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=center)
    o = register(bpy.context.object, name, key, part)
    o.scale = scale
    return o

def tube(name, points, radius, key='stem', part='stem', sides=5):
    # Polyline rings provide predictable export tessellation and real rounded stems.
    points = [Vector(p) for p in points]
    vertices = []
    for i,p in enumerate(points):
        tangent = (points[min(i+1,len(points)-1)] - points[max(0,i-1)]).normalized()
        guide = Vector((0,0,1)) if abs(tangent.z) < .9 else Vector((1,0,0))
        x = tangent.cross(guide).normalized(); y = tangent.cross(x).normalized()
        r = radius * (1 - .38 * i / max(1,len(points)-1))
        for j in range(sides):
            a = j * 2*math.pi/sides
            vertices.append(p + r*(math.cos(a)*x + math.sin(a)*y))
    faces = []
    for i in range(len(points)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces += [tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))]
    return mesh(name, vertices, faces, key, part)

def leaf(name, base=(0,0,0), angle=0, length=.35, width=.16, rise=.15,
         arch=.08, cup=.045, key='leaf', lobes=0, vein=False, shape=.72, n=9, w=4):
    base=Vector(base); d=Vector((math.cos(angle),math.sin(angle),0)); s=Vector((-d.y,d.x,0))
    vertices=[]; centers=[]
    for i in range(n+1):
        t=i/n
        bend=.05*length*math.sin(math.pi*t)
        center=base + d*(length*t) + s*bend + Vector((0,0,rise*t+arch*math.sin(math.pi*t)))
        centers.append(center)
        breadth=max(.015,math.sin(math.pi*t)**shape) * width
        breadth*=1+lobes*math.sin(t*math.pi*5)**2
        for j in range(w+1):
            u=2*j/w-1
            wave=lobes*.028*math.sin(t*math.pi*5)*(abs(u)**3)
            vertices.append(center+s*(u*breadth)+Vector((0,0,cup*u*u*math.sin(math.pi*t)+wave)))
    faces=[]
    for i in range(n):
        for j in range(w):
            a=i*(w+1)+j
            faces.append((a,a+w+1,a+w+2,a+1))
    o=mesh(name,vertices,faces,key)
    solid=o.modifiers.new('Leaf thickness','SOLIDIFY');solid.thickness=.009;solid.offset=0
    if vein:
        tube(name+'_midrib',[p+Vector((0,0,.005)) for p in centers[:-1]],.0038,'vein','veins',4)
        for k in (3,5,7):
            if k>=n: continue
            for side in (-1,1):
                points=[]
                for j in range(4):
                    q=j/3;t=(k+q)/n;u=.72*q*side
                    center=base+d*(length*t)+s*(.05*length*math.sin(math.pi*t))+Vector((0,0,rise*t+arch*math.sin(math.pi*t)))
                    span=width*math.sin(math.pi*t)**shape*(1+lobes*math.sin(t*math.pi*5)**2)
                    wave=lobes*.028*math.sin(t*math.pi*5)*abs(u)**3
                    points.append(center+s*(span*u)+Vector((0,0,cup*u*u*math.sin(math.pi*t)+wave+.005)))
                tube(name+'_side_vein',points,.0022,'vein','veins',3)
    return o

def sprout(seed, leaves=2, length=.16, height=.15):
    tube('Seedling_stem',[(0,0,0),(.008,0,height*.5),(0,0,height)],.014)
    for i in range(leaves):
        leaf('Cotyledon', (0,0,height*.65), i*2*math.pi/leaves+.25*seed, length, length*.42,
             rise=height*.25,arch=.025,key='leaf_light',n=7,w=4)

def cabbage(stage):
    if stage==0: return sprout(1,3,.14,.08)
    tube('Cabbage_short_stem',[(0,0,0),(0,0,.10)],.045)
    head=.19 if stage==1 else .29
    sphere('Cabbage_heart',(0,0,head+.045),(head,head,head*.96),'cabbage',seg=24,rings=14)
    for i in range(6 if stage==1 else 8):
        a=2*math.pi*i/(6 if stage==1 else 8)+.18
        leaf('Outer_cupped_leaf',(.02*math.cos(a),.02*math.sin(a),.035),a,
             length=.31 if stage==1 else .43,width=.14 if stage==1 else .19,
             rise=.17 if stage==1 else .27,arch=.045,cup=.08,
             key=['leaf','leaf_light','leaf_deep'][i%3],vein=True,n=10,w=6)
    # Overlapping spherical leaf patches create the wrapped head, rather than a smooth ball.
    for k in range(5):
        az=k*2*math.pi/5+.35
        verts=[]; faces=[]
        for i in range(10):
            t=i/9; polar=.22+1.83*t
            for j in range(7):
                u=j/6*2-1
                theta=az+u*.82*math.sin(math.pi*(.12+.76*t))
                r=head*(1.018+k*.012+.004*math.sin(math.pi*t))
                verts.append((r*math.sin(polar)*math.cos(theta),r*math.sin(polar)*math.sin(theta),head+.045+r*.96*math.cos(polar)))
        for i in range(9):
            for j in range(6):
                a=i*7+j;faces.append((a,a+7,a+8,a+1))
        o=mesh('Wrapped_head_leaf',verts,faces,'cabbage' if k%2 else 'leaf_light')
        m=o.modifiers.new('Thin head leaf','SOLIDIFY');m.thickness=.007

def calyx(center,radius,angle=0):
    for i in range(5):
        leaf('Fruit_calyx',center,angle+i*2*math.pi/5,radius,radius*.22,rise=.025,arch=.012,cup=.008,key='leaf_deep',n=5,w=2)

def flower(center,radius=.06,key='yellow',petals=5):
    x,y,z=center
    for i in range(petals):
        a=i*2*math.pi/petals
        o=sphere('Flower_petal',(x+math.cos(a)*radius*.57,y-.008,z+math.sin(a)*radius*.57),(radius*.43,.016,radius*.65),key,'bloom',12,8)
        o.rotation_euler.y=a-math.pi/2
    sphere('Flower_center',(x,y-.022,z),(radius*.27,.02,radius*.27),'yellow' if key=='white' else 'gold','bloom',12,8)

def tomato(stage):
    if stage==0: return sprout(2,2,.19,.18)
    h=.49 if stage==1 else .86
    tube('Tomato_main_stem',[(0,0,0),(.015,0,h*.3),(-.025,.01,h*.65),(.015,0,h)],.023)
    for i in range(5):
        a=i*2.39+.45;z=h*(.29+.12*i);start=Vector((0,0,z));end=start+Vector((.13*math.cos(a),.13*math.sin(a),.045))
        tube('Leaf_branch',[start,(start+end)/2,end],.012)
        leaf('Tomato_leaf',end,a,.20 if stage==1 else .27,.085 if stage==1 else .11,rise=.07,arch=.05,lobes=.28,key=['leaf','leaf_light'][i%2],n=10,w=4)
    positions=[(-.18,-.08,h*.53),(.20,-.06,h*.39),(.11,.13,h*.73)]
    for i,p in enumerate(positions[:1 if stage==1 else 3]):
        r=.062 if stage==1 else [.14,.16,.095][i]
        top=Vector(p)+Vector((0,0,r*.9))
        tube('Fruit_pedicel',[(0,0,p[2]+.12),(p[0]*.7,p[1]*.7,p[2]+.12),top],.01)
        sphere('Tomato_fruit',p,(r,r,r*.9),'green_fruit' if stage==1 else ['tomato','tomato_light','tomato'][i],seg=20,rings=12)
        calyx(top,r*.66)
    flower((-.09,-.04,h*.90),.045)

def corn(stage):
    if stage==0:
        tube('Corn_shoot',[(0,0,0),(0,0,.17)],.016)
        for i in range(3): leaf('Corn_first_blade',(0,0,.04),i*2.1,.21,.042,rise=.15,arch=.035,key='leaf_light',shape=1,n=9,w=4)
        return
    h=.69 if stage==1 else 1.25
    tube('Corn_stalk',[(0,0,0),(.014,0,h*.5),(.02,0,h)],.028)
    for i in range(6):
        a=i*2.6+.3
        leaf('Corn_arching_leaf',(0,0,h*(.13+.12*i)),a,.31 if stage==1 else .48,.065 if stage==1 else .09,
             rise=.12 if stage==1 else .19,arch=.11,cup=.022,key=['leaf','leaf_light'][i%2],shape=1.0,n=12,w=4)
    if stage==1: return
    base=Vector((.03,-.03,.55));axis=Vector((.30,-.17,.94)).normalized();length=.43
    ear=sphere('Corn_cob_core',base+axis*length*.5,(.073,.073,length*.53),'gold',seg=16,rings=10)
    ear.rotation_mode='QUATERNION';ear.rotation_quaternion=Vector((0,0,1)).rotation_difference(axis)
    u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
    for row in range(9):
        t=(row+.5)/9;radius=.070*math.sin(math.pi*(.08+.84*t))**.30
        for j in range(8):
            a=j*2*math.pi/8
            p=base+axis*(t*length)+(u*math.cos(a)+v*math.sin(a))*radius
            kernel=sphere('Rounded_kernel',p,(.027,.027,.024),'yellow' if (row+j)%3 else 'corn_pale','produce',8,5)
            kernel.rotation_mode='QUATERNION';kernel.rotation_quaternion=ear.rotation_quaternion
    for i in range(3):
        leaf('Corn_husk',base,i*2.1+.4,.14,.055,rise=.32,arch=.04,key='leaf_light',shape=1,n=10,w=4)
    for a in (-.45,0,.45):
        tube('Corn_tassel',[(.02,0,1.16),(.02+a*.06,0,1.29),(.02+a*.15,.005,1.34)],.0065,'gold','bloom',4)

def curved_fruit(name,center,radius,length,key,axis=(0,0,1),lobes=0):
    # Closed ring mesh with softly rounded ends, suitable for gourds and berries.
    center=Vector(center);axis=Vector(axis).normalized()
    u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u)
    verts=[];faces=[];ns=48 if lobes else 20;nr=14
    for i in range(nr+1):
        t=i/nr;profile=max(.008,math.sin(math.pi*t)**.55)
        for j in range(ns):
            a=j*2*math.pi/ns;r=radius*profile*(1+lobes*math.cos(a*8))
            verts.append(center+axis*((t-.5)*length)+u*(r*math.cos(a))+v*(r*math.sin(a)))
    for i in range(nr):
        for j in range(ns):
            a=i*ns+j;b=i*ns+(j+1)%ns;faces.append((a,b,b+ns,a+ns))
    faces.extend([tuple(reversed(range(ns))),tuple(nr*ns+j for j in range(ns))])
    return mesh(name,verts,faces,key,'produce')

def vine_plant(stage,kind):
    if stage==0:return sprout(4,2,.16,.10)
    mature=stage==2;h=.40 if mature else .25
    tube('Vine_stem',[(0,0,0),(.04,0,h*.5),(0,.015,h)],.023)
    for i in range(5 if mature else 3):
        a=i*2.4+.2;z=.065+i*.045
        leaf('Lobed_gourd_leaf',(0,0,z),a,.33 if mature else .24,.13 if mature else .10,rise=.13,arch=.065,cup=.035,lobes=.30,vein=True,n=10,w=4)
    if mature:
        for i,p in enumerate([(-.16,-.14,.21),(.18,-.06,.18)]):
            is_cuke=kind=='cucumber';axis=Vector((.30 if i else -.35,.1,.94)).normalized()
            curved_fruit('Cucumber' if is_cuke else 'Zucchini',p,.067 if is_cuke else .085,.34 if is_cuke else .31,'zucchini',axis)
            top=Vector(p)+axis*.17
            tube('Fruit_stem',[top,(0,0,.30)],.012)
            if is_cuke:
                for j in range(10):
                    a=j*2.4;t=(j%5)/5-.4
                    q=Vector(p)+axis*(t*.24)+Vector((math.cos(a)*.06,math.sin(a)*.06,0))
                    sphere('Tiny_cucumber_bump',q,(.007,.007,.007),'leaf_light',seg=6,rings=4)
        flower((.06,-.04,h+.06),.055)
    else:flower((.04,-.01,h+.025),.025)

def pumpkin(stage):
    if stage==0:return sprout(5,2,.16,.09)
    for i in range(4 if stage==2 else 3):
        a=i*2.1+.1
        leaf('Pumpkin_leaf',(0,.03,.04),a,.43 if stage==2 else .26,.16 if stage==2 else .11,rise=.13,arch=.06,cup=.04,lobes=.22,vein=True)
    r=.29 if stage==2 else .11;z=r*.77
    curved_fruit('Ribbed_pumpkin',(.05,-.08,z),r,r*1.5,'orange' if stage==2 else 'green_fruit',lobes=.12)
    tube('Pumpkin_curved_stem',[(.05,-.08,z+r*.72),(.045,-.08,z+r*.98),(.10,-.07,z+r*1.06)],.026,'brown')
    if stage==2:
        pts=[]
        for i in range(24):
            t=i/23;a=t*math.pi*3;pts.append((.11+t*.20,-.04+.035*math.sin(a),.06+.035*math.cos(a)))
        tube('Curled_tendril',pts,.007)

def sunflower(stage):
    if stage==0:return sprout(6,2,.17,.17)
    h=.56 if stage==1 else 1.08
    tube('Sunflower_stem',[(0,0,0),(.02,0,h*.6),(0,0,h)],.027)
    for i in range(4):leaf('Sunflower_leaf',(0,0,h*(.17+i*.15)),i*2.5,.23,.11,rise=.10,arch=.05,cup=.025,lobes=.08,vein=True)
    if stage==1:
        sphere('Green_flower_bud',(0,0,h),(.08,.075,.10),'leaf_light','bloom');return
    center=Vector((0,0,h));radius=.23
    for i in range(15):
        a=i*2*math.pi/15;o=sphere('Sunflower_golden_petal',center+Vector((math.cos(a)*radius*.77,-.014,math.sin(a)*radius*.77)),(.047,.024,.13),'yellow' if i%2 else 'corn_pale','bloom',12,8)
        o.rotation_euler.y=math.pi/2-a
    sphere('Sunflower_seed_disk',(0,-.037,h),(.124,.045,.124),'brown','bloom',20,12)
    for i in range(26):
        a=i*2.4;r=.098*math.sqrt((i+.5)/26)
        sphere('Seed_disk_detail',(r*math.cos(a),-.078,h+r*math.sin(a)),(.009,.006,.009),'gold','bloom',6,4)

def wheat(stage):
    if stage==0:
        for i in range(3):leaf('Wheat_shoot',(0,0,.01),i*2.2,.12,.018,rise=.20,arch=.025,key='leaf_light',shape=1)
        return
    for i in range(5 if stage==2 else 3):
        a=i*2.4;base=Vector((math.cos(a)*.07,math.sin(a)*.07,0));h=(.67 if stage==2 else .39)+.06*math.sin(i*1.8)
        key='gold' if stage==2 else 'stem';top=base+Vector((.03*math.cos(a),.03*math.sin(a),h))
        tube('Wheat_stalk',[base,top],.009,key)
        leaf('Wheat_blade',base+Vector((0,0,h*.35)),a,.20,.025,rise=.15,arch=.04,key='corn_pale' if stage==2 else 'leaf_light',shape=1,n=9,w=2)
        if stage==2:
            for row in range(5):
                for side in (-1,1):
                    p=top+Vector((side*(.025-row*.002),0,row*.035));o=sphere('Wheat_grain',p,(.018,.018,.038),'yellow','produce',10,6);o.rotation_euler.y=side*.50
            for side in (-1,1):tube('Wheat_awn',[top+Vector((side*.025,0,.10)),top+Vector((side*.05,0,.24))],.0028,'corn_pale','bloom',3)

def bokchoy(stage):
    if stage==0:return sprout(8,2,.13,.08)
    count=7 if stage==2 else 5;size=1 if stage==2 else .62
    for i in range(count):
        a=i*2.4;d=Vector((math.cos(a),math.sin(a),0));tip=d*.14*size+Vector((0,0,(.22+.07*(i%3))*size))
        # Thick white petiole is separate editable geometry; green spoon blades fan outward.
        o=sphere('Bok_choy_white_petiole',tip*.5,(.045*size,.04*size,tip.length*.58),'white','stem',12,8)
        o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(tip.normalized())
        leaf('Bok_choy_spoon_leaf',tip*.74,a,.23*size,.11*size,rise=.18*size,arch=.055*size,cup=.04*size,key='leaf' if i%2 else 'leaf_light',vein=True,n=10,w=6)

def rose(stage):
    if stage==0:return sprout(9,2,.12,.12)
    h=.43 if stage==1 else .65
    tube('Rose_stem',[(0,0,0),(.015,0,h*.5),(0,0,h)],.014)
    for i in range(3):leaf('Rose_leaf',(0,0,.15+i*.09),i*2.5,.18,.065,rise=.05,arch=.04,lobes=.08,vein=True)
    if stage==1:
        sphere('Closed_rose_bud',(0,0,h),(.065,.06,.10),'pink','bloom');calyx((0,0,h-.07),.09);return
    for ring,count in [(0,7),(1,6),(2,5),(3,3)]:
        for j in range(count):
            a=j*2*math.pi/count+ring*.6;r=.14-ring*.031;verts=[];faces=[]
            for i in range(9):
                t=i/8
                for k in range(9):
                    u=k/8*2-1;theta=a+u*(.53 if ring<2 else .70)
                    rr=r*(.25+.75*math.sin(t*math.pi*.64))
                    z=h-.045+ring*.024+t*(.115-ring*.009)-.035*u*u*t
                    verts.append((rr*math.cos(theta),rr*math.sin(theta),z))
            for i in range(8):
                for k in range(8):q=i*9+k;faces.append((q,q+1,q+10,q+9))
            o=mesh('Curled_rose_petal',verts,faces,'pink_light' if (j+ring)%3 else 'pink','bloom');m=o.modifiers.new('Petal thickness','SOLIDIFY');m.thickness=.007
    calyx((0,0,h-.06),.10)

def strawberry(stage):
    if stage==0:return sprout(10,2,.12,.08)
    for i in range(3 if stage==1 else 5):
        a=i*2.4;end=Vector((math.cos(a)*.15,math.sin(a)*.15,.19 if stage==2 else .12))
        tube('Strawberry_leaf_stalk',[(0,0,0),end],.010)
        for k in (-1,0,1):leaf('Strawberry_trifoliate',end,a+k*.65,.15 if stage==2 else .12,.068,rise=.035,arch=.045,lobes=.13,key='leaf' if i%2 else 'leaf_light',n=9,w=4)
    flower((.05,-.09,.22 if stage==2 else .17),.038,'white')
    if stage==1:return
    for i,p in enumerate([(-.18,-.16,.105),(.14,-.20,.10),(.18,.04,.12)]):
        x,y,z=p;verts=[];faces=[];ns=16;nr=12;r=.085;h=.16
        for row in range(nr+1):
            t=row/nr;radius=r*math.sin(math.pi*t)**.65*(.50+.65*t)
            for j in range(ns):a=j*2*math.pi/ns;verts.append((x+radius*math.cos(a),y+radius*math.sin(a),z+(t-.5)*h))
        for row in range(nr):
            for j in range(ns):q=row*ns+j;b=row*ns+(j+1)%ns;faces.append((q,b,b+ns,q+ns))
        mesh('Strawberry_fruit',verts,faces,'berry','produce');calyx((x,y,z+h*.42),r*.8)
        for row in range(1,5):
            t=row/6;rad=r*math.sin(math.pi*t)**.65*(.50+.65*t)
            for j in range(6):
                a=j*math.pi/3+row*.4;sphere('Strawberry_seed',(x+(rad+.002)*math.cos(a),y+(rad+.002)*math.sin(a),z+(t-.5)*h),(.003,.003,.005),'cream','produce',6,4)
        tube('Berry_stalk',[(x,y,z+h*.45),(x*.5,y*.5,.22),(0,0,.12)],.008)

def cauliflower(stage):
    if stage==0:return sprout(11,3,.14,.08)
    tube('Cauliflower_short_stem',[(0,0,0),(0,0,.12)],.04)
    scale=1 if stage==2 else .62
    for i in range(7):leaf('Cauliflower_cupped_leaf',(0,0,.025),i*2.4,.36*scale,.13*scale,rise=.26*scale,arch=.04,cup=.065,key='leaf' if i%2 else 'leaf_deep',vein=True)
    if stage==1:return
    sphere('Cauliflower_core',(0,0,.22),(.23,.23,.16),'cream',seg=16,rings=10)
    for i in range(23):
        a=i*2.4;r=.20*math.sqrt(i/23);z=.24+.12*math.sqrt(max(0,1-(r/.24)**2))
        sphere('Cauliflower_curds',(math.cos(a)*r,math.sin(a)*r,z),(.063,.061,.052),'cream' if i%3 else 'white',seg=10,rings=6)

def watermelon(stage):
    if stage==0:return sprout(13,2,.16,.09)
    for i in range(4):
        a=i*2.3;leaf('Melon_leaf',(0,0,.045),a,.39 if stage==2 else .25,.11,rise=.12,arch=.055,cup=.025,lobes=.30,vein=True)
    tube('Melon_trailing_vine',[(0,0,.025),(.22,-.07,.03),(.38,-.18,.035)],.012)
    if stage==1:return
    center=Vector((.08,-.14,.23));rx=.30;ry=.23;rz=.22;ns=40;nr=16;verts=[];faces=[]
    for i in range(nr+1):
        p=math.pi*i/nr
        for j in range(ns):
            a=j*2*math.pi/ns;wave=.018*math.sin(p*9+j*.3)
            verts.append(center+Vector((rx*math.cos(p),ry*math.sin(p)*math.cos(a+wave),rz*math.sin(p)*math.sin(a+wave))))
    for i in range(nr):
        for j in range(ns):q=i*ns+j;b=i*ns+(j+1)%ns;faces.append((q,q+ns,b+ns,b))
    o=mesh('Striped_watermelon',verts,faces,'melon','produce');o.data.materials.append(mat('melon_dark'))
    for i,p in enumerate(o.data.polygons):p.material_index=1 if i%ns%5<2 else 0

def tulip(stage):
    if stage==0:
        for i in range(2):leaf('Tulip_shoot',(0,0,0),i*3.0,.12,.032,rise=.17,arch=.03,key='leaf_light')
        return
    for k in range(3 if stage==2 else 2):
        x=(k-1)*.16;y=.04*(k%2);h=.51+.09*(k%2) if stage==2 else .30
        tube('Tulip_stem',[(x*.4,y*.4,0),(x,y,h)],.014)
        for j in range(2):leaf('Tulip_lance_leaf',(x*.5,y,.06+j*.07),k*2+j*2.8,.20,.055,rise=.24,arch=.035,key='leaf_light',shape=1)
        if stage==1:
            sphere('Closed_tulip_bud',(x,y,h),(.035,.035,.07),'green_fruit','bloom',12,8);continue
        for i in range(6):
            a=i*2*math.pi/6;verts=[];faces=[]
            for row in range(9):
                t=row/8;r=.018+.08*math.sin(t*math.pi*.60)
                for j in range(7):
                    u=j/6*2-1;theta=a+u*.56;verts.append((x+r*math.cos(theta),y+r*math.sin(theta),h+t*.16-.02*u*u*t))
            for row in range(8):
                for j in range(6):q=row*7+j;faces.append((q,q+1,q+8,q+7))
            o=mesh('Tulip_cup_petal',verts,faces,'orange_light' if i%2 else 'orange','bloom');m=o.modifiers.new('Petal thickness','SOLIDIFY');m.thickness=.008

def lettuce(stage):
    if stage==0:return sprout(15,3,.13,.07)
    tube('Lettuce_short_stem',[(0,0,0),(0,0,.08)],.04)
    for ring,count in [(0,8),(1,6),(2,4)]:
        for i in range(count):
            a=i*2*math.pi/count+ring*.7;s=1 if stage==2 else .62
            leaf('Ruffled_lettuce_leaf',(0,0,.025+ring*.025),a,(.38-ring*.08)*s,(.16-ring*.025)*s,rise=(.13+ring*.065)*s,arch=.05,cup=.05,lobes=.32,key='leaf_light' if ring else 'leaf',vein=ring==0,n=14,w=6)

def scallion(stage):
    count=[3,5,7][stage];h=[.20,.40,.65][stage]
    for i in range(count):
        a=i*2.4;r=.06*math.sqrt(i/max(1,count-1));x=r*math.cos(a);y=r*math.sin(a);z=h*(.82+.18*math.sin(i*1.4)**2)
        curved_fruit('Scallion_white_base',(x,y,.07 if stage else .035),.023 if stage else .015,.16 if stage else .08,'bulb')
        tube('Scallion_green_hollow_blade',[(x,y,.10 if stage else .045),(x*1.5,y*1.5,z*.66),(x*2.3+.018,y*2.3,z)],.020 if stage else .011,'leaf' if i%2 else 'leaf_light','foliage',7)

BUILDERS={'cabbage':cabbage,'tomato':tomato,'corn':corn,'cucumber':lambda s:vine_plant(s,'cucumber'),
          'pumpkin':pumpkin,'sunflower':sunflower,'wheat':wheat,'bokchoy':bokchoy,'rose':rose,
          'strawberry':strawberry,'cauliflower':cauliflower,'zucchini':lambda s:vine_plant(s,'zucchini'),
          'watermelon':watermelon,'tulip':tulip,'lettuce':lettuce,'scallion':scallion}
CATALOG=[('cabbage','卷心菜','C01'),('tomato','番茄','C02'),('corn','玉米','C03'),('cucumber','黄瓜','C04'),
         ('pumpkin','南瓜','C05'),('sunflower','向日葵','C06'),('wheat','小麦','C07'),('bokchoy','小白菜','C08'),
         ('rose','玫瑰','C09'),('strawberry','草莓','C10'),('cauliflower','花椰菜','C11'),('zucchini','西葫芦','C12'),
         ('watermelon','西瓜','C13'),('tulip','郁金香','C14'),('lettuce','生菜','C15'),('scallion','小葱','C16')]

def export_stage(objects,path):
    # Evaluate editable curves/modifiers, then consolidate by semantic part for efficient GLBs.
    temp=bpy.data.collections.new('EXPORT_TEMP');bpy.context.scene.collection.children.link(temp)
    deps=bpy.context.evaluated_depsgraph_get();groups={}
    for source in objects:
        if source.type not in {'MESH','CURVE'}:continue
        data=bpy.data.meshes.new_from_object(source.evaluated_get(deps),depsgraph=deps)
        o=bpy.data.objects.new(source.name,data);temp.objects.link(o);o.matrix_world=source.matrix_world.copy()
        groups.setdefault(source.get('part','foliage'),[]).append(o)
    merged=[]
    for role,items in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in items:o.select_set(True)
        bpy.context.view_layer.objects.active=items[0]
        if len(items)>1:bpy.ops.object.join()
        o=bpy.context.object;o.name=role;o['crop_part']=role;merged.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in merged:o.select_set(True)
    bpy.context.view_layer.objects.active=merged[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
    for o in list(temp.objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(temp)
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);a=g['accessors']
    triangles=sum((a[p['indices']]['count'] if 'indices' in p else a[p['attributes']['POSITION']]['count'])//3 for m in g['meshes'] for p in m['primitives'])
    return {'file':path.name,'bytes':len(raw),'triangles':triangles,'meshes':len(g['meshes']),'materials':len(g.get('materials',[]))}

def studio(span=4.0):
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.use_denoising=True
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    sc.render.resolution_x=1200;sc.render.resolution_y=680;sc.render.resolution_percentage=100
    if sc.world is None:sc.world=bpy.data.worlds.new('Crop_studio_world')
    sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.82,.72,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));floor=bpy.context.object;floor.name='Studio_floor'
    fm=bpy.data.materials.new('Studio_cream');fm.diffuse_color=(*color('#F7F6EE'),1);floor.data.materials.append(fm)
    for name,loc,power,size in [('Key',(-3,-4,7),180,5),('Fill',(4,0,5),80,4),('Rim',(0,4,5),100,4)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.4))-o.location).to_track_quat('-Z','Y').to_euler()
    camdata=bpy.data.cameras.new('Crop_camera');cam=bpy.data.objects.new('Crop_camera',camdata);sc.collection.objects.link(cam)
    cam.location=(2.7,-6.5,4.2);cam.rotation_euler=(Vector((0,0,.46))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=span;sc.camera=cam
    return sc

def main():
    manifest=[]
    for crop,name,code in CATALOG:
        if ONLY and crop not in ONLY:continue
        bpy.ops.wm.read_factory_settings(use_empty=True);MATS.clear()
        bpy.context.preferences.filepaths.save_version=0
        records=[];objects_by_stage=[]
        for stage,label in enumerate(STAGES):
            global COLLECTION,PARTS
            COLLECTION=bpy.data.collections.new(f'{code}_{crop}_{label}');bpy.context.scene.collection.children.link(COLLECTION)
            PARTS=[];BUILDERS[crop](stage);bpy.context.view_layer.update()
            objects=list(PARTS);objects_by_stage.append(objects)
            record=export_stage(objects,OUT/f'{crop}-{label}.glb');record['stage']=label
            records.append(record)
        # Keep three editable stages side by side in the .blend, after origin-centered exports.
        for i,objects in enumerate(objects_by_stage):
            for o in objects:o.location.x+=(i-1)*1.45
        sc=studio(4.9)
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects_by_stage[2]:o.select_set(True)
        bpy.context.view_layer.objects.active=objects_by_stage[2][0]
        bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{crop}.blend'))
        if RENDER:
            sc.render.filepath=str(REVIEW/f'{crop}-stages.png');bpy.ops.render.render(write_still=True)
        manifest.append({'id':crop,'name':name,'code':code,'source':f'assets-source/crops/{crop}.blend','stages':records})
        print('CROP_COMPLETE',crop,json.dumps(records),flush=True)
    existing={}
    path=OUT/'manifest.json'
    if path.exists():existing={m['id']:m for m in json.loads(path.read_text()).get('crops',[])}
    existing.update({m['id']:m for m in manifest})
    ordered=[existing[c[0]] for c in CATALOG if c[0] in existing]
    path.write_text(json.dumps({'version':'crop-v1','built_with':bpy.app.version_string,'unit_cell':1.2,'crops':ordered},ensure_ascii=False,indent=2)+'\n')
    print('CROP_LIBRARY_COMPLETE',len(ordered),flush=True)

if __name__=='__main__':main()
