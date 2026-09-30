import FreeCAD as App, Part, re, sys
sys.path.insert(0, r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad")
import dt_lift

doc = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd")

src = open(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad\selfcheck_overhaul03.py").read()

def names(pat):
    m = re.search(pat, src, re.S)
    return set(re.findall(r'"([A-Z][A-Z0-9_]+)"', m.group(1)))

BALL_OK = names(r'BALL_OK\s*=\s*\{([^}]*)\}')
BALL_SX = BALL_OK | names(r'BALL_STATIC_EX\s*=\s*BALL_OK\s*\|\s*\{([^}]*)\}')
print("BALL_OK", len(BALL_OK), "BALL_STATIC_EX", len(BALL_SX))

sheet = doc.getObject("Parameters")
def P(k): return float(sheet.get(k))

solids = []
for o in doc.Objects:
    if not hasattr(o, "Shape"): continue
    s = o.Shape
    if not s or s.isNull() or not s.Solids: continue
    if o.Name.startswith(("ENV_", "VOL_", "TOOL_", "GRP_")): continue
    solids.append(o)
print("solids:", len(solids))

def shape(o):
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    return s

# ---- pass 1: VOL_BALL_P/N vs BALL_OK-exempt only ----
bad1 = []
for pn in ("VOL_BALL_P", "VOL_BALL_N"):
    pv = doc.getObject(pn)
    if pv is None:
        bad1.append("missing " + pn); continue
    ps = shape(pv)
    for o in solids:
        if o.Name in BALL_OK: continue
        try: com = ps.common(shape(o))
        except Exception: continue
        if com.Volume > 0.5:
            bad1.append((pn, o.Name, round(com.Volume, 1)))
print("VOL_BALL hits:", bad1[:20])

# ---- pass 2: station spheres vs BALL_STATIC_EX ----
p0c, p1c, p2c = dt_lift.CHUTE_PTS
d1c, _w1, n1c, _L1 = dt_lift._frame_for(p0c, p1c)
d2c, _w2, n2c, _L2 = dt_lift._frame_for(p1c, p2c)
m1 = (App.Vector(*p0c) + App.Vector(*p1c)) * 0.5 + n1c * 46.5
m2 = (App.Vector(*p1c) + App.Vector(*p2c)) * 0.5 + n2c * 46.5
cdx = P("cradle_x") + 5.0
cdy = P("cradle_y") - 3.0 - 46.5
cdz = P("cradle_z") + 3.0
ST = [
    ("S1_mouth", (205.0, 0.0, 80.0)), ("S3_undercrown", (178.0, 0.0, 85.0)),
    ("S4_basin", (105.0, 0.0, 155.0)), ("S5_incline", (62.0, 0.0, 142.0)),
    ("S6_lane", (40.0, 0.0, 134.0)), ("S7_approach", (35.0, 0.0, 132.0)),
    ("S8_win_throat", (10.0, 0.0, 125.0)), ("S9a_bore_rest", (-66.0, 0.0, 162.0)),
    ("S9b_bore_mid", (-66.0, 0.0, 200.0)), ("S9c_bore_top", (-66.0, 0.0, 240.0)),
    ("S10_gate", (-66.0, 0.0, 175.0)), ("S11_port", (-66.0, 52.0, 203.0)),
    ("S12_flange", (-66.0, 57.0, 204.0)),
    ("S13_col_exit", (P("column_x"), 0.0, P("column_z1"))),
    ("S14_nip", (P("fly_axis_x"), 0.0, P("fly_axis_z"))),
    ("S15_chute_leg1", (m1.x, m1.y, m1.z)),
    ("S16_chute_leg2", (m2.x, m2.y, m2.z)),
    ("S17_cradle", (cdx, cdy, cdz)),
]
print("S15", [round(v,1) for v in (m1.x,m1.y,m1.z)],
      "S16", [round(v,1) for v in (m2.x,m2.y,m2.z)],
      "S17", (cdx, cdy, cdz))
bad2 = []
for sname, c in ST:
    sp = Part.makeSphere(46.5, App.Vector(*c))
    for o in solids:
        if o.Name in BALL_SX: continue
        try: com = sp.common(shape(o))
        except Exception: continue
        if com.Volume > 0.5:
            bad2.append((sname, o.Name, round(com.Volume, 1)))
print("STATION hits:", len(bad2))
for h in sorted(set(bad2)): print("  ", h)

# ---- pass 3: VOL_ pose volumes vs BALL_STATIC_EX ----
bad3 = []
for vn in ("VOL_GATE_OPEN", "VOL_GATE_CLOSED", "VOL_DIV_A", "VOL_DIV_B",
           "VOL_HOOD_LO", "VOL_HOOD_HI", "VOL_S1_DEP", "VOL_S2_DEP",
           "VOL_CRADLE_DEP"):
    vo = doc.getObject(vn)
    if vo is None: continue
    vs = shape(vo)
    for o in solids:
        if o.Name in BALL_SX: continue
        try: com = vs.common(shape(o))
        except Exception: continue
        if com.Volume > 0.5:
            bad3.append((vn, o.Name, round(com.Volume, 1)))
print("POSE hits:", len(bad3))
for h in sorted(set(bad3))[:20]: print("  ", h)
