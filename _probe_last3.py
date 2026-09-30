import FreeCAD as App
import Part
doc = App.openDocument(u"cad/master_robot.FCStd")
doc.recompute(None, True, True)
def bb(n):
    o = doc.getObject(n)
    if o is None or not hasattr(o, "Shape"):
        return "%s: MISSING" % n
    s = o.Shape
    g = s.translated(getattr(o, "getGlobalPlacement", lambda: o.Placement)().Base) if False else s
    try:
        sh = o.getSubObject("") if False else None
    except Exception:
        pass
    # apply global placement
    pl = o.getGlobalPlacement()
    sh = s.copy()
    sh.Placement = pl
    b = sh.BoundBox
    return "%-16s x%.1f..%.1f y%.1f..%.1f z%.1f..%.1f" % (n, b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)
for n in ("NUT_TWC_L_0","NUT_TWC_L_1","TOWER_L","TURRET_DECK","FEED_COLUMN","YAW_TRAY",
          "BOLT_S2TIE_1","ROPE_DYNEEMA","LIFT_S2_TIE","BOLT_YTR_0","BOLT_YTR_3",
          "YAW_SERVO","YAW_SHAFT","SCRW_CARM_0","LIFT_S2_BAR","CRADLE_ARM"):
    print(bb(n))
# common-region for the two GEO2 pairs
for a,b in (("FEED_COLUMN","YAW_TRAY"),("BOLT_S2TIE_1","ROPE_DYNEEMA"),
            ("NUT_TWC_L_0","TOWER_L")):
    oa,ob = doc.getObject(a),doc.getObject(b)
    sa,sb = oa.Shape.copy(), ob.Shape.copy()
    sa.Placement = oa.getGlobalPlacement(); sb.Placement = ob.getGlobalPlacement()
    c = sa.common(sb)
    if c.Volume>0.01:
        bx = c.BoundBox
        print("COMMON %s x %s v=%.2f x%.1f..%.1f y%.1f..%.1f z%.1f..%.1f" %
              (a,b,c.Volume,bx.XMin,bx.XMax,bx.YMin,bx.YMax,b.ZMin,b.ZMax))
    else:
        d = sa.distToShape(sb)[0]
        print("COMMON %s x %s v=0 dist=%.3f" % (a,b,d))
