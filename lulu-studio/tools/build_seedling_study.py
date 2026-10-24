"""Independent Blender seedling route study; not a completed B08 batch.

Does not import old crop generators or alter mature Meshy files. Each leaf is
an authored continuous petiole/blade surface with Solidify and a small bevel.
"""
import bpy
import hashlib
import json
import math
import struct
from pathlib import Path
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "assets-source/seedling-studies/r01"
OUTPUT = PROJECT / "public/models/seedling-studies/r01"
REVIEW = PROJECT / "review/seedling-concepts-20261018/blender-study"
VIEWS = {"front": (0, -1, .025), "side": (1, 0, .025), "back": (0, 1, .025),
         "quarter": (1.35, -4, 2.25), "top": (0, -.001, 1)}
SCOPE = "仅三物种幼苗原生Blender路线研究，不是B08成品或用户美术通过；未替换成熟模型或改变Meshy主流程。"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def material(name, color, rough=.76):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    return m


def mesh_object(name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj['study_geometry'] = True
    return obj


def leaf_modifiers(obj, thickness):
    smooth = obj.modifiers.new('One level outline and surface relaxation', 'SUBSURF')
    smooth.levels = 1
    smooth.render_levels = 1
    solid = obj.modifiers.new('True leaf thickness - editable', 'SOLIDIFY')
    solid.thickness = thickness
    solid.offset = 0
    solid.use_even_offset = True
    solid.use_quality_normals = True
    bevel = obj.modifiers.new('Rounded leaf rim - restrained', 'BEVEL')
    bevel.width = thickness * .28
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = .65
    obj['continuous_leaf_and_petiole'] = True
    obj['floating_vein_geometry'] = False


def smoothstep(x):
    x = min(1., max(0., x))
    return x * x * (3 - 2 * x)


def profile_interpolate(s, knots):
    for i in range(len(knots) - 1):
        a, va = knots[i]; b, vb = knots[i + 1]
        if s <= b:
            t = smoothstep((s - a) / (b - a))
            return va * (1 - t) + vb * t
    return knots[-1][1]


def leaf(name, mat, azimuth, base_z, length, half_width, rise, droop,
         petiole=.21, cup=.006, thickness=.002, tomato_lobes=False, bend=.008,
         kind='dicot'):
    """A single surface runs from a narrow attached petiole into its blade."""
    nu, nv = (18, 4) if kind == 'corn' else ((8, 4) if kind == 'bud' else (14, 4))
    if tomato_lobes:
        nu = 12 if kind == 'bud' else 20
    az = math.radians(azimuth)
    along = Vector((math.cos(az), math.sin(az), 0))
    across = Vector((-math.sin(az), math.cos(az), 0))
    vertices = []
    for i in range(nu + 1):
        # Cluster sampling at both ends, so rounded tips do not become cut
        # polygons. A single low subdivision level then relaxes the outline.
        t = (1 - math.cos(math.pi * i / nu)) * .5
        s = max(0., (t - petiole) / (1 - petiole))
        if kind == 'corn':
            width = .002 + half_width * math.sin(math.pi * t) ** .78
            radial = length * (.18 * t + .82 * t * t)
            center_z = base_z + rise * math.sin(math.pi * .77 * t)
            blade_amount = math.sin(math.pi * t)
        else:
            if t <= petiole:
                width = .0023 * (1 + .25 * t / max(petiole, .01))
                blade_amount = 0
            else:
                if tomato_lobes:
                    shape = profile_interpolate(s, [(0, .08), (.12, .50), (.23, 1),
                        (.35, .40), (.49, 1.05), (.62, .43), (.76, .84), (.88, .35), (1, .025)])
                else:
                    shape = math.sin(math.pi * s) ** .58
                width = .0007 + half_width * shape + .0021 * (1 - smoothstep(s / .16))
                blade_amount = math.sin(math.pi * s)
            radial = length * (.35 * t + .65 * t * t)
            center_z = base_z + rise * t - droop * t ** 3
        center = along * radial + across * (bend * math.sin(math.pi * t))
        center.z = center_z
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            point = center + across * (width * v)
            # The shallow midrib and leaf's cupped arc belong to this surface.
            point.z += cup * blade_amount * v * v
            point.z += .0032 * blade_amount * math.exp(-(v / .24) ** 2)
            point.z += .0013 * blade_amount * v * math.sin(math.pi * t)
            vertices.append(tuple(point))
    faces = []
    for i in range(nu):
        for j in range(nv):
            p = i * (nv + 1) + j
            faces.append((p, p + nv + 1, p + nv + 2, p + 1))
    obj = mesh_object(name, vertices, faces, mat)
    leaf_modifiers(obj, thickness)
    return obj


def stem(name, mat, height, radius):
    vertices, faces = [], []
    rings, sides = 9, 12
    for i in range(rings):
        t = i / (rings - 1)
        r = radius * (1 - .30 * t) * (1 - .82 * smoothstep((t - .82) / .18))
        for j in range(sides):
            a = math.tau * j / sides
            vertices.append((r * math.cos(a) + .003 * math.sin(t * 2),
                             r * math.sin(a), height * t))
    for i in range(rings - 1):
        for j in range(sides):
            a = i * sides + j; b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces += [tuple(reversed(range(sides))), tuple((rings - 1) * sides + j for j in range(sides))]
    obj = mesh_object(name, vertices, faces, mat)
    bevel = obj.modifiers.new('Soft stem end', 'BEVEL')
    bevel.width = .0008 if radius >= .008 else .00025
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'; bevel.angle_limit = .8
    return obj


def corn_rolled_heart(mat):
    vertices, faces = [], []
    nu, nv = 14, 6
    for i in range(nu + 1):
        t = i / nu
        radius = .004 + .0025 * math.sin(math.pi * t / 2)
        opening = 2.15 * (1 - .84 * smoothstep((t - .68) / .32))
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            angle = .25 * t + opening * v
            vertices.append((radius * math.cos(angle) + .011 * t * t,
                             radius * math.sin(angle), .038 + .242 * t))
    for i in range(nu):
        for j in range(nv):
            p = i * (nv + 1) + j
            faces.append((p, p + 1, p + nv + 2, p + nv + 1))
    obj = mesh_object('Corn central rolled developing leaf', vertices, faces, mat)
    leaf_modifiers(obj, .0016)
    obj['monocot_whorl_not_two_cotyledons'] = True
    return obj


def create_seedling(slug):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if slug == 'cabbage':
        leafmat = material('Cabbage young leaf green', (.26, .49, .075))
        cotmat = material('Cabbage cotyledon green', (.33, .56, .11))
        stemmat = material('Cabbage short stalk', (.29, .47, .10))
        stem('Cabbage short stem', stemmat, .047, .009)
        leaf('Cabbage cotyledon left', cotmat, 128, .020, .078, .026, .026, .011, petiole=.24, cup=.004, thickness=.0030)
        leaf('Cabbage cotyledon right', cotmat, 310, .023, .074, .025, .024, .010, petiole=.25, cup=.004, thickness=.0030, bend=-.006)
        leaf('Cabbage broad true leaf A', leafmat, 42, .039, .108, .054, .144, .010, cup=.021, thickness=.0036)
        leaf('Cabbage broad true leaf B', leafmat, 223, .043, .100, .049, .133, .009, cup=.020, thickness=.0035, bend=-.010)
        leaf('Cabbage central developing small leaf',cotmat,122,.044,.031,.014,.054,.003,
             petiole=.17,cup=.005,thickness=.0027,kind='bud')
    elif slug == 'tomato':
        leafmat = material('Tomato young true leaf', (.12, .37, .055))
        cotmat = material('Tomato narrow cotyledon', (.25, .46, .075))
        stemmat = material('Tomato short sturdy green stem', (.24, .39, .075))
        stem('Tomato short sturdy stem', stemmat, .104, .0065)
        leaf('Tomato narrow cotyledon A', cotmat, 113, .035, .068, .0140, .031, .010, petiole=.20, cup=.004, thickness=.0027, bend=.002)
        leaf('Tomato narrow cotyledon B', cotmat, 293, .038, .064, .0135, .028, .009, petiole=.20, cup=.004, thickness=.0027, bend=-.002)
        leaf('Tomato shallow lobed true leaf A', leafmat, 30, .074, .102, .034, .112, .010, petiole=.26, cup=.011, thickness=.0030, tomato_lobes=True)
        leaf('Tomato shallow lobed true leaf B', leafmat, 205, .083, .092, .031, .108, .008, petiole=.24, cup=.010, thickness=.0030, tomato_lobes=True, bend=-.004)
        leaf('Tomato central developing true leaf',leafmat,113,.095,.061,.021,.124,.007,
             petiole=.20,cup=.007,thickness=.0025,tomato_lobes=True,kind='bud')
    elif slug == 'corn':
        leafmat = material('Corn long young leaf', (.23, .45, .055))
        innermat = material('Corn central new leaf', (.36, .58, .085))
        stemmat = material('Corn basal sheath', (.29, .47, .075))
        stem('Corn young basal sheath', stemmat, .062, .007)
        leaf('Corn first arched long blade', leafmat, 188, .008, .142, .023, .255, 0, petiole=.08, cup=.004, thickness=.0021, kind='corn', bend=-.009)
        leaf('Corn second unequal arched blade', leafmat, 20, .020, .116, .021, .215, 0, petiole=.08, cup=.0045, thickness=.0020, kind='corn', bend=.004)
        corn_rolled_heart(innermat)
    else:
        raise ValueError(slug)
    scene = bpy.context.scene
    scene['study_scope'] = SCOPE
    scene['stage'] = 'seedling'
    scene['grid_cell_size'] = 1.2
    scene['native_authored_geometry'] = True
    scene['mature_model_used_as_geometry'] = False
    scene['species'] = slug
    scene['iteration'] = 'refined-2-outline' if slug == 'tomato' else 'refined-1'
    text = bpy.data.texts.new('README - seedling route study')
    text.write(SCOPE + '\n叶面、叶柄连续参数曲面；Solidify真厚度、细小Bevel圆边；中脉直接在曲面中。\n没有成熟花果、土台或纹理。\n')
    return [o for o in scene.objects if o.get('study_geometry')]


def bounds(objects):
    bpy.context.view_layer.update()
    dep = bpy.context.evaluated_depsgraph_get()
    points = []
    for obj in objects:
        evaluated = obj.evaluated_get(dep)
        points += [evaluated.matrix_world @ Vector(c) for c in evaluated.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return lo, hi


def inspection_setup():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
    scene.cycles.samples = 16; scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0; scene.view_settings.gamma = 1
    scene.world = bpy.data.worlds.new('B01 neutral studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.78, .80, .75, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .32
    for label, loc, power, size in [('Key',(-3,-4,6),280,4), ('Fill',(4,-1,3),140,3), ('Rim',(0,4,5),230,3)]:
        data=bpy.data.lights.new(label,'AREA');obj=bpy.data.objects.new(label,data)
        scene.collection.objects.link(obj);obj.location=loc
        obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
        data.energy=power;data.shape='DISK';data.size=size
    groundmat = material('QA ground only', (.905,.888,.815), 1)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.0007))
    bpy.context.object.name='QA ground - never exported';bpy.context.object.data.materials.append(groundmat)
    data=bpy.data.cameras.new('Fixed study camera')
    obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);scene.camera=obj
    data.type='ORTHO';data.ortho_scale=.44
    set_camera('quarter')


