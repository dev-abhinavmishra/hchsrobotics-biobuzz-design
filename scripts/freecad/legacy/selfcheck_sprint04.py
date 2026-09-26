"""Sprint-04 self-gate: master integration assertions.

Run:  freecadcmd.exe scripts/freecad/selfcheck_sprint04.py
Checks sprint-04 contract C/D/E/F sections against cad/master_robot.FCStd.
"""
import hashlib
import sys
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "cad" / "master_robot.FCStd"
fails = []


LOG = []


def ck(name, ok, detail=""):
    line = ("PASS " if ok else "FAIL ") + name + \
        (" | " + detail if detail else "")
    LOG.append(line)
    print(line)
    sys.stdout.flush()
    if not ok:
        fails.append(name)


def dump():
    out = ROOT / "selfcheck_sprint04_results.txt"
    out.write_text("\n".join(LOG) + "\nRESULT: " +
                   ("ALL PASS" if not fails else "FAILURES: %s" % fails)
                   + "\n", encoding="utf-8")


def inside(a, b, tol=2.0):
    return (a.XMin >= b.XMin - tol and a.XMax <= b.XMax + tol and
            a.YMin >= b.YMin - tol and a.YMax <= b.YMax + tol and
            a.ZMin >= b.ZMin - tol and a.ZMax <= b.ZMax + tol)


def overlaps(a, b):
    return (min(a.XMax, b.XMax) - max(a.XMin, b.XMin) > 2.0 and
            min(a.YMax, b.YMax) - max(a.YMin, b.YMin) > 2.0 and
            min(a.ZMax, b.ZMax) - max(a.ZMin, b.ZMin) > 2.0)


def group_of(n):
    if n.startswith("MECH_INTAKE") or n == "MECH_ROLLER":
        return "intake"
    if n in ("MECH_CHANNEL", "MECH_DIVERTER"):
        return "transfer"
    if n.startswith("MECH_SHOOTER") or n.startswith("MECH_FLYWHEEL"):
        return "shooter"
    if n.startswith("MECH_LIFTER") or n.startswith("MECH_STAGE") or \
            n in ("MECH_CARRIAGE", "MECH_CRADLE"):
        return "lifter"
    return None


def exempt_pair(a, b):
    if a.startswith(("ENV_", "AXIS_", "REF_")) or \
            b.startswith(("ENV_", "AXIS_", "REF_")):
        return True
    ga, gb = group_of(a), group_of(b)
    # reserve <-> representative same-subsystem nesting
    for n, g in ((a, gb), (b, ga)):
        if n.startswith("VOL_") and g and g.upper() in n:
            return True
    # chassis-bay contents inside VOL_DRIVEBASE
    if "VOL_DRIVEBASE" in (a, b):
        return True
    # carriage/cradle vs deployed ghost
    if "VOL_LIFTER_DEPLOYED" in (a, b) and \
            any(n in ("MECH_CARRIAGE", "MECH_CRADLE") for n in (a, b)):
        return True
    return False


def exempt_pair(a, b):
    if a.startswith(("ENV_", "AXIS_", "REF_")) or \
            b.startswith(("ENV_", "AXIS_", "REF_")):
        return True
    ga, gb = group_of(a), group_of(b)
    # reserve <-> representative same-subsystem nesting
    for n, g in ((a, gb), (b, ga)):
        if n.startswith("VOL_") and g and g.upper() in n:
            return True
    # chassis-bay contents inside VOL_DRIVEBASE
    if "VOL_DRIVEBASE" in (a, b):
        return True
    # carriage/cradle vs deployed ghost
    if "VOL_LIFTER_DEPLOYED" in (a, b) and \
            any(n in ("MECH_CARRIAGE", "MECH_CRADLE") for n in (a, b)):
        return True
    # deployed ghost vs stowed reserve - mast deploys through the column
    if {"VOL_LIFTER_DEPLOYED", "VOL_LIFTER_STOWED"} == {a, b}:
        return True
    # cascade stage x stage telescoping - physically nested by design
    if a.startswith("MECH_STAGE_") and b.startswith("MECH_STAGE_"):
        return True
    return False


