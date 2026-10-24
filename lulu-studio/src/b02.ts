import './b02.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';

const $=<E extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as E;
const select=(id:string)=>$<HTMLSelectElement>(id);
const qs=new URLSearchParams(location.search);
for(const id of ['asset','revision','layout','material']){
  const value=qs.get(id);
  if(value&&Array.from(select(id).options).some(option=>option.value===value))select(id).value=value;
}
if(select('layout').value==='three')select('asset').value='fence';
const directions:Record<string,T.Vector3>={quarter:new T.Vector3(1.35,2.25,4),front:new T.Vector3(0,.025,1),side:new T.Vector3(1,.025,0),back:new T.Vector3(0,.025,-1),top:new T.Vector3(0,1,.001)};
let view=qs.get('view')&&directions[qs.get('view')!]?qs.get('view')!:'quarter';
let request=0;

const pathsForRevision=(revision:string)=>({
  facade:`/models/farm-assets/B02/s01-facade-sample-${revision}.glb`,
  fence:`/models/farm-assets/B02/s05-fence-repeat-${revision}.glb`,
  endcap:`/models/farm-assets/B02/s05-fence-endcap-${revision}.glb`,
  lulu:'/models/lulu-meshy-notail.glb'
});
const sourceRoot='/@fs/Users/haowen/GameProject/farm-game/lulu-studio/assets-source/farm-assets/B02/';
const scene=new T.Scene();scene.background=new T.Color('#f4f2e8');
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(1280,720);renderer.setPixelRatio(1);renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
$('stage').append(renderer.domElement);renderer.domElement.setAttribute('aria-label','B02 立面样段与围栏实际 GLB 三维预览');
scene.add(new T.HemisphereLight('#fffef8','#c4c7b6',.85));
const key=new T.DirectionalLight('#fffaf0',2);key.position.set(-3,6,4);key.castShadow=true;key.shadow.mapSize.set(2048,2048);
Object.assign(key.shadow.camera,{left:-10,right:10,top:10,bottom:-10,near:.1,far:30});key.shadow.normalBias=.02;scene.add(key);
const fill=new T.DirectionalLight('#f2f6ff',.5);fill.position.set(4,3,-2);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(100,100),new T.MeshStandardMaterial({color:'#f4f2e8',roughness:1}));
floor.rotation.x=-Math.PI/2;floor.position.y=-.014;floor.receiveShadow=true;scene.add(floor);
const camera=new T.OrthographicCamera(-2,2,1.125,-1.125,.01,100);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
const content=new T.Group();scene.add(content);
const loader=new GLTFLoader(),cache=new Map<string,Promise<T.Group>>();
const originalMaterials=new WeakMap<T.Mesh,T.Material|T.Material[]>();
const clay=new T.MeshStandardMaterial({color:'#a3a3a3',roughness:.85});
const wire=new T.MeshBasicMaterial({color:'#5a6e4b',wireframe:true});
const tileGeometry=new T.BoxGeometry(1.17,.03,1.17),tileMaterial=new T.MeshStandardMaterial({color:'#dddccf',roughness:1});

