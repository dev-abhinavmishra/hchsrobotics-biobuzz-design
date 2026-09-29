"""Build cad/lift/lift.FCStd -- sprint-03 flower lift + load chute.

Cascade mast on the left rail top flange (base, guide posts, stop
collars, stage-1/2 slides, ties, pulleys), winch + dyneema rig,
cradle arm + tilt cup, and the two-leg load chute -- expression-bound
to the Parameters sheet. Geometry is shared with the master via
dt_lift.py, so every solid name+bbox+volume matches its master
counterpart (DET3).

Run:  freecadcmd.exe scripts/freecad/build_lift.py
"""
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401  registers Part::* objects
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_build  # noqa: E402
import dt_lift  # noqa: E402

TARGET = dt_build.CAD_DIR / "lift" / "lift.FCStd"


def main():
    doc = App.newDocument("lift")
    ctx = dt_build.new_ctx()
    dt_lift.populate_lift(doc, ctx)
    dt_build.finish_doc(doc, ctx, TARGET, "lift")
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
