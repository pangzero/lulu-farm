import './lulu-rig.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const params=new URLSearchParams(location.search);
const revision=params.get('rev')||'r11';
const prior=params.get('reference')==='r04';
let armAngle=[5,10,15].includes(Number(params.get('angle')))?Number(params.get('angle')):15;
let oneArm=params.get('arm')==='right';
const views={front:[0,1.19,10],side:[-10,1.75,2.6],back:[0,1.19,-10],quarter:[-7,1.4,7],opposite:[10,1.75,2.6]} as const;
type View=keyof typeof views;
type Pose='rest'|'head'|'forward'|'backward'|'raise'|'leg'|'spine'|'play';
const labels:Record<Pose,string>={rest:'静止 · 同机位对比',head:'头部转动 12°',forward:'手臂前摆 20°',backward:'手臂后摆 12°',raise:'手臂外展 15°',leg:'单腿小幅屈膝',spine:'脊柱小幅弯曲',play:'小幅摆臂 · 验证用'};
let view=(params.get('view')||'front') as View;if(!(view in views))view='front';
let pose=(params.get('pose')||'rest') as Pose;if(!(pose in labels))pose='rest';
const narrow=matchMedia('(max-width:900px)');
let layout: 'single'|'compare'=params.get('layout')==='single'?'single':params.get('layout')==='compare'?'compare':narrow.matches?'single':'compare';
let layoutExplicit=params.has('layout');
let showBones=params.get('bones')==='1',clay=params.get('clay')==='1',detail=params.get('detail')==='1';
const root=document.querySelector<HTMLElement>('#comparison')!,status=document.querySelector<HTMLElement>('#status')!;
const gray=new T.MeshStandardMaterial({color:0xbebebe,roughness:1});
function stage(id:string){
 const host=document.querySelector<HTMLElement>(id)!,renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.VSMShadowMap;host.append(renderer.domElement);
 const scene=new T.Scene();scene.background=new T.Color('#fafaf6');const pmrem=new T.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;scene.environmentIntensity=.15;
 const camera=new T.OrthographicCamera(-1,1,1,-1,.1,50);scene.add(new T.HemisphereLight('#fffef5','#fff2cf',1.5));const lights=new T.Group();scene.add(lights);
 const key=new T.DirectionalLight('white',.85);key.position.set(-3,5,5);key.castShadow=true;key.shadow.mapSize.set(1024,1024);Object.assign(key.shadow.camera,{left:-2,right:2,top:3,bottom:-1,near:.1,far:15});key.shadow.normalBias=.015;key.shadow.bias=-.0001;key.shadow.radius=20;key.shadow.blurSamples=24;
 const fill=new T.DirectionalLight('white',.55);fill.position.set(4,2,3);const front=new T.DirectionalLight('#fff9ed',.65);front.position.set(0,1.3,5);front.target.position.set(0,1.2,0);lights.add(key,fill,front,front.target);
 const floor=new T.Mesh(new T.PlaneGeometry(200,200),new T.ShadowMaterial({color:'#756e4f',opacity:.07}));floor.rotation.x=-Math.PI/2;floor.position.y=-.007;floor.receiveShadow=true;scene.add(floor);
 return{host,renderer,scene,camera,lights};
}
const stages=[stage('#baseline'),stage('#bound')];
const boneMaps=[new Map<string,{bone:T.Bone;rest:T.Quaternion}>(),new Map<string,{bone:T.Bone;rest:T.Quaternion}>()];
const boneMap=boneMaps[1],materials=new Map<T.Mesh,T.Material|T.Material[]>();
let skeleton:T.LineSegments|undefined,ready=false,frame=0;
const boneTails=new Map<T.Bone,T.Vector3>();
let skinned:T.SkinnedMesh[]=[];
function reset(){for(const map of boneMaps)for(const{bone,rest}of map.values())bone.quaternion.copy(rest);stages[1].scene.updateMatrixWorld(true);}
const q=new T.Quaternion(),par=new T.Quaternion(),a=new T.Vector3();
function turn(name:string,axis:[number,number,number],deg:number,stageIndex=1){const item=boneMaps[stageIndex].get(name);if(!item)return;item.bone.parent!.getWorldQuaternion(par).invert();a.fromArray(axis).applyQuaternion(par);q.setFromAxisAngle(a,T.MathUtils.degToRad(deg));item.bone.quaternion.premultiply(q);item.bone.updateMatrixWorld(true);}
function applyPose(t=0){
 reset();
 for(const i of prior?[0,1]:[1]){
  if(pose==='head')turn('Head',[0,1,0],12,i);
  if(['forward','backward','raise','play'].includes(pose))for(const side of oneArm?['Right']:['Left','Right']){
   const sign=side==='Left'?1:-1;
   const deg=pose==='forward'?20:pose==='backward'?-12:pose==='play'?14*Math.sin(t*1.6):0;
   turn(side+'Arm',[1,0,0],-deg,i);
   turn(side+'ForeArm',[1,0,0],-Math.max(0,deg)*.1,i);
   if(pose==='raise')turn(side+'Arm',[0,0,1],armAngle*sign,i);
  }
  if(pose==='leg'){turn('LeftUpLeg',[1,0,0],-12,i);turn('LeftLeg',[1,0,0],20,i);turn('LeftFoot',[1,0,0],-8,i);}
  if(pose==='spine'){turn('Spine',[1,0,0],4,i);turn('Spine1',[1,0,0],3,i);}
 }
 for(const s of stages)s.scene.updateMatrixWorld(true);for(const mesh of skinned)mesh.skeleton.update();
}

