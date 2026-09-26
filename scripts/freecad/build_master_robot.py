"""Build cad/master_robot.FCStd -- BIOBUZZ robot (rehaul sprint-01).

Chassis + drivetrain are component-fidelity feature DAGs built through
scripts/freecad/partkit.py: U-channel frame with hole rows and shaft
notches, filleted belly pan / rear deck, mecanum wheel assemblies
(hub + bored+chamfered face plates + slanted rollers on pins), 5203
motors with face plates, flange bearing blocks, and REX live shafts.
Mechanism volumes stay placeholder-grade pending sprints 02-04; every
solid still reaches the frame (mount-chain rule).

Run:  freecadcmd.exe scripts/freecad/build_master_robot.py
All paths resolve relative to this file (project_root/scripts/freecad/).
"""

import math
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401  registers Part::Box / Part::Cylinder
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
import partkit as pk  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = ROOT / "cad"
ARCHIVE_DIR = CAD_DIR / "archive"
TARGET = CAD_DIR / "master_robot.FCStd"
DOC_NAME = "master_robot"

# wheel corner table: (tag, sx, sy, slant-sgn). X-pattern = diagonal
# pairing: FL+RR one handedness, FR+RL the other -> sgn = sx*sy.
WHEELS = (("FL", 1, 1, 1), ("FR", 1, -1, -1), ("RL", -1, 1, -1),
          ("RR", -1, -1, 1))

# (alias, value, unit, status, source)
PARAMS = [
    ("start_cube", 457.2, "mm", "VERIFIED", "R102 TU01"),
    ("expansion_width", 457.2, "mm", "VERIFIED", "R105 TU01"),
    ("expansion_depth", 609.6, "mm", "VERIFIED", "R105 TU01"),
    ("expansion_height", 736.5, "mm", "VERIFIED", "R105 TU01"),
    ("chassis_length", 420.0, "mm", "UNVERIFIED", "assumed packaging"),
    ("chassis_width", 420.0, "mm", "UNVERIFIED", "assumed packaging"),
    ("chassis_height", 120.0, "mm", "UNVERIFIED", "assumed packaging"),
    ("wheel_dia", 96.0, "mm", "VENDOR-PENDING",
     "goBILDA 96mm mecanum 3213-3606-0002, schematic 3606-0000-0096"),
    ("wheel_width", 32.0, "mm", "VENDOR-PENDING",
     "goBILDA schematic 3606-0000-0096 overall width (was 25 placeholder)"),
    ("wheel_x_offset", 140.0, "mm", "UNVERIFIED",
     "assumed; keeps motor bodies clear of the end rails"),
    ("wheel_y_offset", 180.0, "mm", "UNVERIFIED",
     "assumed; roller OD leaves 0.6mm margin to R102 cube"),
    ("battery_l", 180.0, "mm", "UNVERIFIED", "assumed"),
    ("battery_w", 55.0, "mm", "UNVERIFIED",
     "assumed slim pack, fits bay between channel and rail web"),
    ("battery_h", 35.0, "mm", "UNVERIFIED",
     "assumed slim pack; clears the rear deck underside"),
    ("bat_x", -110.0, "mm", "UNVERIFIED",
     "-Y bay; forward of the rear motor corridor"),
    ("bat_y", -113.0, "mm", "UNVERIFIED",
     "-Y bay between channel wall and side-rail web"),
    ("bat_z", 5.5, "mm", "UNVERIFIED",
     "sits on belly pan top (rail_wall + pan_thk)"),
    ("elec_l", 160.0, "mm", "UNVERIFIED", "assumed"),
    ("elec_w", 55.0, "mm", "UNVERIFIED",
     "assumed slim stack, fits bay between channel and rail web"),
    ("elec_h", 28.0, "mm", "UNVERIFIED",
     "assumed slim stack; clears the rear deck underside"),
    ("elec_x", -120.0, "mm", "UNVERIFIED", "belly mount, clear of wheels/channel"),
    ("elec_y", 60.0, "mm", "UNVERIFIED", "+Y side, clear of channel"),
    ("elec_z", 11.5, "mm", "UNVERIFIED",
     "on electronics rails (rail_wall + pan_thk + erail_h)"),
    ("axis_len", 120.0, "mm", "UNVERIFIED", "reference marker"),
    ("axis_thk", 4.0, "mm", "UNVERIFIED", "reference marker"),
    # sprint-02 mechanism packaging volumes (shared values with concept files)
    ("intake_depth", 160.0, "mm", "UNVERIFIED", "assumed intake reserve"),
    ("intake_width", 326.0, "mm", "UNVERIFIED",
     "fits between wheel inner faces (+-164 with datasheet 32mm wheels)"),
    ("intake_height", 120.0, "mm", "UNVERIFIED", "assumed intake reserve"),
    ("channel_w", 110.0, "mm", "UNVERIFIED", "clears 91mm ball + margin"),
    ("channel_h", 110.0, "mm", "UNVERIFIED", "clears 91mm ball + margin"),
    ("channel_x0", -160.0, "mm", "UNVERIFIED", "channel rear end"),
    ("channel_z", 10.0, "mm", "UNVERIFIED", "floor-level through-chassis lane"),
    ("plate_thk", 8.0, "mm", "UNVERIFIED", "thin plate thickness (shared)"),
    ("plate_w", 10.0, "mm", "UNVERIFIED", "intake cheek width"),
    ("div_h", 60.0, "mm", "UNVERIFIED", "diverter rep height"),
    ("shooter_l", 200.0, "mm", "UNVERIFIED", "assumed shooter volume"),
    ("shooter_w", 200.0, "mm", "UNVERIFIED", "assumed shooter volume"),
    ("shooter_h", 250.0, "mm", "UNVERIFIED", "assumed shooter volume"),
    ("shooter_z", 120.0, "mm", "UNVERIFIED", "shooter base height"),
    ("bore", 100.0, "mm", "UNVERIFIED", "universal bore per D10"),
    ("flywheel_dia", 72.0, "mm", "VENDOR-PENDING", "goBILDA-style, datasheet pending"),
    ("flywheel_w", 30.0, "mm", "VENDOR-PENDING", "goBILDA-style, datasheet pending"),
    ("flywheel_x", -40.0, "mm", "UNVERIFIED", "flywheel center X"),
    ("roller_dia", 30.0, "mm", "UNVERIFIED",
     "intake roller representative; clears motors + front rail"),
    ("roller_width", 306.0, "mm", "UNVERIFIED",
     "spans intake cheek inner faces (intake_width - 2*plate_w)"),
    ("lifter_stow_l", 200.0, "mm", "UNVERIFIED", "assumed stowed lifter"),
    ("lifter_stow_w", 200.0, "mm", "UNVERIFIED", "assumed stowed lifter"),
    ("lifter_stow_h", 150.0, "mm", "UNVERIFIED", "assumed stowed lifter"),
    ("lifter_stow_x", 20.0, "mm", "UNVERIFIED", "stowed X offset"),
    ("lifter_stow_z", 120.0, "mm", "UNVERIFIED", "stowed base (top-mounted)"),
    ("mast_w", 80.0, "mm", "UNVERIFIED", "deployed mast section"),
    ("lifter_dep_z0", 120.0, "mm", "UNVERIFIED", "deployed mast base"),
    ("reach_z", 610.0, "mm", "UNVERIFIED", "deployed reach (>=546 sec 9.7 + clearance)"),
    ("stage1_w", 76.0, "mm", "UNVERIFIED", "outer cascade stage"),
    ("stage1_z1", 340.0, "mm", "UNVERIFIED", "outer stage top"),
    ("stage2_w", 74.0, "mm", "UNVERIFIED", "middle cascade stage"),
    ("stage2_z0", 230.0, "mm", "UNVERIFIED", "middle stage base"),
    ("stage2_z1", 440.0, "mm", "UNVERIFIED", "middle stage top"),
    ("stage3_w", 72.0, "mm", "UNVERIFIED", "inner cascade stage"),
    ("stage3_z0", 335.0, "mm", "UNVERIFIED", "inner stage base"),
    ("stage3_z1", 560.0, "mm", "UNVERIFIED", "inner stage top"),
    ("carriage_w", 120.0, "mm", "UNVERIFIED", "carriage plate section"),
    ("carriage_h", 40.0, "mm", "UNVERIFIED", "carriage plate height"),
    ("cradle_w", 120.0, "mm", "UNVERIFIED", "cradle width (91mm Nectar + clearance)"),
    ("cradle_h", 40.0, "mm", "UNVERIFIED", "cradle height"),
    ("cradle_z", 600.0, "mm", "UNVERIFIED", "cradle base height (>=546 sec 9.7)"),
    ("hive_aim_dist", 800.0, "mm", "UNVERIFIED", "aiming-reference standoff distance"),
    ("hive_aim_z", 300.0, "mm", "UNVERIFIED", "aiming-reference height (~launch_z)"),
    ("ref_size", 60.0, "mm", "UNVERIFIED", "field reference marker size"),
    ("flower_aim_x", 180.0, "mm", "UNVERIFIED", "flower aim marker X offset"),
    ("flower_aim_z", 546.0, "mm", "VERIFIED", "sec 9.7 flower top height"),
    ("flower_aim_w", 60.0, "mm", "UNVERIFIED", "flower aim marker width"),
    # sprint-06: mecanum rollers + secondary mechanism detail
    ("roller_count", 10.0, "count", "VENDOR-PENDING",
     "counted on goBILDA schematic 3606-0000-0096; STEP file authoritative"),
    ("mec_roll_dia", 14.0, "mm", "VENDOR-PENDING",
     "goBILDA schematic 3606-0000-0096 O14 roller"),
    ("mec_roll_rad", 41.0, "mm", "VENDOR-PENDING",
     "derived (wheel_dia - mec_roll_dia) / 2"),
    ("mec_roll_len", 20.0, "mm", "UNVERIFIED",
     "assumed roller length; keeps flat-cap ends inside O96 envelope"),
    ("mec_roll_pitch", 36.0, "deg", "VENDOR-PENDING",
     "derived 360 / roller_count"),
    ("mec_roll_slant", 45.0, "deg", "UNVERIFIED", "mecanum roller slant"),
    ("mec_pin_dia", 5.0, "mm", "UNVERIFIED",
     "roller axle pin dia (pins seat into face plates)"),
    ("mec_pin_len", 34.0, "mm", "UNVERIFIED",
     "roller pin overall length; tips embed ~1mm into face plates"),
    ("pv_boss_dia", 24.0, "mm", "UNVERIFIED", "intake pivot boss dia"),
    ("pv_boss_len", 20.0, "mm", "UNVERIFIED", "intake pivot boss length"),
    ("pv_boss_x", 180.0, "mm", "UNVERIFIED",
     "intake pivot boss center X (clear of lifter pedestal + roller)"),
    ("pv_boss_z", 60.0, "mm", "UNVERIFIED", "intake pivot boss center Z"),
    ("horn_l", 30.0, "mm", "UNVERIFIED", "diverter servo horn length"),
    ("horn_w", 10.0, "mm", "UNVERIFIED", "diverter servo horn width"),
    ("horn_h", 20.0, "mm", "UNVERIFIED", "diverter servo horn height"),
    ("stub_dia", 8.0, "mm", "VENDOR-PENDING",
     "goBILDA 8mm REX shaft standard, series page"),
    ("stub_len", 40.0, "mm", "UNVERIFIED", "flywheel stub shaft length"),
    ("guide_w", 6.0, "mm", "UNVERIFIED", "lifter stage guide block section"),
    ("guide_l", 20.0, "mm", "UNVERIFIED", "lifter stage guide block height"),
    ("lip_h", 12.0, "mm", "UNVERIFIED", "cradle lip height"),
    ("lip_t", 6.0, "mm", "UNVERIFIED", "cradle lip thickness"),
    ("erail_l", 140.0, "mm", "UNVERIFIED", "electronics rail length"),
    ("erail_w", 8.0, "mm", "UNVERIFIED", "electronics rail width"),
    ("erail_h", 6.0, "mm", "UNVERIFIED", "electronics rail height"),
    # sprint-07 frame aliases + rehaul drivetrain hardware
    ("rail_size", 48.0, "mm", "VENDOR-PENDING",
     "goBILDA 1120 U-channel ~48mm outer, D12"),
    ("rail_wall", 2.5, "mm", "UNVERIFIED",
     "assumed ~0.09in channel sheet wall; measure on hardware"),
    ("notch_w", 16.0, "mm", "UNVERIFIED", "shaft clearance notch width"),
    ("notch_d", 14.0, "mm", "UNVERIFIED", "shaft clearance notch depth"),
    ("hole_dia", 4.0, "mm", "VENDOR-PENDING",
     "goBILDA hole-grid ~O4 holes, catalog typical"),
    ("hole_pitch", 48.0, "mm", "UNVERIFIED",
     "subset of the 8mm goBILDA grid; visual pitch assumed"),
    ("pan_thk", 3.0, "mm", "UNVERIFIED", "belly pan sheet"),
    ("deck_thk", 3.0, "mm", "UNVERIFIED", "rear deck sheet"),
    ("pan_fillet", 8.0, "mm", "UNVERIFIED", "belly pan corner fillet"),
    ("deck_fillet", 8.0, "mm", "UNVERIFIED", "rear deck corner fillet"),
    ("plate_fillet", 4.0, "mm", "UNVERIFIED", "small-plate edge fillet"),
    ("wplate_dia", 92.0, "mm", "UNVERIFIED",
     "wheel side plate dia (inset inside O96 envelope)"),
    ("wplate_thk", 4.0, "mm", "UNVERIFIED", "wheel side plate thickness"),
    ("wplate_gap", 1.0, "mm", "UNVERIFIED",
     "wheel plate standoff inside the O96 envelope face"),
    ("hub_dia", 26.0, "mm", "UNVERIFIED", "wheel hub OD"),
    ("hub_w", 20.0, "mm", "UNVERIFIED", "wheel hub width"),
    ("bore_dia", 8.4, "mm", "VENDOR-PENDING",
     "8mm REX clearance bore (goBILDA REX bore typical)"),
    ("plate_bore", 9.0, "mm", "UNVERIFIED", "wheel plate shaft clearance"),
    ("shaft_dia", 8.0, "mm", "VENDOR-PENDING",
     "goBILDA 8mm REX shaft standard, series page"),
    ("shaft_len", 76.0, "mm", "UNVERIFIED",
     "live drive shaft: motor face -> web notch -> bearing -> hub"),
    ("bear_w", 26.0, "mm", "UNVERIFIED", "bearing block face width"),
    ("bear_h", 26.0, "mm", "UNVERIFIED", "bearing block face height"),
    ("bear_t", 6.0, "mm", "UNVERIFIED", "bearing block thickness"),
    ("bear_bore", 8.4, "mm", "VENDOR-PENDING",
     "bearing bore, 8mm REX clearance"),
    ("bear_bolt_d", 4.0, "mm", "UNVERIFIED", "bearing block bolt hole dia"),
    ("bear_bolt_off", 9.0, "mm", "UNVERIFIED", "bearing bolt hole offset"),
    ("mface_w", 30.0, "mm", "UNVERIFIED", "motor face plate width"),
    ("mface_h", 30.0, "mm", "UNVERIFIED", "motor face plate height"),
    ("mface_t", 2.5, "mm", "UNVERIFIED", "motor face plate thickness"),
    ("motor_dia", 36.0, "mm", "VENDOR-PENDING",
     "goBILDA 5203 Yellow Jacket ~36mm gearbox, D12"),
    ("motor_len", 60.0, "mm", "UNVERIFIED", "motor body length inward"),
    ("intake_axle_dia", 12.0, "mm", "UNVERIFIED", "intake pivot axle"),
    ("post_w", 20.0, "mm", "UNVERIFIED", "shooter support post width"),
    ("lifter_base_w", 116.0, "mm", "UNVERIFIED",
     "lifter base plate (clears channel top corner)"),
    ("lifter_ped_w", 80.0, "mm", "UNVERIFIED",
     "lifter pedestal section (clears front rail + intake axle)"),
    # rehaul coherence glue (mount-chain placeholders pending sprints 02-04)
    ("imount_l", 20.0, "mm", "UNVERIFIED", "intake mount bracket length"),
    ("imount_h", 20.0, "mm", "UNVERIFIED", "intake mount bracket height"),
    ("csupp_w", 10.0, "mm", "UNVERIFIED", "channel saddle width"),
    ("csupp_h", 9.5, "mm", "UNVERIFIED",
     "channel saddle height (pan top to channel floor)"),
    ("sfloor_thk", 10.0, "mm", "UNVERIFIED", "shooter floor plate thickness"),
    ("sside_thk", 6.0, "mm", "UNVERIFIED", "shooter side plate thickness"),
    ("daxle_dia", 6.0, "mm", "UNVERIFIED", "diverter hinge axle dia"),
    ("cheek_bore", 11.0, "mm", "UNVERIFIED",
     "cheek clearance bore for the drive shaft (8mm shaft + 3mm)"),
    ("axle_bore", 13.0, "mm", "UNVERIFIED",
     "cheek clearance bore for the intake pivot axle (O12 + 1mm)"),
    # sprint-02: intake + transfer component fidelity
    ("nectar_dia", 91.0, "mm", "VERIFIED",
     "Nectar ball ~91mm, competition manual sec 9.8"),
    ("pollen_dia", 71.0, "mm", "VERIFIED",
     "Pollen ball ~71mm, competition manual sec 9.8"),
    ("paddle_sweep_deg", 90.0, "deg", "UNVERIFIED",
     "diverter paddle swing arc to clear the lane"),
    ("roller_bore", 9.0, "mm", "UNVERIFIED",
     "cheek bore for the 8mm roller shaft (+1mm clearance)"),
    ("rib_count", 12.0, "count", "UNVERIFIED", "intake roller grip ribs"),
    ("rib_w", 4.0, "mm", "UNVERIFIED", "grip rib tangential width"),
    ("rib_h", 3.0, "mm", "UNVERIFIED",
     "grip rib height (embeds 0.5mm into the tube)"),
    ("rib_inset", 6.0, "mm", "UNVERIFIED", "rib inset from tube ends"),
    ("servo_l", 40.5, "mm", "VENDOR-PENDING",
     "REV SRS-class servo ~40.5mm body"),
    ("servo_w", 20.4, "mm", "VENDOR-PENDING",
     "REV SRS-class servo ~20.4mm body"),
    ("servo_h", 36.0, "mm", "VENDOR-PENDING",
     "REV SRS-class servo ~36mm body"),
    ("chan_wall_t", 3.0, "mm", "UNVERIFIED", "transfer wall sheet"),
    ("chan_floor_t", 3.0, "mm", "UNVERIFIED", "transfer floor sheet"),
    ("bush_dia", 10.0, "mm", "UNVERIFIED", "diverter bushing OD"),
    ("bush_t", 4.0, "mm", "UNVERIFIED", "diverter bushing thickness"),
    ("bush_bore", 6.4, "mm", "UNVERIFIED",
     "bushing bore for the O6 hinge axle"),
    ("paddle_bore", 6.4, "mm", "UNVERIFIED", "paddle hinge bore"),
    ("mbolt_d", 4.4, "mm", "UNVERIFIED",
     "M4 clearance bolt hole in mounts/cheeks"),
    ("imount_t", 4.0, "mm", "UNVERIFIED", "intake mount bracket leg"),
    ("csupp_t", 2.5, "mm", "UNVERIFIED", "channel saddle foot thickness"),
    ("lip_sill_d", 22.0, "mm", "UNVERIFIED", "intake mouth sill depth"),
    ("wall_chamfer", 0.8, "mm", "UNVERIFIED", "sheet-edge chamfer"),
]

