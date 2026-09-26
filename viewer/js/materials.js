// materials.js — shared PBR material set (goBILDA / REV Robotics inspired)
import * as THREE from 'three';

// ---------- procedural canvas textures ----------
export function canvasTex(w, h, draw, { srgb = true } = {}) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

// deterministic pseudo-random — same pattern every load
function rng(seed) { let s = seed; return () => (s = (s * 16807) % 2147483647) / 2147483647; }

// 36h11-style fiducial: white field, black border, inner data grid
export function aprilTagTex(seed = 7) {
  return canvasTex(160, 160, (g) => {
    g.fillStyle = '#f2f2ee'; g.fillRect(0, 0, 160, 160);
    g.fillStyle = '#101010'; g.fillRect(16, 16, 128, 128);
    g.fillStyle = '#f2f2ee'; g.fillRect(30, 30, 100, 100);
    const n = 8, cell = 100 / n, r = rng(seed * 7919 + 13);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      if (r() > 0.5) { g.fillStyle = '#101010'; g.fillRect(30 + i * cell, 30 + j * cell, cell, cell); }
    }
  });
}

// FTC alliance number plate — vinyl digits on colored field
export function numberPlateTex(num = '27475', hue = '#1b3fa0') {
  return canvasTex(360, 240, (g) => {
    g.fillStyle = hue; g.fillRect(0, 0, 360, 240);
    g.strokeStyle = '#ffffff'; g.lineWidth = 10; g.strokeRect(10, 10, 340, 220);
    g.fillStyle = '#ffffff';
    g.font = '900 150px "Arial Black", Arial, sans-serif';
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(num, 180, 128);
  });
}

// closed-cell foam tile: subtle mottling + waffle grid dimples
export function tileTex(light) {
  return canvasTex(256, 256, (g) => {
    g.fillStyle = light ? '#626c76' : '#59636d'; g.fillRect(0, 0, 256, 256);
    const r = rng(light ? 31 : 47);
    for (let i = 0; i < 900; i++) {
      g.fillStyle = `rgba(${r() > 0.5 ? '255,255,255' : '0,0,0'},${0.03 + r() * 0.05})`;
      g.fillRect(r() * 256, r() * 256, 2 + r() * 4, 2 + r() * 4);
    }
    // waffle dimple grid
    const n = 8, cell = 256 / n;
    for (let i = 0; i <= n; i++) for (let j = 0; j <= n; j++) {
      const x = i * cell, y = j * cell;
      g.fillStyle = 'rgba(0,0,0,0.16)';
      g.beginPath(); g.arc(x, y, 5, 0, Math.PI * 2); g.fill();
      g.fillStyle = 'rgba(255,255,255,0.07)';
      g.beginPath(); g.arc(x - 1.2, y - 1.2, 3, 0, Math.PI * 2); g.fill();
    }
    // interlock seam shadows at edges
    g.strokeStyle = 'rgba(0,0,0,0.25)'; g.lineWidth = 3;
    g.strokeRect(0, 0, 256, 256);
  });
}

// motor wrap label
export function motorLabelTex() {
  return canvasTex(256, 64, (g) => {
    g.fillStyle = '#3a3e44'; g.fillRect(0, 0, 256, 64);
    g.fillStyle = '#c9ced6'; g.font = '700 26px Arial';
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('5203 · 12V DC', 128, 24);
    g.font = '400 16px Arial'; g.fillStyle = '#8b929c';
    g.fillText('YELLOW JACKET', 128, 48);
  });
}

// hub faceplate label
export function hubLabelTex() {
  return canvasTex(256, 96, (g) => {
    g.fillStyle = '#22252b'; g.fillRect(0, 0, 256, 96);
    g.fillStyle = '#e8b10c'; g.fillRect(0, 0, 256, 8);
    g.fillStyle = '#dfe3ea'; g.font = '700 24px Arial';
    g.textAlign = 'center';
    g.fillText('CONTROL HUB', 128, 40);
    g.font = '400 14px Arial'; g.fillStyle = '#8b93a3';
    g.fillText('M0  M1  M2  M3', 128, 66);
  });
}

