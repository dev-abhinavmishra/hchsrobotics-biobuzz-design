import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for n in ("NUT_CHT_0","NUT_CHT_1","BOLT_CHT_0","CLAMP_RL_1","CLAMP_RL_2","CHUTE_TOWER_PAD"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape") and o.Shape.Solids:
        bb=shape(o).BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
for a,b in (("NUT_CHT_0","DECK_L"),("WIRE_TILT_SV","CLAMP_RL_1"),("WIRE_TILT_SV","CLAMP_RL_2")):
    c=shape(doc.getObject(a)).common(shape(doc.getObject(b)))
    bb=c.BoundBox
    print(a,"x",b,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
