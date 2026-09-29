import FreeCAD as App, Part, json
d = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
MOV=("ROLLER_","STAR_SHAFT","ROLLER_SHAFT","FLOAT_","TORSION_","SPRING_","BELT_","TENS_","CHAIN_","MASTER_LINK","SPROCKET_","FEED_WHEEL","FEED_SHAFT","SPUR_","AGIT_","GATE_FLAG","GATE_HORN","DIV_FLAP","DIV_SHAFT","DIV_SERVO","VOL_","REF_","AXIS_","ENV_","TOOL_","JACK_SHAFT","INT_BRG","PIVOT_PIN","FEED_MTR_SHAFT","INT_MOTOR","FEED_MOTOR","GATE_SERVO","AGIT_SERVO","GRP_")
def gsh(o):
    s=o.Shape.copy()
    try: s.Placement=o.getGlobalPlacement()
    except Exception: pass
    return s
static=[]
for o in d.Objects:
    if not (hasattr(o,"Shape") and not o.Shape.isNull()): continue
    if not o.Shape.Solids or o.Name.startswith(MOV): continue
    static.append((o.Name,gsh(o)))
out={}
# S8 re-site candidate sweep around (10,0,128)
for tag,(x,y,z) in {"S8v2_(10,0,128)":(10,0,128),"alt(10,0,125)":(10,0,125),"alt(15,0,128)":(15,0,128),"alt(15,0,130)":(15,0,130)}.items():
    sp=Part.makeSphere(46.5,App.Vector(x,y,z))
    sb=sp.BoundBox; hits=[]
    for n,t in static:
        tb=t.BoundBox
        if (sb.XMin>tb.XMax or sb.XMax<tb.XMin or sb.YMin>tb.YMax or sb.YMax<tb.YMin or sb.ZMin>tb.ZMax or sb.ZMax<tb.ZMin): continue
        try: v=sp.common(t).Volume
        except Exception: v=0
        if v>0.5: hits.append((n,round(v,1)))
    out[tag]=sorted(hits,key=lambda h:-h[1])[:5]
# cradle park zone at z~140: box x-140..-112, y160..196, z120..160
bx=Part.makeBox(28,36,40,App.Vector(-140,160,120))
hits=[]
for n,t in static:
    tb=t.BoundBox
    if tb.XMax<-140 or tb.XMin>-112 or tb.YMax<160 or tb.YMin>196 or tb.ZMax<120 or tb.ZMin>160: continue
    try: v=bx.common(t).Volume
    except Exception: v=0
    if v>0.5: hits.append((n,round(v,1)))
out["cradle_park_z140_zone"]=hits[:8]
# chute corridor check: capsule along leg2 mid->cradle, sphere D70 along it sampling
for t in (0.0,0.25,0.5,0.75,1.0):
    px=-96+(-127+96)*t; py=115+(178-115)*t; pz=168+(140-168)*t
    sp=Part.makeSphere(35.5,App.Vector(px,py,pz))
    sb=sp.BoundBox; hh=[]
    for n,s in static:
        tb=s.BoundBox
        if (sb.XMin>tb.XMax or sb.XMax<tb.XMin or sb.YMin>tb.YMax or sb.YMax<tb.YMin or sb.ZMin>tb.ZMax or sb.ZMax<tb.ZMin): continue
        try: v=sp.common(s).Volume
        except Exception: v=0
        if v>0.5: hh.append((n,round(v,1)))
    out["chute_leg2_t%.2f"%t]=sorted(hh,key=lambda h:-h[1])[:4]
print("S3V2 "+json.dumps(out))
