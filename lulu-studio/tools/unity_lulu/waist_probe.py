import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu/locomotion-r04/lulu-game-lod0.blend'))
for name in ['Body','Shorts']:
 o=bpy.data.objects[name];print(name)
 for lo,hi in [(-.7,-.6),(-.6,-.55),(-.55,-.5),(-.5,-.45),(-.45,-.4)]:
  vs=[v for v in o.data.vertices if lo<v.co.z<=hi];g={}
  for v in vs:
   for x in v.groups:g[o.vertex_groups[x.group].name]=g.get(o.vertex_groups[x.group].name,0)+x.weight
  print(lo,hi,len(vs),{k:round(v/max(len(vs),1),3) for k,v in g.items() if v>0.00001})
