// main.js — scene, interaction, UI
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/CSS2DRenderer.js';
import { M, highlight, setXray } from './materials.js';
import { buildRobot, SUBS } from './robot.js';
import { buildField } from './field.js';
import { createMatchDemo } from './demo.js';

/* ---------- renderer / scene ---------- */
const app = document.getElementById('app');
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false; // world-space map — only re-baked while geometry moves
renderer.shadowMap.needsUpdate = true;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
app.appendChild(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(innerWidth, innerHeight);
labelRenderer.domElement.style.cssText = 'position:absolute;top:0;pointer-events:none;';
app.appendChild(labelRenderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0e13);
scene.fog = new THREE.Fog(0x0b0e13, 120, 320);

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
pmrem.dispose();
scene.environmentIntensity = 0.55;

const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 0.5, 1000);
camera.position.set(23, 16, -26);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 6, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.maxPolarAngle = Math.PI * 0.52;
controls.minDistance = 6;
controls.maxDistance = 220;

/* ---------- lights ---------- */
const key = new THREE.DirectionalLight(0xfff4dd, 2.6);
key.position.set(30, 45, 25);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.left = key.shadow.camera.bottom = -40;
key.shadow.camera.right = key.shadow.camera.top = 40;
key.shadow.camera.far = 140;
key.shadow.bias = -0.0004;
scene.add(key);
const rim = new THREE.DirectionalLight(0x6f9fff, 0.9);
rim.position.set(-35, 25, -30);
scene.add(rim);
scene.add(new THREE.HemisphereLight(0x404856, 0x0a0c10, 0.7));

/* ---------- ground ---------- */
const ground = new THREE.Mesh(new THREE.CircleGeometry(160, 64),
  new THREE.MeshStandardMaterial({ color: 0x14171d, roughness: 0.95, metalness: 0 }));
ground.rotation.x = -Math.PI / 2; ground.position.y = -0.02;
ground.receiveShadow = true;
scene.add(ground);
const grid = new THREE.GridHelper(160, 40, 0x2a2f38, 0x1c2027);
grid.position.y = 0.01;
scene.add(grid);

/* ---------- build ---------- */
const { robot, groups, entries, anim, dims, counts } = buildRobot();
scene.add(robot);

// soft contact shadow — rides under the robot (moves with it in field mode)
const contactShadow = new THREE.Mesh(new THREE.CircleGeometry(14, 40), M.blobShadow);
contactShadow.rotation.x = -Math.PI / 2;
contactShadow.position.y = 0.03;
contactShadow.userData.noXray = true;
robot.add(contactShadow);

const { field, refs } = buildField();
field.visible = false;
scene.add(field);

/* ---------- match demo ---------- */
const captionEl = document.getElementById('caption');
const demo = createMatchDemo({
  scene, robot, anim, refs, camera, controls,
  caption(cap, sub) {
    captionEl.innerHTML = `<b>${cap}</b><span>${sub}</span>
      <span class="cam-hint">drag to orbit freely — "Resume cinematic camera" re-engages</span>`;
  },
  ensureField() { if (!fieldOn) $('btn-field').onclick(); },
  setLift(v) { liftTarget = v; syncBtn(); },
  isAnimating(v) { animating = v; syncBtn(); },
  resetLiftBall() {
    const L = anim.lift;
    L.guided = null;
    L.cradle.add(L.ball);
    L.ball.position.set(0.1, 1.08, 0);
    L.ball.visible = true;
    L.ball.userData.vy = 0;
    L.ballState = 'cup';
    liftTarget = 0; liftT = 0;
    L.s1.position.y = L.s2.position.y = 0;
    L.cradle.rotation.x = -0.1;
  },
  clearShot() { // abort an in-flight Launch Demo ball
    if (shot) {
      shot.ball.visible = false; shot.ball.position.y = -100; shot = null;
      animating = shotAnimWas; syncBtn();
    }
  },
});

/* ---------- sizing cube ---------- */
const cube = new THREE.Group();
{
  const geo = new THREE.BoxGeometry(18, 18, 18);
  cube.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo), M.cubeEdge));
  const ghost = new THREE.Mesh(geo, M.cubeGhost);
  cube.add(ghost);
  cube.position.y = 9;
}
cube.visible = false;
scene.add(cube);

