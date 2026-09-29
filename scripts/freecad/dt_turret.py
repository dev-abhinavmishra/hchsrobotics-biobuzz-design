"""scripts/freecad/dt_turret.py -- sprint-03 turret tower + launcher.

Shared builders for the turret subsystem (used by both the subsystem
FCStd and the master build -- DET3 parity).

Static stack (grounds through the sprint-01 deck panels):
    FRAME/DECK -> TOWER_L/R risers + TOWER_GUS_* braces
             -> TURRET_DECK (O114 bore on AXIS_TURRET, x=-66 y=0)
             -> LAZY_SUSAN_LO -> [race pair contact] -> LAZY_SUSAN_HI
             -> RING_GEAR -> TURRET_PLATE -> GRP_TURRET_ROT stack.
    YAW_SERVO on YAW_TRAY under the deck drives YAW_PINION through a
    deck bore; the pinion meshes the ring's EXTERNAL teeth at the
    pinned 72.8 mm center distance (FC1: internal mesh impossible --
    the static feed column owns r < 55).

Rotating stack (GRP_TURRET_ROT): cheek pair, dual counter-rotating
O88.9 flywheels + face-mounted 5203 motors + bearing/shaft/hub-clamp
support chain (N4), HOOD on pivot pins + servo/link, NIP_BACKPLATE,
TURRET_TOP_BRACE, VSN_CAM + CAM_LED, YAW_MAGNET, and the baked
service-loop wiring routed in the r55..80 annular gap BELOW the
pinion plane (N2 -- never through the r<55 column channel).

Pinned deviations (same class as the sprint-02 pose corrections; the
numbers are in robot_params.py + docs/robot-parameters.md):
  * fly_axis_z 292 -> 308.5: wheel R44.45 at z292 dips to z247.5 and
    would interpenetrate the column top (z<=254), the ring gear and
    the susan races. Raised to clear the whole static stack while
    keeping the cheek/bearing/hood geometry coherent.
  * hood_piv_z 321 -> 359: z321 sat inside the flywheel disc; with
    the wheels at z308.5 their top is 352.95, so the pivot rides at
    359 (pin surface 2mm clear) and the cheeks grow to z379.
"""

import math

import FreeCAD as App
import Part  # noqa: F401  registers Part::* object types
import Spreadsheet  # noqa: F401  registers Spreadsheet::Sheet

import partkit as pk
from dt_build import (_s, _jm, _fp, _em, _jl, _cn, _bom, _y,
                      _wire, _clip, _sheet, build_frame, _env)
from dt_path import _feat

# -- expression aliases -------------------------------------------------
AXX = "Parameters.column_x"          # -66 : turret yaw axis x
DTOP = "(Parameters.deck_z + Parameters.deck_thk / 2)"      # 86.8
DZ = "Parameters.turret_deck_z0"                            # 244
DT = "Parameters.turret_deck_t"                             # 4
DTP = "(%s + %s)" % (DZ, DT)                                # 248
HIZ = "(%s + Parameters.susan_race_h)" % DTP                # 252.25
RINGZ = "(%s + 2 * Parameters.susan_race_h)" % DTP          # 256.5
PLZ = "(Parameters.plate_z - Parameters.plate_t / 2)"       # 263
PLTOP = "(Parameters.plate_z + Parameters.plate_t / 2)"     # 267

B4 = "Parameters.bolt_d"            # 4.2 clearance-shaft bolt
BHD = "Parameters.bolt_head_d"      # 8.2
BHH = "Parameters.bolt_head_h"      # 2.4
N4W = "Parameters.nut4_wrench"
N4H = "Parameters.nut4_h"
N4B = "Parameters.nut4_bore"


def _bolt(doc, ctx, name, pos, axis, length="12", spec="M4"):
    pk.bolt(doc, name, name + "_%sx%s_UNVERIFIED" % (spec, length),
            "UNVERIFIED - %s bolt" % spec, B4, length, BHD, BHH,
            pos, axis)
    _s(ctx, doc.getObject(name))
    return name


def _nut(doc, ctx, name, pos, axis="Z"):
    pk.hex_nut(doc, name, name + "_M4_UNVERIFIED",
               "UNVERIFIED - M4 nylock", N4W, N4H, N4B, pos, axis)
    _s(ctx, doc.getObject(name))
    return name


def _screw(doc, ctx, name, pos, axis, length="5", spec="M3"):
    pk.bolt(doc, name, name + "_%sx%s_UNVERIFIED" % (spec, length),
            "UNVERIFIED - %s selftap screw" % spec,
            "3.2", length, "5.5", "2.0", pos, axis)
    _s(ctx, doc.getObject(name))
    return name


# ======================================================================
# STATIC SIDE
# ======================================================================
def _tower(doc, ctx, sgn):
    """Tower riser: leg + inboard foot + top cap flange, fused then cut.
    L side takes the ELEC_SHELF slot (z94-96) and the load-chute slot;
    R side carries the same foot/cap scheme minus cutouts."""
    nm = "TOWER_L" if sgn > 0 else "TOWER_R"
    lat = _y("Parameters.tower_lat_off", sgn)
    leg = pk.tool_box(
        doc, "%s_LEG" % nm,
        {"Length": "(Parameters.tower_x1 - Parameters.tower_x0)",
         "Width": "Parameters.tower_thk",
         "Height": "(Parameters.tower_z1 - %s)" % DTOP},
        {"Placement.Base.x": "Parameters.tower_x0",
         "Placement.Base.y": "(%s - Parameters.tower_thk / 2)" % lat,
         "Placement.Base.z": DTOP})
    # foot + cap share the same inboard footprint (leg-inner-face -24)
    fy0 = ("(%s - Parameters.tower_thk / 2 - 24)" % lat if sgn > 0
           else "(%s - Parameters.tower_thk / 2)" % lat)
    fw = "(Parameters.tower_thk + 24)"
    fx = "(Parameters.tower_x0 + 6)"
    fl = "(Parameters.tower_x1 - Parameters.tower_x0 - 12)"
    foot = pk.tool_box(doc, "%s_FOOT" % nm,
                       {"Length": fl, "Width": fw, "Height": "3"},
                       {"Placement.Base.x": fx,
                        "Placement.Base.y": fy0,
                        "Placement.Base.z": DTOP})
    cap = pk.tool_box(doc, "%s_CAP" % nm,
                      {"Length": fl, "Width": fw, "Height": "3"},
                      {"Placement.Base.x": fx,
                       "Placement.Base.y": fy0,
                       "Placement.Base.z": "(Parameters.tower_z1 - 3)"})
    body = pk.fuse(doc, "TOOL_" + nm + "_BLANK", nm + "_blank_UNVERIFIED",
                   "UNVERIFIED - tower blank", leg, [foot, cap])
    tools = []
    # foot bolt clearance bores (through the foot flange)
    if sgn > 0:
        fbxs = ("-160", "-124", "-88", "-52")
        fby = "(Parameters.tower_lat_off - 5.8)"
        cbxs = ("-168", "-156", "-18", "-10")
        cby = "(Parameters.tower_lat_off - 22.8)"
    else:
        fbxs = ("-160", "-140", "-124", "-88")
        fby = "-(Parameters.tower_lat_off - 5.8)"
        cbxs = ("-160", "-140", "-124", "-88")
        cby = "-(Parameters.tower_lat_off - 22.8)"
    for i, px in enumerate(fbxs):
        tools.append(pk.tool_cyl(
            doc, "%s_FB%d" % (nm, i), {"Radius": "2.4", "Height": "5"},
            {"Placement.Base.x": px, "Placement.Base.y": fby,
             "Placement.Base.z": "(%s - 1)" % DTOP}))
    # cap bolt clearance bores (through the top cap flange)
    for i, px in enumerate(cbxs):
        tools.append(pk.tool_cyl(
            doc, "%s_CB%d" % (nm, i), {"Radius": "2.4", "Height": "5"},
            {"Placement.Base.x": px, "Placement.Base.y": cby,
             "Placement.Base.z": "(Parameters.tower_z1 - 4)"}))
    # gusset tower-bolt clearance bores through the leg (axis Y)
    gy = ("(%s - Parameters.tower_thk / 2 - 1)" % lat if sgn > 0 else
          "(%s - Parameters.tower_thk / 2 - 1)" % lat)
    for i, (gx, gz) in enumerate((("-170.5", "104"), ("-170.5", "120"),
                                  ("-20.5", "104"), ("-20.5", "120"))):
        tools.append(pk.tool_cyl(
            doc, "%s_GB%d" % (nm, i), {"Radius": "2.4",
                                       "Height": "5"},
            {"Placement.Base.x": gx,
             "Placement.Base.y": gy,
             "Placement.Base.z": gz},
            pk.axis_rot("Y")))
    if sgn > 0:
        # ELEC_SHELF pass-through slot (shelf x -165..-30, z 94..96)
        tools.append(pk.tool_box(
            doc, "%s_SHELF" % nm,
            {"Length": "137", "Width": "12", "Height": "5.5"},
            {"Placement.Base.x": "-166",
             "Placement.Base.y": "(%s - 6)" % lat,
             "Placement.Base.z": "92.5"}))
        # load-chute pass-through slot (ball sweep x -150..-52, z 98..214)
        tools.append(pk.tool_box(
            doc, "%s_CHUTE" % nm,
            {"Length": "110", "Width": "12", "Height": "116"},
            {"Placement.Base.x": "-158",
             "Placement.Base.y": "(%s - 6)" % lat,
             "Placement.Base.z": "98"}))
    tw = pk.cut(doc, nm,
                nm + "_3mm_polycarb_UNVERIFIED",
                "UNVERIFIED - turret tower riser %s" % nm[-1],
                body, tools)
    _s(ctx, tw)
    _bom(ctx, "turret", "tower riser 3mm polycarb", "polycarb",
         "176x3x157", "UNVERIFIED", [tw.Name])
    deck = "DECK_L" if sgn > 0 else "DECK_R"
    _fp(ctx, tw.Name, deck)
    _fp(ctx, tw.Name, "TURRET_DECK")
    # foot bolts: through foot + deck -> nut under deck
    bolts, nuts = [], []
    for i, px in enumerate(fbxs):
        bn = "BOLT_TWF_%s_%d" % (nm[-1], i)
        nn = "NUT_TWF_%s_%d" % (nm[-1], i)
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": fby,
               "Placement.Base.z": "(%s + 3 + Parameters.bolt_head_h)"
               % DTOP},
              "-Z", "9")
        _nut(doc, ctx, nn,
             {"Placement.Base.x": "(%s - Parameters.nut4_wrench / 2)" % px,
              "Placement.Base.y": "(%s - Parameters.nut4_wrench / 2)" % fby,
              "Placement.Base.z":
              "(Parameters.deck_z - Parameters.deck_thk / 2 - "
              "Parameters.nut4_h)"})
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "tower_%s" % nm[-1].lower(), [tw.Name, deck],
        bolts, nuts, deck)
    # cap bolts: turret deck -> tower cap -> nut under cap
    bolts, nuts = [], []
    for i, px in enumerate(cbxs):
        bn = "BOLT_TWC_%s_%d" % (nm[-1], i)
        nn = "NUT_TWC_%s_%d" % (nm[-1], i)
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": cby,
               "Placement.Base.z":
               "(Parameters.turret_deck_z0 + Parameters.turret_deck_t "
               "+ Parameters.bolt_head_h)"},
              "-Z", "9")
        _nut(doc, ctx, nn,
             {"Placement.Base.x": "(%s - Parameters.nut4_wrench / 2)" % px,
              "Placement.Base.y": "(%s - Parameters.nut4_wrench / 2)" % cby,
              "Placement.Base.z":
              "(Parameters.tower_z1 - 3 - Parameters.nut4_h)"})
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "tdeck_%s" % nm[-1].lower(), ["TURRET_DECK", tw.Name],
        bolts, nuts, tw.Name)
    return tw


