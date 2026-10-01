import FreeCAD as App
import Part
doc = App.openDocument(u"cad/master_robot.FCStd")
doc.recompute(None, True, True)
o = doc.getObject("TOWER_L")
sh = o.Shape.copy(); sh.Placement = o.getGlobalPlacement()
# grid of inside-tests at z242.5 (mid-cap) over the cap region
print("inside@z242.5: rows=y, cols=x")
xs = list(range(-176, 1, 4))
print("      " + "".join("%4d" % x for x in xs))
for y in range(104, 134, 2):
    row = "".join("   X" if sh.isInside(App.Vector(x, y, 242.5), 1e-6, True) else "   ." for x in xs)
    print("y=%3d %s" % (y, row))
# and at z222 (wall top level hint)
print("inside@z236:")
for y in range(104, 134, 2):
    row = "".join("   X" if sh.isInside(App.Vector(x, y, 236.0), 1e-6, True) else "   ." for x in xs)
    print("y=%3d %s" % (y, row))
