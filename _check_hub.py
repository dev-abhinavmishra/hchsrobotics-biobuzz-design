import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\electronics\electronics.FCStd")
import json
meta = json.load(open("exports/meta/electronics.json"))
print("dropped:", len(meta.get("dropped", [])))
for d in meta.get("dropped", [])[:30]: print("  ", d)
for nm in ("HUB_EXP","FRAME_RAIL_R"):
    o = doc.getObject(nm)
    if o and o.Shape:
        bb = o.Shape.BoundBox
        print(nm, [round(v,2) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
for i in range(4):
    for nm in ("BOLT_HUB_E_%d"%i, "NUT_HUB_E_%d"%i):
        o = doc.getObject(nm)
        if o and o.Shape:
            bb = o.Shape.BoundBox
            print(nm, [round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
# hub vs rail face contact
hub = doc.getObject("HUB_EXP").Shape
rail = doc.getObject("FRAME_RAIL_R").Shape
c = hub.common(rail)
print("hub-rail common vol:", round(c.Volume,2) if c and c.Solids else 0)
d = hub.distToShape(rail)[0]
print("hub-rail dist:", round(d,3))
