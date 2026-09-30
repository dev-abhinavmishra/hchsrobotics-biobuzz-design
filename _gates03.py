"""Fast focused re-check of the sprint-03 failing gates against the
master doc + meta -- skips DET2/PAR mutation phases. Run:
    freecadcmd _gates03.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "scripts", "freecad"))
import FreeCAD as App
import Part  # noqa
import dt_lift

ROOT = os.getcwd()
CAD = os.path.join(ROOT, "cad")
EXPORTS = os.path.join(ROOT, "exports")

EXCLUDE_TYPES = ("App::DocumentObjectGroup", "App::Part",
                 "Spreadsheet::Sheet", "PartDesign::Body",
                 "App::LinkGroup", "App::Link")


def _consumed_add(o, s):
    if o is None:
        return
    s.add(o.Name)
    try:
        s.update(x.Name for x in o.OutList)
    except Exception:
        pass


def exportable(doc):
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
                        _consumed_add(x, consumed)
    return [o for o in doc.Objects
            if hasattr(o, "Shape") and not o.Shape.isNull()
            and o.Shape.Volume > 0
            and o.TypeId not in EXCLUDE_TYPES
            and o.Name not in consumed]


def gshape(o):
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    return s


doc = App.openDocument(os.path.join(CAD, "master_robot.FCStd"))
mmeta = json.load(open(os.path.join(EXPORTS, "meta", "master.json")))

solids = exportable(doc)
shape_map = {o.Name: gshape(o) for o in solids}
print("shapes:", len(shape_map))


def com(a, b):
    try:
        return shape_map[a].common(shape_map[b]).Volume
    except Exception:
        return -1


def dist(a, b):
    try:
        return shape_map[a].distToShape(shape_map[b])[0]
    except Exception:
        return -1


print("\n== previously-failing / touched overlap pairs ==")
for a, b in (("LIFT_S2_BAR", "LIFT_WINCH"), ("HUB_EXP", "TOWER_L"),
             ("HUB_EXP", "TOWER_GUS_L0"), ("HOOD", "TURRET_TOP_BRACE"),
             ("LIFT_PULLEY", "LIFT_S1_TIE"),
             ("LIFT_TOP_PULLEY", "LIFT_TOP_TIE"),
             ("LIFT_TOP_PULLEY", "LIFT_PULLEY"),
             ("CRADLE_PIV", "CRADLE_ARM"), ("CRADLE_PIV", "TILT_SERVO"),
             ("TILT_SERVO", "CRADLE_CUP"), ("CRADLE_ARM", "CRADLE_CUP"),
             ("ROPE_DYNEEMA", "LIFT_TOP_PULLEY"),
             ("ROPE_DYNEEMA", "LIFT_PULLEY"),
             ("FLY_MCLAMP_L", "FLY_MOTOR_L"),
             ("FLY_MCLAMP_R", "FLY_MOTOR_R"),
             ("LIFT_RAIL_L", "LIFT_BASE"),
             ("LAZY_SUSAN_HI", "TURRET_PLATE"),
             ("LAZY_SUSAN_LO", "TURRET_DECK"),
             ("LOAD_CHUTE", "TOWER_L"),
             ("CHUTE_TOWER_PAD", "LOAD_CHUTE"),
             ("CHUTE_TOWER_PAD", "TOWER_L"),
             ("HUB_EXP", "TOWER_GUS_L1"),
             ("BOLT_GUS_L0_0", "TOWER_L"),
             ("BOLT_GUS_L0_1", "TOWER_L"),
             ("ELEC_SHELF", "TOWER_L"),
             ("LIFT_BASE", "TIE_RB_L"),
             ("LIFT_RAIL_L", "TIE_RB_L")):
    print("  %-22s %-18s common=%.2f dist=%.3f"
          % (a, b, com(a, b), dist(a, b)))

print("\n== ball path stations S15/S16 ==")
p0c, p1c, p2c = dt_lift.CHUTE_PTS
d1c, w1, n1c, L1 = dt_lift._frame_for(p0c, p1c)
d2c, w2, n2c, L2 = dt_lift._frame_for(p1c, p2c)
m1 = (App.Vector(*p0c) + App.Vector(*p1c)) * 0.5 + n1c * 46.5
m2 = (App.Vector(*p1c) + App.Vector(*p2c)) * 0.5 + n2c * 46.5
for nm, c in (("S15", m1), ("S16", m2)):
    ball = Part.makeSphere(46.5, c)
    print("  %s center (%.1f, %.1f, %.1f)" % (nm, c.x, c.y, c.z))
    for o_name, sh in shape_map.items():
        if o_name.startswith(("LOAD_CHUTE", "CHUTE_LIP", "CHUTE_PORT",
                              "CHUTE_TOWER_PAD", "CRADLE_", "TILT_",
                              "ROPE_", "SCRW_CHL")):
            continue
        try:
            v = ball.common(sh).Volume
        except Exception:
            continue
        if v > 0.5:
            print("    BALL x %-20s %.1f mm3" % (o_name, v))

print("\n== chute leg angles ==")
for nm_, pa, pb in (("leg1", p0c, p1c), ("leg2", p1c, p2c)):
    dv = App.Vector(*pb) - App.Vector(*pa)
    horiz = math.hypot(dv.x, dv.y)
    print("  %s %.1f deg" % (nm_, math.degrees(math.atan2(-dv.z, horiz))))

print("\n== GEOL lift pieces ==")
rl = shape_map.get("LIFT_RAIL_L")
rr = shape_map.get("LIFT_RAIL_R")
if rl and rr:
    rlx = rl.BoundBox
    rlx.add(rr.BoundBox)
    print("  rail union x %.1f..%.1f y %.1f..%.1f z ..%.1f"
          % (rlx.XMin, rlx.XMax, rlx.YMin, rlx.YMax, rlx.ZMax))
    for nm, s in sorted(shape_map.items()):
        if nm.startswith(("LIFT_S1_TRUCK_", "LIFT_S2_TRUCK_")):
            b = s.BoundBox
            out = (b.XMin < rlx.XMin - 1 or b.XMax > rlx.XMax + 1 or
                   b.YMin < rlx.YMin - 1 or b.YMax > rlx.YMax + 1)
            print("  %-18s x%.1f..%.1f y%.1f..%.1f %s"
                  % (nm, b.XMin, b.XMax, b.YMin, b.YMax,
                     "OUT" if out else "ok"))
    rtop = rlx.ZMax
    for nm, bn, vn in (("S1", "LIFT_S1_BAR_L", "VOL_S1_DEP"),
                       ("S2", "LIFT_S2_BAR", "VOL_S2_DEP")):
        bo = doc.getObject(bn)
        vo = doc.getObject(vn)
        if bo is None or vo is None:
            print("  missing", bn, vn)
            continue
        bs = vo.Shape.copy()
        bs.Placement = vo.getGlobalPlacement()
        bb = shape_map[bn].BoundBox if bn in shape_map else bs.BoundBox
        vb = bs.BoundBox
        travel = vb.ZMax - bb.ZMax
        overlap = rtop - (bb.ZMin + travel)
        print("  %s travel=%.1f overlap=%.1f %s"
              % (nm, travel, overlap, "FAIL" if overlap < 40 else "ok"))
    for cn_ in ("STOP_COLLAR_L", "STOP_COLLAR_R"):
        co = doc.getObject(cn_)
        if co:
            cb = shape_map[cn_].BoundBox
            print("  %s z%.1f..%.1f rtop %.1f %s"
                  % (cn_, cb.ZMin, cb.ZMax, rtop,
                     "FAIL" if (cb.ZMin < rtop - 20 or
                                cb.ZMax > rtop + 1.5) else "ok"))
cup = shape_map.get("CRADLE_CUP")
if cup:
    bores = []
    for f in cup.Faces:
        try:
            su = f.Surface
        except Exception:
            continue
        if su.TypeId == "Part::GeomCylinder" and abs(su.Axis.y) > 0.99:
            bores.append(su.Radius)
    print("  cradle bore dia %.1f %s"
          % (max(bores) * 2 if bores else 0,
             "FAIL" if not bores or max(bores) * 2 < 99 else "ok"))

print("\n== hood yaw sweep probes ==")
rot_pref = ("TURRET_PLATE", "TURRET_TOP_BRACE", "RING_",
            "LAUNCH_", "FLY_", "FLYWHEEL_", "HOOD", "NIP_",
            "VSN_", "CAM_", "YAW_MAGNET", "YAW_PINION",
            "YAW_SHAFT", "WIRE_")
rot_names = {o.Name for o in solids if o.Name.startswith(rot_pref)}
rot_hw = set()
for j in mmeta.get("joints", []):
    if any(x in rot_names for x in j.get("members", [])):
        rot_hw.update(j.get("bolts", []))
        rot_hw.update(j.get("nuts", []))
yaw_pr = [o for o in doc.Objects if o.Name.startswith("VOL_YAW_")]
print("  %d probes" % len(yaw_pr))
for vo in yaw_pr:
    vs = gshape(vo)
    for o_name, sh in shape_map.items():
        if o_name in rot_names or o_name in rot_hw:
            continue
        try:
            v = vs.common(sh).Volume
        except Exception:
            continue
        if v > 0.5:
            print("    %s x %-20s %.1f" % (vo.Name, o_name, v))

print("\n== GEOB_probe_pose (hood probes) ==")
for vn in ("VOL_HOOD_LO", "VOL_HOOD_HI"):
    vo = doc.getObject(vn)
    if vo is None:
        print("  missing", vn)
        continue
    vs = gshape(vo)
    for o_name, sh in shape_map.items():
        if o_name.startswith(("HOOD", "ENV_", "VOL_", "TOOL_")):
            continue
        try:
            v = vs.common(sh).Volume
        except Exception:
            continue
        if v > 0.5:
            print("    %s x %-20s %.1f" % (vn, o_name, v))

App.closeDocument(doc.Name)
print("\ndone")
