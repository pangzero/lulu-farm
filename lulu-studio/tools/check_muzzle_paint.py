"""Compare rendered paint data to the pre-muzzle-edit atlas, preserving eyes/lower half."""
from pathlib import Path
from PIL import Image
import numpy as np, json, hashlib
r=Path(__file__).resolve().parents[1]
a=np.array(Image.open(r/'review/muzzle-paint-baseline/lulu-complete-paint.png'))[::-1]
b=np.array(Image.open(r/'assets-source/lulu-complete-paint.png'))[::-1]
n=a.shape[0];x=np.linspace(-.82,.82,n)[None,:];z=np.linspace(.25,2.12,n)[:,None]
diff=np.any(a!=b,axis=2);eyes=np.zeros((n,n),bool)
for side in [-1,1]:
 cx=side*.287-side*.014;cz=1.747+side*.005+.003;t=.22 if side==-1 else -.25;rx=.111 if side==-1 else .110;rz=.089 if side==-1 else .088
 q=((x-cx-(z-cz)*t)/rx)**2+((z-cz)/rz)**2;eyes|=q<.98
v={'lower_muzzle_and_body_paint_preserved':bool(not diff[z[:,0]<=1.35].any()),'back_paint_preserved':bool(not diff[:,n:].any()),'eye_interiors_preserved':bool(not diff[:,:n][eyes].any()),'changed_pixels':int(diff.sum()),'glb_sha256':hashlib.sha256((r/'public/models/lulu-complete.glb').read_bytes()).hexdigest()}
(r/'review/muzzle-paint-color-validation.json').write_text(json.dumps(v,indent=2));print(v)
assert v['lower_muzzle_and_body_paint_preserved'] and v['back_paint_preserved'] and v['eye_interiors_preserved']
