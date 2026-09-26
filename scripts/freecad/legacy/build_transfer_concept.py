"""Build cad/transfer/transfer_concept_v01.FCStd -- BIOBUZZ transfer concept.

Sprint-02 rebuild: component-fidelity transfer channel via partkit.py --
sheet floor + bored/chamfered walls, L-bracket saddles to the pan stub,
a bored diverter paddle hinged on a real shaft through wall bushings,
a diverter servo on the wall outer face with a horn on the axle end, and
route markers with mount feet. Interior clears the ~91 mm Nectar ball
(VERIFIED, Competition Manual sec 9.8) -- see VOL_CHANNEL_CLEAR and
VOL_BALL_PATH.

Run:  freecadcmd.exe scripts/freecad/build_transfer_concept.py
Paths resolve relative to this file (project_root/scripts/freecad/).
"""

import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401  registers Part::Box / Part::Cylinder
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
import partkit as pk  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = ROOT / "cad" / "transfer"
ARCHIVE_DIR = ROOT / "cad" / "archive"
TARGET = CAD_DIR / "transfer_concept_v01.FCStd"
DOC_NAME = "transfer_concept_v01"

# (alias, value, unit, status, source)
PARAMS = [
    ("channel_len", 340.0, "mm", "UNVERIFIED", "assumed channel length"),
    ("channel_w", 110.0, "mm", "UNVERIFIED", "clears 91mm ball + margin"),
    ("channel_h", 110.0, "mm", "UNVERIFIED", "clears 91mm ball + margin"),
    ("channel_x0", -160.0, "mm", "UNVERIFIED",
     "channel rear end (scoring side)"),
    ("channel_z", 10.0, "mm", "UNVERIFIED",
     "floor-level through-chassis lane"),
    ("diverter_axis_x", -150.0, "mm", "UNVERIFIED",
     "diverter hinge center X"),
    ("paddle_sweep_deg", 90.0, "deg", "UNVERIFIED",
     "diverter paddle swing arc to clear the lane"),
    ("div_h", 60.0, "mm", "UNVERIFIED", "diverter paddle height"),
    ("plate_thk", 8.0, "mm", "UNVERIFIED", "diverter paddle thickness"),
    ("route_len", 90.0, "mm", "UNVERIFIED", "route marker length"),
    ("route_thk", 10.0, "mm", "UNVERIFIED", "route marker thickness"),
    ("route_w", 20.0, "mm", "UNVERIFIED", "route marker width"),
    ("horn_l", 30.0, "mm", "UNVERIFIED", "diverter servo horn length"),
    ("horn_w", 10.0, "mm", "UNVERIFIED", "diverter servo horn width"),
    ("horn_h", 20.0, "mm", "UNVERIFIED", "diverter servo horn height"),
    # sprint-02 component hardware
    ("nectar_dia", 91.0, "mm", "VERIFIED",
     "Nectar ball ~91mm, competition manual sec 9.8"),
    ("daxle_dia", 6.0, "mm", "UNVERIFIED", "diverter hinge shaft dia"),
    ("chan_wall_t", 3.0, "mm", "UNVERIFIED", "channel wall sheet"),
    ("chan_floor_t", 3.0, "mm", "UNVERIFIED", "channel floor sheet"),
    ("bush_dia", 10.0, "mm", "UNVERIFIED", "diverter bushing OD"),
    ("bush_t", 4.0, "mm", "UNVERIFIED", "diverter bushing thickness"),
    ("bush_bore", 6.4, "mm", "UNVERIFIED",
     "bushing bore for the O6 hinge axle"),
    ("paddle_bore", 6.4, "mm", "UNVERIFIED", "paddle hinge bore"),
    ("servo_l", 40.5, "mm", "VENDOR-PENDING", "REV SRS-class servo body"),
    ("servo_w", 20.4, "mm", "VENDOR-PENDING", "REV SRS-class servo body"),
    ("servo_h", 36.0, "mm", "VENDOR-PENDING", "REV SRS-class servo body"),
    ("mbolt_d", 4.4, "mm", "UNVERIFIED", "M4 clearance bolt hole"),
    ("csupp_w", 10.0, "mm", "UNVERIFIED", "channel saddle width"),
    ("csupp_t", 2.5, "mm", "UNVERIFIED", "channel saddle foot thickness"),
    ("pan_thk", 3.0, "mm", "UNVERIFIED", "pan stub sheet"),
    ("wall_chamfer", 0.8, "mm", "UNVERIFIED", "sheet-edge chamfer"),
]