function load(path:string){
  if(!cache.has(path))cache.set(path,loader.loadAsync(path).then(result=>result.scene).catch(error=>{cache.delete(path);throw new Error(`${path}: ${error instanceof Error?error.message:String(error)}`);}));
  return cache.get(path)!;
}
function instance(source:T.Group,parent:T.Group,x=0,z=0,scale=1){
  const object=source.clone(true);object.position.set(x,0,z);object.scale.setScalar(scale);
  object.traverse(child=>{if(child instanceof T.Mesh){child.castShadow=true;child.receiveShadow=true;originalMaterials.set(child,child.material);}});
  parent.add(object);return object;
}
function fence(repeat:T.Group,endcap:T.Group,count:number,x=0,z=0){
  const group=new T.Group();group.position.set(x-count*1.2/2,0,z);content.add(group);
  for(let index=0;index<count;index++)instance(repeat,group,index*1.2);
  instance(endcap,group,count*1.2);return group;
}
function lulu(source:T.Group,x:number,z:number){
  const object=instance(source,content,x,z,.6313689262131015);
  object.position.y-=new T.Box3().setFromObject(object).min.y;return object;
}
function tile(x:number,z:number){const object=new T.Mesh(tileGeometry,tileMaterial);object.position.set(x,-.03,z);object.receiveShadow=true;content.add(object);}
function appearance(){content.traverse(object=>{if(object instanceof T.Mesh&&originalMaterials.has(object))object.material=select('material').value==='clay'?clay:select('material').value==='wire'?wire:originalMaterials.get(object)!;});}
function updateQuery(){for(const id of ['asset','revision','layout','material'])qs.set(id,select(id).value);qs.set('view',view);history.replaceState(null,'','?'+qs.toString());}
function fit(){
  const asset=select('asset').value,layout=select('layout').value;
  let height=asset==='facade'?4.6:1.85,target=new T.Vector3(0,asset==='facade'?1.45:.46,0),direction=directions[view].clone().normalize();
  if(layout==='three'){height=2.8;target.set(0,.46,0);}
  if(layout==='scale'){height=5.25;target.set(0,1.35,0);}
  if(layout==='farm'){
    height=14.1;target.set(0,0,0);const elevation=T.MathUtils.degToRad(50);
    direction.set(Math.cos(elevation)/Math.sqrt(2),Math.sin(elevation),Math.cos(elevation)/Math.sqrt(2));view='quarter';
  }
  camera.left=-height*1280/720/2;camera.right=-camera.left;camera.top=height/2;camera.bottom=-height/2;camera.zoom=1;camera.updateProjectionMatrix();
  camera.position.copy(target).addScaledVector(direction,20);controls.target.copy(target);camera.lookAt(target);controls.update();
  document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>{button.classList.toggle('active',button.dataset.view===view);button.disabled=layout==='farm'&&button.dataset.view!=='quarter';});
  updateQuery();
}
async function show(preserveCamera=false){
  const currentRequest=++request,asset=select('asset').value,layout=select('layout').value,revision=select('revision').value;
  const paths=pathsForRevision(revision);
  $('status').textContent='正在载入实际 GLB…';$('status').classList.remove('error');
  const selectedPath=asset==='facade'?paths.facade:paths.fence;
  $<HTMLAnchorElement>('download').href=selectedPath;
  $<HTMLAnchorElement>('source').href=sourceRoot+(asset==='facade'?`s01-facade-sample-${revision}.blend`:`s05-fence-${revision}.blend`);
  $<HTMLAnchorElement>('endcap-download').href=paths.endcap;
  try{
    const needsBoth=layout==='scale'||layout==='farm';
    const selected=await load(selectedPath);
    const [facadeModel,repeatModel,endcapModel,luluModel,crops]=await Promise.all([
      needsBoth?load(paths.facade):Promise.resolve(null),
      asset==='fence'||needsBoth?load(paths.fence):Promise.resolve(null),
      asset==='fence'||needsBoth?load(paths.endcap):Promise.resolve(null),
      needsBoth?load(paths.lulu):Promise.resolve(null),
      layout==='farm'?Promise.all(['cabbage','tomato','corn'].map(id=>load(`/models/farm-assets/B01/${id}-mature-r03.glb`))):Promise.resolve([])
    ]);
    if(currentRequest!==request)return;
    content.clear();floor.position.y=layout==='farm'?-.052:-.014;
    if(layout==='single'){
      if(asset==='facade')instance(selected,content);else fence(repeatModel!,endcapModel!,1);
    }else if(layout==='three'){
      fence(repeatModel!,endcapModel!,3);
    }else if(layout==='scale'){
      instance(facadeModel!,content,-2.0,-.3);fence(repeatModel!,endcapModel!,3,2.25,.5);lulu(luluModel!,0,1.5);
    }else{
      for(let x=0;x<12;x++)for(let z=0;z<8;z++)tile((x-5.5)*1.2,(z-3.5)*1.2);
      instance(facadeModel!,content,-2.4,-2.3);fence(repeatModel!,endcapModel!,3,3.0,-1.8);lulu(luluModel!,0,1.8);
      for(let crop=0;crop<3;crop++)for(let index=0;index<3;index++)instance(crops[crop],content,(crop-1)*2.4+(index-1)*.75,3.0);
    }
    appearance();if(preserveCamera)updateQuery();else fit();
    const box=new T.Box3().setFromObject(selected),size=box.getSize(new T.Vector3());
    $('dimensions').textContent=`所选 GLB ${size.x.toFixed(2)} 宽 × ${size.y.toFixed(2)} 高 × ${size.z.toFixed(2)} 深 · 1280 × 720`;
    const description=layout==='single'?(asset==='facade'?'S01 主屋立面样段，非完整主屋':'S05 单段 + 独立末端柱'):layout==='three'?'S05 三段连续拼接 + 独立末端柱':layout==='scale'?'S01 / S05 / Lulu 同尺度检查':'12 × 8 格使用距离 · B01 r03 作物只读参照';
    $('status').textContent=`${description} · ${revision} · ${revision==='r04'?'用户认可美术样板':'历史对照候选'}`;
    $('comparison').textContent=layout==='three'?'跨距 1.20 · 实例 X = 0 / 1.20 / 2.40 · 末柱 3.60':layout==='farm'?'固定 45° 方位 / 50° 俯角 / 正交高 14.1':layout==='scale'?'Lulu 高 1.20 · 建筑与围栏保持制作尺寸':asset==='facade'?'门窗进深 / 墙厚 / 屋檐与木梁倒角':'左柱 + 两横档为重复段；右端单独加末端柱';
  }catch(error){
    if(currentRequest!==request)return;
    content.clear();$('status').textContent='载入失败：'+String(error);$('status').classList.add('error');$('dimensions').textContent='';console.error(error);
  }
}
select('asset').onchange=()=>{if(select('asset').value==='facade'&&select('layout').value==='three')select('layout').value='single';void show();};
select('layout').onchange=()=>{if(select('layout').value==='three')select('asset').value='fence';void show();};
select('revision').onchange=()=>void show(true);
select('material').onchange=()=>{appearance();updateQuery();};
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>button.onclick=()=>{view=button.dataset.view!;controls.autoRotate=false;$('rotate').classList.remove('active');fit();});
$('rotate').onclick=()=>{controls.autoRotate=!controls.autoRotate;$('rotate').classList.toggle('active',controls.autoRotate);};
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
void show();
