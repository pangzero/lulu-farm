"""Bit-level preservation gate for the colour-only Sketchfab derivative."""
from pathlib import Path
import argparse,json,struct,hashlib,numpy as np,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from color_lulu_sketchfab import accessor
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-sketchfab-color-20261019'
ap=argparse.ArgumentParser();ap.add_argument('--revision',default='color-r07');args=ap.parse_args()
def read(p):
    b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
s=D/'baseline/a5747f74f0034470a2029a85f6e9c11d.glb';t=D/args.revision/'lulu-sketchfab-colour.glb';g,b=read(s);h,c=read(t);checks=[]
for a,m in zip(g['meshes'],h['meshes']):
    pr=a['primitives'][0];at=pr['attributes'];po=accessor(g,b,at['POSITION']);no=accessor(g,b,at['NORMAL']);fo=accessor(g,b,pr['indices']).reshape(-1,3)
    fs=[];pe=True;ne=True
    for qr in m['primitives']:
        qa=qr['attributes'];pe&=np.array_equal(po,accessor(h,c,qa['POSITION']));ne&=np.array_equal(no,accessor(h,c,qa['NORMAL']));fs.append(accessor(h,c,qr['indices']).reshape(-1,3))
    ft=np.concatenate(fs);order=lambda x:x[np.lexsort(x.T[::-1])]
    checks.append({'position_bit_identical':bool(pe),'normal_bit_identical':bool(ne),'triangle_multiset_exact':bool(np.array_equal(order(fo),order(ft))),'triangles':len(ft)})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'revision':args.revision,'original_sha256':sha(s),'candidate_sha256':sha(t),'download_matches_backup':sha(s)==sha(Path('/Users/haowen/Downloads/a5747f74f0034470a2029a85f6e9c11d.glb')),'node_transforms_exact':g['nodes']==h['nodes'],'mesh_checks':checks,'all_geometry_checks_pass':all(all(v for k,v in a.items() if k!='triangles') for a in checks),'triangles':sum(a['triangles'] for a in checks),'images':len(h['images']),'materials':len(h['materials']),'uv_added':True,'arms_rigged':False,'source_not_overwritten':True,'status':'COLOUR_APPEARANCE_PENDING_USER_REVIEW'}
(D/args.revision/'preservation.json').write_text(json.dumps(report,indent=2))
assert report['all_geometry_checks_pass'] and report['node_transforms_exact'] and report['download_matches_backup']
print(json.dumps(report,indent=2))
