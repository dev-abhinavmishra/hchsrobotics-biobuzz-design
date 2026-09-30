import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
for n in ("DECK_L","DECK_R","FRAME_RAIL_L","ELEC_SHELF","BELLY_PAN"):
    o = doc.getObject(n)
    if o is not None:
        bb = o.Shape.BoundBox
        print(n, [round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
box = Part.makeBox(142.0, 74.0, 29.0, Base.Vector(-133, 85, 54.8))
hits = []
for o in doc.Objects:
    if not hasattr(o, "Shape"): continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_")): continue
    try: c = s.common(box)
    except Exception: continue
    if c and c.Solids and c.Volume > 0.5:
        hits.append((o.Name, round(c.Volume,1)))
hits.sort(key=lambda h:-h[1])
print("BAY HITS:", hits[:30])
# and for under-deck y-band under the shelf zone orig pos
box2 = Part.makeBox(142.0, 74.0, 29.0, Base.Vector(-170, 75.5, 54.8))
hits2 = []
for o in doc.Objects:
    if not hasattr(o, "Shape"): continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_")): continue
    try: c = s.common(box2)
    except Exception: continue
    if c and c.Solids and c.Volume > 0.5:
        hits2.append((o.Name, round(c.Volume,1)))
hits2.sort(key=lambda h:-h[1])
print("BAY2 HITS:", hits2[:30])
