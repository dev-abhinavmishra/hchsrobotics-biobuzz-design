# Robot parameters -- BIOBUZZ-Robot

Canonical parameter table for the BIOBUZZ CAD foundation. The `Parameters`
spreadsheet inside each FCStd binds geometry to the alias names below; this
file is the human-readable source of truth for what each value means and how
much to trust it. The same table is exported to `exports/parameters.csv`
by `export_step.py`.

**Status enum:** `VERIFIED` = cited to the Competition Manual (TU01) ->
`UNVERIFIED` = assumed placeholder -> `VENDOR-PENDING` = goBILDA-catalog
representative value, pending purchase/datasheet confirmation (never
presented as VERIFIED). Aliases are shared across files where they name the
same quantity.

**Machine-readable summary:** 159 aliases (145 inputs + 14 derived formula rows) -- 1 VERIFIED, 10
VENDOR-PENDING, 134 UNVERIFIED. Bound expressions on every exportable
solid reference these aliases via `Parameters.<alias>`; the PAR1/PAR3
selfcheck gates fail if an alias is missing or a parametric feature is
left unbound.

**Envelope margin (UNVERIFIED inspection risk):** the frame footprint is
444.5 mm square; enumerated fastener classes (axle nylocks, plate bolt
heads/nuts, crown pin hardware, the alliance number plate itself)
protrude past it -- total model span is 453.7 x 454.5 mm, ~2.7 mm
clear of the 457.2 mm start cube (contract amendment A1 requires
>=1 mm per side, prefers >=2 mm). The axle-nut stack is the binding
surface: if the vendor M8 nylock is taller than the modeled 5.0 mm, or
the wheel plates sit outboard of wheel_width/2, the margin erodes.
Check the as-built shaft tip and nut height before competition.

## Envelope

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| start_cube | 457.2 | mm | VERIFIED | FIRST Tech Challenge match start volume 18in cube |

## Frame

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| chassis_sq | 444.5 | mm | UNVERIFIED | viewer frame 17.5in square; goBILDA 1120 kit nominal |
| rail_size | 48.0 | mm | VENDOR-PENDING | goBILDA 1120-series U-channel ~48mm outer section |
| rail_wall | 2.5 | mm | UNVERIFIED | assumed ~0.09in channel sheet wall; measure on hardware |
| rail_elev_z | 39.75 | mm | UNVERIFIED | viewer rail center 1.565in off ground |
| rail_lat_off | 160.02 | mm | UNVERIFIED | rail centerline offset; = wheel_lat_off - wheel_out_gap |
| cross_x_off | 198.12 | mm | UNVERIFIED | viewer crossmember station 7.8in behind center |
| cross_half_len | 136.02 | mm | UNVERIFIED | viewer crossmember half-span 5.35in; butts rail inner faces |
| crown_z | 157.48 | mm | UNVERIFIED | viewer crown center height 6.2in |
| post_top_z | 178.98 | mm | UNVERIFIED | crown riser tongue top = crown web inner face |
| post_span | 84.13 | mm | UNVERIFIED | crown riser tongue span: mouth interior to web stand |
| grid_hole_d | 4.4 | mm | VENDOR-PENDING | goBILDA M4 clearance grid hole O4.4 |
| grid_pitch | 48.0 | mm | UNVERIFIED | grid hole row pitch used on walls/web (subset of 8mm grid) |
| endcap_t | 3.0 | mm | UNVERIFIED | channel end cap face |
| gusset_leg | 35.0 | mm | UNVERIFIED | corner gusset leg |
| gusset_t | 6.0 | mm | UNVERIFIED | corner gusset thickness |
| plate_num_w | 91.0 | mm | UNVERIFIED | number plate width |
| plate_num_h | 61.0 | mm | UNVERIFIED | number plate height |
| plate_num_t | 2.0 | mm | UNVERIFIED | number plate thickness |