// soft round contact-shadow blob
export function blobShadowTex() {
  return canvasTex(128, 128, (g) => {
    const grad = g.createRadialGradient(64, 64, 8, 64, 64, 62);
    grad.addColorStop(0, 'rgba(0,0,0,0.55)');
    grad.addColorStop(0.7, 'rgba(0,0,0,0.28)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = grad; g.fillRect(0, 0, 128, 128);
  });
}

// gaffers tape — slight sheen + edge fibers
export function tapeTex(col = '#e8e6da') {
  return canvasTex(64, 64, (g) => {
    g.fillStyle = col; g.fillRect(0, 0, 64, 64);
    const r = rng(99);
    for (let i = 0; i < 60; i++) {
      g.strokeStyle = `rgba(0,0,0,${0.02 + r() * 0.05})`;
      const y = r() * 64;
      g.beginPath(); g.moveTo(0, y); g.lineTo(64, y + (r() - 0.5) * 8); g.stroke();
    }
  });
}

const tileMapA = tileTex(true), tileMapB = tileTex(false);

export const M = {
  // Frame — dark anodized aluminum channel
  channel: new THREE.MeshStandardMaterial({ color: 0x35393f, metalness: 0.85, roughness: 0.42 }),
  // Accent anodized (team gold — bee theme)
  accent: new THREE.MeshStandardMaterial({ color: 0xd9a406, metalness: 0.75, roughness: 0.38 }),
  // Machined aluminum (mounts, blocks)
  alu: new THREE.MeshStandardMaterial({ color: 0xb8bdc4, metalness: 0.9, roughness: 0.32 }),
  // Steel (shafts, bolts)
  steel: new THREE.MeshStandardMaterial({ color: 0x9aa1a8, metalness: 1.0, roughness: 0.28 }),
  darkSteel: new THREE.MeshStandardMaterial({ color: 0x4a4e54, metalness: 0.95, roughness: 0.4 }),
  bolt: new THREE.MeshStandardMaterial({ color: 0x2c2f33, metalness: 0.9, roughness: 0.45 }),
  // Channel hole interiors — near-black
  holeDark: new THREE.MeshStandardMaterial({ color: 0x0a0b0d, metalness: 0.2, roughness: 0.9 }),
  // Wheel rubber
  rubber: new THREE.MeshStandardMaterial({ color: 0x15161a, metalness: 0.0, roughness: 0.95 }),
  // Mecanum roller rubber (slightly lighter)
  roller: new THREE.MeshStandardMaterial({ color: 0x23262c, metalness: 0.0, roughness: 0.9 }),
  // Compliant intake stars — translucent flex blue
  starFlex: new THREE.MeshPhysicalMaterial({ color: 0x2f7fd6, metalness: 0.05, roughness: 0.55, clearcoat: 0.3 }),
  // Compliant green feed wheel
  flexGreen: new THREE.MeshPhysicalMaterial({ color: 0x37b34a, metalness: 0.05, roughness: 0.5, clearcoat: 0.4 }),
  // PETG printed parts — yellow
  print: new THREE.MeshStandardMaterial({ color: 0xe8b10c, metalness: 0.05, roughness: 0.6 }),
  printGray: new THREE.MeshStandardMaterial({ color: 0x8b9096, metalness: 0.05, roughness: 0.65 }),
  // Polycarbonate sheets — smoked clear. Cheap transparency (not transmission):
  // a transmissive material would force a second full scene render per frame.
  polycarb: new THREE.MeshPhysicalMaterial({
    color: 0x8fa4b8, metalness: 0.0, roughness: 0.15, transparent: true, opacity: 0.3,
    clearcoat: 0.6, side: THREE.DoubleSide, depthWrite: false,
  }),
  polycarbSolid: new THREE.MeshPhysicalMaterial({
    color: 0x39434f, metalness: 0.1, roughness: 0.35, transparent: true, opacity: 0.55, side: THREE.DoubleSide,
  }),
  // Clear tube (feed column)
  tube: new THREE.MeshPhysicalMaterial({
    color: 0xcfe4f0, metalness: 0.0, roughness: 0.06, transparent: true, opacity: 0.2,
    clearcoat: 0.8, side: THREE.DoubleSide, depthWrite: false,
  }),
  // Motor housing — zinc plated
  motorBody: new THREE.MeshStandardMaterial({ color: 0x707880, metalness: 0.9, roughness: 0.35 }),
  motorEnd: new THREE.MeshStandardMaterial({ color: 0x30343a, metalness: 0.7, roughness: 0.5 }),
  // Gearbox gold (UltraPlanetary face)
  gearbox: new THREE.MeshStandardMaterial({ color: 0xc7a34a, metalness: 0.85, roughness: 0.35 }),
  // Electronics
  pcb: new THREE.MeshStandardMaterial({ color: 0x1d3a26, metalness: 0.2, roughness: 0.7 }),
  hubCase: new THREE.MeshStandardMaterial({ color: 0x1e2126, metalness: 0.3, roughness: 0.55 }),
  portOrange: new THREE.MeshStandardMaterial({ color: 0xd97c1e, metalness: 0.2, roughness: 0.5 }),
  portWhite: new THREE.MeshStandardMaterial({ color: 0xd8d8d8, metalness: 0.1, roughness: 0.5 }),
  portYellow: new THREE.MeshStandardMaterial({ color: 0xd8b820, metalness: 0.15, roughness: 0.5 }),
  battery: new THREE.MeshStandardMaterial({ color: 0x2e5aa8, metalness: 0.2, roughness: 0.5 }),
  // Wires
  wireRed: new THREE.MeshStandardMaterial({ color: 0xb02020, roughness: 0.7 }),
  wireBlack: new THREE.MeshStandardMaterial({ color: 0x111214, roughness: 0.8 }),
  wireOrange: new THREE.MeshStandardMaterial({ color: 0xc86018, roughness: 0.7 }),
  wireYellow: new THREE.MeshStandardMaterial({ color: 0xc9a700, roughness: 0.7 }),
  // Scoring elements
  pollen: new THREE.MeshPhysicalMaterial({ color: 0xf5c518, metalness: 0.05, roughness: 0.42, clearcoat: 0.35 }),
  nectarRed: new THREE.MeshPhysicalMaterial({ color: 0xc62b2b, metalness: 0.1, roughness: 0.32, clearcoat: 0.6 }),
  nectarBlue: new THREE.MeshPhysicalMaterial({ color: 0x2255c8, metalness: 0.1, roughness: 0.32, clearcoat: 0.6 }),
  // Field
  tile: new THREE.MeshStandardMaterial({ map: tileMapA, color: 0xffffff, metalness: 0.0, roughness: 0.94, bumpMap: tileMapA, bumpScale: 0.5 }),
  tileAlt: new THREE.MeshStandardMaterial({ map: tileMapB, color: 0xffffff, metalness: 0.0, roughness: 0.94, bumpMap: tileMapB, bumpScale: 0.5 }),
  wallAlu: new THREE.MeshStandardMaterial({ color: 0x7d848c, metalness: 0.85, roughness: 0.4 }),
  wallPanel: new THREE.MeshPhysicalMaterial({
    color: 0xaab6c4, metalness: 0.0, roughness: 0.1, transparent: true, opacity: 0.3,
    clearcoat: 0.5, side: THREE.DoubleSide, depthWrite: false,
  }),
  hiveFrame: new THREE.MeshStandardMaterial({ color: 0x3a3f45, metalness: 0.8, roughness: 0.5 }),
  hiveRed: new THREE.MeshStandardMaterial({ color: 0xb03030, metalness: 0.2, roughness: 0.5 }),
  hiveBlue: new THREE.MeshStandardMaterial({ color: 0x2b4ec8, metalness: 0.2, roughness: 0.5 }),
  hiveScreen: new THREE.MeshStandardMaterial({ color: 0x22262b, metalness: 0.3, roughness: 0.8 }),
  flowerPipe: new THREE.MeshStandardMaterial({ color: 0x6fbf5f, metalness: 0.1, roughness: 0.5 }),
  flowerRing: new THREE.MeshStandardMaterial({ color: 0xe07ab8, metalness: 0.1, roughness: 0.55 }),
  flowerLeaf: new THREE.MeshStandardMaterial({ color: 0x4f9c42, metalness: 0.0, roughness: 0.7, side: THREE.DoubleSide }),
  tapeWhite: new THREE.MeshStandardMaterial({ map: tapeTex(), color: 0xffffff, roughness: 0.85 }),
  tapeRed: new THREE.MeshStandardMaterial({ map: tapeTex('#c25450'), color: 0xffffff, roughness: 0.85 }),
  tapeBlue: new THREE.MeshStandardMaterial({ map: tapeTex('#4a68c8'), color: 0xffffff, roughness: 0.85 }),
  aprilTag: new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: 0.85 }),
  // LEDs / emissives
  ledGreen: new THREE.MeshStandardMaterial({ color: 0x12331a, emissive: 0x2aff66, emissiveIntensity: 1.4 }),
  ledOrange: new THREE.MeshStandardMaterial({ color: 0x3a2408, emissive: 0xff9a1f, emissiveIntensity: 1.2 }),
  ledBlue: new THREE.MeshStandardMaterial({ color: 0x0c1e3a, emissive: 0x3f8cff, emissiveIntensity: 1.2 }),
  lensGlass: new THREE.MeshPhysicalMaterial({ color: 0x18243c, metalness: 0.2, roughness: 0.05, clearcoat: 1.0 }),
  // Contact shadow blob under the robot
  blobShadow: new THREE.MeshBasicMaterial({ map: blobShadowTex(), transparent: true, depthWrite: false }),
  // Ghost / sizing cube
  cubeGhost: new THREE.MeshBasicMaterial({ color: 0xffd23f, transparent: true, opacity: 0.08, depthWrite: false, side: THREE.DoubleSide }),
  cubeEdge: new THREE.LineBasicMaterial({ color: 0xffd23f }),
};

