# BIOBUZZ-Robot

FTC BIOBUZZ-season robot CAD. Fully parametric FreeCAD model — Python
builders regenerate every `cad/*.FCStd` document from a shared
`Parameters` spreadsheet, and three selfcheck gate suites are the repo's
regression contract (all green on main). ~1,090 exportable solids across
six subsystem docs plus the integrated `master_robot.FCStd`, with full
fastener detail.

## For the CAD team (SolidWorks)

**You don't need FreeCAD.** Everything manufacturable is pre-exported to
STEP — the FCStd files are the editable sources only if you want to
change the design itself.

### What to open

| You want | Use |
|---|---|
| The whole robot, assembled | `exports/step/master_robot.step` (one AP203 STEP, ~1,090 parts, each at its true position) |
| One subsystem at a time | `exports/step/subassembly/{drivebase,intake,hopper,electronics,turret,lift}.step` |
| A group of related parts | `exports/step/subassembly/GRP_*.step` (frame, pods, turret rotation, fasteners…) |
| A single part | `exports/step/parts/<NAME>.step` — product names preserved (no anonymous Part__Feature) |
| 2D drawings | `exports/drawings/` — one A4 sheet per unique part as PDF + SVG (TOP/FRONT/RIGHT views, overall dimensions, title block with material + qty), and `exports/drawings/dxf/` R12 flat profiles for the 165 plate parts (ready for waterjet/laser) |
| Bill of materials | `exports/bom/bom.csv` — subsystem, description, material, spec, qty |
| Renders | `exports/renders/*.png` — shaded orthographic previews per subsystem |

### SolidWorks import notes

1. `File → Open → master_robot.step`, import as **assembly** (not
   multibody part). ~1,090 parts — give it a minute. For quicker work,
   import a subsystem STEP instead and mate them yourself (they're in
   world coordinates — parts land exactly where they sit in the master).
2. Units are mm. Part names carry a status suffix (`_VERIFIED`,
   `_VENDOR-PENDING`, `_UNVERIFIED`) — see the checklist below.
3. Non-physical construction geometry (`TOOL_`, `VOL_`, `ENV_`, `REF_`,
   `AXIS_` prefixes) is intentionally excluded from STEP — if you see it,
   it came from an FCStd, not an export.

### Before you cut metal: the verification checklist

Every dimension carries a status label in `exports/parameters.csv`
(and `docs/robot-parameters.md`): **3 VERIFIED** (manual-cited),
**24 VENDOR-PENDING** (goBILDA catalog values awaiting datasheet), and
**245 UNVERIFIED** (assumed). Nothing UNVERIFIED has been measured
against physical hardware — the gates verify parametric integrity,
mounting/declared-contact consistency, envelope fit, and rebuild
determinism, **not** real-world fit.

Measure/confirm before manufacturing, roughly in order of risk:

- **Stock + hardware dims**: all sheet/plate thicknesses, extrusion
  sizes, bearing bores — anything your parts physically mate to
- **Vendor parts**: all `VENDOR-PENDING` goBILDA dims vs the actual
  purchased parts (datasheet or calipers)
- **Ball-path clearances**: column bore Ø99 vs your ball's true
  diameter; chute width 97 mm; port window height
- **Mesh/engagement**: 72T ring + 14T pinion at 72.8 mm center distance;
  belt/chain center distances; lazy-susan race stack heights
- **Mounts**: every fastener lands in a real declared bore (the gates
  prove this geometrically) — but hole sizes/threads are UNVERIFIED
- **Envelopes**: stowed 453.7×454.5×379.0 mm inside the 457.2 cube;
  deployed lift tops 586.5 mm (inside the 609.6 reach / 736.5 height)

### Known design-contact notes (intentional touches/brushes)

- `PORT_FLANGE` sill: the ball rides over the port sill edge on the way
  out (designed ride surface, ~0.5 mm brush).
- `SCRW_CHL_1_0` (leg-2 lip tip) and `ROPE_DYNEEMA` (lift line): the
  ball brushes these ~2–5 mm on the cradle drop — acceptable grazing
  contact for hand-loaded parts; move the rope guide ~8 mm west if it
  ever deflects a ball in testing.
- `CHUTE_PTS + n·46.5` is the *ride* model only — the ball enters leg 1
  on a ballistic transition, rides the bed, and free-falls ~40 mm into
  the cradle mouth (see `dt_lift.py` comments).

### Change the design?

See "Quickstart" below — edit `scripts/freecad/robot_params.py` or the
`dt_*.py` builders, rebuild the affected doc, re-run the gates, then
re-export (`export_step.py`) and re-draw (`make_drawings.py`). The CI
workflow runs all of it on every push to `main`.

