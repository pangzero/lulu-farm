"""Launch an unmodified O7 Player for native input evidence; no route or camera automation."""
from pathlib import Path
import argparse,subprocess,datetime,json
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--seconds',type=int,default=1200);a=p.parse_args()
u=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
exe=u/'Builds/r07/O7/development/LuluFarm.app/Contents/MacOS/噜噜农场'
log=out/(a.label+'.log');e=out/(a.label+'-execution.json')
if log.exists() or e.exists():raise SystemExit('Refusing overwrite')
cmd=['/usr/bin/caffeinate','-di',str(exe),'-screen-width','1280','-screen-height','720','-screen-fullscreen','0','--farm-evidence',str(out/a.label),'--farm-quit-after',str(a.seconds),'-logFile',str(log)]
start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,cwd=u)
e.write_text(json.dumps({'startedUtc':start,'finishedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exitCode':r.returncode,'intent':'Native CUA keyboard/mouse only, no route automation. F9 actual frame recording; captures are not performance runs.'},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(r.returncode)
