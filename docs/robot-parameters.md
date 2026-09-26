# Robot parameters — BIOBUZZ-Robot

Canonical parameter table for the BIOBUZZ CAD foundation. The `Parameters`
spreadsheet inside each FCStd binds geometry to the alias names below; this
file is the human-readable source of truth for what each value means and how
much to trust it.

**Status enum:** `VERIFIED` = cited to the Competition Manual TU01 ·
`UNVERIFIED` = assumed placeholder · `VENDOR-PENDING` = goBILDA-catalog-
representative value, pending purchase/datasheet confirmation (never
presented as VERIFIED). Aliases are shared across files where they name the
same quantity.

## Envelopes (VERIFIED — Competition Manual TU01)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `start_cube` | 457.2 | mm | VERIFIED | master, lifter | R102 — 18 in start cube |
| `expansion_width` | 457.2 | mm | VERIFIED | master, lifter | R105 — 18 in side |
| `expansion_depth` | 609.6 | mm | VERIFIED | master, lifter | R105 — 24 in side |
| `expansion_height` | 736.5 | mm | VERIFIED | master, lifter | R105 — 29 in, stays vertical |

## Drivebase / chassis (master + drivebase_concept_v01)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `chassis_length` | 420 | mm | UNVERIFIED | master, drivebase, electronics | assumed packaging footprint (X) |
| `chassis_width` | 420 | mm | UNVERIFIED | master, drivebase, electronics | assumed packaging footprint (Y) |
| `chassis_height` | 120 | mm | UNVERIFIED | master, electronics | assumed drivebase packaging height |
| `wheel_dia` | 96 | mm | VENDOR-PENDING | master, drivebase | goBILDA 96 mm mecanum set 3213-3606-0002 — schematic 3606-0000-0096: Ø96 measured at roller surfaces |
| `wheel_width` | 32 | mm | VENDOR-PENDING | master, drivebase | goBILDA schematic 3606-0000-0096 overall width (was 25 placeholder → corrected sprint-06) |
| `wheel_x_offset` | 140 | mm | UNVERIFIED | master, drivebase | assumed wheel center offset ±X (rehaul sprint-01: was 170; keeps motor bodies clear of the end rails) |
| `wheel_y_offset` | 180 | mm | UNVERIFIED | master, drivebase | assumed wheel center offset ±Y; roller OD leaves 0.6 mm margin to R102 cube |
| `motor_dia` | 36 | mm | VENDOR-PENDING | master, drivebase | goBILDA Yellow Jacket 5203-series ~36 mm gearbox dia (D12) |
| `motor_len` | 60 | mm | UNVERIFIED | master, drivebase | motor body length inward through the side-rail mouth (was 90 in the old drivebase concept) |
| `roller_count` | 10 | count | VENDOR-PENDING | master, drivebase | counted on goBILDA schematic 3606-0000-0096 (~10 visible); vendor STEP file authoritative |
| `mec_roll_dia` | 14 | mm | VENDOR-PENDING | master, drivebase | goBILDA schematic 3606-0000-0096 Ø14 roller |
| `mec_roll_rad` | 41 | mm | VENDOR-PENDING | master, drivebase | derived (wheel_dia − mec_roll_dia)/2 — roller surfaces reach Ø96 |
| `mec_roll_len` | 20 | mm | UNVERIFIED | master, drivebase | assumed roller length; ≤20 keeps flat-cap cylinder ends inside the Ø96 envelope |
| `mec_roll_pitch` | 36 | deg | VENDOR-PENDING | master, drivebase | derived 360/roller_count |
| `mec_roll_slant` | 45 | deg | UNVERIFIED | master, drivebase | mecanum roller slant; FTC X-pattern (FL+RR one slant, FR+RL opposite) |
| `mec_pin_dia` | 5 | mm | UNVERIFIED | master, drivebase | roller axle pin dia; pin tips embed ~1 mm into the wheel face plates |
| `mec_pin_len` | 34 | mm | UNVERIFIED | master, drivebase | roller pin overall length (spans the roller + both seat embeds) |

## Drivetrain hardware (rehaul sprint-01 — partkit component detail)

