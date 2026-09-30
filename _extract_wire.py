import FreeCAD as App, re
g = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\lift.FCStd")
for base in ("TOOL_ROPE_A","TOOL_WIRE_TILT_SV","TOOL_WIRE_WINCH"):
    segs = sorted((o.Name,o) for o in g.Objects
                  if re.match(base+r"_S\d+$", o.Name))
    print("===",base,len(segs))
    for nm,o in segs:
        s=o.Shape.copy(); s.Placement=o.getGlobalPlacement()
        b=s.BoundBox
        print(nm,[round(v,1) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)])
