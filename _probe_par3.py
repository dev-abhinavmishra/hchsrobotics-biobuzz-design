import FreeCAD as App
doc = App.openDocument(u"cad/turret/turret.FCStd")
doc.recompute(None, True, True)
sheet = doc.getObject("Parameters")
def gs(nm):
    o = doc.getObject(nm)
    if o is None: return None
    s = o.Shape.copy(); s.Placement = o.getGlobalPlacement(); return s
for nm in ("TOWER_L","TURRET_DECK","LAZY_SUSAN_LO","TURRET_PLATE"):
    o = doc.getObject(nm)
    print("===", nm)
    try:
        for path, expr in o.ExpressionEngine:
            if "Placement.Base.z" in path or "Height" in path:
                print("   ", path, "=", expr)
    except Exception as e:
        print("   (no expr)", e)
tz = float(sheet.get("turret_deck_z0"))
before = {nm: gs(nm).BoundBox.ZMin for nm in ("TOWER_L","TURRET_DECK","LAZY_SUSAN_LO","TURRET_PLATE")}
sheet.set("turret_deck_z0", repr(tz+4.0))
doc.recompute(None, True, True)
after = {nm: gs(nm).BoundBox.ZMin for nm in ("TOWER_L","TURRET_DECK","LAZY_SUSAN_LO","TURRET_PLATE")}
sheet.set("turret_deck_z0", repr(tz))
for nm in before: print(nm, "%.2f -> %.2f" % (before[nm], after[nm]))
