import FreeCAD as App
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
def com(a,b):
    oa,ob=doc.getObject(a),doc.getObject(b)
    if oa is None or ob is None: print(a,b,"MISSING"); return
    c=shape(oa).common(shape(ob))
    if c and c.Solids and c.Volume>0.5:
        bb=c.BoundBox
        print(a,"x",b,"vol",round(c.Volume,1),"at",[round(v,1) for v in (bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax)])
    else:
        print(a,"x",b,"vol 0")
for p in (("LIFT_WINCH","DECK_L"),("LIFT_WINCH","DECK_POST_L0"),
          ("LIFT_WINCH","ELEC_SHELF"),("WINCH_SPOOL","ELEC_SHELF"),
          ("WINCH_SPOOL","STANDOFF_1"),("LIFT_WINCH","WIRE_TILT_SV"),
          ("LIFT_WINCH","FRAME_RAIL_L"),("LIFT_WINCH","LIFT_BASE"),
          ("CHUTE_TOWER_PAD","ELEC_SHELF"),("CHUTE_TOWER_PAD","DECK_L"),
          ("CHUTE_TOWER_PAD","LOAD_CHUTE"),("BOLT_CHT_0","ELEC_SHELF"),
          ("BOLT_CHT_0","DECK_L"),("NUT_CHT_0","DECK_L"),
          ("NUT_CHT_0","NUT_CHT_1"),("BOLT_CHT_0","BOLT_CHT_1"),
          ("SCRW_CHL_1_0","SCRW_CHL_1_1"),("ROPE_DYNEEMA","CRADLE_ARM"),
          ("ROPE_DYNEEMA","BOLT_CARM_2"),("ROPE_DYNEEMA","BOLT_S2TIE_2"),
          ("DECK_POST_L0","STANDOFF_1"),("DECK_POST_L0","LIFT_WINCH"),
          ("ELEC_SHELF","LIFT_WINCH"),("STANDOFF_1","LIFT_WINCH")):
    com(*p)
