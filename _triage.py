import FreeCAD as App
m = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def g(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
pairs=[("LIFT_RAIL_R","CRADLE_ARM"),("PORT_FLANGE","RING_GEAR"),
("PORT_FLANGE","LAZY_SUSAN_HI"),("HOOD","HOOD_SERVO"),
("WHEEL_PLATE_RL_IN","CRADLE_CUP"),("CRADLE_CUP","CHUTE_LIP_R2"),
("LIFT_S1_TRUCK_R0","LIFT_S2_TRUCK_0"),("LIFT_RAIL_R","TILT_SERVO"),
("BOLT_S2TIE_3","CRADLE_ARM"),("YAW_PINION","YAW_MAGNET"),
("BOLT_CAM_0","VSN_CAM"),("FLYWHEEL_R","WIRE_CAM_USB"),
("FLY_MOTOR_L","BOLT_MCL_L0"),("LIFT_S1_BAR_R","S1_PPIN"),
("WHEEL_PLATE_RL_IN","LIFT_BASE"),("LIFT_TOP_PULLEY","BOLT_CARM_2"),
("CRADLE_CUP","SCRW_CHL_3_0"),("YAW_PINION","NUT_CK_R3"),
("FLYWHEEL_R","WIRE_HOOD_SV"),("SCRW_S1T_L1_0","LIFT_S1_BAR_R")]
for a,b in pairs:
    oa,ob=m.getObject(a),m.getObject(b)
    if not oa or not ob: print(a,b,"MISSING"); continue
    com=g(oa).common(g(ob))
    if com.Volume<0.3: continue
    c=com.BoundBox
    print("%s x %s V=%.1f region"%(a,b,com.Volume),
          [round(v,1) for v in (c.XMin,c.XMax,c.YMin,c.YMax,c.ZMin,c.ZMax)])
# also dump the solids' own bboxes for context
for n in ("LIFT_RAIL_R","CRADLE_ARM","PORT_FLANGE","RING_GEAR","LAZY_SUSAN_HI",
          "HOOD","HOOD_SERVO","WHEEL_PLATE_RL_IN","CRADLE_CUP","CHUTE_LIP_R2",
          "LIFT_S1_TRUCK_R0","LIFT_S2_TRUCK_0","TILT_SERVO","YAW_PINION",
          "YAW_MAGNET","VSN_CAM","S1_PPIN","LIFT_BASE","CRADLE_PIV","SCRW_TSV_0",
          "LIFT_TOP_PULLEY","BOLT_CARM_2"):
    o=m.getObject(n)
    if o and hasattr(o,"Shape") and o.Shape.Solids:
        bb=g(o).BoundBox
        print(n,"bbox",[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
