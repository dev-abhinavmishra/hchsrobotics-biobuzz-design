"""One-shot diagnostic: reproduce sprint-03 selfcheck failures with full lists."""
import json
import math
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
CAD = ROOT / "cad"
EXPORTS = ROOT / "exports"

d = App.openDocument(str(CAD / "master_robot.FCStd"))
d.recompute(None, True, True)
mmeta = json.loads((EXPORTS / "meta" / "master.json").read_text())

EXCLUDE_TYPES = {"Spreadsheet::Sheet"}
EXCLUDE_PREFIX = ("ENV_", "TOOL_")


def gshape(o):
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    return s


solids = [o for o in d.Objects
          if hasattr(o, "Shape") and not o.Shape.isNull()
          and o.Shape.Volume > 0
          and o.TypeId not in EXCLUDE_TYPES
          and not o.Name.startswith(EXCLUDE_PREFIX)]
print("solids:", len(solids))
gshapes = {o.Name: gshape(o) for o in solids}
shape_map = {o.Name: gshapes[o.Name] for o in solids
             if o.Name in set(mmeta["solids"])}

declared = set()
for coll in ("embeds", "faces", "journals", "contacts"):
    for a, b in mmeta[coll]:
        declared.add(tuple(sorted((a, b))))
for j in mmeta["joints"]:
    ms = j["members"] + j.get("bolts", []) + j.get("nuts", [])
    for i_ in range(len(ms)):
        for k_ in range(i_ + 1, len(ms)):
            declared.add(tuple(sorted((ms[i_], ms[k_]))))

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
            overlaps.append((round(com.Volume, 1), a, b))
overlaps.sort(reverse=True)
print("\n=== GEO2 undeclared overlaps: %d ===" % len(overlaps))
for v, a, b in overlaps:
    print("  %8.1f  %s <> %s" % (v, a, b))
