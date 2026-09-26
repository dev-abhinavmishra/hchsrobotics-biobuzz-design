# Mechanism architecture — BIOBUZZ placeholder concepts

**Two-phase scoring (settled, `docs/design-decisions.md` D8):** early game a
shooter launches Pollen (~71 mm dia, VERIFIED §9.8) into the Hive cell; in
the final 60 s of TeleOp a top-mounted lifter places Nectar (~91 mm dia,
VERIFIED §9.8) into Flower tops (~101.5 mm opening at ~546 mm height,
VERIFIED §9.7). Every number below is either cited (VERIFIED, and present in
`docs/robot-parameters.md`) or marked UNVERIFIED/assumed on the same line.
The models are mechanism-level placeholders — shaped like the decided
mechanisms (D9–D11) but still primitive solids, never manufacturing data.
Canonical values live in `docs/robot-parameters.md`; the frame convention is
`docs/coordinate-system.md`.

## Drivetrain — 4× 96 mm goBILDA mecanum (D9)

Rehaul sprint-01 rebuilt the drivetrain in both `master_robot.FCStd` and
`drivebase_concept_v01.FCStd` from the shared `scripts\freecad\partkit.py`
component kit:

- **Frame ring**: `RAIL_*`/`FRAME_RAIL_*` four goBILDA 1120-series
  U-channel rails (48 mm faces VENDOR-PENDING, wall 2.5 mm assumed
  UNVERIFIED) — genuine open channel cross-sections cut from solid, with
  a Ø4 hole grid on flanges and web, plus Ø16 shaft-clearance notches
  through the side-rail mouths where the drive shafts pass.
- **Sheets**: `BELLY_PAN` 3 mm filleted sheet inside the frame ring
  (sitting on the lower flange lip); `REAR_DECK_L/R` 3 mm filleted deck
  plates flanking the ball channel (master only), ending forward of the
  rear motor corridor.
- **Wheels**: each wheel is a `WHEEL_ASSY_*` carrier placed as a unit at
  ±140 mm X / ±180 mm Y (assumed, UNVERIFIED — moved inboard from ±170 so
  the motors clear the end rails). Per wheel: `WHEEL_HUB_*` Ø26 × 20 mm
  hub with Ø8.4 mm REX bore, `WHEEL_PLATE_*_IN/OUT` Ø92 × 4 mm face
  plates with shaft bores + edge chamfer, and 10 `ROLLER_*` fused
  roller+pin bodies (Ø14 × 20 mm rollers on Ø5 pins, ~45° slant, FTC
  X-pattern — FL+RR one slant, FR+RL opposite). All inside `ENV_WHEEL_*`
  Ø96 × 32 markers, Ø96 measured at roller surfaces (VENDOR-PENDING,
  goBILDA 3213-3606-0002 / schematic 3606-0000-0096).
- **Drive chain per wheel** (the mounting chain the contract requires):
  `MOTOR_*` 5203 Yellow Jacket-style Ø36 × 60 mm (dia VENDOR-PENDING,
  length UNVERIFIED) bolted by `MOUNT_MOTOR_*` face plate (30 × 30 ×
  2.5 mm, bored Ø8.4 + 4 bolt holes) to the rail web inner face →
  `SHAFT_*` 8 mm REX live shaft (VENDOR-PENDING dia, 76 mm UNVERIFIED)
  through the face plate, through the side-rail web notch, supported by
  `BEARING_*` flange block (26 × 26 × 6 mm, bored + 4 bolt holes) on the
  web cavity face → through the intake cheek clearance bore → into the
  wheel hub bore. Every stage is an expression-bound placement on the
  `Parameters` sheet.
- `VOL_DRIVEBASE` in `master_robot.FCStd` still reserves 420 × 420 ×
  120 mm (assumed, UNVERIFIED) inside the 457.2 mm start cube (VERIFIED,
  R102).

## Intake

