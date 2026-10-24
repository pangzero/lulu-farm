import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-animals/game-r02/cow/source-import.blend'))
for m in bpy.data.materials:
 print('MATERIAL',m.name)
 if m.node_tree:
  for n in m.node_tree.nodes:
   print(n.name,n.type,'image',n.image.name if n.type=='TEX_IMAGE' and n.image else None)
   if n.type=='BSDF_PRINCIPLED':print('FACTORS',list(n.inputs['Base Color'].default_value),n.inputs['Roughness'].default_value)
  print('LINKS',[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links])
for im in bpy.data.images:
 if im.source=='FILE':print(im.name,list(im.size),im.colorspace_settings.name)
