// parts.js — parametric FTC part library (dimensions in inches, Y-up world)
import * as THREE from 'three';
import { M, numberPlateTex, aprilTagTex, motorLabelTex, hubLabelTex } from './materials.js';

function shadowify(o) {
  o.traverse(m => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  return o;
}
const G = (geo, mat) => shadowify(new THREE.Mesh(geo, mat));

// ---------- structural ----------

// goBILDA-style U-channel, extruded along Z, open face down-X by default.
// size = section width/height (1.89"), t = wall thickness
export function channel(len, mat = M.channel, withHoles = true) {
  const s = 1.89, t = 0.09;
  const g = new THREE.Group();
  // U profile extruded along Z: outer box minus inner cavity -> outline with hole
  const outer = new THREE.Shape();
  outer.moveTo(-s / 2, -s / 2); outer.lineTo(s / 2, -s / 2); outer.lineTo(s / 2, s / 2); outer.lineTo(-s / 2, s / 2); outer.closePath();
  const cavity = new THREE.Path();
  cavity.moveTo(-s / 2 + t, -s / 2 - 0.01); cavity.lineTo(s / 2 - t, -s / 2 - 0.01);
  cavity.lineTo(s / 2 - t, s / 2 - t); cavity.lineTo(-s / 2 + t, s / 2 - t); cavity.closePath();
  outer.holes.push(cavity);
  const geo = new THREE.ExtrudeGeometry(outer, { depth: len, bevelEnabled: false });
  geo.translate(0, 0, -len / 2);
  g.add(G(geo, mat));
  if (withHoles) {
    // 8mm grid holes — dark discs flush with each outer face
    const step = 0.315, r = 0.085;
    const n = Math.floor(len / step) - 1;
    const hole = new THREE.CylinderGeometry(r, r, 0.03, 12);
    hole.rotateZ(Math.PI / 2); // axis -> X
    const inst = new THREE.InstancedMesh(hole, M.holeDark, n * 2);
    const m4 = new THREE.Matrix4();
    let i = 0;
    for (let k = 0; k < n; k++) {
      const z = -len / 2 + (k + 1) * (len / (n + 1));
      for (const x of [s / 2 - 0.01, -s / 2 + 0.01]) {
        m4.makeTranslation(x, 0, z);
        inst.setMatrixAt(i++, m4);
      }
    }
    inst.count = i;
    g.add(inst);
    // top face hole strip (open face is -Y, no material there)
    const topHole = new THREE.CylinderGeometry(r, r, 0.03, 12);
    const inst2 = new THREE.InstancedMesh(topHole, M.holeDark, n);
    let j = 0;
    for (let k = 0; k < n; k++) {
      const z = -len / 2 + (k + 1) * (len / (n + 1));
      m4.makeTranslation(0, s / 2 - 0.01, z);
      inst2.setMatrixAt(j++, m4);
    }
    inst2.count = j;
    g.add(inst2);
  }
  return g;
}

export function plate(w, h, t = 0.09, mat = M.alu) {
  return G(new THREE.BoxGeometry(w, t, h), mat);
}
export function plateV(w, h, t = 0.09, mat = M.alu) { // vertical plate, w along X, h along Y
  return G(new THREE.BoxGeometry(w, h, t), mat);
}

export function gusset(w = 1.5, h = 1.5, t = 0.08, mat = M.accent) {
  const s = new THREE.Shape();
  s.moveTo(0, 0); s.lineTo(w, 0); s.lineTo(0, h); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false });
  geo.translate(0, 0, -t / 2);
  return G(geo, mat);
}

export function standoff(len = 1, mat = M.alu) {
  return G(new THREE.CylinderGeometry(0.12, 0.12, len, 6).rotateX(Math.PI / 2), mat);
}

// ---------- fasteners & shafting ----------

export function bolt(len = 0.35) {
  const g = new THREE.Group();
  const shaft = G(new THREE.CylinderGeometry(0.055, 0.055, len, 10), M.bolt);
  const head = G(new THREE.CylinderGeometry(0.095, 0.095, 0.09, 10), M.bolt);
  head.position.y = len / 2 + 0.04;
  const socket = G(new THREE.CylinderGeometry(0.045, 0.045, 0.02, 6), M.holeDark);
  socket.position.y = len / 2 + 0.09;
  g.add(shaft, head, socket);
  return g;
}

export function hexShaft(len) { // 8mm REX — hex profile
  return G(new THREE.CylinderGeometry(0.157, 0.157, len, 6).rotateZ(Math.PI / 2), M.steel);
}

export function bearing() {
  const g = new THREE.Group();
  g.add(G(new THREE.CylinderGeometry(0.31, 0.31, 0.28, 20).rotateZ(Math.PI / 2), M.alu));
  const flange = G(new THREE.CylinderGeometry(0.55, 0.55, 0.06, 6).rotateZ(Math.PI / 2), M.alu);
  flange.position.x = 0.16;
  const bore = G(new THREE.CylinderGeometry(0.16, 0.16, 0.3, 12).rotateZ(Math.PI / 2), M.holeDark);
  // rubber seal ring around the bore
  const seal = G(new THREE.TorusGeometry(0.2, 0.035, 6, 18).rotateY(Math.PI / 2), M.rubber);
  seal.position.x = 0.13;
  g.add(flange, bore, seal);
  // 4 flange bolts
  const boltGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.12, 6).rotateZ(Math.PI / 2);
  const inst = new THREE.InstancedMesh(boltGeo, M.bolt, 4);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 4; i++) {
    const a = (i / 4) * Math.PI * 2 + Math.PI / 4;
    m4.makeTranslation(0.19, Math.cos(a) * 0.4, Math.sin(a) * 0.4);
    inst.setMatrixAt(i, m4);
  }
  g.add(inst);
  return g;
}

