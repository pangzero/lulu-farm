#!/usr/bin/env python3
"""O2: long-frame analysis from exported r07 Profiler timelines and runtime samples.

Reads only existing evidence (timeline.json.gz exported from the binary .data, samples.jsonl,
route-samples.jsonl). Writes Evidence/r07/O2/longframes.json. No conclusion is inferred from
means; every long frame is classified from its own main-thread markers.
"""
import collections, glob, gzip, json, os, statistics, sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Evidence', 'r07')
SESSIONS = {'D5': ('profiler-r02', 'performance-r02'), 'D2': ('profiler', 'performance'), 'D3': ('profiler', 'performance'),
            'D4': ('profiler', 'performance'), 'D6': ('profiler', 'performance')}
WAIT = 'Semaphore.WaitForSignal'


def frames(profiler):
    cap = json.load(open(os.path.join(profiler, 'capture.json')))
    t0, prev_end, out, gaps, total, missing = None, None, [], [], 0, []
    for ch in cap['chunks']:
        path = os.path.join(profiler, ch['file'].replace('.data', '.timeline.json.gz'))
        if not os.path.exists(path) or open(path, 'rb').read(2) != b'\x1f\x8b':
            missing.append(ch['file']); prev_end = None; continue
        events = json.load(gzip.open(path))['traceEvents']
        main = sorted((e for e in events if e.get('tid') == 0), key=lambda e: e['ts'])
        roots = [e for e in main if e['name'] == 'Main Thread']
        if t0 is None: t0 = roots[0]['ts'] - ch['fromSeconds'] * 1e6
        if prev_end is not None: gaps.append(round((roots[0]['ts'] - prev_end) / 1000, 2))
        prev_end = roots[-1]['ts'] + roots[-1]['dur']; total += len(roots)
        for r in roots:
            if r['dur'] < 50000: continue
            a, b = r['ts'], r['ts'] + r['dur']
            inside = [e for e in main if a <= e['ts'] and e['ts'] + e['dur'] <= b + 1 and e['name'] not in ('Main Thread', 'PlayerLoop')]
            wait = sum(e['dur'] for e in inside if e['name'] == WAIT)
            # Render thread state over the same interval: waiting for main-thread commands = idle.
            rt_idle = sum(e['dur'] for e in events if e['args'].get('thread') == 'Render Thread'
                          and e['name'] == 'Gfx.WaitForGfxCommandsFromMainThread' and e['ts'] < b and e['ts'] + e['dur'] > a)
            top = sorted(inside, key=lambda e: -e['dur'])[:6]
            if wait > .6 * r['dur']: cls = 'presentation_wait_cpu_idle'
            elif any(e['name'] == 'FixedUpdate.PhysicsFixedUpdate' and e['dur'] > .3 * r['dur'] for e in inside): cls = 'physics_step_slow'
            else: cls = 'mixed_or_other'
            out.append({'sessionSeconds': round((a - t0) / 1e6, 2), 'ms': round(r['dur'] / 1000, 1), 'class': cls,
                        'semaphoreWaitMs': round(wait / 1000, 1), 'renderThreadIdleMs': round(rt_idle / 1000, 1),
                        'chunk': ch['file'], 'top': [[e['name'][:90], round(e['dur'] / 1000, 1)] for e in top]})
    return {'framesInTimelines': total, 'missingChunks': missing, 'interChunkGapMs': {'median': statistics.median(gaps) if gaps else None,
            'max': max(gaps) if gaps else None}, 'longFrames': out}


def runtime(perf):
    rows = [json.loads(l.lstrip('﻿')) for l in open(glob.glob(os.path.join(perf, '*', 'performance', 'samples.jsonl'))[0])]
    summary = json.load(open(glob.glob(os.path.join(perf, '*', 'performance', 'summary.json'))[0]))
    impossible = []
    for prev, r in zip(rows, rows[1:]):
        ft = r['frameTimeMs']
        if not ft.get('available'): continue
        wall = r['elapsedSeconds'] - prev['elapsedSeconds']
        summed = ft['mean'] * ft['sampleCount'] / 1000
        if summed > wall + .25:
            impossible.append({'elapsedSeconds': round(r['elapsedSeconds'], 1), 'windowWallSeconds': round(wall, 3),
                               'sumUnscaledDeltaSeconds': round(summed, 2), 'maxFrameMs': round(ft['maximum'], 1), 'frames': ft['sampleCount']})
    route = [json.loads(l.lstrip('﻿')) for l in open(glob.glob(os.path.join(perf, '*', 'route-samples.jsonl'))[0])]
    gpu = sorted(r['gpuFrameMs'] for r in route if r.get('gpuTimingAvailable'))
    cpu = sorted(r['cpuFrameMs'] for r in route if r.get('cpuTimingAvailable'))
    pct = lambda v, q: round(v[min(len(v) - 1, int(q * len(v)))], 2)
    return {'summaryFrameTimeMs': {k: round(summary['frameTimeMs'][k], 3) for k in ('mean', 'p95', 'maximum')},
            'windowsWithMoreFrameTimeThanWallTime': impossible,
            'frameTimingSamples': {'gpuMs': {'n': len(gpu), 'median': pct(gpu, .5), 'p95': pct(gpu, .95), 'max': round(gpu[-1], 1)},
                                   'cpuMs': {'n': len(cpu), 'median': pct(cpu, .5), 'p95': pct(cpu, .95), 'max': round(cpu[-1], 1)}}}


result = {'method': 'Exported filtered timelines (thread roots + markers >=0.1ms) of the binary captures; runtime samples.jsonl/route-samples.jsonl. '
          'Binary .data files were not re-read here.', 'sessions': {}}
for name, (prof, perf) in SESSIONS.items():
    p = frames(os.path.join(root, name, prof)); rt = runtime(os.path.join(root, name, perf))
    lf = p.pop('longFrames')
    classes = collections.Counter(f['class'] for f in lf)
    result['sessions'][name] = {**p, 'runtime': rt, 'longFrameCount50ms': len(lf), 'byClass': classes,
                                'profilerMaxFrameMs': max((f['ms'] for f in lf), default=None),
                                'framesOver400ms': [f for f in lf if f['ms'] >= 400], 'longFrames': lf}
    print(name, 'long>=50ms', len(lf), dict(classes), 'profiler max', result['sessions'][name]['profilerMaxFrameMs'],
          'runtime max', rt['summaryFrameTimeMs']['maximum'], 'impossible windows', len(rt['windowsWithMoreFrameTimeThanWallTime']))
out = os.path.join(root, 'O2'); os.makedirs(out, exist_ok=True)
json.dump(result, open(os.path.join(out, 'longframes.json'), 'w'), indent=1, ensure_ascii=False)