MANAGED = {
    "Parameters", "TransferAssembly",
    "PAN_STUB", "CHANNEL_FLOOR", "CHANNEL_WALL_L", "CHANNEL_WALL_R",
    "CHANNEL_SUPP_F", "CHANNEL_SUPP_B",
    "DIVERTER_PADDLE", "DIVERTER_AXLE",
    "DIVERTER_BUSH_L", "DIVERTER_BUSH_R",
    "DIVERTER_SERVO", "DIVERTER_HORN",
    "ZONE_INLET", "ZONE_OUTLET", "ROUTE_POLLEN", "ROUTE_NECTAR",
    "VOL_CHANNEL_CLEAR", "VOL_BALL_PATH",
}
MANAGED.update(("TOOL_CHANNEL_FLOOR_BLK",))
MANAGED.update("TOOL_CHANNEL_WALL_%s_%s" % (s, t)
               for s in "LR" for t in ("BLK", "CUT"))
MANAGED.update("TOOL_CHANNEL_WALL_L_BORE%02d" % i for i in range(3))
MANAGED.add("TOOL_CHANNEL_WALL_R_BORE00")
MANAGED.add("TOOL_DIVERTER_PADDLE_BORE00")
MANAGED.add("TOOL_DIVERTER_PADDLE_BLK")
for n in ("CHANNEL_SUPP_F", "CHANNEL_SUPP_B", "ROUTE_POLLEN",
          "ROUTE_NECTAR"):
    MANAGED.update("TOOL_%s_%s" % (n, t) for t in ("LEG", "FOOT", "L"))
    MANAGED.update("TOOL_%s_B%02d" % (n, i) for i in range(2))
for n in ("DIVERTER_BUSH_L", "DIVERTER_BUSH_R"):
    MANAGED.update("TOOL_%s_%s" % (n, t) for t in ("BLK", "BORE"))


def archive_if_foreign():
    """Preserve a pre-existing file that holds objects we did not create."""
    if not TARGET.exists():
        return
    foreign = True
    try:
        doc = App.openDocument(str(TARGET))
        managed = set(MANAGED)
        for o in doc.Objects:
            if o.TypeId == "App::Origin":
                managed.add(o.Name)
                managed.update(c.Name for c in getattr(o, "OriginFeatures", []))
        foreign = [o.Name for o in doc.Objects if o.Name not in managed]
        App.closeDocument(doc.Name)
    except Exception:
        pass
    if not foreign:
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = ARCHIVE_DIR / ("%s_%s.FCStd" % (TARGET.stem, stamp))
    n = 1
    while dst.exists():
        dst = ARCHIVE_DIR / ("%s_%s_%02d.FCStd" % (TARGET.stem, stamp, n))
        n += 1
    shutil.copy2(str(TARGET), str(dst))
    print("BUILD: archived prior content -> cad/archive/%s" % dst.name)