export function collar() {
  return G(new THREE.CylinderGeometry(0.22, 0.22, 0.18, 14).rotateZ(Math.PI / 2), M.darkSteel);
}

// ---------- gears ----------

// spur gear: teeth around a cylinder. Build along Y, caller rotates.
export function spurGear(teeth, pitchR, t = 0.24, mat = M.accent, hubR = 0.22) {
  const outer = pitchR + 0.09, root = pitchR - 0.07;
  const s = new THREE.Shape();
  const N = teeth;
  for (let i = 0; i < N; i++) {
    const a0 = (i / N) * Math.PI * 2, a1 = ((i + 0.35) / N) * Math.PI * 2;
    const a2 = ((i + 0.5) / N) * Math.PI * 2, a3 = ((i + 0.85) / N) * Math.PI * 2;
    if (i === 0) s.moveTo(Math.cos(a0) * root, Math.sin(a0) * root);
    s.lineTo(Math.cos(a1) * root, Math.sin(a1) * root);
    s.lineTo(Math.cos(a2) * outer, Math.sin(a2) * outer);
    s.lineTo(Math.cos(a3) * outer, Math.sin(a3) * outer);
    s.lineTo(Math.cos((i + 1) / N * Math.PI * 2) * root, Math.sin((i + 1) / N * Math.PI * 2) * root);
  }
  const hole = new THREE.Path(); hole.absarc(0, 0, hubR * 0.55, 0, Math.PI * 2, true); s.holes.push(hole);
  const geo = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false });
  geo.translate(0, 0, -t / 2);
  geo.rotateX(-Math.PI / 2); // teeth in XZ plane, axis = Y
  const g = new THREE.Group();
  g.add(G(geo, mat));
  const hub = G(new THREE.CylinderGeometry(hubR, hubR, t + 0.12, 14), mat);
  g.add(hub);
  return g;
}

// ---------- wheels ----------

// mecanum wheel, axis along X. r = radius, w = width. rollers at 45°
export function mecanumWheel(r = 1.89, w = 1.5, handed = 1) {
  const g = new THREE.Group();
  const hubR = r * 0.55;
  // hub plates
  for (const side of [-1, 1]) {
    const plateGeo = new THREE.CylinderGeometry(hubR, hubR, 0.09, 24);
    plateGeo.rotateZ(Math.PI / 2);
    const p = G(plateGeo, M.alu);
    p.position.x = side * (w / 2 - 0.06);
    g.add(p);
  }
  const core = G(new THREE.CylinderGeometry(hubR * 0.8, hubR * 0.8, w * 0.8, 18).rotateZ(Math.PI / 2), M.accent);
  g.add(core);
  // hub bolt circle on each plate face
  const hubBoltGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.12, 6).rotateZ(Math.PI / 2);
  const hb = new THREE.InstancedMesh(hubBoltGeo, M.bolt, 12);
  const m4 = new THREE.Matrix4();
  let bi = 0;
  for (const side of [-1, 1]) for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2;
    m4.makeTranslation(side * (w / 2 - 0.01), Math.cos(a) * hubR * 0.72, Math.sin(a) * hubR * 0.72);
    hb.setMatrixAt(bi++, m4);
  }
  g.add(hb);
  // rollers — one instanced draw for the whole ring
  const n = 11;
  const rollerGeo = new THREE.CapsuleGeometry(0.17, w * 0.62, 4, 10);
  const rollers = new THREE.InstancedMesh(rollerGeo, M.roller, n);
  const rq = new THREE.Quaternion(), rp = new THREE.Vector3(), rs = new THREE.Vector3(1, 1, 1);
  for (let i = 0; i < n; i++) {
    const th = (i / n) * Math.PI * 2;
    const radial = new THREE.Vector3(0, Math.sin(th), Math.cos(th));
    const tangent = new THREE.Vector3(0, Math.cos(th), -Math.sin(th));
    const axis = new THREE.Vector3(handed * 0.707, 0, 0).addScaledVector(tangent, 0.707).normalize();
    rq.setFromUnitVectors(new THREE.Vector3(0, 1, 0), axis);
    // capsule outer surface should just reach the wheel radius (r - 0.2 offset)
    rp.copy(radial).multiplyScalar(r - 0.2);
    m4.compose(rp, rq, rs);
    rollers.setMatrixAt(i, m4);
  }
  rollers.castShadow = rollers.receiveShadow = true;
  g.add(rollers);
  return g;
}

// 48mm omni wheel for odometry pods — axis along X
export function omniWheel(r = 0.95) {
  const g = new THREE.Group();
  g.add(G(new THREE.CylinderGeometry(r * 0.72, r * 0.72, 0.35, 18).rotateZ(Math.PI / 2), M.printGray));
  const n = 10;
  const rollerGeo = new THREE.CapsuleGeometry(0.09, 0.26, 3, 8);
  rollerGeo.rotateZ(Math.PI / 2); // roller axis along wheel axle (X)
  const rollers = new THREE.InstancedMesh(rollerGeo, M.roller, n);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < n; i++) {
    const th = (i / n) * Math.PI * 2;
    m4.makeTranslation(0, Math.sin(th) * (r - 0.09), Math.cos(th) * (r - 0.09));
    rollers.setMatrixAt(i, m4);
  }
  rollers.castShadow = rollers.receiveShadow = true;
  g.add(rollers);
  return g;
}