---

## Interactive 3D design review

`viewer/` is a self-contained Three.js design-review app for the full
competition robot concept — no CAD software needed:

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

Design intent: 17.5×17.5×14.9" — starts legal inside the 18" cube (R101); the
deposit lift is the only expansion and tops out ~26", inside the R105 29"
vertical cap with hard-stop collars (G416). Over/under intake → inclined
hopper → feed column through the turret axis → dual-flywheel turret launcher
with AprilTag camera lobs POLLEN/NECTAR into the HIVE cell. For FLOWERS the
same column doubles as the elevator — a servo Y-flap diverts a ball through a
side port into the lift cradle, which deposits NECTAR into the ~4" mouth at
~22" (a lob into a 4" opening for a 3.6" ball was rejected as unreliable).

---

## Layout

```
cad\                  master_robot.FCStd (styled view baked in) +
                      master_robot_view.FCStd (styled copy)
cad\drivebase\        drivebase.FCStd     cad\intake\    intake.FCStd
cad\electronics\      electronics.FCStd   cad\hopper\    hopper.FCStd
cad\turret\           turret.FCStd        cad\lift\      lift.FCStd
cad\archive\          timestamped backups (auto-created before overwrites)
scripts\freecad\      build_*.py builders, selfcheck_overhaul*.py gates,
                      partkit/dt_* helpers, export/drawing/render tools
scripts\freecad\legacy\  superseded pre-overhaul concept scripts
scripts\validation\   ci_selfcheck.sh + probes
docs\                 project documentation (see index below)
exports\              STEP parts/subassemblies, bom.csv, mount_graph.json,
                      meta/, renders/, drawings/ (see exports/README.md)
viewer\               self-contained Three.js design-review app
.devin\               agent instructions and generator state
.github\workflows\    cad-verify.yml — rebuild + gates on every push to main
```

## Quickstart

Requires FreeCAD **1.1.3** (`freecadcmd` on PATH — AppImage extract or apt;
gate signatures are version-sensitive, other 1.1.x builds may differ):

```bash
freecadcmd scripts/freecad/build_drivebase.py
freecadcmd scripts/freecad/build_electronics.py
freecadcmd scripts/freecad/build_intake.py
freecadcmd scripts/freecad/build_hopper.py
freecadcmd scripts/freecad/build_turret.py
freecadcmd scripts/freecad/build_lift.py
freecadcmd scripts/freecad/build_master_robot.py   # integrated assembly
```

Exports + previews (regenerate after rebuilding):

```bash
freecadcmd scripts/freecad/export_step.py      # STEP parts/subassemblies + bom/meta
freecadcmd scripts/freecad/render_png.py       # exports/renders/*.png
freecadcmd scripts/freecad/make_view_copy.py   # restyle master_robot_view.FCStd
freecadcmd scripts/freecad/make_drawings.py    # exports/drawings/: A4 PDF+SVG
                                               # sheets + plate DXFs + manifest
```

Regression gates (must stay green — these are the repo's contract):

```bash
bash scripts/validation/ci_selfcheck.sh   # all selfcheck_overhaul* gates,
                                          # or run each directly:
freecadcmd scripts/freecad/selfcheck_overhaul01.py   # 45 gates
freecadcmd scripts/freecad/selfcheck_overhaul02.py   # 61 gates
freecadcmd scripts/freecad/selfcheck_overhaul03.py   # 73 gates
```

The `.github/workflows/cad-verify.yml` workflow runs the same build +
gates on every push to `main` (cached FreeCAD 1.1.3 install) and uploads
selfcheck output + `exports/` as artifacts.

Viewing in the FreeCAD GUI: just open `cad\master_robot.FCStd` (or the
identical `cad\master_robot_view.FCStd`). The file carries baked-in view
state: non-physical `ENV_*`/`VOL_*`/`REF_*` volumes and field markers are
hidden, subsystem solids are colored, and the camera opens on a fitted
isometric. Re-run `make_view_copy.py` after any rebuild to restore that
styling; `view_robot.py` does the same for a live session (Macro ->
Macros -> Run).

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
- `docs/eval-sprint03-independent.md` — independent adversarial eval of the
  gates + probes (ball-path findings, since fixed)
- `docs/initial-autonomous-build-report.md` — what the autonomous build produced

## Honesty notice

`VERIFIED` values are cited to a Competition Manual rule/section;
goBILDA-catalog values are `VENDOR-PENDING` pending datasheet/purchase;
everything else is an assumption labeled `UNVERIFIED`. The selfcheck gates
verify parametric integrity, mounting/declared-contact consistency,
envelope fit, and rebuild determinism — the UNVERIFIED checklist above is
what still needs a human + physical hardware.
