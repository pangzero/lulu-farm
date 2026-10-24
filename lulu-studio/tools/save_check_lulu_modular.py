"""Import a real modular GLB into an editable Blender assembly; validate parts."""
from pathlib import Path
import bpy,numpy as np,json,sys,hashlib
R=Path(__file__).resolve().parents[1];rev=sys.argv[sys.argv.index('--')+1]
src=R/'public/models/modular'/rev/'lulu-assembled.glb';dest=R/'assets-source/modular'/rev/'lulu-assembled.blend';report=R/'review/lulu-modular-20261018'/rev
assert src.exists() and not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(src),merge_vertices=True)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks=[]
for o in objects:
 me=o.data;me.calc_loop_triangles();p=np.array([v.co[:] for v in me.vertices]);f=np.array([t.vertices[:] for t in me.loop_triangles]);_,first,inv=np.unique(np.round(p,6),axis=0,return_index=True,return_inverse=True);wf=inv[f];valid=(wf[:,0]!=wf[:,1])&(wf[:,1]!=wf[:,2])&(wf[:,0]!=wf[:,2]);wf=wf[valid]
 edges=np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1);ue,counts=np.unique(edges,axis=0,return_counts=True)
 # Signed volume includes the thin garment interior with reversed winding.
 vol=float(np.einsum('ij,ij->i',p[f[:,0]],np.cross(p[f[:,1]],p[f[:,2]])).sum()/6)
 checks.append({'name':o.name,'vertices':len(p),'triangles':len(f),'welded_vertices':len(first),'boundary_edges':int(np.sum(counts==1)),'nonmanifold_edges':int(np.sum(counts>2)),'quantized_degenerate_triangles':int(np.sum(~valid)),'signed_volume':vol,'bounds':[p.min(0).tolist(),p.max(0).tolist()]})
 o['source_asset']='Lulu 正式版 v1 / cheekfix-r4';o['part_status']='Static modular candidate; no skin weights or skeleton';o['revision']=rev
bpy.context.scene['asset_name']='Lulu 静态分件候选 '+rev;bpy.context.scene['source_kind']='Preserved Meshy exterior plus authored hidden connection surfaces; not a native sculpt';bpy.context.scene['rigging_status']='No skeleton / skin / animations';bpy.context.scene['baseline_sha256']='5f770f539c3927b9e4d26a73bf96070e86e6b6cdd04e9710074b4c6645207e7d'
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
# Reopen the saved assembly and verify object/texture presence.
bpy.ops.wm.open_mainfile(filepath=str(dest));reopened=[o for o in bpy.context.scene.objects if o.type=='MESH']
images=[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file or im.packed_files)} for im in bpy.data.images if im.source=='FILE']
result={'revision':rev,'source_glb_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'blend':str(dest.relative_to(R)),'parts':checks,'reopened_mesh_count':len(reopened),'armatures':sum(o.type=='ARMATURE' for o in bpy.context.scene.objects),'actions':len(bpy.data.actions),'packed_images':images,'note':'Topology checks do not imply art acceptance. Static screenshots are evaluated separately.'}
(report/'blender-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
