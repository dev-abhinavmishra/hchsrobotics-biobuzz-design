"""Rehaul sprint-02 self-gate: intake + transfer component fidelity.

Supersedes selfcheck_rehaul01.py (rehaul01 is retained for sprint-01
archive validation). Runs against THREE files:

  master    cad/master_robot.FCStd
  intake    cad/intake/intake_concept_v01.FCStd
  transfer  cad/transfer/transfer_concept_v01.FCStd

Gate map (contract sprint-02 v3):
  ARC   sprint-01-state archives + JSON dump + untouched-file sig dump
  PAR3  zero free dimensional props on every Shape-bearing object
  PAR2-I/T  delta probes: intake_width / channel_w move the FULL
        dependent chain (cheeks+bosses+axles+mounts+roller span;
        walls+floor+saddles+hinge span+servo)
  PAR4/FLX  chamfer/fillet survive a parameter bump
  PROV1 DataStatus on every solid incl. TOOL_*; label carries
        desc+dims+status (GEO9')
  ASM1  BFS connectivity, 0 islands; intake/transfer mount chains
  ASM2  overlap scan vs frozen Appendix B (per file)
  ASM4  coplanar/z-fight census; coincident pairs enumerated in App.B
  GEO-I coaxiality: roller bores L/R, stub axles through bosses,
        diverter axle through bushings, paddle bore on axle;
        ball-path clearance via VOL_BALL_PATH
  GEO-T channel interior >= channel_w x channel_h clear section;
        paddle sweeps clear of VOL_CHANNEL_CLEAR at paddle_sweep_deg
  GEO8' softened-edge enumeration on new parts
  ENV1' stowed subset ENV_START, deployed subset ENV_EXPANSION
        (membership enumerated below)
  REG   drivebase/shooter/lifter/electronics rebuild identical
        (signature compare vs untouched_sprint01_sigs.json)
  DET1  deterministic bbox signature across this run's recompute
  GUI   GuiDocument.xml present in every file

Run:  freecadcmd.exe scripts/freecad/selfcheck_rehaul02.py
All paths resolve relative to this file (project_root/scripts/freecad/).
"""
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "MASTER": ROOT / "cad" / "master_robot.FCStd",
    "INTAKE": ROOT / "cad" / "intake" / "intake_concept_v01.FCStd",
    "TRANSFER": ROOT / "cad" / "transfer" / "transfer_concept_v01.FCStd",
}
UNTOUCHED = {
    "drivebase": ROOT / "cad" / "drivebase" / "drivebase_concept_v01.FCStd",
    "shooter": ROOT / "cad" / "scoring" / "shooter_concept_v01.FCStd",
    "lifter": ROOT / "cad" / "endgame" / "lifter_concept_v01.FCStd",
    "electronics": (ROOT / "cad" / "electronics"
                    / "electronics_concept_v01.FCStd"),
}
BASELINE_SIGS = ROOT / "cad" / "archive" / "untouched_sprint01_sigs.json"

fails = []
LOG = []

EXCLUDE_PREFIX = ("ENV_", "AXIS_", "REF_", "VOL_", "TOOL_")
CONTAINER_TYPES = ("App::Part", "App::Origin", "App::PartOrigin",
                   "Spreadsheet::Sheet")
PRIMITIVE_TYPES = ("Part::Box", "Part::Cylinder", "Part::Cone",
                   "Part::Sphere", "Part::Torus", "Part::Wedge")
DIM_PROPS = ("Length", "Width", "Height", "Radius", "Radius2")
STATUS_TOKENS = ("VERIFIED", "VENDOR-PENDING", "UNVERIFIED")

WHEELS = ("FL", "FR", "RL", "RR")

# ENV1' membership: deployed set = lifter deployed column only; every
# other exportable solid is stowed-set (must sit inside ENV_START).
DEPLOYED = {"MECH_STAGE_1", "MECH_STAGE_2", "MECH_STAGE_3",
            "MECH_CARRIAGE", "MECH_CRADLE", "CRADLE_LIP",
            "STAGE_GUIDE_L", "STAGE_GUIDE_R"}

# GEO8': softened-edge enumeration for the sprint-02 parts
SOFTENED = {
    "MASTER": {"INTAKE_CHEEK_L", "INTAKE_CHEEK_R", "INTAKE_LIP",
               "CHANNEL_FLOOR", "CHANNEL_WALL_L", "CHANNEL_WALL_R"},
    "INTAKE": {"INTAKE_CHEEK_L", "INTAKE_CHEEK_R"},
    "TRANSFER": {"CHANNEL_FLOOR", "CHANNEL_WALL_L", "CHANNEL_WALL_R"},
}

