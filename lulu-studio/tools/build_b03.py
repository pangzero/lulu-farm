"""B03 authored terrain samples. Never modifies other batches. Run with Blender."""
import bpy, math, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1]
REV=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'r01'
SRC=ROOT/'assets-source/farm-assets/B03';OUT=ROOT/'public/models/farm-assets/B03';QA=ROOT/'review/farm-assets/B03'
ASSETS={'e01':'空田格','e05':'水岸直段','e07':'水面格','e13':'石头组'}
PARTS=[]

def lin(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
def material(name,color,rough=.8,paint=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*lin(color),1)
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=m.diffuse_color
    p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.28
    if paint:
        a=m.node_tree.nodes.new('ShaderNodeVertexColor');a.layer_name='Color';m.node_tree.links.new(a.outputs['Color'],p.inputs['Base Color'])
    return m
def mesh(name,vertices,faces,mat,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(mat)
    for p in me.polygons:p.use_smooth=smooth
    PARTS.append(o);return o
def paint(o,color,amount=.05,seed=0):
    a=o.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT');o.data.color_attributes.active_color=a
    base=lin(color)
    for v,c in zip(o.data.vertices,a.data):
        x,y,z=v.co
        n=.48*sin(x*16+y*11+seed)*sin(z*19-x*9)+.3*cos(x*43+y*37+z*28+seed)+.22*sin(x*87-y*65)
        f=1+amount*n
        c.color=(*[max(0,min(1,b*f)) for b in base],1)
def box(name,loc,size,mat,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new('Soft timber arris','BEVEL');mod.width=bevel;mod.segments=4
        mod=o.modifiers.new('Broad face normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    for p in o.data.polygons:p.use_smooth=True
    PARTS.append(o);return o
def rock(name,loc,dims,seed,color,mat):
    # Eroded asymmetric boulder: flatter crown, broad shoulders, displaced lobes, seated base.
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,radius=1);o=bpy.context.object;o.name=name
    vs=[]
    for v in o.data.vertices:
        x,y,z=v.co;az=math.atan2(y,x)
        r=1+.085*sin(3*az+seed)*(1-z*z)+.035*sin(5*az+z*4+seed)
        px=x*r+.11*z+.035*sin(z*3+seed);py=y*(1+.06*cos(az*3+seed))+.045*z*z
        pz=z*(1.22-.22*z*z)+.065*x-.035*y+.018*sin(az*4+seed)*(1-z*z)
        vs.append((px,py,pz))
    lo=[min(v[k] for v in vs) for k in range(3)];hi=[max(v[k] for v in vs) for k in range(3)]
    for v,p in zip(o.data.vertices,vs):
        v.co=tuple((p[k]-lo[k])/(hi[k]-lo[k])*dims[k]-(dims[k]/2 if k<2 else 0) for k in range(3))
    o.location=loc;o.rotation_euler.z=.19*sin(seed);o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    paint(o,color,.07,seed)
    mod=o.modifiers.new('Eroded contour smoothing','SUBSURF');mod.levels=1;mod.render_levels=1
    PARTS.append(o);return o

def soil_surface(mat):
    # Broad four-quadrant shallow cultivation marks, not four detached lumps.
    n=48;vs=[];fs=[]
    for j in range(n+1):
        y=-.555+1.11*j/n
        for i in range(n+1):
            x=-.555+1.11*i/n
            planting_pad=1-math.exp(-(x*x+y*y)/.01)
            z=-.003-.018*planting_pad*(math.exp(-(x/.034)**2)+math.exp(-(y/.034)**2))
            z+=.0025*sin(x*13+.3)*cos(y*15)*sin(pi*i/n)*sin(pi*j/n)
            vs.append((x,y,z))
    for j in range(n):
        for i in range(n):
            a=j*(n+1)+i;fs.append((a,a+1,a+n+2,a+n+1))
    ring=list(range(n+1))+[j*(n+1)+n for j in range(1,n+1)]+[n*(n+1)+i for i in range(n-1,-1,-1)]+[j*(n+1) for j in range(n-1,0,-1)]
    bot=len(vs)
    for a in ring:vs.append((vs[a][0],vs[a][1],-.14))
    for i,a in enumerate(ring):b=ring[(i+1)%len(ring)];fs.append((a,bot+i,bot+(i+1)%len(ring),b))
    fs.append(tuple(reversed(range(bot,len(vs)))))
    o=mesh('E01 continuous soil / shallow cross furrow',vs,fs,mat);paint(o,'#94613F',.11,1)
    for v,c in zip(o.data.vertices,o.data.color_attributes['Color'].data):
        shade=1-.15*max(math.exp(-(v.co.x/.045)**2),math.exp(-(v.co.y/.045)**2))
        c.color=(*[x*shade for x in c.color[:3]],1)

def e01():
    earth=material('E01 warm tilled soil','#94613F',.94,True);wood=material('E01 honey timber','#D3A069',.78,True)
    base=material('E01 below-grade earth','#805938',1)
    # Full exact square underside keeps the 1.2 seam watertight despite rounded trim.
    box('E01 continuous square foundation',(0,0,-.1275),(1.2,1.2,.105),base,0)
    soil_surface(earth)
    for axis in range(2):
        for s in [-1,1]:
            loc=(s*.56,0,-.021) if axis==0 else (0,s*.56,-.021)
            size=(.08,.96,.12) if axis==0 else (.96,.08,.12)
            o=box('E01 rounded edge rail',loc,size,wood,.017);paint(o,'#D3A069',.035,axis+s)
    for x in [-.54,.54]:
        for y in [-.54,.54]:
            o=box('E01 inset corner joint',(x,y,-.005),(.12,.12,.17),wood,.025);paint(o,'#DBAF78',.025,2)
    # A handful of low soil granules, no plants or separate environment asset.
    for k,(x,y,s) in enumerate([(-.33,.30,.026),(.31,.29,.020),(.28,-.26,.023),(-.19,-.32,.016),(.38,-.12,.012)]):
        rock('E01 small soil clod',(x,y,-.008),(s*1.5,s,s*.55),k,'#A57149',earth)

def extrusion(name,profile,mat,wave=False):
    n=32;vs=[];fs=[];m=len(profile)
    for i in range(n+1):
        x=-.6+1.2*i/n
        for y,z in profile:
            # Periodic endpoints share positions AND tangents; rear land stays exactly level.
            d=.014*(1-cos(2*pi*i/n))*.5 if wave and y<.2 else 0
            vs.append((x,y+d,z))
    for i in range(n):
        for j in range(m):
            a=i*m+j;b=i*m+(j+1)%m;fs.append((a,b,b+m,a+m))
    fs.append(tuple(reversed(range(m))));fs.append(tuple(n*m+j for j in range(m)))
    o=mesh(name,vs,fs,mat)
    o.data.polygons[-1].use_smooth=o.data.polygons[-2].use_smooth=False
    return o

def e05():
    earth=material('E05 rounded soil strata','#B49461',.92,True)
    grass=material('E05 soft grass cap','#8FBF52',.90,True);stone=material('E05 smooth shore stones','#AEAFA4',.80,True)
    # Clockwise cross-section seen from +X, explicit underside below water.
    o=extrusion('E05 solid bank core',[(-.38,-.28),(.6,-.28),(.6,-.065),(-.13,-.09),(-.25,-.17),(-.38,-.23)],earth,True)
    paint(o,'#B49461',.04)
    o=extrusion('E05 continuous level turf cap',[(-.13,-.09),(.6,-.065),(.6,0),(.25,0),(.09,-.006),(-.01,-.025),(-.09,-.052)],grass,True)
    paint(o,'#8FBF52',.055)
    for k,(x,y,w,d,h) in enumerate([(-.46,-.16,.27,.27,.21),(-.22,-.11,.28,.33,.28),(.04,-.16,.24,.27,.22),(.29,-.12,.29,.31,.26),(.495,-.16,.18,.24,.18)]):
        rock('E05 shoreline stone %02d'%k,(x,y,-.14),(w,d,h),k+3,['#A9AEA7','#B5B7AA','#B9BAB1'][k%3],stone)

def water_image():
    # Deterministic periodic Voronoi caustic atlas authored inside Blender, embedded in GLB.
    n=512;y,x=np.mgrid[0:n,0:n]/n
    # Smooth periodic warping removes the straight polygon-network appearance.
    x,y=(x+.023*np.sin(2*pi*y)+.013*np.sin(4*pi*y+2*pi*x))%1,(y+.026*np.sin(2*pi*x)+.011*np.sin(4*pi*x-2*pi*y))%1
    rng=np.random.default_rng(37);dist=[]
    for j in range(4):
        for i in range(4):
            px=(i+.5+rng.uniform(-.25,.25))/4;py=(j+.5+rng.uniform(-.25,.25))/4
            dx=np.minimum(abs(x-px),1-abs(x-px));dy=np.minimum(abs(y-py),1-abs(y-py))
            dist.append(np.sqrt(dx*dx+dy*dy))
    d=np.sort(np.stack(dist),axis=0);edge=np.exp(-((d[1]-d[0])/.010)**2)
    shade=.035*np.sin(2*pi*x)*np.sin(2*pi*y)
    a=np.array([.19,.68,.73]);b=np.array([.46,.81,.81]);rgb=a[None,None,:]*(1-edge[:,:,None]*.46)+b[None,None,:]*(edge[:,:,None]*.46)+shade[:,:,None]
    rgba=np.concatenate((rgb,np.ones((n,n,1))),axis=2).astype(np.float32)
    im=bpy.data.images.new('E07 periodic pool color / 512px',width=n,height=n,alpha=True)
    im.colorspace_settings.name='sRGB';im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/f'e07-water-color-{REV}.png');im.file_format='PNG';im.save();im.pack();return im

def e07():
    mat=material('E07 static opaque water fallback','#3EAFBA',.35)
    p=mat.node_tree.nodes['Principled BSDF'];p.inputs['Specular IOR Level'].default_value=.25
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=water_image();tex.extension='REPEAT';mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    # One horizontal sheet. No glass cube or vertical interior walls; boundary intentionally open.
    n=12;vs=[(-.6+1.2*i/n,-.6+1.2*j/n,-.105) for j in range(n+1) for i in range(n+1)];fs=[]
    for j in range(n):
        for i in range(n):a=j*(n+1)+i;fs.append((a,a+1,a+n+2,a+n+1))
    o=mesh('E07 level water sheet / no displacement',vs,fs,mat,False);uv=o.data.uv_layers.new(name='UVMap')
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=((co.x+.6)/1.2,(co.y+.6)/1.2)
    o['water_level']=-.105;o['runtime_water']='Optional web-only color ripples; geometry remains fixed'

def e13():
    m=material('E13 warm neutral river stone','#B6B5AB',.82,True)
    for k,(loc,dims,color) in enumerate([((-.16,.09,0),(.62,.43,.39),'#B6B5AB'),((.30,.01,0),(.32,.29,.23),'#BBB9AE'),((.01,-.30,0),(.35,.27,.20),'#AAAFA8')]):
        rock('E13 sculpted boulder %02d'%k,loc,dims,8+k,color,m)

def setup(ortho=1.8,target=(0,0,0)):
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100
    sc.world=bpy.data.worlds.new('B01 reference world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(1,1,1,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.32
    qa=bpy.data.collections.new('QA_ONLY / excluded from GLB');sc.collection.children.link(qa)
    def move(o):
        for c in list(o.users_collection):c.objects.unlink(o)
        qa.objects.link(o)
    floor=box('QA ground',(0,0,-.335),(200,200,.02),material('QA matte ivory','#F4F2E8',1),0);PARTS.remove(floor);move(floor)
    for name,loc,power,size in [('key',(-3,-4,6),280,4),('fill',(4,-1,3),140,3),('rim',(0,4,5),230,3)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);qa.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new('B03 fixed camera');d.type='ORTHO';d.ortho_scale=ortho;o=bpy.data.objects.new('B03 fixed camera',d);qa.objects.link(o);sc.camera=o
    aim(sc,target,(1.35,-4,2.25),ortho)
    sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
    return sc
def aim(sc,target,view,scale):
    t=Vector(target);sc.camera.location=t+Vector(view).normalized()*6;sc.camera.rotation_euler=(t-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale
def render(sc,path):
    sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def main():
    for p in [SRC,OUT,QA]:p.mkdir(parents=True,exist_ok=True)
    for a in ASSETS:
        if (SRC/f'{a}-{REV}.blend').exists() or (OUT/f'{a}-{REV}.glb').exists():raise RuntimeError('Revision exists; select a new revision: '+REV)
    for a in ASSETS:
        bpy.ops.wm.read_factory_settings(use_empty=True);PARTS.clear()
        prod=bpy.data.collections.new(f'B03 {a} editable production');bpy.context.scene.collection.children.link(prod)
        bpy.context.view_layer.active_layer_collection=bpy.context.view_layer.layer_collection.children[prod.name]
        globals()[a]();sc=setup(target=(0,0,-.03 if a!='e13' else .15))
        sc.objects['QA ground'].location.z={'e01':-.20,'e05':-.30,'e07':-.15,'e13':-.02}[a]
        sc['B03_revision']=REV;sc['grid_pitch']=1.2;sc['land_z']=0.;sc['water_z']=-.105
        bpy.ops.wm.save_as_mainfile(filepath=str(SRC/f'{a}-{REV}.blend'))
        bpy.ops.object.select_all(action='DESELECT')
        for o in PARTS:o.select_set(True)
        bpy.context.view_layer.objects.active=PARTS[0]
        bpy.ops.export_scene.gltf(filepath=str(OUT/f'{a}-{REV}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_extras=True)
        render(sc,QA/f'{a}-{REV}-initial.png');print('B03 BUILT',a,REV,flush=True)

if __name__=='__main__':main()
