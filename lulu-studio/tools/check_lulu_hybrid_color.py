"""Read back geometry and save native copy; colors never authorize sculpt edits."""
from pathlib import Path
import bpy,hashlib,json,struct,sys
import numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-hybrid-color-20261023'
rev=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'color-r02';O=D/rev
def load(p):
    b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def acc(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    return np.ndarray((a['count'],k),dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*k),dt.itemsize)).copy()
def sortedrows(a):
    return a[np.lexsort(a.T[::-1])]
g0,b0=load(D/'baseline/lulu-neck.glb');g,b=load(O/'lulu-colored.glb');assert g['nodes']==g0['nodes'];assert not g.get('skins') and not g.get('animations')
checks={}
for ni,n in enumerate(g['nodes']):
    if 'mesh' not in n:continue
    old=g0['meshes'][n['mesh']]['primitives'];new=g['meshes'][n['mesh']]['primitives']
    # Position/normal accessor IDs are reused, including the split face group.
    for p in new:
        for key in ['POSITION','NORMAL']:
            i=p['attributes'][key];assert np.array_equal(acc(g0,b0,i),acc(g,b,i))
    # Preserve actual oriented triangle connectivity, allowing material splits.
    for a in old:
        key=a['attributes']['POSITION'];parts=[p for p in new if p['attributes']['POSITION']==key]
        assert parts
        before=acc(g0,b0,a['indices']).reshape(-1,3);after=np.concatenate([acc(g,b,p['indices']).reshape(-1,3) for p in parts])
        assert np.array_equal(sortedrows(before),sortedrows(after))
    checks[n['name']]={'position_normal_bytes_identical':True,'oriented_triangle_multiset_identical':True}
backups=[]
for e in json.loads((D/'backup.json').read_text()):
    assert hashlib.sha256((R/e['source']).read_bytes()).hexdigest()==e['sha256']==hashlib.sha256((R/e['backup']).read_bytes()).hexdigest();backups.append(e['source'])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'lulu-colored.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==9
for o in meshes:o['edit_scope']='Reference colors/materials/face UV only; geometry preserved from neck-r02'
for v in ['front','side','back']:
    im=bpy.data.images.load(str(D/'reference'/f'full-{v}.png'));im.name=f'Lulu_original_reference_{v}';im.pack()
bpy.context.scene['source']='neck-r02 gray preserved; head Spencer0131 Sketchfab / old Meshy modular r04 body'
bpy.context.scene['status']='Reference color candidate; user appearance approval pending. No rig.'
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        sp=area.spaces.active;sp.shading.type='MATERIAL';sp.region_3d.view_distance=1.7;sp.region_3d.view_location=Vector((0,0,.53))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(O/'lulu-colored.blend'));bpy.ops.wm.open_mainfile(filepath=str(O/'lulu-colored.blend'))
assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==9;assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
report={'revision':rev,'geometry_checks':checks,'all_nodes_identical':True,'source_and_backup_sha256_unchanged':backups,'glb_import_blend_save_reopen':True,'meshes':9,'armatures':0,'reference_images_packed':3,'status':'Technical preservation passed; appearance separate user review'}
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
