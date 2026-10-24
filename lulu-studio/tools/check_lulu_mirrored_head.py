"""Reopen native and exported head; verify scope and retained source surface."""
from pathlib import Path
import bpy, bmesh, numpy as np, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-head-mirror-20261021';O=D/'head-r04'
bpy.ops.wm.open_mainfile(filepath=str(O/'lulu-head-mirrored.blend'))
head=bpy.data.objects['Lulu_Head_Mirrored']; bm=bmesh.new();bm.from_mesh(head.data)
raw=np.array([(v.co.x,v.co.z,-v.co.y) for v in head.data.vertices])
faces=[list(p.vertices) for p in head.data.polygons]
bvh=BVHTree.FromPolygons(raw.tolist(),faces,all_triangles=False)
a=np.load(D/'baseline/welded-source.npz');p=a['p'];h=np.einsum('ij,kj->ik',p-a['head_center'],a['head_basis']);h[:,1]+=.72
keep=(h[:,0]<-.013)&(h[:,1]>.475)&(h[:,1]<.910)
pts=p[keep][::3];dist=np.array([bvh.find_nearest(Vector(x))[3] for x in pts])
unseen=set(bm.verts);components=[]
while unseen:
    seed=unseen.pop();stack=[seed];cnt=0
    while stack:
        v=stack.pop();cnt+=1
        for e in v.link_edges:
            v2=e.other_vert(v)
            if v2 in unseen:unseen.remove(v2);stack.append(v2)
    components.append(cnt)
native={'mesh_objects':len([o for o in bpy.data.objects if o.type=='MESH']),'armatures':len([o for o in bpy.data.objects if o.type=='ARMATURE']),'head_closed':not any(e.is_boundary for e in bm.edges),'head_nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'head_components':components,'head_bounds_raw':[raw.min(0).tolist(),raw.max(0).tolist()],'retained_half_surface_samples':len(pts),'retained_half_surface_max_distance':float(dist.max()),'retained_half_surface_p99_distance':float(np.quantile(dist,.99)),'vertex_groups':[v.name for v in head.vertex_groups],'reference_hidden':bpy.data.objects['Original_Source_Unmodified'].hide_render}
bm.free();bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(O/'lulu-head-mirrored.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
export={'meshes':[(o.name,len(o.data.vertices),len(o.data.polygons)) for o in meshes],'armatures':len([o for o in bpy.data.objects if o.type=='ARMATURE']),'finite':all(all(np.isfinite(v.co[:])) for o in meshes for v in o.data.vertices)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files={'download':Path('/Users/haowen/Downloads/a5747f74f0034470a2029a85f6e9c11d.glb'),'backup':D/'baseline/a5747f74f0034470a2029a85f6e9c11d.glb','original_colour':R/'review/lulu-sketchfab-color-20261019/color-r08/lulu-sketchfab-colour.glb','old_official':R/'public/models/lulu-official-v1.glb','head_glb':O/'lulu-head-mirrored.glb','head_blend':O/'lulu-head-mirrored.blend'}
hashes={k:sha(p) for k,p in files.items()}
assert hashes['download']==hashes['backup']=='13c234b586876b53cc5bd435b55ffd8612cb3994accb83648c5ba9f5fd0a037b'
assert hashes['original_colour']=='01e9ef974ac2e39206b4448562f1918c053fbc2c1a584d88ba12246e609ba2ac'
assert hashes['old_official']=='5f770f539c3927b9e4d26a73bf96070e86e6b6cdd04e9710074b4c6645207e7d'
report={'native_reopened':native,'export_reopened':export,'sha256':hashes,'status':'Technical check only; see screenshots for shape acceptance.'}
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
