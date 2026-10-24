"""Reference colour study of the untouched Spencer0131 Lulu geometry.

Adds corner-preserving material groups, linear vertex colours and a native UV
face artwork. No vertex, normal, source node transform or triangle is moved.
"""
from pathlib import Path
import argparse, copy, hashlib, io, json, math, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

R=Path(__file__).resolve().parents[1]
D=R/'review/lulu-sketchfab-color-20261019'
SOURCE=D/'baseline/a5747f74f0034470a2029a85f6e9c11d.glb'
ROLL=math.radians(8.7)
C,S=math.cos(ROLL),math.sin(ROLL)

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def rgb(h):
    return np.array([int(h[i:i+2],16) for i in (1,3,5)],float)/255

SKIN=rgb('#ffe35a');ORANGE=rgb('#ffa00b');SHORTS=rgb('#ff963d')
FOOT_PROFILE=None

def foot_profiles():
    global FOOT_PROFILE
    if FOOT_PROFILE is not None:return FOOT_PROFILE
    p=np.load(D/'baseline/geometry.npz')['p'];profiles=[]
    for sign in [-1,1]:
        sub=p[(p[:,1]>.012)&(p[:,1]<.042)&(p[:,0]*sign>0)]
        x=sub[:,0]-sign*.225;z=sub[:,2]+.052
        a=(np.arctan2(z,x)+2*np.pi)%(2*np.pi);ii=np.floor(a/(2*np.pi)*96).astype(int)%96
        rr=np.hypot(x,z);bounds=np.zeros(96)
        np.maximum.at(bounds,ii,rr)
        for _ in range(3):bounds=(np.roll(bounds,1)+2*bounds+np.roll(bounds,-1))/4
        profiles.append(bounds)
    FOOT_PROFILE=profiles;return profiles

def headcoords(p):
    x,y,z=np.asarray(p).T
    return np.c_[C*x+S*(y-.72),-S*x+C*(y-.72)+.72,z]

def arm_mask(p):
    # Colour-only exclusion. Never carve or edit this original shoulder/hand.
    x,y,z=p.T
    centers=np.array([[.235,.435,.005],[.255,.435,.09],[.23,.465,.17],[.19,.51,.235],[.15,.54,.245]])
    d=np.full(len(p),np.inf)
    for a,b in zip(centers[:-1],centers[1:]):
        v=b-a;t=np.clip((p-a)@v/(v@v),0,1)
        d=np.minimum(d,np.linalg.norm(p-a-t[:,None]*v,axis=1))
    return (d<.057)&(x>.095)&(y<.603)

def colour(p,head_only=False):
    x,y,z=np.asarray(p).T;h=headcoords(p);hx,hy,hz=h.T
    col=np.tile(SKIN,(len(p),1))
    # Broad soft orange volume, lower than the eyes in the original turnaround.
    radius=np.sqrt((hx/.325)**2+((hy-.625)/.134)**2+((z-.265)/.60)**2)
    muzzle=(1-smooth(.90,1.075,radius))*smooth(-.005,.085,z)
    if not head_only:muzzle*=1-arm_mask(p)
    orange=ORANGE[None,:]+np.c_[np.zeros(len(p)),np.clip((hy-.57)*.22,0,.033),np.zeros(len(p))]
    col=col*(1-muzzle[:,None])+orange*muzzle[:,None]
    # The sculpted waistband is roughly .265 above the soles. The hem follows
    # the existing sloped short-leg openings, rather than a single flat cutoff.
    pants=1-smooth(.278,.280,y)
    # Follow the original rounded leg walls up to the sculpted cuff. A colour
    # boundary based on a flat height plane would leave orange ankle stripes.
    feet=np.zeros(len(p))
    for sign,profile in zip([-1,1],foot_profiles()):
        dx=x-sign*.225;dz=z+.052;theta=(np.arctan2(dz,dx)+2*np.pi)%(2*np.pi)
        value=theta/(2*np.pi)*96-.5;ii=np.floor(value).astype(int);t=value-ii
        r0=profile[ii%96]*(1-t)+profile[(ii+1)%96]*t
        limit=r0+np.clip((y-.025)*.06,0,.005)+.0015
        f=(1-smooth(limit-.0008,limit+.0010,np.hypot(dx,dz)))*(1-smooth(.109,.119,y))
        feet=np.maximum(feet,f)
    pants*=1-feet
    col=col*(1-pants[:,None])+SHORTS*pants[:,None]
    fr=np.sqrt(((hx+.00535)/.106)**2+((hy-.94473)/.074)**2+((z-.006)/.103)**2)
    fruit=(hy>.909)&(fr<1.08)
    col[fruit]=rgb('#ffac20')
    leaf=hy>1.022
    col[leaf]=rgb('#7caa37')
    return np.clip(col,0,1)