def _gusset(doc, ctx, sgn, idx, gx0):
    """L-bracket gusset on the tower inner face, bolted 2+2 (riser+deck)."""
    nm = "TOWER_GUS_%s%d" % ("L" if sgn > 0 else "R", idx)
    tower = "TOWER_L" if sgn > 0 else "TOWER_R"
    lat = _y("Parameters.tower_lat_off", sgn)
    lx = "(%s)" % gx0
    lw = "26"
    leg = pk.tool_box(
        doc, "%s_LEG" % nm,
        {"Length": lw, "Width": "3", "Height": "40"},
        {"Placement.Base.x": lx,
         "Placement.Base.y":
         ("(%s - Parameters.tower_thk / 2 - 3)" % lat if sgn > 0 else
          "(%s + Parameters.tower_thk / 2)" % lat),
         "Placement.Base.z": DTOP})
    foot = pk.tool_box(
        doc, "%s_FOOT" % nm,
        {"Length": lw, "Width": "23", "Height": "3"},
        {"Placement.Base.x": lx,
         "Placement.Base.y":
         ("(%s - Parameters.tower_thk / 2 - 23)" % lat if sgn > 0 else
          "(%s + Parameters.tower_thk / 2)" % lat),
         "Placement.Base.z": DTOP})
    body = pk.fuse(doc, "TOOL_" + nm + "_BLANK",
                   nm + "_blank_UNVERIFIED",
                   "UNVERIFIED - gusset blank", leg, [foot])
    tools = []
    if sgn > 0:
        # shelf slot: keep a 10 mm side strip, open notch on the east edge
        tools.append(pk.tool_box(
            doc, "%s_SHELF" % nm,
            {"Length": "20", "Width": "6", "Height": "5.5"},
            {"Placement.Base.x": "(%s + 10)" % gx0,
             "Placement.Base.y": "(%s - 6)" % lat,
             "Placement.Base.z": "92.5"}))
        # tower-bolt clearance bores (axis Y)
    gy = ("(%s - Parameters.tower_thk / 2 - 4)" % lat if sgn > 0 else
          "(%s + Parameters.tower_thk / 2 - 1)" % lat)
    for i, gz in enumerate(("104", "120")):
        tools.append(pk.tool_cyl(
            doc, "%s_TB%d" % (nm, i), {"Radius": "2.4", "Height": "6"},
            {"Placement.Base.x": "(%s + 5.5)" % gx0,
             "Placement.Base.y": gy,
             "Placement.Base.z": gz},
            pk.axis_rot("Y")))
    g = pk.cut(doc, nm, nm + "_3mm_alu_UNVERIFIED",
               "UNVERIFIED - tower gusset L-bracket", body, tools)
    _s(ctx, g)
    deck = "DECK_L" if sgn > 0 else "DECK_R"
    _fp(ctx, g.Name, tower)
    _fp(ctx, g.Name, deck)
    bolts, nuts = [], []
    for i, gz in enumerate(("104", "120")):
        bn = "BOLT_GUS_%s_%d" % (nm[-2:], i)
        nn = "NUT_GUS_%s_%d" % (nm[-2:], i)
        sgn_char = "Y" if sgn > 0 else "-Y"
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": "(%s + 5.5)" % gx0,
               "Placement.Base.y":
               ("(%s - Parameters.tower_thk / 2 - 3 - "
                 "Parameters.bolt_head_h)" % lat if sgn > 0 else
                "(%s + Parameters.tower_thk / 2 + 3 + "
                 "Parameters.bolt_head_h)" % lat),
               "Placement.Base.z": gz},
              sgn_char, "8")
        _nut(doc, ctx, nn,
             {"Placement.Base.x": "(%s + 5.5 - Parameters.nut4_wrench / 2)"
              % gx0,
              "Placement.Base.y":
              ("(%s + Parameters.tower_thk / 2)" % lat if sgn > 0 else
               "(%s - Parameters.tower_thk / 2 - Parameters.nut4_h)" % lat),
              "Placement.Base.z": "(%s - Parameters.nut4_wrench / 2)" % gz},
             "Y")
        bolts.append(bn)
        nuts.append(nn)
    for i, bx in enumerate(("(%s + 4)" % gx0, "(%s + 18)" % gx0)):
        bn = "BOLT_GUD_%s_%d" % (nm[-2:], i)
        nn = "NUT_GUD_%s_%d" % (nm[-2:], i)
        by = ("(Parameters.tower_lat_off - 12.8)" if sgn > 0 else
              "-(Parameters.tower_lat_off - 12.8)")
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": bx, "Placement.Base.y": by,
               "Placement.Base.z": "(%s + 3 + Parameters.bolt_head_h)"
               % DTOP},
              "-Z", "9")
        _nut(doc, ctx, nn,
             {"Placement.Base.x": "(%s - Parameters.nut4_wrench / 2)" % bx,
              "Placement.Base.y": "(%s - Parameters.nut4_wrench / 2)" % by,
              "Placement.Base.z":
              "(Parameters.deck_z - Parameters.deck_thk / 2 - "
              "Parameters.nut4_h)"})
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "gusset_%s" % nm[-2:].lower(),
        [g.Name, tower, deck], bolts, nuts, tower)