## Wheels + drivetrain

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| wheel_lat_off | 203.2 | mm | UNVERIFIED | viewer wheel track center 8.0in |
| wheel_out_gap | 43.18 | mm | UNVERIFIED | rail center to wheel center standoff (wheel_lat_off - rail_lat) |
| wheel_lon_off | 127.0 | mm | UNVERIFIED | viewer wheel longitudinal station 5.0in |
| wheel_dia | 96.0 | mm | VENDOR-PENDING | goBILDA 96mm mecanum set 3213-3606-0002, schematic 3606-0000-0096 |
| wheel_width | 38.1 | mm | VENDOR-PENDING | viewer overall wheel width 1.5in |
| roller_count | 10.0 | count | VENDOR-PENDING | counted on goBILDA schematic 3606-0000-0096 |
| mec_roll_dia | 14.0 | mm | VENDOR-PENDING | goBILDA schematic O14 roller |
| mec_roll_rad | 41.0 | mm | VENDOR-PENDING | roller-center radius; envelope radius = rad + len*sin45/2 + r*cos45 ~ wheel_dia/2 |
| mec_roll_len | 24.0 | mm | UNVERIFIED | assumed roller length; stays inside O96x38 envelope |
| mec_roll_pitch | 36.0 | deg | VENDOR-PENDING | derived 360 / roller_count |
| mec_roll_phase | 18.0 | deg | UNVERIFIED | pitch phase: puts a roller dead-bottom (roller at 270 deg) |
| mec_roll_slant | 45.0 | deg | UNVERIFIED | mecanum roller slant |
| mec_pin_dia | 5.0 | mm | UNVERIFIED | roller axle pin dia; tips seat into face plates |
| mec_pin_len | 38.1 | mm | UNVERIFIED | roller pin overall; tips embed into face plates (declared) |
| wplate_dia | 92.0 | mm | UNVERIFIED | wheel side plate dia inside O96 envelope |
| wplate_thk | 4.0 | mm | UNVERIFIED | wheel side plate thickness |
| wplate_gap | 1.0 | mm | UNVERIFIED | wheel plate standoff inside the envelope face |
| hub_dia | 26.0 | mm | UNVERIFIED | wheel hub OD |
| hub_w | 30.1 | mm | UNVERIFIED | wheel hub width spanning the plate inner faces |
| hub_hex_af | 8.4 | mm | UNVERIFIED | hub hex bore across-flats; rides 8mm REX flats +0.4 clearance |
| plate_bore | 10.0 | mm | UNVERIFIED | wheel plate shaft clearance bore |
| rex_af | 8.0 | mm | VENDOR-PENDING | goBILDA 8mm REX shaft across-flats, series page |
| rex_crad | 4.62 | mm | VENDOR-PENDING | REX circumradius = af / (2 cos30); corners O9.24 |
| shaft_len | 100.0 | mm | UNVERIFIED | live axle: socket seat -> outboard tip, viewver stack reconciled |
| shaft_tip_d | 7.4 | mm | UNVERIFIED | axle outboard tip turned+threaded M8x1.25 for retaining nut |
| shaft_tip_len | 9.2 | mm | UNVERIFIED | M8 tip: spans out plate bore + nut + margin |
| sock_hex_af | 8.4 | mm | UNVERIFIED | motor output REX socket across-flats (hex bore) |
| sock_depth | 16.0 | mm | UNVERIFIED | socket bore depth into gearbox face |

