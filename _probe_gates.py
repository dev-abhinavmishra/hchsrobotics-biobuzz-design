import FreeCAD as App, json
from pathlib import Path
ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
EXCLUDE_PREFIX = ("ENV_","TOOL_","AXIS_","REF_","VOL_")
EXCLUDE_TYPES = ("App::Part","App::Origin","Spreadsheet::Sheet","App::DocumentObjectGroup")
def _consumed_add(x,out):
    out.add(x.Name)
    for p in ("Links","Group"):
        g=getattr(x,p,None)
        if g is None: continue
        for y in (g if isinstance(g,(list,tuple)) else (g,)):
            if y is not None: _consumed_add(y,out)
def exportable(doc):
    consumed=set()
    for o in doc.Objects:
        if o.TypeId in ("Part::Fuse","Part::Cut","Part::Chamfer","Part::Common","Part::MultiFuse"):
            for p in ("Base","Tool","Shapes"):
                t=getattr(o,p,None)
                if t is None: continue
                for x in (t if isinstance(t,(list,tuple)) else (t,)):
                    if x is not None: _consumed_add(x,consumed)
    return [o for o in doc.Objects if hasattr(o,"Shape") and not o.Shape.isNull()
            and o.Shape.Volume>0 and o.TypeId not in EXCLUDE_TYPES
            and not o.Name.startswith(EXCLUDE_PREFIX) and o.Name not in consumed]
def gshape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
m = App.openDocument(str(ROOT/"cad/master_robot.FCStd"))
mmeta = json.loads((ROOT/"exports/meta/master.json").read_text(encoding="utf-8"))
solids = exportable(m)
shape_map = {o.Name:gshape(o) for o in solids}
# ---- PAR3 unbound
def bound_tree(o, depth=0):
    if depth>8: return False
    if getattr(o,"ExpressionEngine",None): return True
    kids=[]
    for p in ("Base","Tool","Shapes","Links","Group"):
        t=getattr(o,p,None)
        if t is None: continue
        kids += list(t) if isinstance(t,(list,tuple)) else [t]
    return any(bound_tree(k,depth+1) for k in kids if k is not None)
unb=[o.Name for o in solids if not o.Name.startswith("WIRE_") and not bound_tree(o)]
print("PAR3 unbound:",unb)
# ---- FAST1 bad
JMIN={"bearing_":4,"motor_face":4,"mplate_rail":12}
import re as _re
jlines=[l for l in open(str(ROOT/"scripts/freecad/selfcheck_overhaul03.py")) ]
# replicate JMIN from source lines 369-396 read manually -- just report which joints fail and why
def jmin(jid):
    for k,v in JMIN_FULL.items():
        if jid==k: return v
    for k,v in JMIN_FULL.items():
        if jid.startswith(k): return v
    return 1
JMIN_FULL={"bearing_":4,"motor_face":4,"mplate_rail":12,
 "twr_riser":8,"tower_gus":8,"tdeck":8,"susan_lo":4,"susan_hi":4,
 "ring_gear":4,"cheek":8,"fly_brg":16,"fly_motor":8,"mclamp":4,
 "hood_piv":2,"hood_servo":4,"cam_mount":4,"lift_rail":4,"lift_base":4,
 "top_tie":4,"stage_tie":4,"truck":2,"stopper":2,"cradle_arm":4,
 "cradle_piv":1,"tilt_servo":4,"lift_winch":4,"chute_mount":2,
 "chute_lips":8,"chute_tower":2}
embeds={tuple(sorted(x)) for x in mmeta["embeds"]}
bad=[]
for j in mmeta["joints"]:
    jid=j.get("id","?"); hw=list(j.get("bolts",[])); need=jmin(jid)
    if len(hw)<need: bad.append("%s:%d<%d"%(jid,len(hw),need))
    for bt in hw+list(j.get("nuts",[])):
        if not any(bt in pair for pair in embeds):
            bad.append("%s:%s not embedded"%(jid,bt))
print("FAST1 bad:",bad)
# ---- ASM5
eng_bad,nut_bad=[],[]
for j in mmeta.get("joints",[]):
    mems=[x for x in j.get("members",[]) if x in shape_map]
    for bn in j.get("bolts",[]):
        if bn not in shape_map: continue
        if not any(shape_map[bn].distToShape(shape_map[x])[0]<=0.2 for x in mems):
            eng_bad.append((j["id"],bn))
    for nn in j.get("nuts",[]):
        if nn not in shape_map: continue
        on=any(shape_map[nn].common(shape_map[bn]).Volume>0.3
               for bn in j.get("bolts",[]) if bn in shape_map)
        se=any(shape_map[nn].distToShape(shape_map[x])[0]<=0.15 for x in mems)
        if not on: nut_bad.append((j["id"],nn,"not-on-shaft"))
        elif not se: nut_bad.append((j["id"],nn,"floating"))
print("ASM5 bolts:",eng_bad)
print("ASM5 nuts:",nut_bad)
# ---- DECL contacts
emb_pairs={tuple(sorted(x)) for x in mmeta.get("embeds",[])}
cn_bad=[]
for a,b in mmeta.get("contacts",[]):
    if a in shape_map and b in shape_map and tuple(sorted((a,b))) not in emb_pairs:
        d_=shape_map[a].distToShape(shape_map[b])[0]
        com=shape_map[a].common(shape_map[b]).Volume
        if d_>1.5 or com>0.5: cn_bad.append((a,b,round(d_,2),round(com,1)))
print("DECL contacts:",cn_bad)
