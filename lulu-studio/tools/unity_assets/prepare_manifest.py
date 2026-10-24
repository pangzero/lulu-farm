import json,hashlib,struct,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];OUT=R/'public/models/unity-integration';A=json.loads((R/'review/farm-integration-20261018/unity-plan-audit.json').read_text());F=json.loads((R/'public/models/facilities-meshy/manifest.json').read_text());rows=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def glb(p):
 b=Path(p).read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n])
def add(x,key,kind,stage='',height=None,target=0,note=''):
 p=Path(x['path']);d=glb(p);bounds=[]
 for m in d.get('meshes',[]):
  for q in m['primitives']:
   a=d['accessors'][q['attributes']['POSITION']]
   if 'min' in a:bounds.append((a['min'],a['max']))
 row={'id':key,'species':x.get('id',key),'name':x.get('name',key),'type':kind,'stage':stage,'file':str(p),'source':str(p),'source_name':p.name,'source_sha256':sha(p),'source_triangles':x.get('triangles'),'selected_version':'existing-input','bounds_raw_accessor':bounds,'suggested_world_height':height,'candidate_target_triangles':target,'notes':note,'technical':'input_inventory_only','visual':'historical_evidence_only','user_art':'pending','optimization':'pending' if target else 'reuse','device':'not_tested'};rows.append(row)
mt={'cabbage':10000,'tomato':18000,'corn':12000,'cucumber':14000,'pumpkin':10000,'sunflower':14000,'wheat':10000,'bokchoy':10000,'rose':14000,'strawberry':24000,'cauliflower':18000,'watermelon':10000,'tulip':8000,'lettuce':14000}
for c in A['crops']:
 for stage in ['mature','seedling']:
  x={**c[stage],'id':c['id'],'name':c['name']};target=mt[c['id']] if stage=='mature' else (8000 if c['id'] in ['cabbage','bokchoy','cauliflower','lettuce'] else 3500)
  add(x,c['id']+'-'+stage,'crop',stage,c[stage]['height'],target,'shared Meshy family representative' if stage=='seedling' else '')
  if c['id']=='rose' and stage=='mature':rows[-1]['visual']='known_color_failure_do_not_promote';rows[-1]['notes']='Existing game-r02 failed color classification. Needs independent semantic geometry/UV correction.'
heights={'cow':1.02,'sheep':.72,'duck':.48,'chicken':.50,'pig':.66,'alpaca':1.15,'hamster':.34,'donkey':1.05,'capybara':.64,'ostrich':1.35,'pony':1.10,'goat':.85,'goose':.68,'black-pig':.66,'deer':1.08}
for x in A['animals']:add(x,x['id'],'animal',height=heights[x['id']],target=22000 if x['id'] in ['sheep','alpaca'] else 16000,note='Cow selects head-clean-v4; rest material-refined v1.')
fh={'S01':4.9,'S03':2.25,'S04':2.2,'S06':.82,'S07':.70,'S08':.6,'S09':.52,'S10':2.1,'S11':.6,'S12':.43,'E03':.18,'E04':.12,'E06':.45,'E08':3.2,'E09':3.4,'E10':.75,'E11':.45,'E12':1.1,'E14':.16,'E15':.65,'E16':.30}
ft={'S01':55000,'S03':30000,'S04':26000,'S06':7000,'S07':12000,'S08':12000,'S09':7000,'S10':8000,'S11':12000,'S12':6000,'E03':3000,'E04':2500,'E06':7000,'E08':6500,'E09':8000,'E10':5000,'E11':7500,'E12':6000,'E14':5000,'E15':5000,'E16':5000}
for x in A['facilities']:add(x,x['id'],'facility' if x['id'].startswith('S') else 'environment',height=fh[x['id']],target=ft[x['id']],note='Height is initial adapter suggestion; dock/water/shore use contact-plane alignment, not root-ground normalization.')
for x in A['reused']:
 if x['id']=='S01-native-alternative':continue
 add(x,x['id'],'reused',target={'E01':2000,'E05':5000,'E13':4000}.get(x['id'],0),note='Accepted B02/B03 original retained. Authored project scale; preserve connection axes and contact plane.')
d={'schema':1,'scope':'Unity integration source selection, no Unity visual approval','assets':rows,'deferred':['S02','C12','C16'],'source_registry_only':True};(OUT/'manifest.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(len(rows),'assets',OUT/'manifest.json')
