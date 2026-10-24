"""Read-only baseline restoration and actual Lulu doorway envelope check."""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_b02 as B
R=Path(__file__).resolve().parents[1];Q=R/'review/farm-assets/B14'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bounds(obs):
    pts=[o.matrix_world@v.co for o in obs if o.type=='MESH' for v in o.data.vertices]
    return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
base=[]
for batch,name in [('B01','cabbage-mature-r03'),('B01','tomato-mature-r03'),('B01','corn-mature-r03'),('B02','s01-facade-sample-r04')]:
    src=R/f'assets-source/farm-assets/{batch}/{name}.blend';glb=R/f'public/models/farm-assets/{batch}/{name}.glb'
    bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene
    record={'source':str(src.relative_to(R)),'source_sha256':sha(src),'reopened':True,'mesh_curve_objects':sum(o.type in ['MESH','CURVE'] for o in s.objects),
       'color':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma],
       'lights':[{ 'name':o.name,'energy':o.data.energy,'location':list(o.location)} for o in s.objects if o.type=='LIGHT']}
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb));bpy.context.view_layer.update()
    record.update({'glb':str(glb.relative_to(R)),'glb_sha256':sha(glb),'readback':True,'bbox':bounds(bpy.context.scene.objects)})
    base.append(record)
(Q/'baseline-reopen.json').write_text(json.dumps(base,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/farm-assets/B14/r02/s01-main-house.blend'));s=bpy.context.scene
col=bpy.data.collections['S01 editable door']
hidden=[]
for o in col.objects:
    if o.type in ['MESH','CURVE'] and not ('jamb' in o.name or 'casing' in o.name):o.hide_render=True;hidden.append(o.name)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/'public/models/lulu-official-v1.glb'));added=list(set(bpy.data.objects)-before)
root=bpy.data.objects.new('QA Lulu doorway envelope - not exported',None);s.collection.objects.link(root)
for o in added:
    if o.parent not in added:o.parent=root
root.scale=(.6313689262131015,)*3;bpy.context.view_layer.update();b=bounds(added)
root.location=(0,-1.72,.31-b[0][2]);bpy.context.view_layer.update();b=bounds(added)
pts=[o.matrix_world@v.co for o in added if o.type=='MESH' for v in o.data.vertices]
violations=[]
for p in pts:
    cap=1.57+math.sqrt(max(0,.555**2-p.x**2))
    if abs(p.x)>.555 or p.z>cap+1e-5:violations.append(list(p))
measurement={'readonly_lulu_sha256':sha(R/'public/models/lulu-official-v1.glb'),'lulu_instance_scale':.6313689262131015,'lulu_display_bbox':b,
 'lulu_width':b[1][0]-b[0][0],'lulu_height':b[1][2]-b[0][2], 'structural_opening_width':1.18,'timber_clear_width':1.11,
 'timber_spring_z':1.57,'timber_inner_crown_z':2.125,'threshold_top_z':.30,'wood_sill_top_z':.31,
 'standing_qa_z':.31,'min_side_margin':.555-max(abs(b[0][0]),abs(b[1][0])), 'top_margin_at_centre':2.125-b[1][2],
 'projected_head_body_outside_arch_vertices':len(violations),'result':'pass' if not violations else 'fail',
 'scope':'Static frontal envelope only. Door leaf hidden in QA memory, no production file change, no nav/collision or interior work.',
 'qa_only_hidden_door_parts':hidden}
(Q/'r02/entrance-clearance.json').write_text(json.dumps(measurement,ensure_ascii=False,indent=2))
B.camera(s,(0,-1.7,1.3),2.8,(0,-1,.025));s.render.resolution_x=s.render.resolution_y=768
s.render.threads_mode='FIXED';s.render.threads=3;s.render.filepath=str(Q/'r02/entrance-clearance.png');bpy.ops.render.render(write_still=True)
print('BASELINES RESTORED READONLY; ENTRANCE',measurement['result'],flush=True)
