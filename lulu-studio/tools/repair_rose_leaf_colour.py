from pathlib import Path
import json,shutil
import numpy as np
from PIL import Image,ImageFilter
r=Path('/Users/haowen/GameProject/farm-game/lulu-studio/review/crop-mature-remaining-20261018/rose');o=r/'toon-r03';o.mkdir(exist_ok=True)
a=np.asarray(Image.open(r/'toon-r01/basecolor.png'),dtype=np.float32)/255
rr,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
mask=(rr>g*.86)&(g>rr*.65)&(b<g*.78)&(rr>.25)&(rr<.84)
green=(g>rr*1.30)&(g>b*1.45)&(g>.22)
weights=np.asarray(Image.fromarray(np.uint8(green*255)).filter(ImageFilter.GaussianBlur(32)),dtype=np.float32)/255
weighted=np.asarray(Image.fromarray(np.uint8(a*green[:,:,None]*255)).filter(ImageFilter.GaussianBlur(32)),dtype=np.float32)/255
mask&=weights>.025
strength=np.asarray(Image.fromarray(np.uint8(mask*255)).filter(ImageFilter.GaussianBlur(1.3)),dtype=np.float32)/255
donor=weighted/np.maximum(weights[:,:,None],.001)
result=a*(1-strength[:,:,None])+donor*strength[:,:,None]
Image.fromarray(np.uint8(result.clip(0,1)*255)).save(o/'basecolor.png');shutil.copy2(r/'toon-r01/roughness.png',o/'roughness.png')
Image.fromarray(np.uint8(mask*255)).save(o/'repaired-leaf-pigment-mask.png')
(o/'repair.json').write_text(json.dumps({'issue':'Visible tan patch on mid-right rose leaf in original and r01','mask_pixels':int(mask.sum()),'fraction':float(mask.mean()),'method':'Warm brown/olive leaf pixels only; locally weighted green donor at 32-pixel radius. Pink petals excluded.','geometry_unchanged':True,'source_basecolor':'toon-r01/basecolor.png'},indent=2));print('rose repaired pixels',int(mask.sum()))
