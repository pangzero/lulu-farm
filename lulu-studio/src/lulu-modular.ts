import './lulu-modular.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const params=new URLSearchParams(location.search),revision=params.get('rev')||'parts-v2';
const compareParts=params.get('base')==='parts-v2';
const views={front:[0,1.13,10],side:[-10,1.13,0],back:[0,1.13,-10],quarter:[-7,1.6,7],opposite:[10,1.13,0],inner:[7,1.6,7]} as const;
type View=keyof typeof views;type Mode='assembled'|'exploded'|'withoutArms'|'body'|'armR'|'head'|'shorts'|'legs'|'part';
const labels:Record<Mode,string>={assembled:'完整组装',exploded:'分件展开',withoutArms:'隐藏手臂',body:'身体单件',armR:'右臂单件',head:'头部单件',shorts:'短裤单件',legs:'腿脚单件',part:'独立部件'};
let view=(params.get('view')||'front') as View;if(!(view in views))view='front';
let mode=(params.get('mode')||'assembled') as Mode;if(!(mode in labels))mode='assembled';
let selectedPart=params.get('part')||'';
let clay=params.get('clay')==='1',detail=params.get('detail')==='1',alternate=params.get('light')==='1',ready=false;
const root=document.querySelector<HTMLElement>('#comparison')!,status=document.querySelector<HTMLElement>('#status')!;
const mat=new T.MeshStandardMaterial({color:'#c0c0c0',roughness:1});const materials=new Map<T.Mesh,T.Material|T.Material[]>();
function stage(id:string){
 const host=document.querySelector<HTMLElement>(id)!,renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;host.append(renderer.domElement);
 const scene=new T.Scene();scene.background=new T.Color('#fafaf6');const pmrem=new T.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;scene.environmentIntensity=.15;pmrem.dispose();
 const camera=new T.OrthographicCamera(-1,1,1,-1,.1,50),lights=new T.Group();scene.add(new T.HemisphereLight('#fffef5','#fff2cf',1.5));scene.add(lights);
 const key=new T.DirectionalLight('white',.85);key.position.set(-3,5,5);const fill=new T.DirectionalLight('white',.55);fill.position.set(4,2,3);const front=new T.DirectionalLight('#fff9ed',.65);front.position.set(0,1.3,5);front.target.position.set(0,1.2,0);lights.add(key,fill,front,front.target);
 const floor=new T.Mesh(new T.PlaneGeometry(200,200),new T.MeshBasicMaterial({color:'#f6f6ef'}));floor.rotation.x=-Math.PI/2;floor.position.y=-.8;scene.add(floor);
 const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=false;controls.enablePan=false;controls.minZoom=.5;controls.maxZoom=3;return{host,renderer,scene,camera,lights,controls};
}
const stages=[stage('#baseline'),stage('#candidate')],partMaps=[new Map<string,T.Object3D>(),new Map<string,T.Object3D>()],parts=partMaps[1];
let syncing=false;
for(let i=0;i<2;i++)stages[i].controls.addEventListener('change',()=>{if(syncing)return;syncing=true;const a=stages[i],b=stages[1-i];b.camera.position.copy(a.camera.position);b.camera.quaternion.copy(a.camera.quaternion);b.camera.zoom=a.camera.zoom;b.controls.target.copy(a.controls.target);b.controls.update();render();syncing=false;});
function render(){for(const s of stages){let w=s.host.clientWidth,h=s.host.clientHeight;if(!w||!h)continue;const half=Math.max(mode==='exploded'?1.95:1.22,(mode==='exploded'?1.4:.84)*h/w);s.renderer.setSize(w,h,false);Object.assign(s.camera,{left:-half*w/h,right:half*w/h,top:half,bottom:-half});s.camera.updateProjectionMatrix();s.lights.rotation.y=Math.atan2(s.camera.position.x,s.camera.position.z)+(alternate?Math.PI*.65:0);s.renderer.render(s.scene,s.camera);}if(ready){root.dataset.rendered=[revision,view,mode,clay,detail,alternate].join('|');root.setAttribute('aria-busy','false');}}
const names:Record<string,string>={Arm_R:'右臂（角色右侧）',Arm_L:'左臂',Body_Head_Legs_Shorts:'身体及其余部位（单侧验证）',Body:'身体',Core:'身体',Head:'头部',Orange:'橘子',Shorts:'短裤',Leg_R:'右腿脚',Leg_L:'左腿脚'};
function update(resetCamera=true){
 root.dataset.mode=mode;
 for(const map of (compareParts?partMaps:[parts]))for(const[name,o]of map){o.position.set(0,0,0);o.visible=mode==='part'&&name===selectedPart||mode==='assembled'||mode==='exploded'||mode==='withoutArms'&&!name.startsWith('Arm')||mode==='body'&&['Body','Core','Body_Head_Legs_Shorts'].includes(name)||mode==='armR'&&name==='Arm_R'||mode==='head'&&['Head','Orange'].includes(name)||mode==='shorts'&&name==='Shorts'||mode==='legs'&&name.startsWith('Leg');
 if(mode==='exploded'){if(name==='Arm_R')o.position.x=-.47;if(name==='Arm_L')o.position.x=.47;if(name==='Head')o.position.y=.35;if(name==='Orange')o.position.y=.66;if(name==='Shorts')o.position.y=-.52;if(name==='Leg_R')o.position.x=-.5;if(name==='Leg_L')o.position.x=.5;if(name.startsWith('Leg'))o.position.y=-.23;}}
 for(const[m,original]of materials)m.material=clay?mat:original;
 if(resetCamera){syncing=true;for(const s of stages){s.controls.target.set(detail?-.53:0,detail?.76:1.13,0);s.camera.position.fromArray(views[view]);if(detail){s.camera.position.y-=.37;s.camera.position.x-=.53;}s.camera.zoom=detail?(mode==='armR'?2.8:1.65):1;s.camera.lookAt(s.controls.target);s.controls.update();}syncing=false;}
 if(mode==='part')params.set('part',selectedPart);else params.delete('part');
 (document.querySelector('#part-select') as HTMLSelectElement).value=mode==='part'?selectedPart:'';
 params.set('rev',revision);params.set('view',view);params.set('mode',mode);for(const[k,v]of [['clay',clay],['detail',detail],['light',alternate]]as const)v?params.set(k,'1'):params.delete(k);history.replaceState(null,'',location.pathname+'?'+params);
 document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));for(const[k,v]of [['clay',clay],['detail',detail],['light',alternate]]as const)document.querySelector('#'+k)!.classList.toggle('active',v);
 const revisionLabel=revision==='right-junction-r04'?'右侧补面修整 r04':revision==='parts-v2'?'静态分件候选':revision;
 document.querySelector('#candidate-label')!.textContent=revisionLabel+' · '+(mode==='part'?(names[selectedPart]||selectedPart):labels[mode]);if(ready)status.textContent=`${parts.size} 个独立部件 · 静态候选 · 无骨骼动作`;
 if(revision.startsWith('right-junction-'))document.querySelector('.review-warning')!.textContent='本轮只改角色右侧新增补面。大片扇状折面已减弱；内面周缘仍有接线和局部硬边，身体补面靠腰部仍有浅痕。保留待验收状态，尚未达到绑定前的连接质量要求。';
 document.querySelector('#note')!.textContent=mode==='exploded'?'部件平移展开用于检查，并非骨骼动作。隐藏面的曲面为新增重建，仍需验收。':'拖动旋转，两侧同步。正式版保持原样；分件候选等待外观验收。';render();
}
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view as View;update();});document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode as Mode;update();});document.querySelector<HTMLButtonElement>('#clay')!.onclick=()=>{clay=!clay;update(false);};document.querySelector<HTMLButtonElement>('#detail')!.onclick=()=>{detail=!detail;update();};document.querySelector<HTMLButtonElement>('#light')!.onclick=()=>{alternate=!alternate;update(false);};
document.querySelector<HTMLSelectElement>('#part-select')!.onchange=e=>{selectedPart=(e.target as HTMLSelectElement).value;mode=selectedPart?'part':'assembled';update();};
for(const s of stages)new ResizeObserver(()=>render()).observe(s.host);
document.querySelector<HTMLAnchorElement>('#download')!.href=`/models/modular/${revision}/lulu-assembled.glb`;
document.querySelector('#baseline-label')!.textContent=compareParts?'修改前 · parts-v2 分件':'Lulu 正式版 v1 · 原始静态';
(document.querySelector('#baseline-select') as HTMLSelectElement).value=compareParts?'parts-v2':'official';
document.querySelector<HTMLSelectElement>('#baseline-select')!.onchange=e=>{const base=(e.target as HTMLSelectElement).value;base==='official'?params.delete('base'):params.set('base',base);location.href=location.pathname+'?'+params;};
const loader=new GLTFLoader();Promise.all([loader.loadAsync(compareParts?'/models/modular/parts-v2/lulu-assembled.glb':'/models/lulu-official-v1.glb'),loader.loadAsync(`/models/modular/${revision}/lulu-assembled.glb`)]).then(models=>{
 const box=new T.Box3().setFromObject(models[0].scene),center=box.getCenter(new T.Vector3()),scale=2.275/box.getSize(new T.Vector3()).y;
 models.forEach((g,i)=>{const group=new T.Group();group.scale.setScalar(scale);group.position.set(-center.x*scale,-box.min.y*scale,-center.z*scale);group.add(g.scene);stages[i].scene.add(group);g.scene.traverse(o=>{if(o instanceof T.Mesh)materials.set(o,o.material);});for(const o of g.scene.children)partMaps[i].set(o.name,o);});
 for(const[name]of parts){const opt=document.createElement('option');opt.value=name;opt.textContent=names[name]||name;document.querySelector('#part-select')!.append(opt);const a=document.createElement('a');a.href=`/models/modular/${revision}/${name}.glb`;a.textContent=(names[name]||name)+' GLB';a.download='';document.querySelector('#parts')!.append(a);}
 for(const m of ['head','shorts','legs']as const){const available=m==='head'?parts.has('Head'):m==='shorts'?parts.has('Shorts'):parts.has('Leg_R');document.querySelector<HTMLButtonElement>(`[data-mode="${m}"]`)!.disabled=!available;}
 ready=true;update();
}).catch(e=>{console.error(e);status.textContent='载入失败：'+String(e);root.dataset.error=String(e);});
