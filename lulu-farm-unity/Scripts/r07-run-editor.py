#!/usr/bin/env python3
"""Serial r07 editor invocations. Run with the project closed; preserves locked inputs."""
import argparse, datetime, hashlib, json, pathlib, subprocess
root=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('task',choices=['D5','D2','D3','D4','D6','O6','O7','O8','O9']);parser.add_argument('steps',nargs='+',choices=['generate','development','release','export'])
parser.add_argument('--profiler-directory')
args=parser.parse_args()
editor=root.parent/'.unity-install/Editors/6000.3.16f1/Unity.app/Contents/MacOS/Unity'
out=root/'Evidence/r07'/args.task;out.mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=json.loads((root/'Evidence/r07/D5/before/protected-lulu.json').read_text())
locks={str(p.relative_to(root)):digest(p) for p in (root/'Packages').glob('*.json')}
methods={'generate':'FarmProjectBuilder.R07GenerateReview','development':'FarmProjectBuilder.R07BuildDevelopment','release':'FarmProjectBuilder.R07BuildRelease','export':'FarmProfilerExportR07.Export'}
for step in args.steps:
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')
    log=out/f'{step}-{stamp}.log'
    cmd=[str(editor),'-batchmode','-quit','-projectPath',str(root),'-buildTarget','StandaloneOSX','-executeMethod','LuluFarm.Editor.'+methods[step],'--r07-task',args.task,'-logFile',str(log)]
    if step=='export' and args.profiler_directory:cmd+=['--r07-profiler-directory',str(pathlib.Path(args.profiler_directory).resolve())]
    print('Running',step,'log',log,flush=True)
    result=subprocess.run(cmd,cwd=root)
    changed=[p for p,v in {**protected,**locks}.items() if not (root/p).is_file() or digest(root/p)!=v]
    record={'step':step,'exitCode':result.returncode,'changedProtectedFiles':changed,'log':str(log)}
    (out/f'{step}-{stamp}-execution.json').write_text(json.dumps(record,indent=2))
    if result.returncode or changed:raise SystemExit(json.dumps(record))
    print(step,'finished; protected inputs unchanged',flush=True)