// solid rubber traction roller (intake bottom) — axis along X
export function tractionRoller(r = 1.0, len = 11) {
  const g = new THREE.Group();
  const body = G(new THREE.CylinderGeometry(r, r, len, 24).rotateZ(Math.PI / 2), M.rubber);
  g.add(body);
  // grip ribs
  const ribGeo = new THREE.TorusGeometry(r + 0.01, 0.035, 6, 24);
  ribGeo.rotateY(Math.PI / 2);
  const nRibs = Math.floor(len / 0.55);
  const ribs = new THREE.InstancedMesh(ribGeo, M.roller, nRibs);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < nRibs; i++) {
    m4.makeTranslation(-len / 2 + (i + 0.5) * (len / nRibs), 0, 0);
    ribs.setMatrixAt(i, m4);
  }
  ribs.castShadow = ribs.receiveShadow = true;
  g.add(ribs);
  return g;
}

// intake star roller — stacked compliant 6-point stars, axis along X
export function starRoller(r = 1.6, len = 10.5) {
  const g = new THREE.Group();
  const shaft = hexShaft(len + 1.2);
  g.add(shaft);
  const star = new THREE.Shape();
  const P = 6;
  for (let i = 0; i < P * 2; i++) {
    const rad = i % 2 === 0 ? r : r * 0.55;
    const a = (i / (P * 2)) * Math.PI * 2;
    if (i === 0) star.moveTo(Math.cos(a) * rad, Math.sin(a) * rad);
    else star.lineTo(Math.cos(a) * rad, Math.sin(a) * rad);
  }
  star.closePath();
  const h = new THREE.Path(); h.absarc(0, 0, 0.17, 0, Math.PI * 2, true); star.holes.push(h);
  const starGeo = new THREE.ExtrudeGeometry(star, { depth: 0.1, bevelEnabled: false });
  starGeo.rotateY(Math.PI / 2); // extrude axis -> X: discs stand perpendicular to the shaft
  const nStars = 9;
  const stars = new THREE.InstancedMesh(starGeo, M.starFlex, nStars);
  const spacers = new THREE.InstancedMesh(
    new THREE.CylinderGeometry(0.42, 0.42, 0.14, 12).rotateZ(Math.PI / 2), M.printGray, nStars);
  const m4 = new THREE.Matrix4(), sq = new THREE.Quaternion(), s1 = new THREE.Vector3(1, 1, 1),
    sp = new THREE.Vector3(), X = new THREE.Vector3(1, 0, 0);
  for (let i = 0; i < nStars; i++) {
    const x = -len / 2 + (i + 0.5) * (len / nStars);
    sq.setFromAxisAngle(X, (i % 2) * 0.5); // offset phases in the disc plane
    sp.set(x, 0, 0);
    m4.compose(sp, sq, s1);
    stars.setMatrixAt(i, m4);
    m4.makeTranslation(x, 0, 0);
    spacers.setMatrixAt(i, m4);
  }
  stars.castShadow = stars.receiveShadow = true;
  spacers.castShadow = spacers.receiveShadow = true;
  g.add(stars, spacers);
  return g;
}

// green compliant feed wheel — axis along Z by default
export function compliantWheel(r = 1.6, w = 0.9) {
  const g = new THREE.Group();
  const body = G(new THREE.CylinderGeometry(r, r, w, 20), M.flexGreen);
  g.add(body);
  // slots between compliant fingers — instanced
  const slotGeo = new THREE.BoxGeometry(0.09, w + 0.02, r * 0.7);
  const slots = new THREE.InstancedMesh(slotGeo, M.holeDark, 12);
  const m4 = new THREE.Matrix4(), sq = new THREE.Quaternion(), s1 = new THREE.Vector3(1, 1, 1),
    sp = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2;
    sq.setFromAxisAngle(Y, -a);
    sp.set(Math.cos(a) * r * 0.62, 0, Math.sin(a) * r * 0.62);
    m4.compose(sp, sq, s1);
    slots.setMatrixAt(i, m4);
  }
  g.add(slots);
  const hub = G(new THREE.CylinderGeometry(0.3, 0.3, w + 0.1, 10), M.printGray);
  g.add(hub);
  return g;
}

// ---------- motors & servos ----------

