"""Export prototype STL + STEP of the BIOBUZZ master assembly.

Exports the robot placeholder solids ONLY (excludes ENV_*/AXIS_*/REF_*
references, VOL_* packaging reserves, and App::Part containers), labeled
PROTOTYPE / VERIFY BEFORE MANUFACTURING in the filenames and manifest.

Run:  freecadcmd.exe scripts/freecad/export_prototypes.py
All paths resolve relative to this file (project_root/scripts/freecad/).
"""
import hashlib
import sys
import traceback
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "cad" / "master_robot.FCStd"
STL_DIR = ROOT / "exports" / "prototype_stl"
STEP_DIR = ROOT / "exports" / "prototype_step"
STL_OUT = STL_DIR / "master_robot_PROTOTYPE.stl"
STEP_OUT = STEP_DIR / "master_robot_PROTOTYPE.step"
MANIFEST = ROOT / "exports" / "MANIFEST.md"
RESULTS = ROOT / "exports" / "export_validation.txt"
LABEL = "PROTOTYPE / VERIFY BEFORE MANUFACTURING"

# non-physical references: envelopes, coordinate markers, field aim
# markers, packaging reserves, and construction tools are never exported
EXCLUDE_PREFIX = ("ENV_", "AXIS_", "REF_", "VOL_", "TOOL_")
EXCLUDE_TYPES = ("App::Part", "App::Origin")


def exportable(doc):
    return [o for o in doc.Objects
            if hasattr(o, "Shape") and not o.Shape.isNull()
            and o.Shape.Volume > 0
            and o.TypeId not in EXCLUDE_TYPES
            and not o.Name.startswith(EXCLUDE_PREFIX)]


def main():
    log = []

    def say(msg):
        print(msg)
        sys.stdout.flush()
        log.append(msg)

    doc = App.openDocument(str(MASTER))
    doc.recompute()
    objs = exportable(doc)
    names = sorted(o.Name for o in objs)
    say("EXPORT: %d robot solids" % len(objs))

    # carrier children store local-frame Shape; the world position lives
    # in the App::Part chain. Globalize every shape before export.
    shapes = []
    for o in objs:
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        shapes.append(s)

    STL_DIR.mkdir(parents=True, exist_ok=True)
    STEP_DIR.mkdir(parents=True, exist_ok=True)

    import Part
    compound = Part.makeCompound(shapes)

    import Mesh
    mesh = Mesh.Mesh()
    for s in shapes:
        mesh.addMesh(Mesh.Mesh(s.tessellate(0.5)))
    mesh.write(str(STL_OUT))
    m = Mesh.Mesh(str(STL_OUT))
    bb = m.BoundBox
    say("EXPORT: stl facets=%d bbox=(%.1f,%.1f,%.1f)-(%.1f,%.1f,%.1f)" % (
        m.CountFacets, bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax))

    compound.exportStep(str(STEP_OUT))
    head = open(STEP_OUT, "rb").read(20)
    say("EXPORT: step head=%r" % head)

    rd = App.newDocument("step_reimport_check")
    import Import
    Import.insert(str(STEP_OUT), rd.Name)
    rd.recompute()
    n = sum(1 for o in rd.Objects
            if hasattr(o, "Shape") and not o.Shape.isNull()
            and o.Shape.Volume > 0)
    App.closeDocument(rd.Name)
    say("EXPORT: step reimport solids=%d" % n)

    # manifest -- deterministic content, regenerated each run
    lines = [
        "# BIOBUZZ prototype export manifest",
        "",
        "**%s**" % LABEL,
        "",
        "Every artifact listed here is placeholder-grade prototype geometry",
        "for packaging review. NOT manufacturing data. All assumed values",
        "are UNVERIFIED or VENDOR-PENDING (see `docs/robot-parameters.md`).",
        "",
        "## Artifacts",
        "",
        "- `prototype_stl/master_robot_PROTOTYPE.stl` - %s" % LABEL,
        "- `prototype_step/master_robot_PROTOTYPE.step` - %s" % LABEL,
        "- `renders/master_{front,side,top,iso}.svg` - %s" % LABEL,
        "",
        "## Export set (%d solids, units mm)" % len(names),
        "",
        "Robot leaf solids from `cad/master_robot.FCStd` only. Excluded:",
        "`ENV_*`/`AXIS_*`/`REF_*` non-physical references, `VOL_*`",
        "packaging reserves, `TOOL_*` construction intermediates, and",
        "`App::Part`/`App::Origin` containers. Shapes are exported in",
        "world coordinates (carrier-chain placements applied).",
        "",
    ]
    lines += ["- `%s`" % n2 for n2 in names]
    lines += [
        "",
        "## Validation",
        "",
        "- STL facets: %d" % m.CountFacets,
        "- STL bbox: (%.1f, %.1f, %.1f) - (%.1f, %.1f, %.1f)" % (
            bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax),
        "- STEP re-import solids: %d" % n,
        "",
        "Regenerate with:",
        "",
        '    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" '
        "scripts\\freecad\\export_prototypes.py",
    ]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    say("EXPORT: manifest written (%d objects listed)" % len(names))

    ok = (m.CountFacets > 0 and head.startswith(b"ISO-10303-21")
          and n > 0 and len(objs) > 0)
    say("EXPORT: validation %s" % ("PASS" if ok else "FAIL"))
    App.closeDocument(doc.Name)
    RESULTS.write_text("\n".join(log) + "\n", encoding="utf-8")
    say("EXPORT: DONE")


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
