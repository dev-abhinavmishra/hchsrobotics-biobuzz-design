# Independent evaluation — sprint-03/04 state (`main` @ HEAD)

Evaluator: Devin (cloud session), cold read, adversarial but verify-first.
Target: `main` @ `4221246` (HEAD at eval time; identical to `54a61eb`,
the merge of `cloud/ci-verify`, plus a `.devin/evaluator-state.json`
bookkeeping commit — no CAD/builder/export changes). FreeCAD **1.1.3**
(AppImage `~/opt/fc113`), eval branch `cloud/eval-sprint03`.

All probe results below come from standalone freecadcmd scripts written for
this eval — they open the built FCStd/STEP artifacts and measure solids
directly. Nothing reuses builder/gate code paths; claimed values were
hardcoded from the eval brief and docs for comparison.

## Verdict summary

| Area | Verdict | Evidence |
|---|---|---|
| selfcheck_overhaul01 | **PASS — 45/45** | exports/selfcheck_overhaul01.txt |
| selfcheck_overhaul02 | **PASS — 61/61** | exports/selfcheck_overhaul02.txt |
| selfcheck_overhaul03 | **PASS — 73/73** | exports/selfcheck_overhaul03.txt |
| Rebuilds "bit-identical" | **PASS (geometry) / FAIL (literal bytes)** | see below |
| STEP reimport | **PASS — 1106/1106** | independent reimport |
| Ball path Ø93 | **FAIL (marginal — wiring + fasteners intrude)** | dense sweep evidence below |
| Yaw drive | **PASS** | measured on built solids |
| Lazy susan | **PASS** | measured on built solids |
| Envelopes | **PASS** | union bbox probe |
| Floating parts / fasteners | **PASS** | contact + mount-graph reach |
| Exports BOM/params/naming | **PASS** | coverage + PRODUCT scan |

## Gate suites

| Suite | Result |
|---|---|
| selfcheck_overhaul01 | **45/45 PASS** (rc=0) |
| selfcheck_overhaul02 | **61/61 PASS** (rc=0) |
| selfcheck_overhaul03 | **73/73 PASS** (rc=0) |

