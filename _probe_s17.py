import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
sp = Part.makeSphere(46.5, Base.Vector(-122, 128.5, 143))
EX = ("ENV_","VOL_","TOOL_","GRP_","LOAD_CHUTE","CHUTE_LIP","CRADLE_","PORT_","FEED_COLUMN","COL_FLANGE","LAZY_","RING_GEAR","NIP","FLY","HOOD","TURRET_PLATE","DIV","GATE","LAUNCH","BELT","CHAIN","WIRE")
for o in doc.Objects:
    if not hasattr(o, "Shape"): continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(EX): continue
    try: c = s.common(sp)
    except Exception: continue
    if c and c.Solids and c.Volume > 0.5:
        print(o.Name, round(c.Volume,1))
