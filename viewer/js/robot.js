// robot.js — BIOBUZZ competition robot assembly (inches, Y-up, front = -Z)
//
// Positions follow the as-built CAD (cad/master_robot.FCStd, sprint-04 state),
// converted mm→in with: viewer.x = -cad.y/25.4, viewer.y = cad.z/25.4,
// viewer.z = -cad.x/25.4. Where the viewer can't express a real feature
// (ring-gear tooth profile, formed-plate flanges, chute lip flare, slot cutouts
// in round shells) a comment marks the deviation.
import * as THREE from 'three';
import { M } from './materials.js';
import * as P from './parts.js';

export const SUBS = {
  drive:       { label: 'Drivetrain & Frame',   color: '#9aa3ad', explode: new THREE.Vector3(0, -0.4, 0),  desc: '17.5×17.5 in. goBILDA-pattern U-channel chassis. 4× 96 mm mecanum wheels on live 8 mm REX hex axles, each coaxially driven by a 5203-class motor with a 5.2:1+ planetary gearbox through flange bearing blocks. Three dead-wheel odometry pods under the belly pan feed the pose estimator. Raised front crossmember doubles as the intake crown.' },
  intake:      { label: 'Intake',               color: '#2f7fd6', explode: new THREE.Vector3(0, -1.2, -5), desc: 'Full-width over/under dual-roller intake. Bottom: ribbed rubber traction roller ahead of the throat; top: stacked compliant star roller on torsion-spring floating mounts, offset behind and above the bottom roller — passes both 2.8" POLLEN and 3.6" NECTAR. #25 chain drive from a motor under the hopper incline; GT-belt cross-drive spins the star roller off the bottom shaft.' },
  hopper:      { label: 'Hopper & Feed',        color: '#37b34a', explode: new THREE.Vector3(0, 2.2, 0),   desc: 'Gravity-assisted ~21° inclined magazine (capacity ~6) in PETG/polycarb walls. Servo agitator paddle breaks jams at the low corner. Green compliant feed wheel meters single balls into the clear 4" feed column that rises through the turret axis — allowing unlimited turret yaw. A servo gate meters the column mouth; a Y-flap below the deck can divert a ball out the side port to the flower lift instead of the nip.' },
  turret:      { label: 'Turret',               color: '#e07ab8', explode: new THREE.Vector3(0, 4.6, 0),   desc: 'Split lazy-susan races (lower + upper) carry the launch deck: 4 mm PETG deck 244–248, susan 248–256.5, 72T ring gear 256.5–263, rotating plate 263–267. External ring mesh — the 14T pinion drives the ring outer rim at 72.8 mm center distance from a continuous-rotation servo at −Y of the turret axis. The feed column passes through the hollow center, so ammo supply is yaw-independent.' },
  launcher:    { label: 'Flywheel Launcher',    color: '#d9a406', explode: new THREE.Vector3(0, 7.6, 0),   desc: 'Dual counter-rotating 3.5" flywheels (independent 5203 motors → tunable spin differential) on a 73.7 mm nip gap. Servo-driven hood rides nearly flat on the rear pivot — sets exit angle ~40–65° for the HIVE cell lob. FLOWER deposits go to the lift (a 4" mouth for a 3.6" NECTAR is too tight a lob window). Vision camera rides the turret and tracks CELL AprilTags.' },
  lift:        { label: 'Flower Lift',          color: '#8e6fd8', explode: new THREE.Vector3(-2.6, 2.0, 3.2), desc: 'Two-stage cascade deposit lift on slim guide rails, dyneema-rigged from a continuous-servo winch with a traveling pulley on stage 1. The feed column doubles as the ball elevator: a servo Y-flap below the turret deck kicks one ball out the +Y side port, down the two-leg load chute (28.5°/21.8°, through a slot in the left tower cheek), and into the Ø99 mm tipping cradle. Raise +14.6" → cradle rim ~22.3" clears the ~21.5" FLOWER mouth (§9.7); a micro servo tips the ball in. Travel hard-stop collars satisfy R105/G416.' },
  electronics: { label: 'Electronics',          color: '#d97c1e', explode: new THREE.Vector3(0, -3.2, 0),  desc: 'REV Control Hub on the belly pan + Expansion Hub face-mounted on the right-rail outer wall. Twin polycarb side decks span the tower bays (standoffs to the rail tops) with a small shelf over the left deck, 3000 mAh battery with straps and main switch, color sensor at hopper entry, full motor/servo wiring loom.' },
};

