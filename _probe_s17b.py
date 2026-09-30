import FreeCAD as App, Part
from FreeCAD import Base
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
EX = {"FLYWHEEL_L","FLYWHEEL_R","FLY_SHAFT_L","FLY_SHAFT_R","FLY_CLAMP_L",
"FLY_CLAMP_R","NIP_BACKPLATE","TURRET_PLATE","HOOD","HOOD_PIV_L","HOOD_PIV_R",
"HOOD_COL_L","HOOD_COL_R","LOAD_CHUTE","CHUTE_LIP_L1","CHUTE_LIP_L2",
"CHUTE_LIP_R1","CHUTE_LIP_R2","CRADLE_CUP","CRADLE_FOAM","CRADLE_PIV",
"CRADLE_COL_0","CRADLE_COL_1","ROLLER_SHAFT","DIV_SHAFT","GATE_HORN",
"CHAIN_25","BELT_XROLL","TENS_IDLER","TENS_ARM","TENS_PIN","TENS_SPRING",
"TORSION_SPRING_L","TORSION_SPRING_R","BELT_PUL_LOW","BELT_PUL_TOP",
"SPROCKET_9T","SPROCKET_16T","MASTER_LINK","FLOAT_SLIDE_L","FLOAT_SLIDE_R",
"FLOAT_PIN_L","FLOAT_PIN_R","SPUR_FEED_M","SPUR_FEED_W","FEED_MTR_SHAFT"}
ball = Part.makeSphere(46.5, Base.Vector(-122,128.5,143))
hits=[]
for o in doc.Objects:
    if not hasattr(o,"Shape"): continue
    s=o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_","VOL_","TOOL_","GRP_")) or o.Name in EX: continue
    try: c=s.common(ball)
    except Exception: continue
    if c and c.Solids and c.Volume>0.5:
        bb=s.BoundBox
        hits.append((o.Name,round(c.Volume,1),[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)]))
hits.sort(key=lambda h:-h[1])
print("S17 non-exempt conflicts:")
for h in hits[:25]: print("  ",h)
