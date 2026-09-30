import FreeCAD as App, Part
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
for n in ("ROLLER_RL_02","ROLLER_RL_00","BOLT_CK_L1","NUT_CK_L1","FLY_MCLAMP_L","BOLT_MCL_L0","NUT_MCL_L0","BATTERY","HOP_FLOOR","LIFT_S2_BAR","CRADLE_ARM","CRADLE_CUP","LIFT_COLUMN","LIFT_RAIL_L","LIFT_TOP_TIE"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape") and o.Shape.Solids:
        bb=o.Shape.BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
# S15 ball vs wall-face hardware: what's within the S15 sphere near the wall
ball = Part.makeSphere(46.5, App.Vector(-91.5,126.6,211.2))
hits=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","AXIS_","REF_","GRP_","WIRE_")): continue
    try: c=s.common(ball)
    except Exception: continue
    if c and c.Solids and c.Volume>0.5:
        hits.append((o.Name,round(c.Volume,1)))
print("S15 hits:",sorted(hits,key=lambda h:-h[1])[:15])
ball16 = Part.makeSphere(46.5, App.Vector(-122.0,184.1,169.9))
hits=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","AXIS_","REF_","GRP_","WIRE_")): continue
    try: c=s.common(ball16)
    except Exception: continue
    if c and c.Solids and c.Volume>0.5:
        hits.append((o.Name,round(c.Volume,1)))
print("S16 hits:",sorted(hits,key=lambda h:-h[1])[:15])
