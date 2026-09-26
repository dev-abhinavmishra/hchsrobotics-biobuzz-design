# Requirements — BIOBUZZ-Robot

This file separates **manual-cited constraints** (VERIFIED against the BIOBUZZ
Competition Manual TU01) from **assumptions** (UNVERIFIED placeholders awaiting
measurement or team decision).

## Verified constraints (Competition Manual TU01)

| Constraint | Value | Source |
|---|---|---|
| Starting size limit | 457.2 mm cube (18 in side), self-contained | R101 |
| Expansion volume | 457.2 × 609.6 mm footprint × 736.5 mm max height; 736.5 mm dimension stays vertical; hard physical stops required | R105, G416 |
| Field | ~3657.6 mm square, 36 foam tiles | §9.2 |
| Pollen ball | ~71 mm dia, yellow; not perfectly spherical | §9.8 |
| Nectar ball | ~91 mm dia, alliance colored; not perfectly spherical | §9.8 |
| Hive cell opening | ~508 × 356 mm opening, ~305 mm deep; bi-stable pivot | §9.6 |
| Flower top opening | ~101.5 mm dia at ~546 mm height | §9.7 |
| AprilTags | 82.55 mm (3.25 in) square | §9.9 |
| Match timing | 30 s autonomous + 2 min TeleOp; Flower scoring in final 60 s | §8 / §10 |
| Hive protection | Robot may not manipulate Hive motion | G417 |

## Assumptions (UNVERIFIED — placeholders, not commitments)

| Assumption | Value | Status |
|---|---|---|
| Chassis footprint | 420 × 420 mm | UNVERIFIED — conservative packaging guess |
| Drivebase volume height | 120 mm | UNVERIFIED |
| Chassis plate thickness / ride height | 20 mm / 30 mm | UNVERIFIED |
| Wheels | 96 mm dia × 32 mm wide | VENDOR-PENDING — goBILDA schematic 3606-0000-0096 (sprint-06) |
| Wheel rollers | Ø14 mm, ~10 per wheel at ~45° slant, X-pattern | VENDOR-PENDING — same schematic; count pending vendor STEP |
| Wheel offsets from origin | ±170 mm X, ±180 mm Y | UNVERIFIED |
| Motors | 36 mm dia × 90 mm, beside each wheel | VENDOR-PENDING dia (Yellow Jacket 5203 page) / UNVERIFIED len |
| Battery | 180 × 90 × 75 mm | UNVERIFIED |
| Electronics / control hub | 160 × 120 × 35 mm | UNVERIFIED |

Every UNVERIFIED row must be replaced with a measured or cited value before
any part is manufactured. See `docs/robot-parameters.md` for the canonical
table and `docs/open-questions.md` for what is still undecided.

## Deliverable status (sprint-06)

- `exports\prototype_stl\master_robot_PROTOTYPE.stl` and
  `exports\prototype_step\master_robot_PROTOTYPE.step` — delivered;
  placeholder solids only (71 exportable leaf solids incl. 40 mecanum
  rollers + detail solids), labeled `PROTOTYPE / VERIFY BEFORE
  MANUFACTURING` in filename + `exports\MANIFEST.md`.
- `exports\renders\master_{front,side,top,iso}.svg` — headless colored
  per-subsystem filled previews + wireframe overlay + legend (no GUI
  renderer exists in `freecadcmd`; SVG projections are the documented
  approach; iso = orthographic az 45° / el 35.264°).
- Exports deliberately exclude the `ENV_*`/`AXIS_*`/`REF_*` references and
  `VOL_*` packaging reserves — see `exports\MANIFEST.md`.