## Bearings + retention

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| bear_w | 26.0 | mm | UNVERIFIED | bearing block face width |
| bear_h | 26.0 | mm | UNVERIFIED | bearing block face height |
| bear_t | 6.0 | mm | UNVERIFIED | bearing block thickness |
| bear_bore | 9.6 | mm | UNVERIFIED | bearing bore, clears REX circumcircle O9.24 |
| bear_pilot_d | 15.6 | mm | UNVERIFIED | bearing pilot OD registers in O16 wall axle hole |
| bear_pilot_l | 2.0 | mm | UNVERIFIED | bearing pilot length |
| wall_axle_bore | 16.0 | mm | UNVERIFIED | rail wall axle clearance bore O16 (clears pilot O15.6) |
| bear_bolt_d | 4.4 | mm | UNVERIFIED | M4 clearance through bearing flange + wall |
| bear_bolt_off | 9.0 | mm | UNVERIFIED | bearing bolt square half-spacing |
| rivnut_d | 6.5 | mm | UNVERIFIED | M4 rivnut seat bore in rail wall; insert OD O6.4 |
| collar_d | 18.0 | mm | UNVERIFIED | set-screw collar OD |
| collar_w | 5.0 | mm | UNVERIFIED | collar width |
| collar_bore | 9.6 | mm | UNVERIFIED | collar bore clears REX circumcircle O9.24 |
| washer_d | 16.0 | mm | UNVERIFIED | M8 washer OD |
| washer_t | 1.8 | mm | UNVERIFIED | washer thickness |
| washer_bore | 9.6 | mm | UNVERIFIED | washer bore clears REX circumcircle |
| nut8_wrench | 13.0 | mm | UNVERIFIED | M8 nylock across-flats |
| nut8_h | 5.0 | mm | UNVERIFIED | thin M8 nylock retaining nut height |
| nut8_bore | 7.0 | mm | UNVERIFIED | nut thread core O7.0 on O7.4 tip = modeled thread interference |
| nut6_wrench | 10.0 | mm | UNVERIFIED | M6 nut across-flats |
| nut6_h | 5.0 | mm | UNVERIFIED | M6 nut height |
| nut6_bore | 5.0 | mm | UNVERIFIED | M6 nut core O5.0 on O6 pin = modeled thread interference |
| pinion_d | 17.0 | mm | UNVERIFIED | coupling hub OD riding axle in channel cavity |
| pinion_w | 7.0 | mm | UNVERIFIED | coupling hub width |
| pinion_bore | 9.6 | mm | UNVERIFIED | pinion slip bore clears REX circumcircle |

## Motors + mounting

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| motor_dia | 36.0 | mm | VENDOR-PENDING | goBILDA 5203-class ~36mm gearbox motor, series page |
| motor_gb_dia | 40.0 | mm | UNVERIFIED | planetary gearbox housing dia |
| motor_len | 65.0 | mm | UNVERIFIED | motor can length |
| motor_gb_l | 30.0 | mm | UNVERIFIED | gearbox housing length from mount face |
| mplate_len | 304.8 | mm | UNVERIFIED | motor plate spans both stations + grid margins |
| mplate_h | 48.3 | mm | UNVERIFIED | viewer motor plate 1.9in |
| mplate_t | 3.05 | mm | UNVERIFIED | viewer motor plate 0.12in |
| mplate_bore | 17.0 | mm | UNVERIFIED | shaft + bearing-pilot clearance bore through motor plate |
| motor_bolt_d | 4.0 | mm | UNVERIFIED | M4 motor face bolts (bolt_d), tap drill O3.3 |
| motor_bolt_off | 16.0 | mm | UNVERIFIED | motor face bolt x offset (rect pattern clears bearings) |
| motor_bolt_dz | 4.0 | mm | UNVERIFIED | motor face bolt z offset |
| tap_drill | 3.3 | mm | UNVERIFIED | M4 tap drill dia |
| clamp_w | 12.0 | mm | UNVERIFIED | motor clamp width along Y |
| clamp_ear | 14.0 | mm | UNVERIFIED | clamp ear reach |

## Fasteners

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| bolt_d | 4.0 | mm | UNVERIFIED | M4 bolt shaft dia |
| bolt_head_d | 7.0 | mm | UNVERIFIED | M4 button head dia |
| bolt_head_h | 4.0 | mm | UNVERIFIED | M4 button head height |
| bolt_len | 16.0 | mm | UNVERIFIED | generic M4 bolt length |
| nut4_wrench | 7.0 | mm | UNVERIFIED | M4 nut across-flats |
| nut4_h | 3.2 | mm | UNVERIFIED | M4 nut height |
| nut4_bore | 3.6 | mm | UNVERIFIED | M4 nut core O3.6 on O4 shaft = modeled thread interference |

