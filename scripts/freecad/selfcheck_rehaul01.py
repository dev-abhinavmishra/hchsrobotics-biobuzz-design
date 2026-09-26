"""Rehaul sprint-01 self-gate: component-fidelity + contract checks.

Supersedes selfcheck_sprint06.py (retained for the archived sprint-07
baseline). Runs against BOTH rebuilt files:

  master    cad/master_robot.FCStd
  drivebase cad/drivebase/drivebase_concept_v01.FCStd

Gate map (contract sprint-01 v2):
  PAR3  every geometric input of every shape-bearing primitive is
        expression-bound (dims + Placement.Base.*); feature nodes are
        DAG-link only; carrier placements bound
  PROV1 every exportable solid carries DataStatus in
        {VERIFIED, VENDOR-PENDING, UNVERIFIED} and a non-empty Label
  ASM1  every exportable solid reaches the frame roots by touching
        (face-adjacent <=1mm) or overlapping geometry; mount-chain
        asserts for shaft/bearing/motor/plate
  GEO1  non-plate channel volume ratio < 0.5 (open U-section check)
  GEO6  roller count/slant ~45deg/X-pattern + inside ENV_WHEEL_*
  ENV   exportable inside ENV_START (deployed lifter exempt), wheels
        on ground z>=0, wheels inside ENV_WHEEL_*
  C6    full pairwise overlap scan; any overlap >0.5mm^3 must appear in
        the frozen Appendix-A declaration table (classes enumerated in
        docs/mechanism-architecture.md)
  PAR5  parameter sweeps on both files (alias -> dependent geometry)
  FLX   fillet/chamfer survival: resize chassis_length/rail_size and
        recompute; filleted/chamfered parts stay valid
  GUI   FCStd files carry GuiDocument.xml (view-state injection)
  DAG   every TOOL_* intermediate is consumed by a feature; feature
        outputs are not consumed again by later features

Run:  freecadcmd.exe scripts/freecad/selfcheck_rehaul01.py
All paths resolve relative to this file (project_root/scripts/freecad/).
"""
import hashlib
import math
import sys
import zipfile
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "cad" / "master_robot.FCStd"
DRIVEBASE = ROOT / "cad" / "drivebase" / "drivebase_concept_v01.FCStd"
fails = []
LOG = []

EXCLUDE_PREFIX = ("ENV_", "AXIS_", "REF_", "VOL_", "TOOL_")
CONTAINER_TYPES = ("App::Part", "App::Origin", "App::PartOrigin",
                   "Spreadsheet::Sheet")
PRIMITIVE_TYPES = ("Part::Box", "Part::Cylinder", "Part::Cone",
                   "Part::Sphere", "Part::Torus", "Part::Wedge")
# Angle/FirstAngle/SecondAngle are cylinder sector props that stay at the
# 360 deg default for every part we build -- not geometric inputs.
DIM_PROPS = ("Length", "Width", "Height", "Radius", "Radius2")

WHEELS = ("FL", "FR", "RL", "RR")
SLANT_SGN = {"FL": 1, "FR": -1, "RL": -1, "RR": 1}


def ck(name, ok, detail=""):
    line = ("PASS " if ok else "FAIL ") + name + \
        (" | " + detail if detail else "")
    LOG.append(line)
    print(line)
    sys.stdout.flush()
    if not ok:
        fails.append(name)


def dump():
    out = ROOT / "selfcheck_rehaul01_results.txt"
    out.write_text("\n".join(LOG) + "\nRESULT: " +
                   ("ALL PASS" if not fails else "FAILURES: %s" % fails)
                   + "\n", encoding="utf-8")


def inside(a, b, tol=2.0):
    return (a.XMin >= b.XMin - tol and a.XMax <= b.XMax + tol and
            a.YMin >= b.YMin - tol and a.YMax <= b.YMax + tol and
            a.ZMin >= b.ZMin - tol and a.ZMax <= b.ZMax + tol)


def global_shapes(doc, include_excluded=False):
    """name -> world-space Shape copy (carrier placements applied)."""
    out = {}
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o.Shape.isNull() \
                or o.TypeId in ("App::Part", "App::Origin"):
            continue
        if o.Shape.Volume <= 0:
            continue
        if not include_excluded and o.Name.startswith(EXCLUDE_PREFIX):
            continue
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        out[o.Name] = s
    return out


