"""Build cad/intake/intake_concept_v01.FCStd -- BIOBUZZ floor-intake concept.

Sprint-02 rebuild: component-fidelity intake via partkit.py -- bored and
chamfered cheek plates, two ribbed roller tubes on live 8mm REX shafts
with bearing blocks, bored pivot bosses with stub axles, a pivot servo on
a riser bracket, a tilted lip ramp, and L-bracket mounts tying the cheeks
back to the chassis stub. Throat clears the ~91 mm Nectar ball (VERIFIED,
Competition Manual sec 9.8) -- see VOL_BALL_PATH.

Run:  freecadcmd.exe scripts/freecad/build_intake_concept.py
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
CAD_DIR = ROOT / "cad" / "intake"
ARCHIVE_DIR = ROOT / "cad" / "archive"
TARGET = CAD_DIR / "intake_concept_v01.FCStd"
DOC_NAME = "intake_concept_v01"

# (alias, value, unit, status, source)
PARAMS = [
    ("intake_width", 326.0, "mm", "UNVERIFIED",
     "fits between wheel inner faces (+-164 with datasheet 32mm wheels)"),
    ("intake_depth", 160.0, "mm", "UNVERIFIED", "assumed frame depth"),
    ("intake_height", 120.0, "mm", "UNVERIFIED", "assumed frame height"),
    ("throat_clear_w", 120.0, "mm", "UNVERIFIED",
     "assumed; clears 91mm Nectar + margin"),
    ("throat_depth", 35.0, "mm", "UNVERIFIED", "assumed mouth depth"),
    ("throat_z", 10.0, "mm", "UNVERIFIED", "assumed mouth base height"),
    ("roller_dia", 50.0, "mm", "UNVERIFIED", "assumed intake roller"),
    ("roller_x", 100.0, "mm", "UNVERIFIED", "assumed roller center X"),
    ("roller_z1", 28.0, "mm", "UNVERIFIED",
     "lower roller center height (rib tips stay above the tile plane)"),
    ("roller_z2", 95.0, "mm", "UNVERIFIED", "upper roller center height"),
    ("chassis_stub_l", 60.0, "mm", "UNVERIFIED", "chassis edge reference"),
    ("chassis_stub_w", 340.0, "mm", "UNVERIFIED", "chassis edge reference"),
    ("chassis_stub_h", 40.0, "mm", "UNVERIFIED", "chassis edge reference"),
    ("chassis_stub_z", 30.0, "mm", "UNVERIFIED", "chassis edge reference"),
    ("plate_thk", 8.0, "mm", "UNVERIFIED", "cheek plate thickness"),
    ("pivot_boss_dia", 24.0, "mm", "UNVERIFIED", "pivot boss diameter"),
    ("pv_boss_len", 20.0, "mm", "UNVERIFIED", "cheek pivot boss length"),
    ("pivot_boss_x", 15.0, "mm", "UNVERIFIED", "pivot boss center X"),
    ("pivot_boss_z", 60.0, "mm", "UNVERIFIED", "pivot boss center height"),
    ("lip_len", 45.0, "mm", "UNVERIFIED", "mouth lip length"),
    ("lip_thk", 6.0, "mm", "UNVERIFIED", "mouth lip thickness"),
    ("lip_z", 25.0, "mm", "UNVERIFIED", "lip base height"),
    ("lip_ang", 20.0, "deg", "UNVERIFIED", "lip pitch angle"),
    # sprint-02 component hardware
    ("nectar_dia", 91.0, "mm", "VERIFIED",
     "Nectar ball ~91mm, competition manual sec 9.8"),
    ("shaft_dia", 8.0, "mm", "VENDOR-PENDING",
     "goBILDA 8mm REX shaft standard"),
    ("bore_dia", 8.4, "mm", "VENDOR-PENDING",
     "8mm REX clearance bore"),
    ("roller_bore", 9.0, "mm", "UNVERIFIED",
     "cheek bore for the roller shaft (+1mm)"),
    ("axle_dia", 12.0, "mm", "UNVERIFIED", "pivot stub axle dia"),
    ("axle_bore", 13.0, "mm", "UNVERIFIED", "boss/cheek bore for axle"),
    ("bear_w", 26.0, "mm", "UNVERIFIED", "bearing block face width"),
    ("bear_h", 26.0, "mm", "UNVERIFIED", "bearing block face height"),
    ("bear_t", 6.0, "mm", "UNVERIFIED", "bearing block thickness"),
    ("bear_bore", 8.4, "mm", "VENDOR-PENDING", "bearing bore"),
    ("bear_bolt_d", 4.0, "mm", "UNVERIFIED", "bearing bolt hole dia"),
    ("bear_bolt_off", 9.0, "mm", "UNVERIFIED", "bearing bolt offset"),
    ("rib_count", 12.0, "count", "UNVERIFIED", "roller grip ribs"),
    ("rib_w", 4.0, "mm", "UNVERIFIED", "rib tangential width"),
    ("rib_h", 3.0, "mm", "UNVERIFIED", "rib height"),
    ("rib_inset", 6.0, "mm", "UNVERIFIED", "rib axial inset"),
    ("servo_l", 40.5, "mm", "VENDOR-PENDING", "REV SRS-class servo body"),
    ("servo_w", 20.4, "mm", "VENDOR-PENDING", "REV SRS-class servo body"),
    ("servo_h", 36.0, "mm", "VENDOR-PENDING", "REV SRS-class servo body"),
    ("mbolt_d", 4.4, "mm", "UNVERIFIED", "M4 clearance bolt hole"),
    ("imount_l", 20.0, "mm", "UNVERIFIED", "mount bracket length"),
    ("imount_t", 4.0, "mm", "UNVERIFIED", "mount bracket leg thickness"),
    ("imount_h", 30.0, "mm", "UNVERIFIED", "mount bracket height"),
    ("wall_chamfer", 0.8, "mm", "UNVERIFIED", "sheet-edge chamfer"),
]

MANAGED = {
    "Parameters", "IntakeAssembly",
    "CHASSIS_STUB", "VOL_THROAT", "VOL_BALL_PATH",
    "INTAKE_CHEEK_L", "INTAKE_CHEEK_R",
    "ROLLER_LO", "ROLLER_HI",
    "ROLLER_SHAFT_LO", "ROLLER_SHAFT_HI",
    "INTAKE_BEARING_LO_L", "INTAKE_BEARING_LO_R",
    "INTAKE_BEARING_HI_L", "INTAKE_BEARING_HI_R",
    "PIVOT_MOUNT_L", "PIVOT_MOUNT_R",
    "INTAKE_AXLE_L", "INTAKE_AXLE_R",
    "INTAKE_MOTOR", "INTAKE_MOTOR_BRKT",
    "INTAKE_MOUNT_L", "INTAKE_MOUNT_R", "LIP_RAMP",
}
MANAGED.update("TOOL_INTAKE_CHEEK_%s_%s" % (s, t)
               for s in "LR" for t in ("BLK", "CUT"))
MANAGED.update("TOOL_INTAKE_CHEEK_%s_BORE%02d" % (s, i)
               for s in "LR" for i in range(5))
for n in ("ROLLER_LO", "ROLLER_HI"):
    MANAGED.update(("TOOL_%s_TUBE" % n, "TOOL_%s_TUBE_BLK" % n,
                    "TOOL_%s_TUBE_BORE" % n, "TOOL_%s_TOOLS" % n))
    MANAGED.update("TOOL_%s_RIB%02d" % (n, i) for i in range(12))
for n in ("INTAKE_BEARING_LO_L", "INTAKE_BEARING_LO_R",
          "INTAKE_BEARING_HI_L", "INTAKE_BEARING_HI_R"):
    MANAGED.update("TOOL_%s_%s" % (n, t) for t in ("BLK", "BORE"))
    MANAGED.update("TOOL_%s_B%02d" % (n, i) for i in range(4))
for n in ("PIVOT_MOUNT_L", "PIVOT_MOUNT_R"):
    MANAGED.update("TOOL_%s_%s" % (n, t) for t in ("BLK", "BORE"))
for n in ("INTAKE_MOUNT_L", "INTAKE_MOUNT_R"):
    MANAGED.update("TOOL_%s_%s" % (n, t) for t in ("LEG", "FOOT", "L"))
    MANAGED.update("TOOL_%s_B%02d" % (n, i) for i in range(2))
MANAGED.update(("TOOL_LIP_RAMP_BLK",))


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

    asm = doc.addObject("App::Part", "IntakeAssembly")
    asm.Label = "INTAKE_assembly_v02_component_fidelity"
    doc.recompute()  # let the App::Part Origin child appear
    solids = []

    # chassis reference edge the intake mounts to
    stub = pk.box(doc, "CHASSIS_STUB",
                  "CHASSIS_STUB_front_edge_reference_UNVERIFIED",
                  "UNVERIFIED - chassis edge reference",
                  {"Length": "Parameters.chassis_stub_l",
                   "Width": "Parameters.chassis_stub_w",
                   "Height": "Parameters.chassis_stub_h"},
                  {"Placement.Base.x": "-Parameters.chassis_stub_l",
                   "Placement.Base.y": "-Parameters.chassis_stub_w / 2",
                   "Placement.Base.z": "Parameters.chassis_stub_z"})
    solids.append(stub)

    # cheek plates: 2 roller-shaft bores + pivot bore + 2 mount bolts,
    # rim chamfer on the long edges
    for name, sgn in (("INTAKE_CHEEK_L", 1), ("INTAKE_CHEEK_R", -1)):
        cy = ("Parameters.intake_width / 2 - Parameters.plate_thk"
              if sgn > 0 else "-Parameters.intake_width / 2")
        by = ("Parameters.intake_width / 2 - Parameters.plate_thk - 1"
              if sgn > 0 else "-Parameters.intake_width / 2 - 1")
        bores = [
            ("Parameters.roller_bore",
             {"Placement.Base.x": "Parameters.roller_x",
              "Placement.Base.y": by,
              "Placement.Base.z": "Parameters.roller_z1"}, "Y",
             "Parameters.plate_thk + 2"),
            ("Parameters.roller_bore",
             {"Placement.Base.x": "Parameters.roller_x",
              "Placement.Base.y": by,
              "Placement.Base.z": "Parameters.roller_z2"}, "Y",
             "Parameters.plate_thk + 2"),
            ("Parameters.axle_bore",
             {"Placement.Base.x": "Parameters.pivot_boss_x",
              "Placement.Base.y": by,
              "Placement.Base.z": "Parameters.pivot_boss_z"}, "Y",
             "Parameters.plate_thk + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "6",
              "Placement.Base.y": by,
              "Placement.Base.z": "Parameters.imount_h / 2 + 2"}, "Y",
             "Parameters.plate_thk + 2"),
            ("Parameters.mbolt_d",
             {"Placement.Base.x": "16",
              "Placement.Base.y": by,
              "Placement.Base.z": "Parameters.imount_h / 2 + 2"}, "Y",
             "Parameters.plate_thk + 2")]
        solids.append(pk.bored_plate(
            doc, name, "%s_cheek_plate_bored_chamfered_UNVERIFIED" % name,
            "UNVERIFIED - intake cheek plate (2 roller + pivot + bolt "
            "bores, rim chamfer)",
            {"Length": "Parameters.intake_depth",
             "Width": "Parameters.plate_thk",
             "Height": "Parameters.intake_height"},
            {"Placement.Base.x": "0", "Placement.Base.y": cy},
            bores=bores, chamfer_l=pk.pval(sheet, "wall_chamfer"),
            chamfer_pred=pk.pred_not_axis((0, 1, 0))))

    # rollers: ribbed tube on a live shaft through the cheek bores;
    # bearing blocks on the cheek inner faces
    roller_span = "Parameters.intake_width - 2 * Parameters.plate_thk - 4"
    for tag, zalias in (("LO", "roller_z1"), ("HI", "roller_z2")):
        center = {"x": "Parameters.roller_x", "z": "Parameters." + zalias}
        solids.append(pk.ribbed_roller(
            doc, "ROLLER_%s" % tag,
            "ROLLER_%s_O50_ribbed_tube_on_8mmREX_UNVERIFIED" % tag,
            "UNVERIFIED - ribbed intake roller on live shaft",
            "Parameters.roller_dia", roller_span, "Parameters.bore_dia",
            {"Placement.Base.x": center["x"],
             "Placement.Base.y": "-(%s) / 2" % roller_span,
             "Placement.Base.z": center["z"]},
            center=center,
            ribs={"count": int(pk.pval(sheet, "rib_count")),
                  "w": "Parameters.rib_w", "h": "Parameters.rib_h",
                  "inset": "Parameters.rib_inset"}))
        solids.append(pk.shaft(
            doc, "ROLLER_SHAFT_%s" % tag,
            "ROLLER_SHAFT_%s_8mmREX_thru_cheeks_VENDOR-PENDING" % tag,
            "VENDOR-PENDING - goBILDA 8mm REX roller shaft",
            "Parameters.shaft_dia", "Parameters.intake_width + 10",
            {"Placement.Base.x": center["x"],
             "Placement.Base.y":
                 "-(Parameters.intake_width + 10) / 2",
             "Placement.Base.z": center["z"]}, "Y"))
        for sgn, sfx in ((1, "L"), (-1, "R")):
            by = ("Parameters.intake_width / 2 - Parameters.plate_thk"
                  " - Parameters.bear_t" if sgn > 0 else
                  "-Parameters.intake_width / 2 + Parameters.plate_thk")
            solids.append(pk.bearing_block(
                doc, "INTAKE_BEARING_%s_%s" % (tag, sfx),
                "INTAKE_BEARING_%s_%s_flanged_UNVERIFIED" % (tag, sfx),
                "UNVERIFIED - roller bearing block on cheek inner face",
                "Parameters.bear_w", "Parameters.bear_t",
                "Parameters.bear_h", "Parameters.bear_bore",
                {"Placement.Base.x":
                     "Parameters.roller_x - Parameters.bear_w / 2",
                 "Placement.Base.y": by,
                 "Placement.Base.z": "Parameters.%s - Parameters.bear_h / 2"
                                     % zalias},
                "Y", "Parameters.bear_bolt_d", "Parameters.bear_bolt_off"))

    # bored pivot bosses + stub axles (stubs stay clear of the throat)
    for name, sgn in (("PIVOT_MOUNT_L", 1), ("PIVOT_MOUNT_R", -1)):
        by = ("Parameters.intake_width / 2 - Parameters.plate_thk"
              " - Parameters.pv_boss_len" if sgn > 0 else
              "-Parameters.intake_width / 2 + Parameters.plate_thk")
        solids.append(pk.bore_cyl(
            doc, name, "%s_bored_pivot_boss_UNVERIFIED" % name,
            "UNVERIFIED - pivot boss ring on cheek inner face",
            "Parameters.pivot_boss_dia", "Parameters.pv_boss_len",
            "Parameters.axle_bore",
            {"Placement.Base.x": "Parameters.pivot_boss_x",
             "Placement.Base.y": by,
             "Placement.Base.z": "Parameters.pivot_boss_z"}, "Y"))
    for name, sgn in (("INTAKE_AXLE_L", 1), ("INTAKE_AXLE_R", -1)):
        ay = ("Parameters.intake_width / 2 - Parameters.plate_thk"
              " - Parameters.pv_boss_len / 2" if sgn > 0 else
              "-(Parameters.intake_width / 2) + 2")
        solids.append(pk.shaft(
            doc, name, "%s_pivot_stub_axle_UNVERIFIED" % name,
            "UNVERIFIED - pivot stub axle through cheek bore into boss",
            "Parameters.axle_dia",
            "Parameters.plate_thk + Parameters.pv_boss_len / 2 - 2",
            {"Placement.Base.x": "Parameters.pivot_boss_x",
             "Placement.Base.y": ay,
             "Placement.Base.z": "Parameters.pivot_boss_z"}, "Y"))

    # pivot servo bolted to the cheek inner face below the boss
    # (output coupling implied); riser foot props it off the floor
    solids.append(pk.box(
        doc, "INTAKE_MOTOR",
        "INTAKE_MOTOR_servo_40x20x36_VENDOR-PENDING",
        "VENDOR-PENDING - REV SRS-class intake pivot servo",
        {"Length": "Parameters.servo_l", "Width": "Parameters.servo_w",
         "Height": "Parameters.servo_h"},
        {"Placement.Base.x":
             "Parameters.pivot_boss_x + Parameters.pivot_boss_dia / 2 + 2",
         "Placement.Base.y":
             "Parameters.intake_width / 2 - Parameters.plate_thk"
             " - Parameters.servo_w",
         "Placement.Base.z": "Parameters.imount_t"}))
    solids.append(pk.box(
        doc, "INTAKE_MOTOR_BRKT",
        "INTAKE_MOTOR_BRKT_riser_foot_UNVERIFIED",
        "UNVERIFIED - servo riser foot under the servo",
        {"Length": "Parameters.servo_l + 4",
         "Width": "Parameters.servo_w + 10",
         "Height": "Parameters.imount_t"},
        {"Placement.Base.x":
             "Parameters.pivot_boss_x + Parameters.pivot_boss_dia / 2",
         "Placement.Base.y":
             "Parameters.intake_width / 2 - Parameters.plate_thk"
             " - Parameters.servo_w - 5",
         "Placement.Base.z": "0"}))

    # mounts: L-bracket from stub front face to each cheek inner face
    for name, sgn in (("INTAKE_MOUNT_L", 1), ("INTAKE_MOUNT_R", -1)):
        leg_y = ("Parameters.intake_width / 2 - Parameters.plate_thk"
                 " - Parameters.imount_t" if sgn > 0 else
                 "-Parameters.intake_width / 2 + Parameters.plate_thk")
        foot_y = leg_y
        solids.append(pk.l_bracket(
            doc, name, "%s_L_bracket_stub_to_cheek_UNVERIFIED" % name,
            "UNVERIFIED - intake mount L-bracket (stub face + cheek)",
            {"Length": "Parameters.imount_l",
             "Width": "Parameters.imount_t",
             "Height": "Parameters.imount_h"},
            {"Placement.Base.x": "0",
             "Placement.Base.y": leg_y,
             "Placement.Base.z": "2"},
            {"Length": "Parameters.imount_t",
             "Width": "Parameters.imount_t",
             "Height": "Parameters.imount_h"},
            {"Placement.Base.x": "-Parameters.imount_t",
             "Placement.Base.y": foot_y,
             "Placement.Base.z": "2"},
            bolts=[("Parameters.mbolt_d",
                    {"Placement.Base.x": "-Parameters.imount_t - 1",
                     "Placement.Base.y":
                         "Parameters.intake_width / 2"
                         " - Parameters.plate_thk"
                         " - Parameters.imount_t / 2" if sgn > 0 else
                         "-(Parameters.intake_width / 2"
                         " - Parameters.plate_thk"
                         " - Parameters.imount_t / 2)",
                     "Placement.Base.z": "12"}, "X",
                    "Parameters.imount_t + 2")]))

    # tilted lip ramp at the mouth floor
    lip = pk.box(doc, "LIP_RAMP",
                 "LIP_RAMP_mouth_scoop_tilted_UNVERIFIED",
                 "UNVERIFIED - tilted mouth lip ramp",
                 {"Length": "Parameters.lip_len",
                  "Width": "Parameters.intake_width"
                           " - 2 * Parameters.plate_thk",
                  "Height": "Parameters.lip_thk"},
                 {"Placement.Base.x":
                      "Parameters.intake_depth - Parameters.lip_len",
                  "Placement.Base.y":
                      "-(Parameters.intake_width"
                      " - 2 * Parameters.plate_thk) / 2",
                  "Placement.Base.z": "Parameters.lip_z"})
    lip.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), 0)
    lip.setExpression("Placement.Rotation.Angle", "Parameters.lip_ang")
    solids.append(lip)

    # probe volumes (VOL_ = excluded reference class)
    solids.append(pk.box(
        doc, "VOL_THROAT",
        "VOL_THROAT_clear_section_UNVERIFIED",
        "UNVERIFIED - throat clear-section probe",
        {"Length": "Parameters.throat_depth",
         "Width": "Parameters.intake_width - 2 * Parameters.plate_thk",
         "Height": "Parameters.intake_height - 20"},
        {"Placement.Base.x":
             "Parameters.intake_depth - Parameters.throat_depth",
         "Placement.Base.y":
             "-(Parameters.intake_width - 2 * Parameters.plate_thk) / 2",
         "Placement.Base.z": "Parameters.throat_z"}))
    solids.append(pk.cyl(
        doc, "VOL_BALL_PATH",
        "VOL_BALL_PATH_O91_nectar_lane_VERIFIED",
        "VERIFIED - O91 Nectar ball path probe (sec 9.8)",
        {"Radius": "Parameters.nectar_dia / 2",
         "Height": "Parameters.intake_depth - 0.2"},
        {"Placement.Base.x": "0",
         "Placement.Base.y": "0",
         "Placement.Base.z": "Parameters.nectar_dia / 2 + 5"},
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
