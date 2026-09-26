# CAD architecture — BIOBUZZ-Robot

## Files

- `cad\master_robot.FCStd` — top-level packaging model built by
  `scripts\freecad\build_master_robot.py`.
- `cad\drivebase\drivebase_concept_v01.FCStd` — drivebase concept built by
  `scripts\freecad\build_drivebase_concept.py`.
- `scripts\freecad\partkit.py` — shared component kit used by the two
  rebuilt files (rehaul sprint-01): predicate-based edge selection
  (`pred_axis`, `pred_radius`, `pred_at_z`), filleted plates, U-channel
  extrusions with hole grids + shaft notches, shafts, bored hubs,
  bearing blocks, bored motor face plates, fused roller+pin bodies, and
  `mecanum_wheel` which returns an `App::Part` carrier placed as a unit.
- `cad\master_robot_view.FCStd` and
  `cad\drivebase\drivebase_concept_v01_view.FCStd` — GUI-styled copies
  produced by `scripts\freecad\make_view_copy.py` (also injects
  `GuiDocument.xml` view state into the build targets in place).
- `cad\intake\intake_concept_v01.FCStd` — floor-intake concept built by
  `scripts\freecad\build_intake_concept.py`.
- `cad\transfer\transfer_concept_v01.FCStd` — transfer-channel concept built
  by `scripts\freecad\build_transfer_concept.py`.
- `cad\scoring\shooter_concept_v01.FCStd` — Pollen shooter concept built by
  `scripts\freecad\build_shooter_concept.py`.
- `cad\endgame\lifter_concept_v01.FCStd` — Nectar lifter concept built by
  `scripts\freecad\build_lifter_concept.py`.
- `cad\electronics\electronics_concept_v01.FCStd` — battery + control /
  expansion hub layout placeholders built by
  `scripts\freecad\build_electronics_concept.py`.
- `cad\archive\` — timestamped `.FCStd` copies written automatically before a
  script would overwrite a file containing objects it did not create (holds
  the sprint-01 `master_robot` snapshot taken before the sprint-02
  extension, plus staged `*_sprint02_*` backups of each concept taken before
  the sprint-03 mechanism-level upgrade).
- `cad\library` — reserved for future shared subsystem models.

## Document structure (all files)

- A `Spreadsheet::Sheet` named `Parameters` holds every named dimension:
  column A = alias, B = value (aliased cell), C = unit, D = status
  (`VERIFIED`/`UNVERIFIED`/`VENDOR-PENDING`), E = source.
- An `App::Part` container (`RobotAssembly` / `DrivebaseAssembly` /
  `IntakeAssembly` / `TransferAssembly` / `ShooterAssembly` /
  `LifterAssembly` / `ElectronicsAssembly`) groups all placeholder solids so
  nothing sits loose at
  the document root; FreeCAD's auto-created `App::Origin` children stay
  inside the container.
- In the master model a second `App::Part` (`COORD_REF_world_origin_axes`)
  groups the three axis-indicator solids.
- The master additionally carries `VOL_*` mechanism packaging reserves
  plus `MECH_*` representative solids inside them and `REF_*` field
  aiming markers (sprint-04)
  (intake, transfer, shooter, lifter stowed + deployed ghost) sharing alias
  names with the matching concept files.
- Construction intermediates (cut tools, pre-feature blocks, hole/pin
  solids) are named `TOOL_*` and grouped under a `Tools` App::Part. They
  are excluded from exports, renders, provenance sweeps, and the physical
  overlap scan; each must be consumed by a feature (Base/Tool link) so no
  tool floats unreferenced.
- Every placeholder solid is a parametric `Part::Box` / `Part::Cylinder`
  or a feature result (`Part::Cut` channels/cheeks, `Part::Fillet` pans/
  decks, `Part::Chamfer` face plates, `Part::Fuse` roller+pin bodies)
  whose `Length`/`Width`/`Height`/`Radius`/`Placement.Base.*` components
  are bound to `Parameters.<alias>` expressions (features inherit the
  bound upstream tools), so the model recomputes from the spreadsheet.
- Children of `App::Part` carriers (`WHEEL_ASSY_*` wheel sub-assemblies)
  keep local-frame shapes: `o.Shape` does NOT include the carrier's
  placement. Any geometric analysis (overlap/connectivity/export) must
  use `s = o.Shape.copy(); s.Placement = o.getGlobalPlacement()`.
- Every placeholder solid carries a `DataStatus` string property
  (`UNVERIFIED`, or `VERIFIED - <rule>` when all its dimensions are
  manual-cited) and a descriptive label — no bare `Box`/`Cylinder` names.

## Rebuild and archive policy

The scripts delete nothing by merging — they always rebuild a fresh document,
which keeps runs idempotent (same object names/labels every time). Before
overwriting, `archive_if_foreign()` opens the target: if any object is not in
the script's managed set (App::Origin children count as managed), a
timestamped copy goes to `cad\archive\` first. FreeCAD `.FCBak` sidecars are
removed after each save so `cad\` stays clean.

## Verification gate

`scripts\freecad\selfcheck_rehaul01.py` is the active contract gate
(rehaul sprint-01): PAR3 expression sweep, PROV1 provenance, ASM1
connectivity + mount chains, GEO1 open-channel ratio, GEO6 roller
slant/X-pattern, envelope discipline, C6 overlap scan against the frozen
declaration table, PAR5 parameter sweeps, fillet-survival probe, and GUI
view-state presence — run against BOTH the master and the drivebase
concept. `selfcheck_sprint06.py` is superseded but retained runnable
against the archived sprint-07 baseline (pass the archive path as
argv[1]).

## Coordinate convention

All models share the convention in `docs/coordinate-system.md`: origin at the
center of the robot footprint on the tile surface, +X forward, +Y left, +Z up,
Z=0 at the tile top. Parameter values and statuses are mirrored in
`docs/robot-parameters.md`.
