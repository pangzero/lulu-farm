from pathlib import Path
import bpy,json,hashlib,struct,numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-hybrid-assembly-20261023'
def load(f):
 b=f.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def acc(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4};types={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'};dt=np.dtype(types[a['componentType']]);k=dims[a['type']];return np.ndarray((a['count'],k),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*k),dt.itemsize)).copy()
def fingerprints(g,b):
 res={}
 for n in g['nodes']:
  if 'mesh' not in n:continue
  pr=[]
  for p in g['meshes'][n['mesh']]['primitives']:
   v={k:hashlib.sha256(acc(g,b,i).tobytes()).hexdigest() for k,i in p['attributes'].items()};v['indices']=hashlib.sha256(acc(g,b,p['indices']).tobytes()).hexdigest();pr.append(v)
  res[n['name']]=pr
 return res
old=load(D/'baseline/public/models/modular/right-junction-r04/lulu-assembled.glb');new=load(D/'baseline/public/models/lulu-sketchfab/head-approved-v1/lulu-head.glb');expected={**fingerprints(*old),**fingerprints(*new)}
for rev in ['hybrid-r01','hybrid-r02']:
 O=D/rev;g,b=load(O/'lulu-hybrid.glb');actual=fingerprints(g,b)
 assert len(actual)==8 and not g.get('skins') and not g.get('animations')
 checks={n:actual[n]==expected[n] for n in actual};assert all(checks.values())
 hn={n['name']:n for n in new[0]['nodes']}
 transforms={n['name']:all(n.get(k)==hn[n['name']].get(k) for k in ['matrix','rotation','scale','translation']) for n in g['nodes'] if n['name'] in hn};assert all(transforms.values())
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'lulu-hybrid.glb'))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==8
 for ob in meshes:ob['provenance']='head-approved-v1' if ob.name in hn else 'right-junction-r04';ob['edits']='No sculpt or topology changes; only original lower assembly has uniform parent transform.'
 bpy.context.scene['stage']='Static hybrid trial; eight source components; no bone or mesh sculpt. Neck seam pending visual approval.'
 for area in bpy.context.screen.areas if bpy.context.screen else []:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='SOLID';area.spaces.active.region_3d.view_distance=1.8;area.spaces.active.region_3d.view_location=Vector((0,0,.53))
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(O/'lulu-hybrid.blend'));bpy.ops.wm.open_mainfile(filepath=str(O/'lulu-hybrid.blend'))
 assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==8;assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
 report={'revision':rev,'all_component_position_normal_uv_index_bytes_identical':checks,'accepted_head_node_transforms_identical':transforms,'glb_import_and_blend_reopen':True,'mesh_objects':8,'armatures':0,'head_material_note':'Accepted gray head. Original old body materials retained; preview uses neutral gray for honest shape comparison.','status':'Technical preservation verified; neck interface is a static overlap, not a continuous skin or art approval.'}
 (O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
for e in json.loads((D/'backup.json').read_text()):assert hashlib.sha256((R/e['source']).read_bytes()).hexdigest()==e['sha256']==hashlib.sha256((R/e['backup']).read_bytes()).hexdigest()
(D/'preservation.json').write_text(json.dumps({'source_and_backup_files_checked':13,'all_sha256_identical':True,'mesh_edits':0,'accepted_head_transform_edits':0},indent=2))