// REV 5203-class motor + UltraPlanetary-style gearbox. Axis along X, output toward +X.
export function driveMotor(len = 4.6) {
  const g = new THREE.Group();
  const body = G(new THREE.CylinderGeometry(0.72, 0.72, 2.4, 20).rotateZ(Math.PI / 2), M.motorBody);
  body.position.x = -len / 2 + 1.2;
  // cooling ribs along the can — instanced
  const ribGeo = new THREE.TorusGeometry(0.735, 0.03, 6, 20).rotateY(Math.PI / 2);
  const ribs = new THREE.InstancedMesh(ribGeo, M.motorEnd, 3);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 3; i++) {
    m4.makeTranslation(-len + 0.7 + i * 0.6, 0, 0);
    ribs.setMatrixAt(i, m4);
  }
  ribs.castShadow = ribs.receiveShadow = true;
  g.add(ribs);
  const band = motorBand(1.6);
  band.position.x = -len + 1.2;
  g.add(band);
  const endCap = G(new THREE.CylinderGeometry(0.5, 0.5, 0.5, 16).rotateZ(Math.PI / 2), M.motorEnd);
  endCap.position.x = -len + 0.25;
  // encoder housing + feedback connector on the rear face
  const enc = G(new THREE.BoxGeometry(0.34, 0.62, 0.62), M.motorEnd);
  enc.position.x = -len - 0.02;
  g.add(enc);
  const encPort = G(new THREE.BoxGeometry(0.16, 0.22, 0.3), M.portWhite);
  encPort.position.set(-len - 0.2, 0.12, 0);
  g.add(encPort);
  const gb1 = G(new THREE.CylinderGeometry(0.85, 0.85, 1.15, 20).rotateZ(Math.PI / 2), M.gearbox);
  gb1.position.x = -len + 2.4 + 0.575;
  // UltraPlanetary stage seams — instanced
  const seamGeo = new THREE.TorusGeometry(0.85, 0.025, 6, 20).rotateY(Math.PI / 2);
  const seams = new THREE.InstancedMesh(seamGeo, M.holeDark, 2);
  for (let i = 0; i < 2; i++) {
    m4.makeTranslation(gb1.position.x + [-0.28, 0.28][i], 0, 0);
    seams.setMatrixAt(i, m4);
  }
  g.add(seams);
  const gbFace = G(new THREE.CylinderGeometry(0.7, 0.7, 0.35, 16).rotateZ(Math.PI / 2), M.alu);
  gbFace.position.x = -len + 2.4 + 1.15 + 0.17;
  // gearbox face bolt circle
  const fb = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.045, 0.045, 0.1, 6).rotateZ(Math.PI / 2), M.bolt, 6);
  const fm = new THREE.Matrix4();
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2;
    fm.makeTranslation(gbFace.position.x + 0.14, Math.cos(a) * 0.55, Math.sin(a) * 0.55);
    fb.setMatrixAt(i, fm);
  }
  g.add(fb);
  const shaft = G(new THREE.CylinderGeometry(0.157, 0.157, 0.7, 6).rotateZ(Math.PI / 2), M.steel);
  shaft.position.x = -0.2;
  g.add(body, endCap, gb1, gbFace, shaft);
  // power leads
  g.add(cable([[-len + 0.3, 0.3, 0.3], [-len - 0.4, 0.9, 0.6], [-len - 0.4, 1.6, 0.4]], M.wireOrange, 0.05));
  return g;
}

// compact spur-gearbox motor (intake / feed / flywheel) — axis along X, output +X
export function compactMotor() {
  const g = new THREE.Group();
  const body = G(new THREE.CylinderGeometry(0.72, 0.72, 2.55, 20).rotateZ(Math.PI / 2), M.motorBody);
  body.position.x = -1.5;
  const endCap = G(new THREE.CylinderGeometry(0.52, 0.52, 0.4, 16).rotateZ(Math.PI / 2), M.motorEnd);
  endCap.position.x = -2.9;
  const gb = G(new THREE.CylinderGeometry(0.78, 0.78, 0.7, 18).rotateZ(Math.PI / 2), M.motorEnd);
  gb.position.x = 0.15;
  const shaft = G(new THREE.CylinderGeometry(0.157, 0.157, 0.6, 6).rotateZ(Math.PI / 2), M.steel);
  shaft.position.x = 0.7;
  g.add(body, endCap, gb, shaft);
  g.add(cable([[-2.7, 0.25, 0.25], [-3.2, 0.8, 0.5], [-3.2, 1.3, 0.3]], M.wireOrange, 0.045));
  return g;
}

export function servoMotor() { // standard FTC servo
  const g = new THREE.Group();
  g.add(G(new THREE.BoxGeometry(1.65, 0.95, 1.15), M.hubCase));
  const horn = G(new THREE.CylinderGeometry(0.42, 0.42, 0.1, 16), M.portWhite);
  horn.position.set(0.35, 0.53, 0);
  const spline = G(new THREE.CylinderGeometry(0.1, 0.1, 0.16, 12), M.alu);
  spline.position.set(0.35, 0.55, 0);
  g.add(horn, spline);
  const ears = new THREE.InstancedMesh(new THREE.BoxGeometry(0.3, 0.14, 0.28), M.hubCase, 2);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 2; i++) {
    m4.makeTranslation(-0.55, -0.55, [-0.35, 0.35][i]);
    ears.setMatrixAt(i, m4);
  }
  ears.castShadow = ears.receiveShadow = true;
  g.add(ears);
  return g;
}

// ---------- turret ----------