## Belly pan + deck

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| pan_thk | 2.0 | mm | UNVERIFIED | belly pan sheet thickness |
| pan_w | 264.0 | mm | UNVERIFIED | viewer pan 10.6in wide |
| pan_len | 333.8 | mm | UNVERIFIED | pan spans electronics + pods; inside rail inner faces |
| pan_x_c | -6.9 | mm | UNVERIFIED | pan center offset |
| pan_z | 26.67 | mm | UNVERIFIED | viewer pan center 1.05in |
| pan_fillet | 8.0 | mm | UNVERIFIED | pan corner fillet |
| pan_brkt | 40.0 | mm | UNVERIFIED | pan bracket leg length |
| deck_z | 85.3 | mm | UNVERIFIED | viewer electronics shelf level |
| deck_thk | 3.0 | mm | UNVERIFIED | deck panel thickness |
| deck_lane | 66.0 | mm | UNVERIFIED | hopper lane edge; decks span |Y| in [deck_in_off, rail outer] |
| deck_in_off | 66.0 | mm | UNVERIFIED | deck inner edge offset |
| deck_x_lo | -174.0 | mm | UNVERIFIED | deck rear extent |
| deck_x_hi | 120.0 | mm | UNVERIFIED | deck front extent |
| deck_post_d | 10.0 | mm | UNVERIFIED | deck standoff dia |

## Odometry pods

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| odo_pod_lat | 116.84 | mm | UNVERIFIED | viewer pod 4.6in |
| odo_pod_x | 30.48 | mm | UNVERIFIED | lateral pods station |
| odo_pod_lon_x | -152.4 | mm | UNVERIFIED | rear pod station |
| odo_wheel_d | 48.0 | mm | VENDOR-PENDING | 48mm omni tracking wheel, vendor typical |
| odo_wheel_w | 16.0 | mm | UNVERIFIED | odo wheel width |
| odo_arm_len | 30.0 | mm | UNVERIFIED | odo arm drop |
| odo_block_h | 12.0 | mm | UNVERIFIED | pod mount block height |
| odo_pin_d | 6.0 | mm | UNVERIFIED | odo wheel/pivot pin dia |
| odo_spring_d | 8.0 | mm | UNVERIFIED | pod preload spring OD |

## Electronics

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| shelf_z | 85.3 | mm | UNVERIFIED | electronics riser shelf center Z in the center lane |
| shelf_thk | 2.0 | mm | UNVERIFIED | shelf thickness |
| shelf_x_lo | -172.72 | mm | UNVERIFIED | shelf rear edge |
| shelf_x_hi | 86.28 | mm | UNVERIFIED | shelf front edge |
| shelf_y_lo | -49.0 | mm | UNVERIFIED | shelf edge: stays inside the deck flank gap |
| shelf_y_hi | 49.0 | mm | UNVERIFIED | shelf edge |
| standoff_d | 8.0 | mm | UNVERIFIED | shelf standoff dia |
| so_d | 8.0 | mm | UNVERIFIED | standoff dia (shelf risers) |
| batt_l | 95.0 | mm | VENDOR-PENDING | REV 3000mAh pack envelope approx |
| batt_w | 65.0 | mm | UNVERIFIED | battery width |
| batt_h | 40.0 | mm | UNVERIFIED | battery height; strap top stays under the deck |
| batt_x | 65.0 | mm | UNVERIFIED | battery station; pack fully on the pan, clear of hubs |
| batt_y | 0.0 | mm | UNVERIFIED | battery offset; strap feet stay clear of the clamp notches |
| strap_w | 30.0 | mm | UNVERIFIED | battery strap width |
| strap_t | 1.5 | mm | UNVERIFIED | strap band thickness |
| strap_foot | 12.0 | mm | UNVERIFIED | strap foot tab reach |
| hub_l | 142.0 | mm | VENDOR-PENDING | REV hub 5.6in long |
| ehub_w | 79.0 | mm | VENDOR-PENDING | REV hub 3.1in wide |
| hub_h | 29.0 | mm | UNVERIFIED | REV hub 1.15in tall |
| ctrl_x | -48.5 | mm | UNVERIFIED | viewer ctrl hub station |
| ctrl_y | 0.0 | mm | UNVERIFIED | viewer ctrl hub offset |
| exp_x | -75.0 | mm | UNVERIFIED | exp hub mirrored L/R |
| exp_y | 0.0 | mm | UNVERIFIED | exp hub offset |
| sw_x | -115.0 | mm | UNVERIFIED | main switch station |
| sw_y | 0.0 | mm | UNVERIFIED | main switch offset |
| sw_l | 15.0 | mm | UNVERIFIED | switch body length |
| sw_h | 13.0 | mm | UNVERIFIED | switch body height |
| sw_w | 9.0 | mm | UNVERIFIED | switch body width |
| wire_d | 3.0 | mm | UNVERIFIED | wire bundle dia |

