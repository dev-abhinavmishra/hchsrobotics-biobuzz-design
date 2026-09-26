"""Determinism probe: dump {name: bbox} for every solid in the three
sprint-02 files, write cad/archive/_det_sigs_<tag>.json.
Run: freecadcmd.exe scripts/freecad/sig_dump.py <tag>
"""
import json
import sys
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
TAG = sys.argv[-1] if len(sys.argv) > 1 else "run"
FILES = {
    "master": ROOT / "cad" / "master_robot.FCStd",
    "intake": ROOT / "cad" / "intake" / "intake_concept_v01.FCStd",
    "transfer": ROOT / "cad" / "transfer" / "transfer_concept_v01.FCStd",
}
out = {}
for tag, p in FILES.items():
    doc = App.openDocument(str(p))
    doc.recompute()
    cur = {}
    for o in doc.Objects:
        try:
            s = o.Shape.copy()
            s.Placement = o.getGlobalPlacement()
            if s and s.Volume > 0:
                b = s.BoundBox
                cur[o.Name] = [round(b.XMin, 3), round(b.YMin, 3),
                               round(b.ZMin, 3), round(b.XMax, 3),
                               round(b.YMax, 3), round(b.ZMax, 3),
                               round(s.Volume, 3)]
        except Exception:
            pass
    out[tag] = cur
    App.closeDocument(doc.Name)
dst = ROOT / "cad" / "archive" / ("_det_sigs_%s.json" % TAG)
dst.write_text(json.dumps(out, sort_keys=True, indent=1),
               encoding="utf-8")
print("SIGDUMP: %s -> %s" % (TAG, dst.name))
