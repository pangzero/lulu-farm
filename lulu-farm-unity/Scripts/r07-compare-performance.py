#!/usr/bin/env python3
"""Expose measured values and provenance without diagnosing or accepting performance."""
import json,pathlib,datetime
root=pathlib.Path(__file__).resolve().parents[1]
sources=[('r06 baseline',root/'Evidence/mac-player-performance-r06/20261023-030818-971/performance/summary.json',False)]
import sys
target=sys.argv[1] if len(sys.argv)>1 else 'D7'
# Writing to D7 reproduces the delivered table; any other target (e.g. O6) also lists that stage's sessions.
for stage in ['D5','D2','D3','D4','D6']+([target] if target!='D7' else []):
    folder=root/'Evidence/r07'/stage/('performance-r02' if stage=='D5' else 'performance')
    files=list(folder.glob('*/performance/summary.json'))
    if files:sources.append((stage,sorted(files)[-1],True))
    if stage==target:
        for extra in sorted((root/'Evidence/r07'/stage).glob('performance-*/*/performance/summary.json')):sources.append((stage+' '+extra.parts[-4],extra,True))
rows=[]
for name,p,profiler in sources:
    s=json.loads(p.read_text(encoding='utf-8-sig'));f=s['frameTimeMs']
    rows.append({'name':name,'source':str(p.relative_to(root)),'profilerEnabled':profiler,'measurementSeconds':s['measurementSeconds'],'laps':s['completedLaps'],'frames':f['sampleCount'],'meanMs':f['mean'],'p95Ms':f['p95'],'maxMs':f['maximum'],'configurationUnchanged':s['configurationUnchanged'],'acceptance':'Opus_analysis_pending'})
out=root/'Evidence/r07'/target;out.mkdir(parents=True,exist_ok=True)
data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'comparisonLimit':'r06 had no binary Profiler; r07 captures include CPU Profiler and ten-second rotation flush overhead. Same M5, 1280x720, Desktop and 20 mature plots, but profiler overhead is not subtracted. D6 final route moves two west-house intermediate points 0.6m east to avoid the inherited fence endpoint; the 31 points and key stops remain, but this is not an identical-path A/B comparison. No causal or acceptance conclusion.','rows':rows}
(out/'performance-table.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
lines=['# 性能记录原值','',data['comparisonLimit'],'','| 阶段 | 有效秒 | 圈 | 帧 | 均值 ms | P95 ms | 最大 ms | 二进制 Profiler |','|---|---:|---:|---:|---:|---:|---:|---|']
for r in rows:lines.append(f"| {r['name']} | {r['measurementSeconds']:.3f} | {r['laps']} | {r['frames']} | {r['meanMs']:.4f} | {r['p95Ms']:.4f} | {r['maxMs']:.4f} | {'开' if r['profilerEnabled'] else '关'} |")
lines+=['','只采集和列值；原因、预算和验收由 Opus 判断。Main Thread / Render Thread 不可用项不能当作 0ms；温度未测。','']
(out/'performance-table.md').write_text('\n'.join(lines))
print(len(rows),'recorded rows')
