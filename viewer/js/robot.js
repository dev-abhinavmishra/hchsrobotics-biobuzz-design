// robot.js — BIOBUZZ competition robot assembly (inches, Y-up, front = -Z)
import * as THREE from 'three';
import { M } from './materials.js';
import * as P from './parts.js';

export const SUBS = {
  drive:       { label: 'Drivetrain & Frame',   color: '#9aa3ad', explode: new THREE.Vector3(0, -0.4, 0),  desc: '17.5×17.5 in. goBILDA-pattern U-channel chassis. 4× 96 mm mecanum wheels on live 8 mm REX hex axles, each coaxially driven by a 5203-class motor with a 5.2:1+ planetary gearbox through flange bearing blocks. Three dead-wheel odometry pods under the belly pan feed the pose estimator. Raised front crossmember doubles as the intake crown.' },
  intake:      { label: 'Intake',               color: '#2f7fd6', explode: new THREE.Vector3(0, -1.2, -5), desc: 'Full-width over/under dual-roller intake. Bottom: ribbed rubber traction roller. Top: stacked compliant star roller on torsion-spring-loaded floating mounts — passes both 2.8" POLLEN and 3.6" NECTAR. Counter-rotating rollers via 1:1 spur pair; #25 chain drive from a motor under the hopper incline; throat feeds the hopper ramp.' },
  hopper:      { label: 'Hopper & Feed',        color: '#37b34a', explode: new THREE.Vector3(0, 2.2, 0),   desc: 'Gravity-assisted inclined magazine (capacity ~6) in PETG/polycarb walls. Servo agitator paddle breaks jams at the low corner. Green compliant feed wheel meters single balls into the clear 4" feed column that rises through the turret axis — allowing unlimited turret yaw. A Y-flap at the column top can divert a ball to the flower lift instead of the nip.' },
  turret:      { label: 'Turret',               color: '#e07ab8', explode: new THREE.Vector3(0, 4.6, 0),   desc: 'Lazy-susan bearing + 72T ring gear driven by a continuous-rotation servo pinion → unlimited-yaw launch deck. The feed column passes through the hollow center, so ammo supply is yaw-independent.' },
  launcher:    { label: 'Flywheel Launcher',    color: '#d9a406', explode: new THREE.Vector3(0, 7.6, 0),   desc: 'Dual counter-rotating 3.5" flywheels (independent 5203 motors → tunable spin differential for curve compensation). Servo-driven hood sets exit angle ~40–65° tuned for the HIVE cell lob — FLOWER deposits moved to the lift (a 4" mouth for a 3.6" NECTAR is too tight a lob window). Vision camera rides the turret and tracks CELL AprilTags.' },
  lift:        { label: 'Flower Lift',          color: '#8e6fd8', explode: new THREE.Vector3(-2.6, 2.0, 3.2), desc: 'Two-stage cascade deposit lift on slim guide rails, dyneema-rigged from a continuous-servo winch with a traveling pulley on stage 1. The feed column doubles as the ball elevator: a servo Y-flap below the turret deck kicks one ball out a side port, down the load chute, and into the tipping cradle. Raise +14.6" → cradle rim ~22.3" clears the ~21.5" FLOWER mouth (§9.7); a micro servo tips the ball in. Travel hard-stop collars satisfy R105/G416.' },
  electronics: { label: 'Electronics',          color: '#d97c1e', explode: new THREE.Vector3(0, -3.2, 0),  desc: 'REV Control Hub on the belly pan + Expansion Hub on a polycarb shelf in the tower bay (clears the drive motors), 3000 mAh battery with strap and main switch, color sensor at hopper entry, full motor/servo wiring loom.' },
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

  /* ================= DRIVETRAIN ================= */
  const RAIL_X = 6.3, RAIL_Y = 1.565, WHEEL_Y = 1.89, WHEEL_X = 8.0, WHEEL_Z = 5.0;

  for (const s of [-1, 1]) {
    reg('drive', 'Side rail — U-channel', 'goBILDA-pattern low-side U-channel, 48 mm section, 6061-T6 anodized', 1,
      'Primary structure. 8 mm grid hole pattern; wheel axles pass through both rail faces on flange bearings.',
      P.channel(17.5), [s * RAIL_X, RAIL_Y, 0]);
    reg('drive', 'Motor mount plate', '3 mm 5052 aluminum', 1,
      'Mounts the drive motors to the rail inner face.',
      P.plateV(12.0, 1.9, 0.12, M.alu), [s * 5.3, RAIL_Y, 0], [0, Math.PI / 2, 0]);
    // drive motors + shafts + wheels (wheels OUTBOARD of rails)
    for (const z of [-WHEEL_Z, WHEEL_Z]) {
      reg('drive', 'Drive motor — 5203 + UltraPlanetary', 'REV UltraPlanetary 5.2:1, 312 rpm output', 1,
        'Inboard motor drives the outboard wheel through a through-rail live axle — low CG, no chain slop.',
        P.driveMotor(3.8), [s * 4.35, WHEEL_Y, z], [0, s > 0 ? 0 : Math.PI, 0]);
      reg('drive', 'Wheel axle — 8 mm REX', '8 mm REX hex shaft, 6061', 1,
        'Through-rail live axle — rides flange bearings on both rail faces.',
        P.hexShaft(4.2), [s * 6.63, WHEEL_Y, z]);
      reg('drive', 'Flange bearing — rail', '8 mm REX flange bearing block', 1,
        'Pilots the live axle through the rail wall — one bearing on each rail face per wheel.',
        P.bearing(), [s * 5.45, WHEEL_Y, z], [0, s < 0 ? Math.PI : 0, 0]);
      reg('drive', 'Flange bearing — rail', '8 mm REX flange bearing block', 1,
        '', P.bearing(), [s * 7.15, WHEEL_Y, z], [0, s < 0 ? Math.PI : 0, 0]);
      const wheel = reg('drive', '96 mm mecanum wheel', 'goBILDA 96 mm mecanum, 11 rollers, 45° layout', 1,
        'Outboard of the rail for maximum track width; rollers handed per corner for true holonomic strafe.',
        P.mecanumWheel(1.89, 1.5, (s * z) > 0 ? 1 : -1), [s * WHEEL_X, WHEEL_Y, z], [0, 0, 0]);
      anim.wheels.push({ obj: wheel, r: 1.89 });
      reg('drive', 'Shaft collar', '8 mm clamping collar', 1,
        'Axial keeper beside the inboard bearing — takes thrust load off the pinion.',
        P.collar(), [s * 5.2, WHEEL_Y, z]);
      reg('drive', 'Axle nut — nylock', '8 mm nylock on the outboard shaft tip', 1,
        'Locks the axle tip outboard of the wheel; nylon insert resists vibration.',
        P.shaftNut(), [s * 8.85, WHEEL_Y, z]);
      reg('drive', 'Motor pinion — 15T brass', '15T brass spur on the output shaft', 1,
        'Transfers motor torque to the axle — brass wears better than acetal at this pitch.',
        P.pinion(0.34), [s * 4.95, WHEEL_Y, z]);
      reg('drive', 'Axle washer', '8 mm flat washer — bearing spacer', 1,
        'Shim — keeps the collar clear of the bearing seal.',
        P.washer(), [s * 5.33, WHEEL_Y, z]);
      // split clamp blocks gripping the motor can
      for (const cx of [3.05, 4.25])
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
  // rail end caps — pressed into every open channel end
  for (const s of [-1, 1]) for (const ez of [-8.6, 8.6])
    reg('drive', 'Rail end cap', 'press-fit HDPE cap', 1,
      'Press-fit plug — keeps swarf out of the channel and softens sharp rail ends.',
      P.endCap(), [s * RAIL_X, RAIL_Y, ez]);
  for (const s of [-1, 1]) {
    reg('drive', 'Rail end cap', 'press-fit HDPE cap', 1, '',
      P.endCap(), [s * 5.2, RAIL_Y, 7.8], [0, Math.PI / 2, 0]);
    reg('drive', 'Rail end cap', 'press-fit HDPE cap', 1, '',
      P.endCap(), [s * 5.2, 6.2, -7.8], [0, Math.PI / 2, 0]);
  }
  reg('drive', 'Belly pan', '3 mm polycarbonate, waterjet', 1,
    'Electronics mounting deck; stops ahead of the intake rollers.',
    P.plate(10.6, 12.6, 0.1, M.polycarbSolid), [0, 1.05, 0]);
  for (const s of [-1, 1]) for (const z of [-1, 1]) {
    reg('drive', 'Corner gusset', '48 mm inside-corner bracket', 1,
      'Stiffens the frame square at every rail joint — resists racking under strafe loads.',
      P.gusset(1.4, 1.4, 0.08, M.accent), [s * 5.4, 0.72, z * 6.9], [0, s * z > 0 ? 0 : Math.PI, 0]);
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
    pod(false), [-4.6, 1.08, -1.2]);
  reg('drive', 'Odometry pod — lateral', '48 mm omni dead-wheel + encoder, sprung', 1,
    '', pod(false), [4.6, 1.08, -1.2]);
  reg('drive', 'Odometry pod — longitudinal', '48 mm omni dead-wheel + encoder, sprung', 1,
    'Measures strafe — third leg of the pose estimator.',
    pod(true), [0, 1.08, 6.0]);
  // team number plates — rear rail face + left rail face (adjacent sides)
  reg('drive', 'Alliance number plate — rear', '0.8 mm PETG + vinyl numerals', 1,
    'Required on two adjacent sides; swap red/blue per alliance.',
    P.numberPlate(3.6, 2.4), [0, 1.62, 8.82]);
  reg('drive', 'Alliance number plate — left', '0.8 mm PETG + vinyl numerals', 1,
    'Second required plate — on a side adjacent to the rear plate per game rules.',
    P.numberPlate(3.6, 2.4), [-7.32, 1.62, 0], [0, -Math.PI / 2, 0]);
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
  for (const s of [-1, 1]) {
    reg('intake', 'Intake cheek plate', '5 mm PETG, CNC routed', 1,
      'Spring posts for the floating top roller; slot allows 0.7" of vertical give for NECTAR.',
      P.plateV(3.2, 3.9, 0.14, M.print), [s * 5.45, 2.45, -7.15], [0, Math.PI / 2, 0]);
    reg('intake', 'Torsion spring — floating roller', 'music-wire torsion spring', 1,
      'Preloads the star roller down onto incoming balls; deflects upward for 3.6" NECTAR.',
      P.springHelix(0.28, 0.55, 5), [s * 5.05, 5.0, -7.15]);
    reg('intake', 'Intake gusset', 'inside-corner bracket', 1,
      'Ties the cheek plates to the front rail — keeps the roller span rigid under impact.',
      P.gusset(1.3, 1.3, 0.08, M.accent), [s * 5.0, 0.72, -7.0], [0, s > 0 ? Math.PI : 0, 0]);
    // floating-roller slide block riding the cheek slot
    reg('intake', 'Float slide block', 'acetal slider on the star-roller shaft', 1,
      'Slides in the cheek slot — gives the top roller its 0.7" of compliance travel.',
      P.plateV(0.4, 0.55, 0.24, M.printGray), [s * 5.6, 3.6, -7.15]);
    reg('intake', 'Cheek float slot', 'routed slot in the cheek plate', 1,
      'Vertical travel path for the floating shaft — bounds the 0.7 in of give.',
      P.plateV(0.36, 1.5, 0.05, M.holeDark), [s * 5.56, 4.35, -7.15]);
  }
  const rollerB = reg('intake', 'Traction roller', '2" rubberized roller, ribbed grip surface', 1,
    'First contact — pulls POLLEN off the tile. Surface speed matched to ~1.4× drive speed.',
    P.tractionRoller(1.0, 10.2), [0, 1.45, -7.15]);
  const rollerT = reg('intake', 'Compliant star roller', '9× 6-point silicone stars on 8 mm REX', 1,
    'Conforms to ball tops; star phases offset so there is always contact.',
    P.starRoller(1.55, 10.2), [0, 3.6, -7.15]);
  anim.intake.push({ obj: rollerB, speed: 9 }, { obj: rollerT, speed: -9 });
  reg('intake', 'Intake motor — compact 5203', '312 rpm, #25 chain drive', 1,
    'Mounted under the hopper incline; chain runs inside the rail channel.',
    P.compactMotor(), [4.0, 1.92, -3.3]);
  reg('intake', 'Motor clamp — compact', 'split-ring clamp on the motor can', 1,
    'Grips the motor can at the belly standoffs — swap without pulling the sprocket.',
    P.clampBlock(0.72), [2.5, 1.92, -3.3]);
  reg('intake', 'Intake motor shaft', '8 mm REX hex, through rail wall', 1,
    'Short jackshaft carrying motor power through the rail wall to the sprocket.',
    P.hexShaft(1.3), [5.4, 1.92, -3.3]);
  reg('intake', 'Intake drive sprocket — 9T', '#25 steel sprocket', 1,
    'Driver — small sprocket trades speed for torque into the roller loop.',
    P.spurGear(9, 0.4, 0.15), [5.75, 1.92, -3.3], [0, 0, Math.PI / 2]);
  reg('intake', 'Intake driven sprocket — 16T', '#25 steel sprocket, outboard of cheek', 1,
    'Driven sprocket on the roller shaft — ~1.8:1 reduction from the motor.',
    P.spurGear(16, 0.75, 0.15), [5.75, 1.45, -7.15], [0, 0, Math.PI / 2]);
  reg('intake', 'Intake chain — #25', 'steel roller chain loop inside rail channel', 1,
    'Continuous loop linking the motor sprocket to the roller shaft.',
    P.chainLoop([1.92, -3.3], 0.5, [1.45, -7.15], 0.85, 5.75));
  reg('intake', 'Chain guard', '2 mm polycarb cover over the chain run', 1,
    'Keeps fingers and game elements out of the chain pinch point.',
    P.plateV(1.0, 4.6, 0.06, M.polycarbSolid), [5.95, 2.6, -5.3], [0.28, Math.PI / 2, 0]);
  reg('intake', 'Chain master link', 'clip-style connecting link on the #25 loop', 1,
    'Removable service link — bright side plates mark it on the straight run.',
    P.plateV(0.34, 0.2, 0.1, M.alu), [5.75, 1.7, -5.2], [0.11, Math.PI / 2, 0]);
  reg('intake', 'Intake drive shaft', '8 mm REX hex, full width', 1,
    'Full-width axle both rollers key into — carries torque across to the far cheek.',
    P.hexShaft(11.5), [0, 1.45, -7.15]);
  // meshing gear pair on the right cheek — counter-rotates the rollers
  reg('intake', 'Roller spur gear — 24T', '15 DP acetal, 1:1', 1,
    'Bottom roller drives the top roller counter-rotating — both pull balls inward.',
    P.spurGear(24, 1.08, 0.22), [5.24, 1.45, -7.15], [0, 0, Math.PI / 2]);
  reg('intake', 'Roller spur gear — 24T', '15 DP acetal, 1:1', 1, '',
    P.spurGear(24, 1.08, 0.22), [5.24, 3.6, -7.15], [0, 0, Math.PI / 2]);
  reg('intake', 'Cheek flange bearing', '8 mm flange bearing', 1,
    'Supports each roller shaft in the cheek plate — one bearing per shaft end.',
    P.bearing(), [5.45, 1.45, -7.15]);
  reg('intake', 'Cheek flange bearing', '8 mm flange bearing', 1, '',
    P.bearing(), [5.45, 3.6, -7.15]);
  reg('intake', 'Cheek flange bearing', '8 mm flange bearing', 1, '',
    P.bearing(), [-5.45, 1.45, -7.15], [0, Math.PI, 0]);
  reg('intake', 'Cheek flange bearing', '8 mm flange bearing', 1, '',
    P.bearing(), [-5.45, 3.6, -7.15], [0, Math.PI, 0]);
  reg('intake', 'Exit ramp', '2 mm polycarbonate', 1,
    'Chute over the crown channel — hands balls down into the hopper throat.',
    P.plate(10.2, 2.8, 0.07, M.polycarb), [0, 4.5, -6.2], [-0.45, 0, 0]);

  /* ================= HOPPER ================= */
  // inclined floor — ends ahead of the column mouth
  reg('hopper', 'Hopper floor — incline', '3 mm polycarbonate, 20° incline', 1,
    'Balls stage single-file and roll toward the feed column.',
    P.plate(4.2, 4.5, 0.09, M.polycarbSolid), [0, 3.58, -2.45], [-0.34, 0, 0]);
  for (const s of [-1, 1]) {
    reg('hopper', 'Hopper side wall', '3 mm polycarbonate', 1,
      'Clear walls keep balls channelled single-file while jams stay visible.',
      P.plateV(7.6, 3.4, 0.09, M.polycarbSolid), [s * 2.15, 5.4, -0.9], [0, Math.PI / 2, 0]);
  }
  reg('hopper', 'Hopper rear curb', '3 mm polycarbonate', 1,
    'Low curb sealing the gap under the column mouth — the tube shell is the rear stop.',
    P.plateV(4.3, 0.8, 0.09, M.polycarbSolid), [0, 4.3, 2.75], [0, 0, 0]);
  // agitator paddle + servo
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
    agit, [0, 4.55, -2.6]);
  anim.agitator = agit;
  reg('hopper', 'Agitator servo', 'standard servo, 180°', 1,
    'Oscillates the paddle ±45° at the low corner — breaks bridges over the feed nip.',
    P.servoMotor(), [2.9, 4.55, -2.6], [0, 0, Math.PI / 2]);
  reg('hopper', 'Agitator drive horn', 'servo horn bar to the paddle shaft', 1,
    'Clamp-fit horn linking the servo spline to the paddle shaft.',
    P.plate(0.5, 0.08, 0.14, M.alu), [2.45, 4.55, -2.6]);
  // feed wheel + column
  const feedW = reg('hopper', 'Feed wheel — compliant', '3.2" green compliant wheel', 1,
    'Meters one ball per rev-segment into the column; compliance handles both POLLEN and NECTAR.',
    P.compliantWheel(1.6, 0.9), [0, 5.15, 1.45], [0, 0, Math.PI / 2]);
  feedW.rotation.order = 'ZYX';
  anim.feed.push({ obj: feedW, speed: 6 });
  reg('hopper', 'Feed motor — compact 5203', '435 rpm, on belly stand-offs', 1,
    'Parallel-shaft drive: drops power to the feed axle through a 28T gear pair — clears the hopper wall and feed column.',
    (() => {
      const g = new THREE.Group();
      g.add(P.compactMotor());
      for (const px of [-1.7, -0.4]) {
        const post = P.pillar(0.92, 0.14, M.alu);
        post.position.set(px, -1.24, 0);
        g.add(post);
      }
      return g;
    })(), [4.0, 2.8, 1.45]);
  reg('hopper', 'Motor clamp — compact', 'split-ring clamp on the motor can', 1,
    'Clamps the feed motor to its standoff posts.',
    P.clampBlock(0.72), [2.5, 2.8, 1.45]);
  reg('hopper', 'Feed spur gear — 28T', '15 DP acetal, 1:1 drop pair', 1,
    'On the feed axle; meshes the motor pinion below.',
    P.spurGear(28, 1.17, 0.22), [4.7, 5.15, 1.45], [0, 0, Math.PI / 2]);
  reg('hopper', 'Feed spur gear — 28T', '15 DP acetal, 1:1 drop pair', 1, '',
    P.spurGear(28, 1.17, 0.22), [4.7, 2.8, 1.45], [0, 0, Math.PI / 2]);
  reg('hopper', 'Feed shaft — 8 mm REX', 'through-wall drive shaft', 1,
    'Carries the feed wheel through the hopper wall on a flange bearing.',
    P.hexShaft(5.2), [2.35, 5.15, 1.45]);
  reg('hopper', 'Feed wall bearing', '8 mm flange bearing', 1,
    'Supports the feed shaft where it exits the hopper wall.',
    P.bearing(), [2.15, 5.15, 1.45]);
  reg('hopper', 'Feed guide scoop', 'PETG front shroud', 1,
    'Keeps the ball seated through the lift arc into the column mouth.',
    P.plateV(3.6, 1.9, 0.08, M.print), [0, 5.15, -0.35]);
  reg('hopper', 'Feed column — clear 4"', '4" ID clear polycarbonate tube', 1,
    'Rises through the turret axis — ammo feed is independent of yaw. Lower band is windowed for the feed wheel.',
    (() => {
      const upper = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, 3.0, 28, 1, true), M.tube);
      upper.position.y = 1.15; upper.castShadow = false;
      // lower band has a -Z window so the feed wheel can enter the bore
      const lower = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, 2.3, 28, 1, true, Math.PI + 0.5, Math.PI * 2 - 1.0), M.tube);
      lower.position.y = -1.5; lower.castShadow = false;
      const g = new THREE.Group(); g.add(upper, lower);
      const lip = new THREE.Mesh(new THREE.TorusGeometry(2.02, 0.07, 8, 28).rotateX(Math.PI / 2), M.accent);
      lip.position.y = -2.65; lip.castShadow = true; g.add(lip);
      const lip2 = lip.clone(); lip2.position.y = 2.65; g.add(lip2);
      return g;
    })(), [0, 7.35, 2.6]);
  reg('hopper', 'Column base flange', 'machined ring clamping the tube to the deck', 1,
    'Clamps the tube square to the deck — sets the column vertical through the turret axis.',
    (() => {
      const g = new THREE.Group();
      g.add(P.plate(4.6, 4.6, 0.08, M.alu));
      const ring = new THREE.Mesh(new THREE.TorusGeometry(2.06, 0.09, 8, 32).rotateX(Math.PI / 2), M.alu);
      ring.position.y = 0.08; ring.castShadow = true;
      g.add(ring);
      return g;
    })(), [0, 5.02, 2.6]);
  reg('hopper', 'Gate servo + flag', 'micro servo, one-ball metering flag', 1,
    'Closes the column mouth between shots so flywheel recovery isn\'t wasted.',
    (() => {
      const g = P.servoMotor();
      const flag = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.08, 1.4), M.accent);
      flag.position.set(0.35, 0.62, 0.7); flag.castShadow = true;
      g.add(flag);
      return g;
    })(), [-2.9, 6.6, 2.6], [0, 0, Math.PI / 2]);
  // ball staged inside the clear column — visible through the tube
  reg('hopper', 'POLLEN (in column)', 'Ø2.8" element queued at the gate flag', 1,
    'Static staged ball — hidden during the match demo while real feeds run through.',
    P.ball(1.4, M.pollen), [0, 6.55, 2.6]);
  reg('hopper', 'Entry color sensor', 'I2C color/proximity sensor', 1,
    'Counts balls in, identifies NECTAR vs POLLEN for shot-speed lookup.',
    P.plateV(0.8, 0.6, 0.1, M.pcb), [2.28, 3.4, -3.4], [0, Math.PI / 2, 0]);

  /* ================= TURRET (static) ================= */
  // tower side plates + deck
  for (const s of [-1, 1]) {
    reg('turret', 'Tower cheek', '3 mm polycarbonate tower riser', 1,
      'Vertical risers forming the tower bay — carry the deck and electronics shelf.',
      P.plateV(8.0, 7.2, 0.09, M.polycarbSolid), [s * 5.15, 6.0, 4.0], [0, Math.PI / 2, 0]);
    reg('turret', 'Tower brace — diagonal', '3 mm PETG gusset tying cheek to deck', 1,
      'Triangulates the cheek-to-deck joint against launch recoil.',
      P.gusset(2.6, 2.6, 0.09, M.print), [s * 5.0, 6.6, 6.2], [0, s > 0 ? -Math.PI / 2 : Math.PI / 2, 0]);
  }
  reg('turret', 'Turret deck', '4 mm PETG deck plate', 1,
    'Carries the lazy susan; central bore passes the feed column.',
    (() => {
      const s = new THREE.Shape();
      s.moveTo(-5.15, -4.4); s.lineTo(5.15, -4.4); s.lineTo(5.15, 4.4); s.lineTo(-5.15, 4.4); s.closePath();
      const hole = new THREE.Path(); hole.absarc(0, -1.2, 2.15, 0, Math.PI * 2, true); s.holes.push(hole);
      const hole2 = new THREE.Path(); hole2.absarc(3.4, -1.2, 0.45, 0, Math.PI * 2, true); s.holes.push(hole2);
      const geo = new THREE.ExtrudeGeometry(s, { depth: 0.14, bevelEnabled: false });
      geo.rotateX(-Math.PI / 2);
      const m = new THREE.Mesh(geo, M.print); m.castShadow = m.receiveShadow = true;
      const g = new THREE.Group(); g.add(m);
      return g;
    })(), [0, 9.6, 1.4]);
  reg('turret', 'Lazy susan bearing', '5.2" ball-bearing ring', 1,
    'Full-rotation turret race; 20 ball track.',
    P.lazySusan(2.6), [0, 9.74, 2.6]);
  reg('turret', 'Yaw servo — continuous', 'dual-mode continuous-rotation servo', 1,
    'Under-deck mount: output shaft rises through the deck bore to drive the 14T pinion → ~190°/s slew with encoder homing.',
    (() => {
      const g = new THREE.Group();
      g.add(P.servoMotor());
      const tray = P.plate(2.8, 1.5, 0.08, M.alu);
      tray.position.set(0.6, -0.49, 0);
      g.add(tray);
      return g;
    })(), [3.05, 9.11, 2.6]);
  reg('turret', 'Yaw pinion — 14T', '15 DP brass on REX shaft', 1,
    'Meshes the 72T ring gear — 3.4" center distance, teeth inside the ring band.',
    (() => {
      const g = new THREE.Group();
      g.add(P.spurGear(14, 0.5, 0.24));
      const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.5, 6), M.steel);
      sh.position.y = -0.22; sh.castShadow = true;
      g.add(sh);
      return g;
    })(), [3.4, 9.93, 2.6]);
  // yaw homing: magnet on the plate rim sweeps a hall sensor on the deck
  reg('turret', 'Hall sensor — yaw index', 'magnetic reed on the static deck', 1,
    'Index pulse homes the turret yaw encoder each boot.',
    P.plateV(0.34, 0.2, 0.16, M.pcb), [3.15, 9.78, 2.6]);

  /* ================= LAUNCHER (rotating) ================= */
  const turret = new THREE.Group();          // rotates about Y at (0,?,2.6)
  turret.position.set(0, 0, 2.6);
  groups.launcher.add(turret);
  anim.turret = turret;
  {
    reg('launcher', 'Turret ring gear — 72T', '15 DP acetal ring, bolted under the rotating plate', 1,
      '5.14:1 with the servo pinion; homed against an index magnet.',
      P.ringGear(2.9, 72, 0.28), [0, 9.83, 0], [0, 0, 0], turret);
    // rotating plate with center hole
    const plateShape = new THREE.Shape();
    plateShape.absarc(0, 0, 3.35, 0, Math.PI * 2);
    const ph = new THREE.Path(); ph.absarc(0, 0, 2.1, 0, Math.PI * 2, true);
    plateShape.holes.push(ph);
    const pg = new THREE.ExtrudeGeometry(plateShape, { depth: 0.14, bevelEnabled: false });
    pg.rotateX(-Math.PI / 2);
    const tplate = new THREE.Mesh(pg, M.accent); tplate.castShadow = tplate.receiveShadow = true;
    reg('launcher', 'Turret rotating plate', '4 mm acetal disc, Ø6.7"', 1,
      'Everything above this line rotates together.', tplate, [0, 10.11, 0], [0, 0, 0], turret);

    // cheek plates on rotating plate
    for (const s of [-1, 1]) {
      reg('launcher', 'Launcher cheek plate', '5 mm PETG', 1, 'Flywheel + hood bearing mounts.',
        P.plateV(4.4, 2.9, 0.12, M.print), [s * 2.62, 11.6, 0], [0, Math.PI / 2, 0], turret);
      reg('launcher', 'Flywheel motor — 5203', '6000 rpm class, 1:1 to wheel', 1,
        'Independent left/right speed control trims lateral spin → straight shots at range.',
        P.compactMotor(), [s * 4.0, 11.1, 0.55], [0, s > 0 ? Math.PI : 0, 0], turret);
      const fw = P.flywheel(1.75, 0.72);
      fw.rotation.order = 'ZYX';
      reg('launcher', 'Flywheel — 3.5"', 'balanced aluminum + urethane tread band', 1,
        'Counter-rotating pair; 2.9" nip compresses NECTAR ~19% for grip.',
        fw, [s * 1.8, 11.1, 0.55], [0, 0, Math.PI / 2], turret);
      anim.fly.push({ obj: fw, speed: s * 34 });
      reg('launcher', 'Flywheel bearing', '8 mm flange bearing', 1,
        'Supports each flywheel shaft outboard of the cheek — takes the nip side-load.',
        P.bearing(), [s * 2.62, 11.1, 0.55], [0, s < 0 ? Math.PI : 0, 0], turret);
      reg('launcher', 'Motor clamp — compact', 'split-ring clamp on the motor can', 1,
        'Straps the flywheel motor can to the turret plate — no slop at launch rpm.',
        P.clampBlock(0.72), [s * 5.5, 11.1, 0.55], [0, 0, 0], turret);
    }
    // hood — pivots at rear of cheeks
    const hood = new THREE.Group();
    const hoodPlate = new THREE.Mesh(new THREE.BoxGeometry(4.6, 0.1, 2.9), M.accent);
    hoodPlate.castShadow = hoodPlate.receiveShadow = true;
    hoodPlate.position.z = -1.35;
    hood.add(hoodPlate);
    const hoodLip = new THREE.Mesh(new THREE.BoxGeometry(4.6, 0.5, 0.09), M.accent);
    hoodLip.position.set(0, 0.22, -2.72); hoodLip.castShadow = true;
    hood.add(hoodLip);
    reg('launcher', 'Adjustable hood', '2 mm anodized aluminum, servo-linked', 1,
      'Exit angle 40–65°: shallow lob for the HIVE cell, steep drop for FLOWER tops.',
      hood, [0, 12.55, 1.35], [-0.9, 0, 0], turret);
    anim.hood = hood;
    reg('launcher', 'Hood servo', 'standard servo', 1,
      'Positions the hood through the linkage — holds exit angle under launch vibration.',
      P.servoMotor(), [2.62, 12.35, 1.2], [0, 0, 0], turret);
    reg('launcher', 'Hood linkage', 'steel pushrod', 1,
      'Rigid pushrod — servo horn to hood pivot, no compliance in the aim path.',
      P.plate(0.08, 1.6, 0.06, M.steel), [2.62, 12.7, 0.6], [0.6, 0, 0], turret);
    // turret wiring — service loops droop into the slip ring throat
    for (const s of [-1, 1])
      reg('electronics', 'Flywheel motor lead — on turret', '18 AWG pair, service loop', 1,
        'Droops through the slip ring throat — slack sized for unlimited yaw.',
        P.wireBundle([[s * 3.7, 10.9, 0.7], [s * 3.0, 10.3, -0.5], [s * 2.05, 9.9, -1.15]],
          [M.wireRed, M.wireBlack], 0.04, 0.08), [0, 0, 0], turret);
    reg('electronics', 'Hood servo lead — on turret', '22 AWG PWM, service loop', 1,
      'PWM lead routed alongside the flywheel service loop into the slip ring.',
      P.wireBundle([[2.9, 12.1, 1.5], [2.5, 10.8, 0.3], [1.9, 9.9, -0.9]]), [0, 0, 0], turret);
    // backplate behind nip — guides ball from column into nip (narrow enough to clear the column shell)
    reg('launcher', 'Nip backplate', 'curved ball guide (shown flat)', 1,
      'Directs the rising ball into the flywheel nip.',
      P.plateV(1.8, 1.8, 0.09, M.printGray), [0, 11.6, 1.5], [-0.25, 0, 0], turret);
    // camera on turret — front lip, lens faces the -Z exit direction, pitched up at the hive
    reg('launcher', 'Vision camera', 'global-shutter USB camera', 1,
      'Rides the turret — always faces the launch target. Reads CELL AprilTags for range + tip state.',
      P.webcam(), [0, 10.85, -2.3], [0.55, Math.PI, 0], turret);
    reg('launcher', 'Camera status LED', 'amber indicator', 1,
      'Streaming/exposure indicator readable from the pit side.',
      P.ledDot(0.05, M.ledOrange), [0.55, 11.05, -2.32], [0.55, 0, 0], turret);
    // index magnet rides the rotating plate rim — sweeps the hall sensor
    reg('launcher', 'Yaw index magnet', 'Ø6 mm neodymium in the plate edge', 1,
      'Trips the deck hall sensor once per revolution — turret homing reference.',
      P.pillar(0.1, 0.09, M.portWhite), [3.1, 10.2, 0], [0, 0, 0], turret);
    // hood pivot hardware on both cheeks + top stiffener bar
    for (const s of [-1, 1]) {
      reg('launcher', 'Hood pivot bearing', '8 mm flange bearing at the hood pivot', 1,
        'Hood swings on real bearings, not a bare bolt — keeps the exit angle repeatable.',
        P.bearing(), [s * 2.66, 12.55, 1.35], [0, s < 0 ? Math.PI : 0, 0], turret);
      reg('launcher', 'Hood pivot bolt', 'M4 shoulder bolt through the cheek', 1,
        'Shoulder bolt — the hood pivot axle running through both cheeks.',
        P.washer(0.12), [s * 2.7, 12.55, 1.35], [0, 0, 0], turret);
    }
    reg('launcher', 'Launcher top brace', 'PETG bar tying the cheek tops', 1,
      'Spans the cheek tops — keeps the nip width constant under belt load.',
      P.plate(5.0, 0.5, 0.09, M.print), [0, 12.92, 0.9], [0, 0, 0], turret);
  }

  /* ================= FLOWER LIFT ================= */
  // Two-stage cascade deposit lift — the feed column doubles as the elevator:
  // a servo Y-flap below the turret deck kicks one ball out the column's side
  // port, down the load chute (through a slot in the tower cheek), and into the
  // cradle. The mast raises the cradle ~14.6" so its rim clears the ~21.5"
  // FLOWER mouth, then a micro servo tips the ball in. Hard-stop collars cap
  // travel inside the R105 29" vertical limit.
  const liftS1 = new THREE.Group(), liftS2 = new THREE.Group();
  liftS1.name = 'lift-stage1'; liftS2.name = 'lift-stage2';
  groups.lift.add(liftS1); liftS1.add(liftS2);
  // mast — rear-left corner, rails stand on the side-rail top flange
  for (const x of [-6.2, -7.8]) {
    reg('lift', 'Lift guide rail', '14 mm slide extrusion, 10.6"', 1,
      'Fixed mast stage, bolted to the side-rail flange — sits behind the rear wheel.',
      P.slideRail(10.6), [x, 7.9, 7.3]);
  }
  reg('lift', 'Mast base plate', '3 mm aluminum on the side-rail flange', 1,
    'Distributes the mast loads into the side-rail top flange.',
    P.plate(2.3, 0.9, 0.09, M.alu), [-7.0, 2.62, 7.3]);
  reg('lift', 'Mast top tie', '3 mm aluminum', 1,
    'Closes the top of the guide-rail pair — sets rail parallelism under side load.',
    P.plateV(2.3, 0.45, 0.09, M.alu), [-7.0, 13.0, 7.3]);
  for (const x of [-6.2, -7.8])
    reg('lift', 'Travel stop collar', 'hard stop at full extension — R105/G416 physical stop', 1,
      'Physical travel limit — stage 1 cannot over-extend past this collar.',
      P.collar(), [x, 12.85, 7.3], [0, 0, Math.PI / 2]);
  // stage 1 — rides the fixed rails
  for (const x of [-6.2, -7.8]) {
    reg('lift', 'Stage-1 slide bar', '14 mm extrusion in the guide rails', 1,
      'Moving extrusion — carries the stage-2 rails and the cradle.',
      P.slideRail(9.4, 0.42, M.darkSteel), [x, 7.7, 7.3], [0, 0, 0], liftS1);
    for (const y of [3.35, 11.85])
      reg('lift', 'Slide truck — stage 1', 'acetal pad riding the rail', 1,
        'Low-friction pads keeping stage 1 square inside the fixed rails.',
        P.plate(0.5, 0.5, 0.3, M.holeDark), [x, y, 7.3], [0, 0, 0], liftS1);
  }
  reg('lift', 'Stage-1 cross tie', '3 mm aluminum', 1,
    'Synchronizes the two stage-1 bars so they lift together.',
    P.plateV(2.3, 0.4, 0.09, M.alu), [-7.0, 12.15, 7.3], [0, 0, 0], liftS1);
  reg('lift', 'Traveling pulley', 'sheave on the stage-1 tie — reels stage 2 at 2× rope rate', 1,
    'Moving sheave — doubles stage-2 travel per inch of stage-1 rise.',
    P.pulley(), [-7.0, 11.9, 7.05], [0, 0, 0], liftS1);
  // stage 2 — rides stage 1
  for (const x of [-6.2, -7.8]) {
    reg('lift', 'Stage-2 slide bar', '14 mm extrusion, inner stage', 1,
      'Innermost stage — carries the cradle arm at its top.',
      P.slideRail(8.6, 0.38, M.steel), [x, 7.45, 7.3], [0, 0, 0], liftS2);
    for (const y of [3.5, 11.3])
      reg('lift', 'Slide truck — stage 2', 'acetal pad riding stage 1', 1,
        'Low-friction pads riding inside the stage-1 channels.',
        P.plate(0.44, 0.44, 0.28, M.holeDark), [x, y, 7.3], [0, 0, 0], liftS2);
  }
  reg('lift', 'Stage-2 cross tie', '3 mm aluminum', 1,
    'Keeps the stage-2 bars paired; anchors the rope dead-end.',
    P.plateV(2.3, 0.4, 0.09, M.alu), [-7.0, 11.5, 7.3], [0, 0, 0], liftS2);
  // cradle — cantilevered forward of the mast so its rise path clears the
  // rotating turret plate (Ø6.7" swept radius) and both tower cheeks
  reg('lift', 'Cradle arm', '3 mm aluminum cantilever — carries the cradle forward of the mast', 1,
    'Offsets the cradle forward so its rise path clears the turret plate sweep.',
    P.plate(0.6, 2.6, 0.09, M.alu), [-7.0, 7.55, 6.15], [0, 0, 0], liftS2);
  const cradlePivot = new THREE.Group();
  cradlePivot.position.set(-7.0, 6.9, 5.0);
  liftS2.add(cradlePivot);
  cradlePivot.rotation.x = -0.1;
  reg('lift', 'Deposit cradle', 'PETG C-cup, 3.6" pocket, servo-tipped', 1,
    'Rises ~14.6" — rim ~22.3" clears the 21.5" FLOWER mouth; tips forward to drop NECTAR in.',
    P.cradleCup(1.8, 1.6), [0, 0, 0], [0, 0, 0], cradlePivot);
  reg('lift', 'Cradle foam liner', 'closed-cell foam ring — cushions the NECTAR seat', 1,
    'Soft seat — grips the NECTAR during transport and cushions the tip-out.',
    (() => {
      const m = new THREE.Mesh(new THREE.TorusGeometry(1.5, 0.12, 8, 24).rotateX(Math.PI / 2), M.rubber);
      m.castShadow = true;
      return m;
    })(), [0, -0.35, 0], [0, 0, 0], cradlePivot);
  reg('lift', 'Tilt servo — cradle', 'micro servo on the arm', 1,
    'Rotates the cradle ~65° at full extension to pour the ball into the mouth.',
    P.servoMotor(), [-7.6, 7.7, 5.6], [0, Math.PI / 2, 0], liftS2);
  const liftBall = P.ball(1.8, M.nectarBlue);
  reg('lift', 'NECTAR (staged)', 'Ø3.6" alliance element — seated in the cradle', 1,
    'Loaded by the column diverter; drops on cradle tip.',
    liftBall, [0.1, 1.08, 0], [0, 0, 0], cradlePivot);
  liftBall.userData.vy = 0;
  // winch + rigging
  reg('lift', 'Lift winch — continuous servo', 'winch-mode servo, spool on the horn', 1,
    'Drives the cascade: dead-ends at stage 1, returns over the traveling pulley to stage 2.',
    P.servoMotor(), [-7.0, 2.0, 7.75], [-Math.PI / 2, 0, 0]);
  reg('lift', 'Winch spool', 'drum on the winch horn', 1,
    'Reels the dyneema — drum diameter sets the lift speed.',
    P.spool(), [-6.6, 2.0, 7.02]);
  reg('lift', 'Top pulley', 'sheave on the mast tie', 1,
    'Redirects the winch line down to the stage-1 anchor point.',
    P.pulley(), [-7.0, 12.85, 7.05]);
  reg('lift', 'Rope guide eyelet', 'welded ring — keeps the dead-end run off the rail', 1,
    'Aligns the dead-end run so it cannot jump the spool.',
    P.eyelet(), [-7.0, 3.0, 7.05], [Math.PI / 2, 0, 0]);
  reg('lift', 'Lift rope — dyneema', '1.5 mm UHMWPE run', 1,
    'Rigging path: winch → top pulley → stage-1 dead-end → traveling pulley → stage-2 tie.',
    P.cable([[-6.5, 2.05, 7.05], [-7.35, 3.6, 7.1], [-7.35, 12.4, 7.1], [-7.05, 12.8, 7.08]], M.wireBlack, 0.028));
  // moving rope legs — cylinder meshes rescaled each frame in main.js
  const rope1 = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 1, 6), M.wireBlack);
  const rope2 = rope1.clone();
  rope1.castShadow = rope2.castShadow = false;
  robot.add(rope1, rope2);
  anim.lift = { s1: liftS1, s2: liftS2, cradle: cradlePivot, ball: liftBall, ballState: 'cup', rope1, rope2 };
  // load path — column side port + cheek slot + chute into the parked cradle
  reg('lift', 'Column load port', 'cutout in the 4" column below the deck', 1,
    'Window in the tube wall — the diverter kicks one ball out through here.',
    P.plateV(0.85, 0.75, 0.07, M.holeDark), [-1.95, 9.25, 3.55], [0, -1.1, 0]);
  reg('lift', 'Column diverter — Y flap', 'servo flap inside the column top', 1,
    'Launch mode: flap closed, balls continue to the nip. Lift mode: kicks the ball out the port.',
    P.plateV(0.9, 1.1, 0.06, M.accent), [-1.75, 9.2, 3.35], [0, -1.1, 0]);
  reg('lift', 'Diverter servo', 'micro servo on the column shell', 1,
    'Positions the Y-flap — launch vs lift routing decided here.',
    P.servoMotor(), [-2.75, 8.85, 4.15], [0, 0, Math.PI / 2]);
  reg('lift', 'Tower cheek slot', 'load chute passes through the tower cheek', 1,
    'Routed opening — the load chute passes through the tower wall.',
    P.plateV(1.0, 1.15, 0.07, M.holeDark), [-5.18, 8.15, 4.5], [0, Math.PI / 2, 0]);
  reg('lift', 'Lift load chute', 'PETG tray — column port to cradle rim', 1,
    'Ball rolls port → cheek slot → cradle on ~35° slope.',
    (() => {
      const g = new THREE.Group();
      const floor = P.plate(0.95, 5.4, 0.07, M.print);
      floor.rotation.order = 'YXZ';
      floor.rotation.set(0.29, -1.28, 0);
      floor.position.set(-4.45, 8.42, 4.3);
      g.add(floor);
      for (const s of [-1, 1]) {
        const lip = P.plateV(5.4, 0.32, 0.06, M.print);
        lip.rotation.order = 'YXZ';
        lip.rotation.set(0.29, -2.86, 0);
        lip.position.set(-4.45 - s * 0.13, 8.55, 4.3 + s * 0.42);
        g.add(lip);
      }
      return g;
    })());

  /* ================= ELECTRONICS ================= */
  reg('electronics', 'Electronics shelf', '3 mm polycarbonate tray', 1,
    'Spans the tower bay; carries both hubs above the drive motors.',
    P.plate(10.2, 3.4, 0.08, M.polycarbSolid), [0, 3.36, 5.1]);
  reg('electronics', 'REV Control Hub', 'Android-based main controller', 1,
    'Runs the robot: pose estimation, turret PID, flywheel velocity loops.',
    P.controlHub(), [-2.55, 1.66, 2.15]);
  reg('electronics', 'REV Expansion Hub', 'secondary I/O hub', 1,
    'Splits motor/servo load; RS485-linked to the Control Hub. Shelf-mounted in the tower bay.',
    P.controlHub(), [0, 3.98, 5.1]);
  reg('electronics', 'Battery — 3000 mAh', '12 V NiMH, XT30', 1,
    'Main pack — strapped to the belly pan beside the Control Hub.',
    P.battery(), [-2.0, 1.81, -3.0]);
  reg('electronics', 'Main power switch', 'REV switch w/ bracket', 1,
    'Robot main disconnect — required to be reachable and labeled.',
    P.mainSwitch(), [-5.2, 2.0, 6.5], [0, Math.PI / 2, 0]);
  // ---- wiring: motor power runs to the Expansion Hub shelf ----
  const motorRuns = [
    // front-left drive motor → rail → shelf port
    [[-3.3, 2.6, -4.7], [-5.4, 1.35, -3.4], [-5.4, 1.15, 3.6], [-3.0, 1.5, 4.5], [-1.9, 3.55, 4.75]],
    // front-right
    [[3.3, 2.6, -4.7], [5.4, 1.35, -3.4], [5.4, 1.15, 3.6], [2.2, 3.3, 4.6], [1.4, 3.55, 4.78]],
    // rear-left
    [[-3.3, 2.6, 5.3], [-5.4, 1.3, 5.9], [-4.4, 1.5, 4.6], [-2.3, 3.55, 4.82]],
    // rear-right
    [[3.3, 2.6, 5.3], [5.4, 1.3, 5.9], [3.2, 2.3, 4.7], [1.9, 3.6, 4.85]],
    // intake motor → rail → shelf
    [[3.3, 2.4, -3.1], [5.4, 1.3, -1.4], [5.4, 1.2, 3.9], [2.4, 3.5, 4.65], [0.9, 3.6, 4.8]],
    // feed motor → shelf
    [[3.3, 3.3, 1.5], [4.9, 2.1, 2.6], [4.4, 2.3, 4.5], [0.5, 3.55, 4.82]],
  ];
  for (const run of motorRuns)
    reg('electronics', 'Motor power lead — 18 AWG pair', 'red/black twisted pair, loomed to Expansion Hub', 1,
      'Each motor home-runs to a hub port — loomed along the inside of the rails.',
      P.wireBundle(run, [M.wireRed, M.wireBlack], 0.045, 0.09));
  // ---- servo 3-wire looms ----
  const servoRuns = [
    // agitator
    [[3.5, 4.4, -2.4], [4.6, 2.5, -0.4], [4.4, 2.4, 4.4], [1.0, 3.7, 4.92]],
    // column gate
    [[-3.6, 6.2, 2.9], [-4.8, 4.2, 4.0], [-3.0, 3.75, 4.65], [-1.2, 3.7, 4.92]],
    // yaw servo under deck
    [[4.0, 8.6, 2.9], [4.9, 5.6, 4.2], [3.0, 3.9, 4.7], [0.2, 3.7, 4.92]],
    // diverter servo on the column
    [[-3.5, 8.4, 4.3], [-4.6, 6.2, 4.6], [-3.4, 3.95, 4.75], [-1.4, 3.7, 4.92]],
    // lift winch — down the mast, along the rear rail
    [[-7.5, 2.3, 7.2], [-7.4, 2.5, 4.2], [-5.6, 2.7, 4.6], [-2.0, 3.65, 4.88]],
  ];
  for (const run of servoRuns)
    reg('electronics', 'Servo extension — 3-wire', '22 AWG PWM extension, loomed', 1,
      'PWM extension loomed from each servo back to the Expansion Hub.',
      P.wireBundle(run));
  // tilt servo rides stage 2 — short loom parented to the stage
  reg('electronics', 'Servo extension — tilt (stage 2)', '22 AWG PWM, rides the moving stage', 1,
    'Service loop long enough for full stage-2 travel without snagging.',
    P.wireBundle([[-7.4, 7.4, 5.9], [-7.3, 5.9, 6.8], [-7.35, 4.2, 7.05]]), [0, 0, 0], anim.lift.s2);
  // ---- encoder / sensor runs to the Control Hub ----
  const encRuns = [
    [[-4.6, 1.85, -0.9], [-4.0, 1.45, 0.6], [-3.0, 1.5, 2.1], [-2.2, 1.95, 2.5]],
    [[4.6, 1.85, -0.9], [4.2, 1.4, 0.6], [2.6, 1.5, 2.2], [-0.9, 1.95, 2.9]],
    [[0.2, 1.9, 5.9], [-0.6, 1.5, 4.4], [-1.6, 1.7, 3.0], [-2.0, 1.95, 2.55]],
    // hopper color sensor
    [[2.9, 3.0, -3.3], [4.8, 1.4, -0.9], [4.6, 1.5, 3.4], [2.0, 1.9, 2.6], [-1.5, 2.0, 3.4]],
  ];
  for (const run of encRuns)
    reg('electronics', 'Sensor/encoder lead — 4-pin JST', '22 AWG I2C/quadrature run', 1,
      'I2C/quadrature runs — odometry pods and the hopper color sensor.',
      P.wireBundle(run, [M.wireYellow, M.wireBlack], 0.026, 0.06));
  // JST housings at the sensor/servo ends of the looms — keyed, serviceable joints
  for (const p of [[-4.6, 1.85, -0.9], [4.6, 1.85, -0.9], [0.2, 1.9, 5.9], [2.9, 3.0, -3.3], [3.5, 4.4, -2.4]])
    reg('electronics', 'Wire connector — JST', '4-pin JST-XH housing pair', 1,
      'Keyed connector where each loom meets its sensor or servo.',
      P.connector(0.3), p);
  // ---- power trunk: battery → switch → Control Hub ----
  reg('electronics', 'Battery → switch lead', '14 AWG silicone, XT30', 1,
    'Main power trunk to the switch — shortest practical route off the pack.',
    P.wireBundle([[1.4, 2.2, -2.7], [-0.8, 1.45, -0.6], [-3.4, 1.5, 2.0], [-4.6, 1.9, 5.6], [-4.95, 2.0, 6.2]],
      [M.wireRed, M.wireBlack], 0.06, 0.11));
  reg('electronics', 'Switch → hub lead', '14 AWG silicone', 1,
    'Switched feed into the Control Hub — downstream of the disconnect.',
    P.wireBundle([[-4.85, 2.0, 6.85], [-3.8, 1.75, 5.0], [-2.9, 1.85, 3.6], [-2.5, 2.1, 3.2]],
      [M.wireRed, M.wireBlack], 0.06, 0.11));
  // RS485 link between the two hubs
  reg('electronics', 'Hub RS485 link', '4-pin JST-PH, shielded', 1,
    'Expansion Hub data link — daisy-chained off the Control Hub port.',
    P.wireBundle([[-1.6, 2.3, 3.5], [-0.9, 2.9, 4.2], [-0.5, 3.6, 4.55]], [M.wireYellow, M.wireBlack], 0.03, 0.07));
  // camera USB — hub port up the tower to the slip-ring side
  reg('electronics', 'Camera USB lead', 'USB 2.0 pigtail through the slip ring', 1,
    'Vision feed — climbs the tower to the slip ring and out to the turret camera.',
    P.wireBundle([[-1.3, 2.2, 3.3], [0.8, 2.9, 4.3], [2.6, 5.0, 4.5], [2.4, 8.6, 3.1], [1.9, 9.6, 2.6]],
      [M.wireBlack], 0.05, 0));
  reg('electronics', 'USB ferrite bead', 'snap-on choke on the camera lead', 1,
    'EMI choke — keeps motor/encoder noise off the image feed.',
    P.pillar(0.5, 0.09, M.holeDark), [2.42, 8.1, 3.35], [0.5, 0, 0.3]);
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
    })(), [-4.85, 2.0, 6.35]);
  // slip ring on the feed column — passes power/signal to the rotating turret
  reg('electronics', 'Turret slip ring', '8-circuit capsule slip ring on the column', 1,
    'Keeps turret wiring twist-free through unlimited yaw.',
    P.slipRing(), [0, 9.45, 2.6]);
  // zip ties on the long rail runs + servo loom anchors on the tower
  for (const s of [-1, 1]) for (const z of [-1.6, 1.8])
    reg('electronics', 'Cable tie', '4" nylon zip tie', 1,
      'Loom anchors along the rail and tower runs — snipped flush after routing.',
      P.zipTie(0.14), [s * 5.4, 1.25, z]);
  for (const p of [[4.9, 5.6, 4.2], [-4.6, 6.2, 4.6], [-7.4, 2.5, 4.2]])
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
      for (const s of [-1, 1]) for (const z of [1.0, 3.4, 5.8, 7.4]) for (const y of [3.1, 8.9])
        l.push([s * 5.24, y, z]);
      return l;
    })(), 0.06, 0.09, 'x'));
  reg('hopper', 'Plate bolts — hopper walls', 'M4 socket head', 16,
    'Fasten the hopper wall panels to the floor and braces.',
    P.boltField((() => {
      const l = [];
      for (const s of [-1, 1]) for (const z of [-4.0, -2.0, 0.2, 2.2]) for (const y of [4.0, 6.8])
        l.push([s * 2.24, y, z]);
      return l;
    })(), 0.06, 0.09, 'x'));
  reg('intake', 'Plate bolts — intake cheeks', 'M4 socket head', 8,
    'Bolt the intake cheeks to the front rail and gussets.',
    P.boltField((() => {
      const l = [];
      for (const s of [-1, 1]) for (const z of [-8.3, -6.0]) for (const y of [1.0, 4.0])
        l.push([s * 5.36, y, z]);
      return l;
    })(), 0.06, 0.09, 'x'));
  reg('electronics', 'Shelf bolts', 'M4 socket head', 8,
    'Attach the electronics shelf across the tower bay.',
    P.boltField([[-4.5, 3.44, 4.2], [-2.5, 3.44, 4.2], [2.5, 3.44, 4.2], [4.5, 3.44, 4.2],
      [-4.5, 3.44, 6.0], [-2.5, 3.44, 6.0], [2.5, 3.44, 6.0], [4.5, 3.44, 6.0]], 0.06, 0.09, 'y'));
  reg('turret', 'Deck bolts', 'M4 socket head', 8,
    'Clamp the turret deck plate to the tower cheeks.',
    P.boltField([[-4.6, 9.75, -1.8], [4.6, 9.75, -1.8], [-4.6, 9.75, 4.4], [4.6, 9.75, 4.4],
      [-1.6, 9.75, -1.8], [1.6, 9.75, -1.8], [-1.6, 9.75, 4.4], [1.6, 9.75, 4.4]], 0.06, 0.09, 'y'));
  reg('lift', 'Mast mount bolts', 'M4 socket head', 8,
    'Bolt the mast base plate and top tie to the rail flange.',
    P.boltField([[-7.9, 2.7, 6.95], [-6.1, 2.7, 6.95], [-7.9, 2.7, 7.65], [-6.1, 2.7, 7.65],
      [-7.9, 13.0, 7.18], [-6.1, 13.0, 7.18], [-7.9, 13.0, 7.42], [-6.1, 13.0, 7.42]], 0.055, 0.08, 'y'));

  // ammo staged in hopper for looks (3 pollen) — ride the incline surface
  const ballsGroup = new THREE.Group();
  for (let i = 0; i < 3; i++) {
    const b = P.ball(1.4, M.pollen);
    const z = -3.6 + i * 2.15;
    b.position.set(0, 4.85 + (z + 0.9) * 0.36, z);
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
    'Side rail — U-channel': ['Motor mount plate', 'Flange bearing — rail', 'Corner gusset', 'Rail end cap', 'Belly pan'],
    'Motor mount plate': ['Drive motor — 5203 + UltraPlanetary', 'Side rail — U-channel'],
    'Drive motor — 5203 + UltraPlanetary': ['Motor pinion — 15T brass', 'Wheel axle — 8 mm REX', 'Motor mount plate', 'Motor power lead — 18 AWG pair'],
    'Wheel axle — 8 mm REX': ['Flange bearing — rail', '96 mm mecanum wheel', 'Shaft collar', 'Axle nut — nylock', 'Motor pinion — 15T brass'],
    'Flange bearing — rail': ['Wheel axle — 8 mm REX', 'Side rail — U-channel'],
    '96 mm mecanum wheel': ['Wheel axle — 8 mm REX', 'Axle nut — nylock', 'Flange bearing — rail'],
    'Shaft collar': ['Wheel axle — 8 mm REX'],
    'Axle nut — nylock': ['Wheel axle — 8 mm REX', '96 mm mecanum wheel'],
    'Motor pinion — 15T brass': ['Drive motor — 5203 + UltraPlanetary', 'Wheel axle — 8 mm REX'],
    'Rear crossmember — U-channel': ['Side rail — U-channel', 'Corner gusset'],
    'Front crown crossmember — raised': ['Side rail — U-channel', 'Intake cheek plate', 'Exit ramp'],
    'Rail end cap': ['Side rail — U-channel'],
    'Belly pan': ['Side rail — U-channel', 'Odometry pod — lateral', 'Odometry pod — longitudinal', 'REV Control Hub'],
    'Corner gusset': ['Side rail — U-channel', 'Rear crossmember — U-channel'],
    'Odometry pod — lateral': ['Sensor/encoder lead — 4-pin JST', 'Belly pan'],
    'Odometry pod — longitudinal': ['Sensor/encoder lead — 4-pin JST', 'Belly pan'],
    'Alliance number plate — rear': ['Rear crossmember — U-channel'],
    'Alliance number plate — left': ['Side rail — U-channel'],
    'Frame hardware — M4 socket head': ['Side rail — U-channel'],

    'Intake cheek plate': ['Torsion spring — floating roller', 'Cheek flange bearing', 'Intake gusset', 'Front crown crossmember — raised'],
    'Torsion spring — floating roller': ['Compliant star roller', 'Intake cheek plate'],
    'Intake gusset': ['Intake cheek plate', 'Side rail — U-channel'],
    'Traction roller': ['Intake drive shaft', 'Roller spur gear — 24T', 'Cheek flange bearing'],
    'Compliant star roller': ['Roller spur gear — 24T', 'Cheek flange bearing', 'Torsion spring — floating roller'],
    'Intake motor — compact 5203': ['Intake drive sprocket — 9T', 'Intake motor shaft', 'Motor power lead — 18 AWG pair', 'Motor clamp — compact'],
    'Intake motor shaft': ['Intake motor — compact 5203', 'Intake drive sprocket — 9T'],
    'Intake drive sprocket — 9T': ['Intake chain — #25', 'Intake motor shaft'],
    'Intake driven sprocket — 16T': ['Intake chain — #25', 'Intake drive shaft'],
    'Intake chain — #25': ['Intake drive sprocket — 9T', 'Intake driven sprocket — 16T', 'Chain guard', 'Chain master link'],
    'Chain master link': ['Intake chain — #25'],
    'Chain guard': ['Intake chain — #25'],
    'Intake drive shaft': ['Traction roller', 'Intake driven sprocket — 16T', 'Roller spur gear — 24T', 'Cheek flange bearing'],
    'Roller spur gear — 24T': ['Traction roller', 'Compliant star roller', 'Intake drive shaft'],
    'Cheek flange bearing': ['Intake cheek plate', 'Intake drive shaft', 'Compliant star roller'],
    'Exit ramp': ['Front crown crossmember — raised', 'Hopper floor — incline'],

    'Hopper floor — incline': ['Hopper side wall', 'Feed wheel — compliant', 'POLLEN (staged)', 'Exit ramp'],
    'Hopper side wall': ['Hopper floor — incline', 'Hopper rear curb'],
    'Hopper rear curb': ['Hopper side wall', 'Feed column — clear 4"'],
    'Agitator paddle': ['Agitator servo'],
    'Agitator servo': ['Agitator paddle', 'Servo extension — 3-wire'],
    'Feed wheel — compliant': ['Feed shaft — 8 mm REX', 'Feed spur gear — 28T', 'Feed guide scoop', 'Feed column — clear 4"'],
    'Feed motor — compact 5203': ['Feed spur gear — 28T', 'Motor power lead — 18 AWG pair', 'Motor clamp — compact'],
    'Feed spur gear — 28T': ['Feed motor — compact 5203', 'Feed shaft — 8 mm REX', 'Feed wheel — compliant'],
    'Feed shaft — 8 mm REX': ['Feed wheel — compliant', 'Feed wall bearing', 'Feed spur gear — 28T'],
    'Feed wall bearing': ['Feed shaft — 8 mm REX'],
    'Feed guide scoop': ['Feed wheel — compliant', 'Feed column — clear 4"'],
    'Feed column — clear 4"': ['Gate servo + flag', 'Column diverter — Y flap', 'Turret slip ring', 'POLLEN (in column)', 'Nip backplate'],
    'Gate servo + flag': ['Feed column — clear 4"', 'Servo extension — 3-wire'],
    'POLLEN (in column)': ['Feed column — clear 4"', 'Gate servo + flag'],
    'Entry color sensor': ['Sensor/encoder lead — 4-pin JST', 'Hopper side wall'],
    'POLLEN (staged)': ['Hopper floor — incline'],

    'Tower cheek': ['Turret deck', 'Tower brace — diagonal', 'Tower cheek slot'],
    'Tower brace — diagonal': ['Tower cheek', 'Turret deck'],
    'Turret deck': ['Lazy susan bearing', 'Tower cheek', 'Yaw servo — continuous', 'Yaw pinion — 14T'],
    'Lazy susan bearing': ['Turret deck', 'Turret rotating plate', 'Turret ring gear — 72T'],
    'Yaw servo — continuous': ['Yaw pinion — 14T', 'Turret deck', 'Servo extension — 3-wire'],
    'Yaw pinion — 14T': ['Yaw servo — continuous', 'Turret ring gear — 72T'],

    'Turret ring gear — 72T': ['Yaw pinion — 14T', 'Turret rotating plate', 'Lazy susan bearing'],
    'Turret rotating plate': ['Turret ring gear — 72T', 'Launcher cheek plate', 'Lazy susan bearing'],
    'Launcher cheek plate': ['Flywheel bearing', 'Flywheel motor — 5203', 'Adjustable hood', 'Turret rotating plate', 'Vision camera'],
    'Flywheel motor — 5203': ['Flywheel — 3.5"', 'Flywheel motor lead — on turret', 'Launcher cheek plate', 'Motor clamp — compact'],
    'Flywheel — 3.5"': ['Flywheel motor — 5203', 'Flywheel bearing', 'Nip backplate', 'Adjustable hood'],
    'Flywheel bearing': ['Flywheel — 3.5"', 'Launcher cheek plate'],
    'Adjustable hood': ['Hood servo', 'Hood linkage', 'Launcher cheek plate', 'Hood pivot bearing'],
    'Hood pivot bearing': ['Adjustable hood', 'Hood pivot bolt', 'Launcher cheek plate'],
    'Hood servo': ['Hood linkage', 'Adjustable hood', 'Hood servo lead — on turret'],
    'Hood linkage': ['Hood servo', 'Adjustable hood'],
    'Nip backplate': ['Flywheel — 3.5"', 'Feed column — clear 4"'],
    'Vision camera': ['Camera USB lead', 'Camera status LED', 'Launcher cheek plate'],
    'Camera status LED': ['Vision camera'],

    'Lift guide rail': ['Slide truck — stage 1', 'Mast base plate', 'Travel stop collar', 'Mast top tie'],
    'Mast base plate': ['Lift guide rail', 'Side rail — U-channel'],
    'Mast top tie': ['Lift guide rail', 'Top pulley'],
    'Travel stop collar': ['Lift guide rail'],
    'Stage-1 slide bar': ['Slide truck — stage 1', 'Stage-1 cross tie', 'Lift guide rail'],
    'Slide truck — stage 1': ['Stage-1 slide bar', 'Lift guide rail'],
    'Stage-1 cross tie': ['Stage-1 slide bar', 'Traveling pulley'],
    'Traveling pulley': ['Stage-1 cross tie', 'Lift rope — dyneema'],
    'Stage-2 slide bar': ['Slide truck — stage 2', 'Stage-2 cross tie', 'Cradle arm'],
    'Slide truck — stage 2': ['Stage-2 slide bar'],
    'Stage-2 cross tie': ['Stage-2 slide bar', 'Lift rope — dyneema'],
    'Cradle arm': ['Deposit cradle', 'Tilt servo — cradle', 'Stage-2 slide bar'],
    'Deposit cradle': ['Cradle arm', 'Tilt servo — cradle', 'NECTAR (staged)', 'Lift load chute'],
    'Tilt servo — cradle': ['Deposit cradle', 'Servo extension — tilt (stage 2)'],
    'NECTAR (staged)': ['Deposit cradle'],
    'Lift winch — continuous servo': ['Winch spool', 'Lift rope — dyneema', 'Servo extension — 3-wire'],
    'Winch spool': ['Lift winch — continuous servo', 'Lift rope — dyneema'],
    'Top pulley': ['Mast top tie', 'Lift rope — dyneema'],
    'Lift rope — dyneema': ['Winch spool', 'Top pulley', 'Traveling pulley', 'Stage-2 cross tie'],
    'Column load port': ['Column diverter — Y flap', 'Lift load chute', 'Feed column — clear 4"'],
    'Column diverter — Y flap': ['Diverter servo', 'Column load port', 'Feed column — clear 4"'],
    'Diverter servo': ['Column diverter — Y flap', 'Servo extension — 3-wire'],
    'Tower cheek slot': ['Tower cheek', 'Lift load chute'],
    'Lift load chute': ['Column load port', 'Tower cheek slot', 'Deposit cradle'],

    'Electronics shelf': ['REV Expansion Hub', 'Tower cheek'],
    'REV Control Hub': ['Hub RS485 link', 'Switch → hub lead', 'Camera USB lead', 'Sensor/encoder lead — 4-pin JST', 'Belly pan'],
    'REV Expansion Hub': ['Hub RS485 link', 'Motor power lead — 18 AWG pair', 'Servo extension — 3-wire', 'Electronics shelf'],
    'Battery — 3000 mAh': ['Battery → switch lead', 'Belly pan'],
    'Main power switch': ['Battery → switch lead', 'Switch → hub lead'],
    'Motor power lead — 18 AWG pair': ['REV Expansion Hub', 'Drive motor — 5203 + UltraPlanetary', 'Intake motor — compact 5203', 'Feed motor — compact 5203'],
    'Servo extension — 3-wire': ['REV Expansion Hub', 'Agitator servo', 'Gate servo + flag', 'Yaw servo — continuous', 'Diverter servo', 'Lift winch — continuous servo'],
    'Servo extension — tilt (stage 2)': ['Tilt servo — cradle', 'REV Expansion Hub'],
    'Sensor/encoder lead — 4-pin JST': ['REV Control Hub', 'Odometry pod — lateral', 'Odometry pod — longitudinal', 'Entry color sensor', 'Wire connector — JST'],
    'Wire connector — JST': ['Sensor/encoder lead — 4-pin JST', 'Servo extension — 3-wire'],
    'Battery → switch lead': ['Battery — 3000 mAh', 'Main power switch'],
    'Switch → hub lead': ['Main power switch', 'REV Control Hub'],
    'Hub RS485 link': ['REV Control Hub', 'REV Expansion Hub'],
    'Camera USB lead': ['REV Control Hub', 'Turret slip ring', 'Vision camera'],
    'Turret slip ring': ['Camera USB lead', 'Flywheel motor lead — on turret', 'Hood servo lead — on turret', 'Feed column — clear 4"'],
    'Flywheel motor lead — on turret': ['Turret slip ring', 'Flywheel motor — 5203'],
    'Hood servo lead — on turret': ['Turret slip ring', 'Hood servo'],
    'Cable tie': ['Motor power lead — 18 AWG pair', 'Side rail — U-channel'],
    'Axle washer': ['Wheel axle — 8 mm REX', 'Flange bearing — rail'],
    'Motor clamp block': ['Drive motor — 5203 + UltraPlanetary', 'Motor mount plate'],
    'Float slide block': ['Compliant star roller', 'Cheek float slot', 'Torsion spring — floating roller'],
    'Cheek float slot': ['Intake cheek plate', 'Float slide block'],
    'Agitator drive horn': ['Agitator servo', 'Agitator paddle'],
    'Column base flange': ['Feed column — clear 4"', 'Turret deck'],
    'Hall sensor — yaw index': ['Yaw index magnet', 'Turret deck', 'Sensor/encoder lead — 4-pin JST'],
    'Yaw index magnet': ['Hall sensor — yaw index', 'Turret rotating plate'],
    'Hood pivot bolt': ['Adjustable hood', 'Launcher cheek plate', 'Hood pivot bearing'],
    'Launcher top brace': ['Launcher cheek plate'],
    'intake|Motor clamp — compact': ['Intake motor — compact 5203'],
    'hopper|Motor clamp — compact': ['Feed motor — compact 5203'],
    'launcher|Motor clamp — compact': ['Flywheel motor — 5203'],
    'Rope guide eyelet': ['Lift rope — dyneema', 'Mast base plate'],
    'Cradle foam liner': ['Deposit cradle', 'NECTAR (staged)'],
    'USB ferrite bead': ['Camera USB lead'],
    'Powerpole connector pair': ['Battery → switch lead', 'Main power switch'],
    'Plate bolts — motor mounts': ['Motor mount plate', 'Drive motor — 5203 + UltraPlanetary'],
    'Plate bolts — tower cheeks': ['Tower cheek', 'Turret deck'],
    'Plate bolts — hopper walls': ['Hopper side wall'],
    'Plate bolts — intake cheeks': ['Intake cheek plate'],
    'Shelf bolts': ['Electronics shelf', 'REV Expansion Hub'],
    'Deck bolts': ['Turret deck', 'Tower cheek'],
    'Mast mount bolts': ['Mast base plate', 'Mast top tie'],
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
    dims: { w: 17.5, d: 17.5, h: 13.3 },
    counts: { motors: 8, servos: 7 } };
}