/* ---------- callout labels ---------- */
const labels = [];
function addLabel(text, parent, pos) {
  const div = document.createElement('div');
  div.className = 'p-label';
  div.innerHTML = text;
  const o = new CSS2DObject(div);
  o.position.set(...pos);
  parent.add(o);
  labels.push(o);
  o.visible = false;
}
// launcher parts live in turret-local space (turret origin at z=2.6) — offset callouts to match
addLabel('<b>360° turret</b> · ring gear yaw', groups.launcher, [0, 10.4, 2.6]);
addLabel('<b>dual flywheels</b> · 2.9" nip', groups.launcher, [0, 12.9, 3.15]);
addLabel('<b>servo hood</b> · 40–65° exit', groups.launcher, [0, 13.4, 1.2]);
addLabel('<b>star roller</b> · flexes for NECTAR', groups.intake, [0, 4.6, -7.6]);
addLabel('<b>traction roller</b>', groups.intake, [0, 0.8, -7.6]);
addLabel('<b>feed column</b> · through turret axis', groups.hopper, [0, 8.2, 2.6]);
addLabel('<b>odometry pods</b> ×3', groups.drive, [0, 0.6, 6.0]);
addLabel('<b>control + expansion hub</b>', groups.electronics, [-1.2, 2.6, 5.8]);
addLabel('<b>96mm mecanum</b> ×4', groups.drive, [5.7, 2.2, -5.0]);
addLabel('<b>deposit lift</b> · 2-stage, +14.6"', groups.lift, [-7.0, 13.5, 7.3]);
addLabel('<b>deposit cradle</b> · tips at ~22"', anim.lift.s2, [-7.0, 4.6, 4.9]);
addLabel('<b>column diverter</b> · feeds the lift', groups.lift, [-2.2, 9.9, 3.8]);

/* ---------- state ---------- */
let explodeT = 0, explodeTarget = 0;
let liftT = 0, liftTarget = 0;
let animating = false, xray = false, isolated = null, selected = null;
let fieldOn = false;
const ray = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = document.getElementById('tooltip');

/* ---------- tree panel ---------- */
const treeList = document.getElementById('tree-list');
for (const id in SUBS) {
  const s = SUBS[id];
  const count = entries.filter(e => e.sub === id).length;
  const row = document.createElement('div');
  row.className = 'sub-item'; row.dataset.sub = id;
  row.innerHTML = `<div class="sub-swatch" style="background:${s.color}"></div>
    <div class="sub-name">${s.label}</div>
    <div class="sub-count">${count}</div>
    <div class="sub-eye" title="toggle visibility">◉</div>`;
  row.onclick = (e) => {
    if (e.target.classList.contains('sub-eye')) {
      const g = groups[id]; g.visible = !g.visible;
      e.target.classList.toggle('off', !g.visible);
      return;
    }
    isolate(id === isolated ? null : id);
  };
  treeList.appendChild(row);
}

function isolate(id) {
  isolated = id;
  soloObjs = null;
  document.querySelectorAll('.sub-item').forEach(r =>
    r.classList.toggle('active', r.dataset.sub === id));
  if (!id) { setXray(robot, false); xray = false; syncBtn(); controls.target.set(0, 6, 0); showDefaultInfo(); return; }
  setXray(robot, true, groups[id]);
  xray = 'partial';
  // focus camera on subsystem
  const box = new THREE.Box3().setFromObject(groups[id]);
  const c = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3()).length();
  controls.target.copy(c);
  const dir = camera.position.clone().sub(c).normalize();
  camera.position.copy(c).addScaledVector(dir, Math.max(14, size * 1.5));
  showSubInfo(id);
  syncBtn();
}

