import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/wardrobe-rig/full-r02/lulu-rig.blend'))
a=next(o for o in bpy.data.objects if o.type=='ARMATURE')
d={'objects':[{'name':o.name,'verts':len(o.data.vertices),'tris':sum(len(p.vertices)-2 for p in o.data.polygons),'uv':[u.name for u in o.data.uv_layers],'location':list(o.location),'bbox':[list(x) for x in o.bound_box],'materials':[m.name if m else None for m in o.data.materials]} for o in bpy.data.objects if o.type=='MESH'],'bones':[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in a.data.bones],'actions':[x.name for x in bpy.data.actions]}
(R/'review/unity-integration-20261018/lulu/probe.json').write_text(json.dumps(d,indent=2))
print(json.dumps(d,indent=2))
