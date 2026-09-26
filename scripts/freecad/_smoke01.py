"""Minimal dt_build smoke test: populate drivebase in a headless doc."""
import sys, os, traceback
sys.path.insert(0, r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad")
import FreeCAD as App

try:
    import dt_build
    doc = App.newDocument("smoke")
    ctx = dt_build.new_ctx()
    dt_build.populate_drivebase(doc, ctx)
    doc.recompute(None, True, True)
    names = [o.Name for o in doc.Objects]
    solids = ctx["solids"]
    print("OBJECTS:", len(names))
    print("SOLIDS:", len(solids), "JOINTS:", len(ctx["joints"]),
          "FACES:", len(ctx["faces"]), "EMBEDS:", len(ctx["embeds"]),
          "JOURNALS:", len(ctx["journals"]), "BOM:", len(ctx["bom"]))
    # shape validity + bbox audit on named solids
    bad, nulls = [], []
    for nm in solids:
        o = doc.getObject(nm)
        if o is None:
            nulls.append(nm); continue
        try:
            sh = o.Shape
            if sh is None or sh.isNull():
                nulls.append(nm); continue
            if not sh.isValid():
                bad.append(nm)
        except Exception as e:
            bad.append("%s(EXC %s)" % (nm, e))
    print("NULL_SHAPES:", nulls[:20])
    print("INVALID_SHAPES:", bad[:20])
    # bbox of a few key members
    for nm in ("FRAME_RAIL_L", "FRAME_RAIL_R", "BELLY_PAN",
               "WHEEL_FL_ASSY", "MOTOR_FL", "MPLATE_L",
               "ODO_BLK_LAT_L", "ENV_START"):
        o = doc.getObject(nm)
        if o is not None and hasattr(o, "Shape"):
            b = o.Shape.BoundBox
            print("BB %s: X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]" % (
                nm, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
        else:
            print("BB %s: MISSING" % nm)
    doc.saveAs(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_smoke01.FCStd")
    print("SAVED")
except Exception:
    traceback.print_exc()
    sys.exit(2)
