"""Per-species, UV-preserving texture derivatives; never edits original images."""
from pathlib import Path
import json,struct,io
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018'
# high-frequency retention, vein compression, normal strength, leaf/organ roughness,
# simplification ratio chosen for the observed structure, not a global ratio.
P={
'cucumber':(.68,.10,.24,.81,.61,.18,'Keep fruit speckles and curved tendril; calm heart-leaf veins.'),
'pumpkin':(.70,.13,.19,.83,.62,.15,'Preserve broad gourd lobes and orange gradients; calm foliage.'),
'sunflower':(.72,.12,.22,.82,.74,.21,'Preserve thick yellow petals, brown disk relief and green calyx.'),
'wheat':(.78,.05,.30,.81,.72,.25,'Keep separate grain rows and narrow blades; shorten no stems or ears.'),
'bokchoy':(.50,.27,.12,.84,.78,.17,'Reduce bright green veins; protect cream fleshy petioles and front/back leaves.'),
'rose':(.76,.09,.17,.84,.74,.24,'Protect pink curl gradients, petal gaps, bud sepals and serrated leaves.'),
'strawberry':(.78,.13,.23,.83,.59,.14,'Protect red fruit, small embedded gold seeds and white flower; simplify leaf noise.'),
'cauliflower':(.46,.20,.10,.84,.87,.19,'Soften curd texture micro-noise, preserve white lobe clusters and wrapper gaps.'),
'watermelon':(.79,.08,.21,.82,.64,.17,'Protect large fruit stripes and lobed leaves; avoid blurring colour boundaries.'),
'tulip':(.80,.08,.14,.82,.67,.19,'Keep orange cup overlap gradients and long smooth blade separation.'),
'lettuce':(.44,.25,.12,.85,.85,.16,'Reduce chalky veins and tiny ridges while retaining curled leaf edges and centre.'),
}
entries=json.loads((O/'scope.json').read_text());recipes={}
for e in entries:
 slug=e['id'];retain,vein,normal,leaf,organ,ratio,note=P[slug];out=O/slug/'toon-r01';out.mkdir(parents=True,exist_ok=True)
 raw=(R/'public'/e['file'].lstrip('/')).read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);bin=raw[n+28:]
 ti=d['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'];im=d['images'][d['textures'][ti]['source']];v=d['bufferViews'][im['bufferView']];start=v.get('byteOffset',0)
 src=Image.open(io.BytesIO(bin[start:start+v['byteLength']])).convert('RGB');src.save(out/'input-basecolor.png')
 a=np.asarray(src,dtype=np.float32)/255;b=np.asarray(src.filter(ImageFilter.GaussianBlur(3.0)),dtype=np.float32)/255
 c=np.asarray(src.filter(ImageFilter.GaussianBlur(9)),dtype=np.float32)/255
 rr,g,bb=a[:,:,0],a[:,:,1],a[:,:,2]
 green=np.clip((g-rr*.91)*12,0,1)*np.clip((g-bb*1.23)*9,0,1)
 red=np.clip((rr-g*1.18)*9,0,1)*np.clip((rr-bb*1.15)*9,0,1)
 pink=np.clip((rr-g*1.2)*8,0,1)*np.clip((bb-g*.7)*7,0,1)
 gold=np.clip((rr-bb*1.6)*6,0,1)*np.clip((g-bb*1.3)*5,0,1)*(1-green)
 white=np.clip((a.min(axis=2)-.58)*5,0,1)*(1-green)
 # Leaf-only detail calming, with colour boundaries retained by a soft chroma mask.
 w=(1-retain)*green
 if slug=='cauliflower':w=np.maximum(w,white*.67)
 dest=a*(1-w[:,:,None])+b*w[:,:,None]
 hi=np.maximum(0,a.max(axis=2)-c.max(axis=2))
 dest*=1-(hi*vein*2.0*green)[:,:,None]
 # Compress only very bright leaf veins; do not tint cream petioles or flower heads.
 dest*=1-(np.clip((a.max(axis=2)-.63)/.37,0,1)*green*vein*.33)[:,:,None]
 if slug in ['cucumber','pumpkin','rose','strawberry','tulip']:mask=red if slug!='rose' else pink
 elif slug in ['sunflower','wheat']:mask=gold
 elif slug=='cauliflower':mask=white
 elif slug=='bokchoy':mask=white
 elif slug=='watermelon':mask=np.zeros_like(green)+.55 # retain matte striped skin, leaves a little less matte than siblings
 else:mask=np.zeros_like(green)
 rough=leaf+(organ-leaf)*mask
 Image.fromarray(np.uint8(np.clip(dest,0,1)*255)).save(out/'basecolor.png')
 Image.fromarray(np.uint8(np.clip(rough,0,1)*255)).save(out/'roughness.png')
 recipe={'id':slug,'batch':e['batch'],'source':e['file'],'source_sha256':e['sha256'],'input_size':list(src.size),'uv_unchanged':True,'geometry_policy':'Preserve mature Meshy main geometry; editable optimization is separate.','leaf_detail_retention':retain,'leaf_vein_compression':vein,'normal_strength':normal,'leaf_roughness':leaf,'organ_roughness':organ,'optimization_ratio':ratio,'texture_max_optimized':2048,'individual_treatment':note,'luminance_detail_blur_pixels':[3,9],'seeds_stripes_petals_protected':True}
 (out/'texture-recipe.json').write_text(json.dumps(recipe,indent=2));recipes[slug]=recipe;print('PREPARED',slug,flush=True)
(O/'profiles.json').write_text(json.dumps(recipes,indent=2))
