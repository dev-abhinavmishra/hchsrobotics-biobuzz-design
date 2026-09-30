import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
for n in ("NUT_LW_0","BOLT_LW_0","NUT_LW_0_BLK","NUT_LW_0_BORE"):
    o=doc.getObject(n)
    if o:
        print(n, o.Placement.Base if hasattr(o,"Placement") else "?")
