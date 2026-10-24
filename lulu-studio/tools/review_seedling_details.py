"""Read-only material/clay connection close-ups of current Meshy seedlings.

Blender --background --python tools/review_seedling_details.py renders 56 PNGs
in one process. Only inspection PNG/JSON files are written; no asset is saved
or exported and no generator entry point is invoked.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review/seedling-meshy-mapping-20261018'
MANIFEST = ROOT / 'public/models/crop-two-stage/manifest.json'
SPEC = importlib.util.spec_from_file_location('read_only_seedling_detail_qa', ROOT / 'tools/build_seedling_study.py')
QA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QA)  # The module's main() guard prevents generation.


def asset_path(url):
    path = (ROOT / 'public' / url.lstrip('/')).resolve()
    assert path.is_relative_to((ROOT / 'public/models').resolve()), f'Unexpected asset path: {url}'
    assert path.is_file(), f'Missing inspection input: {path}'
    return path


def load_plant(entry):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(asset_path(entry['file'])))
    imported = set(bpy.context.scene.objects) - before
    roots = [o for o in imported if o.parent not in imported]
    meshes = [o for o in imported if o.type == 'MESH']
    assert roots and meshes
    for obj in roots:
        obj.scale *= entry['scale']
    lo, hi = QA.bounds(meshes)
    offset = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    for obj in roots:
        obj.location += offset
    bpy.context.view_layer.update()
    lo, hi = QA.bounds(meshes)
    assert abs(lo.z) < 1e-5
    return meshes, [list(lo), list(hi)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crop', nargs='+', help='Inspect only the named crops.')
    parser.add_argument('--candidate-only', action='store_true', help='Reuse original details and render only each current candidate.')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    crops = json.loads(MANIFEST.read_text())['crops']
    assert len(crops) == 14
    if args.crop:
        requested = set(args.crop)
        crops = [crop for crop in crops if crop['id'] in requested]
        assert {crop['id'] for crop in crops} == requested, 'Unknown crop requested'
    rendered = 0
    for crop in crops:
        slug = crop['id']
        settings = json.loads((REVIEW / slug / 'review-settings.json').read_text())
        target = list(settings['target'])
        target[2] = float(settings['world_height']) * .62
        ortho = float(settings['height']) * .60
        pinned_camera = None
        original_details = REVIEW / slug / 'original/detail-settings.json'
        if args.candidate_only and original_details.is_file():
            # A later source build can slightly alter derived bounds by roundoff.
            # Reuse the original image's recorded camera exactly for true A/B.
            pinned_camera = json.loads(original_details.read_text())['camera']
            target = list(pinned_camera['target_z_up'])
            ortho = float(pinned_camera['ortho_scale'])
        current = crop.get('defaultSeedlingVersion', 'meshy-toon-r01')
        variants = [(current, current)] if args.candidate_only else [('original', 'meshy-original'), (current, current)]
        for folder_name, version in variants:
            entry = crop['seedling'][version]
            if version != 'meshy-original':
                assert entry['scale'] == 1
            paths = {asset_path(entry['file'])}
            if entry.get('source'):
                paths.add(asset_path(entry['source']))
            before = {str(p.relative_to(ROOT)): QA.sha(p) for p in paths}
            bpy.ops.wm.read_factory_settings(use_empty=True)
            meshes, bounds = load_plant(entry)
            QA.inspection_setup()
            scene = bpy.context.scene
            scene.render.resolution_x = scene.render.resolution_y = 768
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = 'PNG'
            scene.render.image_settings.color_mode = 'RGBA'
            scene.camera.data.ortho_scale = ortho
            scene.camera.location = Vector(target) + Vector(QA.VIEWS['quarter']).normalized() * 30
            scene.camera.rotation_euler = (Vector(target) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
            folder = REVIEW / slug / folder_name
            folder.mkdir(parents=True, exist_ok=True)
            for mode in ['material', 'clay']:
                if mode == 'clay':
                    gray = QA.material('Neutral close-up geometry gray', (.38, .38, .38), .85)
                    for obj in meshes:
                        obj.data.materials.clear()
                        obj.data.materials.append(gray)
                scene.render.filepath = str(folder / f'{mode}-detail.png')
                bpy.ops.render.render(write_still=True)
                rendered += 1
                print(f'COMPLETE detail {slug} {version} {mode}', flush=True)
            after = {str(p.relative_to(ROOT)): QA.sha(p) for p in paths}
            assert before == after, f'Input changed: {slug} {version}'
            record = {
                'crop': slug,
                'code': crop['code'],
                'name': crop['name'],
                'version': version,
                'input_file': entry['file'],
                'input_scale': entry['scale'],
                'family': entry.get('family'),
                'purpose': '关键局部：茎叶连接、叶缘厚度和中脉。允许外叶尖被局部取景截断；不是整株轮廓图。',
                'camera': {'target_z_up': target, 'ortho_scale': ortho,
                           'quarter_direction_z_up': list(QA.VIEWS['quarter']),
                           'position': list(scene.camera.location),
                           'original_and_candidate_shared': True,
                           'formula': 'target.z=world_height*0.62; ortho=review_settings.height*0.60'},
                'based_on': str((REVIEW / slug / 'review-settings.json').relative_to(ROOT)),
                'exact_camera_reused_from': str(original_details.relative_to(ROOT)) if pinned_camera else None,
                'resolution': [768, 768],
                'renderer': 'Cycles CPU 16 samples, denoising, 4 threads',
                'color': {'view': 'Standard', 'look': 'None', 'exposure': 0, 'gamma': 1},
                'lights': 'Exact B01 world/area positions, powers and sizes via guarded inspection_setup()',
                'bounds_z_up': bounds,
                'material_file': str((folder / 'material-detail.png').relative_to(ROOT)),
                'clay_file': str((folder / 'clay-detail.png').relative_to(ROOT)),
                'input_sha256_before': before,
                'input_sha256_after': after,
                'input_preservation': 'pass',
                'model_file_mutations': False,
                'user_art_acceptance': 'pending',
                'device_performance': 'not_tested',
            }
            (folder / 'detail-settings.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    assert rendered == len(crops) * (2 if args.candidate_only else 4), rendered
    print(f'COMPLETE ALL seedling-details {rendered}', flush=True)


if __name__ == '__main__':
    main()