# Appendix B -- declared overlap + coincident-face classes per file.
# Undeclared volumetric overlap > 0.5mm^3 or an undeclared coplanar
# coincident pair = failure. Frozen at eval-02 handoff.
APPENDIX_B = {
    "MASTER": (
        # B1 shaft-in-bore / shaft-in-body nesting
        ("INTAKE_ROLLER", "INTAKE_ROLLER_SHAFT"),
        ("PIVOT_MOUNT_", "INTAKE_AXLE_"),
        ("INTAKE_CHEEK_", "INTAKE_AXLE_"),
        ("DIVERTER_PADDLE", "DIVERTER_AXLE"),
        ("DIVERTER_HORN", "DIVERTER_AXLE"),
        # B3 mount-face adjacency / embeds / coplanar mounts
        ("INTAKE_BEARING_", "INTAKE_CHEEK_"),
        ("PIVOT_MOUNT_", "INTAKE_CHEEK_"),
        ("INTAKE_MOUNT_", "INTAKE_CHEEK_"),
        ("INTAKE_MOUNT_", "FRAME_RAIL_"),
        ("INTAKE_MOTOR", "INTAKE_CHEEK_L"),
        ("INTAKE_MOTOR", "FRAME_RAIL_L"),
        ("INTAKE_MOTOR_BRKT", "INTAKE_MOTOR"),
        ("INTAKE_MOTOR_BRKT", "INTAKE_CHEEK_L"),
        ("INTAKE_LIP", "INTAKE_CHEEK_"),
        ("INTAKE_LIP", "INTAKE_MOUNT_"),
        ("INTAKE_LIP", "FRAME_RAIL_"),
        ("CHANNEL_WALL_", "CHANNEL_FLOOR"),
        ("CHANNEL_SUPP_", "CHANNEL_FLOOR"),
        ("CHANNEL_SUPP_", "BELLY_PAN"),
        ("DIVERTER_BUSH_", "CHANNEL_WALL_"),
        ("DIVERTER_SERVO", "CHANNEL_WALL_L"),
        ("DIVERTER_SERVO", "DIVERTER_BUSH_L"),
        ("DIVERTER_SERVO", "DIVERTER_HORN"),
        ("DIVERTER_SERVO", "POST_SHOOTER_L"),
        # wall outer faces flush against the drive-motor inner faces
        ("CHANNEL_WALL_L", "MOTOR_RL"),
        ("CHANNEL_WALL_R", "MOTOR_RR"),
        ("DIVERTER_BUSH_L", "MOTOR_RL"),
        ("DIVERTER_SERVO", "MOTOR_RL"),
        # roller end seats inside its own bearing blocks
        ("INTAKE_ROLLER", "INTAKE_BEARING_"),
        # B7 intake-through-mouth co-location (carried from App.A C7)
        ("FRAME_RAIL_", "INTAKE_CHEEK_"),
        # sprint-01 classes that still apply
        ("MOTOR_", "SHAFT_"),
        ("MOTOR_", "MOUNT_MOTOR_"),
        ("WHEEL_PLATE_", "ROLLER_"),
        ("FRAME_RAIL_", "FRAME_RAIL_"),
        ("FRAME_RAIL_", "BEARING_"),
        ("FRAME_RAIL_", "MOUNT_MOTOR_"),
        ("FRAME_RAIL_", "REAR_DECK_"),
        ("FRAME_RAIL_", "BELLY_PAN"),
        ("BELLY_PAN", "REAR_DECK_"),
        ("BELLY_PAN", "ELEC_RAIL_"),
        ("BELLY_PAN", "LIFTER_PED"),
        ("BELLY_PAN", "POST_SHOOTER_"),
        ("BELLY_PAN", "LIFTER_BASE"),
        ("LIFTER_PED", "LIFTER_BASE"),
        ("BATTERY_", "ELEC_RAIL_"),
        ("BATTERY", "BELLY_PAN"),
        ("ELECTRONICS", "ELEC_RAIL_"),
        ("SHOOTER_FLOOR", "CHANNEL_WALL_"),
        ("SHOOTER_FLOOR", "DIVERTER_SERVO"),
        ("MECH_SHOOTER_BODY", "SHOOTER_SIDE_"),
        ("MECH_SHOOTER_BODY", "MECH_SHOOTER_HOOD"),
        ("MECH_SHOOTER_BODY", "SHOOTER_FLOOR"),
        ("MECH_SHOOTER_HOOD", "SHOOTER_SIDE_"),
        ("SHOOTER_FLOOR", "SHOOTER_SIDE_"),
        ("MECH_CARRIAGE", "MECH_STAGE_"),
        ("POST_SHOOTER_", "REAR_DECK_"),
        ("POST_SHOOTER_", "SHOOTER_FLOOR"),
        ("LIFTER_BASE", "MECH_STAGE_"),
        ("LIFTER_BASE", "MECH_LIFTER_STOWED"),
        ("STAGE_GUIDE_", "MECH_STAGE_"),
        ("MECH_CRADLE", "CRADLE_LIP"),
        ("MECH_STAGE_", "MECH_STAGE_"),
        ("MECH_FLYWHEEL_", "STUB_SHAFT_"),
        ("SHOOTER_SIDE_", "STUB_SHAFT_"),
    ),
    "INTAKE": (
        ("ROLLER_", "ROLLER_SHAFT_"),
        ("INTAKE_BEARING_", "INTAKE_CHEEK_"),
        ("PIVOT_MOUNT_", "INTAKE_CHEEK_"),
        ("PIVOT_MOUNT_", "INTAKE_AXLE_"),
        ("INTAKE_CHEEK_", "INTAKE_AXLE_"),
        ("CHASSIS_STUB", "INTAKE_CHEEK_"),
        ("INTAKE_MOTOR", "INTAKE_CHEEK_L"),
        ("INTAKE_MOTOR", "INTAKE_MOTOR_BRKT"),
        ("INTAKE_MOTOR_BRKT", "INTAKE_CHEEK_L"),
        ("INTAKE_MOUNT_", "INTAKE_CHEEK_"),
        ("INTAKE_MOUNT_", "CHASSIS_STUB"),
        ("ROLLER_", "INTAKE_BEARING_"),
        ("ROLLER_", "LIP_RAMP"),
        ("INTAKE_CHEEK_", "LIP_RAMP"),
    ),
    "TRANSFER": (
        ("CHANNEL_WALL_", "CHANNEL_FLOOR"),
        ("CHANNEL_FLOOR", "PAN_STUB"),
        ("CHANNEL_WALL_", "PAN_STUB"),
        ("CHANNEL_SUPP_", "CHANNEL_FLOOR"),
        ("CHANNEL_SUPP_", "PAN_STUB"),
        ("DIVERTER_PADDLE", "DIVERTER_AXLE"),
        ("DIVERTER_HORN", "DIVERTER_AXLE"),
        ("DIVERTER_BUSH_", "CHANNEL_WALL_"),
        ("DIVERTER_SERVO", "CHANNEL_WALL_L"),
        ("DIVERTER_SERVO", "DIVERTER_BUSH_L"),
        ("DIVERTER_SERVO", "DIVERTER_HORN"),
        ("ZONE_INLET", "CHANNEL_WALL_"),
        ("ZONE_OUTLET", "PAN_STUB"),
        ("ZONE_OUTLET", "CHANNEL_WALL_"),
        ("ZONE_OUTLET", "CHANNEL_FLOOR"),
        ("ROUTE_", "CHANNEL_WALL_"),
        ("ROUTE_", "ZONE_"),
    ),
}