// Highlight helpers — clone-on-select so shared materials don't all light up.
// Each mesh's real material is cached once in userData.xraySaved; while a part
// is selected, _saved holds that same base material and userData.hlMat holds the
// installed emissive clone — so restores in any order never resurrect a clone.
const _saved = new Map();
export function highlight(obj, on) {
  obj.traverse(m => {
    if (!m.isMesh) return;
    if (on) {
      if (!_saved.has(m)) _saved.set(m, m.userData.xraySaved || m.material);
      if (m.userData.hlMat) m.userData.hlMat.dispose();
      const c = _saved.get(m).clone();
      if ('emissive' in c) { c.emissive = new THREE.Color(0xffd23f); c.emissiveIntensity = 0.35; }
      c.transparent = false; c.opacity = 1.0; c.depthWrite = true;
      m.userData.hlMat = c;
      m.material = c;
    } else if (_saved.has(m)) {
      if (m.userData.hlMat) { m.userData.hlMat.dispose(); delete m.userData.hlMat; }
      m.material = m.userData.xrayOn ? m.userData.xrayMat : _saved.get(m);
      _saved.delete(m);
    }
  });
}

// X-ray ghosting: swap every mesh to a transparent material, keep the selected
// subsystem (or list of part objects) opaque
export function setXray(root, on, keepOpaque = null) {
  const keeps = keepOpaque ? (Array.isArray(keepOpaque) ? keepOpaque : [keepOpaque]) : null;
  root.traverse(m => {
    if (!m.isMesh || m.userData.noXray) return;
    if (!m.userData.xraySaved) m.userData.xraySaved = _saved.get(m) || m.material;
    const keep = keeps && keeps.some(k => m === k || k.getObjectById(m.id));
    const ghost = on && !keep;
    m.userData.xrayOn = ghost;
    if (ghost) {
      if (!m.userData.xrayMat) {
        const c = (m.userData.xraySaved.color ? m.userData.xraySaved.color.clone() : new THREE.Color(0x8899aa));
        m.userData.xrayMat = new THREE.MeshPhysicalMaterial({
          color: c.lerp(new THREE.Color(0x88aacc), 0.55), transparent: true, opacity: 0.16,
          metalness: 0.1, roughness: 0.4, depthWrite: false, side: THREE.DoubleSide,
        });
      }
      m.material = m.userData.xrayMat;
    } else {
      m.material = m.userData.hlMat || m.userData.xraySaved;
    }
  });
}
