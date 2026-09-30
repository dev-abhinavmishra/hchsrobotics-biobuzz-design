import sys, json, math
sys.path.insert(0, r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad")
import FreeCAD as App, Part

m = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
mmeta = json.load(open(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\exports\meta\master.json"))
sheet = m.getObject("Parameters")

EXCLUDE_PREFIX = ("ENV_", "TOOL_", "AXIS_", "REF_", "VOL_")
EXCLUDE_TYPES = ("App::Part", "App::DocumentObjectGroup", "Part::Compound")

def exportable(doc):
    consumed = set()
    for o in doc.Objects:
        if o.TypeId in ("Part::Fuse","Part::Cut","Part::Chamfer","Part::Common","Part::MultiFuse"):
            for p in ("Base","Tool","Shapes"):
                t=getattr(o,p,None)
                if t is None: continue
                for x in (t if isinstance(t,(list,tuple)) else (t,)):
                    if x is not None: consumed.add(x.Name)
    return [o for o in doc.Objects
            if hasattr(o,"Shape") and not o.Shape.isNull()
            and o.Shape.Volume>0
            and o.TypeId not in EXCLUDE_TYPES
            and not o.Name.startswith(EXCLUDE_PREFIX)
            and o.Name not in consumed]

def gshape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s

solids = exportable(m)
gshapes = {o.Name: gshape(o) for o in solids}
print("solids:", len(solids))

# ---------- GEO-B ----------
BALL_OK={"FEED_WHEEL","ROLLER_TOP","ROLLER_LOW","AGIT_PADDLE","GATE_FLAG",
         "DIV_FLAP","FEED_SCOOP","AGIT_HORN","STAR_SHAFT","FEED_SHAFT"}
BALL_STATIC_EX=BALL_OK|{"ROLLER_SHAFT","DIV_SHAFT","GATE_HORN","CHAIN_25",
    "BELT_XROLL","TENS_IDLER","TENS_ARM","TENS_PIN","TENS_SPRING",
    "TORSION_SPRING_L","TORSION_SPRING_R","BELT_PUL_LOW","BELT_PUL_TOP",
    "SPROCKET_9T","SPROCKET_16T","MASTER_LINK","FLOAT_SLIDE_L",
    "FLOAT_SLIDE_R","FLOAT_PIN_L","FLOAT_PIN_R","SPUR_FEED_M",
    "SPUR_FEED_W","FEED_MTR_SHAFT","FLYWHEEL_L","FLYWHEEL_R",
    "FLY_SHAFT_L","FLY_SHAFT_R","FLY_CLAMP_L","FLY_CLAMP_R",
    "NIP_BACKPLATE","TURRET_PLATE","HOOD","HOOD_PIV_L","HOOD_PIV_R",
    "HOOD_COL_L","HOOD_COL_R","LOAD_CHUTE","CHUTE_LIP_L1","CHUTE_LIP_L2",
    "CHUTE_LIP_R1","CHUTE_LIP_R2","CRADLE_CUP","CRADLE_FOAM","CRADLE_PIV",
    "CRADLE_COL_0","CRADLE_COL_1"}
import dt_lift
p0c,p1c,p2c=dt_lift.CHUTE_PTS
d1c,_w1,n1c,_L1=dt_lift._frame_for(p0c,p1c)
d2c,_w2,n2c,_L2=dt_lift._frame_for(p1c,p2c)
m1=(App.Vector(*p0c)+App.Vector(*p1c))*0.5+n1c*46.5
m2=(App.Vector(*p1c)+App.Vector(*p2c))*0.5+n2c*46.5
col_cx=float(sheet.get("column_x")); col_z1=float(sheet.get("column_z1"))
fax=float(sheet.get("fly_axis_x")); faz=float(sheet.get("fly_axis_z"))
cdx=float(sheet.get("cradle_x"))+5.0
cdy=float(sheet.get("cradle_y"))-3.0-46.5
cdz=float(sheet.get("cradle_z"))+3.0
STATIONS=(("S1",46.5,(205,0,80)),("S3",46.5,(178,0,85)),("S4",46.5,(105,0,155)),
("S5",46.5,(62,0,142)),("S6",46.5,(40,0,134)),("S7",46.5,(35,0,132)),
("S8",46.5,(10,0,125)),("S9a",46.5,(-66,0,162)),("S9b",46.5,(-66,0,200)),
("S9c",46.5,(-66,0,240)),("S10",46.5,(-66,0,175)),("S11",46.5,(-66,52,203)),
("S12",46.5,(-66,57,204)),("S13",46.5,(col_cx,0,col_z1)),("S14",46.5,(fax,0,faz)),
("S15",46.5,(m1.x,m1.y,m1.z)),("S16",46.5,(m2.x,m2.y,m2.z)),
("S17",46.5,(cdx,cdy,cdz)))
bb=[]
for sn,sr,c in STATIONS:
    sp=Part.makeSphere(sr,App.Vector(*c))
    for o in solids:
        if o.Name in BALL_STATIC_EX or o.Name.startswith(("ENV_","VOL_")): continue
        try: com=sp.common(gshapes[o.Name])
        except Exception: continue
        if com.Volume>0.5: bb.append((sn,o.Name,round(com.Volume,1)))
for pn in ("VOL_BALL_P","VOL_BALL_N"):
    pv=m.getObject(pn)
    if pv is None: bb.append(("missing",pn,0)); continue
    ps=gshape(pv)
    for o in solids:
        if o.Name in BALL_OK or o.Name.startswith(("ENV_","VOL_")): continue
        try: com=ps.common(gshapes[o.Name])
        except Exception: continue
        if com.Volume>0.5: bb.append((pn,o.Name,round(com.Volume,1)))
print("GEOB:", "PASS" if not bb else bb)

# ---------- GEO2 ----------
declared=set()
for coll in ("embeds","faces","journals","contacts"):
    for a,b in mmeta[coll]: declared.add(tuple(sorted((a,b))))
for j in mmeta["joints"]:
    ms=j["members"]+j.get("bolts",[])+j.get("nuts",[])
    for i_ in range(len(ms)):
        for k_ in range(i_+1,len(ms)):
            declared.add(tuple(sorted((ms[i_],ms[k_]))))
names=list(gshapes); bbs={n:gshapes[n].BoundBox for n in names}
ov=[]
for i_ in range(len(names)):
    a=names[i_]
    for j_ in range(i_+1,len(names)):
        b=names[j_]
        if tuple(sorted((a,b))) in declared: continue
        ba,bbx=bbs[a],bbs[b]
        if ba.XMin>bbx.XMax or ba.XMax<bbx.XMin or ba.YMin>bbx.YMax or \
           ba.YMax<bbx.YMin or ba.ZMin>bbx.ZMax or ba.ZMax<bbx.ZMin: continue
        try: com=gshapes[a].common(gshapes[b])
        except Exception: continue
        if com.Volume>0.5: ov.append((round(com.Volume,1),a,b))
ov.sort(reverse=True)
print("GEO2:",len(ov))
for v,a,b in ov[:200]: print("  %.1f %s x %s"%(v,a,b))