def _turret_deck(doc, ctx):
    """TURRET_DECK: 4mm PETG plate over both tower caps, O114 bore,
    pinion-shaft bore, susan bolt pattern, cap-bolt pattern, chute notch."""
    bores = [("Parameters.deck_bore_d",
              {"Placement.Base.x": AXX, "Placement.Base.y": "0",
               "Placement.Base.z": "(%s - 1)" % DZ},
              "Z", "(%s + 2)" % DT),
             ("9",
              {"Placement.Base.x": AXX,
               "Placement.Base.y": "-(Parameters.yaw_off)",
               "Placement.Base.z": "(%s - 1)" % DZ},
              "Z", "(%s + 2)" % DT)]
    # susan-LO bolt clearance (r 62.5 at 20/160/200/340 deg)
    for i, (px, py) in enumerate((("-7.27", "21.39"),
                                  ("-124.73", "21.39"),
                                  ("-124.73", "-21.39"),
                                  ("-7.27", "-21.39"))):
        bores.append(("Parameters.grid_hole_d",
                      {"Placement.Base.x": px, "Placement.Base.y": py,
                       "Placement.Base.z": "(%s - 1)" % DZ},
                      "Z", "(%s + 2)" % DT))
    # cap-bolt bores (through the deck onto each tower cap)
    for i, (px, py) in enumerate(
            (("-168", "(Parameters.tower_lat_off - 22.8)"),
             ("-156", "(Parameters.tower_lat_off - 22.8)"),
             ("-18", "(Parameters.tower_lat_off - 22.8)"),
             ("-10", "(Parameters.tower_lat_off - 22.8)"),
             ("-160", "-(Parameters.tower_lat_off - 22.8)"),
             ("-140", "-(Parameters.tower_lat_off - 22.8)"),
             ("-124", "-(Parameters.tower_lat_off - 22.8)"),
             ("-88", "-(Parameters.tower_lat_off - 22.8)"))):
        bores.append(("Parameters.grid_hole_d",
                      {"Placement.Base.x": px, "Placement.Base.y": py,
                       "Placement.Base.z": "(%s - 1)" % DZ},
                      "Z", "(%s + 2)" % DT))
    p0 = pk.bored_plate(
        doc, "TOOL_TURRET_DECK_P0", "TURRET_DECK_p0_UNVERIFIED",
        "UNVERIFIED - turret deck pre-notch",
        {"Length": "(Parameters.tower_x1 - Parameters.tower_x0 + 12)",
         "Width": "(2 * Parameters.tower_lat_off + 10.4)",
         "Height": DT},
        {"Placement.Base.x": "(Parameters.tower_x0 - 4)",
         "Placement.Base.y": "-(Parameters.tower_lat_off + 5.2)",
         "Placement.Base.z": DZ},
        bores=bores)
    # +Y notch: the turret deck must not shadow the hopper/chute mouth
    notch = pk.tool_box(
        doc, "TOOL_TURRET_DECK_NOTCH",
        {"Length": "126", "Width": "108", "Height": "8"},
        {"Placement.Base.x": "-148", "Placement.Base.y": "30",
         "Placement.Base.z": "(Parameters.turret_deck_z0 - 1)"})
    dk = pk.cut(doc, "TURRET_DECK", "TURRET_DECK_4mm_petg_UNVERIFIED",
                "UNVERIFIED - turret deck plate O114 bore", p0, [notch])
    _s(ctx, dk)
    _bom(ctx, "turret", "turret deck plate 4mm PETG", "petg",
         "188x272x4", "UNVERIFIED", [dk.Name])


def _susan(doc, ctx):
    """Split lazy-susan races: LO bolted to the deck, HI bolted to the
    rotating plate; the race pair contact is the real load path."""
    lo = pk.bore_cyl(doc, "LAZY_SUSAN_LO",
                     "LAZY_SUSAN_LO_132x116_UNVERIFIED",
                     "UNVERIFIED - lazy susan lower race",
                     "Parameters.susan_d", "Parameters.susan_race_h",
                     "Parameters.susan_bore_d",
                     {"Placement.Base.x": AXX, "Placement.Base.y": "0",
                      "Placement.Base.z": DTP}, "Z")
    _s(ctx, lo)
    hi = pk.bore_cyl(doc, "LAZY_SUSAN_HI",
                     "LAZY_SUSAN_HI_132x116_UNVERIFIED",
                     "UNVERIFIED - lazy susan upper race",
                     "Parameters.susan_d", "Parameters.susan_race_h",
                     "Parameters.susan_bore_d",
                     {"Placement.Base.x": AXX, "Placement.Base.y": "0",
                      "Placement.Base.z": HIZ}, "Z")
    _s(ctx, hi)
    _bom(ctx, "turret", "lazy susan race pair O132xO116", "steel",
         "D132x8.5", "VENDOR-PENDING", [lo.Name, hi.Name])
    _fp(ctx, lo.Name, "TURRET_DECK")
    _cn(ctx, lo.Name, hi.Name)          # the real rolling load path
    bolts = []
    for i, (px, py) in enumerate((("-7.27", "21.39"),
                                  ("-124.73", "21.39"),
                                  ("-124.73", "-21.39"),
                                  ("-7.27", "-21.39"))):
        bn = "BOLT_SLO_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(%s - Parameters.bolt_head_h)" % DZ},
              "Z", "8")
        bolts.append(bn)
    _jm(ctx, "susan_lo", [lo.Name, "TURRET_DECK"], bolts,
        terminal=lo.Name)


def _yaw_drive(doc, ctx):
    """YAW_TRAY + YAW_SERVO under the deck; YAW_SHAFT through the deck
    bore (journal); YAW_PINION meshing the ring's outer teeth."""
    tray = pk.bored_plate(
        doc, "YAW_TRAY", "YAW_TRAY_3mm_steel_UNVERIFIED",
        "UNVERIFIED - yaw servo tray under deck",
        {"Length": "40", "Width": "35", "Height": "3"},
        {"Placement.Base.x": "-86", "Placement.Base.y": "-90",
         "Placement.Base.z": "(Parameters.turret_deck_z0 - 3)"},
        bores=[("12.4",
                {"Placement.Base.x": AXX,
                 "Placement.Base.y": "-(Parameters.yaw_off)",
                 "Placement.Base.z":
                 "(Parameters.turret_deck_z0 - 4)"},
                "Z", "5")])
    _s(ctx, tray)
    _bom(ctx, "turret", "yaw servo tray 3mm steel", "steel", "40x35x3",
         "UNVERIFIED", [tray.Name])
    _fp(ctx, tray.Name, "TURRET_DECK")
    bolts = []
    for i, (px, py) in enumerate((("-80", "-88"), ("-52", "-88"),
                                  ("-80", "-57"), ("-52", "-57"))):
        bn = "BOLT_YTR_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(Parameters.turret_deck_z0 - 3 - Parameters.bolt_head_h)"},
              "Z", "5")
        bolts.append(bn)
    _jm(ctx, "yaw_tray", [tray.Name, "TURRET_DECK"], bolts,
        terminal="TURRET_DECK")

    # servo: can + ears + boss + stub socket, face-mounted to tray bottom
    can = pk.tool_box(doc, "TOOL_YAW_SV_CAN",
                      {"Length": "40", "Width": "20.5", "Height": "34"},
                      {"Placement.Base.x": "-86",
                       "Placement.Base.y": "-82.75",
                       "Placement.Base.z": "205"})
    ear_a = pk.tool_box(doc, "TOOL_YAW_SV_EA",
                        {"Length": "40", "Width": "2.5", "Height": "3"},
                        {"Placement.Base.x": "-86",
                         "Placement.Base.y": "-85.5",
                         "Placement.Base.z": "238"})
    ear_b = pk.tool_box(doc, "TOOL_YAW_SV_EB",
                        {"Length": "40", "Width": "2.5", "Height": "3"},
                        {"Placement.Base.x": "-86",
                         "Placement.Base.y": "-62",
                         "Placement.Base.z": "238"})
    boss = pk.tool_cyl(doc, "TOOL_YAW_SV_BOSS",
                       {"Radius": "6", "Height": "4.5"},
                       {"Placement.Base.x": AXX,
                        "Placement.Base.y": "-(Parameters.yaw_off)",
                        "Placement.Base.z": "239"})
    sbody = pk.fuse(doc, "TOOL_YAW_SV_F", "YAW_SERVO_blank_UNVERIFIED",
                    "UNVERIFIED - yaw servo blank", can,
                    [ear_a, ear_b, boss])
    ear_bores = []
    for i, (px, py) in enumerate((("-80", "-84.3"), ("-52", "-84.3"),
                                  ("-80", "-61"), ("-52", "-61"))):
        ear_bores.append(pk.tool_cyl(
            doc, "TOOL_YAW_SV_EB%d" % i, {"Radius": "1.7", "Height": "5"},
            {"Placement.Base.x": px, "Placement.Base.y": py,
             "Placement.Base.z": "237"}))
    sock = pk.tool_prism(doc, "TOOL_YAW_SV_SOCK", 6, "4.04", "4.5",
                         {"Placement.Base.x": AXX,
                          "Placement.Base.y":
                          "(-(Parameters.yaw_off) - 1)",
                          "Placement.Base.z": "235"},
                         pk.axis_rot("Z"))
    sv = pk.cut(doc, "YAW_SERVO", "YAW_SERVO_CRservo_UNVERIFIED",
                "UNVERIFIED - continuous-rotation yaw servo",
                sbody, ear_bores + [sock])
    _s(ctx, sv)
    _bom(ctx, "turret", "CR servo 40x20.5x36", "servo", "40x20.5",
         "VENDOR-PENDING", [sv.Name])
    _fp(ctx, sv.Name, tray.Name)
    bolts = []
    for i, (px, py) in enumerate((("-80", "-84.3"), ("-52", "-84.3"),
                                  ("-80", "-61"), ("-52", "-61"))):
        bn = "SCRW_YSV_%d" % i
        _screw(doc, ctx, bn,
               {"Placement.Base.x": px, "Placement.Base.y": py,
                "Placement.Base.z": "236"},
               "Z", "5")
        bolts.append(bn)
    _jm(ctx, "yaw_servo", [sv.Name, tray.Name], bolts,
        terminal=tray.Name)

    shaft = pk.cyl(doc, "YAW_SHAFT", "YAW_SHAFT_O8_UNVERIFIED",
                   "UNVERIFIED - pinion drive shaft O8",
                   {"Radius": "(Parameters.yaw_shaft_d) / 2",
                    "Height": "32.5"},
                   {"Placement.Base.x": AXX,
                    "Placement.Base.y": "-(Parameters.yaw_off)",
                    "Placement.Base.z": "230"})
    _s(ctx, shaft)
    _em(ctx, shaft.Name, sv.Name)          # shaft in the servo socket
    _jl(ctx, shaft.Name, "TURRET_DECK")    # contract journal: deck bore
    pinion = pk.bore_cyl(doc, "YAW_PINION",
                         "YAW_PINION_14T_PD23.7_UNVERIFIED",
                         "UNVERIFIED - 14T brass pinion PD23.7",
                         "Parameters.pinion_od", "6",
                         "(Parameters.yaw_shaft_d - 1)",
                         {"Placement.Base.x": AXX,
                          "Placement.Base.y": "-(Parameters.yaw_off)",
                          "Placement.Base.z": "256.9"}, "Z")
    _s(ctx, pinion)
    _bom(ctx, "turret", "14T pinion brass PD23.7", "brass",
         "PD23.7", "VENDOR-PENDING", [pinion.Name])
    _em(ctx, pinion.Name, shaft.Name)      # bore 7 on O8 shaft
    _em(ctx, pinion.Name, "RING_GEAR")     # declared tooth-envelope mesh
    _cn(ctx, pinion.Name, "TURRET_PLATE")  # 0.1mm grazing clearance


