#!/usr/bin/env python3
"""Re-sign Evidence/import-stamp.json after the 2026-10-24 workspace path migration, without re-importing.

The migration rewrote the absolute prefix /Users/haowen/IdeaProjects/farm-game -> /Users/haowen/GameProject/farm-game
inside Assets/Farm/Data/asset-registry.json, which changes its SHA256 and makes FarmProjectBuilder reject the stamp.
Re-running ConfigureAndImport would rebuild every prefab (Lulu included), so this tool only updates the hash, and only
when ALL of these hold:
  1. the stamp's hash equals the pre-migration registry snapshot (Evidence/r07/D5/before/...);
  2. that snapshot with the prefix replaced is byte-identical to the current registry;
  3. the stamp status is imported_pending_visual_review with no issues.
Default is a dry run; pass --apply to write. The original stamp is copied aside first and never overwritten twice.
"""
import argparse, datetime, hashlib, json, pathlib, shutil, sys

OLD, NEW = b'/Users/haowen/IdeaProjects/farm-game', b'/Users/haowen/GameProject/farm-game'
root = pathlib.Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(); p.add_argument('--apply', action='store_true'); p.add_argument('--task', default='O6'); a = p.parse_args()
stamp_file = root / 'Evidence/import-stamp.json'
current_file = root / 'Assets/Farm/Data/asset-registry.json'
snapshot_file = root / 'Evidence/r07/D5/before/Assets/Farm/Data/asset-registry.json'
sha = lambda b: hashlib.sha256(b).hexdigest()

stamp = json.loads(stamp_file.read_text(encoding='utf-8-sig'))
current, snapshot = current_file.read_bytes(), snapshot_file.read_bytes()
checks = {
    'stampMatchesPreMigrationSnapshot': stamp.get('registrySHA256') == sha(snapshot),
    'prefixReplacementOnly': snapshot.replace(OLD, NEW) == current,
    'stampStatusImported': stamp.get('status') == 'imported_pending_visual_review',
    'stampHasNoIssues': not stamp.get('issues'),
    'stampNotAlreadyCurrent': stamp.get('registrySHA256') != sha(current),
}
record = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'apply': a.apply, 'checks': checks,
          'replacementOccurrences': snapshot.count(OLD), 'snapshotSHA256': sha(snapshot), 'currentSHA256': sha(current),
          'originalStamp': stamp, 'note': 'Path-migration re-sign only; no import, prefab, scene or asset was rebuilt.'}
ok = all(checks.values())
if a.apply and ok:
    backup = root / 'Evidence/import-stamp-before-path-migration.json'
    if backup.exists(): sys.exit('Refusing: backup already exists at ' + str(backup))
    shutil.copy2(stamp_file, backup)
    new = dict(stamp); new['registrySHA256'] = sha(current); new['utc'] = record['utc']
    new['pathMigrationResign'] = {'from': stamp['registrySHA256'], 'originalUtc': stamp.get('utc'), 'tool': 'Scripts/opus-r07-restamp-path-migration.py'}
    stamp_file.write_text(json.dumps(new, indent=4))
    record['newStamp'] = new; record['backup'] = str(backup.relative_to(root))
out = root / 'Evidence/r07' / a.task; out.mkdir(parents=True, exist_ok=True)
(out / ('import-stamp-resign.json' if a.apply else 'import-stamp-resign-dryrun.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2))
print(json.dumps({'checks': checks, 'applied': a.apply and ok}, indent=1))
sys.exit(0 if ok else 1)
