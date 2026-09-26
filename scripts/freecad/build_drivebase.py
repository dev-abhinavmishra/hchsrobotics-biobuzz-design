"""Build cad/drivebase/drivebase.FCStd -- sprint-01 drivebase subsystem.

Frame + drivetrain + odometry pods + deck, all expression-bound to the
Parameters sheet. Geometry is shared with the master via dt_build.py,
so every solid name+bbox+volume matches its master counterpart (DET3).

Run:  freecadcmd.exe scripts/freecad/build_drivebase.py
"""
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401  registers Part::* objects
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_build  # noqa: E402

TARGET = dt_build.CAD_DIR / "drivebase" / "drivebase.FCStd"


def main():
    doc = App.newDocument("drivebase")
    ctx = dt_build.new_ctx()
    dt_build.populate_drivebase(doc, ctx)
    dt_build.finish_doc(doc, ctx, TARGET, "drivebase")
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
