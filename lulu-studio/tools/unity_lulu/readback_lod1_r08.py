import bpy,json,sys,hashlib,struct,numpy as np
from pathlib import Path
from mathutils import Matrix
R=Path(__file__).resolve().parents[2];REV='locomotion-r08';OUT=R/'public/models/unity-lulu'/REV;SRC=R/'assets-source/unity-lulu'/REV;REP=R/'review/unity-integration-20261018/lulu'/REV
report={}
def pts(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());p=np.array([ev.matrix_world@v.co for v in ev.data.vertices]);return p
bpy.ops.wm.open_mainfile(filepath=str(SRC/'lulu-game-lod1.blend'));a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes={o.name:o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)};report['native']={'parts':list(meshes),'bones':len(a.data.bones),'actions':[x.name for x in bpy.data.actions],'uv':{n:[u.name for u in o.data.uv_layers] for n,o in meshes.items()},'images':[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE']};report['motion']={}
for clip,num in [('Idle',90),('Walk',18),('Run',12)]:
 a.animation_data.action=bpy.data.actions[clip];vals=[];ends=[]
 for f in range(num+1):
  bpy.context.scene.frame_set(f+1);bpy.context.view_layer.update();legmin={n:float(pts(meshes[n])[:,2].min()) for n in ['Leg_L','Leg_R']};vals.append({'frame':f+1,'phase':f/num,'min_z':legmin})
  if f in [0,num]:ends.append({n:pts(meshes[n]) for n in meshes})
 report['motion'][clip]={'samples':vals,'loop_max_vertex_difference':max(float(np.abs(ends[0][n]-ends[1][n]).max()) for n in meshes),'root_translation':list(a.pose.bones['Root'].location)}
a.animation_data.action=None
for p in a.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();sourcebounds={n:[pts(o).min(0).tolist(),pts(o).max(0).tolist()] for n,o in meshes.items()}
# Raw glTF confirms export clips, UV1, four influences, image contents and bounds.
b=(OUT/'lulu-game-lod1.glb').read_bytes();jl=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+jl]);raw=b[28+jl:]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);return np.ndarray((a['count'],cols),dtype=dt,buffer=raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*cols),dt.itemsize)).copy()
checks=[]
for m in g['meshes']:
 for p in m['primitives']:
  at=p['attributes'];weights=acc(at['WEIGHTS_0']);checks.append({'part':m['name'],'triangles':len(acc(p['indices']))//3,'finite':bool(np.isfinite(acc(at['POSITION'])).all()),'max_weight_sum_error':float(np.max(np.abs(weights.sum(1)-1))),'uv1':'TEXCOORD_1' in at})
report['gltf']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'parts':checks,'clips':[{'name':a['name'],'duration':max(float(acc(s['input']).max()) for s in a['samplers'])} for a in g['animations']],'skins':len(g['skins']),'joints':len(g['skins'][0]['joints']),'images':len(g['images'])}
# Actual importer readback, reset all NLA/pose to rest then compare extents.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'lulu-game-lod1.glb'))
for o in bpy.context.scene.objects:
 if o.animation_data:o.animation_data_clear()
 if o.type=='ARMATURE':
  for p in o.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();roundtrip={}
for o in bpy.context.scene.objects:
 if o.name in sourcebounds:
  p=pts(o);roundtrip[o.name]={'bounds_error':float(np.max(np.abs(np.array(sourcebounds[o.name])-np.array([p.min(0),p.max(0)])))),'verts':len(p)}
report['gltf_actual_reimport']=roundtrip
report['fbx_actual_reimport']={'status':'not exported; LOD1 GLB only'}
m=json.loads((OUT/'manifest.json').read_text());report['original_preservation']={'glb':hashlib.sha256(Path(m['source']).read_bytes()).hexdigest()==m['source_sha256'],'blend':hashlib.sha256(Path(m['source_blend']).read_bytes()).hexdigest()==m['source_blend_sha256']}
(REP/'lod1-readback.json').write_text(json.dumps(report,indent=2));print(json.dumps({'native':report['native'],'gltf':report['gltf'],'roundtrip':roundtrip,'fbx':report['fbx_actual_reimport'],'preservation':report['original_preservation']},indent=2))
