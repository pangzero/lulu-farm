"""Historical v0.20 eye-only scope check. Current v0.21 uses check_cheek_eye.py."""
import bpy,json,struct,hashlib
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'public/models/lulu-complete.glb';data=p.read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n]);binary=data[28+n:]
report={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'finite_float_accessors':True,'skins':len(g.get('skins',[])),'embedded_images':len(g.get('images',[])),'source_nodes':[x['name'] for x in g['nodes'] if x.get('name','').startswith('Source_')]}
for acc in g['accessors']:
 if acc['componentType']!=5126 or 'bufferView' not in acc:continue
 v=g['bufferViews'][acc['bufferView']];size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[acc['type']]
 arr=np.ndarray((acc['count'],size),dtype='<f4',buffer=binary,offset=v.get('byteOffset',0)+acc.get('byteOffset',0),strides=(v.get('byteStride',size*4),4))
 report['finite_float_accessors'] &= bool(np.isfinite(arr).all())
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/lulu-arm-test.blend'))
base={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/lulu-complete.blend'))
report['preserved_objects']={}
for name,coords in base.items():
 now=np.array([v.co[:] for v in bpy.data.objects[name].data.vertices]);delta=now-coords
 if name!='Lulu_ArmTestSkin':report['preserved_objects'][name]=bool(np.array_equal(now,coords));continue
 report['skin_xz_preserved']=bool(np.array_equal(now[:,[0,2]],coords[:,[0,2]]))
 changed=np.max(np.abs(delta),axis=1)>1e-7
 report['changed_skin_vertices']=int(changed.sum())
 q=((np.abs(coords[:,0])-.287)/.14)**2+((coords[:,2]-(1.747+np.sign(coords[:,0])*.005))/.12)**2
 allowed=(q<3)&(coords[:,1]<-.15)&(coords[:,2]>1.55)&(coords[:,2]<1.96)
 report['all_changes_within_eye_footprints']=bool(np.all(~changed|allowed))
 report['eye_y_delta_range']=[float(delta[:,1].min()),float(delta[:,1].max())]
 report['torso_arms_palms_preserved']=bool(np.array_equal(now[coords[:,2]<1.55],coords[coords[:,2]<1.55]))
body=bpy.data.objects['Lulu_ArmTestSkin'];rig=bpy.data.objects['Lulu_ArmInspectionRig']
report['bones']=[b.name for b in rig.data.bones]
report['no_eye_shells']=not any(o.name.startswith('Lulu_EyeSurface') for o in bpy.data.objects)
report['mouth_mesh']=bpy.data.objects['Lulu_Smile'].type=='MESH'
report['basis_equals_skin']=max((v.co-k.co).length for v,k in zip(body.data.vertices,body.data.shape_keys.key_blocks['Basis'].data))<1e-6
report['passed']=all([report['finite_float_accessors'],report['skins']==1,not report['source_nodes'],report['embedded_images']==1,all(report['preserved_objects'].values()),report['skin_xz_preserved'],report['all_changes_within_eye_footprints'],report['torso_arms_palms_preserved'],report['no_eye_shells'],report['mouth_mesh'],report['basis_equals_skin']])
(R/'review/complete-asset-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert report['passed']