def populate(doc):
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.Label = "Parameters"
    for col, head in zip("ABCDE",
                         ("alias", "value", "unit", "status", "source")):
        sheet.set(col + "1", head)
    for i, (alias, val, unit, status, src) in enumerate(PARAMS):
        r = str(i + 2)
        sheet.set("A" + r, alias)
        sheet.set("B" + r, repr(val))
        sheet.set("C" + r, unit)
        sheet.set("D" + r, status)
        sheet.set("E" + r, src)
        sheet.setAlias("B" + r, alias)

    asm = doc.addObject("App::Part", "TransferAssembly")
    asm.Label = "TRANSFER_assembly_v02_component_fidelity"
    doc.recompute()
    solids = []

    # pan stub the channel saddles stand on
    solids.append(pk.box(
        doc, "PAN_STUB",
        "PAN_STUB_under_channel_UNVERIFIED",
        "UNVERIFIED - belly-pan reference under the channel",
        {"Length": "Parameters.channel_len + 15",
         "Width": "Parameters.channel_w + 40",
         "Height": "Parameters.pan_thk"},
        {"Placement.Base.x": "Parameters.channel_x0 - 15",
         "Placement.Base.y": "-(Parameters.channel_w + 40) / 2",
         "Placement.Base.z":
             "Parameters.channel_z - Parameters.pan_thk"}))

    # floor + walls (real sheet channel); L wall gets hinge + servo bores
    solids.append(pk.bored_plate(
        doc, "CHANNEL_FLOOR", "CHANNEL_FLOOR_3mm_sheet_UNVERIFIED",
        "UNVERIFIED - transfer channel floor sheet",
        {"Length": "Parameters.channel_len",
         "Width": "Parameters.channel_w",
         "Height": "Parameters.chan_floor_t"},
        {"Placement.Base.x": "Parameters.channel_x0",
         "Placement.Base.y": "-Parameters.channel_w / 2",
         "Placement.Base.z": "Parameters.channel_z"},
        bores=(), chamfer_l=pk.pval(sheet, "wall_chamfer"),
        chamfer_pred=pk.pred_axis((0, 0, 1))))
    axle_z = "Parameters.channel_z + Parameters.channel_h - 5"
    for name, sgn in (("CHANNEL_WALL_L", 1), ("CHANNEL_WALL_R", -1)):
        wy = ("Parameters.channel_w / 2 - Parameters.chan_wall_t"
              if sgn > 0 else "-Parameters.channel_w / 2")
        bores = [
            ("Parameters.bush_bore",
             {"Placement.Base.x": "Parameters.diverter_axis_x",
              "Placement.Base.y":
                  ("Parameters.channel_w / 2 - Parameters.chan_wall_t - 1"
                   if sgn > 0 else "-Parameters.channel_w / 2 - 1"),
              "Placement.Base.z": axle_z}, "Y",
             "Parameters.chan_wall_t + 2")]
        if sgn > 0:
            bores += [
                ("Parameters.mbolt_d",
                 {"Placement.Base.x": "Parameters.diverter_axis_x"
                                      " + Parameters.bush_dia / 2 + 9",
                  "Placement.Base.y": "Parameters.channel_w / 2"
                                      " - Parameters.chan_wall_t - 1",
                  "Placement.Base.z": "Parameters.channel_z"
                                      " + Parameters.channel_h"
                                      " - Parameters.servo_h + 6"}, "Y",
                 "Parameters.chan_wall_t + 2"),
                ("Parameters.mbolt_d",
                 {"Placement.Base.x": "Parameters.diverter_axis_x"
                                      " + Parameters.bush_dia / 2"
                                      " + Parameters.servo_l - 4",
                  "Placement.Base.y": "Parameters.channel_w / 2"
                                      " - Parameters.chan_wall_t - 1",
                  "Placement.Base.z": "Parameters.channel_z"
                                      " + Parameters.channel_h - 6"}, "Y",
                 "Parameters.chan_wall_t + 2")]
        solids.append(pk.bored_plate(
            doc, name, "%s_channel_wall_sheet_UNVERIFIED" % name,
            "UNVERIFIED - channel wall (hinge bore + chamfer)",
            {"Length": "Parameters.channel_len",
             "Width": "Parameters.chan_wall_t",
             "Height": "Parameters.channel_h"},
            {"Placement.Base.x": "Parameters.channel_x0",
             "Placement.Base.y": wy,
             "Placement.Base.z": "Parameters.channel_z"},
            bores=bores, chamfer_l=pk.pval(sheet, "wall_chamfer"),
            chamfer_pred=pk.pred_axis((1, 0, 0))))

    # saddle L-brackets under the floor onto the pan stub
    sadd_w = "Parameters.channel_w - 2 * Parameters.chan_wall_t - 4"
    for name, x0 in (("CHANNEL_SUPP_F",
                      "Parameters.channel_x0 + Parameters.channel_len"
                      " - Parameters.csupp_w - 15"),
                     ("CHANNEL_SUPP_B",
                      "Parameters.channel_x0 + Parameters.csupp_w")):
        bolts = [
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "(%s) + Parameters.csupp_w / 2 - 2"
                                  % x0,
              "Placement.Base.y": "-(%s) / 2 + 8" % sadd_w,
              "Placement.Base.z":
                  "Parameters.channel_z - Parameters.pan_thk - 1"}, "Z",
             "Parameters.csupp_t + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "(%s) + Parameters.csupp_w / 2 - 2"
                                  % x0,
              "Placement.Base.y": "(%s) / 2 - 8" % sadd_w,
              "Placement.Base.z":
                  "Parameters.channel_z - Parameters.pan_thk - 1"}, "Z",
             "Parameters.csupp_t + 2")]
        solids.append(pk.l_bracket(
            doc, name, "%s_saddle_L_bracket_UNVERIFIED" % name,
            "UNVERIFIED - channel saddle L-bracket to pan",
            {"Length": "Parameters.csupp_w", "Width": sadd_w,
             "Height": "Parameters.csupp_t + 2"},
            {"Placement.Base.x": x0,
             "Placement.Base.y": "-(%s) / 2" % sadd_w,
             "Placement.Base.z":
                 "Parameters.channel_z - Parameters.csupp_t - 2"},
            {"Length": "Parameters.csupp_w + 6", "Width": sadd_w,
             "Height": "Parameters.csupp_t"},
            {"Placement.Base.x": "(%s) - 3" % x0,
             "Placement.Base.y": "-(%s) / 2" % sadd_w,
             "Placement.Base.z":
                 "Parameters.channel_z - Parameters.csupp_t"
                 " - Parameters.pan_thk - 2"},
            bolts=bolts))

    # diverter: bored paddle on a hinge shaft through wall bushings
    solids.append(pk.bored_plate(
        doc, "DIVERTER_PADDLE",
        "DIVERTER_PADDLE_hinged_O6bore_UNVERIFIED",
        "UNVERIFIED - diverter paddle hinged on the axle",
        {"Length": "Parameters.plate_thk",
         "Width": "Parameters.channel_w - 2 * Parameters.chan_wall_t - 4",
         "Height": "Parameters.div_h"},
        {"Placement.Base.x": "Parameters.diverter_axis_x - 4",
         "Placement.Base.y":
             "-(Parameters.channel_w - 2 * Parameters.chan_wall_t - 4)"
             " / 2",
         "Placement.Base.z":
             "Parameters.channel_z + Parameters.channel_h"
             " - Parameters.div_h - 3"},
        bores=[("Parameters.paddle_bore",
                {"Placement.Base.x": "Parameters.diverter_axis_x",
                 "Placement.Base.y":
                     "-(Parameters.channel_w - 2 * Parameters.chan_wall_t"
                     " - 4) / 2 - 1",
                 "Placement.Base.z": axle_z}, "Y",
                "Parameters.channel_w")]))
    solids.append(pk.shaft(
        doc, "DIVERTER_AXLE",
        "DIVERTER_AXLE_O6_hinge_shaft_UNVERIFIED",
        "UNVERIFIED - diverter hinge shaft through wall bushings",
        "Parameters.daxle_dia",
        "Parameters.channel_w + 2 * Parameters.bush_t + 8",
        {"Placement.Base.x": "Parameters.diverter_axis_x",
         "Placement.Base.y":
             "-(Parameters.channel_w + 2 * Parameters.bush_t + 8) / 2",
         "Placement.Base.z": axle_z}, "Y"))
    for name, sgn in (("DIVERTER_BUSH_L", 1), ("DIVERTER_BUSH_R", -1)):
        by = ("Parameters.channel_w / 2" if sgn > 0 else
              "-Parameters.channel_w / 2 - Parameters.bush_t")
        solids.append(pk.bore_cyl(
            doc, name, "%s_wall_bushing_UNVERIFIED" % name,
            "UNVERIFIED - diverter wall bushing",
            "Parameters.bush_dia", "Parameters.bush_t",
            "Parameters.bush_bore",
            {"Placement.Base.x": "Parameters.diverter_axis_x",
             "Placement.Base.y": by,
             "Placement.Base.z": axle_z}, "Y"))
    solids.append(pk.box(
        doc, "DIVERTER_SERVO",
        "DIVERTER_SERVO_40x20x36_on_wall_VENDOR-PENDING",
        "VENDOR-PENDING - REV SRS-class diverter servo",
        {"Length": "Parameters.servo_l", "Width": "Parameters.servo_w",
         "Height": "Parameters.servo_h"},
        {"Placement.Base.x":
             "Parameters.diverter_axis_x + Parameters.bush_dia / 2 + 1",
         "Placement.Base.y": "Parameters.channel_w / 2",
         "Placement.Base.z":
             "Parameters.channel_z + Parameters.channel_h"
             " - Parameters.servo_h"}))
    solids.append(pk.box(
        doc, "DIVERTER_HORN",
        "DIVERTER_HORN_on_axle_end_UNVERIFIED",
        "UNVERIFIED - diverter horn on the hinge axle end",
        {"Length": "Parameters.horn_l", "Width": "Parameters.horn_w",
         "Height": "Parameters.horn_h"},
        {"Placement.Base.x":
             "Parameters.diverter_axis_x - Parameters.horn_l + 5",
         "Placement.Base.y": "Parameters.channel_w / 2"
                             " + Parameters.bush_t + 1",
         "Placement.Base.z":
             "Parameters.channel_z + Parameters.channel_h - 5"
             " - Parameters.horn_h"}))

    # zone markers: INLET band on the wall tops; OUTLET band behind the
    # channel rear end on the pan stub (clear of the hinge axle)
    solids.append(pk.l_bracket(
        doc, "ZONE_INLET", "ZONE_INLET_marker_with_feet_UNVERIFIED",
        "UNVERIFIED - inlet zone marker band, foot on wall top",
        {"Length": "Parameters.route_thk",
         "Width": "Parameters.channel_w + 2 * Parameters.chan_wall_t",
         "Height": "Parameters.route_w"},
        {"Placement.Base.x":
             "Parameters.channel_x0 + Parameters.channel_len"
             " - Parameters.route_thk",
         "Placement.Base.y":
             "-(Parameters.channel_w + 2 * Parameters.chan_wall_t) / 2",
         "Placement.Base.z":
             "Parameters.channel_z + Parameters.channel_h"},
        {"Length": "Parameters.route_thk",
         "Width": "Parameters.chan_wall_t + 8",
         "Height": "4"},
        {"Placement.Base.x":
             "Parameters.channel_x0 + Parameters.channel_len"
             " - Parameters.route_thk",
         "Placement.Base.y": "-Parameters.channel_w / 2 - 4",
         "Placement.Base.z":
             "Parameters.channel_z + Parameters.channel_h - 4"}))
    solids.append(pk.l_bracket(
        doc, "ZONE_OUTLET", "ZONE_OUTLET_marker_behind_lane_UNVERIFIED",
        "UNVERIFIED - outlet zone marker band behind channel end",
        {"Length": "Parameters.route_thk",
         "Width": "Parameters.channel_w + 2 * Parameters.chan_wall_t",
         "Height": "Parameters.channel_h + 10"},
        {"Placement.Base.x": "Parameters.channel_x0 - 15",
         "Placement.Base.y":
             "-(Parameters.channel_w + 2 * Parameters.chan_wall_t) / 2",
         "Placement.Base.z": "Parameters.channel_z"},
        {"Length": "Parameters.route_thk",
         "Width": "Parameters.chan_wall_t + 8",
         "Height": "4"},
        {"Placement.Base.x": "Parameters.channel_x0 - 15",
         "Placement.Base.y": "-Parameters.channel_w / 2 - 4",
         "Placement.Base.z": "Parameters.channel_z"}))

    # route markers (Pollen up toward shooter / Nectar toward hopper),
    # feet on the wall tops
    for name, lbl, sgn in (
            ("ROUTE_POLLEN", "ROUTE_POLLEN_to_shooter_up_UNVERIFIED", 1),
            ("ROUTE_NECTAR", "ROUTE_NECTAR_to_lifter_UNVERIFIED", -1)):
        solids.append(pk.l_bracket(
            doc, name, lbl,
            "UNVERIFIED - route marker with mount foot on wall top",
            {"Length": "Parameters.route_thk",
             "Width": "Parameters.route_thk",
             "Height": "Parameters.route_len"},
            {"Placement.Base.x":
                 "Parameters.diverter_axis_x - Parameters.route_thk - 8",
             "Placement.Base.y":
                 ("Parameters.channel_w / 2 - Parameters.route_thk"
                  if sgn > 0 else "-Parameters.channel_w / 2"),
             "Placement.Base.z":
                 "Parameters.channel_z + Parameters.channel_h"},
            {"Length": "Parameters.route_thk",
             "Width": "Parameters.route_thk",
             "Height": "4"},
            {"Placement.Base.x":
                 "Parameters.diverter_axis_x - Parameters.route_thk - 8",
             "Placement.Base.y":
                 ("Parameters.channel_w / 2 - Parameters.route_thk"
                  if sgn > 0 else "-Parameters.channel_w / 2"),
             "Placement.Base.z":
                 "Parameters.channel_z + Parameters.channel_h - 4"}))

    # probe volumes (excluded VOL_ class)
    solids.append(pk.box(
        doc, "VOL_CHANNEL_CLEAR",
        "VOL_CHANNEL_CLEAR_interior_UNVERIFIED",
        "UNVERIFIED - channel interior clear-section probe",
        {"Length": "Parameters.channel_len",
         "Width": "Parameters.channel_w - 2 * Parameters.chan_wall_t",
         "Height": "Parameters.channel_h - Parameters.chan_floor_t"},
        {"Placement.Base.x": "Parameters.channel_x0",
         "Placement.Base.y":
             "-(Parameters.channel_w - 2 * Parameters.chan_wall_t) / 2",
         "Placement.Base.z": "Parameters.channel_z"
                             " + Parameters.chan_floor_t"}))
    solids.append(pk.cyl(
        doc, "VOL_BALL_PATH",
        "VOL_BALL_PATH_O91_nectar_lane_VERIFIED",
        "VERIFIED - O91 Nectar ball path probe (sec 9.8)",
        {"Radius": "Parameters.nectar_dia / 2",
         "Height": "Parameters.channel_len"
                   " - (Parameters.diverter_axis_x"
                   "    + Parameters.plate_thk / 2"
                   "    - Parameters.channel_x0) - 0.2"},
        {"Placement.Base.x":
             "Parameters.diverter_axis_x + Parameters.plate_thk / 2",
         "Placement.Base.y": "0",
         "Placement.Base.z": "Parameters.channel_z"
                             " + Parameters.channel_h / 2"},
        pk.axis_rot("X")))

    pk.group_add(asm, *solids)
    doc.recompute()

    bad = [o.Name for o in doc.Objects
           if hasattr(o, "Shape") and o.Shape.Solids
           and not o.Shape.isValid()]
    solids_all = [o for o in doc.Objects
                  if hasattr(o, "Shape") and o.Shape.Solids]
    print("BUILD: objects=%d solids=%d invalid=%s"
          % (len(doc.Objects), len(solids_all), bad or "none"))
    for o in solids_all:
        if o.Name.startswith(pk.TOOL_PREFIX):
            continue
        bb = o.Shape.BoundBox
        print("BUILD: %-22s | %-52s | bbox (%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f)"
              % (o.Name, o.Label, bb.XMin, bb.YMin, bb.ZMin,
                 bb.XMax, bb.YMax, bb.ZMax))
    if bad:
        raise RuntimeError("invalid solids: %s" % bad)


def main():
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    archive_if_foreign()
    doc = App.newDocument(DOC_NAME)
    populate(doc)
    doc.saveAs(str(TARGET))
    for bak in TARGET.parent.glob(TARGET.stem + ".*.FCBak"):
        bak.unlink()  # FreeCAD backup sidecar; keep cad/ clean on re-runs
    print("BUILD: saved %s (%d bytes)" % (TARGET, TARGET.stat().st_size))
    print("BUILD: DONE")


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
