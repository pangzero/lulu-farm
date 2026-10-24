import './lulu.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const stage=document.querySelector<HTMLDivElement>('#model-stage')!;
const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.NoToneMapping;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.VSMShadowMap;stage.append(renderer.domElement);
const scene=new T.Scene();scene.background=new T.Color('#fafaf6');
const envGenerator=new T.PMREMGenerator(renderer);scene.environment=envGenerator.fromScene(new RoomEnvironment(),.04).texture;scene.environmentIntensity=.15;
const camera=new T.OrthographicCamera(-1,1,1,-1,.1,50);
const controls=new OrbitControls(camera,renderer.domElement);controls.enablePan=false;controls.minZoom=.65;controls.maxZoom=3;controls.enableRotate=false;controls.maxPolarAngle=Math.PI*.9;controls.target.set(0,1.13,0);
scene.add(new T.HemisphereLight('#fffef5','#fff2cf',1.5));
const key=new T.DirectionalLight('#ffffff',.85);key.position.set(-3,5,5);key.castShadow=true;key.shadow.mapSize.set(1024,1024);Object.assign(key.shadow.camera,{left:-2,right:2,top:3,bottom:-1,near:.1,far:15});key.shadow.normalBias=.015;key.shadow.bias=-.0001;key.shadow.radius=20;key.shadow.blurSamples=24;const lights=new T.Group();scene.add(lights);lights.add(key);
const fill=new T.DirectionalLight('#ffffff',.55);fill.position.set(4,2,3);lights.add(fill);
const frontFill=new T.DirectionalLight('#fff9ed',.65);frontFill.position.set(0,1.3,5);frontFill.target.position.set(0,1.2,0);lights.add(frontFill,frontFill.target);
let alternateLight=false;
document.querySelector<HTMLButtonElement>('#inspect-light')!.onclick=()=>{alternateLight=!alternateLight;key.position.set(...(alternateLight?[4,2,-4]:[-3,5,5]) as [number,number,number]);fill.intensity=alternateLight?.8:.45;document.querySelector('#inspect-light')!.classList.toggle('active',alternateLight);};
const floor=new T.Mesh(new T.PlaneGeometry(200,200),new T.ShadowMaterial({color:'#756e4f',opacity:.07}));floor.rotation.x=-Math.PI/2;floor.position.y=-.007;floor.receiveShadow=true;scene.add(floor);
function resize(){const w=stage.clientWidth,h=stage.clientHeight,half=Math.max(1.19,.84*h/w);renderer.setSize(w,h);camera.left=-half*w/h;camera.right=half*w/h;camera.top=half;camera.bottom=-half;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(stage);resize();
const views={front:[0,1.19,10],side:[-10,1.75,2.6],back:[0,1.19,-10],quarter:[-7,1.4,7]} as const;
const refCanvas=document.querySelector<HTMLCanvasElement>('#reference')!;
const reference=new Image();let currentView:keyof typeof views='front';
const bounds={front:[382,1217],side:[356,1285],back:[357,1295]} as const;
function drawReference(){
 const host=refCanvas.parentElement!,w=host.clientWidth,h=host.clientHeight,dpr=Math.min(devicePixelRatio,2);
 refCanvas.width=w*dpr;refCanvas.height=h*dpr;refCanvas.style.width=`${w}px`;refCanvas.style.height=`${h}px`;
 const ctx=refCanvas.getContext('2d')!;ctx.scale(dpr,dpr);ctx.fillStyle='#fafaf6';ctx.fillRect(0,0,w,h);
 if(!reference.complete||!reference.naturalWidth)return;
 const refView=currentView==='quarter'?'front':currentView;const anchor={front:344,side:325,back:355}[refView];
 const [top,bottom]=bounds[refView],dh=h*2.275*camera.zoom/(2*Math.max(1.19,.84*h/w)),dw=714*dh/(bottom-top);
 ctx.drawImage(reference,0,top,714,bottom-top,w/2-anchor*dh/(bottom-top),(h-dh)/2+(controls.target.y-1.13)*dh/2.275,dw,dh);
}
reference.onload=drawReference;new ResizeObserver(drawReference).observe(refCanvas.parentElement!);
function view(name:keyof typeof views){controls.enableRotate=false;document.querySelector('#orbit')!.classList.remove('active');document.querySelector('section h2')!.textContent=name==='quarter'?'正面参考（无对应斜角原图）':'原始参考';currentView=name;camera.position.fromArray(views[name]);camera.zoom=1;camera.updateProjectionMatrix();controls.target.set(0,1.13,0);controls.update();document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===name));reference.src=`/reference/full-${name==='quarter'?'front':name}.png`;}
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view as keyof typeof views));view('front');
document.querySelector<HTMLButtonElement>('#detail')!.onclick=()=>{view(currentView);camera.position.y-=.65;controls.target.y-=.65;camera.zoom=currentView==='side'?2.25:1.8;camera.updateProjectionMatrix();controls.update();drawReference();outlineOn=false;outline.style.display='none';document.querySelector('#outline')!.classList.remove('active');};
document.querySelector<HTMLButtonElement>('#arm-detail')!.onclick=()=>{view(currentView);camera.position.y-=.38;controls.target.y-=.38;camera.zoom=currentView==='side'?2.45:1.75;camera.updateProjectionMatrix();controls.update();drawReference();outlineOn=false;outline.style.display='none';};
document.querySelector<HTMLButtonElement>('#face-detail')!.onclick=()=>{view(currentView);camera.position.y+=.48;controls.target.y+=.48;camera.zoom=1.75;camera.updateProjectionMatrix();controls.update();drawReference();outlineOn=false;outline.style.display='none';};
document.querySelector<HTMLButtonElement>('#ear-detail')!.onclick=()=>{view(currentView);camera.position.y+=.66;controls.target.y+=.66;camera.zoom=currentView==='side'?2.75:1.8;camera.updateProjectionMatrix();controls.update();drawReference();outlineOn=false;outline.style.display='none';};
document.querySelector<HTMLButtonElement>('#orbit')!.onclick=()=>{controls.enableRotate=!controls.enableRotate;document.querySelector('#orbit')!.classList.toggle('active',controls.enableRotate);document.querySelector('section h2')!.textContent=controls.enableRotate?'原图（自由旋转时机位不对应）':'原始参考';if(!controls.enableRotate)view(currentView);};
// Reference contours use exactly the same scale and anchor as the left image.
const outline=document.createElement('canvas');outline.style.cssText='position:absolute;inset:0;pointer-events:none;display:none';stage.append(outline);
type OutlineData={rows:number[][];top:number;bottom:number;anchor:number};
let contours:Record<string,OutlineData>={};let outlineOn=false;
function drawOutline(){
 const w=stage.clientWidth,h=stage.clientHeight,dpr=Math.min(devicePixelRatio,2);outline.width=w*dpr;outline.height=h*dpr;outline.style.width=`${w}px`;outline.style.height=`${h}px`;
 const data=contours[currentView];if(!data||!outlineOn)return;
 const ctx=outline.getContext('2d')!;ctx.scale(dpr,dpr);const dh=h*2.275/(2*Math.max(1.19,.84*h/w)),scale=dh/(data.bottom-data.top);
 ctx.strokeStyle='#bf4963';ctx.lineWidth=1.5;ctx.setLineDash([5,3]);
 for(const side of [0,1]){ctx.beginPath();data.rows.forEach((r,i)=>{const x=w/2+(r[side]-data.anchor)*scale,y=(h-dh)/2+(r[2]-data.top)*scale;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();}
}
fetch('/reference/head-outlines.json').then(r=>r.json()).then(data=>{contours=data;drawOutline();});
document.querySelector<HTMLButtonElement>('#outline')!.onclick=()=>{outlineOn=!outlineOn;outline.style.display=outlineOn?'block':'none';document.querySelector('#outline')!.classList.toggle('active',outlineOn);view(currentView);drawOutline();};
new ResizeObserver(drawOutline).observe(stage);
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(b=>b.onclick=()=>{view(b.dataset.view as keyof typeof views);drawOutline();});
controls.addEventListener('change',drawReference);
controls.addEventListener('start',()=>{outlineOn=false;outline.style.display='none';document.querySelector('#outline')!.classList.remove('active');});
type PoseMode='rest'|'forward'|'backward'|'raise'|'play'|'original';
let poseMode:PoseMode='rest',testModel:T.Group|undefined,originalModel:T.Group|undefined;
let clayMode=false;
const coloredMaterials=new Map<T.Mesh,T.Material|T.Material[]>();
const clayMaterial=new T.MeshStandardMaterial({color:0xbebebe,roughness:1,metalness:0});
document.querySelector<HTMLButtonElement>('#clay-toggle')!.onclick=()=>{clayMode=!clayMode;for(const [mesh,material] of coloredMaterials){mesh.material=clayMode?clayMaterial:material;if(mesh.name==='Lulu_Smile'||mesh.name.startsWith('Lulu_EyeSurface'))mesh.visible=!clayMode;}document.querySelector('#clay-toggle')!.classList.toggle('active',clayMode);updateAppearanceLabel();};
const correctiveMeshes:T.Mesh[]=[];
const armBones=new Map<string,{bone:T.Bone;rest:T.Quaternion}>();
const poseButtons=document.querySelectorAll<HTMLButtonElement>('[data-pose]');
function updateAppearanceLabel(){document.querySelector('#state')!.textContent=poseMode==='original'?'上色前素模':clayMode?'灰模检查':'全彩 · 可旋转检查';}
function choosePose(mode:PoseMode){poseMode=mode;if(testModel)testModel.visible=mode!=='original';if(originalModel)originalModel.visible=mode==='original';poseButtons.forEach(b=>b.classList.toggle('active',b.dataset.pose===mode));document.querySelector('#pose-label')!.textContent=({rest:'完整模型 · 静止',forward:'定格 · 向前小幅摆动',backward:'定格 · 向后小幅摆动',raise:'定格 · 小幅抬臂',play:'循环测试 · 点击测试静止停止',original:'本轮上色前素模 · 对照用'})[mode];updateAppearanceLabel();}
poseButtons.forEach(b=>b.onclick=()=>choosePose(b.dataset.pose as PoseMode));
function setupMesh(group:T.Group){group.traverse(o=>{if(o.name.startsWith('Can'))o.visible=false;if(o instanceof T.Mesh){o.castShadow=true;o.receiveShadow=true;}});scene.add(group);}
new GLTFLoader().load('/models/lulu-arm-test.glb?revision=arm-root-3',g=>{originalModel=g.scene;setupMesh(originalModel);originalModel.visible=poseMode==='original';});
new GLTFLoader().load('/models/lulu-complete.glb?revision=front-form-head-restored',g=>{testModel=g.scene;setupMesh(testModel);testModel.traverse(o=>{if(o instanceof T.Mesh)coloredMaterials.set(o,o.material);if(o instanceof T.Mesh&&o.morphTargetDictionary?.BackShoulderSupport!==undefined)correctiveMeshes.push(o);if(o instanceof T.Bone&&/UpperArm|Forearm/.test(o.name))armBones.set(o.name,{bone:o,rest:o.quaternion.clone()});});poseButtons.forEach(b=>b.disabled=false);document.querySelector<HTMLButtonElement>('#clay-toggle')!.disabled=false;choosePose('rest');document.querySelector('#state')!.textContent='全彩 · 可旋转检查';},undefined,error=>{console.error(error);document.querySelector('#state')!.textContent='完整模型载入失败';});
const axis=new T.Vector3(),parentQ=new T.Quaternion(),rotation=new T.Quaternion();
function updateArmPose(time:number){
 if(!testModel||poseMode==='original')return;
 let forward=poseMode==='forward'?18:poseMode==='backward'?-12:poseMode==='play'?3+15*Math.sin(time*1.5):0;
 const lift=poseMode==='raise'?25:0;
 for(const mesh of correctiveMeshes){const index=mesh.morphTargetDictionary!.BackShoulderSupport;mesh.morphTargetInfluences![index]=Math.max(0,-forward)/12;}
 for(const name of ['UpperArm_-1','UpperArm_1','Forearm_-1','Forearm_1']){
  const item=armBones.get(name);if(!item)continue;const {bone,rest}=item;
  bone.quaternion.copy(rest);bone.parent!.getWorldQuaternion(parentQ);parentQ.invert();
  const upper=name.startsWith('Upper'),side=name.endsWith('-1')?-1:1;
  axis.set(1,0,0).applyQuaternion(parentQ);rotation.setFromAxisAngle(axis,T.MathUtils.degToRad(-(upper?forward:forward*.12)));bone.quaternion.premultiply(rotation);
  if(upper&&lift){axis.set(0,0,1).applyQuaternion(parentQ);rotation.setFromAxisAngle(axis,T.MathUtils.degToRad(side*lift));bone.quaternion.premultiply(rotation);}
  bone.updateMatrixWorld(true);
 }
}
let frames=0,stamp=performance.now(),lastFrame=stamp;const frameIntervals:number[]=[];
renderer.setAnimationLoop(()=>{const frameNow=performance.now();frameIntervals.push(frameNow-lastFrame);lastFrame=frameNow;updateArmPose(frameNow/1000);controls.update();lights.rotation.y=Math.atan2(camera.position.x,camera.position.z);renderer.render(scene,camera);frames++;const now=performance.now();if(now-stamp>2000){const metrics=document.querySelector<HTMLElement>('#metrics')!;const fps=frames*1000/(now-stamp),sorted=frameIntervals.slice().sort((a,b)=>a-b),p95=sorted[Math.floor(sorted.length*.95)]??0;metrics.textContent=`${Math.round(fps)} FPS`;Object.assign(metrics.dataset,{fps:fps.toFixed(1),p95FrameMs:p95.toFixed(2),drawCalls:String(renderer.info.render.calls),triangles:String(renderer.info.render.triangles),samples:String(frames)});frameIntervals.length=0;frames=0;stamp=now;}});