def _hall(doc, ctx):
    """Yaw-index reed sensor on the static deck rim; the plate-rim
    YAW_MAGNET sweeps it (contact declared, ~1mm working gap)."""
    sns = pk.box(doc, "HALL_SNSR", "HALL_SNSR_reed_UNVERIFIED",
                 "UNVERIFIED - yaw-index reed sensor",
                 {"Length": "16", "Width": "8", "Height": "5"},
                 {"Placement.Base.x": "-74", "Placement.Base.y": "-84",
                  "Placement.Base.z": DTP})
    _s(ctx, sns)
    _bom(ctx, "turret", "reed sensor", "sensor", "16x8x5",
         "VENDOR-PENDING", [sns.Name])
    _fp(ctx, sns.Name, "TURRET_DECK")


# ======================================================================
# ROTATING SIDE  (GRP_TURRET_ROT, all about AXIS_TURRET = (-66, 0))
# ======================================================================
def _ring(doc, ctx):
    rg = pk.bore_cyl(doc, "RING_GEAR",
                     "RING_GEAR_72T_PD121.9_UNVERIFIED",
                     "VENDOR-PENDING - 72T acetal ring gear ext teeth",
                     "Parameters.ring_od", "6.5",
                     "Parameters.deck_bore_d",
                     {"Placement.Base.x": AXX, "Placement.Base.y": "0",
                      "Placement.Base.z": RINGZ}, "Z")
    _s(ctx, rg)
    _bom(ctx, "turret", "72T ring gear acetal", "acetal",
         "PD121.9 OD128.8", "VENDOR-PENDING", [rg.Name])
    _fp(ctx, rg.Name, "TURRET_PLATE")
    bolts = []
    for i, (px, py) in enumerate((("-22.8", "43.1"), ("-109.2", "43.1"),
                                  ("-109.2", "-43.1"),
                                  ("-22.8", "-43.1"))):
        bn = "BOLT_RING_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(Parameters.plate_z + Parameters.plate_t / 2 + "
               "Parameters.bolt_head_h)"},
              "-Z", "10")
        bolts.append(bn)
    _jm(ctx, "ring_gear", [rg.Name, "TURRET_PLATE"], bolts,
        terminal=rg.Name)


def _plate(doc, ctx):
    """O170 disc O114 bore + 2 motor-support tabs (r<=118), drilled for
    susan/ring/cheek/clamp/cam bolts, magnet press bore, wire-pass bore,
    flywheel scallops."""
    disc = pk.bore_cyl(doc, "TOOL_TPLATE_DISC",
                       "TURRET_PLATE_disc_UNVERIFIED",
                       "UNVERIFIED - plate disc blank",
                       "Parameters.plate_od", "Parameters.plate_t",
                       "Parameters.deck_bore_d",
                       {"Placement.Base.x": AXX, "Placement.Base.y": "0",
                        "Placement.Base.z": PLZ}, "Z")
    tabs = []
    for sgn in (1, -1):
        tabs.append(pk.tool_box(
            doc, "TOOL_TPLATE_TAB_%d" % sgn,
            {"Length": "48", "Width": "50", "Height": "Parameters.plate_t"},
            {"Placement.Base.x": "-102",
             "Placement.Base.y": "62" if sgn > 0 else "-112",
             "Placement.Base.z": PLZ}))
    body = pk.fuse(doc, "TOOL_TPLATE_F", "TURRET_PLATE_blank_UNVERIFIED",
                   "UNVERIFIED - plate blank", disc, tabs)
    tools = []
    # susan-HI bolt clearance (r65)
    for i, (px, py) in enumerate((("-9.71", "32.5"), ("-122.29", "32.5"),
                                  ("-122.29", "-32.5"),
                                  ("-9.71", "-32.5"))):
        tools.append(pk.tool_cyl(
            doc, "TOOL_TPLATE_HI%d" % i, {"Radius": "2.4", "Height": "6"},
            {"Placement.Base.x": px, "Placement.Base.y": py,
             "Placement.Base.z": "(%s - 1)" % PLZ}))
    # ring bolt clearance (r61)
    for i, (px, py) in enumerate((("-22.8", "43.1"), ("-109.2", "43.1"),
                                  ("-109.2", "-43.1"),
                                  ("-22.8", "-43.1"))):
        tools.append(pk.tool_cyl(
            doc, "TOOL_TPLATE_RG%d" % i, {"Radius": "2.4", "Height": "6"},
            {"Placement.Base.x": px, "Placement.Base.y": py,
             "Placement.Base.z": "(%s - 1)" % PLZ}))
    # cheek-foot bolts x8
    for i, (px, py) in enumerate((("-88", "71.5"), ("-88", "77.5"),
                                  ("-59", "71.5"), ("-59", "77.5"),
                                  ("-88", "-71.5"), ("-88", "-77.5"),
                                  ("-59", "-71.5"), ("-59", "-77.5"))):
        tools.append(pk.tool_cyl(
            doc, "TOOL_TPLATE_CK%d" % i, {"Radius": "2.4", "Height": "6"},
            {"Placement.Base.x": px, "Placement.Base.y": py,
             "Placement.Base.z": "(%s - 1)" % PLZ}))
    # motor-clamp bolts x4 (through the tabs)
    for i, (px, py) in enumerate((("-87", "95"), ("-73", "95"),
                                  ("-87", "-95"), ("-73", "-95"))):
        tools.append(pk.tool_cyl(
            doc, "TOOL_TPLATE_MC%d" % i, {"Radius": "2.4", "Height": "6"},
            {"Placement.Base.x": px, "Placement.Base.y": py,
             "Placement.Base.z": "(%s - 1)" % PLZ}))
    # camera-mount bolts x4
    for i, (px, py) in enumerate((("-20", "8"), ("-5", "8"),
                                  ("-20", "-8"), ("-5", "-8"))):
        tools.append(pk.tool_cyl(
            doc, "TOOL_TPLATE_CM%d" % i, {"Radius": "2.4", "Height": "6"},
            {"Placement.Base.x": px, "Placement.Base.y": py,
             "Placement.Base.z": "(%s - 1)" % PLZ}))
    # yaw magnet press bore + wire pass bore
    tools.append(pk.tool_cyl(
        doc, "TOOL_TPLATE_MAG", {"Radius": "3.1", "Height": "6"},
        {"Placement.Base.x": AXX,
         "Placement.Base.y": "-(Parameters.magnet_r)",
         "Placement.Base.z": "(%s - 1)" % PLZ}))
    tools.append(pk.tool_cyl(
        doc, "TOOL_TPLATE_WIRE", {"Radius": "5", "Height": "6"},
        {"Placement.Base.x": "-115", "Placement.Base.y": "-50",
         "Placement.Base.z": "(%s - 1)" % PLZ}))
    # flywheel scallops: the wheels dip ~3mm below the plate top
    for sgn in (1, -1):
        tools.append(pk.tool_box(
            doc, "TOOL_TPLATE_SCP_%d" % sgn,
            {"Length": "34", "Width": "16", "Height": "7"},
            {"Placement.Base.x": "-97",
             "Placement.Base.y": "46" if sgn > 0 else "-62",
             "Placement.Base.z": "(%s - 1.5)" % PLZ}))
    pl = pk.cut(doc, "TURRET_PLATE", "TURRET_PLATE_4mm_acetal_UNVERIFIED",
                "UNVERIFIED - rotating turret plate O170/O114",
                body, tools)
    _s(ctx, pl)
    _bom(ctx, "turret", "turret plate 4mm acetal", "acetal",
         "O170x4 + tabs", "UNVERIFIED", [pl.Name])
    # susan-HI bolts (down through plate into the race top)
    bolts = []
    for i, (px, py) in enumerate((("-9.71", "32.5"), ("-122.29", "32.5"),
                                  ("-122.29", "-32.5"),
                                  ("-9.71", "-32.5"))):
        bn = "BOLT_SHI_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z": "(%s + Parameters.bolt_head_h)" % PLTOP},
              "-Z", "12")
        bolts.append(bn)
    _jm(ctx, "susan_hi", ["LAZY_SUSAN_HI", pl.Name], bolts,
        terminal="LAZY_SUSAN_HI")
    _fp(ctx, "LAZY_SUSAN_HI", pl.Name)
    return pl


