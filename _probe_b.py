import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for n in ("BOLT_TWF_L_0","TOWER_GUS_L0","BOLT_GUS_L0_1","BOLT_FBRG_R1",
          "BOLT_FM_R1","FLY_BRG_R","ODO_WHEEL_LAT_R","WIRE_ENC_LAT_L",
          "NUT_LRF_L0","GUSSET_BL","WHEEL_PLATE_RL_IN","LIFT_BASE",
          "LIFT_TOP_PULLEY","BOLT_CARM_2","FEED_MOTOR","NUT_GUD_R3_0"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape"):
        b=shape(o).BoundBox
        print(n,[round(v,1) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)])
for a,b in (("BOLT_TWF_L_0","TOWER_GUS_L0"),("BOLT_FBRG_R1","BOLT_FM_R1"),
            ("ODO_WHEEL_LAT_R","WIRE_ENC_LAT_L"),
            ("WHEEL_PLATE_RL_IN","LIFT_BASE"),("LIFT_TOP_PULLEY","BOLT_CARM_2")):
    c=shape(doc.getObject(a)).common(shape(doc.getObject(b)))
    bb=c.BoundBox
    print(a,"x",b,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
