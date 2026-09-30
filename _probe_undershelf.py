import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def probe(box, tag):
    hits=[]
    for o in doc.Objects:
        if not hasattr(o,"Shape"): continue
        s=o.Shape
        if not s or s.isNull() or not s.Solids: continue
        if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_","WIRE_","HUB_EXP","ELEC_SHELF")): continue
        try: c=s.common(box)
        except Exception: continue
        if c and c.Solids and c.Volume>0.5:
            bb=s.BoundBox
            hits.append((o.Name,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)]))
    hits.sort(key=lambda h:-h[1])
    print(tag)
    for h in hits[:15]: print("  ",h)
# hub under shelf at orig xy: x-170..-28, y75.5..149.5, z64.5..93.5
probe(Part.makeBox(142,74,29,Base.Vector(-170,75.5,64.5)),"ORIG-XY undershelf")
