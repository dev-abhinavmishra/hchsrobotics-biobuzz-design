import FreeCAD as App, Part
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
from FreeCAD import Base
box = Part.makeBox(102.0, 100.0, 34.0, Base.Vector(-30, 65, 93))
hits = []
for o in doc.Objects:
    if not hasattr(o, "Shape"):
        continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids:
        continue
    try:
        c = s.common(box)
    except Exception:
        continue
    if c and c.Solids and c.Volume > 0.5:
        bb = s.BoundBox
        hits.append((o.Name, round(c.Volume,1),
                     round(bb.XMin,1),round(bb.XMax,1),
                     round(bb.YMin,1),round(bb.YMax,1),
                     round(bb.ZMin,1),round(bb.ZMax,1)))
hits.sort(key=lambda h:-h[1])
for h in hits[:40]:
    print(h)
print("done", len(hits))
