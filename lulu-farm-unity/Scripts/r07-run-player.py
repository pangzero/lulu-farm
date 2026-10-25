#!/usr/bin/env python3
"""Run an independent visible macOS player session; never mix screenshot and performance runs."""
import argparse, datetime, json, pathlib, subprocess
root=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('task',choices=['D5','D2','D3','D4','D6','O6','O7','O8','O9']);p.add_argument('mode',choices=['route','performance','ambient']);p.add_argument('--seconds',type=int)
# O6: requiredDuration follows --seconds (20 s warm-up, as 920→900 / 320→300).
# O6: --label keeps extra sessions (e.g. wind A/B) apart; --wind off starts with wind motion disabled.
p.add_argument('--label');p.add_argument('--wind',choices=['on','off'],default='on');a=p.parse_args()
out=root/'Evidence/r07'/a.task;out.mkdir(parents=True,exist_ok=True)
exe=root/'Builds/r07'/a.task/'development/LuluFarm.app/Contents/MacOS/噜噜农场'
if not exe.exists():raise SystemExit('Build required: '+str(exe))
seconds=a.seconds or (320 if a.task=='D3' and a.mode=='performance' else 920 if a.mode=='performance' else 72 if a.mode=='ambient' else 175)
name=a.mode+('-'+a.label if a.label else '');session=out/name;log=out/(name+'.log')
if log.exists():raise SystemExit('Refusing to overwrite prior run: '+str(log))
cmd=['/usr/bin/caffeinate','-di',str(exe),'-screen-width','1280','-screen-height','720','-screen-fullscreen','0','--farm-evidence',str(session),'--farm-quit-after',str(seconds),'-logFile',str(log)]
if a.mode=='route':cmd+=['--farm-route']
elif a.mode=='performance':
    profiler=out/('profiler-'+a.label if a.label else 'profiler');profiler.mkdir(exist_ok=True)
    if list(profiler.glob('*.data*')):raise SystemExit('Refusing to overwrite profiler capture')
    cmd+=['--farm-performance-route','--farm-performance-stage','mature','--farm-performance-quality','desktop','--farm-performance-warmup','5','--r07-profiler-directory',str(profiler)]
else:cmd+=['--r07-ambient-evidence']
if a.wind=='off':cmd+=['--r07-wind-off']
start=datetime.datetime.now(datetime.timezone.utc).isoformat();print('Running',a.task,a.mode,'for',seconds,'seconds',flush=True)
r=subprocess.run(cmd,cwd=root)
if a.mode=='performance':
    for f in profiler.glob('*.data.raw'):
        target=f.with_suffix('')
        if target.exists():raise SystemExit('Duplicate profiler target '+str(target))
        f.rename(target)
checks={}
if a.mode=='route':
    results=sorted(session.glob('*/automated-route.json'))
    result=json.loads(results[-1].read_text(encoding='utf-8-sig')) if results else {}
    checks={'routeResultPresent':bool(results),'planned31':result.get('plannedWaypoints')==31,'reached31':result.get('reachedWaypoints')==31,'completedStatus':str(result.get('status','')).startswith('completed_input_route')}
elif a.mode=='performance':
    results=sorted(session.glob('*/performance/summary.json'))
    result=json.loads(results[-1].read_text(encoding='utf-8-sig')) if results else {}
    windows=[json.loads(x) for x in results[-1].with_name('samples.jsonl').read_text(encoding='utf-8-sig').splitlines()] if results else []
    checks={'summaryPresent':bool(results),'requiredDuration':result.get('measurementSeconds',0)>=(300 if a.task=='D3' else a.seconds-20 if a.seconds else 900),'configurationUnchanged':result.get('configurationUnchanged') is True,'loopRunningAtStop':result.get('routeLoopRunningAtStop') is True,'allWindowsFocused':bool(windows) and all(x.get('applicationFocused') for x in windows)}
(out/(name+'-execution.json')).write_text(json.dumps({'startedUtc':start,'finishedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exitCode':r.returncode,'completionChecks':checks,'captureIntent':'actual visible player; caffeinate only for this process lifetime; profiler capture overhead is recorded separately from r06 no-profiler baseline'},ensure_ascii=False,indent=2))
print('Finished',a.mode,'player exit',r.returncode,'completion checks',checks,flush=True)
raise SystemExit(r.returncode or (2 if checks and not all(checks.values()) else 0))
