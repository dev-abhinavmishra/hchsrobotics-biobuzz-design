import json
import FreeCAD as App

M = r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd"
doc = App.openDocument(M)
doc.recompute()

consumed = set()
for o in doc.Objects:
    if o.TypeId in ("Part::Fuse", "Part::Cut", "Part::Chamfer",
                    "Part::Common", "Part::MultiFuse"):
        for p in ("Base", "Tool", "Shapes"):
            t = getattr(o, p, None)
            if t is None:
                continue
            for x in (t if isinstance(t, (list, tuple)) else (t,)):
                if x is not None:
                    consumed.add(x.Name)

solids = [o for o in doc.Objects
          if hasattr(o, "Shape") and not o.Shape.isNull()
          and o.Shape.Volume > 0
          and o.TypeId not in ("App::Part", "Part::Compound")
          and not o.Name.startswith(("TOOL_", "ENV_", "AXIS_",
                                     "COORD_", "Parameters"))
          and o.Name not in consumed]
print("solids", len(solids))

# PAR3 - unbound
unb = []
for o in solids:
    ee = getattr(o, "ExpressionEngine", None)
    if ee:
        continue
    kids = []
    for p in ("Base", "Tool", "Shapes"):
        t = getattr(o, p, None)
        if t is None:
            continue
        kids += list(t) if isinstance(t, (list, tuple)) else [t]
    if not any(getattr(k, "ExpressionEngine", None)
               for k in kids if k is not None):
        unb.append((o.Name, o.TypeId))
print("UNBOUND %d:" % len(unb), unb[:50])

# PROV - unlabeled
unl = []
for o in solids:
    if not any(s in o.Label for s in
               ("UNVERIFIED", "VENDOR-PENDING", "VERIFIED")):
        unl.append(o.Name)
print("UNLABELED %d:" % len(unl), unl[:50])

# ASM1 - ungrouped
def topg(o):
    p = o.getParentGeoFeatureGroup()
    top = None
    while p is not None:
        if p.Name.startswith("GRP_"):
            top = p
        p = p.getParentGeoFeatureGroup()
    return top
ung = [o.Name for o in solids if topg(o) is None]
print("UNGROUPED %d:" % len(ung), ung[:60])

# FAST - joints below minimum
meta = json.load(open(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\exports\meta\master.json"))
JMIN = {"bearing_": 4, "motor_face": 4, "mplate_rail": 12,
        "clamp_wall": 2, "gusset_rail": 4, "gusset_cross": 4,
        "gusset_low": 2, "crown_pin": 2, "post_foot": 4,
        "tie_web": 2, "numplate": 2, "panbrkt_wall": 2,
        "panbrkt_pan": 2, "deckpost_web": 1, "deckpost_panel": 1,
        "hub_pinch": 1, "odo_mount": 2, "odo_wheelpin": 1,
        "odo_pivot": 1, "strap_pan": 2, "shelf_so": 2,
        "switch_brkt": 4, "hub_mount": 4}
em = {tuple(sorted(x)) for x in meta["embeds"]}
for j in meta["joints"]:
    jid = j.get("id", "?")
    hw = list(j.get("bolts", []))
    need = JMIN.get(jid, 1)
    msgs = []
    if len(hw) < need:
        msgs.append("BOLTS %d<%d" % (len(hw), need))
    for bt in hw + list(j.get("nuts", [])):
        if not any(bt in pair for pair in em):
            msgs.append("%s noembed" % bt)
    if msgs:
        print("JOINT", jid, msgs)
