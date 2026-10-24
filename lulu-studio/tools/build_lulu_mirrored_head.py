"""Independent head component from the original sculpture's intact half.

No arm labels, posed meshes or previous gap patches are used. Raw source is
Y-up; head reconstruction uses the measured tilted symmetry frame. Only short
neck and crown closures are new surfaces; the exposed half-head is retained.
"""
from pathlib import Path
import argparse, sys, json, math, hashlib
import bpy, bmesh, numpy as np
from mathutils import Vector

R=Path(__file__).resolve().parents[1]; D=R/'review/lulu-head-mirror-20261021'
arg=argparse.ArgumentParser();arg.add_argument('--revision',default='head-r04')
args=arg.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=D/args.revision
if out.exists():raise RuntimeError('Use a new revision; never overwrite head candidates')
out.mkdir()
a=np.load(D/'baseline/welded-source.npz');p=a['p'];f=a['f'];basis=a['head_basis'];center=a['head_center']
h=np.einsum('ij,kj->ik',p-center,basis);h[:,1]+=.72
bpy.ops.wm.read_factory_settings(use_empty=True)
gray=bpy.data.materials.new('Neutral gray');gray.diffuse_color=(.47,.47,.47,1);gray.use_nodes=True
bs=gray.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.47,.47,.47,1);bs.inputs['Roughness'].default_value=.85

def bm_from(v,faces):
    m=bpy.data.meshes.new('Working topology');m.from_pydata(v,[],faces);m.update()
    bm=bmesh.new();bm.from_mesh(m);bpy.data.meshes.remove(m);return bm

def cut(bm,point,normal):
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,
        plane_co=point,plane_no=normal,clear_outer=True,clear_inner=False)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')

def boundaries(bm):
    edges={e for e in bm.edges if e.is_boundary};loops=[]
    while edges:
        first=next(iter(edges));start=first.verts[0];v=start;loop=[]
        while True:
            loop.append(v);opts=[e for e in v.link_edges if e in edges]
            if not opts:break
            e=opts[0];edges.remove(e);v=e.other_vert(v)
            if v==start:break
        loops.append(loop)
    return loops

def close_round(bm,loop,rise,crown=False):
    # Complete the short neck connector / covered crown, not the source cheek.
    xyz=np.array([v.co[:] for v in loop]);c=xyz.mean(0);old=loop;made=[]
    rings=[(.98,rise*.22),(.90,rise*.65),(.65,rise*.95),(.30,rise)]
    if crown:rings=[(s,rise*(1-s*s)) for s in [.97,.88,.73,.53,.30,.10]]
    for scale,dy in rings:
        new=[]
        for v in xyz:
            q=c+(v-c)*scale;q[1]=c[1]+dy
            w=bm.verts.new(q.tolist());new.append(w);made.append(w)
        for i in range(len(old)):bm.faces.new((old[i],old[(i+1)%len(old)],new[(i+1)%len(old)],new[i]))
        old=new
    tip=bm.verts.new((c+[0,rise,0]).tolist());made.append(tip)
    for i in range(len(old)):bm.faces.new((old[i],old[(i+1)%len(old)],tip))
    return made

def obj_from_bm(bm,name,collection=None):
    bm.normal_update();bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    # Local head frame -> raw Y-up -> Blender Z-up.
    for v in bm.verts:
        q=np.array(v.co[:]);q[1]-=.72
        raw=np.einsum('i,ij->j',q,basis)+center
        v.co=(raw[0],-raw[2],raw[1])
    mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);mesh.update()
    o=bpy.data.objects.new(name,mesh);(collection or bpy.context.collection).objects.link(o)
    mesh.materials.append(gray)
    for poly in mesh.polygons:poly.use_smooth=True
    return o

# The intact anatomical RIGHT half (front screen-left) contains no raised hand.
bm=bm_from(h.tolist(),f.tolist());cut(bm,(0,.470,0),(0,-1,0));cut(bm,(0,.913,0),(0,1,0));cut(bm,(0,0,0),(1,0,0))
for v in bm.verts:
    if abs(v.co.x)<2e-6:v.co.x=0
bm.verts.index_update();bm.verts.ensure_lookup_table()
v=np.array([v.co[:] for v in bm.verts]);faces=[list(fv.index for fv in face.verts) for face in bm.faces];bm.free()
nv=len(v);mirror=v.copy();mirror[:,0]*=-1
bm=bm_from(np.concatenate([v,mirror]).tolist(),faces+[[i+nv for i in reversed(face)] for face in faces])
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
loops=boundaries(bm)
if len(loops)!=2:raise RuntimeError(f'Expected crown and neck boundaries, got {len(loops)}')
closures={}
for loop in loops:
    y=sum(v.co.y for v in loop)/len(loop)
    key='NeckClosure' if y<.6 else 'CoveredCrownClosure'
    closures[key]=close_round(bm,loop,-.014 if y<.6 else .022,crown=y>.6)
