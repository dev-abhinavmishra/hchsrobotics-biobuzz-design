"""robot_params.py -- shared Parameters sheet for the Sprint-01 overhaul.

One alias table consumed identically by build_drivebase.py,
build_electronics.py and build_master_robot.py, so the three
spreadsheets stay value-consistent by construction (DET3). Every row:
(alias, value, unit, status, source). Status vocabulary per contract:
VERIFIED needs a citation; VENDOR-PENDING is a catalog representative
value pending confirmation; UNVERIFIED is an assumed placeholder.

All values are millimeters in the repository frame: origin = center of
the footprint on the tile, +X forward, +Y left, +Z up, Z=0 = tile top.
"""

PARAMS = [
    # ---- regulatory envelope -------------------------------------------
    ("start_cube", 457.2, "mm", "VERIFIED",
     "FIRST Tech Challenge match start volume 18in cube"),
    # ---- frame -----------------------------------------------------------
    ("chassis_sq", 444.5, "mm", "UNVERIFIED",
     "viewer frame 17.5in square; goBILDA 1120 kit nominal"),
    ("rail_size", 48.0, "mm", "VENDOR-PENDING",
     "goBILDA 1120-series U-channel ~48mm outer section"),
    ("rail_wall", 2.5, "mm", "UNVERIFIED",
     "assumed ~0.09in channel sheet wall; measure on hardware"),
    ("rail_elev_z", 39.75, "mm", "UNVERIFIED",
     "viewer rail center 1.565in off ground"),
    ("wheel_lat_off", 203.2, "mm", "UNVERIFIED",
     "viewer wheel track center 8.0in"),
    ("wheel_out_gap", 43.18, "mm", "UNVERIFIED",
     "rail center to wheel center standoff (wheel_lat_off - rail_lat)"),
    ("rail_lat_off", 160.02, "mm", "UNVERIFIED",
     "rail centerline offset; = wheel_lat_off - wheel_out_gap"),
    ("wheel_lon_off", 127.0, "mm", "UNVERIFIED",
     "viewer wheel longitudinal station 5.0in"),
    ("cross_x_off", 198.12, "mm", "UNVERIFIED",
     "viewer crossmember station 7.8in behind center"),
    ("cross_half_len", 135.89, "mm", "UNVERIFIED",
     "viewer crossmember half-span 5.35in; butts rail inner faces"),
    ("crown_z", 157.48, "mm", "UNVERIFIED",
     "viewer crown center height 6.2in"),
    ("post_top_z", 178.98, "mm", "UNVERIFIED",
     "crown riser tongue top = crown web inner face"),
    ("post_span", 84.13, "mm", "UNVERIFIED",
     "crown riser tongue span: mouth interior to web stand"),
    # ---- wheels / drivetrain ---------------------------------------------
    ("wheel_dia", 96.0, "mm", "VENDOR-PENDING",
     "goBILDA 96mm mecanum set 3213-3606-0002, schematic 3606-0000-0096"),
    ("wheel_width", 38.1, "mm", "VENDOR-PENDING",
     "viewer overall wheel width 1.5in"),
    ("roller_count", 10.0, "count", "VENDOR-PENDING",
     "counted on goBILDA schematic 3606-0000-0096"),
    ("mec_roll_dia", 14.0, "mm", "VENDOR-PENDING",
     "goBILDA schematic O14 roller"),
    ("mec_roll_rad", 41.0, "mm", "VENDOR-PENDING",
     "roller-center radius; envelope radius = rad + len*sin45/2 + "
     "r*cos45 ~ wheel_dia/2"),
    ("mec_roll_len", 24.0, "mm", "UNVERIFIED",
     "assumed roller length; stays inside O96x38 envelope"),
    ("mec_roll_pitch", 36.0, "deg", "VENDOR-PENDING",
     "derived 360 / roller_count"),
    ("mec_roll_phase", 18.0, "deg", "UNVERIFIED",
     "pitch phase: puts a roller dead-bottom (roller at 270 deg)"),
    ("mec_roll_slant", 45.0, "deg", "UNVERIFIED", "mecanum roller slant"),
    ("mec_pin_dia", 5.0, "mm", "UNVERIFIED",
     "roller axle pin dia; tips seat into face plates"),
    ("mec_pin_len", 38.1, "mm", "UNVERIFIED",
     "roller pin overall; tips embed into face plates (declared)"),
    ("wplate_dia", 92.0, "mm", "UNVERIFIED",
     "wheel side plate dia inside O96 envelope"),
    ("wplate_thk", 4.0, "mm", "UNVERIFIED", "wheel side plate thickness"),
    ("wplate_gap", 1.0, "mm", "UNVERIFIED",
     "wheel plate standoff inside the envelope face"),
    ("hub_dia", 26.0, "mm", "UNVERIFIED", "wheel hub OD"),
    ("hub_w", 28.1, "mm", "UNVERIFIED",
     "wheel hub width spanning the plate inner faces"),
    ("hub_hex_af", 8.4, "mm", "UNVERIFIED",
     "hub hex bore across-flats; rides 8mm REX flats +0.4 clearance"),
    ("plate_bore", 10.0, "mm", "UNVERIFIED",
     "wheel plate shaft clearance bore"),
    # ---- live axle stack ---------------------------------------------------
    ("rex_af", 8.0, "mm", "VENDOR-PENDING",
     "goBILDA 8mm REX shaft across-flats, series page"),
    ("rex_crad", 4.62, "mm", "VENDOR-PENDING",
     "REX circumradius = af / (2 cos30); corners O9.24"),
    ("shaft_len", 100.0, "mm", "UNVERIFIED",
     "live axle: socket seat -> outboard tip, viewver stack reconciled"),
    ("shaft_tip_d", 7.4, "mm", "UNVERIFIED",
     "axle outboard tip turned+threaded M8x1.25 for retaining nut"),
    ("shaft_tip_len", 9.2, "mm", "UNVERIFIED",
     "M8 tip: spans out plate bore + washer + nut + margin"),
    ("sock_hex_af", 8.4, "mm", "UNVERIFIED",
     "motor output REX socket across-flats (hex bore)"),
    ("sock_depth", 16.0, "mm", "UNVERIFIED",
     "socket bore depth into gearbox face"),
    ("bear_w", 26.0, "mm", "UNVERIFIED", "bearing block face width"),
    ("bear_h", 26.0, "mm", "UNVERIFIED", "bearing block face height"),
    ("bear_t", 6.0, "mm", "UNVERIFIED", "bearing block thickness"),
    ("bear_bore", 9.6, "mm", "UNVERIFIED",
     "bearing bore, clears REX circumcircle O9.24"),
    ("bear_pilot_d", 15.6, "mm", "UNVERIFIED",
     "bearing pilot OD registers in O16 wall axle hole"),
    ("bear_pilot_l", 2.0, "mm", "UNVERIFIED", "bearing pilot length"),
    ("wall_axle_bore", 16.0, "mm", "UNVERIFIED",
     "rail wall axle clearance bore O16 (clears pilot O15.6)"),
    ("bear_bolt_d", 4.4, "mm", "UNVERIFIED",
     "M4 clearance through bearing flange + wall"),
    ("bear_bolt_off", 9.0, "mm", "UNVERIFIED",
     "bearing bolt square half-spacing"),
    ("rivnut_d", 6.5, "mm", "UNVERIFIED",
     "M4 rivnut seat bore in rail wall; insert OD O6.4"),
    ("collar_d", 18.0, "mm", "UNVERIFIED", "set-screw collar OD"),
    ("collar_w", 5.0, "mm", "UNVERIFIED", "collar width"),
    ("collar_bore", 9.6, "mm", "UNVERIFIED",
     "collar bore clears REX circumcircle O9.24"),
    ("washer_d", 16.0, "mm", "UNVERIFIED", "M8 washer OD"),
    ("washer_t", 1.8, "mm", "UNVERIFIED", "washer thickness"),
    ("washer_bore", 9.6, "mm", "UNVERIFIED",
     "washer bore clears REX circumcircle"),
    ("nut8_wrench", 13.0, "mm", "UNVERIFIED", "M8 nylock across-flats"),
    ("nut8_h", 5.5, "mm", "UNVERIFIED", "retaining nut height"),
    ("nut8_bore", 7.0, "mm", "UNVERIFIED",
     "nut thread core O7.0 on O7.4 tip = modeled thread interference"),
    ("nut6_wrench", 10.0, "mm", "UNVERIFIED", "M6 nut across-flats"),
    ("nut6_h", 5.0, "mm", "UNVERIFIED", "M6 nut height"),
    ("nut6_bore", 5.0, "mm", "UNVERIFIED",
     "M6 nut core O5.0 on O6 pin = modeled thread interference"),
    ("pinion_d", 17.0, "mm", "UNVERIFIED",
     "coupling hub OD riding axle in channel cavity"),
    ("pinion_w", 7.0, "mm", "UNVERIFIED", "coupling hub width"),
    ("pinion_bore", 9.6, "mm", "UNVERIFIED",
     "pinion slip bore clears REX circumcircle"),
    # ---- motors ---------------------------------------------------------
    ("motor_dia", 36.0, "mm", "VENDOR-PENDING",
     "goBILDA 5203-class ~36mm gearbox motor, series page"),
    ("motor_gb_dia", 40.0, "mm", "UNVERIFIED",
     "planetary gearbox housing dia"),
    ("motor_len", 65.0, "mm", "UNVERIFIED", "motor can length"),
    ("motor_gb_l", 30.0, "mm", "UNVERIFIED",
     "gearbox housing length from mount face"),
    ("mplate_len", 304.8, "mm", "UNVERIFIED",
     "motor plate spans both stations + grid margins"),
    ("mplate_h", 48.3, "mm", "UNVERIFIED", "viewer motor plate 1.9in"),
    ("mplate_t", 3.05, "mm", "UNVERIFIED", "viewer motor plate 0.12in"),
    ("mplate_bore", 17.0, "mm", "UNVERIFIED",
     "shaft + bearing-pilot clearance bore through motor plate"),
    ("motor_bolt_d", 4.0, "mm", "UNVERIFIED",
     "M4 motor face bolts (bolt_d), tap drill O3.3"),
    ("motor_bolt_off", 16.0, "mm", "UNVERIFIED",
     "motor face bolt x offset (rect pattern clears bearings)"),
    ("motor_bolt_dz", 4.0, "mm", "UNVERIFIED",
     "motor face bolt z offset"),
    ("tap_drill", 3.3, "mm", "UNVERIFIED", "M4 tap drill dia"),
    ("clamp_w", 12.0, "mm", "UNVERIFIED", "motor clamp width along Y"),
    ("clamp_ear", 14.0, "mm", "UNVERIFIED", "clamp ear reach"),
    ("bolt_d", 4.0, "mm", "UNVERIFIED", "M4 bolt shaft dia"),
    ("bolt_head_d", 7.0, "mm", "UNVERIFIED", "M4 button head dia"),
    ("bolt_head_h", 4.0, "mm", "UNVERIFIED", "M4 button head height"),
    ("bolt_len", 16.0, "mm", "UNVERIFIED", "generic M4 bolt length"),
    ("nut4_wrench", 7.0, "mm", "UNVERIFIED", "M4 nut across-flats"),
    ("nut4_h", 3.2, "mm", "UNVERIFIED", "M4 nut height"),
    ("nut4_bore", 3.6, "mm", "UNVERIFIED",
     "M4 nut core O3.6 on O4 shaft = modeled thread interference"),
    # ---- sheets ---------------------------------------------------------
    ("pan_thk", 2.0, "mm", "UNVERIFIED", "belly pan sheet thickness"),
    ("pan_w", 264.0, "mm", "UNVERIFIED", "viewer pan 10.6in wide"),
    ("pan_len", 333.8, "mm", "UNVERIFIED",
     "pan spans electronics + pods; inside rail inner faces"),
    ("pan_x_c", -6.9, "mm", "UNVERIFIED", "pan center offset"),
    ("pan_z", 26.67, "mm", "UNVERIFIED", "viewer pan center 1.05in"),
    ("pan_fillet", 8.0, "mm", "UNVERIFIED", "pan corner fillet"),
    ("pan_brkt", 40.0, "mm", "UNVERIFIED", "pan bracket leg length"),
    ("grid_hole_d", 4.4, "mm", "VENDOR-PENDING",
     "goBILDA M4 clearance grid hole O4.4"),
    ("grid_pitch", 48.0, "mm", "UNVERIFIED",
     "grid hole row pitch used on walls/web (subset of 8mm grid)"),
    ("deck_z", 85.3, "mm", "UNVERIFIED", "viewer electronics shelf level"),
    ("deck_thk", 3.0, "mm", "UNVERIFIED", "deck panel thickness"),
    ("deck_lane", 66.0, "mm", "UNVERIFIED",
     "hopper lane edge; decks span |Y| in [deck_in_off, rail outer]"),
    ("deck_in_off", 66.0, "mm", "UNVERIFIED", "deck inner edge offset"),
    ("deck_x_lo", -174.0, "mm", "UNVERIFIED", "deck rear extent"),
    ("deck_x_hi", 120.0, "mm", "UNVERIFIED", "deck front extent"),
    ("deck_post_d", 10.0, "mm", "UNVERIFIED", "deck standoff dia"),
    ("shelf_z", 85.3, "mm", "UNVERIFIED",
     "electronics riser shelf center Z in the center lane"),
    ("shelf_thk", 2.0, "mm", "UNVERIFIED", "shelf thickness"),
    ("shelf_x_lo", -172.72, "mm", "UNVERIFIED", "shelf rear edge"),
    ("shelf_x_hi", 86.28, "mm", "UNVERIFIED", "shelf front edge"),
    ("shelf_y_lo", -43.0, "mm", "UNVERIFIED",
     "shelf edge: stays inside the deck flank gap"),
    ("shelf_y_hi", 43.0, "mm", "UNVERIFIED", "shelf edge"),
    ("standoff_d", 8.0, "mm", "UNVERIFIED", "shelf standoff dia"),
    ("so_d", 8.0, "mm", "UNVERIFIED", "standoff dia (shelf risers)"),
    # ---- odometry -------------------------------------------------------
    ("odo_pod_lat", 116.84, "mm", "UNVERIFIED", "viewer pod 4.6in"),
    ("odo_pod_x", 30.48, "mm", "UNVERIFIED", "lateral pods station"),
    ("odo_pod_lon_x", -152.4, "mm", "UNVERIFIED", "rear pod station"),
    ("odo_wheel_d", 48.0, "mm", "VENDOR-PENDING",
     "48mm omni tracking wheel, vendor typical"),
    ("odo_wheel_w", 16.0, "mm", "UNVERIFIED", "odo wheel width"),
    ("odo_arm_len", 30.0, "mm", "UNVERIFIED", "odo arm drop"),
    ("odo_block_h", 12.0, "mm", "UNVERIFIED", "pod mount block height"),
    ("odo_pin_d", 6.0, "mm", "UNVERIFIED", "odo wheel/pivot pin dia"),
    ("odo_spring_d", 8.0, "mm", "UNVERIFIED", "pod preload spring OD"),
    # ---- electronics -----------------------------------------------------
    ("batt_l", 140.0, "mm", "VENDOR-PENDING",
     "REV 3000mAh pack envelope approx"),
    ("batt_w", 70.0, "mm", "UNVERIFIED", "battery width"),
    ("batt_h", 52.0, "mm", "UNVERIFIED",
     "battery height; strap top stays under the deck"),
    ("batt_x", 90.0, "mm", "UNVERIFIED",
     "battery station; pack fully on the pan, clear of hubs"),
    ("batt_y", 40.0, "mm", "UNVERIFIED",
     "battery offset; strap feet stay clear of the clamp notches"),
    ("strap_w", 30.0, "mm", "UNVERIFIED", "battery strap width"),
    ("strap_t", 1.5, "mm", "UNVERIFIED", "strap band thickness"),
    ("strap_foot", 12.0, "mm", "UNVERIFIED", "strap foot tab reach"),
    ("hub_l", 142.0, "mm", "VENDOR-PENDING",
     "REV hub 5.6in long"),
    ("ehub_w", 79.0, "mm", "VENDOR-PENDING", "REV hub 3.1in wide"),
    ("hub_h", 29.0, "mm", "UNVERIFIED", "REV hub 1.15in tall"),
    ("ctrl_x", -54.61, "mm", "UNVERIFIED", "viewer ctrl hub station"),
    ("ctrl_y", 85.0, "mm", "UNVERIFIED", "viewer ctrl hub offset"),
    ("exp_x", -55.0, "mm", "UNVERIFIED", "exp hub mirrored L/R"),
    ("exp_y", 0.0, "mm", "UNVERIFIED", "exp hub offset"),
    ("sw_x", -158.0, "mm", "UNVERIFIED", "main switch station"),
    ("sw_y", -80.0, "mm", "UNVERIFIED", "main switch offset"),
    ("sw_l", 15.0, "mm", "UNVERIFIED", "switch body length"),
    ("sw_h", 13.0, "mm", "UNVERIFIED", "switch body height"),
    ("sw_w", 9.0, "mm", "UNVERIFIED", "switch body width"),
    ("wire_d", 3.0, "mm", "UNVERIFIED", "wire bundle dia"),
    ("plate_num_w", 91.0, "mm", "UNVERIFIED", "number plate width"),
    ("plate_num_h", 61.0, "mm", "UNVERIFIED", "number plate height"),
    ("plate_num_t", 2.0, "mm", "UNVERIFIED", "number plate thickness"),
    ("endcap_t", 3.0, "mm", "UNVERIFIED", "channel end cap face"),
    ("gusset_leg", 35.0, "mm", "UNVERIFIED", "corner gusset leg"),
    ("gusset_t", 6.0, "mm", "UNVERIFIED", "corner gusset thickness"),
]


