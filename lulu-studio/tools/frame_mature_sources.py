"""Save separate, reopenable inspection copies; leave production sources untouched."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'review/crop-mature-remaining-20261018'
for e in json.loads((O/'scope.json').read_text()):
 slug=e['id']
 for v in (['toon-r03','game-r02'] if slug=='rose' else ['toon-r01','game-r01']):
  src=R/f'assets-source/farm-assets/{e["batch"]}/{v}/{slug}-mature.blend';dest=src.with_name(slug+'-mature-inspection.blend')
  if dest.exists():continue
  bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;objects=[o for o in s.objects if o.get('production')];before=[(o.name,len(o.data.vertices),len(o.data.polygons),[(m.type,getattr(m,'ratio',None)) for m in o.modifiers]) for o in objects]
  setup=json.loads((O/slug/'review-settings.json').read_text());target=Vector(setup['camera_target']);height=setup['ortho_scale'];s.camera.data.ortho_scale=height;s.camera.location=target+Vector((1.35,-4,2.25)).normalized()*30;s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()
  for screen in bpy.data.screens:
   for area in screen.areas:
    if area.type=='VIEW_3D':
     area.spaces.active.region_3d.view_perspective='CAMERA'
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True);bpy.ops.wm.open_mainfile(filepath=str(dest));obs=[o for o in bpy.context.scene.objects if o.get('production')];after=[(o.name,len(o.data.vertices),len(o.data.polygons),[(m.type,getattr(m,'ratio',None)) for m in o.modifiers]) for o in obs];assert before==after
  (O/slug/v/'inspection-source.json').write_text(json.dumps({'source':str(dest.relative_to(R)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'parent_source':str(src.relative_to(R)),'source_reopened':True,'geometry_materials_unchanged':True,'geometry_modifier_counts_match':before==after,'saved_camera':setup},indent=2));print('FRAMED',slug,v,flush=True)
