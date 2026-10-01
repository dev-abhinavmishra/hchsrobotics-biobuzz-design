import FreeCAD as App
which = "turret"
gold = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\%s.FCStd" % which)
new = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\%s\%s.FCStd" % (which, which))
gd={o.Name:o for o in gold.Objects}; nd={o.Name:o for o in new.Objects}
print("ONLY_GOLD:", [n for n in sorted(set(gd)-set(nd))])
print("ONLY_NEW:", [n for n in sorted(set(nd)-set(gd))])
for n in sorted(set(gd)&set(nd)):
    g,o=gd[n],nd[n]
    ge={k:v for k,v in getattr(g,"ExpressionEngine",[])}
    oe={k:v for k,v in getattr(o,"ExpressionEngine",[])}
    if ge!=oe and not n.startswith("TOOL_NUT"):
        ch=[(k,ge.get(k),oe.get(k)) for k in sorted(set(ge)|set(oe)) if ge.get(k)!=oe.get(k)]
        print("  %s: %s"%(n,ch))
    try:
        gs,os_=g.Shape,o.Shape
        if gs.Solids and os_.Solids:
            gb,ob=gs.BoundBox,os_.BoundBox
            if abs(gs.Volume-os_.Volume)>0.5 or any(abs(a-b)>0.06 for a,b in zip(
                (gb.XMin,gb.XMax,gb.YMin,gb.YMax,gb.ZMin,gb.ZMax),
                (ob.XMin,ob.XMax,ob.YMin,ob.YMax,ob.ZMin,ob.ZMax))):
                if "NUT_" not in n and not n.startswith("GRP_"):
                    print("  GEO %s dV=%.1f" % (n, abs(gs.Volume-os_.Volume)))
    except Exception: pass
print("DONE")