- `cad\intake\intake_concept_v01.FCStd`: universal floor intake at the
- `cad\intake\intake_concept_v01.FCStd` (sprint-02 rebuild, component
  fidelity): bored cheek plates (`INTAKE_CHEEK_L/R`, five bores each,
  chamfered edges), dual ribbed intake rollers (`ROLLER_LO/HI` tubes +
  12 ribs each), 8 mm roller shafts on flanged bearing blocks
  (`INTAKE_BEARING_LO/HI_L/R`), bored pivot bosses (`PIVOT_MOUNT_L/R`)
  with pivot *stub* axles (`INTAKE_AXLE_L/R` - no cross-shaft, so the
  O91 ball path stays clear), pivot servo `INTAKE_MOTOR` bolted to the
  cheek inner face on a riser foot (`INTAKE_MOTOR_BRKT`),
  `INTAKE_MOUNT_L/R` L-brackets to the chassis stub, and `LIP_RAMP`
  scoop at the mouth. `VOL_THROAT` + `VOL_BALL_PATH` probes retained.
- `VOL_INTAKE` reserve in `master_robot.FCStd`: 160 x 340 x 120 mm at
  the +X front, floor-level (width covers the roller-shaft tips). The
  master carries the same vocabulary: `INTAKE_CHEEK_L/R`,
  `INTAKE_ROLLER` + `INTAKE_ROLLER_SHAFT`, `INTAKE_BEARING_L/R`,
  `PIVOT_MOUNT_L/R` + `INTAKE_AXLE_L/R` stub axles, `INTAKE_MOTOR`
  inside the rail-mouth pocket resting on the bottom flange,
  `INTAKE_MOTOR_BRKT` clamp strap, `INTAKE_MOUNT_L/R` brackets on the
  side-rail inner faces, `INTAKE_LIP` sill on the bottom flange (all
  assumed, UNVERIFIED).

## Transfer

- `cad\transfer\transfer_concept_v01.FCStd` (sprint-02 rebuild,
  component fidelity): `CHANNEL_FLOOR` sheet + `CHANNEL_WALL_L/R`
  bored walls, `CHANNEL_SUPP_F/B` saddle brackets, `DIVERTER_PADDLE`
  (bored hinge plate) on `DIVERTER_AXLE` through wall bushings
  (`DIVERTER_BUSH_L/R`), `DIVERTER_SERVO` + `DIVERTER_HORN` on the
  wall outer face, `ZONE_INLET`/`ZONE_OUTLET` markers (inlet on wall
  tops; outlet behind the channel end on the pan stub, clear of the
  hinge), `ROUTE_POLLEN`/`ROUTE_NECTAR` arrows, `VOL_CHANNEL_CLEAR` +
  `VOL_BALL_PATH` probes (all assumed, UNVERIFIED).
- `VOL_TRANSFER` in `master_robot.FCStd`: floor-level lane from the
  scoring end to the intake face, now spanning the bushing/axle tips
  and the saddle feet (z from the pan top). Master carries the same
  vocabulary: `CHANNEL_FLOOR`, `CHANNEL_WALL_L/R` (outer faces flush
  against the drive-motor inner faces; interior lane 101 mm > O91),
  `CHANNEL_SUPP_F/B`, `DIVERTER_PADDLE/AXLE/BUSH_*/SERVO/HORN`,
  `VOL_CHANNEL_CLEAR` + `VOL_BALL_PATH`.

## Scoring

- `cad\scoring\shooter_concept_v01.FCStd`: universal dual-flywheel launcher
  — Nectar-capable per D10 (settled 2026-09-20). `SHOOTER_BODY` housing
  200 × 200 × 250 mm (assumed, UNVERIFIED); twin flywheels 72 mm dia × 30 mm
  (VENDOR-PENDING, goBILDA-style) spaced by the ~100 mm `bore` — the clear
  gap between inner faces (assumed, UNVERIFIED — clears ~91 mm Nectar,
  §9.8); `MUZZLE_CLEAR` 110 × 110 mm opening (assumed, UNVERIFIED);
  `HOOD` over the muzzle + `BACKSTOP` behind the bore; `FEED_INLET` at the
  −X face where the transfer channel arrives (all assumed, UNVERIFIED);
  `STUB_SHAFT_L/R` 8 mm REX stub shafts through the flywheel bores
  (sprint-06 — dia VENDOR-PENDING per goBILDA 8 mm REX standard, length
  UNVERIFIED); `LAUNCH_DIR` indicator pointing +X toward where the Hive
  cell opening ~508 × 356 mm (VERIFIED, §9.6) is approached.
