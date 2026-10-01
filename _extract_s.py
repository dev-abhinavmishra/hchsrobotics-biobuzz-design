import FreeCAD as App, re
g = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\lift.FCStd")
for o in g.Objects:
    if re.match(r"TOOL_SCRW_CHL_\d_\d_HD", o.Name):
        ee = dict(o.ExpressionEngine)
        print(o.Name, ee)