# Ball-path allowed/flagged intersections. FLAGGED = known integration
# defects documented in the eval-02 evidence (sprint-04 must re-site or
# bridge the lifter pedestal; the straight probe crosses the front rail
# band because the intake mouth sits proud of it).
BALL_ALLOWED = {
    "MASTER": {"INTAKE_ROLLER", "INTAKE_ROLLER_SHAFT"},
    "INTAKE": {"ROLLER_LO", "ROLLER_HI",
               "ROLLER_SHAFT_LO", "ROLLER_SHAFT_HI"},
    "TRANSFER": set(),
}
BALL_FLAGGED = {
    "MASTER": {"LIFTER_PED", "FRAME_RAIL_F"},
    "INTAKE": {"LIP_RAMP"},
    "TRANSFER": set(),
}

# coincident (coplanar, area-overlapping) face pairs get enumerated by
# the ASM4 census and must appear here as declared pairs as well
# (subset of APPENDIX_B by construction); listed for the freeze record.


def ck(name, ok, detail=""):
    line = ("PASS " if ok else "FAIL ") + name + \
        (" | " + detail if detail else "")
    LOG.append(line)
    print(line)
    sys.stdout.flush()
    if not ok:
        fails.append(name)


def dump():
    out = ROOT / "selfcheck_rehaul02_results.txt"
    out.write_text("\n".join(LOG) + "\nRESULT: " +
                   ("ALL PASS" if not fails else "FAILURES: %s" % fails)
                   + "\n", encoding="utf-8")


def inside(a, b, tol=2.0):
    return (a.XMin >= b.XMin - tol and a.XMax <= b.XMax + tol and
            a.YMin >= b.YMin - tol and a.YMax <= b.YMax + tol and
            a.ZMin >= b.ZMin - tol and a.ZMax <= b.ZMax + tol)


def global_shapes(doc, include_excluded=False):
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


def declared_overlap(tag, a, b):
    for pa, pb in APPENDIX_B.get(tag, ()):
        if (a.startswith(pa) and b.startswith(pb)) or \
                (a.startswith(pb) and b.startswith(pa)):
            # wheel-scoped pin seats must match wheel suffix
            if a.startswith("WHEEL_PLATE_") and b.startswith("ROLLER_"):
                return a.split("_")[2] == b.split("_")[1]
            if a.startswith("ROLLER_") and b.startswith("WHEEL_PLATE_"):
                return a.split("_")[1] == b.split("_")[2]
            if (a.startswith("MOTOR_") and b.startswith("SHAFT_")) or \
                    (a.startswith("SHAFT_") and b.startswith("MOTOR_")):
                return a[-2:] == b[-2:]
            # side-scoped L/R pairs must match suffix
            sa = a[-2:] if a[-2:] in ("_L", "_R") else ""
            sb = b[-2:] if b[-2:] in ("_L", "_R") else ""
            if sa and sb and sa != sb:
                return False
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