## Sprint-02: intake + hopper/feed path

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| intake_x | 190.0 | mm | UNVERIFIED | intake mouth station (viewer front edge) |
| roller_low_z | 36.8 | mm | UNVERIFIED | lower roller center height |
| roller_low_r | 25.4 | mm | UNVERIFIED | ribbed traction roller radius (Ø50.8) |
| roller_len | 255.0 | mm | UNVERIFIED | full-width roller span |
| roller_top_x | 133.0 | mm | UNVERIFIED | star roller x (corrected: viewer gave -10mm nip gap) |
| roller_top_z | 175.0 | mm | UNVERIFIED | star roller center height |
| roller_top_r | 39.35 | mm | UNVERIFIED | star roller outer radius (Ø78.7) |
| star_core_r | 22.0 | mm | UNVERIFIED | star roller core radius |
| float_travel | 17.8 | mm | UNVERIFIED | sprung float travel; opens nip >=91 for NECTAR |
| cheek_lat_off | 130.5 | mm | UNVERIFIED | cheek plate offset: flush on rail inner face |
| cheek_thk | 5.0 | mm | UNVERIFIED | cheek plate thickness |
| sprocket_plane | 164.0 | mm | UNVERIFIED | chain run plane (right rail channel) |
| belt_plane | 155.0 | mm | UNVERIFIED | crossed belt plane (left cheek) |
| sprocket9_pd | 18.6 | mm | VENDOR-PENDING | 9T #25 sprocket pitch dia |
| sprocket16_pd | 32.6 | mm | VENDOR-PENDING | 16T #25 sprocket pitch dia |
| belt_pul_d | 40.0 | mm | UNVERIFIED | crossed-belt pulley dia |
| spring_post_d | 8.0 | mm | UNVERIFIED | spring post dia; coils wound snug (coil_r 5.5) |
| int_motor_x | 76.0 | mm | UNVERIFIED | intake motor station |
| int_motor_z | 43.0 | mm | UNVERIFIED | intake motor axis height (right rail channel) |
| int_motor_lat | 101.6 | mm | UNVERIFIED | intake motor lateral offset |
| lane_wid | 114.0 | mm | UNVERIFIED | hopper lane width (curb + scoop widths derive) |
| hop_wall_y | 60.0 | mm | UNVERIFIED | hopper wall offset |
| hopper_incline | 20.0 | deg | UNVERIFIED | magazine floor incline toward feed corner |
| hop_wall_x0 | -73.0 | mm | UNVERIFIED | wall rear edge |
| hop_wall_x1 | 92.0 | mm | UNVERIFIED | wall front edge |
| hop_curb_x | -70.0 | mm | UNVERIFIED | rear curb station under column mouth |
| feed_x | -36.8 | mm | UNVERIFIED | feed wheel center x |
| feed_z | 130.8 | mm | UNVERIFIED | feed wheel center height |
| feed_wheel_r | 40.65 | mm | UNVERIFIED | metering wheel radius |
| feed_wheel_w | 40.0 | mm | UNVERIFIED | metering wheel width |
| feed_motor_z | 71.1 | mm | UNVERIFIED | feed motor height under incline |
| feed_motor_lat | 104.0 | mm | UNVERIFIED | feed motor lateral offset |
| feed_gear_d | 59.8 | mm | UNVERIFIED | 1:1 spur pitch dia |
| column_x | -66.0 | mm | UNVERIFIED | feed column axis (future turret axis) |
| column_id | 104.0 | mm | UNVERIFIED | column bore, ~4in clear |
| column_od | 110.0 | mm | UNVERIFIED | column shell OD |
| column_z0 | 88.0 | mm | UNVERIFIED | column bottom (flange seat) |
| column_z1 | 254.0 | mm | UNVERIFIED | column top (deck interface below) |
| col_flange_z | 90.0 | mm | UNVERIFIED | base flange center |
| col_post_off | 55.0 | mm | UNVERIFIED | flange post offset along x |
| col_post_lat | 76.0 | mm | UNVERIFIED | flange post lateral offset |
| gate_y | 73.7 | mm | UNVERIFIED | gate servo offset magnitude (right/-Y wall; moved off the +Y port corridor) |
| gate_z | 174.0 | mm | UNVERIFIED | gate servo height / flag sweep station |
| div_z | 204.0 | mm | UNVERIFIED | diverter port center on the +Y column wall |
| div_port_d | 100.0 | mm | UNVERIFIED | port flange bore dia; >=93 + sphere margin for NECTAR |
| agit_x | 66.0 | mm | UNVERIFIED | agitator servo station |
| agit_y | -73.7 | mm | UNVERIFIED | agitator offset on the right wall |
| agit_z | 115.6 | mm | UNVERIFIED | agitator servo height |
| snsr_x | 96.0 | mm | UNVERIFIED | entry color sensor station |
| snsr_y | -58.0 | mm | UNVERIFIED | sensor offset at hopper entry |
| snsr_z | 86.0 | mm | UNVERIFIED | sensor height at hopper entry |
| ball_p_dia | 71.0 | mm | VERIFIED | POLLEN game-piece diameter |
| ball_n_dia | 91.0 | mm | VERIFIED | NECTAR game-piece diameter |
| ball_clear | 2.0 | mm | UNVERIFIED | ball-to-wall clearance margin (apertures sized ball_n_dia + margin >=93 clear) |

