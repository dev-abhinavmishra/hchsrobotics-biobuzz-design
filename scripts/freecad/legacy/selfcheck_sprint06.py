"""Sprint-06 self-gate: detail + accuracy assertions on the master.

SUPERSEDED as of rehaul sprint-01 -- the active gate is
selfcheck_rehaul01.py. This file is retained so the archived sprint-07
baseline can still be validated against its own contract; pass the
baseline archive path as argv[1], e.g.:

  freecadcmd.exe scripts/freecad/selfcheck_sprint06.py
      cad/archive/master_robot_sprint07_baseline_20260920_200910.FCStd

(NB: it will FAIL against the rebuilt master_robot.FCStd -- object
names, placement conventions, and the declared-overlap table all
changed in the rehaul.)

Original notes:
Supersedes selfcheck_sprint04.py (same checks, updated for sprint-06):
- C4 exemption table = sprint-04 classes + the 9 classes enumerated in
  the sprint-06 contract v3
- roller geometry: 10/wheel, inside ENV_WHEEL_* + ENV_START, ~45 deg
  slant, FTC X-pattern (FL+RR vs FR+RL)
- intake_width probe updated to the datasheet-driven 326 mm value
"""
import hashlib
import math
import sys
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
T = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 \
    else ROOT / "cad" / "master_robot.FCStd"
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
    out = ROOT / "selfcheck_sprint06_results.txt"
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
    if n.startswith("MECH_INTAKE") or n == "MECH_ROLLER" or \
            n.startswith("PIVOT_MOUNT"):
        return "intake"
    if n in ("MECH_CHANNEL", "MECH_DIVERTER", "DIVERTER_HORN"):
        return "transfer"
    if n.startswith("MECH_SHOOTER") or n.startswith("MECH_FLYWHEEL") or \
            n.startswith("STUB_SHAFT"):
        return "shooter"
    if n.startswith("MECH_LIFTER") or n.startswith("MECH_STAGE") or \
            n in ("MECH_CARRIAGE", "MECH_CRADLE", "STAGE_GUIDE_L",
                  "STAGE_GUIDE_R", "CRADLE_LIP"):
        return "lifter"
    return None


def wheel_of(n):
    for w in ("FL", "FR", "RL", "RR"):
        if n.startswith("ROLLER_" + w):
            return "WHEEL_" + w
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
    # deployed ghost vs stowed reserve - mast deploys through the column
    if {"VOL_LIFTER_DEPLOYED", "VOL_LIFTER_STOWED"} == {a, b}:
        return True
    # cascade stage x stage telescoping - physically nested by design
    if a.startswith("MECH_STAGE_") and b.startswith("MECH_STAGE_"):
        return True
    # ---- sprint-06 enumerated classes ----
    # rollers embedded in their own wheel rim
    wa, wb = wheel_of(a), wheel_of(b)
    if wa and b == wa or wb and a == wb:
        return True
    # motor mount plates bolted to chassis members (drivebase concept)
    if a.startswith("MOUNT_MOTOR_") or b.startswith("MOUNT_MOTOR_"):
        if any(n.startswith(("RAIL_", "CHASSIS", "MOUNT_MOTOR_"))
               for n in (a, b)):
            return True
    # pivot bosses on intake cheeks
    if {a, b} - {"PIVOT_MOUNT_L", "PIVOT_MOUNT_R"} != {a, b}:
        if any(n.startswith(("MECH_INTAKE_CHEEK", "PIVOT_MOUNT"))
               for n in (a, b)):
            return True
    # servo horn fixed to the diverter paddle
    if {a, b} == {"DIVERTER_HORN", "MECH_DIVERTER"}:
        return True
    # stub shafts through flywheel bores
    if a.startswith("STUB_SHAFT_") or b.startswith("STUB_SHAFT_"):
        if any(n.startswith(("MECH_FLYWHEEL", "STUB_SHAFT"))
               for n in (a, b)):
            return True
    # stage guide blocks riding stage walls
    if a.startswith("STAGE_GUIDE_") or b.startswith("STAGE_GUIDE_"):
        if any(n.startswith(("MECH_STAGE_", "STAGE_GUIDE_"))
               for n in (a, b)):
            return True
    # cradle lip integral to cradle
    if {a, b} == {"CRADLE_LIP", "MECH_CRADLE"}:
        return True
    # electronics rails under the hub volume
    if a.startswith("ELEC_RAIL_") or b.startswith("ELEC_RAIL_"):
        if any(n.startswith(("ELECTRONICS", "ELEC_RAIL_"))
               for n in (a, b)):
            return True
    # ---- sprint-07 cohesion classes (frame/mount contact) ----
    # frame ring + sheets meet each other, reserves, and things mounted
    # on/through them (cheeks, intake roller, channel, battery, elec)
    if a.startswith(("FRAME_", "BELLY_PAN", "REAR_DECK")) or \
            b.startswith(("FRAME_", "BELLY_PAN", "REAR_DECK")):
        if any(n.startswith(("FRAME_", "BELLY_PAN", "REAR_DECK", "VOL_",
                             "MECH_INTAKE_CHEEK", "MECH_ROLLER",
                             "MECH_CHANNEL", "BATTERY", "ELECTRONICS",
                             "ELEC_RAIL", "MOTOR_", "WHEEL_"))
               for n in (a, b)):
            return True
    # motors bolt to side rails and meet wheel hubs
    if a.startswith("MOTOR_") or b.startswith("MOTOR_"):
        if any(n.startswith(("MOTOR_", "FRAME_", "WHEEL_", "VOL_",
                             "BELLY_PAN", "REAR_DECK"))
               for n in (a, b)):
            return True
    # wheel side plates face their own wheel + rollers
    if a.startswith("WHEEL_PLATE_") or b.startswith("WHEEL_PLATE_"):
        if any(n.startswith(("WHEEL_PLATE_", "WHEEL_", "ROLLER_"))
               for n in (a, b)):
            return True
    # intake pivot axle through both cheek plates / boss
    if "INTAKE_AXLE" in (a, b):
        if any(n.startswith(("MECH_INTAKE_CHEEK", "PIVOT_MOUNT",
                             "INTAKE_AXLE", "VOL_"))
               for n in (a, b)):
            return True
    # shooter upright posts stand on deck/frame under the reserve
    if a.startswith("POST_SHOOTER_") or b.startswith("POST_SHOOTER_"):
        if any(n.startswith(("POST_SHOOTER_", "REAR_DECK", "FRAME_",
                             "VOL_", "MECH_SHOOTER"))
               for n in (a, b)):
            return True
    # lifter pedestal/base tie the mast column to pan/deck/frame
    if a.startswith(("LIFTER_BASE", "LIFTER_PED")) or \
            b.startswith(("LIFTER_BASE", "LIFTER_PED")):
        if any(n.startswith(("LIFTER_BASE", "LIFTER_PED", "REAR_DECK",
                             "BELLY_PAN", "FRAME_", "VOL_", "MECH_CHANNEL",
                             "MECH_LIFTER", "MECH_STAGE"))
               for n in (a, b)):
            return True
    return False


