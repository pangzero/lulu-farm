import './gallery.css';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {animalCatalog} from './animal-catalog';
import {animalMaterialRevisions} from './animal-material-revisions';

type ModelId = string;
type Selection = ModelId | 'all';
type ViewName = 'front' | 'side' | 'back' | 'quarter';
type Appearance = 'original' | 'clay' | 'wire';
type ModelEntry = {
  id: ModelId; name: string; icon: string; tint: string; ink: string;
  url: string; bytes: number; version: string; source: string; note: string;
};
type ModelStats = {triangles: number; meshes: number; materials: number; textures: number; bones: number; animations: number};
type LoadedModel = {wrapper: T.Group; size: T.Vector3; stats: ModelStats; materials: Map<T.Mesh, T.Material | T.Material[]>; url: string};

const catalog: ModelEntry[] = [
  {id: 'lulu', name: 'Lulu', icon: 'Lu', tint: '#fae7b8', ink: '#bf8b2b', url: '/models/lulu-official-v1.glb', bytes: 23641420, version: '5f770f53', source: 'lulu-official-v1.glb', note: 'Lulu 正式版 v1 · 用户已确认'},
  ...animalCatalog,
];
const views: Record<ViewName, T.Vector3> = {
  front: new T.Vector3(0, .10, 1).normalize(),
  side: new T.Vector3(-1, .07, 0).normalize(),
  back: new T.Vector3(0, .10, -1).normalize(),
  quarter: new T.Vector3(-1, .24, 1).normalize(),
};
const query = new URLSearchParams(location.search);
const requested = query.get('model');
const materialRevisions = new Map(animalMaterialRevisions.map(item => [item.id, item]));
let eyeVersion: 'original' | 'refined' = query.get('eyes') === 'original' ? 'original' : 'refined';
let detailView: 'full' | 'head' | 'eyes' = query.get('detail') === 'eyes' ? 'eyes' : query.get('detail') === 'head' ? 'head' : 'full';
let selection: Selection = requested === 'all' || catalog.some(m => m.id === requested) ? requested! : 'lulu';
const comparisonSize = 4;
const comparisonPages = Math.ceil(catalog.length / comparisonSize);
const requestedGroup = Number(query.get('group') ?? 0);
let comparisonPage = Number.isInteger(requestedGroup) ? Math.max(0, Math.min(comparisonPages - 1, requestedGroup)) : 0;
let currentView: ViewName = query.get('view') && query.get('view')! in views ? query.get('view') as ViewName : 'front';
let appearance: Appearance = 'original';
let interactionStarted = false;
const loaded = new Map<ModelId, LoadedModel>();
const failed = new Set<ModelId>();
const cards = new Map<ModelId, HTMLButtonElement>();
const statuses = new Map<ModelId, HTMLElement>();
let loadingId: ModelId | null = null;
const stage = document.querySelector<HTMLDivElement>('#gallery-stage')!;
const allButton = document.querySelector<HTMLButtonElement>('#all-models')!;
const loadingState = document.querySelector<HTMLDivElement>('#loading-state')!;
const loadingMessage = document.querySelector<HTMLSpanElement>('#loading-message')!;
const retry = document.querySelector<HTMLButtonElement>('#retry-load')!;
const download = document.querySelector<HTMLAnchorElement>('#download-model')!;
const autoRotate = document.querySelector<HTMLButtonElement>('#auto-rotate')!;
const paging = document.querySelector<HTMLDivElement>('#comparison-paging')!;
const previousGroup = document.querySelector<HTMLButtonElement>('#previous-group')!;
const nextGroup = document.querySelector<HTMLButtonElement>('#next-group')!;
const eyeStudyControls = document.querySelector<HTMLDivElement>('#eye-study-controls')!;
const number = new Intl.NumberFormat('zh-CN');
document.querySelector('#model-count')!.textContent = String(catalog.length).padStart(2, '0');
document.querySelector('#library-summary')!.textContent = `Lulu 与 ${animalCatalog.length} 个动物模型，点击即可查看。`;
document.querySelector('#footer-library')!.textContent = `模型工作台 / Lulu · ${animalCatalog.length} 个农场动物`;

