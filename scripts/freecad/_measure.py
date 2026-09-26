import sys
sys.path.insert(0, r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad")
import FreeCAD as App
import dt_build
doc = App.newDocument("m")
ctx = dt_build.new_ctx()
dt_build.populate_master(doc, ctx)
doc.recompute(None, True, True)
out = open(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_m.txt", "w")
for n in ("CLIP_0", "CLIP_1", "CLIP_2", "CLIP_3", "BATTERY",
          "HUB_CTRL", "SWITCH_BRKT", "STANDOFF_2", "STANDOFF_3",
          "MOTOR_FR", "ELEC_SHELF", "WIRE_MTR_FR"):
    o = doc.getObject(n)
    if o and hasattr(o, "Shape") and not o.Shape.isNull():
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        b = s.BoundBox
        out.write("%-14s X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]\n"
                  % (n, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
out.close()
