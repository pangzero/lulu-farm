# Reference-driven replacement for the first Lulu mesh. Blender 4.5 CLI.
import sys
from pathlib import Path
__file__ = str(Path(__file__).resolve())
base = Path(__file__).with_name('lulu_primitives.py').read_text()
exec(base)
start = set(bpy.data.objects)
bodymat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb('#FFE36A')
bodymat.diffuse_color=rgb('#FFE36A')
for softmat in [bodymat,pantsmat,orange,white,iris,pupil]:
 softmat.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=0
 softmat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.82
orange.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb('#FFB42B')
pantsmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb('#FF8731')
iris.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb('#63A4DF')
pupil.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb('#02050B')
# Height, half width, front depth, back depth. The cheek is the widest section.
profile = [(.33,.46,.43,.39),(.45,.545,.48,.40),(.56,.565,.48,.39),
 (.78,.525,.425,.33),(.94,.495,.36,.30),(1.035,.510,.39,.30),
 (1.14,.555,.51,.35),(1.22,.640,.615,.42),(1.295,.676,.74,.47),(1.39,.696,.80,.522),
 (1.48,.680,.805,.534),(1.56,.660,.775,.528),(1.663,.610,.730,.512),
 (1.765,.550,.600,.434),(1.867,.450,.500,.378),(1.96,.29,.24,.21),
 (2.03,.015,.018,.018)]
# Shape-preserving cubic interpolation in physical height (nonuniform knots).
# Uniform-index Catmull-Rom caused changes of slope at every height station.
slopes={}
for col in [1,2,3]:
 h=[profile[i+1][0]-profile[i][0] for i in range(len(profile)-1)]
 d=[(profile[i+1][col]-profile[i][col])/h[i] for i in range(len(h))]
 mm=[d[0]]
 for i in range(1,len(profile)-1):
  if d[i-1]*d[i]<=0:mm.append(0)
  else:
   w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];mm.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
 mm.append(d[-1]);slopes[col]=mm
def interp(z,col):
 for i in range(len(profile)-1):
  if profile[i][0]<=z<=profile[i+1][0]:
   h=profile[i+1][0]-profile[i][0];t=(z-profile[i][0])/h
   return (2*t**3-3*t*t+1)*profile[i][col]+(t**3-2*t*t+t)*h*slopes[col][i]+(-2*t**3+3*t*t)*profile[i+1][col]+(t**3-t*t)*h*slopes[col][i+1]
 return profile[-1][col]
# Smooth the loft's second derivative as well, without moving its measured landmarks.
import numpy as np
raw_interp=interp
heights=np.linspace(.33,2.03,4096)
smoothed={}
for c,sigma in [(1,.085),(2,.085),(3,.105)]:
 half=int(3*sigma/((2.03-.33)/4095));kx=np.arange(-half,half+1)*((2.03-.33)/4095)
 kernel=np.exp(-.5*(kx/sigma)**2);kernel/=kernel.sum()
 smoothed[c]=np.convolve(np.pad([raw_interp(float(z),c) for z in heights],half,mode='edge'),kernel,mode='valid')
def interp(z,col):
 value=float(np.interp(z,heights,smoothed[col]))
 # Ellipsoidal crown avoids endpoint blur flattening the head into a roof.
 t=max(0,min(1,(z-1.55)/.40));t=t*t*t*(t*(t*6-15)+10)
 crown={1:.70,2:.78,3:.60}[col]*math.sqrt(max(.00001,1-((z-1.36)/.67)**2))
 return value*(1-t)+crown*t
def head_shift(z):
 t=max(0,min(1,(z-1.0)/.30));return 0.0
def front(x,z):
 r=interp(z,1);y=-interp(z,2)*max(0,1-(abs(x)/r)**2)**.50
 # Small integrated eye beds: tangent correction is confined to the painted eye.
 # The forehead/muzzle silhouette remains the full continuous head surface.
 for side in [-1,1]:
  cx=side*.287;cz=1.745
  q=((x-cx)/.14)**2+((z-cz)/.12)**2
  mask=math.exp(-.60*q**3)
  anchor=-interp(cz,2)*max(0,1-(abs(cx)/interp(cz,1))**2)**.50
  plane=anchor+.030+.55*(z-cz)+side*.40*(x-cx)
  y=y*(1-mask)+plane*mask
 return y-head_shift(z)
