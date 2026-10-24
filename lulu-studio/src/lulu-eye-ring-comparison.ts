import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

// These camera, normalization, environment and light values match meshy-review.ts.
// Both files use the baseline's transform so a changed local bound cannot hide a scale change.
const views={front:[0,1.19,10],side:[-10,1.75,2.6],back:[0,1.19,-10],quarter:[-7,1.4,7],game:[0,4.7,5.2],gamequarter:[-3.8,4.7,3.8]} as const;
type View=keyof typeof views;
type Detail='full'|'eye'|'mark';
type Mode='color'|'clay'|'base'|'nonormal'|'noshadow';
const query=new URLSearchParams(location.search);
const requestedView=query.get('view');
let view:View=requestedView&&requestedView in views?requestedView as View:'front';
let detail:Detail=query.get('detail')==='mark'?'mark':query.get('detail')==='eye'?'eye':'full';
let mode:Mode=query.get('mode')==='noshadow'?'noshadow':query.get('mode')==='clay'?'clay':query.get('mode')==='base'?'base':query.get('mode')==='nonormal'?'nonormal':'color';
let lighting=query.get('light')||'studio';
const revision=query.get('rev')||'orbit-r03';
const root=document.querySelector<HTMLElement>('#compare')!;
const download=document.querySelector<HTMLAnchorElement>('#after-stage + .download a')!;
download.href=`/review/lulu-eye-ring-20261018/${encodeURIComponent(revision)}/lulu-eye-ring.glb`;
document.querySelector('#after-label')!.textContent=`修改后 · 单眼连面试改 ${revision}`;
const status=document.querySelector<HTMLElement>('#status')!;
const clay=new T.MeshStandardMaterial({color:0xbebebe,roughness:1,metalness:0});
const materials=new Map<T.Mesh,{original:T.Material|T.Material[];base:T.Material|T.Material[];nonormal:T.Material|T.Material[];visible:boolean}>();
let ready=false;
let scheduled=false;

function makeStage(id:string){
  const host=document.querySelector<HTMLDivElement>(id)!;
  const renderer=new T.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.outputColorSpace=T.SRGBColorSpace;
  renderer.toneMapping=T.NoToneMapping;
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=T.VSMShadowMap;
  host.append(renderer.domElement);
  const scene=new T.Scene();scene.background=new T.Color('#fafaf6');
  const environment=new T.PMREMGenerator(renderer);
  scene.environment=environment.fromScene(new RoomEnvironment(),.04).texture;
  scene.environmentIntensity=.15;
  const camera=new T.OrthographicCamera(-1,1,1,-1,.1,50);const perspective=new T.PerspectiveCamera(52,1,.06,90);
  const hemi=new T.HemisphereLight('#fffef5','#fff2cf',1.5);scene.add(hemi);
  const lights=new T.Group();scene.add(lights);
  const key=new T.DirectionalLight('#ffffff',.85);key.position.set(-3,5,5);key.castShadow=true;
  key.shadow.mapSize.set(1024,1024);
  Object.assign(key.shadow.camera,{left:-2,right:2,top:3,bottom:-1,near:.1,far:15});
  key.shadow.normalBias=.015;key.shadow.bias=-.0001;key.shadow.radius=20;key.shadow.blurSamples=24;
  const fill=new T.DirectionalLight('#ffffff',.55);fill.position.set(4,2,3);
  const frontFill=new T.DirectionalLight('#fff9ed',.65);frontFill.position.set(0,1.3,5);frontFill.target.position.set(0,1.2,0);
  lights.add(key,fill,frontFill,frontFill.target);
  const floor=new T.Mesh(new T.PlaneGeometry(200,200),new T.ShadowMaterial({color:'#756e4f',opacity:.07}));
  floor.rotation.x=-Math.PI/2;floor.position.y=-.007;floor.receiveShadow=true;scene.add(floor);
  return{host,renderer,scene,camera,perspective,lights,key,fill,frontFill,hemi};
}
const stages=[makeStage('#before-stage'),makeStage('#after-stage')];

function invalidate(){
  delete root.dataset.rendered;
  for(const s of stages)delete s.host.dataset.rendered;
  if(scheduled)return;
  scheduled=true;
  requestAnimationFrame(()=>{scheduled=false;render();});
}

