import FreeCAD as App
m = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def g(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
pairs=[("BOLT_FBRG_L0","BOLT_FM_L0"),("YAW_PINION","BOLT_CK_R3"),
("YAW_PINION","YAW_MAGNET"),("BOLT_S2TIE_3","BOLT_CARM_0"),
("FLYWHEEL_R","WIRE_FLY_R"),("LIFT_S1_BAR_R","S1_PPIN"),
("BOLT_SC_R0","LIFT_S1_TIE"),("LIFT_RAIL_R","LIFT_TOP_PULLEY")]
for a,b in pairs:
    oa,ob=m.getObject(a),m.getObject(b)
    if not oa or not ob: continue
    com=g(oa).common(g(ob))
    if com.Volume<0.2: continue
    c=com.BoundBox
    print("%s x %s V=%.1f"%(a,b,com.Volume),
          [round(v,1) for v in (c.XMin,c.XMax,c.YMin,c.YMax,c.ZMin,c.ZMax)])
for n in ("BOLT_FBRG_L0","BOLT_FM_L0","YAW_PINION","NUT_CK_R3","BOLT_CK_R3",
          "LAUNCH_CHEEK_R","LIFT_TOP_PULLEY","BOLT_S2TIE_3","BOLT_CARM_0",
          "LIFT_S2_TIE","S1_PPIN","LIFT_S1_BAR_R","VSN_CAM","BOLT_CAM_0"):
    o=m.getObject(n)
    if o and hasattr(o,"Shape") and o.Shape.Solids:
        bb=g(o).BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
