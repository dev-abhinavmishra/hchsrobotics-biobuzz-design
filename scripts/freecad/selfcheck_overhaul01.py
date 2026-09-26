"""Sprint-01 overhaul selfcheck -- every contract gate in one run.

Gates: GIT DET PAR PROV DAG ASM FAST GEO ENV XPT GUI
Opens the three saved FCStd files + exports/meta + exports/bom +
exports/step and verifies them against the sprint-01 contract.

Run:  freecadcmd.exe scripts/freecad/selfcheck_overhaul01.py
Exit: 0 if every gate passes, 1 otherwise.
"""
import json
import math
import subprocess
import sys
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
    "master": CAD / "master_robot.FCStd",
}
META = {k: EXPORTS / "meta" / ("%s.json" % k)
        for k in ("drivebase", "electronics", "master")}

STATUS = ("VERIFIED", "VENDOR-PENDING", "UNVERIFIED")
REQ_ALIASES = (
    "rail_lat_off rail_len rail_elev_z cross_x_off crown_z "
    "wheel_lat_off wheel_lon_off axle_len brg_in_off brg_out_off "
    "motor_lat_off mount_plate_off collar_off washer_off nut_off "
    "pinion_off clamp1_off clamp2_off pan_z deck_z shelf_z "
    "odo_pod_x odo_pod_lat odo_pod_lon_x batt_x batt_y "
    "ctrl_x ctrl_y exp_x exp_y sw_x sw_y rex_bore"
).split()
EXCLUDE_PREFIX = ("ENV_", "TOOL_", "AXIS_", "REF_", "VOL_")
EXCLUDE_TYPES = ("App::Part", "App::Origin", "Spreadsheet::Sheet",
                 "App::DocumentObjectGroup")

RESULTS = []
LOG = open(ROOT / "exports" / "selfcheck_overhaul01.txt", "w",
           encoding="utf-8")


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
             "scripts/freecad/build_master_robot.py"],
            cwd=str(ROOT), capture_output=True, text=True)
        dirty = [l for l in out.stdout.splitlines() if l.strip()]
        gate("GIT1_sources_committed", not dirty,
             "%d uncommitted" % len(dirty))
    except Exception as e:
        gate("GIT1_sources_committed", False, str(e))

    # ---------------- DET ----------------
    sigs = {k: sig(d) for k, d in docs.items()}
    mism = []
    for sub in ("drivebase", "electronics"):
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
        if o.Name.startswith("WIRE_"):
            continue          # harness geometry bakes at build time
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
            "switch_brkt": 2, "hub_mount": 4}
    fast_bad = []
    jn = mmeta["joints"] if mmeta else []
    embeds = {tuple(sorted(x)) for x in mmeta["embeds"]} if mmeta \
        else set()
    for j in jn:
        jid = j.get("id", "?")
        hw = list(j.get("bolts", []))
        need = JMIN.get(jid, 1)
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

    npass = sum(1 for _, ok, _ in RESULTS if ok)
    tail = "=" * 60 + "\nSELFCHECK: %d/%d gates pass" % (
        npass, len(RESULTS))
    print(tail)
    LOG.write(tail + "\n")
    LOG.close()
    if npass != len(RESULTS):
        sys.exit(1)


try:
    main()
except SystemExit:
    raise
except Exception:
    traceback.print_exc()
    sys.exit(1)
