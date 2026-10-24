from pathlib import Path
import bpy,json

R=Path(__file__).resolve().parents[1];D=R/'review/lulu-eye-ring-20261018/orbit-r03'
out=D/'lulu-eye-ring-candidate.blend'
if out.exists():raise RuntimeError('Candidate source exists; do not overwrite')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(D/'lulu-eye-ring.glb'))
for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    slots=[i for i,m in enumerate(obj.data.materials) if m and m.name.startswith('Right_Orbital_Continuous_Surface')]
    if slots:
        group=obj.vertex_groups.new(name='Right_orbital_reconstructed_region')
        ids={v for p in obj.data.polygons if p.material_index in slots for v in p.vertices}
        group.add(list(ids),1,'REPLACE')
        obj['edit_scope']='Only right orbital patch rebuilt; old eye rim released; front painted appearance reprojected.'
bpy.context.scene['status']='PARTIAL IMPROVEMENT CANDIDATE: sharp ring reduced; shallow socket remains; user art pending. Original assets unchanged.'
bpy.context.scene['provenance']='Imported independent orbital reconstruction GLB. Not a manually sculpted production retopology.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.wm.open_mainfile(filepath=str(out))
report={'source_reopened':True,'mesh_count':len([o for o in bpy.data.objects if o.type=='MESH']),'packed_images':len([i for i in bpy.data.images if i.packed_file]),'marked_orbital_vertex_groups':[o.name for o in bpy.data.objects if o.type=='MESH' and o.vertex_groups.get('Right_orbital_reconstructed_region')],'status':'independent candidate; visual/user acceptance separate'}
(D/'native-readback.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
