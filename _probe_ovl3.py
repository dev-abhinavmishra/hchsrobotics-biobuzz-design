import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
targets=["STANDOFF_1","BOLT_SO_T_1","BOLT_SO_B_1","DECK_POST_L0",
         "BOLT_DP_T_L0","BOLT_DP_B_L0","DECK_L","ELEC_SHELF",
         "WIRE_TILT_SV","CHUTE_TOWER_PAD","LOAD_CHUTE","CHUTE_LIP_L2"]
solids=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","AXIS_","REF_","GRP_")): continue
    solids.append(o)
shapes={o.Name:shape(o) for o in solids}
for tn in targets:
    t=doc.getObject(tn)
    if t is None or not hasattr(t,"Shape") or not t.Shape.Solids:
        print(tn,"MISSING"); continue
    ts=shapes.get(tn) or shape(t)
    hits=[]
    for o in solids:
        if o.Name==tn: continue
        try: c=ts.common(shapes[o.Name])
        except Exception: continue
        if c and c.Solids and c.Volume>0.5:
            hits.append((o.Name,round(c.Volume,1)))
    print(tn,"ovl:",sorted(hits,key=lambda h:-h[1])[:10])
