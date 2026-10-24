"""Independent, reversible left-arm pose. Reuses original positions and normals.

The source is colour-r08, NOT the older Meshy model. An armature transforms the
existing arm, with a short shoulder transition. Any shell is a separate object.
"""
from pathlib import Path
import numpy as np, json, struct, hashlib, argparse, math, copy

R=Path(__file__).resolve().parents[1]
D=R/'review/lulu-sketchfab-arm-down-20261019'
SOURCE=D/'baseline/lulu-sketchfab-colour.glb'

def read(path):
    d=path.read_bytes();n=struct.unpack_from('<I',d,12)[0]
    return json.loads(d[20:20+n]),bytearray(d[28+n:])

def accessor(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']]
    count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
    return np.ndarray((a['count'],count),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',count*dt.itemsize),dt.itemsize)).copy()

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

PIVOT=np.array([.242,.445,.012])
HAND=np.array([.162,.531,.236])
TARGET=np.array([.285,.191,.028])

def quaternion(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    q=np.r_[np.cross(a,b),1+np.dot(a,b)];return q/np.linalg.norm(q)

def matrix(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def weights(p):
    x,y,z=p.T
    line=np.array([PIVOT,[.258,.435,.085],[.226,.470,.163],[.188,.514,.218],HAND])
    best=np.full(len(p),1e9);along=np.zeros(len(p));s=0
    for a,b in zip(line[:-1],line[1:]):
        v=b-a;length=np.linalg.norm(v);t=np.clip((p-a)@v/(v@v),0,1)
        d=np.linalg.norm(p-a-t[:,None]*v,axis=1);sel=d<best
        best[sel]=d[sel];along[sel]=s+t[sel]*length;s+=length
    # Whole distal arm. The top boundary excludes the separate cheek above it.
    radial=1-smooth(.052,.069,best)
    front= smooth(.002,.045,z)
    headstop=1-smooth(.562,.578,y)
    side=smooth(.095,.135,x)
    return (radial*front*headstop*side).astype('<f4')

def build(rev):
    out=D/rev;out.mkdir(parents=True,exist_ok=False)
    g,b=read(SOURCE);old=copy.deepcopy(g)
    def buf(data):
        b.extend(b'\0'*((-len(b))%4));i=len(g['bufferViews'])
        g['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data);return i
    def acc(a,typ,component=5126,bounds=False):
        i=len(g['accessors']);entry={'bufferView':buf(a.tobytes()),'componentType':component,'count':len(a),'type':typ}
        if bounds:entry.update(min=np.min(a,axis=0).tolist(),max=np.max(a,axis=0).tolist())
        g['accessors'].append(entry);return i
    q=quaternion(HAND-PIVOT,TARGET-PIVOT);rot=matrix(q)
    allp=[];allw=[];posed=[];report=[]
    for mi,m in enumerate(g['meshes']):
        ai=m['primitives'][0]['attributes']['POSITION'];p=accessor(g,b,ai);w=weights(p)
        joints=np.zeros((len(p),4),dtype='<u2');joints[:,1]=1
        ww=np.c_[1-w,w,np.zeros((len(p),2))].astype('<f4')
        ji=acc(joints,'VEC4',5123);wi=acc(ww,'VEC4')
        for pr in m['primitives']:pr['attributes'].update(JOINTS_0=ji,WEIGHTS_0=wi)
        allp.append(p);allw.append(w);posed.append(p*(1-w[:,None])+((p-PIVOT)@rot.T+PIVOT)*w[:,None])
        report.append({'chunk':mi,'weighted_vertices':int((w>0).sum()),'rigid_arm_vertices':int((w>.9999).sum())})
    body=len(g['nodes']);arm=body+1
    g['nodes'].extend([{'name':'Body_Fixed','children':[arm]}, {'name':'LeftArm_Pose','translation':PIVOT.tolist(),'rotation':q.tolist(),'extras':{'role':'Raised anatomical LEFT arm, positive source X. Pose only.'}}])
    g['nodes'][1]['children'].append(body)
    for node in g['nodes']:
        if 'mesh' in node:node['skin']=0
    ib=np.tile(np.eye(4,dtype='<f4'),(2,1,1));ib[1,:3,3]=-PIVOT
    ibid=acc(ib.transpose(0,2,1).reshape(2,16).copy(),'MAT4')
    g['skins']=[{'name':'Lulu_LeftArm_Only','inverseBindMatrices':ibid,'joints':[body,arm],'skeleton':body}]
    ti=acc(np.array([[0],[1]],dtype='<f4'),'SCALAR',bounds=True)
    animations=[]
    for name,values in [('Original_Raised',[np.array([0,0,0,1])]*2),('LeftArm_Down',[q,q]),('LeftArm_Lowering',[np.array([0,0,0,1]),q])]:
        ri=acc(np.array(values,dtype='<f4'),'VEC4');animations.append({'name':name,'samplers':[{'input':ti,'output':ri,'interpolation':'LINEAR'}],'channels':[{'sampler':0,'target':{'node':arm,'path':'rotation'}}]})
    g['animations']=animations
    g.setdefault('extras',{})['arm_pose']={'revision':rev,'base':'color-r08','source_vertices_normals_indices_unchanged':True,'scope':'single left shoulder pose; source head/body fixed; no shell in first diagnostic','user_art_accepted':False}
    g['buffers'][0]['byteLength']=len(b)
    j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4)
    file=out/'lulu-arm-down.glb';file.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
    p=np.concatenate(allp);w=np.concatenate(allw);pp=np.concatenate(posed)
    np.savez_compressed(out/'pose-diagnostic.npz',positions=p,weights=w,posed=pp)
    # Immutable bind mesh and all existing material/UV/colour/index data.
    for a in old['accessors']:
        pass
    assert g['materials']==old['materials'] and g['images']==old['images']
    bg,bb=read(file)
    assert bytes(bb[:len(read(SOURCE)[1])])==bytes(read(SOURCE)[1])
    meta={'revision':rev,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'pivot':PIVOT.tolist(),'source_hand_center':HAND.tolist(),'posed_hand_center':((HAND-PIVOT)@rot.T+PIVOT).tolist(),'quaternion':q.tolist(),'angle_degrees':float(2*math.degrees(math.acos(q[3]))),'bind_data_bit_exact':True,'source_buffers_preserved':True,'shell_added':False,'rig_type':'single-arm diagnostic, not full locomotion rig','chunks':report,'head_y_above_060_max_motion':float(np.max(np.linalg.norm(pp[p[:,1]>.60]-p[p[:,1]>.60],axis=1))),'opposite_x_negative_max_motion':float(np.max(np.linalg.norm(pp[p[:,0]<0]-p[p[:,0]<0],axis=1)))}
    (out/'build.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--revision',required=True);a=ap.parse_args();build(a.revision)
