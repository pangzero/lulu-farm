import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

/** The current assembled candidate; the accepted static v1 remains untouched. */
export const FARM_CAMERA_LULU_URL = '/models/wardrobe-rig/full-r02/lulu-rig.glb';
export const LULU_SOURCE = {
  revision: 'full-r02',
  url: FARM_CAMERA_LULU_URL,
  sha256: '38a474b3a9f75c05debda10fb29f50a84f668481373e8c16653a20a835007057',
  status: '最新组装候选；有限小动作与换装初检，走跑和用户美术未验收',
  displayHeight: 1.2,
} as const;

export interface FarmCameraStudy {
  dispose: () => void;
  reset: () => void;
  ready: Promise<void>;
}

type Block = { label: string; x: number; z: number; w: number; d: number; h: number; color: string };

/**
 * A camera/layout experiment, not a production farm or locomotion system.
 * The one loaded Lulu is left in her original rest pose, with her original shorts.
 */
export function mountFarmCameraStudy(
  container: HTMLElement,
  onStatus?: (message: string) => void,
): FarmCameraStudy {
  let disposed = false, frame = 0, lastTime = 0, ready = false;
  let yaw = 0, pitch = 0.61, distance = 5.1, actualDistance = distance, lastStatusTime = 0;
  let dragPointer: number | null = null, lastPointerX = 0, lastPointerY = 0;
  const aborter = new AbortController();
  const keys = new Set<string>();
  const root = document.createElement('section');
  root.className = 'farm-camera-study';
  root.style.cssText = 'position:relative;overflow:hidden;border-radius:14px;background:#c9dfdf;isolation:isolate;';
  const viewport = document.createElement('div');
  viewport.style.cssText = 'width:100%;height:clamp(380px,64vh,620px);min-height:380px;';
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:absolute;top:14px;left:14px;right:14px;display:flex;gap:12px;align-items:flex-start;justify-content:space-between;pointer-events:none;font:13px/1.55 system-ui,sans-serif;color:#243933;';
  const explanation = document.createElement('div');
  explanation.style.cssText = 'padding:10px 13px;background:#ffffffed;border:1px solid #dbe5de;border-radius:10px;max-width:480px;';
  explanation.innerHTML = '<strong>第三人称跟随 · 相机与布局试验</strong><br>Lulu 使用最新组装 full-r02，静止滑行；色块只是布局占位。<br>此处未验收走跑动作，也不代表正式农场或完整碰撞系统。';
  const resetButton = document.createElement('button');
  resetButton.type = 'button';
  resetButton.textContent = '重置视角与位置';
  resetButton.style.cssText = 'pointer-events:auto;flex:none;border:1px solid #c7d6ca;border-radius:9px;padding:9px 12px;color:#274139;background:#ffffffed;cursor:pointer;font:inherit;';
  overlay.append(explanation, resetButton);
  const footer = document.createElement('div');
  footer.style.cssText = 'position:absolute;left:14px;right:14px;bottom:14px;pointer-events:none;border-radius:9px;padding:9px 12px;color:#263c34;background:#ffffffeb;font:13px/1.5 system-ui,sans-serif;';
  const instructions = document.createElement('div');
  instructions.textContent = '点击画面后：WASD／方向键移动 · 拖拽环视 · 滚轮调距离 · Shift 慢移 · R 重置';
  const status = document.createElement('div');
  status.setAttribute('role', 'status');
  status.textContent = '正在载入一份 Lulu 组装模型…';
  footer.append(instructions, status);
  root.append(viewport, overlay, footer);
  container.append(root);
  function report(message: string) {
    if (disposed) return;
    status.textContent = message;
    onStatus?.(message);
  }

  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const canvas = renderer.domElement;
  canvas.tabIndex = 0;
  canvas.setAttribute('aria-label', 'Lulu 第三人称相机试验；点击后使用 WASD 或方向键移动');
  canvas.style.cssText = 'display:block;width:100%;height:100%;outline:none;touch-action:none;cursor:grab;';
  viewport.append(canvas);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#c9dfdf');
  scene.fog = new THREE.Fog('#c9dfdf', 24, 55);
  const camera = new THREE.PerspectiveCamera(52, 1, 0.06, 90);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const environment = pmrem.fromScene(room, 0.04);
  room.dispose();
  pmrem.dispose();
  scene.environment = environment.texture;
  scene.environmentIntensity = 0.16;
  scene.add(new THREE.HemisphereLight('#fffef4', '#a5b5a0', 1.5));
  const sun = new THREE.DirectionalLight('#fffae9', 1.6);
  sun.position.set(-8, 16, 10);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  Object.assign(sun.shadow.camera, { left: -17, right: 17, top: 15, bottom: -15, near: 1, far: 45 });
  sun.shadow.normalBias = 0.035;
  scene.add(sun);
  const fill = new THREE.DirectionalLight('#e2f2ff', 0.5);
  fill.position.set(7, 6, -5);
  scene.add(fill);

  const materials = new Set<THREE.Material>();
  const geometries = new Set<THREE.BufferGeometry>();
  const labelTextures = new Set<THREE.Texture>();
  const colliders: THREE.Mesh[] = [];
  const obstacles: THREE.Box3[] = [];
  function material(color: string, roughness = 1) {
    const m = new THREE.MeshStandardMaterial({ color, roughness, metalness: 0 });
    materials.add(m);
    return m;
  }
  function box(w: number, h: number, d: number, x: number, y: number, z: number, mat: THREE.Material) {
    const geometry = new THREE.BoxGeometry(w, h, d);
    geometries.add(geometry);
    const mesh = new THREE.Mesh(geometry, mat);
    mesh.position.set(x, y, z);
    mesh.castShadow = h > 0.12;
    mesh.receiveShadow = true;
    scene.add(mesh);
    return mesh;
  }
  function label(text: string, x: number, y: number, z: number) {
    const image = document.createElement('canvas');
    image.width = 512; image.height = 100;
    const ctx = image.getContext('2d')!;
    ctx.fillStyle = '#ffffffed';
    ctx.fillRect(0, 0, 512, 100);
    ctx.fillStyle = '#34483a';
    ctx.font = '500 37px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(text, 256, 50);
    const texture = new THREE.CanvasTexture(image);
    texture.colorSpace = THREE.SRGBColorSpace;
    labelTextures.add(texture);
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
    materials.add(spriteMaterial);
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(2.7, 0.53, 1);
    sprite.position.set(x, y, z);
    scene.add(sprite);
  }
  box(29, 0.18, 25, 0, -0.1, 0, material('#b1c28f'));
  box(2.0, 0.016, 24.5, 0, 0, 0, material('#dccaaa'));
  box(20, 0.017, 1.4, 0, 0.002, -0.7, material('#dccaaa'));
  const blocks: Block[] = [
    { label: '主屋位置 · 占位', x: 0, z: -7.1, w: 5.5, d: 4.6, h: 4.2, color: '#e7cda8' },
    { label: '牧场位置 · 占位', x: 7.1, z: -6.7, w: 4.0, d: 4.0, h: 2.3, color: '#c1b89a' },
    { label: '摊位位置 · 占位', x: -7.2, z: -4.1, w: 3.4, d: 2.6, h: 2.3, color: '#e0b497' },
  ];
  for (const b of blocks) {
    const mesh = box(b.w, b.h, b.d, b.x, b.h / 2, b.z, material(b.color));
    mesh.updateMatrixWorld();
    obstacles.push(new THREE.Box3().setFromObject(mesh));
    colliders.push(mesh);
    label(b.label, b.x, b.h + 0.5, b.z);
  }
  const soil = material('#a88765');
  for (let row = 0; row < 3; row++) for (let col = 0; col < 4; col++) {
    box(1.12, 0.055, 1.12, -7.2 + col * 1.2, 0.021, 2.0 + row * 1.2, soil);
  }
  label('田区 · 每格 1.2 单位', -5.4, 1.0, 4.8);
  const water = box(2.2, 0.04, 24, 11.9, -0.015, 0, material('#88bfcb', 0.82));
  water.castShadow = false;
  obstacles.push(new THREE.Box3(new THREE.Vector3(10.7, -1, -12), new THREE.Vector3(13.1, 1, 12)));
  label('水岸位置 · 占位', 11.1, 0.8, -2.5);

  const actor = new THREE.Group();
  actor.name = 'Lulu_current_assembled_readonly';
  actor.position.set(0, 0, 3.0);
  scene.add(actor);
  const facing = new THREE.Group();
  facing.rotation.y = Math.PI;
  actor.add(facing);
  const focus = new THREE.Vector3(0, 0.78, 3);
  const desiredFocus = new THREE.Vector3();
  const cameraOffset = new THREE.Vector3();
  const desiredCamera = new THREE.Vector3();
  const movement = new THREE.Vector3();
  const ray = new THREE.Raycaster();
  const rayDirection = new THREE.Vector3();
  let fadedCollider: THREE.Mesh | null = null;
  const radius = 0.32;
  const walkKeys = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowLeft', 'ArrowDown', 'ArrowRight', 'ShiftLeft', 'ShiftRight']);
  function isTyping(target: EventTarget | null) {
    return target instanceof HTMLElement && (target.isContentEditable || !!target.closest('input,textarea,select,[contenteditable="true"]'));
  }
  function clearKeys() { keys.clear(); }
  function fadePlaceholder(next: THREE.Mesh | null) {
    if (next === fadedCollider) return;
    for (const [mesh, faded] of [[fadedCollider, false], [next, true]] as const) {
      if (!mesh) continue;
      for (const mat of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        mat.transparent = faded;
        mat.opacity = faded ? 0.15 : 1;
        mat.depthWrite = !faded;
        mat.needsUpdate = true;
      }
    }
    fadedCollider = next;
  }
  function canStand(x: number, z: number) {
    if (x < -13.4 || x > 10.3 || z < -11.3 || z > 11.3) return false;
    for (const b of obstacles) {
      const cx = Math.max(b.min.x, Math.min(x, b.max.x));
      const cz = Math.max(b.min.z, Math.min(z, b.max.z));
      if ((x - cx) ** 2 + (z - cz) ** 2 < radius ** 2) return false;
    }
    return true;
  }
  function updateCamera(dt: number, snap = false) {
    desiredFocus.copy(actor.position); desiredFocus.y += 0.78;
    focus.lerp(desiredFocus, snap ? 1 : 1 - Math.exp(-12 * dt));
    cameraOffset.set(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
    desiredCamera.copy(focus).addScaledVector(cameraOffset, distance);
    rayDirection.copy(desiredCamera).sub(focus).normalize();
    ray.set(focus, rayDirection);
    ray.near = 0.08; ray.far = distance;
    const hit = ray.intersectObjects(colliders, false)[0];
    // A near wall would force the lens into Lulu's head. In this layout study,
    // fade that temporary block instead; real-asset occlusion needs its own pass.
    const tooNear = !!hit && hit.distance < 2.48;
    fadePlaceholder(tooNear ? hit.object as THREE.Mesh : null);
    const clearDistance = hit ? Math.max(2.2, hit.distance - 0.28) : distance;
    root.dataset.cameraOcclusion = tooNear ? 'placeholder-fade' : hit ? 'close-in' : 'clear';
    // Close in immediately at an obstruction; return outward more gently.
    actualDistance = snap || clearDistance < actualDistance ? clearDistance : THREE.MathUtils.lerp(actualDistance, clearDistance, 1 - Math.exp(-6 * dt));
    desiredCamera.copy(focus).addScaledVector(cameraOffset, actualDistance);
    camera.position.lerp(desiredCamera, snap || hit ? 1 : 1 - Math.exp(-16 * dt));
    camera.position.y = Math.max(0.4, camera.position.y);
    camera.lookAt(focus);
  }
  function reset() {
    if (disposed) return;
    clearKeys();
    actor.position.set(0, 0, 3.0);
    facing.rotation.y = Math.PI;
    yaw = 0; pitch = 0.61; distance = actualDistance = 5.1;
    updateCamera(0, true);
    if (ready) report('Lulu full-r02 · 1.2 单位高 · 默认原裤静止 · 仅相机与粗碰撞试验');
  }
  function keydown(event: KeyboardEvent) {
    if (disposed || isTyping(event.target) || document.activeElement !== canvas) return;
    if (walkKeys.has(event.code)) { event.preventDefault(); keys.add(event.code); }
    if (event.code === 'KeyR') { event.preventDefault(); reset(); }
  }
  function keyup(event: KeyboardEvent) { keys.delete(event.code); }
  function visibility() { if (document.hidden) clearKeys(); }
  function pointerdown(event: PointerEvent) {
    if (event.button !== 0 || dragPointer !== null) return;
    canvas.focus({ preventScroll: true });
    dragPointer = event.pointerId; lastPointerX = event.clientX; lastPointerY = event.clientY;
    canvas.setPointerCapture(event.pointerId); canvas.style.cursor = 'grabbing';
    event.preventDefault();
  }
  function pointermove(event: PointerEvent) {
    if (event.pointerId !== dragPointer) return;
    yaw -= (event.clientX - lastPointerX) * 0.005;
    pitch = THREE.MathUtils.clamp(pitch + (event.clientY - lastPointerY) * 0.004, 0.08, 1.12);
    lastPointerX = event.clientX; lastPointerY = event.clientY;
  }
  function pointerup(event: PointerEvent) {
    if (event.pointerId !== dragPointer) return;
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    dragPointer = null; canvas.style.cursor = 'grab';
  }
  function wheel(event: WheelEvent) {
    event.preventDefault();
    distance = THREE.MathUtils.clamp(distance + event.deltaY * 0.006, 2.5, 8.6);
  }
  const resize = new ResizeObserver(() => {
    if (disposed) return;
    const w = Math.max(1, viewport.clientWidth), h = Math.max(1, viewport.clientHeight);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  });
  resize.observe(viewport);
  canvas.addEventListener('keydown', keydown);
  canvas.addEventListener('pointerdown', pointerdown);
  canvas.addEventListener('pointermove', pointermove);
  canvas.addEventListener('pointerup', pointerup);
  canvas.addEventListener('pointercancel', pointerup);
  canvas.addEventListener('lostpointercapture', pointerup);
  canvas.addEventListener('wheel', wheel, { passive: false });
  canvas.addEventListener('blur', clearKeys);
  window.addEventListener('keyup', keyup);
  window.addEventListener('blur', clearKeys);
  document.addEventListener('visibilitychange', visibility);
  resetButton.addEventListener('click', reset);
  reset();
  function tick(time: number) {
    if (disposed) return;
    const dt = lastTime ? Math.min((time - lastTime) / 1000, 0.05) : 0;
    lastTime = time;
    if (ready && !document.hidden) {
      const forward = Number(keys.has('KeyW') || keys.has('ArrowUp')) - Number(keys.has('KeyS') || keys.has('ArrowDown'));
      const right = Number(keys.has('KeyD') || keys.has('ArrowRight')) - Number(keys.has('KeyA') || keys.has('ArrowLeft'));
      movement.set(-Math.sin(yaw) * forward + Math.cos(yaw) * right, 0, -Math.cos(yaw) * forward - Math.sin(yaw) * right);
      if (movement.lengthSq() > 0) {
        movement.normalize();
        const speed = keys.has('ShiftLeft') || keys.has('ShiftRight') ? 0.85 : 2.1;
        const nextX = actor.position.x + movement.x * speed * dt;
        if (canStand(nextX, actor.position.z)) actor.position.x = nextX;
        const nextZ = actor.position.z + movement.z * speed * dt;
        if (canStand(actor.position.x, nextZ)) actor.position.z = nextZ;
        const angle = Math.atan2(movement.x, movement.z);
        const delta = Math.atan2(Math.sin(angle - facing.rotation.y), Math.cos(angle - facing.rotation.y));
        facing.rotation.y += delta * (1 - Math.exp(-13 * dt));
      }
    }
    updateCamera(dt);
    renderer.render(scene, camera);
    root.dataset.rendered = ready ? 'ready' : 'loading';
    root.dataset.actorPosition = `${actor.position.x.toFixed(3)},${actor.position.z.toFixed(3)}`;
    root.dataset.cameraDistance = actualDistance.toFixed(3);
    root.dataset.cameraYaw = THREE.MathUtils.radToDeg(yaw).toFixed(2);
    root.dataset.cameraPitch = THREE.MathUtils.radToDeg(pitch).toFixed(2);
    root.dataset.cameraRequestedDistance = distance.toFixed(3);
    root.dataset.cameraFov = String(camera.fov);
    root.dataset.cameraPosition = camera.position.toArray().map(v => v.toFixed(3)).join(',');
    root.dataset.cameraTarget = focus.toArray().map(v => v.toFixed(3)).join(',');
    root.dataset.gpuGeometries = String(renderer.info.memory.geometries);
    root.dataset.gpuTextures = String(renderer.info.memory.textures);
    root.dataset.drawCalls = String(renderer.info.render.calls);
    root.dataset.pressedKeys = String(keys.size);
    if (ready && time - lastStatusTime > 200) {
      status.textContent = `Lulu full-r02 · 高 1.2 · 静止滑行｜位置 ${actor.position.x.toFixed(1)}, ${actor.position.z.toFixed(1)}｜镜距 ${actualDistance.toFixed(1)}／${distance.toFixed(1)} · 俯角 ${THREE.MathUtils.radToDeg(pitch).toFixed(0)}°${fadedCollider ? ' · 近处占位物淡化' : ''}`;
      lastStatusTime = time;
    }
    frame = requestAnimationFrame(tick);
  }
  frame = requestAnimationFrame(tick);

  const loadedRoots = new Set<THREE.Object3D>();
  function disposeModel(model: THREE.Object3D) {
    const textures = new Set<THREE.Texture>();
    const modelMaterials = new Set<THREE.Material>();
    const modelGeometries = new Set<THREE.BufferGeometry>();
    const skeletons = new Set<THREE.Skeleton>();
    model.traverse(o => {
      if (!(o instanceof THREE.Mesh)) return;
      modelGeometries.add(o.geometry);
      for (const mat of Array.isArray(o.material) ? o.material : [o.material]) {
        modelMaterials.add(mat);
        for (const value of Object.values(mat)) if (value instanceof THREE.Texture) textures.add(value);
      }
      if (o instanceof THREE.SkinnedMesh) skeletons.add(o.skeleton);
    });
    for (const texture of textures) {
      texture.dispose();
      const image = texture.source.data;
      if (typeof ImageBitmap !== 'undefined' && image instanceof ImageBitmap) image.close();
    }
    for (const mat of modelMaterials) mat.dispose();
    for (const geo of modelGeometries) geo.dispose();
    for (const skeleton of skeletons) skeleton.dispose();
  }
  const readyPromise = (async () => {
    try {
      const response = await fetch(FARM_CAMERA_LULU_URL, { signal: aborter.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.arrayBuffer();
      if (disposed) return;
      const model = await new GLTFLoader().parseAsync(data, '/models/wardrobe-rig/full-r02/');
      if (disposed) { disposeModel(model.scene); return; }
      loadedRoots.add(model.scene);
      const bounds = new THREE.Box3().setFromObject(model.scene);
      const size = bounds.getSize(new THREE.Vector3());
      if (!(size.y > 0)) throw new Error('Lulu 包围盒高度无效');
      const center = bounds.getCenter(new THREE.Vector3());
      const scale = 1.2 / size.y;
      const normalization = new THREE.Group();
      normalization.scale.setScalar(scale);
      normalization.position.set(-center.x * scale, -bounds.min.y * scale, -center.z * scale);
      normalization.add(model.scene);
      facing.add(normalization);
      model.scene.traverse(o => {
        if (o instanceof THREE.Mesh) { o.castShadow = true; o.receiveShadow = true; }
        if (o instanceof THREE.SkinnedMesh) o.frustumCulled = false;
      });
      // Intentionally do not instantiate an AnimationMixer or play diagnostic clips.
      ready = true;
      root.dataset.luluSource = FARM_CAMERA_LULU_URL;
      root.dataset.luluHeight = '1.2';
      report('Lulu full-r02 · 1.2 单位高 · 默认原裤静止 · 仅相机与粗碰撞试验');
    } catch (error) {
      if (disposed || aborter.signal.aborted) return;
      root.dataset.error = String(error);
      report(`Lulu 载入失败：${String(error)}`);
      console.error('Farm camera study:', error);
    }
  })();

  function dispose() {
    if (disposed) return;
    disposed = true; ready = false;
    aborter.abort(); clearKeys();
    cancelAnimationFrame(frame); resize.disconnect();
    canvas.removeEventListener('keydown', keydown);
    canvas.removeEventListener('pointerdown', pointerdown);
    canvas.removeEventListener('pointermove', pointermove);
    canvas.removeEventListener('pointerup', pointerup);
    canvas.removeEventListener('pointercancel', pointerup);
    canvas.removeEventListener('lostpointercapture', pointerup);
    canvas.removeEventListener('wheel', wheel);
    canvas.removeEventListener('blur', clearKeys);
    window.removeEventListener('keyup', keyup);
    window.removeEventListener('blur', clearKeys);
    document.removeEventListener('visibilitychange', visibility);
    resetButton.removeEventListener('click', reset);
    for (const model of loadedRoots) disposeModel(model);
    for (const geometry of geometries) geometry.dispose();
    for (const mat of materials) mat.dispose();
    for (const texture of labelTextures) texture.dispose();
    environment.dispose(); sun.shadow.dispose();
    renderer.renderLists.dispose(); renderer.dispose(); renderer.forceContextLoss();
    scene.clear(); root.remove();
  }
  return { dispose, reset, ready: readyPromise };
}
