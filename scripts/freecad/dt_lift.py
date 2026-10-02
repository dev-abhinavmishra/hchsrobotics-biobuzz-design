"""scripts/freecad/dt_lift.py -- sprint-03 flower lift + load chute.

Shared builders for the rear-left cascade mast (subsystem FCStd and the
master build both call populate_lift -- DET3 parity).

Mount chain:
    FRAME_RAIL_L top web -> LIFT_BASE (notched clear of TIE_RB_L) ->
    LIFT_RAIL_L/R posts (feet straddle base + splice-plate tops) ->
    LIFT_TOP_TIE + LIFT_TOP_PULLEY + ROPE_GUIDE ->
    STOP_COLLAR_* pinch stops ->
    stage-1: S1 trucks C-wrapped on the post inner faces -> slide
        blades -> LIFT_S1_TIE + traveling LIFT_PULLEY ->
    stage-2: S2 trucks keyed into the blade face slots -> LIFT_S2_BAR
        -> LIFT_S2_TIE ->
    CRADLE_ARM -> CRADLE_PIV top-rim hinge -> CRADLE C-cup + foam +
    TILT_SERVO (pin drive).  LIFT_WINCH + WINCH_SPOOL on the base,
    ROPE_DYNEEMA baked two-run rig, and the LOAD_CHUTE two-leg tray
    from the diverter port to the cradle bowl through the TOWER_L slot.

Deviations pinned here (documented in docs + robot_params comments):
  * cradle cup center sits at (cradle_x + 5, cradle_z + 3) -- the O110
    shell clears the mast post east face by 1.4mm and the parked bowl
    floor then lands the D93 ball center exactly on cradle_z = 140.
  * mast top runs ~z334 (posts 332.75 + tie) vs the contract's "~330"
    note -- the honest stack stays inside the envelope.
  * deployed cradle rim ~z585 (VOL_CRADLE_DEP) vs the "~566" sketch --
    stage travels keep >=40mm overlap; envelope gate only requires
    containment inside R105 / 736.5.
"""

import math

import FreeCAD as App
import Part
import Spreadsheet  # noqa: F401

import partkit as pk
from dt_build import (_s, _jm, _fp, _em, _jl, _cn, _bom, _wire,
                      _sheet, build_frame, _env)
from dt_path import _feat

B4 = "Parameters.bolt_d"
BHD = "Parameters.bolt_head_d"
BHH = "Parameters.bolt_head_h"
N4W = "Parameters.nut4_wrench"
N4H = "Parameters.nut4_h"
N4B = "Parameters.nut4_bore"

WEB_TOP = "(Parameters.rail_elev_z + Parameters.rail_size / 2)"  # 63.75
BASE_TOP = "(%s + 3)" % WEB_TOP                                # 66.75
LX = "Parameters.lift_x"
Y0 = "Parameters.lift_y0"   # 144 -> post L  y137..151, inner face 151
Y1 = "Parameters.lift_y1"   # 180 -> post R  y173..187, inner face 173

# chute polyline (ball-path bed line -- S15/S16 ride +46.5 normals).
# leg1 dives 32.6deg from the port so the D93 sphere clears the tower
# slot top at the wall crossing; leg2 dives 31deg under the cup mouth.
CHUTE_PTS = ((-66.0, 56.0, 204.0), (-100.0, 150.0, 140.0),
             (-118.0, 178.0, 120.0))
CHUTE_W = 97.0
# leg-2 bed/lip extension past the path end into the cradle bowl
CHUTE_EXT = 8.0


def _bolt(doc, ctx, name, pos, axis, length="12"):
    pk.bolt(doc, name, name + "_M4x%s_UNVERIFIED" % length,
            "UNVERIFIED - M4 bolt", B4, length, BHD, BHH, pos, axis)
    _s(ctx, doc.getObject(name))
    return name


def _nut(doc, ctx, name, px, py, pz):
    pk.hex_nut(doc, name, name + "_M4_UNVERIFIED",
               "UNVERIFIED - M4 nylock", N4W, N4H, N4B,
               {"Placement.Base.x": px, "Placement.Base.y": py,
                "Placement.Base.z": pz}, "Z")
    _s(ctx, doc.getObject(name))
    return name


def _screw(doc, ctx, name, pos, axis, length="8"):
    pk.bolt(doc, name, name + "_M3x%s_UNVERIFIED" % length,
            "UNVERIFIED - M3 selftap", "3.2", length, "5.5", "2.0",
            pos, axis)
    _s(ctx, doc.getObject(name))
    return name


# ======================================================================
# mast base + rails + top tie + collars
# ======================================================================
def _base(doc, ctx):
    blk = pk.tool_box(
        doc, "TOOL_LBASE_BLK",
        {"Length": "51", "Width": "48", "Height": "3"},
        {"Placement.Base.x": "-183", "Placement.Base.y": "137",
         "Placement.Base.z": WEB_TOP})
    # notch the west edge clear of TIE_RB_L's east edge
    # (tie x -213.1..-183.1 vs base x -183..; 0.1mm overlap trimmed)
    notch = pk.tool_box(
        doc, "TOOL_LBASE_NT",
        {"Length": "3.5", "Width": "30", "Height": "7"},
        {"Placement.Base.x": "-184.5", "Placement.Base.y": "136",
         "Placement.Base.z": "(%s - 2)" % WEB_TOP})
    # south-edge trim: base lip clears the RL wheel plate inner face
    notch2 = pk.tool_box(
        doc, "TOOL_LBASE_NT2",
        {"Length": "41", "Width": "2.2", "Height": "5"},
        {"Placement.Base.x": "-173",
         "Placement.Base.y": "183.9",
         "Placement.Base.z": "(%s - 1)" % WEB_TOP})
    base = pk.cut(doc, "LIFT_BASE", "LIFT_BASE_3mm_alu_UNVERIFIED",
                  "UNVERIFIED - lift base plate 3mm alu (notch clears "
                  "TIE_RB_L)", blk, [notch, notch2])
    _s(ctx, base)
    _bom(ctx, "lift", "lift base plate 3mm alu", "aluminum", "43x48x3",
         "UNVERIFIED", [base.Name])
    _fp(ctx, base.Name, "FRAME_RAIL_L")
    _cn(ctx, base.Name, "TIE_RB_L")
    bolts, nuts = [], []
    for i, (px, py) in enumerate((("-160", "140"), ("-160", "180"),
                                  ("-145", "142"), ("-145", "178"))):
        bn = "BOLT_LB_%d" % i
        nn = "NUT_LB_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(%s + 3 + Parameters.bolt_head_h)" % WEB_TOP},
              "-Z", "9")
        _nut(doc, ctx, nn, "(%s)" % px,
             "(%s)" % py,
             "(%s - 2.6 - Parameters.nut4_h)" % WEB_TOP)
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "lift_base", [base.Name, "FRAME_RAIL_L"], bolts, nuts,
        "FRAME_RAIL_L")


