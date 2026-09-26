# Agent instructions — BIOBUZZ-Robot

Guidance for anyone (human or agent) working in this repository.

## Building the CAD

FreeCAD headless binary (verified on this machine, v1.1.3):

```
C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe
```

Rebuild all sprint-01 models (idempotent — safe to re-run; all three
wrappers share `scripts\freecad\dt_build.py`):

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_drivebase.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_electronics.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_master_robot.py
```

- `build_drivebase.py` → `cad\drivebase\drivebase.FCStd` (frame + drivetrain + pods)
- `build_electronics.py` → `cad\electronics\electronics.FCStd` (tray + wiring subset)
- `build_master_robot.py` → `cad\master_robot.FCStd` (sprint-01 union)

Each wrapper calls `dt_build.populate_*(doc, ctx)` then
`dt_build.finish_doc(...)` — recompute, shape validation, `GRP_*`
assembly grouping, save, and `exports\meta\<tag>.json` pair tables
(joints / faces / embeds / journals / contacts / ground census / bom).

Exports + previews + view state + gate (run after rebuilding):

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\export_step.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\make_view_copy.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\render_png.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\selfcheck_overhaul01.py
```

- `export_step.py` → `exports\step\parts\<name>.step` (per exportable
  solid), `exports\step\subassembly\GRP_*.step` + subsystem STEP,
  `exports\step\master_robot.step` (reimported + counted);
  `exports\bom\bom.csv`, `exports\parameters.csv`,
  `exports\mount_graph.json`
- `render_png.py` → `exports\renders\{master,drivebase,electronics}_{front,side,top,iso}.png`
  (shaded z-buffer raster; consumed/tool shapes excluded)
- `make_view_copy.py` → styled `*_view.FCStd` copies + in-place
  `GuiDocument.xml` injection (hides ENV_/TOOL_/consumed, subsystem
  palette, orthographic iso camera)
- `selfcheck_overhaul01.py` → the sprint-01 contract gate, 21 checks
  (GIT/DET/PAR/PROV/DAG/ASM/FAST/GEO/ENV/XPT/GUI), writes
  `exports\selfcheck_overhaul01.txt`; current result: **21/21 pass**
- `scripts\freecad\_probe_overlap.py` → standalone undeclared-overlap
  probe (same declared-pair table as the selfcheck)

## Conventions to keep

- All dimensions in mm; geometry stays parametric — bind dimensions to
  the `Parameters` spreadsheet via `setExpression`, never bake numbers
  into shape calls. Wire harness (`WIRE_*`) and baked strut segments are
  the sanctioned exception (baked endpoints).
- Coordinate convention in `docs\coordinate-system.md`: origin at center
  of the robot footprint on the tile surface; +X forward, +Y left, +Z up.
- Scripts resolve paths from `__file__` — never hardcode absolute paths
  (the repo may be checked out elsewhere, and evaluators mirror it).
- Every assumed dimension is `UNVERIFIED` — in `DataStatus` properties,
  in object labels (name carries a `_UNVERIFIED`/`_VENDOR-PENDING`
  suffix), and in `docs\robot-parameters.md`. `VERIFIED` requires a
  Competition Manual citation (R102, R105, §9.x, TU01). goBILDA-catalog
  values are `VENDOR-PENDING` until datasheets or physical parts confirm
  them — never VERIFIED.
- Every exportable solid carries a status token in its label, a
  `DataStatus` property, and membership in exactly one `GRP_*`
  `App::Part` (nested carriers like `WHEEL_ASSY_*` count through their
  parent chain).
- Construction intermediates live in `*_TOOLS` `Part::Compound`
  containers; consumed shapes (fuse/cut/chamfer inputs) are excluded
  from exports, probes, and renders. `exportable()`/`_consumed_add` in
  `selfcheck_overhaul01.py` is the reference implementation.
- Fastener model (R7 hybrid): real clearance bores through pass-through
  members; the bolt solid may embed only into the terminal threaded
  member (declared in `meta['embeds']`).
- Journal pairs (shaft↔bore) are declared in `meta['journals']`;
  mount face pairs in `meta['faces']`; incidental touch/contact pairs
  in `meta['contacts']`; spring/wire contacts in `meta['embeds']` or
  `contacts`. Anything that overlaps without a declaration fails GEO2.
- Children of `App::Part` carriers (e.g. `WHEEL_ASSY_*`) hold
  local-frame shapes — `o.Shape` ignores carrier placement. Use
  `o.Shape.copy(); s.Placement = o.getGlobalPlacement()` for analysis.
- The declared-overlap/contact tables emitted by `dt_build.py` are the
  contract — a newly discovered undeclared overlap is a failure to fix
  in geometry, not a reason to extend the declaration.
- If a build script would overwrite an FCStd containing foreign
  objects, archive a timestamped copy under `cad\archive\` first.

## Sprint-01 scope guard

The master intentionally contains sprint-01 solids only: frame,
drivetrain, three odometry pods, electronics tray, the sprint-01 wiring
subset, and all fasteners. Intake, hopper, turret, lift, servos,
camera, and USB-loom solids are sprint-02/03 scope — do not add them.
