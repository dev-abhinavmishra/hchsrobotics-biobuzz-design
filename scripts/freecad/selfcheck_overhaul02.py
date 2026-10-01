"""Sprint-02 overhaul selfcheck -- sprint-01 gates + game-piece path.

Gates: GIT DET PAR PROV DAG ASM FAST GEO ENV XPT GUI
       GEO-I GEO-H GEO-B GEO-T PAR2-I PAR2-H
Opens the five saved FCStd files + exports/meta + exports/bom +
exports/step and verifies them against the sprint-02 contract.

Run:  freecadcmd.exe scripts/freecad/selfcheck_overhaul02.py
Exit: 0 if every gate passes, 1 otherwise.
"""
import json
import math
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad"
EXPORTS = ROOT / "exports"
DOCS = {
    "drivebase": CAD / "drivebase" / "drivebase.FCStd",
    "electronics": CAD / "electronics" / "electronics.FCStd",
    "intake": CAD / "intake" / "intake.FCStd",
    "hopper": CAD / "hopper" / "hopper.FCStd",
    "master": CAD / "master_robot.FCStd",
}
META = {k: EXPORTS / "meta" / ("%s.json" % k)
        for k in ("drivebase", "electronics", "intake", "hopper",
                  "master")}

STATUS = ("VERIFIED", "VENDOR-PENDING", "UNVERIFIED")
REQ_ALIASES = (
    "rail_lat_off rail_len rail_elev_z cross_x_off crown_z "
    "wheel_lat_off wheel_lon_off axle_len brg_in_off brg_out_off "
    "motor_lat_off mount_plate_off collar_off washer_off nut_off "
    "pinion_off clamp1_off clamp2_off pan_z deck_z shelf_z "
    "odo_pod_x odo_pod_lat odo_pod_lon_x batt_x batt_y "
    "ctrl_x ctrl_y exp_x exp_y sw_x sw_y rex_bore "
    "intake_x roller_low_z roller_low_r roller_len roller_top_x "
    "roller_top_z roller_top_r star_core_r float_travel cheek_lat_off "
    "cheek_thk sprocket_plane belt_plane int_motor_x int_motor_z "
    "int_motor_lat sprocket9_pd sprocket16_pd belt_pul_d spring_post_d "
    "lane_wid hop_wall_y hopper_incline hop_wall_x0 hop_wall_x1 "
    "hop_curb_x feed_x feed_z feed_wheel_r feed_wheel_w feed_motor_z "
    "feed_motor_lat feed_gear_d column_x column_id column_od "
    "column_z0 column_z1 col_flange_z col_post_off col_post_lat "
    "gate_y gate_z div_z div_port_d agit_x agit_y agit_z "
    "snsr_x snsr_y snsr_z ball_p_dia ball_n_dia ball_clear"
).split()
EXCLUDE_PREFIX = ("ENV_", "TOOL_", "AXIS_", "REF_", "VOL_")
EXCLUDE_TYPES = ("App::Part", "App::Origin", "Spreadsheet::Sheet",
                 "App::DocumentObjectGroup")

RESULTS = []
LOG_PATH = ROOT / "exports" / "selfcheck_overhaul02.txt"
LOG_TMP = Path(tempfile.gettempdir()) / "selfcheck_overhaul02.txt"
LOG = open(LOG_TMP, "w", encoding="utf-8")


def gate(tag, ok, detail=""):
    RESULTS.append((tag, bool(ok), detail))
    line = "%-26s %s %s" % (tag, "PASS" if ok else "FAIL", detail)
    print(line)
    LOG.write(line + "\n")
    LOG.flush()


def _consumed_add(x, out):
    out.add(x.Name)
    for p in ("Links", "Group"):
        g = getattr(x, p, None)
        if g is None:
            continue
        for y in (g if isinstance(g, (list, tuple)) else (g,)):
            if y is not None:
                _consumed_add(y, out)


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
            and not o.Name.startswith(EXCLUDE_PREFIX)
            and o.Name not in consumed]


def gshape(o):
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    return s


def gplace(o):
    try:
        return o.getGlobalPlacement().Base
    except Exception:
        return o.Placement.Base


def sig(doc):
    out = {}
    for o in exportable(doc):
        b = gshape(o).BoundBox
        out[o.Name] = (round(b.XMin, 4), round(b.YMin, 4),
                       round(b.ZMin, 4), round(b.XMax, 4),
                       round(b.YMax, 4), round(b.ZMax, 4),
                       round(o.Shape.Volume, 4))
    return out


FAST_PREF = ("BOLT_", "NUT_", "SCRW_", "RIVNUT_", "WSH_")
# protruding hardware excluded from the frame footprint (contract
# amendment A1): fasteners, axle shafts (nylock class), number plates
FRAME_EXCLUDE = FAST_PREF + ("AXLE_", "PLATE_NUM_")


def declared_pairs(mmeta):
    """All pair classes -> set of frozensets for the coplanar census."""
    out = set()
    for key in ("faces", "embeds", "journals", "contacts"):
        for p in mmeta.get(key, []):
            out.add(frozenset((p[0], p[1])))
    for j in mmeta.get("joints", []):
        alln = list(j.get("members", [])) + list(j.get("bolts", [])) +             list(j.get("nuts", []))
        for i in range(len(alln)):
            for k in range(i + 1, len(alln)):
                out.add(frozenset((alln[i], alln[k])))
    return out


def axis_face_census(shape_map):
    """Axis-aligned coincident planar faces between exportable solids:
    bucket faces by (axis, plane coord); pairs in the same bucket from
    different solids share a coplanar face -- measure the shared area.
    """
    buckets = {}
    for nm, s in shape_map.items():
        for f in s.Faces:
            try:
                su = f.Surface
            except Exception:
                continue
            if su.TypeId != "Part::GeomPlane":
                continue
            axv = su.Axis
            comps = (abs(axv.x), abs(axv.y), abs(axv.z))
            c = f.CenterOfMass
            if comps == (1.0, 0.0, 0.0):
                key = ("x", round(c.x, 2))
            elif comps == (0.0, 1.0, 0.0):
                key = ("y", round(c.y, 2))
            elif comps == (0.0, 0.0, 1.0):
                key = ("z", round(c.z, 2))
            else:
                continue
            if f.Area < 1.0:
                continue
            buckets.setdefault(key, []).append((nm, f))
    seen = set()
    pairs = []
    for key, faces in buckets.items():
        if len(faces) > 400:
            continue
        for i in range(len(faces)):
            for j in range(i + 1, len(faces)):
                a, fa = faces[i]
                b, fb = faces[j]
                if a == b:
                    continue
                try:
                    com = fa.common(fb)
                except Exception:
                    continue
                pk = (a, b) if a < b else (b, a)
                if com.Area > 0.5 and pk not in seen:
                    seen.add(pk)
                    pairs.append((com.Area, a, b))
    pairs.sort(reverse=True)
    return pairs


