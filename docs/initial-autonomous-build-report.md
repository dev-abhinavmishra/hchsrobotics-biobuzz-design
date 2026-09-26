# Initial autonomous build report — BIOBUZZ-Robot sprint-01

## What was produced

Built by the autobuild Generator via `freecadcmd.exe` (FreeCAD 1.1.3):

- `cad\master_robot.FCStd` (≈14.7 KB, 31 objects / 14 solids) — packaging
  foundation: `Parameters` spreadsheet (19 bound aliases), R102 start
  envelope (457.2 mm cube, VERIFIED), R105 expansion envelope
  (457.2 × 609.6 × 736.5 mm, VERIFIED), 420 × 420 × 120 mm drivebase
  packaging volume, 4 wheel placeholders, battery and control-hub
  placeholders, and a `COORD_REF` coordinate-reference part with three
  axis-indicator solids at the world origin.
- `cad\drivebase\drivebase_concept_v01.FCStd` (≈9.4 KB, 19 objects /
  10 solids) — parametric chassis plate, 4 wheels, 4 motor placeholders, all
  bound to a 10-alias `Parameters` sheet.
- Build scripts: `scripts\freecad\build_master_robot.py`,
  `scripts\freecad\build_drivebase_concept.py`.
- Full documentation set under `docs\`.

## Project-root path note

The mission text referenced `C:\Users\pmsma\Documents\BIOBUZZ-Robot`; that
path does not exist on this machine. The real skeleton — and the root used
for all work — is `C:\Users\pmsma\OneDrive\Documents\BIOBUZZ-Robot`. The
scripts resolve paths from `__file__`, so they are unaffected by the
OneDrive location.

## How it was verified

- Both scripts executed via `freecadcmd.exe`: exit 0, `BUILD: DONE`.
- Each script run twice: identical sorted object lists, no duplicates, no
  archive or `.FCBak` strays under `cad\` (idempotent).
- Both FCStd reopened and recomputed cleanly; every solid `isValid()` with
  volume > 0; all expression bindings resolved (no `#ERR`).