Shared `partkit.py` component vocabulary used by `master_robot.FCStd` and
`drivebase_concept_v01.FCStd`. U-channels are cut solids (outer box −
interior void − hole grid − shaft notches); plates are filleted solids;
motor mounts/bearing blocks are bored + bolt-hole + edge-chamfer
features; every wheel is a `WHEEL_ASSY_*` carrier (hub, IN/OUT face
plates, 10 roller+pin fused bodies) placed as a unit.

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `rail_size` | 48 | mm | VENDOR-PENDING | master, drivebase | goBILDA 1120 U-channel ~48 mm outer (D12) |
| `rail_wall` | 2.5 | mm | UNVERIFIED | master, drivebase | assumed ~0.09 in channel sheet wall; measure on hardware |
| `notch_w` | 16 | mm | UNVERIFIED | master, drivebase | shaft clearance notch width through side-rail mouth |
| `notch_d` | 14 | mm | UNVERIFIED | master, drivebase | shaft clearance notch depth (from web toward mouth) |
| `hole_dia` | 4 | mm | VENDOR-PENDING | master, drivebase | goBILDA hole-grid ~Ø4 holes, catalog typical |
| `hole_pitch` | 48 | mm | UNVERIFIED | master, drivebase | subset of the 8 mm goBILDA grid; visual pitch assumed |
| `pan_thk` | 3 | mm | UNVERIFIED | master, drivebase | belly pan sheet inside frame ring |
| `deck_thk` | 3 | mm | UNVERIFIED | master | rear deck sheet flanking the ball channel |
| `pan_fillet` | 8 | mm | UNVERIFIED | master, drivebase | belly pan corner fillet |
| `deck_fillet` | 8 | mm | UNVERIFIED | master | rear deck corner fillet |
| `plate_fillet` | 4 | mm | UNVERIFIED | master, drivebase | small-plate edge chamfer/fillet |
| `wplate_dia` | 92 | mm | UNVERIFIED | master, drivebase | mecanum side plate dia, inset inside Ø96 envelope |
| `wplate_thk` | 4 | mm | UNVERIFIED | master, drivebase | mecanum side plate thickness |
| `wplate_gap` | 1 | mm | UNVERIFIED | master, drivebase | face plate standoff inside the Ø96 envelope face |
| `hub_dia` | 26 | mm | UNVERIFIED | master, drivebase | wheel hub OD |
| `hub_w` | 20 | mm | UNVERIFIED | master, drivebase | wheel hub width |
| `bore_dia` | 8.4 | mm | VENDOR-PENDING | master, drivebase | 8 mm REX clearance bore (goBILDA REX bore typical) |
| `plate_bore` | 9 | mm | UNVERIFIED | master, drivebase | wheel face plate shaft clearance bore |
| `shaft_dia` | 8 | mm | VENDOR-PENDING | master, drivebase | goBILDA 8 mm REX shaft standard, series page |
| `shaft_len` | 76 | mm | UNVERIFIED | master, drivebase | live shaft: motor face → web notch → bearing → hub |
| `bear_w` | 26 | mm | UNVERIFIED | master, drivebase | bearing block face width |
| `bear_h` | 26 | mm | UNVERIFIED | master, drivebase | bearing block face height |
| `bear_t` | 6 | mm | UNVERIFIED | master, drivebase | bearing block thickness |
| `bear_bore` | 8.4 | mm | VENDOR-PENDING | master, drivebase | bearing bore, 8 mm REX clearance |
| `bear_bolt_d` | 4 | mm | UNVERIFIED | master, drivebase | bearing block bolt hole dia |
| `bear_bolt_off` | 9 | mm | UNVERIFIED | master, drivebase | bearing bolt hole offset from bore center |
| `mface_w` | 30 | mm | UNVERIFIED | master, drivebase | motor face plate width |
| `mface_h` | 30 | mm | UNVERIFIED | master, drivebase | motor face plate height |
| `mface_t` | 2.5 | mm | UNVERIFIED | master, drivebase | motor face plate thickness |
| `cheek_bore` | 11 | mm | UNVERIFIED | master | cheek clearance bore for the drive shaft (Ø8 + 3 mm) |
| `axle_bore` | 13 | mm | UNVERIFIED | master | cheek clearance bore for the intake pivot axle (Ø12 + 1 mm) |
| `imount_l` | 20 | mm | UNVERIFIED | master | intake cheek mount bracket length |
| `imount_h` | 20 | mm | UNVERIFIED | master | intake cheek mount bracket height |
| `csupp_w` | 10 | mm | UNVERIFIED | master | channel saddle support width |
| `csupp_h` | 9.5 | mm | UNVERIFIED | master | channel saddle height (pan top to channel floor) |
| `sfloor_thk` | 10 | mm | UNVERIFIED | master | shooter floor plate thickness |
| `sside_thk` | 6 | mm | UNVERIFIED | master | shooter side plate thickness |
| `daxle_dia` | 6 | mm | UNVERIFIED | master | diverter hinge axle dia |

