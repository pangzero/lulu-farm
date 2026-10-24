from pathlib import Path
import json,struct,io
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[1];O=R/'review/seedling-meshy-mapping-20261018'
for c in json.loads((O/'mapping.json').read_text()):
 p=R/'public'/c['input']['file'].lstrip('/');data=p.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=data[28+n:];mat=doc['materials'][0];idx=doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source'];bv=doc['bufferViews'][doc['images'][idx]['bufferView']];off=bv.get('byteOffset',0);im=Image.open(io.BytesIO(binary[off:off+bv['byteLength']])).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
 a=np.asarray(im).astype(np.float32)/255;blur=np.asarray(im.filter(ImageFilter.GaussianBlur(2.5))).astype(np.float32)/255
 # Retain painted leaf/petiole gradients; compress high-frequency bright veins.
 hi=np.maximum(0,a-blur);out=a-hi*.42;out=out*.88+blur*.12
 lum=out.mean(axis=2,keepdims=True);out=lum+(out-lum)*.94;out*=np.array(c['tint'])
 if c['family']=='broad':
  pale=np.clip((out[:,:,1]-.6)*3,0,1)*np.clip((.86-out[:,:,2])*3,0,1);out[:,:,0]-=pale*.035;out[:,:,2]+=pale*.012
 folder=O/c['id']/'meshy-toon-r01';folder.mkdir(parents=True,exist_ok=True);Image.fromarray(np.uint8(np.clip(out,0,1)*255)).save(folder/'basecolor.png')
 (folder/'texture-recipe.json').write_text(json.dumps({'original_sha256':c['input']['sha256'],'basecolor':'sRGB decoded directly from original GLB','high_frequency_bright_detail_compression':.42,'blur_mix':.12,'chroma_retention':.94,'tint':c['tint'],'normal_strength':.14,'roughness':.84,'texture_size':[1024,1024]},indent=2))
print('Prepared14selective textures')
