import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'assets-source/unity-lulu/locomotion-r04/lulu-game-lod0.blend'));a=bpy.data.objects['Lulu_Modular_Rig'];a.animation_data.action=bpy.data.actions['Run'];bpy.context.scene.frame_set(4);bpy.context.view_layer.update();t=Vector((0,0,-.69));d=Vector((1.35,-4,2.25)).normalized();cam=t+d*5;q=(-d).to_track_quat('-Z','Y');right=q@Vector((1,0,0));up=q@Vector((0,1,0));dg=bpy.context.evaluated_depsgraph_get()
for x,y in [(665,330),(670,340),(672,350),(675,355),(680,340),(650,350),(655,365),(640,375)]:
 origin=cam+right*((x/768-.5)*1.12)+up*((.5-y/768)*1.12);hit,loc,n,i,o,ma=bpy.context.scene.ray_cast(dg,origin,-d);print((x,y),hit,o.name if o else '',list(loc),list(a.matrix_world.inverted()@loc))
