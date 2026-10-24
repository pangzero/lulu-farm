import './b03.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $=<E extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as E;
const sel=(id:string)=>$<HTMLSelectElement>(id);
const qs=new URLSearchParams(location.search);
const ids=['asset','revision','layout','material','water'];
function readQuery(){for(const id of ids){const v=qs.get(id);if(v&&Array.from(sel(id).options).some(o=>o.value===v))sel(id).value=v;}}
readQuery();
const scene=new T.Scene();scene.background=new T.Color('#f4f2e8');
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(1280,720);renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
$('stage').append(renderer.domElement);renderer.domElement.setAttribute('aria-label','B03 实际 GLB 三维预览');
scene.add(new T.HemisphereLight('#fffef8','#c4c7b6',.85));
const key=new T.DirectionalLight('#fffaf0',2);key.position.set(-3,6,4);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-10,right:10,top:10,bottom:-10,near:.1,far:30});key.shadow.normalBias=.02;scene.add(key);
const fill=new T.DirectionalLight('#f2f6ff',.5);fill.position.set(4,3,-2);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.MeshStandardMaterial({color:'#f4f2e8',roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.33;floor.receiveShadow=true;scene.add(floor);
const camera=new T.OrthographicCamera(-2,2,1.125,-1.125,.01,100);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
const content=new T.Group();scene.add(content);const loader=new GLTFLoader();
let loadedSources:T.Group[]=[],pending:AbortController|null=null;
const clay=new T.MeshStandardMaterial({color:'#a3a3a3',roughness:.85,side:T.DoubleSide}),wire=new T.MeshBasicMaterial({color:'#5a6e4b',wireframe:true});
const originals=new WeakMap<T.Mesh,T.Material|T.Material[]>();const waterMaterials=new Map<T.Material,T.MeshStandardMaterial>();const time={value:0};
const names:Record<string,string>={e01:'E01 空田格',e05:'E05 水岸直段',e07:'E07 水面格',e13:'E13 石头组'};
const directions:Record<string,T.Vector3>={quarter:new T.Vector3(1.35,2.25,4),front:new T.Vector3(0,.025,1),side:new T.Vector3(1,.025,0),back:new T.Vector3(0,.025,-1),top:new T.Vector3(0,1,.001)};
const file=(id:string,r=sel('revision').value)=>`/models/farm-assets/B03/${id}-${r}.glb`;
let view=qs.get('view')&&directions[qs.get('view')!]?qs.get('view')!:'quarter',token=0,metadata:Record<string,{triangles:number;bytes:number}>={};
function disposeGroups(groups:T.Object3D[]){
  const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>(),textures=new Set<T.Texture>();
  for(const group of groups)group.traverse(o=>{if(o instanceof T.Mesh){geometries.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material])if(m!==clay&&m!==wire)materials.add(m);}});
  for(const m of materials)for(const value of Object.values(m))if(value instanceof T.Texture)textures.add(value);
  for(const t of textures)t.dispose();for(const m of materials)m.dispose();for(const g of geometries)g.dispose();
}
function releaseCurrent(){disposeGroups([...loadedSources,content]);loadedSources=[];content.clear();for(const m of waterMaterials.values())m.dispose();waterMaterials.clear();}
async function load(path:string,signal:AbortSignal){const response=await fetch(path,{signal});if(!response.ok)throw new Error(`${response.status} ${path}`);const data=await response.arrayBuffer();return (await loader.parseAsync(data,'')).scene;}
function place(source:T.Group,x=0,z=0,scale=1){const g=source.clone(true);g.position.set(x,0,z);g.scale.multiplyScalar(scale);g.traverse(o=>{if(o instanceof T.Mesh){o.castShadow=!o.name.includes('E07');o.receiveShadow=true;originals.set(o,o.material);}});content.add(g);return g;}
function animateWater(m:T.Material){
  if(!waterMaterials.has(m)){
    const wm=(m as T.MeshStandardMaterial).clone();
    wm.onBeforeCompile=s=>{s.uniforms.b03Time=time;s.vertexShader='varying vec3 b03World;\n'+s.vertexShader;s.vertexShader=s.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nb03World=(modelMatrix*vec4(transformed,1.0)).xyz;');s.fragmentShader='uniform float b03Time; varying vec3 b03World;\n'+s.fragmentShader;s.fragmentShader=s.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat ripple=sin(b03World.x*5.5+b03World.z*3.0+b03Time*.8)*sin(b03World.z*6.5-b03Time*.65); diffuseColor.rgb*=1.0+.055*ripple;');};wm.customProgramCacheKey=()=> 'b03-world-ripples-v1';waterMaterials.set(m,wm);
  }return waterMaterials.get(m)!;
}
function appearance(){content.traverse(o=>{if(o instanceof T.Mesh&&originals.has(o)){const m=originals.get(o)!;o.material=sel('material').value==='clay'?clay:sel('material').value==='wire'?wire:sel('water').value==='animated'&&o.name.includes('E07')?(Array.isArray(m)?m.map(animateWater):animateWater(m)):m;}});updateQuery();}
function updateQuery(){for(const id of ids)qs.set(id,sel(id).value);qs.set('view',view);history.replaceState(null,'','?'+qs.toString());}
function fit(){
  const layout=sel('layout').value,a=sel('asset').value;let height=1.8,target=new T.Vector3(0,a==='e13'?.15:-.03,0),d=directions[view].clone().normalize();
  if(layout==='tiles'){height=5.0;target.set(0,.35,0);}
  if(layout==='shore'){height=5.4;target.set(0,-.03,.6);}
  if(layout==='farm'){view='quarter';height=14.1;target.set(0,0,0);const el=T.MathUtils.degToRad(50);d.set(Math.cos(el)/Math.sqrt(2),Math.sin(el),Math.cos(el)/Math.sqrt(2));}
  camera.left=-height*1280/720/2;camera.right=-camera.left;camera.top=height/2;camera.bottom=-height/2;camera.zoom=1;camera.updateProjectionMatrix();camera.position.copy(target).addScaledVector(d,20);controls.target.copy(target);camera.lookAt(target);controls.update();
  document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);b.disabled=layout==='farm'&&b.dataset.view!=='quarter';});
  updateQuery();
}
async function show(){
  const t=++token,r=sel('revision').value,layout=sel('layout').value,a=layout==='shore'?'e05':layout==='single'?sel('asset').value:'e01';sel('asset').value=a;sel('asset').disabled=layout!=='single';$('status').textContent='正在读取实际 GLB…';$('status').classList.remove('error');
  pending?.abort();pending=new AbortController();const signal=pending.signal;releaseCurrent();
  const requested=new Map<string,T.Group>();
  try{
    const envIds=layout==='single'?[a]:layout==='tiles'?['e01']:['e01','e05','e07','e13'];
    const cropIds=layout==='tiles'||layout==='farm'?['cabbage','tomato','corn']:[];
    const paths=[...envIds.map(id=>file(id)),...cropIds.map(id=>`/models/farm-assets/B01/${id}-mature-r03.glb`),...(layout==='farm'?['/models/lulu-official-v1.glb']:[])];
    const results=await Promise.allSettled(paths.map(async path=>{const group=await load(path,signal);requested.set(path,group);return group;}));
    if(t!==token){disposeGroups([...requested.values()]);return;}
    const failure=results.find(x=>x.status==='rejected');if(failure?.status==='rejected')throw failure.reason;
    loadedSources=[...requested.values()];
    const current=requested.get(file(a))||requested.get(file(envIds[0]))!;
    const needed=['e01','e05','e07','e13'].map(id=>requested.get(file(id))!);
    const crops=cropIds.map(id=>requested.get(`/models/farm-assets/B01/${id}-mature-r03.glb`)!);
    const lulu=requested.get('/models/lulu-official-v1.glb');
    $('stage').dataset.loadedPaths=JSON.stringify(paths);
    floor.position.y=layout==='single'?({e01:-.19,e05:-.29,e07:-.14,e13:0}[a]??-.33):-.33;
    if(layout==='single')place(current);
    if(layout==='tiles'){for(let x=-1;x<=1;x++)for(let z=-1;z<=1;z++){place(needed[0],x*1.2,z*1.2);if(z!==1)place(crops[x+1],x*1.2,z*1.2);}}
    if(layout==='shore'){for(let x=-1;x<=1;x++){place(needed[1],x*1.2,0);place(needed[0],x*1.2,-1.2);for(let z=0;z<3;z++)place(needed[2],x*1.2,z*1.2);}place(needed[3],-1.2,-1.2);}
    if(layout==='farm'){
      const bench=new T.Mesh(new T.BoxGeometry(14.4,.05,9.6),new T.MeshStandardMaterial({color:'#d4d8b8',roughness:1}));bench.position.y=-.31;bench.receiveShadow=true;content.add(bench);
      for(const [x,z,w,d] of [[-3.6,0,7.2,9.6],[3.6,-3.3,7.2,3]]){const pad=new T.Mesh(new T.BoxGeometry(w,.27,d),new T.MeshStandardMaterial({color:'#d4d8b8',roughness:1}));pad.position.set(x,-.15,z);pad.receiveShadow=true;content.add(pad);}
      for(let x=0;x<3;x++)for(let z=0;z<3;z++){place(needed[0],(x-4)*1.2,(z-1)*1.2);place(crops[x],(x-4)*1.2,(z-1)*1.2);}
      for(let x=0;x<4;x++){place(needed[1],(x+.6)*1.2,-1.2);for(let z=0;z<4;z++)place(needed[2],(x+.6)*1.2,(z-1)*1.2);}
      place(needed[3],1.5,-2.2);place(needed[3],4.2,-2.4);
      if(lulu){const lu=place(lulu,-.45,1.0,.6313689262131015);lu.position.y-=new T.Box3().setFromObject(lu).min.y;}
    }
    appearance();fit();renderer.render(scene,camera);$('stage').dataset.geometries=String(renderer.info.memory.geometries);$('stage').dataset.textures=String(renderer.info.memory.textures);const size=new T.Box3().setFromObject(current,true).getSize(new T.Vector3()),m=r==='r03'?metadata[a]:undefined;
    $('dimensions').textContent=`所选单件 X/Y高/Z深 ${size.x.toFixed(3)} / ${size.y.toFixed(3)} / ${size.z.toFixed(3)}${m?` · ${m.triangles.toLocaleString()} 三角面`:''}`;
    const sceneName=layout==='single'?names[a]:layout==='tiles'?'九格田地 + B01 作物':layout==='shore'?'三段岸线 + 连续水面':'农场距离与 Lulu 比例';
    $('status').textContent=`B03 · ${sceneName} · ${r} · 已载入实际 GLB · ${r==='r03'?'待用户验收':'历史版本对照'}`;
    $('scene-note').textContent=layout==='single'?'拖动旋转、滚轮缩放。五视图固定比例；水面为水平片，正侧视接近一条线。':layout==='tiles'?'9 个真实 E01 按 1.2 间距排列；6 株 B01 r03 保持原始高度。前排留空用于检查土面与接缝。':layout==='shore'?'3 段 E05 首尾相接；9 块 E07 水面向岸体下方延伸，岸石分件。可切换俯视和侧面检查接口。':'1280×720 · DPR 1 · 45° 方位 / 50° 俯角 · 12×8 格检查台。Lulu 高 1.2，作物原始尺寸；这不是完整农场交付。';
    $<HTMLAnchorElement>('download').href=file(a);$<HTMLAnchorElement>('source').href=`/@fs/Users/haowen/GameProject/farm-game/lulu-studio/assets-source/farm-assets/B03/${a}-${r}.blend`;
  }catch(e){disposeGroups([...requested.values()]);if(t!==token||signal.aborted)return;$('status').textContent='载入失败：'+String(e);$('status').classList.add('error');console.error(e);}
}
for(const id of ['asset','revision','layout'])sel(id).onchange=()=>void show();for(const id of ['material','water'])sel(id).onchange=appearance;
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view!;controls.autoRotate=false;fit();});
$('rotate').onclick=()=>{controls.autoRotate=!controls.autoRotate;$('rotate').classList.toggle('active',controls.autoRotate);};
$('capture').onclick=()=>{renderer.render(scene,camera);const a=document.createElement('a');a.href=renderer.domElement.toDataURL('image/png');a.download=`B03-${sel('asset').value}-${sel('revision').value}-${sel('layout').value}.png`;a.click();};
let lastStats=0;
renderer.setAnimationLoop(ms=>{time.value=ms/1000;controls.update();renderer.render(scene,camera);if(ms-lastStats>500){$('stage').dataset.geometries=String(renderer.info.memory.geometries);$('stage').dataset.textures=String(renderer.info.memory.textures);lastStats=ms;}});
fetch('/models/farm-assets/B03/manifest.json',{cache:'no-store'}).then(r=>r.json()).then(d=>{sel('revision').innerHTML=d.revisions.map((r:string)=>`<option value="${r}">${r} · ${r===d.revision?'当前候选':'历史版本'}</option>`).join('');sel('revision').value=d.revision;metadata=d.metrics||{};readQuery();return show();}).catch(e=>{$('status').textContent='清单载入失败：'+String(e);});
