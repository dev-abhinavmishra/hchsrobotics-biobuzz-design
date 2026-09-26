# Change log - BIOBUZZ-Robot

## 2026-09-24 - Final audit + repo cleanup

- **Final CAD audit** — `selfcheck_rehaul02.py` re-run headless against the
  current tree: 47 checks, `RESULT: ALL PASS` (fresh
  `selfcheck_rehaul02_results.txt`). Flagged conflicts unchanged and
  documented: `VOL_BALL_PATH` vs `FRAME_RAIL_F`/`LIFTER_PED`,
  `LIP_RAMP` (scoop by design).
- **Viewer design audit** — vertex-exact robot bounds measured live:
  17.89" × 17.62" footprint, 13.22" stowed height (inside the 18" cube),
  wheels rest at y=0, lift tops out ~24.5" extended (< 29" cap). 136 BOM
  lines, zero dangling relation links, zero instanced-field qty/drawn
  mismatches, zero NaN transforms.
- **Cleanup** — removed `.playwright-mcp/` browser-test artifacts,
  `scripts/freecad/__pycache__/`, `.devin/spike_expr.py` + stray
  `.devin/mecanum_schematic.png` scratch files, unreferenced
  `exports/renders/fc_screenshot.png`, and the empty legacy
  `exports/{dxf,pdf,step,stl}` dirs (superseded by `prototype_*`).
- **Docs** — `.devin/instructions.md` updated: `selfcheck_rehaul02.py`
  is the current contract gate (was still pointing at rehaul01). Root
  `package.json` tidied (dropped nonexistent `main` + stub test).

## 2026-09-24 - Review fixes (`viewer/`)

- **Connected-parts graph** — `REL` keys can be subsystem-scoped
  (`sub|name`), and link resolution prefers a same-subsystem entry when a
  part name is registered in several. Fixes 'Motor clamp — compact' chips
  jumping to the intake clamp from the feed/flywheel motors, and each
  clamp claiming all three motors as relations.
- **Isolation state** — part **Isolate** now supersedes subsystem
  isolation (mirror of `isolate()` dropping part solo); "Show all" no
  longer leaves a stale active subsystem row with nothing ghosted.
- **Frame hardware** — added the missing bolt pair at the raised
  crown-member junction; drawn instance count now matches the ×24 BOM
  line.
