import FreeCAD as App, json
from pathlib import Path
ROOT = Path(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot")
EXCLUDE_PREFIX = ("ENV_","TOOL_","AXIS_","REF_","VOL_")
EXCLUDE_TYPES = ("App::Part","App::Origin","Spreadsheet::Sheet","App::DocumentObjectGroup")
def _consumed_add(x,out):
    out.add(x.Name)
    for p in ("Links","Group"):
        g=getattr(x,p,None)
        if g is None: continue
        for y in (g if isinstance(g,(list,tuple)) else (g,)):
            if y is not None: _consumed_add(y,out)
def exportable(doc):
    consumed=set()
    for o in doc.Objects:
        if o.TypeId in ("Part::Fuse","Part::Cut","Part::Chamfer","Part::Common","Part::MultiFuse"):
            for p in ("Base","Tool","Shapes"):
                t=getattr(o,p,None)
                if t is None: continue
                for x in (t if isinstance(t,(list,tuple)) else (t,)):
                    if x is not None: _consumed_add(x,consumed)
    return [o for o in doc.Objects if hasattr(o,"Shape") and not o.Shape.isNull()
            and o.Shape.Volume>0 and o.TypeId not in EXCLUDE_TYPES
            and not o.Name.startswith(EXCLUDE_PREFIX) and o.Name not in consumed]
def gshape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
m = App.openDocument(str(ROOT/"cad/master_robot.FCStd"))
mmeta = json.loads((ROOT/"exports/meta/master.json").read_text(encoding="utf-8"))
solids = exportable(m)
declared=set()
for coll in ("embeds","faces","journals","contacts"):
    for a,b in mmeta[coll]: declared.add(tuple(sorted((a,b))))
for j in mmeta["joints"]:
    ms=j["members"]+j.get("bolts",[])+j.get("nuts",[])
    for i_ in range(len(ms)):
        for k_ in range(i_+1,len(ms)): declared.add(tuple(sorted((ms[i_],ms[k_]))))
gshapes={o.Name:gshape(o) for o in solids}
names=list(gshapes); bbs={n:gshapes[n].BoundBox for n in names}
overlaps=[]
for i_ in range(len(names)):
    a=names[i_]
    for j_ in range(i_+1,len(names)):
        b=names[j_]
        if tuple(sorted((a,b))) in declared: continue
        ba,bb_=bbs[a],bbs[b]
        if (ba.XMax<=bb_.XMin or ba.XMin>=bb_.XMax or ba.YMax<=bb_.YMin
            or ba.YMin>=bb_.YMax or ba.ZMax<=bb_.ZMin or ba.ZMin>=bb_.ZMax): continue
        try: com=gshapes[a].common(gshapes[b])
        except Exception: continue
        if com.Volume>0.5: overlaps.append((round(com.Volume,1),a,b))
overlaps.sort(reverse=True)
print("GEO2 total:",len(overlaps))
for v,a,b in overlaps: print("  %8.1f %s x %s"%(v,a,b))