def load():
    data=SOURCE.read_bytes();n=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+n]),bytearray(data[28+n:])

def accessor(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
    size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']])
    return np.ndarray((a['count'],size),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*dt.itemsize),dt.itemsize)).copy()

def srgb_to_linear(c):
    return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)

def artwork(out,revision):
    # Editable UV-space eye/mouth paths; colour and proportions are based on the
    # original front/side/back refs, projected onto this sculpt's actual eyes.
    W,H=2048,1536
    xx,yy=np.meshgrid(np.linspace(-.345,.345,W),np.linspace(.93,.475,H))
    # The front skin is sampled from the source to retain the 3-D orange border.
    gg,bb=load();pp=[]
    for m in gg['meshes']:
        p=accessor(gg,bb,m['primitives'][0]['attributes']['POSITION'])
        hc=headcoords(p);keep=(p[:,2]>.04)&(hc[:,1]>.475)&(~arm_mask(p))
        pp.append(p[keep])
    pp=np.concatenate(pp);hc=headcoords(pp)
    ix=np.clip(np.rint((hc[:,0]+.345)/.69*(W-1)).astype(int),0,W-1)
    iy=np.clip(np.rint((.93-hc[:,1])/.455*(H-1)).astype(int),0,H-1)
    dep=np.full((H,W),-1.,np.float32);np.maximum.at(dep,(iy,ix),pp[:,2])
    valid=dep>=0
    # Normalized convolution fills the sparse projected point samples. It is
    # texture reconstruction only; source vertices remain immutable.
    def boxblur(a,r):
        for axis in (0,1):
            pads=[(0,0),(0,0)];pads[axis]=(r,r)
            p=np.pad(a,pads,mode='edge')
            cs=np.cumsum(p,axis=axis,dtype=float)
            shape=list(cs.shape);shape[axis]=1
            cs=np.concatenate([np.zeros(shape),cs],axis=axis)
            aa=[slice(None),slice(None)];bb=aa.copy();aa[axis]=slice(2*r+1,None);bb[axis]=slice(None,-(2*r+1))
            a=(cs[tuple(aa)]-cs[tuple(bb)])/(2*r+1)
        return a
    mask=valid.astype(float);value=np.maximum(dep,0).astype(float)
    for _ in range(3):mask=boxblur(mask,5);value=boxblur(value,5)
    z=np.where(mask>1e-10,value/np.maximum(mask,1e-10),.22)
    hy=yy;hx=xx
    # Invert the head roll back to source coordinates for the existing colour fn.
    px=C*hx-S*(hy-.72);py=S*hx+C*(hy-.72)+.72
    base=colour(np.c_[px.ravel(),py.ravel(),z.ravel()],head_only=True).reshape(H,W,3)
    image=Image.fromarray(np.uint8(np.clip(base*255,0,255)))
    rough=Image.new('RGB',(W,H),(255,224,0))
    eye_data=[(-.125,.792,.041,.044,1),(.124,.792,.041,.043,-1)]
    # Analytic masks rasterize the same editable ellipses into a high-res UV map.
    arr=np.asarray(image).copy().astype(float)
    rarr=np.asarray(rough).copy()
    paths=[]
    for ex,ey,rx,ry,direction in eye_data:
        u=(xx-ex)/rx;v=(yy-ey)/ry
        r=np.sqrt(u*u+v*v)
        white=1-smooth(.985,1.015,r)
        # Continuous near-black fine edge at the existing sculpted eye boundary.
        edge=(1-smooth(.98,1.018,r))*smooth(.94,.975,r)
        arr=arr*(1-white[...,None])+rgb('#fffdf1')*255*white[...,None]
        cx=direction*.20;cy=-.015
        iris=np.sqrt(((u-cx)/.76)**2+((v-cy)/.90)**2)
        ia=(1-smooth(.985,1.012,iris))*white
        g=np.clip((v+1)/2,0,1)
        blue=rgb('#548bc7')[None,None,:]*(1-g[...,None])+rgb('#7ba8d9')[None,None,:]*g[...,None]
        arr=arr*(1-ia[...,None])+blue*255*ia[...,None]
        pupil=np.sqrt(((u-direction*.32)/.59)**2+((v+.045)/.72)**2)
        pa=(1-smooth(.985,1.015,pupil))*white
        arr=arr*(1-pa[...,None])+rgb('#060b12')*255*pa[...,None]
        glint=np.sqrt(((u-direction*.27-.11)/.19)**2+((v-.35)/.17)**2)
        ga=(1-smooth(.97,1.03,glint))*pa
        arr=arr*(1-ga[...,None])+rgb('#fffefa')*255*ga[...,None]
        arr=arr*(1-edge[...,None])+rgb('#3b3b30')*255*edge[...,None]
        rarr[r<1.02]=[255,145,0]
        paths.append({'center_head_xy':[ex,ey],'radii':[rx,ry],'iris_offset':cx,'pupil_offset':direction*.32})
    # Original reference's small, fine smile. A texture, with no carved groove.
    curve=.573+.025*(xx/.078)**2
    dist=np.abs(yy-curve)/np.sqrt(1+(.05*xx/.078**2)**2)
    a=(1-smooth(.0008,.00145,dist))*(1-smooth(.077,.079,np.abs(xx)))
    arr=arr*(1-a[...,None])+rgb('#4e3323')*255*a[...,None]
    Image.fromarray(np.uint8(np.clip(arr,0,255))).save(out/'lulu-face-basecolor.png')
    Image.fromarray(rarr).save(out/'lulu-face-metalrough.png')
    (out/'eye-landmarks.json').write_text(json.dumps({'head_roll_degrees':8.7,'eyes':paths,'mouth':'y=.573+.025*(x/.078)^2; half width .078; fine brown-black line','refs':['lulu_front.png','lulu_side.png','lulu_back.png']},indent=2))
    # The source artwork remains editable and separates eyes from the smile.
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-.345 -.93 .69 .455">']
    for ex,ey,rx,ry,direction in eye_data:
        svg.append(f'<g transform="translate({ex} {-ey}) scale({rx} {-ry})"><ellipse rx="1" ry="1" fill="#fffdf1" stroke="#3b3b30" stroke-width=".035"/><ellipse cx="{direction*.20}" cy="-.015" rx=".76" ry=".90" fill="#6699cc"/><ellipse cx="{direction*.32}" cy="-.045" rx=".59" ry=".72" fill="#060b12"/><ellipse cx="{direction*.27+.11}" cy=".35" rx=".19" ry=".17" fill="#fffefa"/></g>')
    svg.append('<path d="M -.078 -.598 Q 0 -.548 .078 -.598" fill="none" stroke="#4e3323" stroke-width=".0022" stroke-linecap="round"/></svg>')
    (out/'lulu-face-artwork.svg').write_text('\n'.join(svg))