- `VOL_SHOOTER` reserve in `master_robot.FCStd`: same housing dims; master
  reps include `STUB_SHAFT_L/R` coaxial with the flywheels.

## Endgame

- `cad\endgame\lifter_concept_v01.FCStd`: top-mounted cascade elevator
  (D11, settled 2026-09-20). `LIFTER_STOWED` 200 × 200 × 150 mm (assumed,
  UNVERIFIED) sits inside the 457.2 mm start cube (VERIFIED, R102) above
  the 120 mm drivebase zone; `LIFTER_DEPLOYED` mast ghost reaches 610 mm
  (assumed, UNVERIFIED — the ~546 mm Flower top plus clearance, §9.7) while
  staying inside the 457.2 × 609.6 × 736.5 mm expansion volume (VERIFIED,
  R105); three nested cascade stages `STAGE_1/2/3` (76/74/72 mm sections,
  telescoped at increasing bases, all assumed UNVERIFIED) inside the ghost;
  `CARRIAGE` plate on the innermost stage carrying the `CRADLE` 120 × 120 mm
  (assumed, UNVERIFIED — holds the ~91 mm Nectar, §9.8) at ~600 mm with a
  `CRADLE_LIP` retention rim on its +X edge (sprint-06, assumed UNVERIFIED);
  `STAGE_GUIDE_L/R` guide blocks ride the stage walls (sprint-06, assumed
  UNVERIFIED); a labeled `HARD_STOP` marker at the outer stage top — the
  physical travel stop R105 requires (requirement cited; marker dims
  UNVERIFIED).
- `VOL_LIFTER_STOWED` / `VOL_LIFTER_DEPLOYED` ghosts mirror this in
  `master_robot.FCStd`.

## Electronics

- `cad\electronics\electronics_concept_v01.FCStd` (sprint-03): layout
  placeholders inside a 420 × 420 × 120 mm chassis volume matching the
  drivebase reserve — `BATTERY` 180 × 90 × 75 mm, `HUB_CTRL` + `HUB_EXP`
  160 × 120 × 35 mm each on `ELEC_RAIL_L/R` mounting rails (sprint-06,
  assumed UNVERIFIED), pairwise disjoint (all VENDOR-PENDING, REV-style,
  datasheet pending). Master still carries the sprint-01 battery/elec
  placeholders plus matching `ELEC_RAIL_L/R` rails. Sensor/camera mounts
  (e.g. for the 82.55 mm AprilTags, VERIFIED §9.9) are not placed yet
  (UNVERIFIED).

## Integration (rehaul sprint-01 — `master_robot.FCStd`, ~877 objects /
~390 solids incl. construction tools; 115 exportable leaf solids)

The master carries the partkit drivetrain described above plus
representative `MECH_*` solids inside each `VOL_*` reserve — intake cheek
plates (with shaft + pivot-axle clearance bores) + roller + pivot bosses,
floor-level channel + diverter + servo horn + hinge axle, shooter rear
plate + hood + flywheel pair + stub shafts at the 100 mm `bore`, lifter
stowed region + three deployed stages + guide blocks + carriage + cradle +
lip at ~600 mm. Mount-chain placeholders tie mechanisms to the frame:
`INTAKE_MOUNT_*` cheek brackets bolted between the side-rail cavity faces
and cheek inner faces, `CHANNEL_SUPP_*` saddles under the channel floor,
`POST_SHOOTER_*` uprights on the deck carrying the `SHOOTER_FLOOR` +
`SHOOTER_SIDE_*` plates, `LIFTER_PED`/`LIFTER_BASE` pedestal + base plate
under the mast column, `ELEC_RAIL_*` standoff rails under the electronics
hub. All expression-bound to the shared aliases.

Flagged reserve overlaps resolved:

- `VOL_INTAKE` narrowed to 326 mm (sprint-06; was 330) so the intake frame
  clears the wheel inner faces at ±164 mm given the cited 32 mm wheels —
  no intake↔wheel/roller intersection.
- `VOL_TRANSFER` dropped to floor level (z 10..120, the through-chassis
  lane continuous with the intake throat) and ends flush at the intake
  face — no transfer↔shooter/lifter intersection.