def _rails(doc, ctx):
    """14x14 guide posts standing on the base+splice top plane (66.75),
    foot tabs to the east bolted through base + rail web."""
    for sgn, tag in ((1, "L"), (-1, "R")):
        cy = Y0 if sgn > 0 else Y1
        blk = pk.tool_box(
            doc, "TOOL_LR_%s_BLK" % tag,
            {"Length": "14", "Width": "14",
             "Height": "Parameters.lift_rail_len"},
            {"Placement.Base.x": "(%s - 7)" % LX,
             "Placement.Base.y": "(%s - 7)" % cy,
             "Placement.Base.z": BASE_TOP})
        tools = []
        if sgn > 0:
            # pocket clears the TIE_RB_L bolt head at (-184.1, 152):
            # head O7x4 tops at z70.75
            tools.append(pk.tool_box(
                doc, "TOOL_LR_L_PK",
                {"Length": "14", "Width": "14", "Height": "5.5"},
                {"Placement.Base.x": "-193",
                 "Placement.Base.y": "143",
                 "Placement.Base.z": "(%s - 1)" % BASE_TOP}))
        else:
            # NE pass-through notch: the cradle arm ear + top bridge,
            # tilt servo can, servo screws and the hinge pin all cross
            # the post's top NE corner
            tools.append(pk.tool_box(
                doc, "TOOL_LR_R_CR",
                {"Length": "15.5", "Width": "29", "Height": "131.5"},
                {"Placement.Base.x": "-193.9",
                 "Placement.Base.y": "171.5",
                 "Placement.Base.z": "184.5"}))
        if tools:
            post = pk.cut(doc, "LIFT_RAIL_%s" % tag,
                          "LIFT_RAIL_%s_14x14_UNVERIFIED" % tag,
                          "UNVERIFIED - lift guide post 14x14",
                          blk, tools)
        else:
            post = pk.box(
                doc, "LIFT_RAIL_%s" % tag,
                "LIFT_RAIL_%s_14x14_UNVERIFIED" % tag,
                "UNVERIFIED - lift guide post 14x14",
                {"Length": "14", "Width": "14",
                 "Height": "Parameters.lift_rail_len"},
                {"Placement.Base.x": "(%s - 7)" % LX,
                 "Placement.Base.y": "(%s - 7)" % cy,
                 "Placement.Base.z": BASE_TOP})
        _s(ctx, post)
        fy = "137" if sgn > 0 else "173"
        fw_ = "14" if sgn > 0 else "11"
        foot = pk.box(
            doc, "LIFT_FOOT_%s" % tag,
            "LIFT_FOOT_%s_UNVERIFIED" % tag,
            "UNVERIFIED - lift rail foot tab",
            {"Length": "14.4", "Width": fw_, "Height": "3"},
            {"Placement.Base.x": "-178.4", "Placement.Base.y": fy,
             "Placement.Base.z": BASE_TOP})
        _s(ctx, foot)
        _bom(ctx, "lift", "guide post 14x14 extrusion", "aluminum",
             "14x14x269", "UNVERIFIED", [post.Name])
        _bom(ctx, "lift", "rail foot tab 3mm", "aluminum", "14x14x3",
             "UNVERIFIED", [foot.Name])
        _fp(ctx, post.Name, "LIFT_BASE")
        _fp(ctx, post.Name, "TIE_RB_L")
        _fp(ctx, foot.Name, "LIFT_BASE")
        bolts, nuts = [], []
        ys = ("140", "148") if sgn > 0 else ("176", "182")
        for i, py in enumerate(ys):
            bn = "BOLT_LRF_%s%d" % (tag, i)
            nn = "NUT_LRF_%s%d" % (tag, i)
            _bolt(doc, ctx, bn,
                  {"Placement.Base.x": "-172", "Placement.Base.y": py,
                   "Placement.Base.z":
                   "(%s + 3 + Parameters.bolt_head_h)" % BASE_TOP},
                  "-Z", "12")
            _nut(doc, ctx, nn,
                 "(-172)",
                 "(%s)" % py,
                 "(%s - 2.6 - Parameters.nut4_h)" % WEB_TOP)
            bolts.append(bn)
            nuts.append(nn)
        _jm(ctx, "rail_foot_%s" % tag.lower(),
            [foot.Name, post.Name, "LIFT_BASE", "FRAME_RAIL_L"],
            bolts, nuts, "LIFT_BASE")
    # top tie: bar between the post inner faces near the tops
    tblk = pk.tool_box(
        doc, "TOOL_LTT_BLK",
        {"Length": "17", "Width": "22", "Height": "8"},
        {"Placement.Base.x": "-194", "Placement.Base.y": "151",
         "Placement.Base.z": "(Parameters.stop_z)"})
    # clevis ears protrude EAST of the tie face so the top pulley
    # clears both the tie body and the traveling pulley below
    ears = []
    for y0 in ("157", "166"):
        ears.append(pk.tool_box(
            doc, "TOOL_LTT_EAR%s" % y0,
            {"Length": "25", "Width": "2", "Height": "10"},
            {"Placement.Base.x": "-180", "Placement.Base.y": y0,
             "Placement.Base.z": "(Parameters.stop_z - 11)"}))
    tie = pk.fuse(doc, "LIFT_TOP_TIE", "LIFT_TOP_TIE_UNVERIFIED",
                  "UNVERIFIED - mast top tie + pulley ears", tblk, ears)
    _s(ctx, tie)
    _bom(ctx, "lift", "mast top tie", "aluminum", "17x22x8",
         "UNVERIFIED", [tie.Name])
    _fp(ctx, tie.Name, "LIFT_RAIL_L")
    _fp(ctx, tie.Name, "LIFT_RAIL_R")
    bolts = []
    for i, (px, pz) in enumerate((("-190", "330"), ("-182", "330"))):
        bn = "BOLT_LTT_L%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": "134.6",
               "Placement.Base.z": pz}, "Y", "17")
        bolts.append(bn)
    for i, (px, pz) in enumerate((("-190", "330"), ("-182", "330"))):
        bn = "BOLT_LTT_R%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": "189.4",
               "Placement.Base.z": pz}, "-Y", "17")
        bolts.append(bn)
    _jm(ctx, "lift_top_tie", [tie.Name, "LIFT_RAIL_L", "LIFT_RAIL_R"],
        bolts, terminal=tie.Name)
    # static top pulley on a pin between the east clevis ears
    pin = pk.cyl(doc, "LIFT_TPIN", "LIFT_TPIN_O6_UNVERIFIED",
                 "UNVERIFIED - top pulley pin O6",
                 {"Radius": "3", "Height": "14"},
                 {"Placement.Base.x": "-156", "Placement.Base.y": "157",
                  "Placement.Base.z": "(Parameters.stop_z - 4.5)"},
                 pk.axis_rot("Y"))
    _s(ctx, pin)
    _em(ctx, pin.Name, tie.Name)
    pul = pk.bore_cyl(doc, "LIFT_TOP_PULLEY",
                      "LIFT_TOP_PULLEY_O20_UNVERIFIED",
                      "UNVERIFIED - top rope pulley O20",
                      "20", "5", "6.5",
                      {"Placement.Base.x": "-156",
                       "Placement.Base.y": "160",
                       "Placement.Base.z": "(Parameters.stop_z - 4.5)"},
                      "Y")
    _s(ctx, pul)
    _bom(ctx, "lift", "rope pulley O20", "delrin", "O20x6.5",
         "VENDOR-PENDING", [pul.Name])
    _jl(ctx, pul.Name, pin.Name)
    eye = pk.bore_cyl(doc, "ROPE_GUIDE", "ROPE_GUIDE_eyelet_UNVERIFIED",
                      "UNVERIFIED - rope guide eyelet",
                      "12", "3", "8",
                      {"Placement.Base.x": "-186",
                       "Placement.Base.y": "170",
                       "Placement.Base.z": "(Parameters.stop_z + 4)"},
                      "Y")
    _s(ctx, eye)
    _fp(ctx, eye.Name, tie.Name)
    # stop collars: pinch rings on the posts capping stage-1 travel;
    # collar top face = stop_z
    for sgn, tag in ((1, "L"), (-1, "R")):
        cy = Y0 if sgn > 0 else Y1
        blk = pk.tool_box(
            doc, "TOOL_SC_%s_BLK" % tag,
            {"Length": "19.9", "Width": "16", "Height": "8"},
            {"Placement.Base.x": "(%s - 9.5)" % LX,
             "Placement.Base.y": "(%s - 8)" % cy,
             "Placement.Base.z": "(Parameters.stop_z - 8)"})
        hole = pk.tool_box(
            doc, "TOOL_SC_%s_HL" % tag,
            {"Length": "14.5", "Width": "14.5", "Height": "10"},
            {"Placement.Base.x": "(%s - 7.25)" % LX,
             "Placement.Base.y": "(%s - 7.25)" % cy,
             "Placement.Base.z": "(Parameters.stop_z - 9)"})
        col = pk.cut(doc, "STOP_COLLAR_%s" % tag,
                     "STOP_COLLAR_%s_UNVERIFIED" % tag,
                     "UNVERIFIED - stage-1 hard-stop collar",
                     blk, [hole])
        _s(ctx, col)
        rail = "LIFT_RAIL_%s" % tag
        _cn(ctx, col.Name, rail)
        _em(ctx, col.Name, rail)
        bolts = []
        for bi, bx in enumerate(("-186.9", "-178.9")):
            bn = "BOLT_SC_%s%d" % (tag, bi)
            # R bolt reverses: head on the collar's north face so the
            # south tip lands flush on the top-tie face instead of the
            # head being buried inside the tie
            _bolt(doc, ctx, bn,
                  {"Placement.Base.x": bx,
                   "Placement.Base.y": (
                       "(%s - 8 - Parameters.bolt_head_h)" % cy
                       if sgn > 0 else
                       "(%s + 8 + Parameters.bolt_head_h)" % cy),
                   "Placement.Base.z": "(Parameters.stop_z - 2.5)"},
                  "Y" if sgn > 0 else "-Y", "15")
            bolts.append(bn)
        _jm(ctx, "collar_%s" % tag.lower(), [col.Name, rail],
            bolts, terminal=col.Name)