const list = document.querySelector<HTMLDivElement>('#model-list')!;
for (const asset of catalog) {
  const button = document.createElement('button');
  button.className = 'model-card';
  button.dataset.model = asset.id;
  button.style.setProperty('--tint', asset.tint);
  button.style.setProperty('--ink', asset.ink);
  button.setAttribute('aria-pressed', 'false');
  button.setAttribute('aria-label', `查看${asset.name}模型`);
  button.innerHTML = `<span class="model-icon" aria-hidden="true">${asset.icon}</span><span><strong>${asset.name}</strong><small>GLB · ${(asset.bytes / 1e6).toFixed(1)} MB</small></span><span class="model-status">查看</span>`;
  button.onclick = () => selectModel(asset.id);
  cards.set(asset.id, button);
  statuses.set(asset.id, button.querySelector<HTMLElement>('.model-status')!);
  list.append(button);
}

const renderer = new T.WebGLRenderer({antialias: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.outputColorSpace = T.SRGBColorSpace;
renderer.toneMapping = T.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = T.PCFSoftShadowMap;
renderer.domElement.setAttribute('aria-label', 'Lulu 与农场动物的交互式三维模型');
renderer.domElement.setAttribute('role', 'img');
stage.prepend(renderer.domElement);
const scene = new T.Scene();
scene.background = new T.Color('#fafaf6');
const pmrem = new T.PMREMGenerator(renderer);
const room = new RoomEnvironment();
const environment = pmrem.fromScene(room, .04);
scene.environment = environment.texture;
scene.environmentIntensity = .15;
room.dispose();
pmrem.dispose();
scene.add(new T.HemisphereLight('#fffef5', '#fff2cf', 1.5));
const lights = new T.Group();
scene.add(lights);
const key = new T.DirectionalLight('#ffffff', .85);
key.position.set(-3, 6, 5);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
Object.assign(key.shadow.camera, {left: -13, right: 13, top: 6, bottom: -6, near: .1, far: 30});
key.shadow.normalBias = .02;
key.shadow.bias = -.0001;
lights.add(key);
const fill = new T.DirectionalLight('#ffffff', .55);
fill.position.set(4, 2, 3);
lights.add(fill);
const frontFill = new T.DirectionalLight('#fff9ed', .65);
frontFill.position.set(0, 2, 6);
lights.add(frontFill);
const floor = new T.Mesh(new T.PlaneGeometry(100, 100), new T.ShadowMaterial({color: '#756e4f', opacity: .08}));
floor.rotation.x = -Math.PI / 2;
floor.position.y = -.012;
floor.receiveShadow = true;
scene.add(floor);
const camera = new T.OrthographicCamera(-6, 6, 3, -3, .01, 200);
camera.position.set(0, 2, 12);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = .08;
controls.minZoom = .35;
controls.maxZoom = 7;
controls.minPolarAngle = .05;
controls.maxPolarAngle = Math.PI * .91;
controls.autoRotateSpeed = 1.1;
controls.target.set(0, 1.1, 0);
controls.update();
const clay = new T.MeshStandardMaterial({color: '#d3d7cb', roughness: 1, metalness: 0});
const wire = new T.MeshBasicMaterial({color: '#657356', wireframe: true});

function wantedAssets() {
  return selection === 'all'
    ? catalog.slice(comparisonPage * comparisonSize, (comparisonPage + 1) * comparisonSize)
    : catalog.filter(asset => asset.id === selection);
}

function effectiveAsset(asset: ModelEntry): ModelEntry {
  if (asset.id === 'cow' && eyeVersion === 'refined' && query.get('cowHead') === 'previous') {
    return {...asset, url: '/models/animals-refined/v1/cow.glb', bytes: 30399340,
      version: '98d461ac', source: 'cow-materials-v1.glb', note: '上一版 v1 · 耳部乱纹清理不足'};
  }
  const revision = materialRevisions.get(asset.id);
  const cowHeadV4 = revision?.url.endsWith('cow-head-clean-v4.glb');
  return revision && eyeVersion === 'refined'
    ? {...asset, url: revision.url, bytes: revision.bytes, version: revision.version,
      source: cowHeadV4 ? 'cow-head-clean-v4.glb' : `${asset.id}-materials-v1.glb`,
      note: cowHeadV4 ? '牛头材质 v4 · 耳部主要乱纹已减弱，角根仍有细痕' : '材质修订 v1 · 眼部'}
    : asset;
}

function currentModels(): [ModelId, LoadedModel][] {
  return wantedAssets().filter(asset => loaded.has(asset.id)).map(asset => [asset.id, loaded.get(asset.id)!]);
}

function syncURL() {
  const url = new URL(location.href);
  url.searchParams.set('model', selection);
  url.searchParams.set('view', currentView);
  if (selection === 'all') url.searchParams.set('group', String(comparisonPage));
  else url.searchParams.delete('group');
  if (selection === 'all' || materialRevisions.has(selection)) {
    url.searchParams.set('eyes', eyeVersion);
    if (selection !== 'all' && detailView !== 'full') url.searchParams.set('detail', detailView);
    else url.searchParams.delete('detail');
  } else {
    url.searchParams.delete('eyes');
    url.searchParams.delete('detail');
  }
  history.replaceState(null, '', url);
}

function arrangeModels(direction: T.Vector3) {
  if (selection !== 'all') {
    loaded.get(selection)?.wrapper.position.set(0, 0, 0);
    return;
  }
  const right = new T.Vector3().crossVectors(new T.Vector3(0, 1, 0), direction).normalize();
  const entries = currentModels().map(([, item]) => item);
  const widths = entries.map(item => Math.abs(right.x) * item.size.x + Math.abs(right.z) * item.size.z);
  const gap = .78;
  let offset = -(widths.reduce((sum, width) => sum + width, 0) + Math.max(0, entries.length - 1) * gap) / 2;
  entries.forEach((item, i) => {
    item.wrapper.position.copy(right).multiplyScalar(offset + widths[i] / 2);
    offset += widths[i] + gap;
  });
}

function modelBounds() {
  const box = new T.Box3();
  for (const [, item] of currentModels()) box.union(new T.Box3().setFromObject(item.wrapper));
  return box;
}

function fitCamera(direction: T.Vector3) {
  const revision = materialRevisions.get(selection);
  const detailBox = revision && detailView !== 'full' ? (detailView === 'eyes' ? revision.focus_box : revision.head_box) : null;
  const box = detailBox
    ? new T.Box3(new T.Vector3(...detailBox[0] as [number, number, number]), new T.Vector3(...detailBox[1] as [number, number, number]))
    : modelBounds();
  if (box.isEmpty()) return;
  const center = box.getCenter(new T.Vector3());
  const size = box.getSize(new T.Vector3());
  controls.target.copy(center);
  camera.position.copy(center).addScaledVector(direction, Math.max(10, size.length() * 2));
  camera.up.set(0, 1, 0);
  camera.lookAt(center);
  const right = new T.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  const up = new T.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
  let halfWidth = 0, halfHeight = 0;
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
    const point = new T.Vector3(x, y, z).sub(center);
    halfWidth = Math.max(halfWidth, Math.abs(point.dot(right)));
    halfHeight = Math.max(halfHeight, Math.abs(point.dot(up)));
  }
  const aspect = stage.clientWidth / Math.max(1, stage.clientHeight);
  const minimumHalf = detailBox ? .18 : .8;
  const half = Math.max(halfHeight, halfWidth / aspect, minimumHalf) * 1.33;
  camera.left = -half * aspect;
  camera.right = half * aspect;
  camera.top = half;
  camera.bottom = -half;
  camera.zoom = 1;
  camera.updateProjectionMatrix();
  // Reserve space for the floating view controls instead of covering the model's feet.
  const shift = 2 * half * Math.min(24, stage.clientHeight * .07) / stage.clientHeight;
  camera.position.addScaledVector(up, -shift);
  controls.target.addScaledVector(up, -shift);
  controls.update();
}

function markView(view: ViewName | null) {
  document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button => {
    const active = button.dataset.view === view;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

function setView(view: ViewName) {
  currentView = view;
  interactionStarted = false;
  controls.autoRotate = false;
  autoRotate.classList.remove('active');
  autoRotate.setAttribute('aria-pressed', 'false');
  arrangeModels(views[view]);
  fitCamera(views[view]);
  markView(view);
  syncURL();
}

function applyAppearance(item: LoadedModel) {
  for (const [mesh, original] of item.materials) mesh.material = appearance === 'clay' ? clay : appearance === 'wire' ? wire : original;
}

function updateInfo() {
  const entries = currentModels();
  const wanted = wantedAssets();
  const sum: ModelStats = {triangles: 0, meshes: 0, materials: 0, textures: 0, bones: 0, animations: 0};
  for (const [, item] of entries) for (const field of Object.keys(sum) as (keyof ModelStats)[]) sum[field] += item.stats[field];
  document.querySelector('#stat-triangles')!.textContent = entries.length ? number.format(sum.triangles) : '—';
  document.querySelector('#stat-meshes')!.textContent = entries.length ? String(sum.meshes) : '—';
  document.querySelector('#stat-materials')!.textContent = entries.length ? `${sum.materials} / ${sum.textures}` : '—';
  document.querySelector('#stat-animation')!.textContent = entries.length ? `${sum.bones} / ${sum.animations}` : '—';
  const baseAsset = catalog.find(item => item.id === selection);
  const asset = baseAsset ? effectiveAsset(baseAsset) : undefined;
  document.querySelector('#view-title')!.textContent = asset ? `${asset.name} · 模型预览` : 'Lulu 与农场伙伴';
  document.querySelector('#view-subtitle')!.textContent = asset ? `${asset.note} · 拖动查看完整外形` : `第 ${comparisonPage + 1} / ${comparisonPages} 组 · 按相同显示高度排列，方便对照外形。`;
  const fileInfo = document.querySelector<HTMLElement>('#file-info')!;
  fileInfo.textContent = asset ? asset.source : `${eyeVersion === 'refined' ? '材质修订版' : 'Meshy 原版'} · 仅在查看器中统一显示高度`;
  fileInfo.title = asset?.source ?? '相同几何，不同材质版本；显示比例不代表实际体型。';
  download.hidden = !asset;
  if (asset) {
    download.href = asset.url;
    download.download = eyeVersion === 'refined' && materialRevisions.has(asset.id) ? asset.source : asset.url.split('/').pop()!;
  }
  allButton.classList.toggle('active', selection === 'all');
  allButton.setAttribute('aria-pressed', String(selection === 'all'));
  for (const [id, button] of cards) {
    const shown = effectiveAsset(catalog.find(item => item.id === id)!);
    button.querySelector('small')!.textContent = `GLB · ${(shown.bytes / 1e6).toFixed(1)} MB`;
    button.classList.toggle('active', id === selection);
    button.classList.toggle('in-group', selection === 'all' && wanted.some(item => item.id === id));
    button.setAttribute('aria-pressed', String(id === selection));
  }
  paging.hidden = selection !== 'all';
  eyeStudyControls.hidden = selection !== 'all' && !materialRevisions.has(selection);
  document.querySelector('#material-version-title')!.textContent = asset ? `${asset.name} · 材质对比` : '当前组 · 材质对比';
  document.querySelector<HTMLElement>('#detail-controls')!.hidden = selection === 'all';
  document.querySelectorAll<HTMLButtonElement>('button[data-eye-version]').forEach(button => {
    const active = button.dataset.eyeVersion === eyeVersion;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  document.querySelectorAll<HTMLButtonElement>('[data-eye-detail]').forEach(button => {
    const active = button.dataset.eyeDetail === detailView;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  stage.dataset.eyeVersion = selection === 'all' || materialRevisions.has(selection) ? eyeVersion : '';
  stage.dataset.detail = materialRevisions.has(selection) ? detailView : 'full';
  previousGroup.disabled = comparisonPage === 0;
  nextGroup.disabled = comparisonPage === comparisonPages - 1;
  document.querySelector('#group-label')!.textContent = `${comparisonPage + 1} / ${comparisonPages}`;
  const failures = wanted.filter(item => failed.has(item.id)).length;
  const hasError = failures === wanted.length;
  loadingState.hidden = entries.length > 0;
  loadingState.classList.toggle('failed', hasError);
  loadingMessage.textContent = hasError ? '模型载入失败，请检查文件后重试。' : '正在载入模型与贴图…';
  retry.hidden = !hasError;
  document.querySelector('#load-summary')!.textContent = `${entries.length} / ${wanted.length} 已载入 · 共 ${catalog.length} 项资产${failures ? ` · ${failures} 个失败` : ''}`;
  stage.dataset.readyModels = [...loaded.keys()].join(',');
  stage.dataset.selection = selection;
  stage.dataset.state = entries.length === wanted.length ? 'ready' : hasError ? 'error' : entries.length ? 'partial' : 'loading';
}

function selectModel(id: Selection) {
  selection = id;
  if (id !== 'all') comparisonPage = Math.floor(catalog.findIndex(asset => asset.id === id) / comparisonSize);
  const wanted = new Set(wantedAssets().map(asset => asset.id));
  for (const [key, item] of loaded) {
    if (wanted.has(key) && item.url === effectiveAsset(catalog.find(asset => asset.id === key)!).url) continue;
    scene.remove(item.wrapper);
    for (const [mesh, material] of item.materials) mesh.material = material;
    disposeModel(item.wrapper);
    loaded.delete(key);
    statuses.get(key)!.textContent = '查看';
  }
  renderer.renderLists.dispose();
  const firstVisible = wantedAssets()[0];
  cards.get(firstVisible.id)?.scrollIntoView({block: 'start', inline: 'nearest'});
  setView(currentView);
  updateInfo();
  void loadNextModel();
}
allButton.onclick = () => selectModel('all');
previousGroup.onclick = () => {if (comparisonPage > 0) {comparisonPage--; selectModel('all');}};
nextGroup.onclick = () => {if (comparisonPage < comparisonPages - 1) {comparisonPage++; selectModel('all');}};
document.querySelectorAll<HTMLButtonElement>('button[data-eye-version]').forEach(button => {
  button.onclick = () => {
    if (eyeVersion === button.dataset.eyeVersion) return;
    eyeVersion = button.dataset.eyeVersion as typeof eyeVersion;
    for (const [id, item] of loaded) {
      if (!materialRevisions.has(id)) continue;
      scene.remove(item.wrapper);
      for (const [mesh, material] of item.materials) mesh.material = material;
      disposeModel(item.wrapper);
      loaded.delete(id);
      failed.delete(id);
      statuses.get(id)!.classList.remove('error');
      statuses.get(id)!.textContent = '载入中';
    }
    renderer.renderLists.dispose();
    // Identical geometry/bounds let the comparison preserve orbit and zoom.
    interactionStarted = true;
    for (const asset of wantedAssets()) failed.delete(asset.id);
    syncURL();
    updateInfo();
    void loadNextModel();
  };
});
document.querySelectorAll<HTMLButtonElement>('[data-eye-detail]').forEach(button => {
  button.onclick = () => {
    detailView = button.dataset.eyeDetail as typeof detailView;
    setView(currentView);
    updateInfo();
  };
});
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button => {button.onclick = () => setView(button.dataset.view as ViewName);});
document.querySelector<HTMLButtonElement>('#reset-view')!.onclick = () => setView(currentView);
document.querySelectorAll<HTMLButtonElement>('[data-material]').forEach(button => {
  button.onclick = () => {
    appearance = button.dataset.material as Appearance;
    loaded.forEach(applyAppearance);
    document.querySelectorAll<HTMLButtonElement>('[data-material]').forEach(other => {
      const active = other === button;
      other.classList.toggle('active', active);
      other.setAttribute('aria-pressed', String(active));
    });
  };
});
autoRotate.onclick = () => {
  controls.autoRotate = !controls.autoRotate;
  autoRotate.classList.toggle('active', controls.autoRotate);
  autoRotate.setAttribute('aria-pressed', String(controls.autoRotate));
  if (controls.autoRotate) markView(null);
};
retry.onclick = () => {
  for (const asset of wantedAssets()) {
    failed.delete(asset.id);
    statuses.get(asset.id)!.classList.remove('error');
  }
  updateInfo();
  void loadNextModel();
};
controls.addEventListener('start', () => {interactionStarted = true; markView(null);});

new ResizeObserver(() => {
  const width = stage.clientWidth, height = stage.clientHeight;
  if (!width || !height) return;
  renderer.setSize(width, height);
  const direction = camera.position.clone().sub(controls.target).normalize();
  fitCamera(direction);
}).observe(stage);

const loader = new GLTFLoader();

// Downloads contain 4K color/normal and 2K material maps. Keep only this group
// resident and load sequentially to avoid decoding every animal at startup.
function disposeModel(model: T.Object3D) {
  const geometries = new Set<T.BufferGeometry>();
  const materials = new Set<T.Material>();
  const textures = new Set<T.Texture>();
  const bitmaps = new Set<ImageBitmap>();
  model.traverse(object => {
    if (!(object instanceof T.Mesh)) return;
    geometries.add(object.geometry);
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      materials.add(material);
      for (const value of Object.values(material)) if (value instanceof T.Texture) {
        textures.add(value);
        if (typeof ImageBitmap !== 'undefined' && value.source.data instanceof ImageBitmap) bitmaps.add(value.source.data);
      }
    }
  });
  geometries.forEach(value => value.dispose());
  materials.forEach(value => value.dispose());
  textures.forEach(value => value.dispose());
  bitmaps.forEach(value => value.close());
}

async function loadNextModel() {
  if (loadingId !== null) return;
  const asset = wantedAssets().find(item => !loaded.has(item.id) && !failed.has(item.id));
  if (!asset) return;
  loadingId = asset.id;
  await loadModel(effectiveAsset(asset));
  loadingId = null;
  void loadNextModel();
}

async function loadModel(asset: ModelEntry) {
  try {
    const gltf = await loader.loadAsync(`${asset.url}?v=${asset.version}`, event => {
      const percent = Math.min(99, Math.round(event.loaded / (event.total || asset.bytes) * 100));
      statuses.get(asset.id)!.textContent = percent < 99 ? `${percent}%` : '贴图';
    });
    if (!wantedAssets().some(item => item.id === asset.id && effectiveAsset(item).url === asset.url)) {
      disposeModel(gltf.scene);
      statuses.get(asset.id)!.textContent = '查看';
      return;
    }
    const model = gltf.scene;
    model.updateMatrixWorld(true);
    const box = new T.Box3().setFromObject(model);
    const size = box.getSize(new T.Vector3());
    const center = box.getCenter(new T.Vector3());
    if (box.isEmpty() || size.y <= 0) throw new Error('模型没有可预览的网格');
    const scale = 2.2 / size.y;
    // Display transforms live on parent groups; the imported mesh, UVs and materials are untouched.
    const wrapper = new T.Group();
    wrapper.name = asset.id;
    const normalizer = new T.Group();
    normalizer.scale.setScalar(scale);
    const origin = new T.Group();
    origin.position.set(-center.x, -box.min.y, -center.z);
    origin.add(model);
    normalizer.add(origin);
    wrapper.add(normalizer);
    const materials = new Map<T.Mesh, T.Material | T.Material[]>();
    const uniqueMaterials = new Set<T.Material>();
    const textures = new Set<unknown>();
    const stats: ModelStats = {triangles: 0, meshes: 0, materials: 0, textures: 0, bones: 0, animations: gltf.animations.length};
    model.traverse(object => {
      if (object instanceof T.Bone) stats.bones++;
      if (!(object instanceof T.Mesh)) return;
      stats.meshes++;
      stats.triangles += (object.geometry.index?.count ?? object.geometry.getAttribute('position').count) / 3;
      object.castShadow = true;
      object.receiveShadow = true;
      materials.set(object, object.material);
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        uniqueMaterials.add(material);
        for (const value of Object.values(material)) if (value instanceof T.Texture) textures.add(value.source.data);
      }
    });
    stats.materials = uniqueMaterials.size;
    stats.textures = textures.size;
    const entry: LoadedModel = {wrapper, size: size.multiplyScalar(scale), stats, materials, url: asset.url};
    wrapper.visible = selection === 'all' || selection === asset.id;
    scene.add(wrapper);
    loaded.set(asset.id, entry);
    applyAppearance(entry);
    const status = statuses.get(asset.id)!;
    status.textContent = '就绪';
    status.title = `${number.format(stats.triangles)} 三角面`;
    arrangeModels(views[currentView]);
    if (!interactionStarted) {
      fitCamera(views[currentView]);
    }
    updateInfo();
  } catch (error) {
    console.error(`无法载入 ${asset.id}`, error);
    failed.add(asset.id);
    const status = statuses.get(asset.id)!;
    status.textContent = '失败';
    status.classList.add('error');
    updateInfo();
  }
}

selectModel(selection);
let frames = 0, stamp = performance.now();
renderer.setAnimationLoop(() => {
  controls.update();
  lights.rotation.y = Math.atan2(camera.position.x - controls.target.x, camera.position.z - controls.target.z);
  renderer.render(scene, camera);
  // Expose readiness only after the selected model/material/view has rendered.
  // GLTF decoding can finish before its first visible WebGL frame.
  stage.dataset.rendered = currentModels().length === wantedAssets().length
    ? [selection, eyeVersion, currentView, detailView].join('|') : '';
  frames++;
  const now = performance.now();
  if (now - stamp >= 1500) {
    document.querySelector('#render-status')!.textContent = `${Math.round(frames * 1000 / (now - stamp))} FPS · ${loaded.size} 个模型已就绪`;
    stamp = now;
    frames = 0;
  }
});
