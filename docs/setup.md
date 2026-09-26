# Setup — BIOBUZZ-Robot

## Prerequisites

- FreeCAD 1.1 installed on Windows. The verified console binary is:
  `C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe` (v1.1.3, probe-verified).
- No other dependencies; the build scripts use only `FreeCAD`, `Part`, and
  `Spreadsheet` modules that ship with FreeCAD.

## Build the models

From `cmd.exe` or PowerShell (PowerShell needs the `&` call operator):

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_master_robot.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_drivebase_concept.py
```

```powershell
& "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_master_robot.py
& "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_drivebase_concept.py
```

Working directory does not matter — all scripts resolve the project root from
`__file__` (`<root>\scripts\freecad\` → `<root>`). The full build set (7
scripts) also covers `build_intake_concept.py`, `build_transfer_concept.py`,
`build_shooter_concept.py`, `build_lifter_concept.py`, and
`build_electronics_concept.py` — see `README.md` for the complete list.

Outputs:

- `cad\master_robot.FCStd` — robot packaging foundation (envelopes, drivebase
  volume, wheels, battery, electronics, mechanism `VOL_*` reserves +
  `MECH_*` representatives, `REF_*` aim markers, coordinate reference).
- `cad\*\*_concept_v01.FCStd` — one parametric concept per subsystem
  (drivebase, intake, transfer, scoring, endgame, electronics).

All files open in the FreeCAD GUI for inspection. Re-running a script
rebuilds the same object set (idempotent); if the target file ever contains
objects the script did not create, a timestamped copy is preserved under
`cad\archive\` first.

## Exports + previews

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\export_prototypes.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\render_views.py
```

Prototype STL/STEP land under `exports\prototype_stl` /
`exports\prototype_step`; colored SVG previews (front/side/top/iso) land
under `exports\renders`. All labeled `PROTOTYPE / VERIFY BEFORE
MANUFACTURING` — see `exports\MANIFEST.md`. The current geometry gate is
`scripts\freecad\selfcheck_sprint06.py` (writes
`selfcheck_sprint06_results.txt`).

## Optional smoke test

`scripts\validation\freecadcmd_probe.py` exercises the FreeCAD APIs the build
relies on:

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\validation\freecadcmd_probe.py
```

Look for `PROBE: RESULT: PASS`.

## Editing parameters

Open either FCStd, edit the `Parameters` spreadsheet cells (column B), and
recompute — bound geometry follows. Canonical values/status are tracked in
`docs/robot-parameters.md`; axes follow `docs/coordinate-system.md`.
