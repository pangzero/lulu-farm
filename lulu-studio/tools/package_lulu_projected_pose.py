from pose_lulu_sketchfab_arm import read,accessor,D
from color_lulu_sketchfab import colour,srgb_to_linear,SKIN
import numpy as np,json,struct,hashlib,copy
src=D/'pose-r09';out=D/'pose-r10';out.mkdir(exist_ok=False);g,b=read(src/'lulu-arm-down.glb');a=np.load(src/'projected-guards.npz')
def replace(i,data):
 ac=g['accessors'][i];bv=g['bufferViews'][ac['bufferView']];pos=bv.get('byteOffset',0)+ac.get('byteOffset',0);raw=data.tobytes();b[pos:pos+len(raw)]=raw
 if ac['type']=='VEC3' and 'min' in ac:ac['min']=data.min(0).tolist();ac['max']=data.max(0).tolist()
for mi,m in enumerate(g['meshes']):
 if str(mi)+'_p' not in a:continue
 pr=m['primitives'][0];p=a[str(mi)+'_p'];n=a[str(mi)+'_n'];assert np.isfinite(p).all() and np.isfinite(n).all();print(m['name'],p.min(0),p.max(0));replace(pr['attributes']['POSITION'],p);replace(pr['attributes']['NORMAL'],n)
 part=int(m['name'].split('_')[1]);c=colour(p,head_only=True) if part==0 and p[:,1].mean()>.4 else colour(p)
 if part>0:c[:]=SKIN
 replace(pr['attributes']['COLOR_0'],srgb_to_linear(c).astype('<f4'))
g['extras']['arm_pose']['revision']='pose-r10';g['buffers'][0]['byteLength']=len(b);j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4);file=out/'lulu-arm-down.glb';file.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
meta=json.loads((src/'build.json').read_text());meta.update(revision='pose-r10',output_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),guard_method='added shells projected to intact opposite body surface; no original source vertex edited');(out/'build.json').write_text(json.dumps(meta,indent=2))