# Fair all three coordinates at the bisected/welded center to avoid folding
# skinny cut triangles. A tapered 0.024-wide band leaves outer shapes fixed.
seam=[v for v in bm.verts if abs(v.co.x)<.012 and .49<v.co.y<.90]
seam_initial={v:v.co.copy() for v in seam}
for _ in range(24):
    updates={}
    for v in seam:
        w=max(0,1-(abs(seam_initial[v].x)/.012)**2)**2
        near=[e.other_vert(v).co for e in v.link_edges]
        avg=sum(near,Vector())/len(near)
        q=v.co.lerp(avg,.30*w)
        if abs(seam_initial[v].x)<1e-7:q.x=0
        updates[v]=q
    for v,q in updates.items():v.co=q
bm.verts.index_update()
groups={k:[v.index for v in vals] for k,vals in closures.items()}
groups['MidlineBlend']=[v.index for v in seam]
groups['IntactHalf']=[v.index for v in bm.verts if v.co.x<-.004]
groups['MirroredHalf']=[v.index for v in bm.verts if v.co.x>.004]
head=obj_from_bm(bm,'Lulu_Head_Mirrored');bm.free()
for name,indices in groups.items():
    vg=head.vertex_groups.new(name=name);vg.add(indices,1,'REPLACE')
head['source_half']='Character RIGHT, front screen-left; intact head half.'
head['method']='Tilted-plane bilateral reconstruction; original half surface plus mirrored counterpart; narrow welded center; rounded short neck closure.'
head['scope']='HEAD ONLY. No armature. Original body and arms not modified.'

# Keep the asymmetric original fruit/leaf ornament in its original position.
# The short overlapping underside is inside the newly closed crown.
fruit=bm_from(h.tolist(),f.tolist());cut(fruit,(0,.921,0),(0,-1,0))
for loop in boundaries(fruit):close_round(fruit,loop,-.020)
ornament=obj_from_bm(fruit,'Original_Crown_Ornament');fruit.free()
ornament['note']='Original top ornament above local y=.921; retained exterior and position, closed underside inside reconstructed crown. Not mirrored.'

reference_col=bpy.data.collections.new('Original source — hidden comparison');bpy.context.scene.collection.children.link(reference_col)
reference=bm_from(h.tolist(),f.tolist());ref=obj_from_bm(reference,'Original_Source_Unmodified',reference_col);reference.free()
ref.hide_render=True;ref.hide_set(True);ref['note']='Full unmodified sculpture reference. Do not edit.'
for obj in bpy.context.scene.objects:obj.select_set(False)
head.select_set(True);ornament.select_set(True);bpy.context.view_layer.objects.active=head
bpy.ops.export_scene.gltf(filepath=str(out/'lulu-head-mirrored.glb'),export_format='GLB',use_selection=True,export_yup=True,export_materials='EXPORT',export_extras=True)
# Additional actual head-only file, useful for later component assembly.
ornament.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(out/'lulu-head-only.glb'),export_format='GLB',use_selection=True,export_yup=True,export_materials='EXPORT',export_extras=True)
bpy.context.scene['stage']='Independent head prototype; user shape approval required before torso/arms/rig.'
bpy.context.scene['source']='Spencer0131 / Sketchfab a5747f74f0034470a2029a85f6e9c11d / CC-BY-4.0'
bpy.context.scene['fitted_symmetry_basis']=json.dumps(basis.tolist())
bpy.ops.wm.save_as_mainfile(filepath=str(out/'lulu-head-mirrored.blend'))
check=bmesh.new();check.from_mesh(head.data)
report={'revision':args.revision,'head_vertices':len(head.data.vertices),'head_polygons':len(head.data.polygons),'head_boundary_edges':sum(e.is_boundary for e in check.edges),'head_nonmanifold_edges':sum(not e.is_manifold for e in check.edges),'source_unchanged':hashlib.sha256((D/'baseline/a5747f74f0034470a2029a85f6e9c11d.glb').read_bytes()).hexdigest(),'head_cut_local_y':.470,'head_crown_join_local_y':.913,'symmetry_fit':json.loads((D/'symmetry-fit.json').read_text()),'status':'AWAITING_VISUAL_REVIEW','armatures':0}
check.free();(out/'build.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='symmetry_fit'},indent=2),flush=True)