def _cheek(doc, ctx, sgn):
    nm = "LAUNCH_CHEEK_L" if sgn > 0 else "LAUNCH_CHEEK_R"
    ch = pk.tool_box(
        doc, "TOOL_%s_PL" % nm,
        {"Length": "76", "Width": "Parameters.cheek_thk",
         "Height": "112"},
        {"Placement.Base.x": "-110",
         "Placement.Base.y":
         ("(Parameters.cheek_lat - Parameters.cheek_thk / 2)" if sgn > 0
          else "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2)"),
         "Placement.Base.z": "(Parameters.plate_z + Parameters.plate_t / 2)"})
    foot = pk.tool_box(
        doc, "TOOL_%s_FT" % nm,
        {"Length": "39", "Width": "10", "Height": "3"},
        {"Placement.Base.x": "-93",
         "Placement.Base.y": "69" if sgn > 0 else "-79",
         "Placement.Base.z": "(Parameters.plate_z + Parameters.plate_t / 2)"})
    body = pk.fuse(doc, "TOOL_%s_F" % nm, nm + "_blank_UNVERIFIED",
                   "UNVERIFIED - cheek blank", ch, [foot])
    tools = []
    # bearing pilot bore O16.4
    tools.append(pk.tool_cyl(
        doc, "TOOL_%s_BRG" % nm, {"Radius": "8.2", "Height": "8"},
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y":
         ("(Parameters.cheek_lat - Parameters.cheek_thk / 2 - 1)"
          if sgn > 0 else
          "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 1)"),
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y")))
    # hood pivot bore O8.4
    tools.append(pk.tool_cyl(
        doc, "TOOL_%s_PIV" % nm, {"Radius": "4.2", "Height": "8"},
        {"Placement.Base.x": "Parameters.hood_piv_x",
         "Placement.Base.y":
         ("(Parameters.cheek_lat - Parameters.cheek_thk / 2 - 1)"
          if sgn > 0 else
          "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 1)"),
         "Placement.Base.z": "Parameters.hood_piv_z"},
        pk.axis_rot("Y")))
    # motor face-bolt clearance bores (M3.4)
    for i, (dx, dz) in enumerate((("-15", "15"), ("-15", "-15"),
                                  ("15", "15"), ("15", "-15"))):
        tools.append(pk.tool_cyl(
            doc, "TOOL_%s_MB%d" % (nm, i), {"Radius": "1.7", "Height": "8"},
            {"Placement.Base.x":
             "(Parameters.fly_axis_x + %s)" % dx,
             "Placement.Base.y":
             ("(Parameters.cheek_lat - Parameters.cheek_thk / 2 - 1)"
              if sgn > 0 else
              "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 1)"),
             "Placement.Base.z":
             "(Parameters.fly_axis_z + %s)" % dz},
            pk.axis_rot("Y")))
    # top-brace bolt bores
    tools.append(pk.tool_cyl(
        doc, "TOOL_%s_TB" % nm, {"Radius": "2.4", "Height": "8"},
        {"Placement.Base.x": "-104",
         "Placement.Base.y":
         ("(Parameters.cheek_lat - Parameters.cheek_thk / 2 - 1)"
          if sgn > 0 else
          "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 1)"),
         "Placement.Base.z": "370"},
        pk.axis_rot("Y")))
    ck = pk.cut(doc, nm, nm + "_5mm_petg_UNVERIFIED",
                "UNVERIFIED - launcher cheek 5mm PETG", body, tools)
    _s(ctx, ck)
    _bom(ctx, "turret", "launcher cheek 5mm PETG", "petg", "76x5x112",
         "UNVERIFIED", [ck.Name])
    _fp(ctx, ck.Name, "TURRET_PLATE")
    bolts, nuts = [], []
    for i, (px, py) in enumerate(
            (("-88", "71.5"), ("-88", "77.5"),
             ("-59", "71.5"), ("-59", "77.5")) if sgn > 0 else
            (("-88", "-71.5"), ("-88", "-77.5"),
             ("-59", "-71.5"), ("-59", "-77.5"))):
        bn = "BOLT_CK_%s%d" % (nm[-1], i)
        nn = "NUT_CK_%s%d" % (nm[-1], i)
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(Parameters.plate_z + Parameters.plate_t / 2 + 3 + "
               "Parameters.bolt_head_h)"},
              "-Z", "10")
        _nut(doc, ctx, nn,
             {"Placement.Base.x": "(%s - Parameters.nut4_wrench / 2)" % px,
              "Placement.Base.y": "(%s - Parameters.nut4_wrench / 2)" % py,
              "Placement.Base.z":
              "(Parameters.plate_z - Parameters.plate_t / 2 - "
              "Parameters.nut4_h)"})
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "cheek_%s" % nm[-1].lower(), [ck.Name, "TURRET_PLATE"],
        bolts, nuts, "TURRET_PLATE")
    return ck


