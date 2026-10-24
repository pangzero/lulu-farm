#!/usr/bin/env python3
"""Index actual outputs and compare recorded values. Does not make acceptance decisions."""
import argparse, datetime, hashlib, html, json, pathlib, shutil
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('task');p.add_argument('--before');a=p.parse_args();out=root/'Evidence/r07'/a.task;out.mkdir(parents=True,exist_ok=True)
if a.before:
    previous=root/'Evidence/r07'/a.before
    for name in ['fixed','fixed-pp-on']:
        destination=out/'before'/name
        if destination.exists():raise SystemExit(f'Already exists: {destination}; snapshots are immutable')
        shutil.copytree(previous/name,destination)
    for pattern in ['Assets/Farm/Editor/FarmProjectBuilder.cs','Assets/Farm/Editor/FarmLandscapePolish.cs','Assets/Farm/Editor/*R07.cs','Assets/Farm/Editor/FarmDecorScatter.cs','Assets/Farm/Scripts/Runtime/*R07.cs','Assets/Farm/Shaders/*r0*.shader','Assets/Farm/Scenes/FarmWorld.unity','Assets/Farm/Settings/*.asset']:
        for path in root.glob(pattern):
            target=out/'before'/path.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    print('Saved before snapshot from',a.before);raise SystemExit()
load=lambda path:json.loads(path.read_text(encoding='utf-8-sig'))
perf=[]
for summary in sorted(out.glob('performance*/**/summary.json')):
    s=load(summary);file=summary.parent/'samples.jsonl';samples=[json.loads(x) for x in file.read_text(encoding='utf-8-sig').splitlines()] if file.exists() else []
    gaps=[{'fromElapsed':x['elapsedSeconds'],'toElapsed':y['elapsedSeconds'],'gapSeconds':y['elapsedSeconds']-x['elapsedSeconds']} for x,y in zip(samples,samples[1:]) if y['elapsedSeconds']-x['elapsedSeconds']>3]
    perf.append({'source':str(summary.relative_to(root)),'stoppedBecause':s.get('stoppedBecause'),'routeLoopRunningAtStop':s.get('routeLoopRunningAtStop'),'configurationUnchanged':s.get('configurationUnchanged'),'measurementSeconds':s.get('measurementSeconds'),'laps':s.get('completedLaps'),'frameTimeMs':s.get('frameTimeMs'),'sampleWindowGapsOver3Seconds':gaps,'sampleWindows':len(samples),'unfocusedWindows':sum(not x.get('applicationFocused',False) for x in samples),'conclusion':'recorded_values_only_Opus_analysis_pending'})
routes=[]
for f in out.glob('route*/**/automated-route.json'):
    s=load(f);routes.append({'file':str(f.relative_to(root)),**{k:s[k] for k in ['status','mode','revision','reachedWaypoints','plannedWaypoints','finalPosition']}})
comparisons=[];sections=[]
for folder in ['fixed','fixed-pp-on']:
    before=out/'before'/folder;after=out/folder
    if not before.exists() or not after.exists():continue
    b=load(before/'review-settings.json');c=load(after/'review-settings.json')
    byname={s['name']:s for s in b['shots']}
    for shot in c['shots']:
        name=shot['name'];old=byname.get(name)
        if old is None:continue
        equal=all(old.get(k)==shot.get(k) for k in ['position','target','fov','width','height'])
        comparisons.append({'group':folder,'name':name,'cameraAndResolutionIdentical':equal,'before':str((before/(name+'.png')).relative_to(root)),'after':str((after/(name+'.png')).relative_to(root))})
        sections.append(f'<h3>{html.escape(folder+" / "+name)}</h3><div><figure><figcaption>Before</figcaption><img src="before/{folder}/{name}.png"></figure><figure><figcaption>{a.task}</figcaption><img src="{folder}/{name}.png"></figure></div>')
(out/'compare.html').write_text('<meta charset="utf-8"><title>r07 '+a.task+' same camera comparison</title><style>body{background:#202923;color:#eee;font:16px sans-serif}div{display:flex;gap:8px}figure{margin:0;width:50%}img{width:100%}h3{margin-top:30px}</style>'+''.join(sections))
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task':a.task,'status':'pending_Opus_review','builds':[load(f) for f in out.glob('build-*.json')],'routes':routes,'performance':perf,'fixedComparisons':comparisons,'profilerExports':[str(f.relative_to(root)) for f in out.glob('profiler*/export-index.json')],'artAcceptance':'not_granted','performanceAcceptance':'no_conclusion'}
(out/'metrics.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));print(json.dumps({'task':a.task,'routes':len(routes),'performanceSessions':len(perf),'comparisons':len(comparisons)}))
