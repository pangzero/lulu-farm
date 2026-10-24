import './seedling-study.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

type CropId='cabbage'|'tomato'|'corn';
type View='quarter'|'front'|'side'|'back'|'top';
type Appearance='original'|'clay'|'wire';
const crops:Record<CropId,{code:string;name:string;note:string}>={cabbage:{code:'C01',name:'卷心菜',note:'圆润子叶与中央真叶的网格研究；未制作成熟菜球。'},tomato:{code:'C02',name:'番茄',note:'子叶、分枝叶柄与浅裂真叶的网格研究；没有花果。'},corn:{code:'C03',name:'玉米',note:'窄长弧叶与中央卷心叶的网格研究；保留单子叶幼株结构。'}};
const directions:Record<View,T.Vector3>={quarter:new T.Vector3(1.35,2.25,4),front:new T.Vector3(0,.025,1),side:new T.Vector3(1,.025,0),back:new T.Vector3(0,.025,-1),top:new T.Vector3(0,1,.001)};
const $=<E extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as E;
const query=new URLSearchParams(location.search);
let cropId:CropId=query.get('crop')! in crops?query.get('crop') as CropId:'cabbage';
let view:View=query.get('view')! in directions?query.get('view') as View:'quarter';
let appearance:Appearance=['original','clay','wire'].includes(query.get('material')||'')?query.get('material') as Appearance:'original';
let version=0;
let activeFetch:AbortController|null=null;
let activeModel:T.Object3D|null=null;
let parseQueue:Promise<void>=Promise.resolve();
const stage=$('study-stage');
const scene=new T.Scene();scene.background=new T.Color('#f4f2e8');
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;
renderer.domElement.setAttribute('aria-label','可旋转的实际 Blender 幼苗网格，不是概念图片');renderer.domElement.setAttribute('role','img');stage.prepend(renderer.domElement);
scene.add(new T.HemisphereLight('#fffef8','#c4c7b6',.85));
const key=new T.DirectionalLight('#fffaf0',2);key.position.set(-3,6,4);scene.add(key);
const fill=new T.DirectionalLight('#f2f6ff',.5);fill.position.set(4,3,-2);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.MeshStandardMaterial({color:'#f4f2e8',roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.001;scene.add(floor);
const content=new T.Group();scene.add(content);
const camera=new T.OrthographicCamera(-.3,.3,.22,-.22,.001,100);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.minZoom=.25;controls.maxZoom=6;controls.maxPolarAngle=Math.PI*.95;
const loader=new GLTFLoader();
const originals=new WeakMap<T.Mesh,T.Material|T.Material[]>();
const clay=new T.MeshStandardMaterial({color:'#a3a3a3',roughness:.85}),wire=new T.MeshBasicMaterial({color:'#5a6e4b',wireframe:true});
let animation=0;
function requestRender(){if(!animation&&!document.hidden)animation=requestAnimationFrame(()=>{animation=0;renderer.render(scene,camera);renderer.domElement.dataset.triangles=String(renderer.info.render.triangles);});}
controls.addEventListener('change',requestRender);
function sync(){const url=new URL(location.href);url.search='';url.searchParams.set('crop',cropId);url.searchParams.set('material',appearance);url.searchParams.set('view',view);history.replaceState(null,'',url);}
function pressed(selector:string,attribute:string,value:string){document.querySelectorAll<HTMLButtonElement>(selector).forEach(button=>{const active=button.getAttribute(attribute)===value;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});}
function fit(){
  const aspect=Math.max(1,stage.clientWidth)/Math.max(1,stage.clientHeight),halfHeight=Math.max(.22,.18/aspect);
  camera.left=-halfHeight*aspect;camera.right=halfHeight*aspect;camera.top=halfHeight;camera.bottom=-halfHeight;camera.zoom=1;camera.up.set(0,1,0);
  const target=new T.Vector3(0,.14,0);camera.position.copy(target).addScaledVector(directions[view].clone().normalize(),8);camera.lookAt(target);camera.updateProjectionMatrix();controls.target.copy(target);controls.update();
  $('scale-note').textContent=`三株统一缩放 1.00 · 共同相机目标高度 0.14 · 重置后画幅高度 ${(halfHeight*2).toFixed(2)} 世界单位。模型保留原始高度差异。`;
  requestRender();
}
function resize(){renderer.setSize(Math.max(1,stage.clientWidth),Math.max(1,stage.clientHeight));fit();}
new ResizeObserver(resize).observe(stage);
function dispose(root:T.Object3D){
  const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>(),textures=new Set<T.Texture>(),images=new Set<ImageBitmap>();
  root.traverse(object=>{if(object instanceof T.Mesh){geometries.add(object.geometry);const assigned=originals.get(object)||object.material;for(const material of Array.isArray(assigned)?assigned:[assigned]){if(material===clay||material===wire)continue;materials.add(material);for(const value of Object.values(material))if(value instanceof T.Texture){textures.add(value);if(typeof ImageBitmap!=='undefined'&&value.image instanceof ImageBitmap)images.add(value.image);}}}});
  geometries.forEach(geometry=>geometry.dispose());textures.forEach(texture=>texture.dispose());materials.forEach(material=>material.dispose());images.forEach(image=>image.close());
}
function clear(){if(activeModel){content.remove(activeModel);dispose(activeModel);activeModel=null;}renderer.renderLists.dispose();for(const id of ['download-model','download-source']){const link=$<HTMLAnchorElement>(id);link.hidden=true;link.removeAttribute('href');}renderer.domElement.removeAttribute('data-crop');renderer.domElement.removeAttribute('data-file');for(const id of ['stat-triangles','stat-size','stat-height'])$(id).textContent='—';requestRender();}
function applyAppearance(){activeModel?.traverse(object=>{if(object instanceof T.Mesh)object.material=appearance==='original'?originals.get(object)!:appearance==='clay'?clay:wire;});pressed('[data-material]','data-material',appearance);sync();requestRender();}
function overlay(message:string,failed=false){const element=$('loading-state');element.hidden=false;element.classList.toggle('failed',failed);$('loading-message').textContent=message;$('retry-load').hidden=!failed;}
function loadConcept(current:number){
  const crop=crops[cropId],file=`/reference/seedling-concepts/B08/${crop.code}-${cropId}-seedling.png`;
  const frame=$('concept-frame'),message=document.createElement('p');message.textContent='正在读取独立幼苗概念图…';frame.replaceChildren(message);
  const download=$<HTMLAnchorElement>('download-concept');download.hidden=true;download.removeAttribute('href');
  const image=new Image();image.alt=`${crop.name}幼苗概念图，AI 生成造型参考`;image.decoding='async';
  image.onload=()=>{if(current!==version)return;frame.replaceChildren(image);download.href=file;download.download=`${crop.code}-${cropId}-seedling-concept.png`;download.hidden=false;};
  image.onerror=()=>{if(current!==version)return;message.textContent='独立幼苗概念图尚未同步到预览；实际网格可在旁边单独检查。';frame.replaceChildren(message);};
  image.src=file;
  $('concept-heading').textContent=`${crop.name} · 幼苗概念图`;
  $('concept-note').textContent='AI 图片只用于造型参考；相邻窗口读取独立 GLB，可切灰模并旋转检查。';
}
async function parseSerial(buffer:ArrayBuffer,current:number){
  const result=parseQueue.then(async()=>{if(current!==version)return null;const gltf=await loader.parseAsync(buffer,'/models/seedling-studies/r01/');if(current!==version){for(const root of gltf.scenes)dispose(root);return null;}return gltf;});parseQueue=result.then(()=>undefined,()=>undefined);return result;
}
async function show(){
  const current=++version;activeFetch?.abort();activeFetch=null;clear();
  const crop=crops[cropId],file=`/models/seedling-studies/r01/${cropId}-seedling.glb`;
  pressed('[data-crop]','data-crop',cropId);pressed('[data-view]','data-view',view);pressed('[data-material]','data-material',appearance);sync();loadConcept(current);
  $('model-heading').textContent=`${crop.name} · 实际 Blender 模型`;$('model-subtitle').textContent=`原生网格技术样例 · r01 · ${crop.note}`;$('load-summary').textContent='载入中';overlay('正在读取实际幼苗 GLB…');
  const controller=new AbortController();activeFetch=controller;
  try{
    const response=await fetch(file,{signal:controller.signal,cache:'no-store'});if(!response.ok)throw new Error(`GLB 请求失败（HTTP ${response.status}）`);
    const buffer=await response.arrayBuffer();if(current!==version)return;const bytes=buffer.byteLength;
    const gltf=await parseSerial(buffer,current);if(!gltf||current!==version)return;
    const model=gltf.scene;activeModel=model;
    model.updateMatrixWorld(true);const initialBounds=new T.Box3().setFromObject(model);if(initialBounds.isEmpty())throw new Error('模型内没有可显示的几何体');
    model.position.y-=initialBounds.min.y;
    let triangles=0;model.traverse(object=>{if(object instanceof T.Mesh){originals.set(object,object.material);triangles+=(object.geometry.index?.count||object.geometry.getAttribute('position')?.count||0)/3;}});
    content.add(model);const size=new T.Box3().setFromObject(model).getSize(new T.Vector3());
    $('stat-triangles').textContent=Math.round(triangles).toLocaleString('zh-CN');$('stat-size').textContent=`${(bytes/1000).toFixed(1)} KB`;$('stat-height').textContent=`${size.y.toFixed(3)} 单位`;
    applyAppearance();fit();
    const modelLink=$<HTMLAnchorElement>('download-model');modelLink.href=file;modelLink.download=`${cropId}-seedling-study-r01.glb`;modelLink.hidden=false;
    const source=$<HTMLAnchorElement>('download-source');source.href=`/models/seedling-studies/r01/source/${cropId}-seedling.blend`;source.download=`${cropId}-seedling-study-r01.blend`;source.hidden=false;
    renderer.domElement.dataset.crop=cropId;renderer.domElement.dataset.file=file;$('loading-state').hidden=true;$('load-summary').textContent='真实 GLB 已载入';$('render-status').textContent=`${crop.name} · 单株按需渲染`;requestRender();
  }catch(error){if(current!==version||controller.signal.aborted)return;clear();overlay(`模型载入失败：${error instanceof Error?error.message:String(error)}`,true);$('load-summary').textContent='载入失败';console.error(error);}
  finally{if(activeFetch===controller)activeFetch=null;}
}
document.querySelectorAll<HTMLButtonElement>('[data-crop]').forEach(button=>button.onclick=()=>{cropId=button.dataset.crop as CropId;void show();});
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>button.onclick=()=>{view=button.dataset.view as View;pressed('[data-view]','data-view',view);sync();fit();});
document.querySelectorAll<HTMLButtonElement>('[data-material]').forEach(button=>button.onclick=()=>{appearance=button.dataset.material as Appearance;applyAppearance();});
$('reset-view').onclick=()=>{view='quarter';pressed('[data-view]','data-view',view);sync();fit();};$('retry-load').onclick=()=>void show();
document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(animation);animation=0;}else requestRender();});
window.addEventListener('pagehide',()=>{++version;activeFetch?.abort();cancelAnimationFrame(animation);animation=0;clear();});window.addEventListener('pageshow',event=>{if(event.persisted)void show();});
renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();overlay('图形预览已中断，请重新读取模型。',true);});renderer.domElement.addEventListener('webglcontextrestored',()=>void show());
resize();void show();