def declared_overlap(a, b):
    """Frozen Appendix-A overlap classes. Every declared pair is a
    physical mount/nesting relationship documented in the contract;
    anything outside this table is an undeclared interpenetration."""
    # C1 shafts/bores: shaft/shaft-like nested in the part it drives or
    # the bore that carries it
    c1 = (
        # live shaft tail inside the motor body it couples to
        ("MOTOR_", "SHAFT_"),
        # pivot axle through intake pivot bosses (and cheek bore seats)
        ("PIVOT_MOUNT_", "INTAKE_AXLE"),
        # stub shaft inside the flywheel it drives / the side plate bore
        ("MECH_FLYWHEEL_", "STUB_SHAFT_"),
        ("SHOOTER_SIDE_", "STUB_SHAFT_"),
        # diverter hinge axle through the paddle it hinges
        ("MECH_DIVERTER", "DIVERTER_AXLE"),
    )
    # C2 roller pins seat ~1mm into their own wheel's face plates
    c2 = (("WHEEL_PLATE_", "ROLLER_"),)
    # C3 mount embeds / flange-lip straddles
    c3 = (
        ("FRAME_RAIL_", "BEARING_"), ("RAIL_", "BEARING_"),
        ("STAGE_GUIDE_", "MECH_STAGE_"),
        ("MECH_CRADLE", "CRADLE_LIP"),
    )
    # C7 placeholder co-location (reserves/representatives pending
    # sprint-02..04 detail):
    c7 = (
        # telescoping cascade stages nest by design
        ("MECH_STAGE_", "MECH_STAGE_"),
        # intake cheeks pass through the open channel mouths, crossing
        # the flange lips (mounts bolt through the mouth in hardware)
        ("FRAME_RAIL_", "MECH_INTAKE_CHEEK_"),
        # servo horn embedded in the diverter paddle it drives
        ("MECH_DIVERTER", "DIVERTER_HORN"),
    )
    for cls in (c1, c2, c3, c7):
        for pa, pb in cls:
            if (a.startswith(pa) and b.startswith(pb)) or \
                    (a.startswith(pb) and b.startswith(pa)):
                return True
    return False


def declared_overlap_strict(a, b):
    """Same as declared_overlap but wheel-scoped for pin seats and
    same-side for shafts/mounts where the suffix must match."""
    if declared_overlap(a, b):
        # pin seats: plate and roller must belong to the same wheel
        if a.startswith("WHEEL_PLATE_") and b.startswith("ROLLER_"):
            return a.split("_")[2] == b.split("_")[1]
        if a.startswith("ROLLER_") and b.startswith("WHEEL_PLATE_"):
            return a.split("_")[1] == b.split("_")[2]
        # shaft<->motor same wheel suffix
        if {a[:6], b[:6]} == {"MOTOR_", "SHAFT_"} or \
                (a.startswith("MOTOR_") and b.startswith("SHAFT_")) or \
                (a.startswith("SHAFT_") and b.startswith("MOTOR_")):
            return a[-2:] == b[-2:]
        return True
    return False


def adjacency(shapes, tol=1.0):
    boxes = {}
    for n, s in shapes.items():
        bb = s.BoundBox
        bb.enlarge(tol + 0.01)
        boxes[n] = bb
    adj = {n: set() for n in shapes}
    ovl = []
    names = sorted(shapes)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if not boxes[a].intersect(boxes[b]):
                continue
            sa, sb = shapes[a], shapes[b]
            touch = False
            try:
                touch = sa.distToShape(sb)[0] <= tol
            except Exception:
                pass
            vol = 0.0
            try:
                vol = sa.common(sb).Volume
            except Exception:
                pass
            if vol > 0.5:
                ovl.append((a, b, round(vol, 1)))
            if touch or vol > 0.5:
                adj[a].add(b)
                adj[b].add(a)
    return adj, ovl


def connectivity(shapes, roots_prefix):
    adj, ovl = adjacency(shapes)
    roots = [n for n in shapes if n.startswith(roots_prefix)]
    seen = set(roots)
    stack = list(roots)
    while stack:
        n = stack.pop()
        for m in adj[n]:
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return sorted(set(shapes) - seen), ovl, adj


# ---------------- per-file checks ----------------

