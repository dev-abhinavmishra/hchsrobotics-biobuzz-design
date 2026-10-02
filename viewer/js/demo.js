// demo.js — scripted BIOBUZZ match demonstration.
// Drives the robot through every game task: pollen intake, hive-cell launches,
// hive tipping via nectar, flower deposit via the lift, and a loading-zone park.
// Coordinates are field-space inches (field center = origin).
import * as THREE from 'three';
import { M } from './materials.js';
import * as P from './parts.js';

const lerp = (a, b, k) => a + (b - a) * k;
const ease = k => k * k * (3 - 2 * k); // smoothstep
function lerpAngle(a, b, k) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return a + d * k;
}
const V = (x, y, z) => new THREE.Vector3(x, y, z);

export function createMatchDemo(ctx) {
  // ctx: { scene, robot, anim, refs, camera, controls, caption, ensureField, setLift, resetLiftBall, clearShot, isAnimating(v) }
  const { scene, robot, anim, refs, camera, controls } = ctx;

  const flying = [];    // balls in ballistic flight
  const sucking = [];   // balls being pulled into the intake (two-stage path)
  const rising = [];    // balls climbing the feed column toward the nip
  const transfers = []; // scripted carries (e.g. column port → chute → cradle)
  const hopperRolls = []; // brief roll-down visible through the hopper walls
  const consumed = [];  // field pickups swept up — restored to their floor spots on stop
  const landed = [];    // balls scored into a cell — cleared on the next run
  let active = false, freeCam = false, phaseIdx = -1, phaseT = 0, lastPos = new THREE.Vector3();
  let camPosT = new THREE.Vector3(), camTgtT = new THREE.Vector3();
  const followBtn = document.getElementById('btn-followcam');
  controls.addEventListener('start', () => { if (active) { freeCam = true; followBtn.classList.add('show'); } });
  followBtn.onclick = () => { freeCam = false; followBtn.classList.remove('show'); };

  /* ---------- helpers ---------- */

  function mouthWorld() { return robot.localToWorld(V(0, 2.2, -8.4)); }
  function nipWorld() {
    const yawW = robot.rotation.y + anim.turret.rotation.y;
    return robot.localToWorld(V(0, 12.3, 2.6))
      .addScaledVector(V(-Math.sin(yawW), 0, -Math.cos(yawW)), 2.6);
  }
  function aimAt(target) {
    const start = nipWorld();
    const dx = target.x - start.x, dz = target.z - start.z;
    return Math.atan2(-dx, -dz) - robot.rotation.y; // world yaw → turret-local
  }
  function fly(ball, start, target, dur, arcUp, landIn) {
    const mid = start.clone().lerp(target, 0.45);
    mid.y = Math.max(start.y, target.y) + arcUp;
    flying.push({ ball, curve: new THREE.QuadraticBezierCurve3(start, mid, target), t: 0, dur, landIn });
  }
  // ball rises inside the clear column, then launches — sells the feed path
  function riseLaunch(target, mat, r, dur, arcUp, landIn) {
    const ball = P.ball(r, mat);
    robot.add(ball);
    ball.position.set(0, 5.0, 2.6); // inside the column, just above the feed wheel
    rising.push({ ball, t: 0, target, dur, arcUp, landIn });
  }
  // visible carry along a world-space path (column port → chute → cradle)
  function transfer(ball, pts, dur, onDone) {
    scene.attach(ball);
    const mid = [];
    for (let i = 1; i < pts.length - 1; i++) mid.push(pts[i]);
    const curve = new THREE.CatmullRomCurve3([pts[0], ...mid, pts[pts.length - 1]]);
    transfers.push({ ball, curve, t: 0, dur, onDone });
  }
  function suckNearest(center, radius = 7) {
    let best = null, bd = radius;
    for (const b of refs.pickups) {
      if (!b.visible) continue;
      const d = b.getWorldPosition(new THREE.Vector3()).distanceTo(center);
      if (d < bd) { bd = d; best = b; }
    }
    if (best) {
      const w0 = best.getWorldPosition(new THREE.Vector3());
      // stage 1 — floor slide to just in front of the intake mouth
      const fwd = V(-Math.sin(robot.rotation.y), 0, -Math.cos(robot.rotation.y));
      const mouth = mouthWorld();
      const approach = mouth.clone().addScaledVector(fwd, 2.6);
      approach.y = w0.y;
      // stage 2 — arc up over the traction roller into the throat
      const throat = robot.localToWorld(V(0, 4.0, -5.6));
      best.userData.suck = {
        t: 0,
        c1: new THREE.QuadraticBezierCurve3(w0, w0.clone().lerp(approach, 0.5), approach),
        c2: new THREE.QuadraticBezierCurve3(approach, approach.clone().lerp(throat, 0.5).add(V(0, 0.9, 0)), throat),
      };
      best.userData.home = { parent: best.parent, pos: best.position.clone() };
      consumed.push(best);
      scene.attach(best);
      sucking.push(best);
    }
  }
  // brief roll down the hopper incline — visible through the translucent walls
  function hopperRoll(mat) {
    const b = P.ball(1.35, mat);
    robot.add(b);
    b.position.set(0, 4.35, -5.7);
    hopperRolls.push({ ball: b, t: 0 });
  }
  function tipHive(which = 'blue') {
    const h = refs.hives.find(h => h.name === which);
    if (h) h.pivot.userData.tipT = tNow;
  }

  /* ---------- drive helper ---------- */
  // segs: [{ k0,k1, to:[x,z], h0,h1 }] — position eases across each leg;
  // heading slews h0→h1 within the leg (pass h only to hold a heading).
  function makeDrive(segs) {
    let start = null, startH = 0;
    return {
      enter() { start = robot.position.clone(); startH = robot.rotation.y; },
      update(dt, k) {
        let px = start.x, pz = start.z;
        for (const s of segs) {
          if (k < s.k0) break;
          if (k <= s.k1) {
            const kk = ease((k - s.k0) / (s.k1 - s.k0));
            px = lerp(px, s.to[0], kk); pz = lerp(pz, s.to[1], kk);
            const h1 = s.h !== undefined ? s.h : s.h1;
            const h0 = s.h0 !== undefined ? s.h0 : startH;
            if (h1 !== undefined) robot.rotation.y = lerpAngle(h0, h1, kk);
            break;
          }
          px = s.to[0]; pz = s.to[1];
          if (s.h !== undefined) robot.rotation.y = s.h;
          else if (s.h1 !== undefined) robot.rotation.y = s.h1;
        }
        robot.position.x = px; robot.position.z = pz;
      },
    };
  }

  /* ---------- camera shots ---------- */
  const chase = () => {
    const f = V(-Math.sin(robot.rotation.y), 0, -Math.cos(robot.rotation.y));
    return { pos: robot.position.clone().addScaledVector(f, -32).add(V(0, 17, 0)), tgt: robot.position.clone().add(V(0, 4, 0)).addScaledVector(f, 8) };
  };
  const fixed = (px, py, pz, tx, ty, tz) => () => ({ pos: V(px, py, pz), tgt: V(tx, ty, tz) });

  /* ---------- phase list ---------- */
  const CELL = () => refs.upCellBlue.clone();
  const cellInner = () => refs.upCellBlue.clone().add(V(0, -1.2, -0.6));
  const FLOWER = V(64, 0, -64), MOUTH = V(64, 19.7, -64);
  const hiveCam = () => { // elevated 3/4 view framing both robot and the up-cell mouth
    const mid = robot.position.clone().lerp(CELL(), 0.45);
    return { pos: mid.clone().add(V(18, 26, 18)), tgt: mid.clone().add(V(0, -1, 0)) };
  };

  const phases = [
    {
      cap: 'MATCH START', sub: 'Blue alliance · 18" cube · 30s autonomous',
      dur: 2.0, cam: fixed(8, 30, 92, 34, 5, 48), gates: {},
      enter() { robot.position.set(40, 0, 56); robot.rotation.y = 0; },
      update() {},
    },
    {
      cap: 'AUTONOMOUS — POLLEN RUN', sub: 'Intake rollers spin up · over/under rollers sweep the floor cluster',
      dur: 4.6, cam: chase, gates: { intake: true, agit: true },
      drive: makeDrive([{ k0: 0.05, k1: 1, to: [31.6, -9.5], h: 0 }]),
      update(dt, k) {
        if (k > 0.62 && !this._p1) { this._p1 = 1; suckNearest(V(31.6, 0, -16.5), 6); }
        if (k > 0.78 && !this._p2) { this._p2 = 1; suckNearest(V(31.6, 0, -16.5), 6); }
        if (k > 0.9 && !this._p3) { this._p3 = 1; suckNearest(V(31.6, 0, -18.5), 7); }
      },
    },
    {
      cap: 'AIMING', sub: 'Turret slews to the blue CELL AprilTag · flywheels spin up to speed',
      dur: 2.4, cam: hiveCam, gates: { fly: true },
      drive: makeDrive([{ k0: 0, k1: 0.5, to: [26, -14], h: 0 }]),
      aim: () => aimAt(CELL()),
      update() {},
    },
    {
      cap: 'SCORING — POLLEN ×3', sub: 'Feed wheel meters balls up the column · dual flywheel lob into the up-cell',
      dur: 5.2, cam: hiveCam, gates: { fly: true, feed: true, agit: true },
      aim: () => aimAt(CELL()),
      update(dt, k) {
        const t = k * this.dur;
        if (t > 0.5 && !this._f1) { this._f1 = 1; riseLaunch(cellInner(), M.pollen, 1.4, 0.95, 10, refs.hives[1].pivot.children.find(c => c.position.z < 0)); }
        if (t > 2.1 && !this._f2) { this._f2 = 1; riseLaunch(cellInner(), M.pollen, 1.4, 0.95, 10, refs.hives[1].pivot.children.find(c => c.position.z < 0)); }
        if (t > 3.7 && !this._f3) { this._f3 = 1; riseLaunch(cellInner(), M.pollen, 1.4, 0.95, 10, refs.hives[1].pivot.children.find(c => c.position.z < 0)); }
      },
    },
    {
      cap: 'TELEOP — NECTAR PICKUP', sub: 'Mecanum strafe to the alliance stash · intake both NECTAR',
      dur: 4.4, cam: chase, gates: { intake: true, agit: true },
      drive: makeDrive([
        { k0: 0, k1: 0.62, to: [55, -16], h: 0 },
        { k0: 0.62, k1: 1, to: [55, -21.5], h: 0 },
      ]),
      update(dt, k) {
        if (k > 0.68 && !this._p1) { this._p1 = 1; suckNearest(V(55, 0, -28), 8); }
        if (k > 0.85 && !this._p2) { this._p2 = 1; suckNearest(V(55, 0, -30), 8); }
      },
    },
    {
      cap: 'SCORING — NECTAR ×2', sub: 'Balls rise through the column · mass in the up cell tips the HIVE',
      dur: 5.6, cam: hiveCam, gates: { fly: true, feed: true, agit: true },
      drive: makeDrive([{ k0: 0, k1: 0.4, to: [26, -20], h: 0 }]),
      aim: () => aimAt(CELL()),
      update(dt, k) {
        const t = k * this.dur;
        if (t > 0.8 && !this._f1) { this._f1 = 1; riseLaunch(cellInner(), M.nectarBlue, 1.8, 1.0, 9, refs.hives[1].pivot.children.find(c => c.position.z < 0)); }
        if (t > 2.4 && !this._f2) { this._f2 = 1; riseLaunch(cellInner(), M.nectarBlue, 1.8, 1.0, 9, refs.hives[1].pivot.children.find(c => c.position.z < 0)); }
        if (t > 3.9 && !this._tip) { this._tip = 1; tipHive('blue'); ctx.caption('HIVE TIPPED', 'Nectar payload dumps the cell — pivot arm swings down'); }
      },
    },
    {
      cap: 'LATE MATCH — FLOWER RUN', sub: 'Diverter flap kicks a NECTAR down the load chute · swing to the corner FLOWER',
      dur: 4.8, cam: chase, gates: { feed: true, agit: true },
      drive: makeDrive([
        { k0: 0, k1: 0.45, to: [40, -34], h0: 0, h1: Math.PI * 0.9 },
        { k0: 0.45, k1: 1, to: [51.5, -53.5], h0: Math.PI * 0.9, h1: Math.PI },
      ]),
      update() {},
    },
    {
      cap: 'DEPOSIT — FLOWER', sub: 'Chute loads the cradle · two-stage lift rises +14.6" and tips the NECTAR in',
      dur: 8.2, gates: {},
      cam: fixed(46, 25, -42, 63, 21.5, -62),
      enter() {
        // ball diverts out the column port, down the load chute, into the cradle
        const port = robot.localToWorld(V(-2.5, 8.0, 2.9));
        const mid = robot.localToWorld(V(-4.6, 6.9, 3.8));
        const cup = anim.lift.cradle.localToWorld(V(0.28, -1.2, -0.67));
        const nb = P.ball(1.8, M.nectarBlue);
        nb.position.copy(port); scene.add(nb);
        anim.lift.ball.visible = false;
        transfer(nb, [port, mid, cup], 1.15, () => { anim.lift.ball.visible = true; this._ld = 1; });
        anim.lift.dropHook = (lb) => {
          const from = lb.getWorldPosition(new THREE.Vector3());
          const m2 = from.clone().lerp(MOUTH, 0.45); m2.y += 2.2;
          anim.lift.guided = { curve: new THREE.QuadraticBezierCurve3(from, m2, MOUTH), t: 0 };
        };
      },
      update(dt, k) {
        const t = k * this.dur;
        if (this._ld && !this._up) { this._up = 1; ctx.setLift(1); }
        if (t > 6.5 && !this._dn) { this._dn = 1; ctx.setLift(0); ctx.caption('NECTAR SCORED', 'Ball dropped through the ~4" mouth — cradle retracting'); }
      },
      exit() { anim.lift.dropHook = null; },
    },
    {
      cap: 'ENDGAME — PARK', sub: 'Return fully inside the LOADING ZONE tape',
      dur: 4.8, cam: chase, gates: {},
      drive: makeDrive([
        { k0: 0, k1: 0.5, to: [40, -10], h0: Math.PI, h1: 0 },
        { k0: 0.5, k1: 1, to: [40, 52], h: 0 },
      ]),
      update() {},
    },
    {
      cap: 'MATCH COMPLETE', sub: 'POLLEN ×3 · NECTAR ×2 in the hive · hive tipped · NECTAR in the flower · parked',
      dur: 2.5, cam: fixed(52, 34, 86, 10, 6, 0), gates: {},
      update() {},
    },
  ];

  /* ---------- engine ---------- */
  let tNow = 0;

  function setPhase(i) {
    const p = phases[phaseIdx];
    if (p && p.exit) p.exit();
    phaseIdx = i;
    phaseT = 0;
    const ph = phases[i];
    if (!ph) return;
    for (const k in ph) if (k.startsWith('_')) delete ph[k];
    ctx.caption(ph.cap, ph.sub);
    anim.gates = ph.gates || {};
    if (ph.enter) ph.enter.call(ph);
    if (ph.drive) ph.drive.enter();
  }

  let columnBall = null;
  function start() {
    if (active) return;
    ctx.ensureField();
    ctx.resetLiftBall();
    ctx.clearShot(); // drop any in-flight Launch Demo ball so it can't fight the aim
    // clear balls scored into the cell on a previous run — fresh match, empty cell
    for (const b of landed) b.parent && b.parent.remove(b);
    landed.length = 0;
    anim.lift.ball.visible = false; // cradle loads visibly via the chute transfer
    // hide the static staged column ball — real feed runs carry the column during the demo
    robot.traverse(o => { if (o.userData.entry?.name === 'POLLEN (in column)') columnBall = o; });
    if (columnBall) columnBall.visible = false;
    robot.rotation.y = 0;
    lastPos.copy(robot.position);
    freeCam = false;
    controls.enabled = true; // spectator may grab the camera at any time
    document.getElementById('caption').classList.add('show');
    active = true;
    setPhase(0);
    ctx.isAnimating(true);
  }

  function stop() {
    active = false;
    freeCam = false;
    followBtn.classList.remove('show');
    controls.enabled = true;
    document.getElementById('caption').classList.remove('show');
    anim.lift.dropHook = null;
    ctx.resetLiftBall(); // re-seat the cradle ball and ease the lift down
    anim.gates = null;
    if (columnBall) columnBall.visible = true;
    ctx.isAnimating(false);
    robot.position.y = 0;
    // clean up in-flight / mid-motion balls
    for (const f of flying) scene.remove(f.ball);
    for (const r of rising) robot.remove(r.ball);
    for (const tr of transfers) scene.remove(tr.ball);
    for (const h of hopperRolls) robot.remove(h.ball);
    // swept pickups go back to their staged floor spots so replays stay populated
    for (const b of consumed) {
      const hm = b.userData.home;
      if (hm) { hm.parent.add(b); b.position.copy(hm.pos); }
      b.scale.setScalar(1);
      b.visible = true;
      delete b.userData.suck;
      delete b.userData.home;
    }
    flying.length = sucking.length = rising.length = transfers.length = hopperRolls.length = consumed.length = 0;
  }

  function update(dt, t) {
    if (!active) return;
    tNow = t;
    const ph = phases[phaseIdx];
    if (!ph) { stop(); return; }
    phaseT += dt;
    const k = Math.min(1, phaseT / ph.dur);

    // drive + aim + phase logic
    if (ph.drive) ph.drive.update(dt, k);
    if (ph.aim) {
      const target = ph.aim();
      anim.turret.rotation.y = lerpAngle(anim.turret.rotation.y, target, Math.min(1, dt * 3.5));
    }
    ph.update.call(ph, dt, k);

    // wheels spin with travel speed + subtle body bob
    const v = robot.position.distanceTo(lastPos) / Math.max(dt, 1e-4);
    const dirSign = V(-Math.sin(robot.rotation.y), 0, -Math.cos(robot.rotation.y))
      .dot(robot.position.clone().sub(lastPos)) >= 0 ? 1 : -1;
    for (const w of anim.wheels) w.obj.rotation.x += (v / w.r) * dirSign * dt;
    robot.position.y = Math.min(0.12, v * 0.02) * Math.abs(Math.sin(t * 9));
    lastPos.copy(robot.position);

    // balls being swept into the intake — floor slide, then arc up the throat
    for (let i = sucking.length - 1; i >= 0; i--) {
      const b = sucking[i], s = b.userData.suck;
      s.t += dt / 0.95;
      if (s.t < 0.55) {
        b.position.copy(s.c1.getPoint(ease(Math.min(1, s.t / 0.55))));
      } else {
        const k = ease(Math.min(1, (s.t - 0.55) / 0.45));
        b.position.copy(s.c2.getPoint(k));
        b.scale.setScalar(1 - k * 0.3);
      }
      b.rotation.x += 10 * dt;
      if (s.t >= 1) { b.visible = false; sucking.splice(i, 1); hopperRoll(b.material); }
    }

    // hopper roll-through glimpses
    for (let i = hopperRolls.length - 1; i >= 0; i--) {
      const h = hopperRolls[i];
      h.t += dt / 0.8;
      const k = Math.min(1, h.t);
      h.ball.position.set(0.2 * Math.sin(k * 3), 4.35 + ease(k) * 0.5, -5.7 + k * 2.9);
      h.ball.rotation.x -= 7 * dt;
      if (k >= 1) { robot.remove(h.ball); hopperRolls.splice(i, 1); }
    }

    // balls climbing the feed column, then handed to the launcher
    for (let i = rising.length - 1; i >= 0; i--) {
      const r = rising[i];
      r.t += dt / 0.62;
      const k = Math.min(1, r.t);
      r.ball.position.set(0, 5.0 + ease(k) * 7.0, 2.6);
      if (k >= 1) {
        scene.attach(r.ball);
        fly(r.ball, nipWorld(), r.target, r.dur, r.arcUp, r.landIn);
        rising.splice(i, 1);
      }
    }

    // scripted carries (load chute → cradle)
    for (let i = transfers.length - 1; i >= 0; i--) {
      const tr = transfers[i];
      tr.t += dt / tr.dur;
      const k = Math.min(1, tr.t);
      tr.ball.position.copy(tr.curve.getPoint(ease(k)));
      tr.ball.rotation.z += 5 * dt;
      if (k >= 1) {
        const done = tr.onDone;
        scene.remove(tr.ball);
        transfers.splice(i, 1);
        if (done) done();
      }
    }

    // ballistic shots
    for (let i = flying.length - 1; i >= 0; i--) {
      const f = flying[i];
      f.t += dt / f.dur;
      const kk = Math.min(1, f.t);
      f.ball.position.copy(f.curve.getPoint(kk));
      f.ball.rotation.x += 7 * dt;
      if (kk >= 1) {
        if (f.landIn) {
          const wp = f.ball.getWorldPosition(new THREE.Vector3());
          f.landIn.add(f.ball);
          f.ball.position.copy(f.landIn.worldToLocal(wp));
          f.ball.position.y -= 1.15; // settle below the mouth plane — reads as inside the cell
          landed.push(f.ball);
        }
        flying.splice(i, 1);
      }
    }

    // camera chase — spectator keeps control once they grab it
    if (!freeCam) {
      const shot = ph.cam();
      camPosT.copy(shot.pos); camTgtT.copy(shot.tgt);
      const cf = Math.min(1, dt * 2.6);
      camera.position.lerp(camPosT, cf);
      controls.target.lerp(camTgtT, cf);
    }

    if (phaseT >= ph.dur) {
      if (phaseIdx + 1 < phases.length) setPhase(phaseIdx + 1);
      else stop();
    }
  }

  return { start, stop, update, get active() { return active; } };
}
