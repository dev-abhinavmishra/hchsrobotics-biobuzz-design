import FreeCAD as App, Part
doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")
def shape(o):
    s=o.Shape.copy(); s.Placement=o.getGlobalPlacement(); return s
def probe(name,x0,x1,y0,y1,z0,z1):
    bx=Part.makeBox(x1-x0,y1-y0,z1-z0,App.Vector(x0,y0,z0))
    hits=[]
    for o in doc.Objects:
        if not hasattr(o,"Shape"): continue
        s=o.Shape
        if not s or s.isNull() or not s.Solids: continue
        if o.Name.startswith(("ENV_","VOL_","TOOL_","AXIS_","REF_","GRP_")): continue
        try: c=bx.common(shape(o))
        except Exception: continue
        if c and c.Solids and c.Volume>0.5: hits.append((o.Name,round(c.Volume,1)))
    print(name,sorted(hits,key=lambda h:-h[1])[:10])
probe("STANDOFF1@(-110,157)",-115,-105,152,162,60,101)
probe("STANDOFF1@(-155,120)",-160,-150,115,125,60,101)
probe("POST_L0@(-124,160)",-131,-118,154,166,60,92)
probe("pad_shelf_slot",-76,-58,128,145,92,98)
probe("winch_shelf_slot",-163,-131,145,175,92,98)
probe("winch_deck_slot",-163,-131,145,175,82,88)
