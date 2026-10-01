import FreeCAD as App
g = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\turret.FCStd")
n = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\turret\turret.FCStd")
for nm in ("BOLT_FM_L0","BOLT_FM_L1","BOLT_FM_L2","BOLT_FM_L3","BOLT_FBRG_L0","BOLT_FBRG_L1"):
    for d,tag in ((g,"G"),(n,"N")):
        o=d.getObject(nm)
        if o:
            s=o.Shape.copy(); s.Placement=o.getGlobalPlacement()
            b=s.BoundBox
            cx=(b.XMin+b.XMax)/2; cy=(b.YMin+b.YMax)/2; cz=(b.ZMin+b.ZMax)/2
            print(nm,tag,round(cx,1),round(cy,1),round(cz,1))
