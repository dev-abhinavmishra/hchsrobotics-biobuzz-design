"""FreeCAD GUI companion for viewing the BIOBUZZ master assembly.

Run inside an open FreeCAD session:
    Macro -> Macros -> Create -> paste this file -> Run
(FreeCAD does not execute .py files passed as command-line arguments;
see scripts/freecad/make_view_copy.py for the persistent alternative --
it bakes this same styling into the FCStd's GuiDocument.xml so a plain
double-click opens the styled model.)

The build pipeline is headless (freecadcmd), so the FCStd carries no
view state: a plain open can show a black/empty viewport (camera inside
an opaque ENV_* envelope solid) or a tiny robot (REF_* field markers sit
~1.2 m away, so Fit All zooms far out). This script hides the
non-physical volumes/markers, colors each subsystem (same palette as
exports/renders/*.svg), frames an isometric view of the robot, writes
shaded PNG snapshots to exports/renders/, and saves a styled viewer copy
at cad/master_robot_view.FCStd for future double-click opens.
The managed master_robot.FCStd itself is not modified.
"""
import time
import traceback
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "cad" / "master_robot.FCStd"
VIEW_COPY = ROOT / "cad" / "master_robot_view.FCStd"
OUT = ROOT / "exports" / "renders"
LOG = OUT / "view_log.txt"

HIDE_PREFIX = ("ENV_", "VOL_", "REF_")

SUBSYS = (
    (("WHEEL_", "ROLLER_"), "#4a4a52"),
    (("BATTERY",), "#2f9e5f"),
    (("ELECTRONICS", "ELEC_RAIL"), "#e8890c"),
    (("MECH_INTAKE", "PIVOT_MOUNT"), "#2f6fd6"),
    (("MECH_CHANNEL", "MECH_DIVERTER", "DIVERTER_HORN"), "#2aa3a3"),
    (("MECH_SHOOTER", "MECH_FLYWHEEL", "STUB_SHAFT"), "#c23b3b"),
    (("MECH_LIFTER", "MECH_STAGE", "MECH_CARRIAGE", "MECH_CRADLE",
      "CRADLE_LIP", "STAGE_GUIDE"), "#8a5fc0"),
)

_log_lines = []


def log(msg):
    line = "VIEW: %s" % msg
    print(line)
    _log_lines.append(line)
    try:
        LOG.write_text("\n".join(_log_lines) + "\n", encoding="utf-8")
    except Exception:
        pass


def hexrgb(h):
    return (int(h[1:3], 16) / 255.0, int(h[3:5], 16) / 255.0,
            int(h[5:7], 16) / 255.0)


def color_for(name):
    for prefixes, c in SUBSYS:
        if name.startswith(prefixes):
            return hexrgb(c)
    return None


def wait_doc():
    """The macro may run before the FCStd is fully attached to the GUI;
    poll briefly for an active document with view providers."""
    for _ in range(60):
        doc = App.ActiveDocument
        if doc is not None and doc.Name == "master_robot":
            if Gui.ActiveDocument is not None:
                return doc
        elif doc is not None:
            return doc
        time.sleep(0.5)
    return App.ActiveDocument or App.openDocument(str(MASTER))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = wait_doc()
    log("document=%s objects=%d" % (doc.Name, len(doc.Objects)))

    hidden = colored = 0
    for o in doc.Objects:
        vo = getattr(o, "ViewObject", None)
        if vo is None:
            continue
        if o.Name.startswith(HIDE_PREFIX):
            try:
                vo.Visibility = False
                hidden += 1
            except Exception:
                pass
            continue
        rgb = color_for(o.Name)
        if rgb is not None:
            try:
                vo.ShapeColor = rgb
                colored += 1
            except Exception:
                pass
    log("hid %d env/vol/ref objects, colored %d subsystem solids"
        % (hidden, colored))

    Gui.updateGui()
    view = Gui.ActiveDocument.ActiveView

    for name, meth in (("front", "viewFront"), ("side", "viewRight"),
                       ("top", "viewTop"), ("iso", "viewIsometric")):
        try:
            getattr(view, meth)()
            Gui.SendMsgToActiveView("ViewFit")
            Gui.updateGui()
            time.sleep(0.4)
            view.saveImage(str(OUT / ("master_%s.png" % name)),
                           1600, 1100, "White")
            log("wrote master_%s.png" % name)
        except Exception as exc:
            log("png %s failed: %s" % (name, exc))

    view.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    Gui.updateGui()

    try:
        doc.saveAs(str(VIEW_COPY))
        log("styled copy -> %s" % VIEW_COPY)
    except Exception as exc:
        log("saveAs skipped: %s" % exc)
    log("DONE")


try:
    main()
except Exception:
    _log_lines.append(traceback.format_exc())
    try:
        LOG.write_text("\n".join(_log_lines) + "\n", encoding="utf-8")
    except Exception:
        pass
    traceback.print_exc()