export function lazySusan(r = 2.6) {
  const g = new THREE.Group();
  const ring = (rad, t, holeR = rad - 0.55) => {
    const s = new THREE.Shape();
    s.absarc(0, 0, rad, 0, Math.PI * 2);
    const hole = new THREE.Path(); hole.absarc(0, 0, holeR, 0, Math.PI * 2, true);
    s.holes.push(hole);
    const geo = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false });
    geo.rotateX(-Math.PI / 2);
    return G(geo, M.alu);
  };
  const lower = ring(r, 0.09, r - 0.5); lower.position.y = 0;
  const upper = ring(r - 0.15, 0.09, r - 0.5); upper.position.y = 0.28;
  g.add(lower, upper);
  // bearing balls
  const ballGeo = new THREE.SphereGeometry(0.11, 10, 8);
  const balls = new THREE.InstancedMesh(ballGeo, M.steel, 20);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 20; i++) {
    const a = (i / 20) * Math.PI * 2;
    m4.makeTranslation(Math.cos(a) * (r - 0.3), 0.14, Math.sin(a) * (r - 0.3));
    balls.setMatrixAt(i, m4);
  }
  g.add(balls);
  return g;
}

// ring gear: teeth on outer edge — axis Y
export function ringGear(r = 2.9, teeth = 72, t = 0.3) {
  const s = new THREE.Shape();
  const outer = r + 0.11, root = r - 0.08;
  for (let i = 0; i < teeth; i++) {
    const a0 = (i / teeth) * Math.PI * 2, a1 = ((i + 0.4) / teeth) * Math.PI * 2;
    const a2 = ((i + 0.55) / teeth) * Math.PI * 2, a3 = ((i + 0.9) / teeth) * Math.PI * 2;
    if (i === 0) s.moveTo(Math.cos(a0) * root, Math.sin(a0) * root);
    s.lineTo(Math.cos(a1) * root, Math.sin(a1) * root);
    s.lineTo(Math.cos(a2) * outer, Math.sin(a2) * outer);
    s.lineTo(Math.cos(a3) * outer, Math.sin(a3) * outer);
    s.lineTo(Math.cos((i + 1) / teeth * Math.PI * 2) * root, Math.sin((i + 1) / teeth * Math.PI * 2) * root);
  }
  const hole = new THREE.Path(); hole.absarc(0, 0, r - 0.45, 0, Math.PI * 2, true); s.holes.push(hole);
  const geo = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);
  return G(geo, M.accent);
}

// flywheel with lightening spokes — axis along Y (rotate group to use)
export function flywheel(r = 2.0, w = 0.8) {
  const g = new THREE.Group();
  // rim
  const rimShape = new THREE.Shape();
  rimShape.absarc(0, 0, r, 0, Math.PI * 2);
  const rimHole = new THREE.Path(); rimHole.absarc(0, 0, r - 0.32, 0, Math.PI * 2, true);
  rimShape.holes.push(rimHole);
  const rimGeo = new THREE.ExtrudeGeometry(rimShape, { depth: w, bevelEnabled: false });
  rimGeo.translate(0, 0, -w / 2); rimGeo.rotateX(-Math.PI / 2);
  g.add(G(rimGeo, M.motorEnd));
  // spokes — instanced
  const spokeGeo = new THREE.BoxGeometry(r - 0.15, w * 0.5, 0.24);
  const spokes = new THREE.InstancedMesh(spokeGeo, M.accent, 6);
  const m4 = new THREE.Matrix4(), sq = new THREE.Quaternion(), s1 = new THREE.Vector3(1, 1, 1),
    sp = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);
  const off = (r - 0.15) / 2 + 0.1;
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2;
    sq.setFromAxisAngle(Y, a);
    sp.set(Math.cos(a) * off, 0, -Math.sin(a) * off);
    m4.compose(sp, sq, s1);
    spokes.setMatrixAt(i, m4);
  }
  spokes.castShadow = spokes.receiveShadow = true;
  g.add(spokes);
  g.add(G(new THREE.CylinderGeometry(0.32, 0.32, w + 0.2, 14), M.steel));
  // tread band
  const tread = G(new THREE.TorusGeometry(r - 0.02, 0.06, 8, 40).rotateX(Math.PI / 2), M.rubber);
  tread.scale.y = w * 6;
  g.add(tread);
  return g;
}

// ---------- electronics ----------

export function controlHub() {
  const g = new THREE.Group();
  g.add(G(new THREE.BoxGeometry(5.6, 1.15, 3.1), M.hubCase));
  const lid = G(new THREE.BoxGeometry(5.2, 0.12, 2.7), M.pcb);
  lid.position.y = 0.63;
  g.add(lid);
  // face label
  const lbl = hubLabel();
  lbl.position.y = 0.7;
  g.add(lbl);
  // status LEDs
  for (let i = 0; i < 3; i++) {
    const led = ledDot(0.05, [M.ledGreen, M.ledOrange, M.ledBlue][i]);
    led.position.set(-2.2 + i * 0.35, 0.65, -1.3);
    g.add(led);
  }
  // port rows + corner bolts — instanced
  const m4 = new THREE.Matrix4();
  const portA = new THREE.InstancedMesh(new THREE.BoxGeometry(0.7, 0.5, 0.35), M.portOrange, 4);
  for (let i = 0; i < 4; i++) {
    m4.makeTranslation(-1.8 + i * 1.2, 0.1, 1.62);
    portA.setMatrixAt(i, m4);
  }
  const portB = new THREE.InstancedMesh(new THREE.BoxGeometry(0.55, 0.4, 0.3), M.portWhite, 3);
  for (let i = 0; i < 3; i++) {
    m4.makeTranslation(-1.4 + i * 1.4, 0.1, -1.6);
    portB.setMatrixAt(i, m4);
  }
  const cornerB = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.06, 0.06, 0.1, 8), M.bolt, 4);
  let ci = 0;
  for (const bx of [-2.6, 2.6]) for (const bz of [-1.3, 1.3]) {
    m4.makeTranslation(bx, -0.6, bz);
    cornerB.setMatrixAt(ci++, m4);
  }
  portA.castShadow = portB.castShadow = true;
  g.add(portA, portB, cornerB);
  return g;
}