/* ---------- part explorer (Parts tab) ---------- */
const partsListEl = document.getElementById('parts-list');
const partsSearch = document.getElementById('parts-search');
const partRows = [];
{
  let curSub = null;
  entries.forEach((e) => {
    if (e.sub !== curSub) {
      curSub = e.sub;
      const gh = document.createElement('div');
      gh.className = 'part-group';
      gh.textContent = SUBS[curSub].label;
      partsListEl.appendChild(gh);
    }
    const row = document.createElement('div');
    row.className = 'part-item';
    row.innerHTML = `<div class="part-dot" style="background:${SUBS[e.sub].color}"></div>
      <div class="sub-name" style="font-size:11.5px">${e.name}</div><div class="pq">×${e.qty}</div>`;
    row.onclick = () => selectEntry(e, true);
    partsListEl.appendChild(row);
    partRows.push({ row, e });
  });
  partsSearch.oninput = () => {
    const q = partsSearch.value.trim().toLowerCase();
    for (const { row, e } of partRows) {
      row.style.display = (!q || e.name.toLowerCase().includes(q)
        || SUBS[e.sub].label.toLowerCase().includes(q)) ? '' : 'none';
    }
    document.querySelectorAll('.part-group').forEach(g => {
      let el = g.nextElementSibling, any = false;
      while (el && !el.classList.contains('part-group')) {
        if (el.style.display !== 'none') any = true;
        el = el.nextElementSibling;
      }
      g.style.display = any ? '' : 'none';
    });
  };
}
document.getElementById('tab-subs').onclick = () => {
  document.getElementById('tab-subs').classList.add('active');
  document.getElementById('tab-parts').classList.remove('active');
  treeList.style.display = ''; partsListEl.style.display = 'none'; partsSearch.style.display = 'none';
};
document.getElementById('tab-parts').onclick = () => {
  document.getElementById('tab-parts').classList.add('active');
  document.getElementById('tab-subs').classList.remove('active');
  treeList.style.display = 'none'; partsListEl.style.display = 'block'; partsSearch.style.display = 'block';
};

let selectedEntry = null, soloObjs = null;
function clearSelection() {
  if (selectedEntry) { for (const o of selectedEntry.objs) highlight(o, false); selectedEntry = null; }
  if (selected) { highlight(selected, false); selected = null; }
  if (soloObjs) { soloObjs = null; setXray(robot, false); xray = false; syncBtn(); }
  partRows.forEach(p => p.row.classList.remove('active'));
}
function selectEntry(e, focusCam = true) {
  const keepSolo = soloObjs; // clearSelection() drops solo — re-apply to the new entry below
  clearSelection();
  selectedEntry = e;
  for (const o of e.objs) highlight(o, true);
  partRows.forEach(p => p.row.classList.toggle('active', p.e === e));
  if (keepSolo) { soloObjs = e.objs; setXray(robot, true, e.objs); xray = 'partial'; }
  showEntryInfo(e);
  if (focusCam && e.objs.length) {
    const box = new THREE.Box3().setFromObject(e.objs[0]);
    for (const o of e.objs.slice(1)) box.union(new THREE.Box3().setFromObject(o));
    const c = box.getCenter(new THREE.Vector3());
    const size = Math.max(5, box.getSize(new THREE.Vector3()).length());
    controls.target.copy(c);
    const dir = camera.position.clone().sub(c).normalize();
    camera.position.copy(c).addScaledVector(dir, size * 1.1 + 4);
  }
}
function showEntryInfo(e) {
  const idx = entries.indexOf(e);
  const eb = new THREE.Box3().setFromObject(e.objs[0]);
  for (const o of e.objs.slice(1)) eb.union(new THREE.Box3().setFromObject(o));
  const esz = eb.getSize(new THREE.Vector3());
  infoBody.innerHTML = `<h2>${e.name}</h2>
    <div class="sub-label">${SUBS[e.sub].label} · part ${idx + 1} of ${entries.length}</div>
    <div class="spec-row"><span class="k">Spec / material</span><span class="v">${e.spec}</span></div>
    <div class="spec-row"><span class="k">Qty on robot</span><span class="v">×${e.qty}</span></div>
    <div class="spec-row"><span class="k">Placed instances</span><span class="v">${e.objs.length}</span></div>
    <div class="spec-row"><span class="k">Bounding size</span><span class="v">${esz.x.toFixed(1)} × ${esz.y.toFixed(1)} × ${esz.z.toFixed(1)} in</span></div>
    ${e.notes ? `<div class="notes">${e.notes}</div>` : ''}
    ${e.links && e.links.length ? `<div class="rel-title">Connected parts — click to jump</div><div class="rel-chips">` +
      e.links.map((l, i) => `<div class="rel-chip" data-l="${i}"><span class="rs">${SUBS[l.sub].label}</span>${l.name}</div>`).join('') + `</div>` : ''}
    <div class="part-nav"><button id="pn-prev">◂ Prev part</button><button id="pn-next">Next part ▸</button>
      <button id="pn-solo">${soloObjs ? '◉ Show all' : '◎ Isolate'}</button></div>
    <div class="hint">All placed instances highlighted · Isolate ghosts everything else</div>`;
  infoBody.querySelectorAll('.rel-chip').forEach(ch => {
    ch.onclick = () => selectEntry(e.links[+ch.dataset.l], true);
  });
  infoBody.querySelector('#pn-prev').onclick = () =>
    selectEntry(entries[(idx - 1 + entries.length) % entries.length], true);
  infoBody.querySelector('#pn-next').onclick = () =>
    selectEntry(entries[(idx + 1) % entries.length], true);
  infoBody.querySelector('#pn-solo').onclick = () => {
    if (soloObjs) { soloObjs = null; setXray(robot, false); xray = false; }
    else {
      soloObjs = e.objs; setXray(robot, true, e.objs); xray = 'partial';
      // part solo supersedes subsystem isolation — mirror of isolate() dropping soloObjs
      isolated = null;
      document.querySelectorAll('.sub-item').forEach(r => r.classList.remove('active'));
    }
    syncBtn();
    showEntryInfo(e);
  };
}