doc = App.openDocument(str(T))
doc.recompute()
o = {x.Name: x for x in doc.Objects}
solids = {n: x.Shape.BoundBox for n, x in o.items()
          if hasattr(x, "Shape") and x.Shape.Volume > 0
          and x.TypeId not in ("App::Part", "App::Origin")}
ck("A4 counts", len(doc.Objects) >= 100 and len(solids) >= 70,
   "%d objects / %d solids" % (len(doc.Objects), len(solids)))

env_s, env_e = solids["ENV_START"], solids["ENV_EXPANSION"]

# ---- C: named overlap pairs ----
wheels = ["WHEEL_FL", "WHEEL_FR", "WHEEL_RL", "WHEEL_RR"]
intake = ["VOL_INTAKE", "MECH_INTAKE_CHEEK_L", "MECH_INTAKE_CHEEK_R",
          "MECH_ROLLER", "PIVOT_MOUNT_L", "PIVOT_MOUNT_R"]
trans = ["VOL_TRANSFER", "MECH_CHANNEL", "MECH_DIVERTER", "DIVERTER_HORN"]
shoot = ["VOL_SHOOTER", "MECH_SHOOTER_BODY", "MECH_SHOOTER_HOOD",
         "MECH_FLYWHEEL_L", "MECH_FLYWHEEL_R", "STUB_SHAFT_L",
         "STUB_SHAFT_R"]
lift = ["VOL_LIFTER_STOWED", "VOL_LIFTER_DEPLOYED", "MECH_LIFTER_STOWED",
        "MECH_STAGE_1", "MECH_STAGE_2", "MECH_STAGE_3",
        "MECH_CARRIAGE", "MECH_CRADLE", "STAGE_GUIDE_L", "STAGE_GUIDE_R",
        "CRADLE_LIP"]

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

# C5 regression: sprint-02..05 objects still present
need = ["ENV_START", "ENV_EXPANSION", "VOL_DRIVEBASE",
        "WHEEL_FL", "WHEEL_FR", "WHEEL_RL", "WHEEL_RR", "BATTERY",
        "ELECTRONICS", "AXIS_X", "AXIS_Y", "AXIS_Z", "VOL_INTAKE",
        "VOL_TRANSFER", "VOL_SHOOTER", "VOL_LIFTER_STOWED",
        "VOL_LIFTER_DEPLOYED",
        "ENV_WHEEL_FL", "ENV_WHEEL_FR", "ENV_WHEEL_RL", "ENV_WHEEL_RR",
        "PIVOT_MOUNT_L", "PIVOT_MOUNT_R", "DIVERTER_HORN",
        "STUB_SHAFT_L", "STUB_SHAFT_R",
        "STAGE_GUIDE_L", "STAGE_GUIDE_R", "CRADLE_LIP",
        "ELEC_RAIL_L", "ELEC_RAIL_R"]
