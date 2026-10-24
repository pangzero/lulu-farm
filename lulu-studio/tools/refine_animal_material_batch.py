"""Author the approved 15-animal material revision without sculpting.

Decode source color maps to identify existing iris/pupil faces and partition
the original triangles into material groups. The cow additionally receives a
localized UV material bake. Geometry, UVs and downloaded originals stay intact.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import shutil
import struct
import subprocess
import numpy as np
from PIL import Image
from refine_animal_eye_materials import hull_2d, inside_hull

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT/'review/animal-materials-20261018'
OUTPUT = ROOT/'public/models/animals-refined/v1'
# Visual target is shared; surface response is tuned per animal.
PROFILES = {
    'cow':(.24,.08,.20), 'sheep':(.23,.06,.18),
    'duck':(.22,.06,.20), 'chicken':(.24,.06,.20),
    'pig':(.24,.08,.18), 'alpaca':(.25,.05,.18),
    'hamster':(.24,.05,.18), 'donkey':(.24,.07,.20),
    'capybara':(.26,.05,.18), 'ostrich':(.23,.06,.20),
    'pony':(.24,.06,.20), 'goat':(.24,.06,.20),
    'goose':(.23,.06,.20), 'black-pig':(.25,.06,.18),
    'deer':(.24,.08,.22),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def revise(asset):
    source = ROOT/asset['file']
    raw = source.read_bytes()
    assert sha(raw)==asset['sha256'], 'Source mismatch: '+asset['id']
    backup = REVIEW/'baseline'/asset['file']
    if not backup.exists():
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,backup)
    assert sha(backup.read_bytes())==asset['sha256']
    n = struct.unpack_from('<I',raw,12)[0]
    doc = json.loads(raw[20:20+n])
    binary_length = struct.unpack_from('<I',raw,20+n)[0]
    binary = raw[28+n:28+n+binary_length]
    original_doc = copy.deepcopy(doc)
    assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==1
    assert np.array_equal(doc['nodes'][0]['matrix'],np.eye(4).ravel())
    def accessor(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
        width={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']]
        step=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,
                          offset=v.get('byteOffset',0)+a.get('byteOffset',0),
                          strides=(v.get('byteStride',step*width),step))
    p=doc['meshes'][0]['primitives'][0]
    positions=accessor(p['attributes']['POSITION'])
    uv=accessor(p['attributes']['TEXCOORD_0'])
    indices=accessor(p['indices']).reshape(-1,3)
    material=doc['materials'][p['material']]
    ti=material['pbrMetallicRoughness']['baseColorTexture']['index']
    im=doc['images'][doc['textures'][ti]['source']]
    view=doc['bufferViews'][im['bufferView']];offset=view.get('byteOffset',0)
    color=np.asarray(Image.open(io.BytesIO(binary[offset:offset+view['byteLength']])).convert('RGB'))
    height,width=color.shape[:2]
    def sample(coords):
        return color[np.clip((coords[...,1]*height).astype(int),0,height-1),np.clip((coords[...,0]*width).astype(int),0,width-1)].astype(int)
    rgb=sample(uv)
    blue=(rgb[:,2]>rgb[:,0]+25)&(rgb[:,2]>rgb[:,1]+5)&(rgb[:,2]>80)&(rgb[:,0]<150)
    centers=positions[indices].mean(axis=1)
    eye_mask=np.zeros(len(indices),dtype=bool)
    eyes=[]
    for sign in (-1,1):
        seeds=positions[blue&(positions[:,0]*sign>0)]
        assert len(seeds)>35,(asset['id'],sign,'iris seeds')
        center=seeds.mean(axis=0)
        _,_,basis=np.linalg.svd(seeds-center,full_matrices=False)
        hull=hull_2d((seeds-center)@basis[:2].T)
        middle=(hull.min(axis=0)+hull.max(axis=0))/2
        hull=middle+(hull-middle)*1.055
        depth99=float(np.percentile(np.abs((seeds-center)@basis[2]),99))
        depth=.014 if asset['id']=='cow' else min(.035,max(.008,depth99*2.8))
        selected=inside_hull((centers-center)@basis[:2].T,hull)&(np.abs((centers-center)@basis[2])<depth)
        assert selected.sum()>100,(asset['id'],sign,'empty eye region')
        eye_mask|=selected
        eyes.append(dict(side=sign,triangles=int(selected.sum()),depth=depth,
                         center=center.tolist(),min=centers[selected].min(0).tolist(),max=centers[selected].max(0).tolist()))
    assert 100<eye_mask.sum()<len(indices)*.10,(asset['id'],'eye region too large')
    roughness,normal_scale,specular=PROFILES[asset['id']]
    revised_eye=copy.deepcopy(material)
    revised_eye['name']=asset['id']+'_eyes_soft_gloss_v1'
    pbr=revised_eye['pbrMetallicRoughness']
    pbr.pop('metallicRoughnessTexture',None)
    pbr['metallicFactor']=0.0;pbr['roughnessFactor']=roughness
    revised_eye['normalTexture']['scale']=normal_scale
    revised_eye.setdefault('extensions',{})['KHR_materials_specular']={'specularFactor':specular}
    doc.setdefault('extensionsUsed',[])
    if 'KHR_materials_specular' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_specular')
    eye_index=len(doc['materials']);doc['materials'].append(revised_eye)
    groups=[(~eye_mask,p['material']),(eye_mask,eye_index)]
    labels=np.stack([g[0] for g in groups]).sum(axis=0)
    assert np.all(labels==1),'Every source triangle must occur exactly once'
    payload=bytearray(binary)
    primitives=[]
    for mask,material_index in groups:
        values=indices[mask]
        payload.extend(b'\x00'*((-len(payload))%4))
        start=len(payload);encoded=values.astype('<u4').tobytes();payload.extend(encoded)
        view_index=len(doc['bufferViews'])
        doc['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=len(encoded),target=34963))
        accessor_index=len(doc['accessors'])
        doc['accessors'].append(dict(bufferView=view_index,byteOffset=0,componentType=5125,count=int(values.size),type='SCALAR',min=[int(values.min())],max=[int(values.max())]))
        q=copy.deepcopy(p);q['indices']=accessor_index;q['material']=material_index;primitives.append(q)
    doc['meshes'][0]['primitives']=primitives
    doc['buffers'][0]['byteLength']=len(payload)
    doc.setdefault('extras',{})['materialRevision']={'revision':'animals-materials-v1','sourceSha256':asset['sha256'],'scope':'eye response and cow existing black head/outer-ear material only'}
    assert doc['materials'][0]==original_doc['materials'][0]
    assert doc['images']==original_doc['images'] and doc['textures']==original_doc['textures']
    assert doc['nodes']==original_doc['nodes'] and doc['accessors'][:len(original_doc['accessors'])]==original_doc['accessors']
    assert bytes(payload[:len(binary)])==binary
    j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
    payload.extend(b'\x00'*((-len(payload))%4))
    output=struct.pack('<4sII',b'glTF',2,28+len(j)+len(payload))+struct.pack('<II',len(j),0x4E4F534A)+j+struct.pack('<II',len(payload),0x004E4942)+payload
    target=OUTPUT/(asset['id']+'.glb');target.write_bytes(output)
    bake={}
    if asset['id']=='cow':
        command=['/Users/haowen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',str(ROOT/'tools/bake_cow_clean_material.mjs'),str(target)]
        baked=subprocess.run(command,check=True,capture_output=True,text=True)
        bake=json.loads(baked.stdout)
        output=target.read_bytes()
    assert source.read_bytes()==raw
    lo,hi=positions.min(0),positions.max(0);scale=2.2/float(hi[1]-lo[1]);middle=(lo+hi)/2
    def normalize(v):
        return [(v[0]-middle[0])*scale,(v[1]-lo[1])*scale,(v[2]-middle[2])*scale]
    eye_lo=np.min([e['min'] for e in eyes],axis=0);eye_hi=np.max([e['max'] for e in eyes],axis=0)
    focus=[normalize(eye_lo-np.array([.08,.09,.10])),normalize(eye_hi+np.array([.08,.09,.06]))]
    height_world=float(hi[1]-lo[1])
    head_lo=np.maximum(lo,eye_lo-np.array([.18,.22,.20])*height_world)
    head_hi=np.minimum(hi,eye_hi+np.array([.18,.30,.16])*height_world)
    record=dict(id=asset['id'],name=asset['name'],source=asset['file'],source_sha256=asset['sha256'],file=str(target.relative_to(ROOT)),
                url='/'+str(target.relative_to(ROOT/'public')),bytes=len(output),version=sha(output)[:8],sha256=sha(output),
                roughness=roughness,normal_scale=normal_scale,specular=specular,triangles=int(len(indices)),eye_triangles=int(eye_mask.sum()),
                eyes=eyes,focus_box=focus,head_box=[normalize(head_lo),normalize(head_hi)],
                vertices_normals_uvs_unchanged=True,texture_images_unchanged=not bool(bake),cow_head_bake=bake,source_verified=True,visual_review='pending')
    print(asset['id'],'eyes',record['eye_triangles'],'cow_bake',bool(bake),'roughness',roughness,'normal',normal_scale,'specular',specular,flush=True)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ids',nargs='*')
    args=parser.parse_args()
    models=json.loads((ROOT/'public/models/animals/manifest.json').read_text())['models']
    assert set(m['id'] for m in models)==set(PROFILES)
    REVIEW.mkdir(parents=True,exist_ok=True);OUTPUT.mkdir(parents=True,exist_ok=True)
    for relative in ('src/gallery.ts','gallery.html','src/gallery.css','assets-manifest.json','src/animal-eye-study.ts'):
        src=ROOT/relative;dst=REVIEW/'baseline'/relative
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    manifest_path=OUTPUT.parent/'manifest.json'
    old=json.loads(manifest_path.read_text())['models'] if manifest_path.exists() else []
    records={m['id']:m for m in old}
    for model in models:
        if not args.ids or model['id'] in args.ids:
            records[model['id']]=revise(model)
    ordered=[records[m['id']] for m in models if m['id'] in records]
    manifest={'revision':'animals-materials-v1','date':'2026-10-18','originals_preserved':True,'models':ordered}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'src/animal-material-revisions.ts').write_text('// Generated by tools/refine_animal_material_batch.py.\nexport const animalMaterialRevisions = '+json.dumps(ordered,ensure_ascii=False,indent=2)+';\n')
    print('Completed',len(ordered),'material revisions. Original GLBs and geometry preserved; cow derivative maps baked separately.')


if __name__=='__main__':
    main()
