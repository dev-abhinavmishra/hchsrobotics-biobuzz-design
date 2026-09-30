import FreeCAD as App, json
from pathlib import Path
ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
m = App.openDocument(str(ROOT/"cad/master_robot.FCStd"))
mmeta = json.loads((ROOT/"exports/meta/master.json").read_text(encoding="utf-8"))
sm={}
def gs(n):
    if n not in sm:
        o=m.getObject(n)
        if o is None or not hasattr(o,"Shape") or o.Shape.isNull(): return None
        s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); sm[n]=s
    return sm[n]
for j in mmeta["joints"]:
    if j["id"] in ("lift_winch","tdeck_l","gusset_r3","rail_foot_l","rail_foot_r","s2_tie","cradle_arm","collar_l","collar_r","yaw_tray"):
        print(j["id"],"mems:",j["members"])
        print("   bolts:",j.get("bolts"),"nuts:",j.get("nuts"))
print("== nut distances to members ==")
JOINTS={j["id"]:j for j in mmeta["joints"]}
for jid,nuts in (("lift_winch",["NUT_LW_0","NUT_LW_1"]),
                 ("tdeck_l",["NUT_TWC_L_0","NUT_TWC_L_2"]),
                 ("gusset_r3",["NUT_GUD_R3_0"]),
                 ("rail_foot_l",["NUT_LRF_L1"]),
                 ("rail_foot_r",["NUT_LRF_R0"])):
    j=JOINTS[jid]
    for nn in nuts:
        ns=gs(nn)
        if ns is None: print(nn,"MISSING"); continue
        for mem in j["members"]:
            ms=gs(mem)
            if ms is None: continue
            try:
                d=ns.distToShape(ms)
                print("%-14s -> %-18s dist=%.3f"%(nn,mem,d[0]))
            except Exception as e:
                print(nn,mem,"ERR",e)
# faces near the nuts -- find closest face of each member below nut
print("== nearest face analysis ==")
import math
for nn,mem in (("NUT_LW_0","FRAME_RAIL_L"),("NUT_TWC_L_0","TOWER_L"),
               ("NUT_GUD_R3_0","TOWER_GUS_R3"),("NUT_LRF_L1","LIFT_RAIL_L"),
               ("NUT_LRF_L1","LIFT_BASE"),("NUT_LRF_L1","FRAME_RAIL_L"),
               ("NUT_LW_0","LIFT_WINCH"),("NUT_LW_0","DECK_L"),
               ("NUT_TWC_L_0","TURRET_DECK")):
    ns,ms=gs(nn),gs(mem)
    if ns is None or ms is None:
        print(nn,mem,"missing"); continue
    print("%-14s -> %-14s d=%.3f common=%.1f"%(nn,mem,ns.distToShape(ms)[0],ns.common(ms).Volume))
print("DONE")
