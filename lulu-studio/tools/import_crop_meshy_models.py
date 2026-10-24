"""Register user-returned mature Meshy GLBs without changing original bytes."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'review/crop-meshy-progress-20261018'
PACK = ROOT.parent / 'art-concepts/crop-meshy-pack-20261018'
DEST = ROOT / 'public/models/crops-meshy'
THUMBS = ROOT / 'public/reference/crops-meshy'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

inventory=json.loads((QA/'download-inventory.json').read_text())
refs=json.loads((PACK/'manifest.json').read_text())
previous=json.loads((ROOT/'review/farm-assets/B04-meshy-20261018/import-manifest.json').read_text())['assets']
by_code={e['catalog_id']:e for e in refs['entries']}
download_by_code={e['catalog_id']:e for e in inventory['items']}
protected=[ROOT/'public/models/lulu-meshy-notail.glb']
protected+=list((ROOT/'public/models/farm-assets/B01').glob('*-mature-r03.glb'))
protected+=list((ROOT/'public/models/farm-assets/B02').glob('*-r04.glb'))
backup=QA/'protected-model-hashes.json'
if backup.exists():
    saved=json.loads(backup.read_text())
    for name,digest in saved.items():assert sha(ROOT/name)==digest,name
else:
    saved={str(p.relative_to(ROOT)):sha(p) for p in protected}
    write(backup,saved)
rows=[]; imports=[]
THUMBS.mkdir(parents=True,exist_ok=True)
for code in sorted(by_code):
    ref=by_code[code]; slug=ref['id']; batch=ref['batch']
    row=dict(id=slug,name=ref['name'],code=code,batch=batch,stage='mature',revision='meshy-r01',
             common_scale=.47,art_status='待用户验收',game_optimization_status='未执行',
             file=None,bytes=0,triangles=0,source='',original_name='')
    if code in download_by_code:
        item=download_by_code[code];source=Path(item['source_path'])
        assert sha(source)==item['sha256']
        dest=ROOT/f'public/models/farm-assets/{batch}/meshy-r01/{slug}-mature.glb'
        dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert sha(dest)==item['sha256'],f'Existing different model: {dest}'
        else:shutil.copy2(source,dest)
        assert sha(dest)==item['sha256'] and sha(source)==item['sha256']
        blend=f'assets-source/farm-assets/{batch}/meshy-r01/{slug}-import-review.blend'
        row.update(status='available',file='/'+str(dest.relative_to(ROOT/'public')),
                   bytes=item['bytes'],triangles=item['triangle_count'],original_name=source.name,
                   source=blend,source_kind='user_meshy_import',sha256=item['sha256'])
        imports.append(dict(id=slug,code=code,batch=batch,original_download=str(source),
                            original_name=source.name,file=str(dest.relative_to(ROOT)),
                            source=blend,sha256=item['sha256'],bytes=item['bytes'],
                            triangles=item['triangle_count'],raw_file_unchanged=True))
        image_source=QA/f'{slug}-quarter.png'
    elif batch=='B04':
        item=previous[slug];p=ROOT/item['file']
        assert sha(p)==item['sha256']
        row.update(status='available',file=item['url'],bytes=item['bytes'],triangles=item['triangles'],
                   original_name=Path(item['original_download']).name,source=item['import_review_source'],
                   source_kind='user_meshy_import',sha256=item['sha256'])
        image_source=ROOT/f'review/farm-assets/B04-meshy-20261018/{slug}-material-quarter.png'
    else:
        assert slug in ['zucchini','scallion']
        row.update(status='pending',revision='未提供',missing_note='用户确认稍后补充成熟态模型')
        image_source=None
    if image_source:
        thumb=THUMBS/f'{slug}.jpg'
        if not thumb.exists():
            with Image.open(image_source) as im:
                im.convert('RGB').resize((512,512),Image.Resampling.LANCZOS).save(thumb,quality=88)
        row['thumbnail']='/reference/crops-meshy/'+thumb.name
    rows.append(row)

assert len(rows)==16
assert sum(e['status']=='available' for e in rows)==14
assert len(imports)==11
for name,digest in saved.items():assert sha(ROOT/name)==digest,name
manifest=dict(revision='meshy-latest-20261018',updated='2026-10-18',stage_policy=['seedling','mature'],
              default_stage='mature',available_mature=14,planned_species=16,seedling_models=0,
              note='用户要求将新Meshy模型作为当前作物预览；旧认可版保留，最新不等于最终美术或性能验收。',crops=rows)
write(DEST/'manifest.json',manifest)
write(QA/'import-manifest.json',dict(revision=manifest['revision'],new_model_count=11,
                                   existing_B04_count=3,originals_unchanged=True,imports=imports,
                                   preview_manifest=str((DEST/'manifest.json').relative_to(ROOT)),
                                   user_art_status='待用户验收',game_optimization_status='未执行'))
print(json.dumps(dict(available=14,pending=['zucchini','scallion'],new_imports=11,
                      total_raw_bytes=sum(r['bytes'] for r in rows)),ensure_ascii=False))