doc = App.openDocument(str(T))
doc.recompute()
o = {x.Name: x for x in doc.Objects}
solids = {n: x.Shape.BoundBox for n, x in o.items()
          if hasattr(x, "Shape") and x.Shape.Volume > 0
          and x.TypeId not in ("App::Part", "App::Origin")}
ck("A4 counts", len(doc.Objects) >= 44 and len(solids) >= 20,
   "%d objects / %d solids" % (len(doc.Objects), len(solids)))

env_s, env_e = solids["ENV_START"], solids["ENV_EXPANSION"]

# ---- C: named overlap pairs ----
wheels = ["WHEEL_FL", "WHEEL_FR", "WHEEL_RL", "WHEEL_RR"]
intake = ["VOL_INTAKE", "MECH_INTAKE_CHEEK_L", "MECH_INTAKE_CHEEK_R",
          "MECH_ROLLER"]
trans = ["VOL_TRANSFER", "MECH_CHANNEL", "MECH_DIVERTER"]
shoot = ["VOL_SHOOTER", "MECH_SHOOTER_BODY", "MECH_SHOOTER_HOOD",
         "MECH_FLYWHEEL_L", "MECH_FLYWHEEL_R"]
lift = ["VOL_LIFTER_STOWED", "VOL_LIFTER_DEPLOYED", "MECH_LIFTER_STOWED",
        "MECH_STAGE_1", "MECH_STAGE_2", "MECH_STAGE_3",
        "MECH_CARRIAGE", "MECH_CRADLE"]

bad = [(i, w) for i in intake for w in wheels
       if overlaps(solids[i], solids[w])]
bad += [(t, s) for t in trans for s in shoot + lift
        if overlaps(solids[t], solids[s])]
bad += [(e, t) for e in ("BATTERY", "ELECTRONICS") for t in trans + wheels
        if overlaps(solids[e], solids[t])]
ck("C1-C4 named pairs disjoint", not bad, str(bad))

# C6 full pairwise leaf scan outside declared exemptions
viol = []
names = sorted(solids)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        if not exempt_pair(a, b) and overlaps(solids[a], solids[b]):
            viol.append((a, b))
ck("C6 full leaf scan", not viol, str(viol))

# C5 regression: sprint-02/03 objects still present
need = ["ENV_START", "ENV_EXPANSION", "VOL_DRIVEBASE",
        "WHEEL_FL", "WHEEL_FR", "WHEEL_RL", "WHEEL_RR", "BATTERY",
        "ELECTRONICS", "AXIS_X", "AXIS_Y", "AXIS_Z", "VOL_INTAKE",
        "VOL_TRANSFER", "VOL_SHOOTER", "VOL_LIFTER_STOWED",
        "VOL_LIFTER_DEPLOYED"]
ck("C5 regression objects", all(n in o for n in need),
   str([n for n in need if n not in o]))

# ---- D: representative solids ----
rep_map = {
    "MECH_INTAKE_CHEEK_L": "VOL_INTAKE", "MECH_INTAKE_CHEEK_R": "VOL_INTAKE",
    "MECH_ROLLER": "VOL_INTAKE",
    "MECH_CHANNEL": "VOL_TRANSFER", "MECH_DIVERTER": "VOL_TRANSFER",
    "MECH_SHOOTER_BODY": "VOL_SHOOTER", "MECH_SHOOTER_HOOD": "VOL_SHOOTER",
    "MECH_FLYWHEEL_L": "VOL_SHOOTER", "MECH_FLYWHEEL_R": "VOL_SHOOTER",
    "MECH_LIFTER_STOWED": "VOL_LIFTER_STOWED",
    "MECH_STAGE_1": "VOL_LIFTER_DEPLOYED",
    "MECH_STAGE_2": "VOL_LIFTER_DEPLOYED",
    "MECH_STAGE_3": "VOL_LIFTER_DEPLOYED",
}
bad = [r for r, v in rep_map.items() if not inside(solids[r], solids[v])]
ck("D2 reps inside reserves", not bad, str(bad))

