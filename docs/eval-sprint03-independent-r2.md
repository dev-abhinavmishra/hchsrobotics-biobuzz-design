# Independent evaluation r2 — sprint-03/04 state (`main`)

Evaluator: Devin (cloud session), cold read, adversarial but
verify-first. Second independent pass — the first landed at
`docs/eval-sprint03-independent.md` (PR #4, commit `49b2cee`) and
graded ball-path FAIL. This pass re-verifies everything with **new,
independently written probes** and extends the wire/corridor
measurements.

Target: `main` @ `b1ceb92`. The eval brief pinned `4221246`; HEAD has
since advanced two commits (`49b2cee` eval doc, `b1ceb92`
viewer/docs/drawings resync). `git diff 4221246..b1ceb92` touches only
`viewer/`, `docs/`, and the drawings manifest — **CAD, builders, gates,
and exports are byte-identical between the two commits**, so results
apply to both.

Toolchain: FreeCAD **1.1.3** AppImage headless (`freecadcmd`), same as
the gate contract. All numbers below come from probes written for this
eval (`~/eval-probes/probe_{geom,path,wires,mounts,exports,tables}.py`);
nothing reuses builder/gate code paths. Probes open the built
`cad/master_robot.FCStd` and `exports/step/` artifacts and measure
solids directly.

## Verdict summary

| Area | Claim | Verdict |
|---|---|---|
| selfcheck_overhaul01 | 45/45 | **PASS — 45/45** |
| selfcheck_overhaul02 | 61/61 | **PASS — 61/61** |
| selfcheck_overhaul03 | 73/73 | **PASS — 73/73** |
| Rebuilds "bit-identical" | bit-identical | **PARTIAL — geometry identical, FCStd bytes differ** |
| Part STEPs reimport | 1089/1089 | **PASS — 1089/1089** |
| Ball path Ø93 | clears all statics | **FAIL — wiring + rope + fasteners intrude** |
| Yaw drive | external mesh @72.8, pinion clears column | **PASS** |
| Lazy susan | two separate races | **PASS** |
| Envelopes | 457.2 stow / 609.6×736.5 deployed | **PASS** |
| Floating parts / fasteners | mount path + engaged bores | **PASS** |
| Exports BOM/params/naming | coverage sane | **PASS (1 rounding nit)** |

## Gate suites (re-run, not just committed logs)

All three gates re-run from a clean worktree under freecadcmd 1.1.3:

| Suite | Claimed | Measured |
|---|---|---|
| selfcheck_overhaul01 | 45/45 | **45/45** (exit 0) |
| selfcheck_overhaul02 | 61/61 | **61/61** (exit 0) |
| selfcheck_overhaul03 | 73/73 | **73/73** (exit 0) |

Operational caveat (confirmed with the first evaluator): `GIT2_tree_clean`
gates on `git status --porcelain`, so any stray untracked file mid-run
flips it. A clean-tree run is required to reproduce 73/73; this is
environmental, not a model defect.

## Rebuild determinism

Method: two independent full `build_*` passes in separate worktrees
from identical source; per-solid signature `[name → bbox6, volume]`
dumped for every solid in all 7 FCStd docs, plus sha256 of each
`cad/**/*.FCStd` (61 files).

- Per-solid geometry signatures: **15,136/15,136 identical** between
  the two build passes (all docs, all solids — bbox and volume).
- FCStd file bytes: **7/7 regenerated docs differ in sha256**
  (FreeCAD serialization nondeterminism); the 54 non-regenerated
  files are byte-identical.

**Verdict:** rebuilds are geometry-deterministic; the literal claim
"bit-identical" is false of file bytes. Recommend wording the claim
"geometry-identical" — the DET* signature gates already check that.

## STEP exports & reimport

- `exports/step/parts/`: **1089/1089** files reimport — `Part.read`
  yields a non-empty, named solid with a sane bbox (<1 m extent) for
  every file. No missing/extra files vs the 1089-object exportable
  census.
- Product naming/positions sane (spot-checked against FCStd bboxes).
- `export_step_report.json`'s `master_step_reimport: 1222` vs 1089 is
  an occurrence count over nested products, not a file count — matches
  the r1 reading.

## BOM / parameters coverage

- `exports/bom/bom.csv`: **1089/1089 exportable solids** appear in the
  per-row `objects` column; the only non-solid entries are the 4
  `WHEEL_ASSY_{FL,FR,RL,RR}` aggregate rows. (Explains the 1093 count
  in r1 — the 4 wheel assemblies are bom-level groupings, not
  additional solids.)
- `exports/bom/parameters.csv`: sheet has 273 alias rows (1 header +
  272 params); **all 272 CSV rows match sheet aliases, zero missing**.
  One value nit: `nip_rest_gap` is rounded to 4 decimals in CSV
  (84.7433 vs sheet 84.743277) — cosmetic.

## Ball path — independent Ø93 corridor sweep

Two probes: (a) a per-station sphere + per-segment capsule sweep
against every exportable solid (17 segments, 18 station spheres,
r46.5); (b) per-wire/per-rope tube vs every corridor segment plus the
port-area fasteners. Exempt-by-design ride surfaces: `LOAD_CHUTE` bed,
flywheel nip faces, `CRADLE_CUP` — plus the intake rollers/feed wheel
the ball mechanically rides and actuated members (`AGIT_PADDLE/HORN`,
`GATE_FLAG/HORN`, `DIV_FLAP/SHAFT`) that occupy the ball volume as
mechanism poses.

**Result: FAIL — real, path-independent intrusions confirmed** (r1
verdict upheld, local flag confirmed and extended):

| Intruder | Corridor leg | Clearance | Common vol |
|---|---|---|---|
| `WIRE_FLY_L` | S14_nip→S15_chute_leg1 | **0.0 mm** | **621.1 mm³** |
| `WIRE_FLY_L` | S13_col_exit→S14_nip | **0.0 mm** | touch |
| `WIRE_CAM_USB` | S12_flange→S13_col_exit | **0.21 mm** | touch (graze) |
| `WIRE_CAM_USB` | S13_col_exit→S14_nip | **0.0 mm** | touch |
| `ROPE_DYNEEMA` | S16_chute_leg2→S17_cradle | **0.0 mm** | **80.3 mm³** |
| `BOLT_PORT_1`, `BOLT_PORT_2` | S10_gate→S11_port | **1.13 mm** | graze |

- `WIRE_FLY_L` (flagged "~4mm graze") is **worse than a graze**: its
  polyline crosses y=0 at (−114, 0, 272), inside the ball's post-nip
  descent space — 621 mm³ common, zero clearance. It also touches the
  S13→S14 corridor leg.
- `WIRE_CAM_USB` (flagged "1–2mm graze") measured **0.21 mm** clear on
  S12→S13 plus a touch on S13→S14 — tighter than flagged. Its first
  leg runs (−8,0,288)→(−30,−30,278), directly through the launch
  plane.
- **New vs r1:** `ROPE_DYNEEMA` intrudes 80 mm³ into the
  chute-leg2→cradle leg — the winch line crosses the ball's final
  approach.
- `BOLT_PORT_1/2` heads leave 1.13 mm clearance on the gate→port leg —
  same observation as r1's "port fasteners graze the only feasible
  transition", measured as clearance rather than common volume.
- All other routed members (`WIRE_BATT_SW`, `WIRE_SW_CTRL`,
  `WIRE_HUB_RS485`, `WIRE_MTR_*`, `WIRE_ENC_*`, `WIRE_WINCH`,
  `WIRE_TILT_SV`, `WIRE_YAW_SV`, `WIRE_FLY_R`, `WIRE_HOOD_SV`,
  `ROPE_GUIDE`) are clear or >3 mm.

**Secondary observations from the full sweep:**

- Structural grazes at the cradle approach: `CHUTE_LIP_L1/L2` (1.1–2.2K
  mm³), `CRADLE_PIV` (~3–4K mm³), `CRADLE_COL_1` (~0.1K) on
  S16→S17/S17 — the ball drops past chute-lip walls and cradle pivot
  hardware; tight but plausibly intended contact surfaces.
- Straight-chord artifacts: a linear S14_nip→S15 leg cuts through the
  launch stack (`FLY_MCLAMP_L` 19K, `TURRET_PLATE` 15.4K,
  `LAUNCH_CHEEK_L` 14.4K, `FLY_MOTOR_L` 7.6K, `RING_GEAR` 4.8K mm³).
  Same caveat r1 documented — the physical exit follows the flywheel
  tangent + chute bed, not the straight chord, so those hits are
  corridor-model artifacts, not blockers. r1's port-height analysis
  showed the feasible corridor exists and grazes only the port
  fasteners above.
- Intended-contact hits (exempted above): `FEED_WHEEL` up to ~88K mm³,
  `ROLLER_*`/`STAR_SHAFT` tens of K mm³, `FLY_SHAFT` ~0.1K — all
  ride-surface/mechanism contacts at intake and feed stations.
- **Gate gap (mechanism):** `GEOB_ball_path` samples only the discrete
  stations; every confirmed intrusion lies *between* stations — the
  gate is correct where it measures and blind where it doesn't.

## Discrepancies vs the r1 evaluation

- **Agree:** all gate scores, geometry determinism, STEP counts
  (1089 parts; r1's 1106 includes 16 subassemblies + master — same
  files, different denominator), envelopes, yaw, susan, mounts, and
  the ball-path FAIL verdict.
- **Differ:** r1 quoted wire intrusions ≤151 mm³ on S13→S14 only; my
  corridor measure finds 621 mm³ on S14→S15 plus the rope on
  S16→S17 — the intrusion set is broader than r1 reported. r1's
  port-fastener graze (≤10.4 mm³) and my 1.13 mm clearance are the
  same observation in different metrics.
- r1 counted 1093 "master solids" — that includes the 4 `WHEEL_ASSY_*`
  bom aggregates; the exportable solid census is 1089.

## Yaw drive — measured on built solids

- `RING_GEAR`↔`YAW_PINION` center distance: **72.80 mm** (claimed 72.8),
  external mesh confirmed — pinion outside ring pitch circle, teeth
  overlap in plan.
- Ring tip r = 64.4 (OD 128.8 claimed), pinion tip r = 13.9 (OD 27.8
  claimed); both on pitch radii consistent with 72T/14T.
- Pinion→`FEED_COLUMN` clearance: **3.9 mm** — fully clear of the Ø110
  column (r1 measured 4.86 to a different surface; both clear).
- Z overlap sane: ring 256.5–263.0, pinion 256.9–262.9.

## Lazy susan — measured on built solids

- Two distinct solids, zero common: `LAZY_SUSAN_LO` z=248.00–252.25,
  `LAZY_SUSAN_HI` z=252.25–256.50, both Ø132 / Ø116 bore, ~4.25 mm
  races.
- Load path verified by contact: LO→`TURRET_DECK` dist 0.0; HI→
  `RING_GEAR` dist 0.0; `RING_GEAR`→`TURRET_PLATE` dist 0.0. (HI sits
  6.5 mm off the plate *with the ring gear between them* — the claimed
  HI→plate race carries the rotating plate through the gear.)

## Envelopes — union bbox of 1089 exportable solids

- **Stowed:** 453.7 × 454.5 × 379.0 mm — inside the 457.2 cube on all
  axes.
- **Deployed** (`VOL_S1_DEP/S2_DEP/CRADLE_DEP` positions): max radial
  reach **284.7 mm** (limit 609.6), max height **586.5 mm** (limit
  736.5). Passes with large margin.

## Floating parts & fasteners

- Nearest-solid probe over all 1089 exportable solids: **0 floating**
  (every solid ≤0.5 mm from a neighbor; typical press/mount gaps
  0–0.25 mm).
- Fastener engagement: 751 `BOLT_/SCRW_/NUT_/WASH_/STDF_` solids all
  contact or embed in a non-fastener member (0 isolated).
- Bore evidence: every fastener either embeds >0.5 mm³ into a member or
  touches ≥2 members — consistent with real joints (through-bolt +
  nut, screw into standoff, etc.). 0 suspects.

## Exports — names/positions

- All 1089 part STEP files reimport with non-empty geometry, product
  names matching solid names, and bboxes identical to FCStd placement
  (<1 mm).

## Discrepancies vs the r1 evaluation

- **Agree:** all gate scores, geometry determinism, STEP counts
  (1089 parts; r1's 1106 includes 16 subassemblies + master — same
  files, different denominator), envelopes, yaw, susan, mounts, and
  the ball-path FAIL verdict.
- **Differ:** r1 quoted wire intrusions ≤151 mm³ on S13→S14 only; my
  corridor measure finds 621 mm³ on S14→S15 plus the rope on
  S16→S17 — the intrusion set is broader than r1 reported. r1's
  port-fastener graze (≤10.4 mm³) and my 1.13 mm clearance are the
  same observation in different metrics.
- r1 counted 1093 "master solids" — that includes the 4 `WHEEL_ASSY_*`
  bom aggregates; the exportable solid census is 1089.

## Bottom line

The claimed gate scores are real and reproducible; determinism is
solid at the geometry level; exports are complete and clean. The one
hard failure remains the **ball path**: routed wiring
(`WIRE_FLY_L`, `WIRE_CAM_USB`), the dyneema lift line, and port
fastener heads occupy the D93 corridor between stations — unchanged
from r1, now measured to worse tolerances. PASS everywhere else.

Report only — no production edits.
