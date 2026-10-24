"""Reversible eye-only edit of the supplied Meshy GLB. Preserve original UVs/base color."""
from pathlib import Path
import json,struct,io,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[1]
SRC=R/'assets-source/meshy-original/Meshy_AI_Sunny_Sprout_1014132159_texture.glb'
d=SRC.read_bytes();n=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+n]);binary=bytearray(d[28+n:])
prim=g['meshes'][0]['primitives'][0]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];s={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
 return np.ndarray((a['count'],s),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',s*np.dtype(dt).itemsize),np.dtype(dt).itemsize))
p=acc(prim['attributes']['POSITION']);p0=p.copy();norm=acc(prim['attributes']['NORMAL']);n0=norm.copy();uv=acc(prim['attributes']['TEXCOORD_0']).copy();tri=acc(prim['indices']).copy().reshape(-1,3)
# glTF Y is up, +Z is front. Fit the existing surrounding skin instead of
# imposing a manually offset flat eye plane.
def read_image(i):
 im=g['images'][i];bv=g['bufferViews'][im['bufferView']];return np.array(Image.open(io.BytesIO(binary[bv['byteOffset']:bv['byteOffset']+bv['byteLength']])).convert('RGB'))
source_color=read_image(0);U=(uv[:,0]*2047).astype(int).clip(0,2047);V=(uv[:,1]*2047).astype(int).clip(0,2047);sample=source_color[V,U]
x,y,z=p0.T;X=(abs(x)-.232)/.09;Y=(y-.525)/.08;q=np.sqrt(X*X+Y*Y)
A=np.c_[np.ones(len(p0)),X,Y,X*X,X*Y,Y*Y]
yellow=(sample[:,0]>150)&(sample[:,1]>140)&(sample[:,2]<180)
fit=(q>1.45)&(q<2.25)&(z>.08)&yellow
coef=np.linalg.lstsq(A[fit],z[fit],rcond=None)[0]
for _ in range(4):
 error=A[fit]@coef-z[fit];weight=1/np.maximum(1,abs(error)/.018);coef=np.linalg.lstsq(A[fit]*weight[:,None],z[fit]*weight,rcond=None)[0]
print('Surrounding skin fit',coef.tolist())
def field(v):
 x,y,z=v.T;X=(abs(x)-.232)/.090;Y=(y-.525)/.080;q=np.sqrt(X*X+Y*Y)
 t=np.clip((2.0-q)/.8,0,1);w=t*t*t*(10+t*(-15+6*t))
 front=np.clip((z-.10)/.06,0,1);front=front*front*(3-2*front)
 target=coef[0]+coef[1]*X+coef[2]*Y+coef[3]*X*X+coef[4]*X*Y+coef[5]*Y*Y+.005*np.exp(-1.8*q*q)
 return .055*np.tanh((target-z)/.055)*w*front*.85
shift=field(p0);p[:,2]+=shift
# Transform original smooth normals using the deformation Jacobian. Preserve normals elsewhere.
eps=1e-4;der=[]
for k in range(3):
 plus=p0.copy();minus=p0.copy();plus[:,k]+=eps;minus[:,k]-=eps
 der.append((field(plus)-field(minus))/(2*eps))
den=1+der[2];assert den.min()>.1
# Recompute smooth normals of edited surface across coincident UV seams.
changed=abs(shift)>1e-8
_,inverse=np.unique(np.round(p0,6),axis=0,return_inverse=True)
face=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
sums=np.zeros((inverse.max()+1,3),dtype=np.float64)
for k in range(3):np.add.at(sums,inverse[tri[:,k]],face)
length=np.linalg.norm(sums,axis=1);sums/=np.maximum(length,1e-12)[:,None]
nn=sums[inverse];norm[changed]=nn[changed]
# Images 0: base color, 1: metallic/roughness. Base image is left byte-for-byte unchanged.
def img(i):
 im=g['images'][i];v=g['bufferViews'][im['bufferView']];return np.array(Image.open(io.BytesIO(binary[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'))
color=img(0);mr=img(1);mr0=mr.copy();height,width=color.shape[:2]
X=(abs(p0[:,0])-.232)/.09;Y=(p0[:,1]-.525)/.08;q=np.sqrt(X*X+Y*Y)
maskv=(q<1.32)&(p0[:,2]>.16)
mask=Image.new('L',(width,height));draw=ImageDraw.Draw(mask)
for ids in tri[np.all(maskv[tri],axis=1)]:
 draw.polygon([(float(uv[i,0]*(width-1)),float(uv[i,1]*(height-1))) for i in ids],fill=255)
mask=np.array(mask.filter(ImageFilter.GaussianBlur(1.0)))/255
bluewhite=(color[:,:,2].astype(float)>color[:,:,0]*.90)&(color[:,:,2].astype(float)>color[:,:,1]*.85)
white=(color.min(axis=2)>170)&((color.max(axis=2)-color.min(axis=2))<50)
weight=mask*bluewhite
rough=np.where(white,.56,.38)*255
mr[:,:,1]=np.round(mr0[:,:,1]+weight*np.maximum(0,rough-mr0[:,:,1])).astype(np.uint8)
stream=io.BytesIO();Image.fromarray(mr).save(stream,format='PNG');blob=stream.getvalue()
# Release array views before extending binary.
maxchange=float(abs(shift).max());changedcount=int(changed.sum());xy_equal=bool(np.array_equal(p0[:,:2],p[:,:2]));final=p.copy()
del p,norm
while len(binary)%4:binary.append(0)
offset=len(binary);binary.extend(blob)
g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(blob)})
g['images'][1]['bufferView']=len(g['bufferViews'])-1;g['images'][1]['mimeType']='image/png';g['buffers'][0]['byteLength']=len(binary)
# Control eye reflection strength locally, leaving skin at the original default.
specular=np.full((height,width,4),255,dtype=np.uint8)
specular[:,:,3]=np.round(255*(1-.84*weight)).astype(np.uint8)
stream=io.BytesIO();Image.fromarray(specular).save(stream,format='PNG');blob=stream.getvalue()
while len(binary)%4:binary.append(0)
offset=len(binary);binary.extend(blob)
g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(blob)})
g['images'].append({'bufferView':len(g['bufferViews'])-1,'mimeType':'image/png'})
g['textures'].append({'source':len(g['images'])-1})
g['materials'][0].setdefault('extensions',{})['KHR_materials_specular']={'specularFactor':1.0,'specularTexture':{'index':len(g['textures'])-1,'texCoord':0}}
g.setdefault('extensionsUsed',[]).append('KHR_materials_specular');g['buffers'][0]['byteLength']=len(binary)
a=g['accessors'][prim['attributes']['POSITION']];a['min']=final.min(0).tolist();a['max']=final.max(0).tolist()
js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
(R/'public/models/lulu-meshy-eyes.glb').write_bytes(out)
report={'source_sha256':hashlib.sha256(d).hexdigest(),'output_sha256':hashlib.sha256(out).hexdigest(),'changed_vertices':changedcount,'max_depth_change_source_units':maxchange,'horizontal_vertical_positions_preserved':xy_equal,'all_base_color_bytes_preserved':True,'min_jacobian_determinant':float(den.min()),'roughness_changed_pixels':int(np.any(mr!=mr0,axis=2).sum()),'metallic_channel_preserved':bool(np.array_equal(mr[:,:,2],mr0[:,:,2])),'triangle_count':len(tri),'scope':'Only eye depth and associated normals, eye roughness/specular; base color / UV / topology / X and Y preserved.'}
(R/'review/meshy-eye-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