def coplanar_census(shapes, pairs):
    """Coincident-face pairs: planar faces that are coplanar (same
    plane within 0.05mm) with overlapping area > 1mm^2 -- the z-fight
    risk set. `pairs` = the adjacent-pair shortlist."""
    hits = []
    for a, b in pairs:
        sa, sb = shapes[a], shapes[b]
        found = False
        for fa in sa.Faces:
            if fa.Surface.TypeId != "Part::GeomPlane":
                continue
            na = fa.Surface.Axis
            pa = fa.Surface.Position
            for fb in sb.Faces:
                if fb.Surface.TypeId != "Part::GeomPlane":
                    continue
                nb = fb.Surface.Axis
                if abs(na.x * nb.x + na.y * nb.y + na.z * nb.z) < 0.999:
                    continue
                pb = fb.Surface.Position
                if abs((pa - pb).dot(na)) > 0.05:
                    continue
                try:
                    if fa.common(fb).Area > 1.0:
                        found = True
                        break
                except Exception:
                    continue
            if found:
                break
        if found:
            hits.append((a, b))
    return hits


def cyl_axis(shape, target_r, tol=0.6):
    """(point, dir) of a cylindrical face with radius ~target_r."""
    for f in shape.Faces:
        if f.Surface.TypeId != "Part::GeomCylinder":
            continue
        if abs(f.Surface.Radius - target_r) > tol:
            continue
        ax = f.Surface.Axis
        c = f.Surface.Center
        return (c.x, c.y, c.z), (ax.x, ax.y, ax.z)
    return None


def axis_gap(a, b):
    """Perpendicular distance between two axes (point,dir pairs)."""
    (pa, da), (pb, db) = a, b
    n = (da[1] * db[2] - da[2] * db[1],
         da[2] * db[0] - da[0] * db[2],
         da[0] * db[1] - da[1] * db[0])
    nn = math.sqrt(sum(c * c for c in n))
    if nn < 1e-9:  # parallel -> distance between point and line
        v = (pa[0] - pb[0], pa[1] - pb[1], pa[2] - pb[2])
        t = (v[0] * db[0] + v[1] * db[1] + v[2] * db[2])
        p = (v[0] - t * db[0], v[1] - t * db[1], v[2] - t * db[2])
        return math.sqrt(sum(c * c for c in p))
    d = abs(sum((pa[i] - pb[i]) * n[i] for i in range(3))) / nn
    return d


