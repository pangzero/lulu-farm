import './b04.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const $ = <E extends HTMLElement = HTMLElement>(id:string) => document.getElementById(id) as E;
const select = (id:string) => $<HTMLSelectElement>(id);
const query = new URLSearchParams(location.search);
const currentRevision='r02';
const cropIds = ['bokchoy','lettuce','cauliflower'] as const;
const names:Record<string,string> = {bokchoy:'小白菜',lettuce:'生菜',cauliflower:'花椰菜'};
const repairNotes:Record<string,string> = {
  bokchoy:'叶柄已改善，但绿叶仍有尖角和削切感。',
  lettuce:'三重同心碗和中央规则孔、等高环壁仍明显；卷曲集中在叶缘，叶身缺少疏松错落。',
  cauliflower:'花球仍像尖瘤白块，缺少圆钝的花簇层次。'
};
const directions:Record<string,T.Vector3> = {
  quarter:new T.Vector3(1.35,2.25,4), front:new T.Vector3(0,.025,1),
  side:new T.Vector3(1,.025,0), back:new T.Vector3(0,.025,-1), top:new T.Vector3(0,1,.001)
};
for (const id of ['crop','revision','layout','material']) {
  const value=query.get(id);
  if(value && Array.from(select(id).options).some(option=>option.value===value)) select(id).value=value;
}
let view = query.get('view') || 'quarter';
if(!(view in directions)) view='quarter';
let request=0;
const scene=new T.Scene();
scene.background=new T.Color('#f4f2e8');
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);
renderer.setSize(1280,720);
renderer.outputColorSpace=T.SRGBColorSpace;
renderer.toneMapping=T.NoToneMapping;
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=T.PCFSoftShadowMap;
$('stage').append(renderer.domElement);
renderer.domElement.setAttribute('aria-label','B04 三个成熟态的实际 GLB 预览');
scene.add(new T.HemisphereLight('#fffef8','#c4c7b6',.85));
const key=new T.DirectionalLight('#fffaf0',2);
key.position.set(-3,6,4);key.castShadow=true;key.shadow.mapSize.set(2048,2048);
Object.assign(key.shadow.camera,{left:-10,right:10,top:10,bottom:-10,near:.1,far:30});
key.shadow.normalBias=.02;scene.add(key);
const fill=new T.DirectionalLight('#f2f6ff',.5);fill.position.set(4,3,-2);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.MeshStandardMaterial({color:'#f4f2e8',roughness:1}));
floor.rotation.x=-Math.PI/2;floor.position.y=-.014;floor.receiveShadow=true;scene.add(floor);
const camera=new T.OrthographicCamera(-2,2,1.125,-1.125,.01,100);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
const content=new T.Group();scene.add(content);
const loader=new GLTFLoader();
const cache=new Map<string,Promise<T.Group>>();
const originals=new WeakMap<T.Mesh,T.Material|T.Material[]>();
const clay=new T.MeshStandardMaterial({color:'#a3a3a3',roughness:.85});
const wire=new T.MeshBasicMaterial({color:'#5a6e4b',wireframe:true});
const tileGeometry=new T.BoxGeometry(1.17,.03,1.17);
const tileMaterial=new T.MeshStandardMaterial({color:'#dddccf',roughness:1});
const luluScale=.6313689262131015;

