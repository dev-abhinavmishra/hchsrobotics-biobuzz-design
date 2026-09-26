# Agent instructions — BIOBUZZ-Robot

Guidance for anyone (human or agent) working in this repository.

## Building the CAD

FreeCAD headless binary (verified on this machine, v1.1.3):

```
C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe
```

Rebuild all models (idempotent — safe to re-run any number of times):

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_master_robot.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_drivebase_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_intake_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_transfer_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_shooter_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_lifter_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_electronics_concept.py
```

- `build_master_robot.py` → `cad\master_robot.FCStd`
- `build_drivebase_concept.py` → `cad\drivebase\drivebase_concept_v01.FCStd`
- `build_intake_concept.py` → `cad\intake\intake_concept_v01.FCStd`
- `build_transfer_concept.py` → `cad\transfer\transfer_concept_v01.FCStd`
- `build_shooter_concept.py` → `cad\scoring\shooter_concept_v01.FCStd`
- `build_lifter_concept.py` → `cad\endgame\lifter_concept_v01.FCStd`
- `build_electronics_concept.py` → `cad\electronics\electronics_concept_v01.FCStd`

Exports + previews + view state (read-only against the FCStd — run after
rebuilding; `make_view_copy.py` must run before the selfcheck so the GUI
view-state check sees `GuiDocument.xml`):

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\make_view_copy.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\render_png.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\render_views.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\export_prototypes.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\selfcheck_rehaul02.py
```

- `export_prototypes.py` → `exports\prototype_stl\master_robot_PROTOTYPE.stl`,
  `exports\prototype_step\master_robot_PROTOTYPE.step`, `exports\MANIFEST.md`
- `render_views.py` → `exports\renders\master_{front,side,top,iso}.svg`
  (colored per-subsystem fills; iso = orthographic az 45° / el 35.264°)
- `render_png.py` → `exports\renders\{master,drivebase}_{front,side,top,iso}.png`
  (shaded z-buffer raster; correct occlusion for interpenetrating solids)
- `make_view_copy.py` → styled `*_view.FCStd` copies + in-place
  `GuiDocument.xml` injection for master and drivebase
- `selfcheck_rehaul02.py` → the current contract gate (writes
  `selfcheck_rehaul02_results.txt`); supersedes `selfcheck_rehaul01.py`
  and `selfcheck_sprint06.py` (both retained for archived-baseline
  validation)

## Conventions to keep

- All dimensions in mm; geometry stays parametric — bind dimensions to the
  `Parameters` spreadsheet via `setExpression`, never bake numbers into
  shape calls.
- Coordinate convention in `docs\coordinate-system.md`: origin at center of
  the robot footprint on the tile surface; +X forward, +Y left, +Z up.
- Scripts resolve paths from `__file__` — never hardcode absolute paths
  (the repo may be checked out elsewhere, and evaluators mirror it).
- Every assumed dimension is `UNVERIFIED` — in `DataStatus` properties, in
  object labels, and in `docs\robot-parameters.md`. `VERIFIED` requires a
  Competition Manual citation (R102, R105, §9.x, TU01). goBILDA-catalog
  values are `VENDOR-PENDING` (combined with `UNVERIFIED` on solids) until
  datasheets or physical parts confirm them — never VERIFIED.
- New files under `exports\` must carry `PROTOTYPE` in the filename or sit
  beside a README stating `PROTOTYPE / VERIFY BEFORE MANUFACTURING`.
- If a build script would overwrite an FCStd containing foreign objects,
  archive a timestamped copy under `cad\archive\` first.
- Construction intermediates are `TOOL_*`-named, grouped under a `Tools`
  container, and excluded from exports/renders/overlap checks.
- Children of `App::Part` carriers (e.g. `WHEEL_ASSY_*`) hold local-frame
  shapes — `o.Shape` ignores carrier placement. Use
  `o.Shape.copy(); s.Placement = o.getGlobalPlacement()` for analysis.
- The C6 declared-overlap table in `selfcheck_rehaul02.py` /
  `docs\mechanism-architecture.md` is frozen — a newly discovered
  undeclared overlap is a failure to fix, not a reason to extend it.