/* ---------- info panel ---------- */
const infoBody = document.getElementById('info-body');
function showSubInfo(id) {
  const s = SUBS[id];
  const list = entries.filter(e => e.sub === id);
  infoBody.innerHTML = `<h2>${s.label}</h2><div class="sub-label">subsystem · ${list.length} BOM lines</div>
    <div class="notes">${s.desc}</div>
    <div class="panel-title" style="padding:12px 0 4px">Parts</div>` +
    list.map(e => `<div class="spec-row"><span class="k">${e.name}</span><span class="v">×${e.qty}</span></div>`).join('');
}

function showDefaultInfo() {
  infoBody.innerHTML = `<h2>Robot Overview</h2><div class="sub-label">BIOBUZZ 2026-27 · concept v1</div>
    <div class="spec-row"><span class="k">Footprint</span><span class="v">17.5 × 17.5 in</span></div>
    <div class="spec-row"><span class="k">Height</span><span class="v">${dims.h} in</span></div>
    <div class="spec-row"><span class="k">Motors / servos</span><span class="v">${counts.motors} / ${counts.servos}</span></div>
    <div class="spec-row"><span class="k">BOM lines</span><span class="v">${entries.length}</span></div>
    <div class="notes">Strategy: starts inside the 18" cube; the deposit lift is the only expansion (≤29" R105 cap, footprint stays 18×18). Over/under intake vacuums POLLEN and NECTAR → inclined hopper → feed column through the turret axis → dual flywheel launcher lobs into the HIVE cell. For FLOWERS, a Y-flap at the column top diverts a NECTAR into the 2-stage lift cradle, which rises ~14.6" and tips it into the ~4" mouth — no lob needed.</div>`;
}

/* ---------- compliance ---------- */
document.getElementById('compliance-body').innerHTML = [
  ['R101 · 18" cube start', '17.5×17.5×13.3 ✓'],
  ['R105 · horizontal', '18×18 footprint ✓'],
  ['R105 · vertical cap', 'lift tops ~26" < 29" ✓'],
  ['Motors (max 8)', '8 — at cap'],
  ['Servos (max 8)', '7 ✓'],
  ['Odometry', '3-pod + IMU'],
].map(([k, v]) => `<div class="badge-row"><span class="k">${k}</span><span class="${v.includes('cap') ? 'warn' : 'ok'}">${v}</span></div>`).join('');

