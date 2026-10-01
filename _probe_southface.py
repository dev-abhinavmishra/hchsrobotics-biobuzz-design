import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
hub = Part.makeBox(142,29,74,Base.Vector(-70,-213,96))
hits=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("TOOL_","GRP_","HUB_EXP")): continue
    try: c=s.common(hub)
    except Exception: continue
    if c and c.Solids and c.Volume>0.5:
        bb=s.BoundBox
        hits.append((o.Name,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)]))
hits.sort(key=lambda h:-h[1])
print("HUB-SOUTH x-70..72 y-213..-184 z96..170:")
for h in hits[:15]: print("  ",h)
ball = Part.makeSphere(46.5, Base.Vector(-122,128.5,143))
print("vs S17:", ball.common(hub).Volume)
# also check envelope object bounds
for o in doc.Objects:
    if o.Name.startswith("ENV_") and hasattr(o,"Shape") and o.Shape and o.Shape.Solids:
        bb=o.Shape.BoundBox
        print(o.Name,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
