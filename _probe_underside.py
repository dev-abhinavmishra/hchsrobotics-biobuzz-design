import FreeCAD as App
import Part
doc = App.openDocument(u"cad/master_robot.FCStd")
doc.recompute(None, True, True)
o = doc.getObject("TOWER_L")
sh = o.Shape.copy(); sh.Placement = o.getGlobalPlacement()
# for the two nut footprints, find the lowest tower face above each (x,y)
for y in (110, 126, 118, 130):
    # vertical ray: sample point at z just above nut top; find dist up
    v = Part.Vertex(App.Vector(-173, y, 241.0))
    d = v.distToShape(sh)
    v2 = Part.Vertex(App.Vector(-173, y, 243.5))
    d2 = v2.distToShape(sh)
    # is the point inside the solid?
    inside = sh.isInside(App.Vector(-173, y, 242.0), 1e-6, True)
    inside2 = sh.isInside(App.Vector(-173, y, 244.5), 1e-6, True)
    print("y=%g  dist(z241)=%.3f dist(z243.5)=%.3f inside242=%s inside244.5=%s" %
          (y, d[0], d2[0], inside, inside2))
# also across x on the west stub at the nut_0 line
for x in (-175, -173, -171, -169.5):
    print("x=%g inside242=%s dist241=%.3f" %
          (x, sh.isInside(App.Vector(x, 110, 242.0), 1e-6, True),
           Part.Vertex(App.Vector(x, 110, 241.0)).distToShape(sh)[0]))