/* ---------- picking ---------- */
let downPos = null;
renderer.domElement.addEventListener('pointerdown', e => { downPos = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (!downPos) return;
  const d = Math.hypot(e.clientX - downPos[0], e.clientY - downPos[1]);
  downPos = null;
  if (d > 5) return;
  pick(e);
});
renderer.domElement.addEventListener('dblclick', e => {
  const hit = raycastAt(e);
  if (hit) {
    const box = new THREE.Box3().setFromObject(hit);
    const c = box.getCenter(new THREE.Vector3());
    const size = Math.max(6, box.getSize(new THREE.Vector3()).length());
    controls.target.copy(c);
    const dir = camera.position.clone().sub(c).normalize();
    camera.position.copy(c).addScaledVector(dir, size * 1.6);
  }
});
renderer.domElement.addEventListener('pointermove', e => {
  const hit = raycastAt(e);
  if (hit && hit.userData.entry) {
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top = (e.clientY + 10) + 'px';
    tooltip.textContent = hit.userData.entry.name;
    renderer.domElement.style.cursor = 'pointer';
  } else {
    tooltip.style.display = 'none';
    renderer.domElement.style.cursor = '';
  }
});

function raycastAt(e) {
  mouse.x = (e.clientX / innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / innerHeight) * 2 + 1;
  ray.setFromCamera(mouse, camera);
  const hits = ray.intersectObjects(robot.children, true);
  for (const h of hits) {
    let o = h.object;
    while (o && !o.userData.entry) o = o.parent;
    if (!o) continue; // no entry on this hit — keep testing deeper hits
    // skip hits inside hidden groups, keep testing deeper hits
    let vis = o, hidden = false;
    while (vis) { if (vis.visible === false) { hidden = true; break; } vis = vis.parent; }
    if (!hidden) return o;
  }
  return null;
}

function pick(e) {
  const hit = raycastAt(e);
  if (hit) {
    selectEntry(hit.userData.entry, false);
  } else {
    clearSelection();
    if (!isolated) showDefaultInfo();
  }
}

/* ---------- toolbar ---------- */
const $ = id => document.getElementById(id);
$('explode').oninput = e => { explodeTarget = e.target.value / 100; };
$('btn-anim').onclick = () => {
  if (demo.active) return;
  animating = !animating;
  if (shot) shotAnimWas = animating; // a mid-shot toggle wins over the restore on completion
  syncBtn();
};
$('btn-xray').onclick = () => {
  if (xray === true) { xray = false; setXray(robot, false); }
  else {
    xray = true; isolated = null; soloObjs = null;
    document.querySelectorAll('.sub-item').forEach(r => r.classList.remove('active'));
    setXray(robot, true);
  }
  syncBtn();
};
$('btn-labels').onclick = () => { const on = !labels[0].visible; labels.forEach(l => l.visible = on); syncBtn(); };
$('btn-cube').onclick = () => { cube.visible = !cube.visible; syncBtn(); };
$('btn-field').onclick = () => {
  if (demo.active) return; // field must stay put while the match demo drives it
  fieldOn = !fieldOn;
  field.visible = fieldOn;
  grid.visible = !fieldOn;
  robot.position.set(fieldOn ? 30 : 0, 0, fieldOn ? 50 : 0);
  if (fieldOn) { camera.position.set(78, 60, 128); controls.target.set(0, 10, 14); controls.maxDistance = 400; }
  else { camera.position.set(23, 16, -26); controls.target.set(0, 6, 0); controls.maxDistance = 220; }
  syncBtn();
};
$('btn-rot').onclick = () => { controls.autoRotate = !controls.autoRotate; controls.autoRotateSpeed = 1.6; syncBtn(); };
$('cam-preset').onchange = e => {
  const p = e.target.value;
  const views = {
    iso: [[23, 16, -26], [0, 6, 0]], front: [[0, 9, -34], [0, 6, 0]],
    side: [[34, 9, 0], [0, 6, 0]], top: [[0.01, 44, 0.01], [0, 0, 0]],
    intake: [[0, 4.5, -20], [0, 3.4, -6]], turret: [[11, 15.5, 12], [0, 11.2, 2.6]],
  };
  if (views[p]) { camera.position.set(...views[p][0]); controls.target.set(...views[p][1]); }
};
$('btn-launch').onclick = launchDemo;
$('btn-lift').onclick = () => { if (demo.active) return; liftTarget = liftTarget > 0.5 ? 0 : 1; syncBtn(); };
$('btn-demo').onclick = () => { demo.active ? demo.stop() : demo.start(); syncBtn(); };