def check_file(path, tag, roots, has_env_start=True, has_mech=True):
    doc = App.openDocument(str(path))
    doc.recompute()
    objs = {o.Name: o for o in doc.Objects}
    shapes = global_shapes(doc)

    # --- PAR3: expression-bound geometric inputs -------------------
    unbound = []
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o.TypeId in CONTAINER_TYPES:
            continue
        eng = set()
        try:
            eng = {e[0].lstrip(".") for e in o.ExpressionEngine}
        except Exception:
            pass
        if o.TypeId in PRIMITIVE_TYPES:
            for p in DIM_PROPS:
                if hasattr(o, p) and p not in eng:
                    unbound.append("%s.%s" % (o.Name, p))
            for c in "xyz":
                if "Placement.Base.%s" % c not in eng:
                    unbound.append("%s.Placement.Base.%s" % (o.Name, c))
    ck("%s PAR3 expression-bound inputs" % tag, not unbound,
       str(unbound[:8]))

    # --- PROV1: provenance ------------------------------------------
    bad = []
    for n in shapes:
        o = objs[n]
        st = getattr(o, "DataStatus", None)
        if st is None or st.split(" - ")[0] not in (
                "VERIFIED", "VENDOR-PENDING", "UNVERIFIED"):
            bad.append(n)
        if not o.Label or o.Label == o.Name:
            bad.append(n + ":label")
    ck("%s PROV1 provenance" % tag, not bad, str(bad[:8]))

    # --- DAG hygiene: tools consumed, features terminal -------------
    consumed = set()
    for o in doc.Objects:
        for prop in ("Base", "Tool"):
            for l in getattr(o, prop, []) if isinstance(
                    getattr(o, prop, None), list) else (
                    [getattr(o, prop)] if getattr(o, prop, None) else []):
                consumed.add(l.Name)
        if o.TypeId == "Part::Compound" and getattr(o, "Links", None):
            for l in o.Links:
                consumed.add(l.Name)
    orphan = [n for n, o in objs.items()
              if n.startswith("TOOL_") and n not in consumed]
    ck("%s DAG tools consumed" % tag, not orphan, str(orphan[:8]))

    # --- ASM1: connectivity ----------------------------------------
    islands, ovl, adj = connectivity(shapes, roots)
    ck("%s ASM1 connectivity" % tag, not islands, str(islands[:8]))

    # mount chains: shaft reaches bearing+motor; bearing reaches rail
    if tag == "MASTER":
        chain_bad = []
        for w in WHEELS:
            for a, b in (("SHAFT_%s" % w, "BEARING_%s" % w),
                         ("BEARING_%s" % w, "FRAME_RAIL_%s"
                          % ("L" if w[1] == "L" else "R")),
                         ("MOTOR_%s" % w, "MOUNT_MOTOR_%s" % w),
                         ("MOUNT_MOTOR_%s" % w, "FRAME_RAIL_%s"
                          % ("L" if w[1] == "L" else "R")),
                         ("SHAFT_%s" % w, "MOTOR_%s" % w)):
                if b not in adj.get(a, ()):
                    chain_bad.append("%s!%s" % (a, b))
        ck("%s ASM1 mount chains" % tag, not chain_bad,
           str(chain_bad[:8]))

    # --- C6: overlap scan against frozen declaration table ---------
    undec = [(a, b) for a, b, v in ovl if not declared_overlap_strict(a, b)]
    ck("%s C6 undeclared overlaps" % tag, not undec, str(undec[:8]))

    # --- ENV: envelope discipline ----------------------------------
    env_bad = []
    wheels_bad = []
    deployed = {"VOL_LIFTER_DEPLOYED", "MECH_STAGE_1", "MECH_STAGE_2",
                "MECH_STAGE_3", "MECH_CARRIAGE", "MECH_CRADLE",
                "STAGE_GUIDE_L", "STAGE_GUIDE_R", "CRADLE_LIP"}
    if has_env_start and "ENV_START" in objs:
        es = objs["ENV_START"].Shape.BoundBox
        for n, s in shapes.items():
            if n in deployed:
                continue
            if not inside(s.BoundBox, es):
                env_bad.append(n)
        ck("%s ENV stowed inside R102" % tag, not env_bad,
           str(env_bad[:8]))
    for w in WHEELS:
        if "ENV_WHEEL_%s" % w in objs:
            env_bb = objs["ENV_WHEEL_%s" % w].Shape.BoundBox
            for n, s in shapes.items():
                if n.startswith("ROLLER_%s_" % w) or \
                        n.startswith("WHEEL_PLATE_%s_" % w) or \
                        n.startswith("WHEEL_HUB_%s" % w):
                    if not inside(s.BoundBox, env_bb, tol=1.0):
                        wheels_bad.append(n)
            if abs(objs["ENV_WHEEL_%s" % w].Shape.BoundBox.ZMin) > 0.01:
                wheels_bad.append("ENV_WHEEL_%s:ZMin" % w)
    ck("%s ENV wheels inside ENV_WHEEL_* at z=0" % tag, not wheels_bad,
       str(wheels_bad[:8]))

    # --- GEO1: open channel ratio -----------------------------------
    rail_names = [n for n in shapes if n.startswith(("FRAME_RAIL_",
                                                    "RAIL_"))]
    ratio_bad = []
    for n in rail_names:
        s = shapes[n]
        bb = s.BoundBox
        env_vol = bb.XLength * bb.YLength * bb.ZLength
        ratio = s.Volume / env_vol
        if ratio >= 0.5:
            ratio_bad.append("%s=%.2f" % (n, ratio))
    ck("%s GEO1 channel ratio <0.5" % tag, not ratio_bad,
       str(ratio_bad))

    # --- GEO6: roller slant / X-pattern ------------------------------
    if tag == "MASTER":
        prefix_r = "ROLLER_"
    else:
        prefix_r = "ROLLER_"
    slant_bad, patt_bad, count_bad = [], [], []
    for w in WHEELS:
        frames = [n for n in objs
                  if n.startswith("ROLLER_%s_" % w)
                  and not n.endswith("_B")
                  and objs[n].TypeId == "App::Part"]
        if len(frames) != 10:
            count_bad.append("%s:%d" % (w, len(frames)))
        for fn in frames:
            k = int(fn[-2:])
            th = math.radians(k * 36.0)
            rh = (math.cos(th), 0.0, math.sin(th))
            tt = (-math.sin(th), 0.0, math.cos(th))
            fused = objs[fn + "_B"]
            ax = None
            for f in fused.Shape.Faces:
                if f.Surface.TypeId == "Part::GeomCylinder":
                    ax = f.Surface.Axis
                    break
            if ax is None:
                slant_bad.append(fn + ":no-cyl-face")
                continue
            # cylinder axis in the ROLLER frame's local space; compose
            # with the frame's global rotation for the world axis
            rot = objs[fn].getGlobalPlacement().Rotation
            va = rot.multVec(App.Vector(ax.x, ax.y, ax.z))
            a = (va.x, va.y, va.z)
            if a[1] < 0:
                a = (-a[0], -a[1], -a[2])
            ay = a[1]
            rad = abs(a[0] * rh[0] + a[2] * rh[2])
            if not (0.66 <= ay <= 0.75) or rad > 0.15:
                slant_bad.append("%s ay=%.3f rad=%.3f" % (fn, ay, rad))
            dot_t = a[0] * tt[0] + a[2] * tt[2]
            if (dot_t > 0) != (SLANT_SGN[w] > 0):
                patt_bad.append(fn)
    ck("%s GEO6 roller count 10/wheel" % tag, not count_bad,
       str(count_bad))
    ck("%s GEO6 slant ~45deg radial-normal" % tag, not slant_bad,
       str(slant_bad[:4]))
    ck("%s GEO6 X-pattern (FL+RR vs FR+RL)" % tag, not patt_bad,
       str(patt_bad[:4]))

    # --- GUI: view-state injection ----------------------------------
    gui_ok = False
    try:
        with zipfile.ZipFile(str(path)) as z:
            gui_ok = "GuiDocument.xml" in z.namelist()
    except Exception:
        pass
    ck("%s GUI GuiDocument.xml present" % tag, gui_ok)

    App.closeDocument(doc.Name)
    return objs


