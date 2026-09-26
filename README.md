# BIOBUZZ-Robot

## Interactive 3D design review (new)

`viewer/` is a self-contained Three.js design-review app for the full competition
robot concept — no CAD software needed:

```bat
cd viewer
python serve.py        :: no-cache dev server (avoids stale JS modules)
:: open http://127.0.0.1:8017
:: `python -m http.server 8017` also works, but hard-refresh if modules look stale
```

Features: 7 subsystems / ~270 placed parts merged into 136 BOM lines, per-part
inspector (spec, qty, notes, bounding size, connected-parts graph), an
**Isolate** button that ghosts everything but the selected part — combined with
Prev/Next it steps through every piece in solo view — exploded view slider,
X-ray and subsystem isolation, animated
mechanisms (mecanum rollers, flywheels, 360° turret, hood, agitator, 2-stage
deposit lift with live rope rigging), a launch demo that slews the turret,
lobs a POLLEN into the HIVE cell and tips it, a lift demo that raises the
cradle ~14.6" and tips the ball, an 18" sizing-cube overlay, and a full
BIOBUZZ field at scale (hives, 4 flowers, loading zones, staged elements).

**Part Explorer** (`Parts` tab in the left panel): every BOM line is listed
per subsystem with a live filter; clicking a part highlights all placed
instances and frames them. The inspector shows spec, quantity, bounding size,
notes, and a **Connected parts** graph — clickable chips jump between mated
parts (motor → pinion → axle → bearings → wheel; winch → spool → rope →
pulleys → stages; hubs → every wire run). Prev/Next steps through the whole
BOM, and **◎ Isolate** solos any part — the solo view follows selection so
stepping parts keeps everything else ghosted.

Production-realism pass: procedural canvas textures (alliance number plates,
AprilTags, foam-tile waffle, motor/hub labels), full wiring loom (motor power,
servo PWM, encoder/sensor JST, battery→switch→hub, slip-ring to the turret),
instanced fastener fields, sealed bearings, #25 chain with pins and a master
link, rail end caps, nylocks, shaft collars, compact-motor clamps, JST wire
connectors, hub LEDs, main-switch detail, zip ties, and a contact shadow.

Performance: repeated geometry (mecanum/omni rollers, star discs, wheel ribs,
slots, spokes, ports, fasteners) renders through InstancedMesh — roughly 200
meshes collapsed into instanced draws; clear polycarbonate uses cheap
alpha-blend instead of a transmission pass (which would double the scene
render), and the shadow map re-bakes only while geometry actually moves.

**Match Demo** (`⏵ Match Demo` button): a ~45-second scripted match —
autonomous pollen intake run (intake rollers spin, balls sweep along the
floor and arc up the throat), turret aims at the CELL AprilTag, feed wheel
meters balls **visibly rising through the clear column** into 3 POLLEN lobs,
teleop mecanum strafe to the alliance NECTAR stash, 2 NECTAR launches that
tip the HIVE, a corner run where the diverter kicks a ball down the load
chute into the cradle, then the lift rises and pours it into the FLOWER
mouth, and a loading-zone park. Cinematic chase/fixed cameras with phase
captions — **drag anytime to take a free spectator camera**, then "Resume
cinematic camera" to hand control back. Subsystem motion is gated per phase
(intake spins only while collecting, flywheels only while shooting). Every
scored ball stays in the cell. Click the button again to abort.

Design intent: 17.5×17.5×13.3" — starts legal inside the 18" cube (R101); the
deposit lift is the only expansion and tops out ~26", inside the R105 29"
vertical cap with hard-stop collars (G416). Over/under intake → inclined
hopper → feed column through the turret axis → dual-flywheel turret launcher
with AprilTag camera lobs POLLEN/NECTAR into the HIVE cell. For FLOWERS the
same column doubles as the elevator — a servo Y-flap diverts a ball through a
side port into the lift cradle, which deposits NECTAR into the ~4" mouth at
~22" (a lob into a 4" opening for a 3.6" ball was rejected as unreliable).

---

