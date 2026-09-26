"""Build cad/drivebase/drivebase_concept_v01.FCStd -- BIOBUZZ drivebase concept.

Rehaul sprint-01: the drivebase uses the same partkit vocabulary as the
master -- U-channel frame ring with hole rows + shaft notches, filleted
belly pan, full mecanum wheel assemblies (hub + bored/chamfered face
plates + slanted rollers on pins), 5203-style motors with face plates,
flange bearing blocks, and REX live shafts. All load-bearing dimensions
are expression-bound to the Parameters sheet.
Run:  freecadcmd.exe scripts/freecad/build_drivebase_concept.py
All paths resolve relative to this file (project_root/scripts/freecad/).
"""

import math
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
CAD_DIR = ROOT / "cad" / "drivebase"
ARCHIVE_DIR = ROOT / "cad" / "archive"
TARGET = CAD_DIR / "drivebase_concept_v01.FCStd"
DOC_NAME = "drivebase_concept_v01"

WHEELS = (("FL", 1, 1, 1), ("FR", 1, -1, -1), ("RL", -1, 1, -1),
          ("RR", -1, -1, 1))

# (alias, value, unit, status, source) - shared values with master_robot
PARAMS = [
    ("chassis_length", 420.0, "mm", "UNVERIFIED", "assumed"),
    ("chassis_width", 420.0, "mm", "UNVERIFIED", "assumed"),
    ("wheel_dia", 96.0, "mm", "VENDOR-PENDING",
     "goBILDA 96mm mecanum set 3213-3606-0002, schematic 3606-0000-0096"),
    ("wheel_width", 32.0, "mm", "VENDOR-PENDING",
     "goBILDA schematic 3606-0000-0096 overall width (was 25 placeholder)"),
    ("wheel_x_offset", 140.0, "mm", "UNVERIFIED",
     "assumed; keeps motor bodies clear of the end rails"),
    ("wheel_y_offset", 180.0, "mm", "UNVERIFIED",
     "assumed; roller OD leaves 0.6mm margin to R102 cube"),
    ("motor_dia", 36.0, "mm", "VENDOR-PENDING",
     "goBILDA Yellow Jacket 5203-series ~36mm gearbox dia, series page"),
    ("motor_len", 60.0, "mm", "UNVERIFIED", "motor body length inward"),
    ("rail_size", 48.0, "mm", "VENDOR-PENDING",
     "goBILDA 1120 U-channel ~48mm outer, D12"),
    ("rail_wall", 2.5, "mm", "UNVERIFIED",
     "assumed ~0.09in channel sheet wall; measure on hardware"),
    ("notch_w", 16.0, "mm", "UNVERIFIED", "shaft clearance notch width"),
    ("notch_d", 14.0, "mm", "UNVERIFIED", "shaft clearance notch depth"),
    ("hole_dia", 4.0, "mm", "VENDOR-PENDING",
     "goBILDA hole-grid ~O4 holes, catalog typical"),
    ("hole_pitch", 48.0, "mm", "UNVERIFIED",
     "subset of the 8mm goBILDA grid; visual pitch assumed"),
    ("pan_thk", 3.0, "mm", "UNVERIFIED", "belly pan sheet"),
    ("pan_fillet", 8.0, "mm", "UNVERIFIED", "belly pan corner fillet"),
    ("plate_fillet", 4.0, "mm", "UNVERIFIED", "small-plate edge fillet"),
    # mecanum wheel assembly (shared values with master)
    ("roller_count", 10.0, "count", "VENDOR-PENDING",
     "counted on goBILDA schematic 3606-0000-0096; STEP file authoritative"),
    ("mec_roll_dia", 14.0, "mm", "VENDOR-PENDING",
     "goBILDA schematic 3606-0000-0096 O14 roller"),
    ("mec_roll_rad", 41.0, "mm", "VENDOR-PENDING",
     "derived (wheel_dia - mec_roll_dia) / 2"),
    ("mec_roll_len", 20.0, "mm", "UNVERIFIED",
     "assumed roller length; keeps flat-cap ends inside O96 envelope"),
    ("mec_roll_pitch", 36.0, "deg", "VENDOR-PENDING",
     "derived 360 / roller_count"),
    ("mec_roll_slant", 45.0, "deg", "UNVERIFIED", "mecanum roller slant"),
    ("mec_pin_dia", 5.0, "mm", "UNVERIFIED",
     "roller axle pin dia (pins seat into face plates)"),
    ("mec_pin_len", 34.0, "mm", "UNVERIFIED",
     "roller pin overall length; tips embed ~1mm into face plates"),
    ("wplate_dia", 92.0, "mm", "UNVERIFIED",
     "wheel side plate dia (inset inside O96 envelope)"),
    ("wplate_thk", 4.0, "mm", "UNVERIFIED", "wheel side plate thickness"),
    ("wplate_gap", 1.0, "mm", "UNVERIFIED",
     "wheel plate standoff inside the O96 envelope face"),
    ("hub_dia", 26.0, "mm", "UNVERIFIED", "wheel hub OD"),
    ("hub_w", 20.0, "mm", "UNVERIFIED", "wheel hub width"),
    ("bore_dia", 8.4, "mm", "VENDOR-PENDING",
     "8mm REX clearance bore (goBILDA REX bore typical)"),
    ("plate_bore", 9.0, "mm", "UNVERIFIED", "wheel plate shaft clearance"),
    ("shaft_dia", 8.0, "mm", "VENDOR-PENDING",
     "goBILDA 8mm REX shaft standard, series page"),
    ("shaft_len", 76.0, "mm", "UNVERIFIED",
     "live drive shaft: motor face -> web notch -> bearing -> hub"),
    ("bear_w", 26.0, "mm", "UNVERIFIED", "bearing block face width"),
    ("bear_h", 26.0, "mm", "UNVERIFIED", "bearing block face height"),
    ("bear_t", 6.0, "mm", "UNVERIFIED", "bearing block thickness"),
    ("bear_bore", 8.4, "mm", "VENDOR-PENDING",
     "bearing bore, 8mm REX clearance"),
    ("bear_bolt_d", 4.0, "mm", "UNVERIFIED", "bearing block bolt hole dia"),
    ("bear_bolt_off", 9.0, "mm", "UNVERIFIED", "bearing bolt hole offset"),
    ("mface_w", 30.0, "mm", "UNVERIFIED", "motor face plate width"),
    ("mface_h", 30.0, "mm", "UNVERIFIED", "motor face plate height"),
    ("mface_t", 2.5, "mm", "UNVERIFIED", "motor face plate thickness"),
]