# contract sec.5 derived aliases - formula cells, not new inputs
DERIVED = [
    ("rail_len", "chassis_sq", "UNVERIFIED",
     "alias: rail length"),
    ("axle_len", "shaft_len", "UNVERIFIED",
     "alias: live axle length"),
    ("rex_bore", "bear_bore", "VENDOR-PENDING",
     "alias: 9.6mm REX clearance bore"),
    ("brg_in_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 + rail_wall",
     "UNVERIFIED", "alias: inner bearing face offset"),
    ("brg_out_off",
     "wheel_lat_off - wheel_out_gap + rail_size / 2 - rail_wall",
     "UNVERIFIED", "alias: outer bearing face offset"),
    ("motor_lat_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 - mplate_t - "
     "motor_gb_l - motor_len / 2",
     "UNVERIFIED", "alias: motor can center offset"),
    ("mount_plate_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 - mplate_t / 2",
     "UNVERIFIED", "alias: mount plate center offset"),
    ("collar_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 + rail_wall + "
     "bear_t + washer_t + collar_w / 2",
     "UNVERIFIED", "alias: shaft collar center offset"),
    ("washer_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 + rail_wall + "
     "bear_t + washer_t / 2",
     "UNVERIFIED", "alias: shaft washer center offset"),
    ("pinion_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 + rail_wall + "
     "bear_t + washer_t + collar_w + 1 + pinion_w / 2",
     "UNVERIFIED", "alias: pinion/coupler center offset"),
    ("nut_off",
     "wheel_lat_off + wheel_width / 2 - wplate_gap + washer_t + "
     "nut8_h / 2",
     "UNVERIFIED", "alias: nylock center offset"),
    ("clamp1_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 - mplate_t - "
     "clamp_w / 2",
     "UNVERIFIED", "alias: inner clamp center offset"),
    ("clamp2_off",
     "wheel_lat_off - wheel_out_gap - rail_size / 2 - mplate_t - "
     "clamp_w - 18 - clamp_w / 2",
     "UNVERIFIED", "alias: outer clamp center offset"),
]


def populate_sheet(doc):
    """Create + fill the Parameters spreadsheet. Returns the sheet."""
    import Spreadsheet  # noqa: F401
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.Label = "Parameters"
    for col, head in zip("ABCDE",
                         ("alias", "value", "unit", "status", "source")):
        sheet.set(col + "1", head)
    for i, (alias, val, unit, status, src) in enumerate(PARAMS):
        r = str(i + 2)
        sheet.set("A" + r, alias)
        sheet.set("B" + r, repr(val))
        sheet.set("C" + r, unit)
        sheet.set("D" + r, status)
        sheet.set("E" + r, src)
        sheet.setAlias("B" + r, alias)
    r0 = len(PARAMS) + 2
    for j, (alias, expr, status, src_) in enumerate(DERIVED):
        r = str(r0 + j)
        sheet.set("A" + r, alias)
        sheet.set("B" + r, "=" + expr)
        sheet.set("C" + r, "mm")
        sheet.set("D" + r, status)
        sheet.set("E" + r, src_)
        sheet.setAlias("B" + r, alias)
    return sheet