def _fly_assy(doc, ctx, sgn):
    """Flywheel + shaft + bearing + clamp + motor + saddle, one side.
    Support chain (N4): motor-stub -> shaft -> cheek bearing -> hub clamp.
    Wheel sits in the nip gap; counterbored hub clamp on the outer face."""
    tag = "L" if sgn > 0 else "R"
    wy = "(Parameters.nip_gap / 2)" if sgn > 0 else \
        "(-(Parameters.nip_gap / 2) - Parameters.fly_w)"
    # wheel blank disc
    blank = pk.tool_cyl(
        doc, "TOOL_FW_%s_BLK" % tag,
        {"Radius": "(Parameters.fly_d / 2)", "Height": "Parameters.fly_w"},
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y": wy,
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y"))
    thr = pk.tool_cyl(
        doc, "TOOL_FW_%s_THR" % tag,
        {"Radius": "3.5", "Height": "(Parameters.fly_w + 2)"},
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y": ("(%s - 1)" % wy if sgn > 0 else
                              "(%s - 1)" % wy),
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y"))
    cb = pk.tool_cyl(
        doc, "TOOL_FW_%s_CB" % tag,
        {"Radius": "9", "Height": "6"},
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y":
         ("(Parameters.nip_gap / 2 + Parameters.fly_w - 6)" if sgn > 0
          else "(-(Parameters.nip_gap / 2) - Parameters.fly_w)"),
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y"))
    wh = pk.cut(doc, "FLYWHEEL_%s" % tag,
                "FLYWHEEL_%s_O88.9_VENDOR-PENDING" % tag,
                "VENDOR-PENDING - O88.9 compliant flywheel alu+urethane",
                blank, [thr, cb])
    _s(ctx, wh)
    _bom(ctx, "turret", "O88.9 compliant flywheel", "alu+urethane",
         "O88.9x18.3", "VENDOR-PENDING", [wh.Name])
    # hub clamp recessed into the wheel's outer-face counterbore
    cl = pk.bore_cyl(
        doc, "FLY_CLAMP_%s" % tag,
        "FLY_CLAMP_%s_O17.8_UNVERIFIED" % tag,
        "UNVERIFIED - flywheel hub clamp ring",
        "17.8", "6", "7.2",
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y":
         ("(Parameters.nip_gap / 2 + Parameters.fly_w - 6)" if sgn > 0
          else "(-(Parameters.nip_gap / 2) - Parameters.fly_w)"),
         "Placement.Base.z": "Parameters.fly_axis_z"}, "Y")
    _s(ctx, cl)
    # shaft: wheel bore -> bearing -> cheek clearance -> motor socket
    shy = "44" if sgn > 0 else "-67"
    sh = pk.cyl(doc, "FLY_SHAFT_%s" % tag,
                "FLY_SHAFT_%s_O8_UNVERIFIED" % tag,
                "UNVERIFIED - flywheel shaft O8",
                {"Radius": "4", "Height": "23"},
                {"Placement.Base.x": "Parameters.fly_axis_x",
                 "Placement.Base.y": shy,
                 "Placement.Base.z": "Parameters.fly_axis_z"},
                pk.axis_rot("Y"))
    _s(ctx, sh)
    # cheek bearing on the inner face
    bg = pk.flange_bearing(
        doc, "FLY_BRG_%s" % tag,
        "FLY_BRG_%s_MF83_UNVERIFIED" % tag,
        "VENDOR-PENDING - flanged bearing 8mm",
        "24", "6", "24", "8.5", "16", "4",
        {"Placement.Base.x": "(Parameters.fly_axis_x - 12)",
         "Placement.Base.y": "58" if sgn > 0 else "-64",
         "Placement.Base.z": "(Parameters.fly_axis_z - 12)"},
        "Y", "3.4", "9", 1 if sgn > 0 else -1)
    _s(ctx, bg)
    cheek = "LAUNCH_CHEEK_%s" % tag
    _jl(ctx, sh.Name, bg.Name)
    _em(ctx, sh.Name, wh.Name)
    _em(ctx, sh.Name, cl.Name)
    _fp(ctx, bg.Name, cheek)
    bolts = []
    for i, (dx, dz) in enumerate((("-9", "9"), ("-9", "-9"),
                                  ("9", "9"), ("9", "-9"))):
        bn = "BOLT_FBRG_%s%d" % (tag, i)
        _screw(doc, ctx, bn,
               {"Placement.Base.x":
                "(Parameters.fly_axis_x + %s)" % dx,
                "Placement.Base.y":
                ("(58 - 2.0)" if sgn > 0 else "(-58 + 2.0)"),
                "Placement.Base.z":
                "(Parameters.fly_axis_z + %s)" % dz},
               "Y" if sgn > 0 else "-Y", "11")
        bolts.append(bn)
    _jm(ctx, "flybrg_%s" % tag.lower(), [bg.Name, cheek], bolts,
        terminal=cheek)

    # motor: can + face boss + shaft stub, tapped face + hex socket
    my = "(Parameters.cheek_lat + Parameters.cheek_thk / 2 + 2)" \
        if sgn > 0 else \
        "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 34)"
    can = pk.tool_cyl(
        doc, "TOOL_FM_%s_CAN" % tag,
        {"Radius": "(Parameters.fly_motor_d / 2)", "Height": "32"},
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y": my,
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y"))
    fb = pk.tool_cyl(
        doc, "TOOL_FM_%s_FB" % tag,
        {"Radius": "12", "Height": "2"},
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y":
         ("(Parameters.cheek_lat + Parameters.cheek_thk / 2)" if sgn > 0
          else "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 2)"),
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y"))
    stub = pk.tool_cyl(
        doc, "TOOL_FM_%s_STUB" % tag,
        {"Radius": "3", "Height": "8"},
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y":
         ("(Parameters.cheek_lat + Parameters.cheek_thk / 2 - 8)"
          if sgn > 0 else
          "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2)"),
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y"))
    mbody = pk.fuse(doc, "TOOL_FM_%s_F" % tag, "FLY_MOTOR_blank_UNVERIFIED",
                    "UNVERIFIED - flywheel motor blank", can, [fb, stub])
    tools = []
    for i, (dx, dz) in enumerate((("-15", "15"), ("-15", "-15"),
                                  ("15", "15"), ("15", "-15"))):
        tools.append(pk.tool_cyl(
            doc, "TOOL_FM_%s_TP%d" % (tag, i),
            {"Radius": "1.7", "Height": "8.5"},
            {"Placement.Base.x":
             "(Parameters.fly_axis_x + %s)" % dx,
             "Placement.Base.y":
             ("(Parameters.cheek_lat + Parameters.cheek_thk / 2 - 1)"
              if sgn > 0 else
              "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 1)"),
             "Placement.Base.z":
             "(Parameters.fly_axis_z + %s)" % dz},
            pk.axis_rot("Y")))
    tools.append(pk.tool_prism(
        doc, "TOOL_FM_%s_SOCK" % tag, 6, "4.04", "6",
        {"Placement.Base.x": "Parameters.fly_axis_x",
         "Placement.Base.y":
         ("(Parameters.cheek_lat + Parameters.cheek_thk / 2 - 7)"
          if sgn > 0 else
          "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 + 1)"),
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("Y")))
    mt = pk.cut(doc, "FLY_MOTOR_%s" % tag,
                "FLY_MOTOR_%s_5203_VENDOR-PENDING" % tag,
                "VENDOR-PENDING - 5203-class 6000rpm motor O36",
                mbody, tools)
    _s(ctx, mt)
    _bom(ctx, "turret", "5203-class motor O36x36", "motor",
         "O36x36", "VENDOR-PENDING", [mt.Name])
    _fp(ctx, mt.Name, cheek)
    _em(ctx, sh.Name, mt.Name)      # shaft tip seated in the hex socket
    bolts = []
    for i, (dx, dz) in enumerate((("-15", "15"), ("-15", "-15"),
                                  ("15", "15"), ("15", "-15"))):
        bn = "BOLT_FM_%s%d" % (tag, i)
        _screw(doc, ctx, bn,
               {"Placement.Base.x":
                "(Parameters.fly_axis_x + %s)" % dx,
                "Placement.Base.y":
                ("(Parameters.cheek_lat - Parameters.cheek_thk / 2 - 2.0)"
                 if sgn > 0 else
                 "(-(Parameters.cheek_lat) + Parameters.cheek_thk / 2 "
                 "+ 2.0)"),
                "Placement.Base.z":
                "(Parameters.fly_axis_z + %s)" % dz},
               "Y" if sgn > 0 else "-Y", "8")
        bolts.append(bn)
    _jm(ctx, "flymotor_%s" % tag.lower(), [mt.Name, cheek], bolts,
        terminal=mt.Name)
    # motor saddle clamp on the plate tab
    cy = "84" if sgn > 0 else "-100"
    blk = pk.tool_box(
        doc, "TOOL_MCL_%s_BLK" % tag,
        {"Length": "26", "Width": "16", "Height": "24"},
        {"Placement.Base.x": "-93", "Placement.Base.y": cy,
         "Placement.Base.z": "(Parameters.plate_z + Parameters.plate_t / 2)"})
    sad = pk.tool_cyl(
        doc, "TOOL_MCL_%s_SAD" % tag,
        {"Radius": "(Parameters.fly_motor_d / 2 + 0.5)", "Height": "28"},
        {"Placement.Base.x": "-94",
         "Placement.Base.y":
         ("(Parameters.cheek_lat + Parameters.cheek_thk / 2 + 18)"
          if sgn > 0 else
          "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 - 18)"),
         "Placement.Base.z": "Parameters.fly_axis_z"},
        pk.axis_rot("X"))
    mc = pk.cut(doc, "FLY_MCLAMP_%s" % tag,
                "FLY_MCLAMP_%s_saddle_UNVERIFIED" % tag,
                "UNVERIFIED - motor saddle clamp block",
                blk, [sad])
    _s(ctx, mc)
    _fp(ctx, mc.Name, "TURRET_PLATE")
    _cn(ctx, mc.Name, mt.Name)
    bolts, nuts = [], []
    for i, px in enumerate((("-87", "95"), ("-73", "95")) if sgn > 0 else
                           (("-87", "-95"), ("-73", "-95"))):
        bn = "BOLT_MCL_%s%d" % (tag, i)
        nn = "NUT_MCL_%s%d" % (tag, i)
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px[0] if isinstance(px, tuple) else px,
               "Placement.Base.y":
               "95" if sgn > 0 else "-95",
               "Placement.Base.z":
               "(Parameters.plate_z + Parameters.plate_t / 2 + 24 + "
               "Parameters.bolt_head_h)"},
              "-Z", "30")
        bolts.append(bn)
        nuts.append(_nut(doc, ctx, nn,
                         {"Placement.Base.x":
                          "(%s - Parameters.nut4_wrench / 2)"
                          % (px[0] if isinstance(px, tuple) else px),
                          "Placement.Base.y":
                          "(95 - Parameters.nut4_wrench / 2)" if sgn > 0
                          else "(-95 - Parameters.nut4_wrench / 2)",
                          "Placement.Base.z":
                          "(Parameters.plate_z - Parameters.plate_t / 2 - "
                          "Parameters.nut4_h)"}))
    _jm(ctx, "mclamp_%s" % tag.lower(), [mc.Name, "TURRET_PLATE"],
        bolts, nuts, "TURRET_PLATE")


def _hood(doc, ctx):
    """HOOD shell + ears (baked fuse), pivot pins through both cheeks,
    collars, HOOD_SERVO on cheek R, HOOD_LINK pushrod, VOL probes."""
    shell = Part.makeBox(86, 96, 2, App.Vector(-118, -48, 369))
    lip = Part.makeBox(30, 96, 3, App.Vector(-32, -48, 366))
    lip.rotate(App.Vector(-32, -48, 366), App.Vector(0, 1, 0), 25)
    solid = shell.fuse(lip)
    for sgn in (1, -1):
        strap = Part.makeBox(30, 29, 2.5,
                             App.Vector(-115, 45 if sgn > 0 else -74,
                                        368.5))
        ear = Part.makeBox(30, 5, 30,
                           App.Vector(-115, 69 if sgn > 0 else -74, 344))
        ebore = Part.makeCylinder(
            4.2, 8, App.Vector(-100.3, 68 if sgn > 0 else -75, 359),
            App.Vector(0, 1, 0))
        ear = ear.cut(ebore)
        pin = Part.makeCylinder(
            1.6, 3.4, App.Vector(-93, 74 if sgn > 0 else -77.4, 351),
            App.Vector(0, 1, 0))
        ear = ear.fuse(pin)
        solid = solid.fuse(strap).fuse(ear)
    solid = solid.removeSplitter()
    hd = _feat(doc, "HOOD", "HOOD_2mm_alu_UNVERIFIED",
               "UNVERIFIED - adjustable launch hood shell+ears", solid)
    _s(ctx, hd)
    _bom(ctx, "turret", "launch hood 2mm alu", "aluminum", "shell",
         "UNVERIFIED", [hd.Name])
    bolts, nuts = [], []
    for sgn in (1, -1):
        tag = "L" if sgn > 0 else "R"
        bg = pk.flange_bearing(
            doc, "HOOD_PIV_%s" % tag,
            "HOOD_PIV_%s_MF83_UNVERIFIED" % tag,
            "VENDOR-PENDING - hood pivot flanged bearing 8mm",
            "24", "6", "24", "8.5", "14", "4",
            {"Placement.Base.x": "(Parameters.hood_piv_x - 12)",
             "Placement.Base.y": "58" if sgn > 0 else "-64",
             "Placement.Base.z": "(Parameters.hood_piv_z - 12)"},
            "Y", "3.4", "9", 1 if sgn > 0 else -1)
        _s(ctx, bg)
        cheek = "LAUNCH_CHEEK_%s" % tag
        _fp(ctx, bg.Name, cheek)
        pin = pk.cyl(doc, "HOOD_PIN_%s" % tag,
                     "HOOD_PIN_%s_O8_UNVERIFIED" % tag,
                     "UNVERIFIED - hood pivot pin O8",
                     {"Radius": "4", "Height": "23.5"},
                     {"Placement.Base.x": "Parameters.hood_piv_x",
                      "Placement.Base.y": "55.5" if sgn > 0 else "-79",
                      "Placement.Base.z": "Parameters.hood_piv_z"},
                     pk.axis_rot("Y"))
        _s(ctx, pin)
        _jl(ctx, pin.Name, bg.Name)
        _jl(ctx, pin.Name, hd.Name)
        col = pk.bore_cyl(
            doc, "HOOD_COL_%s" % tag,
            "HOOD_COL_%s_UNVERIFIED" % tag,
            "UNVERIFIED - hood pivot collar",
            "14", "5", "7",
            {"Placement.Base.x": "Parameters.hood_piv_x",
             "Placement.Base.y": "74" if sgn > 0 else "-79",
             "Placement.Base.z": "Parameters.hood_piv_z"}, "Y")
        _s(ctx, col)
        _cn(ctx, col.Name, hd.Name)
        bolts.append(pin.Name)
        nuts.append(col.Name)
        _em(ctx, pin.Name, cheek)
        _jl(ctx, pin.Name, cheek)
    _jm(ctx, "hood_piv", [hd.Name, "LAUNCH_CHEEK_L", "LAUNCH_CHEEK_R"],
        bolts, nuts, None)
    # hood servo on cheek R outer face + pushrod to the ear pin
    sb = pk.tool_box(doc, "TOOL_HSV_BODY",
                     {"Length": "23", "Width": "12", "Height": "30"},
                     {"Placement.Base.x": "-95", "Placement.Base.y": "-81",
                      "Placement.Base.z": "328"})
    horn = pk.tool_cyl(doc, "TOOL_HSV_HORN",
                       {"Radius": "4", "Height": "4"},
                       {"Placement.Base.x": "-84",
                        "Placement.Base.y": "-83",
                        "Placement.Base.z": "357"},
                       pk.axis_rot("Y"))
    hsv = pk.fuse(doc, "HOOD_SERVO", "HOOD_SERVO_micro_UNVERIFIED",
                  "UNVERIFIED - hood servo micro", sb, [horn])
    _s(ctx, hsv)
    _bom(ctx, "turret", "hood micro servo", "servo", "23x12x30",
         "VENDOR-PENDING", [hsv.Name])
    _fp(ctx, hsv.Name, "LAUNCH_CHEEK_R")
    bolts = []
    for i, (px, pz) in enumerate((("-91", "334"), ("-77", "334"),
                                  ("-91", "352"), ("-77", "352"))):
        bn = "SCRW_HSV_%d" % i
        _screw(doc, ctx, bn,
               {"Placement.Base.x": px, "Placement.Base.y": "-81",
                "Placement.Base.z": pz},
               "Y", "6")
        bolts.append(bn)
    _jm(ctx, "hood_servo", [hsv.Name, "LAUNCH_CHEEK_R"], bolts,
        terminal="LAUNCH_CHEEK_R")
    # pushrod: baked link from horn tip to the ear pin boss
    p0 = App.Vector(-84, -83, 357)
    p1 = App.Vector(-93, -75.5, 351)
    d = p1 - p0
    link = Part.makeCylinder(1.6, d.Length + 6, p0 - d * 0.25, d)
    lk = _feat(doc, "HOOD_LINK", "HOOD_LINK_pushrod_UNVERIFIED",
               "UNVERIFIED - hood servo pushrod O3", link)
    _s(ctx, lk)
    _em(ctx, lk.Name, hsv.Name)
    _em(ctx, lk.Name, hd.Name)
    # hood pose probes (non-exportable volumes)
    vlo = Part.makeBox(88, 100, 6, App.Vector(-120, -50, 363))
    vhi = vlo.transformGeometry(App.Placement(
        App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 1, 0), -35),
        App.Vector(-100.3, 0, 359)).toMatrix())
    _feat(doc, "VOL_HOOD_LO", "VOL_HOOD_LO_probe_UNVERIFIED",
          "UNVERIFIED - hood closed-pose probe", vlo)
    _feat(doc, "VOL_HOOD_HI", "VOL_HOOD_HI_probe_UNVERIFIED",
          "UNVERIFIED - hood open-pose probe (~35deg)", vhi)


def _extras(doc, ctx):
    """NIP_BACKPLATE, TURRET_TOP_BRACE, VSN_CAM + CAM_LED, YAW_MAGNET."""
    # nip backplate: vertical guide wall behind the nip mouth
    # (x -129..-126, just west of the wheel discs which end at -124.45)
    # on two plate-top feet that straddle the wheel face clearance.
    plate = Part.makeBox(3, 76, 49, App.Vector(-129, -38, 267))
    solid = plate
    for sgn in (1, -1):
        strip = Part.makeBox(14, 18, 5,
                             App.Vector(-131, 36 if sgn > 0 else -54,
                                        267))
        solid = solid.fuse(strip)
    solid = solid.removeSplitter()
    bp = _feat(doc, "NIP_BACKPLATE", "NIP_BACKPLATE_3mm_UNVERIFIED",
               "UNVERIFIED - rotating nip backplate guide wall", solid)
    _s(ctx, bp)
    _bom(ctx, "turret", "nip backplate 3mm alu", "aluminum", "guide",
         "UNVERIFIED", [bp.Name])
    _fp(ctx, bp.Name, "TURRET_PLATE")
    bolts, nuts = [], []
    for i, (px, py) in enumerate((("-120", "40"), ("-120", "48"),
                                  ("-120", "-40"), ("-120", "-48"))):
        bn = "BOLT_NBP_%d" % i
        nn = "NUT_NBP_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(Parameters.plate_z + Parameters.plate_t / 2 + 6 + "
               "Parameters.bolt_head_h)"},
              "-Z", "12")
        _nut(doc, ctx, nn,
             {"Placement.Base.x": "(%s - Parameters.nut4_wrench / 2)" % px,
              "Placement.Base.y": "(%s - Parameters.nut4_wrench / 2)" % py,
              "Placement.Base.z":
              "(Parameters.plate_z - Parameters.plate_t / 2 - "
              "Parameters.nut4_h)"})
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "nip_backplate", [bp.Name, "TURRET_PLATE"], bolts, nuts,
        "TURRET_PLATE")

    # top brace between the cheeks
    br = pk.box(doc, "TURRET_TOP_BRACE",
                "TURRET_TOP_BRACE_petg_UNVERIFIED",
                "UNVERIFIED - cheek top brace PETG",
                {"Length": "8", "Width": "128", "Height": "4.5"},
                {"Placement.Base.x": "-108", "Placement.Base.y": "-64",
                 "Placement.Base.z": "368"})
    _s(ctx, br)
    _bom(ctx, "turret", "cheek top brace PETG", "petg", "8x128x4.5",
         "UNVERIFIED", [br.Name])
    _fp(ctx, br.Name, "LAUNCH_CHEEK_L")
    _fp(ctx, br.Name, "LAUNCH_CHEEK_R")
    bolts = []
    for i, sgn in enumerate((1, -1)):
        bn = "BOLT_TBR_%d" % i
        if sgn > 0:
            pos = {"Placement.Base.x": "-104",
                   "Placement.Base.y":
                   "(Parameters.cheek_lat + Parameters.cheek_thk / 2 + "
                    "Parameters.bolt_head_h)",
                   "Placement.Base.z": "370"}
            ax = "-Y"
        else:
            pos = {"Placement.Base.x": "-104",
                   "Placement.Base.y":
                   "(-(Parameters.cheek_lat) - Parameters.cheek_thk / 2 "
                    "- Parameters.bolt_head_h)",
                   "Placement.Base.z": "370"}
            ax = "Y"
        _bolt(doc, ctx, bn, pos, ax, "8")
        bolts.append(bn)
    _jm(ctx, "top_brace", [br.Name, "LAUNCH_CHEEK_L", "LAUNCH_CHEEK_R"],
        bolts, terminal=br.Name)

    # camera + mount + LED
    mnt = pk.box(doc, "CAM_MOUNT", "CAM_MOUNT_post_UNVERIFIED",
                 "UNVERIFIED - camera mount post",
                 {"Length": "23", "Width": "20", "Height": "14"},
                 {"Placement.Base.x": "-24", "Placement.Base.y": "-10",
                  "Placement.Base.z": PLTOP})
    _s(ctx, mnt)
    _fp(ctx, mnt.Name, "TURRET_PLATE")
    bolts, nuts = [], []
    for i, (px, py) in enumerate((("-20", "8"), ("-5", "8"),
                                  ("-20", "-8"), ("-5", "-8"))):
        bn = "BOLT_CAM_%d" % i
        nn = "NUT_CAM_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(Parameters.plate_z + Parameters.plate_t / 2 + 14 + "
               "Parameters.bolt_head_h)"},
              "-Z", "16")
        _nut(doc, ctx, nn,
             {"Placement.Base.x": "(%s - Parameters.nut4_wrench / 2)" % px,
              "Placement.Base.y": "(%s - Parameters.nut4_wrench / 2)" % py,
              "Placement.Base.z":
              "(Parameters.plate_z - Parameters.plate_t / 2 - "
              "Parameters.nut4_h)"})
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "cam_mount", [mnt.Name, "TURRET_PLATE"], bolts, nuts,
        "TURRET_PLATE")
    cam = pk.box(doc, "VSN_CAM", "VSN_CAM_usb_VENDOR-PENDING",
                 "VENDOR-PENDING - USB camera body",
                 {"Length": "28", "Width": "28", "Height": "14"},
                 {"Placement.Base.x": "-20", "Placement.Base.y": "-14",
                  "Placement.Base.z": "(Parameters.plate_z + "
                  "Parameters.plate_t / 2 + 14)"})
    _s(ctx, cam)
    _bom(ctx, "turret", "USB camera module", "camera", "28x28x14",
         "VENDOR-PENDING", [cam.Name])
    _fp(ctx, cam.Name, mnt.Name)
    for i, (px, pz) in enumerate((("-14", "284"), ("-4", "284"))):
        _screw(doc, ctx, "SCRW_CAM_%d" % i,
               {"Placement.Base.x": px, "Placement.Base.y": "-10",
                "Placement.Base.z": pz}, "Y", "4")
    _em(ctx, cam.Name, mnt.Name)
    led = pk.box(doc, "CAM_LED", "CAM_LED_chip_UNVERIFIED",
                 "UNVERIFIED - camera illuminator LED",
                 {"Length": "6", "Width": "4", "Height": "2"},
                 {"Placement.Base.x": "-16", "Placement.Base.y": "-2",
                  "Placement.Base.z": "(Parameters.plate_z + "
                  "Parameters.plate_t / 2 + 28)"})
    _s(ctx, led)
    _fp(ctx, led.Name, cam.Name)
    # yaw index magnet pressed into the plate rim
    mg = pk.cyl(doc, "YAW_MAGNET", "YAW_MAGNET_O6_UNVERIFIED",
                "UNVERIFIED - O6 index magnet",
                {"Radius": "3", "Height": "13.5"},
                {"Placement.Base.x": AXX,
                 "Placement.Base.y": "-(Parameters.magnet_r)",
                 "Placement.Base.z": "253.5"})
    _s(ctx, mg)
    _em(ctx, mg.Name, "TURRET_PLATE")
    _cn(ctx, mg.Name, "HALL_SNSR")


