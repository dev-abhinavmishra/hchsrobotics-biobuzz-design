import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
# winch block x-50..-28 y150..170 on deck z86.8..137.6 + ears/spool to ~160
box = Part.makeBox(30,20,80,Base.Vector(-54,150,86.8))
hits=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_","WIRE_")): continue
    try: c=s.common(box)
    except Exception: continue
    if c and c.Solids and c.Volume>0.5:
        bb=s.BoundBox
        hits.append((o.Name,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)]))
hits.sort(key=lambda h:-h[1])
print("DECK-WINCH x-54..-24 y150..170 z86.8..166.8:")
for h in hits[:15]: print("  ",h)
