import FreeCAD as App
from pathlib import Path
ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
m = App.openDocument(str(ROOT/"cad/master_robot.FCStd"))
for n in ("DECK_R","DECK_L","TOWER_L","TOWER_GUS_R3","NUT_GUD_R3_0",
          "BOLT_GUD_R3_0","BOLT_GUS_R3_0","NUT_GUS_R3_0",
          "BOLT_GUS_L0_0","BOLT_GUS_L0_1","BOLT_GUS_L0_2","BOLT_GUS_L0_3",
          "BOLT_CAP_L_0","BOLT_CAP_L_1","BOLT_CAP_L_2","BOLT_CAP_L_3",
          "BOLT_TWC_L_0","BOLT_TWC_L_1","BOLT_TWC_L_2","BOLT_TWC_L_3",
          "NUT_TWC_L_0","NUT_TWC_L_1","NUT_TWC_L_2","NUT_TWC_L_3",
          "NUT_LW_0","NUT_LRF_L1","FRAME_RAIL_L","FRAME_RAIL_R",
          "TOOL_TOWER_L_CAPCUT","TOOL_TOWER_L_PORT","TOOL_TOWER_L_SHELF"):
    o=m.getObject(n)
    if o is None or not hasattr(o,"Shape") or o.Shape.isNull():
        print("%-24s MISSING"%n); continue
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); b=s.BoundBox
    print("%-24s x %8.2f..%8.2f  y %8.2f..%8.2f  z %8.2f..%8.2f"%(
        n,b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))
# what's directly above NUT_GUD_R3_0: cast upward region occupancy
o=m.getObject("NUT_GUD_R3_0"); s=o.Shape.copy(); s.Placement=o.getGlobalPlacement()
b=s.BoundBox
import Part
probe=Part.makeBox(b.XLength,b.YLength,60,
                   App.Vector(b.XMin,b.YMin,b.ZMax))
hits=[]
for o in m.Objects:
    if not hasattr(o,"Shape") or o.Shape.isNull() or o.Shape.Volume<=0: continue
    if o.Name.startswith(("ENV_","TOOL_","AXIS_","REF_","VOL_")): continue
    try:
        c=s and probe.common(o.Shape)
    except Exception:
        continue
    try:
        if probe.common(o.Shape).Volume>0.2:
            hits.append(o.Name)
    except Exception: pass
print("above NUT_GUD_R3_0:",sorted(hits))
print("DONE")
