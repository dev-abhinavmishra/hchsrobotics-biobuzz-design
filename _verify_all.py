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
print("solids:",len(solids))
def sdist(a,b): return shape_map[a].distToShape(shape_map[b])[0]
def scom(a,b):
    try: return shape_map[a].common(shape_map[b]).Volume
    except Exception: return -1

# ---- PAR3 ----
def bound_tree(o, depth=0):
    if depth>8: return False
    if getattr(o,"ExpressionEngine",None): return True
    kids=[]
    for p in ("Base","Tool","Shapes","Links","Group"):
        t=getattr(o,p,None)
        if t is None: continue
        kids += list(t) if isinstance(t,(list,tuple)) else [t]
    return any(bound_tree(k,depth+1) for k in kids if k is not None)
unb=[o.Name for o in solids if not o.Name.startswith(("WIRE_","ROPE_")) and not bound_tree(o)]
print("PAR3 unbound: %d %s"%(len(unb),unb[:20]))

# ---- FAST1 (real JMIN) ----
JMIN={"bearing_":4,"motor_face":4,"mplate_rail":12,
 "clamp_wall":2,"gusset_rail":2,"gusset_cross":2,"gusset_low":2,
 "crown_pin":2,"post_foot":4,"tie_web":2,"numplate":2,
 "panbrkt_wall":2,"panbrkt_pan":1,"deckpost_web":1,"deckpost_panel":1,
 "hub_pinch":1,"odo_mount":2,"odo_wheelpin":1,"odo_pivot":1,
 "strap_pan":2,"shelf_so":2,"switch_brkt":2,"hub_mount":4,
 "int_bearing":4,"cheek_pivot":1,"cheek_wall":2,"cheek_lock":2,
 "int_motor_face":4,"int_motor_plate":12,"int_motor_post":1,
 "throat_guard":4,"hop_ledge":3,"hop_brkt":2,"agit_brkt":4,
 "agit_servo":4,"feed_bearing":4,"feed_motor_plate":4,
 "feed_plate_post":1,"col_post":2,"gate_brkt":4,"gate_servo":4,
 "div_brkt":4,"div_servo":4,"div_port_flange":4,"snsr_brkt":2,
 "tower_":4,"tdeck_":4,"susan_lo":4,"susan_hi":4,"yaw_tray":4,
 "yaw_servo":4,"ring_gear":4,"cheek_":4,"flybrg_":4,"flymotor_":4,
 "mclamp_":2,"hood_piv":2,"hood_servo":4,"nip_backplate":2,
 "top_brace":2,"cam_mount":4,"lift_base":4,"rail_foot_":2,
 "lift_top_tie":4,"collar_":2,"s1truck_":2,"s2truck_":2,
 "s1_tie":2,"s2_tie":2,"cradle_arm":4,"cradle_piv":1,
 "tilt_servo":4,"lift_winch":4,"chute_mount":2,"chute_lips":8,
 "chute_tower":2}
def _jmin(jid):
    if jid in JMIN: return JMIN[jid]
    for k,v in JMIN.items():
        if jid.startswith(k): return v
    return 1
embeds={tuple(sorted(x)) for x in mmeta["embeds"]}
fast_bad=[]
for j in mmeta["joints"]:
    jid=j.get("id","?"); hw=list(j.get("bolts",[])); need=_jmin(jid)
    if len(hw)<need: fast_bad.append("%s: %d<%d"%(jid,len(hw),need))
    for bt in hw+list(j.get("nuts",[])):
        if not any(bt in pair for pair in embeds):
            fast_bad.append("%s:%s not embedded"%(jid,bt))
print("FAST1 bad: %d"%len(fast_bad))
for x in fast_bad: print("   ",x)

# ---- ASM5 ----
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
print("ASM5 bolts: %d %s"%(len(eng_bad),eng_bad))
print("ASM5 nuts: %d %s"%(len(nut_bad),nut_bad))

# ---- DECL gates ----
emb_bad=[]
for a,b in mmeta.get("embeds",[]):
    if a in shape_map and b in shape_map:
        if scom(a,b)<0.5: emb_bad.append((a,b))
print("DECL_embeds_real bad: %d %s"%(len(emb_bad),emb_bad[:20]))
cn_bad=[]
for a,b in mmeta.get("contacts",[]):
    if a in shape_map and b in shape_map and tuple(sorted((a,b))) not in embeds:
        d_=sdist(a,b); com=scom(a,b)
        if d_>1.5 or com>0.5: cn_bad.append((a,b,round(d_,2),round(com,1)))
