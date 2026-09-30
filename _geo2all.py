import FreeCAD as App, json
m = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
meta = json.load(open(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\exports\meta\master.json"))
decl = set()
for grp in ("embeds","faces","journals","contacts"):
    for pr in meta.get(grp,[]):
        decl.add(tuple(sorted(pr)))
for j in meta.get("joints",[]):
    mem=j.get("members",[]); fas=j.get("bolts",[])+j.get("nuts",[])
    for x in mem+fas:
        for y in mem+fas:
            if x!=y: decl.add(tuple(sorted((x,y))))
EXC=("ENV_","TOOL_","AXIS_","REF_","VOL_","GRP_")
solids=[]
for o in m.Objects:
    if not o.Name.startswith(EXC) and hasattr(o,"Shape") and o.Shape.Solids:
        s=o.Shape.copy(); s.Placement=o.getGlobalPlacement()
        solids.append((o.Name,s))
out=[]
for i in range(len(solids)):
    a,sa=solids[i]; ba=sa.BoundBox
    for j in range(i+1,len(solids)):
        b,sb=solids[j]
        if tuple(sorted((a,b))) in decl: continue
        bb=sb.BoundBox
        if ba.XMax<=bb.XMin or bb.XMax<=ba.XMin: continue
        if ba.YMax<=bb.YMin or bb.YMax<=ba.YMin: continue
        if ba.ZMax<=bb.ZMin or bb.ZMax<=ba.ZMin: continue
        com=sa.common(sb)
        if com.Volume>0.3:
            out.append((round(com.Volume,1),a,b))
out.sort(reverse=True)
with open("_geo2full.txt","w") as f:
    for v,a,b in out: f.write("%9.1f  %s x %s\n"%(v,a,b))
print("TOTAL",len(out))
