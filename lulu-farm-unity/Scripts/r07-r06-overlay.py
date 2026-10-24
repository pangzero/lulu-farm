#!/usr/bin/env python3
"""Unmodified original PNG overlays; slider only, no image resampling or retouching."""
import json, pathlib, html
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'Evidence/r07/D3'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
old=load(out/'r06-baseline/review-settings.json')
new=load(out/'fixed/review-settings.json')
previous={s['name']:s for s in old['shots']}
records=[]; sections=[]
for shot in new['shots']:
    name=shot['name']; before=previous[name]
    fields=['position','target','fov','width','height']
    records.append({'name':name,'cameraAndResolutionIdentical':all(before.get(k)==shot.get(k) for k in fields),'r06':before,'r07':shot})
    sections.append(f'<h2>{html.escape(name)}</h2><div class="pair"><img src="r06-baseline/{name}.png"><img class="after" src="fixed/{name}.png"></div>')
(out/'compare-r06.html').write_text('''<meta charset="utf-8"><title>D3 versus r06</title>
<style>body{background:#202923;color:#eee;font:16px sans-serif}.pair{position:relative;width:min(100%,1600px)}img{width:100%;display:block}.after{position:absolute;top:0;opacity:.5}header{position:sticky;top:0;background:#202923;padding:12px;z-index:2}</style>
<header>r06 ↔ D3；原始图直接叠加，亮度差包含 D2 灯光调整。<br>r07 不透明度 <input type="range" min="0" max="100" value="50" oninput="document.querySelectorAll('.after').forEach(x=>x.style.opacity=this.value/100)"></header>'''+''.join(sections))
(out/'r06-camera-comparison.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
p=out/'compare-r06-template-not-generated.txt'
if p.exists():p.unlink()
print({'pairs':len(records),'identicalCameras':sum(x['cameraAndResolutionIdentical'] for x in records)})