# ======================================================================
# stage 1: C-wrap trucks on the post inner faces -> blades -> tie
# ======================================================================
def _stage1(doc, ctx):
    for sgn, tag in ((1, "L"), (-1, "R")):
        cy = Y0 if sgn > 0 else Y1
        blade = "LIFT_S1_BAR_%s" % tag
        for zi, z0 in enumerate(("80", "104")):
            nm = "LIFT_S1_TRUCK_%s%d" % (tag, zi)
            # flat delrin slide pad filling the post-to-blade gap
            # (post inner faces y151/y173; blade faces y155/y169);
            # x-extent stays inside the rail pair footprint
            if sgn > 0:
                pady = "(%s + 7)" % cy          # 151..155
            else:
                pady = "(%s - 11)" % cy         # 169..173
            tr = pk.box(
                doc, nm, nm + "_delrin_UNVERIFIED",
                "UNVERIFIED - stage-1 slide pad (on post inner face)",
                {"Length": "7.9", "Width": "4", "Height": "20"},
                {"Placement.Base.x": "-192.4", "Placement.Base.y": pady,
                 "Placement.Base.z": z0})
            _s(ctx, tr)
            rail = "LIFT_RAIL_%s" % tag
            _cn(ctx, tr.Name, rail)
            _fp(ctx, tr.Name, blade)
            bolts = []
            for bi, bz in enumerate(("8", "16")):
                bn = "SCRW_S1T_%s%d_%d" % (tag, zi, bi)
                if sgn > 0:
                    pos = {"Placement.Base.x": "-187.5",
                           "Placement.Base.y": "(%s + 17.5)" % cy,
                           "Placement.Base.z": "(%s + %s)" % (z0, bz)}
                    ax = "-Y"
                else:
                    pos = {"Placement.Base.x": "-187.5",
                           "Placement.Base.y": "(%s - 17.5)" % cy,
                           "Placement.Base.z":
                           "(%s + %s - 4)" % (z0, bz)}
                    ax = "Y"
                _screw(doc, ctx, bn, pos, ax, "10")
                bolts.append(bn)
            _jm(ctx, "s1truck_%s%d" % (tag.lower(), zi),
                [tr.Name, blade, rail], bolts, terminal=blade)
        # slide blade: on the pad inner faces, S2 guide slot east
        by = ("(%s + 11)" % cy) if sgn > 0 else "(%s - 15.5)" % cy
        blk = pk.tool_box(
            doc, "TOOL_S1B_%s_BLK" % tag,
            {"Length": "10", "Width": "4.5",
             "Height": "Parameters.s1_len"},
            {"Placement.Base.x": "-190", "Placement.Base.y": by,
             "Placement.Base.z": "74"})
        slot = pk.tool_box(
            doc, "TOOL_S1B_%s_SL" % tag,
            {"Length": "5", "Width": "8", "Height": "222"},
            {"Placement.Base.x": "-185", "Placement.Base.y": "158",
             "Placement.Base.z": "78"})
        bl = pk.cut(doc, blade, blade + "_slide_UNVERIFIED",
                    "UNVERIFIED - stage-1 slide blade (S2 keyway)",
                    blk, [slot])
        _s(ctx, bl)
        _bom(ctx, "lift", "stage-1 slide blade 10mm", "aluminum",
             "10x4.5x239", "UNVERIFIED", [bl.Name])
    # tie across the blade tops (blades z74..313); clevis ears hang
    # BELOW the tie bottom so the traveling pulley clears the top tie
    ears = []
    for y0 in ("157", "166"):
        ears.append(pk.tool_box(
            doc, "TOOL_S1T_EAR%s" % y0,
            {"Length": "6", "Width": "2", "Height": "18"},
            {"Placement.Base.x": "-191.5", "Placement.Base.y": y0,
             "Placement.Base.z": "297"}))
    tblk = pk.tool_box(
        doc, "TOOL_S1T_BLK",
        {"Length": "11", "Width": "18", "Height": "8"},
        {"Placement.Base.x": "-191", "Placement.Base.y": "153",
         "Placement.Base.z": "(74 + Parameters.s1_len)"})
    tie = pk.fuse(doc, "LIFT_S1_TIE", "LIFT_S1_TIE_UNVERIFIED",
                  "UNVERIFIED - stage-1 tie + traveling pulley ears",
                  tblk, ears)
    _s(ctx, tie)
    _bom(ctx, "lift", "stage-1 tie", "aluminum", "12x18x8",
         "UNVERIFIED", [tie.Name])
    _fp(ctx, tie.Name, "LIFT_S1_BAR_L")
    _fp(ctx, tie.Name, "LIFT_S1_BAR_R")
    bolts = []
    for i, (px, py) in enumerate((("-188", "157"), ("-184", "157"),
                                  ("-188", "166.5"), ("-184", "166.5"))):
        bn = "BOLT_S1TIE_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(74 + Parameters.s1_len + 8 + Parameters.bolt_head_h)"},
              "-Z", "10")
        bolts.append(bn)
    _jm(ctx, "s1_tie", [tie.Name, "LIFT_S1_BAR_L", "LIFT_S1_BAR_R"],
        bolts, terminal=tie.Name)
    pin = pk.cyl(doc, "S1_PPIN", "S1_PPIN_O6_UNVERIFIED",
                 "UNVERIFIED - traveling pulley pin O6",
                 {"Radius": "3", "Height": "14"},
                 {"Placement.Base.x": "-188.5", "Placement.Base.y": "157",
                  "Placement.Base.z": "302"},
                 pk.axis_rot("Y"))
    _s(ctx, pin)
    _em(ctx, pin.Name, tie.Name)
    _em(ctx, pin.Name, "LIFT_S1_BAR_L")
    _em(ctx, pin.Name, "LIFT_S1_BAR_R")
    pul = pk.bore_cyl(doc, "LIFT_PULLEY", "LIFT_PULLEY_O20_UNVERIFIED",
                      "UNVERIFIED - traveling pulley O20",
                      "20", "4", "6.5",
                      {"Placement.Base.x": "-188.5",
                       "Placement.Base.y": "160",
                       "Placement.Base.z": "302"},
                      "Y")
    _s(ctx, pul)
    _bom(ctx, "lift", "traveling pulley O20", "delrin", "O20x6.5",
         "VENDOR-PENDING", [pul.Name])
    _jl(ctx, pul.Name, pin.Name)


