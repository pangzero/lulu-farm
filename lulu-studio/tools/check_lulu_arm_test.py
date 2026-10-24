import bpy,json,struct,hashlib,math
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'public/models/lulu-arm-test.glb';data=p.read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n]);binary=data[28+n:]
report={'skins':len(g.get('skins',[])),'source_nodes':[x['name'] for x in g['nodes'] if x.get('name','').startswith('Source_')],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'finite_float_accessors':True}
for acc in g['accessors']:
 if acc['componentType']!=5126 or 'bufferView' not in acc:continue
 view=g['bufferViews'][acc['bufferView']];size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[acc['type']];start=view.get('byteOffset',0)+acc.get('byteOffset',0)
 arr=np.ndarray((acc['count'],size),dtype='<f4',buffer=binary,offset=start,strides=(view.get('byteStride',size*4),4))
 report['finite_float_accessors'] &= bool(np.isfinite(arr).all())
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/lulu-arm-test.blend'))
skin=bpy.data.objects['Lulu_ArmTestSkin'];rig=bpy.data.objects['Lulu_ArmInspectionRig']
report['bones']=[b.name for b in rig.data.bones]
bonegroups={group.index for group in skin.vertex_groups if group.name in report['bones']}
report['max_weight_sum_error']=max(abs(sum(g.weight for g in v.groups if g.group in bonegroups)-1) for v in skin.data.vertices)
report['static_source_sha256']=hashlib.sha256((R/'public/models/lulu-head-study.glb').read_bytes()).hexdigest()
report['user_accepted']=False
(R/'review/arm-motion-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
assert report['finite_float_accessors'] and report['skins']==1 and not report['source_nodes'] and report['max_weight_sum_error']<1e-5
