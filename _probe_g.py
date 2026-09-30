import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for n in ("BOLT_LB_2","BOLT_CLMP_RL_1_1","CLAMP_RL_1"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape"):
        bb=shape(o).BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
for a,b in (("WIRE_WINCH","BOLT_LB_2"),("WIRE_WINCH","BOLT_CLMP_RL_1_1"),("WIRE_WINCH","WIRE_TILT_SV")):
    c=shape(doc.getObject(a)).common(shape(doc.getObject(b)))
    bb=c.BoundBox
    print(a,"x",b,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
