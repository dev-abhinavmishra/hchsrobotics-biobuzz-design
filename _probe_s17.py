import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
ball = Part.makeSphere(46.5, Base.Vector(-122,128.5,143))
EX = set()
import re
src = open(r"scripts\freecad\selfcheck_overhaul03.py").read()
m = re.search(r"BALL_STATIC_EX\s*=\s*(?:frozenset|set)?\(?\{([^}]*)\}", src, re.S)
if m:
    for q in re.findall(r'"([^"]+)"', m.group(1)):
        EX.add(q)
hits=[]; ex_hits=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_","WIRE_")): continue
    try: c=s.common(ball)
    except Exception: continue
    if c and c.Solids and c.Volume>0.5:
        (ex_hits if o.Name in EX else hits).append((o.Name,round(c.Volume,1)))
print("EXEMPT hits:",len(ex_hits))
print("NON-EXEMPT hits:",len(hits))
for h in sorted(hits,key=lambda h:-h[1]): print("  ",h)
# also sanity-check the winch stack + pad bboxes
for n in ("LIFT_WINCH","WINCH_SPOOL","WINCH_DPIN","CHUTE_TOWER_PAD","TOWER_L","ROPE_DYNEEMA"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape"):
        bb=o.Shape.BoundBox
        print(n,[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
