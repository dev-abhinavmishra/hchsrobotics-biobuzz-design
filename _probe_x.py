import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for n in ("CRADLE_CUP","WHEEL_PLATE_RL_IN","ROLLER_RL_01_B","ROLLER_RL_02_B",
          "LIFT_RAIL_R","CRADLE_ARM","CRADLE_PIV","LIFT_S1_TRUCK_R0",
          "LIFT_S2_TRUCK_0","CHUTE_LIP_R2"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape"):
        b=shape(o).BoundBox
        print(n,[round(v,1) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)])
for a,b in (("LIFT_RAIL_R","CRADLE_ARM"),("WHEEL_PLATE_RL_IN","CRADLE_CUP"),
            ("LIFT_S1_TRUCK_R0","LIFT_S2_TRUCK_0"),("CRADLE_CUP","CHUTE_LIP_R2")):
    c=shape(doc.getObject(a)).common(shape(doc.getObject(b)))
    bb=c.BoundBox
    print(a,"x",b,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
