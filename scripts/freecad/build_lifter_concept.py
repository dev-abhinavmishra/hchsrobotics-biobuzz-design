"""Build cad/endgame/lifter_concept_v01.FCStd -- BIOBUZZ Nectar lifter concept.

Top-mounted lifter placeholder: stowed solid inside the 457.2 mm start cube
(R102), deployed ghost mast reaching >=600 mm toward the ~546 mm Flower top
opening (sec 9.7) while staying inside the R105 expansion volume
(457.2 x 609.6 x 736.5 mm), plus a >=100 mm cradle for the ~91 mm Nectar ball.
Reference envelopes are VERIFIED per the Competition Manual (TU01); every
lifter dimension is an UNVERIFIED assumption bound to the Parameters sheet.
Run:  freecadcmd.exe scripts/freecad/build_lifter_concept.py
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
CAD_DIR = ROOT / "cad" / "endgame"
ARCHIVE_DIR = ROOT / "cad" / "archive"
TARGET = CAD_DIR / "lifter_concept_v01.FCStd"
DOC_NAME = "lifter_concept_v01"

# (alias, value, unit, status, source)
PARAMS = [
    ("start_cube", 457.2, "mm", "VERIFIED", "R102 TU01"),
    ("expansion_width", 457.2, "mm", "VERIFIED", "R105 TU01"),
    ("expansion_depth", 609.6, "mm", "VERIFIED", "R105 TU01"),
    ("expansion_height", 736.5, "mm", "VERIFIED", "R105 TU01"),
    ("lifter_stow_l", 200.0, "mm", "UNVERIFIED", "assumed stowed length"),
    ("lifter_stow_w", 200.0, "mm", "UNVERIFIED", "assumed stowed width"),
    ("lifter_stow_h", 150.0, "mm", "UNVERIFIED", "assumed stowed height"),
    ("lifter_stow_x", 20.0, "mm", "UNVERIFIED", "stowed X offset"),
    ("lifter_stow_z", 120.0, "mm", "UNVERIFIED", "stowed base height (top-mounted)"),
    ("mast_w", 80.0, "mm", "UNVERIFIED", "deployed mast section"),
    ("lifter_dep_z0", 120.0, "mm", "UNVERIFIED", "deployed mast base height"),
    ("reach_z", 610.0, "mm", "UNVERIFIED", "deployed top reach (>=546 + clearance, sec 9.7)"),
    ("cradle_w", 120.0, "mm", "UNVERIFIED", "cradle width (91mm Nectar + clearance)"),
    ("cradle_h", 40.0, "mm", "UNVERIFIED", "cradle height"),
    ("cradle_z", 600.0, "mm", "UNVERIFIED", "cradle base height (>=546 sec 9.7)"),
    ("stage1_w", 76.0, "mm", "UNVERIFIED", "outer cascade stage section"),
    ("stage1_z1", 340.0, "mm", "UNVERIFIED", "outer stage top"),
    ("stage2_w", 74.0, "mm", "UNVERIFIED", "middle cascade stage section"),
    ("stage2_z0", 230.0, "mm", "UNVERIFIED", "middle stage base"),
    ("stage2_z1", 440.0, "mm", "UNVERIFIED", "middle stage top"),
    ("stage3_w", 72.0, "mm", "UNVERIFIED", "inner cascade stage section"),
    ("stage3_z0", 335.0, "mm", "UNVERIFIED", "inner stage base"),
    ("stage3_z1", 560.0, "mm", "UNVERIFIED", "inner stage top"),
    ("carriage_w", 120.0, "mm", "UNVERIFIED", "carriage plate section"),
    ("carriage_h", 40.0, "mm", "UNVERIFIED", "carriage plate height"),
    ("hardstop_h", 10.0, "mm", "UNVERIFIED", "hard-stop marker height"),
    ("guide_w", 6.0, "mm", "UNVERIFIED", "stage guide block section"),
    ("guide_l", 20.0, "mm", "UNVERIFIED", "stage guide block height"),
    ("lip_h", 12.0, "mm", "UNVERIFIED", "cradle lip height"),
    ("lip_t", 6.0, "mm", "UNVERIFIED", "cradle lip thickness"),
]

MANAGED = {
    "Parameters", "LifterAssembly",
    "ENV_START", "ENV_EXPANSION",
    "LIFTER_STOWED", "LIFTER_DEPLOYED", "CRADLE",
    "STAGE_1", "STAGE_2", "STAGE_3", "CARRIAGE", "HARD_STOP",
    "STAGE_GUIDE_L", "STAGE_GUIDE_R", "CRADLE_LIP",
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

    asm = doc.addObject("App::Part", "LifterAssembly")
    asm.Label = "LIFTER_assembly_v01_nectar_top_mount_placeholders"
    doc.recompute()  # let the App::Part Origin child appear

    env = solid(doc, "Part::Box", "ENV_START",
                "ENV_START_18in_cube_457mm_VERIFIED_R102",
                "VERIFIED - R102 TU01")
    for prop in ("Length", "Width", "Height"):
        env.setExpression(prop, "Parameters.start_cube")
    env.setExpression("Placement.Base.x", "-Parameters.start_cube / 2")
    env.setExpression("Placement.Base.y", "-Parameters.start_cube / 2")

    ex = solid(doc, "Part::Box", "ENV_EXPANSION",
               "ENV_EXPANSION_18x24x29in_VERIFIED_R105",
               "VERIFIED - R105 TU01")
    ex.setExpression("Length", "Parameters.expansion_width")
    ex.setExpression("Width", "Parameters.expansion_depth")
    ex.setExpression("Height", "Parameters.expansion_height")
    ex.setExpression("Placement.Base.x", "-Parameters.expansion_width / 2")
    ex.setExpression("Placement.Base.y", "-Parameters.expansion_depth / 2")

    stow = solid(doc, "Part::Box", "LIFTER_STOWED",
                 "LIFTER_STOWED_200x200x150_top_mount_UNVERIFIED",
                 "UNVERIFIED - assumed stowed lifter volume")
    stow.setExpression("Length", "Parameters.lifter_stow_l")
    stow.setExpression("Width", "Parameters.lifter_stow_w")
    stow.setExpression("Height", "Parameters.lifter_stow_h")
    stow.setExpression("Placement.Base.x", "Parameters.lifter_stow_x")
    stow.setExpression("Placement.Base.y", "-Parameters.lifter_stow_w / 2")
    stow.setExpression("Placement.Base.z", "Parameters.lifter_stow_z")

    dep = solid(doc, "Part::Box", "LIFTER_DEPLOYED",
                "LIFTER_DEPLOYED_mast_ghost_reach610_UNVERIFIED",
                "UNVERIFIED - assumed deployed mast envelope")
    dep.setExpression("Length", "Parameters.mast_w")
    dep.setExpression("Width", "Parameters.mast_w")
    dep.setExpression("Height",
                      "Parameters.reach_z - Parameters.lifter_dep_z0")
    dep.setExpression("Placement.Base.x",
                      "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                      " - Parameters.mast_w / 2")
    dep.setExpression("Placement.Base.y", "-Parameters.mast_w / 2")
    dep.setExpression("Placement.Base.z", "Parameters.lifter_dep_z0")

    cr = solid(doc, "Part::Box", "CRADLE",
               "CRADLE_120x120x40_nectar_cup_UNVERIFIED",
               "UNVERIFIED - assumed cradle (91mm Nectar + clearance)")
    cr.setExpression("Length", "Parameters.cradle_w")
    cr.setExpression("Width", "Parameters.cradle_w")
    cr.setExpression("Height", "Parameters.cradle_h")
    cr.setExpression("Placement.Base.x",
                     "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                     " - Parameters.cradle_w / 2")
    cr.setExpression("Placement.Base.y", "-Parameters.cradle_w / 2")
    cr.setExpression("Placement.Base.z", "Parameters.cradle_z")

    # cascade stages nested inside the deployed ghost envelope
    stages = []
    stage_defs = (
        ("STAGE_1", "stage1_w", "Parameters.lifter_dep_z0",
         "Parameters.stage1_z1"),
        ("STAGE_2", "stage2_w", "Parameters.stage2_z0",
         "Parameters.stage2_z1"),
        ("STAGE_3", "stage3_w", "Parameters.stage3_z0",
         "Parameters.stage3_z1"),
    )
    for name, walias, z0expr, z1expr in stage_defs:
        s = solid(doc, "Part::Box", name,
                  "%s_cascade_section_UNVERIFIED" % name,
                  "UNVERIFIED - assumed cascade stage section")
        s.setExpression("Length", "Parameters." + walias)
        s.setExpression("Width", "Parameters." + walias)
        s.setExpression("Height", "(%s) - (%s)" % (z1expr, z0expr))
        s.setExpression("Placement.Base.x",
                        "Parameters.lifter_stow_x + Parameters.lifter_stow_l"
                        " / 2 - Parameters.%s / 2" % walias)
        s.setExpression("Placement.Base.y", "-Parameters.%s / 2" % walias)
        s.setExpression("Placement.Base.z", z0expr)
        stages.append(s)

    car = solid(doc, "Part::Box", "CARRIAGE",
                "CARRIAGE_stage3_top_UNVERIFIED",
                "UNVERIFIED - assumed carriage plate")
    car.setExpression("Length", "Parameters.carriage_w")
    car.setExpression("Width", "Parameters.carriage_w")
    car.setExpression("Height", "Parameters.carriage_h")
    car.setExpression("Placement.Base.x",
                      "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                      " - Parameters.carriage_w / 2")
    car.setExpression("Placement.Base.y", "-Parameters.carriage_w / 2")
    car.setExpression("Placement.Base.z", "Parameters.stage3_z1")

    hs = solid(doc, "Part::Box", "HARD_STOP",
               "HARD_STOP_R105B_physical_marker_UNVERIFIED",
               "UNVERIFIED - physical travel stop required by R105")
    hs.setExpression("Length", "Parameters.stage1_w")
    hs.setExpression("Width", "Parameters.stage1_w")
    hs.setExpression("Height", "Parameters.hardstop_h")
    hs.setExpression("Placement.Base.x",
                     "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                     " - Parameters.stage1_w / 2")
    hs.setExpression("Placement.Base.y", "-Parameters.stage1_w / 2")
    hs.setExpression("Placement.Base.z",
                     "Parameters.stage1_z1 - Parameters.hardstop_h")

    # sprint-06: stage guide blocks ride the stage walls; cradle lip is a
    # retention rim on the cradle's +X edge (declared overlap classes)
    guides = []
    for name, sgn in (("STAGE_GUIDE_L", 1), ("STAGE_GUIDE_R", -1)):
        gd = solid(doc, "Part::Box", name,
                   "%s_cascade_guide_block_UNVERIFIED" % name,
                   "UNVERIFIED - stage guide block riding stage walls")
        gd.setExpression("Length", "Parameters.guide_w")
        gd.setExpression("Width", "Parameters.guide_w")
        gd.setExpression("Height", "Parameters.guide_l")
        gd.setExpression("Placement.Base.x",
                         "Parameters.lifter_stow_x + Parameters.lifter_stow_l"
                         " / 2 - Parameters.guide_w / 2")
        gd.setExpression("Placement.Base.y",
                         "Parameters.stage1_w / 2 - Parameters.guide_w / 2"
                         if sgn > 0 else
                         "-Parameters.stage1_w / 2 - Parameters.guide_w / 2")
        gd.setExpression("Placement.Base.z",
                         "Parameters.stage1_z1 - Parameters.guide_l * 3 / 4")
        guides.append(gd)

    lip = solid(doc, "Part::Box", "CRADLE_LIP",
                "CRADLE_LIP_retention_rim_UNVERIFIED",
                "UNVERIFIED - cradle retention lip")
    lip.setExpression("Length", "Parameters.lip_t")
    lip.setExpression("Width", "Parameters.cradle_w")
    lip.setExpression("Height", "Parameters.lip_h")
    lip.setExpression("Placement.Base.x",
                      "Parameters.lifter_stow_x + Parameters.lifter_stow_l / 2"
                      " + Parameters.cradle_w / 2 - Parameters.lip_t")
    lip.setExpression("Placement.Base.y", "-Parameters.cradle_w / 2")
    lip.setExpression("Placement.Base.z",
                      "Parameters.cradle_z + Parameters.cradle_h"
                      " - Parameters.lip_h")

    group_add(asm, env, ex, stow, dep, cr, *stages, car, hs, *guides, lip)
    doc.recompute()

    bad = [o.Name for o in doc.Objects
           if hasattr(o, "Shape") and o.Shape.Solids and not o.Shape.isValid()]
    solids = [o for o in doc.Objects
              if hasattr(o, "Shape") and o.Shape.Solids]
    print("BUILD: objects=%d solids=%d invalid=%s"
          % (len(doc.Objects), len(solids), bad or "none"))
    for o in solids:
        bb = o.Shape.BoundBox
        print("BUILD: %-16s | %-52s | bbox (%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f)"
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
