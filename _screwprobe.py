import FreeCAD as App
m = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def g(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
pairs=[]
for i in range(4):
    for j in range(3):
        n="SCRW_CHL_%d_%d"%(i,j)
        if m.getObject(n):
            for t in ("CHUTE_LIP_L%d"%(i+1),"CHUTE_LIP_R%d"%(i+1),
                      "CHUTE_LIP_L2","CHUTE_LIP_R2","LOAD_CHUTE"):
                pairs.append((n,t))
for tg in ("L","R"):
    for i in range(4):
        pairs.append(("BOLT_FM_%s%d"%(tg,i),"LAUNCH_CHEEK_%s"%tg))
        pairs.append(("BOLT_FM_%s%d"%(tg,i),"FLY_MOTOR_%s"%tg))
for a,b in pairs:
    oa,ob=m.getObject(a),m.getObject(b)
    if not oa or not ob: continue
    com=g(oa).common(g(ob))
    d=g(oa).distToShape(g(ob))[0]
    if com.Volume>0.1 or d<2:
        print("%-14s x %-15s com=%6.2f dist=%5.2f"%(a,b,com.Volume,d))