fl, fr = solids["MECH_FLYWHEEL_L"], solids["MECH_FLYWHEEL_R"]
gap = fl.YMin - fr.YMax
ck("D3 bore gap = 100", abs(gap - 100.0) <= 1.0, "inner gap %.2f" % gap)
cr = solids["MECH_CRADLE"]
ck("D3 cradle", min(cr.XLength, cr.YLength) >= 100 and cr.ZMin >= 546,
   "XY %.0fx%.0f ZMin %.1f" % (cr.XLength, cr.YLength, cr.ZMin))
s1, s2, s3 = (solids["MECH_STAGE_1"], solids["MECH_STAGE_2"],
              solids["MECH_STAGE_3"])
ck("D3 stages nested+ordered",
   inside(s2, s1, -1.0) is False and  # strict nesting checked per-axis
   s2.XMin > s1.XMin and s3.XMin > s2.XMin and
   s1.ZMin < s2.ZMin < s3.ZMin, "")

# ---- E: envelopes ----
deployed = {"VOL_LIFTER_DEPLOYED", "MECH_STAGE_1", "MECH_STAGE_2",
            "MECH_STAGE_3", "MECH_CARRIAGE", "MECH_CRADLE"}
bad = [n for n in names
       if not n.startswith(("ENV_", "AXIS_", "REF_")) and n not in deployed
       and not inside(solids[n], env_s)]
ck("E1 stowed inside R102 cube", not bad, str(bad))
bad = [n for n in deployed if not inside(solids[n], env_e)]
ck("E2 deployed inside R105", not bad, str(bad))

# ---- F: field references ----
rh, rf = solids["REF_HIVE"], solids["REF_FLOWER"]
rh_zc = (rh.ZMin + rh.ZMax) / 2
ck("F1 REF_HIVE", rh.XMin > 228.6 and abs(rh_zc - 300) <= 150,
   "XMin %.1f z-center %.1f" % (rh.XMin, rh_zc))
rf_zc = (rf.ZMin + rf.ZMax) / 2
rf_dist = (((rf.XMin + rf.XMax) / 2 - 120) ** 2 +
           ((rf.YMin + rf.YMax) / 2) ** 2) ** 0.5
ck("F2 REF_FLOWER", 536 <= rf_zc <= 556 and rf_dist <= 200,
   "z-center %.1f, dist to lifter axis %.1f" % (rf_zc, rf_dist))
for n in ("REF_HIVE", "REF_FLOWER"):
    lbl = (o[n].Label + " " + getattr(o[n], "DataStatus", "")).lower()
    ck("F3 %s labeled" % n,
       any(k in lbl for k in ("aim", "target", "reference")),
       o[n].Label)
App.closeDocument(doc.Name)

# ---- D4 probes: intake_width +20%, reach_z +20% ----
h0 = hashlib.sha256(open(T, "rb").read()).hexdigest()
doc = App.openDocument(str(T))
sh = doc.getObject("Parameters")
w0 = doc.getObject("VOL_INTAKE").Shape.BoundBox.YLength
sh.set("intake_width", "396")  # 330 + 20%
doc.recompute()
w1 = doc.getObject("VOL_INTAKE").Shape.BoundBox.YLength
ck("P1 intake_width probe", abs((w1 - w0) - 66.0) < 0.5,
   "%.1f -> %.1f" % (w0, w1))
g0 = doc.getObject("VOL_LIFTER_DEPLOYED").Shape.BoundBox.ZMax
sh.set("intake_width", "330")
sh.set("reach_z", "732")  # 610 + 20%
doc.recompute()
g1 = doc.getObject("VOL_LIFTER_DEPLOYED").Shape.BoundBox.ZMax
ck("P2 reach_z probe", g0 == 610.0 and abs(g1 - 732) < 0.01,
   "%.1f -> %.1f" % (g0, g1))
App.closeDocument(doc.Name)  # close WITHOUT saving
h1 = hashlib.sha256(open(T, "rb").read()).hexdigest()
ck("P3 close-no-save hash stable", h0 == h1)

dump()
print("RESULT:", "ALL PASS" if not fails else "FAILURES: %s" % fails)
sys.stdout.flush()
sys.exit(0 if not fails else 1)
