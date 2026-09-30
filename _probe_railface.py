import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
# candidate: slab x-76..66, y184..213, z30..104 + mounting zone y180..190
box = Part.makeBox(142, 33, 78, Base.Vector(-76, 180, 26))
for o in doc.Objects:
    if not hasattr(o, "Shape"): continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_")): continue
    try: c = s.common(box)
    except Exception: continue
    if c and c.Solids and c.Volume > 0.5:
        bb = s.BoundBox
        print(o.Name, round(c.Volume,1), [round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
