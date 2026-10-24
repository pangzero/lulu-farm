import './b14.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

type ModuleSpec={id:string;name:string;nodes?:string[];file?:string;source?:string};
type AssetSpec={id:string;name:string;file:string;source?:string;revision?:string;modules?:ModuleSpec[];triangles?:number;bytes?:number};
type Manifest={revision:string;status?:string;assets:AssetSpec[];modules?:ModuleSpec[];checks?:{technical?:string;visual?:string};revisions?:string[];versions?:Record<string,AssetSpec>};
const $=<E extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as E;
const sel=(id:string)=>$<HTMLSelectElement>(id),query=new URLSearchParams(location.search);
const queryIds=['asset','revision','module','layout','material'];
function readQuery(ids=queryIds){for(const id of ids){const value=query.get(id);if(value&&Array.from(sel(id).options).some(o=>o.value===value))sel(id).value=value;}}
readQuery();
const directions:Record<string,T.Vector3>={quarter:new T.Vector3(1.35,2.25,4),front:new T.Vector3(0,.025,1),side:new T.Vector3(1,.025,0),left:new T.Vector3(-1,.025,0),back:new T.Vector3(0,.025,-1),top:new T.Vector3(0,1,.001),door:new T.Vector3(1.35,1.1,4),roof:new T.Vector3(1.35,2.25,4)};
let view=directions[query.get('view')||'']?query.get('view')!:'quarter';
let manifest:Manifest|undefined,selectedRoot:T.Group|undefined,selectedSpec:AssetSpec|undefined,token=0,abort:AbortController|undefined,loaded:T.Group[]=[];
const originalMaterials=new WeakMap<T.Mesh,T.Material|T.Material[]>();
const scene=new T.Scene();scene.background=new T.Color('#f4f2e8');
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(1280,720);renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;renderer.toneMappingExposure=1;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
$('stage').append(renderer.domElement);renderer.domElement.setAttribute('aria-label','B14 中央主屋实际 GLB 三维预览');
scene.add(new T.HemisphereLight('#fffef8','#c4c7b6',.85));
const key=new T.DirectionalLight('#fffaf0',2);key.position.set(-3,6,4);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-10,right:10,top:10,bottom:-10,near:.1,far:40});key.shadow.normalBias=.02;scene.add(key);
const fill=new T.DirectionalLight('#f2f6ff',.5);fill.position.set(4,3,-2);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.MeshStandardMaterial({color:'#f4f2e8',roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.014;floor.receiveShadow=true;scene.add(floor);
const camera=new T.OrthographicCamera(-2,2,1.125,-1.125,.01,100),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
const content=new T.Group(),grid=new T.Group();scene.add(content,grid);
const loader=new GLTFLoader(),clay=new T.MeshStandardMaterial({color:'#a3a3a3',roughness:.85}),wire=new T.MeshBasicMaterial({color:'#5a6e4b',wireframe:true});
const tileGeometry=new T.BoxGeometry(1.17,.03,1.17),tileMaterial=new T.MeshStandardMaterial({color:'#dddccf',roughness:1});
for(let x=0;x<12;x++)for(let z=0;z<8;z++){const tile=new T.Mesh(tileGeometry,tileMaterial);tile.position.set((x-5.5)*1.2,-.015,(z-3.5)*1.2);tile.receiveShadow=true;grid.add(tile);}grid.visible=false;

function dispose(root:T.Object3D){
  const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>(),textures=new Set<T.Texture>();
  root.traverse(object=>{if(object instanceof T.Mesh){geometries.add(object.geometry);const m=originalMaterials.get(object)||object.material;for(const material of Array.isArray(m)?m:[m])materials.add(material);}});
  for(const material of materials){for(const value of Object.values(material)){if(value instanceof T.Texture)textures.add(value);}material.dispose();}
  geometries.forEach(g=>g.dispose());textures.forEach(t=>{t.dispose();const image=t.source?.data;if(image instanceof ImageBitmap)image.close();});
}
function unload(){content.clear();loaded.forEach(dispose);loaded=[];selectedRoot=undefined;selectedSpec=undefined;renderer.renderLists.dispose();}
async function load(path:string,signal:AbortSignal,current:number){
  const response=await fetch(path,{signal,cache:'no-store'});if(!response.ok)throw new Error(`${path} · HTTP ${response.status}`);
  const bytes=await response.arrayBuffer();if(signal.aborted||current!==token)throw new DOMException('旧请求已取消','AbortError');
  const gltf=await loader.parseAsync(bytes,path.slice(0,path.lastIndexOf('/')+1));
  if(signal.aborted||current!==token){dispose(gltf.scene);throw new DOMException('旧请求已取消','AbortError');}
  const root=gltf.scene;root.traverse(object=>{if(object instanceof T.Mesh){object.castShadow=true;object.receiveShadow=true;originalMaterials.set(object,object.material);}});loaded.push(root);return root;
}
function setDownload(id:string,path?:string){const link=$<HTMLAnchorElement>(id);if(path){link.href=path.startsWith('assets-source/')?'/@fs/Users/haowen/GameProject/farm-game/lulu-studio/'+path:path;link.setAttribute('aria-disabled','false');}else{link.removeAttribute('href');link.setAttribute('aria-disabled','true');}}
function currentHouse(){return manifest?.versions?.[sel('revision').value]||manifest?.assets.find(a=>a.id==='S01')||manifest?.assets[0];}
function modules(){return currentHouse()?.modules||manifest?.modules||[];}
function populateModules(){const previous=sel('module').value;sel('module').replaceChildren(new Option('完整组装','all'));for(const module of modules())sel('module').add(new Option(module.name,module.id));if(Array.from(sel('module').options).some(o=>o.value===previous))sel('module').value=previous;sel('module').disabled=sel('asset').value==='facade';}
function updateQuery(){for(const id of queryIds)query.set(id,sel(id).value);query.set('view',view);history.replaceState(null,'','?'+query.toString());}
function appearance(){content.traverse(object=>{if(object instanceof T.Mesh&&originalMaterials.has(object))object.material=sel('material').value==='clay'?clay:sel('material').value==='wire'?wire:originalMaterials.get(object)!;});updateQuery();}
function isolate(){
  const module=sel('asset').value==='house'?modules().find(m=>m.id===sel('module').value):undefined;
  if(selectedRoot){selectedRoot.traverse(object=>{if(object instanceof T.Mesh){let match=!module||Boolean(module.file);let ancestor:T.Object3D|null=object;while(!match&&ancestor){match=module?.nodes?.includes(ancestor.name)||false;ancestor=ancestor.parent;}object.visible=match;}});}
  $('module-note').textContent=module?(module.file?`独立模块：${module.name}；下载为当前模块 GLB。`:`仅隔离显示「${module.name}」，保持组装位置；下载提供完整主屋 GLB 与完整可编辑源。`):sel('asset').value==='house'?'完整组装，下载为当前主屋版本。':'B02 r04 已认可立面样段，不是完整主屋；同一相机和世界尺度对照。';
  $('download').textContent=module&&!module.file?'下载完整主屋 GLB ↓':'下载当前 GLB ↓';
  updateQuery();
}
function fit(){
  const layout=sel('layout').value;let height=7.3,target=new T.Vector3(0,2.5,0),direction=directions[view].clone().normalize();
  if(layout==='scale'){height=8.5;target.set(0,2.25,0);}
  if(view==='door'){height=3;target.set(0,1.2,1.8);}
  if(view==='roof'){height=5.8;target.set(0,4.2,0);}
  if(layout==='farm'){view='quarter';height=14.1;target.set(0,0,0);const elevation=T.MathUtils.degToRad(50);direction.set(Math.cos(elevation)/Math.sqrt(2),Math.sin(elevation),Math.cos(elevation)/Math.sqrt(2));}
  camera.left=-height*1280/720/2;camera.right=-camera.left;camera.top=height/2;camera.bottom=-height/2;camera.zoom=1;camera.updateProjectionMatrix();camera.position.copy(target).addScaledVector(direction,25);controls.target.copy(target);camera.lookAt(target);controls.update();
  document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>{button.classList.toggle('active',button.dataset.view===view);button.disabled=layout==='farm'&&button.dataset.view!=='quarter';});
  $('scene-note').textContent=layout==='farm'?'12 × 8 格中性检查台 · 格距 1.2 · 固定 45° 方位 / 50° 俯角 / 正交高 14.1 · Lulu 高 1.2':`固定正交高 ${height.toFixed(1)} · 原制作尺寸 · ${layout==='scale'?'Lulu 正式版 v1 高 1.2，脚底着地':'不按资产或模块重新归一比例'} · 画布 1280 × 720 / DPR 1`;
  updateQuery();
}
async function show(){
  const current=++token;abort?.abort();abort=new AbortController();const signal=abort.signal;
  unload();$('stage').dataset.ready='false';setDownload('download');setDownload('source');$('status').textContent='正在载入实际 GLB…';$('status').classList.remove('error');$('dimensions').textContent='';
  grid.visible=sel('layout').value==='farm';floor.position.y=grid.visible?-.052:-.014;populateModules();fit();
  try{
    const house=currentHouse();if(!house)throw new Error('B14 清单尚未提供主屋模型');
    const module=sel('asset').value==='house'?modules().find(m=>m.id===sel('module').value):undefined;
    const spec:AssetSpec=sel('asset').value==='facade'?{id:'B02-S01',name:'B02 r04 已认可立面样段',revision:'r04',file:'/models/farm-assets/B02/s01-facade-sample-r04.glb',source:'assets-source/farm-assets/B02/s01-facade-sample-r04.blend'}:module?.file?{...house,name:module.name,file:module.file,source:module.source||house.source}:house;
    const root=await load(spec.file,signal,current);if(current!==token)return;content.add(root);selectedRoot=root;selectedSpec=spec;
    if(sel('layout').value!=='single'){
      const lulu=await load('/models/lulu-official-v1.glb',signal,current);if(current!==token)return;lulu.scale.setScalar(.6313689262131015);lulu.position.set(3.3,0,2.4);lulu.position.y-=new T.Box3().setFromObject(lulu).min.y;content.add(lulu);
    }
    if(current!==token)return;appearance();isolate();
    const size=new T.Box3().setFromObject(root).getSize(new T.Vector3());let triangles=0,meshes=0;root.traverse(o=>{if(o instanceof T.Mesh){meshes++;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;}});
    $('dimensions').textContent=`当前文件：${spec.file.split('/').pop()} · 宽 ${size.x.toFixed(3)} / 高 ${size.y.toFixed(3)} / 深 ${size.z.toFixed(3)} · ${Math.round(triangles).toLocaleString()} 三角面 · ${meshes} 渲染分件`;
    $('status').textContent=`${spec.name} · ${spec.revision||sel('revision').value} · 已载入实际 GLB · ${sel('asset').value==='facade'?'用户已认可美术样段':sel('revision').value!==manifest?.revision?'历史版本：墙角接缝需返修':'待用户验收'}`;
    $('technical').textContent=sel('asset').value==='facade'?'技术：见 B02 验收记录':'技术：'+(manifest?.checks?.technical||'未验证');
    $('visual').textContent=sel('asset').value==='facade'?'视觉：B02 已认可样段':sel('revision').value!==manifest?.revision?'视觉初审：需返修（历史墙角接缝）':'视觉初审：'+(manifest?.checks?.visual||'未验证');
    $('user-art').textContent=sel('asset').value==='facade'?'用户美术：B02 r04 已认可':'用户美术：待验收';
    setDownload('download',spec.file);setDownload('source',spec.source);
    renderer.render(scene,camera);$('stage').dataset.file=spec.file;$('stage').dataset.ready='true';$('stage').dataset.geometries=String(renderer.info.memory.geometries);$('stage').dataset.textures=String(renderer.info.memory.textures);$('stage').dataset.loaded=String(loaded.length);
  }catch(error){if(current!==token||signal.aborted)return;unload();$('stage').dataset.ready='false';$('status').textContent='载入失败：'+String(error);$('status').classList.add('error');console.error(error);}
}
sel('asset').onchange=()=>{sel('module').value='all';void show();};
sel('revision').onchange=()=>{populateModules();void show();};sel('layout').onchange=()=>void show();sel('material').onchange=appearance;
sel('module').onchange=()=>{const module=modules().find(m=>m.id===sel('module').value);if(module?.file||selectedSpec?.file!==currentHouse()?.file)void show();else isolate();};
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>button.onclick=()=>{view=button.dataset.view!;controls.autoRotate=false;$('rotate').classList.remove('active');fit();});
$('reset').onclick=fit;$('rotate').onclick=()=>{controls.autoRotate=!controls.autoRotate;$('rotate').classList.toggle('active',controls.autoRotate);};
$('capture').onclick=()=>{renderer.render(scene,camera);const link=document.createElement('a');link.href=renderer.domElement.toDataURL('image/png');link.download=`B14-${sel('asset').value}-${sel('revision').value}-${sel('material').value}-${view}-${sel('layout').value}.png`;link.click();};
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
fetch('/models/farm-assets/B14/manifest.json',{cache:'no-store'}).then(async response=>{if(!response.ok)throw new Error(`HTTP ${response.status}`);return await response.json() as Manifest;}).then(data=>{
  manifest=data;const revisions=data.revisions||[data.revision];sel('revision').replaceChildren(...revisions.map(r=>new Option(`${r} · ${r===data.revision?'当前待用户验收':'历史墙角需返修'}`,r)));sel('revision').value=data.revision;sel('revision').disabled=revisions.length<2;readQuery(['revision']);populateModules();readQuery(['module']);
  $('technical').textContent='技术：'+(data.checks?.technical||'未验证');$('visual').textContent='视觉初审：'+(data.checks?.visual||'未验证');return show();
}).catch(error=>{$('status').textContent='B14 清单暂不可用：'+String(error);$('status').classList.add('error');});
window.addEventListener('pagehide',()=>{abort?.abort();unload();renderer.setAnimationLoop(null);controls.dispose();clay.dispose();wire.dispose();tileGeometry.dispose();tileMaterial.dispose();floor.geometry.dispose();(floor.material as T.Material).dispose();renderer.dispose();});
