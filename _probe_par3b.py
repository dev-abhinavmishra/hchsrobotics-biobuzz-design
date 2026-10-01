import FreeCAD as App
doc = App.openDocument(u"cad/turret/turret.FCStd")
doc.recompute(None, True, True)
sheet = doc.getObject("Parameters")
def gs(nm):
    o = doc.getObject(nm)
    s = o.Shape.copy(); s.Placement = o.getGlobalPlacement(); return s
tz = float(sheet.get("turret_deck_z0"))
names = ("TOWER_L","TURRET_DECK","LAZY_SUSAN_LO","TURRET_PLATE")
before = {nm: gs(nm).BoundBox.ZMin for nm in names}
sheet.set("turret_deck_z0", repr(tz+4.0))
doc.recompute(None, True, True)
after = {nm: gs(nm).BoundBox.ZMin for nm in names}
sheet.set("turret_deck_z0", repr(tz))
doc.recompute(None, True, True)
for nm in names: print("PAR3_turret_z:", nm, "%.2f -> %.2f" % (before[nm], after[nm]))
App.closeDocument(doc.Name)

doc = App.openDocument(u"cad/lift/lift.FCStd")
doc.recompute(None, True, True)
sheet = doc.getObject("Parameters")
lr = float(sheet.get("lift_rail_len"))
lt0 = gs("LIFT_TOP_TIE").BoundBox; rl0 = gs("LIFT_RAIL_L").BoundBox
sheet.set("lift_rail_len", repr(lr + 10.0))
doc.recompute(None, True, True)
lt1 = gs("LIFT_TOP_TIE").BoundBox; rl1 = gs("LIFT_RAIL_L").BoundBox
sheet.set("lift_rail_len", repr(lr))
print("PAR3_lift_rail_len: rail ZMax %.1f->%.1f tie %.1f->%.1f" %
      (rl0.ZMax, rl1.ZMax, lt0.ZMax, lt1.ZMax))
