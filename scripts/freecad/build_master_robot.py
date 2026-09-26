"""Build cad/master_robot.FCStd -- BIOBUZZ robot (overhaul sprint-01).

The master is the union of the sprint-01 subsystem content, built by the
same dt_build.py builders the subsystem files use, so every same-named
solid matches its subsystem counterpart in name, bounding box and
volume (DET3 by construction).

Contents: goBILDA-pattern channel frame, mecanum drivetrain with real
bore/journal relationships, odometry pods, deck panels, electronics
tray, sprint-01 wiring subset, and the ENV_START 457.2mm cube.

Run:  freecadcmd.exe scripts/freecad/build_master_robot.py
"""
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401  registers Part::* objects
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_build  # noqa: E402

TARGET = dt_build.CAD_DIR / "master_robot.FCStd"


def main():
    doc = App.newDocument("master_robot")
    ctx = dt_build.new_ctx()
    dt_build.populate_master(doc, ctx)
    dt_build.finish_doc(doc, ctx, TARGET, "master")
    dt_build.write_exports_tables(ctx)
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
