import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'public/models/animal-studies/cow-head-clean-v4.glb'))
for o in bpy.data.objects:
 if o.type=='MESH':
  print(o.name,len(o.data.vertices),len(o.data.polygons),list(o.dimensions),[m.name for m in o.data.materials]);print([(i,sum(len(p.vertices)-2 for p in o.data.polygons if p.material_index==i)) for i in range(len(o.data.materials))])
