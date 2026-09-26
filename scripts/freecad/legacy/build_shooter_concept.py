"""Build cad/scoring/shooter_concept_v01.FCStd -- BIOBUZZ shooter concept.

Pollen-primary launcher placeholder: packaging volume, twin flywheels, muzzle
clear opening, and a +X launch-direction indicator aimed toward the Hive
cell opening (~508 x 356 mm, Competition Manual TU01 section 9.6). Pollen is
~71 mm dia (sec 9.8); the muzzle clears 80 mm+ for margin. Whether the shooter
must also handle Nectar is an OPEN question -- nothing here claims it.
All dimensions are UNVERIFIED assumptions bound to the Parameters sheet.
Run:  freecadcmd.exe scripts/freecad/build_shooter_concept.py
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
CAD_DIR = ROOT / "cad" / "scoring"
ARCHIVE_DIR = ROOT / "cad" / "archive"
TARGET = CAD_DIR / "shooter_concept_v01.FCStd"
DOC_NAME = "shooter_concept_v01"

# (alias, value, unit, status, source)
PARAMS = [
    ("shooter_l", 200.0, "mm", "UNVERIFIED", "assumed housing length"),
    ("shooter_w", 200.0, "mm", "UNVERIFIED", "assumed housing width"),
    ("shooter_h", 250.0, "mm", "UNVERIFIED", "assumed housing height"),
    ("shooter_z", 120.0, "mm", "UNVERIFIED", "housing base height above tile"),
    ("flywheel_dia", 72.0, "mm", "VENDOR-PENDING", "goBILDA-style wheel, datasheet pending"),
    ("flywheel_w", 30.0, "mm", "VENDOR-PENDING", "goBILDA-style wheel, datasheet pending"),
    ("flywheel_x", -40.0, "mm", "UNVERIFIED", "flywheel center X"),
    ("bore", 100.0, "mm", "UNVERIFIED", "universal bore per D10 - clears 91mm Nectar"),
    ("muzzle_clear", 110.0, "mm", "UNVERIFIED", "clears 91mm Nectar + margin (sec 9.8)"),
    ("muzzle_depth", 30.0, "mm", "UNVERIFIED", "muzzle channel depth"),
    ("hood_l", 50.0, "mm", "UNVERIFIED", "hood plate length"),
    ("hood_w", 120.0, "mm", "UNVERIFIED", "hood plate width"),
    ("hood_thk", 8.0, "mm", "UNVERIFIED", "hood plate thickness"),
    ("backstop_thk", 8.0, "mm", "UNVERIFIED", "backstop plate thickness"),
    ("backstop_h", 100.0, "mm", "UNVERIFIED", "backstop plate height"),
    ("inlet_depth", 40.0, "mm", "UNVERIFIED", "feed inlet depth into housing"),
    ("inlet_w", 90.0, "mm", "UNVERIFIED", "feed inlet width"),
    ("inlet_h", 90.0, "mm", "UNVERIFIED", "feed inlet height"),
    ("inlet_z", 130.0, "mm", "UNVERIFIED", "feed inlet base height"),
    ("launch_len", 160.0, "mm", "UNVERIFIED", "launch indicator length"),
    ("launch_thk", 8.0, "mm", "UNVERIFIED", "launch indicator thickness"),
    ("launch_z", 300.0, "mm", "UNVERIFIED", "launch height above tile"),
    ("stub_dia", 8.0, "mm", "VENDOR-PENDING",
     "goBILDA 8mm REX shaft standard, series page"),
    ("stub_len", 40.0, "mm", "UNVERIFIED", "flywheel stub shaft length"),
]

MANAGED = {
    "Parameters", "ShooterAssembly",
    "SHOOTER_BODY", "FLYWHEEL_L", "FLYWHEEL_R",
    "MUZZLE_CLEAR", "LAUNCH_DIR",
    "HOOD", "BACKSTOP", "FEED_INLET",
    "STUB_SHAFT_L", "STUB_SHAFT_R",
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


def solid(doc, typeid, name, label, status):
    o = doc.addObject(typeid, name)
    o.Label = label
    o.addProperty("App::PropertyString", "DataStatus", "Status",
                  "verification state of this placeholder")
    o.DataStatus = status
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

    asm = doc.addObject("App::Part", "ShooterAssembly")
    asm.Label = "SHOOTER_assembly_v01_pollen_launcher_placeholders"
    doc.recompute()  # let the App::Part Origin child appear

    body = solid(doc, "Part::Box", "SHOOTER_BODY",
                 "SHOOTER_BODY_200x200x250_pollen_UNVERIFIED",
                 "UNVERIFIED - assumed housing volume")
    body.addProperty("App::PropertyString", "DataNote", "Notes",
                     "open design note")
    body.DataNote = ("Universal launcher per D10: ~100mm bore clears Pollen "
                     "and Nectar; Nectar-capable per D10 (settled)")
    body.setExpression("Length", "Parameters.shooter_l")
    body.setExpression("Width", "Parameters.shooter_w")
    body.setExpression("Height", "Parameters.shooter_h")
    body.setExpression("Placement.Base.x", "-Parameters.shooter_l")
    body.setExpression("Placement.Base.y", "-Parameters.shooter_w / 2")
    body.setExpression("Placement.Base.z", "Parameters.shooter_z")

    wheels = []
    for name, sgn in (("FLYWHEEL_L", 1), ("FLYWHEEL_R", -1)):
        f = solid(doc, "Part::Cylinder", name,
                  "%s_72x30_goBILDA-style_VENDOR-PENDING" % name,
                  "UNVERIFIED - VENDOR-PENDING (goBILDA-style flywheel)")
        f.addProperty("App::PropertyString", "VendorRef", "Vendor",
                      "vendor reference, pending verification")
        f.VendorRef = ("goBILDA-style launcher wheel placeholder - "
                       "datasheet verification pending")
        f.setExpression("Radius", "Parameters.flywheel_dia / 2")
        f.setExpression("Height", "Parameters.flywheel_w")
        f.Placement = App.Placement(App.Vector(0, 0, 0),
                                    App.Rotation(App.Vector(1, 0, 0), -90))
        f.setExpression("Placement.Base.x", "Parameters.flywheel_x")
        f.setExpression("Placement.Base.y",
                        "Parameters.bore / 2" if sgn > 0 else
                        "-Parameters.bore / 2 - Parameters.flywheel_w")
        f.setExpression("Placement.Base.z", "Parameters.launch_z")
        wheels.append(f)

    muz = solid(doc, "Part::Box", "MUZZLE_CLEAR",
                "MUZZLE_CLEAR_110x110_universal_exit_UNVERIFIED",
                "UNVERIFIED - assumed clear muzzle (91mm Nectar + margin)")
    muz.setExpression("Length", "Parameters.muzzle_depth")
    muz.setExpression("Width", "Parameters.muzzle_clear")
    muz.setExpression("Height", "Parameters.muzzle_clear")
    muz.setExpression("Placement.Base.x", "-Parameters.muzzle_depth")
    muz.setExpression("Placement.Base.y", "-Parameters.muzzle_clear / 2")
    muz.setExpression("Placement.Base.z",
                      "Parameters.launch_z - Parameters.muzzle_clear / 2")

    ld = solid(doc, "Part::Box", "LAUNCH_DIR",
               "LAUNCH_DIR_plusX_toward_HIVE_UNVERIFIED",
               "UNVERIFIED - launch direction marker (+X, toward Hive)")
    ld.setExpression("Length", "Parameters.launch_len")
    ld.setExpression("Width", "Parameters.launch_thk")
    ld.setExpression("Height", "Parameters.launch_thk")
    ld.setExpression("Placement.Base.y", "-Parameters.launch_thk / 2")
    ld.setExpression("Placement.Base.z",
                     "Parameters.launch_z - Parameters.launch_thk / 2")

    hood = solid(doc, "Part::Box", "HOOD",
                 "HOOD_muzzle_top_plate_UNVERIFIED",
                 "UNVERIFIED - assumed hood over muzzle")
    hood.setExpression("Length", "Parameters.hood_l")
    hood.setExpression("Width", "Parameters.hood_w")
    hood.setExpression("Height", "Parameters.hood_thk")
    hood.setExpression("Placement.Base.x", "-Parameters.hood_l")
    hood.setExpression("Placement.Base.y", "-Parameters.hood_w / 2")
    hood.setExpression("Placement.Base.z",
                     "Parameters.launch_z + Parameters.muzzle_clear / 2")

    bs = solid(doc, "Part::Box", "BACKSTOP",
               "BACKSTOP_behind_bore_UNVERIFIED",
               "UNVERIFIED - assumed backstop plate")
    bs.setExpression("Length", "Parameters.backstop_thk")
    bs.setExpression("Width", "Parameters.bore")
    bs.setExpression("Height", "Parameters.backstop_h")
    bs.setExpression("Placement.Base.x",
                     "Parameters.flywheel_x - Parameters.flywheel_dia / 2"
                     " - Parameters.backstop_thk")
    bs.setExpression("Placement.Base.y", "-Parameters.bore / 2")
    bs.setExpression("Placement.Base.z",
                     "Parameters.launch_z - Parameters.backstop_h / 2")

    fi = solid(doc, "Part::Box", "FEED_INLET",
               "FEED_INLET_rear_entry_UNVERIFIED",
               "UNVERIFIED - assumed feed opening at -X face")
    fi.setExpression("Length", "Parameters.inlet_depth")
    fi.setExpression("Width", "Parameters.inlet_w")
    fi.setExpression("Height", "Parameters.inlet_h")
    fi.setExpression("Placement.Base.x", "-Parameters.shooter_l")
    fi.setExpression("Placement.Base.y", "-Parameters.inlet_w / 2")
    fi.setExpression("Placement.Base.z", "Parameters.inlet_z")

    # sprint-06: flywheel stub shafts (8mm REX placeholders) through bores
    stubs = []
    for name, sgn in (("STUB_SHAFT_L", 1), ("STUB_SHAFT_R", -1)):
        ss = solid(doc, "Part::Cylinder", name,
                   "%s_8mmREX_flywheel_shaft_VENDOR-PENDING" % name,
                   "VENDOR-PENDING - goBILDA 8mm REX stub shaft")
        ss.setExpression("Radius", "Parameters.stub_dia / 2")
        ss.setExpression("Height", "Parameters.stub_len")
        ss.Placement = App.Placement(App.Vector(0, 0, 0),
                                     App.Rotation(App.Vector(1, 0, 0), -90))
        ss.setExpression("Placement.Base.x", "Parameters.flywheel_x")
        ss.setExpression("Placement.Base.y",
                         "Parameters.bore / 2 - (Parameters.stub_len"
                         " - Parameters.flywheel_w) / 2"
                         if sgn > 0 else
                         "-Parameters.bore / 2 - Parameters.flywheel_w"
                         " - (Parameters.stub_len - Parameters.flywheel_w) / 2")
        ss.setExpression("Placement.Base.z", "Parameters.launch_z")
        stubs.append(ss)

    group_add(asm, body, *wheels, *stubs, muz, ld, hood, bs, fi)
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