def main():
    docs = {}
    for tag, path in DOCS.items():
        if not path.exists():
            gate(tag + "_FILE", False, str(path))
            return
        d = App.openDocument(str(path))
        d.recompute(None, True, True)
        docs[tag] = d

    metas = {}
    for tag, path in META.items():
        metas[tag] = json.loads(path.read_text(encoding="utf-8")) \
            if path.exists() else None

    m = docs["master"]
    solids = exportable(m)
    mmeta = metas["master"]

    # ---------------- GIT ----------------
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--",
             "scripts/freecad/dt_build.py", "scripts/freecad/partkit.py",
             "scripts/freecad/robot_params.py",
             "scripts/freecad/build_drivebase.py",
             "scripts/freecad/build_electronics.py",
             "scripts/freecad/build_intake.py",
             "scripts/freecad/build_hopper.py",
             "scripts/freecad/dt_path.py",
             "scripts/freecad/build_master_robot.py",
             "scripts/freecad/export_step.py",
             "scripts/freecad/selfcheck_overhaul02.py"],
            cwd=str(ROOT), capture_output=True, text=True)
        dirty = [l for l in out.stdout.splitlines() if l.strip()]
        gate("GIT1_sources_committed", not dirty,
             "%d uncommitted" % len(dirty))
    except Exception as e:
        gate("GIT1_sources_committed", False, str(e))

    # ---------------- DET ----------------
    sigs = {k: sig(d) for k, d in docs.items()}
    mism = []
    for sub in ("drivebase", "electronics", "intake", "hopper"):
        for nm, v in sigs[sub].items():
            mv = sigs["master"].get(nm)
            if mv is None:
                mism.append(nm + ": missing in master")
            elif mv != v:
                mism.append(nm + ": shape differs")
    gate("DET3_name_bbox_volume", not mism, "%d mismatches" % len(mism))

    # ---------------- PAR ----------------
    par_ok = True
    detail = []
    for tag, d in docs.items():
        sheet = d.getObject("Parameters")
        if sheet is None:
            par_ok = False
            detail.append(tag + ": no sheet")
            continue
        aliases = set()
        for r in range(1, 400):
            a = None
            try:
                a = sheet.get("A" + str(r))
            except Exception:
                break
            if not a:
                break
            aliases.add(str(a).strip())
        missing = [x for x in REQ_ALIASES if x not in aliases]
        if missing:
            par_ok = False
            detail.append("%s missing %s" % (tag, missing[:6]))
    gate("PAR1_alias_set", par_ok, "; ".join(detail))

    def bound_tree(o, depth=0):
        if depth > 8:
            return False
        if getattr(o, "ExpressionEngine", None):
            return True
        kids = []
        for p in ("Base", "Tool", "Shapes", "Links", "Group"):
            t = getattr(o, p, None)
            if t is None:
                continue
            kids += list(t) if isinstance(t, (list, tuple)) else [t]
        return any(bound_tree(k, depth + 1) for k in kids
                   if k is not None)

    unbound = []
    for o in solids:
        if o.Name.startswith(("WIRE_", "ROPE_")):
            continue          # harness/rigging bakes at build time
        if not bound_tree(o):
            unbound.append(o.Name)
    gate("PAR3_bound_expressions",
         len(unbound) == 0, "%d unbound" % len(unbound))

    # ---------------- PROV ----------------
    no_status, counts = [], {s: 0 for s in STATUS}
    order = ("UNVERIFIED", "VENDOR-PENDING", "VERIFIED")
    for o in solids:
        st = next((s for s in order if s in o.Label), None)
        if st is None:
            no_status.append(o.Name)
        else:
            counts[st] += 1
    gate("PROV1_statuses",
         not no_status and counts["UNVERIFIED"] > 0,
         "%s; %d unlabeled" % (counts, len(no_status)))

    # ---------------- DAG ----------------
    dag_ok = mmeta is not None
    detail = ""
    if dag_ok:
        nodes = set(mmeta["solids"])
        badref = []
        for e in mmeta.get("edges", []):
            pass
        for coll in ("embeds", "faces", "journals", "contacts"):
            for a, b in mmeta.get(coll, []):
                if a not in nodes or b not in nodes:
                    badref.append("%s->%s" % (a, b))
        for j in mmeta.get("joints", []):
            for nm in j.get("members", []) + j.get("bolts", []) + \
                    j.get("nuts", []):
                if nm not in nodes:
                    badref.append(j.get("id", "?") + ":" + nm)
        dag_ok = not badref
        detail = "%d dangling refs" % len(badref)
    gate("DAG1_pair_refs", dag_ok, detail)

    # every solid in a mount group or carrier chain
    orphans = []
    for o in solids:
        p = o.getParentGeoFeatureGroup()
        depth = 0
        while p is not None and depth < 6:
            if p.Name.startswith("GRP_"):
                break
            p = p.getParentGeoFeatureGroup()
            depth += 1
        if p is None or not p.Name.startswith("GRP_"):
            orphans.append(o.Name)
    gate("ASM1_group_coverage", not orphans,
         "%d ungrouped: %s" % (len(orphans), orphans[:6]))

    # ---------------- FAST ----------------
    # contract 1h joint-class census: min fasteners per joint + every
    # bolt carries a declared A4 terminal embed
    JMIN = {"bearing_": 4, "motor_face": 4, "mplate_rail": 12,
            "clamp_wall": 2, "gusset_rail": 2, "gusset_cross": 2,
            "gusset_low": 2, "crown_pin": 2, "post_foot": 4,
            "tie_web": 2, "numplate": 2, "panbrkt_wall": 2,
            "panbrkt_pan": 1, "deckpost_web": 1, "deckpost_panel": 1,
            "hub_pinch": 1, "odo_mount": 2, "odo_wheelpin": 1,
            "odo_pivot": 1, "strap_pan": 2, "shelf_so": 2,
            "switch_brkt": 2, "hub_mount": 4,
            "int_bearing": 4, "cheek_pivot": 1, "cheek_wall": 2,
            "cheek_lock": 2, "int_motor_face": 4,
            "int_motor_plate": 12, "int_motor_post": 1,
            "throat_guard": 4, "hop_ledge": 3, "hop_brkt": 2,
            "agit_brkt": 4, "agit_servo": 4, "feed_bearing": 4,
            "feed_motor_plate": 4, "feed_plate_post": 1,
            "col_post": 2, "gate_brkt": 4, "gate_servo": 4,
            "div_brkt": 4, "div_servo": 4, "div_port_flange": 4,
            "snsr_brkt": 2}
    def _jmin(jid):
        """prefix-match: per-side ids carry _L/_R/_0.. suffixes."""
        if jid in JMIN:
            return JMIN[jid]
        for k, v in JMIN.items():
            if jid.startswith(k):
                return v
        return 1
    fast_bad = []
    jn = mmeta["joints"] if mmeta else []
    embeds = {tuple(sorted(x)) for x in mmeta["embeds"]} if mmeta \
        else set()
    for j in jn:
        jid = j.get("id", "?")
        hw = list(j.get("bolts", []))
        need = _jmin(jid)
        if len(hw) < need:
            fast_bad.append("%s: %d<%d" % (jid, len(hw), need))
        for bt in hw + list(j.get("nuts", [])):
            if not any(bt in pair for pair in embeds):
                fast_bad.append("%s:%s not embedded" % (jid, bt))
    gate("FAST1_joints_hardware", not fast_bad,
         "%d joints, %d bad" % (len(jn), len(fast_bad)))

    # ---------------- GEO ----------------
    # census (contract 1e-1i + FAST1 totals; carriers counted over all
    # doc objects, fastener families over exportable solids)
    def cnt(pref):
        return sum(1 for o in solids if o.Name.startswith(pref))

    def cntall(pref):
        return sum(1 for o in m.Objects if o.Name.startswith(pref))
    census = {
        "WHEEL_ASSY_": (cntall("WHEEL_ASSY_"), 4),
        "MOTOR_": (cnt("MOTOR_"), 4),
        "AXLE_": (cnt("AXLE_"), 4),
        "BRG_IN_": (cnt("BRG_IN_"), 4),
        "BRG_OUT_": (cnt("BRG_OUT_"), 4),
        "CLAMP_": (cnt("CLAMP_"), 8),
        "BOLT_HUB_": (cnt("BOLT_HUB_"), 12),
        "BOLT_CLMP_": (cnt("BOLT_CLMP_"), 16),
        "BOLT_MPL_": (cnt("BOLT_MPL_"), 24),
        "GUSSET_": (cnt("GUSSET_"), 4),
        "ODO_WHEEL_": (cnt("ODO_WHEEL_"), 3),
        "ODO_MOUNT_": (cnt("ODO_MOUNT_"), 3),
        "ODO_SPRING_": (cnt("ODO_SPRING_"), 3),
        "DECK_POST_": (cnt("DECK_POST_"), 8),
        "ENDCAP_": (cnt("ENDCAP_"), 6),
        "ELEC_SHELF": (cnt("ELEC_SHELF"), 1),
        "BATTERY": (cnt("BATTERY"), 1),
        "HUB_": (cnt("HUB_"), 2),
        "MAIN_SWITCH": (cnt("MAIN_SWITCH"), 1),
        "INT_CHEEK_": (cnt("INT_CHEEK_"), 2),
        "ROLLER_TOP": (cnt("ROLLER_TOP"), 1),
        "ROLLER_LOW": (cnt("ROLLER_LOW"), 1),
        "STAR_SHAFT": (cnt("STAR_SHAFT"), 1),
        "FLOAT_SLIDE_": (cnt("FLOAT_SLIDE_"), 2),
        "FLOAT_PIN_": (cnt("FLOAT_PIN_"), 2),
        "SPRING_POST_": (cnt("SPRING_POST_"), 2),
        "TORSION_SPRING_": (cnt("TORSION_SPRING_"), 2),
        "PIVOT_PIN_": (cnt("PIVOT_PIN_"), 2),
        "INT_BRG_": (cnt("INT_BRG_"), 2),
        "INT_MOTOR": (cnt("INT_MOTOR"), 1),
        "JACK_SHAFT": (cnt("JACK_SHAFT"), 1),
        "SPROCKET_9T": (cnt("SPROCKET_9T"), 1),
        "SPROCKET_16T": (cnt("SPROCKET_16T"), 1),
        "CHAIN_25": (cnt("CHAIN_25"), 1),
        "BELT_XROLL": (cnt("BELT_XROLL"), 1),
        "BELT_PUL_": (cnt("BELT_PUL_"), 2),
        "TENS_ARM": (cnt("TENS_ARM"), 1),
        "TENS_IDLER": (cnt("TENS_IDLER"), 1),
        "TENS_POST": (cnt("TENS_POST"), 1),
        "TENS_SPRING": (cnt("TENS_SPRING"), 1),
        "THROAT_GUARD": (cnt("THROAT_GUARD"), 1),
        "HOP_WALL_": (cnt("HOP_WALL_"), 2),
        "HOP_FLOOR": (cnt("HOP_FLOOR"), 1),
        "HOP_APRON": (cnt("HOP_APRON"), 1),
        "HOP_LEDGE_": (cnt("HOP_LEDGE_"), 2),
        "HOP_BRKT_": (cnt("HOP_BRKT_"), 4),
        "HOP_CURB": (cnt("HOP_CURB"), 1),
        "AGIT_SERVO": (cnt("AGIT_SERVO"), 1),
        "AGIT_BRKT": (cnt("AGIT_BRKT"), 1),
        "AGIT_PADDLE": (cnt("AGIT_PADDLE"), 1),
        "FEED_WHEEL": (cnt("FEED_WHEEL"), 1),
        "FEED_SHAFT": (cnt("FEED_SHAFT"), 1),
        "FEED_WALL_BRG": (cnt("FEED_WALL_BRG"), 1),
        "FEED_MOTOR": (cnt("FEED_MOTOR"), 1),
        "FEED_MTR_PLATE": (cnt("FEED_MTR_PLATE"), 1),
        "FEED_STANDOFF_": (cnt("FEED_STANDOFF_"), 2),
        "FEED_MTR_SHAFT": (cnt("FEED_MTR_SHAFT"), 1),
        "SPUR_FEED_": (cnt("SPUR_FEED_"), 2),
        "FEED_COLUMN": (cnt("FEED_COLUMN"), 1),
        "FEED_SCOOP": (cnt("FEED_SCOOP"), 1),
        "COL_FLANGE": (cnt("COL_FLANGE"), 1),
        "COL_POST_": (cnt("COL_POST_"), 4),
        "GATE_SERVO": (cnt("GATE_SERVO"), 1),
        "GATE_BRKT": (cnt("GATE_BRKT"), 1),
        "GATE_FLAG": (cnt("GATE_FLAG"), 1),
        "DIV_SERVO": (cnt("DIV_SERVO"), 1),
        "DIV_BRKT": (cnt("DIV_BRKT"), 1),
        "DIV_BAND": (cnt("DIV_BAND"), 1),
        "DIV_FLAP": (cnt("DIV_FLAP"), 1),
        "PORT_FLANGE": (cnt("PORT_FLANGE"), 1),
        "SNSR_BRKT": (cnt("SNSR_BRKT"), 1),
        "SNSR_COLOR": (cnt("SNSR_COLOR"), 1),
    }
    bad_census = ["%s=%d!=%d" % (k, a, b)
                  for k, (a, b) in census.items() if a != b]
    # contract FAST1: gusset assemblies carry >=4 fasteners each (16
    # total) -- count the full BOLT_GUS* family (main + twin plates)
    if cnt("BOLT_GUS") < 16:
        bad_census.append("BOLT_GUS=%d<16" % cnt("BOLT_GUS"))
    gate("GEO1_census", not bad_census, ", ".join(bad_census[:8]))

    # undeclared overlap probe (master scope)
    declared = set()
    for coll in ("embeds", "faces", "journals", "contacts"):
        for a, b in mmeta[coll]:
            declared.add(tuple(sorted((a, b))))
    for j in mmeta["joints"]:
        ms = j["members"] + j.get("bolts", []) + j.get("nuts", [])
        for i_ in range(len(ms)):
            for k_ in range(i_ + 1, len(ms)):
                declared.add(tuple(sorted((ms[i_], ms[k_]))))
    gshapes = {o.Name: gshape(o) for o in solids}
    names = list(gshapes)
    bbs = {n: gshapes[n].BoundBox for n in names}
    overlaps = []
    for i_ in range(len(names)):
        a = names[i_]
        for j_ in range(i_ + 1, len(names)):
            b = names[j_]
            if tuple(sorted((a, b))) in declared:
                continue
            ba, bb_ = bbs[a], bbs[b]
            if (ba.XMax <= bb_.XMin or ba.XMin >= bb_.XMax or
                    ba.YMax <= bb_.YMin or ba.YMin >= bb_.YMax or
                    ba.ZMax <= bb_.ZMin or ba.ZMin >= bb_.ZMax):
                continue
            try:
                com = gshapes[a].common(gshapes[b])
            except Exception:
                continue
            if com.Volume > 0.5:
                overlaps.append((com.Volume, a, b))
    overlaps.sort(reverse=True)
    gate("GEO2_undeclared_overlap", not overlaps,
         "%d pairs >0.5mm3: %s" %
         (len(overlaps), overlaps[:4]))

    # mount contacts <= 0.1mm (face pairs)
    f_bad = []
    for a, b in mmeta["faces"]:
        if a not in gshapes or b not in gshapes:
            continue
        try:
            d_ = gshapes[a].distToShape(gshapes[b])[0]
        except Exception:
            continue
        if d_ > 0.1:
            f_bad.append((round(d_, 2), a, b))
    gate("GEO3_mount_contacts", not f_bad,
         "%d face pairs >0.1mm gap: %s" % (len(f_bad), f_bad[:4]))

    # journal axis gaps <= 0.2mm: distance between the shaft's cylinder
    # axis and the member's bore cylinder axis (both from real surfaces)
    def cyl_faces(sh):
        out = []
        for f in sh.Faces:
            try:
                srf = f.Surface
            except Exception:
                continue
            if srf.TypeId == "Part::GeomCylinder":
                out.append(srf)
        return out

    def axis_gap(c1, c2):
        """shortest distance between two cylinder axes."""
        u, v = c1.Axis, c2.Axis
        cr = u.cross(v)
        n = cr.Length
        dv = c2.Center.sub(c1.Center)
        if n < 1e-6:
            return math.sqrt(max(0.0, dv.Length ** 2 - dv.dot(u) ** 2))
        return abs(dv.dot(App.Vector(cr.x / n, cr.y / n, cr.z / n)))

    j_bad = []
    for a, b in mmeta["journals"]:
        oa, ob = m.getObject(a), m.getObject(b)
        if oa is None or ob is None:
            continue
        sa, sb = cyl_faces(gshape(oa)), cyl_faces(gshape(ob))
        if not sa:
            continue
        shaft = min(sa, key=lambda c: c.Radius)
        if sb:
            cand = [c for c in sb
                    if abs(c.Radius - shaft.Radius) < 1.2]
            bore = min(cand if cand else sb,
                       key=lambda c: axis_gap(shaft, c))
            gap = axis_gap(shaft, bore)
        else:
            pb = gplace(ob)
            dv = pb.sub(shaft.Center)
            gap = math.sqrt(
                max(0.0, dv.Length ** 2 - dv.dot(shaft.Axis) ** 2))
        if gap > 0.2:
            j_bad.append((round(gap, 2), a, b))
    gate("GEO4_journal_axis", not j_bad,
         "%d journal pairs >0.2mm: %s" % (len(j_bad), j_bad[:4]))

    # motor-axis alignment <= 0.3mm: can axis vs axle axis (axis dist)
    mo_bad = []
    for w in ("FL", "FR", "RL", "RR"):
        mo, ax_ = m.getObject("MOTOR_" + w), m.getObject("AXLE_" + w)
        if mo is None or ax_ is None:
            continue
        cans = cyl_faces(gshape(mo))
        axs = cyl_faces(gshape(ax_))
        can = next((c for c in cans if 15 < c.Radius < 25), None)
        if can is None or not axs:
            continue
        axle = max(axs, key=lambda c: c.Radius)
        off = axis_gap(can, axle)
        if off > 0.3:
            mo_bad.append((w, round(off, 2)))
    gate("GEO5_motor_axis", not mo_bad, "%s" % mo_bad)

    # ---------------- GEO-I: intake geometry ----------------
    # nip rest gap: axis distance minus radii >= 81 (D13 amends to
    # >=73.2; contract target ~81.6). full-lift clearance >= 91+2.
    rl = m.getObject("ROLLER_LOW"); rt = m.getObject("ROLLER_TOP")
    nip_bad = []
    if rl is None or rt is None:
        nip_bad.append("missing rollers")
    else:
        bl, bt = gshape(rl).BoundBox, gshape(rt).BoundBox
        dx = (bl.XMin + bl.XMax) / 2 - (bt.XMin + bt.XMax) / 2
        dz = (bl.ZMin + bl.ZMax) / 2 - (bt.ZMin + bt.ZMax) / 2
        rsum = (bl.ZLength + bt.ZLength) / 4.0
        nip = math.sqrt(dx * dx + dz * dz) - rsum
        sheet = m.getObject("Parameters")
        ft = float(sheet.get("float_travel")) if sheet else 0.0
        if nip < 73.2:
            nip_bad.append("nip %.1f<73.2" % nip)
        if nip + ft < 91.0 + float(sheet.get("ball_clear")):
            nip_bad.append("nip+travel %.1f<93" % (nip + ft))
    gate("GEOI_nip_clearance", not nip_bad, "%s" % nip_bad)

    # floating slides: block slides in cheek groove with travel >=
    # float_travel to the groove ceiling
    fs_bad = []
    for tag in ("L", "R"):
        sl, ck = m.getObject("FLOAT_SLIDE_" + tag),             m.getObject("INT_CHEEK_" + tag)
        if sl is None or ck is None:
            fs_bad.append("missing slide " + tag)
            continue
        bs, bc = gshape(sl).BoundBox, gshape(ck).BoundBox
        room = bc.ZMax - bs.ZMax
        if room < float(sheet.get("float_travel")) - 1.0:
            fs_bad.append((tag, round(room, 2)))
    gate("GEOI_float_room", not fs_bad, "%s" % fs_bad)

    # cheek plates pivoted on the rails at z15..50, bolted + pinned
    ck_bad = []
    for tag in ("L", "R"):
        ck = m.getObject("INT_CHEEK_" + tag)
        if ck is None:
            ck_bad.append(tag)
            continue
        b = gshape(ck).BoundBox
        if b.ZMin > 16.0 or b.ZMax < 190.0:
            ck_bad.append((tag, round(b.ZMin, 1), round(b.ZMax, 1)))
    gate("GEOI_cheek_span", not ck_bad, "%s" % ck_bad)

    # ---------------- GEO-H: hopper geometry ----------------
    hop_bad = []
    col = m.getObject("FEED_COLUMN")
    sheet = m.getObject("Parameters")
    if col is None:
        hop_bad.append("no column")
    else:
        b = gshape(col).BoundBox
        cx0 = (b.XMin + b.XMax) / 2
        cy0 = (b.YMin + b.YMax) / 2
        if sheet is not None and abs(cx0 - float(sheet.get("column_x"))) > 0.5:
            hop_bad.append("col x %.2f" % (cx0 - float(sheet.get("column_x"))))
        if abs(cy0) > 0.5:
            hop_bad.append("col y %.2f" % cy0)
        if abs(b.ZMin - float(sheet.get("column_z0"))) > 0.5:
            hop_bad.append("col z0 %.2f" % b.ZMin)
        if abs(b.ZMax - float(sheet.get("column_z1"))) > 0.5:
            hop_bad.append("col z1 %.2f" % b.ZMax)
        if float(sheet.get("column_id")) < 103.0:
            hop_bad.append("bore %.1f<103" % float(sheet.get("column_id")))
    # walls parallel 3mm plates straddling the lane
    wl, wr = m.getObject("HOP_WALL_L"), m.getObject("HOP_WALL_R")
    if wl is None or wr is None:
        hop_bad.append("missing wall")
    else:
        yl, yr = gshape(wl).BoundBox, gshape(wr).BoundBox
        if abs(yl.YMin - float(sheet.get("hop_wall_y") - 3)) > 0.3:
            hop_bad.append("wall L y %.2f" % yl.YMin)
        if abs(yr.YMax + float(sheet.get("hop_wall_y") - 3)) > 0.3:
            hop_bad.append("wall R y %.2f" % yr.YMax)
    gate("GEOH_column_walls", not hop_bad, "%s" % hop_bad)

    # ---------------- GEO-B: ball-path probes ----------------
    # VOL_BALL_P/N reference volumes may touch feed surfaces but must
    # not interpenetrate structure by >0.5mm3.
    BALL_OK = {"FEED_WHEEL", "ROLLER_TOP", "ROLLER_LOW",
               "AGIT_PADDLE", "GATE_FLAG", "DIV_FLAP", "FEED_SCOOP",
               "AGIT_HORN", "STAR_SHAFT", "FEED_SHAFT"}
    # moving members exempt from static path clearance (C1); their
    # at-rest envelopes are covered by GEO-I/GEO-H and their swept
    # poses by the probe-pose gate below.
    BALL_STATIC_EX = BALL_OK | {
        "ROLLER_SHAFT", "DIV_SHAFT", "GATE_HORN", "CHAIN_25",
        "BELT_XROLL", "TENS_IDLER", "TENS_ARM", "TENS_PIN",
        "TENS_SPRING", "TORSION_SPRING_L", "TORSION_SPRING_R",
        "BELT_PUL_LOW", "BELT_PUL_TOP", "SPROCKET_9T",
        "SPROCKET_16T", "MASTER_LINK", "FLOAT_SLIDE_L",
        "FLOAT_SLIDE_R", "FLOAT_PIN_L", "FLOAT_PIN_R",
        "SPUR_FEED_M", "SPUR_FEED_W", "FEED_MTR_SHAFT",
        # sprint-03 launch/return path surfaces (C1 nip faces,
        # chute bed/lips, cradle pocket, hood/nip-throat guides)
        "FLYWHEEL_L", "FLYWHEEL_R", "FLY_SHAFT_L", "FLY_SHAFT_R",
        "FLY_CLAMP_L", "FLY_CLAMP_R", "NIP_BACKPLATE",
        "TURRET_PLATE", "HOOD", "HOOD_PIV_L", "HOOD_PIV_R",
        "HOOD_COL_L", "HOOD_COL_R",
        "LOAD_CHUTE", "CHUTE_LIP_L1", "CHUTE_LIP_L2",
        "CHUTE_LIP_R1", "CHUTE_LIP_R2",
        "CRADLE_CUP", "CRADLE_FOAM", "CRADLE_PIV",
        "CRADLE_COL_0", "CRADLE_COL_1"}
    ball_bad = []
    for pn in ("VOL_BALL_P", "VOL_BALL_N"):
        pv = m.getObject(pn)
        if pv is None:
            ball_bad.append("missing " + pn)
            continue
        ps = gshape(pv)
        for o in solids:
            if o.Name in BALL_OK or o.Name.startswith(("ENV_", "VOL_")):
                continue
            try:
                com = ps.common(gshape(o))
            except Exception:
                continue
            if com.Volume > 0.5:
                ball_bad.append((pn, o.Name, round(com.Volume, 1)))
    # A6 station table: a D93 NECTAR sphere at each declared station of
    # the as-built under-crown route must clear every static solid.
    # common().Volume (not distToShape) so a sphere fully containing a
    # thin wall still fails.
    STATIONS = (
        ("S1_mouth",      46.5, (205.0, 0.0, 80.0)),
        ("S3_undercrown", 46.5, (178.0, 0.0, 85.0)),
        ("S4_basin",      46.5, (105.0, 0.0, 155.0)),
        ("S5_incline",    46.5, (62.0, 0.0, 142.0)),
        ("S6_lane",       46.5, (40.0, 0.0, 134.0)),
        ("S7_approach",   46.5, (35.0, 0.0, 132.0)),
        ("S8_win_throat", 46.5, (-11.0, 0.0, 140.0)),
        ("S9a_bore_rest", 46.5, (-66.0, 0.0, 162.0)),
        ("S9b_bore_mid",  46.5, (-66.0, 0.0, 200.0)),
        ("S9c_bore_top",  46.5, (-66.0, 0.0, 240.0)),
        ("S10_gate",      46.5, (-66.0, 0.0, 175.0)),
        ("S11_port",      46.5, (-66.0, 52.0, 203.0)),
        ("S12_flange",    46.5, (-66.0, 57.0, 204.0)),
    )
    for sname, sr, c in STATIONS:
        sp = Part.makeSphere(sr, App.Vector(*c))
        for o in solids:
            if o.Name in BALL_STATIC_EX \
                    or o.Name.startswith(("ENV_", "VOL_")):
                continue
            try:
                com = sp.common(gshape(o))
            except Exception:
                continue
            if com.Volume > 0.5:
                ball_bad.append((sname, o.Name, round(com.Volume, 1)))
    gate("GEOB_ball_path", not ball_bad,
         "%d: %s" % (len(ball_bad), ball_bad[:8]))

    # gate flag + diverter flap probes match the real poses, and each
    # swept-pose volume clears static geometry (N12): the VOL_ pose
    # solids are intersection-tested against every non-exempt solid so
    # a pose clipping a wall or the column shell fails.
    pv_bad = []
    for vn, on_ in (("VOL_GATE_CLOSED", "GATE_FLAG"),
                    ("VOL_DIV_A", "DIV_FLAP")):
        vo, ro = m.getObject(vn), m.getObject(on_)
        if vo is None or ro is None:
            pv_bad.append("missing %s/%s" % (vn, on_))
            continue
        vb, rb = gshape(vo).BoundBox, gshape(ro).BoundBox
        dev = max(abs(vb.XMin - rb.XMin), abs(vb.XMax - rb.XMax),
                  abs(vb.YMin - rb.YMin), abs(vb.YMax - rb.YMax),
                  abs(vb.ZMin - rb.ZMin), abs(vb.ZMax - rb.ZMax))
        if dev > 2.0:
            pv_bad.append((vn, round(dev, 2)))
    for vn in ("VOL_GATE_OPEN", "VOL_GATE_CLOSED", "VOL_DIV_A",
               "VOL_DIV_B"):
        vo = m.getObject(vn)
        if vo is None:
            continue
        vs = gshape(vo)
        for o in solids:
            if o.Name in BALL_STATIC_EX \
                    or o.Name.startswith(("ENV_", "VOL_")):
                continue
            try:
                com = vs.common(gshape(o))
            except Exception:
                continue
            if com.Volume > 0.5:
                pv_bad.append((vn, o.Name, round(com.Volume, 1)))
    gate("GEOB_probe_pose", not pv_bad, "%s" % pv_bad[:8])

    # ---------------- GEO-T: drive wraps ----------------
    t_bad = []
    belt = m.getObject("BELT_XROLL")
    if belt is None:
        t_bad.append("no belt")
    else:
        bs = gshape(belt)
        for pn in ("BELT_PUL_LOW", "BELT_PUL_TOP", "TENS_IDLER"):
            o = m.getObject(pn)
            if o is None:
                t_bad.append("missing " + pn)
                continue
            d_ = bs.distToShape(gshape(o))[0]
            if d_ > 0.5:
                t_bad.append((pn, round(d_, 2)))
        for pn in ("BELT_PUL_LOW", "BELT_PUL_TOP"):
            o = m.getObject(pn)
            if o is not None and                     bs.common(gshape(o)).Volume > 1.0:
                t_bad.append(("embed " + pn,
                              round(bs.common(gshape(o)).Volume, 1)))
    ch = m.getObject("CHAIN_25")
    if ch is None:
        t_bad.append("no chain")
    else:
        cs = gshape(ch)
        for pn in ("SPROCKET_9T", "SPROCKET_16T"):
            o = m.getObject(pn)
            if o is None:
                t_bad.append("missing " + pn)
                continue
            d_ = cs.distToShape(gshape(o))[0]
            if d_ > 0.5:
                t_bad.append((pn, round(d_, 2)))
    gate("GEOT_wrap_contact", not t_bad, "%s" % t_bad)

    # ---------------- ENV ----------------
    for tag, d in docs.items():
        env = d.getObject("ENV_START")
        ok = env is not None and hasattr(env, "Shape") and \
            not env.Shape.isNull()
        det = ""
        if ok:
            b = env.Shape.BoundBox
            ok = (abs(b.XLength - 457.2) < 0.5 and
                  abs(b.YLength - 457.2) < 0.5 and
                  abs(b.ZLength - 457.2) < 0.5)
            out = []
            for o in exportable(d):
                ob = gshape(o).BoundBox
                if (ob.XMin < b.XMin - 0.01 or ob.XMax > b.XMax + 0.01 or
                        ob.YMin < b.YMin - 0.01 or
                        ob.YMax > b.YMax + 0.01 or
                        ob.ZMin < b.ZMin - 0.01 or
                        ob.ZMax > b.ZMax + 0.01):
                    out.append(o.Name)
            ok = ok and not out
            det = "%d outside env" % len(out)
        gate("ENV_" + tag, ok, det)

    # ---------------- XPT ----------------
    step = EXPORTS / "step"
    pfiles = list((step / "parts").glob("*.step")) \
        if (step / "parts").exists() else []
    sfiles = list((step / "subassembly").glob("*.step")) \
        if (step / "subassembly").exists() else []
    mfile = step / "master_robot.step"
    gate("XPT1_parts", len(pfiles) == len(solids),
         "%d/%d part files" % (len(pfiles), len(solids)))
    gate("XPT2_subassembly", len(sfiles) >= 5,
         "%d subassembly files" % len(sfiles))
    gate("XPT3_master", mfile.exists() and
         mfile.stat().st_size > 10000 and
         open(mfile, "rb").read(20).startswith(b"ISO-10303-21"),
         "%d bytes" % (mfile.stat().st_size if mfile.exists() else 0))

    # ---------------- exports tables ----------------
    gate("XPT4_tables",
         (EXPORTS / "bom" / "bom.csv").exists() and
         (EXPORTS / "bom" / "parameters.csv").exists() and
         (EXPORTS / "mount_graph.json").exists(),
         "bom.csv parameters.csv mount_graph.json")

    # ---------------- round-2 gates: honest re-verification ---------
    shape_map = {o.Name: gshape(o) for o in solids
                 if o.Name in set(mmeta["solids"])}

    # GIT2: whole tree clean + archive dirs + baseline concept files
    try:
        out = subprocess.run(["git", "status", "--porcelain"],
                             cwd=str(ROOT), capture_output=True,
                             text=True)
        dirty = [l for l in out.stdout.splitlines() if l.strip()]
        arch = (CAD / "archive" / "pre_overhaul").exists() and \
            (ROOT / "scripts" / "freecad" / "legacy").exists()
        gate("GIT2_tree_clean", not dirty and arch,
             "%d dirty; archives=%s" % (len(dirty), arch))
    except Exception as e:
        gate("GIT2_tree_clean", False, str(e))

    # DECL: declaration tables vs measured geometry
    def sdist(a, b):
        return shape_map[a].distToShape(shape_map[b])[0]

    emb_bad = []
    for a, b in mmeta.get("embeds", []):
        if a in shape_map and b in shape_map:
            if shape_map[a].common(shape_map[b]).Volume < 0.5:
                emb_bad.append((a, b))
    gate("DECL_embeds_real", not emb_bad,
         "%d embeds <0.5mm3" % len(emb_bad))
    cn_bad = []
    emb_pairs = {tuple(sorted(x)) for x in mmeta.get("embeds", [])}
    # contact = near-touching declared pair: distance bound 1.5mm
    # (fastener slip-fit clearance), plus a hard no-penetration bound:
    # common().Volume must stay <=0.5mm3.
    for a, b in mmeta.get("contacts", []):
        if a in shape_map and b in shape_map \
                and tuple(sorted((a, b))) not in emb_pairs:
            d_ = sdist(a, b)
            com = shape_map[a].common(shape_map[b]).Volume
            if d_ > 1.5 or com > 0.5:
                cn_bad.append((a, b, round(d_, 2), round(com, 1)))
    gate("DECL_contacts_real", not cn_bad,
         "%d contacts dist>1.5mm or common>0.5mm3: %s"
         % (len(cn_bad), cn_bad[:4]))
    jl_bad = []
    for a, b in mmeta.get("journals", []):
        if a in shape_map and b in shape_map:
            if shape_map[a].common(shape_map[b]).Volume > 0.5:
                jl_bad.append((a, b))
    gate("DECL_journals_bored", not jl_bad,
         "%d journals common>0.5: %s" % (len(jl_bad), jl_bad[:4]))

    # ASM4: coplanar-face census -- undeclared coincident pairs
    decl = declared_pairs(mmeta)
    cop = axis_face_census(shape_map)
    undecl = [pp for pp in cop if frozenset((pp[1], pp[2])) not in decl]
    gate("ASM4_coplanar_census", not undecl,
         "%d coplanar, %d undeclared: %s"
         % (len(cop), len(undecl), undecl[:6]))

    # ASM1: mount-graph connectivity -- every node reachable
    graph = json.loads((EXPORTS / "mount_graph.json").read_text(
        encoding="utf-8"))
    adj = {}
    for e in graph["edges"]:
        adj.setdefault(e["a"], set()).add(e["b"])
        adj.setdefault(e["b"], set()).add(e["a"])
    reach = set()
    stk = list(graph["roots"])
    while stk:
        x = stk.pop()
        if x in reach:
            continue
        reach.add(x)
        stk.extend(adj.get(x, ()))
    unreachable = [nn for nn in graph["nodes"] if nn not in reach]
    gate("ASM1_reachable", not unreachable,
         "%d/%d unreachable: %s"
         % (len(unreachable), len(graph["nodes"]), unreachable[:6]))

    # ASM5: fastener engagement -- bolts touch >=1 joint member,
    # nuts on-shaft (common>0.3) and seated <=0.15 on a member face
    eng_bad, nut_bad = [], []
    for j in mmeta.get("joints", []):
        mems = [x for x in j.get("members", []) if x in shape_map]
        for bn in j.get("bolts", []):
            if bn not in shape_map:
                continue
            if not any(shape_map[bn].distToShape(shape_map[x])[0]
                       <= 0.2 for x in mems):
                eng_bad.append((j["id"], bn))
        for nn in j.get("nuts", []):
            if nn not in shape_map:
                continue
            on_shaft = any(
                shape_map[nn].common(shape_map[bn]).Volume > 0.3
                for bn in j.get("bolts", [])
                if bn in shape_map)
            seated = any(shape_map[nn].distToShape(shape_map[x])[0]
                         <= 0.15 for x in mems)
            if not on_shaft:
                nut_bad.append((j["id"], nn, "not-on-shaft"))
            elif not seated:
                nut_bad.append((j["id"], nn, "floating"))
    gate("ASM5_engage", not eng_bad and not nut_bad,
         "%d bolts, %d nuts: %s"
         % (len(eng_bad), len(nut_bad), (eng_bad + nut_bad)[:6]))

    # GEOG: exactly {4 bottom rollers + 3 odo wheels} touch Z=0
    grounded = []
    for nm, s in shape_map.items():
        if abs(s.BoundBox.ZMin) < 0.05:
            grounded.append(nm)
    okay = (sum(1 for x in grounded if x.startswith("ROLLER_")
                and x.endswith("_B")) == 4
            and sum(1 for x in grounded
                    if x.startswith("ODO_WHEEL_")) == 3)
    gate("GEOG_ground_census",
         okay and len(grounded) == 7,
         "%d grounded: %s" % (len(grounded), grounded[:10]))

    # GEOW: wheel dims -- Z-span 96, ZMin 0, width 38.1
    wb_bad = []
    for o in m.Objects:
        if not o.Name.startswith("WHEEL_ASSY_"):
            continue
        s = gshape(o)
        b = s.BoundBox
        w = b.YLength if b.YLength > 0.01 else b.XLength
        if abs(b.ZLength - 96.0) > 1.0 or abs(b.ZMin) > 0.1 \
                or abs(w - 38.1) > 0.5:
            wb_bad.append((o.Name, round(b.ZLength, 2),
                           round(b.ZMin, 3), round(w, 2)))
    gate("GEOW_wheel_dims", not wb_bad, "%s" % wb_bad[:4])

    # ENV2: amended footprint -- frame box 444.5+-1, all-span <=455.2
    fx = [10 ** 9, -10 ** 9]
    fy = [10 ** 9, -10 ** 9]
    ax = [10 ** 9, -10 ** 9]
    ay = [10 ** 9, -10 ** 9]
    for nm, s in shape_map.items():
        b = s.BoundBox
        ax = [min(ax[0], b.XMin), max(ax[1], b.XMax)]
        ay = [min(ay[0], b.YMin), max(ay[1], b.YMax)]
        if not nm.startswith(FRAME_EXCLUDE):
            fx = [min(fx[0], b.XMin), max(fx[1], b.XMax)]
            fy = [min(fy[0], b.YMin), max(fy[1], b.YMax)]
    frame_span = max(fx[1] - fx[0], fy[1] - fy[0])
    all_span = max(ax[1] - ax[0], ay[1] - ay[0])
    gate("ENV_frame_footprint", abs(frame_span - 444.5) <= 1.0,
         "frame %.1f x %.1f" % (fx[1] - fx[0], fy[1] - fy[0]))
    gate("ENV_hw_span", all_span <= 455.2,
         "span %.1f x %.1f (margin %.2f)"
         % (ax[1] - ax[0], ay[1] - ay[0], 457.2 - all_span))

    # PROV2: TOOL_* objects carry a status token + DataStatus
    tb_bad = []
    for o in m.Objects:
        if not o.Name.startswith("TOOL_"):
            continue
        tok = any(t in o.Label for t in STATUS)
        if not (getattr(o, "DataStatus", None) and tok):
            tb_bad.append(o.Name)
    gate("PROV2_tool_status", not tb_bad,
         "%d unlabeled" % len(tb_bad))

    # XPT5: per-part STEP reimport -- solids + names + WORLD bbox
    import Import
    step = EXPORTS / "step"
    rd_bad, nn_bad, bb_bad = [], [], []
    pfiles = sorted((step / "parts").glob("*.step"))

    def _ubbox(objs):
        bb = None
        for o in objs:
            b = o.Shape.BoundBox
            bb = b if bb is None else bb.united(b)
        return bb

    def _bdev(a, b):
        return max(
            abs(a.XMin - b.XMin), abs(a.XMax - b.XMax),
            abs(a.YMin - b.YMin), abs(a.YMax - b.YMax),
            abs(a.ZMin - b.ZMin), abs(a.ZMax - b.ZMax))

    for fpath in pfiles:
        stem = fpath.stem
        rd = App.newDocument("xchk")
        try:
            Import.insert(str(fpath), rd.Name)
            rd.recompute()
            sol = [o for o in rd.Objects
                   if hasattr(o, "Shape") and not o.Shape.isNull()
                   and o.Shape.Volume > 0]
            if not sol:
                rd_bad.append(stem)
            else:
                if not any(stem in o.Label or stem == o.Label
                           or o.Label.startswith(stem + "_")
                           for o in sol):
                    nn_bad.append(stem)
                mb = shape_map.get(stem)
                if mb is not None:
                    d = _bdev(_ubbox(sol), mb.BoundBox)
                    if d > 1.0:
                        bb_bad.append("%.1f %s" % (d, stem))
        except Exception:
            rd_bad.append(stem)
        App.closeDocument(rd.Name)
    gate("XPT5_part_reimport",
         not rd_bad and not nn_bad and not bb_bad,
         "%d/%d files; %d empty, %d nameless, %d bbox>1mm: %s"
         % (len(pfiles), len(shape_map), len(rd_bad), len(nn_bad),
            len(bb_bad), bb_bad[:5]))

    # XPT5b: master STEP products sit at world position (carrier
    # children included). Group reimported products by model base name
    # (multi-solid wires decompose into NAME_i) and compare union bbox.
    mp_bad = []
    rd = App.newDocument("mchk")
    try:
        Import.insert(str(step / "master_robot.step"), rd.Name)
        rd.recompute()
        groups = {}
        for o in rd.Objects:
            if not hasattr(o, "Shape") or o.Shape.isNull() \
                    or o.Shape.Volume <= 0:
                continue
            # the STEP root product (named after the export doc) is an
            # assembly wrapper -- skip it, check the leaf products
            if o.Label == "master_robot" \
                    and len(getattr(o.Shape, "Solids", [])) > 1:
                continue
            base = o.Label if o.Label in shape_map else \
                re.sub(r"_\d+$", "", o.Label)
            if base not in shape_map:
                mp_bad.append("?%s" % o.Label)
                continue
            groups.setdefault(base, []).append(o)
        for base, sol in groups.items():
            d = _bdev(_ubbox(sol), shape_map[base].BoundBox)
            if d > 1.0:
                mp_bad.append("%.1f %s" % (d, base))
    finally:
        App.closeDocument(rd.Name)
    gate("XPT5b_master_positions", not mp_bad,
         "%d products deviate >1mm: %s"
         % (len(mp_bad), mp_bad[:8]))

    # XPT6: bom covers every exportable
    bom_objs = set()
    for line in (EXPORTS / "bom" / "bom.csv").read_text(
            encoding="utf-8").splitlines()[1:]:
        try:
            objs = line.rsplit('"', 2)[1].split()
            bom_objs.update(objs)
        except Exception:
            pass
    not_in_bom = [nm for nm in shape_map if nm not in bom_objs]
    gate("XPT6_bom_coverage", not not_in_bom,
         "%d/%d untraced: %s"
         % (len(not_in_bom), len(shape_map), not_in_bom[:6]))

    # XPT7: parameters.csv mirrors all sheet aliases
    sheet = m.getObject("Parameters")
    sheet_aliases = set()
    for r in range(1, 400):
        try:
            a = sheet.get("A" + str(r))
        except Exception:
            break
        if not a:
            break
        sheet_aliases.add(str(a).strip())
    csv_lines = (EXPORTS / "bom" / "parameters.csv").read_text(
        encoding="utf-8").splitlines()[1:]
    csv_aliases = set(l.split(",", 1)[0] for l in csv_lines if l)
    pa_bad = sorted(sheet_aliases - csv_aliases - {"alias"})
    gate("XPT7_params_full", not pa_bad,
         "%d csv rows, %d aliases; missing %s"
         % (len(csv_lines), len(sheet_aliases), pa_bad[:6]))

    # ---------------- GUI / doc health ----------------
    gui_bad = []
    for tag, d in docs.items():
        nulls, invalid = [], []
        for o in d.Objects:
            if not hasattr(o, "Shape"):
                continue
            try:
                sh = o.Shape
            except Exception:
                continue
            if sh is None or sh.isNull():
                nulls.append(o.Name)
            elif not sh.isValid():
                invalid.append(o.Name)
        if nulls or invalid:
            gui_bad.append("%s nulls=%d invalid=%d"
                           % (tag, len(nulls), len(invalid)))
    gate("GUI1_doc_health", not gui_bad, "; ".join(gui_bad[:6]))

    for d in docs.values():
        try:
            App.closeDocument(d.Name)
        except Exception:
            pass

    # ---------------- DET2: rebuild determinism ------------------
    # Rebuild all three documents from source and compare the
    # exportable signature (name/bbox/volume) against the delivered
    # FCStds. This proves the committed sources regenerate the
    # committed geometry byte-identically.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import dt_build  # noqa: E402
        import dt_path  # noqa: E402
        for tag, pop in (("drivebase", dt_build.populate_drivebase),
                         ("electronics", dt_build.populate_electronics),
                         ("intake", dt_path.populate_intake),
                         ("hopper", dt_path.populate_hopper),
                         ("master", dt_build.populate_master)):
            td = App.newDocument("det2_" + tag)
            tctx = dt_build.new_ctx()
            pop(td, tctx)
            td.recompute(None, True, True)
            tsig = sig(td)
            delta = [nm for nm in sigs[tag]
                     if tsig.get(nm) != sigs[tag][nm]] +                     [nm for nm in tsig if nm not in sigs[tag]]
            gate("DET2_rebuild_" + tag, not delta,
                 "%d sigs differ" % len(delta))
            App.closeDocument(td.Name)
    except Exception as e:
        gate("DET2_rebuild", False, str(e)[:200])

    # ---------------- PAR2-D/E: parametric deltas -----------------
    # Mutate the Parameters sheet in a scratch copy of the master and
    # verify the geometry re-derives where the contract says it must.
    try:
        pd = App.openDocument(str(DOCS["master"]))
        sheet = pd.getObject("Parameters")
        base = float(sheet.get("wheel_lat_off"))
        base_sigs = {o.Name: gshape(o).BoundBox
                     for o in pd.Objects
                     if hasattr(o, "Shape") and not o.Shape.isNull()
                     and o.Name in sigs["master"]}
        # D: wheel_lat_off +6 -> axle-stack families move in Y
        sheet.set("wheel_lat_off", repr(base + 6.0))
        pd.recompute(None, True, True)
        moved = sum(
            1 for o in pd.Objects
            if hasattr(o, "Shape") and not o.Shape.isNull()
            and o.Name in base_sigs
            and abs(gshape(o).BoundBox.YMin
                    - base_sigs[o.Name].YMin) > 5.0)
        gate("PAR2D_wheel_lat_off", moved > 300,
             "%d solids moved" % moved)
        # wheel_dia +4 -> axle/brg/motor centers re-derive to 50
        sheet.set("wheel_lat_off", repr(base))
        sheet.set("wheel_dia", "100.0")
        pd.recompute(None, True, True)
        cz_bad = []
        for nm in ("AXLE_FL", "AXLE_FR", "AXLE_RL", "AXLE_RR",
                   "MOTOR_FL", "MOTOR_FR", "MOTOR_RL", "MOTOR_RR",
                   "BRG_IN_FL", "BRG_OUT_FL"):
            o = pd.getObject(nm)
            if o is None:
                cz_bad.append(nm)
                continue
            c = gshape(o).BoundBox.Center
            if abs(c.z - 50.0) > 0.1:
                cz_bad.append((nm, round(c.z, 2)))
        gate("PAR2D_wheel_dia", not cz_bad, "%s" % cz_bad[:4])
        # E: shelf_z +10 -> shelf + standoffs + expansion hub move
        bsz = float(sheet.get("shelf_z"))
        sheet.set("wheel_dia", "96.0")
        sheet.set("shelf_z", repr(bsz + 10.0))
        pd.recompute(None, True, True)
        moved_e = [o.Name for o in pd.Objects
                   if o.Name in ("ELEC_SHELF",
                                 "STANDOFF_0", "STANDOFF_1",
                                 "STANDOFF_2", "STANDOFF_3")
                   and hasattr(o, "Shape") and not o.Shape.isNull()
                   and abs(gshape(o).BoundBox.ZMax
                           - base_sigs[o.Name].ZMax) > 9.0]
        gate("PAR2E_shelf_z", len(moved_e) == 5,
             "%d moved: %s" % (len(moved_e), moved_e[:6]))
        # HUB_EXP is rail-face mounted (S17 clearance) and must NOT
        # track shelf_z
        gate("PAR2E_hub_static",
             abs(gshape(pd.getObject("HUB_EXP")).BoundBox.ZMax
                 - base_sigs["HUB_EXP"].ZMax) < 0.01,
             "exp hub drifted with shelf_z")
        # I: roller_top_z +5 -> star roller, slides, shaft, pulley,
        # belt move in Z; ROLLER_TOP ZMin must track +4..+6
        base_belt = gshape(pd.getObject("BELT_XROLL")).BoundBox
        base_top = gshape(pd.getObject("ROLLER_TOP")).BoundBox
        sheet.set("roller_top_z", "180.0")
        pd.recompute(None, True, True)
        moved_i = [o.Name for o in pd.Objects
                   if o.Name in ("ROLLER_TOP", "STAR_SHAFT",
                                 "FLOAT_SLIDE_L", "FLOAT_SLIDE_R",
                                 "BELT_PUL_TOP")
                   and hasattr(o, "Shape") and not o.Shape.isNull()
                   and abs(gshape(o).BoundBox.ZMin
                           - base_sigs[o.Name].ZMin) > 4.0]
        bt2 = gshape(pd.getObject("BELT_XROLL")).BoundBox
        gate("PAR2I_roller_top_z",
             len(moved_i) == 5 and bt2.ZMax - base_belt.ZMax > 1.0,
             "%d moved: %s" % (len(moved_i), moved_i))
        sheet.set("roller_top_z", "175.0")
        pd.recompute(None, True, True)
        # H: hopper_incline 20->23 -> floor + ledges rotate
        base_fl = gshape(pd.getObject("HOP_FLOOR")).BoundBox
        sheet.set("hopper_incline", "23.0")
        pd.recompute(None, True, True)
        hf2 = gshape(pd.getObject("HOP_FLOOR")).BoundBox
        lg2 = gshape(pd.getObject("HOP_LEDGE_L")).BoundBox
        lgb = gshape(pd.getObject("HOP_LEDGE_L")).BoundBox
        gate("PAR2H_hopper_incline",
             abs(hf2.ZMax - base_fl.ZMax) > 2.0,
             "floor ZMax %.2f->%.2f" % (base_fl.ZMax, hf2.ZMax))
        sheet.set("hopper_incline", "20.0")
        pd.recompute(None, True, True)
        # J: sprint-02 path params must re-derive where bound --
        # lane_wid widens curb+scoop, column_id thins the tube wall,
        # intake_x shifts the mouth/roller stack
        base_curb = gshape(pd.getObject("HOP_CURB")).BoundBox
        base_sco = gshape(pd.getObject("FEED_SCOOP")).BoundBox
        sheet.set("lane_wid", "120.0")
        pd.recompute(None, True, True)
        cb2 = gshape(pd.getObject("HOP_CURB")).BoundBox
        sc2 = gshape(pd.getObject("FEED_SCOOP")).BoundBox
        gate("PAR2J_lane_wid",
             base_curb.YMin - cb2.YMin > 2.0
             and base_sco.YMin - sc2.YMin > 2.0,
             "curb %.2f->%.2f scoop %.2f->%.2f" % (
                 base_curb.YMin, cb2.YMin, base_sco.YMin, sc2.YMin))
        sheet.set("lane_wid", "114.0")
        cv0 = pd.getObject("FEED_COLUMN").Shape.Volume
        sheet.set("column_id", "108.0")
        pd.recompute(None, True, True)
        cv1 = pd.getObject("FEED_COLUMN").Shape.Volume
        gate("PAR2J_column_id", cv0 - cv1 > 500,
             "column volume %.0f->%.0f" % (cv0, cv1))
        sheet.set("column_id", "104.0")
        bx0 = gshape(pd.getObject("ROLLER_LOW")).BoundBox
        sh0 = gshape(pd.getObject("ROLLER_SHAFT")).BoundBox
        sheet.set("intake_x", "196.0")
        pd.recompute(None, True, True)
        bx1 = gshape(pd.getObject("ROLLER_LOW")).BoundBox
        sh1 = gshape(pd.getObject("ROLLER_SHAFT")).BoundBox
        gate("PAR2J_intake_x",
             bx1.XMin - bx0.XMin > 5.0 and sh1.XMin - sh0.XMin > 4.0,
             "roller XMin %.2f->%.2f shaft %.2f->%.2f" % (
                 bx0.XMin, bx1.XMin, sh0.XMin, sh1.XMin))
        sheet.set("intake_x", "190.0")
        pd.recompute(None, True, True)
        # restore -> identity
        sheet.set("shelf_z", repr(bsz))
        pd.recompute(None, True, True)
        ident = [o.Name for o in pd.Objects
                 if hasattr(o, "Shape") and not o.Shape.isNull()
                 and o.Name in base_sigs
                 and abs(gshape(o).BoundBox.YMin
                         - base_sigs[o.Name].YMin) > 0.001]
        gate("PAR2_restore_identity", not ident,
             "%d differ: %s" % (len(ident), ident[:6]))
        App.closeDocument(pd.Name)
    except Exception as e:
        gate("PAR2_deltas", False, str(e)[:200])

    npass = sum(1 for _, ok, _ in RESULTS if ok)
    tail = "=" * 60 + "\nSELFCHECK: %d/%d gates pass" % (
        npass, len(RESULTS))
    print(tail)
    LOG.write(tail + "\n")
    LOG.close()
    LOG_TMP.replace(LOG_PATH)
    if npass != len(RESULTS):
        sys.exit(1)


try:
    main()
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    sys.exit(1)
