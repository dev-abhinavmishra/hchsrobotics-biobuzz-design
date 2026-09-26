"""Build cad/master_robot_view.FCStd - a GUI-styled copy of the master.

The build pipeline runs headless (freecadcmd), so master_robot.FCStd
stores no view state. Opened raw it can look broken: the camera may sit
inside an opaque ENV_* box (black viewport), and Fit All zooms out to
REF_* field markers ~1.2 m away, shrinking the robot to a speck.

This script copies the FCStd archive and injects a GuiDocument.xml:
  - ENV_*/VOL_*/REF_*/Origin view providers -> Visibility false
  - subsystem solids -> ShapeColor matching exports/renders palette
  - orthographic isometric camera fitted to the robot

The same GuiDocument.xml is also injected into master_robot.FCStd in
place (view data only; Document.xml and all Shape.brp geometry are
byte-identical), so a plain double-click on the managed file opens the
styled robot as well. Re-run after any rebuild to restore view state.

Run:  freecadcmd.exe scripts/freecad/make_view_copy.py
"""
import sys
import traceback
import zipfile
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
TARGETS = (
    (ROOT / "cad" / "master_robot.FCStd",
     ROOT / "cad" / "master_robot_view.FCStd"),
    (ROOT / "cad" / "drivebase" / "drivebase_concept_v01.FCStd",
     ROOT / "cad" / "drivebase" / "drivebase_concept_v01_view.FCStd"),
    (ROOT / "cad" / "intake" / "intake_concept_v01.FCStd",
     ROOT / "cad" / "intake" / "intake_concept_v01_view.FCStd"),
    (ROOT / "cad" / "transfer" / "transfer_concept_v01.FCStd",
     ROOT / "cad" / "transfer" / "transfer_concept_v01_view.FCStd"),
)

HIDE_PREFIX = ("ENV_", "VOL_", "REF_", "TOOL_")

SUBSYS = (
    (("FRAME_", "RAIL_", "BELLY_PAN", "REAR_DECK"), "#8b9199"),
    (("WHEEL_", "ROLLER_"), "#3a3a40"),
    (("SHAFT_", "BEARING_", "MOUNT_MOTOR_"), "#b8bfc8"),
    (("MOTOR_",), "#d9a520"),
    (("BATTERY",), "#2f9e5f"),
    (("ELECTRONICS", "ELEC_RAIL"), "#e8890c"),
    (("INTAKE_", "PIVOT_MOUNT", "MECH_INTAKE", "MECH_ROLLER"),
     "#2f6fd6"),
    (("CHANNEL_", "DIVERTER_", "MECH_CHANNEL", "MECH_DIVERTER"), "#2aa3a3"),
    (("MECH_SHOOTER", "MECH_FLYWHEEL", "STUB_SHAFT", "POST_SHOOTER",
      "SHOOTER_FLOOR", "SHOOTER_SIDE"), "#c23b3b"),
    (("MECH_LIFTER", "MECH_STAGE", "MECH_CARRIAGE", "MECH_CRADLE",
      "CRADLE_LIP", "STAGE_GUIDE", "LIFTER_BASE", "LIFTER_PED"),
     "#8a5fc0"),
)

# orthographic isometric camera, az=45 el=35.264, fitted to the robot
CAMERA = ("OrthographicCamera {&#10;"
          "  viewportMapping ADJUST_CAMERA&#10;"
          "  position 520 520 520&#10;"
          "  orientation 0.4247082 0.17591992 0.33985114 0.82047319&#10;"
          "  nearDistance 1&#10;"
          "  farDistance 6000&#10;"
          "  aspectRatio 1&#10;"
          "  focalDistance 900&#10;"
          "  height 780&#10;&#10;}&#10;")


def color_uint(hex_color):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return (r << 24) | (g << 16) | (b << 8) | 0xFF


def color_for(name):
    for prefixes, c in SUBSYS:
        if name.startswith(prefixes):
            return c
    return None


def view_provider(name, hidden, color_hex):
    props = ['<Property name="Visibility" type="App::PropertyBool" '
             'status="1"><Bool value="%s"/></Property>'
             % ("false" if hidden else "true")]
    if color_hex:
        props.append('<Property name="ShapeColor" '
                     'type="App::PropertyColor" status="1">'
                     '<PropertyColor value="%d"/></Property>'
                     % color_uint(color_hex))
        props.append('<Property name="DisplayMode" '
                     'type="App::PropertyEnumeration" status="1">'
                     '<Integer value="1"/></Property>')
    return ('<ViewProvider name="%s" expanded="0" treeRank="-1">'
            '<Properties Count="%d" TransientCount="0">%s</Properties>'
            '</ViewProvider>' % (name, len(props), "".join(props)))


def build_gui_xml(doc):
    vps = []
    hidden = colored = 0
    for o in doc.Objects:
        hide = o.Name.startswith(HIDE_PREFIX) or o.TypeId == "App::Origin"
        col = None if hide else color_for(o.Name)
        if hide:
            hidden += 1
        if col:
            colored += 1
        vps.append(view_provider(o.Name, hide, col))
    gui = ("<?xml version='1.0' encoding='utf-8'?>\n"
           "<Document SchemaVersion=\"1\">\n"
           "    <ViewProviderData Count=\"%d\">" % len(vps)
           + "".join(vps)
           + "    </ViewProviderData>\n"
           "    <Camera settings=\"%s\"/>\n"
           "</Document>\n" % CAMERA)
    return gui, hidden, colored


def main():
    for src, dst in TARGETS:
        doc = App.openDocument(str(src))
        gui, hidden, colored = build_gui_xml(doc)
        n = len(doc.Objects)
        App.closeDocument(doc.Name)

        with zipfile.ZipFile(str(src)) as zin:
            entries = [(i, zin.read(i.filename)) for i in zin.infolist()]
        for target in (src, dst):
            with zipfile.ZipFile(str(target), "w",
                                 zipfile.ZIP_DEFLATED) as zout:
                for info, data in entries:
                    if info.filename == "GuiDocument.xml":
                        continue
                    zout.writestr(info.filename, data)
                zout.writestr("GuiDocument.xml", gui)
        print("VIEWCOPY: %d objects, %d hidden, %d colored -> %s + styled %s"
              % (n, hidden, colored, dst.name, src.name))
        sys.stdout.flush()


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