def clamp(v):return max(0,min(1,v))
vs=[];fs=[];colors=[];nr=112;ns=112
for j in range(nr):
 z=.33+1.70*j/(nr-1);rx=interp(z,1)
 for k in range(ns):
  a=2*math.pi*k/ns;x=rx*math.cos(a);s=math.sin(a);f=max(0,-s)
  y=(front(x,z) if s<0 else interp(z,3)*s-head_shift(z))
  hidden_taper=1-.60*clamp((.57-z)/.12)
  vs.append((x*hidden_taper,y*hidden_taper,z))
  # Paint follows the continuous cheek, not an attached snout sphere.
  ell=(x/.71)**2+((z-1.345)/.40)**2
  mask=clamp((1.12-ell)*2.9)*clamp((f-.12)*4.5)
  belly=clamp((1-((x/.52)**2+((z-.78)/.31)**2))*2)*clamp(f*2)
  b=rgb('#FFE36A');bel=rgb('#FFF084');mu=rgb('#FFAF21')
  c=tuple(b[i]*(1-belly)+bel[i]*belly for i in range(3))
  colors.append(tuple(c[i]*(1-mask)+mu[i]*mask for i in range(3))+(1,))
for j in range(nr-1):
 for k in range(ns):
  a=j*ns+k;b=j*ns+(k+1)%ns;fs.append((a,b,b+ns,a+ns))
fs.extend([tuple(reversed(tuple(range(ns)))),tuple((nr-1)*ns+k for k in range(ns))])
body=mesh('Lulu_ContinuousBody',vs,fs,bodymat);smooth(body)
attribute=body.data.color_attributes.new(name='BodyPaint',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colors):attribute.data[i].color=c
paintmat=bodymat.copy();paintmat.name='Lulu_BodyPaint';body.data.materials[0]=paintmat
bs=paintmat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.74
col=paintmat.node_tree.nodes.new('ShaderNodeVertexColor');col.layer_name='BodyPaint';paintmat.node_tree.links.new(col.outputs['Color'],bs.inputs['Base Color'])

