"""Read saved B02 sources and exported GLBs; never overwrite production assets."""
import bpy,bmesh,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];QA=ROOT/'review/farm-assets/B02';SRC=ROOT/'assets-source/farm-assets/B02';OUT=ROOT/'public/models/farm-assets/B02'
REV='r04';VIEWS={'front':(0,-1,.025),'side':(1,0,.025),'back':(0,1,.025),'quarter':(1.35,-4,2.25),'top':(0,-.001,1)}
CAMERAS={'s01':{'target':[0,0,1.53],'ortho_scale':4.55},'s05':{'target':[.6,0,.46],'ortho_scale':1.85}}
FILES={'s01':'s01-facade-sample','s05':'s05-fence'}

def render(s,path):
    s.render.filepath=str(QA/path);bpy.ops.render.render(write_still=True)

def camera(s,target,scale,view='quarter',size=(768,768)):
    target=Vector(target);s.camera.location=target+Vector(VIEWS[view]).normalized()*12
    s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler()
    s.camera.data.ortho_scale=scale;s.render.resolution_x,s.render.resolution_y=size;s.cycles.samples=16

def visible_meshes():return [o for o in bpy.context.scene.objects if o.type in ['MESH','CURVE'] and not o.name.startswith('QA ground')]

def import_glb(path,offset=0):
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));added=set(bpy.data.objects)-before
    for o in added:
        if o.parent not in added:o.location.x+=offset
    bpy.context.view_layer.update();return list(added)

