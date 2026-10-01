import FreeCAD as App
from pathlib import Path
ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
m = App.openDocument(str(ROOT/"cad/master_robot.FCStd"))
NAMES = """BOLT_YTR_0 BOLT_YTR_1 BOLT_YTR_2 BOLT_YTR_3 YAW_SERVO YAW_SHAFT YAW_TRAY
TURRET_DECK SCRW_YSV_0 SCRW_YSV_1 SCRW_YSV_2 SCRW_YSV_3
FLYWHEEL_R FLYWHEEL_L WIRE_CAM_USB WIRE_HOOD_SV WIRE_FLY_R WIRE_FLY_L NIP_BACKPLATE
BOLT_SC_L0 BOLT_SC_L1 BOLT_SC_R0 BOLT_SC_R1 LIFT_TOP_TIE LIFT_S1_TIE ROPE_GUIDE
BOLT_LTT_L0 BOLT_LTT_L1 BOLT_LTT_R0 BOLT_LTT_R1 STOP_COLLAR_L STOP_COLLAR_R
LIFT_PULLEY LIFT_S2_TIE BOLT_S2TIE_0 BOLT_S2TIE_1 BOLT_S2TIE_2 BOLT_S2TIE_3
LIFT_S1_BAR_L LIFT_S1_BAR_R LIFT_S2_BAR CRADLE_ARM SCRW_CARM_0 SCRW_CARM_1
BOLT_CARM_0 BOLT_CARM_1 SCRW_S1T_L0_0 SCRW_S1T_L0_1 SCRW_S1T_L1_0 SCRW_S1T_L1_1
SCRW_S1T_R0_0 SCRW_S1T_R0_1 SCRW_S1T_R1_0 SCRW_S1T_R1_1
LIFT_S2_TRUCK_0 LIFT_S2_TRUCK_1 BOLT_PORT_0 BOLT_PORT_1 BOLT_PORT_2 BOLT_PORT_3
LOAD_CHUTE PORT_FLANGE
NUT_LW_0 NUT_LW_1 NUT_LW_2 NUT_LW_3 BOLT_LW_0 BOLT_LW_1 BOLT_LW_2 BOLT_LW_3
LIFT_WINCH FRAME_RAIL_L DECK_L ELEC_SHELF
NUT_TWC_L_0 NUT_TWC_L_1 NUT_TWC_L_2 NUT_TWC_L_3 BOLT_TWC_L_0 BOLT_TWC_L_1 BOLT_TWC_L_2 BOLT_TWC_L_3
NUT_GUD_R3_0 BOLT_GUD_R3_0 TOWER_GUS_R3 TOWER_R
NUT_LRF_L1 BOLT_LRF_L1 NUT_LRF_R0 BOLT_LRF_R0 LIFT_RAIL_L LIFT_RAIL_R LIFT_BASE
CRADLE_COL_0 CRADLE_CUP LIFT_RAIL_R""".split()
for n in NAMES:
    o = m.getObject(n)
    if o is None or not hasattr(o,"Shape") or o.Shape.isNull():
        print("%-22s MISSING"%n); continue
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); b=s.BoundBox
    print("%-22s x %8.2f..%8.2f  y %8.2f..%8.2f  z %8.2f..%8.2f"%(
        n,b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))
# common-region bboxes for the key pairs
PAIRS=[("LIFT_TOP_TIE","LIFT_S1_TIE"),("LIFT_S2_TIE","LIFT_PULLEY"),
       ("LIFT_S2_TIE","LIFT_S1_BAR_L"),("LIFT_S2_TIE","LIFT_S1_BAR_R"),
       ("BOLT_S2TIE_0","LIFT_S1_BAR_L"),("BOLT_S2TIE_2","CRADLE_ARM"),
       ("BOLT_S2TIE_2","LIFT_S1_BAR_R"),("SCRW_CARM_0","LIFT_S2_BAR"),
       ("BOLT_YTR_0","YAW_SERVO"),("BOLT_YTR_0","YAW_SHAFT"),
       ("FLYWHEEL_R","WIRE_CAM_USB"),("FLYWHEEL_R","WIRE_HOOD_SV"),
       ("NIP_BACKPLATE","WIRE_FLY_R"),
       ("SCRW_S1T_L0_1","LIFT_S2_TRUCK_0"),("SCRW_S1T_L0_0","LIFT_S2_TRUCK_0"),
       ("BOLT_PORT_0","LOAD_CHUTE"),("BOLT_LTT_L0","BOLT_SC_L0"),
       ("ROPE_GUIDE","BOLT_SC_R1"),("LIFT_TOP_TIE","BOLT_SC_R0"),
       ("CRADLE_ARM","CRADLE_COL_0"),("LIFT_RAIL_R","ROPE_GUIDE"),
       ("LIFT_S1_BAR_L","LIFT_S2_TIE"),("BOLT_FBRG_R1","FLY_MOTOR_R"),
       ("BOLT_TIE_L_1","LIFT_BASE"),("WIRE_HOOD_SV","WIRE_CAM_USB"),
       ("NUT_LW_0","LIFT_WINCH"),("NUT_LW_0","FRAME_RAIL_L"),
       ("NUT_LW_0","BOLT_LW_0"),("NUT_TWC_L_0","TURRET_DECK"),
       ("NUT_TWC_L_0","BOLT_TWC_L_0"),("NUT_GUD_R3_0","TOWER_GUS_R3"),
       ("NUT_LRF_L1","LIFT_RAIL_L"),("NUT_LRF_R0","LIFT_RAIL_R"),
       ("NUT_LRF_L1","LIFT_BASE"),("NUT_LW_0","DECK_L")]
print("== pair commons ==")
sm={}
for a,b in PAIRS:
    for n in (a,b):
        if n not in sm:
            o=m.getObject(n)
            if o is not None and hasattr(o,"Shape"):
                s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); sm[n]=s
    if a in sm and b in sm:
        try:
            c=sm[a].common(sm[b]); bb=c.BoundBox
            print("%s x %s  vol=%.1f  x%.1f..%.1f y%.1f..%.1f z%.1f..%.1f"%(
                a,b,c.Volume,bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax))
        except Exception as e:
            print("%s x %s ERR %s"%(a,b,e))
    else:
        print("%s x %s MISSING"%(a,b))
print("DONE")
