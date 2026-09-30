import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
# candidate hub slab: x50..192, y184..216, z15..89
box = Part.makeBox(142, 32, 74, Base.Vector(50, 184, 15))
hits=[]
for o in doc.Objects:
    if not hasattr(o, "Shape"): continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_")): continue
    try: c = s.common(box)
    except Exception: continue
    if c and c.Solids and c.Volume > 0.5:
        bb = s.BoundBox
        hits.append((o.Name, round(c.Volume,1), [round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)]))
hits.sort(key=lambda h:-h[1])
for h in hits[:25]: print(h)
# also S-ball clearance: check sphere at S16 and S17 x-extents
for tag,(x,y,z) in {"S17":(-122,128.5,143),"S16":(-108.2,165.3,185.8),"S11":(-66,52,203)}.items():
    sp=Part.makeSphere(46.5,Base.Vector(x,y,z))
    c=sp.common(box)
    print(tag, "vs candidate box common:", round(c.Volume,1) if c.Solids else 0)
