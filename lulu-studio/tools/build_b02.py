"""B02 only: editable facade sample and a repeatable fence with terminal post.

Never imports/runs B01. Revisions are immutable once written.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'assets-source/farm-assets/B02'
OUT=ROOT/'public/models/farm-assets/B02'
QA=ROOT/'review/farm-assets/B02'
REV='r04'
PARTS=[]

def linear(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)

def material(name,h,rough=.76):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF'];m.diffuse_color=(*linear(h),1)
    p.inputs['Base Color'].default_value=m.diffuse_color
    p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.28
    return m

def mesh(name,vs,fs,mat):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
    bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
    if mat:d.materials.append(mat)
    PARTS.append(o);return o

def bevel(o,width=.025,segments=3):
    m=o.modifiers.new('Soft crafted edges','BEVEL');m.width=width;m.segments=segments
    m=o.modifiers.new('Broad planar normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=40
    for p in o.data.polygons:p.use_smooth=True
    return o

def box(name,loc,dims,mat,rounding=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat);PARTS.append(o)
    if rounding:bevel(o,rounding)
    return o

def profile(r,base,spring,n=32):
    return [(-r,base),(r,base),(r,spring)]+[(r*math.cos(math.pi*i/n),spring+r*math.sin(math.pi*i/n)) for i in range(1,n+1)]

def extrusion(name,outline,xcenter,yfront,yback,mat,rounding=0):
    N=len(outline);vs=[(x+xcenter,y,z) for y in [yfront,yback] for x,z in outline]
    fs=[tuple(range(N)),tuple(reversed(range(N,2*N)))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
    o=mesh(name,vs,fs,mat)
    return bevel(o,rounding) if rounding else o

def arch_ring(name,xc,ri,ro,base,spring,yf,yb,mat):
    # Corresponding closed contours make a genuinely open ring, not an arch decal.
    inn=profile(ri,base,spring);out=profile(ro,base-.035,spring);n=len(inn)
    vs=[(x+xc,y,z) for y in [yf,yb] for p in [out,inn] for x,z in p];fs=[]
    for i in range(n):
        j=(i+1)%n
        fs += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
               (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    return bevel(mesh(name,vs,fs,mat),.018,3)

def curve(name,pts,r,mat):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=8;d.bevel_depth=r;d.bevel_resolution=2;d.use_fill_caps=True
    s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for p,co in zip(s.bezier_points,pts):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(mat);PARTS.append(o);return o

def plug(name,loc,r,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=loc,rotation=(math.pi/2,0,0))
    o=bpy.context.object;o.name=name;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat);PARTS.append(o);return bevel(o,min(depth*.35,.006),3)

def cut(o,cutter):
    bpy.context.view_layer.objects.active=o
    m=o.modifiers.new('Actual arched opening','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name)
    PARTS.remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True)

def reset():
    global PARTS
    bpy.ops.wm.read_factory_settings(use_empty=True);PARTS=[]
    bpy.context.preferences.filepaths.save_version=0

def studio():
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
    s.render.resolution_x=s.render.resolution_y=768;s.render.resolution_percentage=100
    s.world=bpy.data.worlds.new('B01 inherited neutral studio');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.80,.75,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.32
    s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
    for name,loc,power,size in [('Key',(-3,-4,6),280,4),('Fill',(4,-1,3),140,3),('Rim',(0,4,5),230,3)]:
        d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc
        o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.shape='DISK';d.size=size
    ground=material('QA ground only','#F4F2E8',1)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));o=bpy.context.object;o.name='QA ground - NEVER EXPORT';o.data.materials.append(ground)
    d=bpy.data.cameras.new('Fixed B02 review camera');o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);s.camera=o;d.type='ORTHO'
    return s

def camera(sc,target,scale,direction=(1.35,-4,2.25)):
    target=Vector(target);sc.camera.location=target+Vector(direction).normalized()*12
    sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale

def export(parts,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.duplicate();copies=list(bpy.context.selected_objects)
    bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.ops.object.join()
    o=bpy.context.object;o.name=name;bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    o.data.calc_loop_triangles()
    degenerate=sum(t.area<1e-12 for t in o.data.loop_triangles)
    if degenerate:raise RuntimeError(f'Export has {degenerate} degenerate triangles: {name}')
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
    bpy.data.objects.remove(o,do_unlink=True)

def organize(parts,name):
    col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(col)
    for o in parts:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
    root=bpy.data.objects.new(name+' origin at ground',None);col.objects.link(root)
    for o in parts:o.parent=root
    return col

def roof_z(x,y):return 2.69+.26*(1-(x/1.98)**2)+.20*(y+.60)

def roof_patch(name,xa,xb,ya,yb,thickness,mat):
    n=6;vs=[]
    for lift in [0,thickness]:
        for y in [ya,yb]:
            for j in range(n+1):
                x=xa+(xb-xa)*j/n;vs.append((x,y,roof_z(x,y)+lift))
    N=n+1;fs=[]
    for j in range(n):fs += [(j,j+1,N+j+1,N+j),(2*N+j,3*N+j,3*N+j+1,2*N+j+1),(j,2*N+j,2*N+j+1,j+1),(N+j,N+j+1,3*N+j+1,3*N+j)]
    fs += [(0,N,3*N,2*N),(n,2*N+n,3*N+n,N+n)]
    return bevel(mesh(name,vs,fs,mat),.019,3)

def facade():
    reset()
    cream=material('Warm lime plaster','#F4E6C9',.87);stone=material('Limestone footing','#DBC9A7',.84)
    oak=material('Honey oak frames','#B97635');wood=material('Golden oak door','#C88A43');wood2=material('Oak plank quiet variation','#D2944B')
    dark=material('Recessed oak end grain','#99602C',.85);gold=material('Aged brass handles','#DAB859',.58)
    glass=material('Opaque soft sky glass - no transparency','#60B9D2',.42);glass2=material('Sky glass muted variation','#71C4D8',.44)
    tiles=[material('Terracotta tile '+str(i),h,.78) for i,h in enumerate(['#E98436','#EE8D3B','#E68132','#F19743'])]
    wall=box('S01 wall 340mm with genuine openings',(0,0,1.335),(3.60,.34,2.67),cream,0)
    cut(wall,extrusion('Door opening cutter',profile(.59,.11,1.39),-.78,-.65,.65,None))
    cut(wall,extrusion('Window opening cutter',profile(.47,.94,1.55),.85,-.65,.65,None))
    bevel(wall,.035,4)
    # Close the curved roof/wall junction all the way through wall thickness.
    n=40;vs=[]
    for y in [-.17,.17]:
        for top in [False,True]:
            for j in range(n+1):
                x=-1.8+3.6*j/n;vs.append((x,y,roof_z(x,y)+.025 if top else 2.64))
    N=n+1;fs=[]
    for j in range(n):fs += [(j,j+1,N+j+1,N+j),(2*N+j,3*N+j,3*N+j+1,2*N+j+1),(j,2*N+j,2*N+j+1,j+1),(N+j,N+j+1,3*N+j+1,3*N+j)]
    fs += [(0,N,3*N,2*N),(n,2*N+n,3*N+n,N+n)]
    bevel(mesh('Shaped plaster wall head meets curved eave',vs,fs,cream),.015,3)
    # Thin plinth divided by the actual threshold; no false wall behind the door.
    for x,w in [(-1.61,.44),(.825,2.03)]:box('Plaster base limestone course',(x,-.035,.085),(w,.44,.17),stone,.024)
    arch_ring('Door full depth timber jamb',-.78,.555,.592,.13,1.39,-.13,.17,dark)
    extrusion('Door continuous solid rear backing',profile(.582,.135,1.39),-.78,.044,.105,dark,.005)
    arch_ring('Door deep rounded arch casing',-.78,.57,.72,.13,1.39,-.285,-.12,oak)
    # Each real plank follows the round arch. Six boards form two readable door leaves.
    r=.552;spring=1.39;base=.145
    for k in range(6):
        a=-r+k*2*r/6+.005;b=-r+(k+1)*2*r/6-.005
        top=lambda x:spring+math.sqrt(max(0,r*r-x*x))
        poly=[(a,base),(b,base)]+[(b+(a-b)*j/8,top(b+(a-b)*j/8)) for j in range(9)]
        extrusion('Door leaf %s plank %02d'%('L' if k<3 else 'R',k+1),poly,-.78,-.065,.045,wood if k%3 else wood2,.009)
        if k in [0,2,4]:
            x=-.78+(a+b)*.5
            curve('Sparse door grain %d'%k,[(x,-.068,.35),(x+.007,-.068,.65),(x-.006,-.068,1.05),(x+.002,-.068,1.26)],.0023,dark)
    # Shallow dark timber inlays; decorative, not real through slots or carving.
    for x in [-.99,-.57]:box('Door upper inset slot',(x,-.071,1.47),(.06,.016,.25),dark,.006)
    for x in [-.90,-.66]:
        plug('Brass handle backplate',(x,-.091,.88),.044,.025,gold)
        plug('Rounded door knob',(x,-.121,.88),.026,.046,gold)
    box('Door threshold slab',(-.78,-.15,.105),(1.27,.53,.15),stone,.023)
    arch_ring('Window full depth timber reveal',.85,.431,.472,.95,1.55,-.13,.17,oak)
    arch_ring('Window deep rounded arch casing',.85,.445,.575,.95,1.55,-.30,-.11,oak)
    # Glass is inside the wall thickness; front mullions cast real depth shadows.
    pane=profile(.432,.972,1.55)
    extrusion('Window inset sky glazing',pane,.85,-.043,.012,glass,.005)
    box('Window vertical mullion',(.85,-.168,1.477),(.065,.095,1.02),oak,.016)
    for x in [.617,.85+.233]:box('Window horizontal half transom',(x,-.168,1.49),(.401,.095,.065),oak,.012)
    box('Window generous sill',(.85,-.245,.932),(1.25,.49,.13),wood2,.03)
    for x in [.43,1.27]:box('Window sill under support',(x,-.194,.82),(.13,.30,.17),oak,.022)
    # Structural underside visible from low and side cameras.
    box('Eave structural oak bearer',(0,-.065,2.595),(3.77,.54,.18),oak,.035)
    for x in [-1.43,1.43]:
        poly=[(-.13,2.42),(.13,2.42),(.13,2.59),(-.13,2.59)]
        box('Eave exposed wall corbel',(x,-.28,2.46),(.20,.40,.30),wood,.036)
    # Only a shallow roof/eave strip, with curved cross-section and tile mass.
    roof_patch('Continuous thick curved eave underdeck',-1.98,1.98,-.60,.43,.12,tiles[0])
    for row in range(2):
        ya=-.59+row*.50;yb=ya+.492
        for k in range(12):
            xa=-1.97+k*3.94/12+.004;xb=-1.97+(k+1)*3.94/12-.004
            roof_patch('Eave clay tile row %d unit %02d'%(row+1,k+1),xa,xb,ya,yb,.145,tiles[(k+row)%4])
    originals=list(PARTS);organize(originals,'PRODUCTION S01 facade SAMPLE')
    export(originals,'s01-facade-sample-'+REV)
    s=studio();camera(s,(0,0,1.53),4.55)
    s['asset_scope']='S01 facade sample only. NOT a complete house. Back and cut ends are inferred sample construction.'
    s['door_clear_opening']='1.18 wide; base .11; spring 1.39; arch crown 1.98; Lulu display height 1.2'
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/('s01-facade-sample-'+REV+'.blend')))
    s.render.filepath=str(QA/('s01-'+REV+'-initial.png'));bpy.ops.render.render(write_still=True)

def rail(name,z,mat):
    # Rounded rectangular section swept without rounding the X contact planes.
    # Flat X ends meet neighbouring post surfaces exactly, without buried rails.
    wy=.055;hz=.075;rad=.024;section=[]
    for cy,cz,start in [(wy-rad,hz-rad,0),(-wy+rad,hz-rad,90),(-wy+rad,-hz+rad,180),(wy-rad,-hz+rad,270)]:
        for j in range(5):
            a=math.radians(start+j*90/4);section.append((cy+rad*math.cos(a),cz+rad*math.sin(a)))
    N=len(section);vs=[(x,y,z+zz) for x in [.11,1.09] for y,zz in section]
    fs=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
    o=mesh(name,vs,fs,mat)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    m=o.modifiers.new('Rail face weighted normals','WEIGHTED_NORMAL');m.keep_sharp=True
    return o

def fence():
    reset()
    post=material('Fence warm rounded oak posts','#C48646',.80);railmat=material('Fence light planed rails','#DDA769',.80)
    endgrain=material('Fence quiet end grain','#BA793D',.86);pegs=material('Fence inset pale wooden pegs','#E6C899',.83)
    box('S05 left owner post 220x240x940mm',(0,0,.47),(.22,.24,.94),post,.045)
    for z in [.32,.67]:
        plug('Front seated wooden peg',(0,-.120,z),.024,.012,pegs)
        plug('Back seated wooden peg',(0,.120,z),.024,.012,pegs)
    for i,z in enumerate([.32,.67]):
        rail('S05 continuous rounded rail '+str(i+1),z,railmat)
        curve('Sparse long rail grain '+str(i+1),[(.21,-.056,z-.018),(.44,-.056,z-.012),(.71,-.056,z-.021),(.99,-.056,z-.015)],.002,endgrain)
    curve('Sparse vertical post grain',[(-.035,-.121,.13),(-.028,-.121,.24),(-.038,-.121,.43),(-.029,-.121,.54)],.002,endgrain)
    repeated=list(PARTS[:5])+[o for o in PARTS[5:]]
    postparts=[o for o in repeated if 'rail' not in o.name.lower()]
    organize(repeated,'PRODUCTION S05 repeat - left post owns next span')
    export(repeated,'s05-fence-repeat-'+REV)
    # Terminal is the same post design at its own origin. Does not duplicate rails.
    export(postparts,'s05-fence-endcap-'+REV)
    qa=bpy.data.collections.new('QA standalone terminal at x 1.2 - NOT in repeat export');bpy.context.scene.collection.children.link(qa)
    for o in postparts:
        q=o.copy();q.data=o.data.copy();q.parent=None;q.location.x+=1.2;qa.objects.link(q)
    s=studio();camera(s,(.6,0,.46),1.85)
    s['asset_scope']='S05 repeat + terminal accessory. One left post per 1.2-unit span. No double posts.'
    s['repeat_interface']='Origins at x=0,1.2,2.4; terminal at x=3.6. Rail X planes .11/1.09; post faces +/-.11. Contacts touch, never overlap.'
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/('s05-fence-'+REV+'.blend')))
    s.render.filepath=str(QA/('s05-'+REV+'-initial.png'));bpy.ops.render.render(write_still=True)

if __name__=='__main__':
    for p in [SRC,OUT,QA]:p.mkdir(parents=True,exist_ok=True)
    targets=[SRC/('s01-facade-sample-'+REV+'.blend'),SRC/('s05-fence-'+REV+'.blend'),OUT/('s01-facade-sample-'+REV+'.glb'),OUT/('s05-fence-repeat-'+REV+'.glb'),OUT/('s05-fence-endcap-'+REV+'.glb')]
    if any(p.exists() for p in targets):raise RuntimeError('Immutable revision already exists; use a new revision.')
    facade();fence()
    (OUT/'manifest.json').write_text(json.dumps({'batch':'B02','revision':REV,'status':'待用户验收','baseline':'B01 r03 user accepted art baseline','cell':1.2,'lulu_scale':.6313689262131015,'assets':[{'id':'S01','name':'主屋立面样段（非完整主屋）','file':'/models/farm-assets/B02/s01-facade-sample-r04.glb','source':'assets-source/farm-assets/B02/s01-facade-sample-r04.blend','scope':'door, window, plaster wall and shallow eave only'},{'id':'S05','name':'围栏直段','file':'/models/farm-assets/B02/s05-fence-repeat-r04.glb','endcap':'/models/farm-assets/B02/s05-fence-endcap-r04.glb','source':'assets-source/farm-assets/B02/s05-fence-r04.blend','repeat_step':1.2,'post_dimensions':[.22,.24,.94],'rail_contact_x':[.11,1.09],'three_segment_origins':[0,1.2,2.4],'terminal_origin':3.6,'assembly_rule':'Each repeat owns left post plus two rails; add one terminal post at the far end. Do not place full two-post modules on top of each other.'}]},ensure_ascii=False,indent=2))
