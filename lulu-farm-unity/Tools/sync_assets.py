#!/usr/bin/env python3
"""Stage explicitly selected independent assets as external glTF for Unity import.
Original GLB/source files stay read-only. This does not claim Unity import/visual acceptance.
"""
import argparse, hashlib, json, pathlib, shutil, struct
ROOT=pathlib.Path(__file__).resolve().parents[1]
STUDIO=ROOT.parent/'lulu-studio'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def failed(value):
    value=str(value).lower()
    return any(word in value for word in ('failed','failure','rejected','do_not_promote','revision_required','needs_rework','not_passed','blocked'))

def verified_source(a):
    source=pathlib.Path(a['source'])
    expected=a.get('source_sha256')
    actual=sha(source)
    if expected and expected!=actual: raise ValueError(f'Source SHA256 changed: {source}')
    return source,actual

def externalize(src, dst):
    raw=src.read_bytes()
    if raw[:4]!=b'glTF': raise ValueError(f'Not GLB: {src}')
    pos=12; chunks={}
    while pos<len(raw):
        n,t=struct.unpack_from('<II',raw,pos); pos+=8; chunks[t]=raw[pos:pos+n];pos+=n
    doc=json.loads(chunks[0x4e4f534a]); blob=chunks[0x004e4942]
    dst.mkdir(parents=True,exist_ok=True)
    (dst/'model.bin').write_bytes(blob)
    doc['buffers'][0]['uri']='model.bin'
    image_uses={}
    for mat in doc.get('materials',[]):
        pbr=mat.get('pbrMetallicRoughness',{})
        for kind,ref in [('basecolor',pbr.get('baseColorTexture')),('mask',pbr.get('metallicRoughnessTexture')),('normal',mat.get('normalTexture')),('occlusion',mat.get('occlusionTexture')),('emissive',mat.get('emissiveTexture'))]:
            if ref is not None:
                image_uses.setdefault(doc['textures'][ref['index']]['source'],[]).append(kind)
    image_views={img['bufferView'] for img in doc.get('images',[]) if 'bufferView' in img}
    for i,img in enumerate(doc.get('images',[])):
        if 'bufferView' not in img: raise ValueError('External images in GLB require explicit resolution')
        bv=doc['bufferViews'][img['bufferView']]; offset=bv.get('byteOffset',0)
        ext='jpg' if img.get('mimeType')=='image/jpeg' else 'png'
        uses=image_uses.get(i,['image']); name=f'{i:02d}_{"_".join(uses)}.{ext}'
        (dst/name).write_bytes(blob[offset:offset+bv['byteLength']])
        img.pop('bufferView');img.pop('mimeType',None);img['uri']=name
    # Remove unused embedded image payload from Unity geometry buffers.
    packed=bytearray()
    for index,bv in enumerate(doc.get('bufferViews',[])):
        while len(packed)%4: packed.append(0)
        data=b'\0'*4 if index in image_views else blob[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]
        bv['byteOffset']=len(packed);bv['byteLength']=len(data);packed.extend(data)
    (dst/'model.bin').write_bytes(packed);doc['buffers'][0]['byteLength']=len(packed)
    (dst/'model.gltf').write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':')))
    return 'Assets/'+str((dst/'model.gltf').relative_to(ROOT/'Assets'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--ids',nargs='*');p.add_argument('--lulu',help='Explicit reviewed independent revision; no automatic promotion');p.add_argument('--comparisons',action='store_true');args=p.parse_args()
    manifest=json.loads((STUDIO/'public/models/unity-integration/manifest.json').read_text())
    # Interface derivatives keep their explicit assembly datums, not their open-pose bounding centre.
    by_id={a['id']:dict(a) for a in manifest['assets']}
    animal_file=STUDIO/'public/models/unity-animals/manifest.json'
    if animal_file.exists():
        for item in json.loads(animal_file.read_text())['assets']:
            status=item.get('status',{})
            if not str(status.get('visual','')).startswith('passed_candidate'):
                continue
            a=by_id[item['id']]
            a.update(item)
            a.update(status)
            a['selected_version']=item['revision']
    interface_file=STUDIO/'public/models/unity-integration/interfaces-manifest.json'
    if interface_file.exists():
        for item in json.loads(interface_file.read_text())['assets']:
            a=by_id.get(item['id'],{'id':item['id'],'name':item['id'],'species':item['id'],'stage':''})
            optimized=dict(a) if a.get('source')==item['file'] and not failed(a.get('visual','')) else None
            a.update({k:v for k,v in item.items() if k not in ('interface','acceptance')})
            acceptance=item.get('acceptance',{})
            if isinstance(acceptance,str):acceptance=json.loads(pathlib.Path(acceptance).read_text())
            a.update({k:v for k,v in acceptance.items() if k in ('technical','visual','user_art','optimization','device')})
            a['selected_version']=item.get('version',pathlib.Path(item['file']).parent.name)
            if optimized is not None:a.update(optimized)
            if item['id'] in ('E05-corner','S05-rail-connector'):a['type']='reused'
            if item['id']=='S06':
                spec=item['interface'];scale=spec['world_scale_for_height_082'];bounds=spec['original_bounds_zup']
                lo,hi=bounds['min'],bounds['max'];a['adapterScale']=scale
                # Interface export already subtracts original Z-min. Do not lift the grounded door twice.
                a['adapterOffset']={'x':(lo[0]+hi[0])*.5*scale,'y':0,'z':(lo[1]+hi[1])*.5*scale}
                if optimized is None:a['source_to_derived_transform']={'scale':1,'subtract_offset_blender_zup':[0,0,lo[2]]}
            by_id[a['id']]=a
    manifest['assets']=list(by_id.values())
    previous=ROOT/'Assets/Farm/Data/asset-registry.json'
    registry=json.loads(previous.read_text()) if previous.exists() else {'schema':1,'assets':[],'unity_import':'not_verified'}
    entries={x['id']:x for x in registry['assets']}
    for a in manifest['assets']:
        if args.ids and a['id'] not in args.ids:continue
        if failed(a.get('visual','')):
            entries.pop(a['id'],None)
            print('EXCLUDED visual failure:',a['id']);continue
        source,source_hash=verified_source(a)
        src=pathlib.Path(a['file'])
        if a.get('sha256') and a['sha256']!=sha(src):raise ValueError(f'Selected candidate SHA256 changed: {src}')
        path=externalize(src,ROOT/'Assets/Farm/Art'/a['id'])
        entries[a['id']]={'id':a['id'],'name':a['name'],'type':a['type'],'species':a['species'],'stage':a['stage'],
            'path':path,'source':str(source),'sourceSHA256':source_hash,'importSource':str(src),'importSHA256':sha(src),
            'sourceKind':a['sourceKind'],'version':a['selected_version'],'worldHeight':a.get('suggested_world_height') or 0,
            'technical':a.get('technical','pending'),'visual':a.get('visual','pending'),'userArt':a.get('user_art','pending'),'device':'not_tested','lodPaths':[],'lodImports':[]}
        for key in ('adapterScale','adapterOffset'):
            if key in a:entries[a['id']][key]=a[key]
        transform=a.get('source_to_derived_transform',{}) if src!=source else {}
        entries[a['id']]['sourceSpaceScale']=transform.get('scale',1)
        offset=transform.get('subtract_offset_blender_zup',[0,0,0])
        entries[a['id']]['sourceSpaceOffset']={'x':offset[0],'y':-offset[2],'z':offset[1]}
        if args.comparisons and source.suffix.lower()=='.glb':
            entries[a['id']]['beforePath']=externalize(source,ROOT/'Assets/Farm/Art/Comparisons'/a['id'])
        for lod in a.get('lods',[])[1:]:
            model=lod.get('model') or lod.get('file')
            if model and not failed(lod.get('status','')):
                lod_path=externalize(pathlib.Path(model),ROOT/'Assets/Farm/Art'/a['id']/('lod'+str(lod.get('level',1))))
                entries[a['id']]['lodPaths'].append(lod_path)
                entries[a['id']]['lodImports'].append({'path':lod_path,'importSource':model,'importSHA256':sha(pathlib.Path(model))})
    lulu_path=STUDIO/f'public/models/unity-lulu/{args.lulu}/manifest.json' if args.lulu else None
    if lulu_path and lulu_path.exists() and (not args.ids or 'Lulu' in args.ids):
        a=json.loads(lulu_path.read_text());src=pathlib.Path(a['model'])
        status=a.get('status',{})
        temporary_authorization=status.get('integration','')=='user_authorized_temporary_replaceable_motion_candidate_2026-10-19'
        if failed(status.get('visual','')) and not temporary_authorization: raise ValueError(f'Rejected Lulu visual candidate: {args.lulu}')
        source,source_hash=verified_source(a)
        entries['Lulu']={'id':'Lulu','name':'Lulu','type':'player','species':'lulu','stage':'',
            'path':externalize(src,ROOT/'Assets/Farm/Art/Lulu'),'source':str(source),'sourceSHA256':source_hash,
            'importSource':str(src),'importSHA256':sha(src),'sourceKind':'imported_edited_derivative','version':a['revision'],'worldHeight':1.2,'technical':status.get('technical','pending'),'visual':status.get('visual','pending'),'userArt':status.get('user_art','pending'),'device':'not_tested'}
        entries['Lulu']['temporaryMotionAuthorized']=temporary_authorization
        if args.comparisons:
            entries['Lulu']['beforePath']=externalize(source,ROOT/'Assets/Farm/Art/Comparisons/Lulu')
        entries['Lulu']['lodPaths']=[];entries['Lulu']['lodImports']=[]
        for lod in a.get('lods',[])[1:]:
            lod_path=externalize(pathlib.Path(lod['model']),ROOT/'Assets/Farm/Art/Lulu'/lod['name'])
            entries['Lulu']['lodPaths'].append(lod_path)
            entries['Lulu']['lodImports'].append({'path':lod_path,'importSource':lod['model'],'importSHA256':sha(pathlib.Path(lod['model']))})
        registry['luluLocomotion']=a['clips']
        wardrobe=ROOT/'Assets/Farm/Art/Wardrobe';wardrobe.mkdir(parents=True,exist_ok=True)
        for name in ['blue-stars.png','watermelon.png']:
            shutil.copy2(STUDIO/'public/models/wardrobe-rig/materials-v2'/name,wardrobe/name)
    elif args.lulu and (not args.ids or 'Lulu' in args.ids):
        raise FileNotFoundError(lulu_path)
    registry['assets']=list(entries.values());registry['sourceRegistry']=str(STUDIO/'public/models/unity-integration/manifest.json')
    registry['unity_import']='not_verified_after_staging'
    previous.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    print('Staged records:',len(entries),'Unity verification pending')
if __name__=='__main__':main()
