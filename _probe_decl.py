import FreeCAD as App, json
from pathlib import Path
ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
mmeta = json.loads((ROOT/"exports/meta/master.json").read_text(encoding="utf-8"))
decl_t={tuple(sorted((p[0],p[1]))) for key in ("embeds","faces","journals","contacts") for p in mmeta[key]}
for j in mmeta["joints"]:
    ms=j["members"]+j.get("bolts",[])+j.get("nuts",[])
    for i_ in range(len(ms)):
        for k_ in range(i_+1,len(ms)):
            decl_t.add(tuple(sorted((ms[i_],ms[k_]))))
print("PAIR IN DECL:", ("BOLT_S2TIE_1","ROPE_DYNEEMA") in decl_t)
doc = App.openDocument(str(ROOT/"cad/master_robot.FCStd"))
doc.recompute(None, True, True)
o = doc.getObject("BOLT_S2TIE_1")
r = doc.getObject("ROPE_DYNEEMA")
print("names:", o.Name, r.Name)
s1, s2 = o.Shape.copy(), r.Shape.copy()
s1.Placement = o.getGlobalPlacement(); s2.Placement = r.getGlobalPlacement()
print("common:", s1.common(s2).Volume)