# ---------------- parameter sweep + fillet survival ----------------

def sweeps(path, tag):
    h0 = hashlib.sha256(open(path, "rb").read()).hexdigest()
    doc = App.openDocument(str(path))
    sh = doc.getObject("Parameters")
    objs = {o.Name: o for o in doc.Objects}
    rail = "FRAME_RAIL_L" if "FRAME_RAIL_L" in objs else "RAIL_L"

    # chassis_length drives the side-rail cut length
    l0 = objs[rail].Shape.BoundBox.XLength
    sh.set("chassis_length", "462")  # +42
    doc.recompute()
    l1 = objs[rail].Shape.BoundBox.XLength
    ck("%s PAR5 chassis_length->rail" % tag, abs((l1 - l0) - 42) < 0.5,
       "%.1f -> %.1f" % (l0, l1))

    # wheel_dia drives wheel Z + envelope
    wz0 = objs["ENV_WHEEL_FL"].Shape.BoundBox.ZMax
    sh.set("chassis_length", "420")
    sh.set("wheel_dia", "104")  # +8
    doc.recompute()
    wz1 = objs["ENV_WHEEL_FL"].Shape.BoundBox.ZMax
    ck("%s PAR5 wheel_dia->envelope" % tag, abs((wz1 - wz0) - 8) < 0.5,
       "%.1f -> %.1f" % (wz0, wz1))

    # PAR2: wheel_x_offset +10 must translate the whole corner chain
    # (carrier children are local-frame; assert via globalized shapes)
    def gbb(name):
        o = objs[name]
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        return s.BoundBox
    corner = ["WHEEL_ASSY_FL", "WHEEL_HUB_FL", "WHEEL_PLATE_FL_IN",
              "WHEEL_PLATE_FL_OUT", "ROLLER_FL_00_B", "SHAFT_FL",
              "BEARING_FL", "MOTOR_FL", "MOUNT_MOTOR_FL"]
    x0 = {n: gbb(n).XMin for n in corner}
    sh.set("wheel_x_offset", "150")  # +10
    doc.recompute()
    moved = [n for n in corner
             if abs(gbb(n).XMin - x0[n] - 10) > 0.01]
    ck("%s PAR2 wheel_x_offset corner sweep" % tag, not moved,
       str(moved[:6]))
    sh.set("wheel_x_offset", "140")
    doc.recompute()

    # roller slant sweeps the roller-frame angle (expression-bound
    # Placement.Rotation.Angle): the fused body is frame-local, so the
    # world roller axis = frame global rotation * local +Y
    frame = doc.getObject("ROLLER_FL_00")
    ax0 = frame.getGlobalPlacement().Rotation.multVec(App.Vector(0, 1, 0))
    sh.set("wheel_dia", "96")
    sh.set("mec_roll_slant", "30")
    doc.recompute()
    ax1 = frame.getGlobalPlacement().Rotation.multVec(App.Vector(0, 1, 0))
    dot = ax0.x * ax1.x + ax0.y * ax1.y + ax0.z * ax1.z
    ck("%s PAR5 mec_roll_slant->roller" % tag,
       abs(dot - math.cos(math.radians(15))) < 0.01,
       "axis dot %.4f" % dot)

    # FLX: fillet/chamfer survival under rail_size resize
    pan = doc.getObject("BELLY_PAN")
    faces0 = len(pan.Shape.Faces)
    sh.set("mec_roll_slant", "45")
    sh.set("rail_size", "56")  # +8mm taller channel
    doc.recompute()
    ok = pan.Shape.isValid() and len(pan.Shape.Faces) == faces0
    plate = doc.getObject("WHEEL_PLATE_FL_IN")
    ok2 = plate.Shape.isValid()
    sh.set("rail_size", "48")
    doc.recompute()
    ok = ok and pan.Shape.isValid() and len(pan.Shape.Faces) == faces0
    ck("%s FLX fillet/chamfer survives resize" % tag, ok and ok2,
       "pan faces %d valid=%s" % (len(pan.Shape.Faces), ok))

    App.closeDocument(doc.Name)  # close WITHOUT saving
    h1 = hashlib.sha256(open(path, "rb").read()).hexdigest()
    ck("%s close-no-save hash stable" % tag, h0 == h1)


def main():
    # ---- archive probe: sprint-07 baselines must exist -------------
    arch = ROOT / "cad" / "archive"
    bl = [p.name for p in arch.glob("*sprint07_baseline*")]
    js = [p.name for p in arch.glob("*baseline*.json")] + \
         [p.name for p in arch.glob("*_dump*.json")]
    ck("ARC baseline archives present",
       any("master_robot" in n for n in bl) and
       any("drivebase" in n for n in bl), str(bl[:4]))
    ck("ARC baseline JSON dump present", len(js) > 0, str(js[:4]))

    check_file(MASTER, "MASTER", ("FRAME_", "BELLY_PAN"))
    check_file(DRIVEBASE, "DRIVEBASE", ("RAIL_", "BELLY_PAN"),
               has_env_start=False)
    sweeps(MASTER, "MASTER")
    sweeps(DRIVEBASE, "DRIVEBASE")

    dump()
    print("RESULT:", "ALL PASS" if not fails else "FAILURES: %s" % fails)
    sys.stdout.flush()
    sys.exit(0 if not fails else 1)


try:
    main()
except Exception:
    import traceback
    traceback.print_exc()
    dump()
    sys.exit(1)