## Electronics packaging (master)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `battery_l` | 180 | mm | VENDOR-PENDING | master, electronics | REV-style battery placeholder — datasheet pending |
| `battery_w` | 55 | mm | UNVERIFIED | master | slim pack assumed; electronics concept keeps 90 mm VENDOR-PENDING (different sheets) |
| `battery_h` | 35 | mm | UNVERIFIED | master | slim pack assumed; clears the rear deck underside; electronics concept keeps 75 mm VENDOR-PENDING |
| `battery_x` | -190 | mm | UNVERIFIED | electronics | battery placement X (concept-local frame) |
| `battery_y` | -45 | mm | UNVERIFIED | electronics | battery placement Y (concept-local frame) |
| `battery_z` | 22.5 | mm | UNVERIFIED | electronics | battery placement Z (concept-local frame) |
| `bat_x` | -110 | mm | UNVERIFIED | master | battery X — −Y bay, forward of the rear motor corridor (rehaul sprint-01) |
| `bat_y` | -113 | mm | UNVERIFIED | master | battery Y — −Y bay between channel wall and side-rail web (rehaul sprint-01) |
| `bat_z` | 5.5 | mm | UNVERIFIED | master | sits on belly pan top (rail_wall + pan_thk) (rehaul sprint-01) |
| `elec_l` | 160 | mm | UNVERIFIED | master | assumed control-hub length |
| `elec_w` | 55 | mm | UNVERIFIED | master | slim stack assumed; fits bay between channel wall and side-rail web (was 120) |
| `elec_h` | 28 | mm | UNVERIFIED | master | slim stack assumed; clears the rear deck underside (was 35) |
| `elec_x` | -120 | mm | UNVERIFIED | master | hub X — belly mount, X-clear of wheels (sprint-04) |
| `elec_y` | 60 | mm | UNVERIFIED | master | hub Y — +Y side, clear of ±55 channel (sprint-04) |
| `elec_z` | 11.5 | mm | UNVERIFIED | master | hub Z — on electronics rails atop the belly pan (rehaul sprint-01) |
| `hub_l` | 160 | mm | VENDOR-PENDING | electronics | REV-style hub placeholder — datasheet pending |
| `hub_w` | 120 | mm | VENDOR-PENDING | electronics | REV-style hub placeholder — datasheet pending |
| `hub_h` | 35 | mm | VENDOR-PENDING | electronics | REV-style hub placeholder — datasheet pending |
| `ctrl_x` | 40 | mm | UNVERIFIED | electronics | control hub placement X |
| `ctrl_y` | -60 | mm | UNVERIFIED | electronics | control hub placement Y |
| `ctrl_z` | 42.5 | mm | UNVERIFIED | electronics | control hub placement Z |
| `exp_x` | -190 | mm | UNVERIFIED | electronics | expansion hub placement X |
| `exp_y` | 60 | mm | UNVERIFIED | electronics | expansion hub placement Y |
| `exp_z` | 42.5 | mm | UNVERIFIED | electronics | expansion hub placement Z |
| `erail_l` | 140 | mm | UNVERIFIED | master, electronics | hub mounting rail length |
| `erail_w` | 8 | mm | UNVERIFIED | master, electronics | hub mounting rail width |
| `erail_h` | 6 | mm | UNVERIFIED | master, electronics | hub mounting rail height |

## Coordinate markers (master)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `axis_len` | 120 | mm | UNVERIFIED | master | reference-marker length (cosmetic) |
| `axis_thk` | 4 | mm | UNVERIFIED | master | reference-marker thickness (cosmetic) |

