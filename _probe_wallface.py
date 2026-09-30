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
probe(Part.makeBox(142,29,74,Base.Vector(-74,133,96)),"NORTH face x-74..68 y133..162 z96..170")
probe(Part.makeBox(142,29,74,Base.Vector(-74,-162,96)),"SOUTH face x-74..68 y-162..-133 z96..170")
# ball check for both
ball = Part.makeSphere(46.5, Base.Vector(-122,128.5,143))
b1 = Part.makeBox(142,29,74,Base.Vector(-74,133,96))
b2 = Part.makeBox(142,29,74,Base.Vector(-74,-162,96))
print("N vs S17:", ball.common(b1).Volume, "  S vs S17:", ball.common(b2).Volume)
# number plate extents
for o in doc.Objects:
    if "NUM" in o.Name or "PLATE_NUM" in o.Name:
        bb=o.Shape.BoundBox
        print(o.Name,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