# managed-name registry: same list populate() produces, used by
# archive_if_foreign() before the rebuild so re-runs never archive
# our own output. Keep in sync with the construction loops below.
def expected_names():
    names = {"Parameters", "RobotAssembly", "CoordRef", "Tools",
             "Envelopes", "Drivebase", "Intake", "Transfer", "Shooter",
             "Lifter", "Electronics",
             "ENV_START", "ENV_EXPANSION", "VOL_DRIVEBASE",
             "BATTERY", "ELECTRONICS",
             "AXIS_X", "AXIS_Y", "AXIS_Z",
             "VOL_INTAKE", "VOL_TRANSFER", "VOL_SHOOTER",
             "VOL_LIFTER_STOWED", "VOL_LIFTER_DEPLOYED",
             "INTAKE_CHEEK_L", "INTAKE_CHEEK_R", "INTAKE_ROLLER",
             "INTAKE_ROLLER_SHAFT", "INTAKE_BEARING_L",
             "INTAKE_BEARING_R", "INTAKE_MOTOR", "INTAKE_MOTOR_BRKT",
             "INTAKE_LIP", "CHANNEL_FLOOR", "CHANNEL_WALL_L",
             "CHANNEL_WALL_R", "DIVERTER_PADDLE", "DIVERTER_BUSH_L",
             "DIVERTER_BUSH_R", "DIVERTER_SERVO",
             "VOL_CHANNEL_CLEAR", "VOL_BALL_PATH",
             "MECH_SHOOTER_BODY", "MECH_SHOOTER_HOOD",
             "MECH_FLYWHEEL_L", "MECH_FLYWHEEL_R",
             "MECH_LIFTER_STOWED", "MECH_STAGE_1", "MECH_STAGE_2",
             "MECH_STAGE_3", "MECH_CARRIAGE", "MECH_CRADLE",
             "REF_HIVE", "REF_FLOWER",
             "PIVOT_MOUNT_L", "PIVOT_MOUNT_R", "DIVERTER_HORN",
             "STUB_SHAFT_L", "STUB_SHAFT_R",
             "STAGE_GUIDE_L", "STAGE_GUIDE_R", "CRADLE_LIP",
             "ELEC_RAIL_L", "ELEC_RAIL_R",
             "INTAKE_AXLE_L", "INTAKE_AXLE_R",
             "POST_SHOOTER_L", "POST_SHOOTER_R",
             "LIFTER_BASE", "LIFTER_PED",
             "BELLY_PAN", "REAR_DECK",
             "FRAME_RAIL_L", "FRAME_RAIL_R", "FRAME_RAIL_F",
             "FRAME_RAIL_B",
             "INTAKE_MOUNT_L", "INTAKE_MOUNT_R",
             "CHANNEL_SUPP_F", "CHANNEL_SUPP_B",
             "SHOOTER_FLOOR", "SHOOTER_SIDE_L", "SHOOTER_SIDE_R",
             "DIVERTER_AXLE", "REAR_DECK_L", "REAR_DECK_R"}
    # rehaul drivetrain (part-kit naming)
    names.update("WHEEL_ASSY_%s" % w for w, *_ in WHEELS)
    names.update("ENV_WHEEL_%s" % w for w, *_ in WHEELS)
    names.update("WHEEL_HUB_%s" % w for w, *_ in WHEELS)
    names.update("WHEEL_PLATE_%s_%s" % (w, io)
                 for w, *_ in WHEELS for io in ("IN", "OUT"))
    names.update("MOTOR_%s" % w for w, *_ in WHEELS)
    names.update("MOUNT_MOTOR_%s" % w for w, *_ in WHEELS)
    names.update("BEARING_%s" % w for w, *_ in WHEELS)
    names.update("SHAFT_%s" % w for w, *_ in WHEELS)
    names.update("ROLLER_%s_%02d" % (w, k)
                 for w, *_ in WHEELS for k in range(10))
    names.update("ROLLER_%s_%02d_B" % (w, k)
                 for w, *_ in WHEELS for k in range(10))
    # tools (all part-kit intermediates are TOOL_-prefixed)
    names.update("TOOL_%s_BLK" % n for n in (
        "BELLY_PAN", "REAR_DECK_L", "REAR_DECK_R",
        "INTAKE_LIP", "CHANNEL_FLOOR",
        "SHOOTER_FLOOR", "SHOOTER_SIDE_L", "SHOOTER_SIDE_R",
        "INTAKE_CHEEK_L", "INTAKE_CHEEK_R",
        "CHANNEL_WALL_L", "CHANNEL_WALL_R",
        "DIVERTER_PADDLE"))
    names.update("TOOL_%s_CUT" % n for n in (
        "INTAKE_CHEEK_L", "INTAKE_CHEEK_R",
        "CHANNEL_WALL_L", "CHANNEL_WALL_R"))
    names.update("TOOL_%s_BORE%02d" % (n, i)
                 for n in ("INTAKE_CHEEK_L", "INTAKE_CHEEK_R")
                 for i in range(7))
    names.update("TOOL_INTAKE_MOTOR_BRKT_%s" % t
                 for t in ("BLK", "CUT"))
    names.update("TOOL_INTAKE_MOTOR_BRKT_BORE%02d" % i for i in range(2))
    names.update("TOOL_CHANNEL_WALL_L_BORE%02d" % i for i in range(3))
    names.add("TOOL_CHANNEL_WALL_R_BORE00")
    names.add("TOOL_DIVERTER_PADDLE_BORE00")
    # ribbed intake roller: TOOL tube + TOOL ribs + TOOL compound
    names.update(("TOOL_INTAKE_ROLLER_TUBE_BLK",
                  "TOOL_INTAKE_ROLLER_TUBE_BORE",
                  "TOOL_INTAKE_ROLLER_TUBE",
                  "TOOL_INTAKE_ROLLER_TOOLS"))
    names.update("TOOL_INTAKE_ROLLER_RIB%02d" % i for i in range(12))
    # L-brackets: TOOL leg + foot + L + bolt cuts
    for n in ("INTAKE_MOUNT_L", "INTAKE_MOUNT_R",
              "CHANNEL_SUPP_F", "CHANNEL_SUPP_B"):
        names.update("TOOL_%s_%s" % (n, t) for t in ("LEG", "FOOT", "L"))
    names.update("TOOL_%s_B%02d" % (n, i)
                 for n in ("INTAKE_MOUNT_L", "INTAKE_MOUNT_R",
                           "CHANNEL_SUPP_F", "CHANNEL_SUPP_B")
                 for i in range(2))
    # bearing_block internals: BLK + BORE + 4 bolt cuts
    names.update("TOOL_INTAKE_BEARING_%s_%s" % (s, t)
                 for s in "LR" for t in ("BLK", "BORE"))
    names.update("TOOL_INTAKE_BEARING_%s_B%02d" % (s, i)
                 for s in "LR" for i in range(4))
    # bore_cyl internals for bosses + bushings
    names.update("TOOL_%s_%s" % (n, t)
                 for n in ("PIVOT_MOUNT_L", "PIVOT_MOUNT_R",
                           "DIVERTER_BUSH_L", "DIVERTER_BUSH_R")
                 for t in ("BLK", "BORE"))
    names.update("TOOL_FRAME_RAIL_%s_OUT" % s for s in "LRFB")
    names.update("TOOL_FRAME_RAIL_%s_INNER" % s for s in "LRFB")
    names.update("TOOL_FRAME_RAIL_%s_TOOLS" % s for s in "LRFB")
    names.update("TOOL_FRAME_RAIL_%s_FH%02d" % (s, i)
                 for s in "LR" for i in range(8))
    names.update("TOOL_FRAME_RAIL_%s_WH%02d" % (s, i)
                 for s in "LR" for i in range(7))
    names.update("TOOL_FRAME_RAIL_%s_FH%02d" % (s, i)
                 for s in "FB" for i in range(5))
    names.update("TOOL_FRAME_RAIL_%s_WH%02d" % (s, i)
                 for s in "FB" for i in range(4))
    names.update("TOOL_FRAME_RAIL_%s_NOTCH%d" % (s, j)
                 for s in "LR" for j in range(2))
    for w, *_ in WHEELS:
        names.add("TOOL_WHEEL_HUB_%s_BLK" % w)
        names.add("TOOL_WHEEL_HUB_%s_BORE" % w)
        for io in ("IN", "OUT"):
            names.add("TOOL_WHEEL_PLATE_%s_%s_BLK" % (w, io))
            names.add("TOOL_WHEEL_PLATE_%s_%s_BORE" % (w, io))
            names.add("TOOL_WHEEL_PLATE_%s_%s_BRD" % (w, io))
        names.add("TOOL_MOUNT_MOTOR_%s_BLK" % w)
        names.add("TOOL_MOUNT_MOTOR_%s_FIL" % w)
        names.add("TOOL_MOUNT_MOTOR_%s_BORE" % w)
        names.update("TOOL_MOUNT_MOTOR_%s_B%02d" % (w, i)
                     for i in range(4))
        names.add("TOOL_BEARING_%s_BLK" % w)
        names.add("TOOL_BEARING_%s_FIL" % w)
        names.add("TOOL_BEARING_%s_BORE" % w)
        names.update("TOOL_BEARING_%s_B%02d" % (w, i) for i in range(4))
        names.add("TOOL_WHEEL_PLATE_%s_IN_BRD_TOOLS" % w)
        names.add("TOOL_WHEEL_PLATE_%s_OUT_BRD_TOOLS" % w)
        names.add("TOOL_WHEEL_HUB_%s_TOOLS" % w)
        names.add("TOOL_MOUNT_MOTOR_%s_TOOLS" % w)
        names.add("TOOL_BEARING_%s_TOOLS" % w)
        for k in range(10):
            names.add("TOOL_ROLLER_%s_%02d_BT" % (w, k))
            names.add("TOOL_ROLLER_%s_%02d_PT" % (w, k))
            names.add("TOOL_ROLLER_%s_%02d_B_TOOLS" % (w, k))
    return names


