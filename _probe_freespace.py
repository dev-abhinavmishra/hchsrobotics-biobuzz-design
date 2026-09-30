import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
shapes = []
for o in doc.Objects:
    if not hasattr(o, "Shape"): continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_","WIRE_")): continue
    if o.Name == "HUB_EXP": continue
    shapes.append((o.Name, s))
print("statics:", len(shapes))
def probe(box, tag):
    hits = []
    for n, s in shapes:
        try: c = s.common(box)
        except Exception: continue
        if c and c.Solids and c.Volume > 0.5:
            hits.append((n, round(c.Volume,1)))
    hits.sort(key=lambda h:-h[1])
    if hits: print(tag, "HITS", hits[:12])
    else: print(tag, "CLEAR")
# grid scan: 142x74x29 box at z54.8..83.8 over interior
for cx in range(-150, 100, 25):
    for cy in range(-120, 140, 20):
        b = Part.makeBox(142, 74, 29, Base.Vector(cx-71, cy-37, 54.8))
        probe(b, "(%d,%d)" % (cx, cy))
