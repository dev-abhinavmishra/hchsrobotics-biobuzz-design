"""Build cad/intake/intake.FCStd -- sprint-02 intake subsystem.

Frame context + cheek plates + rollers + float mounts + chain drive +
crossed belt + throat guard, all expression-bound to the Parameters
sheet. Geometry is shared with the master via dt_path.py, so every
solid name+bbox+volume matches its master counterpart (DET3).

Run:  freecadcmd.exe scripts/freecad/build_intake.py
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

TARGET = dt_build.CAD_DIR / "intake" / "intake.FCStd"


def main():
    doc = App.newDocument("intake")
    ctx = dt_build.new_ctx()
    dt_path.populate_intake(doc, ctx)
    dt_build.finish_doc(doc, ctx, TARGET, "intake")
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
