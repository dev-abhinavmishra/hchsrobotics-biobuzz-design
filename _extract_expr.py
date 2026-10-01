import FreeCAD as App
g = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\lift.FCStd")
n = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\lift\lift.FCStd")
names = [o.Name for o in g.Objects if "CHUTE" in o.Name or "WINCH" in o.Name
         or "LIFT_WINCH" in o.Name or "CHT" in o.Name]
for nm in sorted(names):
    for d,t in ((g,"G"),(n,"N")):
        o=d.getObject(nm)
        if o:
            ee=getattr(o,"ExpressionEngine",None)
            s=o.Shape
            b=s.BoundBox if s else None
            print(nm,t,[str(e) for e in (ee or [])],
                  [round(v,1) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)] if b else None)
