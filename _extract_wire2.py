import FreeCAD as App, re
g = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\lift.FCStd")
for base in ("TOOL_WIRE_TILT_SV","TOOL_WIRE_WINCH","TOOL_TOOL_ROPE_A"):
    segs = sorted((o.Name,o) for o in g.Objects
                  if re.match(base+r"_S\d+$", o.Name))
    print("===",base,len(segs))
    for nm,o in segs:
        gp = o.getGlobalPlacement()
        h = getattr(o, "Height", None)
        # cylinder local +Z = axis dir
        d = gp.Rotation.multVec(App.Vector(0,0,1))
        a = gp.Base; b = a + d*float(h.Value if hasattr(h,'Value') else h or 0)
        print(nm, "A", tuple(round(v,1) for v in a), "B", tuple(round(v,1) for v in b))
