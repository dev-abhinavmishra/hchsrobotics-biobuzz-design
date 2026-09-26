"""Build cad/electronics/electronics.FCStd -- sprint-01 electronics.

Battery + straps, REV control/expansion hubs, electronics shelf with
standoffs, main switch bracket, sprint-01 wiring subset. The frame
context (rails + belly pan + brackets) is rebuilt by the same dt_build
functions as the master, so shared solids match byte-for-bbox (DET3).

Run:  freecadcmd.exe scripts/freecad/build_electronics.py
"""
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401
import Spreadsheet  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_build  # noqa: E402

TARGET = dt_build.CAD_DIR / "electronics" / "electronics.FCStd"


def main():
    doc = App.newDocument("electronics")
    ctx = dt_build.new_ctx()
    dt_build.populate_electronics(doc, ctx)
    dt_build.finish_doc(doc, ctx, TARGET, "electronics")
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
