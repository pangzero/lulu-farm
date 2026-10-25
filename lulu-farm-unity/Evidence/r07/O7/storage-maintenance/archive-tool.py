import pathlib,gzip,hashlib,os,json,shutil,datetime
root=pathlib.Path('/Users/haowen/GameProject/farm-game/lulu-farm-unity')
out=pathlib.Path('/Users/haowen/GameProject/local-evidence-archives/r07-profiler-20261025-o7-space')
out.mkdir(parents=True,exist_ok=True)
ledger=out/'archive-ledger.jsonl'
files=[]
for phase in ['O6','D6']:
 files.extend(sorted((root/'Evidence/r07'/phase).rglob('*.data')))
for src in files:
 if shutil.disk_usage(root).free>=30*1024**3: break
 rel=src.relative_to(root); dst=out/rel; dst=dst.with_name(dst.name+'.gz')
 if dst.exists(): raise RuntimeError('Refusing overwrite '+str(dst))
 dst.parent.mkdir(parents=True,exist_ok=True); tmp=dst.with_name(dst.name+'.partial')
 st=src.stat(); h=hashlib.sha256(); n=0
 with src.open('rb') as f,tmp.open('xb') as raw:
  with gzip.GzipFile(filename=src.name,mode='wb',fileobj=raw,compresslevel=1,mtime=int(st.st_mtime)) as z:
   while True:
    b=f.read(8*1024*1024)
    if not b: break
    h.update(b);n+=len(b);z.write(b)
  raw.flush();os.fsync(raw.fileno())
 v=hashlib.sha256();vn=0
 with gzip.open(tmp,'rb') as f:
  while True:
   b=f.read(8*1024*1024)
   if not b:break
   v.update(b);vn+=len(b)
 if n!=vn or h.digest()!=v.digest() or src.stat().st_mtime_ns!=st.st_mtime_ns or src.stat().st_size!=st.st_size:raise RuntimeError('Verification mismatch '+str(src))
 ch=hashlib.sha256()
 with tmp.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):ch.update(b)
 tmp.rename(dst)
 record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original':str(src),'relativePath':str(rel),'originalBytes':n,'originalSha256':h.hexdigest(),'originalMtimeNs':st.st_mtime_ns,'archive':str(dst),'archiveBytes':dst.stat().st_size,'archiveSha256':ch.hexdigest(),'algorithm':'gzip','compresslevel':1,'decompressedBytes':vn,'decompressedSha256':v.hexdigest(),'verified':True,'restoration':'gzip -dc ARCHIVE > ORIGINAL; verify originalSha256 before use','sourceRemovedAfterVerification':False}
 with ledger.open('a') as f:f.write(json.dumps(record)+'\n');f.flush();os.fsync(f.fileno())
 src.unlink()
 with ledger.open('a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original':str(src),'sourceRemovedAfterVerification':True})+'\n');f.flush();os.fsync(f.fileno())
 print(json.dumps({'file':str(rel),'originalMB':round(n/1e6,1),'archiveMB':round(dst.stat().st_size/1e6,1),'freeGB':round(shutil.disk_usage(root).free/1024**3,2)}),flush=True)
print('FINISHED free GiB',shutil.disk_usage(root).free/1024**3,flush=True)
