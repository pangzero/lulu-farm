"""B04-only Blender authoring helpers, extracted after reading B01 (never imported).

No scene construction, export or file writes occur at import time.
"""
import bpy,bmesh,math
from mathutils import Vector
from math import sin,cos,pi,sqrt,exp
PARTS=[]

def linear(h):
    v=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
def mix(a,b,t):return tuple(x*(1-t)+y*t for x,y in zip(a,b))
def smooth(a,b,t):
    v=max(0,min(1,(t-a)/(b-a)));return v*v*(3-2*v)
def mat(name,color,rough=.72,paint=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*linear(color),1)
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.28
    if paint:
        n=m.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Color';m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color'])
    return m
def mesh(name,vs,faces,material,colors=None):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],faces);d.update()
    bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(material)
    for f in d.polygons:f.use_smooth=True
    if colors:
        a=d.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT');d.color_attributes.active_color=a
        for v,c in zip(a.data,colors):v.color=(*c[:3],1)
    PARTS.append(o);return o
def sphere(name,loc,scale,material,segments=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    PARTS.append(o);return o
def tube(name,pts,r,material):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=10;d.bevel_depth=r;d.bevel_resolution=3;d.use_fill_caps=True
    s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for i,(p,co) in enumerate(zip(s.bezier_points,pts)):
        p.co=co;p.handle_left_type=p.handle_right_type='AUTO';p.radius=1-.4*i/max(1,len(pts)-1)
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(material);PARTS.append(o);return o

def leaf(name,point,colors,thick=.014,nu=24,nv=16,veins=False,paint_material=None,color_fn=None,thickness_fn=None):
    # Square->disc map retains non-collapsed tips and a smooth, closed edge.
    vs=[];cs=[];fs=[];params=[]
    for i in range(nu+1):
        for j in range(nv+1):
            a=j/nv*2-1;b=i/nu*2-1;x=a*sqrt(1-b*b/2);y=b*sqrt(1-a*a/2);t=(y+1)/2;u=x/sqrt(max(1e-9,1-y*y));params.append((t,u))
            vs.append(Vector(point(t,u)))
            if color_fn:c=color_fn(t,u)
            else:
                c=mix(linear(colors[0]),linear(colors[1]),.18+.65*t);rib=exp(-(u/.12)**2)*.23
                if veins:
                    for k in range(5):rib=max(rib,exp(-((t-(.22+k*.13+.20*abs(u)))/.028)**2)*.15*(1-abs(u)))
                c=mix(c,linear(colors[2]),rib)
            cs.append(c)
    for i in range(nu):
        for j in range(nv):
            a=i*(nv+1)+j;fs.append((a,a+1,a+nv+2,a+nv+1))
    if thickness_fn:
        # Fleshy bokchoy petioles taper into blades in one continuous object.
        front=[];back=[]
        for p,(t,u) in zip(vs,params):
            dt=Vector(point(min(1,t+.001),u))-Vector(point(max(0,t-.001),u))
            du=Vector(point(t,min(1,u+.001)))-Vector(point(t,max(-1,u-.001)))
            n=du.cross(dt)
            if n.length<1e-9:n=Vector((p.x,p.y,0))
            if n.length<1e-9:n=Vector((0,-1,0))
            n.normalize();offset=n*thickness_fn(t,u)*.5;front.append(p+offset);back.append(p-offset)
        N=len(vs);vs=front+back;cs=cs+cs;old=fs[:];fs=old+[tuple(v+N for v in reversed(f)) for f in old]
        boundary=list(range(nv+1))+[i*(nv+1)+nv for i in range(1,nu+1)]+[nu*(nv+1)+j for j in range(nv-1,-1,-1)]+[i*(nv+1) for i in range(nu-1,0,-1)]
        for k,a in enumerate(boundary):b=boundary[(k+1)%len(boundary)];fs.append((a,b,b+N,a+N))
    if paint_material is None:paint_material=next((m for m in bpy.data.materials if m.name=='B04 leaf vertex colors'),None) or mat('B04 leaf vertex colors','#FFFFFF',.76,True)
    o=mesh(name,vs,fs,paint_material,cs)
    if not thickness_fn:
        m=o.modifiers.new('True leaf thickness','SOLIDIFY');m.thickness=thick;m.offset=0
    m=o.modifiers.new('Soft leaf surface and fleshy rim','SUBSURF');m.levels=m.render_levels=1
    return o
