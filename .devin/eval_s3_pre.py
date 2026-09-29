import FreeCAD as App, Part, json
d = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
out={}
for n in ["ELEC_SHELF","FEED_COLUMN","HOP_WALL_L","HOP_WALL_R","FRAME_RAIL_L","FRAME_RAIL_R","BELLY_PAN","REF_DIV_PORT","AXIS_TURRET","REF_DECK_IFACE","COL_FLANGE","DIV_FLAP","VOL_BALL_N","HUB_CTRL","HUB_EXP"]:
    o=d.getObject(n)
    if o is None:
        out[n]=None; continue
    if hasattr(o,"Shape") and not o.Shape.isNull() and o.Shape.Solids:
        b=o.Shape.BoundBox
        out[n]=[round(b.XMin,1),round(b.XMax,1),round(b.YMin,1),round(b.YMax,1),round(b.ZMin,1),round(b.ZMax,1)]
    else:
        out[n]=("datum", o.Label[:60])
# solids present at the proposed tower footprints: probe a thin box at (x -100..-30, y +-126..136, z 80..90)
probes={}
for tag,(y0,y1) in {"tower_ypos":(126,136),"tower_yneg":(-136,-126)}.items():
    bx=Part.makeBox(70,y1-y0,10,App.Vector(-100,y0,80))
    hits=[]
    for o in d.Objects:
        if not (hasattr(o,"Shape") and not o.Shape.isNull()): continue
        if not o.Shape.Solids or o.Name.startswith(("VOL_","REF_","AXIS_","ENV_","TOOL_","GRP_")): continue
        s=o.Shape.copy()
        try: s.Placement=o.getGlobalPlacement()
        except Exception: pass
        if s.BoundBox.ZMax<80 or s.BoundBox.ZMin>90: continue
        try: v=s.common(bx).Volume
        except Exception: v=0
        if v>0.5: hits.append((o.Name,round(v,1)))
    probes[tag]=hits[:10]
out["tower_zone"]=probes
# what's under the mast base zone x-200..-170,y136..184,z55..70 (rail top)
bx=Part.makeBox(30,48,15,App.Vector(-200,136,55))
hits=[]
for o in d.Objects:
    if not (hasattr(o,"Shape") and not o.Shape.isNull()): continue
    if not o.Shape.Solids or o.Name.startswith(("VOL_","REF_","AXIS_","ENV_","TOOL_","GRP_")): continue
    s=o.Shape.copy()
    try: s.Placement=o.getGlobalPlacement()
    except Exception: pass
    if s.BoundBox.ZMax<55 or s.BoundBox.ZMin>70: continue
    try: v=s.common(bx).Volume
    except Exception: v=0
    if v>0.5: hits.append((o.Name,round(v,1)))
out["mast_base_zone"]=hits[:10]
# cradle park zone x-140..-115,y165..190,z160..190 -- what's already there
bx=Part.makeBox(25,25,30,App.Vector(-140,165,160))
hits=[]
for o in d.Objects:
    if not (hasattr(o,"Shape") and not o.Shape.isNull()): continue
    if not o.Shape.Solids or o.Name.startswith(("VOL_","REF_","AXIS_","ENV_","TOOL_","GRP_")): continue
    s=o.Shape.copy()
    try: s.Placement=o.getGlobalPlacement()
    except Exception: pass
    if s.BoundBox.ZMax<160 or s.BoundBox.ZMin>190: continue
    try: v=s.common(bx).Volume
    except Exception: v=0
    if v>0.5: hits.append((o.Name,round(v,1)))
out["cradle_zone"]=hits[:10]
print("S3PRE "+json.dumps(out))
