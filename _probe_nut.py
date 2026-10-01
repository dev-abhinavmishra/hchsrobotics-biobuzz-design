import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for n in ("NUT_LW_0","BOLT_LW_0","LIFT_BASE","FRAME_RAIL_L",
          "NUT_LB_1","BOLT_LB_1","NUT_LRF_L1","BOLT_LRF_L1",
          "NUT_TWC_L_0","BOLT_TWF_L_0","TOWER_L","DECK_L",
          "NUT_GUD_R3_0","BOLT_GUD_R3_0","TOWER_GUS_R3"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape") and o.Shape.Solids:
        b=shape(o).BoundBox
        print(n,[round(v,2) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)])
