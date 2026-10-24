import './crops-meshy.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

type Stage='seedling'|'mature';
type Appearance='original'|'clay'|'wire';
type View='quarter'|'front'|'side'|'back'|'top';
type Crop={id:string;name:string;code:string;batch:string;status:'available'|'pending';file:string|null;bytes:number;triangles:number;common_scale:number;revision:string;original_name?:string;source?:string;art_status:string;missing_note?:string;thumbnail?:string};
type Catalog={revision:string;updated:string;stage_policy:Stage[];crops:Crop[]};
const $=<E extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as E;
const stageElement=$('crop-stage');
const query=new URLSearchParams(location.search);
const views:Record<View,T.Vector3>={quarter:new T.Vector3(1.35,2.25,4),front:new T.Vector3(0,.025,1),side:new T.Vector3(1,.025,0),back:new T.Vector3(0,.025,-1),top:new T.Vector3(0,1,.001)};
let view:View=query.get('view')! in views?query.get('view') as View:'quarter';
let appearance:Appearance=['original','clay','wire'].includes(query.get('material')||'')?query.get('material') as Appearance:'original';
let selectedStage:Stage=query.get('stage')==='seedling'?'seedling':'mature';
let cropId=query.get('crop')||'cabbage';
let catalog:Catalog|null=null;
let token=0;
let activeFetch:AbortController|null=null;
let activeModel:T.Object3D|null=null;
let retryAction:()=>void=()=>void init();
let parseQueue:Promise<void>=Promise.resolve();
const cards=new Map<string,HTMLButtonElement>();
const deferredSeedlings=new Set(['zucchini','scallion']);
const originalMaterials=new WeakMap<T.Mesh,T.Material|T.Material[]>();
const clay=new T.MeshStandardMaterial({color:'#a3a3a3',roughness:.85});
const wire=new T.MeshBasicMaterial({color:'#5a6e4b',wireframe:true});
const loader=new GLTFLoader();
const scene=new T.Scene();scene.background=new T.Color('#f4f2e8');
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));
renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;
renderer.domElement.setAttribute('aria-label','用户 Meshy 作物模型，可旋转、缩放和平移');renderer.domElement.setAttribute('role','img');
stageElement.prepend(renderer.domElement);
scene.add(new T.HemisphereLight('#fffef8','#c4c7b6',.85));
const key=new T.DirectionalLight('#fffaf0',2);key.position.set(-3,6,4);scene.add(key);
const fill=new T.DirectionalLight('#f2f6ff',.5);fill.position.set(4,3,-2);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.MeshStandardMaterial({color:'#f4f2e8',roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.014;scene.add(floor);
const content=new T.Group();scene.add(content);
const camera=new T.OrthographicCamera(-2,2,1.125,-1.125,.01,1000);camera.position.set(3,3,6);camera.lookAt(0,.4,0);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.autoRotateSpeed=.65;controls.minZoom=.2;controls.maxZoom=10;controls.maxPolarAngle=Math.PI*.95;controls.target.set(0,.4,0);controls.update();
let scheduled=0;
let lastFrame=0;
function requestRender(){if(!scheduled&&!document.hidden)scheduled=requestAnimationFrame(render);}
function render(now:number){
  scheduled=0;
  if(controls.autoRotate&&activeModel)controls.update(lastFrame?Math.min((now-lastFrame)/1000,.05):1/60);
  lastFrame=now;
  renderer.render(scene,camera);
  renderer.domElement.dataset.triangles=String(renderer.info.render.triangles);
  renderer.domElement.dataset.drawCalls=String(renderer.info.render.calls);
  if(controls.autoRotate&&activeModel)requestRender();
}
controls.addEventListener('change',requestRender);
document.addEventListener('visibilitychange',()=>{lastFrame=0;if(document.hidden){cancelAnimationFrame(scheduled);scheduled=0;}else requestRender();});
function pressed(selector:string,key:string,value:string){document.querySelectorAll<HTMLButtonElement>(selector).forEach(button=>{const active=button.getAttribute(key)===value;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});}
function sync(){const url=new URL(location.href);url.search='';url.searchParams.set('crop',cropId);url.searchParams.set('stage',selectedStage);url.searchParams.set('material',appearance);url.searchParams.set('view',view);history.replaceState(null,'',url);}
function openSeedlingPreview(){const q=new URLSearchParams({crop:cropId,stage:'seedling',material:appearance==='clay'?'clay':'color',view,layout:'single'});location.assign(`/crops-two-stage.html?${q}`);}
function stopRotation(){controls.autoRotate=false;$('auto-rotate').classList.remove('active');$('auto-rotate').setAttribute('aria-pressed','false');lastFrame=0;}
function applyAppearance(){if(activeModel)activeModel.traverse(object=>{if(object instanceof T.Mesh)object.material=appearance==='original'?originalMaterials.get(object)!:appearance==='clay'?clay:wire;});pressed('[data-material]','data-material',appearance);sync();requestRender();}
function disposeModel(root:T.Object3D){
  const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>(),textures=new Set<T.Texture>(),images=new Set<ImageBitmap>();
  root.traverse(object=>{if(object instanceof T.Mesh){geometries.add(object.geometry);const saved=originalMaterials.get(object)||object.material;for(const material of Array.isArray(saved)?saved:[saved]){if(material===clay||material===wire)continue;materials.add(material);for(const value of Object.values(material)){if(value instanceof T.Texture){textures.add(value);if(typeof ImageBitmap!=='undefined'&&value.image instanceof ImageBitmap)images.add(value.image);}}}}});
  geometries.forEach(geometry=>geometry.dispose());textures.forEach(texture=>texture.dispose());materials.forEach(material=>material.dispose());images.forEach(image=>image.close());
}
function clearModel(){if(activeModel){content.remove(activeModel);disposeModel(activeModel);activeModel=null;}renderer.renderLists.dispose();renderer.domElement.removeAttribute('data-crop');renderer.domElement.removeAttribute('data-file');const download=$<HTMLAnchorElement>('download-crop');download.hidden=true;download.removeAttribute('href');download.removeAttribute('download');for(const id of ['view-seedling-concept','download-seedling-concept']){const link=$<HTMLAnchorElement>(id);link.hidden=true;link.removeAttribute('href');}requestRender();}
function fit(){
  const bounds=new T.Box3().setFromObject(content);if(bounds.isEmpty()){requestRender();return;}
  const center=bounds.getCenter(new T.Vector3()),size=bounds.getSize(new T.Vector3());
  camera.up.set(0,1,0);camera.position.copy(center).addScaledVector(views[view].clone().normalize(),Math.max(12,size.length()*3));camera.lookAt(center);
  const right=new T.Vector3(1,0,0).applyQuaternion(camera.quaternion),up=new T.Vector3(0,1,0).applyQuaternion(camera.quaternion);
  let halfWidth=0,halfHeight=0;
  for(const x of [bounds.min.x,bounds.max.x])for(const y of [bounds.min.y,bounds.max.y])for(const z of [bounds.min.z,bounds.max.z]){const corner=new T.Vector3(x,y,z).sub(center);halfWidth=Math.max(halfWidth,Math.abs(corner.dot(right)));halfHeight=Math.max(halfHeight,Math.abs(corner.dot(up)));}
  const aspect=Math.max(stageElement.clientWidth,1)/Math.max(stageElement.clientHeight,1),half=Math.max(halfHeight,halfWidth/aspect,.15)*1.30+.04;
  camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half;camera.zoom=1;camera.far=Math.max(100,size.length()*10);camera.updateProjectionMatrix();
  controls.target.copy(center);controls.update();$('render-status').textContent=`${size.x.toFixed(2)} × ${size.y.toFixed(2)} × ${size.z.toFixed(2)} · 按需渲染`;
  requestRender();
}
function resize(){renderer.setSize(Math.max(stageElement.clientWidth,1),Math.max(stageElement.clientHeight,1));fit();}
new ResizeObserver(resize).observe(stageElement);
function overlay(message:string,state:'loading'|'empty'|'failed',retry=false){const element=$('loading-state');element.hidden=false;element.classList.toggle('empty',state==='empty');element.classList.toggle('failed',state==='failed');$('loading-message').textContent=message;$('retry-load').hidden=!retry;}
function stats(crop:Crop,available:boolean){
  $('stat-triangles').textContent=available?new Intl.NumberFormat('zh-CN').format(crop.triangles):'—';
  $('stat-size').textContent=available?`${(crop.bytes/1e6).toFixed(1)} MB`:'—';
  $('stat-revision').textContent=available?crop.revision:'待制作';
  $('stat-scale').textContent=available?String(crop.common_scale):'—';
}
async function parseSerial(buffer:ArrayBuffer,basePath:string,current:number){
  const result=parseQueue.then(async()=>{if(current!==token)return null;const gltf=await loader.parseAsync(buffer,basePath);if(current!==token){for(const root of gltf.scenes)disposeModel(root);return null;}return gltf;});
  parseQueue=result.then(()=>undefined,()=>undefined);
  return result;
}
async function show(){
  if(!catalog)return;
  const current=++token;activeFetch?.abort();activeFetch=null;stopRotation();clearModel();
  const crop=catalog.crops.find(entry=>entry.id===cropId)!;
  const available=selectedStage==='mature'&&crop.status==='available'&&Boolean(crop.file);
  cards.forEach((button,id)=>{const active=id===cropId;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
  pressed('[data-stage]','data-stage',selectedStage);pressed('[data-view]','data-view',view);pressed('[data-material]','data-material',appearance);sync();
  $('crop-title').textContent=`${crop.name} · ${selectedStage==='mature'?'成熟':'幼苗'}`;
  const seedlingBatch=Number(crop.code.replace('C',''))<=8?'B08':'B09';
  $('crop-subtitle').textContent=`${crop.code} · ${selectedStage==='mature'?crop.batch:seedlingBatch} · ${available?'用户提供的最新 Meshy 原始模型':'待补充模型'}`;
  $('art-status').textContent=available?crop.art_status:'待制作';stats(crop,available);
  $('file-info').textContent=available?(crop.original_name||`${crop.id}-mature.glb`):'此阶段暂未提供 GLB';
  $('render-status').textContent='按需渲染 · 单株预览';
  $('model-note').textContent=available?'统一缩放 0.47，根部居中着地；相机仅调整取景。原始高模尚未完成游戏优化与目标设备测试。':'幼苗与成熟分开交付，不以旧阶段模型代替。';
  retryAction=()=>void show();
  if(!available){
    if(selectedStage==='seedling'){
      const deferred=deferredSeedlings.has(crop.id);
      $('load-summary').textContent=deferred?'用户暂缓':'概念图已备';
      $('art-status').textContent=deferred?'用户暂缓':'正式幼苗模型未制作';
      $('crop-subtitle').textContent=`${crop.code} · ${seedlingBatch} · ${deferred?'用户暂缓':'幼苗概念图已备，正式模型未制作'}`;
      $('file-info').textContent='正式幼苗 GLB 尚未制作；概念图片不作为模型下载。';
      $('model-note').textContent='14 种幼苗概念图已备。3 种 Blender 网格仅为技术研究，待评审，未作为 B08 成品注册。';
      overlay(deferred?`${crop.name}幼苗的概念图与正式模型均由用户暂缓。`:`${crop.name}的独立幼苗概念图已备，正式幼苗模型未制作。可打开下方 AI 造型参考图。`,'empty');
      if(!deferred){const file=`/reference/seedling-concepts/${seedlingBatch}/${crop.code}-${crop.id}-seedling.png`;for(const id of ['view-seedling-concept','download-seedling-concept']){const link=$<HTMLAnchorElement>(id);link.href=file;link.hidden=false;}const download=$<HTMLAnchorElement>('download-seedling-concept');download.download=`${crop.code}-${crop.id}-seedling-concept.png`;}
    }else{const deferred=deferredSeedlings.has(crop.id);$('load-summary').textContent=deferred?'用户暂缓':'待补充';if(deferred){$('art-status').textContent='用户暂缓';$('crop-subtitle').textContent=`${crop.code} · ${crop.batch} · 用户暂缓`;}overlay(crop.missing_note||`${crop.name}成熟模型待补充。`,'empty');}
    return;
  }
  const file=crop.file!;
  if(!file.startsWith('/models/farm-assets/')){overlay('模型路径无效，请核对资产清单。','failed');$('load-summary').textContent='路径错误';return;}
  $('load-summary').textContent='载入中';overlay(`正在读取${crop.name} · ${(crop.bytes/1e6).toFixed(1)} MB…`,'loading');
  const controller=new AbortController();activeFetch=controller;
  try{
    const response=await fetch(file,{signal:controller.signal,cache:'no-store'});
    if(!response.ok)throw new Error(`GLB 请求失败（HTTP ${response.status}）`);
    const buffer=await response.arrayBuffer();if(current!==token)return;
    overlay(`正在解析${crop.name}的真实模型与贴图…`,'loading');
    const gltf=await parseSerial(buffer,file.slice(0,file.lastIndexOf('/')+1),current);if(!gltf||current!==token)return;
    const model=gltf.scene;activeModel=model;
    const scale=Number.isFinite(crop.common_scale)&&crop.common_scale>0?crop.common_scale:.47;model.scale.multiplyScalar(scale);model.updateMatrixWorld(true);
    const bounds=new T.Box3().setFromObject(model);if(bounds.isEmpty())throw new Error('GLB 中没有可显示的几何体');
    const center=bounds.getCenter(new T.Vector3());model.position.add(new T.Vector3(-center.x,-bounds.min.y,-center.z));
    model.traverse(object=>{if(object instanceof T.Mesh)originalMaterials.set(object,object.material);});content.add(model);
    applyAppearance();fit();
    const download=$<HTMLAnchorElement>('download-crop');download.href=file;download.download=crop.original_name||`${crop.id}-mature-${crop.revision}.glb`;download.hidden=false;
    $('loading-state').hidden=true;$('load-summary').textContent='实际模型已载入';renderer.domElement.dataset.crop=crop.id;renderer.domElement.dataset.file=file;requestRender();
  }catch(error){
    if(current!==token||controller.signal.aborted)return;
    clearModel();$('load-summary').textContent='载入失败';overlay(`模型载入失败：${error instanceof Error?error.message:String(error)}`,'failed',true);console.error(error);
  }finally{if(activeFetch===controller)activeFetch=null;}
}
const icons:Record<string,string>={cabbage:'🥬',tomato:'🍅',corn:'🌽',cucumber:'🥒',pumpkin:'🎃',sunflower:'🌻',wheat:'🌾',bokchoy:'🥬',rose:'🌹',strawberry:'🍓',cauliflower:'🥦',zucchini:'🥒',watermelon:'🍉',tulip:'🌷',lettuce:'🥬',scallion:'🌱'};
function buildLibrary(crops:Crop[]){
  $('crop-list').replaceChildren();cards.clear();
  for(const crop of crops){
    const button=document.createElement('button');button.className='crop-card'+(crop.status==='pending'?' pending':'');button.setAttribute('aria-label',`查看${crop.name}${crop.status==='pending'?(deferredSeedlings.has(crop.id)?'，用户暂缓':'，成熟模型待补'):''}`);button.setAttribute('aria-pressed','false');button.style.setProperty('--tint',crop.status==='pending'?'#eceade':'#e2edda');
    const icon=document.createElement('span');icon.className='crop-swatch';icon.setAttribute('aria-hidden','true');
    if(crop.thumbnail?.startsWith('/reference/crops-meshy/')){const image=document.createElement('img');image.src=crop.thumbnail;image.alt='';image.loading='lazy';image.decoding='async';icon.append(image);}else icon.textContent=icons[crop.id]||'🌱';
    const text=document.createElement('span'),name=document.createElement('strong'),meta=document.createElement('small');name.textContent=crop.name;meta.textContent=`${crop.code} · ${crop.status==='available'?'成熟已提供':deferredSeedlings.has(crop.id)?'用户暂缓':'成熟待补'}`;if(crop.status==='pending')meta.className='pending-label';text.append(name,meta);button.append(icon,text);
    button.onclick=()=>{cropId=crop.id;void show();};cards.set(crop.id,button);$('crop-list').append(button);
  }
}
async function init(){
  retryAction=()=>void init();overlay('正在读取最新作物清单…','loading');
  try{
    const response=await fetch('/models/crops-meshy/manifest.json',{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);
    const data=await response.json() as Catalog;if(!Array.isArray(data.crops)||!data.crops.length)throw new Error('作物清单为空');catalog=data;
    if(!catalog.crops.some(crop=>crop.id===cropId))cropId=catalog.crops[0].id;
    const count=catalog.crops.filter(crop=>crop.status==='available'&&crop.file).length;
    $('crop-count').textContent=`${count} / ${catalog.crops.length} 已提供`;
    const deferredCount=catalog.crops.filter(crop=>deferredSeedlings.has(crop.id)&&crop.status==='pending').length;
    $('catalog-status').textContent=`${catalog.crops.length} 种 · 成熟 ${count} 已提供 / ${deferredCount} 暂缓 · 幼苗映射与卡通候选见两阶段预览`;
    if(selectedStage==='seedling'&&!deferredSeedlings.has(cropId)){openSeedlingPreview();return;}
    buildLibrary(catalog.crops);await show();
  }catch(error){$('load-summary').textContent='清单载入失败';overlay('最新作物清单未能载入，请重试。','failed',true);console.error(error);}
}
document.querySelectorAll<HTMLButtonElement>('[data-stage]').forEach(button=>button.onclick=()=>{selectedStage=button.dataset.stage as Stage;if(selectedStage==='seedling'&&!deferredSeedlings.has(cropId)){openSeedlingPreview();return;}void show();});
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>button.onclick=()=>{view=button.dataset.view as View;stopRotation();pressed('[data-view]','data-view',view);sync();fit();});
document.querySelectorAll<HTMLButtonElement>('[data-material]').forEach(button=>button.onclick=()=>{appearance=button.dataset.material as Appearance;applyAppearance();});
$('reset-view').onclick=()=>{view='quarter';stopRotation();pressed('[data-view]','data-view',view);sync();fit();};
$('auto-rotate').onclick=()=>{if(!activeModel)return;controls.autoRotate=!controls.autoRotate;$('auto-rotate').classList.toggle('active',controls.autoRotate);$('auto-rotate').setAttribute('aria-pressed',String(controls.autoRotate));lastFrame=0;requestRender();};
function expand(value:boolean){stageElement.classList.toggle('expanded',value);$('expand-canvas').setAttribute('aria-pressed',String(value));$('expand-canvas').textContent=value?'收起画布 ×':'放大画布 ⤢';resize();}
$('expand-canvas').onclick=()=>expand(!stageElement.classList.contains('expanded'));
document.addEventListener('keydown',event=>{if(event.key==='Escape')expand(false);});
$('retry-load').onclick=()=>retryAction();
window.addEventListener('pagehide',()=>{++token;activeFetch?.abort();stopRotation();cancelAnimationFrame(scheduled);scheduled=0;clearModel();});
window.addEventListener('pageshow',event=>{if(event.persisted)void show();});
renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();overlay('图形上下文已中断，请重新载入当前模型。','failed',true);$('load-summary').textContent='预览已中断';});
renderer.domElement.addEventListener('webglcontextrestored',()=>void show());
resize();void init();
