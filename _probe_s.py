import FreeCAD as App, math
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
s17=App.Vector(-122,128.5,143); s16=App.Vector(-122.0,184.1,169.9)
for n in ("SCRW_CHL_1_0","SCRW_CHL_1_1","CHUTE_LIP_L2","CHUTE_LIP_R2"):
    o=doc.getObject(n)
    if o and hasattr(o,"Shape"):
        b=shape(o).BoundBox
        print(n,[round(v,1) for v in (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax)])
# distance from S17 center to screw axis (vertical line at screw xy)
o=doc.getObject("SCRW_CHL_1_0"); b=shape(o).BoundBox
cx=(b.XMin+b.XMax)/2; cy=(b.YMin+b.YMax)/2
print("screw xy",round(cx,2),round(cy,2),"horiz dist to S17:",
      round(math.hypot(cx+122,cy-128.5),2),"z span",round(b.ZMin,1),round(b.ZMax,1))
o=doc.getObject("SCRW_CHL_1_1"); b=shape(o).BoundBox
cx=(b.XMin+b.XMax)/2; cy=(b.YMin+b.YMax)/2
print("screw1 xy",round(cx,2),round(cy,2),"horiz dist to S17:",
      round(math.hypot(cx+122,cy-128.5),2),"z span",round(b.ZMin,1),round(b.ZMax,1),
      "to S16:",round(math.hypot(cx+122,cy-184.1),2))
