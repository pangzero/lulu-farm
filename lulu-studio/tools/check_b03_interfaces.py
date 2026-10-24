"""Final geometric checks and corrected QA placement; never changes production assets."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
import review_b03 as r
from mathutils import Vector

metrics={a:r.stats(a) for a in r.build.ASSETS}
r.dump(r.QA/'metrics.json',metrics)
m=json.loads((r.OUT/'manifest.json').read_text());m['metrics']=metrics;r.dump(r.OUT/'manifest.json',m)
records={}
for a in r.build.ASSETS:
    bpy.ops.wm.open_mainfile(filepath=str(r.SRC/f'{a}-r03.blend'))
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='QA ground']
    records[a]={'source_reopened':True,'objects':[{'name':o.name,'type':o.type,'modifiers':[m.type for m in o.modifiers],'location':list(o.location)} for o in obs],'unit_scale':bpy.context.scene.unit_settings.scale_length}
    if a=='e13':
        sc=bpy.context.scene;sc.objects['QA ground'].location.z=-.01 # top exactly Z=0
        r.near_camera(sc,a,'quarter');r.image(sc,'e13-r03-contact-at-zero.png')
        r.near_camera(sc,a,'back');r.image(sc,'e13-r03-contact-back.png')
        records[a]['contact_plane_z']=0
r.dump(r.QA/'source-inspection.json',records)
r.assemble('shore')
print('B03 FINAL INTERFACE CHECKS DONE',flush=True)
