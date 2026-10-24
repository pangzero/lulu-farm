"""Make a viewer-portable copy of a Lulu GLB: no vertex colours (COLOR_0).

macOS Preview / Quick Look / AR Quick Look (USDZ conversion) ignore COLOR_0, so
vertex-coloured parts render white. This copy:
  * uniform parts (body, arms, legs, shorts) -> material baseColorFactor = their (uniform) vertex colour
  * crown fruit -> split into orange / leaf-green primitives by vertex colour
  * head (non-face part) + neck (colour gradients) -> cylindrical-projection UV + baked colour texture
Geometry and every other attribute are unchanged; the face/eye textures are kept.
Usage: python3 tools/make_portable_glb.py <in.glb> <out.glb>
"""
import sys, json, struct, copy, io, importlib.util
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('clh', R / 'tools/color_lulu_hybrid.py')
clh = importlib.util.module_from_spec(spec); spec.loader.exec_module(clh)


def to_srgb(c): return np.where(c <= .0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, 1), 1 / 2.4) - .055)


def write_glb(path, g, b):
    b = bytearray(b); b += b'\0' * ((-len(b)) % 4); g['buffers'][0]['byteLength'] = len(b)
    js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(js) + len(b)) + struct.pack('<II', len(js), 0x4e4f534a) + js + struct.pack('<II', len(b), 0x004e4942) + b)


