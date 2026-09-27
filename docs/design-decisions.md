# Design decisions — BIOBUZZ-Robot

## D1 — Parametric primitives, not baked shapes

Each solid is a `Part::Box` / `Part::Cylinder` whose dimensions are bound to
the `Parameters` spreadsheet via `setExpression` (e.g. `Length =
Parameters.chassis_width`). A `Part::Feature` with a baked `Part.makeBox`
shape has no bindable dimensions, so a parameter change could not propagate.

Rationale: a reviewer can change `chassis_width` in one cell and watch every
bound dimension update — the foundation stays editable instead of becoming
frozen geometry.

## D2 — Paths resolved from `__file__`, never from cwd

Both build scripts compute the project root as
`Path(__file__).resolve().parents[2]`. No absolute paths, no reliance on the
current working directory.

Rationale: the same script runs identically from the repo checkout, from a
copied mirror tree, or under an unrelated working directory — which is also
how the evaluator verifies portability.

## D3 — Placeholder volumes only, every assumption labeled UNVERIFIED

The models contain packaging volumes (envelopes, chassis box, wheels, motors,
battery, electronics) — no gears, no mechanisms, no invented detail. Anything
not cited to the Competition Manual carries `DataStatus = "UNVERIFIED"`.

Rationale: an honest placeholder that a team can measure against beats a
detailed-looking model that smuggles in invented numbers. Verified values
(R102, R105, §9.x) are labeled `VERIFIED` with their citation.

## D4 — Always rebuild fresh; archive only foreign content

