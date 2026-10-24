"""Read-only Meshy GLB evaluation with B01 lighting and B04 fixed cameras.

Original GLBs stay byte-identical. The imported review .blend uses a single
documented .47 scale plus ground-centre translation; no mesh/material edits.
"""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_b04 import studio, CAMERAS
QA=ROOT/'review/farm-assets/B04-meshy-20261018'
OUT=ROOT/'public/models/farm-assets/B04/meshy-r01'
SRC=ROOT/'assets-source/farm-assets/B04/meshy-r01'
SCALE=.47
VIEWS={'front':(0,-1,.025),'side':(1,0,.025),'back':(0,1,.025),'quarter':(1.35,-4,2.25),'top':(0,-.001,1),'bottom':(0,-.001,-1)}
metrics={'revision':'meshy-r01','raw_files_unchanged':True,'common_instance_scale':SCALE,'assets':{}}
settings={'baseline':'B01 r03 user accepted','lighting':'Same B01 Cycles Standard/None exposure 0 gamma 1, world .32, key 280/fill 140/rim 230; see B01/review-settings.json','samples':16,'size':[640,640],'cameras':CAMERAS,'views':VIEWS,'common_scale':SCALE,'translation':'Each imported root centred in XY and grounded at min Z. No individual height normalization.','field':{'spacing':1.2,'size':[1280,720],'height':4.3,'camera_direction':[4,-6,6]}}
(QA/'review-settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n')
def cam(s,crop,view='quarter',size=(640,640),target=None,height=1.65):
    t=Vector(target or CAMERAS[crop]['target']);s.camera.location=t+Vector(VIEWS[view]).normalized()*10;s.camera.rotation_euler=(t-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=height*size[0]/size[1];s.render.resolution_x,s.render.resolution_y=size
def render(s,name):
    s.render.filepath=str(QA/name);bpy.ops.render.render(write_still=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['bokchoy','lettuce','cauliflower']
for crop in args:
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    bpy.ops.import_scene.gltf(filepath=str(OUT/f'{crop}-mature.glb'));obs=list(bpy.context.scene.objects);meshes=[o for o in obs if o.type=='MESH']
    pts=[];triangles=verts=zero=bad=badnorm=0
    for o in meshes:
        me=o.data;me.calc_loop_triangles();triangles+=len(me.loop_triangles);verts+=len(me.vertices)
        co=np.empty(len(me.vertices)*3,dtype=np.float64);me.vertices.foreach_get('co',co);co=co.reshape((-1,3));bad+=int((~np.isfinite(co)).any(axis=1).sum())
        areas=np.empty(len(me.polygons),dtype=np.float64);me.polygons.foreach_get('area',areas);zero+=int((areas<1e-12).sum())
        normals=np.empty(len(me.polygons)*3,dtype=np.float64);me.polygons.foreach_get('normal',normals);normals=normals.reshape((-1,3));badnorm+=int(((~np.isfinite(normals)).any(axis=1)|(np.linalg.norm(normals,axis=1)<.5)).sum())
        pts.extend(o.matrix_world@Vector(c) for c in o.bound_box)
    lo=Vector(tuple(min(v[i] for v in pts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in pts) for i in range(3)))
    root=bpy.data.objects.new('QA common scale and ground-centre placement',None);bpy.context.scene.collection.objects.link(root)
    for o in obs:
        if o.parent is None:o.parent=root
    root.scale=(SCALE,)*3;root.location=(-(lo.x+hi.x)*.5*SCALE,-(lo.y+hi.y)*.5*SCALE,-lo.z*SCALE)
    bpy.context.view_layer.update()
    item={'triangles':triangles,'vertices':verts,'mesh_objects':len(meshes),'raw_bbox_z_up':[list(lo),list(hi)],'display_size':list((hi-lo)*SCALE),'review_root_translation':list(root.location),'nonfinite_vertices':bad,'zero_area_faces':zero,'invalid_face_normals':badnorm,'embedded_images':[{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file)} for im in bpy.data.images if im.type=='IMAGE'],'source_type':'Imported Meshy mesh, not procedural authored Blender geometry','raw_mesh_and_materials_changed':False}
    metrics['assets'][crop]=item;(QA/'geometry-check.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
    s=studio();cam(s,crop)
    source=SRC/f'{crop}-import-review.blend'
    if source.exists():raise RuntimeError('Review source already exists; do not overwrite')
    bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
    for view in VIEWS:
        bpy.data.objects['QA ground not exported'].hide_render=view=='bottom'
        cam(s,crop,view);render(s,f'{crop}-material-{view}.png')
    bpy.data.objects['QA ground not exported'].hide_render=False
    original={o.name:list(o.data.materials) for o in meshes}
    clay=bpy.data.materials.new('QA neutral clay no texture or normal maps');clay.use_nodes=True;p=clay.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.38,.38,.38,1);p.inputs['Roughness'].default_value=.85;p.inputs['Specular IOR Level'].default_value=.28
    for o in meshes:o.data.materials.clear();o.data.materials.append(clay)
    for view in ['quarter','back','top']:cam(s,crop,view);render(s,f'{crop}-clay-{view}.png')
    for o in meshes:
        o.data.materials.clear()
        for m in original[o.name]:o.data.materials.append(m)
    # Shared-mesh diagnostic instances; evaluation only, not production rollout.
    for x in [-1.2,0,1.2]:
        for y in [-1.2,0,1.2]:
            if x==0 and y==0:continue
            r=root.copy();r.data=None;bpy.context.scene.collection.objects.link(r);r.location=root.location+Vector((x,y,0))
            for o in meshes:
                q=o.copy();q.data=o.data;q.parent=r;bpy.context.scene.collection.objects.link(q)
    cam(s,crop,size=(1280,720),target=(0,0,.35),height=4.3);t=Vector((0,0,.35));s.camera.location=t+Vector((4,-6,6));s.camera.rotation_euler=(t-s.camera.location).to_track_quat('-Z','Y').to_euler();render(s,f'{crop}-field.png')
    item['native_review_completed']=True;item['review_source']=str(source.relative_to(ROOT));(QA/'geometry-check.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n');print('MESHY REVIEW COMPLETE',crop,flush=True)
print('ALL MESHY NATIVE CHECKS COMPLETE',flush=True)