export function buildRobot() {
  const robot = new THREE.Group();
  robot.name = 'robot';
  const groups = {}, anim = { intake: [], feed: [], fly: [], launch: {}, wheels: [] };
  const entries = [];

  for (const id in SUBS) {
    groups[id] = new THREE.Group();
    groups[id].name = id;
    robot.add(groups[id]);
  }

  // register a placed part instance; repeated (sub, name) pairs merge into one
  // BOM line so clicking any instance shows the true total quantity.
  // parent overrides the subsystem group (e.g. the rotating turret), with
  // pos/rot expressed in that parent's local frame.
  function reg(sub, name, spec, qty, notes, obj, pos = [0, 0, 0], rot = [0, 0, 0], parent = null) {
    obj.position.set(...pos);
    if (rot[0]) obj.rotation.x = rot[0];
    if (rot[1]) obj.rotation.y = rot[1];
    if (rot[2]) obj.rotation.z = rot[2];
    let e = entries.find(x => x.sub === sub && x.name === name);
    if (!e) { e = { name, sub, spec, qty: 0, notes, objs: [] }; entries.push(e); }
    e.qty += qty;
    e.objs.push(obj);
    obj.userData.entry = e;
    (parent || groups[sub]).add(obj);
    return obj;
  }

  // closed-belt loop between two pulleys — a smooth GT-profile band
  // (viewer deviation: belt drawn as a tube, no tooth detail)
  function beltLoop(c1, r1, c2, r2, x = 0, linkR = 0.045) {
    const g = new THREE.Group();
    const dy = c2[0] - c1[0], dz = c2[1] - c1[1];
    const d = Math.hypot(dy, dz), base = Math.atan2(dz, dy);
    const phi = Math.acos(THREE.MathUtils.clamp((r1 - r2) / d, -0.98, 0.98));
    const a1 = base + phi, a2 = base - phi;
    const pt = (c, r, a) => [c[0] + Math.cos(a) * r, c[1] + Math.sin(a) * r];
    const ring = [];
    ring.push(pt(c1, r1, a1), pt(c2, r2, a1));
    const n2 = Math.max(6, Math.round(2 * phi / 0.22));
    for (let i = 1; i <= n2; i++) ring.push(pt(c2, r2, a1 + (i / n2) * (a2 - a1)));
    ring.push(pt(c1, r1, a2));
    const n1 = Math.max(8, Math.round((2 * Math.PI - 2 * phi) / 0.22));
    for (let i = 0; i <= n1; i++) ring.push(pt(c1, r1, a2 + (i / n1) * (a1 - 2 * Math.PI - a2)));
    const curve = new THREE.CatmullRomCurve3(
      ring.map(p => new THREE.Vector3(x, p[0], p[1])), true, 'catmullrom', 0.02);
    const m = new THREE.Mesh(new THREE.TubeGeometry(curve, 80, linkR, 6), M.rubber);
    m.castShadow = m.receiveShadow = true;
    g.add(m);
    return g;
  }

  /* ================= DRIVETRAIN ================= */
  // as-built: rails ±160 mm (x ±6.30), wheels at cad y ±203.2 (x ±8.0) z ±127 (z ∓5.0)
  const RAIL_X = 6.3, RAIL_Y = 1.57, WHEEL_Y = 1.89, WHEEL_X = 8.0, WHEEL_Z = 5.0;

  for (const s of [-1, 1]) {
    reg('drive', 'Side rail — U-channel', 'goBILDA-pattern low-side U-channel, 48 mm section, 6061-T6 anodized', 1,
      'Primary structure. 8 mm grid hole pattern; wheel axles pass through both rail faces on flange bearings.',
      P.channel(17.5), [s * RAIL_X, RAIL_Y, 0]);
    reg('drive', 'Motor mount plate', '3 mm 5052 aluminum', 1,
      'Mounts the drive motors to the rail inner face.',
      P.plateV(12.0, 1.9, 0.12, M.alu), [s * 5.3, 1.89, 0], [0, Math.PI / 2, 0]);
    // drive motors + shafts + wheels (wheels OUTBOARD of rails)
    for (const z of [-WHEEL_Z, WHEEL_Z]) {
      reg('drive', 'Drive motor — 5203 + UltraPlanetary', 'REV UltraPlanetary 5.2:1, 312 rpm output', 1,
        'Inboard motor drives the outboard wheel through a through-rail live axle — low CG, no chain slop.',
        P.driveMotor(3.8), [s * 3.37, WHEEL_Y, z], [0, s > 0 ? 0 : Math.PI, 0]);
      reg('drive', 'Wheel axle — 8 mm REX', '8 mm REX hex shaft, 6061', 1,
        'Through-rail live axle — rides flange bearings on both rail faces.',
        P.hexShaft(3.4), [s * 6.64, WHEEL_Y, z]);
      reg('drive', 'Flange bearing — rail', '8 mm REX flange bearing block', 1,
        'Pilots the live axle through the rail wall — one bearing on each rail face per wheel.',
        P.bearing(), [s * 5.53, WHEEL_Y, z], [0, s < 0 ? Math.PI : 0, 0]);
      reg('drive', 'Flange bearing — rail', '8 mm REX flange bearing block', 1,
        '', P.bearing(), [s * 7.07, WHEEL_Y, z], [0, s < 0 ? Math.PI : 0, 0]);
      const wheel = reg('drive', '96 mm mecanum wheel', 'goBILDA 96 mm mecanum, 11 rollers, 45° layout', 1,
        'Outboard of the rail for maximum track width; rollers handed per corner for true holonomic strafe.',
        P.mecanumWheel(1.89, 1.5, (s * z) > 0 ? 1 : -1), [s * WHEEL_X, WHEEL_Y, z], [0, 0, 0]);
      anim.wheels.push({ obj: wheel, r: 1.89 });
      reg('drive', 'Shaft collar', '8 mm clamping collar', 1,
        'Axial keeper beside the inboard bearing — takes thrust load off the pinion.',
        P.collar(), [s * 5.86, WHEEL_Y, z]);
      reg('drive', 'Axle nut — nylock', '8 mm nylock on the outboard shaft tip', 1,
        'Locks the axle tip outboard of the wheel; nylon insert resists vibration.',
        P.shaftNut(), [s * 8.85, WHEEL_Y, z]);
      reg('drive', 'Motor pinion — 15T brass', '15T brass spur on the output shaft', 1,
        'Transfers motor torque to the axle — brass wears better than acetal at this pitch.',
        P.pinion(0.34), [s * 6.13, WHEEL_Y, z]);
      reg('drive', 'Axle washer', '8 mm flat washer — bearing spacer', 1,
        'Shim — keeps the collar clear of the bearing seal.',
        P.washer(), [s * 5.72, WHEEL_Y, z]);
      // motor clamp saddles between motor and inner bearing (as-built CLAMP_y 115/127)
      for (const cx of [4.53, 5.0])
        reg('drive', 'Motor clamp block', 'split-ring clamp, M4 ear bolts', 1,
          'Two split-ring clamps grip each motor can — swap a motor without pulling the axle.',
          P.clampBlock(0.72), [s * cx, WHEEL_Y, z]);
    }
  }
  reg('drive', 'Rear crossmember — U-channel', '48 mm U-channel', 1, 'Closes the frame box; motor leads route inside.',
    P.channel(10.7), [0, RAIL_Y, 7.8], [0, Math.PI / 2, 0]);
  reg('drive', 'Front crown crossmember — raised', '48 mm U-channel', 1,
    'Raised above the intake rollers so the throat stays open — it doubles as the top roller spring mount.',
    P.channel(10.7), [0, 6.2, -7.8], [0, Math.PI / 2, 0]);
  // crown posts raise the front crossmember off the rail top flanges
  for (const s of [-1, 1])
    reg('drive', 'Crown riser post', '48 mm U-channel stub on the rail top flange', 1,
      'Lifts the crown channel to the top-roller height — the intake mouth clears 3.6" NECTAR.',
      P.channel(4.5), [s * 5.51, 4.78, -7.8], [-Math.PI / 2, 0, 0]);
  // rail end caps — pressed into every open channel end
  for (const s of [-1, 1]) for (const ez of [-8.69, 8.69])
    reg('drive', 'Rail end cap', 'press-fit HDPE cap', 1,
      'Press-fit plug — keeps swarf out of the channel and softens sharp rail ends.',
      P.endCap(), [s * RAIL_X, RAIL_Y, ez]);
  for (const s of [-1, 1]) {
    reg('drive', 'Rail end cap', 'press-fit HDPE cap', 1, '',
      P.endCap(), [s * 5.3, RAIL_Y, 8.33], [0, Math.PI / 2, 0]);
    reg('drive', 'Rail end cap', 'press-fit HDPE cap', 1, '',
      P.endCap(), [s * 5.3, 6.2, -7.8], [0, Math.PI / 2, 0]);
  }
  reg('drive', 'Belly pan', '3 mm polycarbonate, waterjet', 1,
    'Electronics mounting deck; stops ahead of the intake rollers.',
    P.plate(10.4, 12.95, 0.08, M.polycarbSolid), [0, 1.05, 0.37]);
  // belly-pan mounting brackets — 3 per side along the rail inner faces
  for (const s of [-1, 1]) for (const z of [0.43, 1.57, 2.76])
    reg('drive', 'Belly pan bracket', 'formed sheet bracket, pan to rail', 1,
      'Screws the belly pan to the rail inner face grid.',
      P.plateV(1.71, 0.36, 1.1, M.alu), [s * 4.5, 0.83, z], [0, Math.PI / 2, 0]);
  // rear corner gussets (as-built: stacked pair each rear corner)
  for (const s of [-1, 1]) for (const y of [0.79, 1.79]) {
    reg('drive', 'Corner gusset', '48 mm inside-corner bracket', 1,
      'Stiffens the frame square at the rear rail joints — resists racking under strafe loads.',
      P.gusset(1.4, 1.4, 0.08, M.accent), [s * 4.59, y, 7.31], [0, s > 0 ? 0 : Math.PI, 0]);
  }
  // odometry pods — placement comes from reg()'s pos arg (reg overwrites obj.position)
  const pod = (axisZ) => {
    const g = new THREE.Group();
    const arm = P.plate(0.5, 1.9, 0.08, M.accent); arm.rotation.x = axisZ ? 0 : Math.PI / 2;
    arm.position.y = 0.6; g.add(arm);
    const w = P.omniWheel(0.95); w.position.set(0, -0.15, axisZ ? -0.5 : 0);
    if (!axisZ) w.rotation.y = Math.PI / 2;
    g.add(w);
    const spr = P.springHelix(0.2, 0.7, 4); spr.position.y = 1.15; g.add(spr);
    const enc = P.plateV(0.8, 0.8, 0.12, M.pcb); enc.position.set(0, 0.9, axisZ ? 0.35 : 0); g.add(enc);
    return g;
  };
  reg('drive', 'Odometry pod — lateral', '48 mm omni dead-wheel + encoder, sprung', 1,
    'Tracks forward/back travel; spring-loaded to stay planted on foam tiles.',
    pod(false), [-4.6, 1.0, -1.2]);
  reg('drive', 'Odometry pod — lateral', '48 mm omni dead-wheel + encoder, sprung', 1,
    '', pod(false), [4.6, 1.0, -1.2]);
  reg('drive', 'Odometry pod — longitudinal', '48 mm omni dead-wheel + encoder, sprung', 1,
    'Measures strafe — third leg of the pose estimator.',
    pod(true), [0, 1.0, 6.3]);
  // team number plates — rear rail face + left rail face (adjacent sides)
  reg('drive', 'Alliance number plate — rear', '0.8 mm PETG + vinyl numerals', 1,
    'Required on two adjacent sides; swap red/blue per alliance.',
    P.numberPlate(3.6, 2.4), [0, 1.31, 8.79]);
  reg('drive', 'Alliance number plate — left', '0.8 mm PETG + vinyl numerals', 1,
    'Second required plate — on a side adjacent to the rear plate per game rules.',
    P.numberPlate(3.6, 2.4), [-7.28, 1.31, 0], [0, -Math.PI / 2, 0]);
  // rail bolts
  {
    const boltInst = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.07, 0.07, 0.1, 8), M.bolt, 24);
    const m4 = new THREE.Matrix4(); let i = 0;
    for (const s of [-1, 1]) for (const z of [-7.8, 7.8]) for (const y of [1.0, 2.1]) {
      m4.makeTranslation(s * 7.28, y, z); boltInst.setMatrixAt(i++, m4);
      m4.makeTranslation(s * 5.3, y, z * 0.94); boltInst.setMatrixAt(i++, m4);
    }
    // raised front crown member — same bolt pair pattern at its junction
    for (const s of [-1, 1]) for (const y of [5.6, 6.8]) {
      m4.makeTranslation(s * 7.28, y, -7.8); boltInst.setMatrixAt(i++, m4);
      m4.makeTranslation(s * 5.3, y, -7.8); boltInst.setMatrixAt(i++, m4);
    }
    boltInst.count = i;
    reg('drive', 'Frame hardware — M4 socket head', 'M4×8 socket-head cap screws + nylock', 24,
      'Pattern bolts across every rail junction.', boltInst);
  }

  /* ================= INTAKE ================= */
  // as-built: cheeks at cad y ±123.5 (x ∓4.86), bottom roller (0,1.45,-7.48),
  // star roller behind+above at (0,6.89,-5.24), #25 chain + GT belt cross-drive
  for (const s of [-1, 1]) {
    reg('intake', 'Intake cheek plate', '5 mm PETG, CNC routed', 1,
      'Spring posts for the floating top roller; slot allows the roller its compliance travel for NECTAR.',
      P.plateV(3.31, 7.64, 0.14, M.print), [s * 4.86, 4.41, -5.99], [0, Math.PI / 2, 0]);
    reg('intake', 'Torsion spring — floating roller', 'music-wire torsion spring', 1,
      'Preloads the star roller down onto incoming balls; deflects upward for 3.6" NECTAR.',
      P.springHelix(0.28, 0.55, 5), [s * 5.39, 7.78, -5.49]);
    reg('intake', 'Spring post', '8 mm spring boss on the cheek', 1,
      'Torsion-spring leg post — sets the star-roller preload.',
      P.pillar(0.31, 0.16, M.darkSteel), [s * 5.39, 7.91, -5.51]);
    reg('intake', 'Intake pivot pin', '8 mm shoulder pin, cheek to crown post', 1,
      'Cheeks pivot on these pins so the whole intake can kick up for service.',
      P.collar(), [s * 5.45, 1.18, -6.69]);
    // floating-roller slide block riding the cheek slot
    reg('intake', 'Float slide block', 'acetal slider on the star-roller shaft', 1,
      'Slides in the cheek slot — gives the top roller its compliance travel.',
      P.plateV(0.55, 1.18, 0.17, M.printGray), [s * 5.14, 6.89, -5.24]);
    reg('intake', 'Cheek float slot', 'routed slot in the cheek plate', 1,
      'Vertical travel path for the floating shaft — bounds the give.',
      P.plateV(0.36, 2.8, 0.05, M.holeDark), [s * 4.94, 5.9, -5.24]);
  }
  const rollerB = reg('intake', 'Traction roller', '2" rubberized roller, ribbed grip surface', 1,
    'First contact — pulls POLLEN off the tile. Surface speed matched to ~1.4× drive speed.',
    P.tractionRoller(1.0, 10.0), [0, 1.45, -7.48]);
  const rollerT = reg('intake', 'Compliant star roller', '9× 6-point silicone stars on 8 mm REX', 1,
    'Conforms to ball tops; star phases offset so there is always contact. Sits behind+above the bottom roller — balls funnel under it.',
    P.starRoller(1.55, 10.0), [0, 6.89, -5.24]);
  anim.intake.push({ obj: rollerB, speed: 9 }, { obj: rollerT, speed: -9 });
  reg('intake', 'Intake motor — compact 5203', '312 rpm, #25 chain drive', 1,
    'Mounted under the hopper incline; chain runs outboard of the right cheek.',
    P.compactMotor(), [4.06, 1.69, -2.99]);
  reg('intake', 'Motor clamp — compact', 'split-ring clamp on the motor can', 1,
    'Grips the motor can at the belly standoffs — swap without pulling the sprocket.',
    P.clampBlock(0.72), [3.0, 1.69, -2.99]);
  reg('intake', 'Intake motor shaft', '8 mm REX hex, through rail wall', 1,
    'Short jackshaft carrying motor power through the rail wall to the sprocket.',
    P.hexShaft(1.78), [6.15, 1.69, -2.99]);
  reg('intake', 'Intake drive sprocket — 9T', '#25 steel sprocket', 1,
    'Driver — small sprocket trades speed for torque into the roller loop.',
    P.spurGear(9, 0.45, 0.15), [6.46, 1.69, -2.99], [0, 0, Math.PI / 2]);
  reg('intake', 'Intake driven sprocket — 16T', '#25 steel sprocket, outboard of cheek', 1,
    'Driven sprocket on the roller shaft — ~1.8:1 reduction from the motor.',
    P.spurGear(16, 0.72, 0.15), [6.46, 1.45, -7.48], [0, 0, Math.PI / 2]);
  reg('intake', 'Intake chain — #25', 'steel roller chain loop outside the right cheek', 1,
    'Continuous loop linking the motor sprocket to the roller shaft.',
    P.chainLoop([1.69, -2.99], 0.5, [1.45, -7.48], 0.8, 6.46));
  reg('intake', 'Chain guard', '2 mm polycarb cover over the chain run', 1,
    'Keeps fingers and game elements out of the chain pinch point.',
    P.plateV(0.08, 1.65, 5.71, M.polycarbSolid), [7.11, 1.38, -5.61]);
  reg('intake', 'Chain master link', 'clip-style connecting link on the #25 loop', 1,
    'Removable service link — bright side plates mark it on the straight run.',
    P.plateV(0.31, 0.2, 0.1, M.alu), [6.46, 1.51, -5.74], [0.11, 0, 0]);
  reg('intake', 'Intake drive shaft', '8 mm REX hex, full width', 1,
    'Full-width axle both rollers key into — carries torque across to the far cheek.',
    P.hexShaft(13.3), [0, 1.45, -7.48]);
  reg('intake', 'Star roller shaft', '8 mm REX hex, full width', 1,
    'Floating shaft the star roller rides on — ends slide in the cheek slots.',
    P.hexShaft(12.6), [-0.46, 6.89, -5.24]);
  // GT-belt cross-drive on the LEFT cheek — bottom roller drives the star roller
  // counter-rotating. Viewer deviation: belt drawn as a smooth tube, no teeth.
  reg('intake', 'Roller belt pulley — GT', 'GT-profile pulley on the roller shafts', 1,
    'Bottom shaft drives the star roller counter-rotating — both pull balls inward.',
    P.spurGear(20, 0.85, 0.18, M.darkSteel), [-6.1, 1.45, -7.48], [0, 0, Math.PI / 2]);
  reg('intake', 'Roller belt pulley — GT', 'GT-profile pulley on the roller shafts', 1, '',
    P.spurGear(20, 0.85, 0.18, M.darkSteel), [-6.1, 6.89, -5.24], [0, 0, Math.PI / 2]);
  reg('intake', 'Roller cross-belt — GT loop', 'toothed belt, left cheek', 1,
    'Syncs the top roller to the bottom shaft — opposite rotation via wrap side.',
    beltLoop([1.45, -7.48], 0.9, [6.89, -5.24], 0.9, -6.1));
  reg('intake', 'Belt tensioner — idler', 'spring-loaded idler on the belt span', 1,
    'Takes up belt slack so the cross-drive never skips under the float travel.',
    P.pulley(0.59), [-6.1, 4.17, -6.69]);
  reg('intake', 'Belt tensioner — arm + spring', 'pivot arm + torsion spring', 1,
    'Loads the idler into the belt span.',
    P.plateV(0.63, 1.5, 0.2, M.accent), [-4.94, 3.82, -6.61], [0.3, 0, 0]);
  reg('intake', 'Belt tensioner — spring', 'torsion spring loading the idler arm', 1, '',
    P.springHelix(0.25, 0.5, 4), [-5.22, 3.41, -6.69], [Math.PI / 2, 0, 0]);
  reg('intake', 'Cheek flange bearing', '8 mm flange bearing', 1,
    'Supports each roller shaft in the cheek plate — one bearing per shaft end.',
    P.bearing(), [5.53, 1.45, -7.48]);
  reg('intake', 'Cheek flange bearing', '8 mm flange bearing', 1, '',
    P.bearing(), [-5.53, 1.45, -7.48], [0, Math.PI, 0]);
  reg('intake', 'Throat guard plate', '2 mm polycarbonate cover over the mouth', 1,
    'Caps the throat above the star roller — keeps ball containment inside the 18" frame line.',
    P.plate(8.66, 1.97, 0.08, M.polycarbSolid), [0, 7.19, -7.76]);

  /* ================= HOPPER ================= */
  // inclined floor (~21°) — ends ahead of the column mouth
  reg('hopper', 'Hopper floor — incline', '3 mm polycarbonate, ~21° incline', 1,
    'Balls stage single-file and roll toward the feed column.',
    P.plate(4.21, 4.0, 0.09, M.polycarbSolid), [0, 3.45, -2.3], [0.37, 0, 0]);
  reg('hopper', 'Hopper apron', '3 mm polycarbonate lip under the floor', 1,
    'Closes the gap under the incline leading edge.',
    P.plate(3.7, 1.97, 0.12, M.polycarbSolid), [0, 2.7, 0.59]);
  reg('hopper', 'Hopper side wall — left', '3 mm polycarbonate', 1,
    'Clear walls keep balls channelled single-file while jams stay visible.',
    P.plateV(4.39, 4.33, 0.12, M.polycarbSolid), [-2.3, 4.92, -1.43], [0, Math.PI / 2, 0]);
  reg('hopper', 'Hopper side wall — right', '3 mm polycarbonate', 1,
    'Long right wall reaches back to the column.',
    P.plateV(6.5, 4.33, 0.12, M.polycarbSolid), [2.3, 4.92, -0.37], [0, Math.PI / 2, 0]);
  for (const s of [-1, 1])
    reg('hopper', 'Hopper ledge', 'retaining ledge over the floor incline', 1,
      'Keeps stacked balls from rolling back over the incline crest.',
      P.plateV(0.39, 2.0, 5.22, M.polycarbSolid), [s * 2.05, 3.58, -2.85]);
  reg('hopper', 'Hopper rear curb', '3 mm polycarbonate', 1,
    'Low curb sealing the gap under the column mouth — the tube shell is the rear stop.',
    P.plateV(4.72, 0.94, 0.12, M.polycarbSolid), [-0.18, 4.02, 2.7]);
  for (const s of [-1, 1]) for (const z of [-0.28, -3.27])
    reg('hopper', 'Hopper wall bracket', 'inside-corner bracket to the deck', 1,
      'Ties the clear walls down to the deck plates.',
      P.gusset(0.55, 1.0, 0.08, M.accent), [s * 2.68, 3.27, z]);
  // agitator paddle + servo (bracket-mounted on the right wall)
  const agit = new THREE.Group();
  {
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.5, 12).rotateZ(Math.PI / 2), M.printGray);
    hub.castShadow = true; agit.add(hub);
    for (let i = 0; i < 3; i++) {
      const blade = new THREE.Mesh(new THREE.BoxGeometry(0.42, 1.5, 0.12), M.print);
      blade.castShadow = true;
      const hold = new THREE.Group(); hold.add(blade);
      blade.position.y = 0.85;
      hold.rotation.x = (i / 3) * Math.PI * 2;
      agit.add(hold);
    }
  }
  reg('hopper', 'Agitator paddle', '3-arm PETG paddle', 1,
    'Sweeps the low corner so balls can\'t bridge over the feed nip.',
    agit, [1.69, 4.92, -2.5]);
  anim.agitator = agit;
  reg('hopper', 'Agitator servo', 'standard servo, 180°', 1,
    'Oscillates the paddle ±45° at the low corner — breaks bridges over the feed nip.',
    P.servoMotor(), [2.78, 4.55, -2.6], [0, 0, Math.PI / 2]);
  reg('hopper', 'Agitator servo bracket', 'servo ear bracket on the right wall', 1,
    'Mounts the agitator servo flush to the wall.',
    P.plateV(1.02, 1.18, 0.12, M.alu), [2.42, 4.55, -2.6]);
  reg('hopper', 'Agitator drive horn', 'servo horn bar to the paddle shaft', 1,
    'Clamp-fit horn linking the servo spline to the paddle shaft.',
    P.plate(0.5, 0.08, 0.14, M.alu), [1.87, 4.55, -2.6]);
  // feed wheel + column
  const feedW = reg('hopper', 'Feed wheel — compliant', '3.2" green compliant wheel', 1,
    'Meters one ball per rev-segment into the column; compliance handles both POLLEN and NECTAR.',
    P.compliantWheel(1.6, 0.9), [0, 5.15, 1.45], [0, 0, Math.PI / 2]);
  feedW.rotation.order = 'ZYX';
  anim.feed.push({ obj: feedW, speed: 6 });
  reg('hopper', 'Feed motor — compact 5203', '435 rpm, on belly stand-offs', 1,
    'Parallel-shaft drive: drops power to the feed axle through a 28T gear pair — clears the hopper wall and feed column.',
    P.compactMotor(), [4.03, 2.8, 1.45], [0, Math.PI, 0]);
  reg('hopper', 'Feed motor mount plate', '3 mm aluminum standoff plate', 1,
    'Standoffs bolt the feed motor below the incline.',
    P.plateV(1.73, 1.1, 0.12, M.alu), [3.28, 2.74, 1.45], [0, Math.PI / 2, 0]);
  for (const z of [0.5, 2.39])
    reg('hopper', 'Feed motor standoff', 'M3 standoff pair', 1,
      'Lifts the feed motor into mesh with the 28T gear pair.',
      P.pillar(0.8, 0.18, M.alu), [3.31, 1.49, z]);
  reg('hopper', 'Motor clamp — compact', 'split-ring clamp on the motor can', 1,
    'Clamps the feed motor to its standoff posts.',
    P.clampBlock(0.72), [3.0, 2.8, 1.45]);
  reg('hopper', 'Feed spur gear — 28T', '15 DP acetal, 1:1 drop pair', 1,
    'On the feed axle; meshes the motor pinion below.',
    P.spurGear(28, 1.18, 0.22), [2.49, 5.15, 1.45], [0, 0, Math.PI / 2]);
  reg('hopper', 'Feed spur gear — 28T', '15 DP acetal, 1:1 drop pair', 1, '',
    P.spurGear(28, 1.18, 0.22), [2.49, 2.8, 1.45], [0, 0, Math.PI / 2]);
  reg('hopper', 'Feed shaft — 8 mm REX', 'through-wall drive shaft', 1,
    'Carries the feed wheel through the hopper wall on a flange bearing.',
    P.hexShaft(4.5), [0.9, 5.15, 1.45]);
  reg('hopper', 'Feed wall bearing', '8 mm flange bearing', 1,
    'Supports the feed shaft where it exits the hopper wall.',
    P.bearing(), [2.17, 5.15, 1.45]);
  reg('hopper', 'Feed guide scoop', 'wide flat shroud over the nip', 1,
    'Keeps the ball seated through the lift arc into the column mouth.',
    P.plate(4.72, 0.69, 0.39, M.print), [0, 6.89, -0.22]);
  // ---- feed column: Ø110 mm clear tube, z 88–254 (viewer y 3.46–10.0) ----
  // windows as-built: feed wheel on the -Z face, gate slot on +X, diverter
  // port on -X. Viewer deviation: windows approximated with open theta arcs.
  reg('hopper', 'Feed column — clear 4"', '4" ID clear polycarbonate tube', 1,
    'Rises through the turret axis — ammo feed is independent of yaw. Shell is windowed for the feed wheel, gate slot, and the lift port.',
    (() => {
      const R = 2.17, g = new THREE.Group();
      const wall = (y0, y1, thetaStart, thetaLen) => {
        const m = new THREE.Mesh(new THREE.CylinderGeometry(R, R, y1 - y0, 28, 1, true, thetaStart, thetaLen), M.tube);
        m.position.y = (y0 + y1) / 2;
        return m;
      };
      // theta: x = r·sinθ, z = r·cosθ — gap arcs centered on each face
      g.add(wall(3.46, 5.1, Math.PI + 0.6, Math.PI * 2 - 1.2));       // feed wheel window -Z
      g.add(wall(5.1, 6.5, 0, Math.PI * 2));                          // solid band
      g.add(wall(6.5, 7.4, Math.PI / 2 + 0.5, Math.PI * 2 - 1.0));    // gate slot +X
      g.add(wall(7.4, 8.7, -Math.PI / 2 + 0.55, Math.PI * 2 - 1.1));  // diverter port -X
      g.add(wall(8.7, 10.0, 0, Math.PI * 2));                         // to the deck bore
      const lip = new THREE.Mesh(new THREE.TorusGeometry(R + 0.02, 0.07, 8, 28).rotateX(Math.PI / 2), M.accent);
      lip.position.y = 3.5; lip.castShadow = true; g.add(lip);
      const lip2 = lip.clone(); lip2.position.y = 9.95; g.add(lip2);
      return g;
    })(), [0, 0, 2.6]);
  reg('hopper', 'Column base flange', 'machined plate + ring clamping the tube to the deck', 1,
    'Clamps the tube square to the deck — sets the column vertical through the turret axis.',
    (() => {
      const g = new THREE.Group();
      g.add(P.plate(6.3, 4.17, 0.16, M.alu));
      const ring = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.09, 8, 32).rotateX(Math.PI / 2), M.alu);
      ring.position.y = 0.12; ring.castShadow = true;
      g.add(ring);
      return g;
    })(), [0, 3.54, 2.68]);
  for (const s of [-1, 1]) for (const z of [3.15, 3.98])
    reg('hopper', 'Column standoff post', 'M3 standoff pair under the flange', 1,
      'Posts the column flange off the deck plates.',
      P.pillar(2.37, 0.18, M.alu), [s * 2.99, 2.28, z]);
  // gate: servo flag meters the column mouth between shots (as-built on the +X face)
  reg('hopper', 'Gate servo + flag', 'micro servo, one-ball metering flag', 1,
    'Closes the column mouth between shots so flywheel recovery isn\'t wasted — flag swings through the -Y shell slot.',
    (() => {
      const g = P.servoMotor();
      const flag = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.08, 1.69), M.accent);
      flag.position.set(-0.6, 0.62, 0.1); flag.castShadow = true;
      g.add(flag);
      return g;
    })(), [2.62, 6.85, 1.18], [0, 0, Math.PI / 2]);
  reg('hopper', 'Gate servo bracket', 'servo ear bracket on the shell', 1,
    'Mounts the gate servo beside the -Y shell slot.',
    P.plateV(1.65, 0.79, 0.12, M.alu), [2.42, 6.85, 1.14]);
  reg('hopper', 'Gate horn', 'servo horn into the flag', 1,
    'Horn bar driving the metering flag through the shell slot.',
    P.plateV(0.31, 1.22, 0.31, M.alu), [1.71, 6.85, 1.18]);
  // diverter train: servo + shaft + flap inside the column, band bracket on +Y wall
  reg('hopper', 'Diverter band bracket', 'clamped band on the column', 1,
    'Anchor ring the diverter servo mounts on.',
    P.plate(4.53, 2.76, 0.39, M.accent), [-0.06, 5.31, 3.54]);
  reg('hopper', 'Diverter servo', 'micro servo on the column band', 1,
    'Positions the Y-flap — launch vs lift routing decided here.',
    P.servoMotor(), [-2.58, 5.35, 2.6], [0, 0, Math.PI / 2]);
  reg('hopper', 'Diverter shaft', '5 mm pivot shaft through the +Y wall', 1,
    'Carries the flap pivot across the bore.',
    P.hexShaft(1.3), [-1.75, 5.35, 2.6]);
  reg('hopper', 'Column diverter — Y flap', 'servo flap inside the column', 1,
    'Launch mode: flap parked, balls continue to the nip. Lift mode: kicks the ball out the -X port below the deck.',
    P.plateV(0.12, 1.89, 1.42, M.accent), [-1.79, 4.41, 2.6]);
  // ball staged inside the clear column — visible through the tube
  reg('hopper', 'POLLEN (in column)', 'Ø2.8" element queued at the gate flag', 1,
    'Static staged ball — hidden during the match demo while real feeds run through.',
    P.ball(1.4, M.pollen), [0, 6.55, 2.6]);
  reg('hopper', 'Entry color sensor', 'I2C color/proximity sensor on the right wall', 1,
    'Counts balls in, identifies NECTAR vs POLLEN for shot-speed lookup.',
    P.plateV(0.79, 0.59, 0.1, M.pcb), [2.08, 3.39, -3.78]);

  /* ================= TURRET (static) ================= */
  // tower side plates + deck — as-built z-stack:
  //   deck 244–248 → viewer y 9.61–9.76   susan 248–256.5 → 9.76–10.10
  //   ring gear 256.5–263 → 10.10–10.35   plate 263–267 → 10.35–10.51
  for (const s of [-1, 1]) {
    reg('turret', 'Tower cheek', '3 mm polycarbonate tower riser (formed — flanges not shown)', 1,
      'Vertical risers forming the tower bay — carry the deck and electronics shelf.',
      P.plateV(6.93, 6.19, 0.12, M.polycarbSolid), [s * 4.68, 6.51, 3.46], [0, Math.PI / 2, 0]);
    for (const z of [0.51, 6.42])
      reg('turret', 'Tower gusset', 'inside-corner bracket, cheek to deck', 1,
        'Triangulates the cheek-to-deck joint against launch recoil.',
        P.gusset(1.0, 1.57, 0.08, M.print), [s * 4.64, 4.21, z]);
  }
  reg('turret', 'Turret deck', '4 mm PETG deck plate', 1,
    'Carries the lazy susan races; Ø114 mm bore passes the feed column, second bore passes the yaw pinion shaft.',
    (() => {
      const s = new THREE.Shape();
      s.moveTo(-5.35, -3.78); s.lineTo(5.35, -3.78); s.lineTo(5.35, 3.78); s.lineTo(-5.35, 3.78); s.closePath();
      const hole = new THREE.Path(); hole.absarc(0, -0.79, 2.24, 0, Math.PI * 2, true); s.holes.push(hole);
      const hole2 = new THREE.Path(); hole2.absarc(2.87, -0.79, 0.2, 0, Math.PI * 2, true); s.holes.push(hole2);
      const geo = new THREE.ExtrudeGeometry(s, { depth: 0.16, bevelEnabled: false });
      geo.rotateX(-Math.PI / 2);
      const m = new THREE.Mesh(geo, M.print); m.castShadow = m.receiveShadow = true;
      const g = new THREE.Group(); g.add(m);
      return g;
    })(), [0, 9.69, 3.39]);
  // split lazy-susan races — lower race z 248–252.3, upper race 252.3–256.5
  reg('turret', 'Lazy susan race — lower', 'Ø132 mm ball-bearing ring, lower race', 1,
    'Bottom race of the split bearing — bolted to the static deck.',
    (() => {
      const s = new THREE.Shape(); s.absarc(0, 0, 2.6, 0, Math.PI * 2);
      const hole = new THREE.Path(); hole.absarc(0, 0, 2.28, 0, Math.PI * 2, true); s.holes.push(hole);
      const geo = new THREE.ExtrudeGeometry(s, { depth: 0.167, bevelEnabled: false });
      geo.rotateX(-Math.PI / 2);
      const m = new THREE.Mesh(geo, M.alu); m.castShadow = m.receiveShadow = true;
      return m;
    })(), [0, 9.85, 2.6]);
  reg('turret', 'Lazy susan race — upper', 'Ø132 mm ball-bearing ring, upper race', 1,
    'Top race of the split bearing — carries the rotating plate.',
    (() => {
      const g = new THREE.Group();
      const s = new THREE.Shape(); s.absarc(0, 0, 2.6, 0, Math.PI * 2);
      const hole = new THREE.Path(); hole.absarc(0, 0, 2.28, 0, Math.PI * 2, true); s.holes.push(hole);
      const geo = new THREE.ExtrudeGeometry(s, { depth: 0.167, bevelEnabled: false });
      geo.rotateX(-Math.PI / 2);
      const m = new THREE.Mesh(geo, M.alu); m.castShadow = m.receiveShadow = true;
      g.add(m);
      const ballGeo = new THREE.SphereGeometry(0.11, 10, 8);
      const balls = new THREE.InstancedMesh(ballGeo, M.steel, 20);
      const m4 = new THREE.Matrix4();
      for (let i = 0; i < 20; i++) {
        const a = (i / 20) * Math.PI * 2;
        m4.makeTranslation(Math.cos(a) * 2.45, -0.08, Math.sin(a) * 2.45);
        balls.setMatrixAt(i, m4);
      }
      g.add(balls);
      return g;
    })(), [0, 10.02, 2.6]);
  // yaw servo at -Y of the turret axis (viewer +X side) — pinion center distance 72.8 mm
  reg('turret', 'Yaw servo — continuous', 'dual-mode continuous-rotation servo', 1,
    'Under-deck tray mount: output shaft rises through the deck bore to drive the 14T pinion → ~190°/s slew with encoder homing.',
    (() => {
      const g = new THREE.Group();
      g.add(P.servoMotor());
      const tray = P.plate(1.54, 2.2, 0.12, M.alu);
      tray.position.set(0.11, -0.49, 0);
      g.add(tray);
      return g;
    })(), [2.85, 8.83, 2.6], [0, 0, Math.PI / 2]);
  reg('turret', 'Yaw pinion shaft', '8 mm REX through the deck bore', 1,
    'Servo output shaft rising to the pinion.',
    P.pillar(1.28, 0.157, M.steel), [2.87, 9.69, 2.6]);
  reg('turret', 'Yaw pinion — 14T', '15 DP brass on REX shaft', 1,
    'External mesh on the ring outer rim — 72.8 mm center distance, teeth engage the ring outside diameter.',
    (() => {
      const g = new THREE.Group();
      g.add(P.spurGear(14, 0.55, 0.24));
      const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.5, 6), M.steel);
      sh.position.y = -0.22; sh.castShadow = true;
      g.add(sh);
      return g;
    })(), [2.87, 10.23, 2.6]);
  // yaw homing: magnet on the plate rim sweeps a hall sensor on the deck
  reg('turret', 'Hall sensor — yaw index', 'magnetic reed on the static deck', 1,
    'Index pulse homes the turret yaw encoder each boot.',
    P.plateV(0.63, 0.31, 0.2, M.pcb), [2.87, 9.86, 1.44]);

  /* ================= LAUNCHER (rotating) ================= */
  const turret = new THREE.Group();          // rotates about Y at (0,0,2.6)
  turret.position.set(0, 0, 2.6);
  groups.launcher.add(turret);
  anim.turret = turret;
  {
    reg('launcher', 'Turret ring gear — 72T', '15 DP acetal ring, external teeth on the outer rim', 1,
      '5.14:1 with the servo pinion on a 72.8 mm center distance; homed against an index magnet. Viewer deviation: tooth profile simplified.',
      P.ringGear(2.42, 72, 0.26, 2.3), [0, 10.23, 0], [0, 0, 0], turret);
    // rotating plate — obround 170×224 mm with Ø114 bore (approximated as ellipse)
    const plateShape = new THREE.Shape();
    plateShape.absellipse(0, 0, 4.41, 3.35, 0, Math.PI * 2);
    const ph = new THREE.Path(); ph.absarc(0, 0, 2.24, 0, Math.PI * 2, true);
    plateShape.holes.push(ph);
    const pg = new THREE.ExtrudeGeometry(plateShape, { depth: 0.16, bevelEnabled: false });
    pg.rotateX(-Math.PI / 2);
    const tplate = new THREE.Mesh(pg, M.accent); tplate.castShadow = tplate.receiveShadow = true;
    reg('launcher', 'Turret rotating plate', '4 mm acetal plate, ~170×224 mm', 1,
      'Everything above this line rotates together. Viewer deviation: obround plate drawn as an ellipse.',
      tplate, [0, 10.43, 0], [0, 0, 0], turret);

    // cheek plates on rotating plate
    for (const s of [-1, 1]) {
      reg('launcher', 'Launcher cheek plate', '5 mm PETG (flange bosses not shown)', 1, 'Flywheel + hood bearing mounts.',
        P.plateV(2.99, 4.41, 0.12, M.print), [s * 2.81, 12.72, 0.24], [0, Math.PI / 2, 0], turret);
      reg('launcher', 'Flywheel motor — 5203', '6000 rpm class, 1:1 to wheel', 1,
        'Independent left/right speed control trims lateral spin → straight shots at range.',
        P.compactMotor(), [s * 3.23, 12.15, 0.55], [0, s < 0 ? 0 : Math.PI, 0], turret);
      reg('launcher', 'Flywheel motor clamp', 'wide clamp plate to the cheek', 1,
        'Straps the flywheel motor can to the launcher cheek — no slop at launch rpm.',
        P.plateV(2.13, 0.94, 0.63, M.alu), [s * 3.62, 10.98, 0.55], [0, Math.PI / 2, 0], turret);
      const fw = P.flywheel(1.75, 0.72);
      fw.rotation.order = 'ZYX';
      reg('launcher', 'Flywheel — 3.5"', 'balanced aluminum + urethane tread band', 1,
        'Counter-rotating pair; 73.7 mm nip compresses NECTAR ~19% for grip.',
        fw, [s * 1.81, 12.15, 0.55], [0, 0, Math.PI / 2], turret);
      anim.fly.push({ obj: fw, speed: s * 34 });
      reg('launcher', 'Flywheel shaft — 8 mm REX', 'short axle through the cheek bearings', 1,
        'Carries each flywheel across the cheek.',
        P.hexShaft(0.9), [s * 2.19, 12.15, 0.55], [0, 0, 0], turret);
      reg('launcher', 'Flywheel bearing', '8 mm flange bearing', 1,
        'Supports each flywheel shaft outboard of the cheek — takes the nip side-load.',
        P.bearing(), [s * 2.48, 12.15, 0.55], [0, s < 0 ? Math.PI : 0, 0], turret);
      reg('launcher', 'Flywheel shaft collar', '8 mm clamping collar', 1,
        'Keeps each wheel indexed on its shaft.',
        P.collar(), [s * 2.06, 12.15, 0.55], [0, 0, 0], turret);
    }
    // hood — nearly flat as-built, pivots at rear of cheeks (hood_piv z 359 → y 14.13)
    const hood = new THREE.Group();
    const hoodPlate = new THREE.Mesh(new THREE.BoxGeometry(6.0, 0.1, 4.0), M.accent);
    hoodPlate.castShadow = hoodPlate.receiveShadow = true;
    hoodPlate.position.z = -1.55;
    hood.add(hoodPlate);
    const hoodLip = new THREE.Mesh(new THREE.BoxGeometry(6.0, 0.5, 0.09), M.accent);
    hoodLip.position.set(0, 0.22, -3.45); hoodLip.castShadow = true;
    hood.add(hoodLip);
    reg('launcher', 'Adjustable hood', '2 mm anodized aluminum, servo-linked', 1,
      'Exit angle 40–65°: shallow lob for the HIVE cell, steep drop for FLOWER tops. Rides nearly flat as-built.',
      hood, [0, 14.13, 1.35], [-0.26, 0, 0], turret);
    anim.hood = hood;
    reg('launcher', 'Hood servo', 'standard servo', 1,
      'Positions the hood through the linkage — holds exit angle under launch vibration.',
      P.servoMotor(), [2.99, 13.56, 0.69], [0, 0, 0], turret);
    reg('launcher', 'Hood linkage', 'steel pushrod', 1,
      'Rigid pushrod — servo horn to hood pivot, no compliance in the aim path.',
      P.plate(0.08, 1.2, 0.06, M.steel), [3.13, 13.94, 0.88], [0.6, 0, 0], turret);
    // turret wiring — service loops droop toward the slip ring
    for (const s of [-1, 1])
      reg('electronics', 'Flywheel motor lead — on turret', '18 AWG pair, service loop', 1,
        'Droops through the slip ring throat — slack sized for unlimited yaw.',
        P.wireBundle([[s * 3.0, 11.8, 0.7], [s * 2.4, 10.6, -0.4], [s * 1.5, 9.6, -1.15]],
          [M.wireRed, M.wireBlack], 0.04, 0.08), [0, 0, 0], turret);
    reg('electronics', 'Hood servo lead — on turret', '22 AWG PWM, service loop', 1,
      'PWM lead routed alongside the flywheel service loop into the slip ring.',
      P.wireBundle([[2.99, 13.5, 0.7], [2.6, 11.5, 0.0], [2.0, 10.0, -1.0]]), [0, 0, 0], turret);
    // backplate behind nip — guides ball from column into nip
    reg('launcher', 'Nip backplate', 'curved ball guide (shown flat)', 1,
      'Directs the rising ball into the flywheel nip.',
      P.plateV(4.25, 1.93, 0.55, M.printGray), [0, 11.48, 2.28], [-0.25, 0, 0], turret);
    // camera on turret — front lip, lens faces the -Z exit direction, pitched up at the hive
    reg('launcher', 'Vision camera', 'global-shutter USB camera', 1,
      'Rides the turret — always faces the launch target. Reads CELL AprilTags for range + tip state.',
      P.webcam(), [0, 11.34, -2.37], [0.55, Math.PI, 0], turret);
    reg('launcher', 'Camera mount', 'printed bracket on the plate', 1,
      'Stands the camera off the rotating plate.',
      P.plate(0.79, 0.91, 0.55, M.print), [0, 10.79, -0.22], [0, 0, 0], turret);
    reg('launcher', 'Camera status LED', 'amber indicator', 1,
      'Streaming/exposure indicator readable from the pit side.',
      P.ledDot(0.05, M.ledOrange), [0, 11.65, -2.09], [0.55, 0, 0], turret);
    // index magnet rides the rotating plate rim — sweeps the hall sensor
    reg('launcher', 'Yaw index magnet', 'Ø6 mm neodymium in the plate edge', 1,
      'Trips the deck hall sensor once per revolution — turret homing reference.',
      P.pillar(0.53, 0.09, M.portWhite), [2.87, 10.25, -1.16], [0, 0, 0], turret);
    // hood pivot hardware on both cheeks + top stiffener bar
    for (const s of [-1, 1]) {
      reg('launcher', 'Hood pivot bearing', '8 mm flange bearing at the hood pivot', 1,
        'Hood swings on real bearings, not a bare bolt — keeps the exit angle repeatable.',
        P.bearing(), [s * 2.48, 14.13, 1.35], [0, s < 0 ? Math.PI : 0, 0], turret);
      reg('launcher', 'Hood pivot pin', '8 mm pivot pin through the cheek', 1,
        'The hood pivot axle running through both cheeks.',
        P.washer(0.16), [s * 2.65, 14.13, 1.35], [0, 0, 0], turret);
      reg('launcher', 'Hood pivot collar', '8 mm collar on the pivot pin', 1,
        'Axial keepers on the hood pivot pin.',
        P.collar(), [s * 3.01, 14.13, 1.35], [0, 0, 0], turret);
    }
    reg('launcher', 'Launcher top brace', 'PETG bar tying the cheek tops', 1,
      'Spans the cheek tops — keeps the nip width constant under belt load.',
      P.plate(5.04, 0.31, 0.18, M.print), [0, 14.76, -0.95], [0, 0, 0], turret);
  }

  /* ================= FLOWER LIFT ================= */
  // Two-stage cascade deposit lift — the feed column doubles as the elevator:
  // a servo Y-flap below the turret deck kicks one ball out the column's +Y
  // side port, down the two-leg load chute (28.5°/21.8°, through a slot in the
  // left tower cheek), and into the Ø99 mm cradle. The mast raises the cradle
  // ~14.6" so its rim clears the ~21.5" FLOWER mouth, then a micro servo tips
  // the ball in. Hard-stop collars cap travel inside the R105 29" limit.
  const liftS1 = new THREE.Group(), liftS2 = new THREE.Group();
  liftS1.name = 'lift-stage1'; liftS2.name = 'lift-stage2';
  groups.lift.add(liftS1); liftS1.add(liftS2);
  // mast — rear-left corner, rails stand on the side-rail top flange
  // as-built: rails cad (−185.4, 144/180) → viewer (−5.67/−7.09, ·, 7.30)
  for (const x of [-5.67, -7.09]) {
    reg('lift', 'Lift guide rail', '14 mm slide extrusion, 10.6"', 1,
      'Fixed mast stage, bolted to the side-rail flange — sits behind the rear wheel.',
      P.slideRail(10.59), [x, 7.92, 7.3]);
  }
  for (const x of [-5.67, -7.03])
    reg('lift', 'Lift foot pad', '3 mm foot plate under each rail', 1,
      'Levels the mast rails onto the tie plates.',
      P.plate(0.55, 0.55, 0.12, M.alu), [x, 2.69, 6.74]);
  reg('lift', 'Mast base plate', '3 mm aluminum on the side-rail flange', 1,
    'Distributes the mast loads into the side-rail top flange.',
    P.plate(1.89, 2.01, 0.12, M.alu), [-6.34, 2.57, 6.2]);
  for (const s of [-1, 1])
    reg('lift', 'Rail tie plate', '3 mm tie under the mast base', 1,
      'Ties the mast feet across the rail top flange.',
      P.plate(2.83, 1.18, 0.12, M.alu), [s * 5.83, 2.57, 7.8]);
  reg('lift', 'Mast top tie', '3 mm aluminum', 1,
    'Closes the top of the guide-rail pair — sets rail parallelism under side load.',
    P.plateV(0.87, 0.75, 1.54, M.alu), [-6.38, 12.78, 6.87]);
  for (const x of [-5.67, -7.09])
    reg('lift', 'Travel stop collar', 'hard stop at full extension — R105/G416 physical stop', 1,
      'Physical travel limit — stage 1 cannot over-extend past this collar.',
      P.collar(), [x, 12.68, 7.28], [0, 0, Math.PI / 2]);
  // stage 1 — twin slim bars riding the fixed rails (as-built: bars inboard of rails)
  for (const x of [-6.19, -6.57]) {
    reg('lift', 'Stage-1 slide bar', '10×4.5 mm extrusion in the guide rails', 1,
      'Moving extrusion — carries the stage-2 rail and the cradle.',
      P.slideRail(9.41, 0.39, M.darkSteel), [x, 7.62, 7.28], [0, 0, 0], liftS1);
  }
  for (const [x, y] of [[-6.02, 3.54], [-6.02, 4.49], [-6.73, 3.54], [-6.73, 4.49]])
    reg('lift', 'Slide truck — stage 1', 'acetal pad riding the rail', 1,
      'Low-friction pads keeping stage 1 square inside the fixed rails.',
      P.plate(0.31, 0.79, 0.16, M.holeDark), [x, y, 7.42], [0, 0, 0], liftS1);
  reg('lift', 'Stage-1 cross tie', '3 mm aluminum', 1,
    'Synchronizes the two stage-1 bars so they lift together.',
    P.plateV(0.71, 0.94, 0.45, M.alu), [-6.38, 12.17, 7.31], [0, 0, 0], liftS1);
  reg('lift', 'Traveling pulley', 'sheave on the stage-1 tie — reels stage 2 at 2× rope rate', 1,
    'Moving sheave — doubles stage-2 travel per inch of stage-1 rise.',
    P.pulley(), [-6.38, 11.89, 7.42], [0, Math.PI / 2, 0], liftS1);
  // stage 2 — single inner bar rides stage 1
  reg('lift', 'Stage-2 slide bar', '8×16 mm extrusion, inner stage', 1,
    'Innermost stage — carries the cradle arm at its top.',
    P.slideRail(8.58, 0.31, M.steel), [-6.38, 7.52, 6.84], [0, 0, 0], liftS2);
  for (const y of [3.86, 4.8])
    reg('lift', 'Slide truck — stage 2', 'acetal pad riding stage 1', 1,
      'Low-friction pads riding inside the stage-1 channel.',
      P.plate(0.26, 0.71, 0.79, M.holeDark), [-6.38, y, 7.13], [0, 0, 0], liftS2);
  reg('lift', 'Stage-2 cross tie', '3 mm aluminum', 1,
    'Keeps the stage-2 bar straight; anchors the rope dead-end.',
    P.plateV(0.94, 0.31, 0.59, M.alu), [-6.46, 11.97, 6.73], [0, 0, 0], liftS2);
  // cradle — cantilevered forward of the mast so its rise path clears the
  // rotating turret plate sweep and both tower cheeks
  reg('lift', 'Cradle arm', '3 mm aluminum cantilever — carries the cradle forward of the mast', 1,
    'Offsets the cradle forward so its rise path clears the turret plate sweep.',
    P.plateV(1.57, 5.08, 0.94, M.alu), [-7.09, 9.82, 6.85], [0, 0, 0], liftS2);
  const cradlePivot = new THREE.Group();
  cradlePivot.position.set(-7.48, 7.64, 5.47); // CRADLE_PIV (-139,190,194)
  liftS2.add(cradlePivot);
  cradlePivot.rotation.x = -0.1;
  reg('lift', 'Cradle pivot disc', 'Ø110 mm pivot plate on the arm', 1,
    'Pivot plate the cradle rings ride on — tips about the lateral axis.',
    (() => {
      const m = new THREE.Mesh(new THREE.CylinderGeometry(2.17, 2.17, 0.31, 24).rotateZ(Math.PI / 2), M.alu);
      m.castShadow = m.receiveShadow = true;
      return m;
    })(), [0, 0, 0], [0, 0, 0], cradlePivot);
  for (const z of [0.94, 1.44])
    reg('lift', 'Cradle pivot collar', '8 mm collar on the pivot shaft', 1,
      'Keeps the pivot shaft indexed along the arm.',
      P.collar(), [0, 0, z], [0, 0, 0], cradlePivot);
  reg('lift', 'Deposit cradle', 'PETG ring seat, Ø99 mm bore, servo-tipped', 1,
    'Shallow ring seat — ball nests on the foam plug inside the 99 mm bore. Rises ~14.6" — rim ~22.3" clears the 21.5" FLOWER mouth; tips forward to drop NECTAR in.',
    (() => {
      const g = new THREE.Group();
      const cup = P.cradleCup(2.17, 0.71);
      g.add(cup);
      // foam plug filling the bore — the ball rests on its top face
      const foam = new THREE.Mesh(new THREE.CylinderGeometry(1.93, 1.93, 0.59, 24), M.rubber);
      foam.castShadow = true; foam.position.y = -0.06;
      g.add(foam);
      g.rotation.z = Math.PI / 2; // cup axis along X (as-built: bore faces ±Y)
      return g;
    })(), [0.28, -2.01, -0.67], [0, 0, 0], cradlePivot);
  reg('lift', 'Tilt servo — cradle', 'micro servo on the arm', 1,
    'Rotates the cradle ~65° at full extension to pour the ball into the mouth.',
    P.servoMotor(), [-7.52, 7.64, 7.52], [0, Math.PI / 2, 0], liftS2);
  const liftBall = P.ball(1.8, M.nectarBlue);
  reg('lift', 'NECTAR (staged)', 'Ø3.6" alliance element — seated in the cradle', 1,
    'Loaded by the column diverter; drops on cradle tip.',
    liftBall, [0.28, -1.5, -0.67], [0, 0, 0], cradlePivot);
  liftBall.userData.vy = 0;
  // winch + rigging
  reg('lift', 'Lift winch — continuous servo', 'winch-mode servo, spool on the horn', 1,
    'Drives the cascade: dead-ends at stage 1, returns over the traveling pulley to stage 2.',
    P.servoMotor(), [-6.3, 3.31, 5.79], [0, 0, Math.PI / 2]);
  reg('lift', 'Winch spool', 'drum on the winch horn', 1,
    'Reels the dyneema — drum diameter sets the lift speed.',
    P.spool(), [-6.3, 3.81, 5.79], [0, Math.PI / 2, 0]);
  reg('lift', 'Winch drive pin', '6 mm pin locking the spool to the horn', 1, '',
    P.pillar(0.63, 0.12, M.darkSteel), [-6.3, 3.81, 5.79], [0, 0, Math.PI / 2]);
  reg('lift', 'Top pulley', 'sheave on the mast tie', 1,
    'Redirects the winch line down to the stage-1 anchor point.',
    P.pulley(), [-6.4, 12.66, 6.14], [0, Math.PI / 2, 0]);
  reg('lift', 'Top pulley pin', '6 mm sheave pin', 1, '',
    P.pillar(0.55, 0.12, M.darkSteel), [-6.46, 12.66, 6.14], [0, 0, Math.PI / 2]);
  reg('lift', 'Rope guide eyelet', 'welded ring — keeps the dead-end run off the rail', 1,
    'Aligns the dead-end run so it cannot jump the spool.',
    P.eyelet(), [-6.75, 12.99, 7.32], [Math.PI / 2, 0, 0]);
  reg('lift', 'Lift rope — dyneema', '1.5 mm UHMWPE run', 1,
    'Rigging path: winch → top pulley → stage-1 dead-end → traveling pulley → stage-2 tie.',
    P.cable([[-6.3, 3.5, 5.79], [-6.6, 6.0, 6.2], [-6.75, 12.99, 7.32], [-6.5, 12.7, 6.5]], M.wireBlack, 0.028));
  // moving rope legs — cylinder meshes rescaled each frame in main.js
  const rope1 = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 1, 6), M.wireBlack);
  const rope2 = rope1.clone();
  rope1.castShadow = rope2.castShadow = false;
  robot.add(rope1, rope2);
  anim.lift = { s1: liftS1, s2: liftS2, cradle: cradlePivot, ball: liftBall, ballState: 'cup', rope1, rope2 };
  // load path — the diverter port exits through the +Y wall (viewer -X face)
  // into a two-leg tray: port (-2.20,8.03,2.60) → kink (-4.53,6.61,3.78) →
  // cradle (-7.01,5.51,5.00); leg slopes 28.5° / 21.8°. Viewer deviation: lips
  // drawn as straight rails — the real lip plates flare.
  reg('lift', 'Column load port', 'window in the +Y shell below the deck', 1,
    'Opening in the tube wall — the diverter kicks one ball out through here.',
    P.plateV(0.85, 0.9, 0.07, M.holeDark), [-2.2, 8.03, 2.6], [0, Math.PI / 2, 0]);
  reg('lift', 'Port flange', 'bolted flange plate around the port', 1,
    'Frames the port window and carries the chute ear.',
    (() => {
      const s = new THREE.Shape();
      s.moveTo(-2.36, -1.96); s.lineTo(2.36, -1.96); s.lineTo(2.36, 1.96); s.lineTo(-2.36, 1.96); s.closePath();
      const hole = new THREE.Path(); hole.absarc(0, 0.4, 1.97, 0, Math.PI * 2, true); s.holes.push(hole);
      const geo = new THREE.ExtrudeGeometry(s, { depth: 0.16, bevelEnabled: false });
      geo.rotateY(Math.PI / 2); // extrude +Z → +X: plate stands on the wall face
      const m = new THREE.Mesh(geo, M.alu); m.castShadow = m.receiveShadow = true;
      return m;
    })(), [-2.24, 7.63, 2.6]);
  reg('lift', 'Port ear — chute mount', 'small ear plate at the port', 1,
    'Chute leg-1 pins to this ear below the port flange.',
    P.plateV(0.31, 0.39, 0.24, M.alu), [-2.44, 7.68, 4.72]);
  reg('lift', 'Tower cheek slot', 'load chute passes through the tower cheek', 1,
    'Routed opening — the load chute passes through the left tower wall.',
    P.plateV(1.0, 1.2, 0.07, M.holeDark), [-4.68, 6.5, 3.85], [0, Math.PI / 2, 0]);
  reg('lift', 'Chute tower pad', 'pad at the tower crossing', 1,
    'Supports the chute where it crosses the tower cheek slot.',
    P.plateV(0.34, 2.52, 0.55, M.alu), [-5.38, 4.69, 2.64]);
  reg('lift', 'Lift load chute', 'PETG two-leg tray — column port to cradle rim', 1,
    'Ball rolls port → cheek slot → cradle on 28.5° then 21.8° legs; 97 mm wide tray.',
    (() => {
      const g = new THREE.Group();
      // leg between two waypoints: local -Z runs down-slope
      const leg = (p0, p1) => {
        const lg = new THREE.Group();
        const dx = p1[0] - p0[0], dy = p1[1] - p0[1], dz = p1[2] - p0[2];
        const len = Math.hypot(dx, dy, dz);
        lg.position.set((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2);
        lg.rotation.order = 'YXZ';
        lg.rotation.set(Math.atan2(-dy, Math.hypot(dx, dz)), Math.atan2(dx, dz), 0);
        const floor = P.plate(3.82, len, 0.07, M.print);
        lg.add(floor);
        for (const s of [-1, 1]) {
          const lip = P.plateV(0.07, 0.5, len, M.print);
          lip.position.set(s * 1.9, 0.28, 0);
          lg.add(lip);
        }
        return lg;
      };
      g.add(leg([-2.2, 8.03, 2.6], [-4.53, 6.61, 3.78]));
      g.add(leg([-4.53, 6.61, 3.78], [-7.01, 5.51, 5.0]));
      return g;
    })());

  /* ================= ELECTRONICS ================= */
  // twin side decks over the drive bay (as-built DECK_L/R z 83.8–86.8 → y 3.36)
  for (const s of [-1, 1])
    reg('electronics', 'Deck plate — side', '3 mm polycarbonate deck over the drive bay', 1,
      'Twin side decks span the tower bays — the hopper trough runs between them.',
      P.plate(4.65, 11.57, 0.12, M.polycarbSolid), [s * 4.92, 3.36, 1.06]);
  for (const s of [-1, 1]) for (const z of (s < 0 ? [4.88, 2.36, -1.18, -4.33] : [5.91, 2.36, -1.18, -4.33]))
    reg('electronics', 'Deck post', 'standoff post, deck to rail top', 1,
      'Posts the deck plates off the rail top flanges.',
      P.pillar(0.79, 0.2, M.alu), [s * 6.3, 2.91, z]);
  reg('electronics', 'Electronics shelf', '3 mm polycarbonate tray over the left deck', 1,
    'Standoff shelf on the left deck — clears the drive-motor leads.',
    P.plate(3.94, 5.31, 0.08, M.polycarbSolid), [-4.53, 3.74, 3.84]);
  for (const p of [[-2.87, 3.56, 6.1], [-6.18, 3.56, 4.33], [-2.87, 3.56, 1.57], [-6.18, 3.56, 1.57]])
    reg('electronics', 'Shelf standoff', 'M3 standoff under the shelf', 1, '',
      P.pillar(0.28, 0.18, M.alu), p);
  reg('electronics', 'REV Control Hub', 'Android-based main controller', 1,
    'Runs the robot: pose estimation, turret PID, flywheel velocity loops.',
    P.controlHub(), [-0.43, 1.66, 1.14]);
  // Expansion Hub face-mounted on the RIGHT rail outer wall (as-built: exp hub
  // at cad y −201.5 → viewer +7.87, standing on edge)
  reg('electronics', 'REV Expansion Hub', 'secondary I/O hub on the rail out-face', 1,
    'Splits motor/servo load; RS485-linked to the Control Hub. Stands vertically on the right-rail outer face.',
    (() => {
      const outer = new THREE.Group();
      const hub = P.controlHub();
      hub.rotation.y = Math.PI / 2;
      outer.add(hub);
      outer.rotation.z = Math.PI / 2;
      return outer;
    })(), [7.87, 1.57, 0]);
  reg('electronics', 'Battery — 3000 mAh', '12 V NiMH, XT30', 1,
    'Main pack — strapped to the belly pan beside the Control Hub.',
    P.battery(), [0, 1.88, -2.56]);
  for (const z of [-1.67, -3.44])
    reg('electronics', 'Battery strap', 'webbing strap over the pack', 1,
      'Two straps hold the pack to the pan — pulls for pit swaps.',
      P.plate(3.62, 1.18, 0.1, M.rubber), [0, 2.45, z]);
  reg('electronics', 'Main power switch', 'REV switch w/ bracket', 1,
    'Robot main disconnect — required to be reachable and labeled.',
    P.mainSwitch(), [2.54, 1.7, -2.07], [0, Math.PI / 2, 0]);
  reg('electronics', 'Switch bracket', 'formed bracket under the switch', 1,
    'Mounts the switch beside the battery pack.',
    P.plateV(1.18, 0.94, 0.79, M.alu), [2.24, 1.56, -2.07]);
  // wire clips tidied along the belly pan
  for (const p of [[0, 1.17, -5.98], [3.15, 1.17, 1.57], [3.74, 1.17, 1.57], [3.15, 1.17, -1.42]])
    reg('electronics', 'Wire clip', 'stick-on cable clip on the pan', 1,
      'Adhesive clips tidy the long loom runs.',
      P.plateV(0.47, 0.16, 0.47, M.holeDark), p);
  // ---- wiring: motor power runs to the rail-mounted Expansion Hub ----
  const motorRuns = [
    // front-left drive motor → rail → hub face
    [[-3.3, 2.6, -4.7], [-5.4, 1.35, -3.4], [-5.4, 1.15, 3.6], [-4.0, 1.3, 6.5], [1.0, 1.3, 6.8], [6.9, 1.4, 0.6]],
    // front-right
    [[3.3, 2.6, -4.7], [5.4, 1.35, -3.4], [5.4, 1.15, 3.6], [6.8, 1.3, 2.0], [7.4, 1.5, 0.5]],
    // rear-left
    [[-3.3, 2.6, 5.3], [-5.4, 1.3, 5.9], [-4.4, 1.4, 6.6], [0.5, 1.35, 6.9], [6.9, 1.4, 0.9]],
    // rear-right
    [[3.3, 2.6, 5.3], [5.4, 1.3, 5.9], [6.2, 1.35, 4.0], [7.5, 1.5, 1.2]],
    // intake motor → rail → hub
    [[3.3, 2.4, -3.1], [5.4, 1.3, -1.4], [6.0, 1.3, 0.5], [7.4, 1.45, 0.3]],
    // feed motor → hub
    [[3.3, 3.3, 1.5], [4.9, 2.1, 2.6], [5.6, 1.8, 1.8], [7.3, 1.5, 0.7]],
  ];
  for (const run of motorRuns)
    reg('electronics', 'Motor power lead — 18 AWG pair', 'red/black twisted pair, loomed to Expansion Hub', 1,
      'Each motor home-runs to a hub port — loomed along the inside of the rails.',
      P.wireBundle(run, [M.wireRed, M.wireBlack], 0.045, 0.09));
  // ---- servo 3-wire looms (to the Expansion Hub) ----
  const servoRuns = [
    // agitator
    [[3.5, 4.4, -2.4], [4.6, 2.5, -0.4], [5.8, 1.6, 0.6], [7.4, 1.6, 0.4]],
    // column gate
    [[3.2, 6.6, 1.3], [4.8, 4.2, 2.0], [5.9, 2.2, 1.4], [7.4, 1.6, 0.8]],
    // yaw servo under deck
    [[3.4, 8.5, 2.9], [5.2, 5.6, 3.4], [6.2, 3.2, 2.2], [7.4, 1.6, 1.0]],
    // diverter servo on the column
    [[-3.0, 5.4, 2.9], [-4.8, 3.6, 4.4], [-2.0, 2.6, 5.8], [4.0, 1.5, 4.0], [7.3, 1.5, 1.4]],
    // lift winch — down the mast, along the rear rail to the hub
    [[-6.9, 3.0, 5.9], [-7.4, 2.5, 4.2], [-6.0, 2.2, 6.6], [-1.0, 1.5, 6.8], [5.5, 1.4, 3.0], [7.4, 1.5, 0.8]],
  ];
  for (const run of servoRuns)
    reg('electronics', 'Servo extension — 3-wire', '22 AWG PWM extension, loomed', 1,
      'PWM extension loomed from each servo back to the Expansion Hub.',
      P.wireBundle(run));
  // tilt servo rides stage 2 — short loom parented to the stage
  reg('electronics', 'Servo extension — tilt (stage 2)', '22 AWG PWM, rides the moving stage', 1,
    'Service loop long enough for full stage-2 travel without snagging.',
    P.wireBundle([[-7.5, 7.5, 7.3], [-7.4, 5.9, 7.1], [-7.35, 4.2, 7.2]]), [0, 0, 0], anim.lift.s2);
  // ---- encoder / sensor runs to the Control Hub ----
  const encRuns = [
    [[-4.6, 1.85, -0.9], [-4.0, 1.45, 0.6], [-3.0, 1.5, 1.6], [-0.9, 1.85, 1.2]],
    [[4.6, 1.85, -0.9], [4.2, 1.4, 0.6], [2.6, 1.5, 1.6], [-0.1, 1.85, 1.3]],
    [[0.2, 1.9, 6.0], [-0.6, 1.5, 4.4], [-1.4, 1.7, 2.6], [-0.6, 1.9, 1.5]],
    // hopper color sensor
    [[2.9, 3.1, -3.6], [4.8, 1.4, -0.9], [4.6, 1.5, 2.0], [1.0, 1.85, 1.3]],
  ];
  for (const run of encRuns)
    reg('electronics', 'Sensor/encoder lead — 4-pin JST', '22 AWG I2C/quadrature run', 1,
      'I2C/quadrature runs — odometry pods and the hopper color sensor.',
      P.wireBundle(run, [M.wireYellow, M.wireBlack], 0.026, 0.06));
  // JST housings at the sensor/servo ends of the looms — keyed, serviceable joints
  for (const p of [[-4.6, 1.85, -0.9], [4.6, 1.85, -0.9], [0.2, 1.9, 6.0], [2.9, 3.1, -3.6], [3.5, 4.4, -2.4]])
    reg('electronics', 'Wire connector — JST', '4-pin JST-XH housing pair', 1,
      'Keyed connector where each loom meets its sensor or servo.',
      P.connector(0.3), p);
  // ---- power trunk: battery → switch → Control Hub ----
  reg('electronics', 'Battery → switch lead', '14 AWG silicone, XT30', 1,
    'Main power trunk to the switch — shortest practical route off the pack.',
    P.wireBundle([[1.4, 2.1, -2.6], [2.0, 1.9, -2.1], [2.4, 1.75, -2.0]],
      [M.wireRed, M.wireBlack], 0.06, 0.11));
  reg('electronics', 'Switch → hub lead', '14 AWG silicone', 1,
    'Switched feed into the Control Hub — downstream of the disconnect.',
    P.wireBundle([[2.3, 1.75, -1.9], [1.4, 1.7, -0.8], [0.2, 1.8, 0.4], [-0.3, 1.9, 1.0]],
      [M.wireRed, M.wireBlack], 0.06, 0.11));
  // RS485 link between the two hubs
  reg('electronics', 'Hub RS485 link', '4-pin JST-PH, shielded', 1,
    'Expansion Hub data link — daisy-chained off the Control Hub port.',
    P.wireBundle([[0.4, 1.85, 1.1], [2.5, 1.6, 0.7], [5.5, 1.5, 0.4], [7.5, 1.5, 0.2]], [M.wireYellow, M.wireBlack], 0.03, 0.07));
  // camera USB — hub port up the tower to the slip-ring side
  reg('electronics', 'Camera USB lead', 'USB 2.0 pigtail through the slip ring', 1,
    'Vision feed — climbs the tower to the slip ring and out to the turret camera.',
    P.wireBundle([[-0.6, 2.0, 1.3], [0.8, 2.9, 3.6], [2.4, 5.0, 3.6], [2.4, 8.6, 3.0], [1.9, 9.7, 2.6]],
      [M.wireBlack], 0.05, 0));
  reg('electronics', 'USB ferrite bead', 'snap-on choke on the camera lead', 1,
    'EMI choke — keeps motor/encoder noise off the image feed.',
    P.pillar(0.5, 0.09, M.holeDark), [2.4, 8.1, 3.3], [0.5, 0, 0.3]);
  // powerpole connector pair where the battery lead meets the switch
  reg('electronics', 'Powerpole connector pair', '45A red/black PP15 at the switch', 1,
    'Quick-disconnect in the battery trunk — the pack pulls without tools.',
    (() => {
      const g = new THREE.Group();
      for (const s of [-1, 1]) {
        const c = P.connector(0.34);
        c.position.set(0, 0, s * 0.14);
        c.rotation.y = s > 0 ? 0 : Math.PI;
        if (s > 0) c.children[0].material = M.wireRed;
        g.add(c);
      }
      return g;
    })(), [2.2, 1.8, -2.05]);
  // slip ring on the feed column — passes power/signal to the rotating turret
  reg('electronics', 'Turret slip ring', '8-circuit capsule slip ring on the column', 1,
    'Keeps turret wiring twist-free through unlimited yaw. Viewer deviation: ring envelope shown, capsule detail omitted.',
    P.slipRing(), [0, 8.85, 2.6]);
  // zip ties on the long rail runs + servo loom anchors on the tower
  for (const s of [-1, 1]) for (const z of [-1.6, 1.8])
    reg('electronics', 'Cable tie', '4" nylon zip tie', 1,
      'Loom anchors along the rail and tower runs — snipped flush after routing.',
      P.zipTie(0.14), [s * 5.4, 1.25, z]);
  for (const p of [[5.9, 2.2, 1.4], [-4.8, 3.6, 4.4], [-7.4, 2.5, 4.2]])
    reg('electronics', 'Cable tie', '4" nylon zip tie', 1, '', P.zipTie(0.14), p);

  // ---- structural bolt fields (instanced) ----
  reg('drive', 'Plate bolts — motor mounts', 'M4 socket head', 24,
    'Clamp the motor mount plates to both rail inner faces.',
    P.boltField((() => {
      const l = [];
      for (const s of [-1, 1]) for (const z of [-5, -3, -1, 1, 3, 5]) for (const dy of [-0.55, 0.55])
        l.push([s * 5.24, RAIL_Y + dy, z]);
      return l;
    })(), 0.06, 0.09, 'x'));
  reg('turret', 'Plate bolts — tower cheeks', 'M4 socket head', 16,
    'Bolt the tower cheeks to the frame and the turret deck.',
    P.boltField((() => {
      const l = [];
      for (const s of [-1, 1]) for (const z of [1.0, 3.4, 5.8, 6.8]) for (const y of [4.0, 9.0])
        l.push([s * 4.75, y, z]);
      return l;
    })(), 0.06, 0.09, 'x'));
  reg('hopper', 'Plate bolts — hopper walls', 'M4 socket head', 16,
    'Fasten the hopper wall panels to the floor and braces.',
    P.boltField((() => {
      const l = [];
      for (const s of [-1, 1]) for (const z of [-3.4, -1.8, -0.2, 1.4]) for (const y of [3.6, 6.2])
        l.push([s * 2.36, y, z]);
      return l;
    })(), 0.06, 0.09, 'x'));
  reg('intake', 'Plate bolts — intake cheeks', 'M4 socket head', 8,
    'Bolt the intake cheeks to the crown posts and gussets.',
    P.boltField((() => {
      const l = [];
      for (const s of [-1, 1]) for (const z of [-7.6, -5.2]) for (const y of [1.4, 4.4])
        l.push([s * 4.94, y, z]);
      return l;
    })(), 0.06, 0.09, 'x'));
  reg('electronics', 'Deck bolts', 'M4 socket head', 8,
    'Clamp the deck plates to the rail top flanges.',
    P.boltField([[-4.5, 3.44, -3.8], [-2.7, 3.44, -3.8], [2.7, 3.44, -3.8], [4.5, 3.44, -3.8],
      [-4.5, 3.44, 5.8], [-2.7, 3.44, 5.8], [2.7, 3.44, 5.8], [4.5, 3.44, 5.8]], 0.06, 0.09, 'y'));
  reg('turret', 'Deck bolts', 'M4 socket head', 8,
    'Clamp the turret deck plate to the tower cheeks.',
    P.boltField([[-4.6, 9.78, 0.2], [4.6, 9.78, 0.2], [-4.6, 9.78, 6.6], [4.6, 9.78, 6.6],
      [-1.6, 9.78, 0.2], [1.6, 9.78, 0.2], [-1.6, 9.78, 6.6], [1.6, 9.78, 6.6]], 0.06, 0.09, 'y'));
  reg('lift', 'Mast mount bolts', 'M4 socket head', 8,
    'Bolt the mast base plate and top tie to the rail flange.',
    P.boltField([[-7.0, 2.65, 6.9], [-5.7, 2.65, 6.9], [-7.0, 2.65, 7.7], [-5.7, 2.65, 7.7],
      [-7.0, 12.75, 6.9], [-5.8, 12.75, 6.9], [-7.0, 12.75, 7.2], [-5.8, 12.75, 7.2]], 0.055, 0.08, 'y'));

  // ammo staged in hopper for looks (3 pollen) — ride the incline surface
  const ballsGroup = new THREE.Group();
  for (let i = 0; i < 3; i++) {
    const b = P.ball(1.4, M.pollen);
    const z = -3.9 + i * 1.35;
    b.position.set(0, 4.75 - (z + 2.3) * 0.39, z);
    ballsGroup.add(b);
  }
  reg('hopper', 'POLLEN (staged)', 'Ø2.8" neutral scoring element', 3,
    'Capacity ~6 in the magazine.', ballsGroup);

  // launch demo ball (hidden until fired)
  const demoBall = P.ball(1.4, M.pollen);
  demoBall.position.y = -100;
  demoBall.visible = false;
  robot.add(demoBall);
  anim.launch.ball = demoBall;

  // ---- functional relations graph — powers the inspector's "connected parts" ----
  // name → related entry names (functional mates / power & signal chain).
  const REL = {
    'Side rail — U-channel': ['Motor mount plate', 'Flange bearing — rail', 'Corner gusset', 'Rail end cap', 'Belly pan', 'Crown riser post'],
    'Motor mount plate': ['Drive motor — 5203 + UltraPlanetary', 'Side rail — U-channel'],
    'Drive motor — 5203 + UltraPlanetary': ['Motor pinion — 15T brass', 'Wheel axle — 8 mm REX', 'Motor mount plate', 'Motor power lead — 18 AWG pair', 'Motor clamp block'],
    'Wheel axle — 8 mm REX': ['Flange bearing — rail', '96 mm mecanum wheel', 'Shaft collar', 'Axle nut — nylock', 'Motor pinion — 15T brass', 'Axle washer'],
    'Flange bearing — rail': ['Wheel axle — 8 mm REX', 'Side rail — U-channel'],
    '96 mm mecanum wheel': ['Wheel axle — 8 mm REX', 'Axle nut — nylock', 'Flange bearing — rail'],
    'Shaft collar': ['Wheel axle — 8 mm REX'],
    'Axle nut — nylock': ['Wheel axle — 8 mm REX', '96 mm mecanum wheel'],
    'Motor pinion — 15T brass': ['Drive motor — 5203 + UltraPlanetary', 'Wheel axle — 8 mm REX'],
    'Rear crossmember — U-channel': ['Side rail — U-channel', 'Corner gusset', 'Rail end cap'],
    'Front crown crossmember — raised': ['Side rail — U-channel', 'Intake cheek plate', 'Crown riser post', 'Throat guard plate'],
    'Crown riser post': ['Front crown crossmember — raised', 'Side rail — U-channel', 'Intake pivot pin'],
    'Rail end cap': ['Side rail — U-channel'],
    'Belly pan': ['Side rail — U-channel', 'Odometry pod — lateral', 'Odometry pod — longitudinal', 'REV Control Hub', 'Belly pan bracket', 'Wire clip'],
    'Belly pan bracket': ['Belly pan', 'Side rail — U-channel'],
    'Corner gusset': ['Side rail — U-channel', 'Rear crossmember — U-channel'],
    'Odometry pod — lateral': ['Sensor/encoder lead — 4-pin JST', 'Belly pan'],
    'Odometry pod — longitudinal': ['Sensor/encoder lead — 4-pin JST', 'Belly pan'],
    'Alliance number plate — rear': ['Rear crossmember — U-channel'],
    'Alliance number plate — left': ['Side rail — U-channel'],
    'Frame hardware — M4 socket head': ['Side rail — U-channel'],

    'Intake cheek plate': ['Torsion spring — floating roller', 'Cheek flange bearing', 'Intake pivot pin', 'Front crown crossmember — raised', 'Cheek float slot'],
    'Torsion spring — floating roller': ['Compliant star roller', 'Intake cheek plate', 'Spring post'],
    'Spring post': ['Torsion spring — floating roller', 'Intake cheek plate'],
    'Intake pivot pin': ['Intake cheek plate', 'Crown riser post'],
    'Traction roller': ['Intake drive shaft', 'Roller belt pulley — GT', 'Cheek flange bearing'],
    'Compliant star roller': ['Roller belt pulley — GT', 'Cheek flange bearing', 'Torsion spring — floating roller', 'Star roller shaft', 'Float slide block'],
    'Star roller shaft': ['Compliant star roller', 'Float slide block'],
    'Intake motor — compact 5203': ['Intake drive sprocket — 9T', 'Intake motor shaft', 'Motor power lead — 18 AWG pair', 'Motor clamp — compact'],
    'Intake motor shaft': ['Intake motor — compact 5203', 'Intake drive sprocket — 9T'],
    'Intake drive sprocket — 9T': ['Intake chain — #25', 'Intake motor shaft'],
    'Intake driven sprocket — 16T': ['Intake chain — #25', 'Intake drive shaft'],
    'Intake chain — #25': ['Intake drive sprocket — 9T', 'Intake driven sprocket — 16T', 'Chain guard', 'Chain master link'],
    'Chain master link': ['Intake chain — #25'],
    'Chain guard': ['Intake chain — #25'],
    'Intake drive shaft': ['Traction roller', 'Intake driven sprocket — 16T', 'Roller belt pulley — GT', 'Cheek flange bearing'],
    'Roller belt pulley — GT': ['Roller cross-belt — GT loop', 'Traction roller', 'Compliant star roller'],
    'Roller cross-belt — GT loop': ['Roller belt pulley — GT', 'Belt tensioner — idler'],
    'Belt tensioner — idler': ['Roller cross-belt — GT loop', 'Belt tensioner — arm + spring'],
    'Belt tensioner — arm + spring': ['Belt tensioner — idler', 'Belt tensioner — spring'],
    'Belt tensioner — spring': ['Belt tensioner — arm + spring'],
    'Cheek flange bearing': ['Intake cheek plate', 'Intake drive shaft', 'Compliant star roller'],
    'Float slide block': ['Compliant star roller', 'Cheek float slot'],
    'Cheek float slot': ['Intake cheek plate', 'Float slide block'],
    'Throat guard plate': ['Front crown crossmember — raised', 'Compliant star roller'],

    'Hopper floor — incline': ['Hopper side wall — left', 'Hopper side wall — right', 'Feed wheel — compliant', 'POLLEN (staged)', 'Hopper apron'],
    'Hopper apron': ['Hopper floor — incline'],
    'Hopper side wall — left': ['Hopper floor — incline', 'Hopper rear curb', 'Hopper ledge', 'Hopper wall bracket'],
    'Hopper side wall — right': ['Hopper floor — incline', 'Hopper rear curb', 'Hopper ledge', 'Hopper wall bracket', 'Agitator servo'],
    'Hopper ledge': ['Hopper side wall — left', 'Hopper side wall — right'],
    'Hopper rear curb': ['Hopper side wall — left', 'Feed column — clear 4"'],
    'Hopper wall bracket': ['Hopper side wall — left', 'Hopper side wall — right'],
    'Agitator paddle': ['Agitator servo', 'Agitator drive horn'],
    'Agitator servo': ['Agitator paddle', 'Servo extension — 3-wire', 'Agitator servo bracket', 'Agitator drive horn'],
    'Agitator servo bracket': ['Agitator servo', 'Hopper side wall — right'],
    'Agitator drive horn': ['Agitator servo', 'Agitator paddle'],
    'Feed wheel — compliant': ['Feed shaft — 8 mm REX', 'Feed spur gear — 28T', 'Feed guide scoop', 'Feed column — clear 4"'],
    'Feed motor — compact 5203': ['Feed spur gear — 28T', 'Motor power lead — 18 AWG pair', 'Motor clamp — compact', 'Feed motor mount plate', 'Feed motor standoff'],
    'Feed motor mount plate': ['Feed motor — compact 5203', 'Feed motor standoff'],
    'Feed motor standoff': ['Feed motor mount plate'],
    'Feed spur gear — 28T': ['Feed motor — compact 5203', 'Feed shaft — 8 mm REX', 'Feed wheel — compliant'],
    'Feed shaft — 8 mm REX': ['Feed wheel — compliant', 'Feed wall bearing', 'Feed spur gear — 28T'],
    'Feed wall bearing': ['Feed shaft — 8 mm REX'],
    'Feed guide scoop': ['Feed wheel — compliant', 'Feed column — clear 4"'],
    'Feed column — clear 4"': ['Gate servo + flag', 'Column diverter — Y flap', 'Turret slip ring', 'POLLEN (in column)', 'Nip backplate', 'Column base flange', 'Column load port'],
    'Column base flange': ['Feed column — clear 4"', 'Column standoff post', 'Turret deck'],
    'Column standoff post': ['Column base flange'],
    'Gate servo + flag': ['Feed column — clear 4"', 'Servo extension — 3-wire', 'Gate servo bracket', 'Gate horn'],
    'Gate servo bracket': ['Gate servo + flag'],
    'Gate horn': ['Gate servo + flag'],
    'POLLEN (in column)': ['Feed column — clear 4"', 'Gate servo + flag'],
    'Entry color sensor': ['Sensor/encoder lead — 4-pin JST', 'Hopper side wall — right'],
    'POLLEN (staged)': ['Hopper floor — incline'],

    'Tower cheek': ['Turret deck', 'Tower gusset', 'Tower cheek slot', 'Deck plate — side'],
    'Tower gusset': ['Tower cheek', 'Turret deck'],
    'Turret deck': ['Lazy susan race — lower', 'Tower cheek', 'Yaw servo — continuous', 'Yaw pinion — 14T', 'Deck bolts'],
    'Lazy susan race — lower': ['Turret deck', 'Lazy susan race — upper'],
    'Lazy susan race — upper': ['Lazy susan race — lower', 'Turret rotating plate', 'Turret ring gear — 72T'],
    'Yaw servo — continuous': ['Yaw pinion — 14T', 'Turret deck', 'Servo extension — 3-wire', 'Yaw pinion shaft'],
    'Yaw pinion shaft': ['Yaw servo — continuous', 'Yaw pinion — 14T'],
    'Yaw pinion — 14T': ['Yaw servo — continuous', 'Turret ring gear — 72T', 'Yaw pinion shaft'],

    'Turret ring gear — 72T': ['Yaw pinion — 14T', 'Turret rotating plate', 'Lazy susan race — upper'],
    'Turret rotating plate': ['Turret ring gear — 72T', 'Launcher cheek plate', 'Lazy susan race — upper', 'Yaw index magnet'],
    'Launcher cheek plate': ['Flywheel bearing', 'Flywheel motor — 5203', 'Adjustable hood', 'Turret rotating plate', 'Vision camera', 'Launcher top brace'],
    'Flywheel motor — 5203': ['Flywheel — 3.5"', 'Flywheel motor lead — on turret', 'Launcher cheek plate', 'Flywheel motor clamp'],
    'Flywheel motor clamp': ['Flywheel motor — 5203', 'Launcher cheek plate'],
    'Flywheel — 3.5"': ['Flywheel motor — 5203', 'Flywheel bearing', 'Nip backplate', 'Adjustable hood', 'Flywheel shaft — 8 mm REX'],
    'Flywheel shaft — 8 mm REX': ['Flywheel — 3.5"', 'Flywheel bearing', 'Flywheel shaft collar'],
    'Flywheel shaft collar': ['Flywheel shaft — 8 mm REX'],
    'Flywheel bearing': ['Flywheel — 3.5"', 'Launcher cheek plate'],
    'Adjustable hood': ['Hood servo', 'Hood linkage', 'Launcher cheek plate', 'Hood pivot bearing'],
    'Hood pivot bearing': ['Adjustable hood', 'Hood pivot pin', 'Launcher cheek plate'],
    'Hood pivot pin': ['Adjustable hood', 'Hood pivot collar'],
    'Hood pivot collar': ['Hood pivot pin'],
    'Hood servo': ['Hood linkage', 'Adjustable hood', 'Hood servo lead — on turret'],
    'Hood linkage': ['Hood servo', 'Adjustable hood'],
    'Nip backplate': ['Flywheel — 3.5"', 'Feed column — clear 4"'],
    'Vision camera': ['Camera USB lead', 'Camera status LED', 'Camera mount', 'Launcher cheek plate'],
    'Camera mount': ['Vision camera', 'Turret rotating plate'],
    'Camera status LED': ['Vision camera'],
    'Launcher top brace': ['Launcher cheek plate'],

    'Lift guide rail': ['Slide truck — stage 1', 'Mast base plate', 'Travel stop collar', 'Mast top tie', 'Lift foot pad'],
    'Lift foot pad': ['Lift guide rail', 'Rail tie plate'],
    'Rail tie plate': ['Lift foot pad', 'Side rail — U-channel'],
    'Mast base plate': ['Lift guide rail', 'Side rail — U-channel', 'Mast mount bolts'],
    'Mast top tie': ['Lift guide rail', 'Top pulley'],
    'Travel stop collar': ['Lift guide rail'],
    'Stage-1 slide bar': ['Slide truck — stage 1', 'Stage-1 cross tie', 'Lift guide rail'],
    'Slide truck — stage 1': ['Stage-1 slide bar', 'Lift guide rail'],
    'Stage-1 cross tie': ['Stage-1 slide bar', 'Traveling pulley'],
    'Traveling pulley': ['Stage-1 cross tie', 'Lift rope — dyneema'],
    'Stage-2 slide bar': ['Slide truck — stage 2', 'Stage-2 cross tie', 'Cradle arm'],
    'Slide truck — stage 2': ['Stage-2 slide bar'],
    'Stage-2 cross tie': ['Stage-2 slide bar', 'Lift rope — dyneema'],
    'Cradle arm': ['Deposit cradle', 'Tilt servo — cradle', 'Stage-2 slide bar', 'Cradle pivot disc'],
    'Cradle pivot disc': ['Deposit cradle', 'Cradle arm', 'Cradle pivot collar'],
    'Cradle pivot collar': ['Cradle pivot disc'],
    'Deposit cradle': ['Cradle arm', 'Tilt servo — cradle', 'NECTAR (staged)', 'Lift load chute', 'Cradle pivot disc'],
    'Tilt servo — cradle': ['Deposit cradle', 'Servo extension — tilt (stage 2)'],
    'NECTAR (staged)': ['Deposit cradle'],
    'Lift winch — continuous servo': ['Winch spool', 'Lift rope — dyneema', 'Servo extension — 3-wire'],
    'Winch spool': ['Lift winch — continuous servo', 'Lift rope — dyneema', 'Winch drive pin'],
    'Winch drive pin': ['Winch spool'],
    'Top pulley': ['Mast top tie', 'Lift rope — dyneema', 'Top pulley pin'],
    'Top pulley pin': ['Top pulley'],
    'Rope guide eyelet': ['Lift rope — dyneema', 'Mast top tie'],
    'Lift rope — dyneema': ['Winch spool', 'Top pulley', 'Traveling pulley', 'Stage-2 cross tie', 'Rope guide eyelet'],
    'Column load port': ['Column diverter — Y flap', 'Lift load chute', 'Feed column — clear 4"', 'Port flange'],
    'Port flange': ['Column load port', 'Port ear — chute mount'],
    'Port ear — chute mount': ['Lift load chute', 'Port flange'],
    'Tower cheek slot': ['Tower cheek', 'Lift load chute'],
    'Chute tower pad': ['Tower cheek', 'Lift load chute'],
    'Lift load chute': ['Column load port', 'Tower cheek slot', 'Deposit cradle', 'Port ear — chute mount'],
    'Column diverter — Y flap': ['Diverter servo', 'Column load port', 'Feed column — clear 4"', 'Diverter shaft'],
    'Diverter shaft': ['Column diverter — Y flap'],
    'Diverter servo': ['Column diverter — Y flap', 'Servo extension — 3-wire', 'Diverter band bracket'],
    'Diverter band bracket': ['Diverter servo', 'Feed column — clear 4"'],

    'Deck plate — side': ['Tower cheek', 'Deck post', 'Deck bolts', 'Electronics shelf'],
    'Deck post': ['Deck plate — side', 'Side rail — U-channel'],
    'Electronics shelf': ['Deck plate — side', 'Shelf standoff'],
    'Shelf standoff': ['Electronics shelf'],
    'REV Control Hub': ['Hub RS485 link', 'Switch → hub lead', 'Camera USB lead', 'Sensor/encoder lead — 4-pin JST', 'Belly pan'],
    'REV Expansion Hub': ['Hub RS485 link', 'Motor power lead — 18 AWG pair', 'Servo extension — 3-wire'],
    'Battery — 3000 mAh': ['Battery → switch lead', 'Belly pan', 'Battery strap'],
    'Battery strap': ['Battery — 3000 mAh'],
    'Main power switch': ['Battery → switch lead', 'Switch → hub lead', 'Switch bracket'],
    'Switch bracket': ['Main power switch'],
    'Wire clip': ['Motor power lead — 18 AWG pair', 'Belly pan'],
    'Motor power lead — 18 AWG pair': ['REV Expansion Hub', 'Drive motor — 5203 + UltraPlanetary', 'Intake motor — compact 5203', 'Feed motor — compact 5203'],
    'Servo extension — 3-wire': ['REV Expansion Hub', 'Agitator servo', 'Gate servo + flag', 'Yaw servo — continuous', 'Diverter servo', 'Lift winch — continuous servo'],
    'Servo extension — tilt (stage 2)': ['Tilt servo — cradle', 'REV Expansion Hub'],
    'Sensor/encoder lead — 4-pin JST': ['REV Control Hub', 'Odometry pod — lateral', 'Odometry pod — longitudinal', 'Entry color sensor', 'Wire connector — JST', 'Hall sensor — yaw index'],
    'Wire connector — JST': ['Sensor/encoder lead — 4-pin JST', 'Servo extension — 3-wire'],
    'Battery → switch lead': ['Battery — 3000 mAh', 'Main power switch', 'Powerpole connector pair'],
    'Switch → hub lead': ['Main power switch', 'REV Control Hub'],
    'Hub RS485 link': ['REV Control Hub', 'REV Expansion Hub'],
    'Camera USB lead': ['REV Control Hub', 'Turret slip ring', 'Vision camera', 'USB ferrite bead'],
    'Turret slip ring': ['Camera USB lead', 'Flywheel motor lead — on turret', 'Hood servo lead — on turret', 'Feed column — clear 4"'],
    'Flywheel motor lead — on turret': ['Turret slip ring', 'Flywheel motor — 5203'],
    'Hood servo lead — on turret': ['Turret slip ring', 'Hood servo'],
    'USB ferrite bead': ['Camera USB lead'],
    'Powerpole connector pair': ['Battery → switch lead', 'Main power switch'],
    'Cable tie': ['Motor power lead — 18 AWG pair', 'Servo extension — 3-wire'],
    'Axle washer': ['Wheel axle — 8 mm REX', 'Flange bearing — rail'],
    'Motor clamp block': ['Drive motor — 5203 + UltraPlanetary', 'Motor mount plate'],
    'intake|Motor clamp — compact': ['Intake motor — compact 5203'],
    'hopper|Motor clamp — compact': ['Feed motor — compact 5203'],
    'Plate bolts — motor mounts': ['Motor mount plate', 'Drive motor — 5203 + UltraPlanetary'],
    'Plate bolts — tower cheeks': ['Tower cheek', 'Turret deck'],
    'Plate bolts — hopper walls': ['Hopper side wall — left', 'Hopper side wall — right'],
    'Plate bolts — intake cheeks': ['Intake cheek plate'],
    'Deck bolts': ['Turret deck', 'Tower cheek'],
    'electronics|Deck bolts': ['Deck plate — side'],
    'Mast mount bolts': ['Mast base plate', 'Mast top tie'],
    'Hall sensor — yaw index': ['Yaw index magnet', 'Turret deck', 'Sensor/encoder lead — 4-pin JST'],
    'Yaw index magnet': ['Hall sensor — yaw index', 'Turret rotating plate'],
  };
  for (const e of entries) {
    // 'sub|name' keys scope a relation to one entry; a link name registered
    // under several subsystems resolves to the same-subsystem entry first
    e.links = (REL[`${e.sub}|${e.name}`] || REL[e.name] || [])
      .map(n => entries.find(x => x.name === n && x.sub === e.sub)
             || entries.find(x => x.name === n))
      .filter(Boolean);
  }

  // ---- per-subsystem base positions (for explode lerp) ----
  for (const id in groups) {
    groups[id].userData.basePos = groups[id].position.clone();
  }
  // launcher has rotating child — explode on the group itself is fine

  return { robot, groups, entries, anim,
    dims: { w: 17.5, d: 17.5, h: 14.9 },
    counts: { motors: 8, servos: 7 } };
}
