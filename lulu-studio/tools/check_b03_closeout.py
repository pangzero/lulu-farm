"""Read-only B03 r03 reopen/readback and fresh review evidence; no model export."""
import bpy, json, sys, inspect, math, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import review_b03 as r
ROOT=r.ROOT
QA=ROOT/'review/farm-assets/B03/closeout-20261018'
QA.mkdir(parents=True,exist_ok=True)
r.QA=QA
r.sin=math.sin;r.cos=math.cos
# Use the accepted official Lulu read-only instance in the independently saved QA scene.
code=inspect.getsource(r.assemble).replace('public/models/lulu-meshy-notail.glb','public/models/lulu-official-v1.glb')
exec(code,r.__dict__)
r.SETTINGS['lulu']['file']='public/models/lulu-official-v1.glb'
r.SETTINGS['closeout_date']='2026-10-18'
r.SETTINGS['production_assets_modified']=False
r.SETTINGS['qa_ground_top']['e13']=0
r.SETTINGS['web']['baseline_qa_viewport']=r.SETTINGS['web']['qa_viewport']
r.SETTINGS['web']['qa_viewport']=[1280,720]
r.SETTINGS['web']['browser_device_pixel_ratio']=2
r.SETTINGS['web']['renderer_pixel_ratio']=1
metrics={a:r.stats(a) for a in r.build.ASSETS}
r.dump(QA/'metrics.json',metrics)
r.dump(QA/'review-settings.json',r.SETTINGS)
sources={}
for a in r.build.ASSETS:
    p=r.SRC/f'{a}-r03.blend'
    bpy.ops.wm.open_mainfile(filepath=str(p))
    sc=bpy.context.scene
    obs=[o for o in sc.objects if o.type=='MESH' and o.name!='QA ground']
    sources[a]={'reopened':True,'source_sha256':r.sha(p),'unit_scale':sc.unit_settings.scale_length,
      'objects':[{'name':o.name,'modifiers':[m.type for m in o.modifiers], 'materials':[m.name if m else None for m in o.data.materials],
      'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in obs],
      'images':[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file),'pixels_decode':len(i.pixels)>0} for i in bpy.data.images if i.type!='RENDER_RESULT'],
      'color':{'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma}}
    # Fresh renders preserve the fixed B01 lights/color/cameras. E13 grounding is corrected only in QA memory.
    sc.render.threads_mode='FIXED';sc.render.threads=2
    if a=='e13':sc.objects['QA ground'].location.z=-.01
    for view in r.VIEWS:
        r.near_camera(sc,a,view);r.image(sc,f'{a}-r03-material-{view}.png')
    original={o.name:list(o.data.materials) for o in obs};clay=r.build.material('Closeout diagnostic neutral gray','#A3A3A3',.85)
    for o in obs:
        for i in range(len(o.data.materials)):o.data.materials[i]=clay
    for view in r.VIEWS:
        r.near_camera(sc,a,view);r.image(sc,f'{a}-r03-clay-{view}.png')
    for o in obs:
        for i,m in enumerate(original[o.name]):o.data.materials[i]=m
    detail={'e01':((.46,-.46,.015),.50),'e05':((.30,-.10,-.015),.70),'e07':((0,0,-.105),.86),'e13':((-.12,.04,.20),.85)}[a]
    r.build.aim(sc,detail[0],r.VIEWS['quarter'],detail[1]);r.image(sc,f'{a}-r03-detail.png')
    for o in obs:o.hide_render=True
    for rev in ['r01','r02','r03']:
        imported=r.import_glb(r.OUT/f'{a}-{rev}.glb');r.near_camera(sc,a);r.image(sc,f'{a}-{rev}-glb-controlled.png')
        for o in imported:bpy.data.objects.remove(o,do_unlink=True)
    print('CLOSEOUT_REVIEWED',a,flush=True)
r.dump(QA/'source-reopen.json',sources)
oldsetup=r.build.setup
def bounded_setup(*args,**kwargs):
    sc=oldsetup(*args,**kwargs);sc.render.threads_mode='FIXED';sc.render.threads=2;return sc
r.build.setup=bounded_setup
for mode in ['empty-tiles','tiles','shore','farm']:r.assemble(mode)
prior=json.loads((QA/'preservation-before.json').read_text())
records=[{'path':p,'before':s,'after':r.sha(ROOT/p),'unchanged':s==r.sha(ROOT/p)} for p,s in prior.items()]
r.dump(QA/'preservation-check.json',{'files':records,'all_unchanged':all(x['unchanged'] for x in records)})
print('B03_CLOSEOUT_NATIVE_COMPLETE',flush=True)