function render(){
 if(skeleton){const positions=skeleton.geometry.getAttribute('position');let i=0;const start=new T.Vector3(),end=new T.Vector3();for(const[b,tail]of boneTails){b.getWorldPosition(start);end.copy(tail).applyMatrix4(b.matrixWorld);positions.setXYZ(i++,start.x,start.y,start.z);positions.setXYZ(i++,end.x,end.y,end.z);}positions.needsUpdate=true;}
 for(const s of stages){const w=s.host.clientWidth,h=s.host.clientHeight;if(!w||!h)continue;const half=Math.max(1.19,(detail?1.6:.84)*h/w);s.renderer.setSize(w,h);Object.assign(s.camera,{left:-half*w/h,right:half*w/h,top:half,bottom:-half,zoom:detail?1.9:1});s.camera.position.fromArray(views[view]);s.camera.position.y-=detail?.38:0;s.camera.lookAt(0,1.13-(detail?.38:0),0);s.camera.updateProjectionMatrix();s.lights.rotation.y=Math.atan2(s.camera.position.x,s.camera.position.z);s.renderer.render(s.scene,s.camera);}
 if(ready){root.dataset.rendered=`${revision}|${view}|${pose}|${showBones}|${clay}|${detail}|${layout}`;root.setAttribute('aria-busy','false');}
}
function tick(t:number){applyPose(t/1000);render();if(pose==='play')frame=requestAnimationFrame(tick);}
function update(){
 cancelAnimationFrame(frame);delete root.dataset.rendered;params.set('rev',revision);params.set('view',view);params.set('pose',pose);params.set('angle',String(armAngle));oneArm?params.set('arm','right'):params.delete('arm');if(layoutExplicit)params.set('layout',layout);else params.delete('layout');root.dataset.layout=layout;const layoutButton=document.querySelector<HTMLButtonElement>('#layout')!;layoutButton.textContent=layout==='single'?'显示左右对比':'只看绑定模型';layoutButton.setAttribute('aria-pressed',String(layout==='single'));for(const[k,v]of [['bones',showBones],['clay',clay],['detail',detail]] as const)v?params.set(k,'1'):params.delete(k);history.replaceState(null,'',`${location.pathname}?${params}`);
 document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));document.querySelectorAll<HTMLButtonElement>('[data-pose]').forEach(b=>b.classList.toggle('active',b.dataset.pose===pose));for(const[k,v]of [['bones',showBones],['clay',clay],['detail',detail]]as const)document.querySelector('#'+k)!.classList.toggle('active',v);
 if(skeleton)skeleton.visible=showBones;for(const[mesh,m]of materials)mesh.material=clay?gray:m;
 const poseText=pose==='raise'?`手臂外展 ${armAngle}°`:labels[pose];
 document.querySelector('#pose-label')!.textContent=`${revision} · ${poseText}`;
 document.querySelector('#base-label')!.textContent=prior?'r04 · 修改前 · 同动作':'Lulu 正式版 v1 · 静止基准';
 (document.querySelector('#angle') as HTMLSelectElement).value=String(armAngle);
 (document.querySelector('#reference') as HTMLSelectElement).value=prior?'r04':'static';
 document.querySelector('#one-arm')!.textContent=oneArm?'恢复双臂检查':'仅右臂检查';
 document.querySelector('#limitation')!.textContent=['forward','backward','raise','play'].includes(pose)?revision==='r04'?'r04 的腋下与腕旁仍有粘连牵拉。':'局部曲面重建候选：检查腋下开合、肩部轮廓及衣物是否被牵动；未接入 Mixamo。':'基础骨架与小幅变形检查；尚未接入 Mixamo。头脸整体跟随头骨。';
 if(ready)status.textContent=`${boneMap.size} 根骨骼 · ${poseText} · ${revision}`;
 applyPose();render();if(pose==='play')frame=requestAnimationFrame(tick);
}
document.querySelector<HTMLSelectElement>('#angle')!.onchange=e=>{armAngle=Number((e.target as HTMLSelectElement).value);pose='raise';update();};
document.querySelector<HTMLSelectElement>('#reference')!.onchange=e=>{params.set('reference',(e.target as HTMLSelectElement).value);params.set('layout','compare');location.search=params.toString();};
document.querySelector<HTMLButtonElement>('#one-arm')!.onclick=()=>{oneArm=!oneArm;update();};
narrow.addEventListener('change',()=>{if(!layoutExplicit){layout=narrow.matches?'single':'compare';update();}});
document.querySelector<HTMLButtonElement>('#layout')!.onclick=()=>{layoutExplicit=true;layout=layout==='single'?'compare':'single';update();};
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view as View;update();});document.querySelectorAll<HTMLButtonElement>('[data-pose]').forEach(b=>b.onclick=()=>{pose=b.dataset.pose as Pose;update();});document.querySelector<HTMLButtonElement>('#bones')!.onclick=()=>{showBones=!showBones;update();};document.querySelector<HTMLButtonElement>('#clay')!.onclick=()=>{clay=!clay;update();};document.querySelector<HTMLButtonElement>('#detail')!.onclick=()=>{detail=!detail;update();};
stages.forEach(s=>new ResizeObserver(()=>render()).observe(s.host));
document.querySelector<HTMLAnchorElement>('#download')!.href=`/models/rig/lulu-rig-${revision}.glb`;
const loader=new GLTFLoader();
Promise.all([loader.loadAsync(prior?'/models/rig/lulu-rig-r04.glb':'/models/lulu-official-v1.glb'),loader.loadAsync(`/models/rig/lulu-rig-${revision}.glb`)]).then(models=>{
 const box=new T.Box3().setFromObject(models[0].scene),size=box.getSize(new T.Vector3()),center=box.getCenter(new T.Vector3()),scale=2.275/size.y;
 models.forEach((g,i)=>{const group=new T.Group();group.scale.setScalar(scale);group.position.set(-center.x*scale,-box.min.y*scale,-center.z*scale);group.add(g.scene);stages[i].scene.add(group);g.scene.traverse(o=>{if(o instanceof T.Mesh){o.castShadow=true;o.receiveShadow=true;materials.set(o,o.material);}if(o instanceof T.Bone)boneMaps[i].set(o.name,{bone:o,rest:o.quaternion.clone()});if(o instanceof T.SkinnedMesh){o.frustumCulled=false;skinned.push(o);}});});
 stages[1].scene.updateMatrixWorld(true);
 for(const{bone}of boneMap.values()){const tail=bone.userData.boneTail as number[]|undefined;if(tail){const world=new T.Vector3().fromArray(tail).multiplyScalar(scale).add(new T.Vector3(-center.x*scale,-box.min.y*scale,-center.z*scale));boneTails.set(bone,bone.worldToLocal(world));}}
 const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(new Float32Array(boneTails.size*6),3));const mat=new T.LineBasicMaterial({color:'#246d9c',depthTest:false,depthWrite:false,transparent:true,opacity:.95});skeleton=new T.LineSegments(geo,mat);skeleton.frustumCulled=false;skeleton.renderOrder=20;stages[1].scene.add(skeleton);
 ready=true;update();
}).catch(error=>{console.error(error);status.textContent='载入失败：'+String(error);root.dataset.error='load-failed';});
