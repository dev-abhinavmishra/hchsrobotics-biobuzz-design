import sys, FreeCAD as App
sys.path.insert(0, r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad")
doc = App.newDocument("t")
import partkit as pk
pk.hex_nut(doc, "NT", "NT", "UNVERIFIED", "8.08", "3.2", "4",
           {"Placement.Base.x": "0", "Placement.Base.y": "0",
            "Placement.Base.z": "0"}, "Z")
pk.hex_nut(doc, "NY", "NY", "UNVERIFIED", "8.08", "3.2", "4",
           {"Placement.Base.x": "0", "Placement.Base.y": "0",
            "Placement.Base.z": "0"}, "Y")
doc.recompute()
for n in ("NT", "NY"):
    b = doc.getObject(n).Shape.BoundBox
    print(n, [round(v,3) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)])