# One implicit surface for hips and thighs; smooth blending has no union crease.
import runpy
pants=runpy.run_path(str(Path(__file__).with_name('lulu_garment.py')))['build_garment'](mesh,pantsmat,bpy,np)
smooth(pants)
sm=pants.modifiers.new('Continuous garment curvature','SMOOTH');sm.factor=.40;sm.iterations=5;bpy.context.view_layer.objects.active=pants;bpy.ops.object.modifier_apply(modifier=sm.name)
def subtract(tool):
 bpy.context.view_layer.objects.active=pants
 mod=pants.modifiers.new('Leg opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
subtract(box('Rounded crotch',(0,0,.025),(.23,1.5,.44),pantsmat,.042))
for side in [-1,1]:subtract(cylinder('Cuff cutter',(side*.30,-.025,.055),.137,.25,pantsmat,64))
# The fitted upper hip edge is the waistband; no separate intersecting strip.
# Clearly visible in the complete back reference, at the middle of the waistband.
tv=[];tf=[];tn=40
for z,rx,ry,cy in [(.42,.003,.006,.395),(.44,.047,.027,.408),(.49,.064,.04,.419),(.54,.048,.033,.41),(.59,.026,.022,.379),(.64,.024,.018,.36)]:
 for k in range(tn):
  a=k*math.pi*2/tn;tv.append((rx*math.cos(a),cy-.02+ry*math.sin(a),z-.045))
for j in range(5):
 for k in range(tn):a=j*tn+k;b=j*tn+(k+1)%tn;tf.append((a,b,b+tn,a+tn))
tf.extend([tuple(reversed(range(tn))),tuple(5*tn+k for k in range(tn))])
tail=mesh('Waist_BackTeardrop',tv,tf,bodymat);smooth(tail)
sub=tail.modifiers.new('Soft teardrop','SUBSURF');sub.levels=2;bpy.context.view_layer.objects.active=tail;bpy.ops.object.modifier_apply(modifier=sub.name)

# Eye pigment is painted on the actual curved head and cannot float in side views.
# All eye contours are measured in frontal object coordinates, then wrapped by UV.
import numpy as np,struct,zlib
size=2048
zz=np.linspace(.33,2.03,size,dtype=np.float32)[:,None]
angles=np.linspace(0,2*math.pi,size,dtype=np.float32)[None,:]
rr=np.array([interp(float(z),1) for z in zz[:,0]],dtype=np.float32)[:,None]
xx=rr*np.cos(angles);f=np.maximum(0,-np.sin(angles))
ell=(xx/.71)**2+((zz-1.345)/.40)**2
m=np.clip((1.12-ell)*2.9,0,1)*np.clip((f-.12)*4.5,0,1)
belly=np.clip((1-((xx/.52)**2+((zz-.78)/.31)**2))*2,0,1)*np.clip(f*2,0,1)
b=np.array(rgb('#FFE36A')[:3]);bel=np.array(rgb('#FFF084')[:3]);mu=np.array(rgb('#FFAF21')[:3])
colors=(b[None,None,:]*(1-belly[:,:,None])+bel[None,None,:]*belly[:,:,None])*(1-m[:,:,None])+mu[None,None,:]*m[:,:,None]
def pigment(cx,cz,rx,rz,color,tilt=0,clip=None):
 q=((xx-cx-(zz-cz)*tilt)/rx)**2+((zz-cz)/rz)**2
 alpha=np.clip((1-q)*110,0,1)*(f>.05)
 if clip is not None:alpha*=clip
 global colors
 colors=colors*(1-alpha[:,:,None])+np.array(rgb(color)[:3])[None,None,:]*alpha[:,:,None]
for side in [-1,1]:
 cx=side*.287;cz=1.747+side*.005
 tilt=-side*.15
 white_shape=np.clip((1-((xx-cx-(zz-cz)*tilt)/.103)**2-((zz-cz)/.086)**2)*110,0,1)
 pigment(cx,cz,.104,.087,'#B2A26A',tilt=tilt)
 pigment(cx,cz,.103,.086,'#FFFEED',tilt=tilt)
 pigment(cx-side*.014+.008,cz+.002,.083,.079,'#568CC6',tilt=tilt,clip=white_shape)
 pigment(cx-side*.026+.010,cz+.006,.068,.070,'#02050B',tilt=tilt,clip=white_shape)
 pigment(cx-side*.026+.033,cz+.046,.018,.016,'#FFFFFF',clip=white_shape)
srgb=np.where(colors<=.0031308,colors*12.92,1.055*np.power(colors,1/2.4)-.055)
pixels=(np.clip(srgb,0,1)*255+.5).astype(np.uint8)[::-1]
def chunk(typ,data):return struct.pack('>I',len(data))+typ+data+struct.pack('>I',zlib.crc32(typ+data)&0xffffffff)
texture_path=SRC/'lulu-body-paint.png'
raw=b''.join(b'\0'+row.tobytes() for row in pixels)
texture_path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))
uv=body.data.uv_layers.new(name='ReferencePaintUV')
for poly in body.data.polygons:
 ids=[body.data.loops[i].vertex_index for i in poly.loop_indices]
 seam=any(i%ns==0 for i in ids) and any(i%ns==ns-1 for i in ids)
 for loop,i in zip(poly.loop_indices,ids):
  u=(i%ns)/ns
  if seam and i%ns==0:u=1
  uv.data[loop].uv=(u,(i//ns)/(nr-1))
tex=paintmat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(texture_path),check_existing=False);tex.image.pack();tex.interpolation='Linear'
paintmat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
# Remove exported color attributes so glTF does not multiply pigment a second time.
body.data.color_attributes.remove(attribute)
for side in [-1,1]:
 # Rounded triangular cupped ears; concave front instead of thin spike.
 corners=[(-.085,0),(.14,.035),(.135,.205)];boundary=[]
 for i,c in enumerate(corners):
  prev=corners[(i-1)%3];nxt=corners[(i+1)%3]
  p=(c[0]*.58+prev[0]*.42,c[1]*.58+prev[1]*.42)
  q=(c[0]*.58+nxt[0]*.42,c[1]*.58+nxt[1]*.42)
  for k in range(16):
   t=k/16;boundary.append(((1-t)**2*p[0]+2*t*(1-t)*c[0]+t*t*q[0],(1-t)**2*p[1]+2*t*(1-t)*c[1]+t*t*q[1]))
 ev=[];ef=[];center=(.065,.080);N=len(boundary)
 for r in [.001,.25,.5,.75,1]:
  for x,z in boundary:
   xx=center[0]+(x-center[0])*r;zz=center[1]+(z-center[1])*r
   ev.append((side*(.495+xx),-.095+.065*(1-r*r),1.79+zz))
 for j in range(4):
  for k in range(N):a=j*N+k;b=j*N+(k+1)%N;ef.append((a,b,b+N,a+N))
 angle=side*math.radians(45)
 ev=[(side*.445+(x-side*.495)*math.cos(angle)-(y-.02)*math.sin(angle),.02+(x-side*.495)*math.sin(angle)+(y-.02)*math.cos(angle),z-.025) for x,y,z in ev]
 ev=[(side*.46+(x-side*.46)*1.30-side*.06,y*1.30,1.78+(z-1.78)*1.30-.06) for x,y,z in ev]
 ev=[(x+side*.014,.02+(y-.02)*1.65,z+.012) for x,y,z in ev]
 ear=mesh('Ear_'+str(side),ev,[tuple(reversed(f)) for f in ef] if side==1 else ef,bodymat);smooth(ear)
 so=ear.modifiers.new('Soft shell thickness','SOLIDIFY');so.thickness=.040;bpy.context.view_layer.objects.active=ear;bpy.ops.object.modifier_apply(modifier=so.name)
 sub=ear.modifiers.new('Rounded ear surface','SUBSURF');sub.levels=2;bpy.context.view_layer.objects.active=ear;bpy.ops.object.modifier_apply(modifier=sub.name)
 # Continuous tapered arm surface with a small rounded thumb.
 av=[];af=[];stations=[(1.03,.49,-.005,.005),(.96,.51,-.005,.09),(.86,.57,-.03,.108),(.70,.61,-.065,.102),(.60,.612,-.09,.092),(.51,.61,-.11,.084),(.455,.605,-.11,.065),(.425,.605,-.11,.025)]
 for z,x,y,r in stations:
  for k in range(40):a=k*math.pi/20;av.append((side*(x+r*math.cos(a)),y-.04+r*.94*math.sin(a),z))
 for j in range(len(stations)-1):
  for k in range(40):a=j*40+k;b=j*40+(k+1)%40;af.append((a,b,b+40,a+40))
 af.extend([tuple(reversed(tuple(range(40)))),tuple((len(stations)-1)*40+k for k in range(40))])
 arm=mesh('Arm_'+str(side),av,af if side==-1 else [tuple(reversed(f)) for f in af],bodymat);smooth(arm)
 sub=arm.modifiers.new('Organic arm','SUBSURF');sub.levels=2;bpy.context.view_layer.objects.active=arm;bpy.ops.object.modifier_apply(modifier=sub.name)
 hand=sphere('Hand_'+str(side),(side*.605,-.15,.505),(.074,.078,.083),bodymat,32,20)
 thumb=sphere('Thumb_'+str(side),(side*.554,-.195,.528),(.038,.043,.054),bodymat,24,16)
 fingers=[sphere('Finger_'+str(side)+'_'+str(k),(side*(.565+.034*k),-.163,.446+.005*abs(k-1)),(.029,.044,.038),bodymat,20,12) for k in range(3)]
 bpy.ops.object.select_all(action='DESELECT')
 for o in [arm,hand,thumb]+fingers:o.select_set(True)
 bpy.context.view_layer.objects.active=arm;bpy.ops.object.join()
 rem=arm.modifiers.new('Continuous hand and arm','REMESH');rem.mode='VOXEL';rem.voxel_size=.008;bpy.ops.object.modifier_apply(modifier=rem.name)
 sm=arm.modifiers.new('Hand smoothing','SMOOTH');sm.factor=.55;sm.iterations=8;bpy.ops.object.modifier_apply(modifier=sm.name);smooth(arm)
 fv=[];ff=[]
 for z,rx,ry in [(.002,.115,.155),(.022,.151,.19),(.12,.154,.19),(.23,.143,.12),(.26,.11,.105)]:
  for k in range(48):
   a=k*math.pi/24;fv.append((side*.30+rx*math.cos(a),-.025-.08*(1-min(1,z/.22))+ry*math.sin(a),z))
 for j in range(4):
  for k in range(48):a=j*48+k;b=j*48+(k+1)%48;ff.append((a,b,b+48,a+48))
 ff.extend([tuple(reversed(tuple(range(48)))),tuple(192+k for k in range(48))])
 foot=mesh('Foot_'+str(side),fv,ff,bodymat);smooth(foot)
 sub=foot.modifiers.new('Soft small feet','SUBSURF');sub.levels=2;bpy.context.view_layer.objects.active=foot;bpy.ops.object.modifier_apply(modifier=sub.name)

smilepoints=[]
for i in range(25):
 x=-.180+i*.360/24;z=1.17+.052*(x/.180)**2;smilepoints.append((x,front(x,z)-.006,z))
curve('Smile',smilepoints,.0035,mouth)
# The reference orange has a broad resting base and rounded shoulders.
fv=[];ff=[];N=80
for z,r in [(2.004,.10),(2.023,.155),(2.065,.184),(2.12,.188),(2.170,.164),(2.208,.114),(2.228,.055),(2.231,.007)]:
 for k in range(N):
  a=k*2*math.pi/N;fv.append((r*math.cos(a),-.02+r*.93*math.sin(a),z))
for j in range(7):
 for k in range(N):a=j*N+k;b=j*N+(k+1)%N;ff.append((a,b,b+N,a+N))
ff.extend([tuple(reversed(range(N))),tuple(7*N+k for k in range(N))])
fruit=mesh('HeadOrange',fv,ff,orange);smooth(fruit)
sub=fruit.modifiers.new('Fruit rounded contour','SUBSURF');sub.levels=2;bpy.context.view_layer.objects.active=fruit;bpy.ops.object.modifier_apply(modifier=sub.name)
curve('FruitStem',[(0,-.02,2.226),(.003,-.02,2.255),(.010,-.015,2.275)],.019,leafmat)
sphere('FruitStemTip',(.010,-.015,2.275),(.019,.019,.018),leafmat,24,16)
for o in bpy.data.objects:
 if o.name.startswith(('HeadOrange','Fruit')):o.location.z-=.017;o.location.y-=0.0
# Handle meets the wrist; hidden at rest by the runtime to expose silhouette.
canparts=[]
canparts.append(cylinder('Can_Body',(.77,-.12,.22),.15,.27,watermat,32))
canparts.append(curve('CanHandle',[(.64,-.11,.36),(.74,-.11,.46),(.91,-.11,.41),(.93,-.11,.23)],.026,watermat))
canparts.append(curve('CanSpout',[(.88,-.12,.18),(1.03,-.12,.23),(1.10,-.12,.33)],.043,watermat))
canparts.append(sphere('CanRose',(1.13,-.12,.35),(.085,.045,.075),white,24,16))
objects=[o for o in bpy.data.objects if o not in start]
# Reuse validated armature and action export with the new physical landmarks.
rig_code=base.split('# Skin all parts')[1].split('# ---------- Farm restaurant')[0]
rig_code=rig_code[rig_code.index('armdata='):]
rig_code=rig_code.replace("('Arm','Hand')","('Arm','Hand','Thumb')")
rig_code=rig_code.replace("(-.48,0,.95),(-.60,0,.45)","(-.51,0,.96),(-.65,-.10,.39)").replace("(.48,0,.95),(.60,0,.45)","(.51,0,.96),(.65,-.10,.39)")
exec(rig_code)
print('LULU_REFERENCE_REBUILD_COMPLETE')
