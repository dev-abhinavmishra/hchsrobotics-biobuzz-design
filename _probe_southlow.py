import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def probe(box, tag):
    hits=[]
    for o in doc.Objects:
        if not hasattr(o,"Shape"): continue
        s=o.Shape
        if not s or s.isNull() or not s.Solids: continue
        if o.Name.startswith(("TOOL_","GRP_","ENV_","HUB_EXP")): continue
        try: c=s.common(box)
        except Exception: continue
        if c and c.Solids and c.Volume>0.5:
            bb=s.BoundBox
            hits.append((o.Name,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)]))
    hits.sort(key=lambda h:-h[1])
    print(tag)
    for h in hits[:15]: print("  ",h)
probe(Part.makeBox(142,32,74,Base.Vector(-70,-216,3)),"LOW x-70..72 y-216..-184 z3..77")
# rail outer web extent + bolts near face for mount sanity
for nm in ("FRAME_RAIL_R","FRAME_RAIL_L"):
    o=doc.getObject(nm)
    if o and o.Shape:
        bb=o.Shape.BoundBox
        print(nm,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
