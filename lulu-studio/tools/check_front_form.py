"""Ensure cheek/eye refinement stays inside its authorized geometric scope."""
import bpy,json,struct,hashlib
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'public/models/lulu-complete.glb';d=p.read_bytes();n=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+n]);binary=d[28+n:]
r={'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest(),'finite_float_accessors':True,'skins':len(g.get('skins',[])),'source_nodes':[v['name'] for v in g['nodes'] if v.get('name','').startswith('Source_')]}
for a in g['accessors']:
 if a['componentType']!=5126 or 'bufferView' not in a:continue
 v=g['bufferViews'][a['bufferView']];size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 ar=np.ndarray((a['count'],size),dtype='<f4',buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*4),4));r['finite_float_accessors'] &= bool(np.isfinite(ar).all())
bpy.ops.wm.open_mainfile(filepath=str(R/'review/front-form-baseline/lulu-complete.blend'))
base={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/lulu-complete.blend'))
r['preserved_objects']={}
for name,a in base.items():
 b=np.array([v.co[:] for v in bpy.data.objects[name].data.vertices])
 if name=='Lulu_Smile':continue
 if name!='Lulu_ArmTestSkin':r['preserved_objects'][name]=bool(np.array_equal(a,b));continue
 diff=b-a;head=a[:,2]>1.03
 r['all_z_coordinates_preserved']=bool(np.array_equal(a[:,2],b[:,2]))
 r['torso_arms_palms_preserved']=bool(np.array_equal(a[~head],b[~head]))
 changed_x=abs(diff[:,0])>1e-7;allowed_x=(a[:,2]>1.03)&(a[:,2]<1.70)
 q=((abs(b[:,0])-.287)/.16)**2+((b[:,2]-(1.747+np.sign(b[:,0])*.005))/.14)**2
 allowed_y=(q<5.6)&(a[:,1]<-.15)&(a[:,2]>1.42)&(a[:,2]<2.07)
 changed_y=abs(diff[:,1])>1e-7
 r['x_changes_in_cheek_band_only']=bool(np.array_equal(a[:,0],b[:,0]))
 r['y_changes_in_eyes_only']=bool(np.all(~changed_y|allowed_y))
 r['head_width_before']=float(np.ptp(a[head,0]));r['head_width_after']=float(np.ptp(b[head,0]))
 r['max_head_width_change_percent']=(r['head_width_after']/r['head_width_before']-1)*100
 r['foremost_muzzle_before']=float(a[head,1].min());r['foremost_muzzle_after']=float(b[head,1].min())
 r['foremost_muzzle_preserved']=abs(r['foremost_muzzle_before']-r['foremost_muzzle_after'])<1e-7
 r['maximum_cheek_displacement']=float(abs(diff[:,0]).max())
skin=bpy.data.objects['Lulu_ArmTestSkin'];r['basis_equals_skin']=max((v.co-k.co).length for v,k in zip(skin.data.vertices,skin.data.shape_keys.key_blocks['Basis'].data))<1e-6
r['passed']=all([r['finite_float_accessors'],r['skins']==1,not r['source_nodes'],all(r['preserved_objects'].values()),r['all_z_coordinates_preserved'],r['torso_arms_palms_preserved'],r['x_changes_in_cheek_band_only'],r['y_changes_in_eyes_only'],r['foremost_muzzle_preserved'],r['basis_equals_skin'],abs(r['max_head_width_change_percent'])<1])
(R/'review/front-form-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert r['passed']
