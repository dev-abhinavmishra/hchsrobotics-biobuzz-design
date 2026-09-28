"""Build cad/hopper/hopper.FCStd -- sprint-02 hopper/feed subsystem.

Frame context + incline floor/walls + agitator + feed wheel + column +
gate + diverter + sensor + interface datums, all expression-bound to
the Parameters sheet. Geometry is shared with the master via
dt_path.py, so every solid name+bbox+volume matches its master
counterpart (DET3).

Run:  freecadcmd.exe scripts/freecad/build_hopper.py
"""
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401  registers Part::* objects
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_build  # noqa: E402
import dt_path  # noqa: E402

TARGET = dt_build.CAD_DIR / "hopper" / "hopper.FCStd"


def main():
    doc = App.newDocument("hopper")
    ctx = dt_build.new_ctx()
    dt_path.populate_hopper(doc, ctx)
    dt_build.finish_doc(doc, ctx, TARGET, "hopper")
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
