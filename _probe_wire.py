import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\lift\lift.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
solids=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","AXIS_","REF_","GRP_")): continue
    solids.append(o)
shapes={o.Name:shape(o) for o in solids}
for tn in ("WIRE_TILT_SV","WIRE_WINCH"):
    t=doc.getObject(tn); ts=shape(t)
    hits=[]
    for o in solids:
        if o.Name==tn: continue
        try: c=ts.common(shapes[o.Name])
        except Exception: continue
        if c and c.Solids and c.Volume>0.5:
            hits.append((o.Name,round(c.Volume,1)))
    print(tn,"ovl:",sorted(hits,key=lambda h:-h[1])[:12])