## Intake (master VOL_INTAKE + intake_concept_v01)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `intake_depth` | 160 | mm | UNVERIFIED | master, intake | assumed intake frame depth |
| `intake_width` | 326 | mm | UNVERIFIED | master, intake | mouth width — corrected sprint-06: datasheet 32 mm wheels put inner faces at ±164 (was 330 with 25 mm placeholders) |
| `intake_height` | 120 | mm | UNVERIFIED | master, intake | assumed intake frame height |
| `throat_clear_w` | 120 | mm | UNVERIFIED | intake | assumed; clears ~91 mm ball + margin (§9.8) |
| `throat_clear_h` | 110 | mm | UNVERIFIED | intake | assumed; clears ~91 mm ball + margin (§9.8) |
| `throat_depth` | 35 | mm | UNVERIFIED | intake | assumed mouth depth |
| `throat_z` | 10 | mm | UNVERIFIED | intake | assumed mouth base height |
| `roller_dia` | 30 | mm | UNVERIFIED | intake, master | intake roller tube OD (master rep clears the rail top flange; concept rep O50) |
| `roller_width` | 306 | mm | UNVERIFIED | intake | legacy alias; master roller span now binds `intake_width - 2*plate_w - 2` directly (PAR2-I chain) |
| `plate_w` | 10 | mm | UNVERIFIED | master | intake cheek-plate width (master rep) |
| `roller_x` | 100 | mm | UNVERIFIED | intake | assumed roller center X |
| `roller_z1` | 28 | mm | UNVERIFIED | intake | lower roller center height (rib tips stay above tile plane) |
| `roller_z2` | 95 | mm | UNVERIFIED | intake | upper roller center height |
| `chassis_stub_l` | 60 | mm | UNVERIFIED | intake | chassis edge reference |
| `chassis_stub_w` | 340 | mm | UNVERIFIED | intake | chassis edge reference |
| `chassis_stub_h` | 40 | mm | UNVERIFIED | intake | chassis edge reference |
| `chassis_stub_z` | 30 | mm | UNVERIFIED | intake | chassis edge reference |
| `plate_thk` | 8 | mm | UNVERIFIED | intake, master | thin plate thickness (pivot plates, diverter/shooter reps) |
| `pivot_boss_dia` | 24 | mm | UNVERIFIED | intake, master | assumed pivot boss diameter |
| `pv_boss_dia` | 24 | mm | UNVERIFIED | master | intake cheek pivot-mount boss diameter (master rep) |
| `pv_boss_len` | 20 | mm | UNVERIFIED | master, intake | pivot-mount boss length on cheek |
| `pv_boss_x` | 180 | mm | UNVERIFIED | master | pivot-mount boss center X (forward, clear of lifter pedestal + intake roller — was 84) |
| `pv_boss_z` | 60 | mm | UNVERIFIED | master | pivot-mount boss center height |
| `pivot_boss_x` | 15 | mm | UNVERIFIED | intake | pivot boss center X (rear of plates) |
| `pivot_boss_z` | 60 | mm | UNVERIFIED | intake | pivot boss center height |
| `lip_len` | 45 | mm | UNVERIFIED | intake | mouth lip length (clears the bearing blocks) |
| `lip_w` | 140 | mm | UNVERIFIED | intake | assumed mouth lip width |
| `lip_thk` | 6 | mm | UNVERIFIED | intake | assumed mouth lip thickness |
| `lip_x` | 105 | mm | UNVERIFIED | intake | lip base X |
| `lip_z` | 25 | mm | UNVERIFIED | intake | lip base height |
| `lip_ang` | 20 | deg | UNVERIFIED | intake | lip pitch angle (scoop down toward floor) |
| `nectar_dia` | 91 | mm | VERIFIED | master, intake, transfer | Nectar ball ~91mm, competition manual sec 9.8 - drives `VOL_BALL_PATH` |
| `pollen_dia` | 71 | mm | VERIFIED | master | Pollen ball ~71mm, competition manual sec 9.8 |
| `roller_bore` | 9 | mm | UNVERIFIED | master, intake | cheek bore for the 8mm roller shaft (+1mm clearance) |
| `shaft_dia` | 8 | mm | VENDOR-PENDING | master, intake | goBILDA 8mm REX shaft |
| `bore_dia` | 8.4 | mm | VENDOR-PENDING | master, intake | 8mm REX clearance bore |
| `bear_w`/`bear_h` | 26 | mm | UNVERIFIED | master, intake | bearing block face |
| `bear_t` | 6 | mm | UNVERIFIED | master, intake | bearing block thickness |
| `bear_bore` | 8.4 | mm | VENDOR-PENDING | master, intake | bearing bore |
| `bear_bolt_d`/`bear_bolt_off` | 4.0 / 9.0 | mm | UNVERIFIED | master, intake | bearing bolt pattern |
| `rib_count`/`rib_w`/`rib_h`/`rib_inset` | 12 / 4 / 3 / 6 | mm | UNVERIFIED | master, intake | roller grip-rib layout |
| `servo_l`/`servo_w`/`servo_h` | 40.5 / 20.4 / 36 | mm | VENDOR-PENDING | master, intake, transfer | REV SRS-class servo body |
| `mbolt_d` | 4.4 | mm | UNVERIFIED | master, intake, transfer | M4 clearance bolt hole |
| `imount_l`/`imount_t`/`imount_h` | 20 / 4 / 20 | mm | UNVERIFIED | master | intake mount L-bracket dims |
| `lip_sill_d` | 22 | mm | UNVERIFIED | master | intake mouth sill depth |
| `wall_chamfer` | 0.8 | mm | UNVERIFIED | master, intake, transfer | sheet-edge chamfer |

