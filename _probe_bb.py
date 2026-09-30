import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for n in ("DECK_POST_L0","DECK_POST_L1","STANDOFF_0","STANDOFF_1","STANDOFF_2","STANDOFF_3","BOLT_SO_T_1","BOLT_SO_B_1","BOLT_DP_T_L0","BOLT_DP_B_L0","ELEC_SHELF","DECK_L","LIFT_BASE","CRADLE_FOAM","CHUTE_PORT_EAR","LIFT_PULLEY","LIFT_TOP_PULLEY","BOLT_CARM_2"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape") and o.Shape.Solids:
        bb=shape(o).BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