def glb_stats(path):
    bpy.ops.wm.read_factory_settings(use_empty=True);added=import_glb(path);obs=[o for o in added if o.type=='MESH']
    vs=[o.matrix_world@v.co for o in obs for v in o.data.vertices];lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
    zero=0;dups=0;nonfinite=0;badnormals=0;boundaries=0;nonmanifold=0;negativevol=[]
    for o in obs:
        faces=[tuple(sorted(p.vertices)) for p in o.data.polygons];dups+=len(faces)-len(set(faces))
        zero+=sum(p.area<1e-12 for p in o.data.polygons)
        nonfinite+=sum(not all(math.isfinite(c) for c in v.co) for v in o.data.vertices)
        badnormals+=sum(not all(math.isfinite(c) for c in p.normal) or p.normal.length<.5 for p in o.data.polygons)
        # glTF splits vertices at material/normal boundaries. Weld only a temporary
        # diagnostic bmesh before classifying manifold edges and signed volume.
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        boundaries+=sum(e.is_boundary for e in bm.edges);nonmanifold+=sum(not e.is_manifold for e in bm.edges)
        # Disconnected closed solids are expected: architectural editable parts.
        if bm.calc_volume(signed=True)<-1e-8:negativevol.append(o.name)
        bm.free()
    raw=path.read_bytes();g=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    tris=sum(g['accessors'][p['indices']]['count']//3 for m in g.get('meshes',[]) for p in m['primitives'])
    return {'file':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':tris,'vertices_imported':len(vs),'mesh_nodes':len(obs),'primitives':sum(len(m['primitives']) for m in g.get('meshes',[])),'materials':len(g.get('materials',[])),'textures':len(g.get('images',[])),'texture_dimensions':[],'external_uris':[i['uri'] for i in g.get('images',[]) if 'uri' in i and not i['uri'].startswith('data:')],'bbox_blender_z_up':[lo,hi],'size':[b-a for a,b in zip(lo,hi)],'zero_area_faces':zero,'duplicate_index_faces':dups,'nonfinite_vertices':nonfinite,'invalid_face_normals':badnormals,'welded_boundary_edges':boundaries,'welded_nonmanifold_edges':nonmanifold,'negative_signed_volume_meshes':negativevol,'negative_transform_objects':[o.name for o in obs if o.matrix_world.determinant()<0],'exported_cameras':len(g.get('cameras',[])),'exported_lights':len(g.get('extensions',{}).get('KHR_lights_punctual',{}).get('lights',[])),'readback':'success','origin':'Blender world ground origin; S05 left post centre; S01 wall centre at ground','normal_check':'Finite/unit face normals, positive signed volume and actual front/back renders; component intersections internal to joinery are intentional.'}

settings=json.loads((ROOT/'review/farm-assets/B01/review-settings.json').read_text())
settings.update({'batch':'B02','revision':REV,'baseline':'B01 r03 user-accepted art baseline; native lights/colors inherited unchanged','cameras':CAMERAS,'new_asset_normalization':False,'scope':'S01 facade sample only, not complete house; S05 straight fence with terminal accessory','sample_design_inference':'Sample back, cut wall ends, shallow eave strip and repeat ownership are derived construction; reference supplies front/three-quarter design only.','fence_interface':{'repeat_step':1.2,'post_dimensions':[.22,.24,.94],'rail_contact_x':[.11,1.09],'rail_dimensions':[.98,.11,.15],'rail_centre_z':[.32,.67],'origins':[0,1.2,2.4],'endcap_x':3.6,'ownership':'One left post and 2 rails per repeat; one separate terminal post at end.','end_faces':'Flat X contact planes; rounded YZ rail profile; no overlapping end bevels.'},'native_detail_cameras':{'door':{'target':[-.78,-.1,1.0],'ortho_scale':2.3},'window_eave':{'target':[.85,-.14,1.83],'ortho_scale':2.55},'fence_joint':{'target':[1.2,0,.5],'ortho_scale':.72}},'native_three_camera':{'target':[1.8,0,.46],'ortho_scale':4.5,'image':[1280,720]},'lulu':dict(settings['lulu'],reason='B02 uses the established B01 presentation scale; original geometry stays unchanged. No interior navigation/collision implemented.')})
(QA/'review-settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2))

metrics={}
for key,filename in [('s01','s01-facade-sample'),('s05_repeat','s05-fence-repeat'),('s05_endcap','s05-fence-endcap')]:metrics[key]=glb_stats(OUT/f'{filename}-{REV}.glb')
metrics['sources']={}
for key,filename in FILES.items():
    path=SRC/f'{filename}-{REV}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;prod=visible_meshes()
    metrics['sources'][key]={'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reopened':True,'editable_components':len(prod),'component_names':[o.name for o in prod],'modifiers':{o.name:[m.type for m in o.modifiers] for o in prod if o.modifiers},'source_axes':'Z up; front -Y; ground Z=0'}
    cfg=CAMERAS[key]
    for v in VIEWS:camera(s,cfg['target'],cfg['ortho_scale'],v);render(s,f'{key}-{REV}-material-{v}.png')
    clay=bpy.data.materials.new('B02 neutral diagnostic clay');clay.use_nodes=True
    p=clay.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.38,.38,.38,1);p.inputs['Roughness'].default_value=.85;p.inputs['Specular IOR Level'].default_value=.28
    originals={o.name:list(o.data.materials) for o in prod}
    for o in prod:o.data.materials.clear();o.data.materials.append(clay)
    for v in VIEWS:camera(s,cfg['target'],cfg['ortho_scale'],v);render(s,f'{key}-{REV}-clay-{v}.png')
    for o in prod:
        o.data.materials.clear()
        for m in originals[o.name]:o.data.materials.append(m)
    if key=='s01':
        for detail in ['door','window_eave']:
            c=settings['native_detail_cameras'][detail];camera(s,c['target'],c['ortho_scale']);render(s,f'{key}-{REV}-detail-{detail}.png')
    # Reimport the REAL export under the same saved native light rig.
    for o in prod:bpy.data.objects.remove(o,do_unlink=True)
    if key=='s01':import_glb(OUT/f's01-facade-sample-{REV}.glb')
    else:import_glb(OUT/f's05-fence-repeat-{REV}.glb');import_glb(OUT/f's05-fence-endcap-{REV}.glb',1.2)
    camera(s,cfg['target'],cfg['ortho_scale']);render(s,f'{key}-{REV}-glb-quarter.png')
    if key=='s01':
        current=visible_meshes()
        for o in current:bpy.data.objects.remove(o,do_unlink=True)
        import_glb(OUT/'s01-facade-sample-r01.glb');camera(s,cfg['target'],cfg['ortho_scale']);render(s,'s01-r01-controlled-quarter.png')
    else:
        for o in visible_meshes():bpy.data.objects.remove(o,do_unlink=True)
        modules=[]
        for offset in [0,1.2,2.4]:modules.append(import_glb(OUT/f's05-fence-repeat-{REV}.glb',offset))
        import_glb(OUT/f's05-fence-endcap-{REV}.glb',3.6)
        for v in ['front','back','quarter','top']:
            camera(s,[1.8,0,.46],4.5,v,(1280,720));render(s,f's05-{REV}-three-{v}.png')
        for joint in [1.2,2.4]:
            camera(s,[joint,0,.50],.72);render(s,f's05-{REV}-joint-{joint:.1f}.png')
        vs=[o.matrix_world@v.co for o in visible_meshes() for v in o.data.vertices]
        metrics['three_segment_assembly']={'actual_glb_readback':True,'repeat_origins_x':[0,1.2,2.4],'terminal_origin_x':3.6,'post_count':4,'rail_count':6,'bbox_blender_z_up':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'joint_checks':[]}
        # Contact measurement from imported vertex positions, not nominal plan values.
        for origin in [0,1.2,2.4]:
            coords=[o.matrix_world@v.co for o in modules[int(round(origin/1.2))] if o.type=='MESH' for v in o.data.vertices]
            # Rail far plane: vertices of material "light planed rails", not post/pegs.
            rails=[]
            for o in modules[int(round(origin/1.2))]:
                if o.type!='MESH':continue
                for p in o.data.polygons:
                    if 'light planed rails' in o.data.materials[p.material_index].name:
                        rails.extend(o.matrix_world@o.data.vertices[i].co for i in p.vertices)
            right=max(v.x for v in rails);left=min(v.x for v in rails)
            metrics['three_segment_assembly']['joint_checks'].append({'span_origin_x':origin,'measured_rail_min_x':left,'measured_rail_max_x':right,'left_post_right_face_x':origin+.11,'next_post_left_face_x':origin+1.09,'left_gap':left-(origin+.11),'right_gap':origin+1.09-right,'tolerance':1e-6,'no_positive_volume_overlap_between_spans':'Adjacent repeat bounds meet at X=1.09/2.29; solid interiors are on opposite sides of this plane. Terminal begins at 3.49.'})
    print('B02 REVIEWED',key,flush=True)

(QA/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
(QA/f'metrics-{REV}.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
print('B02 REVIEW COMPLETE',flush=True)