def _turret_wires(doc, ctx):
    """Baked service loops (N2): motor/servo/camera leads drop through
    the plate wire-pass bore into the r55..80 annular gap, then arc
    under the pinion plane (z<256.9) back toward the column face.
    Nothing enters r<55; nothing rises above z~255.8 inside r<87."""
    wl = _wire(doc, ctx, "WIRE_FLY_L", [
        (-80, 103, 302), (-82, 82, 294), (-88, 62, 276),
        (-110, 20, 272), (-114, -48, 272), (-114, -48, 255),
        (-105, -60, 254), (-96, -66, 253)], dia="2.5")
    _em(ctx, wl.Name, "FLY_MOTOR_L")
    _cn(ctx, wl.Name, "TURRET_PLATE")
    wr = _wire(doc, ctx, "WIRE_FLY_R", [
        (-80, -103, 302), (-82, -80, 294), (-90, -58, 276),
        (-112, -28, 272), (-117, -51, 272), (-117, -51, 255),
        (-100, -64, 254), (-95, -70, 253)], dia="2.5")
    _em(ctx, wr.Name, "FLY_MOTOR_R")
    _cn(ctx, wr.Name, "TURRET_PLATE")
    wsv = _wire(doc, ctx, "WIRE_HOOD_SV", [
        (-84, -80, 330), (-92, -64, 300), (-98, -52, 274),
        (-115, -32, 272), (-113, -52, 272), (-113, -52, 255),
        (-102, -62, 254), (-98, -68, 253)], dia="2")
    _em(ctx, wsv.Name, "HOOD_SERVO")
    _cn(ctx, wsv.Name, "TURRET_PLATE")
    wc = _wire(doc, ctx, "WIRE_CAM_USB", [
        (-8, 0, 288), (-30, -30, 278), (-84, -46, 272),
        (-110, -46, 272), (-114, -49, 272), (-114, -49, 255),
        (-104, -60, 254), (-98, -66, 253)], dia="3")
    _em(ctx, wc.Name, "VSN_CAM")
    _cn(ctx, wc.Name, "TURRET_PLATE")