def archive_if_foreign():
    """Preserve a pre-existing file that holds objects we did not create."""
    if not TARGET.exists():
        return
    foreign = True
    try:
        doc = App.openDocument(str(TARGET))
        managed = set(expected_names())
        for o in doc.Objects:
            if o.TypeId == "App::Origin":
                managed.add(o.Name)
                managed.update(c.Name for c in getattr(o, "OriginFeatures", []))
        foreign = [o.Name for o in doc.Objects if o.Name not in managed]
        App.closeDocument(doc.Name)
    except Exception:
        pass
    if not foreign:
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = ARCHIVE_DIR / ("%s_%s.FCStd" % (TARGET.stem, stamp))
    n = 1
    while dst.exists():
        dst = ARCHIVE_DIR / ("%s_%s_%02d.FCStd" % (TARGET.stem, stamp, n))
        n += 1
    shutil.copy2(str(TARGET), str(dst))
    print("BUILD: archived prior content -> cad/archive/%s" % dst.name)


def populate(doc):
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.Label = "Parameters"
    for col, head in zip("ABCDE", ("alias", "value", "unit", "status",
                                   "source")):
        sheet.set(col + "1", head)
    for i, (alias, val, unit, status, src) in enumerate(PARAMS):
        r = str(i + 2)
        sheet.set("A" + r, alias)
        sheet.set("B" + r, repr(val))
        sheet.set("C" + r, unit)
        sheet.set("D" + r, status)
        sheet.set("E" + r, src)
        sheet.setAlias("B" + r, alias)

    robot = doc.addObject("App::Part", "RobotAssembly")
    robot.Label = "BIOBUZZ_robot_assembly_rehaul"
    coord = doc.addObject("App::Part", "CoordRef")
    coord.Label = "COORD_REF_world_origin_axes"
    doc.recompute()  # let the App::Part Origin children appear

    # ---------------- envelopes / reference markers -----------------
    env = pk.box(doc, "ENV_START",
                 "ENV_START_18in_cube_457mm_VERIFIED_R102",
                 "VERIFIED - R102 TU01",
                 {"Length": "Parameters.start_cube",
                  "Width": "Parameters.start_cube",
                  "Height": "Parameters.start_cube"},
                 {"Placement.Base.x": "-Parameters.start_cube / 2",
                  "Placement.Base.y": "-Parameters.start_cube / 2"})
    ex = pk.box(doc, "ENV_EXPANSION",
                "ENV_EXPANSION_18x24x29in_VERIFIED_R105",
                "VERIFIED - R105 TU01",
                {"Length": "Parameters.expansion_width",
                 "Width": "Parameters.expansion_depth",
                 "Height": "Parameters.expansion_height"},
                {"Placement.Base.x": "-Parameters.expansion_width / 2",
                 "Placement.Base.y": "-Parameters.expansion_depth / 2"})
    vol = pk.box(doc, "VOL_DRIVEBASE",
                 "VOL_DRIVEBASE_packaging_420x420x120_UNVERIFIED",
                 "UNVERIFIED - assumed packaging volume",
                 {"Length": "Parameters.chassis_length",
                  "Width": "Parameters.chassis_width",
                  "Height": "Parameters.chassis_height"},
                 {"Placement.Base.x": "-Parameters.chassis_length / 2",
                  "Placement.Base.y": "-Parameters.chassis_width / 2"})

    # ================= REHAULED CHASSIS + DRIVETRAIN =================
    # Perimeter ring of goBILDA-1120-style U-channel (open face outboard
    # so the mouth shows the section + web holes; top-flange hole row +
    # top-edge shaft notches on the side rails).
    drive = []
    sy_rail = ("Parameters.wheel_y_offset - Parameters.wheel_width / 2"
               " - Parameters.rail_size")
    flange_line_l = ("Parameters.wheel_y_offset - Parameters.wheel_width / 2"
                     " - Parameters.rail_size / 2")
    flange_line_r = "-(%s)" % flange_line_l
    for name, sgn, face in (("FRAME_RAIL_L", 1, "+Y"),
                            ("FRAME_RAIL_R", -1, "-Y")):
        y0 = (sy_rail if sgn > 0 else
              "-(%s) - Parameters.rail_size" % sy_rail)
        rail = pk.channel_u(
            doc, name,
            "%s_1120channel_48mm_open_side_rail_VENDOR-PENDING" % name,
            "VENDOR-PENDING - goBILDA 1120 ~48mm U-channel (D12)",
            ("-Parameters.chassis_length / 2", y0, "0"),
            "Parameters.chassis_length", "Parameters.rail_size",
            "Parameters.rail_wall", face, axis="X",
            flange_holes={"count": 8, "dia": "Parameters.hole_dia",
                          "pitch": "Parameters.hole_pitch", "start": "42",
                          "line": (flange_line_l if sgn > 0
                                   else flange_line_r)},
            web_holes={"count": 7, "dia": "Parameters.hole_dia",
                       "pitch": "60", "start": "30",
                       "z": "Parameters.rail_size / 2"},
            notches=["Parameters.wheel_x_offset",
                     "-Parameters.wheel_x_offset"])
        drive.append(rail)
    for name, sgn, face in (("FRAME_RAIL_F", 1, "+X"),
                            ("FRAME_RAIL_B", -1, "-X")):
        x0 = ("Parameters.chassis_length / 2 - Parameters.rail_size"
              if sgn > 0 else "-Parameters.chassis_length / 2")
        rail = pk.channel_u(
            doc, name,
            "%s_1120channel_48mm_open_end_rail_VENDOR-PENDING" % name,
            "VENDOR-PENDING - goBILDA 1120 ~48mm U-channel (D12)",
            (x0, "-(%s)" % sy_rail, "0"),
            "2 * (%s)" % sy_rail, "Parameters.rail_size",
            "Parameters.rail_wall", face, axis="Y",
            flange_holes={"count": 5, "dia": "Parameters.hole_dia",
                          "pitch": "Parameters.hole_pitch", "start": "42",
                          "line": ("Parameters.chassis_length / 2"
                                   " - Parameters.rail_size / 2"
                                   if sgn > 0 else
                                   "-Parameters.chassis_length / 2"
                                   " + Parameters.rail_size / 2")},
            web_holes={"count": 4, "dia": "Parameters.hole_dia",
                       "pitch": "60", "start": "30",
                       "z": "Parameters.rail_size / 2"})
        drive.append(rail)

    # belly pan (corner-filleted sheet inside the ring, on the lower lip)
    pan = pk.plate(
        doc, "BELLY_PAN", "BELLY_PAN_3mm_sheet_fillet_UNVERIFIED",
        "UNVERIFIED - belly pan inside frame ring",
        {"Length": "Parameters.chassis_length - 2 * Parameters.rail_size",
         "Width": "2 * (%s)" % sy_rail,
         "Height": "Parameters.pan_thk"},
        {"Placement.Base.x":
             "-(Parameters.chassis_length - 2 * Parameters.rail_size) / 2",
         "Placement.Base.y": "-(%s)" % sy_rail,
         "Placement.Base.z": "Parameters.rail_wall"},
        fillet_r=pk.pval(sheet, "pan_fillet"),
        edge_pred=pk.pred_axis((0, 0, 1)))
    drive.append(pan)

    # rear deck plates flanking the ball channel; the span stops short
    # of the rear motors (they pass inboard) and ends before the front
    # mechanism bay
    for name, sgn in (("REAR_DECK_L", 1), ("REAR_DECK_R", -1)):
        deck = pk.plate(
            doc, name, "%s_3mm_sheet_fillet_UNVERIFIED" % name,
            "UNVERIFIED - rear deck plate beside the ball channel",
            {"Length": "(Parameters.wheel_x_offset - Parameters.motor_dia / 2"
                       " - 2) - 15",
             "Width": "(%s) - Parameters.channel_w / 2" % sy_rail,
             "Height": "Parameters.deck_thk"},
            {"Placement.Base.x":
                 "-(Parameters.wheel_x_offset - Parameters.motor_dia / 2 - 2)",
             "Placement.Base.y":
                 "Parameters.channel_w / 2" if sgn > 0 else
                 "-(%s)" % sy_rail,
             "Placement.Base.z": "Parameters.rail_size - Parameters.rail_wall"
                                 " - Parameters.deck_thk"},
            fillet_r=pk.pval(sheet, "deck_fillet"),
            edge_pred=pk.pred_axis((0, 0, 1)))
        drive.append(deck)

    # ---------------- wheel assemblies + drive hardware --------------
    # X-pattern slant: carrier axes unrotated; the per-wheel sgn in the
    # roller tilt gives diagonal handedness (FL+RR vs FR+RL).
    envs = []
    pitch = pk.pval(sheet, "mec_roll_pitch")
    for wtag, sx, sy, sgn in WHEELS:
        carrier, solids = pk.mecanum_wheel(
            doc, wtag, sgn,
            "VENDOR-PENDING - goBILDA 96mm mecanum 3213-3606-0002"
            " (schematic 3606-0000-0096)",
            "goBILDA 3213-3606-0002 96mm mecanum wheel assembly",
            pitch, int(pk.pval(sheet, "roller_count")))
        pk.bind(carrier, {
            "Placement.Base.x":
                "Parameters.wheel_x_offset" if sx > 0
                else "-Parameters.wheel_x_offset",
            "Placement.Base.y":
                "Parameters.wheel_y_offset" if sy > 0
                else "-Parameters.wheel_y_offset",
            "Placement.Base.z": "Parameters.wheel_dia / 2"})
        drive.append(carrier)

        e = pk.box(doc, "ENV_WHEEL_" + wtag,
                   "ENV_WHEEL_%s_O96x32_roller_envelope_marker" % wtag,
                   "UNVERIFIED - wheel+roller envelope reference; O96 "
                   "measured at roller surfaces per schematic "
                   "3606-0000-0096",
                   {"Length": "Parameters.wheel_dia",
                    "Width": "Parameters.wheel_width",
                    "Height": "Parameters.wheel_dia"},
                   {"Placement.Base.x":
                        "Parameters.wheel_x_offset - Parameters.wheel_dia / 2"
                        if sx > 0 else
                        "-Parameters.wheel_x_offset - Parameters.wheel_dia / 2",
                    "Placement.Base.y":
                        "Parameters.wheel_y_offset - Parameters.wheel_width / 2"
                        if sy > 0 else
                        "-Parameters.wheel_y_offset - Parameters.wheel_width / 2"})
        envs.append(e)

        # live-shaft drivetrain (GEO7 documented): 5203 motor inboard of
        # the side-rail web, face plate on the web inner face, REX shaft
        # through a top-edge web notch, flange bearing on the cavity
        # face, shaft continues into the wheel hub.
        wx = ("Parameters.wheel_x_offset" if sx > 0
              else "-Parameters.wheel_x_offset")
        web_in = ("Parameters.wheel_y_offset - Parameters.wheel_width / 2"
                  " - Parameters.rail_size")
        if sy > 0:
            face_y = "(%s) - Parameters.mface_t" % web_in
            motor_y = "(%s) - Parameters.mface_t - Parameters.motor_len" \
                      % web_in
            bear_y = "(%s) + Parameters.rail_wall" % web_in
            shaft_y = ("(%s) - 16" % web_in)
        else:
            face_y = "-(%s)" % web_in
            motor_y = "-(%s) + Parameters.mface_t" % web_in
            bear_y = ("-(%s) - Parameters.rail_wall - Parameters.bear_t"
                      % web_in)
            shaft_y = ("-(%s) + 16 - Parameters.shaft_len" % web_in)
        m = pk.cyl(doc, "MOTOR_" + wtag,
                   "MOTOR_%s_5203YellowJacket_O36_VENDOR-PENDING" % wtag,
                   "VENDOR-PENDING - goBILDA 5203 Yellow Jacket ~36mm (D12)",
                   {"Radius": "Parameters.motor_dia / 2",
                    "Height": "Parameters.motor_len"},
                   {"Placement.Base.x": wx,
                    "Placement.Base.y": motor_y,
                    "Placement.Base.z": "Parameters.wheel_dia / 2"},
                   pk.axis_rot("Y"),
                   "goBILDA 5203 Yellow Jacket-style motor placeholder")
        face = pk.face_plate(
            doc, "MOUNT_MOTOR_" + wtag,
            "MOUNT_MOTOR_%s_face_plate_30x30_UNVERIFIED" % wtag,
            "UNVERIFIED - motor face plate on rail web inner face",
            "Parameters.mface_w", "Parameters.mface_t",
            "Parameters.mface_h", "Parameters.bore_dia",
            {"Placement.Base.x": "%s - Parameters.mface_w / 2" % wx,
             "Placement.Base.y": face_y,
             "Placement.Base.z": "Parameters.wheel_dia / 2"
                                 " - Parameters.mface_h / 2"},
            "Y", "Parameters.bear_bolt_d", "Parameters.bear_bolt_off",
            pk.pval(sheet, "plate_fillet"))
        brg = pk.bearing_block(
            doc, "BEARING_" + wtag,
            "BEARING_%s_flange_block_26x26_UNVERIFIED" % wtag,
            "UNVERIFIED - flange bearing on rail web cavity face",
            "Parameters.bear_w", "Parameters.bear_t",
            "Parameters.bear_h", "Parameters.bear_bore",
            {"Placement.Base.x": "%s - Parameters.bear_w / 2" % wx,
             "Placement.Base.y": bear_y,
             "Placement.Base.z": "Parameters.wheel_dia / 2"
                                 " - Parameters.bear_h / 2"},
            "Y", "Parameters.bear_bolt_d", "Parameters.bear_bolt_off",
            pk.pval(sheet, "plate_fillet"))
        sh = pk.shaft(doc, "SHAFT_" + wtag,
                      "SHAFT_%s_8mmREX_live_VENDOR-PENDING" % wtag,
                      "VENDOR-PENDING - goBILDA 8mm REX live shaft (GEO7)",
                      "Parameters.shaft_dia", "Parameters.shaft_len",
                      {"Placement.Base.x": wx,
                       "Placement.Base.y": shaft_y,
                       "Placement.Base.z": "Parameters.wheel_dia / 2"},
                      "Y")
        drive += [m, face, brg, sh]

    # ----------------- battery + electronics placeholders ------------
    bat = pk.box(doc, "BATTERY", "BATTERY_180x55x75_on_pan_UNVERIFIED",
                 "UNVERIFIED - assumed dimensions/position",
                 {"Length": "Parameters.battery_l",
                  "Width": "Parameters.battery_w",
                  "Height": "Parameters.battery_h"},
                 {"Placement.Base.x": "Parameters.bat_x",
                  "Placement.Base.y": "Parameters.bat_y",
                  "Placement.Base.z": "Parameters.rail_wall"
                                      " + Parameters.pan_thk"})
    elec = pk.box(doc, "ELECTRONICS",
                  "ELECTRONICS_control_hub_160x55x35_UNVERIFIED",
                  "UNVERIFIED - assumed dimensions/position",
                  {"Length": "Parameters.elec_l",
                   "Width": "Parameters.elec_w",
                   "Height": "Parameters.elec_h"},
                  {"Placement.Base.x": "Parameters.elec_x",
                   "Placement.Base.y": "Parameters.elec_y",
                   "Placement.Base.z": "Parameters.rail_wall"
                                       " + Parameters.pan_thk"
                                       " + Parameters.erail_h"})

    axes = []
    for name, dims, pos in (
            ("AXIS_X", ("Parameters.axis_len", "Parameters.axis_thk",
                        "Parameters.axis_thk"), (0.0, "-t", "-t")),
            ("AXIS_Y", ("Parameters.axis_thk", "Parameters.axis_len",
                        "Parameters.axis_thk"), ("-t", 0.0, "-t")),
            ("AXIS_Z", ("Parameters.axis_thk", "Parameters.axis_thk",
                        "Parameters.axis_len"), ("-t", "-t", 0.0))):
        a = pk.box(doc, name, "%s_indicator_UNVERIFIED" % name,
                   "UNVERIFIED - reference marker")
        a.setExpression("Length", dims[0])
        a.setExpression("Width", dims[1])
        a.setExpression("Height", dims[2])
        a.Placement.Base = App.Vector(*(0.0 if v == "-t" else v for v in pos))
        for comp, v in zip("xyz", pos):
            if v == "-t":
                a.setExpression("Placement.Base." + comp,
                                "-Parameters.axis_thk / 2")
        axes.append(a)

    # ---------------- packaging volumes (hidden placeholders) --------
    mech = []
    vi = pk.box(doc, "VOL_INTAKE",
                "VOL_INTAKE_reserve_160x340x120_UNVERIFIED",
                "UNVERIFIED - intake packaging reserve (shaft tips)",
                {"Length": "Parameters.intake_depth",
                 "Width": "Parameters.intake_width + 14",
                 "Height": "Parameters.intake_height"},
                {"Placement.Base.x":
                     "Parameters.start_cube / 2 - Parameters.intake_depth",
                 "Placement.Base.y":
                     "-(Parameters.intake_width + 14) / 2"})
    mech.append(vi)
    vt = pk.box(doc, "VOL_TRANSFER",
                "VOL_TRANSFER_floor_lane_to_intake_face_UNVERIFIED",
                "UNVERIFIED - through-chassis ball path, ends at intake "
                "face",
                {"Length": "Parameters.start_cube / 2 - Parameters.intake_depth"
                           " - Parameters.channel_x0",
                 "Width": "Parameters.channel_w + 16",
                 "Height": "Parameters.channel_z + Parameters.channel_h"
                           " - Parameters.rail_wall - Parameters.pan_thk"},
                {"Placement.Base.x": "Parameters.channel_x0",
                 "Placement.Base.y":
                     "-(Parameters.channel_w + 16) / 2",
                 "Placement.Base.z": "Parameters.rail_wall"
                                     " + Parameters.pan_thk"})
    mech.append(vt)
    vs = pk.box(doc, "VOL_SHOOTER",
                "VOL_SHOOTER_reserve_200x200x250_UNVERIFIED",
                "UNVERIFIED - assumed shooter packaging volume",
                {"Length": "Parameters.shooter_l",
                 "Width": "Parameters.shooter_w",
                 "Height": "Parameters.shooter_h"},
                {"Placement.Base.x": "-Parameters.shooter_l",
                 "Placement.Base.y": "-Parameters.shooter_w / 2",
                 "Placement.Base.z": "Parameters.shooter_z"})
    mech.append(vs)
    vls = pk.box(doc, "VOL_LIFTER_STOWED",
                 "VOL_LIFTER_STOWED_200x200x150_top_mount_UNVERIFIED",
                 "UNVERIFIED - assumed stowed lifter volume",
                 {"Length": "Parameters.lifter_stow_l",
                  "Width": "Parameters.lifter_stow_w",
                  "Height": "Parameters.lifter_stow_h"},
                 {"Placement.Base.x": "Parameters.lifter_stow_x",
                  "Placement.Base.y": "-Parameters.lifter_stow_w / 2",
                  "Placement.Base.z": "Parameters.lifter_stow_z"})
    mech.append(vls)
    vld = pk.box(doc, "VOL_LIFTER_DEPLOYED",
                 "VOL_LIFTER_DEPLOYED_ghost_reach610_UNVERIFIED",
                 "UNVERIFIED - assumed deployed lifter envelope",
                 {"Length": "Parameters.mast_w",
                  "Width": "Parameters.mast_w",
                  "Height": "Parameters.reach_z - Parameters.lifter_dep_z0"},
                 {"Placement.Base.x":
                      "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                      " - Parameters.mast_w / 2",
                  "Placement.Base.y": "-Parameters.mast_w / 2",
                  "Placement.Base.z": "Parameters.lifter_dep_z0"})
    mech.append(vld)

    # ============ REHAULED INTAKE + TRANSFER (sprint-02) ============
    # Component vocabulary: bored/chamfered cheek plates, ribbed roller
    # tube on a live REX shaft with bearing blocks, bored pivot bosses
    # with stub axles, mount L-brackets, sheet channel, hinge diverter.
    # rib tips (od/2 - 0.5 + rib_h) stay inside the start-cube face and
    # the rib roots clear the side-rail top flange (z=48)
    roller_cx = ("Parameters.start_cube / 2 - Parameters.roller_dia / 2"
                 " - Parameters.rib_h")
    roller_cz = ("Parameters.rail_size + Parameters.roller_dia / 2"
                 " + Parameters.rib_h")

    # cheek plates: roller-shaft bore, drive-shaft clearance bore,
    # pivot-axle bore, 2 mount bolt holes, outer-rim chamfer
    for name, sgn in (("INTAKE_CHEEK_L", 1), ("INTAKE_CHEEK_R", -1)):
        cheek_y = ("Parameters.intake_width / 2 - Parameters.plate_w"
                   if sgn > 0 else "-Parameters.intake_width / 2")
        bore_y = ("Parameters.intake_width / 2 - Parameters.plate_w - 1"
                  if sgn > 0 else "-Parameters.intake_width / 2 - 1")
        bores = [
            ("Parameters.roller_bore",
             {"Placement.Base.x": roller_cx,
              "Placement.Base.y": bore_y,
              "Placement.Base.z": roller_cz}, "Y",
             "Parameters.plate_w + 2"),
            ("Parameters.cheek_bore",
             {"Placement.Base.x": "Parameters.wheel_x_offset",
              "Placement.Base.y": bore_y,
              "Placement.Base.z": "Parameters.wheel_dia / 2"}, "Y",
             "Parameters.plate_w + 2"),
            ("Parameters.axle_bore",
             {"Placement.Base.x": "Parameters.pv_boss_x",
              "Placement.Base.y": bore_y,
              "Placement.Base.z": "Parameters.pv_boss_z"}, "Y",
             "Parameters.plate_w + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.chassis_length / 2"
                                  " - Parameters.imount_l / 2 - 4",
              "Placement.Base.y": bore_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.imount_h / 2"}, "Y",
             "Parameters.plate_w + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.chassis_length / 2 - 4",
              "Placement.Base.y": bore_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.imount_h / 2"}, "Y",
             "Parameters.plate_w + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.pv_boss_x"
                                  " - Parameters.servo_l / 2 - 15 + 8",
              "Placement.Base.y": bore_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.servo_h + 2"}, "Y",
             "Parameters.plate_w + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.pv_boss_x"
                                  " - Parameters.servo_l / 2 - 15 + 32",
              "Placement.Base.y": bore_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.servo_h + 2"}, "Y",
             "Parameters.plate_w + 2"),
        ]
        ck = pk.bored_plate(
            doc, name, "%s_cheek_plate_160x120x10_bored_UNVERIFIED" % name,
            "UNVERIFIED - intake cheek plate (roller + shaft + pivot "
            "bores, bolt pair, rim chamfer)",
            {"Length": "Parameters.intake_depth",
             "Width": "Parameters.plate_w",
             "Height": "Parameters.intake_height"},
            {"Placement.Base.x":
                 "Parameters.start_cube / 2 - Parameters.intake_depth",
             "Placement.Base.y": cheek_y},
            bores=bores,
            chamfer_l=pk.pval(sheet, "wall_chamfer"),
            chamfer_pred=pk.pred_not_axis((0, 1, 0)))
        mech.append(ck)

    # intake roller: bored tube + grip ribs, on a live REX shaft that
    # runs through the cheek bores; bearing blocks on the cheek inners
    mr = pk.ribbed_roller(
        doc, "INTAKE_ROLLER",
        "INTAKE_ROLLER_O30x306_ribbed_tube_8mmREX_UNVERIFIED",
        "UNVERIFIED - intake roller tube + ribs on live shaft",
        "Parameters.roller_dia",
        "Parameters.intake_width - 2 * Parameters.plate_w - 2",
        "Parameters.bore_dia",
        {"Placement.Base.x": roller_cx,
         "Placement.Base.y":
             "-(Parameters.intake_width - 2 * Parameters.plate_w"
             " - 2) / 2",
         "Placement.Base.z": roller_cz},
        center={"x": roller_cx, "z": roller_cz},
        ribs={"count": int(pk.pval(sheet, "rib_count")),
              "w": "Parameters.rib_w", "h": "Parameters.rib_h",
              "inset": "Parameters.rib_inset"})
    mech.append(mr)
    rs = pk.shaft(doc, "INTAKE_ROLLER_SHAFT",
                  "INTAKE_ROLLER_SHAFT_O8x336_REX_VENDOR-PENDING",
                  "VENDOR-PENDING - goBILDA 8mm REX roller shaft",
                  "Parameters.shaft_dia", "Parameters.intake_width + 10",
                  {"Placement.Base.x": roller_cx,
                   "Placement.Base.y":
                       "-(Parameters.intake_width + 10) / 2",
                   "Placement.Base.z": roller_cz}, "Y")
    mech.append(rs)
    for name, sgn in (("INTAKE_BEARING_L", 1), ("INTAKE_BEARING_R", -1)):
        by = ("Parameters.intake_width / 2 - Parameters.plate_w"
              " - Parameters.bear_t" if sgn > 0 else
              "-Parameters.intake_width / 2 + Parameters.plate_w")
        brg = pk.bearing_block(
            doc, name,
            "%s_bearing_26x26x6_bore8.4_UNVERIFIED" % name,
            "UNVERIFIED - roller bearing block on cheek inner face",
            "Parameters.bear_w", "Parameters.bear_t",
            "Parameters.bear_h", "Parameters.bear_bore",
            {"Placement.Base.x":
                 "(%s) - Parameters.bear_w / 2" % roller_cx,
             "Placement.Base.y": by,
             "Placement.Base.z":
                 "(%s) - Parameters.bear_h / 2" % roller_cz},
            "Y", "Parameters.bear_bolt_d", "Parameters.bear_bolt_off")
        mech.append(brg)

    # pivot bosses: bored rings on cheek inner faces; stub axles seat
    # the cheek on them (stubs stay out of the ball path)
    for name, sgn in (("PIVOT_MOUNT_L", 1), ("PIVOT_MOUNT_R", -1)):
        by = ("Parameters.intake_width / 2 - Parameters.plate_w"
              " - Parameters.pv_boss_len" if sgn > 0 else
              "-Parameters.intake_width / 2 + Parameters.plate_w")
        boss = pk.bore_cyl(
            doc, name, "%s_pivot_boss_O24x20_bore13_UNVERIFIED" % name,
            "UNVERIFIED - intake pivot boss ring on cheek inner face",
            "Parameters.pv_boss_dia", "Parameters.pv_boss_len",
            "Parameters.axle_bore",
            {"Placement.Base.x": "Parameters.pv_boss_x",
             "Placement.Base.y": by,
             "Placement.Base.z": "Parameters.pv_boss_z"}, "Y")
        mech.append(boss)

    # stub axles seat through the cheek bores into the boss bores;
    # tips stay 2mm shy of the cheek outer faces (clear of wheels) and
    # never cross the mouth (ball path stays open)
    for name, sgn in (("INTAKE_AXLE_L", 1), ("INTAKE_AXLE_R", -1)):
        ay = ("Parameters.intake_width / 2 - Parameters.plate_w"
              " - Parameters.pv_boss_len / 2" if sgn > 0 else
              "-(Parameters.intake_width / 2) + 2")
        st = pk.shaft(
            doc, name, "%s_pivot_stub_axle_O12x18_UNVERIFIED" % name,
            "UNVERIFIED - pivot stub axle through cheek bore into boss",
            "Parameters.intake_axle_dia",
            "Parameters.plate_w + Parameters.pv_boss_len / 2 - 2",
            {"Placement.Base.x": "Parameters.pv_boss_x",
             "Placement.Base.y": ay,
             "Placement.Base.z": "Parameters.pv_boss_z"}, "Y")
        mech.append(st)

    # pivot servo inside the rail mouth pocket: rests on the bottom
    # flange top (z=rail_wall), bolted to the cheek inner face; clamp
    # strap plate on the inner face over the servo top
    sm = pk.box(doc, "INTAKE_MOTOR",
                "INTAKE_MOTOR_servo_40x20x36_VENDOR-PENDING",
                "VENDOR-PENDING - REV SRS-class intake pivot servo",
                {"Length": "Parameters.servo_l",
                 "Width": "Parameters.servo_w",
                 "Height": "Parameters.servo_h"},
                {"Placement.Base.x":
                     "Parameters.pv_boss_x - Parameters.servo_l / 2 - 15",
                 "Placement.Base.y":
                     "Parameters.intake_width / 2 - Parameters.plate_w"
                     " - Parameters.servo_w",
                 "Placement.Base.z": "Parameters.rail_wall"})
    mech.append(sm)
    strap_y = ("Parameters.intake_width / 2 - Parameters.plate_w"
               " - Parameters.imount_t")
    strap_bolt_y = ("Parameters.intake_width / 2 - Parameters.plate_w"
                    " - Parameters.imount_t - 1")
    mk = pk.bored_plate(
        doc, "INTAKE_MOTOR_BRKT",
        "INTAKE_MOTOR_BRKT_clamp_strap_40x4_UNVERIFIED",
        "UNVERIFIED - servo clamp strap on cheek inner face",
        {"Length": "Parameters.servo_l", "Width": "Parameters.imount_t",
         "Height": "4"},
        {"Placement.Base.x":
             "Parameters.pv_boss_x - Parameters.servo_l / 2 - 15",
         "Placement.Base.y": strap_y,
         "Placement.Base.z":
             "Parameters.rail_wall + Parameters.servo_h"},
        bores=[
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.pv_boss_x"
                                  " - Parameters.servo_l / 2 - 15 + 8",
              "Placement.Base.y": strap_bolt_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.servo_h + 2"}, "Y",
             "Parameters.imount_t + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.pv_boss_x"
                                  " - Parameters.servo_l / 2 - 15 + 32",
              "Placement.Base.y": strap_bolt_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.servo_h + 2"}, "Y",
             "Parameters.imount_t + 2")])
    mech.append(mk)

    # intake mouth sill: chamfered lip plate seated on the rail bottom
    # flange inside the mouth
    lip = pk.bored_plate(
        doc, "INTAKE_LIP",
        "INTAKE_LIP_sill_22x306x3_UNVERIFIED",
        "UNVERIFIED - intake mouth sill plate, chamfered edges",
        {"Length": "Parameters.lip_sill_d",
         "Width": "Parameters.intake_width - 2 * Parameters.plate_w",
         "Height": "Parameters.pan_thk"},
        {"Placement.Base.x":
             "Parameters.start_cube / 2 - Parameters.lip_sill_d",
         "Placement.Base.y":
             "-(Parameters.intake_width - 2 * Parameters.plate_w) / 2",
         "Placement.Base.z": "Parameters.rail_wall"},
        bores=(), chamfer_l=pk.pval(sheet, "wall_chamfer"),
        chamfer_pred=pk.pred_axis((0, 1, 0)))
    mech.append(lip)

    # intake mounts: L-brackets bolted through the cheek, foot across
    # the rail mouth onto the web face, leg on the cheek inner face
    for name, sgn in (("INTAKE_MOUNT_L", 1), ("INTAKE_MOUNT_R", -1)):
        foot_y = (("(%s + Parameters.rail_wall)" % sy_rail)
                  if sgn > 0 else
                  "-Parameters.intake_width / 2 + Parameters.plate_w")
        foot_w = ("Parameters.intake_width / 2 - Parameters.plate_w"
                  " - (%s + Parameters.rail_wall)" % sy_rail)
        leg_y = ("Parameters.intake_width / 2 - Parameters.plate_w"
                 " - Parameters.imount_t" if sgn > 0 else
                 "-Parameters.intake_width / 2 + Parameters.plate_w")
        bolt_y = ("Parameters.intake_width / 2 - Parameters.plate_w"
                  " - Parameters.imount_t - 1" if sgn > 0 else
                  "-Parameters.intake_width / 2 + Parameters.plate_w - 1")
        bolts = [
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.chassis_length / 2"
                                  " - Parameters.imount_l / 2 - 4",
              "Placement.Base.y": bolt_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.imount_h / 2"}, "Y",
             "Parameters.imount_t + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "Parameters.chassis_length / 2 - 4",
              "Placement.Base.y": bolt_y,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.imount_h / 2"}, "Y",
             "Parameters.imount_t + 2"),
        ]
        br = pk.l_bracket(
            doc, name, "%s_L_bracket_20x34.5x20_UNVERIFIED" % name,
            "UNVERIFIED - intake mount L-bracket (cheek bolts + rail "
            "flange foot)",
            {"Length": "Parameters.imount_l",
             "Width": "Parameters.imount_t",
             "Height": "Parameters.imount_h"},
            {"Placement.Base.x":
                 "Parameters.chassis_length / 2 - Parameters.imount_l",
             "Placement.Base.y": leg_y,
             "Placement.Base.z": "Parameters.rail_wall"},
            {"Length": "Parameters.imount_l",
             "Width": foot_w,
             "Height": "Parameters.imount_t"},
            {"Placement.Base.x":
                 "Parameters.chassis_length / 2 - Parameters.imount_l",
             "Placement.Base.y": foot_y,
             "Placement.Base.z": "Parameters.rail_wall"},
            bolts=bolts)
        mech.append(br)

    # transfer channel: sheet floor + walls, L-saddles to the pan
    chan_len = ("Parameters.start_cube / 2 - Parameters.intake_depth"
                " - Parameters.channel_x0 - 10")
    cf = pk.bored_plate(
        doc, "CHANNEL_FLOOR",
        "CHANNEL_FLOOR_214x110x3_sheet_UNVERIFIED",
        "UNVERIFIED - transfer channel floor sheet",
        {"Length": chan_len, "Width": "Parameters.channel_w",
         "Height": "Parameters.chan_floor_t"},
        {"Placement.Base.x": "Parameters.channel_x0",
         "Placement.Base.y": "-Parameters.channel_w / 2",
         "Placement.Base.z": "Parameters.channel_z"},
        bores=(), chamfer_l=pk.pval(sheet, "wall_chamfer"),
        chamfer_pred=pk.pred_axis((0, 0, 1)))
    mech.append(cf)
    # wall outer faces at +-53.5 clear the drive-motor inner faces; the
    # interior lane stays 101mm > O91 Nectar
    for name, sgn in (("CHANNEL_WALL_L", 1), ("CHANNEL_WALL_R", -1)):
        wy = ("Parameters.channel_w / 2 - Parameters.chan_wall_t - 1.5"
              if sgn > 0 else "-Parameters.channel_w / 2 + 1.5")
        by = ("Parameters.channel_w / 2 - Parameters.chan_wall_t - 2.5"
              if sgn > 0 else "-Parameters.channel_w / 2 + 0.5")
        wall_bores = [
            ("Parameters.bush_bore",
             {"Placement.Base.x": "Parameters.channel_x0 + 6",
              "Placement.Base.y": by,
              "Placement.Base.z": "Parameters.channel_z"
                                  " + Parameters.channel_h - 5"}, "Y",
             "Parameters.chan_wall_t + 2")]
        if sgn > 0:
            wall_bores += [
                ("Parameters.mbolt_d",
                 {"Placement.Base.x": "Parameters.channel_x0 + 6"
                                      " + Parameters.bush_dia / 2 + 9",
                  "Placement.Base.y": "Parameters.channel_w / 2"
                                      " - Parameters.chan_wall_t - 2.5",
                  "Placement.Base.z": "Parameters.channel_z"
                                      " + Parameters.channel_h"
                                      " - Parameters.servo_h + 6"}, "Y",
                 "Parameters.chan_wall_t + 2"),
                ("Parameters.mbolt_d",
                 {"Placement.Base.x": "Parameters.channel_x0 + 6"
                                      " + Parameters.bush_dia / 2"
                                      " + Parameters.servo_l - 4",
                  "Placement.Base.y": "Parameters.channel_w / 2"
                                      " - Parameters.chan_wall_t - 2.5",
                  "Placement.Base.z": "Parameters.channel_z"
                                      " + Parameters.channel_h - 6"}, "Y",
                 "Parameters.chan_wall_t + 2")]
        cw = pk.bored_plate(
            doc, name, "%s_wall_214x110x3_bored_UNVERIFIED" % name,
            "UNVERIFIED - transfer channel wall (hinge bore + chamfer)",
            {"Length": chan_len,
             "Width": "Parameters.chan_wall_t",
             "Height": "Parameters.channel_h"},
            {"Placement.Base.x": "Parameters.channel_x0",
             "Placement.Base.y": wy,
             "Placement.Base.z": "Parameters.channel_z"},
            bores=wall_bores,
            chamfer_l=pk.pval(sheet, "wall_chamfer"),
            chamfer_pred=pk.pred_axis((1, 0, 0)))
        mech.append(cw)

    # saddle L-brackets: riser under floor, foot on pan, 2 bolt holes
    for name, x0 in (("CHANNEL_SUPP_F",
                      "Parameters.start_cube / 2 - Parameters.intake_depth"
                      " - Parameters.csupp_w - 15"),
                     ("CHANNEL_SUPP_B",
                      "Parameters.channel_x0 + Parameters.csupp_w")):
        sadd_w = ("Parameters.channel_w - 2 * Parameters.chan_wall_t"
                  " - 7")
        bolts = [
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "(%s) + Parameters.csupp_w / 2 - 2"
                                  % x0,
              "Placement.Base.y": "-(%s) / 2 + 8" % sadd_w,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.pan_thk - 1"}, "Z",
             "Parameters.csupp_t + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "(%s) + Parameters.csupp_w / 2 - 2"
                                  % x0,
              "Placement.Base.y": "(%s) / 2 - 8" % sadd_w,
              "Placement.Base.z": "Parameters.rail_wall"
                                  " + Parameters.pan_thk - 1"}, "Z",
             "Parameters.csupp_t + 2")]
        sp = pk.l_bracket(
            doc, name, "%s_saddle_L_16x100x4.5_UNVERIFIED" % name,
            "UNVERIFIED - channel saddle L-bracket to belly pan",
            {"Length": "Parameters.csupp_w", "Width": sadd_w,
             "Height": "Parameters.channel_z - Parameters.rail_wall"
                       " - Parameters.pan_thk - Parameters.csupp_t"},
            {"Placement.Base.x": x0,
             "Placement.Base.y": "-(%s) / 2" % sadd_w,
             "Placement.Base.z": "Parameters.rail_wall"
                                 " + Parameters.pan_thk"
                                 " + Parameters.csupp_t"},
            {"Length": "Parameters.csupp_w + 6", "Width": sadd_w,
             "Height": "Parameters.csupp_t"},
            {"Placement.Base.x": "(%s) - 3" % x0,
             "Placement.Base.y": "-(%s) / 2" % sadd_w,
             "Placement.Base.z": "Parameters.rail_wall"
                                 " + Parameters.pan_thk"},
            bolts=bolts)
        mech.append(sp)

    # diverter: bored paddle on a hinge axle through wall bushings,
    # servo on the L wall outer face, horn on the axle end
    pd = pk.bored_plate(
        doc, "DIVERTER_PADDLE",
        "DIVERTER_PADDLE_8x100x60_hinged_UNVERIFIED",
        "UNVERIFIED - diverter paddle hinged on axle",
        {"Length": "Parameters.plate_thk",
         "Width": "Parameters.channel_w - 2 * Parameters.chan_wall_t - 7",
         "Height": "Parameters.div_h"},
        {"Placement.Base.x": "Parameters.channel_x0 + 2",
         "Placement.Base.y":
             "-(Parameters.channel_w - 2 * Parameters.chan_wall_t - 7)"
             " / 2",
         "Placement.Base.z":
             "Parameters.channel_z + Parameters.channel_h"
             " - Parameters.div_h - 3"},
        bores=[("Parameters.paddle_bore",
                {"Placement.Base.x": "Parameters.channel_x0 + 6",
                 "Placement.Base.y":
                     "-(Parameters.channel_w - 2 * Parameters.chan_wall_t"
                     " - 7) / 2 - 1",
                 "Placement.Base.z": "Parameters.channel_z"
                                     " + Parameters.channel_h - 5"}, "Y",
                "Parameters.channel_w")]
        )
    mech.append(pd)

    da = pk.shaft(
        doc, "DIVERTER_AXLE",
        "DIVERTER_AXLE_O6x123_hinge_UNVERIFIED",
        "UNVERIFIED - diverter hinge shaft through wall bushings",
        "Parameters.daxle_dia",
        "Parameters.channel_w + 2 * Parameters.bush_t + 5",
        {"Placement.Base.x": "Parameters.channel_x0 + 6",
         "Placement.Base.y":
             "-(Parameters.channel_w + 2 * Parameters.bush_t + 5) / 2",
         "Placement.Base.z": "Parameters.channel_z"
                             " + Parameters.channel_h - 5"}, "Y")
    mech.append(da)
    for name, sgn in (("DIVERTER_BUSH_L", 1), ("DIVERTER_BUSH_R", -1)):
        by = ("Parameters.channel_w / 2 - 1.5" if sgn > 0 else
              "-Parameters.channel_w / 2 + 1.5 - Parameters.bush_t")
        bs = pk.bore_cyl(
            doc, name, "%s_bushing_O10x4_bore6.4_UNVERIFIED" % name,
            "UNVERIFIED - diverter wall bushing",
            "Parameters.bush_dia", "Parameters.bush_t",
            "Parameters.bush_bore",
            {"Placement.Base.x": "Parameters.channel_x0 + 6",
             "Placement.Base.y": by,
             "Placement.Base.z": "Parameters.channel_z"
                                 " + Parameters.channel_h - 5"}, "Y")
        mech.append(bs)
    sv = pk.box(doc, "DIVERTER_SERVO",
                "DIVERTER_SERVO_40.5x20x36_wall_VENDOR-PENDING",
                "VENDOR-PENDING - REV SRS-class diverter servo",
                {"Length": "Parameters.servo_l",
                 "Width": "Parameters.servo_w",
                 "Height": "Parameters.servo_h"},
                {"Placement.Base.x":
                     "Parameters.channel_x0 + 6 + Parameters.bush_dia"
                     " / 2 - 1.7",
                 "Placement.Base.y": "Parameters.channel_w / 2 - 1.5",
                 "Placement.Base.z":
                     "Parameters.channel_z + Parameters.channel_h"
                     " - Parameters.servo_h"})
    mech.append(sv)
    dh = pk.box(doc, "DIVERTER_HORN",
                "DIVERTER_HORN_30x10x20_axle_end_UNVERIFIED",
                "UNVERIFIED - diverter horn on the hinge axle end",
                {"Length": "Parameters.horn_l",
                 "Width": "Parameters.horn_w",
                 "Height": "Parameters.horn_h"},
                {"Placement.Base.x":
                     "Parameters.channel_x0 + 6 - Parameters.horn_l + 5",
                 "Placement.Base.y": "Parameters.channel_w / 2 - 1.5"
                                     " + Parameters.bush_t + 1",
                 "Placement.Base.z":
                     "Parameters.channel_z + Parameters.channel_h - 5"
                     " - Parameters.horn_h"})
    mech.append(dh)

    # reserve volumes for the sprint-02 probes (excluded VOL_ class)
    vc = pk.box(doc, "VOL_CHANNEL_CLEAR",
                "VOL_CHANNEL_CLEAR_214x101x107_UNVERIFIED",
                "UNVERIFIED - channel interior clear-section probe",
                {"Length": chan_len,
                 "Width": "Parameters.channel_w"
                          " - 2 * Parameters.chan_wall_t - 3",
                 "Height": "Parameters.channel_h"
                           " - Parameters.chan_floor_t"},
                {"Placement.Base.x": "Parameters.channel_x0",
                 "Placement.Base.y":
                     "-(Parameters.channel_w"
                     " - 2 * Parameters.chan_wall_t - 3) / 2",
                 "Placement.Base.z": "Parameters.channel_z"
                                     " + Parameters.chan_floor_t"})
    mech.append(vc)
    vb = pk.cyl(doc, "VOL_BALL_PATH",
                "VOL_BALL_PATH_O91x378_lane_VERIFIED",
                "VERIFIED - O91 Nectar ball path probe (sec 9.8); "
                "declared grip/mount intersections only",
                {"Radius": "Parameters.nectar_dia / 2",
                 "Height": "Parameters.start_cube / 2"
                           " - Parameters.channel_x0 - 10.2"},
                {"Placement.Base.x": "Parameters.channel_x0 + 10",
                 "Placement.Base.y": "0",
                 "Placement.Base.z": "Parameters.channel_z"
                                     " + Parameters.channel_h / 2"},
                pk.axis_rot("X"))
    mech.append(vb)

    # shooter rep: rear plate + hood + floor + side plates; flywheels and
    # stub shafts live between the side plates (coherence placeholders)
    sb = pk.box(doc, "MECH_SHOOTER_BODY",
                "MECH_SHOOTER_rear_plate_UNVERIFIED",
                "UNVERIFIED - shooter housing rear plate",
                {"Length": "Parameters.plate_thk",
                 "Width": "Parameters.shooter_w - 20",
                 "Height": "Parameters.shooter_h - 40"},
                {"Placement.Base.x": "-Parameters.shooter_l + 10",
                 "Placement.Base.y": "-(Parameters.shooter_w - 20) / 2",
                 "Placement.Base.z": "Parameters.shooter_z + 10"})
    mech.append(sb)

    sh = pk.box(doc, "MECH_SHOOTER_HOOD",
                "MECH_SHOOTER_hood_plate_UNVERIFIED",
                "UNVERIFIED - shooter hood plate",
                {"Length": "Parameters.shooter_l - 20",
                 "Width": "Parameters.shooter_w - 20",
                 "Height": "Parameters.plate_thk"},
                {"Placement.Base.x": "-Parameters.shooter_l + 10",
                 "Placement.Base.y": "-(Parameters.shooter_w - 20) / 2",
                 "Placement.Base.z":
                     "Parameters.shooter_z + Parameters.shooter_h - 30"})
    mech.append(sh)

    sf = pk.plate(
        doc, "SHOOTER_FLOOR", "SHOOTER_FLOOR_deck_plate_UNVERIFIED",
        "UNVERIFIED - shooter floor plate on support posts",
        {"Length": "Parameters.shooter_l - 20",
         "Width": "Parameters.shooter_w - 20",
         "Height": "Parameters.sfloor_thk"},
        {"Placement.Base.x": "-Parameters.shooter_l + 10",
         "Placement.Base.y": "-(Parameters.shooter_w - 20) / 2",
         "Placement.Base.z": "Parameters.shooter_z"},
        fillet_r=pk.pval(sheet, "plate_fillet"),
        edge_pred=pk.pred_axis((0, 0, 1)))
    mech.append(sf)

    for name, sgn in (("SHOOTER_SIDE_L", 1), ("SHOOTER_SIDE_R", -1)):
        sp = pk.plate(
            doc, name, "%s_wall_UNVERIFIED" % name,
            "UNVERIFIED - shooter side wall carrying stub shafts",
            {"Length": "Parameters.shooter_l - 20 - Parameters.plate_thk",
             "Width": "Parameters.sside_thk",
             "Height": "Parameters.shooter_h - 40"},
            {"Placement.Base.x": "-Parameters.shooter_l + 10"
                                 " + Parameters.plate_thk",
             "Placement.Base.y":
                 "(Parameters.shooter_w - 20) / 2 - Parameters.sside_thk"
                 if sgn > 0 else "-(Parameters.shooter_w - 20) / 2",
             "Placement.Base.z": "Parameters.shooter_z + 10"},
            fillet_r=2.0,
            edge_pred=pk.pred_axis((0, 0, 1)))
        mech.append(sp)

    for name, sgn in (("MECH_FLYWHEEL_L", 1), ("MECH_FLYWHEEL_R", -1)):
        fw = pk.cyl(doc, name,
                    "%s_72x30_goBILDA-style_VENDOR-PENDING" % name,
                    "UNVERIFIED - VENDOR-PENDING (goBILDA-style flywheel)",
                    {"Radius": "Parameters.flywheel_dia / 2",
                     "Height": "Parameters.flywheel_w"},
                    {"Placement.Base.x": "Parameters.flywheel_x",
                     "Placement.Base.y":
                         "Parameters.bore / 2" if sgn > 0 else
                         "-Parameters.bore / 2 - Parameters.flywheel_w",
                     "Placement.Base.z":
                         "Parameters.shooter_z + Parameters.shooter_h / 2"
                         " + 55"},
                    pk.axis_rot("Y"))
        mech.append(fw)

    mm = pk.box(doc, "MECH_LIFTER_STOWED",
                "MECH_LIFTER_stowed_region_UNVERIFIED",
                "UNVERIFIED - collapsed lifter region within the reserve",
                {"Length": "Parameters.mast_w - 20",
                 "Width": "Parameters.mast_w - 20",
                 "Height": "Parameters.lifter_stow_h"},
                {"Placement.Base.x":
                     "Parameters.lifter_stow_x + Parameters.lifter_stow_l"
                     " - Parameters.mast_w + 20",
                 "Placement.Base.y": "-(Parameters.mast_w - 20) / 2",
                 "Placement.Base.z": "Parameters.lifter_stow_z"})
    mech.append(mm)

    stage_defs = (
        ("MECH_STAGE_1", "stage1_w", "Parameters.lifter_dep_z0",
         "Parameters.stage1_z1"),
        ("MECH_STAGE_2", "stage2_w", "Parameters.stage2_z0",
         "Parameters.stage2_z1"),
        ("MECH_STAGE_3", "stage3_w", "Parameters.stage3_z0",
         "Parameters.stage3_z1"),
    )
    for name, walias, z0expr, z1expr in stage_defs:
        s = pk.box(doc, name, "%s_deployed_section_UNVERIFIED" % name,
                   "UNVERIFIED - deployed cascade stage placeholder",
                   {"Length": "Parameters." + walias,
                    "Width": "Parameters." + walias,
                    "Height": "(%s) - (%s)" % (z1expr, z0expr)},
                   {"Placement.Base.x":
                        "Parameters.lifter_stow_x + Parameters.lifter_stow_l"
                        " / 2 - Parameters.%s / 2" % walias,
                    "Placement.Base.y": "-Parameters.%s / 2" % walias,
                    "Placement.Base.z": z0expr})
        mech.append(s)

    car = pk.box(doc, "MECH_CARRIAGE",
                 "MECH_CARRIAGE_stage3_top_UNVERIFIED",
                 "UNVERIFIED - carriage plate on inner stage",
                 {"Length": "Parameters.carriage_w",
                  "Width": "Parameters.carriage_w",
                  "Height": "Parameters.carriage_h"},
                 {"Placement.Base.x":
                      "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                      " - Parameters.carriage_w / 2",
                  "Placement.Base.y": "-Parameters.carriage_w / 2",
                  "Placement.Base.z": "Parameters.stage3_z1"})
    mech.append(car)

    crd = pk.box(doc, "MECH_CRADLE",
                 "MECH_CRADLE_nectar_cup_UNVERIFIED",
                 "UNVERIFIED - Nectar cradle placeholder",
                 {"Length": "Parameters.cradle_w",
                  "Width": "Parameters.cradle_w",
                  "Height": "Parameters.cradle_h"},
                 {"Placement.Base.x":
                      "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                      " - Parameters.cradle_w / 2",
                  "Placement.Base.y": "-Parameters.cradle_w / 2",
                  # +0.05 shim: carriage top (stage3_z1+carriage_h=600)
                  # and cradle base were an equal-area coincident face
                  "Placement.Base.z": "Parameters.cradle_z + 0.05"})
    mech.append(crd)

    # ---------------- secondary mechanism detail --------------------
    # (pivot bosses, diverter horn, and intake axles moved into the
    # sprint-02 intake/transfer component block above)
    detail = []
    for name, sgn in (("STUB_SHAFT_L", 1), ("STUB_SHAFT_R", -1)):
        ss = pk.cyl(doc, name,
                    "%s_8mmREX_flywheel_shaft_VENDOR-PENDING" % name,
                    "VENDOR-PENDING - goBILDA 8mm REX stub shaft",
                    {"Radius": "Parameters.stub_dia / 2",
                     "Height": "Parameters.stub_len"},
                    {"Placement.Base.x": "Parameters.flywheel_x",
                     "Placement.Base.y":
                         "Parameters.bore / 2 - (Parameters.stub_len"
                         " - Parameters.flywheel_w) / 2" if sgn > 0 else
                         "-Parameters.bore / 2 - Parameters.flywheel_w"
                         " - (Parameters.stub_len - Parameters.flywheel_w) / 2",
                     "Placement.Base.z":
                         "Parameters.shooter_z + Parameters.shooter_h / 2"
                         " + 55"},
                    pk.axis_rot("Y"))
        detail.append(ss)

    for name, sgn in (("STAGE_GUIDE_L", 1), ("STAGE_GUIDE_R", -1)):
        gd = pk.box(doc, name, "%s_cascade_guide_block_UNVERIFIED" % name,
                    "UNVERIFIED - lifter stage guide block",
                    {"Length": "Parameters.guide_w",
                     "Width": "Parameters.guide_w",
                     "Height": "Parameters.guide_l"},
                    {"Placement.Base.x":
                         "Parameters.lifter_stow_x + Parameters.lifter_stow_l"
                         " / 2 - Parameters.guide_w / 2",
                     "Placement.Base.y":
                         "Parameters.stage1_w / 2 - Parameters.guide_w / 2"
                         if sgn > 0 else
                         "-Parameters.stage1_w / 2 - Parameters.guide_w / 2",
                     "Placement.Base.z":
                         "Parameters.stage1_z1 - Parameters.guide_l * 3 / 4"})
        detail.append(gd)

    cl = pk.box(doc, "CRADLE_LIP",
                "CRADLE_LIP_retention_rim_UNVERIFIED",
                "UNVERIFIED - cradle retention lip",
                {"Length": "Parameters.lip_t",
                 "Width": "Parameters.cradle_w",
                 "Height": "Parameters.lip_h"},
                {"Placement.Base.x":
                     "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                     " + Parameters.cradle_w / 2 - Parameters.lip_t",
                 "Placement.Base.y": "-Parameters.cradle_w / 2",
                 "Placement.Base.z":
                     "Parameters.cradle_z + Parameters.cradle_h"
                     " - Parameters.lip_h"})
    detail.append(cl)

    for name, sgn in (("ELEC_RAIL_L", 1), ("ELEC_RAIL_R", -1)):
        er = pk.box(doc, name, "%s_hub_mount_rail_UNVERIFIED" % name,
                    "UNVERIFIED - electronics mounting rail",
                    {"Length": "Parameters.erail_l",
                     "Width": "Parameters.erail_w",
                     "Height": "Parameters.erail_h"},
                    {"Placement.Base.x":
                         "Parameters.elec_x + (Parameters.elec_l"
                         " - Parameters.erail_l) / 2",
                     "Placement.Base.y":
                         "Parameters.elec_y + 10" if sgn > 0 else
                         "Parameters.elec_y + Parameters.elec_w"
                         " - Parameters.erail_w - 10",
                     "Placement.Base.z": "Parameters.rail_wall"
                                         " + Parameters.pan_thk"})
        detail.append(er)

    # shooter uprights: rear deck top to shooter floor plate
    for name, sgn in (("POST_SHOOTER_L", 1), ("POST_SHOOTER_R", -1)):
        ps = pk.box(doc, name, "%s_shooter_upright_UNVERIFIED" % name,
                    "UNVERIFIED - shooter support post to rear deck",
                    {"Length": "Parameters.post_w",
                     "Width": "Parameters.post_w",
                     "Height": "Parameters.shooter_z - Parameters.rail_size"
                               " + Parameters.rail_wall"},
                    {"Placement.Base.x":
                         "-Parameters.shooter_l / 2 - Parameters.post_w / 2",
                     "Placement.Base.y":
                         "Parameters.shooter_w / 2 - Parameters.post_w - 10"
                         if sgn > 0 else "-Parameters.shooter_w / 2 + 10",
                     "Placement.Base.z": "Parameters.rail_size"
                                         " - Parameters.rail_wall"})
        detail.append(ps)

    # lifter pedestal on the belly pan + base plate under the mast
    lp = pk.box(doc, "LIFTER_PED", "LIFTER_PED_mast_pedestal_UNVERIFIED",
                "UNVERIFIED - pedestal tying lifter mast to belly pan",
                {"Length": "Parameters.lifter_ped_w",
                 "Width": "Parameters.lifter_ped_w",
                 "Height": "Parameters.lifter_dep_z0 - Parameters.plate_thk"
                           " - Parameters.rail_wall - Parameters.pan_thk"},
                {"Placement.Base.x":
                     "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                     " - Parameters.lifter_ped_w / 2",
                 "Placement.Base.y": "-Parameters.lifter_ped_w / 2",
                 "Placement.Base.z": "Parameters.rail_wall"
                                     " + Parameters.pan_thk"})
    detail.append(lp)

    lb = pk.box(doc, "LIFTER_BASE", "LIFTER_BASE_120x120_plate_UNVERIFIED",
                "UNVERIFIED - lifter base mounting plate",
                {"Length": "Parameters.lifter_base_w",
                 "Width": "Parameters.lifter_base_w",
                 "Height": "Parameters.plate_thk"},
                {"Placement.Base.x":
                     "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                     " - Parameters.lifter_base_w / 2",
                 "Placement.Base.y": "-Parameters.lifter_base_w / 2",
                 "Placement.Base.z":
                     "Parameters.lifter_dep_z0 - Parameters.plate_thk"})
    detail.append(lb)

    rh = pk.box(doc, "REF_HIVE",
                "REF_HIVE_aim_marker_position_UNVERIFIED",
                "UNVERIFIED - aiming reference toward Hive cell (sec 9.6); "
                "position assumed, not a field model",
                {"Length": "Parameters.ref_size",
                 "Width": "Parameters.ref_size",
                 "Height": "Parameters.ref_size"},
                {"Placement.Base.x":
                     "Parameters.start_cube / 2 + Parameters.hive_aim_dist",
                 "Placement.Base.y": "-Parameters.ref_size / 2",
                 "Placement.Base.z":
                     "Parameters.hive_aim_z - Parameters.ref_size / 2"})
    mech.append(rh)

    rf = pk.box(doc, "REF_FLOWER",
                "REF_FLOWER_aim_marker_z546_sec9.7",
                "Z VERIFIED - sec 9.7 flower top height; XY position "
                "UNVERIFIED - aiming reference, not a field model",
                {"Length": "Parameters.flower_aim_w",
                 "Width": "Parameters.flower_aim_w",
                 "Height": "Parameters.ref_size / 6"},
                {"Placement.Base.x": "Parameters.flower_aim_x",
                 "Placement.Base.y": "-Parameters.flower_aim_w / 2",
                 "Placement.Base.z":
                     "Parameters.flower_aim_z - Parameters.ref_size / 12"})
    mech.append(rf)

    # ---------------- subsystem grouping -----------------------------
    GROUP_MAP = (
        ("Envelopes", ("ENV_", "VOL_", "REF_")),
        ("Drivebase", ("WHEEL_", "ROLLER_", "MOTOR_", "MOUNT_MOTOR_",
                       "BEARING_", "SHAFT_", "FRAME_", "BELLY_PAN",
                       "REAR_DECK")),
        ("Intake", ("INTAKE_", "PIVOT_MOUNT")),
        ("Transfer", ("CHANNEL_", "DIVERTER_")),
        ("Shooter", ("MECH_SHOOTER", "MECH_FLYWHEEL", "STUB_SHAFT",
                     "POST_SHOOTER", "SHOOTER_FLOOR", "SHOOTER_SIDE")),
        ("Lifter", ("MECH_LIFTER", "MECH_STAGE", "MECH_CARRIAGE",
                    "MECH_CRADLE", "STAGE_GUIDE", "CRADLE_LIP",
                    "LIFTER_BASE", "LIFTER_PED")),
        ("Electronics", ("BATTERY", "ELECTRONICS", "ELEC_RAIL")),
        ("Tools", (pk.TOOL_PREFIX,)),
    )
    groups = {}
    for gname, _pf in GROUP_MAP:
        g = doc.addObject("App::Part", gname)
        g.Label = "GRP_%s" % gname.lower()
        groups[gname] = g
        pk.group_add(robot, g)
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o.Name.startswith("AXIS_") \
                or o.TypeId in ("App::Part", "App::Origin"):
            continue
        if o.getParentGeoFeatureGroup() is not None:
            continue  # already owned (wheel-carrier children etc.)
        for gname, prefixes in GROUP_MAP:
            if o.Name.startswith(prefixes):
                pk.group_add(groups[gname], o)
                break
        else:
            pk.group_add(robot, o)
    for o in doc.Objects:
        if o.TypeId == "App::Part" and o.Name in ("Drivebase",):
            for wtag, *_ in WHEELS:
                pk.group_add(o, doc.getObject("WHEEL_ASSY_" + wtag))
    pk.group_add(coord, *axes)
    doc.recompute()

    bad = []
    nulls = []
    for o in doc.Objects:
        if not hasattr(o, "Shape"):
            continue
        if o.Shape.isNull():
            nulls.append(o.Name)
        elif not o.Shape.isValid():
            bad.append(o.Name)
    if nulls:
        print("BUILD: NULL shapes: %s" % nulls)
    solids = [o for o in doc.Objects
              if hasattr(o, "Shape") and not o.Shape.isNull()
              and o.Shape.Volume > 0
              and o.TypeId not in ("App::Part", "App::Origin")]
    print("BUILD: objects=%d solids=%d invalid=%s"
          % (len(doc.Objects), len(solids), bad or "none"))
    for o in doc.Objects:
        if hasattr(o, "Shape") and not o.Shape.isNull() \
                and o.Shape.Volume > 0 and \
                o.TypeId not in ("App::Part", "App::Origin"):
            bb = o.Shape.BoundBox
            print("BUILD: %-24s | %-48s | bbox (%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f)"
                  % (o.Name, o.Label, bb.XMin, bb.YMin, bb.ZMin,
                     bb.XMax, bb.YMax, bb.ZMax))
    if bad or nulls:
        raise RuntimeError("invalid=%s null=%s" % (bad or "none",
                                                 nulls or "none"))


def main():
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    archive_if_foreign()
    doc = App.newDocument(DOC_NAME)
    populate(doc)
    doc.saveAs(str(TARGET))
    for bak in TARGET.parent.glob(TARGET.stem + ".*.FCBak"):
        bak.unlink()  # FreeCAD backup sidecar; keep cad/ clean on re-runs
    print("BUILD: saved %s (%d bytes)" % (TARGET, TARGET.stat().st_size))
    print("BUILD: DONE")


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