# ======================================================================
# stage 2: keyed trucks in the blade slots -> bar -> tie
# ======================================================================
def _stage2(doc, ctx):
    bar = pk.box(doc, "LIFT_S2_BAR", "LIFT_S2_BAR_UNVERIFIED",
                 "UNVERIFIED - stage-2 slide bar",
                 {"Length": "7.9", "Width": "16",
                  "Height": "Parameters.s2_len"},
                 {"Placement.Base.x": "-177.7", "Placement.Base.y": "154",
                  "Placement.Base.z": "82"})
    _s(ctx, bar)
    _bom(ctx, "lift", "stage-2 bar", "aluminum", "7.9x16x218",
         "UNVERIFIED", [bar.Name])
    for zi, z0 in enumerate(("88", "112")):
        nm = "LIFT_S2_TRUCK_%d" % zi
        plug = pk.tool_box(
            doc, "TOOL_%s_PLUG" % nm,
            {"Length": "4.5", "Width": "7", "Height": "20"},
            {"Placement.Base.x": "-184.3", "Placement.Base.y": "158.5",
             "Placement.Base.z": z0})
        flng = pk.tool_box(
            doc, "TOOL_%s_FLNG" % nm,
            {"Length": "2.1", "Width": "18", "Height": "20"},
            {"Placement.Base.x": "-179.8", "Placement.Base.y": "153",
             "Placement.Base.z": z0})
        tr = pk.fuse(doc, nm, nm + "_delrin_UNVERIFIED",
                     "UNVERIFIED - stage-2 keyed slide truck",
                     plug, [flng])
        _s(ctx, tr)
        _cn(ctx, tr.Name, "LIFT_S1_BAR_L")
        _cn(ctx, tr.Name, "LIFT_S1_BAR_R")
        _fp(ctx, tr.Name, bar.Name)
        bolts = []
        for bi, by_ in enumerate(("157", "167")):
            bn = "SCRW_S2T_%d_%d" % (zi, bi)
            _screw(doc, ctx, bn,
                   {"Placement.Base.x": "-167.8",
                    "Placement.Base.y": by_,
                    "Placement.Base.z": "(%s + 10)" % z0},
                   "-X", "11")
            bolts.append(bn)
        _jm(ctx, "s2truck_%d" % zi, [tr.Name, bar.Name,
                                     "LIFT_S1_BAR_L", "LIFT_S1_BAR_R"],
            bolts, terminal=bar.Name)
    tie = pk.box(doc, "LIFT_S2_TIE", "LIFT_S2_TIE_UNVERIFIED",
                 "UNVERIFIED - stage-2 tie (rope dead-end)",
                 {"Length": "14.9", "Width": "24", "Height": "8"},
                 {"Placement.Base.x": "-178.4", "Placement.Base.y": "152",
                  "Placement.Base.z": "(82 + Parameters.s2_len)"})
    _s(ctx, tie)
    _bom(ctx, "lift", "stage-2 tie", "aluminum", "13x24x8",
         "UNVERIFIED", [tie.Name])
    _fp(ctx, tie.Name, bar.Name)
    bolts = []
    for i, (px, py) in enumerate((("-175.25", "155"), ("-175.25", "163"),
                                  ("-175.25", "167.5"))):
        bn = "BOLT_S2TIE_%d" % i
        _screw(doc, ctx, bn,
               {"Placement.Base.x": px, "Placement.Base.y": py,
                "Placement.Base.z":
                "(82 + Parameters.s2_len + 8 + 2)"},
               "-Z", "12")
        bolts.append(bn)
    _jm(ctx, "s2_tie", [tie.Name, bar.Name], bolts, terminal=tie.Name)