export function battery() {
  const g = new THREE.Group();
  const b = G(new THREE.BoxGeometry(4.4, 1.35, 2.0), M.battery);
  g.add(b);
  const strap = G(new THREE.BoxGeometry(4.5, 1.42, 0.35), M.rubber);
  g.add(strap);
  // strap buckle
  const buckle = G(new THREE.BoxGeometry(0.5, 0.18, 0.42), M.darkSteel);
  buckle.position.set(1.2, 0.76, 0);
  g.add(buckle);
  // terminal caps + XT30 pigtail
  for (const s of [-1, 1]) {
    const term = G(new THREE.BoxGeometry(0.3, 0.3, 0.3), s < 0 ? M.wireRed : M.wireBlack);
    term.position.set(2.15, 0.35, s * 0.4);
    g.add(term);
  }
  g.add(cable([[2.2, 0.2, 0.6], [3.0, 0.5, 0.9], [3.4, 0.3, 0.3]], M.wireRed, 0.055));
  const xt = G(new THREE.BoxGeometry(0.5, 0.3, 0.35), M.portYellow);
  xt.position.set(3.5, 0.28, 0.3);
  g.add(xt);
  return g;
}

export function webcam() {
  const g = new THREE.Group();
  const body = G(new THREE.BoxGeometry(1.6, 0.55, 0.5), M.hubCase);
  g.add(body);
  const lens = G(new THREE.CylinderGeometry(0.18, 0.18, 0.15, 16).rotateX(Math.PI / 2), M.holeDark);
  lens.position.z = 0.3;
  const glass = G(new THREE.CylinderGeometry(0.13, 0.13, 0.03, 16).rotateX(Math.PI / 2),
    new THREE.MeshStandardMaterial({ color: 0x224488, metalness: 0.6, roughness: 0.1 }));
  glass.position.z = 0.38;
  g.add(lens, glass);
  const mount = G(new THREE.BoxGeometry(0.5, 0.7, 0.12), M.print);
  mount.position.y = -0.55;
  g.add(mount);
  return g;
}

// ---------- flower lift ----------

// slim slide/guide extrusion — axis along Y
export function slideRail(len, w = 0.55, mat = M.alu) {
  return G(new THREE.BoxGeometry(w, len, w), mat);
}

// open deposit cradle — axis along Y, gap sector faces -Z, floor seats the ball
export function cradleCup(r = 1.9, h = 1.1, mat = M.print) {
  const g = new THREE.Group();
  const wall = new THREE.Mesh(
    new THREE.CylinderGeometry(r, r, h, 24, 1, true, Math.PI + 1.1, Math.PI * 2 - 2.2), mat);
  wall.castShadow = wall.receiveShadow = true;
  g.add(wall);
  const floor = G(new THREE.CylinderGeometry(r - 0.05, r - 0.05, 0.08, 24), mat);
  floor.position.y = -h / 2 + 0.04;
  g.add(floor);
  const rim = G(new THREE.TorusGeometry(r - 0.02, 0.045, 8, 28).rotateX(Math.PI / 2), M.accent);
  rim.position.y = h / 2;
  g.add(rim);
  return g;
}

// winch spool — axis along Z, drum + flanges + wound dyneema coils
export function spool(r = 0.42, mat = M.printGray) {
  const g = new THREE.Group();
  g.add(G(new THREE.CylinderGeometry(r * 0.55, r * 0.55, 0.55, 16).rotateX(Math.PI / 2), mat));
  for (const s of [-1, 1]) {
    const fl = G(new THREE.CylinderGeometry(r, r, 0.06, 16).rotateX(Math.PI / 2), mat);
    fl.position.z = s * 0.3;
    g.add(fl);
  }
  // rope windings on the drum — instanced
  const winds = new THREE.InstancedMesh(new THREE.TorusGeometry(r * 0.55 + 0.02, 0.022, 6, 20), M.wireBlack, 5);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 5; i++) {
    m4.makeTranslation(0, 0, -0.2 + i * 0.1);
    winds.setMatrixAt(i, m4);
  }
  g.add(winds);
  return g;
}

// rope sheave — axis along Z
export function pulley(r = 0.34) {
  const g = new THREE.Group();
  g.add(G(new THREE.CylinderGeometry(r, r, 0.12, 18).rotateX(Math.PI / 2), M.hubCase));
  g.add(G(new THREE.TorusGeometry(r - 0.04, 0.045, 8, 20), M.holeDark));
  return g;
}

// ---------- misc ----------

export function cable(points, mat = M.wireBlack, r = 0.045) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)));
  const m = new THREE.Mesh(new THREE.TubeGeometry(curve, 24, r, 6), mat);
  m.receiveShadow = true; // wires are sub-pixel in the shadow map — skip casting
  return m;
}

export function springHelix(r = 0.35, len = 0.8, coils = 6) {
  const pts = [];
  const n = coils * 16;
  for (let i = 0; i <= n; i++) {
    const t = i / n, a = t * coils * Math.PI * 2;
    pts.push(new THREE.Vector3(Math.cos(a) * r, t * len, Math.sin(a) * r));
  }
  return shadowify(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), n * 2, 0.035, 6), M.steel));
}