## Transfer (master VOL_TRANSFER + transfer_concept_v01)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `channel_len` | 340 | mm | UNVERIFIED | transfer | standalone concept channel span; master's `VOL_TRANSFER`/`MECH_CHANNEL` derive their length from the intake face (`start_cube/2 − intake_depth − channel_x0`) and do not bind this alias (sprint-04) |
| `channel_w` | 110 | mm | UNVERIFIED | master, transfer | clears ~91 mm ball + margin (§9.8) |
| `channel_h` | 110 | mm | UNVERIFIED | master, transfer | clears ~91 mm ball + margin (§9.8) |
| `channel_x0` | -160 | mm | UNVERIFIED | master, transfer | channel rear end (scoring side) |
| `channel_z` | 10 | mm | UNVERIFIED | master, transfer | floor-level through-chassis lane; continuous with intake throat (sprint-04) |
| `div_h` | 60 | mm | UNVERIFIED | master | diverter rep marker height (master) |
| `guide_thk` | 10 | mm | UNVERIFIED | transfer | assumed channel wall thickness |
| `zone_thk` | 10 | mm | UNVERIFIED | transfer | zone marker thickness |
| `diverter_axis_dia` | 16 | mm | UNVERIFIED | transfer | assumed diverter hinge diameter |
| `diverter_axis_x` | -150 | mm | UNVERIFIED | transfer | diverter hinge center X (scoring end) |
| `paddle_len` | 100 | mm | UNVERIFIED | transfer | assumed diverter paddle length |
| `paddle_thk` | 8 | mm | UNVERIFIED | transfer | assumed diverter paddle thickness |
| `paddle_ang` | 35 | deg | UNVERIFIED | transfer | diverter paddle angle |
| `route_len` | 90 | mm | UNVERIFIED | transfer | route marker length |
| `route_thk` | 10 | mm | UNVERIFIED | transfer | route marker thickness |
| `route_w` | 20 | mm | UNVERIFIED | transfer | route marker width |
| `horn_l` | 30 | mm | UNVERIFIED | master, transfer | diverter servo horn length |
| `horn_w` | 10 | mm | UNVERIFIED | master, transfer | diverter servo horn width |
| `horn_h` | 20 | mm | UNVERIFIED | master, transfer | diverter servo horn height |
| `paddle_sweep_deg` | 90 | deg | UNVERIFIED | master, transfer | paddle swing arc that clears the O91 lane |
| `daxle_dia` | 6 | mm | UNVERIFIED | master, transfer | diverter hinge shaft dia |
| `chan_wall_t`/`chan_floor_t` | 3 / 3 | mm | UNVERIFIED | master, transfer | channel sheet thickness |
| `bush_dia`/`bush_t`/`bush_bore` | 10 / 4 / 6.4 | mm | UNVERIFIED | master, transfer | diverter wall bushings |
| `paddle_bore` | 6.4 | mm | UNVERIFIED | master, transfer | paddle hinge bore |
| `csupp_w`/`csupp_t` | 10 / 2.5 | mm | UNVERIFIED | master, transfer | channel saddle L-bracket dims |