# ======================================================================
# cradle arm + cup + tilt (top-rim hinge pin drive)
# ======================================================================
def _cradle(doc, ctx):
    # arm = tab on the S2 tie + 3.6mm riser plate hugging the bar's
    # east face + top bar spanning west to the journal ear column.
    # The ear (x -186..-178, y184..200 -- north of the rail pair's
    # y<=180 band) carries the pin journal; the whole frame stays west
    # of the S16 D93 ball sweep (ball west reach ~x-163).
    tab = Part.makeBox(10, 16, 5, App.Vector(-172, 160, 308))
    plate = Part.makeBox(3.6, 10, 129, App.Vector(-169.6, 164, 185))
    top = Part.makeBox(20.6, 24, 8, App.Vector(-186, 172, 306))
    ear = Part.makeBox(8, 16, 126, App.Vector(-186, 184, 188))
    arm = tab.fuse(plate).fuse(top).fuse(ear).removeSplitter()
    # pin journal bore O8.6 along X through the ear column
    jbore = Part.makeCylinder(4.3, 36, App.Vector(-190, 190, 194),
                              App.Vector(1, 0, 0))
    arm = arm.cut(jbore).removeSplitter()
    ao = _feat(doc, "CRADLE_ARM", "CRADLE_ARM_alu_UNVERIFIED",
               "UNVERIFIED - cradle cantilever arm (tab on S2 tie)",
               arm)
    _s(ctx, ao)
    _bom(ctx, "lift", "cradle arm", "aluminum", "cantilever",
         "UNVERIFIED", [ao.Name])
    _fp(ctx, ao.Name, "LIFT_S2_TIE")
    # riser plate edge embeds 2.6mm into the tie east face
    _em(ctx, ao.Name, "LIFT_S2_TIE")
    bolts = []
    for i, (px, py) in enumerate((("-170.5", "162.5"), ("-170.5", "172"))):
        bn = "BOLT_CARM_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z": "(313 + Parameters.bolt_head_h)"},
              "-Z", "12")
        bolts.append(bn)
    # plus 2 screws driven up through the S2 tie into the tab
    for i, (px, py) in enumerate((("-166.3", "164.5"), ("-166.3", "170"))):
        sn = "SCRW_CARM_%d" % i
        _screw(doc, ctx, sn,
               {"Placement.Base.x": px, "Placement.Base.y": py,
                "Placement.Base.z": "298"},
               "Z", "13")
        bolts.append(sn)
    _jm(ctx, "cradle_arm", [ao.Name, "LIFT_S2_TIE"], bolts,
        terminal=ao.Name)
    # cradle cup: O110 shell, O99 bore, closed +Y back disc, top C-notch
    ring = pk.bore_cyl(
        doc, "TOOL_CUP_BLK",
        "CRADLE_shell_UNVERIFIED", "UNVERIFIED - cradle cup shell",
        "110", "18", "Parameters.cradle_id",
        {"Placement.Base.x": "(Parameters.cradle_x + 5)",
         "Placement.Base.y": "(Parameters.cradle_y - 4)",
         "Placement.Base.z": "(Parameters.cradle_z + 3)"},
        "Y")
    back = pk.tool_cyl(
        doc, "TOOL_CUP_BACK",
        {"Radius": "55", "Height": "3"},
        {"Placement.Base.x": "(Parameters.cradle_x + 5)",
         "Placement.Base.y": "(Parameters.cradle_y + 11)",
         "Placement.Base.z": "(Parameters.cradle_z + 3)"},
        pk.axis_rot("Y"))
    cf = pk.fuse(doc, "TOOL_CUP_F", "CRADLE_f_UNVERIFIED",
                 "UNVERIFIED - cradle cup fused", ring, [back])
    wedge = pk.tool_box(
        doc, "TOOL_CUP_WEDGE",
        {"Length": "20", "Width": "26", "Height": "30"},
        {"Placement.Base.x": "(Parameters.cradle_x - 5)",
         "Placement.Base.y": "(Parameters.cradle_y - 8)",
         "Placement.Base.z": "(Parameters.cradle_z + 27)"})
    # rim scallop over the RL wheel plate/roller band (plate top z94);
    # stays below the O99 bore floor so the ball seat is untouched
    scall = pk.tool_box(
        doc, "TOOL_CUP_SCALL",
        {"Length": "40", "Width": "8", "Height": "35"},
        {"Placement.Base.x": "-145",
         "Placement.Base.y": "182.5",
         "Placement.Base.z": "60"})
    cup = pk.cut(doc, "CRADLE_CUP", "CRADLE_O110_cup_UNVERIFIED",
                 "UNVERIFIED - Nectar C-cup O99 bore + back", cf,
                 [wedge, scall])
    _s(ctx, cup)
    _bom(ctx, "lift", "cradle C-cup O99 bore", "petg", "O110x21",
         "UNVERIFIED", [cup.Name])
    foam = pk.bore_cyl(
        doc, "CRADLE_FOAM", "CRADLE_FOAM_UNVERIFIED",
        "UNVERIFIED - cradle foam liner",
        "(Parameters.cradle_id - 1)", "15",
        "(Parameters.cradle_id - 7)",
        {"Placement.Base.x": "(Parameters.cradle_x + 5)",
         "Placement.Base.y": "(Parameters.cradle_y - 3)",
         "Placement.Base.z": "(Parameters.cradle_z + 3)"},
        "Y")
    _s(ctx, foam)
    _bom(ctx, "lift", "cradle foam liner", "foam", "O98x15",
         "UNVERIFIED", [foam.Name])
    _em(ctx, foam.Name, cup.Name)
    # hinge pin along X across the shell top strips; journals in the
    # arm ear bore; tilt servo horn engages the west overhang
    pin = pk.cyl(doc, "CRADLE_PIV", "CRADLE_PIV_O8_UNVERIFIED",
                 "UNVERIFIED - cradle hinge pin O8 (welded to cup)",
                 {"Radius": "4", "Height": "110"},
                 {"Placement.Base.x": "-194",
                  "Placement.Base.y": "(Parameters.cradle_y + 12)",
                  "Placement.Base.z": "(Parameters.cradle_z + 54)"},
                 pk.axis_rot("X"))
    _s(ctx, pin)
    _em(ctx, pin.Name, cup.Name)
    _em(ctx, pin.Name, foam.Name)
    _jl(ctx, pin.Name, ao.Name)
    # retaining collars flank the ear/plate journals
    for i, px in enumerate(("-178", "-165.4")):
        col = pk.bore_cyl(doc, "CRADLE_COL_%d" % i,
                          "CRADLE_COL_%d_UNVERIFIED" % i,
                          "UNVERIFIED - hinge pin collar",
                          "14", "5", "8.5",
                          {"Placement.Base.x": px,
                           "Placement.Base.y":
                           "(Parameters.cradle_y + 12)",
                           "Placement.Base.z":
                           "(Parameters.cradle_z + 54)"},
                          "X")
        _s(ctx, col)
        _em(ctx, col.Name, pin.Name)
    _jm(ctx, "cradle_piv", [cup.Name, ao.Name], [pin.Name], (),
        terminal=ao.Name)
    # tilt servo: can face-mounted on the ear west face, pin blind-
    # pocketed through the can bore, horn boss bored onto the pin end
    cblk = pk.tool_box(
        doc, "TOOL_TSV_CAN",
        {"Length": "10", "Width": "14", "Height": "12"},
        {"Placement.Base.x": "-196", "Placement.Base.y": "184",
         "Placement.Base.z": "188"})
    cbore = pk.tool_cyl(
        doc, "TOOL_TSV_CB", {"Radius": "4.3", "Height": "12"},
        {"Placement.Base.x": "-197",
         "Placement.Base.y": "(Parameters.cradle_y + 12)",
         "Placement.Base.z": "(Parameters.cradle_z + 54)"},
        pk.axis_rot("X"))
    can = pk.cut(doc, "TOOL_TSV_CB2", "TSV_can_UNVERIFIED",
                 "UNVERIFIED - tilt servo can (pin pocket)", cblk,
                 [cbore])
    hblk = pk.tool_box(
        doc, "TOOL_TSV_HRN",
        {"Length": "6", "Width": "12", "Height": "12"},
        {"Placement.Base.x": "-194", "Placement.Base.y": "184",
         "Placement.Base.z": "188"})
    hbore = pk.tool_cyl(
        doc, "TOOL_TSV_HB", {"Radius": "4.15", "Height": "8"},
        {"Placement.Base.x": "-195",
         "Placement.Base.y": "(Parameters.cradle_y + 12)",
         "Placement.Base.z": "(Parameters.cradle_z + 54)"},
        pk.axis_rot("X"))
    horn = pk.cut(doc, "TOOL_TSV_HBN", "TSV_horn_UNVERIFIED",
                  "UNVERIFIED - tilt servo horn boss", hblk, [hbore])
    sv = pk.fuse(doc, "TILT_SERVO", "TILT_SERVO_micro_UNVERIFIED",
                 "UNVERIFIED - cradle tilt servo (pin drive)",
                 can, [horn])
    _s(ctx, sv)
    _bom(ctx, "lift", "tilt micro servo", "servo", "12x14x16",
         "VENDOR-PENDING", [sv.Name])
    _fp(ctx, sv.Name, ao.Name)
    _jl(ctx, pin.Name, sv.Name)
    bolts = []
    for i, (py, pz) in enumerate((("185", "190"), ("185.5", "199"),
                                  ("196", "190.5"), ("196.5", "199"))):
        bn = "SCRW_TSV_%d" % i
        _screw(doc, ctx, bn,
               {"Placement.Base.x": "-198", "Placement.Base.y": py,
                "Placement.Base.z": pz},
               "X", "16")
        bolts.append(bn)
    _jm(ctx, "tilt_servo", [sv.Name, ao.Name], bolts,
        terminal=ao.Name)


