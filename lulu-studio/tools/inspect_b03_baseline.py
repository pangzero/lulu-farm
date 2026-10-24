import bpy,json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
result={}
for c in ['cabbage','tomato','corn']:
    bpy.ops.wm.open_mainfile(filepath=str(r/f'assets-source/farm-assets/B01/{c}-mature-r03.blend'))
    result[c]={'objects':len(bpy.data.objects),'editable_meshes':len([o for o in bpy.data.objects if o.type=='MESH']),'modifiers':sorted(set(m.type for o in bpy.data.objects for m in o.modifiers)),'camera':list(bpy.context.scene.camera.location),'view_transform':bpy.context.scene.view_settings.view_transform}
(r/'review/farm-assets/B03/baseline-source-inspection.json').write_text(json.dumps(result,indent=2))
print(result)
