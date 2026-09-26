# Open questions — BIOBUZZ-Robot

Genuinely unresolved items for the BIOBUZZ robot. Nothing on this page is
decided; placeholders in the CAD are UNVERIFIED guesses or VENDOR-PENDING
catalog values (see `docs/robot-parameters.md`).

- DECIDED (2026-09-20): the shooter is universal — dual flywheel with a
  ~100 mm bore serving both Pollen and Nectar (D10). A diverter placeholder
  now routes Pollen→shooter vs Nectar→lifter hopper in the transfer
  concept — does the real paddle geometry survive the ~91 mm ball?
- DECIDED (2026-09-20): lifter is a top-mounted cascade elevator with a
  Nectar cradle (D11); the placeholder uses 3 nested stages + carriage +
  an R105 hard-stop marker. Follow-ups: real stage count/travel vs the
  ~546 mm target inside the 736.5 mm cap; actual hard-stop hardware?
- DECIDED (2026-09-20): drivetrain is 4× 96 mm goBILDA mecanum, one motor
  per wheel (D9). Sprint-06 cited the goBILDA schematic (Ø96 × 32 mm, Ø14
  rollers, ~10/wheel at 45°, 207 g) and the Yellow Jacket 5203 series page
  (Ø36 gearbox, 8 mm REX, ~438 g for 13.7:1) — values now VENDOR-PENDING
  with citations; remaining open: exact roller count (schematic shows ~10,
  vendor STEP authoritative), motor ratio choice, flywheel datasheet.
- Does the 420 × 420 mm chassis footprint still fit once the real intake
  depth and transfer channel are designed?
- How is the transfer channel driven — belts, rollers, or gravity — and does
  its 110 × 110 mm clear section survive contact with real structure?
- Where does the Nectar enter the lifter cradle — direct from the intake, a
  dedicated Nectar path, or handoff from the transfer channel?
- RESOLVED (2026-09-20, sprint-04; sprint-06 update): the flagged `VOL_*`
  overlaps are resolved — intake narrowed to 326 mm once the cited 32 mm
  wheel width put inner faces at ±164 mm, the
  transfer lane dropped to floor level z 10–120 through the chassis bay
  and ends at the intake face. Declared co-locations (channel inside
  `VOL_DRIVEBASE`, intake in the front chassis bay, cascade telescoping,
  deployed-vs-stowed lifter envelopes) are documented in the sprint-04
  contract; all other leaf pairs are disjoint.
- How many balls must the robot hold at once — does the transfer channel
  double as storage, and for which game piece?
- What sensor/camera mounts are needed for AprilTag alignment (82.55 mm
  tags, §9.9) at the Hive and Flower targets?
- Which parameters in `docs/robot-parameters.md` should be locked first so
  the CAD stops being a guess?