function syncBtn() {
  $('btn-anim').classList.toggle('on', animating);
  $('btn-demo').classList.toggle('on', demo.active);
  $('btn-lift').classList.toggle('on', liftTarget > 0.5);
  $('btn-xray').classList.toggle('on', !!xray);
  $('btn-labels').classList.toggle('on', labels[0] && labels[0].visible);
  $('btn-cube').classList.toggle('on', cube.visible);
  $('btn-field').classList.toggle('on', fieldOn);
  $('btn-rot').classList.toggle('on', controls.autoRotate);
}

/* ---------- launch demo ---------- */
let shot = null, shotAnimWas = false;
function launchDemo() {
  if (shot || demo.active) return;
  shotAnimWas = animating;
  animating = true; syncBtn();
  const ball = anim.launch.ball;
  const start = new THREE.Vector3();
  anim.turret.getWorldPosition(start); start.y = 11.9;
  const target = fieldOn ? refs.upCellBlue.clone().add(new THREE.Vector3(0, 3.4, 0))
                         : robot.localToWorld(new THREE.Vector3(0, 4, -30));
  // yaw turret toward target — the launcher exits local -Z (hood lip side)
  const dx = target.x - start.x, dz = target.z - start.z;
  const yaw = Math.atan2(-dx, -dz);
  const mid = start.clone().lerp(target, 0.5); mid.y = Math.max(start.y, target.y) + (fieldOn ? 9 : 5);
  const curve = new THREE.QuadraticBezierCurve3(start, mid, target);
  shot = { t: 0, curve, ball, yaw1: yaw };
  ball.visible = true;
}

