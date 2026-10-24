from pathlib import Path
import json
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

folder=Path(__file__).resolve().parents[1]/'review/lulu-under-eye-20261018/r04'
data=json.loads((folder/'cdt-input.json').read_text())
v,e,f,ov,oe,of=delaunay_2d_cdt([Vector(v) for v in data['vertices']],data['edges'],[],0,1e-8,True)
(folder/'cdt-output.json').write_text(json.dumps({'vertices':[list(v) for v in v],'edges':e,'faces':f,'orig_verts':ov}))
print('CDT',len(v),'vertices',len(f),'triangles')