def expected_names():
    names = {"Parameters", "DrivebaseAssembly", "Tools", "BELLY_PAN",
             "RAIL_L", "RAIL_R", "RAIL_F", "RAIL_B"}
    names.update("WHEEL_ASSY_%s" % w for w, *_ in WHEELS)
    names.update("ENV_WHEEL_%s" % w for w, *_ in WHEELS)
    names.update("WHEEL_HUB_%s" % w for w, *_ in WHEELS)
    names.update("WHEEL_PLATE_%s_%s" % (w, io)
                 for w, *_ in WHEELS for io in ("IN", "OUT"))
    names.update("MOTOR_%s" % w for w, *_ in WHEELS)
    names.update("MOUNT_MOTOR_%s" % w for w, *_ in WHEELS)
    names.update("BEARING_%s" % w for w, *_ in WHEELS)
    names.update("SHAFT_%s" % w for w, *_ in WHEELS)
    names.update("ROLLER_%s_%02d" % (w, k)
                 for w, *_ in WHEELS for k in range(10))
    names.update("ROLLER_%s_%02d_B" % (w, k)
                 for w, *_ in WHEELS for k in range(10))
    names.add("TOOL_BELLY_PAN_BLK")
    names.update("TOOL_RAIL_%s_OUT" % s for s in "LRFB")
    names.update("TOOL_RAIL_%s_INNER" % s for s in "LRFB")
    names.update("TOOL_RAIL_%s_TOOLS" % s for s in "LRFB")
    names.update("TOOL_RAIL_%s_FH%02d" % (s, i)
                 for s in "LR" for i in range(8))
    names.update("TOOL_RAIL_%s_WH%02d" % (s, i)
                 for s in "LR" for i in range(7))
    names.update("TOOL_RAIL_%s_FH%02d" % (s, i)
                 for s in "FB" for i in range(5))
    names.update("TOOL_RAIL_%s_WH%02d" % (s, i)
                 for s in "FB" for i in range(4))
    names.update("TOOL_RAIL_%s_NOTCH%d" % (s, j)
                 for s in "LR" for j in range(2))
    for w, *_ in WHEELS:
        names.add("TOOL_WHEEL_HUB_%s_BLK" % w)
        names.add("TOOL_WHEEL_HUB_%s_BORE" % w)
        for io in ("IN", "OUT"):
            names.add("TOOL_WHEEL_PLATE_%s_%s_BLK" % (w, io))
            names.add("TOOL_WHEEL_PLATE_%s_%s_BORE" % (w, io))
            names.add("TOOL_WHEEL_PLATE_%s_%s_BRD" % (w, io))
        names.add("TOOL_MOUNT_MOTOR_%s_BLK" % w)
        names.add("TOOL_MOUNT_MOTOR_%s_FIL" % w)
        names.add("TOOL_MOUNT_MOTOR_%s_BORE" % w)
        names.update("TOOL_MOUNT_MOTOR_%s_B%02d" % (w, i)
                     for i in range(4))
        names.add("TOOL_MOUNT_MOTOR_%s_TOOLS" % w)
        names.add("TOOL_BEARING_%s_BLK" % w)
        names.add("TOOL_BEARING_%s_FIL" % w)
        names.add("TOOL_BEARING_%s_BORE" % w)
        names.update("TOOL_BEARING_%s_B%02d" % (w, i) for i in range(4))
        names.add("TOOL_BEARING_%s_TOOLS" % w)
        for k in range(10):
            names.add("TOOL_ROLLER_%s_%02d_BT" % (w, k))
            names.add("TOOL_ROLLER_%s_%02d_PT" % (w, k))
            names.add("TOOL_ROLLER_%s_%02d_B_TOOLS" % (w, k))
    return names


