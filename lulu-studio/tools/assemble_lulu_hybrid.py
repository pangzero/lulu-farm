"""Static trial: approved head + original r04 lower six parts.
Only a parent similarity transform is added to the old group. Mesh/UV/normal
accessor bytes are copied verbatim. No body generation, edits, rig or remeshing.
"""
from pathlib import Path
import copy,json,struct,hashlib,argparse
R=Path(__file__).resolve().parents[1];D=R/'review/lulu-hybrid-assembly-20261023'
p=argparse.ArgumentParser();p.add_argument('--rev',default='hybrid-r01');p.add_argument('--height',type=float,default=.56332);p.add_argument('--depth',type=float,default=.01);p.add_argument('--scale',type=float,default=.54151);a=p.parse_args()
O=D/a.rev
if O.exists():raise RuntimeError('Revision exists; preserve it')
O.mkdir()
def load(f):
 b=f.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
for e in json.loads((D/'backup.json').read_text()):assert sha(R/e['source'])==e['sha256']==sha(R/e['backup'])
oldfile=D/'baseline/public/models/modular/right-junction-r04/lulu-assembled.glb';headfile=D/'baseline/public/models/lulu-sketchfab/head-approved-v1/lulu-head.glb'
old,ob=load(oldfile);head,hb=load(headfile)
transform={'scale':[a.scale]*3,'translation':[.0015645*a.scale,a.height,a.depth]}
def assemble(specs,path):
 out={'asset':{'version':'2.0','generator':'Lulu immutable-component assembly'},'buffers':[],'bufferViews':[],'accessors':[],'images':[],'samplers':[],'textures':[],'materials':[],'meshes':[],'nodes':[],'scenes':[{'name':'Static assembly','nodes':[]}],'scene':0};binary=bytearray();proof=[]
 for g,b,names,parent in specs:
  offsets={k:len(out[k]) for k in ['bufferViews','accessors','images','samplers','textures','materials']};base=len(binary);binary.extend(b)
  while len(binary)%4:binary.append(0)
  for v in g.get('bufferViews',[]):
   v=copy.deepcopy(v);assert v['buffer']==0;v['byteOffset']=v.get('byteOffset',0)+base;out['bufferViews'].append(v)
  for ac in g.get('accessors',[]):
   ac=copy.deepcopy(ac)
   if 'bufferView' in ac:ac['bufferView']+=offsets['bufferViews']
   if 'sparse' in ac:
    for k in ['indices','values']:ac['sparse'][k]['bufferView']+=offsets['bufferViews']
   out['accessors'].append(ac)
  for im in g.get('images',[]):
   im=copy.deepcopy(im)
   if 'bufferView' in im:im['bufferView']+=offsets['bufferViews']
   out['images'].append(im)
  out['samplers']+=copy.deepcopy(g.get('samplers',[]))
  for tex in g.get('textures',[]):
   tex=copy.deepcopy(tex)
   if 'source' in tex:tex['source']+=offsets['images']
   if 'sampler' in tex:tex['sampler']+=offsets['samplers']
   for ext in tex.get('extensions',{}).values():
    if 'source' in ext:ext['source']+=offsets['images']
   out['textures'].append(tex)
  def remapmat(obj):
   if isinstance(obj,dict):
    for k,v in obj.items():
     if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:v['index']+=offsets['textures']
     else:remapmat(v)
   elif isinstance(obj,list):
    for x in obj:remapmat(x)
  for mat in g.get('materials',[]):
   mat=copy.deepcopy(mat);remapmat(mat);out['materials'].append(mat)
  children=[]
  for node in g['nodes']:
   if node.get('name') not in names:continue
   assert 'children' not in node and 'skin' not in node
   me=copy.deepcopy(g['meshes'][node['mesh']]);newidx=len(out['meshes'])
   for pr in me['primitives']:
    for attr in pr['attributes']:pr['attributes'][attr]+=offsets['accessors']
    if 'indices' in pr:pr['indices']+=offsets['accessors']
    if 'material' in pr:pr['material']+=offsets['materials']
    for target in pr.get('targets',[]):
     for k in target:target[k]+=offsets['accessors']
   out['meshes'].append(me);nn=copy.deepcopy(node);nn['mesh']=newidx;children.append(len(out['nodes']));out['nodes'].append(nn)
   proof.append({'name':node['name'],'source_accessor_bytes_copied':True,'local_transform_preserved':True})
  if parent:
   pi=len(out['nodes']);out['nodes'].append({'name':'R04_BodyAssembly_UniformFit','children':children,**transform});out['scenes'][0]['nodes'].append(pi)
  else:out['scenes'][0]['nodes']+=children
  for k in ['extensionsUsed','extensionsRequired']:
   if k in g:out[k]=sorted(set(out.get(k,[])+g[k]))
 out['buffers']=[{'byteLength':len(binary)}];out['scenes'][0]['extras']={'trial':a.rev,'no_mesh_edits':True,'head_reference':'head-approved-v1','body_reference':'right-junction-r04','no_rig':True}
 js=json.dumps(out,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
 data=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary;path.write_bytes(data)
 return proof
six=['Body','Shorts','Leg_R','Leg_L','Arm_R','Arm_L']
proof=assemble([(old,ob,six,True),(head,hb,['Lulu_Head_Mirrored','Original_Crown_Ornament'],False)],O/'lulu-hybrid.glb')
assemble([(old,ob,[n['name'] for n in old['nodes']],True)],O/'old-r04-aligned.glb')
report={'revision':a.rev,'method':'Original mesh buffer bytes preserved; old body/arms/shorts/legs share only uniform parent scale and translation. Accepted head has original transform and size.','body_group_transform':transform,'components':proof,'head_unchanged':True,'geometry_edits':0,'bones':0,'animations':0,'status':'STATIC_ASSEMBLY_VISUAL_REVIEW_PENDING','files':{'candidate':'lulu-hybrid.glb','baseline':'old-r04-aligned.glb'}}
(O/'assembly.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