- `BATTERY` sits in the −Y bay (x −110..70, y −113..−58, z 5.5..40.5) on
  the belly pan — forward of the rear motor corridor — and `ELECTRONICS`
  is belly-mounted on `ELEC_RAIL_*` standoffs (x −120..40, y 60..115, z
  5.5..39.5) — both clear of the channel and wheels; placements are
  expression-bound (rehaul sprint-01).

Declared co-locations (intended, not conflicts — the frozen rehaul
sprint-01 Appendix-A overlap classes): the channel and intake live inside
the `VOL_DRIVEBASE` chassis bay; cascade stages telescope (overlapping
bboxes by design); the deployed lifter ghost rises through the stowed
envelope's footprint; carriage/cradle may exceed the deployed ghost at the
top. Enumerated overlap classes:

- **C1 shafts/bores**: live-shaft tail inside its `MOTOR_*` body (4×);
  `INTAKE_AXLE` inside `PIVOT_MOUNT_*` bosses (2×); `STUB_SHAFT_*` inside
  `MECH_FLYWHEEL_*` (2×) and 1 mm into `SHOOTER_SIDE_*` plates (2×);
  `DIVERTER_AXLE` through `MECH_DIVERTER` paddle (1×).
- **C2 pin seats**: `ROLLER_*_B` pin tips embed ~1 mm into their own
  wheel's `WHEEL_PLATE_*_IN/OUT` face plates (80×).
- **C3 mount embeds**: `BEARING_*` flange blocks straddle the side-rail
  top flange lip (4×); `STAGE_GUIDE_*` blocks ride `MECH_STAGE_*` walls
  (6×); `CRADLE_LIP` integral to `MECH_CRADLE` rim (1×).
- **C7 placeholder co-location** (mechanism reps pending sprint-02..04
  detail): `MECH_STAGE_*` telescoping nests (3×); `MECH_INTAKE_CHEEK_*`
  pass through the open channel mouths crossing the flange lips (2×);
  `DIVERTER_HORN` embedded in the paddle (1×); `PIVOT_MOUNT_*` boss
  overlaps its cheek plate (2×).

Envelope references (`ENV_*`), cosmetic `AXIS_*` markers, `REF_*` field
aiming markers, `VOL_*` reserves, and `TOOL_*` construction intermediates
are exempt from overlap checks. Anything else overlapping >0.5 mm³ is a
contract failure — the declared table is frozen at eval-01 handoff.

Field references: `REF_HIVE` aim marker ~800 mm past the front face at
~300 mm launch height (position UNVERIFIED — aiming reference, not a field
model) and `REF_FLOWER` at the ~546 mm Flower top (§9.7 VERIFIED height,
XY position UNVERIFIED) forward of the mast.

## Exports (sprint-05, upgraded sprint-06)

`scripts\freecad\export_prototypes.py` writes prototype STL + STEP of the
computed robot leaf-solid set (115 objects rehaul sprint-01 — partkit
drivetrain + rollers/pins, mechanism reps, mounts, battery, electronics) —
`ENV_*`, `AXIS_*`, `REF_*`, `VOL_*`, `TOOL_*`, and `App::` containers
excluded, shapes globalized (carrier placements applied) — into
`exports\prototype_stl` / `exports\prototype_step`, with
`exports\MANIFEST.md` recording the set and the
`PROTOTYPE / VERIFY BEFORE MANUFACTURING` label.
`scripts\freecad\render_png.py` additionally writes shaded z-buffered PNG
previews `exports\renders\{master,drivebase}_{front,side,top,iso}.png`.
`scripts\freecad\render_views.py` writes colored orthographic SVG previews
(front/side/top + isometric az 45° / el 35.264°) into `exports\renders` —
per-subsystem fills with a legend, painter's-algorithm ordering, and a
wireframe edge overlay (`freecadcmd` has no GUI renderer; SVG is the
documented preview approach).

## Unknowns / open items

- Packaging overlap questions from sprint-02 are resolved (see the
  sprint-04 contract for the declared co-locations); remaining unknowns
  live in `docs/open-questions.md`.
- Diverter reliability at the Pollen/Nectar split is untested (placeholder
  only).
- Cascade stage count/travel vs the 736.5 mm cap and the R105.B hard-stop
  implementation are placeholders awaiting real design.
- Every VENDOR-PENDING goBILDA dimension awaits datasheet/purchase.
- `docs/open-questions.md` carries the full unresolved list.