ck("C5 regression objects", all(n in o for n in need),
   str([n for n in need if n not in o]))

# ---- R: roller geometry (sprint-06 C1/C5) ----
sh = doc.getObject("Parameters")
wxo = float(sh.get("wheel_x_offset"))
wyo = float(sh.get("wheel_y_offset"))
wcent = {"FL": (wxo, wyo, 1), "FR": (wxo, -wyo, -1),
         "RL": (-wxo, wyo, -1), "RR": (-wxo, -wyo, 1)}
slant_bad, env_bad, count_bad, patt_bad = [], [], [], []
for w, (wx, wy, sgn) in wcent.items():
    env = solids["ENV_WHEEL_" + w]
    rs = [n for n in names if n.startswith("ROLLER_%s_" % w)]
    if len(rs) != 10:
        count_bad.append("%s:%d" % (w, len(rs)))
    for rn in rs:
        k = int(rn[-2:])
        th = math.radians(k * 36.0)
        rh = (math.cos(th), 0.0, math.sin(th))      # radial dir
        tt = (-math.sin(th), 0.0, math.cos(th))      # tangent dir
        obj = o[rn]
        # cylinder axis from the cylindrical face
        ax = None
        for f in obj.Shape.Faces:
            if f.Surface.TypeId == "Part::GeomCylinder":
                ax = f.Surface.Axis
                break
        if ax is None:
            slant_bad.append(rn + ":no-cyl-face")
            continue
        a = (ax.x, ax.y, ax.z)
        # canonicalize: cylinder axis is unoriented; true slant axis has
        # a.y = cos(45) > 0
        if a[1] < 0:
            a = (-a[0], -a[1], -a[2])
        # slant ~45 deg: axis.Y ~ cos45; axis perpendicular to radial
        ay = a[1]
        rad = abs(a[0] * rh[0] + a[2] * rh[2])
        if not (0.66 <= ay <= 0.75) or rad > 0.15:
            slant_bad.append("%s ay=%.3f rad=%.3f" % (rn, ay, rad))
        # X-pattern: sign(axis.tangent) == sgn
        dot_t = a[0] * tt[0] + a[2] * tt[2]
        if (dot_t > 0) != (sgn > 0):
            patt_bad.append(rn)
        # inside ENV_WHEEL_* (roller OD defines the wheel O96) + ENV_START
        bb = obj.Shape.BoundBox
        if not inside(bb, env, tol=0.6):
            env_bad.append(rn + ":env")
        if not inside(bb, env_s, tol=0.6):
            env_bad.append(rn + ":start")
ck("R1 roller count 10/wheel", not count_bad, str(count_bad))
ck("R2 roller slant ~45deg + radial-normal", not slant_bad,
   str(slant_bad[:4]))
ck("R3 X-pattern slant (FL+RR vs FR+RL)", not patt_bad, str(patt_bad[:4]))
ck("R4 rollers inside ENV_WHEEL_* + ENV_START", not env_bad,
   str(env_bad[:4]))

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
   inside(s2, s1, -1.0) is False and
   s2.XMin > s1.XMin and s3.XMin > s2.XMin and
   s1.ZMin < s2.ZMin < s3.ZMin, "")

# ---- E: envelopes ----
deployed = {"VOL_LIFTER_DEPLOYED", "MECH_STAGE_1", "MECH_STAGE_2",
            "MECH_STAGE_3", "MECH_CARRIAGE", "MECH_CRADLE",
            "STAGE_GUIDE_L", "STAGE_GUIDE_R", "CRADLE_LIP"}
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

# ---- probes: intake_width +20% (326->391.2), reach_z +20% ----
h0 = hashlib.sha256(open(T, "rb").read()).hexdigest()
doc = App.openDocument(str(T))
sh = doc.getObject("Parameters")
w0 = doc.getObject("VOL_INTAKE").Shape.BoundBox.YLength
sh.set("intake_width", "391.2")  # 326 + 20%
doc.recompute()
w1 = doc.getObject("VOL_INTAKE").Shape.BoundBox.YLength
ck("P1 intake_width probe", abs((w1 - w0) - 65.2) < 0.5,
   "%.1f -> %.1f" % (w0, w1))
g0 = doc.getObject("VOL_LIFTER_DEPLOYED").Shape.BoundBox.ZMax
sh.set("intake_width", "326")
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