function render(){
  for(const s of stages){
    const w=s.host.clientWidth,h=s.host.clientHeight;
    if(!w||!h)continue;
    const half=Math.max(1.19,.84*h/w);
    s.renderer.setSize(w,h);
    Object.assign(s.camera,{left:-half*w/h,right:half*w/h,top:half,bottom:-half,zoom:detail==='mark'?4.2:detail==='eye'?1.75:1});
    s.camera.position.fromArray(views[view]);
    const offset=detail==='mark'?.55:detail==='eye'?.48:0;
    s.camera.position.y+=offset;
    const tx=detail==='mark'?-.29:0,tz=detail==='mark'?.36:0;
    s.camera.position.x+=tx;s.camera.position.z+=tz;
    s.camera.lookAt(tx,1.13+offset,tz);
    s.camera.updateProjectionMatrix();
    const outdoor=lighting==='outdoor';
    s.key.position.set(...(outdoor?[8,16,-10]:lighting==='inspect'?[4,2,-4]:[-3,5,5]) as [number,number,number]);
    s.key.intensity=outdoor?1.6:.85;
    s.fill.position.set(...(outdoor?[-7,6,5]:[4,2,3]) as [number,number,number]);
    s.fill.intensity=outdoor?.5:lighting==='inspect'?.8:.55;
    s.frontFill.intensity=outdoor?0:.65;
    s.hemi.groundColor.set(outdoor?'#a5b5a0':'#fff2cf');
    s.hemi.color.set(outdoor?'#fffef4':'#fffef5');
    s.lights.rotation.y=lighting==='studio'?Math.atan2(s.camera.position.x,s.camera.position.z):0;
    const game=view==='game'||view==='gamequarter';
    const active=game?s.perspective:s.camera;
    if(game){s.perspective.aspect=w/h;s.perspective.position.fromArray(views[view]);s.perspective.zoom=detail==='mark'?3:detail==='eye'?1.6:1;s.perspective.lookAt(0,1.13,0);s.perspective.updateProjectionMatrix();}
    s.renderer.render(s.scene,active);
  }
  // Set only after BOTH actual models have loaded and the new state was drawn.
  if(ready){
    const state=`modular-r04|under-eye|${view}|${detail}|${mode}|${lighting}|${revision}`;
    root.dataset.rendered=state;
    stages.forEach(s=>s.host.dataset.rendered=state);
    root.setAttribute('aria-busy','false');
  }
}

function applyAppearance(){
  for(const[mesh,saved]of materials){
    mesh.receiveShadow=mode!=='noshadow';
    mesh.material=mode==='clay'?clay:mode==='base'?saved.base:mode==='nonormal'?saved.nonormal:saved.original;
    mesh.visible=saved.visible&&!(mode==='clay'&&(mesh.name==='Lulu_Smile'||mesh.name.startsWith('Lulu_EyeSurface')));
  }
}

function update(){
  root.dataset.detail=detail;root.dataset.view=view;root.dataset.mode=mode;
  for(const kind of ['view','detail','mode'] as const){
    const value=kind==='view'?view:kind==='detail'?detail:mode;
    document.querySelectorAll<HTMLButtonElement>(`button[data-${kind}]`).forEach(b=>{
      const active=b.dataset[kind]===value;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));
    });
  }
  document.querySelectorAll<HTMLButtonElement>('button[data-light]').forEach(b=>{const on=b.dataset.light===lighting;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
  query.set('view',view);query.set('detail',detail);query.set('mode',mode);query.set('light',lighting);
  history.replaceState(null,'',`${location.pathname}?${query}`);
  applyAppearance();
  if(ready)status.textContent=`${({front:'正面',side:'侧面',quarter:'斜角',back:'背面',game:'场景正面',gamequarter:'场景斜角'})[view]} · ${detail==='mark'?'单眼连接近景（4.2×）':detail==='eye'?'眼区近景（1.75×）':'全身正常尺寸（1×）'} · ${({color:'原文件材质',clay:'中性灰',base:'仅基础色',nonormal:'关闭法线贴图',noshadow:'关闭自阴影'})[mode]} · 两份真实模型已载入`;
  invalidate();
}

document.querySelectorAll<HTMLButtonElement>('button[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view as View;update();});
document.querySelectorAll<HTMLButtonElement>('button[data-detail]').forEach(b=>b.onclick=()=>{detail=b.dataset.detail as Detail;update();});
document.querySelectorAll<HTMLButtonElement>('button[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode as Mode;update();});
document.querySelectorAll<HTMLButtonElement>('button[data-light]').forEach(b=>b.onclick=()=>{lighting=b.dataset.light!;update();});
stages.forEach(s=>new ResizeObserver(invalidate).observe(s.host));
update();

const loader=new GLTFLoader();
Promise.all([
  loader.loadAsync('/review/lulu-eye-ring-20261018/baseline/modular-r04.glb'),
  loader.loadAsync(`/review/lulu-eye-ring-20261018/${encodeURIComponent(revision)}/lulu-eye-ring.glb`),
]).then(models=>{
  const baseline=models[0].scene;
  const box=new T.Box3().setFromObject(baseline),size=box.getSize(new T.Vector3()),center=box.getCenter(new T.Vector3()),scale=2.275/size.y;
  models.forEach((g,i)=>{
    const model=g.scene;
    model.scale.setScalar(scale);model.position.set(-center.x*scale,-box.min.y*scale,-center.z*scale);
    model.traverse(o=>{
      if(o.name.startsWith('Can'))o.visible=false;
      if(o instanceof T.Mesh){
        o.castShadow=true;o.receiveShadow=true;
        const convert=(m:T.Material)=>{const p=m as T.MeshStandardMaterial;return new T.MeshBasicMaterial({map:p.map,color:p.color,side:p.side});};
        const clear=(m:T.Material)=>{const c=m.clone() as T.MeshStandardMaterial;c.normalMap=null;return c;};
        materials.set(o,{original:o.material,base:Array.isArray(o.material)?o.material.map(convert):convert(o.material),nonormal:Array.isArray(o.material)?o.material.map(clear):clear(o.material),visible:o.visible});
      }
    });
    stages[i].scene.add(model);
  });
  ready=true;update();
}).catch(error=>{
  console.error(error);status.textContent='模型未载入完成。请检查修正版文件是否已生成，再刷新页面。';
  root.dataset.error='model-load-failed';root.setAttribute('aria-busy','false');
});