- Mirror test: scripts copied to an empty `%TEMP%` tree recreate the FCStd
  files under the mirrored `cad\` — proving `__file__`-relative paths.
- Delta test on the drivebase: `chassis_length` +84 mm → chassis X extent
  +84 mm; `wheel_dia` +19.2 mm → wheel diameter extent +19.2 mm;
  `wheel_x_offset` +34 mm → wheel X placement +34 mm.

## Caveats (read before trusting the model)

- Every non-envelope dimension is an UNVERIFIED assumed placeholder — see
  `docs\robot-parameters.md` for status per parameter. Wheels, motors,
  battery, electronics, and chassis sizes have not been measured against
  real parts.
- Envelopes (R102/R105) are the only VERIFIED geometry, cited to the
  Competition Manual TU01.
- Intake, transfer, scoring, and endgame subsystems have no geometry —
  only reserved `cad\` folders and placeholder plans in
  `docs\mechanism-architecture.md`.
- This model asserts nothing about legality or fit; it is a packaging
  baseline for iteration.

---

## Sprint 02 append — mechanism concept placeholders (2026-09-20)

### What was added

- `cad\intake\intake_concept_v01.FCStd` (≈8 KB, 15 objects / 6 solids) —
  floor intake at the chassis front (+X): `THROAT_CLEAR` 120 × 110 mm
  opening (clears ~91 mm Nectar + margin), two floor-level rollers, frame
  and chassis-edge reference — all UNVERIFIED.
- `cad\transfer\transfer_concept_v01.FCStd` (≈8 KB, 15 objects / 6 solids) —
  `CHANNEL` clear 110 × 110 mm spanning 340 mm intake→scoring, wall guides,
  inlet/outlet zone markers — all UNVERIFIED.
- `cad\scoring\shooter_concept_v01.FCStd` (≈8 KB, 15 objects / 6 solids) —
  Pollen-primary housing, twin 72 mm flywheels (VENDOR-PENDING), 90 mm
  `MUZZLE_CLEAR`, `LAUNCH_DIR` +X indicator toward the Hive cell. Nectar
  capability is marked as an open question, not assumed.
- `cad\endgame\lifter_concept_v01.FCStd` (≈8.5 KB, 15 objects / 6 solids) —
  `LIFTER_STOWED` inside the R102 start cube (ZMin 120 mm, top-mounted),
  `LIFTER_DEPLOYED` mast ghost to 610 mm inside the R105 expansion volume,
  `CRADLE` 120 × 120 mm at ~570 mm — envelopes VERIFIED, lifter UNVERIFIED.
- `cad\master_robot.FCStd` extended (≈20.4 KB, 36 objects / 19 solids /
  39 aliases): `VOL_INTAKE`, `VOL_TRANSFER`, `VOL_SHOOTER`,
  `VOL_LIFTER_STOWED`, `VOL_LIFTER_DEPLOYED` packaging volumes; sprint-01
  objects unchanged; sprint-01 file preserved as
  `cad\archive\master_robot_sprint01_20260920_091818.FCStd`.
- `cad\drivebase\drivebase_concept_v01.FCStd`: wheel/motor placeholders
  relabeled goBILDA `UNVERIFIED - VENDOR-PENDING` with `VendorRef`;
  geometry unchanged.
- New scripts: `build_intake_concept.py`, `build_transfer_concept.py`,
  `build_shooter_concept.py`, `build_lifter_concept.py`; updated
  `build_master_robot.py`, `build_drivebase_concept.py`.

### How it was verified

- All six scripts run twice via `freecadcmd.exe`: exit 0, `BUILD: DONE`,
  identical object/alias sets, no stray files, no re-archiving.
- Reopen + `doc.recompute()` clean; all solids valid, volume > 0.
- Delta probes (±20 %) move bound geometry exactly: `throat_clear_w`
  +24 mm, `channel_w` +22 mm, `muzzle_clear` +18 mm, `reach_z` +122 mm;
  close-without-save leaves file hashes unchanged.
- Lifter checks: stowed bbox inside `ENV_START`, deployed bbox inside
  `ENV_EXPANSION` with ZMax 610 mm, stowed↔deployed CoG_xy offset 0 mm.
- Alias union across all six FCStd (70 names) is fully documented in
  `docs\robot-parameters.md`.

### Caveats (unchanged stance)

- Everything except the R102/R105 envelopes and the cited game-element
  facts remains UNVERIFIED or VENDOR-PENDING — packaging placeholders,
  not a design. Nectar-through-shooter was left undecided at sprint-02
  close; it is settled per D10 in sprint-03 (universal ~100 mm bore).

---

## Sprint 03 append — mechanism-level placeholders (2026-09-20)

### What was added

- `cad\drivebase\drivebase_concept_v01.FCStd` (21 objects / 12 solids):
  `RAIL_L`/`RAIL_R` goBILDA U-channel side rails 400 × 48 × 48 mm flush
  with the chassis sides (VENDOR-PENDING); 4 mecanum wheels + 4 motors
  unchanged (one per wheel, D9).
- `cad\intake\intake_concept_v01.FCStd` (19 objects / 10 solids): pivot
  side plates + rear `PIVOT_BOSS` hinge; `LIP_RAMP` tilted scoop lip at
  the mouth bottom (angle bound to `lip_ang`).
- `cad\transfer\transfer_concept_v01.FCStd` (19 objects / 10 solids):
  `DIVERTER_PADDLE` + `DIVERTER_AXIS` hinge at the scoring end;
  `ROUTE_POLLEN`/`ROUTE_NECTAR` markers for the Pollen→shooter /
  Nectar→hopper split.
- `cad\scoring\shooter_concept_v01.FCStd` (18 objects / 9 solids):
  universal ~100 mm `bore` between flywheel inner faces (D10 —
  Nectar-capable, settled), 110 mm `MUZZLE_CLEAR`, `HOOD` + `BACKSTOP` +
  `FEED_INLET`.
- `cad\endgame\lifter_concept_v01.FCStd` (20 objects / 11 solids): cascade
  elevator — nested `STAGE_1/2/3` inside the deployed ghost, `CARRIAGE`
  atop the inner stage, `CRADLE` riding at ~600 mm, `HARD_STOP` marker
  at the outer stage top (R105 physical-stop placeholder, UNVERIFIED).
- NEW `cad\electronics\electronics_concept_v01.FCStd` (14 objects /
  5 solids): `CHASSIS_VOL` reference + pairwise-disjoint `BATTERY`,
  `HUB_CTRL`, `HUB_EXP` REV-style placeholders (VENDOR-PENDING).
- `cad\master_robot.FCStd` untouched (36 objects, sprint-02 state);
  timestamped `*_sprint02_*` backups of all five upgraded targets staged
  in `cad\archive\` before reruns.

### How it was verified

- All six touched scripts run twice via `freecadcmd.exe`: exit 0,
  `BUILD: DONE`, identical object/alias sets, no strays, no re-archiving.
- Reopen + `doc.recompute()` clean; all solids valid, volume > 0.
- Delta probes move bound geometry exactly: `rail_w` +9.6 mm,
  `intake_width` +68 mm, `channel_w` +22 mm, `bore` +10 mm per flywheel
  face (+20 mm gap), `stage1_w` +15.2 mm, `battery_l` +36 mm;
  close-without-save leaves file hashes unchanged.
- Geometry floors: rail outer faces at chassis sides (|Y|=210);
  `LIP_RAMP` pitched 20° with `XMax ≥ THROAT_CLEAR.XMin`, `ZMin ≤ 30`;
  diverter hinge `XMin` within 80 mm of `CHANNEL.XMin`; bore gap = 100 mm
  = `bore`; cascade stages strictly nested ≥1 mm/face, union inside
  `LIFTER_DEPLOYED` +2 mm; hard-stop `ZMin ≥ STAGE_1.ZMax − 20`;
  electronics leaves disjoint ≤2 mm and inside `CHASSIS_VOL` +2 mm.
- Alias union across all seven FCStd (124 names) is fully documented in
  `docs\robot-parameters.md`; shooter Nectar strings carry no stale
  open/undecided qualifiers (D10 settled).

## Sprint 04 append — master integration + field references (2026-09-20)

### What changed

`cad\master_robot.FCStd` grew to 53 objects / 34 leaf solids. The flagged
sprint-02 reserve overlaps are resolved and each mechanism now places
representative `MECH_*` solids in the assembly:

- `intake_width` 340 -> 330 mm: `VOL_INTAKE` clears the wheel inner faces;
  `MECH_INTAKE_CHEEK_L/R` flank `MECH_ROLLER` inside the reserve.
- `channel_z` 100 -> 10 mm: the transfer lane is a floor-level
  through-chassis path (z 10..120), continuous with the intake throat;
  `VOL_TRANSFER`/`MECH_CHANNEL` end flush at the intake face via
  expression. `MECH_DIVERTER` marker sits face-adjacent at the -X end.
- `BATTERY` moved to the -Y chassis side, `ELECTRONICS` belly-mounted —
  placements expression-bound (`bat_*`, `elec_*`).
- Shooter reps: `MECH_SHOOTER_BODY` rear plate, `MECH_SHOOTER_HOOD`,
  `MECH_FLYWHEEL_L/R` at the 100 mm `bore` inner-face gap.
- Lifter reps: `MECH_LIFTER_STOWED`, telescoped `MECH_STAGE_1/2/3` inside
  `VOL_LIFTER_DEPLOYED`, `MECH_CARRIAGE`, `MECH_CRADLE` at ~600 mm.
- `REF_HIVE` aim marker ~800 mm past the front face at ~300 mm;
  `REF_FLOWER` at the 546 mm Flower top (§9.7 height VERIFIED, XY
  UNVERIFIED). Both labeled aiming references, never a field model.
- `intake_concept_v01` / `transfer_concept_v01` re-run with the shared
  `intake_width`/`channel_z` values — object sets unchanged.
- `docs\robot-parameters.md`: integration aliases documented + mass
  table (14.7 kg placeholder total — sum of subsystem rows, all
  UNVERIFIED).
- NEW `scripts\freecad\selfcheck_sprint04.py` — the contract gate.

### Declared co-locations (intended, not collisions)

Channel + intake inside the `VOL_DRIVEBASE` chassis bay; cascade stages
telescope (overlapping by design); the deployed ghost rises through the
stowed envelope's footprint; carriage/cradle may exceed the ghost at the
top; `ENV_*`/`AXIS_*`/`REF_*` and App::Part containers exempt from
overlap/envelope checks. Full leaf scan otherwise clean.

### How it was verified

- Timestamped `*_sprint03_20260920_120918.FCStd` backups staged for all
  three touched targets BEFORE the first upgraded run (pre-change param
  state: `intake_width`=340, `channel_z`=100, master = 36-object set).
- All three touched scripts run twice: exit 0, `BUILD: DONE`, identical
  object/alias sets, no strays; mirror-tree rebuilds from an unrelated
  cwd.
- `selfcheck_sprint04.py`: ALL PASS — C1-C4 named pairs disjoint, C6 full
  leaf scan clean, reps inside reserves +2 mm, bore gap = 100.0 mm,
  cradle ZMin = 600 >= 546, stowed solids inside R102 + deployed inside
  R105, REF_HIVE XMin 1028.6 / REF_FLOWER z-center 546.0, probes
  `intake_width` +66 mm and `reach_z` +122 mm exact, close-without-save
  hash stable.

## Sprint 05 append — prototype exports + renders (2026-09-20)

### What changed

NEW scripts (no model changes — all 8 FCStd byte-stable before/after):

- `scripts\freecad\export_prototypes.py` — exports the 21 robot leaf
  solids (4 wheels, `BATTERY`, `ELECTRONICS`, 15 `MECH_*`) from the master
  assembly; excludes `ENV_*`/`AXIS_*`/`REF_*` references, `VOL_*` reserves,
  and containers. Writes `exports\MANIFEST.md` + self-validation.
- `scripts\freecad\render_views.py` — headless orthographic SVG wireframe
  projections (front XZ / side YZ / top XY) via edge discretization — no
  GUI renderer exists in `freecadcmd`, so wireframe SVGs are the honest
  preview.

### Outputs

- `exports\prototype_stl\master_robot_PROTOTYPE.stl` — 3668 facets,
  bbox (-218, -192.5, 0)..(228.6, 192.5, 640) mm.
- `exports\prototype_step\master_robot_PROTOTYPE.step` — ISO-10303-21,
  re-import yields 22 solids (>=21 exported).
- `exports\renders\master_{front,side,top}.svg` — 189 polylines each,
  true-aspect views.
- `exports\MANIFEST.md` — object list, exclusion rule, and the
  PROTOTYPE / VERIFY BEFORE MANUFACTURING label per artifact.

### How it was verified

- Both scripts run twice via `freecadcmd.exe`: exit 0, idempotent
  overwrite, mirror-tree rebuilds from an unrelated cwd.
- STL re-parses via `Mesh.read` (facets > 0, bbox matches the exported
  set within 2 mm); STEP re-imports >= 21 solids.
- sha256 of all 7 live FCStd identical before and after the export/render
  runs — the scripts never mutate the models. (Earlier notes saying "8"
  were a miscount; the repository has 7 live FCStd files.)
- Exports and renders carry the PROTOTYPE / VERIFY BEFORE MANUFACTURING
  label in filenames and manifest; nothing here is manufacturing data.

## Sprint 06 append — detail + accuracy pass (2026-09-20)

### What changed

All 7 live FCStd rebuilt (pre-change archives under
`cad\archive\*_sprint05_20260920_135103.FCStd`). Still primitive,
expression-bound placeholder geometry — no manufacturing data.

- `build_drivebase_concept.py` / `build_master_robot.py`: 10 mecanum
  roller placeholders per wheel (`ROLLER_*_00..09`, Ø14 × 20 mm at ~45°
  slant, expression-bound `cos/sin(k * mec_roll_pitch)` positions, FTC
  X-pattern FL+RR vs FR+RL) + `ENV_WHEEL_*` envelope markers (Ø96 × 32 mm)
  + `MOUNT_MOTOR_*` plates (drivebase only).
- `build_intake_concept.py` / master: `PIVOT_MOUNT_L/R` cheek bosses;
  `intake_width` 330 → 326 mm (datasheet 32 mm wheels put inner faces at
  ±164 mm).
- `build_transfer_concept.py` / master: `DIVERTER_HORN` servo arm on the
  paddle.
- `build_shooter_concept.py` / master: `STUB_SHAFT_L/R` 8 mm REX shafts
  coaxial with the flywheels.
- `build_lifter_concept.py` / master: `STAGE_GUIDE_L/R` blocks riding the
  stage walls + `CRADLE_LIP` retention rim.
- `build_electronics_concept.py` / master: `ELEC_RAIL_L/R` hub rails.
- Datasheet corrections: `wheel_width` 25 → 32 mm, `motor_dia` 40 → 36 mm
  (goBILDA citations in `docs/robot-parameters.md`); mass-table basis now
  cites 207 g wheels / ~438 g motors — totals unchanged (2.6 / 14.7 kg).
- `export_prototypes.py`: export-set size now computed dynamically (the
  hardcoded 21 removed); manifest prints the computed count.
- `render_views.py`: colored per-subsystem fills (painter's algorithm) +
  wireframe overlay + legend; new `master_iso.svg` at orthographic
  az 45° / el 35.264°.
- New gate `selfcheck_sprint06.py` — supersedes the sprint-04 gate with
  the 9 enumerated overlap classes + roller asserts; probe values updated
  for `intake_width` 326.
- Encoding repair: this file had 17 stray cp1252 bytes (from an earlier
  PowerShell rewrite) — normalized to pure UTF-8.

### Outputs

- Master: 107 objects / 88 solids (71 exportable leaf solids).
- STL: 25740 facets, bbox (−218.0, −196.0, −0.0)–(228.6, 196.0, 640.0) —
  Y grew ±192.5 → ±196 with the cited 32 mm wheel width.
- STEP reimport: 72 solids (≥ 71 exported).
- SVGs: `master_{front,side,top,iso}.svg`, filled + wireframe, labeled
  PROTOTYPE / VERIFY BEFORE MANUFACTURING.

### How it was verified

- `selfcheck_sprint06.py`: 21/21 PASS — roller count/slant/X-pattern/
  envelope containment, leaf-scan under the declared exemption classes,
  R102/R105 containment, probes (intake_width 326→391.2, reach_z
  610→732), close-without-save hash stable.
- Export validation PASS; manifest lists the computed 71-object set.
