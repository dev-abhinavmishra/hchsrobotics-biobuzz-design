import FreeCAD as App, Part
doc = App.openDocument(u"cad/master_robot.FCStd")
doc.recompute(None, True, True)
def gs(nm):
    o = doc.getObject(nm)
    s = o.Shape.copy(); s.Placement = o.getGlobalPlacement(); return s
ch = gs("LOAD_CHUTE")
print("LOAD_CHUTE bbox:", ch.BoundBox)
for nm in ("CHUTE_LIP_L1","CHUTE_LIP_R1","FLYWHEEL_L","FLYWHEEL_R"):
    try: print(nm, "bbox:", gs(nm).BoundBox)
    except Exception as e: print(nm, "ERR", e)
for sname, c in (("S11",(-66.0,52.0,203.0)),("S12",(-66.0,57.0,204.0)),("S9c",(-66.0,0.0,240.0))):
    sp = Part.makeSphere(46.5, App.Vector(*c))
    for nm in ("LOAD_CHUTE","CHUTE_LIP_L1","CHUTE_LIP_R1","FLYWHEEL_L","FLYWHEEL_R"):
        com = sp.common(gs(nm))
        if com.Volume > 0.5:
            print(sname, nm, round(com.Volume,1), "combbox", com.BoundBox)
# bed surface heights under the sphere bottom at the S11/S12 footprint
for y in (40,45,50,52,57,60,65,70):
    probe = Part.makeBox(2,2,60, App.Vector(-67,y,150))
    com = probe.common(ch)
    print("bed col y=%d ztop=%s" % (y, round(com.BoundBox.ZMax,1) if com.Volume>0 else "none"))