print("DECL_contacts_real bad: %d"%len(cn_bad))
for x in cn_bad: print("   ",x)
jl_bad=[]
for a,b in mmeta.get("journals",[]):
    if a in shape_map and b in shape_map:
        if scom(a,b)>0.5: jl_bad.append((a,b))
print("DECL_journals bad: %d %s"%(len(jl_bad),jl_bad[:20]))

# ---- declared pairs for GEO2 + ASM4 ----
def declared_pairs(mm):
    out=set()
    for key in ("faces","embeds","journals","contacts"):
        for p in mm.get(key,[]):
            out.add(frozenset((p[0],p[1])))
    for j in mm.get("joints",[]):
        alln=list(j.get("members",[]))+list(j.get("bolts",[]))+list(j.get("nuts",[]))
        for i in range(len(alln)):
            for k in range(i+1,len(alln)):
                out.add(frozenset((alln[i],alln[k])))
    return out
decl=declared_pairs(mmeta)
decl_t={tuple(sorted((p[0],p[1]))) for key in ("embeds","faces","journals","contacts") for p in mmeta[key]}
for j in mmeta["joints"]:
    ms=j["members"]+j.get("bolts",[])+j.get("nuts",[])
    for i_ in range(len(ms)):
        for k_ in range(i_+1,len(ms)):
            decl_t.add(tuple(sorted((ms[i_],ms[k_]))))

# ---- GEO2 ----
names=list(shape_map)
bbs={n:shape_map[n].BoundBox for n in names}
overlaps=[]
for i_ in range(len(names)):
    a=names[i_]; ba=bbs[a]
    for j_ in range(i_+1,len(names)):
        b=names[j_]
        if tuple(sorted((a,b))) in decl_t: continue
        bb_=bbs[b]
        if (ba.XMax<=bb_.XMin or ba.XMin>=bb_.XMax or
            ba.YMax<=bb_.YMin or ba.YMin>=bb_.YMax or
            ba.ZMax<=bb_.ZMin or ba.ZMin>=bb_.ZMax): continue
        try: com=shape_map[a].common(shape_map[b])
        except Exception: continue
        if com.Volume>0.5: overlaps.append((com.Volume,a,b))
overlaps.sort(reverse=True)
print("GEO2 undeclared overlaps: %d"%len(overlaps))
for v,a,b in overlaps: print("   %8.1f  %s x %s"%(v,a,b))

# ---- GEO3 mount faces ----
f_bad=[]
for a,b in mmeta["faces"]:
    if a not in shape_map or b not in shape_map: continue
    try: d_=shape_map[a].distToShape(shape_map[b])[0]
    except Exception: continue
    if d_>0.1: f_bad.append((round(d_,2),a,b))
print("GEO3 face gaps: %d %s"%(len(f_bad),f_bad[:20]))

# ---- ASM4 coplanar census ----
def axis_face_census(sm):
    buckets={}
    for nm,s in sm.items():
        for f in s.Faces:
            try: su=f.Surface
            except Exception: continue
            if su.TypeId!="Part::GeomPlane": continue
            axv=su.Axis; comps=(abs(axv.x),abs(axv.y),abs(axv.z))
            c=f.CenterOfMass
            if comps==(1.0,0.0,0.0): key=("x",round(c.x,2))
            elif comps==(0.0,1.0,0.0): key=("y",round(c.y,2))
            elif comps==(0.0,0.0,1.0): key=("z",round(c.z,2))
            else: continue
            if f.Area<1.0: continue
            buckets.setdefault(key,[]).append((nm,f))
    seen=set(); pairs=[]
    for key,faces in buckets.items():
        if len(faces)>400: continue
        for i in range(len(faces)):
            for j in range(i+1,len(faces)):
                a,fa=faces[i]; b,fb=faces[j]
                if a==b: continue
                try: com=fa.common(fb)
                except Exception: continue
                pk=(a,b) if a<b else (b,a)
                if com.Area>0.5 and pk not in seen:
                    seen.add(pk); pairs.append((com.Area,a,b))
    pairs.sort(reverse=True)
    return pairs
cop=axis_face_census(shape_map)
undecl=[pp for pp in cop if frozenset((pp[1],pp[2])) not in decl]
print("ASM4 coplanar: %d, undeclared: %d"%(len(cop),len(undecl)))
for ar,a,b in undecl: print("   %8.1f  %s x %s"%(ar,a,b))
print("DONE")