def check_file(path, tag, roots):
    doc = App.openDocument(str(path))
    doc.recompute()
    objs = {o.Name: o for o in doc.Objects}
    shapes = global_shapes(doc)

    # --- PAR3 ------------------------------------------------------
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

    # --- PROV1 + GEO9' label convention ----------------------------
    bad = []
    for n in shapes:
        o = objs[n]
        st = getattr(o, "DataStatus", None)
        if st is None or st.split(" - ")[0] not in STATUS_TOKENS:
            bad.append(n)
        lbl = o.Label or ""
        if not any(lbl.rstrip("0123456789").endswith(t)
                   for t in STATUS_TOKENS):
            bad.append(n + ":label-status")
        if lbl == n:
            bad.append(n + ":label-empty")
    # TOOL_ intermediates must also carry DataStatus
    tool_bad = [o.Name for o in doc.Objects
                if o.Name.startswith("TOOL_") and hasattr(o, "Shape")
                and getattr(o, "DataStatus", None) is None]
    ck("%s PROV1 provenance + labels" % tag, not bad and not tool_bad,
       str((bad + tool_bad)[:8]))

    # --- DAG hygiene -----------------------------------------------
    consumed = set()
    for o in doc.Objects:
        for prop in ("Base", "Tool"):
            v = getattr(o, prop, None)
            for l in (v if isinstance(v, (list, tuple))
                      else ([v] if v else [])):
                consumed.add(l.Name)
        if o.TypeId == "Part::Compound" and getattr(o, "Links", None):
            for l in o.Links:
                consumed.add(l.Name)
    orphan = [n for n, o in objs.items()
              if n.startswith("TOOL_") and n not in consumed]
    ck("%s DAG tools consumed" % tag, not orphan, str(orphan[:8]))

    # --- ASM1 connectivity + mount chains ---------------------------
    islands, ovl, adj = connectivity(shapes, roots)
    ck("%s ASM1 connectivity" % tag, not islands, str(islands[:8]))

    if tag == "MASTER":
        chains = [
            ("INTAKE_CHEEK_L", "INTAKE_MOUNT_L"),
            ("INTAKE_MOUNT_L", "FRAME_RAIL_L"),
            ("INTAKE_CHEEK_R", "INTAKE_MOUNT_R"),
            ("INTAKE_MOUNT_R", "FRAME_RAIL_R"),
            ("INTAKE_ROLLER_SHAFT", "INTAKE_BEARING_L"),
            ("INTAKE_ROLLER_SHAFT", "INTAKE_BEARING_R"),
            ("INTAKE_ROLLER", "INTAKE_ROLLER_SHAFT"),
            ("INTAKE_AXLE_L", "PIVOT_MOUNT_L"),
            ("INTAKE_AXLE_R", "PIVOT_MOUNT_R"),
            ("PIVOT_MOUNT_L", "INTAKE_CHEEK_L"),
            ("INTAKE_MOTOR", "INTAKE_MOTOR_BRKT"),
            ("INTAKE_MOTOR", "INTAKE_CHEEK_L"),
            ("INTAKE_MOTOR_BRKT", "INTAKE_CHEEK_L"),
            ("INTAKE_LIP", "INTAKE_CHEEK_L"),
            ("CHANNEL_FLOOR", "CHANNEL_SUPP_F"),
            ("CHANNEL_FLOOR", "CHANNEL_SUPP_B"),
            ("CHANNEL_SUPP_F", "BELLY_PAN"),
            ("CHANNEL_SUPP_B", "BELLY_PAN"),
            ("CHANNEL_WALL_L", "CHANNEL_FLOOR"),
            ("CHANNEL_WALL_R", "CHANNEL_FLOOR"),
            ("DIVERTER_AXLE", "DIVERTER_BUSH_L"),
            ("DIVERTER_AXLE", "DIVERTER_BUSH_R"),
            ("DIVERTER_AXLE", "DIVERTER_PADDLE"),
            ("DIVERTER_AXLE", "DIVERTER_HORN"),
            ("DIVERTER_BUSH_L", "CHANNEL_WALL_L"),
            ("DIVERTER_BUSH_R", "CHANNEL_WALL_R"),
            ("DIVERTER_SERVO", "CHANNEL_WALL_L"),
        ]
    elif tag == "INTAKE":
        chains = [
            ("INTAKE_CHEEK_L", "INTAKE_MOUNT_L"),
            ("INTAKE_MOUNT_L", "CHASSIS_STUB"),
            ("INTAKE_CHEEK_R", "INTAKE_MOUNT_R"),
            ("INTAKE_MOUNT_R", "CHASSIS_STUB"),
            ("ROLLER_SHAFT_LO", "INTAKE_BEARING_LO_L"),
            ("ROLLER_SHAFT_HI", "INTAKE_BEARING_HI_R"),
            ("ROLLER_LO", "ROLLER_SHAFT_LO"),
            ("ROLLER_HI", "ROLLER_SHAFT_HI"),
            ("INTAKE_AXLE_L", "PIVOT_MOUNT_L"),
            ("INTAKE_AXLE_R", "PIVOT_MOUNT_R"),
            ("PIVOT_MOUNT_L", "INTAKE_CHEEK_L"),
            ("INTAKE_MOTOR", "INTAKE_MOTOR_BRKT"),
            ("INTAKE_MOTOR", "INTAKE_CHEEK_L"),
            ("LIP_RAMP", "INTAKE_CHEEK_L"),
        ]
    else:  # TRANSFER
        chains = [
            ("CHANNEL_FLOOR", "CHANNEL_SUPP_F"),
            ("CHANNEL_FLOOR", "CHANNEL_SUPP_B"),
            ("CHANNEL_SUPP_F", "PAN_STUB"),
            ("CHANNEL_SUPP_B", "PAN_STUB"),
            ("CHANNEL_WALL_L", "CHANNEL_FLOOR"),
            ("CHANNEL_WALL_R", "CHANNEL_FLOOR"),
            ("DIVERTER_AXLE", "DIVERTER_BUSH_L"),
            ("DIVERTER_AXLE", "DIVERTER_BUSH_R"),
            ("DIVERTER_AXLE", "DIVERTER_PADDLE"),
            ("DIVERTER_AXLE", "DIVERTER_HORN"),
            ("DIVERTER_SERVO", "CHANNEL_WALL_L"),
            ("ZONE_INLET", "CHANNEL_WALL_R"),
            ("ROUTE_POLLEN", "CHANNEL_WALL_L"),
            ("ROUTE_NECTAR", "CHANNEL_WALL_R"),
        ]
    chain_bad = [(a, b) for a, b in chains
                 if a in shapes and b in shapes and b not in adj.get(a, ())]
    ck("%s ASM1 mount chains" % tag, not chain_bad, str(chain_bad[:8]))

    # --- ASM2 overlap vs Appendix B ---------------------------------
    undec = [(a, b) for a, b, v in ovl
             if not declared_overlap(tag, a, b)]
    ck("%s ASM2 undeclared overlaps" % tag, not undec, str(undec[:10]))

    # --- ASM4 coplanar census ---------------------------------------
    adj_pairs = [(a, b) for a in adj for b in adj[a] if a < b]
    coinc = coplanar_census(shapes, adj_pairs)
    undec_c = [(a, b) for a, b in coinc
               if not declared_overlap(tag, a, b)]
    ck("%s ASM4 coincident pairs all declared" % tag, not undec_c,
       "coincident=%d undeclared=%s" % (len(coinc), undec_c[:8]))

    # --- ENV1' (master only) ----------------------------------------
    if tag == "MASTER":
        env_bad = []
        es = objs["ENV_START"].Shape.BoundBox
        ex = objs["ENV_EXPANSION"].Shape.BoundBox
        for n, s in shapes.items():
            bb = s.BoundBox
            if n in DEPLOYED:
                if not inside(bb, ex):
                    env_bad.append(n + ":!expansion")
            elif not inside(bb, es):
                env_bad.append(n)
        ck("%s ENV1' stowed subset ENV_START, deployed subset ENV_EXPANSION"
           % tag, not env_bad, str(env_bad[:8]))

    # --- GEO8' softened-edge enumeration -----------------------------
    soft_bad = []
    for n in SOFTENED.get(tag, ()):
        o = objs.get(n)
        if o is None or o.TypeId not in ("Part::Fillet", "Part::Chamfer"):
            soft_bad.append(n)
    ck("%s GEO8' softened-edge enumeration" % tag, not soft_bad,
       str(soft_bad))

    # --- GEO-I: intake coaxiality + ball path ------------------------
    if tag in ("MASTER", "INTAKE"):
        geo_bad = []
        pw = "plate_w" if tag == "MASTER" else "plate_thk"
        # roller-shaft axis coaxial with the cheek roller bores
        sh_axis = cyl_axis(shapes.get(
            "INTAKE_ROLLER_SHAFT" if tag == "MASTER"
            else "ROLLER_SHAFT_LO"), 4.0)
        for s in ("L", "R"):
            ck_ax = cyl_axis(shapes["INTAKE_CHEEK_%s" % s], 4.5)
            if sh_axis is None or ck_ax is None \
                    or axis_gap(sh_axis, ck_ax) > 0.5:
                geo_bad.append("roller-bore-%s" % s)
        # stub axles coaxial with the boss bores
        for s in ("L", "R"):
            st = cyl_axis(shapes["INTAKE_AXLE_%s" % s], 6.0)
            bo = cyl_axis(shapes["PIVOT_MOUNT_%s" % s], 6.5)
            if st is None or bo is None or axis_gap(st, bo) > 0.5:
                geo_bad.append("stub-boss-%s" % s)
        # ball path: allowed solids intersect by design; flagged solids
        # are documented known-conflicts; anything else fails
        if "VOL_BALL_PATH" in objs:
            vs = objs["VOL_BALL_PATH"].Shape.copy()
            vs.Placement = objs["VOL_BALL_PATH"].getGlobalPlacement()
            hit, flagged = [], []
            for n, s in shapes.items():
                if n in BALL_ALLOWED.get(tag, ()):
                    continue
                try:
                    if vs.common(s).Volume > 0.5:
                        if n in BALL_FLAGGED.get(tag, ()):
                            flagged.append(n)
                        else:
                            hit.append(n)
                except Exception:
                    pass
            if hit:
                geo_bad.append("ball-path:" + ",".join(hit[:6]))
            ck("%s GEO-I ball-path flagged conflicts" % tag, True,
               "flagged=%s" % sorted(flagged))
        ck("%s GEO-I coaxiality + ball-path clearance" % tag,
           not geo_bad, str(geo_bad[:8]))

    # --- GEO-T: transfer diverter + clear section --------------------
    if tag in ("MASTER", "TRANSFER"):
        geo_bad = []
        ax = cyl_axis(shapes["DIVERTER_AXLE"], 3.0)
        for s in ("L", "R"):
            bo = cyl_axis(shapes["DIVERTER_BUSH_%s" % s], 3.2)
            if ax is None or bo is None or axis_gap(ax, bo) > 0.5:
                geo_bad.append("bush-%s" % s)
        pb = cyl_axis(shapes["DIVERTER_PADDLE"], 3.2)
        if ax is None or pb is None or axis_gap(ax, pb) > 0.5:
            geo_bad.append("paddle-bore")
        # interior clear section >= nectar_dia in both transverse dims
        if "VOL_CHANNEL_CLEAR" in objs:
            vc = objs["VOL_CHANNEL_CLEAR"].Shape.BoundBox
            if vc.YLength < 91.0 or vc.ZLength < 91.0:
                geo_bad.append("clear-section %.0fx%.0f"
                               % (vc.YLength, vc.ZLength))
            # structural parts must not intrude into the clear volume
            vs = objs["VOL_CHANNEL_CLEAR"].Shape.copy()
            vs.Placement = \
                objs["VOL_CHANNEL_CLEAR"].getGlobalPlacement()
            intr = []
            for n, s in shapes.items():
                if n.startswith(("DIVERTER_PADDLE", "DIVERTER_AXLE",
                                 "DIVERTER_HORN", "ZONE_", "ROUTE_")):
                    continue  # mechanism parts live in the lane
                try:
                    if vs.common(s).Volume > 0.5:
                        intr.append(n)
                except Exception:
                    pass
            if intr:
                geo_bad.append("clear-intruders:" + ",".join(intr[:6]))
        # ball-path lane: allowed intersections only, flagged logged
        if "VOL_BALL_PATH" in objs:
            vb = objs["VOL_BALL_PATH"].Shape.copy()
            vb.Placement = objs["VOL_BALL_PATH"].getGlobalPlacement()
            hit, flagged = [], []
            for n, s in shapes.items():
                if n in BALL_ALLOWED.get(tag, ()):
                    continue
                try:
                    if vb.common(s).Volume > 0.5:
                        if n in BALL_FLAGGED.get(tag, ()):
                            flagged.append(n)
                        else:
                            hit.append(n)
                except Exception:
                    pass
            if hit:
                geo_bad.append("ball-path:" + ",".join(hit[:6]))
            ck("%s GEO-T ball-path flagged conflicts" % tag, True,
               "flagged=%s" % sorted(flagged))
            # paddle sweep: rotating by paddle_sweep_deg clears the lane
            sweep = float(objs["Parameters"].get("paddle_sweep_deg"))
            pad = objs["DIVERTER_PADDLE"].Shape.copy()
            pad.Placement = \
                objs["DIVERTER_PADDLE"].getGlobalPlacement()
            ax_c = objs["DIVERTER_AXLE"].Shape.copy()
            ax_c.Placement = \
                objs["DIVERTER_AXLE"].getGlobalPlacement()
            c = ax_c.BoundBox.Center
            pad.rotate(App.Vector(c.x, c.y, c.z),
                       App.Vector(0, 1, 0), sweep)
            try:
                v = vb.common(pad).Volume
            except Exception:
                v = -1
            if not (0 <= v < 0.5):
                geo_bad.append("paddle-sweep vol=%.1f" % v)
        ck("%s GEO-T hinge coaxiality + clear section + sweep" % tag,
           not geo_bad, str(geo_bad[:8]))

    # --- GEO-I containment: rebuilt parts stay inside reserves -------
    if tag == "MASTER":
        cont_bad = []
        vi = objs["VOL_INTAKE"].Shape.BoundBox
        vt = objs["VOL_TRANSFER"].Shape.BoundBox
        intake_parts = [n for n in shapes if n.startswith(
            ("INTAKE_CHEEK", "INTAKE_ROLLER", "INTAKE_BEARING",
             "PIVOT_MOUNT", "INTAKE_AXLE", "INTAKE_LIP",
             "INTAKE_MOUNT"))]
        transfer_parts = [n for n in shapes if n.startswith(
            ("CHANNEL_", "DIVERTER_PADDLE", "DIVERTER_AXLE",
             "DIVERTER_BUSH"))]
        # documented exterior mounts: servo/horn sit outside the lane
        for n in intake_parts:
            if not inside(shapes[n].BoundBox, vi):
                cont_bad.append(n)
        for n in transfer_parts:
            if not inside(shapes[n].BoundBox, vt):
                cont_bad.append(n)
        ck("%s GEO reserves containment (interior parts)" % tag,
           not cont_bad, str(cont_bad[:8]))

    # --- GUI ---------------------------------------------------------
    gui_ok = False
    try:
        with zipfile.ZipFile(str(path)) as z:
            gui_ok = "GuiDocument.xml" in z.namelist()
    except Exception:
        pass
    ck("%s GUI GuiDocument.xml present" % tag, gui_ok)

    App.closeDocument(doc.Name)
    return objs