def archive_if_foreign():
    """Preserve a pre-existing file that holds objects we did not create."""
    if not TARGET.exists():
        return
    foreign = True
    try:
        doc = App.openDocument(str(TARGET))
        managed = set(expected_names())
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
    for col, head in zip("ABCDE", ("alias", "value", "unit", "status",
                                   "source")):
        sheet.set(col + "1", head)
    for i, (alias, val, unit, status, src) in enumerate(PARAMS):
        r = str(i + 2)
        sheet.set("A" + r, alias)
        sheet.set("B" + r, repr(val))
        sheet.set("C" + r, unit)
        sheet.set("D" + r, status)
        sheet.set("E" + r, src)
        sheet.setAlias("B" + r, alias)

    asm = doc.addObject("App::Part", "DrivebaseAssembly")
    asm.Label = "DRIVEBASE_assembly_v01_partkit"
    tools_grp = doc.addObject("App::Part", "Tools")
    tools_grp.Label = "GRP_construction_tools"
    doc.recompute()  # let the App::Part Origin children appear

    parts = []
    # U-channel frame ring (side rails along X, end rails along Y)
    sy_rail = ("Parameters.wheel_y_offset - Parameters.wheel_width / 2"
               " - Parameters.rail_size")
    flange_line = ("Parameters.wheel_y_offset - Parameters.wheel_width / 2"
                   " - Parameters.rail_size / 2")
    for name, sgn, face in (("RAIL_L", 1, "+Y"), ("RAIL_R", -1, "-Y")):
        y0 = (sy_rail if sgn > 0 else
              "-(%s) - Parameters.rail_size" % sy_rail)
        line = flange_line if sgn > 0 else "-(%s)" % flange_line
        r = pk.channel_u(
            doc, name,
            "%s_1120channel_48mm_open_side_rail_VENDOR-PENDING" % name,
            "VENDOR-PENDING - goBILDA 1120 ~48mm U-channel (D12)",
            ("-Parameters.chassis_length / 2", y0, "0"),
            "Parameters.chassis_length", "Parameters.rail_size",
            "Parameters.rail_wall", face, axis="X",
            flange_holes={"count": 8, "dia": "Parameters.hole_dia",
                          "pitch": "Parameters.hole_pitch", "start": "42",
                          "line": line},
            web_holes={"count": 7, "dia": "Parameters.hole_dia",
                       "pitch": "60", "start": "30",
                       "z": "Parameters.rail_size / 2"},
            notches=["Parameters.wheel_x_offset",
                     "-Parameters.wheel_x_offset"])
        parts.append(r)
    for name, sgn, face in (("RAIL_F", 1, "+X"), ("RAIL_B", -1, "-X")):
        x0 = ("Parameters.chassis_length / 2 - Parameters.rail_size"
              if sgn > 0 else "-Parameters.chassis_length / 2")
        line = ("Parameters.chassis_length / 2 - Parameters.rail_size / 2"
                if sgn > 0 else
                "-Parameters.chassis_length / 2 + Parameters.rail_size / 2")
        r = pk.channel_u(
            doc, name,
            "%s_1120channel_48mm_open_end_rail_VENDOR-PENDING" % name,
            "VENDOR-PENDING - goBILDA 1120 ~48mm U-channel (D12)",
            (x0, "-(%s)" % sy_rail, "0"),
            "2 * (%s)" % sy_rail, "Parameters.rail_size",
            "Parameters.rail_wall", face, axis="Y",
            flange_holes={"count": 5, "dia": "Parameters.hole_dia",
                          "pitch": "Parameters.hole_pitch", "start": "42",
                          "line": line},
            web_holes={"count": 4, "dia": "Parameters.hole_dia",
                       "pitch": "60", "start": "30",
                       "z": "Parameters.rail_size / 2"})
        parts.append(r)

    pan = pk.plate(
        doc, "BELLY_PAN", "BELLY_PAN_3mm_sheet_fillet_UNVERIFIED",
        "UNVERIFIED - belly pan inside frame ring",
        {"Length": "Parameters.chassis_length - 2 * Parameters.rail_size",
         "Width": "2 * (%s)" % sy_rail,
         "Height": "Parameters.pan_thk"},
        {"Placement.Base.x":
             "-(Parameters.chassis_length - 2 * Parameters.rail_size) / 2",
         "Placement.Base.y": "-(%s)" % sy_rail,
         "Placement.Base.z": "Parameters.rail_wall"},
        fillet_r=pk.pval(sheet, "pan_fillet"),
        edge_pred=pk.pred_axis((0, 0, 1)))
    parts.append(pan)

    # four full mecanum wheel assemblies + drive hardware
    pitch = pk.pval(sheet, "mec_roll_pitch")
    for wtag, sx, sy, sgn in WHEELS:
        carrier, solids = pk.mecanum_wheel(
            doc, wtag, sgn,
            "VENDOR-PENDING - goBILDA 96mm mecanum 3213-3606-0002"
            " (schematic 3606-0000-0096)",
            "goBILDA 3213-3606-0002 96mm mecanum wheel assembly",
            pitch, int(pk.pval(sheet, "roller_count")))
        pk.bind(carrier, {
            "Placement.Base.x":
                "Parameters.wheel_x_offset" if sx > 0
                else "-Parameters.wheel_x_offset",
            "Placement.Base.y":
                "Parameters.wheel_y_offset" if sy > 0
                else "-Parameters.wheel_y_offset",
            "Placement.Base.z": "Parameters.wheel_dia / 2"})
        parts.append(carrier)

        e = pk.box(doc, "ENV_WHEEL_" + wtag,
                   "ENV_WHEEL_%s_O96x32_roller_envelope_marker" % wtag,
                   "UNVERIFIED - wheel+roller envelope reference; O96 "
                   "measured at roller surfaces per schematic "
                   "3606-0000-0096",
                   {"Length": "Parameters.wheel_dia",
                    "Width": "Parameters.wheel_width",
                    "Height": "Parameters.wheel_dia"},
                   {"Placement.Base.x":
                        "Parameters.wheel_x_offset - Parameters.wheel_dia / 2"
                        if sx > 0 else
                        "-Parameters.wheel_x_offset - Parameters.wheel_dia / 2",
                    "Placement.Base.y":
                        "Parameters.wheel_y_offset - Parameters.wheel_width / 2"
                        if sy > 0 else
                        "-Parameters.wheel_y_offset - Parameters.wheel_width / 2"})
        parts.append(e)

        wx = ("Parameters.wheel_x_offset" if sx > 0
              else "-Parameters.wheel_x_offset")
        web_in = ("Parameters.wheel_y_offset - Parameters.wheel_width / 2"
                  " - Parameters.rail_size")
        if sy > 0:
            face_y = "(%s) - Parameters.mface_t" % web_in
            motor_y = "(%s) - Parameters.mface_t - Parameters.motor_len" \
                      % web_in
            bear_y = "(%s) + Parameters.rail_wall" % web_in
            shaft_y = "(%s) - 16" % web_in
        else:
            face_y = "-(%s)" % web_in
            motor_y = "-(%s) + Parameters.mface_t" % web_in
            bear_y = ("-(%s) - Parameters.rail_wall - Parameters.bear_t"
                      % web_in)
            shaft_y = "-(%s) + 16 - Parameters.shaft_len" % web_in
        m = pk.cyl(doc, "MOTOR_" + wtag,
                   "MOTOR_%s_5203YellowJacket_O36_VENDOR-PENDING" % wtag,
                   "VENDOR-PENDING - goBILDA 5203 Yellow Jacket ~36mm (D12)",
                   {"Radius": "Parameters.motor_dia / 2",
                    "Height": "Parameters.motor_len"},
                   {"Placement.Base.x": wx,
                    "Placement.Base.y": motor_y,
                    "Placement.Base.z": "Parameters.wheel_dia / 2"},
                   pk.axis_rot("Y"),
                   "goBILDA 5203 Yellow Jacket-style motor placeholder")
        face = pk.face_plate(
            doc, "MOUNT_MOTOR_" + wtag,
            "MOUNT_MOTOR_%s_face_plate_30x30_UNVERIFIED" % wtag,
            "UNVERIFIED - motor face plate on rail web inner face",
            "Parameters.mface_w", "Parameters.mface_t",
            "Parameters.mface_h", "Parameters.bore_dia",
            {"Placement.Base.x": "%s - Parameters.mface_w / 2" % wx,
             "Placement.Base.y": face_y,
             "Placement.Base.z": "Parameters.wheel_dia / 2"
                                 " - Parameters.mface_h / 2"},
            "Y", "Parameters.bear_bolt_d", "Parameters.bear_bolt_off",
            pk.pval(sheet, "plate_fillet"))
        brg = pk.bearing_block(
            doc, "BEARING_" + wtag,
            "BEARING_%s_flange_block_26x26_UNVERIFIED" % wtag,
            "UNVERIFIED - flange bearing on rail web cavity face",
            "Parameters.bear_w", "Parameters.bear_t",
            "Parameters.bear_h", "Parameters.bear_bore",
            {"Placement.Base.x": "%s - Parameters.bear_w / 2" % wx,
             "Placement.Base.y": bear_y,
             "Placement.Base.z": "Parameters.wheel_dia / 2"
                                 " - Parameters.bear_h / 2"},
            "Y", "Parameters.bear_bolt_d", "Parameters.bear_bolt_off",
            pk.pval(sheet, "plate_fillet"))
        sh = pk.shaft(doc, "SHAFT_" + wtag,
                      "SHAFT_%s_8mmREX_live_VENDOR-PENDING" % wtag,
                      "VENDOR-PENDING - goBILDA 8mm REX live shaft (GEO7)",
                      "Parameters.shaft_dia", "Parameters.shaft_len",
                      {"Placement.Base.x": wx,
                       "Placement.Base.y": shaft_y,
                       "Placement.Base.z": "Parameters.wheel_dia / 2"},
                      "Y")
        parts += [m, face, brg, sh]

    pk.group_add(asm, *parts)
    for o in doc.Objects:
        if o.Name.startswith(pk.TOOL_PREFIX) and \
                o.getParentGeoFeatureGroup() is None:
            pk.group_add(tools_grp, o)
    doc.recompute()

    bad = []
    nulls = []
    for o in doc.Objects:
        if not hasattr(o, "Shape"):
            continue
        if o.Shape.isNull():
            nulls.append(o.Name)
        elif not o.Shape.isValid():
            bad.append(o.Name)
    if nulls:
        print("BUILD: NULL shapes: %s" % nulls)
    solids = [o for o in doc.Objects
              if hasattr(o, "Shape") and not o.Shape.isNull()
              and o.Shape.Volume > 0
              and o.TypeId not in ("App::Part", "App::Origin")]
    print("BUILD: objects=%d solids=%d invalid=%s"
          % (len(doc.Objects), len(solids), bad or "none"))
    for o in doc.Objects:
        if hasattr(o, "Shape") and not o.Shape.isNull() \
                and o.Shape.Volume > 0 and \
                o.TypeId not in ("App::Part", "App::Origin"):
            bb = o.Shape.BoundBox
            print("BUILD: %-24s | %-48s | bbox (%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f)"
                  % (o.Name, o.Label, bb.XMin, bb.YMin, bb.ZMin,
                     bb.XMax, bb.YMax, bb.ZMax))
    if bad or nulls:
        raise RuntimeError("invalid=%s null=%s" % (bad or "none",
                                                 nulls or "none"))


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
