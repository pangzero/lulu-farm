"""Color/face pass on arm-root-3 clay. Broad cheek contour and softly blended eye footprints change.
Eyes reuse the last colored model's layered pigment method, projected to this head.
"""
import bpy, math, json, struct, zlib, hashlib
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'assets-source/lulu-arm-test.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
body=bpy.data.objects['Lulu_ArmTestSkin']
def signature(o):
 a=np.array([v.co[:] for v in o.data.vertices],dtype=np.float32)
 return hashlib.sha256(a.tobytes()).hexdigest()
before={o.name:signature(o) for o in bpy.context.scene.objects if o.type=='MESH'}
# Redistribute cheek width across a broad vertical band instead of clipping its tip.
# Only x changes here: muzzle forward projection and all z landmarks stay fixed.
cheek_deltas=[]
for v in body.data.vertices:
 x,y,z=v.co
 if not 1.03<z<1.70:continue
 blend=min(1,max(0,(z-1.03)/.075));blend=blend*blend*(3-2*blend)
 lower=.025*math.exp(-((z-1.17)/.125)**2)*blend
 upper=.006*math.exp(-((z-1.51)/.10)**2)
 delta=x*(lower+upper)/.67
 old_keys=[k.data[v.index].co.x for k in body.data.shape_keys.key_blocks]
 v.co.x=x+delta
 for k,old in zip(body.data.shape_keys.key_blocks,old_keys):k.data[v.index].co.x=old+delta
 cheek_deltas.append(float(delta))
body.data.update()

def rgb(h):
 v=np.array([int(h[i:i+2],16)/255 for i in (1,3,5)])
 return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
def material(name,h,rough=.83):
 m=bpy.data.materials.new(name);m.use_nodes=True
 bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*rgb(h),1)
 bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.08
 m.diffuse_color=(*rgb(h),1);return m
skin=material('Lulu_WarmYellow','#FFE66A')
pants=material('Lulu_OrangeShorts','#F58B35')
fruit=material('Lulu_HeadOrange','#FFB52C')
stem=material('Lulu_GreenStem','#79A13B')
mouth=material('Lulu_SmileBrown','#412811',.9)
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.name.startswith('Source_'):continue
 m=skin
 if o.name.startswith('Shorts'):m=pants
 elif o.name=='HeadOrange':m=fruit
 elif o.name.startswith('Fruit'):m=stem
 o.data.materials.clear();o.data.materials.append(m)
 for p in o.data.polygons:p.material_index=0
