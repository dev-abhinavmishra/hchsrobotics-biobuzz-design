import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
for n in ("TOWER_L","CHUTE_TOWER_PAD","CHUTE_LIP_R1","CHUTE_LIP_L1","LIFT_WINCH","WINCH_SPOOL","WINCH_DPIN","ROPE_DYNEEMA","SCRW_CHL_0_1","SCRW_CHL_1_0","SCRW_CHL_1_1"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape"):
        bb=o.Shape.BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
