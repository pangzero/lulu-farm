"""Render current Meshy seedling/mature pairs at their actual shared world scale.

Run with Blender --background --python this_file -- [--crop SLUG].
This inspection-only script imports GLBs and writes PNG/JSON evidence. It never
saves a Blender project, exports a GLB, or executes a crop generator.
"""
import argparse
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review/seedling-meshy-mapping-20261018'
MANIFEST_PATH = ROOT / 'public/models/crop-two-stage/manifest.json'
SPEC = importlib.util.spec_from_file_location('seedling_pair_qa_helpers', ROOT / 'tools/build_seedling_study.py')
QA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QA)  # main() is guarded; no generation is executed.

CAMERA_TARGET = (0, 0, .5)
CAMERA_HEIGHT = 2.6
POSITIONS = {'seedling': (-.6, 0, 0), 'mature': (.6, 0, 0)}


def public_file(url):
    path = (ROOT / 'public' / url.lstrip('/')).resolve()
    assert path.is_relative_to((ROOT / 'public/models').resolve()), f'Unexpected model path: {url}'
    assert path.is_file(), f'Missing GLB: {path}'
    return path


def import_for_inspection(entry, stage):
    """Track only this import's objects; move its root as a complete hierarchy."""
    path = public_file(entry['file'])
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = set(bpy.context.scene.objects) - before
    meshes = [o for o in imported if o.type == 'MESH']
    roots = [o for o in imported if o.parent not in imported]
    assert meshes and roots, f'No usable mesh/root for {stage}: {path}'
    scale = float(entry.get('scale', 1))
    assert math.isfinite(scale) and scale > 0
    # Both current derivative entries contain the authored world scale already.
    assert scale == 1, f'Do not normalize derivative scale: {stage} {scale}'
    for obj in roots:
        obj.scale *= scale
    lo, hi = QA.bounds(meshes)
    shift = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    placement = Vector(POSITIONS[stage])
    for obj in roots:
        obj.location += shift + placement
    bpy.context.view_layer.update()
    placed_lo, placed_hi = QA.bounds(meshes)
    assert abs(placed_lo.z) < 1e-5, (stage, list(placed_lo))
    return meshes, {
        'entry_file': entry['file'],
        'file_sha256': QA.sha(path),
        'version': None,
        'label': entry['label'],
        'scale': scale,
        'placement': list(placement),
        'ground_centre_shift': list(shift),
        'height': placed_hi.z - placed_lo.z,
        'bounds_before_placement_z_up': [list(lo), list(hi)],
        'bounds_placed_z_up': [list(placed_lo), list(placed_hi)],
        'family': entry.get('family'),
        'mapping_note': entry.get('mappingNote'),
        'review_status': entry.get('reviewStatus'),
        'mesh_nodes': len(meshes),
    }


def make_soil():
    material = QA.material('QA separate soil cells', (.33, .20, .10), 1)
    for stage, position in POSITIONS.items():
        bpy.ops.mesh.primitive_cube_add(size=1, location=(position[0], position[1], -.035))
        obj = bpy.context.object
        obj.name = f'QA soil only - {stage}'
        obj.dimensions = (1.14, 1.14, .07)
        obj.data.materials.append(material)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name.startswith('QA ground'):
            obj.location.z = -.071


