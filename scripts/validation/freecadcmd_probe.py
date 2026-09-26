# freecadcmd_probe.py
# Smoke test for FreeCAD console mode. Exercises every API feature the
# BIOBUZZ build scripts rely on. Run:
#   "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\validation\freecadcmd_probe.py
# All output lines are prefixed PROBE: so results are easy to grep.

import os
import sys
import traceback

import FreeCAD as App
import Part

PROBE_TMP = os.path.join(os.environ.get("TEMP", "."), "freecadcmd_probe.FCStd")


def report(msg):
    print("PROBE: " + str(msg))


def main():
    report("FreeCAD version: " + ".".join(App.Version()[:3]))
    report("Units schema: " + str(App.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("UserSchema", -1)))

    # --- Document create / open / recompute / save ---
    doc = App.newDocument("ProbeDoc")
    report("newDocument OK")

    # --- Part solid on a Part::Feature ---
    box = doc.addObject("Part::Feature", "ProbeBox")
    box.Shape = Part.makeBox(10, 20, 30)
    doc.recompute()
    report("Part::Feature box OK, volume=%.1f mm^3" % box.Shape.Volume)

    # --- Custom properties ---
    box.addProperty("App::PropertyLength", "NominalLength", "Prototype", "UNVERIFIED test prop")
    box.NominalLength = 10.0
    box.addProperty("App::PropertyString", "DataStatus", "Prototype", "UNVERIFIED test str")
    box.DataStatus = "UNVERIFIED"
    report("custom properties OK")

    # --- Spreadsheet with alias + expression binding ---
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.set("A1", "param")
    sheet.set("B1", "value_mm")
    sheet.set("A2", "probe_width")
    sheet.set("B2", "20")
    sheet.setAlias("B2", "probe_width")
    doc.recompute()
    box.setExpression("NominalLength", "Parameters.probe_width")
    doc.recompute()
    report("spreadsheet alias + expression OK, NominalLength=%s" % box.NominalLength)

    # --- App::Part container with Origin ---
    part = doc.addObject("App::Part", "ProbePart")
    doc.recompute()
    origins = [o for o in part.Group if o.TypeId == "App::Origin"] if hasattr(part, "Group") else []
    report("App::Part OK, auto Origin children: %d" % len(origins))

    # --- Cylinder + placement ---
    cyl = doc.addObject("Part::Feature", "ProbeWheel")
    cyl.Shape = Part.makeCylinder(48, 25)
    cyl.Placement.Base = App.Vector(100, 0, 48)
    doc.recompute()
    report("cylinder + placement OK")

    # --- Save / reopen ---
    doc.saveAs(PROBE_TMP)
    App.closeDocument(doc.Name)
    report("saved %s (%d bytes)" % (PROBE_TMP, os.path.getsize(PROBE_TMP)))

    doc2 = App.openDocument(PROBE_TMP)
    names = [o.Name for o in doc2.Objects]
    report("reopened, objects=%s" % names)
    ok = "ProbeBox" in names and "Parameters" in names and "ProbePart" in names
    App.closeDocument(doc2.Name)
    os.remove(PROBE_TMP)
    report("RESULT: " + ("PASS" if ok else "FAIL"))


try:
    main()
except Exception:
    report("EXCEPTION:")
    traceback.print_exc()
    sys.exit(1)