## Shooter — universal Pollen + Nectar (master VOL_SHOOTER + shooter_concept_v01)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `shooter_l` | 200 | mm | UNVERIFIED | master, shooter | assumed housing length |
| `shooter_w` | 200 | mm | UNVERIFIED | master, shooter | assumed housing width |
| `shooter_h` | 250 | mm | UNVERIFIED | master, shooter | assumed housing height |
| `shooter_z` | 120 | mm | UNVERIFIED | master, shooter | housing base height above tile |
| `flywheel_dia` | 72 | mm | VENDOR-PENDING | shooter, master | goBILDA-style launcher wheel — datasheet pending |
| `flywheel_w` | 30 | mm | VENDOR-PENDING | shooter, master | goBILDA-style launcher wheel — datasheet pending |
| `flywheel_x` | -40 | mm | UNVERIFIED | shooter, master | flywheel center X (inside housing) |
| `bore` | 100 | mm | UNVERIFIED | shooter, master | universal bore per D10 — clear gap between flywheel inner faces; clears ~91 mm Nectar (§9.8) |
| `muzzle_clear` | 110 | mm | UNVERIFIED | shooter | clears ~91 mm Nectar + margin (§9.8) |
| `muzzle_depth` | 30 | mm | UNVERIFIED | shooter | muzzle channel depth |
| `hood_l` | 50 | mm | UNVERIFIED | shooter | hood plate length |
| `hood_w` | 120 | mm | UNVERIFIED | shooter | hood plate width |
| `hood_thk` | 8 | mm | UNVERIFIED | shooter | hood plate thickness |
| `backstop_thk` | 8 | mm | UNVERIFIED | shooter | backstop plate thickness |
| `backstop_h` | 100 | mm | UNVERIFIED | shooter | backstop plate height |
| `inlet_depth` | 40 | mm | UNVERIFIED | shooter | feed inlet depth into housing (−X face) |
| `inlet_w` | 90 | mm | UNVERIFIED | shooter | feed inlet width |
| `inlet_h` | 90 | mm | UNVERIFIED | shooter | feed inlet height |
| `inlet_z` | 130 | mm | UNVERIFIED | shooter | feed inlet base height |
| `launch_len` | 160 | mm | UNVERIFIED | shooter | launch indicator length |
| `launch_thk` | 8 | mm | UNVERIFIED | shooter | launch indicator thickness |
| `launch_z` | 300 | mm | UNVERIFIED | shooter | launch height above tile |
| `stub_dia` | 8 | mm | VENDOR-PENDING | master, shooter | goBILDA 8 mm REX shaft standard — series page |
| `stub_len` | 40 | mm | UNVERIFIED | master, shooter | flywheel stub shaft length |

