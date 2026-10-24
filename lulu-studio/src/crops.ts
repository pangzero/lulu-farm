import './crops.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

type Stage='sprout'|'growing'|'mature';
type Mode=Stage|'compare'|'field'|'overview'|'versions';
type Revision='v1'|'v2';
type Appearance='original'|'clay'|'wire';
type View='quarter'|'front'|'side'|'top';
type StageEntry={file:string;bytes:number;triangles:number;meshes:number;materials:number;stage:Stage};
type Crop={id:string;name:string;code:string;source:string;stages:StageEntry[]};
type CropStudy=StageEntry&{source:string;name:string};
type Label={element:HTMLSpanElement;point:T.Vector3};
const $=<E extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as E;
const stage=$('crop-stage');
const stages:Stage[]=['sprout','growing','mature'];
const stageNames={sprout:'幼苗',growing:'成长',mature:'成熟'};
const icons=['🥬','🍅','🌽','🥒','🎃','🌻','🌾','🥬','🌹','🍓','🥦','🥒','🍉','🌷','🥬','🌱'];
const tints=['#e2edcb','#f6ded0','#f7ecc2','#deebcd','#f7e3c5','#f5eac3','#f1e8c9','#e3edda','#f5dfe6','#f5ded9','#e8ecd4','#deead7','#e0ead4','#f5e1d1','#e4edce','#e7eed9'];
const query=new URLSearchParams(location.search);
let catalog:Crop[]=[];
let studies:Record<string,CropStudy>={};
let cropId=query.get('crop')??'cabbage';
const validModes=['sprout','growing','mature','compare','field','overview','versions'];
let mode:Mode=validModes.includes(query.get('mode')??'')?query.get('mode') as Mode:'compare';
let revision:Revision=query.get('revision')==='v1'?'v1':'v2';
let view:View='quarter';
let appearance:Appearance='original';
let request=0;
let labels:Label[]=[];
const cards=new Map<string,HTMLButtonElement>();
const cache=new Map<string,Promise<T.Group>>();
const loader=new GLTFLoader();
const originalMaterials=new WeakMap<T.Mesh,T.Material|T.Material[]>();
const clay=new T.MeshStandardMaterial({color:'#cdd2bd',roughness:1});
const wire=new T.MeshBasicMaterial({color:'#637b4d',wireframe:true});
const soilMat=new T.MeshStandardMaterial({color:'#b28760',roughness:1});
const tileGeometry=new T.BoxGeometry(1.12,.07,1.12);
const tileEdge=new T.EdgesGeometry(tileGeometry,30);
const edgeMat=new T.LineBasicMaterial({color:'#d6bd95',transparent:true,opacity:.4});
const renderer=new T.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.8));
renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
renderer.domElement.setAttribute('aria-label','可旋转的作物三维模型');renderer.domElement.setAttribute('role','img');stage.prepend(renderer.domElement);
const scene=new T.Scene();scene.background=new T.Color('#f9faf4');
scene.add(new T.HemisphereLight('#fffdf0','#cbd3b1',1.25));
const key=new T.DirectionalLight('#fffaf0',1.7);key.position.set(-3,6,4);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-5,right:5,top:5,bottom:-5,near:.1,far:20});key.shadow.normalBias=.012;scene.add(key);
const fill=new T.DirectionalLight('#f2f7ff',.65);fill.position.set(4,3,-2);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.ShadowMaterial({color:'#5d6f3d',opacity:.12}));floor.rotation.x=-Math.PI/2;floor.position.y=-.09;floor.receiveShadow=true;scene.add(floor);
const content=new T.Group();scene.add(content);
const camera=new T.OrthographicCamera(-3,3,2,-2,.01,100);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minZoom=.35;controls.maxZoom=7;controls.maxPolarAngle=Math.PI*.88;controls.autoRotateSpeed=.65;
const directions:Record<View,T.Vector3>={quarter:new T.Vector3(.25,.42,1).normalize(),front:new T.Vector3(0,.08,1).normalize(),side:new T.Vector3(1,.14,0).normalize(),top:new T.Vector3(0,1,.001).normalize()};
const bounds=new T.Box3();
function fit(){
  bounds.setFromObject(content);if(bounds.isEmpty())return;
  const center=bounds.getCenter(new T.Vector3()),size=bounds.getSize(new T.Vector3());
  const direction=view==='quarter'&&mode==='overview'?new T.Vector3(.12,1.15,1).normalize():view==='quarter'&&mode==='field'?new T.Vector3(.23,.80,1).normalize():directions[view];
  controls.target.copy(center);camera.position.copy(center).addScaledVector(direction,12);camera.up.set(0,1,0);camera.lookAt(center);
  const right=new T.Vector3(1,0,0).applyQuaternion(camera.quaternion),up=new T.Vector3(0,1,0).applyQuaternion(camera.quaternion);
  let hw=0,hh=0;
  for(const x of [bounds.min.x,bounds.max.x])for(const y of [bounds.min.y,bounds.max.y])for(const z of [bounds.min.z,bounds.max.z]){const p=new T.Vector3(x,y,z).sub(center);hw=Math.max(hw,Math.abs(p.dot(right)));hh=Math.max(hh,Math.abs(p.dot(up)));}
  const aspect=stage.clientWidth/Math.max(1,stage.clientHeight),half=Math.max(hh,hw/aspect,.30)*1.34+.12;
  camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;camera.zoom=1;camera.updateProjectionMatrix();
  const shift=half*(stage.classList.contains('expanded')?.10:.27);camera.position.addScaledVector(up,-shift);controls.target.addScaledVector(up,-shift);controls.update();
  key.target.position.copy(center);scene.add(key.target);key.position.copy(center).add(new T.Vector3(-3,6,4));
  $('render-status').textContent=`WebGL · ${size.x.toFixed(2)} × ${size.y.toFixed(2)} × ${size.z.toFixed(2)}`;
}
function resize(){renderer.setSize(stage.clientWidth,stage.clientHeight);fit();}
new ResizeObserver(resize).observe(stage);
function modelURL(file:string){return file.startsWith('/')?file:'/models/crops/'+file;}
function mature(crop:Crop,version:Revision=revision):StageEntry{return version==='v2'&&studies[crop.id]?studies[crop.id]:crop.stages.find(s=>s.stage==='mature')!;}
function load(file:string){
  let promise=cache.get(file);
  if(!promise){promise=loader.loadAsync(modelURL(file)).then(g=>{g.scene.traverse(o=>{if(o instanceof T.Mesh){o.castShadow=true;o.receiveShadow=true;}});return g.scene;}).catch(e=>{cache.delete(file);throw e;});cache.set(file,promise);}
  return promise;
}
function material(){content.traverse(o=>{if(o instanceof T.Mesh&&originalMaterials.has(o))o.material=appearance==='original'?originalMaterials.get(o)!:appearance==='clay'?clay:wire;});}
function plant(source:T.Group,x:number,z:number){const o=source.clone(true);o.position.set(x,0,z);o.traverse(c=>{if(c instanceof T.Mesh)originalMaterials.set(c,c.material);});content.add(o);return o;}
function tile(x:number,z:number){const box=new T.Mesh(tileGeometry,soilMat);box.position.set(x,-.045,z);box.receiveShadow=true;const edges=new T.LineSegments(tileEdge,edgeMat);box.add(edges);content.add(box);}
function label(text:string,x:number,z:number){const element=document.createElement('span');element.className='plant-label';element.textContent=text;$('plant-labels').append(element);labels.push({element,point:new T.Vector3(x,-.035,z+(mode==='overview'?.29:.38))});}
function pressed(selector:string,attr:string,value:string){document.querySelectorAll<HTMLButtonElement>(selector).forEach(b=>{const active=b.getAttribute(attr)===value;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});}
async function show(){
  const token=++request,crop=catalog.find(c=>c.id===cropId)!;
  const study=studies[crop.id];
  if(mode==='versions'&&!study)mode='compare';
  const useStudy=revision==='v2'&&Boolean(study);
  $('revision-controls').hidden=!(study||mode==='overview');
  pressed('[data-revision]','data-revision',mode==='versions'?'':revision);
  stage.classList.toggle('overview',mode==='overview');
  const loading=$('loading-state');loading.hidden=false;loading.classList.remove('failed');$('retry-load').hidden=true;$('loading-message').textContent='正在载入作物…';
  $('crop-title').textContent=mode==='overview'?'16 种作物 · 成熟总览':mode==='versions'?crop.name+' · 新旧对照':mode==='mature'&&useStudy?crop.name+' · 试改 v2':crop.name+' · 生长研究';
  $('crop-subtitle').textContent=mode==='versions'?'左：原版 v1 / 右：试改 v2 · 同尺度、同灯光':mode==='overview'?`每格 1.2 × 1.2 · 卷心菜使用${revision==='v2'?'试改 v2':'原版 v1'}`:useStudy?(mode==='compare'?'幼苗、成长：原版 v1；成熟：试改 v2（待定稿）':mode==='sprout'||mode==='growing'?'该阶段目前保留原版 v1':'试改 v2 成熟态 · 质量打样，待定稿'):mode==='field'?'平整方格田地 · 3 × 3 成片种植':'幼苗、成长、成熟使用真实大小差异';
  cards.forEach((b,id)=>{b.classList.toggle('active',id===cropId&&mode!=='overview');b.setAttribute('aria-pressed',String(id===cropId&&mode!=='overview'));});
  pressed('[data-mode]','data-mode',mode);$('overview').classList.toggle('active',mode==='overview');$('overview').setAttribute('aria-pressed',String(mode==='overview'));
  const jobs:{crop:Crop;entry:StageEntry;x:number;z:number;text?:string;soil:boolean}[]=[];
  if(mode==='overview')catalog.forEach((c,i)=>jobs.push({crop:c,entry:mature(c),x:(i%4-1.5)*1.4,z:(Math.floor(i/4)-1.5)*1.4,text:c.name+(revision==='v2'&&studies[c.id]?' · v2':''),soil:true}));
  else if(mode==='versions'){jobs.push({crop,entry:mature(crop,'v1'),x:-.64,z:0,text:'原版 v1',soil:false},{crop,entry:study,x:.64,z:0,text:'试改 v2 · 待定稿',soil:false});}
  else if(mode==='field'){for(let z=0;z<3;z++)for(let x=0;x<3;x++)jobs.push({crop,entry:mature(crop),x:(x-1)*1.2,z:(z-1)*1.2,soil:true});}
  else if(mode==='compare')stages.forEach((s,i)=>jobs.push({crop,entry:s==='mature'?mature(crop):crop.stages.find(v=>v.stage===s)!,x:(i-1)*1.35,z:0,text:stageNames[s]+(s==='mature'&&useStudy?' · 试改 v2':''),soil:false}));
  else jobs.push({crop,entry:mode==='mature'?mature(crop):crop.stages.find(v=>v.stage===mode)!,x:0,z:0,soil:false});
  try{
    const models=await Promise.all(jobs.map(j=>load(j.entry.file)));if(token!==request)return;
    content.clear();$('plant-labels').replaceChildren();labels=[];
    jobs.forEach((j,i)=>{plant(models[i],j.x,j.z);if(j.soil)tile(j.x,j.z);if(j.text)label(j.text,j.x,j.z);});material();
    floor.position.y=mode==='field'||mode==='overview'?-.085:-.008;
    const unique=[...new Map(jobs.map(j=>[j.entry.file,j.entry])).values()];
    $('stat-triangles').textContent=new Intl.NumberFormat('zh-CN').format(jobs.reduce((n,j)=>n+j.entry.triangles,0));
    $('stat-files').textContent=String(unique.length);$('stat-size').textContent=(unique.reduce((n,j)=>n+j.bytes,0)/1024).toFixed(0)+' KB';
    $('load-summary').textContent=mode==='overview'?'16 种已载入':mode==='versions'?'v1 / v2 已载入':mode==='compare'?'3 个阶段已载入':`${jobs.length} 株已载入`;
    const current:Stage=stages.includes(mode as Stage)?mode as Stage:'mature';
    const entry=mode==='versions'?study:current==='mature'?mature(crop):crop.stages.find(s=>s.stage===current)!;
    const download=$<HTMLAnchorElement>('download-crop');download.hidden=mode==='overview';download.href=modelURL(entry.file);download.download=entry.file.split('/').pop()!;download.textContent=mode==='versions'||current==='mature'&&useStudy?'下载试改 v2 GLB ↓':'下载'+stageNames[current]+' GLB ↓';
    $('file-info').textContent=mode==='overview'?`16 份原版 .blend · 卷心菜${revision==='v2'?'另含试改 v2':'使用原版 v1'}`:mode==='versions'?'原版 v1 与试改 v2 · 共用相机、灯光和世界尺度':current==='mature'&&useStudy?study.source+' · 成熟态试改，待定稿':crop.source+' · 原生几何 / 无贴图依赖';
    loading.hidden=true;fit();
    const url=new URL(location.href);url.searchParams.set('crop',cropId);url.searchParams.set('mode',mode);url.searchParams.set('revision',revision);history.replaceState(null,'',url);
  }catch(e){if(token!==request)return;loading.classList.add('failed');$('loading-message').textContent='模型载入失败，请重试';$('retry-load').hidden=false;$('load-summary').textContent='载入失败';console.error(e);}
}
document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode as Mode;if(mode==='versions')cropId='cabbage';void show();});
document.querySelectorAll<HTMLButtonElement>('[data-revision]').forEach(b=>b.onclick=()=>{revision=b.dataset.revision as Revision;if(mode==='versions')mode='mature';void show();});
$('overview').onclick=()=>{mode='overview';void show();};$('retry-load').onclick=()=>void show();
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view as View;controls.autoRotate=false;pressed('[data-view]','data-view',view);$('auto-rotate').classList.remove('active');$('auto-rotate').setAttribute('aria-pressed','false');fit();});
document.querySelectorAll<HTMLButtonElement>('[data-material]').forEach(b=>b.onclick=()=>{appearance=b.dataset.material as Appearance;pressed('[data-material]','data-material',appearance);material();});
$('reset-view').onclick=()=>{view='quarter';pressed('[data-view]','data-view',view);fit();};
$('auto-rotate').onclick=()=>{controls.autoRotate=!controls.autoRotate;$('auto-rotate').classList.toggle('active',controls.autoRotate);$('auto-rotate').setAttribute('aria-pressed',String(controls.autoRotate));};
function expand(value:boolean){stage.classList.toggle('expanded',value);$('expand-canvas').setAttribute('aria-pressed',String(value));$('expand-canvas').textContent=value?'收起画布 ×':'放大画布 ⤢';resize();}
$('expand-canvas').onclick=()=>expand(!stage.classList.contains('expanded'));
document.addEventListener('keydown',e=>{if(e.key==='Escape')expand(false);});
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);for(const l of labels){const p=l.point.clone().project(camera);l.element.style.left=((p.x*.5+.5)*stage.clientWidth)+'px';l.element.style.top=((-p.y*.5+.5)*stage.clientHeight)+'px';l.element.hidden=p.z>1||p.z< -1;}});
async function init(){try{
  const [response,studyData]=await Promise.all([fetch('/models/crops/manifest.json'),fetch('/models/crop-studies/manifest.json',{cache:'no-store'}).then(r=>r.ok?r.json():{}).catch(()=>({}))]);
  if(!response.ok)throw new Error('资产清单缺失');const data=await response.json();catalog=data.crops;studies=studyData;
  if(!catalog.length)throw new Error('作物库为空');if(!catalog.some(c=>c.id===cropId))cropId=catalog[0].id;
  $('crop-count').textContent=`${catalog.length} 种 / ${catalog.length*3} 个阶段`;
  catalog.forEach((c,i)=>{const b=document.createElement('button');b.className='crop-card';b.style.setProperty('--tint',tints[i]);b.setAttribute('aria-label','查看'+c.name);b.innerHTML=`<span class="crop-swatch" aria-hidden="true">${icons[i]}</span><span><strong>${c.name}</strong><small>${c.code} · 3 阶段</small></span>`;b.onclick=()=>{cropId=c.id;if(mode==='overview')mode='compare';void show();};cards.set(c.id,b);$('crop-list').append(b);});
  await show();
}catch(e){$('loading-state').classList.add('failed');$('loading-message').textContent='作物库暂未就绪，请刷新页面';$('load-summary').textContent='清单载入失败';console.error(e);}}
void init();