FreeCAD CAD foundation for an FTC BIOBUZZ-season robot. This repository holds
**placeholder packaging models only** — labeled volumes that reserve space for
the drivebase, battery, electronics, wheels, mechanism concepts, and the
game-rule envelopes. Nothing here is a finished mechanism; every assumed
dimension is marked `UNVERIFIED` (or `VENDOR-PENDING` for goBILDA-catalog
values) in the model and in `docs/robot-parameters.md` until it is measured
or cited against the BIOBUZZ Competition Manual (TU01).

## Layout

```
cad\                  master_robot.FCStd (styled view baked in) +
                      master_robot_view.FCStd (styled copy) +
                      per-subsystem folders
cad\archive\          timestamped backups (auto-created before overwrites)
cad\drivebase\        drivebase_concept_v01.FCStd
cad\intake\           intake_concept_v01.FCStd
cad\transfer\         transfer_concept_v01.FCStd
cad\scoring\          shooter_concept_v01.FCStd
cad\endgame\          lifter_concept_v01.FCStd
cad\electronics\      electronics_concept_v01.FCStd
scripts\freecad\      parametric build scripts (run with freecadcmd.exe)
scripts\validation\   freecadcmd probe / checks
docs\                 project documentation (see index below)
exports\              renders + prototype exports (PROTOTYPE-labeled)
.devin\               agent instructions and generator state
```

## Quickstart

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_master_robot.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_drivebase_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_intake_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_transfer_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_shooter_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_lifter_concept.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\build_electronics_concept.py
```

Exports + previews (regenerate after rebuilding):

```bat
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\export_prototypes.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\render_views.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\render_png.py
"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\make_view_copy.py
```

These write `exports\prototype_stl\master_robot_PROTOTYPE.stl`,
`exports\prototype_step\master_robot_PROTOTYPE.step`,
`exports\renders\master_{front,side,top,iso}.svg` (shaded per-subsystem
fills + visible-edge overlay; iso is orthographic az 45° / el 35.264°),
`exports\renders\master_{front,side,top,iso}.png` (z-buffered shaded
rasters, same views), and `exports\MANIFEST.md` — all labeled
`PROTOTYPE / VERIFY BEFORE MANUFACTURING`.

Viewing in the FreeCAD GUI: just open `cad\master_robot.FCStd` (or the
identical `cad\master_robot_view.FCStd`). The file carries baked-in view
state: non-physical `ENV_*`/`VOL_*`/`REF_*` volumes and field markers are
hidden, subsystem solids are colored, and the camera opens on a fitted
isometric. Re-run `make_view_copy.py` after any rebuild to restore that
styling; `view_robot.py` does the same for a live session (Macro ->
Macros -> Run).

The scripts only read the FCStd files; every model's
sha256 is unchanged by export runs. `scripts\freecad\selfcheck_sprint06.py`
re-runs the current geometry gate (superset of the sprint-04 checks).

All scripts are idempotent and resolve paths relative to their own location.
See `docs/setup.md` for details and `docs/coordinate-system.md` for the axis
convention used by every model.

## Documentation index

- `docs/setup.md` — FreeCAD install path + exact build commands
- `docs/robot-parameters.md` — every named parameter: value, unit, status, source
- `docs/coordinate-system.md` — origin and axis convention
- `docs/cad-architecture.md` — how the FCStd files are structured and rebuilt
- `docs/mechanism-architecture.md` — placeholder plan for all six subsystems
- `docs/requirements.md` — manual-cited constraints vs assumptions
- `docs/design-decisions.md` — why things are built the way they are
- `docs/open-questions.md` — unresolved questions
- `docs/change-log.md` — build history
- `docs/initial-autonomous-build-report.md` — what the autonomous build produced

## Honesty notice

All geometry in this repository is a placeholder. `VERIFIED` values are cited
to a Competition Manual rule/section; goBILDA-catalog values are
`VENDOR-PENDING` pending datasheet/purchase; everything else is an assumption
labeled `UNVERIFIED`. Nothing here has been checked for legality, fit, or
function by a human reviewer yet.
