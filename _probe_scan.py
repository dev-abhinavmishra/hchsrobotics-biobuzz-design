import FreeCAD as App, json
from pathlib import Path
exec(open("_verify_all.py", encoding="utf-8").read().split("# ---- GEO2 ----")[0])
decl_t={tuple(sorted((p[0],p[1]))) for key in ("embeds","faces","journals","contacts") for p in mmeta[key]}
for j in mmeta["joints"]:
    ms=j["members"]+j.get("bolts",[])+j.get("nuts",[])
    for i_ in range(len(ms)):
        for k_ in range(i_+1,len(ms)):
            decl_t.add(tuple(sorted((ms[i_],ms[k_]))))
print("in decl_t:", tuple(sorted(("BOLT_S2TIE_1","ROPE_DYNEEMA"))) in decl_t)
print("rope in names:", "ROPE_DYNEEMA" in shape_map, "bolt in names:", "BOLT_S2TIE_1" in shape_map)
print("shape_map keys w/ ROPE:", [n for n in shape_map if "ROPE" in n])
print("shape_map keys w/ S2TIE:", [n for n in shape_map if "S2TIE" in n])
