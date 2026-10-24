"""Verify reversible edit scope against the user's supplied Meshy GLB."""
from pathlib import Path
import numpy as np,json,struct,io,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1]
source=R/'assets-source/meshy-original/Meshy_AI_Sunny_Sprout_1014132159_texture.glb'
output=R/'public/models/lulu-meshy-eyes.glb'
def read(p):
 d=p.read_bytes();n=struct.unpack_from('<I',d,12)[0];return json.loads(d[20:20+n]),d[28+n:]
def arr(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];sz={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];return np.ndarray((a['count'],sz),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*sz),np.dtype(dt).itemsize))
def image_bytes(g,b,i):
 v=g['bufferViews'][g['images'][i]['bufferView']];return b[v['byteOffset']:v['byteOffset']+v['byteLength']]
g0,b0=read(source);g,b=read(output);pr0=g0['meshes'][0]['primitives'][0];pr=g['meshes'][0]['primitives'][0]
p0=arr(g0,b0,pr0['attributes']['POSITION']);p=arr(g,b,pr['attributes']['POSITION']);diff=p-p0
q=np.sqrt(((abs(p0[:,0])-.232)/.09)**2+((p0[:,1]-.525)/.08)**2)
scope=(q<2.01)&(p0[:,2]>.099)
changed=np.any(diff!=0,axis=1)
uv=bool(np.array_equal(arr(g0,b0,pr0['attributes']['TEXCOORD_0']),arr(g,b,pr['attributes']['TEXCOORD_0'])))
topo=bool(np.array_equal(arr(g0,b0,pr0['indices']),arr(g,b,pr['indices'])))
n0=arr(g0,b0,pr0['attributes']['NORMAL']);n=arr(g,b,pr['attributes']['NORMAL'])
im0=np.array(Image.open(io.BytesIO(image_bytes(g0,b0,1))));im=np.array(Image.open(io.BytesIO(image_bytes(g,b,1))))
r={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'geometry_finite':bool(np.isfinite(p).all()),'normals_finite':bool(np.isfinite(n).all()),'all_X_Y_coordinates_preserved':bool(np.array_equal(p0[:,:2],p[:,:2])),'all_changes_inside_eye_surroundings':bool(np.all(~changed|scope)),'changed_vertices':int(changed.sum()),'max_depth_shift':float(abs(diff[:,2]).max()),'overall_bounds_preserved':bool(np.array_equal(p0.min(0),p.min(0)) and np.array_equal(p0.max(0),p.max(0))),'body_and_back_preserved':bool(np.array_equal(p0[~scope],p[~scope])),'normal_changes_inside_eye_surroundings_only':bool(np.array_equal(n0[~scope],n[~scope])),'UV_preserved':uv,'topology_preserved':topo,'base_color_image_byte_identical':image_bytes(g0,b0,0)==image_bytes(g,b,0),'normal_map_image_byte_identical':image_bytes(g0,b0,2)==image_bytes(g,b,2),'roughness_R_and_B_preserved':bool(np.array_equal(im0[:,:,[0,2]],im[:,:,[0,2]])),'nodes_and_transforms_preserved':g0['nodes']==g['nodes']}
flags=[v for v in r.values() if isinstance(v,bool)];r['passed']=all(flags)
(R/'review/meshy-eye-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert r['passed']