# Subtle garment waistband and warm ear interior, carried by real mesh colors.
def vertex_material(obj,base_mat,name,colors):
 m=base_mat.copy();m.name=name
 attr=obj.data.color_attributes.new(name='DetailColor',type='FLOAT_COLOR',domain='POINT')
 for v,c in zip(attr.data,colors):v.color=(*c,1)
 node=m.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='DetailColor'
 m.node_tree.links.new(node.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
 obj.data.materials.clear();obj.data.materials.append(m)
shorts=bpy.data.objects['Shorts_Tailored'];colors=[]
for v in shorts.data.vertices:
 z=v.co.z
 t=max(0,min(1,(z-.14)/.43));c=rgb('#E77B2D')*(1-t)+rgb('#F78D37')*t
 band=math.exp(-((z-.545)/.014)**4)*.42
 c=c*(1-band)+rgb('#FFA04B')*band;colors.append(c)
vertex_material(shorts,pants,'Lulu_ShortsSoftWaistband',colors)
for side in [-1,1]:
 ear=bpy.data.objects['Ear_'+str(side)];colors=[];angle=side*math.radians(50)
 for v in ear.data.vertices:
  x,y,z=v.co;dx=x-side*.535;dy=y-.115
  local_x=dx*math.cos(angle)+dy*math.sin(angle)
  depth=-dx*math.sin(angle)+dy*math.cos(angle)
  q=(local_x/.09)**2+((z-1.85)/.09)**2
  w=math.exp(-q*2.6)*max(0,min(1,-depth/.035))*.75
  colors.append(rgb('#FFE66A')*(1-w)+rgb('#E5B945')*w)
 vertex_material(ear,skin,'Lulu_WarmEarInterior_'+str(side),colors)
# A front/back planar paint atlas fits the NEW surface without changing eye beds.
# Seam lies on the yellow lateral body, not across the eye or muzzle.
N=2048
xx=np.linspace(-.82,.82,N,dtype=np.float32)[None,:]
zz=np.linspace(.25,2.12,N,dtype=np.float32)[:,None]
verts=np.array([v.co[:] for v in body.data.vertices])
zsample=np.linspace(.25,2.12,512);width=[]
for z in zsample:
 section=verts[np.abs(verts[:,2]-z)<.008]
 width.append(np.max(np.abs(section[:,0])) if len(section) else .005)
r=np.interp(zz[:,0],zsample,width)[:,None]
f=np.sqrt(np.clip(1-(xx/np.maximum(.005,r))**2,0,1))
# Lower only the upper orange paint boundary; retain muzzle geometry and lower half.
ell=(xx/.69)**2+np.where(zz>1.35,((zz-1.35)/.36)**2,((zz-1.35)/.42)**2)
mask=np.clip((1.02-ell)/.43,0,1);mask=mask*mask*(3-2*mask)
seam=np.clip((f-.12)/.10,0,1);mask*=seam*seam*(3-2*seam)
belly=np.clip((1-((xx/.53)**2+((zz-.79)/.34)**2))*1.3,0,1)
base=rgb('#FFE66A');bel=rgb('#FFF18A');mu=rgb('#FF9F13')[None,None,:]*(1-np.clip((1.38-zz)/.36,0,1)[:,:,None])+rgb('#FFAE1F')[None,None,:]*np.clip((1.38-zz)/.36,0,1)[:,:,None]
colors=np.broadcast_to(base,(N,N,3)).copy()
colors=colors*(1-belly[:,:,None])+bel*belly[:,:,None]
colors=colors*(1-mask[:,:,None])+mu*mask[:,:,None]
def pigment(cx,cz,rx,rz,color,tilt=0,clip=None):
 global colors
 q=((xx-cx-(zz-cz)*tilt)/rx)**2+((zz-cz)/rz)**2
 alpha=np.clip((1-q)*105,0,1)
 if clip is not None:alpha*=clip
 colors=colors*(1-alpha[:,:,None])+(rgb(color) if isinstance(color,str) else color)*alpha[:,:,None]
# Expression pass: retain eye beds; large softly oval pupils and uneven sclera
# follow the original frontal reference without adding a lid/socket mesh.
for side in [-1,1]:
 cx=side*.287;cz=1.759+side*.005;tilt=.22 if side==-1 else -.25
 wrx=.096 if side==-1 else .094
 wrz=.087 if side==-1 else .086
 wcx=cx;wcz=cz+.003
 white=np.clip((1-((xx-wcx-(zz-wcz)*tilt)/wrx)**2-((zz-wcz)/wrz)**2)*90,0,1)
 # A dark, narrow eyelid contour outside the unchanged sclera aperture.
 # Upper rim is slightly stronger; lower rim remains fine, not a thick ring.
 rim=.0022+.0014*np.clip((zz-wcz)/wrz*.5+.5,0,1)
 pigment(wcx,wcz,wrx+rim,wrz+rim,'#38372D',tilt)
 pigment(wcx,wcz,wrx,wrz,'#F3F0DA',tilt)
 icx=cx+(.018 if side==-1 else -.014);icz=cz-.007
 irx=.077 if side==-1 else .075
 iq=((xx-icx-(zz-icz)*tilt)/irx)**2+((zz-icz)/.075)**2
 light=np.clip(1-iq,0,1)*.45+np.clip((icz-zz)/.08,0,1)*.20
 iris_color=rgb('#2B5F9E')*(1-light[:,:,None])+rgb('#4A87C1')*light[:,:,None]
 pigment(icx,icz,irx,.075,iris_color,tilt,white)
 pcx=cx+(.033 if side==-1 else -.027);pcz=cz-.014
 pigment(pcx,pcz,.061,.063,'#02050B',tilt,white)
 pigment(pcx+.023,pcz+.036,.0162,.0144,'#FFFFFF',clip=white)
back=np.broadcast_to(base,(N,N,3))
atlas=np.concatenate([colors,back],axis=1)
srgb=np.where(atlas<=.0031308,atlas*12.92,1.055*np.power(atlas,1/2.4)-.055)
pixels=(np.clip(srgb,0,1)*255+.5).astype(np.uint8)[::-1]
def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
png=ROOT/'assets-source/lulu-complete-paint.png'
raw=b''.join(b'\0'+row.tobytes() for row in pixels)
png.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',N*2,N,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,8))+chunk(b'IEND',b''))
paint=skin.copy();paint.name='Lulu_ReferenceFacePaint'
tex=paint.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(png),check_existing=False);tex.image.pack();tex.interpolation='Linear'
paint.node_tree.links.new(tex.outputs['Color'],paint.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
body.data.materials.clear();body.data.materials.append(paint)
for a in list(body.data.color_attributes):body.data.color_attributes.remove(a)
uv=body.data.uv_layers.new(name='Lulu_FrontBackPaint')
for p in body.data.polygons:
 front=sum(body.data.vertices[i].co.y for i in p.vertices)/len(p.vertices)<0
 for li in p.loop_indices:
  x,y,z=body.data.vertices[body.data.loops[li].vertex_index].co
  uv.data[li].uv=((x+.82)/1.64*.5+(0 if front else .5),(z-.25)/1.87)
# Reuse the previous final model's eye tangent treatment on the current head.
# Bounded to the two eye footprints; silhouette, head crown and body stay intact.
original_positions=np.array([v.co[:] for v in body.data.vertices])
eye_adjustments=[]
pre_tree=BVHTree.FromPolygons([v.co[:] for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
anchors={side:pre_tree.ray_cast((side*.287,-2,1.759+side*.005),(0,1,0),4)[0].y for side in [-1,1]}
for v in body.data.vertices:
 x,y,z=original_positions[v.index]
 if y>-.15 or z<1.42 or z>2.07:continue
 side=-1 if x<0 else 1;cx=side*.287;cz=1.759+side*.005
 q=((x-cx)/.16)**2+((z-cz)/.14)**2
 if q>5:continue
 weight=math.exp(-.65*q*q)
 plane=anchors[side]+.010+.60*(z-cz)+side*.40*(x-cx)
 delta=.055*math.tanh((plane-y)/.055)*weight
 if abs(delta)<1e-7:continue
 old_keys=[k.data[v.index].co.y for k in body.data.shape_keys.key_blocks]
 v.co.y=float(y+delta)
 for k,old_y in zip(body.data.shape_keys.key_blocks,old_keys):k.data[v.index].co.y=old_y+delta
 eye_adjustments.append(float(delta))
body.data.update()
# Continuous thin smile projected to the actual head, with tapered endpoints.
tree=BVHTree.FromPolygons([v.co[:] for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons])
cu=bpy.data.curves.new('Lulu_SmileCurve','CURVE');cu.dimensions='3D';cu.bevel_depth=.0030;cu.bevel_resolution=4;cu.resolution_u=2
sp=cu.splines.new('POLY');sp.points.add(64)
for i,p in enumerate(sp.points):
 x=-.18+.36*i/64;z=1.155+.067*(x/.18)**2+.012*x/.18
 hit,n,_,_=tree.ray_cast((x,-2,z),(0,1,0),4)
 if hit is None:raise ValueError('Smile projection missed body')
 p.co=(hit.x+n.x*.0018,hit.y+n.y*.0018,hit.z+n.z*.0018,1)
 p.radius=.55+.45*math.sin(math.pi*i/64)**.3
smile=bpy.data.objects.new('Lulu_Smile',cu);bpy.context.collection.objects.link(smile);cu.materials.append(mouth)
bpy.ops.object.select_all(action='DESELECT');smile.select_set(True);bpy.context.view_layer.objects.active=smile;bpy.ops.object.convert(target='MESH')
for p in smile.data.polygons:p.use_smooth=True
# All other source objects remain unchanged.
assert all(signature(bpy.data.objects[n])==h for n,h in before.items() if n!=body.name)
rig=bpy.data.objects['Lulu_ArmInspectionRig']
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
 if o==rig or (o.type=='MESH' and not o.name.startswith('Source_')):o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets-source/lulu-complete.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/lulu-complete.glb'),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_skins=True)
(ROOT/'review/complete-validation.json').write_text(json.dumps({'source':str(source),'source_mesh_coordinates_preserved_except_cheeks_and_eye_footprints':True,'cheek_x_delta_range':[min(cheek_deltas),max(cheek_deltas)],'eye_footprint_vertices':len(eye_adjustments),'eye_y_adjustment_range':[min(eye_adjustments),max(eye_adjustments)],'mesh_signatures':before,'eye_method':'rounded cheek field and softened eye tangent blend on current head; height and foremost muzzle preserved','texture_size':[4096,2048],'mouth':'surface projected curve mesh','rig_bones':len(rig.data.bones),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},indent=2))
print('COMPLETE_MODEL_EXPORTED')
