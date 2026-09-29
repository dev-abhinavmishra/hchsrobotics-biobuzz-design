"""Export STEP files for the sprint-01 overhaul CAD set.

  exports/step/parts/<solid>.step        - one STEP per exportable solid
  exports/step/subassembly/<group>.step  - GRP_* containers + the two
                                         subsystem documents as compounds
  exports/step/master_robot.step         - full master assembly

Every shape is globalized to world coordinates. STEP PRODUCT records
carry the FreeCAD object names: parts export as
``Import.export([named_object], path)`` so downstream CAD sees real
part names, not 'Part__FeatureNNN'. Non-physical references (ENV_*,
TOOL_*, App::Part/Origin) are excluded.

Run:  freecadcmd.exe scripts/freecad/export_step.py
"""
import json
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Import
import Part  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad"
STEP = ROOT / "exports" / "step"
MASTER = CAD / "master_robot.FCStd"
SUBSYS = {
    "drivebase": CAD / "drivebase" / "drivebase.FCStd",
    "electronics": CAD / "electronics" / "electronics.FCStd",
    "intake": CAD / "intake" / "intake.FCStd",
    "hopper": CAD / "hopper" / "hopper.FCStd",
    "turret": CAD / "turret" / "turret.FCStd",
    "lift": CAD / "lift" / "lift.FCStd",
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


def world_object(tmpdoc, name, shape):
    """Named Part::Feature in tmpdoc: the exported PRODUCT record
    carries `name`; the brep already sits in world coordinates."""
    dup = tmpdoc.addObject("Part::Feature", name)
    dup.Label = name
    dup.Placement = App.Placement()
    dup.Shape = shape
    return dup


def world_parts(o):
    """(name, shape) pairs for export: the brep is transformed to
    world coordinates (carrier children included). Multi-solid shapes
    (wire sweeps made of disconnected segments) decompose into named
    sub-products so nothing reimports as Part__FeatureNNN."""
    s = o.Shape.copy()
    # getGlobalPlacement() is the effective transform that puts the
    # object's local shape into world coords (it already composes the
    # object's own placement + parents). Setting it on the shape and
    # running removeSplitter() bakes the Location into the brep
    # vertices -- a bare Placement on the temp feature is dropped by
    # the STEP writer (carrier children exported at local coords),
    # transformGeometry() corrupts shapes with nested Locations.
    s.Placement = o.getGlobalPlacement()
    s = s.removeSplitter()
    s.Placement = App.Placement()
    sols = s.Solids
    if len(sols) > 1:
        return [("%s_%d" % (o.Name, i), so)
                for i, so in enumerate(sols)]
    return [(o.Name, s)]


def top_group(o):
    p = o.getParentGeoFeatureGroup()
    top = None
    while p is not None:
        if p.Name.startswith("GRP_"):
            top = p
        p = p.getParentGeoFeatureGroup()
    return top


def export_objs(objs, tmpdoc, dst):
    world = [world_object(tmpdoc, nm, sh)
             for o in objs for nm, sh in world_parts(o)]
    Import.export(world, str(dst))
    for w in world:
        tmpdoc.removeObject(w.Name)


def main():
    (STEP / "parts").mkdir(parents=True, exist_ok=True)
    (STEP / "subassembly").mkdir(parents=True, exist_ok=True)
    for stale in (STEP / "parts").glob("*.step"):
        stale.unlink()
    for stale in (STEP / "subassembly").glob("*.step"):
        stale.unlink()
    report = {"parts": 0, "subassemblies": [], "master_solids": 0,
              "master_step_reimport": 0, "files": []}

    tmp = App.newDocument("master_robot")
    doc = App.openDocument(str(MASTER))
    doc.recompute()
    objs = exportable(doc)
    # per-part files
    for o in objs:
        dst = STEP / "parts" / ("%s.step" % o.Name)
        export_objs([o], tmp, dst)
        report["parts"] += 1
    # subassembly compounds: GRP_* containers in the master
    groups = [o for o in doc.Objects
              if o.TypeId == "App::Part" and o.Name.startswith("GRP_")]
    for g in groups:
        leaves = [x for x in objs if top_group(x) is g]
        if leaves:
            dst = STEP / "subassembly" / ("%s.step" % g.Name)
            export_objs(leaves, tmp, dst)
            report["subassemblies"].append({g.Name: len(leaves)})
    # full master
    mstep = STEP / "master_robot.step"
    export_objs(objs, tmp, mstep)
    report["master_solids"] = len(objs)
    App.closeDocument(doc.Name)

    # subsystem documents as their own subassembly files
    for name, path in SUBSYS.items():
        d = App.openDocument(str(path))
        d.recompute()
        sobjs = exportable(d)
        export_objs(sobjs, tmp,
                    STEP / "subassembly" / ("%s.step" % name))
        report["subassemblies"].append({name: len(sobjs)})
        App.closeDocument(d.Name)
    App.closeDocument(tmp.Name)

    # validate: master STEP re-import (solids + names)
    rd = App.newDocument("step_reimport")
    Import.insert(str(mstep), rd.Name)
    rd.recompute()
    solids = [o for o in rd.Objects
              if hasattr(o, "Shape") and not o.Shape.isNull()
              and o.Shape.Volume > 0]
    report["master_step_reimport"] = len(solids)
    report["master_step_named"] = sum(
        1 for o in solids if not o.Label.startswith(
            ("Open CASCADE", "Part__")))
    App.closeDocument(rd.Name)

    head = open(mstep, "rb").read(20)
    assert head.startswith(b"ISO-10303-21"), "STEP header bad"
    report["files"] = sorted(p.name for p in STEP.rglob("*.step"))
    (STEP / "export_step_report.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    print("STEP parts=%d subassemblies=%s master=%d reimport=%d named=%d"
          % (report["parts"], report["subassemblies"],
             report["master_solids"], report["master_step_reimport"],
             report["master_step_named"]))


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