def main(src, dst, wrap_png=None):
    g, b = clh.load(Path(src)); W = clh.worlds(g)

    def buf(raw):
        b.extend(b'\0' * ((-len(b)) % 4)); i = len(g['bufferViews'])
        g['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(raw)}); b.extend(raw); return i

    def acc(a, typ, comp=5126):
        dt = {5126: '<f4', 5125: '<u4'}[comp]; a = np.ascontiguousarray(a, dtype=dt); i = len(g['accessors'])
        g['accessors'].append({'bufferView': buf(a.tobytes()), 'componentType': comp, 'count': len(a), 'type': typ}); return i

    def material(name, rgb_lin=None, tex=None):
        pbr = {'roughnessFactor': .87, 'metallicFactor': 0}
        if rgb_lin is not None: pbr['baseColorFactor'] = [float(x) for x in rgb_lin] + [1]
        if tex is not None: pbr['baseColorTexture'] = {'index': tex}
        g['materials'].append({'name': name, 'pbrMetallicRoughness': pbr}); return len(g['materials']) - 1

    # ---- collect gradient parts (head non-face prim + neck) for the wrap texture
    wrap_parts = []
    for ni, n in enumerate(g['nodes']):
        if n.get('name') in ('Lulu_Head_Mirrored', 'Neck_Transition'):
            M = W[ni]
            for pr in g['meshes'][n['mesh']]['primitives']:
                if 'COLOR_0' in pr['attributes']:
                    P = clh.accessor(g, b, pr['attributes']['POSITION']) @ M[:3, :3].T + M[:3, 3]
                    C = clh.accessor(g, b, pr['attributes']['COLOR_0'])[:, :3]
                    wrap_parts.append((pr, P, C))
    allP = np.vstack([p for _, p, _ in wrap_parts]); allC = np.vstack([c for _, _, c in wrap_parts])
    cx, cz = 0.0, float(np.median(allP[:, 2]))
    y0, y1 = float(allP[:, 1].min()) - .01, float(allP[:, 1].max()) + .01
    TW, TH = 2048, 1024

    def wrap_uv(P):
        th = np.arctan2(P[:, 0] - cx, P[:, 2] - cz)  # 0 = front
        return np.c_[(th + np.pi) / (2 * np.pi), (y1 - P[:, 1]) / (y1 - y0)]

    uv = wrap_uv(allP); ix = np.clip((uv[:, 0] * (TW - 1)).round().astype(int), 0, TW - 1); iy = np.clip((uv[:, 1] * (TH - 1)).round().astype(int), 0, TH - 1)
    rad = np.hypot(allP[:, 0] - cx, allP[:, 2] - cz)
    # outermost surface wins per texel (what is seen from outside)
    order = np.argsort(rad); img = np.zeros((TH, TW, 3)); have = np.zeros((TH, TW), bool)
    img[iy[order], ix[order]] = to_srgb(allC[order]); have[iy[order], ix[order]] = True
    # fill holes by repeated neighbour averaging (dilation)
    for _ in range(200):
        if have.all(): break
        acc_c = np.zeros_like(img); cnt = np.zeros((TH, TW))
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            sh = np.roll(np.roll(have, dy, 0), dx, 1); acc_c += np.roll(np.roll(img, dy, 0), dx, 1) * sh[..., None]; cnt += sh
        new = (~have) & (cnt > 0); img[new] = acc_c[new] / cnt[new, None]; have |= new
    # light blur to remove splat noise (separable box 3)
    for ax in (0, 1):
        img = (np.roll(img, 1, ax) + img + np.roll(img, -1, ax)) / 3
    im = Image.fromarray(np.uint8(np.clip(img, 0, 1) * 255 + .5)); bio = io.BytesIO(); im.save(bio, 'PNG')
    if wrap_png: im.save(wrap_png)
    ii = len(g['images']); g['images'].append({'name': 'body-wrap-basecolor.png', 'mimeType': 'image/png', 'bufferView': buf(bio.getvalue())})
    sm = len(g['samplers']); g['samplers'].append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 33071})
    ti = len(g['textures']); g['textures'].append({'source': ii, 'sampler': sm})
    wrap_mat = material('Lulu skin/muzzle wrap (portable)', tex=ti)
    seam_fixed = 0
    for pr, P, C in wrap_parts:
        # own copies of the vertex attributes, so seam vertices can be duplicated (u + 1, sampler repeats)
        Pl = clh.accessor(g, b, pr['attributes']['POSITION']); Nl = clh.accessor(g, b, pr['attributes']['NORMAL'])
        f = clh.accessor(g, b, pr['indices']).reshape(-1, 3).astype(np.int64)
        u = wrap_uv(P)
        span = u[f, 0].max(1) - u[f, 0].min(1); cross = span > .5
        dup = {}; Pn = [Pl]; Nn = [Nl]; Un = [u]; n0 = len(Pl)
        fc = f[cross]
        for k in range(len(fc)):
            for j in range(3):
                v = int(fc[k, j])
                if u[v, 0] < .5:
                    if v not in dup: dup[v] = n0 + len(dup)
                    fc[k, j] = dup[v]
        f[cross] = fc
        if dup:
            ids = np.array(list(dup.keys())); Pn.append(Pl[ids]); Nn.append(Nl[ids]); Un.append(u[ids] + [1, 0])
        seam_fixed += int(cross.sum())
        pr['attributes']['POSITION'] = acc(np.vstack(Pn), 'VEC3'); g['accessors'][-1]['min'] = np.vstack(Pn).min(0).tolist(); g['accessors'][-1]['max'] = np.vstack(Pn).max(0).tolist()
        pr['attributes']['NORMAL'] = acc(np.vstack(Nn), 'VEC3')
        pr['attributes']['TEXCOORD_0'] = acc(np.vstack(Un), 'VEC2')
        pr['indices'] = acc(f.reshape(-1, 1), 'SCALAR', 5125)
        pr['attributes'].pop('COLOR_0'); pr['material'] = wrap_mat

    report = {'wrap_texture': [TW, TH], 'parts': {}}
    for ni, n in enumerate(g['nodes']):
        if 'mesh' not in n: continue
        mesh = g['meshes'][n['mesh']]; new = []
        for pr in mesh['primitives']:
            if 'COLOR_0' not in pr['attributes']: new.append(pr); continue
            C = clh.accessor(g, b, pr['attributes']['COLOR_0'])[:, :3]
            if n['name'] == 'Original_Crown_Ornament':
                f = clh.accessor(g, b, pr['indices']).reshape(-1, 3); green = C[:, 1] > C[:, 0]
                leaf = green[f].sum(1) >= 2
                for sel, nm in [(~leaf, 'fruit orange'), (leaf, 'fruit leaf')]:
                    col = C[np.unique(f[sel])].mean(0) if nm == 'fruit orange' else C[green].mean(0)
                    if nm == 'fruit orange': col = C[~green].mean(0)
                    p2 = copy.deepcopy(pr); p2['attributes'].pop('COLOR_0'); p2['indices'] = acc(f[sel].reshape(-1, 1), 'SCALAR', 5125)
                    p2['material'] = material(f'Lulu {nm} (portable)', col); new.append(p2)
                report['parts'][n['name']] = 'split orange/leaf'
            else:
                col = C.mean(0); spread = float(np.abs(C - col).max())
                p2 = copy.deepcopy(pr); p2['attributes'].pop('COLOR_0'); p2['material'] = material(f'Lulu {n["name"]} (portable)', col); new.append(p2)
                report['parts'].setdefault(n['name'], []).append(round(spread, 4))
        mesh['primitives'] = new
    left = sum('COLOR_0' in p['attributes'] for m in g['meshes'] for p in m['primitives'])
    report['primitives_with_COLOR_0_left'] = left
    g.setdefault('extras', {})['portable'] = 'Vertex colours converted to materials/textures for viewers that ignore COLOR_0 (macOS Preview/Quick Look/USDZ).'
    write_glb(dst, g, b); print(json.dumps(report, indent=1, ensure_ascii=False)); return left == 0


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None) else 1)
