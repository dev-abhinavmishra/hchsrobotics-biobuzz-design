import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
SKIP = ("AXIS_","REF_","VOL_","TOOL_","GRP_","ENV_")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
names=[o.Name for o in doc.Objects if hasattr(o,"Shape") and o.Shape.Solids
       and not o.Name.startswith(SKIP)]
for t in ("WIRE_WINCH","WIRE_TILT_SV","NUT_CHT_0","DECK_L","ELEC_SHELF"):
    o=doc.getObject(t); s=shape(o); res=[]
    for n in names:
        if n==t: continue
        v=s.common(shape(doc.getObject(n))).Volume
        if v>0.5: res.append((n,round(v,1)))
    print(t,"ovl:",sorted(res,key=lambda x:-x[1]))