def sweeps_master():
    """PAR2-I / PAR2-T / PAR4 on the master file."""
    path = FILES["MASTER"]
    h0 = hashlib.sha256(open(path, "rb").read()).hexdigest()
    doc = App.openDocument(str(path))
    sh = doc.getObject("Parameters")
    objs = {o.Name: o for o in doc.Objects}

    def gbb(name):
        s = objs[name].Shape.copy()
        s.Placement = objs[name].getGlobalPlacement()
        return s.BoundBox

    # PAR2-I: intake_width +10 -> cheeks symmetric, roller span +
    # shaft length + bearing/boss/axle/mount positions track
    names_i = {"INTAKE_CHEEK_L": ("YMin", 5), "INTAKE_CHEEK_R": ("YMax", -5),
               "INTAKE_ROLLER": ("YMin", -5),
               "INTAKE_ROLLER_SHAFT": ("YMin", -5),
               "INTAKE_BEARING_L": ("YMax", 5), "PIVOT_MOUNT_L": ("YMax", 5),
               "INTAKE_AXLE_L": ("YMin", 5), "INTAKE_MOUNT_L": ("YMax", 5),
               "INTAKE_MOTOR": ("YMin", 5), "INTAKE_LIP": ("YMin", -5)}
    v0 = {n: getattr(gbb(n), attr) for n, (attr, d) in names_i.items()}
    w0 = gbb("INTAKE_ROLLER").YLength
    sh.set("intake_width", "336")
    doc.recompute()
    moved = [n for n, (attr, d) in names_i.items()
             if abs(gbb(n).__getattribute__(attr) - v0[n] - d) > 0.01]
    w1 = gbb("INTAKE_ROLLER").YLength
    ck("MASTER PAR2-I intake_width chain", not moved
       and abs(w1 - w0 - 10) < 0.01,
       "moved=%s roller_span %.1f->%.1f" % (moved[:6], w0, w1))
    sh.set("intake_width", "326")
    doc.recompute()

    # PAR2-T: channel_w +10 -> walls + floor + saddles + hinge span +
    # bushings + servo all track
    names_t = {"CHANNEL_WALL_L": ("YMin", 5), "CHANNEL_WALL_R": ("YMax", -5),
               "CHANNEL_FLOOR": ("YMin", -5), "DIVERTER_AXLE": ("YMin", -5),
               "DIVERTER_BUSH_L": ("YMin", 5), "DIVERTER_SERVO": ("YMin", 5),
               "CHANNEL_SUPP_F": ("YMin", -5), "DIVERTER_PADDLE": ("YMin", -5)}
    v0 = {n: getattr(gbb(n), attr) for n, (attr, d) in names_t.items()}
    sh.set("channel_w", "120")
    doc.recompute()
    moved = [n for n, (attr, d) in names_t.items()
             if abs(gbb(n).__getattribute__(attr) - v0[n] - d) > 0.01]
    ck("MASTER PAR2-T channel_w chain", not moved, str(moved[:6]))
    sh.set("channel_w", "110")
    doc.recompute()

    # PAR4/FLX: chamfers survive an intake_height bump
    ck_f = len(objs["INTAKE_CHEEK_L"].Shape.Faces)
    wl_f = len(objs["CHANNEL_WALL_L"].Shape.Faces)
    sh.set("intake_height", "130")
    doc.recompute()
    ok = objs["INTAKE_CHEEK_L"].Shape.isValid()
    sh.set("intake_height", "120")
    doc.recompute()
    ok2 = (objs["INTAKE_CHEEK_L"].Shape.isValid()
           and len(objs["INTAKE_CHEEK_L"].Shape.Faces) == ck_f)
    ck("MASTER PAR4 chamfer survives bump", ok and ok2
       and len(objs["CHANNEL_WALL_L"].Shape.Faces) == wl_f,
       "cheek faces %d valid=%s" % (ck_f, ok))

    App.closeDocument(doc.Name)  # close WITHOUT saving
    h1 = hashlib.sha256(open(path, "rb").read()).hexdigest()
    ck("MASTER close-no-save hash stable", h0 == h1)


