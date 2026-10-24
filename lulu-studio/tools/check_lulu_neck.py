"""Independent readback/preservation checks and native inspection copy.
Run with Blender --background --python. Does not regenerate the candidate.
"""
from pathlib import Path
import bpy, json, struct, hashlib
import numpy as np
from mathutils import Vector

R=Path(__file__).resolve().parents[1]
D=R/'review/lulu-neck-junction-20261023'
O=D/'neck-r02'

def load(p):
    raw=p.read_bytes(); n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n]),raw[28+n:]

def acc(g,b,i):
    a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]
    dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
    k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    return np.ndarray((a['count'],k),dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*k),dt.itemsize)).copy()

def trs(n):
    if 'matrix' in n:return np.array(n['matrix']).reshape(4,4).T
    from mathutils import Quaternion
    x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
    m[:3,:3]=np.array(Quaternion((w,x,y,z)).to_matrix())@np.diag(n.get('scale',[1,1,1]))
    m[:3,3]=n.get('translation',[0,0,0]);return m

def matrices(g):
    out={}
    def visit(i,m):
        m=m@trs(g['nodes'][i]);out[g['nodes'][i]['name']]=m
        for j in g['nodes'][i].get('children',[]):visit(j,m)
    for i in g['scenes'][g.get('scene',0)]['nodes']:visit(i,np.eye(4))
    return out

src=D/'baseline/review/lulu-hybrid-assembly-20261023/hybrid-r02/lulu-hybrid.glb'
g0,b0=load(src);g,b=load(O/'lulu-neck.glb')
n0={n['name']:n for n in g0['nodes']};nn={n['name']:n for n in g['nodes']}
w0=matrices(g0)
transforms={name:all(node.get(k)==nn[name].get(k) for k in ['matrix','translation','rotation','scale','children']) for name,node in n0.items()}
assert all(transforms.values())
untouched={};retained={};gaps={}
for name,node in n0.items():
    if 'mesh' not in node:continue
    p0=g0['meshes'][node['mesh']]['primitives'];pp=g['meshes'][nn[name]['mesh']]['primitives']
    if name not in ['Body','Lulu_Head_Mirrored']:
        same=len(p0)==len(pp)
        for a,c in zip(p0,pp):
            same &= a==c
            for key,i in a['attributes'].items():same &= np.array_equal(acc(g0,b0,i),acc(g,b,c['attributes'][key]))
            same &= np.array_equal(acc(g0,b0,a['indices']),acc(g,b,c['indices']))
        untouched[name]=bool(same);assert same;continue
    kept=0;actual_boundary=[]
    for a,c in zip(p0,pp):
        ix=acc(g0,b0,a['indices']).reshape(-1,3);jx=acc(g,b,c['indices']).reshape(-1,3)
        pos=acc(g0,b0,a['attributes']['POSITION'])[ix].astype(float)
        m=w0[name];pos=np.einsum('...j,ij->...i',pos,m[:3,:3])+m[:3,3]
        field=pos[:,:,1]-.510 if name!='Body' else .425+.035*np.cos(np.arctan2(pos[:,:,2]+.015,pos[:,:,0]))**2-pos[:,:,1]
        keep=(field>=0).all(1);count=int(keep.sum());kept+=count
        for key,i in a['attributes'].items():
            old=acc(g0,b0,i)[ix[keep]];new=acc(g,b,c['attributes'][key])[jx[:count]]
            assert np.array_equal(old,new),(name,key)
        vp=acc(g,b,c['attributes']['POSITION']).astype(float)
        vp=np.einsum('...j,ij->...i',vp,m[:3,:3])+m[:3,3]
        # Inspect actual new clipped faces. The curved cut field is linearly
        # interpolated across a source triangle, not reprojected onto a formula.
        actual_boundary.append(vp[np.unique(jx[count:])])
    retained[name]={'triangle_count':kept,'all_corner_attributes_bit_exact':True}
    data=np.load(O/'neck-boundaries.npz');ring=data['body' if name=='Body' else 'head'][:,:3]
    actual_boundary=np.concatenate(actual_boundary)
    dist=np.sqrt(((ring[:,None,:]-actual_boundary[None,:,:])**2).sum(2).min(1))
    gaps[name]=float(dist.max());print('Boundary check',name,len(actual_boundary),float(dist.max()),flush=True);assert dist.max()<2e-6

data=np.load(O/'neck-boundaries.npz');v=data['bridge'][:,:3];f=data['triangles']
assert np.isfinite(v).all()
area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2
edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
edges,counts=np.unique(edges,axis=0,return_counts=True)
assert counts.max()==2
boundary=edges[counts==1];bi,bc=np.unique(boundary,return_counts=True)
assert np.all(bc==2) and len(boundary)==len(data['head'])+len(data['body'])
assert area.min()>1e-14
assert not g.get('skins') and not g.get('animations')

backup=[]
for entry in json.loads((D/'backup.json').read_text()):
    a=hashlib.sha256((R/entry['source']).read_bytes()).hexdigest()
    c=hashlib.sha256((R/entry['backup']).read_bytes()).hexdigest()
    assert a==c==entry['sha256'];backup.append({'source':entry['source'],'unchanged':True})

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(O/'lulu-neck.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==9
for ob in meshes:
    ob['source']='hybrid-r02; backed up before local neck edit'
    ob['edit_scope']='new boundary-constrained neck band' if ob.name=='Neck_Transition' else ('neck interface clipped only; other triangle attributes preserved' if ob.name in ['Body','Lulu_Head_Mirrored'] else 'untouched source component')
bpy.context.scene['review_status']='neck-r02 static candidate, user appearance acceptance pending; no rig'
bpy.context.scene['boundary_note']='Head/Body/Neck are separate open surfaces with coincident edge loops; not standalone closed parts or animation-ready skin.'
for area_ui in bpy.context.screen.areas if bpy.context.screen else []:
    if area_ui.type=='VIEW_3D':
        space=area_ui.spaces.active;space.shading.type='SOLID';space.region_3d.view_distance=1.8;space.region_3d.view_location=Vector((0,0,.53))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(O/'lulu-neck.blend'))
bpy.ops.wm.open_mainfile(filepath=str(O/'lulu-neck.blend'))
assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==9
assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
report={'revision':'neck-r02','node_transforms_and_hierarchy_unchanged':transforms,'six_other_components_bit_exact':untouched,'head_body_retained_triangles':retained,'boundary_max_distance_world':gaps,'bridge_area_min':float(area.min()),'bridge_boundary_edges':len(boundary),'bridge_nonmanifold_edges':0,'bridge_y_range':[float(v[:,1].min()),float(v[:,1].max())],'backup_files':backup,'native_import_save_reopen':True,'mesh_objects':9,'armatures':0,'status':'Technical preservation checked; visual acceptance remains separate','limitation':'Open component seam loops coincide to float precision. No claim of standalone watertight parts, animation or finished color.'}
(O/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
