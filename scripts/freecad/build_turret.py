"""Build cad/turret/turret.FCStd -- sprint-03 turret tower + launcher.

Towers on the sprint-01 decks, turret deck, split lazy-susan races,
external yaw ring/pinion drive, and the rotating launcher plate
(flywheels, hood, nip backplate, camera) -- all expression-bound to the
Parameters sheet. Geometry is shared with the master via dt_turret.py,
so every solid name+bbox+volume matches its master counterpart (DET3).

Run:  freecadcmd.exe scripts/freecad/build_turret.py
"""
import sys
import traceback
from pathlib import Path

import FreeCAD as App
import Part  # noqa: F401  registers Part::* objects
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_build  # noqa: E402
import dt_turret  # noqa: E402

TARGET = dt_build.CAD_DIR / "turret" / "turret.FCStd"


def main():
    doc = App.newDocument("turret")
    ctx = dt_build.new_ctx()
    dt_turret.populate_turret(doc, ctx)
    dt_build.finish_doc(doc, ctx, TARGET, "turret")
    App.closeDocument(doc.Name)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