function file(crop:string,revision:string) {
  return revision==='v1'?`/models/crops/${crop}-mature.glb`:`/models/farm-assets/B04/${crop}-mature-${revision}.glb`;
}
function load(path:string) {
  if(!cache.has(path)) cache.set(path,loader.loadAsync(path).then(gltf=>gltf.scene).catch(error=>{cache.delete(path);throw error;}));
  return cache.get(path)!;
}
function plant(source:T.Group,x=0,z=0,scale=1) {
  const object=source.clone(true);object.position.set(x,0,z);object.scale.multiplyScalar(scale);
  object.traverse(node=>{if(node instanceof T.Mesh){node.castShadow=true;node.receiveShadow=true;originals.set(node,node.material);}});
  content.add(object);return object;
}
function tile(x:number,z:number) {
  const object=new T.Mesh(tileGeometry,tileMaterial);object.position.set(x,-.03,z);object.receiveShadow=true;content.add(object);
}
function saveQuery() {
  for(const id of ['crop','revision','layout','material']) query.set(id,select(id).value);
  query.set('view',view);history.replaceState(null,'','?'+query.toString());
}
function appearance() {
  content.traverse(object=>{if(object instanceof T.Mesh && originals.has(object)) {
    object.material=select('material').value==='clay'?clay:select('material').value==='wire'?wire:originals.get(object)!;
  }});
}
function fit() {
  const crop=select('crop').value,layout=select('layout').value;
  let height=1.65;
  const target=new T.Vector3(0,crop==='bokchoy'?.45:crop==='lettuce'?.30:.32,0);
  const direction=directions[view].clone().normalize();
  if(layout==='compare') height=2.1;
  if(layout==='types'){height=2.6;target.set(0,.43,0);}
  if(layout==='field'){height=4.3;target.set(0,.4,0);}
  if(layout==='farm') {
    height=14.1;target.set(0,0,0);
    const elevation=T.MathUtils.degToRad(50);
    direction.set(Math.cos(elevation)/Math.sqrt(2),Math.sin(elevation),Math.cos(elevation)/Math.sqrt(2));
    view='quarter';controls.autoRotate=false;$('rotate').classList.remove('active');
  }
  camera.left=-height*1280/720/2;camera.right=-camera.left;camera.top=height/2;camera.bottom=-height/2;
  camera.zoom=1;camera.updateProjectionMatrix();camera.position.copy(target).addScaledVector(direction,20);
  controls.target.copy(target);camera.lookAt(target);controls.update();
  document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>button.classList.toggle('active',button.dataset.view===view));
  renderer.domElement.dataset.layout=layout;renderer.domElement.dataset.view=view;
  renderer.domElement.dataset.orthographicHeight=String(height);saveQuery();
}
async function show(preserveCamera=false) {
  const currentRequest=++request,crop=select('crop').value,layout=select('layout').value;
  const candidateScene=layout==='compare'||layout==='types'||layout==='farm';
  select('revision').disabled=candidateScene;
  if(candidateScene) select('revision').value=currentRevision;
  const revision=select('revision').value;
  $('status').textContent='正在载入实际 GLB…';$('status').classList.remove('error','review-warning');
  try {
    const current=await load(file(crop,revision));
    const companion=layout==='compare'?await load(file(crop,'v1')):null;
    const models=(layout==='farm'||layout==='types')?await Promise.all(cropIds.map(id=>load(file(id,currentRevision)))):[];
    const lulu=layout==='farm'?await load('/models/lulu-meshy-notail.glb'):null;
    if(currentRequest!==request)return;
    content.clear();floor.position.y=layout==='field'||layout==='farm'?-.052:-.014;
    let count=0;
    if(layout==='single'){plant(current);count=1;}
    else if(layout==='compare'){plant(companion!,-.8);plant(current,.8);count=2;}
    else if(layout==='types'){models.forEach((model,index)=>plant(model,(index-1)*1.2));count=3;}
    else if(layout==='field') {
      for(let x=-1;x<=1;x++)for(let z=-1;z<=1;z++){plant(current,x*1.2,z*1.2);tile(x*1.2,z*1.2);count++;}
    } else {
      for(let x=0;x<12;x++)for(let z=0;z<8;z++)tile((x-5.5)*1.2,(z-3.5)*1.2);
      for(let k=0;k<3;k++)for(let x=0;x<3;x++)for(let z=0;z<3;z++){plant(models[k],(k*4+x-5)*1.2,(z-1)*1.2);count++;}
      const luluInstance=plant(lulu!,0,3.6,luluScale),box=new T.Box3().setFromObject(luluInstance);
      luluInstance.position.y-=box.min.y;
    }
    appearance();
    if(preserveCamera) saveQuery();else fit();
    const size=new T.Box3().setFromObject(current).getSize(new T.Vector3());
    $('dimensions').textContent=`单株 ${size.x.toFixed(2)} × ${size.y.toFixed(2)} × ${size.z.toFixed(2)} · 画布 1280 × 720`;
    const allTypes=layout==='farm'||layout==='types';
    const needsRepair=revision===currentRevision && crop in repairNotes;
    const artStatus=revision===currentRevision?'需返修':revision==='r01'?'首轮历史版本，未获美术认可':'历史对照，未获美术认可';
    $('status').textContent=allTypes?`B04 ${currentRevision} · 三种成熟态 · 已载入 ${count} 株 · 含需返修候选，不代表美术通过`:`${names[crop]} · ${revision} · 成熟态 · 已载入 ${count} 株 · ${artStatus}`;
    $('status').classList.toggle('review-warning',allTypes||needsRepair);
    $('review-note').textContent=allTypes?'r02 三项均需返修：小白菜绿叶有尖角和削切感；生菜有同心碗、中央规则孔及等高环壁；花椰菜花球像尖瘤白块，缺少圆钝花簇。已停止当前建模做法，保留失败证据供检查；三项均未获用户美术通过。':needsRepair?`${names[crop]} r02 需返修：${repairNotes[crop]} 已停止当前建模做法，保留实际文件与失败证据；未获用户美术通过。`:`${revision} 为历史对照版本，未获用户美术认可。`;
    $('review-note').classList.toggle('review-warning',allTypes||needsRepair);
    $('comparison').textContent=layout==='compare'?`左：初版 v1　右：${revision} · 同尺度同灯光`:layout==='types'?'三种并排 · 不加文字标签 · 保持世界尺度':layout==='farm'?'Lulu 高 1.2；三类各 9 株；固定农场镜头':layout==='field'?'同类 3 × 3 · 株距 1.2 单位':'仅成熟态；幼苗和成长态不属于本批';
    $<HTMLAnchorElement>('download').href=file(crop,revision);
    $<HTMLAnchorElement>('source').href='/@fs/Users/haowen/GameProject/farm-game/lulu-studio/'+(revision==='v1'?`assets-source/crops/${crop}.blend`:`assets-source/farm-assets/B04/${crop}-mature-${revision}.blend`);
  } catch(error) {
    if(currentRequest!==request)return;
    content.clear();$('status').textContent='实际 GLB 载入失败：'+String(error);$('status').classList.add('error');console.error(error);
  }
}
for(const id of ['crop','layout']) select(id).onchange=()=>void show();
select('revision').onchange=()=>void show(true);
select('material').onchange=()=>{appearance();saveQuery();};
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>button.onclick=()=>{view=button.dataset.view!;controls.autoRotate=false;$('rotate').classList.remove('active');fit();});
$('rotate').onclick=()=>{
  if(select('layout').value==='farm') return;
  controls.autoRotate=!controls.autoRotate;$('rotate').classList.toggle('active',controls.autoRotate);
};
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
void show();
