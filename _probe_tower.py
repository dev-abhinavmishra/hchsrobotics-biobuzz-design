import FreeCAD as App, Part
from pathlib import Path
ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
m = App.openDocument(str(ROOT/"cad/master_robot.FCStd"))
o=m.getObject("TOWER_L"); s=o.Shape.copy(); s.Placement=o.getGlobalPlacement()
# vertical occupancy profile of TOWER_L cap band: for y 80..133 step 4
# probe columns x -175..0 z 241..244 (cap) and report which y bands have material
import math
print("cap-band occupancy (z 241.5..243.5):")
for y0 in range(80,133,4):
    pr=Part.makeBox(175,4,2,App.Vector(-175,y0,241.5))
    v=pr.common(s).Volume
    if v>0: print("  y %3d..%3d  vol=%.0f"%(y0,y0+4,v))
    else:   print("  y %3d..%3d  EMPTY"%(y0,y0+4))
print("leg-band occupancy (z 100..240) y bands:")
for y0 in range(80,133,4):
    pr=Part.makeBox(175,4,140,App.Vector(-175,y0,100))
    v=pr.common(s).Volume
    if v>0: print("  y %3d..%3d  vol=%.0f"%(y0,y0+4,v))
# x occupancy of the cap remnant y 81..101
print("cap remnant x profile (y81..101, z241.5..243.5):")
for x0 in range(-176,0,10):
    pr=Part.makeBox(10,20,2,App.Vector(x0,81,241.5))
    v=pr.common(s).Volume
    if v>0: print("  x %4d..%4d vol=%.0f"%(x0,x0+10,v))
print("DONE")