// sphere geometry shared per radius — the demo spawns/removes balls every run
const _ballGeos = new Map();
export function ball(r, mat) {
  let g = _ballGeos.get(r);
  if (!g) { g = new THREE.SphereGeometry(r, 26, 18); _ballGeos.set(r, g); }
  return G(g, mat);
}

export function pillar(h, r = 0.16, mat = M.alu) {
  return G(new THREE.CylinderGeometry(r, r, h, 10), mat);
}

// ---------- realism pass: labels, caps, fasteners, wiring ----------

// FTC alliance number plate — textured face on a thin plate, faces +Z
export function numberPlate(w = 3.6, h = 2.4, num = '27475', hue = '#1b3fa0') {
  const g = new THREE.Group();
  g.add(G(new THREE.BoxGeometry(w, h, 0.07), M.printGray));
  const face = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.14, h - 0.14),
    new THREE.MeshStandardMaterial({ map: numberPlateTex(num, hue), roughness: 0.55 }));
  face.position.z = 0.045;
  face.receiveShadow = true;
  g.add(face);
  return g;
}

// AprilTag card on a dark backing, faces +Z
export function tagPlate(size = 3.4, seed = 7) {
  const g = new THREE.Group();
  g.add(G(new THREE.BoxGeometry(size + 0.3, size + 0.3, 0.06), M.hubCase));
  const face = new THREE.Mesh(new THREE.PlaneGeometry(size, size),
    new THREE.MeshStandardMaterial({ map: aprilTagTex(seed), roughness: 0.8 }));
  face.position.z = 0.04;
  g.add(face);
  return g;
}

// plastic end cap pressed into a U-channel end — section ~1.89"
export function endCap() {
  return G(new THREE.BoxGeometry(1.78, 1.78, 0.16), M.rubber);
}

// nylock-style hex nut at a shaft tip — axis along X
export function shaftNut() {
  const g = new THREE.Group();
  g.add(G(new THREE.CylinderGeometry(0.19, 0.19, 0.16, 6).rotateZ(Math.PI / 2), M.darkSteel));
  const nyl = G(new THREE.CylinderGeometry(0.12, 0.12, 0.05, 12).rotateZ(Math.PI / 2), M.portWhite);
  nyl.position.x = 0.09;
  g.add(nyl);
  return g;
}

// small brass pinion gear on a motor shaft — axis along X
export function pinion(r = 0.3) {
  const g = spurGear(Math.max(8, Math.round(r * 22)), r, 0.22, M.gearbox, 0.14);
  g.rotation.z = Math.PI / 2; // spurGear builds axis-Y; roll about Z to stand it on the X shaft
  return g;
}

// REV-style main switch: bracket + orange paddle + status window
export function mainSwitch() {
  const g = new THREE.Group();
  g.add(G(new THREE.BoxGeometry(0.5, 1.3, 1.9), M.hubCase));
  const paddle = G(new THREE.BoxGeometry(0.3, 0.55, 0.9), M.portOrange);
  paddle.position.set(0.32, 0.1, 0); paddle.rotation.z = -0.28;
  g.add(paddle);
  const win = G(new THREE.BoxGeometry(0.06, 0.3, 0.7), M.ledGreen);
  win.position.set(0.28, -0.42, 0);
  g.add(win);
  return g;
}

// tiny emissive LED — axis along Y
export function ledDot(r = 0.06, mat = M.ledGreen) {
  const d = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.05, 10), mat);
  return d;
}

// multi-strand servo/extension wire — parallel strands along the same route
export function wireBundle(points, mats = [M.wireRed, M.wireBlack, M.wireYellow], r = 0.028, spread = 0.055) {
  const g = new THREE.Group();
  const n = mats.length;
  mats.forEach((m, i) => {
    const off = (i - (n - 1) / 2) * spread;
    g.add(cable(points.map(p => [p[0] + off, p[1], p[2]]), m, r));
  });
  return g;
}

// zip-tie ring around a bundle — cosmetic, axis along X
export function zipTie(r = 0.12) {
  return G(new THREE.TorusGeometry(r, 0.03, 5, 12).rotateY(Math.PI / 2), M.portWhite);
}

// flat washer — axis along X (sits on shafts beside bearings)
export function washer(r = 0.24) {
  return G(new THREE.CylinderGeometry(r, r, 0.04, 16).rotateZ(Math.PI / 2), M.steel);
}

// split motor clamp — bore ring + ear bolts, axis along X
export function clampBlock(r = 0.78) {
  const g = new THREE.Group();
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(r + 0.16, r + 0.16, 0.34, 20, 1, true).rotateZ(Math.PI / 2), M.alu);
  ring.castShadow = ring.receiveShadow = true;
  g.add(ring);
  for (const s of [-1, 1]) {
    const ear = G(new THREE.BoxGeometry(0.34, 0.5, 0.24), M.alu);
    ear.position.set(0, r + 0.16, s * 0.3);
    g.add(ear);
    const eb = G(new THREE.CylinderGeometry(0.05, 0.05, 0.2, 6).rotateX(Math.PI / 2), M.bolt);
    eb.position.set(0, r + 0.16, s * 0.3);
    g.add(eb);
  }
  return g;
}

