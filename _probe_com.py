import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
for a,b in (("ROPE_DYNEEMA","CRADLE_ARM"),("ROPE_DYNEEMA","BOLT_CARM_2"),
            ("LOAD_CHUTE","CRADLE_CUP"),("LOAD_CHUTE","CRADLE_FOAM"),
            ("CHUTE_TOWER_PAD","LOAD_CHUTE"),("CHUTE_LIP_L2","CHUTE_LIP_L1"),
            ("WINCH_SPOOL","STANDOFF_1"),("LIFT_WINCH","DECK_POST_L0")):
    oa,ob=doc.getObject(a),doc.getObject(b)
    if oa is None or ob is None: print(a,b,"MISSING"); continue
    c=shape(oa).common(shape(ob))
    if c and c.Solids:
        bb=c.BoundBox
        print(a,"x",b,"vol",round(c.Volume,1),"at",[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
    else:
        print(a,"x",b,"vol 0")
# where is the arm's solid material near the wrap zone? arm bbox slice
arm=shape(doc.getObject("CRADLE_ARM"))
for z in (290,295,300,305):
    sl=arm.slice(App.Vector(0,0,1),z)
    # just print area of faces in slice bbox region
print("arm done")