## Lifter — Nectar, top-mounted (master VOL_LIFTER_* + lifter_concept_v01)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `lifter_stow_l` | 200 | mm | UNVERIFIED | master, lifter | assumed stowed length |
| `lifter_stow_w` | 200 | mm | UNVERIFIED | master, lifter | assumed stowed width |
| `lifter_stow_h` | 150 | mm | UNVERIFIED | master, lifter | assumed stowed height |
| `lifter_stow_x` | 20 | mm | UNVERIFIED | master, lifter | stowed X offset |
| `lifter_stow_z` | 120 | mm | UNVERIFIED | master, lifter | stowed base height (top-mounted) |
| `mast_w` | 80 | mm | UNVERIFIED | master, lifter | deployed mast section |
| `lifter_dep_z0` | 120 | mm | UNVERIFIED | master, lifter | deployed mast base height |
| `reach_z` | 610 | mm | UNVERIFIED | master, lifter | deployed reach; ~546 mm Flower top + clearance (§9.7) |
| `cradle_w` | 120 | mm | UNVERIFIED | lifter, master | cradle width; ~91 mm Nectar + clearance (§9.8) |
| `cradle_h` | 40 | mm | UNVERIFIED | lifter, master | cradle height |
| `cradle_z` | 600 | mm | UNVERIFIED | lifter, master | cradle base height (≥546 mm target, §9.7) |
| `stage1_w` | 76 | mm | UNVERIFIED | lifter, master | outer cascade stage section |
| `stage1_z1` | 340 | mm | UNVERIFIED | lifter, master | outer stage top |
| `stage2_w` | 74 | mm | UNVERIFIED | lifter, master | middle cascade stage section |
| `stage2_z0` | 230 | mm | UNVERIFIED | lifter, master | middle stage base |
| `stage2_z1` | 440 | mm | UNVERIFIED | lifter, master | middle stage top |
| `stage3_w` | 72 | mm | UNVERIFIED | lifter, master | inner cascade stage section |
| `stage3_z0` | 335 | mm | UNVERIFIED | lifter, master | inner stage base |
| `stage3_z1` | 560 | mm | UNVERIFIED | lifter, master | inner stage top |
| `carriage_w` | 120 | mm | UNVERIFIED | lifter, master | carriage plate section |
| `carriage_h` | 40 | mm | UNVERIFIED | lifter, master | carriage plate height |
| `hardstop_h` | 10 | mm | UNVERIFIED | lifter | hard-stop marker height; physical stop required by R105 |
| `guide_w` | 6 | mm | UNVERIFIED | master, lifter | stage guide block section (rides stage walls) |
| `guide_l` | 20 | mm | UNVERIFIED | master, lifter | stage guide block height |
| `lip_h` | 12 | mm | UNVERIFIED | master, lifter | cradle retention lip height |
| `lip_t` | 6 | mm | UNVERIFIED | master, lifter | cradle retention lip thickness |
| `intake_axle_dia` | 12 | mm | UNVERIFIED | master, intake | intake pivot axle through both cheeks |
| `post_w` | 20 | mm | UNVERIFIED | master, shooter | shooter upright post width |
| `lifter_base_w` | 116 | mm | UNVERIFIED | master, lifter | lifter base mounting plate (rehaul sprint-01: clears the channel top corner) |
| `lifter_ped_w` | 80 | mm | UNVERIFIED | master, lifter | lifter pedestal section (pan to mast base; clears front rail + intake axle) |

## Game-element references (context for packaging decisions)

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `field_size` | 3657.6 | mm | VERIFIED | — | §9.2 (Competition Manual TU01) — 144 in field |
| `pollen_dia` | ~71 | mm | VERIFIED | — | §9.8 (Competition Manual TU01) — ~2.8 in ball |
| `nectar_dia` | ~91 | mm | VERIFIED | — | §9.8 (Competition Manual TU01) — ~3.6 in ball |
| `hive_cell_opening_w` | 508 | mm | VERIFIED | — | §9.6 (Competition Manual TU01) — ~20 in wide |
| `hive_cell_opening_h` | 356 | mm | VERIFIED | — | §9.6 (Competition Manual TU01) — ~14 in tall |
| `hive_cell_depth` | 305 | mm | VERIFIED | — | §9.6 (Competition Manual TU01) — ~12 in deep |
| `flower_opening_dia` | 101.5 | mm | VERIFIED | — | §9.7 (Competition Manual TU01) — ~4 in |
| `flower_opening_z` | 546 | mm | VERIFIED | — | §9.7 (Competition Manual TU01) — ~21.5 in high |
| `apriltag_size` | 82.55 | mm | VERIFIED | — | §9.9 (Competition Manual TU01) — 3.25 in |

## Field-target reference markers (master, sprint-04)

`REF_HIVE`/`REF_FLOWER` are aiming references for packaging review — they
mark where the shooter/lifter aim, NOT a field model. Positions are
UNVERIFIED standoffs; the Flower height is the §9.7 verified value.