def render_pair(crop):
    slug = crop['id']
    seedling_version = crop.get('defaultSeedlingVersion', 'meshy-toon-r01')
    seedling = crop['seedling'][seedling_version]
    mature_version = 'game-r02' if slug in {'cabbage', 'tomato', 'corn', 'rose'} else 'game-r01'
    mature = crop['mature'][mature_version]
    # Hash the imported derivatives AND their preserved original Meshy inputs.
    inputs = {public_file(e['file']) for e in [seedling, mature, crop['mature']['original']]}
    if seedling.get('originalFile'):
        inputs.add(public_file(seedling['originalFile']))
    hashes_before = {str(p.relative_to(ROOT)): QA.sha(p) for p in inputs}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    seed_meshes, seed_record = import_for_inspection(seedling, 'seedling')
    seed_record['version'] = seedling_version
    mature_meshes, mature_record = import_for_inspection(mature, 'mature')
    mature_record['version'] = mature_version
    QA.inspection_setup()
    make_soil()
    scene = bpy.context.scene
    target = Vector(CAMERA_TARGET)
    scene.camera.data.ortho_scale = CAMERA_HEIGHT
    scene.camera.location = target + Vector(QA.VIEWS['quarter']).normalized() * 30
    scene.camera.rotation_euler = (target - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    folder = REVIEW / slug
    folder.mkdir(parents=True, exist_ok=True)
    previous_settings = folder / 'stage-pair-settings.json'
    previous_image = folder / 'stage-pair.png'
    if previous_settings.is_file():
        previous_version = json.loads(previous_settings.read_text())['seedling']['version']
        if previous_version != seedling_version:
            tag = previous_version.removeprefix('meshy-toon-')
            for old, backup in [(previous_image, folder / f'stage-pair-{tag}.png'),
                                (previous_settings, folder / f'stage-pair-{tag}.json')]:
                assert old.is_file(), f'Incomplete previous evidence: {old}'
                if backup.exists():
                    assert QA.sha(backup) == QA.sha(old), f'Refuse to replace different historical evidence: {backup}'
                else:
                    shutil.copy2(old, backup)
    scene.render.filepath = str(folder / 'stage-pair.png')
    bpy.ops.render.render(write_still=True)
    hashes_after = {str(p.relative_to(ROOT)): QA.sha(p) for p in inputs}
    assert hashes_before == hashes_after, f'Read-only input unexpectedly changed: {slug}'
    settings = {
        'crop': slug,
        'code': crop['code'],
        'name': crop['name'],
        'evidence': str((folder / 'stage-pair.png').relative_to(ROOT)),
        'purpose': '幼苗与当前成熟卡通优化候选同世界尺度并置；左幼苗／右成熟。不是用户美术认可。',
        'seedling': seed_record,
        'mature': mature_record,
        'camera': {'target_z_up': list(CAMERA_TARGET), 'ortho_scale': CAMERA_HEIGHT,
                   'direction_z_up': list(QA.VIEWS['quarter']), 'position': list(scene.camera.location),
                   'same_for_all_species': True, 'normalization': False},
        'soil': {'cell': 1.2, 'geometry': [1.14, 1.14, .07], 'top_z': 0, 'separate_from_models': True},
        'resolution': [768, 768],
        'renderer': 'Cycles CPU, 16 samples, denoising, 4 threads',
        'color': {'view': 'Standard', 'look': 'None', 'exposure': 0, 'gamma': 1},
        'world': {'color': [.78, .80, .75], 'strength': .32},
        'lights': {'key': {'location': [-3, -4, 6], 'power': 280, 'size': 4},
                   'fill': {'location': [4, -1, 3], 'power': 140, 'size': 3},
                   'rim': {'location': [0, 4, 5], 'power': 230, 'size': 3}},
        'model_mutations': False,
        'inputs_sha256_before': hashes_before,
        'inputs_sha256_after': hashes_after,
        'input_preservation': 'pass',
        'user_art_status': 'pending',
        'device_performance': 'not_tested',
    }
    (folder / 'stage-pair-settings.json').write_text(json.dumps(settings, ensure_ascii=False, indent=2) + '\n')
    print(f'COMPLETE stage-pair {slug}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crop', nargs='+', help='Render the named crops; omitting it renders all 14.')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    manifest = json.loads(MANIFEST_PATH.read_text())
    crops = manifest['crops']
    assert len(crops) == 14 and len({c['id'] for c in crops}) == 14
    if args.crop:
        requested = set(args.crop)
        crops = [c for c in crops if c['id'] in requested]
        assert {c['id'] for c in crops} == requested, 'Unknown crop requested'
    for crop in crops:
        render_pair(crop)
    print(f'COMPLETE ALL stage-pairs {len(crops)}', flush=True)


if __name__ == '__main__':
    main()