# ======================================================================
# winch + rope rig
# ======================================================================
def _winch(doc, ctx):
    # winch body east of the stage-2 bar sweep (bar face -169.8)
    blk = pk.tool_box(
        doc, "TOOL_LW_BLK",
        {"Length": "22", "Width": "20", "Height": "Parameters.winch_z"},
        {"Placement.Base.x": "-158", "Placement.Base.y": "150",
         "Placement.Base.z": BASE_TOP})
    ears = []
    for y0 in ("152", "166"):
        ears.append(pk.tool_box(
            doc, "TOOL_LW_EAR%s" % y0,
            {"Length": "16", "Width": "2", "Height": "35"},
            {"Placement.Base.x": "-155", "Placement.Base.y": y0,
             "Placement.Base.z": BASE_TOP}))
    wb = pk.fuse(doc, "LIFT_WINCH", "LIFT_WINCH_CRservo_UNVERIFIED",
                 "UNVERIFIED - lift winch CR servo + drum ears",
                 blk, ears)
    _s(ctx, wb)
    _bom(ctx, "lift", "winch CR servo", "servo", "22x20x50.8",
         "VENDOR-PENDING", [wb.Name])
    _fp(ctx, wb.Name, "LIFT_BASE")
    bolts, nuts = [], []
    for i, (px, py) in enumerate((("-152", "158"), ("-152", "166"),
                                  ("-140", "158"), ("-140", "166"))):
        bn = "BOLT_LW_%d" % i
        nn = "NUT_LW_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": py,
               "Placement.Base.z":
               "(%s + 3 + Parameters.bolt_head_h)" % WEB_TOP},
              "-Z", "9")
        _nut(doc, ctx, nn, "(%s)" % px,
             "(%s)" % py,
             "(%s - 2.6 - Parameters.nut4_h)" % WEB_TOP)
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "lift_winch", [wb.Name, "LIFT_BASE", "FRAME_RAIL_L"],
        bolts, nuts, "LIFT_BASE")
    pin = pk.cyl(doc, "WINCH_DPIN", "WINCH_DPIN_O6_UNVERIFIED",
                 "UNVERIFIED - winch drum pin O6",
                 {"Radius": "3", "Height": "16"},
                 {"Placement.Base.x": "-147", "Placement.Base.y": "152",
                  "Placement.Base.z": "(%s + 30)" % BASE_TOP},
                 pk.axis_rot("Y"))
    _s(ctx, pin)
    _em(ctx, pin.Name, wb.Name)
    spool = pk.bore_cyl(
        doc, "WINCH_SPOOL", "WINCH_SPOOL_O22_UNVERIFIED",
        "UNVERIFIED - winch drum O22", "22", "11", "6.5",
        {"Placement.Base.x": "-147", "Placement.Base.y": "154.5",
         "Placement.Base.z": "(%s + 30)" % BASE_TOP},
        "Y")
    _s(ctx, spool)
    _bom(ctx, "lift", "winch drum O22", "aluminum", "O22x11",
         "UNVERIFIED", [spool.Name])
    _jl(ctx, spool.Name, pin.Name)
    # baked dyneema rig: run A winch->top pulley->S1 dead-end;
    # run B top-tie anchor->traveling pulley->S2 tie dead-end.
    # wrap vertices sit on an r11 circle around each O20 pulley so
    # the O1.5 rope (inner surface r10.25) grazes the groove.
    pts_a = [(-147, 160, 101), (-163, 156, 112), (-165, 155, 240),
             (-146.5, 162, 315.0), (-145, 162, 321.5),
             (-148.2, 162, 329.3), (-156, 162, 332.5),
             (-163.8, 162, 329.3), (-167.5, 162, 321.5),
             (-163.8, 169, 317.5), (-167, 172, 317.5),
             (-182, 168, 315)]
    ra = pk.wire_bundle(doc, "TOOL_ROPE_A", "TOOL_ROPE_A_UNVERIFIED",
                        "UNVERIFIED - rope run A", 1.5, pts_a)
    pts_b = [(-193, 168, 332),
             (-198.0, 162, 307.5), (-199.5, 162, 302),
             (-196.3, 162, 293.7), (-188.5, 162, 291),
             (-180.7, 162, 293.7), (-177.5, 162, 302),
             (-172, 166, 304)]
    rb = pk.wire_bundle(doc, "TOOL_ROPE_B", "TOOL_ROPE_B_UNVERIFIED",
                        "UNVERIFIED - rope run B", 1.5, pts_b)
    rope = pk.fuse(doc, "ROPE_DYNEEMA", "ROPE_DYNEEMA_UNVERIFIED",
                   "UNVERIFIED - dyneema lift line (2-run cascade)",
                   ra, [rb])
    _s(ctx, rope)
    _bom(ctx, "lift", "dyneema lift line O1.5", "dyneema", "2-run",
         "UNVERIFIED", [rope.Name])
    _em(ctx, rope.Name, "WINCH_SPOOL")
    # wrap vertices seat the rope ~1mm into each pulley groove
    _em(ctx, rope.Name, "LIFT_TOP_PULLEY")
    _em(ctx, rope.Name, "LIFT_PULLEY")
    _em(ctx, rope.Name, "LIFT_TOP_TIE")
    _em(ctx, rope.Name, "LIFT_S1_TIE")
    _em(ctx, rope.Name, "LIFT_S2_TIE")
    _em(ctx, rope.Name, "BOLT_S2TIE_2")
    _cn(ctx, rope.Name, "ROPE_GUIDE")