On each run the scripts rebuild the document from scratch, which makes the
object set identical every time. If the target FCStd contains objects the
script did not create, a timestamped copy is written to `cad\archive\` first.

Rationale: idempotent rebuilds keep the CAD reproducible, while the archive
policy protects any hand-edited content from silent loss.

## D5 — Millimetres everywhere, origin at footprint center on the tile

All models use mm and share one convention: origin at the center of the robot
footprint on the tile surface, +X forward, +Y left, +Z up, Z=0 at tile top
(`docs/coordinate-system.md`).

Rationale: mm is FreeCAD's native unit and matches the manual's metric
equivalents; a centered origin makes mirrored quadrant placements (wheels,
motors) trivially symmetric.

## D6 — Project root is the OneDrive Documents folder (settled 2026-09-20)

The project lives at `C:\Users\pmsma\OneDrive\Documents\BIOBUZZ-Robot`. The
original mission text referenced `C:\Users\pmsma\Documents\BIOBUZZ-Robot`,
which does not exist on this machine. User confirmed 2026-09-20: keep the
OneDrive location.

Rationale: user decision; all build scripts resolve the root relative to
`__file__` anyway, so scripts are unaffected by where the tree sits.

## D7 — goBILDA build ecosystem (team direction, pending purchase)

Team plans to buy into the goBILDA ecosystem (settled 2026-09-20). Wheels,
motors, channels, and structure placeholders should use goBILDA-catalog-
representative sizes.

Status: direction is decided; hardware is NOT yet purchased, so all
goBILDA-derived dimensions remain UNVERIFIED until measured against real
parts or cited from goBILDA datasheets (e.g. 96 mm mecanum wheels are a
goBILDA staple — still verify exact width/bore before manufacturing).

## D8 — Two-phase scoring architecture (team direction, settled 2026-09-20)

Scoring splits into two mechanisms rather than one shared scorer:

- Early game (Auto + most of TeleOp): a shooter that prioritizes launching
  Pollen (~71 mm dia, VERIFIED §9.8) into the Hive cell.
- Final 60 s of TeleOp: a top-mounted lifter that places Nectar (~91 mm
  dia, VERIFIED §9.8) into Flower tops — opening ~101.5 mm dia at ~546 mm
  height (VERIFIED §9.7) — where Nectar cannot be removed and decides
  flower ownership by top-most placement.

Rationale: maximizes endgame flower points while keeping the hive-tipping
game loop simple. The implications flagged at D8 time — shooter Nectar
capability and lifter mechanism type — were settled 2026-09-20 by D10
(universal ~100 mm bore, Nectar-capable) and D11 (cascade elevator);
the remaining diverter/hopper feed path is a tracked question in
`docs/open-questions.md`.

## D9 — Drivetrain: 4× 96 mm goBILDA mecanum (settled 2026-09-20)

Four goBILDA 96 mm mecanum wheels in mirrored quadrants, one motor each.

Rationale: holonomic strafing aligns the shooter to the Hive cell and the
lifter to the narrow ~101.5 mm Flower top opening without turning the
chassis. Hardware not yet purchased — dims stay VENDOR-PENDING.

## D10 — Shooter: dual flywheel, universal ~100 mm bore (settled 2026-09-20)

Counter-rotating flywheel pair launches Pollen (~71 mm, VERIFIED §9.8) and
must also accept Nectar (~91 mm, VERIFIED §9.8) — bore ~100 mm assumed,
UNVERIFIED pending prototyping.

Rationale: dual-flywheel is the standard FTC ball launcher (compact,
controllable, channel-fed); a universal bore enables mixed-load Hive tips
and a backup flower-dump path at small packaging cost.

## D11 — Lifter: cascade elevator (settled 2026-09-20)

Top-mounted goBILDA cascade/linear-slide elevator carries a Nectar cradle;
stows inside the 457.2 mm start cube (VERIFIED R102), deploys within the
457.2 × 609.6 × 736.5 mm expansion volume (VERIFIED R105) toward the ~546 mm
Flower top (VERIFIED §9.7).

Rationale: a pure-vertical lift keeps the cradle centered over the narrow
~101.5 mm Flower opening; an arm's arc would make the precise top-load
harder.

## D12 — Datasheet-driven width corrections (settled 2026-09-20, sprint-06)

`wheel_width` corrected 25 → 32 mm and `motor_dia` 40 → 36 mm after the
goBILDA sources were fetched: 96 mm mecanum wheel set 3213-3606-0002 and
its dimension schematic 3606-0000-0096 (Ø96 × 32 mm, Ø14 rollers, ~10 per
wheel at 45° slant, 207 g), plus the Yellow Jacket 5203-series motor page
(Ø36 gearbox, 8 mm REX shaft). `intake_width` narrowed 330 → 326 mm as a
consequence: at the cited 32 mm wheel width, wheel inner faces sit at
±164 mm and the intake frame must clear them (~1.4 mm margin retained).
Roller placeholders are modeled as straight cylinders tangent to the Ø96
datasheet envelope (`mec_roll_len` = 20 keeps flat end caps inside it).

Rationale: values now trace to a real vendor document instead of invented
placeholders; statuses stay VENDOR-PENDING (not VERIFIED) until physical
measurement. The ~1 mm intake-to-wheel clearance is a placeholder-fidelity
limit, flagged as UNVERIFIED — the real intake design must revisit this
gap.

## D13 - Viewer deviations corrected during CAD overhaul (sprint-02, UNVERIFIED pending team review)

Two viewer-robot.js fudge geometries turned out to be physically
impossible once the sprint-02 intake was dimensioned honestly; both were
corrected in CAD (approved by the planner + evaluator as honest-physics
corrections):

1. Compliant star roller repositioned (X=133, Z=175, viewer had it at
   Z~91). At viewer coords the nip surface gap was -10.15 mm (rollers
   interleaved) and g + 17.8 mm float travel could never reach the
   91 mm NECTAR requirement. Separately, the under-crown throat is only
   ~71.8 mm, so the ball path physically must go OVER the crown into the
   hopper basin; the exit ramp became a THROAT_GUARD deflector.
2. Counter-rotation via crossed quarter-twist belt + sprung tensioner
   instead of the viewer's 1:1 24T spur pair -- a rigid gear mesh cannot
   hold across a 17.8 mm floating shaft (same 'defies physics' class as
   the original CAD rejection).

Sprint-04 obligation (planner condition): the viewer-consistency pass
flows these corrections BACK into viewer/js/robot.js so the viewer and
CAD reconverge -- the artifacts diverge only until sprint-04.

Sprint-03 interface contract (frozen): AXIS_TURRET, REF_DECK_IFACE
(bolt-circle + bore datum) and REF_DIV_PORT are published as
non-exportable REF_/AXIS_ datums in the sprint-02 Appendix tables --
sprint-03 builds against their letter.

Rationale: physical credibility (non-negotiable rubric criterion)
outranks viewer-matching; the corrections are documented rather than
silent.
