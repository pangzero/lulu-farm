"""Reference colors on neck-r02. Mesh positions, normals and transforms fixed."""
from pathlib import Path
import argparse,copy,hashlib,json,struct
import numpy as np
from PIL import Image

R=Path(__file__).resolve().parents[1];D=R/'review/lulu-hybrid-color-20261023'
def rgb(h):return np.array([int(h[i:i+2],16) for i in (1,3,5)],float)/255
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def linear(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def load(p):
    b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),bytearray(b[28+n:])
def accessor(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    return np.ndarray((a['count'],k),dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*k),dt.itemsize)).copy()
def trs(n):
    if 'matrix' in n:return np.array(n['matrix']).reshape(4,4).T
    x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
    m[:3,:3]=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
def worlds(g):
    out={}
    def visit(i,m):
        m=m@trs(g['nodes'][i]);out[i]=m
        for j in g['nodes'][i].get('children',[]):visit(j,m)
    for i in g['scenes'][g.get('scene',0)]['nodes']:visit(i,np.eye(4))
    return out
SKIN=rgb('#ffe662');MUZZLE=rgb('#ffa414');PANTS=rgb('#ff963f')
def skincolor(p,head=False):
    col=np.tile(SKIN,(len(p),1))
    if head:
        x,y,z=p.T
        ry=np.where(y>.627,.126,.161)
        radius=np.sqrt((x/.315)**2+((y-.627)/ry)**2+((z-.255)/.65)**2)
        a=(1-smooth(.89,1.105,radius))*smooth(.015,.075,z)
        orange=MUZZLE[None,:]+np.c_[np.zeros(len(p)),np.clip((y-.60)*.21,0,.03),np.zeros(len(p))]
        col=col*(1-a[:,None])+orange*a[:,None]
    return np.clip(col,0,1)

def artwork(O,head):
    W,H=2048,1536;xx,yy=np.meshgrid(np.linspace(-.34,.34,W),np.linspace(.945,.495,H))
    pp=head[(head[:,2]>.025)&(head[:,1]>.495)]
    ix=np.clip(np.rint((pp[:,0]+.34)/.68*(W-1)).astype(int),0,W-1);iy=np.clip(np.rint((.945-pp[:,1])/.45*(H-1)).astype(int),0,H-1)
    dep=np.full((H,W),-1.,np.float32);np.maximum.at(dep,(iy,ix),pp[:,2]);valid=dep>=0
    def boxblur(a,r):
        for axis in (0,1):
            pads=[(0,0),(0,0)];pads[axis]=(r,r);p=np.pad(a,pads,mode='edge')
            cs=np.cumsum(p,axis=axis,dtype=float);shape=list(cs.shape);shape[axis]=1
            cs=np.concatenate([np.zeros(shape),cs],axis=axis)
            hi=[slice(None),slice(None)];lo=hi.copy();hi[axis]=slice(2*r+1,None);lo[axis]=slice(None,-(2*r+1))
            a=(cs[tuple(hi)]-cs[tuple(lo)])/(2*r+1)
        return a
    mask=valid.astype(float);value=np.maximum(dep,0).astype(float)
    for _ in range(3):mask=boxblur(mask,5);value=boxblur(value,5)
    z=np.where(mask>1e-10,value/np.maximum(mask,1e-10),.22)
    base=skincolor(np.c_[xx.ravel(),yy.ravel(),z.ravel()],True).reshape(H,W,3)
    arr=base.copy();rough=np.full((H,W,3),[1.,.87,0.]);eye_data=[]
    for direction in [1,-1]:
        ex=-direction*.120;ey=.801;rx=.043;ry=.033
        angle=direction*.40;c=np.cos(angle);s=np.sin(angle)
        dx=xx-ex;dy=yy-ey;u=(c*dx+s*dy)/rx;v=(-s*dx+c*dy)/ry
        # Small shape variation and nonuniform white, matching reference gaze.
        qx=u+.020*direction*v; r=np.sqrt(qx*qx+v*v)
        white=1-smooth(.986,1.014,r)
        arr=arr*(1-white[...,None])+rgb('#fffdf0')*white[...,None]
        iris=np.sqrt(((u-direction*.20)/.75)**2+((v+.015)/.87)**2)
        ia=(1-smooth(.98,1.015,iris))*white
        grad=np.clip((v+1)/2,0,1)
        blue=rgb('#4c80ba')*(1-grad[...,None])+rgb('#7ba9dc')*grad[...,None]
        arr=arr*(1-ia[...,None])+blue*ia[...,None]
        pupil=np.sqrt(((u-direction*.32)/.57)**2+((v+.04)/.70)**2)
        pa=(1-smooth(.982,1.016,pupil))*white
        arr=arr*(1-pa[...,None])+rgb('#050a10')*pa[...,None]
        glint=np.sqrt(((u-direction*.32-.15)/.18)**2+((v-.34)/.16)**2)
        ga=(1-smooth(.97,1.03,glint))*pa
        arr=arr*(1-ga[...,None])+rgb('#fffefa')*ga[...,None]
        edge=(1-smooth(.995,1.025,r))*smooth(.955,.98,r)
        arr=arr*(1-edge[...,None])+rgb('#414239')*edge[...,None]
        rough[:,:,1]=rough[:,:,1]*(1-white)+.56*white
        eye_data.append({'center_world_xy':[ex,ey],'radii_xy':[rx,ry],'rotation_radians':angle,'iris_offset':direction*.20,'pupil_offset':direction*.32})
    curve=.575+.024*(xx/.080)**2
    distance=np.abs(yy-curve)/np.sqrt(1+(.048*xx/.080**2)**2)
    a=(1-smooth(.00075,.00135,distance))*(1-smooth(.079,.081,np.abs(xx)))
    arr=arr*(1-a[...,None])+rgb('#573725')*a[...,None]
    Image.fromarray(np.uint8(np.clip(arr*255,0,255))).save(O/'face-basecolor.png')
    Image.fromarray(np.uint8(np.clip(rough*255,0,255))).save(O/'face-metalrough.png')
    (O/'landmarks.json').write_text(json.dumps({'eyes':eye_data,'mouth':'y=.575+.024*(x/.080)^2','muzzle_center_y':.627,'palette':{'skin':'#ffe662','muzzle':'#ffa414','shorts':'#ff963f'},'refs':['reference/full-front.png','reference/full-side.png','reference/full-back.png']},indent=2))