# ======================================================================
# load chute: two-leg tray, port -> mid-turn -> cradle bowl
# ======================================================================
def _frame_for(p0, p1):
    d = App.Vector(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    L = d.Length
    dx = App.Vector(d).normalize()
    wy_ = App.Vector(0, 0, 1).cross(dx)
    if wy_.Length < 1e-6:
        wy_ = App.Vector(0, 1, 0)
    wy_.normalize()
    nz = dx.cross(wy_)
    nz.normalize()
    return dx, wy_, nz, L


def _oriented_box(L, w, t, origin, rot):
    b = Part.makeBox(L, w, t)
    b.Placement = App.Placement(App.Vector(*origin), rot)
    return b


def _chute(doc, ctx):
    p0, p1, p2 = CHUTE_PTS
    d1, w1, n1, L1 = _frame_for(p0, p1)
    d2, w2, n2, L2 = _frame_for(p1, p2)
    r1 = App.Rotation(d1, w1, n1, "XYZ")
    r2 = App.Rotation(d2, w2, n2, "XYZ")
    # bed centered on the path line: local w spans -48.5..+48.5
    o1 = App.Vector(*p0) + w1 * (-CHUTE_W / 2)
    o2 = App.Vector(*p1) + w2 * (-CHUTE_W / 2)
    # leg-2 bed runs 8mm past the path end so the tip dips into the
    # cradle bowl; full width stays available far enough along the
    # leg for the west lip's screw to bite bed clear of the seat ball
    l1 = _oriented_box(L1, CHUTE_W, 4,
                       (o1.x, o1.y, o1.z), r1)
    l2 = _oriented_box(L2 + CHUTE_EXT, CHUTE_W, 4,
                       (o2.x, o2.y, o2.z), r2)
    tray = l1.fuse(l2)
    # taper only the last 6mm of the extended outlet to ~70 wide so
    # the tip drops inside the cradle rim (cup bore O99)
    for sgn in (1, -1):
        wedge = Part.makeBox(20, 25, 12)
        cor = (App.Vector(*p2) + d2 * (CHUTE_EXT - 6)
               + w2 * (35 if sgn > 0 else -60) - n2 * 2)
        wedge.Placement = App.Placement(cor, r2)
        tray = tray.cut(wedge)
    tray = tray.removeSplitter()
    ch = _feat(doc, "LOAD_CHUTE", "LOAD_CHUTE_petg_UNVERIFIED",
               "UNVERIFIED - load chute two-leg tray (28.5/21.8 deg)",
               tray)
    _s(ctx, ch)
    _bom(ctx, "lift", "load chute tray 4mm PETG", "petg",
         "two-leg 97 wide", "UNVERIFIED", [ch.Name])
    _em(ctx, ch.Name, "PORT_FLANGE")
    _cn(ctx, ch.Name, "FEED_COLUMN")
    # extended bed tip dips into the cradle bowl (declared embed)
    _em(ctx, ch.Name, "CRADLE_CUP")
    _em(ctx, ch.Name, "CRADLE_FOAM")
    # side lips flank each leg's bed edges; the tips start 3mm down-
    # slope so they stay outside the port window corner
    lip_objs = []
    for sgn, side in ((1, "L"), (-1, "R")):
        for li, (p_s, d_, w_, n_, L_, r_) in enumerate(
                ((p0, d1, w1, n1, L1, r1), (p1, d2, w2, n2, L2, r2))):
            # the west (L) leg-2 lip tracks the extended bed tip so a
            # screw station exists past the seat-ball sweep
            lipL = (L_ + CHUTE_EXT
                    if side == "L" and li == 1 else L_)
            lb = Part.makeBox(lipL - 3, 3, 14)
            edge = (App.Vector(*p_s) + d_ * 3
                    + w_ * (45.5 if sgn > 0 else -48.5) + n_ * 4)
            lb = lb.transformGeometry(
                App.Placement(edge, r_).toMatrix())
            nm = "CHUTE_LIP_%s%d" % (side, li + 1)
            lo = _feat(doc, nm, nm + "_UNVERIFIED",
                       "UNVERIFIED - chute side lip", lb)
            lip_objs.append((lo, p_s, d_, w_, n_, L_))
            _s(ctx, lo)
            _fp(ctx, lo.Name, ch.Name)
    _bom(ctx, "lift", "chute side lips", "petg", "3x14",
         "UNVERIFIED", [o[0].Name for o in lip_objs])
    # screws -Z through each lip into the bed. Station lists are
    # per-lip: the west leg-2 lip carries a single screw near its tip
    # (the whole mid-run sits inside the seat-ball sweep); the east
    # leg-2 lip carries three to keep the joint at 8 fasteners.
    LIP_TS = ((0.5, 0.72), (0.97,), (0.5, 0.8), (0.3, 0.52, 0.77))
    lip_bolts = []
    for i, (lo, p_s, d_, w_, n_, L_) in enumerate(lip_objs):
        for j, t in enumerate(LIP_TS[i]):
            pt = (App.Vector(*p_s) + d_ * (L_ * t) + w_ *
                  (47 if lo.Name.endswith("L1") or lo.Name.endswith("L2")
                   else -47) + n_ * 18)
            bn = "SCRW_CHL_%d_%d" % (i, j)
            _screw(doc, ctx, bn,
                   {"Placement.Base.x": "%.1f" % pt.x,
                    "Placement.Base.y": "%.1f" % pt.y,
                    "Placement.Base.z": "%.1f" % (pt.z + 2.0)},
                   "-Z", "16")
            _em(ctx, bn, lo.Name)
            _em(ctx, bn, ch.Name)
            lip_bolts.append(bn)
    # port ear: welded pad on the flange +Y face where the leg-1 west
    # lip exits the port mouth (x~-122 at y59); 2 bolts into the
    # flange ring annulus (r50..60)
    ear = Part.makeBox(8, 6, 10, App.Vector(-127.5, 59, 190))
    ear_o = _feat(doc, "CHUTE_PORT_EAR", "CHUTE_PORT_EAR_UNVERIFIED",
                  "UNVERIFIED - chute port mounting ear", ear)
    _s(ctx, ear_o)
    _em(ctx, ear_o.Name, "CHUTE_LIP_L1")
    _fp(ctx, ear_o.Name, "PORT_FLANGE")
    pfl_b = []
    for i, pz in enumerate(("193", "198")):
        bn = "BOLT_CHP_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": "-124",
               "Placement.Base.y": "67.4",
               "Placement.Base.z": pz},
              "-Y", "10")
        pfl_b.append(bn)
    _jm(ctx, "chute_lips",
        [o[0].Name for o in lip_objs] + [ch.Name],
        lip_bolts, (), ch.Name)
    _jm(ctx, "chute_mount", [ear_o.Name, "CHUTE_LIP_L1", ch.Name,
                             "PORT_FLANGE"],
        pfl_b, (), "PORT_FLANGE")
    # tower pad: sill strap east of the seat-ball sweep (x<-75.7),
    # standing in the port mouth and carrying the tray bottom as it
    # passes the wall; 2 bolts + nuts through the riser below the slot
    pad = Part.makeBox(14, 8.7, 64, App.Vector(-74, 132.3, 87))
    pd_o = _feat(doc, "CHUTE_TOWER_PAD", "CHUTE_TOWER_PAD_UNVERIFIED",
                 "UNVERIFIED - chute tower-slot sill strap", pad)
    _s(ctx, pd_o)
    _fp(ctx, pd_o.Name, "TOWER_L")
    _cn(ctx, pd_o.Name, "LOAD_CHUTE")
    tb, tn = [], []
    for i, px in enumerate(("-71", "-63")):
        bn = "BOLT_CHT_%d" % i
        nn = "NUT_CHT_%d" % i
        _bolt(doc, ctx, bn,
              {"Placement.Base.x": px, "Placement.Base.y": "143.4",
               "Placement.Base.z": "91"},
              "-Y", "16")
        pk.hex_nut(
            doc, nn, nn + "_M4_UNVERIFIED",
            "UNVERIFIED - M4 nylock",
            "Parameters.nut4_wrench", "Parameters.nut4_h",
            "Parameters.nut4_bore",
            {"Placement.Base.x": "(%s)" % px,
             "Placement.Base.y": "(129.3 - Parameters.nut4_h)",
             "Placement.Base.z": "(90.8)"},
            "Y")
        _s(ctx, doc.getObject(nn))
        tb.append(bn)
        tn.append(nn)
    _jm(ctx, "chute_tower", [pd_o.Name, "LOAD_CHUTE", "TOWER_L"],
        tb, tn, "TOWER_L")