def set_camera(view):
    scene=bpy.context.scene;target=Vector((0,0,.14))
    scene.camera.location=target+Vector(VIEWS[view]).normalized()*6
    scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()


def glb_json(path):
    data=path.read_bytes()
    length=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+length])


def check_glb(path):
    document=glb_json(path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    lo,hi=bounds(objects)
    bad=zero=boundaries=0
    import bmesh
    for obj in objects:
        bad+=sum(not all(math.isfinite(c) for c in vertex.co) for vertex in obj.data.vertices)
        zero+=sum(face.area < 1e-12 for face in obj.data.polygons)
        bm=bmesh.new();bm.from_mesh(obj.data)
        boundaries+=sum(edge.is_boundary for edge in bm.edges)
        bm.free()
    triangles=sum(document['accessors'][p['indices']]['count']//3 for m in document.get('meshes',[]) for p in m['primitives'])
    return {'bytes':path.stat().st_size,'sha256':sha(path),'triangles':triangles,
        'mesh_nodes':len(objects),'materials':len(document.get('materials',[])),
        'textures':len(document.get('images',[])),'bounds_z_up':[list(lo),list(hi)],
        'size':[b-a for a,b in zip(lo,hi)],'nonfinite_vertices':bad,'zero_area_faces':zero,
        'boundary_edges':boundaries,'roundtrip_import':'success',
        'external_uris':[i['uri'] for i in document.get('images',[]) if 'uri' in i]}


def main():
    for folder in (SOURCE,OUTPUT,REVIEW):folder.mkdir(parents=True,exist_ok=True)
    metrics={}
    for slug in ['cabbage','tomato','corn']:
        source=SOURCE/f'{slug}-seedling.blend';output=OUTPUT/f'{slug}-seedling.glb'
        all_views_present=all((REVIEW/f'{slug}-r01-{mode}-{view}.png').exists()
            for mode in ['material','clay'] for view in VIEWS)
        reuse_complete=source.exists() and output.exists() and all_views_present
        if not reuse_complete:
            assert not source.exists() and not output.exists(), f'Refuse to overwrite incomplete study {slug}'
            production=create_seedling(slug)
            lo,hi=bounds(production)
            assert .16 <= hi.z <= .32, (slug,list(lo),list(hi))
            for obj in bpy.context.scene.objects:obj.select_set(False)
            for obj in production:obj.select_set(True)
            bpy.context.view_layer.objects.active=production[0]
            bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,
                export_apply=True,export_yup=True,export_materials='EXPORT',export_extras=True)
            inspection_setup()
            bpy.context.preferences.filepaths.save_version=0
            bpy.ops.wm.save_as_mainfile(filepath=str(source),check_existing=False,compress=True)
        metrics[slug]=check_glb(output)
        assert metrics[slug]['nonfinite_vertices']==0 and metrics[slug]['zero_area_faces']==0
        assert metrics[slug]['materials']<=4 and metrics[slug]['triangles']<10000
        bpy.ops.wm.open_mainfile(filepath=str(source))
        production=[o for o in bpy.context.scene.objects if o.get('study_geometry')]
        assert production and all(o.type=='MESH' for o in production)
        leaf_objects=[o for o in production if o.get('continuous_leaf_and_petiole')]
        assert leaf_objects and all(any(m.type=='SOLIDIFY' for m in o.modifiers) for o in leaf_objects)
        metrics[slug].update({'source':str(source.relative_to(PROJECT)),'source_sha256':sha(source),
            'source_reopened':'success','editable_solidify_leaves':len(leaf_objects),
            'scope':SCOPE,'revision':'r01','stage':'seedling','world_scale':1,'grid_cell':1.2})
        if reuse_complete:
            (REVIEW/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
            print('REVALIDATED COMPLETE STUDY',slug,flush=True)
            continue
        for view in VIEWS:
            set_camera(view);bpy.context.scene.render.filepath=str(REVIEW/f'{slug}-r01-material-{view}.png')
            bpy.ops.render.render(write_still=True)
        gray=material('Neutral diagnostic clay',(.38,.38,.38),.85)
        for obj in production:
            obj.data.materials.clear();obj.data.materials.append(gray)
        for view in VIEWS:
            set_camera(view);bpy.context.scene.render.filepath=str(REVIEW/f'{slug}-r01-clay-{view}.png')
            bpy.ops.render.render(write_still=True)
        (REVIEW/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
        print('SEEDLING STUDY COMPLETE',slug,metrics[slug]['triangles'],flush=True)
    settings={'scope':SCOPE,'revision':'r01','cell':1.2,'author_scale':1,
      'renderer':'Cycles CPU 16 samples denoise, 4 threads','resolution':[768,768],
      'color':{'view':'Standard','look':'None','exposure':0,'gamma':1},
      'world':{'color':[.78,.80,.75],'strength':.32},'lights':'Exact B01 review-settings positions/powers/sizes',
      'views':VIEWS,'camera_target':[0,0,.14],'ortho_scale':.44,'shared_camera_for_all_species':True,
      'materials_and_clay':True,'rendered_from':'Reopened native Blender sources after GLB roundtrip check',
      'not_complete_batch_acceptance':True}
    (REVIEW/'review-settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n')
    print('ALL THREE SEEDLING STUDIES COMPLETE',flush=True)


if __name__=='__main__':main()