- **Match demo hygiene** — `ball()` shares a cached `SphereGeometry` per
  radius (the demo spawns ~10 balls/run — no more per-run GPU buffer
  growth); Launch Demo restores the prior Animate state instead of
  leaving the toggle on; lift ball rest height corrected in field mode
  (was floating ~0.65" over the tiles).

## 2026-09-23 - Part Explorer + demo realism pass (`viewer/`)

- **Part Explorer** — new `Parts` tab lists all 130 BOM lines grouped by
  subsystem with live filter; click highlights every placed instance and
  frames it. Entries now track placed objects (`e.objs`) and carry a
  hand-built **relations graph** (`e.links`) — the inspector renders
  clickable "Connected parts" chips (motor→pinion→axle→bearing→wheel,
  winch→spool→rope→pulleys→stages, hubs→wire runs, …) plus Prev/Next BOM
  stepping. Scene click-picking now selects the whole entry.
- **Detail pass 2** — motor split clamps + encoder caps/ports, axle washers,
  floating-roller slide blocks + cheek slots, agitator servo horn, column
  base flange, yaw homing magnet + hall sensor, hood pivot bolts, launcher
  top brace, spool rope windings, rope guide eyelet, cradle foam liner,
  USB ferrite bead, powerpole pair at the switch.
- **Match demo realism** — intake rollers/feed wheel/flywheels/agitator are
  now gated per phase (`anim.gates`); pickups sweep in a two-stage path
  (floor slide → throat arc) then roll down the hopper incline visibly;
  every launch now **rises up the clear column first** (`riseLaunch`) before
  the ballistic lob; the FLOWER deposit visibly diverts a NECTAR out the
  column port and down the load chute into the cradle before the lift runs.
- **Spectator camera** — controls stay live during the demo: any drag takes
  a free camera ("Resume cinematic camera" button hands control back).
- Anim lists split (`anim.intake/feed/fly`) for per-phase gating.

## 2026-09-23 - Realism pass + scripted match demo (`viewer/`)

- **Procedural textures** (no external assets): canvas-drawn alliance number
  plates (27475), 36h11-style AprilTag faces, foam-tile waffle + bump, motor
  wrap labels, hub faceplate, gaffers-tape sheen, radial contact-shadow blob.
- **Robot detail** — full wiring loom (6 motor power pairs, 5 servo PWM
  extensions + stage-riding tilt lead, 4 encoder/sensor JST runs, battery →
  main switch → hub power trunk, hub RS485 link, camera USB through an
  8-circuit slip ring on the feed column), sealed bearings with flange bolts,
  motor cooling ribs + label bands + brass pinions, #25 roller chain with pin
  detail, nylock axle nuts, rail end caps, hub LEDs/labels/bolts, battery
  strap buckle + XT30, zip ties, instanced bolt fields on every major plate.
- **Field detail** — walls rebuilt as aluminum kick rail + clear polycarb
  panel + top cap + posts + corner posts; textured AprilTags on walls and
  hive-cell undersides; hive cells gain screen insets, mouth rims, and pivot
  bearings; flowers gain throat tube, petal collar, leaves, pipe collars and
  a base block; tape markings (center line, hive approach, zone borders).
- **Match Demo** (`viewer/js/demo.js`) — ~40 s scripted blue-alliance match:
  autonomous pollen intake sweep, AprilTag aim + 3-ball cell lob, teleop
  mecanum strafe to the nectar stash, 2 nectar launches that tip the hive,
  corner approach + lift deposit into the flower mouth, loading-zone park.
  Cinematic chase/fixed cameras, phase captions, wheel-spin and body-bob
  while driving, balls arc on bezier trajectories and stay in the cell.
- `viewer/serve.py` — no-store dev server; `python -m http.server` lets the
  browser cache ES modules and served stale code during iteration.
- `window.__bio` exposes { scene, robot, groups, entries, anim, refs, demo }
  for console debugging.

## 2026-09-23 - Flower deposit lift (`viewer/`)

Design-review finding (user): the robot could not reliably score in FLOWERS —
the flower mouth is a ~4" (101.5 mm) opening at ~21.5" (§9.7) for a 3.6" (91 mm)
NECTAR, leaving ~5 mm radial clearance; a flywheel lob into that window was
judged too unreliable. Replaced with a lift-and-place deposit (the FreeCAD
architecture's original nectar-lifter intent).

- **New subsystem `lift`** — two-stage cascade mast on slim guide rails in the
  rear-left corner (rails stand on the side-rail top flange, clear of the
  wheel), dyneema rigged from a continuous-servo winch: dead-end to stage 1,
  return over a traveling pulley to stage 2 (live rope legs update per frame).
  Hard-stop collars cap travel per R105/G416.
- **Load path reuses the feed column** — a servo Y-flap below the turret deck
  kicks one ball out a side port on the column (below the rotating-plate
  sweep), down a PETG load chute through a slot in the tower cheek, into the
  deposit cradle. No second ball path through the frame.
- **Cradle** — PETG C-cup cantilevered forward of the mast so its rise path
  clears the Ø6.7" rotating turret plate and the tower cheeks; micro-servo
  tips it at ~22" to drop NECTAR into the flower mouth. Staged NECTAR ball
  falls free on tip and re-seats on retract.
- **Compliance update** — servos 4→7 of 8 (winch, diverter, tilt); motors stay
  8/8; robot no longer claims "never leaves the cube": starts inside R101,
  lift tops ~26" against the R105 29" cap, footprint stays 18×18.
- **UI** — `Lift` toolbar button animates extend → tip → ball drop; callouts
  for the mast, cradle, and diverter; compliance panel updated.

## 2026-09-22 - Interactive Three.js design review (`viewer/`)

User-directed pivot away from the FreeCAD pipeline for visualization: a
self-contained Three.js design-review app covering the full competition
robot concept — no CAD software needed (`cd viewer; python -m http.server
8017`).

- **Robot** — 6 subsystems, ~130 placed parts merged into 70 BOM lines:
  17.5×17.5×13.3" mecanum chassis (never leaves the 18" cube),
  over/under intake → inclined hopper → feed column through the turret
  axis → dual-flywheel 360° turret launcher with AprilTag camera.
  Parametric part library in `js/parts.js` (U-channel, mecanum/omni
  wheels, gears, motors, servos, electronics).
- **Review features** — per-part inspector + tooltip pick, subsystem
  tree with isolate/X-ray/visibility toggles, exploded-view slider,
  callout labels, 18" sizing-cube overlay, camera presets, animated
  mechanisms (rollers, flywheels, turret slew, hood, agitator) and a
  launch demo that lobs a POLLEN into the HIVE cell and tips it.
- **Field at scale** — 36-tile 12' field, 12" walls, pivoting red/blue
  HIVE cells with underside AprilTags, 4 FLOWERS, loading zones, and
  manual-accurate staged elements (POLLEN in flowers/on floor, NECTAR in
  up-cells + alliance areas per TU01 §9).
- Compliance panel tracks R101/R105 + motor/servo counts. Vendored
  three.js r170 (matches `viewer/package-lock.json`); no build step, no
  external requests.

## 2026-09-21 - Rehaul sprint-02: intake + transfer component fidelity

Sprint-02 rebuild of the intake and transfer subsystems in
`master_robot.FCStd`, `intake_concept_v01.FCStd`, and
`transfer_concept_v01.FCStd` - all on the shared `partkit.py`
vocabulary, all dims expression-bound to `Parameters`.

- **Intake** - bored cheek plates (7 bores: shaft, pivot, bearing,
  mount, servo-strap), ribbed roller tube + 8 mm shaft + flanged
  bearings, bored pivot bosses with *stub* axles (no cross-shaft -
  clears the O91 ball path), pivot servo in the rail-mouth pocket on
  the bottom flange + clamp strap, mount L-brackets on the side-rail
  inner faces, intake lip sill. `VOL_INTAKE` widened to 340 for the
  shaft tips.
- **Transfer** - chamfered channel floor, bored walls (hinge bore +
  servo bolt pattern) with outer faces flush against the drive-motor
  inner faces (lane 101 mm > O91), saddle supports, bored diverter
  paddle on a 6 mm hinge axle through wall bushings, servo + horn on
  the wall outer face, route markers, `VOL_CHANNEL_CLEAR` +
  `VOL_BALL_PATH` probes. `VOL_TRANSFER` widened/dropped to cover the
  axle tips + saddle feet.
- **New aliases** - `nectar_dia`, `pollen_dia`, `paddle_sweep_deg`,
  roller/bearing/servo/bolt dims, channel sheet dims - all logged in
  `robot-parameters.md`.
- **Flagged integration conflicts** (documented, sprint-04 action):
  the straight `VOL_BALL_PATH` probe intersects `LIFTER_PED` (sprint-01
  pedestal sits inside the intake floor lane) and `FRAME_RAIL_F` (the
  intake mouth sits proud of the front rail - balls ride over it).
- **Verification** - `selfcheck_rehaul02.py`: PAR/PROV/DAG/ASM1-4/
  ENV1'/GEO8'/GEO-I/GEO-T/reserves/GUI/determinism/REG signature
  checks - ALL PASS. Determinism verified across two rebuilds and a
  mirror-tree rebuild (0 sig diffs). Exports: STL 174k facets, STEP
  28.9k entities, 16 PNG renders + master SVG views, view-state
  injected into all files.

## 2026-09-20 - Rehaul sprint-01: partkit drivetrain (component fidelity)

User-directed rehaul: replace the primitive placeholder chassis/drivetrain
with component-grade geometry in both `master_robot.FCStd` and
`drivebase_concept_v01.FCStd`, driven from a new shared kit
`scripts\freecad\partkit.py`. All changes remain expression-bound to the
`Parameters` sheet.

- **partkit.py** — predicate-based edge selection (`pred_axis`,
  `pred_radius`, `pred_at_z`, `pred_combine`), filleted plates, U-channel
  extrusions (cut solid + hole grid + shaft notches), shafts, bored hubs,
  bearing blocks, bored motor face plates, fused roller+pin bodies, and
  `mecanum_wheel` returning an `App::Part` carrier. TOOL-prefixed
  construction intermediates grouped under a `Tools` container.
- **Frame ring** — `FRAME_RAIL_*` (master) / `RAIL_*` (drivebase): real
  open U-channel sections (outer − void − holes − notches), Ø4 hole grid
  on flanges + web, Ø16 shaft notches through the side-rail mouths.
- **Sheets** — filleted `BELLY_PAN` on the lower flange lip; filleted
  `REAR_DECK_L/R` flanking the ball channel, ending forward of the rear
  motors.
- **Wheel assemblies** — `WHEEL_ASSY_*` carriers at ±140/±180 mm (moved
  inboard from ±170 so motors clear the end rails); per wheel a bored
  Ø26 hub, two chamfered Ø92 face plates, and 10 fused roller+pin bodies
  (~45° slant, FTC X-pattern) whose pins seat ~1 mm into the plates.
- **Drive chain** — per wheel: `MOTOR_*` Ø36×60 → `MOUNT_MOTOR_*` face
  plate on the web inner face → `SHAFT_*` 8 mm REX through face plate +
  web notch → `BEARING_*` flange block on the cavity face → cheek
  clearance bore → hub bore.
- **Mount-chain placeholders** — `INTAKE_MOUNT_*` cheek brackets,
  `CHANNEL_SUPP_*` saddles, `POST_SHOOTER_*` uprights +
  `SHOOTER_FLOOR`/`SHOOTER_SIDE_*` plates, `LIFTER_PED`/`LIFTER_BASE`,
  `ELEC_RAIL_*` standoffs — mechanism reps now physically contact the
  frame (0 connectivity islands).
- **Bug fixes during the sprint** — FreeCAD raw `.Shape` stays local for
  carrier children: all analysis/export now uses globalized copies;
  roller bodies fused with their pins (roller was unreachable inside
  carrier space); duplicate `Tools` group auto-rename (`Tools001`)
  removed.
- **Pipeline** — `render_png.py` (new shaded z-buffer PNGs, master +
  drivebase ×4 views), `render_views.py` and `export_prototypes.py`
  globalize shapes and exclude `TOOL_*`; `make_view_copy.py` styles both
  files + `*_view.FCStd` copies; new gate `selfcheck_rehaul01.py`
  supersedes `selfcheck_sprint06.py` (retained, runnable on the archived
  sprint-07 baseline).
- **Frozen Appendix-A overlap table** — 108 master pairs + 88 drivebase
  pairs enumerated by class (shaft/bore C1, pin seats C2, mount embeds
  C3, placeholder co-location C7) in `docs\mechanism-architecture.md`;
  undeclared overlaps are failures, never appended.

## 2026-09-20 — Sprint 07: cohesion + realism pass (user-directed)

User feedback: the model read as floating, disconnected primitive
clusters — no visible chassis tying wheels/mechanisms together, and the
tree was two flat containers. Changes (all parametric/expression-bound):

- **Chassis frame** — closed ring of four goBILDA-1120-style 48 mm
  channel rails (`FRAME_RAIL_L/R/F/B`, VENDOR-PENDING per D12) at
  z 0–48, `BELLY_PAN` sheet inside the ring, `REAR_DECK` half-deck over
  the rear bay. Wheels now visibly hang off the frame instead of
  floating.
- **Drive motors** — four `MOTOR_*` (5203 Yellow Jacket ~O36,
  VENDOR-PENDING) extending inboard through the side rails at each wheel
  hub; `WHEEL_PLATE_*_IN/OUT` O92 side discs on every wheel face.
- **Subsystem attachments** — `INTAKE_AXLE` pivot shaft through both
  intake cheeks; `POST_SHOOTER_L/R` uprights from the rear deck to the
  shooter floor; `LIFTER_PED` pedestal (belly pan to mast base) +
  `LIFTER_BASE` plate under the mast column. Nothing floats anymore.
- **Tree organization** — seven `App::Part` groups inside
  `RobotAssembly` (Envelopes, Drivebase, Intake, Transfer, Shooter,
  Lifter, Electronics); every solid assigned by name prefix.
- New aliases documented in `docs\robot-parameters.md`; new intentional
  contact classes (frame/mount overlaps) enumerated in
  `selfcheck_sprint06.py` — sprint-07 section in `exempt_pair`.

Results: master rebuilt to **193 objects / 111 valid solids, 0 invalid**
(was 107/90). Selfcheck ALL PASS. Re-exports: 94-solid STL
(32,360 facets), STEP reimport 95 solids, MANIFEST synced. SVG + PNG
renders regenerated; styled view re-injected into both FCStd files.
True fillets remain deferred — baked fillets would break the
expression-binding contract; the parametric-primitive look is
documented as the placeholder trade-off.

## 2026-09-20 — Viewing/render fix pass (post-epic, user-reported)

User report: the FCStd opened to a black/empty viewport and the SVG
renders looked buggy and sparse. Root causes and fixes:

- **Black viewport on open.** All sprint scripts run headless
  (freecadcmd), so the FCStd carried no view state: FreeCAD invented a
  default camera that could sit inside the opaque `ENV_*`/`VOL_*`
  packaging solids, and "Fit All" zoomed out to the `REF_HIVE`/`REF_FLOWER`
  field markers ~1.2 m away, shrinking the robot to a speck. Fix:
  `scripts\freecad\make_view_copy.py` injects a `GuiDocument.xml` into
  the FCStd zip — hides `ENV_*`/`VOL_*`/`REF_*`/`Origin`, colors the 70
  subsystem solids to match the render palette, and sets an orthographic
  isometric camera (az 45 / el 35.264, fitted). Written into both
  `cad\master_robot.FCStd` (in place; `Document.xml` and all `Shape.brp`
  payloads byte-identical — verified: 107 objects / 90 valid solids /
  88 expression-bound objects unchanged) and `cad\master_robot_view.FCStd`.
- **Buggy-looking SVGs.** The old overlay drew every edge of every solid
  (hidden, interior, and seam edges included) over the fills. The edge
  pass now draws only silhouette edges and sharp (>~25 deg dihedral)
  edges between front-facing faces — `visible_edges()` in
  `render_views.py`. Facets also get a subtle same-hue darker stroke,
  tessellation tightened to 0.5 mm, canvas raised to 1400 px.
- **New shaded PNG renders.** `scripts\freecad\render_png.py` rasterizes
  the same exportable set through a real z-buffer (numpy) so
  interpenetrating solids occlude correctly — impossible in the old
  painter's-order SVG. Writes `exports\renders\master_{front,side,top,
  iso}.png` with the same views and palette; pure-zlib PNG writer, no
  external deps.
- `scripts\freecad\view_robot.py` kept as the live-session restyle
  helper; note: FreeCAD 1.1 does not execute `.py` files passed as
  command-line arguments, so it runs via Macro -> Macros -> Run.

No geometry, alias, or parameter changes; verification counts identical
to the sprint-06 evaluator record.

## 2026-09-20 — Sprint 06: detail + accuracy pass (autonomous build)

Mechanism-level detail on every subsystem plus datasheet-driven corrections.
Still primitive, expression-bound placeholder geometry — never manufacturing
data. Master: 107 objects / 88 solids; export set grows 21 → 71 leaf solids.
(Contract counted "all 8 FCStd" — the repository has **7** live files; all 7
were archived under `cad\archive\*_sprint05_20260920_135103.FCStd` first.)

Geometry added:

- Mecanum roller placeholders: `ROLLER_{FL,FR,RL,RR}_00..09` — 10 per wheel
  (counted on goBILDA schematic 3606-0000-0096), Ø14 × 20 mm cylinders at
  ~45° slant, positions expression-bound (`cos/sin(k * mec_roll_pitch)`),
  FTC X-pattern (FL+RR one slant, FR+RL opposite). Roller surfaces reach the
  Ø96 datasheet diameter; flat-cap ends stay inside `ENV_WHEEL_*`
  (Ø96 × 32 mm) markers added per wheel.
- Secondary detail: `MOUNT_MOTOR_*` plates (drivebase), `PIVOT_MOUNT_L/R`
  cheek bosses (intake + master), `DIVERTER_HORN` servo arm (transfer +
  master), `STUB_SHAFT_L/R` 8 mm REX shafts (shooter + master),
  `STAGE_GUIDE_L/R` + `CRADLE_LIP` (lifter + master), `ELEC_RAIL_L/R`
  hub rails (electronics + master). All Part:: primitives, expression-bound.

Datasheet-driven corrections (sources in `docs/robot-parameters.md`):

- `wheel_width` 25 → 32 mm (goBILDA schematic 3606-0000-0096).
- `motor_dia` 40 → 36 mm (Yellow Jacket 5203 series page).
- `intake_width` 330 → 326 mm — wheel inner faces at ±164 with the cited
  32 mm wheels; keeps ~1.4 mm clearance to the roller envelope.
- `rail_len` reclassified UNVERIFIED (cut length is a choice, not a catalog
  dim); `rail_w`/`rail_h` 48 mm confirmed against the 1120-series page.
- Mass table basis updated: 4 × 207 g wheels + 4 × ~438 g motors — total
  row still ~2.6 kg; overall placeholder total 14.7 kg unchanged.

Exports/renders:

- `export_prototypes.py`: export-set count now computed dynamically (no
  hardcoded 21); manifest prints the computed count. STL: 25740 facets,
  bbox (−218.0, −196.0, −0.0)–(228.6, 196.0, 640.0) — Y grew ±192.5 → ±196
  with the cited 32 mm wheels. STEP reimports 72 solids.
- `render_views.py`: colored/filled per-subsystem facets (painter's
  algorithm) + wireframe edge overlay + legend; added `master_iso.svg`
  (orthographic, az 45° / el 35.264° — true isometric).
- `selfcheck_sprint06.py` — new gate superset of sprint-04: adds the 9
  enumerated overlap-exemption classes, roller count/slant/X-pattern/
  envelope asserts, and updated probes (intake_width 326).

## 2026-09-20 — Sprint 05: prototype exports + renders (autonomous build)

Prototype export pipeline — no model changes (all 7 live FCStd byte-stable
before/after; earlier notes saying "8" were a miscount, corrected sprint-06).
Everything exported is placeholder geometry, labeled
PROTOTYPE / VERIFY BEFORE MANUFACTURING.

Added:

- `scripts\freecad\export_prototypes.py` — exports the 21 robot leaf
  solids (4 wheels, `BATTERY`, `ELECTRONICS`, 15 `MECH_*`) to
  `exports\prototype_stl\master_robot_PROTOTYPE.stl` (3668 facets) and
  `exports\prototype_step\master_robot_PROTOTYPE.step` (ISO-10303-21,
  re-imports ≥21 solids); writes `exports\MANIFEST.md` with the object
  list, exclusion rule, and labels.
- `scripts\freecad\render_views.py` — headless SVG wireframe projections
  (front/side/top) to `exports\renders\` — `freecadcmd` has no GUI
  renderer, so wireframe SVG is the honest approach.
- `exports\MANIFEST.md`, `exports\export_validation.txt`,
  `exports\renders\render_log.txt`.

Docs: build report sprint-05 append; README + instructions list the
export/render commands; requirements marked delivered.

## 2026-09-20 — Sprint 04: master integration + field references (autonomous build)

`master_robot.FCStd` upgraded to 53 objects / 34 leaf solids: every
mechanism's representative solids now placed in the assembly and the
flagged `VOL_*` reserve overlaps resolved. Still placeholder-grade —
primitive bound solids, never manufacturing data.

Changed:

- `VOL_INTAKE` narrowed to 330 mm (`intake_width` 340→330) — clears the
  wheel inner faces; `MECH_INTAKE_CHEEK_L/R` + `MECH_ROLLER` added.
- `VOL_TRANSFER` dropped to floor level (`channel_z` 100→10, the
  through-chassis lane continuous with the intake throat) and ends flush
  at the intake face (length derived by expression, ~228.6 mm);
  `MECH_CHANNEL` + `MECH_DIVERTER` added. The transfer concept keeps its
  standalone 340 mm `channel_len` study.
- `BATTERY` repositioned to the −Y chassis side and `ELECTRONICS`
  belly-mounted — placements now expression-bound (`bat_*`, `elec_*`
  aliases).
- Shooter reps: `MECH_SHOOTER_BODY` (rear plate), `MECH_SHOOTER_HOOD`,
  `MECH_FLYWHEEL_L/R` with inner-face gap = `bore` 100 mm.
- Lifter reps: `MECH_LIFTER_STOWED`, `MECH_STAGE_1/2/3` telescoped inside
  the deployed ghost, `MECH_CARRIAGE`, `MECH_CRADLE` at ~600 mm.
- Field aiming references: `REF_HIVE` (~800 mm past front face, ~300 mm
  launch height — position UNVERIFIED) and `REF_FLOWER` (~546 mm, §9.7
  VERIFIED height; XY UNVERIFIED).
- `intake_concept_v01` + `transfer_concept_v01` updated for the shared
  `intake_width`/`channel_z` values (object sets unchanged).
- `cad\archive\*_sprint03_20260920_120918.FCStd` — timestamped pre-change
  backups of master + intake + transfer staged before reruns.
- NEW `scripts\freecad\selfcheck_sprint04.py` — contract gate
  (named-pair disjointness, full leaf scan, envelope compliance, field
  refs, expression probes, close-no-save hash).

Docs: `robot-parameters.md` gains master integration aliases + a mass
table (14.7 kg placeholder total, all UNVERIFIED); `mechanism-architecture
.md` gains the integration section with declared co-locations;
`open-questions.md` marks the reserve-overlap question resolved.

## 2026-09-20 — Sprint 03: mechanism-level placeholders (autonomous build)

Upgraded every concept file from packaging volumes to mechanism-level
placeholder geometry per D9–D11 (still primitive solids, expression-bound,
never manufacturing data). `master_robot.FCStd` untouched this sprint
(integration is sprint-04).

Added / upgraded:

- `drivebase_concept_v01.FCStd` (21 objects, 12 solids): `RAIL_L`/`RAIL_R`
  goBILDA U-channel side rails 400 × 48 × 48 mm flush with chassis sides;
  wheels/motors unchanged (one motor per wheel, D9).
- `intake_concept_v01.FCStd` (19 objects, 10 solids): `PIVOT_PLATE_L/R`
  side plates + `PIVOT_BOSS` hinge at the rear; `LIP_RAMP` scoop lip
  pitched ~20° at the mouth bottom.
- `transfer_concept_v01.FCStd` (19 objects, 10 solids): `DIVERTER_PADDLE`
  + `DIVERTER_AXIS` hinge at the scoring end; `ROUTE_POLLEN` (up to
  shooter) and `ROUTE_NECTAR` (to lifter hopper) route markers.
- `shooter_concept_v01.FCStd` (18 objects, 9 solids): universal bore
  `bore` = 100 mm bound between flywheel inner faces (D10, Nectar-capable
  is settled); `MUZZLE_CLEAR` 110 mm; `HOOD` over muzzle, `BACKSTOP`
  behind the bore, `FEED_INLET` at the −X face.
- `lifter_concept_v01.FCStd` (20 objects, 11 solids): three nested cascade
  stages `STAGE_1/2/3` inside the deployed ghost, `CARRIAGE` on the inner
  stage top, `CRADLE` riding it at ~600 mm, labeled `HARD_STOP` marker at
  the outer stage top (R105 physical-stop placeholder).
- NEW `scripts\freecad\build_electronics_concept.py` →
  `cad\electronics\electronics_concept_v01.FCStd` (14 objects, 5 solids):
  chassis volume reference + disjoint `BATTERY`, `HUB_CTRL`, `HUB_EXP`
  REV-style placeholders (VENDOR-PENDING).
- `cad\archive\*_sprint02_20260920_112157.FCStd` — timestamped backups of
  all five upgraded targets staged before their geometry-changing reruns.

Docs: `robot-parameters.md` extended to the full alias union; the
Nectar-shooter open question is closed per D10 in `open-questions.md`;
`mechanism-architecture.md` describes mechanism-level geometry.

## 2026-09-20 — Mechanism decisions recorded (sprint-03 scope setter)

- Drivetrain: 4× 96 mm goBILDA mecanum, one motor per wheel (D9).
- Shooter: dual flywheel, universal ~100 mm bore — Nectar-capable (D10).
- Lifter: top-mounted cascade elevator with Nectar cradle (D11).

## 2026-09-20 — Sprint 02: mechanism concept placeholders (autonomous build)

Second autobuild slice: goBILDA-oriented concept placeholders for the
two-phase scoring architecture (D7/D8).

Added:

- `scripts\freecad\build_intake_concept.py` →
  `cad\intake\intake_concept_v01.FCStd` (15 objects, 6 solids): floor intake
  at the chassis front (+X) with `THROAT_CLEAR` 120 × 110 mm opening,
  two floor-level rollers, chassis-edge reference.
- `scripts\freecad\build_transfer_concept.py` →
  `cad\transfer\transfer_concept_v01.FCStd` (15 objects, 6 solids):
  `CHANNEL` clear 110 × 110 mm cross-section spanning intake (+X) to
  scoring (−X) zones with wall guides and zone markers.
- `scripts\freecad\build_shooter_concept.py` →
  `cad\scoring\shooter_concept_v01.FCStd` (15 objects, 6 solids):
  Pollen-primary housing, twin VENDOR-PENDING flywheels, 90 mm muzzle,
  `LAUNCH_DIR` +X indicator aimed toward the Hive cell.
- `scripts\freecad\build_lifter_concept.py` →
  `cad\endgame\lifter_concept_v01.FCStd` (15 objects, 6 solids):
  `LIFTER_STOWED` inside the 457.2 mm start cube (top-mounted),
  `LIFTER_DEPLOYED` ghost reaching 610 mm inside the R105 expansion
  volume, `CRADLE` 120 × 120 mm at ~570 mm.
- `master_robot.FCStd` extended to 36 objects / 19 solids / 39 aliases:
  `VOL_INTAKE`, `VOL_TRANSFER`, `VOL_SHOOTER`, `VOL_LIFTER_STOWED`,
  `VOL_LIFTER_DEPLOYED` mechanism packaging volumes — sprint-01 objects
  unchanged.
- `drivebase_concept_v01.FCStd`: wheels/motors relabeled goBILDA
  VENDOR-PENDING with `VendorRef` properties; geometry unchanged.
- `cad\archive\master_robot_sprint01_20260920_091818.FCStd` — timestamped
  backup of the sprint-01 master taken before the extension.
- `docs\robot-parameters.md` rewritten: 70-alias union table, status enum
  VERIFIED | UNVERIFIED | VENDOR-PENDING.

Verification performed: all six scripts run twice via `freecadcmd.exe` —
exit 0, identical object lists, no strays; reopen/recompute clean; delta
probes move bound geometry exactly (throat_clear_w +20 % → +24 mm,
channel_w +20 % → +22 mm, muzzle_clear +20 % → +18 mm, reach_z +20 % →
+122 mm); sprint-01 master preserved in `cad\archive\`.

## 2026-09-20 — Team decisions recorded

- Project root confirmed: `C:\Users\pmsma\OneDrive\Documents\BIOBUZZ-Robot`
  (mission's `C:\Users\pmsma\Documents\...` path does not exist).
- Build ecosystem decided: **goBILDA** (purchase pending — vendor dims stay
  UNVERIFIED until parts/datasheets confirm).
- Scoring architecture decided: **two-phase** — Pollen shooter into the Hive
  for early game; top-mounted Nectar lifter for Flower tops in the final
  60 s of TeleOp. See `docs/design-decisions.md` D6–D8 and
  `docs/open-questions.md` for follow-ups.

## 2026-09-19 — Sprint 01: CAD foundation (autonomous build)

Initial foundation generated by the autobuild loop.

Added:

- Directory tree: `cad\{archive,drivebase,intake,transfer,scoring,endgame,
  electronics,library}`, `scripts\{freecad,validation}`,
  `exports\{renders,prototype_stl,prototype_step,prototype_dxf}`, `docs`,
  `.devin`.
- `scripts\freecad\build_master_robot.py` → `cad\master_robot.FCStd`
  (31 objects, 14 solids): `Parameters` spreadsheet with 19 bound aliases;
  `ENV_START` 457.2 mm cube (VERIFIED, R102); `ENV_EXPANSION`
  457.2 × 609.6 × 736.5 mm (VERIFIED, R105); `VOL_DRIVEBASE` packaging volume;
  4 wheel placeholders; battery + electronics placeholders; `COORD_REF`
  App::Part with three axis-indicator solids at the world origin.
- `scripts\freecad\build_drivebase_concept.py` →
  `cad\drivebase\drivebase_concept_v01.FCStd` (19 objects, 10 solids):
  `Parameters` sheet with 10 bound aliases; chassis plate, 4 wheels,
  4 motor placeholders — all expression-bound.
- Full documentation set under `docs\` plus `.devin\instructions.md`.

Verification performed:

- Each script run twice via `freecadcmd.exe` — exit 0, identical object lists,
  no duplicated objects, no stray files under `cad\`.
- Both FCStd reopen and recompute cleanly; every solid valid with volume > 0.
- Mirror-tree test: scripts copied to an empty `%TEMP%` tree rebuild their
  FCStd under the mirrored `cad\` path (proves `__file__`-relative paths).
- Delta test: editing `chassis_length`, `wheel_dia`, `wheel_x_offset` in the
  sheet moves bound geometry by exactly the applied delta.

Known caveats: every non-envelope dimension is an UNVERIFIED placeholder —
see `docs\robot-parameters.md`. Intake/transfer/scoring/endgame subsystems
have no geometry yet; see `docs\mechanism-architecture.md`.