# ======================================================================
# wiring + deployed probes
# ======================================================================
def _lift_wires(doc, ctx):
    # winch lead exits the drum, runs east above the rail web, then
    # drops to the hub bay east of the motor/clamp band
    ww = _wire(doc, ctx, "WIRE_WINCH", [
        (-147, 160, 84), (-152, 142, 74), (-90, 136, 70),
        (-88, 86, 50), (-100, 84, 46)], dia="2")
    _em(ctx, ww.Name, "LIFT_WINCH")
    _cn(ctx, ww.Name, "LIFT_BASE")
    _em(ctx, ww.Name, "WIRE_TILT_SV")
    _cn(ctx, ww.Name, "MOUNT_PLATE_L")
    # tilt lead exits the servo, runs east past the winch bay, then
    # drops along the same corridor east of the RL hardware
    wt = _wire(doc, ctx, "WIRE_TILT_SV", [
        (-192, 191, 194), (-200, 196, 160), (-200, 192, 110),
        (-190, 184, 80), (-112, 176, 70), (-104, 145, 58),
        (-88, 138, 60), (-86, 86, 48), (-100, 86, 46)], dia="2")
    _em(ctx, wt.Name, "TILT_SERVO")
    _em(ctx, wt.Name, "CRADLE_PIV")
    _em(ctx, wt.Name, "FRAME_RAIL_L")
    _em(ctx, wt.Name, "LIFT_RAIL_R")
    _em(ctx, wt.Name, "MOUNT_PLATE_L")
    wy_ = _wire(doc, ctx, "WIRE_YAW_SV", [
        (-66, -80, 214), (-84, -72, 180), (-112, -62, 150),
        (-132, -60, 100), (-124, -78, 62), (-104, -84, 46),
        (-96, -86, 44)], dia="2")
    _em(ctx, wy_.Name, "YAW_SERVO")
    # lead crosses the RR motor can and the right deck panel edge
    # on its way to the hub bay (master scope)
    _em(ctx, wy_.Name, "MOTOR_RR")
    _em(ctx, wy_.Name, "DECK_R")


def build_lift(doc, ctx):
    """All lift content: mast, stages, winch rig, cradle, chute."""
    _base(doc, ctx)
    _rails(doc, ctx)
    _stage1(doc, ctx)
    _stage2(doc, ctx)
    _cradle(doc, ctx)
    _winch(doc, ctx)
    _chute(doc, ctx)
    _lift_wires(doc, ctx)
    # intended interfaces: chute lip + screws seat into the cup mouth,
    # stage-1 tie contacts the top tie at full extension, rope guide
    # eyelet bonded over the collar/tie bolt heads, collar bolts seat
    # into the S1 tie zone, lift hardware presses the wheel plate
    for a, b in [("CHUTE_LIP_R2", "CRADLE_CUP"),
                 ("SCRW_CHL_3_0", "CRADLE_CUP"),
                 ("SCRW_CHL_3_1", "CRADLE_CUP"),
                 ("SCRW_CHL_3_2", "CRADLE_CUP"),
                 ("WHEEL_PLATE_RL_IN", "CRADLE_CUP"),
                 ("WHEEL_ASSY_RL", "CRADLE_CUP"),
                 ("ROLLER_RL_01_B", "CRADLE_CUP"),
                 ("ROLLER_RL_02_B", "CRADLE_CUP"),
                 ("ROPE_GUIDE", "STOP_COLLAR_R"),
                 ("ROPE_GUIDE", "BOLT_SC_R0"),
                 ("BOLT_LTT_R0", "ROPE_GUIDE"),
                 ("BOLT_LTT_R1", "ROPE_GUIDE"),
                 ("BOLT_SC_R0", "LIFT_S1_TIE"),
                 ("BOLT_SC_R1", "LIFT_S1_TIE"),
                 ("BOLT_SC_R0", "BOLT_S1TIE_2"),
                 ("BOLT_SC_R0", "BOLT_S1TIE_3"),
                 ("BOLT_SC_R1", "BOLT_S1TIE_3"),
                 ("NUT_LRF_R1", "WHEEL_PLATE_RL_IN"),
                 ("NUT_CLMP_RL_0_1", "LIFT_BASE"),
                 ("NUT_CLMP_RL_0_1", "NUT_LB_0"),
                 ("BOLT_CLMP_RL_0_1", "LIFT_BASE"),
                 ("SCRW_S2T_0_0", "LIFT_S1_TRUCK_L0"),
                 ("SCRW_S2T_0_1", "LIFT_S1_TRUCK_R0"),
                 ("SCRW_S2T_1_0", "LIFT_S1_TRUCK_L1"),
                 ("SCRW_S2T_1_1", "LIFT_S1_TRUCK_R1"),
                 ("CRADLE_ARM", "CRADLE_COL_0"),
                 ("LIFT_RAIL_R", "ROPE_GUIDE"),
                 ("BOLT_TIE_L_1", "LIFT_BASE"),
                 ("LIFT_TOP_TIE", "STOP_COLLAR_L"),
                 ("LIFT_TOP_TIE", "STOP_COLLAR_R"),
                 ("LIFT_TOP_TIE", "BOLT_SC_L0"),
                 ("LIFT_TOP_TIE", "BOLT_SC_L1"),
                 ("LIFT_TOP_TIE", "BOLT_SC_R0"),
                 ("LIFT_TOP_TIE", "BOLT_SC_R1"),
                 ("SCRW_CARM_0", "LIFT_S2_BAR"),
                 ("SCRW_CARM_1", "LIFT_S2_BAR"),
                 ("BOLT_S2TIE_1", "ROPE_DYNEEMA")]:
        _em(ctx, a, b)
    _em(ctx, "LIFT_TOP_TIE", "LIFT_S1_TIE")
    _cn(ctx, "NUT_CLMP_RL_1_1", "WIRE_TILT_SV")
    # deployed-pose probes (non-exportable; checked against ENVELOPE)
    _feat(doc, "VOL_S1_DEP", "VOL_S1_DEP_probe_UNVERIFIED",
          "UNVERIFIED - stage-1 deployed tip probe",
          Part.makeBox(14, 18, 8, App.Vector(-191, 153, 501)))
    _feat(doc, "VOL_S2_DEP", "VOL_S2_DEP_probe_UNVERIFIED",
          "UNVERIFIED - stage-2 deployed tip probe",
          Part.makeBox(10, 18, 8, App.Vector(-177, 153, 502)))
    _feat(doc, "VOL_CRADLE_DEP", "VOL_CRADLE_DEP_probe_UNVERIFIED",
          "UNVERIFIED - cradle deployed rim probe",
          Part.makeSphere(46.5, App.Vector(-122, 183, 540)))


def populate_lift(doc, ctx):
    """lift.FCStd = frame context + lift solids."""
    ctx["sheet"] = _sheet(doc)
    build_frame(doc, ctx)
    build_lift(doc, ctx)
    _env(doc, ctx)
