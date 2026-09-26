"""Export STEP files for the sprint-01 overhaul CAD set.

  exports/step/parts/<solid>.step        - one STEP per exportable solid
  exports/step/subassembly/<group>.step  - GRP_* containers + the two
                                         subsystem documents as compounds
  exports/step/master_robot.step         - full master assembly

Every shape is globalized to world coordinates before export.
Non-physical references (ENV_*, TOOL_*, App::Part/Origin) are excluded.

Run:  freecadcmd.exe scripts/freecad/export_step.py
"""
import json
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad"
STEP = ROOT / "exports" / "step"
MASTER = CAD / "master_robot.FCStd"
SUBSYS = {
    "drivebase": CAD / "drivebase" / "drivebase.FCStd",
    "electronics": CAD / "electronics" / "electronics.FCStd",
}

EXCLUDE_PREFIX = ("ENV_", "TOOL_", "AXIS_", "REF_", "VOL_")
EXCLUDE_TYPES = ("App::Part", "App::Origin")


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


def global_shape(o):
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    return s


def export_step(shapes, dst):
    Part.makeCompound(shapes).exportStep(str(dst))


def top_group(o):
    p = o.getParentGeoFeatureGroup()
    top = None
    while p is not None:
        if p.Name.startswith("GRP_"):
            top = p
        p = p.getParentGeoFeatureGroup()
    return top


def main():
    (STEP / "parts").mkdir(parents=True, exist_ok=True)
    (STEP / "subassembly").mkdir(parents=True, exist_ok=True)
    for stale in (STEP / "parts").glob("*.step"):
        stale.unlink()
    for stale in (STEP / "subassembly").glob("*.step"):
        stale.unlink()
    report = {"parts": 0, "subassemblies": [], "master_solids": 0,
              "master_step_reimport": 0, "files": []}

    doc = App.openDocument(str(MASTER))
    doc.recompute()
    objs = exportable(doc)
    # per-part files
    for o in objs:
        dst = STEP / "parts" / ("%s.step" % o.Name)
        export_step([global_shape(o)], dst)
        report["parts"] += 1
    # subassembly compounds: GRP_* containers in the master
    groups = [o for o in doc.Objects
              if o.TypeId == "App::Part" and o.Name.startswith("GRP_")]
    for g in groups:
        leaves = [x for x in exportable(doc)
                  if top_group(x) is g]
        if leaves:
            dst = STEP / "subassembly" / ("%s.step" % g.Name)
            export_step([global_shape(x) for x in leaves], dst)
            report["subassemblies"].append({g.Name: len(leaves)})
    # full master
    mstep = STEP / "master_robot.step"
    export_step([global_shape(o) for o in objs], mstep)
    report["master_solids"] = len(objs)
    App.closeDocument(doc.Name)

    # subsystem documents as their own subassembly files
    for name, path in SUBSYS.items():
        d = App.openDocument(str(path))
        d.recompute()
        sobjs = exportable(d)
        export_step([global_shape(o) for o in sobjs],
                    STEP / "subassembly" / ("%s.step" % name))
        report["subassemblies"].append({name: len(sobjs)})
        App.closeDocument(d.Name)

    # validate: master STEP re-import
    rd = App.newDocument("step_reimport")
    import Import
    Import.insert(str(mstep), rd.Name)
    rd.recompute()
    report["master_step_reimport"] = sum(
        1 for o in rd.Objects
        if hasattr(o, "Shape") and not o.Shape.isNull()
        and o.Shape.Volume > 0)
    App.closeDocument(rd.Name)

    head = open(mstep, "rb").read(20)
    assert head.startswith(b"ISO-10303-21"), "STEP header bad"
    report["files"] = sorted(p.name for p in STEP.rglob("*.step"))
    (STEP / "export_step_report.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    print("STEP parts=%d subassemblies=%s master=%d reimport=%d" % (
        report["parts"], report["subassemblies"],
        report["master_solids"], report["master_step_reimport"]))


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