def build(rev):
    O=D/rev;O.mkdir(exist_ok=False);source=D/'baseline/lulu-neck.glb';g,b=load(source);original=copy.deepcopy(g);wm=worlds(g)
    headni=next(i for i,n in enumerate(g['nodes']) if n.get('name')=='Lulu_Head_Mirrored');hp=accessor(g,b,g['meshes'][g['nodes'][headni]['mesh']]['primitives'][0]['attributes']['POSITION']);M=wm[headni];hp=np.einsum('ij,kj->ki',M[:3,:3],hp)+M[:3,3];artwork(O,hp)
    def buf(raw):
        b.extend(b'\0'*((-len(b))%4));i=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(raw)});b.extend(raw);return i
    def acc(a,typ,component=5126):
        dt={5126:'<f4',5125:'<u4'}[component];a=np.ascontiguousarray(a,dtype=dt);i=len(g['accessors']);g['accessors'].append({'bufferView':buf(a.tobytes()),'componentType':component,'count':len(a),'type':typ});return i
    sampler=len(g.setdefault('samplers',[]));g['samplers'].append({'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071});textures=[]
    for name in ['face-basecolor.png','face-metalrough.png']:
        i=len(g.setdefault('images',[]));g['images'].append({'name':name,'mimeType':'image/png','bufferView':buf((O/name).read_bytes())});t=len(g.setdefault('textures',[]));g['textures'].append({'source':i,'sampler':sampler});textures.append(t)
    plain=len(g['materials']);g['materials'].append({'name':'Lulu reference matte colors','extensions':{'KHR_materials_specular':{'specularFactor':.18}},'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'roughnessFactor':.87,'metallicFactor':0}})
    face=len(g['materials']);g['materials'].append({'name':'Lulu reference eyes and smile','extensions':{'KHR_materials_specular':{'specularFactor':.15}},'pbrMetallicRoughness':{'baseColorTexture':{'index':textures[0]},'metallicRoughnessTexture':{'index':textures[1]},'roughnessFactor':1,'metallicFactor':0}})
    g['extensionsUsed']=list(dict.fromkeys(g.get('extensionsUsed',[])+['KHR_materials_specular']))
    for ni,node in enumerate(g['nodes']):
        if 'mesh' not in node:continue
        mesh=g['meshes'][node['mesh']];new=[]
        for pr in mesh['primitives']:
            p=accessor(original,b,pr['attributes']['POSITION']);M=wm[ni];world=np.einsum('ij,kj->ki',M[:3,:3],p)+M[:3,3];name=node['name'];colors=skincolor(world,name in ['Lulu_Head_Mirrored','Neck_Transition'])
            if name=='Shorts':
                colors=np.tile(PANTS,(len(p),1));colors+=np.clip((world[:,1]-.14)*.035,-.004,.004)[:,None]
            if name=='Original_Crown_Ornament':
                colors=np.tile(rgb('#ffac24'),(len(p),1));leaf=smooth(1.009,1.017,world[:,1]);colors=colors*(1-leaf[:,None])+rgb('#7fa83c')*leaf[:,None]
            attrs=copy.deepcopy(pr['attributes']);attrs['COLOR_0']=acc(linear(np.clip(colors,0,1)),'VEC3')
            if name=='Lulu_Head_Mirrored':
                f=accessor(original,b,pr['indices']).reshape(-1,3);mid=world[f].mean(1);onface=(mid[:,2]>.065)&(mid[:,1]>.515)&(mid[:,1]<.925)
                uv=np.c_[(world[:,0]+.34)/.68,(.945-world[:,1])/.45];ui=acc(uv,'VEC2')
                for inside in [False,True]:
                    sub=f[onface==inside]
                    if not len(sub):continue
                    at=copy.deepcopy(attrs)
                    if inside:at.pop('COLOR_0',None);at['TEXCOORD_0']=ui
                    new.append({'attributes':at,'indices':acc(sub.reshape(-1,1),'SCALAR',5125),'material':face if inside else plain,'mode':4})
            else:new.append({**pr,'attributes':attrs,'material':plain})
        mesh['primitives']=new
    g['buffers'][0]['byteLength']=len(b);g.setdefault('extras',{})['neck_color_study']={'revision':rev,'base':'neck-r02','scope':'Colors/materials/face UV only. Every position, normal, triangle and node transform retained.','source_credit':'Spencer0131 Sketchfab a5747f74f0034470a2029a85f6e9c11d (head); user Meshy r04 (body)'}
    js=json.dumps(g,separators=(',',':')).encode();js+=b' '*((-len(js))%4);b+=b'\0'*((-len(b))%4);out=O/'lulu-colored.glb';out.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(b))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(b),0x004e4942)+b)
    (O/'build.json').write_text(json.dumps({'revision':rev,'base':'neck-r02','nodes_unchanged':g['nodes']==original['nodes'],'geometry_edits':0,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'status':'COLOR_CANDIDATE_USER_REVIEW_PENDING'},indent=2));print(out)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--revision',default='color-r01');build(ap.parse_args().revision)