# ======================================================================
# populate entry points
# ======================================================================
def build_turret(doc, ctx):
    """All turret content: static side + GRP_TURRET_ROT rotating stack."""
    for sgn in (1, -1):
        _tower(doc, ctx, sgn)
    _gusset(doc, ctx, 1, 0, "-176")
    _gusset(doc, ctx, 1, 1, "-26")
    _gusset(doc, ctx, -1, 2, "-176")
    _gusset(doc, ctx, -1, 3, "-26")
    _turret_deck(doc, ctx)
    _susan(doc, ctx)
    _yaw_drive(doc, ctx)
    _hall(doc, ctx)
    _ring(doc, ctx)
    _plate(doc, ctx)
    for sgn in (1, -1):
        _cheek(doc, ctx, sgn)
    for sgn in (1, -1):
        _fly_assy(doc, ctx, sgn)
    _hood(doc, ctx)
    _extras(doc, ctx)
    _turret_wires(doc, ctx)
    # swept-yaw probes (non-exportable): rotating-extreme markers at
    # 4 yaw angles (fly-motor rim + cheek corner), used by GEOT_yaw_sweep
    for i, ang in enumerate((0, 90, 180, 270)):
        a = math.radians(ang)
        px = -66 + 105 * math.cos(a)
        py = 105 * math.sin(a)
        _feat(doc, "VOL_YAW_%d" % i,
              "VOL_YAW_%d_probe_UNVERIFIED" % i,
              "UNVERIFIED - yaw-sweep extreme probe %d deg" % ang,
              Part.makeCylinder(3, 20, App.Vector(px, py, 300),
                                App.Vector(0, 0, 1)))


def populate_turret(doc, ctx):
    """turret.FCStd = frame context + turret solids."""
    ctx["sheet"] = _sheet(doc)
    build_frame(doc, ctx)
    build_turret(doc, ctx)
    _env(doc, ctx)