Run locally on this machine under FreeCAD 1.1.3, same as the CI workflow
(`.github/workflows/cad-verify.yml`, also green on this state).
Operational note: `GIT2_tree_clean` gates on `git status --porcelain` —
any untracked file present mid-run (including this report's working
file, or CI's `logs/` dir) flips it. First local 03 run showed 72/73
with GIT2 flagging the eval doc itself; a re-run on a clean tree gives
73/73. Not a model defect — worth knowing when running gates locally.

## Rebuild determinism — the "bit-identical" claim

Two full `build_*` passes + committed-file comparison:

- **Per-solid geometry signature** (name → 6-dim bbox, volume, area,
  vertex/face/edge counts over all ~1,093 solids): **byte-identical**
  between `HEAD:cad/master_robot.FCStd` and a fresh rebuild
  (`diff` clean, 451,937-byte sig dumps).
- **FCStd container bytes: NOT identical.** sha256 differs for every
  `cad/*.FCStd` across any two builds and vs HEAD. Zip member diff shows
  the deltas are confined to `*.Shape.Map.txt` (topological element-map
  naming order — FreeCAD serialization nondeterminism) and ±2-byte
  `.brp` blobs. No `Document.xml` content differences.

**Verdict:** PASS at the level that matters — rebuilds are
geometry-deterministic and the committed FCStd files match what the
builders produce today. FAIL only if "bit-identical" is read as raw
file bytes. Recommend wording the claim "geometry-identical" — the
DET*/PAR* signature gates are already the canonical check.

## STEP exports & reimport

- `exports/step/parts/`: **1089/1089 files reimport cleanly** —
  `Part.read` on every file, each producing ≥1 solid, zero errors.
- `exports/step/subassembly/` (16) + `master_robot.step` (1):
  all reimport — **1106/1106 total**.
- Product naming: zero anonymous `Part__Feature`/`Shape`/`Compound`
  PRODUCT names across all 1089 part STEPs and 16 subassembly STEPs.
  Only non-UPPER_SNAKE name is `master_robot` itself.
- `export_step_report.json` records `master_step_reimport: 1222` vs
  `master_solids: 1089` — the 1222 counts STEP product occurrences
  incl. nested sub-shapes; per-file reimport shows every file loads.

## BOM / parameters coverage

- `exports/bom/bom.csv`: **1093/1093 master solids** appear in `objects`
  columns — zero missing, zero phantom entries.
- `exports/bom/parameters.csv`: 272 rows, statuses VERIFIED /
  UNVERIFIED / VENDOR-PENDING.

## Ball path — independent Ø93 sweep

Method: sphere r46.5 swept at ≤4mm steps along a densified route built
from the documented station set (intake→column→nip), a chute centerline
derived from the built `LOAD_CHUTE` solid (31 z-slice centroids, offset
by bed-normal·46.5), the *declared* chute centerline
(`dt_lift.CHUTE_PTS` + `_frame_for` normals — the same construction the
gate uses for S15/S16), a straight port-height transition S12→S15, three
droop variants, a 27-point bore-lateral grid, and the cradle park seat.
Consumption filter mirrors the earlier probes (skip `TOOL_/REF_/GRP_/
VOL_/ENV_`, consumed boolean children, `AXIS_TURRET` datum).

**Positive evidence:**

- All gate station regions themselves clear; the column bore has ~4mm
  radial margin (sphere pushed ±4mm laterally grazes `FEED_COLUMN`).
- Chute leg2 (kink→cradle) and the cradle park seat: fully clear.
- `VOL_BALL_P/N` corridor volumes: zero contacts ≥0.5mm³ against
  `FRAME_CROWN_F`, `HOP_FLOOR`, susan/ring/clamp stack, wires.
- `AXIS_TURRET` hits in the raw sweep are spurious — it is a datum
  feature (`_feat(...,"AXIS_TURRET_datum_UNVERIFIED")`,
  `dt_path.py:2110`), absent from `meta/master.json` solids and BOM.

**Violations found (verdict: FAIL):**

1. **Launch wiring crosses the flight corridor.** Along S13→S14
   (column exit→nip), `WIRE_FLY_L` intersects the sphere up to
   **151.4mm³** at (−69.5,0,267.6)–(−70.2,0,270.4); `WIRE_CAM_USB` up
   to 17.6mm³. 13 hits total — the wires pass through the y=0 corridor
   between the two gate-verified stations; the gate samples only the
   endpoints and misses it.
2. **Port-transition fasteners graze the sphere.** The only feasible
   corridor hugs port height (straight S12→S15): `SCRW_CHL_0_0/2_0`,
   `BOLT_CHP_1`, `PORT_FLANGE` graze ≤10.4mm³ across ~35mm of travel.
   Drooping lower is strictly worse (port flange/servo hardware:
   `PORT_FLANGE` 3.6K mm³, `DIV_SERVO` 0.8K at −15mm droop).
3. **Declared-path model inconsistency at leg1 start.** Sweeping the
   builders' own construction (bed pts + normal·46.5) puts the sphere
   into `FLY_MCLAMP_L` (15.0K mm³), `LAUNCH_CHEEK_L` (6.7K),
   `RING_GEAR` (3.3K), `LAZY_SUSAN_HI` (2.5K), `PORT_FLANGE` and
   CK/MCL fastener rows for the first ~10 points (z 219–243). The
   physical transition must run at port height (item 2), so this is a
   path-model defect rather than necessarily a hard blockage — but the
   declared centerline does not survive densification.

Excluded as designed-ride contacts (exempt class): `HOP_FLOOR` /
`FRAME_CROWN_F` overlaps on the S3→S4 straight chord — the ball rides
these surfaces; a straight chord is unphysical there. Spurious hits
dropped: `TOOL_*` consumed boolean tools and `GRP_*` container shapes
(2,152 of 2,625 raw hits).

**Summary:** the corridor exists and the structural path is clear, but
the "nothing static may intrude" invariant is violated by routed wiring
in the launch corridor and lip/port fastener heads at the transition —
small-volume, real interpenetrations the sparse station gate cannot see.

## Yaw drive — measured on built solids

- Center distance `RING_GEAR`↔`YAW_PINION` axes: **72.80mm** (claimed
  72.8). `pinion_pd/2 + ring_pd/2 = 11.85 + 60.95 = 72.8` ⇒ **external
  mesh** (an internal mesh would measure 49.1mm).
- `RING_GEAR` outer tip dia via bbox: **128.8mm** (claimed 128.8),
  centered at (−66, 0) = turret axis.
- `YAW_PINION` tip dia: **27.8mm** (claimed 27.8); pinion center
  (−66, −72.8) — **at −Y of the turret axis** as documented; servo
  body center (−66, −72.5), same −Y side.
- Pinion-vs-`FEED_COLUMN` surface distance: **4.86mm** — clears the
  Ø110 column circle entirely (pinion outer tip sweeps r58.9..86.7
  about the turret axis; column OD r55 leaves margin).

## Lazy susan — measured on built solids

- Two distinct solids: `LAZY_SUSAN_LO` z=248.00–252.25,
  `LAZY_SUSAN_HI` z=252.25–256.50 (each 4.25 tall, Ø132).
- `LO`↔`TURRET_DECK` surface distance **0.0** (bolted onto deck
  244–248); `HI`↔`RING_GEAR` **0.0**; `RING_GEAR`↔`TURRET_PLATE` **0.0**.
  Stack: deck 244–248 / races 248–256.5 / ring 256.5–263 / plate
  263–267 — exactly the documented z-stack.
- No single solid spans both race bands as a susan part (other solids
  passing through that z-range are the yaw shaft, lift rails, dyneema —
  structural, not races).

## Envelopes — union bbox of exportable solids

- **Stow (start cube 457.2):** x=453.74, y=454.50, z=379.00mm —
  **inside the cube on all three axes**. Extremes: axle nuts at
  y=±227.2, crown bolts at x extremes, wheels/rollers at z=0 (floor),
  `LAUNCH_CHEEK_L/R` at z_max=379.
- **Deployed (lift pose probes `VOL_S1_DEP/S2_DEP/CRADLE_DEP` unioned
  into the stow set):** x-span 453.7, y-span 456.8, z_top **586.5mm** —
  inside 609.6 reach × 736.5 height with ~150mm margin.
- Caveat worth noting: `GRP_*` group container shapes double-count the
  full robot bbox; probes must filter to leaf exportable solids or the
  envelope reads spuriously (~632mm z). Counted correctly, it passes.

## Floating parts & fasteners

- Independent nearest-neighbor probe over exportable solids (contact
  = `distToShape ≤ 0.5mm`, early exit): **0 floating parts**.
- Declared mount graph (`exports/mount_graph.json`): BFS from the 43
  ground roots over 3,824 edges reaches **1093/1093 nodes** — every
  solid has a declared mount path to frame.
- Fastener engagement: all **471** `BOLT_/SCRW_/RIVNUT_` solids sit
  ≤0.2mm from a non-fastener or NUT_/WSH_ solid — none floating in air.

## Raw artifacts (session-local)

- `/tmp/sig_committed.json` vs `/tmp/sig_rebuilt.json` — identical
- `/tmp/step_res_{00,01,02,sub}.json` — 1106-file reimport results
- `/tmp/eval_probe_fast.json`, `/tmp/eval_env.json` — probe JSON
- `/tmp/eval_probe_ball{,2,3}.json` — ball-path sweep, designed-line
  sweep, and corridor-transition results
- Gate transcripts: `exports/selfcheck_overhaul0{1,2,3}.txt`
