"""Verify the expression paint edit did not modify mesh or deformation shapes."""
import bpy, hashlib, json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path))
 result={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  h=hashlib.sha256(np.array([v.co[:] for v in o.data.vertices],dtype=np.float32).tobytes())
  if o.data.shape_keys:
   for k in o.data.shape_keys.key_blocks:
    h.update(k.name.encode());h.update(np.array([v.co[:] for v in k.data],dtype=np.float32).tobytes())
  result[o.name]=h.hexdigest()
 return result
before=snapshot(R/'review/eye-expression-baseline/lulu-complete.blend')
after=snapshot(R/'assets-source/lulu-complete.blend')
r={'all_meshes_and_shape_keys_unchanged':before==after,'mesh_count':len(after),'glb_sha256':hashlib.sha256((R/'public/models/lulu-complete.glb').read_bytes()).hexdigest()}
(R/'review/eye-expression-validation.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2));assert before==after
