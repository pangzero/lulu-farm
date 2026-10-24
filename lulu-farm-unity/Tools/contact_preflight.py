#!/usr/bin/env python3
"""Read actual GLB geometry for initial contact measurements. Unity checks remain required."""
import json
import pathlib
import struct
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]


def triangles_from_glb(path):
    raw=path.read_bytes();cursor=12;chunks={}
    while cursor<len(raw):
        length,kind=struct.unpack_from('<II',raw,cursor);cursor+=8
        chunks[kind]=raw[cursor:cursor+length];cursor+=length
    doc=json.loads(chunks[0x4E4F534A]);blob=chunks[0x004E4942]
    def accessor(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        return np.ndarray((a['count'],width),dtype,blob,v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dtype.itemsize*width),dtype.itemsize))
    collected=[]
    def visit(index,parent):
        n=doc['nodes'][index]
        if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
        else:
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]))
            m[:3,3]=n.get('translation',[0,0,0])
        world=parent@m
        if 'mesh' in n:
            for primitive in doc['meshes'][n['mesh']]['primitives']:
                assert primitive.get('mode',4)==4
                vertices=accessor(primitive['attributes']['POSITION'])
                vertices=vertices@world[:3,:3].T+world[:3,3]
                indices=accessor(primitive['indices']).reshape(-1,3) if 'indices' in primitive else np.arange(len(vertices)).reshape(-1,3)
                collected.append(vertices[indices])
        for child in n.get('children',[]):visit(child,world)
    for index in doc['scenes'][doc.get('scene',0)]['nodes']:visit(index,np.eye(4))
    # glTFast uses the Unity X-reflection handedness conversion.
    return np.concatenate(collected)*[-1,1,1]


def downward_surface(triangles,x,z):
    a,b,c=triangles[:,0],triangles[:,1],triangles[:,2]
    e1=b-a;e2=c-a;dx=x-a[:,0];dz=z-a[:,2]
    denominator=e1[:,0]*e2[:,2]-e2[:,0]*e1[:,2]
    valid=np.abs(denominator)>1e-12
    u=np.zeros(len(a));v=np.zeros(len(a))
    u[valid]=(dx[valid]*e2[valid,2]-e2[valid,0]*dz[valid])/denominator[valid]
    v[valid]=(e1[valid,0]*dz[valid]-dx[valid]*e1[valid,2])/denominator[valid]
    valid &= (u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)
    return float(np.max(a[valid,1]+u[valid]*e1[valid,1]+v[valid]*e2[valid,1])) if np.any(valid) else None


if __name__=='__main__':
    manifest=json.loads((ROOT.parent/'lulu-studio/public/models/unity-integration/manifest.json').read_text())
    record=next(a for a in manifest['assets'] if a['id']=='S07')
    triangles=triangles_from_glb(pathlib.Path(record['file']))
    lo=triangles.min((0,1));hi=triangles.max((0,1));scale=.7/(hi[1]-lo[1])
    normalized=(triangles-[(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*scale
    yaw=np.array([[0,0,1],[0,1,0],[-1,0,0]])
    placed=normalized@yaw.T+[8.6,-.42,-2.7+1.2/(np.pi/2)+2.4]
    z=-2.7+1.2/(np.pi/2)+2.4
    corrected=(triangles-[(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*1.15/(hi[1]-lo[1])+[8.5,-.5915,z]
    report={'scope':'GLB geometry preflight, not Unity import or gameplay acceptance','asset':record['file'],'source_bounds_unity_axes':[lo.tolist(),hi.tolist()],
            'initial_adapter_scale':float(scale),'placed_bounds':[placed.min((0,1)).tolist(),placed.max((0,1)).tolist()],
            'initial_deck_centerline':[{'x':x,'z':z,'surface_y':downward_surface(placed,x,z)} for x in np.arange(7.2,10.01,.2)],
            'corrected_placement':{'height':1.15,'position':[8.5,-.5915,z],'yaw':0,'bounds':[corrected.min((0,1)).tolist(),corrected.max((0,1)).tolist()]},
            'corrected_deck_probes':[{'x':x,'z':z+offset,'surface_y':downward_surface(corrected,x,z+offset),'collision_y':.075} for x in [7.3,7.5,8.1,8.6,9.2,9.65] for offset in [-.6,0,.6]]}
    output=ROOT/'Preflight/dock-contact-measurements.json';output.parent.mkdir(exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
