import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
names=[]
for o in doc.Objects:
    if not (hasattr(o,"Shape") and o.Shape.Solids): continue
    if o.Name.startswith(("AXIS_","REF_","VOL_")): continue
    names.append(o.Name)
targets=["DECK_L","ELEC_SHELF","NUT_CHT_0","NUT_CHT_1","WIRE_WINCH"]
for t in targets:
    o=doc.getObject(t); 
    if not (o and hasattr(o,"Shape")): continue
    s=shape(o); res=[]
    for n in names:
        if n==t: continue
        v=s.common(shape(doc.getObject(n))).Volume
        if v>0.5: res.append((n,round(v,1)))
    print(t,"ovl:",sorted(res,key=lambda x:-x[1]))