/* ---------- animation loop ---------- */
const clock = new THREE.Clock();
const _up = new THREE.Vector3(0, 1, 0), _ra = new THREE.Vector3(), _rb = new THREE.Vector3();
function setRope(m, ax, ay, az, bx, by, bz) {
  _ra.set(ax, ay, az); _rb.set(bx, by, bz);
  m.position.copy(_ra).lerp(_rb, 0.5);
  m.scale.set(1, Math.max(0.01, _ra.distanceTo(_rb)), 1);
  m.quaternion.setFromUnitVectors(_up, _rb.sub(_ra).normalize());
}
function tick() {
  requestAnimationFrame(tick);
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;

  // explode lerp
  explodeT += (explodeTarget - explodeT) * Math.min(1, dt * 7);
  for (const id in groups) {
    const g = groups[id];
    g.position.copy(g.userData.basePos).addScaledVector(SUBS[id].explode, explodeT);
  }

  // deposit lift — 2-stage cascade, cradle tips at full extension, ball drops
  liftT += (liftTarget - liftT) * Math.min(1, dt * 2.2);
  {
    const L = anim.lift;
    L.s1.position.y = 7.3 * liftT;
    L.s2.position.y = 7.3 * liftT;
    const tip = THREE.MathUtils.smoothstep(liftT, 0.96, 1.0);
    L.cradle.rotation.x = -0.1 - tip * 1.15;
    setRope(L.rope1, -7.0, 12.75, 7.05, -7.0, 3.3 + 7.3 * liftT, 7.05);
    setRope(L.rope2, -7.0, 11.9 + 7.3 * liftT, 7.05, -7.0, 3.5 + 14.6 * liftT, 7.05);
    const lb = L.ball;
    if (tip > 0.9 && L.ballState === 'cup') {
      const w = lb.getWorldPosition(new THREE.Vector3());
      robot.add(lb);
      lb.position.copy(robot.worldToLocal(w));
      lb.userData.vy = 0.6;
      L.ballState = 'fall';
      if (L.dropHook) L.dropHook(lb); // demo mode can steer the pour into the flower
    }
    if (L.guided) {
      L.guided.t += dt / 0.55;
      const k = Math.min(1, L.guided.t);
      lb.position.copy(robot.worldToLocal(L.guided.curve.getPoint(k)));
      lb.rotation.x += 3 * dt;
      if (k >= 1) { lb.visible = false; L.guided = null; L.ballState = 'scored'; }
    } else if (L.ballState === 'fall') {
      lb.userData.vy += 300 * dt;
      lb.position.y -= lb.userData.vy * dt;
      lb.position.z -= 1.1 * dt;
      const floor = 1.85; // ball r 1.8 + clearance — tiles and ground plane both sit at y≈0
      if (lb.position.y <= floor) { lb.position.y = floor; L.ballState = 'down'; }
    }
    if (L.ballState === 'down' && liftTarget === 0 && liftT < 0.04) {
      L.cradle.add(lb);
      lb.position.set(0.1, 1.08, 0);
      lb.visible = true;
      lb.userData.vy = 0;
      L.ballState = 'cup';
    }
  }

  if (animating) {
    // demo mode gates each subsystem's motion per-phase; manual animate runs all
    const gates = demo.active ? (anim.gates || {}) : { intake: true, feed: true, fly: true, agit: true };
    if (gates.intake) for (const s of anim.intake) s.obj.rotation.x += s.speed * dt;
    if (gates.feed) for (const s of anim.feed) s.obj.rotation.y += s.speed * dt;
    if (gates.fly) for (const f of anim.fly) f.obj.rotation.y += f.speed * dt;
    if (!shot && !demo.active) anim.turret.rotation.y = Math.sin(t * 0.5) * 0.85;
    if (anim.agitator && gates.agit) anim.agitator.rotation.x += Math.sin(t * 3.1) * 2.4 * dt;
    if (anim.hood) anim.hood.rotation.x = -0.9 + Math.sin(t * 0.8) * 0.12;
  }

  // hive bi-stable tilt runs unconditionally so a started tip always finishes,
  // even if the demo or the Animate toggle is cut mid-motion
  for (const h of refs.hives) {
    const rest = 0.12 + Math.sin(t * 0.35 + (h.name === 'red' ? 0 : 1.4)) * 0.05;
    const dt2 = h.pivot.userData.tipT ? t - h.pivot.userData.tipT : 1e9;
    if (dt2 < 4) {
      // ease into the tip over 0.5s, hold ~2s, ease back over 1.4s
      const inK = Math.min(1, dt2 / 0.5);
      const hold = Math.min(1, Math.max(0, (dt2 - 2.4) / 1.4));
      const tipped = -0.55;
      h.pivot.rotation.x = rest + (tipped - rest) * (inK * (1 - hold));
    } else {
      h.pivot.rotation.x = rest;
    }
  }

  if (shot) {
    // slew turret first — wrap the error so it takes the short way around
    let dyaw = Math.atan2(Math.sin(shot.yaw1 - anim.turret.rotation.y),
                          Math.cos(shot.yaw1 - anim.turret.rotation.y));
    anim.turret.rotation.y += dyaw * Math.min(1, dt * 6);
    if (Math.abs(dyaw) < 0.02 || shot.t > 0) {
      shot.t += dt / (fieldOn ? 1.5 : 1.0);
      const k = Math.min(shot.t, 1);
      shot.ball.position.copy(robot.worldToLocal(shot.curve.getPoint(k)));
      shot.ball.rotation.x += 8 * dt;
      if (k >= 1) {
        if (fieldOn) {
          refs.hives[1].pivot.userData.tipT = t; // tip the blue hive
        }
        const s = shot; shot = null;
        s.ball.visible = false;
        s.ball.position.y = -100;
        animating = shotAnimWas; syncBtn();
      }
    }
  }

  if (demo.active) demo.update(dt, t);

  // shadow bake only while something actually moves (field hives wobble constantly)
  if (animating || demo.active || shot || fieldOn
      || Math.abs(explodeTarget - explodeT) > 1e-4
      || Math.abs(liftTarget - liftT) > 1e-4) {
    renderer.shadowMap.needsUpdate = true;
  }

  controls.update();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  labelRenderer.setSize(innerWidth, innerHeight);
});

showDefaultInfo();
// console/debug handle — window.__bio
window.__bio = { scene, robot, groups, entries, anim, refs, demo, selectEntry, renderer };
document.getElementById('loading').style.opacity = '0';
setTimeout(() => document.getElementById('loading').remove(), 600);
tick();