## Sprint-03: turret + launcher + flower lift

| Alias | Value | Unit | Status | Meaning |
|---|---|---|---|---|
| tower_lat_off | 130.8 | mm | UNVERIFIED | tower riser plate center offset (viewer 5.15in) |
| tower_thk | 3.0 | mm | UNVERIFIED | polycarb tower riser sheet |
| tower_x0 | -176.0 | mm | UNVERIFIED | tower riser rear edge |
| tower_x1 | 0.0 | mm | UNVERIFIED | tower riser front edge |
| tower_z1 | 244.0 | mm | UNVERIFIED | tower top edge = turret deck underside |
| turret_deck_z0 | 244.0 | mm | UNVERIFIED | turret deck plate bottom |
| turret_deck_t | 4.0 | mm | UNVERIFIED | PETG turret deck sheet |
| deck_bore_d | 114.0 | mm | UNVERIFIED | deck/plate center bore, clears column_od 110 +4 |
| yaw_off | 72.8 | mm | UNVERIFIED | yaw pinion center distance = (ring_pd + pinion_pd)/2 external mesh |
| susan_d | 132.0 | mm | VENDOR-PENDING | lazy-susan race OD 5.2in nominal |
| susan_bore_d | 116.0 | mm | UNVERIFIED | susan center opening (clears column_od 110) |
| susan_race_h | 4.25 | mm | UNVERIFIED | one race height; pair stacks 8.5 (z248-256.5) |
| ring_pd | 121.9 | mm | VENDOR-PENDING | 72T ring gear pitch dia, external teeth |
| ring_od | 128.8 | mm | UNVERIFIED | ring gear outer tip dia |
| pinion_pd | 23.7 | mm | VENDOR-PENDING | 14T brass yaw pinion pitch dia |
| pinion_od | 27.8 | mm | UNVERIFIED | pinion tip dia |
| yaw_shaft_d | 8.0 | mm | UNVERIFIED | yaw pinion REX shaft |
| plate_od | 170.0 | mm | UNVERIFIED | rotating turret plate dia (viewer 6.7in) |
| plate_z | 265.0 | mm | UNVERIFIED | rotating plate center z (plate z263-267) |
| plate_t | 4.0 | mm | UNVERIFIED | acetal turret plate |
| cheek_lat | 66.5 | mm | UNVERIFIED | launcher cheek plate offset |
| fly_axis_x | -80.0 | mm | UNVERIFIED | flywheel axis station (viewer -3.15in rel axis) |
| fly_axis_z | 308.5 | mm | UNVERIFIED | flywheel axis height — raised 292->308.5: wheels at 292 interpenetrated column top/susan/ring; 308.5 clears the static stack |
| fly_d | 88.9 | mm | VENDOR-PENDING | flywheel OD 3.5in compliant |
| fly_w | 18.3 | mm | UNVERIFIED | flywheel face width |
| fly_motor_d | 36.0 | mm | VENDOR-PENDING | 5203-class motor can dia |
| nip_gap | 73.7 | mm | UNVERIFIED | flywheel face gap -> ~19% NECTAR compression |
| hood_piv_x | -100.3 | mm | UNVERIFIED | hood pivot station |
| hood_piv_z | 359.0 | mm | UNVERIFIED | hood pivot height — viewer z321 sat inside the wheel disc; 359 clears wheel top 352.95 |
| hood_piv_d | 8.0 | mm | UNVERIFIED | hood pivot axle dia |
| cam_x | -8.0 | mm | UNVERIFIED | vision camera station on the plate rim |
| cam_z | 286.0 | mm | UNVERIFIED | camera body height |
| magnet_r | 78.7 | mm | UNVERIFIED | yaw index magnet radius on plate rim |
| lift_x | -185.4 | mm | UNVERIFIED | mast center station on the left rail |
| lift_y0 | 144.0 | mm | UNVERIFIED | inner guide rail offset (corrected onto rail flange) |
| lift_y1 | 180.0 | mm | UNVERIFIED | outer guide rail offset |
| lift_z0 | 63.8 | mm | UNVERIFIED | mast base z = rail top flange face |
| lift_rail_len | 269.0 | mm | UNVERIFIED | fixed slide-rail length — z64..333 |
| slide_sec | 14.0 | mm | UNVERIFIED | slide extrusion section |
| s1_len | 239.0 | mm | UNVERIFIED | stage-1 slide bar length |
| s2_len | 218.0 | mm | UNVERIFIED | stage-2 slide bar length |
| mast_top_z | 330.0 | mm | UNVERIFIED | mast top tie z (as-built ~334 with tie block) |
| stop_z | 326.0 | mm | UNVERIFIED | hard-stop collar z — caps stage-1 inside R105 |
| cradle_x | -127.0 | mm | UNVERIFIED | cradle pivot station (viewer 5.0in fwd of mast) |
| cradle_y | 178.0 | mm | UNVERIFIED | cradle pivot offset |
| cradle_z | 140.0 | mm | UNVERIFIED | cradle bowl park height (FC3 drop) |
| cradle_id | 99.0 | mm | UNVERIFIED | cradle cup bore — D91 + 2x3 foam + clearance |
| deploy_z | 566.0 | mm | UNVERIFIED | deployed cradle rim height inside R105 736.5 |
| rope_d | 1.5 | mm | UNVERIFIED | dyneema lift line |
| winch_z | 50.8 | mm | UNVERIFIED | winch servo height |
| chute_w | 97.0 | mm | UNVERIFIED | load-chute tray inner width (D93 + margin) |