| Parameter | Value | Unit | Status | Bound in | Source |
|---|---|---|---|---|---|
| `hive_aim_dist` | 800 | mm | UNVERIFIED | master | assumed aim-point standoff past the front face |
| `hive_aim_z` | 300 | mm | UNVERIFIED | master | aim-point height (~launch_z) |
| `ref_size` | 60 | mm | UNVERIFIED | master | marker cube size |
| `flower_aim_x` | 180 | mm | UNVERIFIED | master | flower aim-marker X offset (forward of mast) |
| `flower_aim_z` | 546 | mm | VERIFIED | master | §9.7 flower top height |
| `flower_aim_w` | 60 | mm | UNVERIFIED | master | flower aim-marker width |

## Mass estimate (UNVERIFIED placeholders, sprint-04)

Rough subsystem mass placeholders for sanity-checking the packaging
envelope. Every row is UNVERIFIED — nothing has been weighed; values are
order-of-magnitude guesses, not procurement data.

| Subsystem | Estimated mass (kg) | Basis |
|---|---|---|
| Drivebase chassis + rails | 3.0 | 420×420 frame + 2 side channels, aluminum |
| Wheels + motors (4 each) | 2.6 | 4 × 0.207 kg goBILDA 96 mm mecanum (3213-3606-0002 product page) + 4 × ~0.44 kg Yellow Jacket (5203-series page, e.g. 13.7:1 at 438 g) |
| Battery + electronics | 1.8 | REV-style battery ~1.3 + hubs/wiring ~0.5 |
| Intake | 1.5 | rollers + pivot frame + lip |
| Transfer | 0.8 | channel walls + diverter |
| Shooter | 2.5 | dual flywheel housing + motors |
| Lifter | 2.5 | 3-stage cascade + carriage + cradle |
| **Total** | **14.7** | sum of rows above |

Sanity check: 14.7 kg is within the typical 12–20 kg range FTC teams aim
for — comfortable, but every number here is a placeholder until parts are
purchased and weighed. No rule citation — FTC imposes no robot mass limit;
this is a team-target sanity check only.

Vendor sources cited (sprint-06):

- goBILDA 96 mm mecanum wheel set 3213-3606-0002:
  `https://www.gobilda.com/96mm-mecanum-wheel-set-70a-durometer-bearing-supported-rollers/`
  and its dimension schematic 3606-0000-0096 — Ø96 overall (at roller
  surfaces), 32 mm wide, Ø14 rollers, ~10 rollers at 45° slant, 207 g each.
- goBILDA Yellow Jacket planetary gear motors (5203 series):
  `https://www.gobilda.com/yellow-jacket-planetary-gear-motors` — 36 mm
  gearbox diameter, 8 mm REX output shaft, ~24 mm shaft length; mass varies
  by ratio (e.g. 13.7:1 listed at 438 g).
- goBILDA 1120-series U-channel:
  `https://www.gobilda.com/1120-series-u-channel-1-hole-48mm-length/` —
  48 mm outer face dimension.
- Roller geometry convention: the Ø96 datasheet figure is the wheel outer
  diameter measured at the roller surfaces. Roller placeholders are straight
  cylinders tangent to that envelope (roller mid-surface reaches Ø96; flat
  end caps are kept inside it by limiting `mec_roll_len` to 20 mm). Real
  rollers have barrel ends — not modeled at placeholder fidelity.

Notes:

- Ball diameters are approximate — the manual states the balls are not
  perfectly spherical (§9.8); every ball-path clearance keeps margin over
  the ~91 mm Nectar (throat 120×110, channel 110, bore 100, muzzle 110).
- VENDOR-PENDING rows describe goBILDA-catalog-representative values chosen
  per the settled ecosystem direction (design-decisions.md D7); they become
  VERIFIED only after datasheet review or physical measurement — until then
  nothing vendor-derived is authoritative.
- All UNVERIFIED values are placeholders sized to fit inside the 457.2 mm
  start cube / R105 expansion envelope with margin; none have been measured
  from real parts.
- Axis convention for every model is defined in `docs/coordinate-system.md`;
  build commands are in `docs/setup.md`. Sprint-04 resolved the flagged
  `VOL_*` reserve overlaps (intake↔wheels, transfer↔shooter/lifter) — the
  declared co-locations live in the sprint-04 contract and
  `docs/mechanism-architecture.md`; remaining open questions are in
  `docs/open-questions.md`.