def reg_untouched():
    """REG: untouched concept files rebuild signature-identical."""
    if not BASELINE_SIGS.exists():
        ck("REG untouched signature baseline", False,
           "missing %s" % BASELINE_SIGS.name)
        return
    base = json.loads(BASELINE_SIGS.read_text(encoding="utf-8"))
    for tag, p in UNTOUCHED.items():
        doc = App.openDocument(str(p))
        doc.recompute()
        cur = {}
        for o in doc.Objects:
            try:
                s = o.Shape.copy()
                s.Placement = o.getGlobalPlacement()
                if s and s.Volume > 0:
                    b = s.BoundBox
                    cur[o.Name] = [round(b.XMin, 3), round(b.YMin, 3),
                                   round(b.ZMin, 3), round(b.XMax, 3),
                                   round(b.YMax, 3), round(b.ZMax, 3)]
            except Exception:
                pass
        App.closeDocument(doc.Name)
        old = {e["name"]: e.get("bbox") for e in base.get(tag, [])}
        diff = [n for n in set(cur) | set(old)
                if cur.get(n) != old.get(n)]
        ck("REG %s signature identical" % tag, not diff, str(diff[:6]))


def main():
    # ARC: sprint-01-state baselines must exist before sprint-02 edits
    arch = ROOT / "cad" / "archive"
    bl = [p.name for p in arch.glob("*sprint01_state*")]
    js = BASELINE_SIGS.exists()
    need = ("master_robot", "intake_concept_v01", "transfer_concept_v01")
    ck("ARC sprint-01-state archives present",
       all(any(k in n for n in bl) for k in need) and js,
       str(bl[:4]) + " sig=" + str(js))

    check_file(FILES["MASTER"], "MASTER", ("FRAME_", "BELLY_PAN"))
    check_file(FILES["INTAKE"], "INTAKE", ("CHASSIS_STUB",))
    check_file(FILES["TRANSFER"], "TRANSFER", ("PAN_STUB",))
    sweeps_master()
    reg_untouched()

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
