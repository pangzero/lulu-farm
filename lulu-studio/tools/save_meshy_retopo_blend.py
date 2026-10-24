"""Save the independently reviewed retopo-5 GLB as an editable packed source."""
from pathlib import Path
import bpy
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'public/models/lulu-meshy-retopo.glb'))
for obj in bpy.context.scene.objects:
 if obj.type!='MESH':continue
 obj.name='Lulu_Meshy_Retopo5_NoTail'
 obj['revision']='retopo-5'
 obj['baseline']='review/meshy-eye-retopo-baseline/lulu-meshy-notail.glb'
 obj['scope']='New annular eye-rim connections. Eye center, head/body and no-tail shorts retained.'
 patch_materials={i for i,m in enumerate(obj.data.materials) if m and 'Retopo_EyeConnection' in m.name}
 indices={v for face in obj.data.polygons if face.material_index in patch_materials for v in face.vertices}
 if indices:obj.vertex_groups.new(name='Rebuilt_EyeConnections').add(sorted(indices),1,'REPLACE')
text=bpy.data.texts.new('READ_ME_Retopo5')
text.write('Independent candidate retopo-5, 2026-10-16.\n'
 'Baseline no-tail-2 is backed up and remains unchanged.\n'
 'Build: tools/retopologize_lulu_eye_rims.py\n'
 'Asset note: /Users/haowen/Documents/Obsidian Vault/04 project/Farm/Lulu 资产说明.md\n'
 'Only eye-rim annuli rebuilt; original central eye cores and outside surface retained.\n'
 'New patch colors transferred in each eye tangent frame; old skin groove shading locally removed.\n'
 'Residual shallow under-eye line remains. Not a claim of final character acceptance.\n')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'assets-source/lulu-meshy-retopo.blend'))
