import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for n in ("MOTOR_RL","GBOX_RL","MOUNT_PLATE_L","NUT_CHT_0","ELEC_SHELF"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape") and o.Shape.Solids:
        bb=shape(o).BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
# where does the wire cross the motor?
c=shape(doc.getObject("WIRE_TILT_SV")).common(shape(doc.getObject("MOTOR_RL")))
bb=c.BoundBox
print("wire x MOTOR_RL", round(c.Volume,1), [round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
