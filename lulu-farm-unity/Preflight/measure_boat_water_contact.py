#!/usr/bin/env python3
"""Read-only S08 hull/floor measurement; no Unity or asset writes. Evidence only."""
import hashlib
import json
import pathlib
import sys
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Tools'))
from contact_preflight import triangles_from_glb

registry = json.loads((ROOT / 'Assets/Farm/Data/asset-registry.json').read_text())
record = next(a for a in registry['assets'] if a['id'] == 'S08')
# Exact serialized VisualAdapter from the currently imported S08.prefab.
scale = .8962987
offset = np.array([-.00022138725, .30042514, .00077522936])
root_position = np.array([10.9, -.22, -1.0])
yaw = np.deg2rad(25)
rotation = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
water = -.105
variants = [('LOD0', record['importSource']), ('LOD1', record['lodImports'][0]['importSource'])]
result = []
for label, source in variants:
    source = pathlib.Path(source)
    t = triangles_from_glb(source) * scale + offset
    a, b, c = t[:, 0], t[:, 1], t[:, 2]
    e, f = b-a, c-a
    den = e[:, 0]*f[:, 2] - f[:, 0]*e[:, 2]
    good = np.abs(den) > 1e-12
    def vertical_hits(x, z):
        uu = np.zeros(len(a)); vv = np.zeros(len(a))
        uu[good] = ((x-a[good, 0])*f[good, 2]-f[good, 0]*(z-a[good, 2]))/den[good]
        vv[good] = (e[good, 0]*(z-a[good, 2])-(x-a[good, 0])*e[good, 2])/den[good]
        valid = good & (uu >= -1e-7) & (vv >= -1e-7) & (uu+vv <= 1+1e-7)
        ys = np.sort(a[valid, 1]+uu[valid]*e[valid, 1]+vv[valid]*f[valid, 1])
        unique = []
        for y in ys:
            if not unique or y-unique[-1] > 1e-5: unique.append(float(y))
        return unique
    samples = []
    for x in np.arange(-.72, .551, .01):
        for z in np.arange(-.30, .301, .01):
            hits = vertical_hits(x, z)
            # A vertical ray crosses the external hull underside, then the inner wooden floor.
            # Further intersections, if present, are seat undersides and seat tops.
            if len(hits) >= 2 and hits[0] < .08 and .05 < hits[1] < .24:
                world = np.array([x, hits[1], z]) @ rotation.T + root_position
                samples.append({'root_local_xz': [float(x), float(z)], 'outer_local_y': hits[0],
                    'inner_local_y': hits[1], 'world_inner_xyz': world.tolist(), 'all_local_hits_y': hits})
    minimum = min(samples, key=lambda p: p['inner_local_y'])
    probes = [{'root_local_xz': [x,z], 'local_hits_y': vertical_hits(x,z),
               'current_world_hits_y': [y + root_position[1] for y in vertical_hits(x,z)]}
              for x,z in [(-.65,0),(-.45,0),(-.2,0),(0,0),(.10,0),(.25,0),(.45,0),(0,-.2),(0,.2)]]
    result.append({'lod': label, 'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'root_local_bounds': [t.min((0,1)).tolist(),t.max((0,1)).tolist()],
        'floor_samples': len(samples), 'minimum_sample': minimum,
        'floor_local_y_percentiles': np.percentile([p['inner_local_y'] for p in samples], [0,1,5,50,95,100]).tolist(),
        'visible_floor_below_current_water_samples': sum(p['world_inner_xyz'][1] < water for p in samples),
        'floor_current_min_world_y': minimum['world_inner_xyz'][1],
        'probes': probes})
floor_min = min(r['minimum_sample']['inner_local_y'] for r in result)
outer_min = min(r['root_local_bounds'][0][1] for r in result)
min_root_y = water - floor_min
recommended = min_root_y + .006
report = {'scope': 'Read-only GLB geometric preflight using actual prefab adapter, not an executed Unity contact check.',
    'asset': 'S08', 'prefab': str(ROOT/'Assets/Farm/Prefabs/S08.prefab'),
    'adapter_scale': scale, 'adapter_offset': offset.tolist(), 'normalized_height': .6,
    'current_root_position': root_position.tolist(), 'yaw_degrees': 25, 'water_world_y': water,
    'method': 'Vertical triangle intersections on a 0.01-unit root-local XZ grid over visible inner hull. First surface is underside; second is inner floor; further hits can be seat planks. Both existing LODs use the same serialized adapter.',
    'variants': result, 'minimum_root_y_to_clear_sampled_floor': min_root_y,
    'recommended_root_y_with_6mm_clearance': recommended,
    'recommended_lift_from_current': recommended-root_position[1],
    'outer_bottom_world_y_after_recommended_lift': outer_min+recommended,
    'remaining_draft_after_recommended_lift': water-(outer_min+recommended),
    'recommendation': 'Raise only the S08 scene root to the stated Y, retain X/Z/yaw/scale/source geometry. Re-render identical dock and opposite-side views at both LODs; verify no water in hull and no floating underside. This small lift is preferable to a water mask if visual checks pass.',
    'water_mask_fallback': 'Only if preserving original draft is required, carve/mask the horizontal water plane within a measured hull cross-section at water height; use source hull footprint, not a large rectangle or a global water lowering. No mask is implemented here.',
    'limitations': ['Grid extrema are sampled, not an exact continuous global minimum proof. Six millimetres of positive clearance provides modest sampling/rendering margin.', 'Visual hull contact and both LODs still require actual Unity verification.', 'No source or scene is modified by this script.']}
output = ROOT/'Preflight/boat-water-contact-measurements-20261023.json'
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['minimum_root_y_to_clear_sampled_floor','recommended_root_y_with_6mm_clearance','recommended_lift_from_current','remaining_draft_after_recommended_lift']},indent=2))
for r in result: print(r['lod'], r['floor_samples'], r['minimum_sample'])
