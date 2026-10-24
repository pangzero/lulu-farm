from pathlib import Path
import json,struct,io,sys
import numpy as np
from PIL import Image,ImageFilter
r=Path(__file__).resolve().parents[1]
catalog=json.loads((r/'public/models/crops-meshy/manifest.json').read_text())
for slug in sys.argv[1:]:
 e=next(x for x in catalog['crops'] if x['id']==slug);raw=(r/'public'/e['file'].lstrip('/')).read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);binary=raw[28+n:]
 mat=d['materials'][0];ti=mat['pbrMetallicRoughness']['baseColorTexture']['index'];im=d['images'][d['textures'][ti]['source']];v=d['bufferViews'][im['bufferView']];off=v.get('byteOffset',0)
 original=Image.open(io.BytesIO(binary[off:off+v['byteLength']])).convert('RGB')
 # Preserve colour-boundaries; reduce only high-frequency luminance variation.
 a=np.asarray(original,dtype=np.float32)/255;b=np.asarray(original.filter(ImageFilter.GaussianBlur(2.2)),dtype=np.float32)/255
 green=(a[:,:,1]>a[:,:,0]*.94)&(a[:,:,1]>a[:,:,2]*1.35)
 blend={'cabbage':.35,'tomato':.14,'corn':.2}.get(slug,.2)
 out=a*(1-blend)+b*blend
 # Retain pale warm-green veins; gentle compression avoids a gray/black vein map.
 lum=out.max(axis=2);weight=np.clip((lum-.55)/.45,0,1)*green
 out*=1-weight[:,:,None]*.11
 folder=r/f'review/crop-two-stage-20261018/{slug}/mature/r02';folder.mkdir(parents=True,exist_ok=True)
 Image.fromarray(np.uint8(np.clip(out,0,1)*255)).save(folder/f'{slug}-cartoon-basecolor.png')
 (folder/'texture-recipe.json').write_text(json.dumps({'input':e['file'],'source_sha256':e['sha256'],'original_size':original.size,'blur_sigma':2.2,'detail_blend':blend,'green_highlight_compression':.11,'uv_unchanged':True},indent=2))
 print(slug,'prepared')
