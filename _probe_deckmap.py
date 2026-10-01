import FreeCAD as App
import Part
doc = App.openDocument(u"cad/master_robot.FCStd")
doc.recompute(None, True, True)
for nm, z in (("TURRET_DECK", 246.0),):
    o = doc.getObject(nm); sh = o.Shape.copy(); sh.Placement = o.getGlobalPlacement()
    xs = list(range(-48, 4, 4))
    print(nm, "inside@z%g" % z)
    print("      " + "".join("%4d" % x for x in xs))
    for y in range(104, 134, 2):
        print("y=%3d %s" % (y, "".join("   X" if sh.isInside(App.Vector(x, y, z), 1e-6, True) else "   ." for x in xs)))
