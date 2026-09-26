"""Build cad/electronics/electronics_concept_v01.FCStd -- BIOBUZZ electronics.

Battery + control hub + expansion hub placeholders positioned disjoint inside
the chassis volume (420 x 420 x 120 mm reserve, matching the drivebase).
Battery/hub sizes are REV-style catalog placeholders -- VENDOR-PENDING, never
VERIFIED. All dimensions bound to the Parameters sheet.
Run:  freecadcmd.exe scripts/freecad/build_electronics_concept.py
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

ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = ROOT / "cad" / "electronics"
ARCHIVE_DIR = ROOT / "cad" / "archive"
TARGET = CAD_DIR / "electronics_concept_v01.FCStd"
DOC_NAME = "electronics_concept_v01"

# (alias, value, unit, status, source)
PARAMS = [
    ("chassis_length", 420.0, "mm", "UNVERIFIED", "chassis volume reference"),
    ("chassis_width", 420.0, "mm", "UNVERIFIED", "chassis volume reference"),
    ("chassis_height", 120.0, "mm", "UNVERIFIED", "chassis volume reference"),
    ("battery_l", 180.0, "mm", "VENDOR-PENDING", "REV-style battery, datasheet pending"),
    ("battery_w", 90.0, "mm", "VENDOR-PENDING", "REV-style battery, datasheet pending"),
    ("battery_h", 75.0, "mm", "VENDOR-PENDING", "REV-style battery, datasheet pending"),
    ("battery_x", -190.0, "mm", "UNVERIFIED", "battery placement"),
    ("battery_y", -45.0, "mm", "UNVERIFIED", "battery placement"),
    ("battery_z", 22.5, "mm", "UNVERIFIED", "battery placement"),
    ("hub_l", 160.0, "mm", "VENDOR-PENDING", "REV-style hub, datasheet pending"),
    ("hub_w", 120.0, "mm", "VENDOR-PENDING", "REV-style hub, datasheet pending"),
    ("hub_h", 35.0, "mm", "VENDOR-PENDING", "REV-style hub, datasheet pending"),
    ("ctrl_x", 40.0, "mm", "UNVERIFIED", "control hub placement"),
    ("ctrl_y", -60.0, "mm", "UNVERIFIED", "control hub placement"),
    ("ctrl_z", 42.5, "mm", "UNVERIFIED", "control hub placement"),
    ("exp_x", -190.0, "mm", "UNVERIFIED", "expansion hub placement"),
    ("exp_y", 60.0, "mm", "UNVERIFIED", "expansion hub placement"),
    ("exp_z", 42.5, "mm", "UNVERIFIED", "expansion hub placement"),
    ("erail_l", 140.0, "mm", "UNVERIFIED", "hub mounting rail length"),
    ("erail_w", 8.0, "mm", "UNVERIFIED", "hub mounting rail width"),
    ("erail_h", 6.0, "mm", "UNVERIFIED", "hub mounting rail height"),
]

MANAGED = {
    "Parameters", "ElectronicsAssembly",
    "CHASSIS_VOL", "BATTERY", "HUB_CTRL", "HUB_EXP",
    "ELEC_RAIL_L", "ELEC_RAIL_R",
}


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


def group_add(part, *objs):
    part.Group = list(part.Group) + [o for o in objs if o not in part.Group]


def solid(doc, typeid, name, label, status, vendor=None):
    o = doc.addObject(typeid, name)
    o.Label = label
    o.addProperty("App::PropertyString", "DataStatus", "Status",
                  "verification state of this placeholder")
    o.DataStatus = status
    if vendor:
        o.addProperty("App::PropertyString", "VendorRef", "Vendor",
                      "vendor reference, pending verification")
        o.VendorRef = vendor
    return o


def populate(doc):
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.Label = "Parameters"
    for col, head in zip("ABCDE", ("alias", "value", "unit", "status", "source")):
        sheet.set(col + "1", head)
    for i, (alias, val, unit, status, src) in enumerate(PARAMS):
        r = str(i + 2)
        sheet.set("A" + r, alias)
        sheet.set("B" + r, repr(val))
        sheet.set("C" + r, unit)
        sheet.set("D" + r, status)
        sheet.set("E" + r, src)
        sheet.setAlias("B" + r, alias)

    asm = doc.addObject("App::Part", "ElectronicsAssembly")
    asm.Label = "ELECTRONICS_assembly_v01_placeholders"
    doc.recompute()  # let the App::Part Origin child appear

    cv = solid(doc, "Part::Box", "CHASSIS_VOL",
               "CHASSIS_VOL_420x420x120_reference_UNVERIFIED",
               "UNVERIFIED - chassis volume reference (matches drivebase)")
    cv.setExpression("Length", "Parameters.chassis_length")
    cv.setExpression("Width", "Parameters.chassis_width")
    cv.setExpression("Height", "Parameters.chassis_height")
    cv.setExpression("Placement.Base.x", "-Parameters.chassis_length / 2")
    cv.setExpression("Placement.Base.y", "-Parameters.chassis_width / 2")

    bat = solid(doc, "Part::Box", "BATTERY",
                "BATTERY_180x90x75_REV-style_VENDOR-PENDING",
                "UNVERIFIED - VENDOR-PENDING (REV-style battery)",
                vendor="REV-style 12V battery placeholder - datasheet pending")
    bat.setExpression("Length", "Parameters.battery_l")
    bat.setExpression("Width", "Parameters.battery_w")
    bat.setExpression("Height", "Parameters.battery_h")
    bat.setExpression("Placement.Base.x", "Parameters.battery_x")
    bat.setExpression("Placement.Base.y", "Parameters.battery_y")
    bat.setExpression("Placement.Base.z", "Parameters.battery_z")

    hc = solid(doc, "Part::Box", "HUB_CTRL",
               "HUB_CTRL_160x120x35_REV-style_VENDOR-PENDING",
               "UNVERIFIED - VENDOR-PENDING (REV-style control hub)",
               vendor="REV Control Hub placeholder - datasheet pending")
    hc.setExpression("Length", "Parameters.hub_l")
    hc.setExpression("Width", "Parameters.hub_w")
    hc.setExpression("Height", "Parameters.hub_h")
    hc.setExpression("Placement.Base.x", "Parameters.ctrl_x")
    hc.setExpression("Placement.Base.y", "Parameters.ctrl_y")
    hc.setExpression("Placement.Base.z", "Parameters.ctrl_z")

    he = solid(doc, "Part::Box", "HUB_EXP",
               "HUB_EXP_160x120x35_REV-style_VENDOR-PENDING",
               "UNVERIFIED - VENDOR-PENDING (REV-style expansion hub)",
               vendor="REV Expansion Hub placeholder - datasheet pending")
    he.setExpression("Length", "Parameters.hub_l")
    he.setExpression("Width", "Parameters.hub_w")
    he.setExpression("Height", "Parameters.hub_h")
    he.setExpression("Placement.Base.x", "Parameters.exp_x")
    he.setExpression("Placement.Base.y", "Parameters.exp_y")
    he.setExpression("Placement.Base.z", "Parameters.exp_z")

    # sprint-06: mounting rails under the two hubs (declared overlap class:
    # rail x hub solid - rail top sits 2mm inside each hub footprint)
    rails = []
    for name, hx, hy, hz in (("ELEC_RAIL_L", "ctrl_x", "ctrl_y", "ctrl_z"),
                            ("ELEC_RAIL_R", "exp_x", "exp_y", "exp_z")):
        er = solid(doc, "Part::Box", name,
                   "%s_hub_mount_rail_UNVERIFIED" % name,
                   "UNVERIFIED - hub mounting rail")
        er.setExpression("Length", "Parameters.erail_l")
        er.setExpression("Width", "Parameters.erail_w")
        er.setExpression("Height", "Parameters.erail_h")
        er.setExpression("Placement.Base.x",
                         "Parameters.%s + (Parameters.hub_l"
                         " - Parameters.erail_l) / 2" % hx)
        er.setExpression("Placement.Base.y",
                         "Parameters.%s + Parameters.hub_w / 2"
                         " - Parameters.erail_w / 2" % hy)
        er.setExpression("Placement.Base.z",
                         "Parameters.%s - Parameters.erail_h + 2" % hz)
        rails.append(er)

    group_add(asm, cv, bat, hc, he, *rails)
    doc.recompute()

    bad = [o.Name for o in doc.Objects
           if hasattr(o, "Shape") and o.Shape.Solids and not o.Shape.isValid()]
    solids = [o for o in doc.Objects
              if hasattr(o, "Shape") and o.Shape.Solids]
    print("BUILD: objects=%d solids=%d invalid=%s"
          % (len(doc.Objects), len(solids), bad or "none"))
    for o in solids:
        bb = o.Shape.BoundBox
        print("BUILD: %-12s | %-52s | bbox (%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f)"
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