def build(revision):
    out=D/revision;out.mkdir(exist_ok=False)
    artwork(out,revision)
    g,b=load();source_g=copy.deepcopy(g)
    hand_source=D/'baseline/hand-colour-segmentation-r02.npz'
    if not hand_source.exists():hand_source=D/'baseline/hand-colour-segmentation.npz'
    hand_labels=np.load(hand_source)['arm_source_vertex']
    (out/'hand-colour-labels.npz').write_bytes(hand_source.read_bytes())
    vertex_offset=0
    def buf(a):
        b.extend(b'\0'*((-len(b))%4));i=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(a)});b.extend(a);return i
    def acc(a,typ,component=5126):
        i=len(g['accessors']);g['accessors'].append({'bufferView':buf(a.tobytes()),'componentType':component,'count':len(a),'type':typ});return i
    g['images']=[];g['textures']=[];g['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]
    for name in ['lulu-face-basecolor.png','lulu-face-metalrough.png']:
        i=len(g['images']);g['images'].append({'name':name,'mimeType':'image/png','bufferView':buf((out/name).read_bytes())});g['textures'].append({'source':i,'sampler':0})
    g['materials']=[{'name':'Lulu_Reference_Body_Colours','doubleSided':True,'extensions':{'KHR_materials_specular':{'specularFactor':.15}},'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'roughnessFactor':.88,'metallicFactor':0}}, {'name':'Lulu_Reference_Face_UV','doubleSided':True,'extensions':{'KHR_materials_specular':{'specularFactor':.15}},'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicRoughnessTexture':{'index':1},'roughnessFactor':1,'metallicFactor':0}}]
    g['extensionsUsed']=list(dict.fromkeys(g.get('extensionsUsed',[])+['KHR_materials_specular']))
    counts=[]
    for mi,mesh in enumerate(g['meshes']):
        pr=mesh['primitives'][0];p=accessor(source_g,b,pr['attributes']['POSITION']);f=accessor(source_g,b,pr['indices']).reshape(-1,3)
        colour_values=colour(p)
        x,y,z=p.T;v=z+.16
        palm_shell=(((x+.255)/.055)**2+((z+.13)/.125)**2<1.12)&(y>.180+.104*v+2.625*v*v)&(y<.46)
        colour_values[hand_labels[vertex_offset:vertex_offset+len(p)]|palm_shell]=SKIN
        vertex_offset+=len(p)
        co=srgb_to_linear(colour_values).astype('<f4');ci=acc(co,'VEC3')
        h=headcoords(p);uv=np.c_[(h[:,0]+.345)/.69,(.93-h[:,1])/.455].astype('<f4');ui=acc(uv,'VEC2')
        mid=p[f].mean(1);hh=headcoords(mid)
        face=(hh[:,1]>.502)&(hh[:,1]<.913)&(mid[:,2]>.085)&(~arm_mask(mid))
        prim=[]
        for isface in [False,True]:
            sub=f[face==isface]
            if not len(sub):continue
            attrs=copy.deepcopy(pr['attributes'])
            if isface:attrs['TEXCOORD_0']=ui
            else:attrs['COLOR_0']=ci
            prim.append({'attributes':attrs,'indices':acc(sub.astype('<u4').reshape(-1,1),'SCALAR',5125),'material':int(isface),'mode':4})
        mesh['primitives']=prim;counts.append({'mesh':mi,'source_triangles':len(f),'face_triangles':int(face.sum())})
    g['buffers'][0]['byteLength']=len(b);g.setdefault('extras',{})['lulu_colour_study']={'revision':revision,'source':'Spencer0131 / Sketchfab a5747f74f0034470a2029a85f6e9c11d','scope':'Vertex positions, normals, original node transforms and all original triangles preserved. Materials, UV, colours only. Raised left hand is retained.'}
    j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4)
    file=out/'lulu-sketchfab-colour.glb';file.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
    (out/'build.json').write_text(json.dumps({'revision':revision,'triangles_by_chunk':counts,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'source_position_accessors_reused':True,'source_normal_accessors_reused':True,'source_node_transforms_preserved':g['nodes']==source_g['nodes'],'no_rig_yet':True,'geometry_moved':False,'status':'COLOUR_CANDIDATE_USER_REVIEW_PENDING'},indent=2))
    print(json.dumps({'file':str(file),'bytes':file.stat().st_size,'counts':counts},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--revision',default='color-r01');args=ap.parse_args();build(args.revision)
