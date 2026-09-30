import sys, FreeCAD as App
gold = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\turret.FCStd")
new = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\turret\turret.FCStd")
gd={o.Name:o for o in gold.Objects}; nd={o.Name:o for o in new.Objects}
out=[]
for n in sorted(set(gd)&set(nd)):
    g,o=gd[n],nd[n]
    if not (hasattr(g,"Shape") and hasattr(o,"Shape")): continue
    try:
        gs,os=g.Shape,o.Shape
        if not gs.Solids or not os.Solids: continue
        gb,ob=gs.BoundBox,os.BoundBox
        dv=abs(gs.Volume-os.Volume)
        tb=[gb.XMin,gb.XMax,gb.YMin,gb.YMax,gb.ZMin,gb.ZMax]
        db=[ob.XMin,ob.XMax,ob.YMin,ob.YMax,ob.ZMin,ob.ZMax]
        if dv>0.5 or any(abs(a-b)>0.05 for a,b in zip(tb,db)):
            out.append((n,dv,[round(a-b,2) for a,b in zip(tb,db)]))
    except Exception as e: pass
for r in out: print(r[0],"dV=%.1f"%r[1],r[2])