// rope guide eyelet — welded ring on the mast, axis along Z
export function eyelet(r = 0.16) {
  const g = new THREE.Group();
  g.add(G(new THREE.TorusGeometry(r, 0.035, 8, 16), M.steel));
  const tab = G(new THREE.BoxGeometry(0.1, 0.22, 0.05), M.steel);
  tab.position.y = r + 0.08;
  g.add(tab);
  return g;
}

// JST-style connector block pair on a wire — axis along Z
export function connector(len = 0.3) {
  const g = new THREE.Group();
  const b = G(new THREE.BoxGeometry(0.22, 0.16, len), M.portWhite);
  g.add(b);
  const latch = G(new THREE.BoxGeometry(0.1, 0.06, len * 0.5), M.holeDark);
  latch.position.y = 0.11;
  g.add(latch);
  return g;
}

// #25 roller chain looped around two sprockets — vertical loop in the YZ plane
// at fixed x; c = [y, z] centers, r = wrap radius (sprocket pitchR + clearance)
export function chainLoop(c1, r1, c2, r2, x = 0, linkR = 0.06) {
  const g = new THREE.Group();
  const dy = c2[0] - c1[0], dz = c2[1] - c1[1];
  const d = Math.hypot(dy, dz), base = Math.atan2(dz, dy);
  // external (open-belt) tangent normal angle offset — same on both circles
  const phi = Math.acos(THREE.MathUtils.clamp((r1 - r2) / d, -0.98, 0.98));
  const a1 = base + phi, a2 = base - phi;
  const pt = (c, r, a) => [c[0] + Math.cos(a) * r, c[1] + Math.sin(a) * r];
  const ring = [];
  // side A straight run: c1@a1 → c2@a1
  ring.push(pt(c1, r1, a1), pt(c2, r2, a1));
  // wrap the far side of c2: a1 → a2 sweeping through `base` (short way, span 2φ)
  const n2 = Math.max(6, Math.round(2 * phi / 0.22));
  for (let i = 1; i <= n2; i++) ring.push(pt(c2, r2, a1 + (i / n2) * (a2 - a1)));
  // side B straight run: c2@a2 → c1@a2
  ring.push(pt(c1, r1, a2));
  // wrap the far side of c1: a2 → a1 the long way through base−π (span 2π−2φ)
  const n1 = Math.max(8, Math.round((2 * Math.PI - 2 * phi) / 0.22));
  for (let i = 1; i <= n1; i++) ring.push(pt(c1, r1, a2 + (i / n1) * (a1 - 2 * Math.PI - a2)));
  const curve = new THREE.CatmullRomCurve3(
    ring.map(p => new THREE.Vector3(x, p[0], p[1])), true, 'catmullrom', 0.02);
  g.add(shadowify(new THREE.Mesh(new THREE.TubeGeometry(curve, 90, linkR, 6), M.darkSteel)));
  // roller pins along the loop
  const pins = new THREE.InstancedMesh(
    new THREE.CylinderGeometry(0.05, 0.05, 0.16, 6).rotateZ(Math.PI / 2), M.steel, 64);
  const m4 = new THREE.Matrix4(), p = new THREE.Vector3();
  const nPins = Math.min(64, Math.floor(curve.getLength() / 0.3));
  for (let i = 0; i < nPins; i++) {
    curve.getPointAt(i / nPins, p);
    m4.makeTranslation(p.x, p.y, p.z);
    pins.setMatrixAt(i, m4);
  }
  pins.count = nPins;
  g.add(pins);
  return g;
}

// motor wrap label band — slides over a Ø1.44 body, axis along X
export function motorBand(len = 1.0) {
  const geo = new THREE.CylinderGeometry(0.745, 0.745, len, 20, 1, true);
  geo.rotateZ(Math.PI / 2);
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: motorLabelTex(), roughness: 0.6, metalness: 0.2 }));
  m.castShadow = false;
  return m;
}

// thin label card for hub top face
export function hubLabel(w = 2.4, h = 0.9) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h),
    new THREE.MeshStandardMaterial({ map: hubLabelTex(), roughness: 0.7 }));
  m.rotation.x = -Math.PI / 2;
  return m;
}

// bolt field — instanced socket-head bolts at [x,y,z] list, axis along Y
export function boltField(list, r = 0.07, h = 0.1, axis = 'y') {
  const geo = new THREE.CylinderGeometry(r, r, h, 8);
  if (axis === 'x') geo.rotateZ(Math.PI / 2);
  if (axis === 'z') geo.rotateX(Math.PI / 2);
  const inst = new THREE.InstancedMesh(geo, M.bolt, list.length);
  const m4 = new THREE.Matrix4();
  list.forEach((p, i) => { m4.makeTranslation(p[0], p[1], p[2]); inst.setMatrixAt(i, m4); });
  inst.count = list.length;
  inst.receiveShadow = true; // sub-pixel in the shadow map — no castShadow
  return inst;
}

// USB / slip-ring stack on the turret column
export function slipRing() {
  const g = new THREE.Group();
  for (const y of [0, 0.22]) {
    const ring = G(new THREE.TorusGeometry(2.16, 0.05, 8, 40).rotateX(Math.PI / 2), M.portWhite);
    ring.position.y = y;
    g.add(ring);
  }
  const sleeve = G(new THREE.CylinderGeometry(2.1, 2.1, 0.34, 40, 1, true), M.holeDark);
  sleeve.position.y = 0.11;
  g.add(sleeve);
  return g;
}
