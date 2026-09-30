"""dt_build.py -- shared Sprint-01 overhaul builder.

Produces, from the robot_params vocabulary:
  frame      - inverted-U side rails, rear crossmember, raised crown,
               crown posts, corner gussets, tie plates, end plugs,
               number plates, belly pan + brackets, deck panels/posts
  drivetrain - per corner: mecanum wheel assembly, REX live axle,
               bored flange bearings in both rail walls, gearbox motor,
               mount plate, cavity collar/washer/pinion, outboard
               washer + retaining nut, clamp pair, all fasteners
  pods       - three dead-wheel odometry pods under the belly pan
  elec       - electronics tray + sprint-01 wiring subset

build_drivebase.py / build_electronics.py / build_master_robot.py call
the same populate functions, so subsystem solids are signature-
identical to their master counterparts (DET3). Carriers stay at
identity; expression-bound world coordinates need no re-derivation.

Frame: +X fwd, +Y left, +Z up, Z=0 tile top. The lateral stack derives
from wheel_lat_off (rail_lat = wheel_lat_off - wheel_out_gap) so one
probe translates the whole chain coherently (PAR2-D).

ctx collects the declared mount table while building:
  solids / joints / faces / embeds / journals / contacts / ground / bom
joints entry = {id, members[], bolts[], nuts[], terminal}
"""

import math

import FreeCAD as App

import partkit as pk

# ---- lateral stack expressions (+Y side; mirror with _y()) ---------
RL = "(Parameters.wheel_lat_off - Parameters.wheel_out_gap)"  # 160.02
WII = "(%s - Parameters.rail_size / 2)" % RL     # 136.02 in-wall inner face
CVI = "(%s + Parameters.rail_wall)" % WII      # 138.52 in-wall cavity face
CVO = "(%s + Parameters.rail_size - Parameters.rail_wall)" % WII  # 181.52
WOF = "(%s + Parameters.rail_size)" % WII      # 184.02 out-wall outer face
MPL_I = "(%s - Parameters.mplate_t)" % WII     # 132.97 plate inner face
MPL_O = WII                                    # 136.02 plate outer face
RAIL_Z0 = "(Parameters.rail_elev_z - Parameters.rail_size / 2)"
RAIL_TOP = "(Parameters.rail_elev_z + Parameters.rail_size / 2)"
WEB_I = "(%s - Parameters.rail_wall)" % RAIL_TOP
AXZ = "(Parameters.wheel_dia / 2)"             # 48.0 axle centerline

WXP = "Parameters.wheel_lon_off"               # +127
WXN = "-Parameters.wheel_lon_off"              # -127
WLAT = "Parameters.wheel_lat_off"              # 203.2

CORNERS = (("FL", 1, 1), ("FR", 1, -1), ("RL", -1, 1), ("RR", -1, -1))
SLANT = {"FL": 1, "FR": -1, "RL": -1, "RR": 1}

# mount-plate bolt columns (x) and rows (z) -- clear of the motor face
# discs at +-127 (which span x+-20, z 28..68)
PLATE_BX = ("-90", "-40", "40", "82")
PLATE_BX_HI = ("-60", "-20", "20", "82")
PLATE_BX_MID = ("-72", "-32", "32", "111")
PLATE_BZ = ("28.0", "62.0")
# (x, z) grid actually used by plate bores, wall bores, and bolts
PLATE_HOLES = ([(bx, "28.0") for bx in PLATE_BX] +
               [(bx, "62.0") for bx in PLATE_BX_HI] +
               [(bx, "28.0") for bx in PLATE_BX_MID])


def _s(ctx, o):
    ctx["solids"].append(o.Name)
    return o


def _jm(ctx, jid, members, bolts=(), nuts=(), terminal=None):
    ctx["joints"].append({"id": jid, "members": list(members),
                          "bolts": list(bolts), "nuts": list(nuts),
                          "terminal": terminal})
    term = terminal if terminal is not None else members[-1]
    for bt in bolts:
        _em(ctx, bt, term)
    for i in range(min(len(bolts), len(nuts))):
        _em(ctx, bolts[i], nuts[i])


def _fp(ctx, a, b):
    ctx["faces"].append((a, b))


def _em(ctx, a, b):
    ctx["embeds"].append((a, b))


def _jl(ctx, a, b):
    ctx["journals"].append((a, b))


def _cn(ctx, a, b):
    ctx["contacts"].append((a, b))


def _bom(ctx, subsys, spec, material, dims, status, members):
    ctx["bom"].append({"subsys": subsys, "spec": spec,
                       "material": material, "dims": dims,
                       "status": status, "members": list(members)})


def new_ctx():
    return {"solids": [], "joints": [], "faces": [], "embeds": [],
            "journals": [], "contacts": [], "ground": [], "bom": [],
            "carriers": [], "doc": None}


def _y(expr, sgn):
    """Mirror a +Y expression for the -Y side."""
    return "(%s)" % expr if sgn > 0 else "-(%s)" % expr


def _flathead(doc, name, status, shaft_len, pos, axis):
    """Countersunk flat-head screw pointing +axis: the cone head sinks
    into a countersink cut, wide face flush at `pos` (the member's
    entry face); the shaft runs +axis for shaft_len from the head."""
    comp = {"X": "x", "Y": "y", "Z": "z"}[axis.strip("+-")]
    sgn = -1 if axis.startswith("-") else 1
    hh = "1.8"
    hd = doc.addObject("Part::Cone", pk.TOOL_PREFIX + name + "_HD")
    pk.stamp(hd, name + "_flathead_cone", status)
    pk.bind(hd, {"Radius1": "(Parameters.bolt_head_d) / 2",
                 "Radius2": "(Parameters.bolt_d) / 2",
                 "Height": hh})
    hp = dict(pos)
    if sgn < 0:
        hp["Placement.Base." + comp] = pos["Placement.Base." + comp]
    pk.bind(hd, hp)
    pk._bind_zeros(hd, hp)
    hd.Placement.Rotation = pk.axis_rot(axis)
    sp = dict(pos)
    if sgn > 0:
        sp["Placement.Base." + comp] = "(%s) + %s" % (
            pos["Placement.Base." + comp], hh)
    else:
        sp["Placement.Base." + comp] = "(%s) - %s" % (
            pos["Placement.Base." + comp], hh)
    sh = pk.tool_cyl(doc, name + "_SH",
                     {"Radius": "(Parameters.bolt_d) / 2",
                      "Height": shaft_len}, sp, pk.axis_rot(axis))
    tok = status.split(" ")[0] if status else ""
    return pk.fuse(doc, name,
                   name + "_flathead_M4" + ("_" + tok if tok else ""),
                   status, hd, sh)


def _sink_tool(doc, name, pos, axis):
    """Countersink cone cut tool: opening (wide) at `pos`, narrowing
    +axis -- matches _flathead's head geometry with clearance."""
    comp = {"X": "x", "Y": "y", "Z": "z"}[axis.strip("+-")]
    sgn = -1 if axis.startswith("-") else 1
    cn = doc.addObject("Part::Cone", pk.TOOL_PREFIX + name)
    pk.stamp(cn, name + "_sink", "UNVERIFIED - countersink tool")
    pk.bind(cn, {"Radius1": "(Parameters.bolt_head_d) / 2 + 0.4",
                 "Radius2": "(Parameters.grid_hole_d) / 2",
                 "Height": "2.0"})
    hp = dict(pos)
    if sgn < 0:
        hp["Placement.Base." + comp] = pos["Placement.Base." + comp]
    pk.bind(cn, hp)
    pk._bind_zeros(cn, hp)
    cn.Placement.Rotation = pk.axis_rot(axis)
    return cn


def _nut(doc, name, pos, status="UNVERIFIED - M4 nylock"):
    n = pk.hex_nut(doc, name, name + "_M4_nylock", status,
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore", pos, "Y")
    _s_g = n
    return n


def _rivnut(doc, name, pos):
    """M4 rivet-nut insert seated in a wall bore: OD 6.4, bore O3.6."""
    return pk.bore_cyl(
        doc, name, name + "_rivnut_M4_UNVERIFIED",
        "UNVERIFIED - M4 rivnut insert",
        "(Parameters.rivnut_d - 0.1)", "Parameters.rail_wall",
        "Parameters.nut4_bore", pos, "Y")


# =====================================================================
# FRAME
# =====================================================================
def _rail_bore_specs(sgn):
    """Dedicated wall holes: (dia_expr, x_expr, z_expr, walls) where
    walls is 'in' (inner wall), 'out' (outer wall), or 'both'."""
    holes = []
    for wx in (WXN, WXP):
        # axle clearance O16 through BOTH walls
        holes.append(("Parameters.wall_axle_bore", wx, AXZ, "both"))
        # bearing rivnut seats O6.5, 4 per wall per station
        for su in (-1, 1):
            for sv in (-1, 1):
                bx = "(%s + %d * Parameters.bear_bolt_off)" % (wx, su)
                bz = "(%s + %d * Parameters.bear_bolt_off)" % (AXZ, sv)
                holes.append(("Parameters.rivnut_d", bx, bz, "both"))
        # clamp ear bolts through the inner wall (two z rows)
        for su in (-1, 1):
            for bz in ("(%s - 14)" % AXZ, "(%s + 14)" % AXZ):
                bx = ("(%s + %d * (Parameters.motor_gb_dia / 2 + 0.25 + "
                      "Parameters.clamp_ear / 2))" % (wx, su))
                holes.append(("Parameters.grid_hole_d", bx, bz, "in"))
        # motor face bolts: O8.4 access holes through the inner wall
        # (flat heads sink into the plate's outer-face countersinks;
        # the driver passes through the wall hole)
        for su in (-1, 1):
            for sv in (-1, 1):
                bx = "(%s + %d * Parameters.motor_bolt_off)" % (wx, su)
                bz = "(%s + %d * Parameters.motor_bolt_dz)" % (AXZ, sv)
                holes.append(("8.4", bx, bz, "in"))
    # sprint-02: outboard roller-shaft tip bores through the outer
    # wall on the belt side (pulleys run outside the channel)
    if sgn > 0:
        holes.append(("9", "Parameters.intake_x",
                      "Parameters.roller_low_z", "both"))
        holes.append(("9", "Parameters.roller_top_x",
                      "Parameters.roller_top_z", "out"))
        # idler stub crosses both walls to the belt plane
        holes.append(("10", "170", "106", "in"))
    # pivot pin bore (x170, z30): both walls carry the cheek pivot
    holes.append(("10", "170", "30", "in"))
    if sgn > 0:
        # belt relief: the crossed belt descends across the out-wall's
        # top edge; two tall slots cut the wall's top clear
        for bx in ("172", "186", "200"):
            holes.append(("14", bx, "62", "out"))
    # mount-plate bolts (plate grid -> inner wall)
    for bx, bz in PLATE_HOLES:
        holes.append(("Parameters.grid_hole_d", bx, bz, "in"))
    # pan bracket leg bolts: 2 per bracket at x offsets +-4, single
    # z row at the leg's bolt line
    for bx in ("-70", "-40", "-11"):
        for bxo in ("-4", "4"):
            holes.append(("Parameters.grid_hole_d",
                          "(%s + %s)" % (bx, bxo),
                          "(Parameters.pan_z - 7)", "in"))
    # gusset leg bolts through the inner wall at the rear end
    for gz in ("(Parameters.rail_elev_z - Parameters.rail_size / 2 + 20)",
               "(Parameters.rail_elev_z - Parameters.rail_size / 2 + 42)"):
        for gx in ("(-Parameters.cross_x_off + 14)",
                   "(-Parameters.cross_x_off + 28)"):
            holes.append(("Parameters.grid_hole_d", gx, gz, "in"))
    # under-gusset twin row
    for gz in ("20.0",):
        for gx in ("(-Parameters.cross_x_off + 14)",
                   "(-Parameters.cross_x_off + 28)"):
            holes.append(("Parameters.grid_hole_d", gx, gz, "in"))
    # number-plate screws through the outer wall
    for gz in ("(Parameters.rail_elev_z + 10)",
               "(Parameters.rail_elev_z - 14)"):
        for gx in ("-25", "25"):
            holes.append(("Parameters.grid_hole_d", gx, gz, "out"))
    # web bores (through the top web, Z axis): deck posts + crown post
    # feet + tie plate bolts
    for px in ("-150", "-60", "30", "110"):
        holes.append(("Parameters.grid_hole_d", px,
                      _y(RL, sgn), "web"))
    for py in (("-8", "16") if sgn > 0 else ("8", "-16")):
        for px in ("(Parameters.cross_x_off - 10)",
                   "(Parameters.cross_x_off + 10)"):
            holes.append(("Parameters.grid_hole_d", px,
                          "(%s + %s)" % (_y(RL, sgn), py), "web"))
    for bx in ("(-Parameters.cross_x_off - 5)",
               "(-Parameters.cross_x_off + 14)"):
        holes.append(("Parameters.grid_hole_d", bx,
                      _y("(Parameters.cross_half_len + 16)", sgn), "web"))
    # ---- sprint-02 intake hardware -------------------------------------
    # roller shaft clearance O16 through the inner wall
    holes.append(("Parameters.wall_axle_bore", "Parameters.intake_x",
                  "Parameters.roller_low_z", "in"))
    # cheek pivot pin bore O8.4 through the inner wall
    holes.append(("8.4", "150", "34", "in"))
    # cheek gusset wall bolts at z25
    for gx in ("149", "157"):
        holes.append(("Parameters.grid_hole_d", gx, "25", "in"))
    # cheek face bolts through the inner wall at z19
    for gx in ("118", "136", "154"):
        holes.append(("Parameters.grid_hole_d", gx, "19", "in"))
    # intake bearing rivnut seats O6.5, 4 per side
    for su in (-1, 1):
        for sv in (-1, 1):
            bx = "(Parameters.intake_x + %d * " \
                 "Parameters.bear_bolt_off)" % su
            bz = "(Parameters.roller_low_z + %d * " \
                 "Parameters.bear_bolt_off)" % sv
            holes.append(("Parameters.rivnut_d", bx, bz, "in"))
    if sgn < 0:
        # right side only: jackshaft clearance + motor plate bolts +
        # face-bolt access holes + chain guard screws
        holes.append(("Parameters.wall_axle_bore",
                      "Parameters.int_motor_x", "Parameters.int_motor_z",
                      "in"))
        # intake motor plate wall bolts: 8 explicit stations dodging
        # the gb face circle, the FR clamp ear nut and the pan edge
        for bx, bz in (("-26", "-9"), ("-18", "-9"), ("-36", "-5"),
                       ("-30", "3"), ("-26", "13"), ("-36", "13"),
                       ("-18", "9"), ("-14", "17")):
            holes.append(("Parameters.grid_hole_d",
                          "(Parameters.int_motor_x + %s)" % bx,
                          "(Parameters.int_motor_z + %s)" % bz, "in"))
        # O8.4 access holes: motor face bolts pass through the wall
        for su in (-1, 1):
            for sv in (-1, 1):
                holes.append(("8.4",
                              "(Parameters.int_motor_x + %d * 8)" % su,
                              "(Parameters.int_motor_z + %d * "
                              "Parameters.motor_bolt_dz)" % sv, "in"))
        for gx in ("85", "165"):
            holes.append(("Parameters.grid_hole_d", gx, "18", "in"))
        # chain guard cover screws through the out wall
        for gx in ("75", "205"):
            holes.append(("Parameters.grid_hole_d", gx, "38", "out"))
    if sgn > 0:
        # crossed-belt web slots: the loop's strands ride this channel
        # and skim the top web around x150..210; open O14 slots on the
        # belt plane so the run never grazes the web
        for bx in ("150", "158", "166", "174", "182", "190", "198",
                   "206", "214"):
            holes.append(("14", bx, "Parameters.belt_plane", "web"))
        # sprint-03: lift base + rail-foot + winch bolts through the
        # top web (stations match BOLT_LB_*, BOLT_LRF_*, BOLT_LW_*)
        for bx, by_ in (("-160", "140"), ("-160", "180"),
                        ("-145", "142"), ("-145", "178"),
                        ("-172", "140"), ("-172", "148"),
                        ("-172", "176"), ("-172", "182"),
                        ("-152", "158"), ("-152", "166"),
                        ("-140", "158"), ("-140", "166")):
            holes.append(("Parameters.grid_hole_d", bx, by_, "web"))
    return holes


def _rail(doc, ctx, sgn):
    name = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
    y0 = ("(%s - Parameters.rail_size / 2)" % RL if sgn > 0
          else "(-%s - Parameters.rail_size / 2)" % RL)
    bores = []
    inwall = 0 if sgn > 0 else 1
    for dia, bx, bz, which in _rail_bore_specs(sgn):
        if which == "web":
            # through the top web band (Z axis); bz carries the y expr
            bores.append((dia,
                          {"Placement.Base.x": bx,
                           "Placement.Base.y": bz,
                           "Placement.Base.z":
                           "(%s - 1)" % WEB_I},
                          "Z", "Parameters.rail_wall + 2"))
            continue
        walls = {"in": [inwall], "out": [1 - inwall],
                 "both": [0, 1]}[which]
        for w_i in walls:
            wy = ("(%s) - 1" % y0 if w_i == 0 else
                  "(%s) + Parameters.rail_size - Parameters.rail_wall "
                  "- 1" % y0)
            bores.append((dia,
                          {"Placement.Base.x": bx,
                           "Placement.Base.y": wy,
                           "Placement.Base.z": bz},
                          "Y", "Parameters.rail_wall + 2"))
    r = pk.channel_open(
        doc, name,
        "%s_gobilda1120_invU_444.5_VENDOR-PENDING" % name,
        "VENDOR-PENDING - goBILDA 1120-series ~48mm channel (D12)",
        ("-Parameters.chassis_sq / 2", y0, RAIL_Z0),
        "Parameters.chassis_sq", "Parameters.rail_size",
        "Parameters.rail_wall", axis="X",
        wall_rows=(
            {"count": 9, "dia": "Parameters.grid_hole_d",
             "pitch": "Parameters.grid_pitch", "start": "16",
             "z": "(Parameters.rail_elev_z - Parameters.rail_size / 2 "
                  "+ 12)"},
            {"count": 9, "dia": "Parameters.grid_hole_d",
             "pitch": "Parameters.grid_pitch", "start": "16",
             "z": "(Parameters.rail_elev_z + 4)"}),
        web_rows=(
            {"count": 9, "dia": "Parameters.grid_hole_d",
             "pitch": "Parameters.grid_pitch", "start": "16",
             "line": _y(RL, sgn)},),
        bores=bores)
    _s(ctx, r)
    _bom(ctx, "frame", "1120 U-channel 444.5mm", "aluminum",
         "444.5x48x48", "VENDOR-PENDING", [r.Name])
    return r


def _crossmember(doc, ctx):
    x0 = "(-Parameters.cross_x_off - Parameters.rail_size / 2)"
    bores = []
    # tie-plate bolts down through the top web near each end
    for sgn in (1, -1):
        for tx in ("(-Parameters.cross_x_off - 8)",
                   "(-Parameters.cross_x_off + 6)"):
            bores.append((
                "Parameters.grid_hole_d",
                {"Placement.Base.x": tx,
                 "Placement.Base.y":
                 _y("(Parameters.cross_half_len - 12)", sgn),
                 "Placement.Base.z": WEB_I},
                "Z", "Parameters.rail_wall + 2"))
    # rear number-plate screws through the -X (outer) wall
    for gy in ("-25", "25"):
        for gz in ("(Parameters.rail_elev_z + 10)",
                   "(Parameters.rail_elev_z - 14)"):
            bores.append((
                "Parameters.grid_hole_d",
                {"Placement.Base.x": "(%s - 1)" % x0,
                 "Placement.Base.y": gy,
                 "Placement.Base.z": gz},
                "X", "Parameters.rail_wall + 2"))
    # gusset leg-B bolts through the +X (inner) wall, 2 per end
    for sgn in (1, -1):
        for gy in ("(Parameters.cross_half_len - 14)",
                   "(Parameters.cross_half_len - 30)"):
            for bz_ in ("(Parameters.rail_elev_z - "
                        "Parameters.rail_size / 2 + 17)", "20"):
                bores.append((
                    "Parameters.grid_hole_d",
                    {"Placement.Base.x":
                     "(-Parameters.cross_x_off + Parameters.rail_size / 2"
                     " - Parameters.rail_wall - 1)",
                     "Placement.Base.y": _y(gy, sgn),
                     "Placement.Base.z": bz_},
                    "X", "Parameters.rail_wall + 2"))
    r = pk.channel_open(
        doc, "FRAME_CROSS_B",
        "FRAME_CROSS_B_invU_271.8_VENDOR-PENDING",
        "VENDOR-PENDING - goBILDA 1120 rear crossmember",
        (x0, "(-Parameters.cross_half_len)", RAIL_Z0),
        "2 * Parameters.cross_half_len", "Parameters.rail_size",
        "Parameters.rail_wall", axis="Y",
        bores=bores)
    _s(ctx, r)
    _bom(ctx, "frame", "1120 U-channel crossmember 271.8mm", "aluminum",
         "271.8x48x48", "VENDOR-PENDING", [r.Name])
    _fp(ctx, r.Name, "FRAME_RAIL_L")
    _fp(ctx, r.Name, "FRAME_RAIL_R")
    return r


def _crown(doc, ctx):
    x0 = "(Parameters.cross_x_off - Parameters.rail_size / 2)"
    z0 = "(Parameters.crown_z - Parameters.rail_size / 2)"
    bores = []
    # post-pin bores through BOTH side walls near each end
    for sgn in (1, -1):
        for py in ("(Parameters.cross_half_len - 25)",
                   "(Parameters.cross_half_len - 9)"):
            for pz in ("(Parameters.crown_z - 8)",
                       "(Parameters.crown_z + 12)"):
                for wx2 in ("(Parameters.cross_x_off - "
                            "Parameters.rail_size / 2 - 1)",
                            "(Parameters.cross_x_off + "
                            "Parameters.rail_size / 2 - "
                            "Parameters.rail_wall - 1)"):
                    bores.append((
                        "Parameters.grid_hole_d",
                        {"Placement.Base.x": wx2,
                         "Placement.Base.y": _y(py, sgn),
                         "Placement.Base.z": pz},
                        "X", "Parameters.rail_wall + 2"))
    r = pk.channel_open(
        doc, "FRAME_CROWN_F",
        "FRAME_CROWN_F_invU_271.8_raised_VENDOR-PENDING",
        "VENDOR-PENDING - goBILDA 1120 raised crown crossmember",
        (x0, "(-Parameters.cross_half_len)", z0),
        "2 * Parameters.cross_half_len", "Parameters.rail_size",
        "Parameters.rail_wall", axis="Y",
        bores=bores)
    _s(ctx, r)
    _bom(ctx, "frame", "1120 U-channel crown 271.8mm", "aluminum",
         "271.8x48x48", "VENDOR-PENDING", [r.Name])
    return r


def _crown_post(doc, ctx, sgn):
    """Crown riser: a tongue plate standing on the rail web that enters
    the raised crown's open mouth end; pinned by two through-bolts that
    cross both crown side walls + the tongue. A foot plate spreads the
    load onto the rail web with 4 bolts -> mouth-side nuts."""
    name = "CROWN_POST_L" if sgn > 0 else "CROWN_POST_R"
    rail = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
    lat = _y(RL, sgn)
    bores = []
    for by in ("(Parameters.cross_half_len - 25)",
               "(Parameters.cross_half_len - 9)"):
        for bz in ("(Parameters.crown_z - 8)",
                   "(Parameters.crown_z + 12)"):
            bores.append((
                "Parameters.grid_hole_d",
                {"Placement.Base.x": "(Parameters.cross_x_off - 5)",
                 "Placement.Base.y": _y(by, sgn),
                 "Placement.Base.z": bz}, "X", "10"))
    stem = pk.bored_plate(
        doc, "TOOL_" + name + "_STEM", name + "_tonguepost_UNVERIFIED",
        "UNVERIFIED - crown riser tongue",
        {"Length": "8", "Width": "Parameters.post_span",
         "Height": "(Parameters.post_top_z - %s)" % RAIL_TOP},
        {"Placement.Base.x": "(Parameters.cross_x_off - 4)",
         "Placement.Base.y":
         (_y("(Parameters.cross_half_len - 40)", sgn) if sgn > 0 else
          "(-(Parameters.cross_half_len - 40) - Parameters.post_span)"),
         "Placement.Base.z": RAIL_TOP},
        bores=bores)
    foot = pk.tool_box(
        doc, name + "_FOOT",
        {"Length": "40", "Width": "40", "Height": "5"},
        {"Placement.Base.x": "(Parameters.cross_x_off - 20)",
         "Placement.Base.y":
         ("(%s - 40)" % WOF if sgn > 0 else "(-%s)" % WOF),
         "Placement.Base.z": RAIL_TOP})
    _raw = pk.fuse(doc, "TOOL_" + name + "_RAW",
                   name + "_raw", "", stem, foot)
    # belt relief: the intake belt's descent grazes the foot's front
    # outboard corner -> clearance notch
    notch = pk.tool_box(
        doc, "TOOL_" + name + "_NCH",
        {"Length": "36", "Width": "34", "Height": "18"},
        {"Placement.Base.x": "(Parameters.cross_x_off - 32)",
         "Placement.Base.y":
         ("(%s - 34)" % WOF if sgn > 0 else "(-%s)" % WOF),
         "Placement.Base.z": "(%s - 4)" % RAIL_TOP})
    post = pk.cut(doc, name, name + "_post_UNVERIFIED",
                  "UNVERIFIED - riser tongue + foot fuse (belt relief)",
                  _raw, [notch])
    _s(ctx, post)
    _fp(ctx, post.Name, rail)
    _fp(ctx, post.Name, "FRAME_CROWN_F")
    _em(ctx, post.Name, "FRAME_CROWN_F")   # tongue nests in the mouth
    _bom(ctx, "frame", "crown riser tongue + foot", "aluminum",
         "8x44x115 + 40x40x5", "UNVERIFIED", [post.Name])
    # crown pin bolts: +X through -X wall + tongue + +X wall -> nut
    bolts, nuts = [], []
    for i, (by, bz) in enumerate(
            (("(Parameters.cross_half_len - 25)",
              "(Parameters.crown_z - 8)"),
             ("(Parameters.cross_half_len - 9)",
              "(Parameters.crown_z + 12)"))):
        bn = "BOLT_CROWN_%s_%d" % (name[-1], i)
        nn = "NUT_CROWN_%s_%d" % (name[-1], i)
        yb = _y(by, sgn)
        pk.bolt(doc, bn, bn + "_M4x56_UNVERIFIED",
                "UNVERIFIED - M4x52 crown pin bolt",
                "Parameters.bolt_d", "52",
                "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                {"Placement.Base.x":
                 "(Parameters.cross_x_off - Parameters.rail_size / 2 "
                 "- Parameters.bolt_head_h)",
                 "Placement.Base.y": yb,
                 "Placement.Base.z": bz},
                "X")
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore",
                   {"Placement.Base.x":
                    "(Parameters.cross_x_off + Parameters.rail_size / 2 "
                    "- Parameters.nut4_h - 1.2)",
                    "Placement.Base.y": yb,
                    "Placement.Base.z": bz}, "X")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "crown_pin", [post.Name, "FRAME_CROWN_F"], bolts, nuts)
    # foot bolts down through the foot plate + rail web -> mouth nuts
    bolts2, nuts2 = [], []
    for i, (px, py) in enumerate((("-10", "2"), ("-10", "12"),
                                  ("10", "2"), ("10", "12"))):
        bn = "BOLT_CPOSTF_%s_%d" % (name[-1], i)
        nn = "NUT_CPOSTF_%s_%d" % (name[-1], i)
        yf = ("(%s - 20 %+d)" % (WOF, int(py)) if sgn > 0 else
              "(-%s %+d)" % (WOF, 20 - int(py)))
        pk.bolt(doc, bn, bn + "_M4x14_UNVERIFIED",
                "UNVERIFIED - M4 bolt", "Parameters.bolt_d", "12",
                "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                {"Placement.Base.x": "(Parameters.cross_x_off + %s)" % px,
                 "Placement.Base.y": yf,
                 "Placement.Base.z":
                 "(%s + 5 + Parameters.bolt_head_h)" % RAIL_TOP}, "-Z")
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore",
                   {"Placement.Base.x":
                    "(Parameters.cross_x_off + %s)" % px,
                    "Placement.Base.y": yf,
                    "Placement.Base.z":
                    "(%s - Parameters.nut4_h)"
                    % WEB_I}, "Z")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        bolts2.append(bn)
        nuts2.append(nn)
    _jm(ctx, "post_foot", [post.Name, rail], bolts2, nuts2)


def _gusset(doc, ctx, sgn):
    """Rear inside-corner gusset at the rail/crossmember joint."""
    name = "GUSSET_B%s" % ("L" if sgn > 0 else "R")
    rail = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
    wy = WII if sgn > 0 else "-(%s)" % WII
    legA_y = ("(%s - Parameters.gusset_t)" % wy if sgn > 0 else wy)
    legA = pk.tool_box(
        doc, name + "_A",
        {"Length": "Parameters.gusset_leg", "Width": "Parameters.gusset_t",
         "Height": "Parameters.gusset_leg"},
        {"Placement.Base.x":
         "(-Parameters.cross_x_off - Parameters.gusset_leg + 30)",
         "Placement.Base.y": legA_y,
         "Placement.Base.z":
         "(Parameters.pan_z + Parameters.pan_thk / 2 + 0.2)"})
    legB = pk.tool_box(
        doc, name + "_B",
        {"Length": "Parameters.gusset_t", "Width": "Parameters.gusset_leg",
         "Height": "Parameters.gusset_leg"},
        {"Placement.Base.x":
         "(-Parameters.cross_x_off + Parameters.rail_size / 2)",
         "Placement.Base.y":
         ("(Parameters.cross_half_len - Parameters.gusset_leg - 4)"
          if sgn > 0 else "(-Parameters.cross_half_len + 4)"),
         "Placement.Base.z":
         "(Parameters.pan_z + Parameters.pan_thk / 2 + 0.2)"})
    gus = pk.fuse(doc, name, name + "_Lgusset_40x40_UNVERIFIED",
                  "UNVERIFIED - corner gusset", legA, legB)
    _s(ctx, gus)
    _fp(ctx, gus.Name, rail)
    _fp(ctx, gus.Name, "FRAME_CROSS_B")
    _bom(ctx, "frame", "inside-corner gusset", "aluminum", "40x40x6",
         "UNVERIFIED", [gus.Name])
    # 2 bolts: head on legA face -> through leg + rail wall -> nut in
    # rail cavity
    bolts, nuts = [], []
    for i, gx in enumerate(("(-Parameters.cross_x_off + 14)",
                            "(-Parameters.cross_x_off + 28)")):
        for k, zoff in enumerate(("20", "42")):
            bn = "BOLT_GUS_%s_%d_%d" % (name[-1], i, k)
            nn = "NUT_GUS_%s_%d_%d" % (name[-1], i, k)
            if sgn > 0:
                hp = {"Placement.Base.x": gx,
                      "Placement.Base.y":
                      "(%s - Parameters.gusset_t - Parameters.bolt_head_h)"
                      % WII,
                      "Placement.Base.z":
                      "(Parameters.rail_elev_z - Parameters.rail_size / 2 "
                      "+ %s)" % zoff}
                np_ = {"Placement.Base.x": gx,
                       "Placement.Base.y": CVI,
                       "Placement.Base.z":
                       "(Parameters.rail_elev_z - Parameters.rail_size / 2 "
                       "+ %s)" % zoff}
                ax = "Y"
            else:
                hp = {"Placement.Base.x": gx,
                      "Placement.Base.y":
                      "(-(%s) + Parameters.gusset_t + "
                      "Parameters.bolt_head_h)" % WII,
                      "Placement.Base.z":
                      "(Parameters.rail_elev_z - Parameters.rail_size / 2 "
                      "+ %s)" % zoff}
                np_ = {"Placement.Base.x": gx,
                       "Placement.Base.y": "-(%s) - Parameters.nut4_h"
                                           % CVI,
                       "Placement.Base.z":
                       "(Parameters.rail_elev_z - Parameters.rail_size / 2 "
                       "+ %s)" % zoff}
                ax = "-Y"
            pk.bolt(doc, bn, bn + "_M4_UNVERIFIED",
                    "UNVERIFIED - M4 bolt", "Parameters.bolt_d",
                    "(Parameters.gusset_t + Parameters.rail_wall + 6)",
                    "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                    hp, ax)
            pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED",
                       "UNVERIFIED - M4 nut", "Parameters.nut4_wrench",
                       "Parameters.nut4_h", "Parameters.nut4_bore",
                       np_, "Y")
            _s(ctx, doc.getObject(bn))
            _s(ctx, doc.getObject(nn))
            bolts.append(bn)
            nuts.append(nn)
    _jm(ctx, "gusset_rail", [gus.Name, rail], bolts, nuts)
    # legB bolts through the crossmember inner wall -> nuts in cavity
    bolts2, nuts2 = [], []
    for i, gy in enumerate(("(Parameters.cross_half_len - 14)",
                            "(Parameters.cross_half_len - 30)")):
        bn = "BOLT_GUSX_%s_%d" % (name[-1], i)
        nn = "NUT_GUSX_%s_%d" % (name[-1], i)
        gy_s = _y(gy, sgn)
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d",
                "(Parameters.gusset_t + Parameters.rail_wall + "
                "Parameters.nut4_h - 1)",
                "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                {"Placement.Base.x":
                 "(-Parameters.cross_x_off + Parameters.rail_size / 2 "
                 "+ Parameters.gusset_t + Parameters.bolt_head_h)",
                 "Placement.Base.y": gy_s,
                 "Placement.Base.z":
                 "(Parameters.rail_elev_z - Parameters.rail_size / 2 "
                 "+ 17)"},
                "-X")
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore",
                   {"Placement.Base.x":
                    "(-Parameters.cross_x_off + Parameters.rail_size / 2 "
                    "- Parameters.rail_wall - Parameters.nut4_h)",
                    "Placement.Base.y": gy_s,
                    "Placement.Base.z":
                    "(Parameters.rail_elev_z - Parameters.rail_size / 2 "
                    "+ 17)"}, "X")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        bolts2.append(bn)
        nuts2.append(nn)
    _jm(ctx, "gusset_cross", [gus.Name, "FRAME_CROSS_B"], bolts2, nuts2)

    # ---- under-gusset twin: second L-bracket below the pan band ------
    uname = "GUSSET_U%s" % ("L" if sgn > 0 else "R")
    ulegA = pk.tool_box(
        doc, uname + "_A",
        {"Length": "Parameters.gusset_leg", "Width": "Parameters.gusset_t",
         "Height": "8"},
        {"Placement.Base.x":
         "(-Parameters.cross_x_off - Parameters.gusset_leg + 30)",
         "Placement.Base.y": legA_y,
         "Placement.Base.z": "16"})
    ulegB = pk.tool_box(
        doc, uname + "_B",
        {"Length": "Parameters.gusset_t", "Width": "Parameters.gusset_leg",
         "Height": "8"},
        {"Placement.Base.x":
         "(-Parameters.cross_x_off + Parameters.rail_size / 2)",
         "Placement.Base.y":
         ("(Parameters.cross_half_len - Parameters.gusset_leg - 4)"
          if sgn > 0 else "(-Parameters.cross_half_len + 4)"),
         "Placement.Base.z": "16"})
    ugus = pk.fuse(doc, uname, uname + "_Lgusset_low_UNVERIFIED",
                   "UNVERIFIED - low corner gusset", ulegA, ulegB)
    _s(ctx, ugus)
    _fp(ctx, ugus.Name, rail)
    _fp(ctx, ugus.Name, "FRAME_CROSS_B")
    _bom(ctx, "frame", "low corner gusset", "aluminum", "35x35x6",
         "UNVERIFIED", [ugus.Name])
    ubolts, unuts = [], []
    for i, gx in enumerate(("(-Parameters.cross_x_off + 14)",
                            "(-Parameters.cross_x_off + 28)")):
        for k, bz in enumerate(("20.0",)):
            bn = "BOLT_GUSU_%s_%d_%d" % (uname[-1], i, k)
            nn = "NUT_GUSU_%s_%d_%d" % (uname[-1], i, k)
            if sgn > 0:
                hp = {"Placement.Base.x": gx,
                      "Placement.Base.y":
                      "(%s - Parameters.gusset_t - Parameters.bolt_head_h)"
                      % WII,
                      "Placement.Base.z": bz}
                np_ = {"Placement.Base.x": gx,
                       "Placement.Base.y": CVI,
                       "Placement.Base.z": bz}
                ax = "Y"
            else:
                hp = {"Placement.Base.x": gx,
                      "Placement.Base.y":
                      "(-(%s) + Parameters.gusset_t + "
                      "Parameters.bolt_head_h)" % WII,
                      "Placement.Base.z": bz}
                np_ = {"Placement.Base.x": gx,
                       "Placement.Base.y": "-(%s) - Parameters.nut4_h"
                                           % CVI,
                       "Placement.Base.z": bz}
                ax = "-Y"
            pk.bolt(doc, bn, bn + "_M4_UNVERIFIED",
                    "UNVERIFIED - M4 bolt", "Parameters.bolt_d",
                    "(Parameters.gusset_t + Parameters.rail_wall + 6)",
                    "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                    hp, ax)
            pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED",
                       "UNVERIFIED - M4 nut", "Parameters.nut4_wrench",
                       "Parameters.nut4_h", "Parameters.nut4_bore",
                       np_, "Y")
            _s(ctx, doc.getObject(bn))
            _s(ctx, doc.getObject(nn))
            ubolts.append(bn)
            unuts.append(nn)
    for i, gy in enumerate(("(Parameters.cross_half_len - 14)",
                            "(Parameters.cross_half_len - 30)")):
        bn = "BOLT_GUSU_X%s_%d" % (uname[-1], i)
        nn = "NUT_GUSU_X%s_%d" % (uname[-1], i)
        gy_s = _y(gy, sgn)
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d",
                "(Parameters.gusset_t + Parameters.rail_wall + "
                "Parameters.nut4_h - 1)",
                "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                {"Placement.Base.x":
                 "(-Parameters.cross_x_off + Parameters.rail_size / 2 "
                 "+ Parameters.gusset_t + Parameters.bolt_head_h)",
                 "Placement.Base.y": gy_s,
                 "Placement.Base.z": "20"},
                "-X")
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore",
                   {"Placement.Base.x":
                    "(-Parameters.cross_x_off + Parameters.rail_size / 2 "
                    "- Parameters.rail_wall - Parameters.nut4_h)",
                    "Placement.Base.y": gy_s,
                    "Placement.Base.z": "20"}, "X")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        ubolts.append(bn)
        unuts.append(nn)
    _jm(ctx, "gusset_low", [ugus.Name, rail, "FRAME_CROSS_B"],
        ubolts, unuts)


def _tie_plate(doc, ctx, sgn):
    """Top-web splice plate bridging rail web + crossmember web at the
    rear corner. 2 bolts land in the rail web, 2 in the crossmember
    web; the plate itself is bored at the same stations."""
    name = "TIE_RB_%s" % ("L" if sgn > 0 else "R")
    rail = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
    # 4 bolt stations: two land in the rail web (y=CHL+16), two in the
    # crossmember web (y=CHL-12); x columns -cross_x_off-5 and +8
    spots = (("(-Parameters.cross_x_off - 5)",
              "(Parameters.cross_half_len + 16)"),
             ("(-Parameters.cross_x_off + 14)",
              "(Parameters.cross_half_len + 16)"),
             ("(-Parameters.cross_x_off - 8)",
              "(Parameters.cross_half_len - 12)"),
             ("(-Parameters.cross_x_off + 6)",
              "(Parameters.cross_half_len - 12)"))
    bores = []
    for bx, byu in spots:
        by = _y(byu, sgn)
        bores.append(("Parameters.grid_hole_d",
                      {"Placement.Base.x": bx, "Placement.Base.y": by,
                       "Placement.Base.z": "(%s - 1)" % RAIL_TOP},
                      "Z", "6"))
    plate = pk.bored_plate(
        doc, name, name + "_splice_30x72x3_UNVERIFIED",
        "UNVERIFIED - top-web splice plate",
        {"Length": "30", "Width": "72", "Height": "3"},
        {"Placement.Base.x": "(-Parameters.cross_x_off - 15)",
         "Placement.Base.y":
         "(Parameters.cross_half_len - 24)" if sgn > 0
         else "(-Parameters.cross_half_len - 48)",
         "Placement.Base.z": RAIL_TOP},
        bores=bores)
    _s(ctx, plate)
    _fp(ctx, plate.Name, rail)
    _fp(ctx, plate.Name, "FRAME_CROSS_B")
    _bom(ctx, "frame", "corner splice plate", "aluminum", "30x72x3",
         "UNVERIFIED", [plate.Name])
    bolts, nuts = [], []
    for i, (bx, byu) in enumerate(spots):
        bn = "BOLT_TIE_%s_%d" % (name[-1], i)
        nn = "NUT_TIE_%s_%d" % (name[-1], i)
        by = _y(byu, sgn)
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "10", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h",
                {"Placement.Base.x": bx, "Placement.Base.y": by,
                 "Placement.Base.z": "(%s + 3 + Parameters.bolt_head_h)"
                 % RAIL_TOP}, "-Z")
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore",
                   {"Placement.Base.x": bx, "Placement.Base.y": by,
                    "Placement.Base.z":
                    "(%s - Parameters.nut4_h)"
                    % WEB_I}, "Z")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "tie_web", [plate.Name, rail, "FRAME_CROSS_B"], bolts, nuts)


def _endcap(doc, ctx, name, pos, axis, member, short=False):
    """Recessed end plug nested inside a channel mouth."""
    S, W = "Parameters.rail_size", "Parameters.rail_wall"
    # press-fit plug: sized 0.1mm oversize per side -> declared embed
    if axis == "X":
        dims = {"Length": "Parameters.endcap_t",
                "Width": "(%s - 2 * %s + 0.2)" % (S, W),
                "Height": "(%s - %s + 0.7)" % (S, W)}
        ppos = {"Placement.Base.x": pos["Placement.Base.x"],
                "Placement.Base.y": "(%s + %s - 0.1)" % (
                    pos["Placement.Base.y"], W),
                "Placement.Base.z": "(%s - 0.1)" % pos["Placement.Base.z"]}
    else:
        dims = {"Length": ("16" if short else
                           "(%s - 2 * %s + 0.2)" % (S, W)),
                "Width": "Parameters.endcap_t",
                "Height": "(%s - %s + 0.7)" % (S, W)}
        ppos = {"Placement.Base.x": "(%s + %s - 0.1)" % (
                    pos["Placement.Base.x"], W),
                "Placement.Base.y": pos["Placement.Base.y"],
                "Placement.Base.z": "(%s - 0.1)" % pos["Placement.Base.z"]}
    cap = pk.plate(doc, name, name + "_endplug_UNVERIFIED",
                   "UNVERIFIED - recessed channel end plug", dims, ppos)
    _s(ctx, cap)
    _em(ctx, cap.Name, member)
    _fp(ctx, cap.Name, member)
    _bom(ctx, "frame", "channel end plug", "nylon", "45x42x3",
         "UNVERIFIED", [cap.Name])


def _number_plate(doc, ctx, name, member, face_pos, axis):
    """Alliance plate bored at its 4 screw stations; M4 bolts through
    plate + member wall to cavity nuts."""
    zs = ("(Parameters.rail_elev_z + 10)",
          "(Parameters.rail_elev_z - 14)")
    bores = []
    if axis == "Y":
        for gx in ("-25", "25"):
            for gz in zs:
                bores.append(("Parameters.grid_hole_d",
                              {"Placement.Base.x": gx,
                               "Placement.Base.y":
                               "(%s - 1)" % face_pos["Placement.Base.y"],
                               "Placement.Base.z": gz},
                              "Y", "Parameters.plate_num_t + 2"))
    else:
        for gy in ("-25", "25"):
            for gz in zs:
                bores.append(("Parameters.grid_hole_d",
                              {"Placement.Base.x":
                               face_pos["Placement.Base.x"],
                               "Placement.Base.y": gy,
                               "Placement.Base.z": gz},
                              "X", "Parameters.plate_num_t + 2"))
    plate = pk.bored_plate(
        doc, name, name + "_alliance_plate_UNVERIFIED",
        "UNVERIFIED - alliance number plate",
        {"Length": "Parameters.plate_num_w" if axis == "Y"
         else "Parameters.plate_num_t",
         "Width": "Parameters.plate_num_t" if axis == "Y"
         else "Parameters.plate_num_w",
         "Height": "Parameters.plate_num_h"},
        face_pos, bores=bores)
    _s(ctx, plate)
    _fp(ctx, plate.Name, member)
    _bom(ctx, "frame", "alliance number plate", "polycarb", "91x61x2",
         "UNVERIFIED", [plate.Name])
    bolts, nuts = [], []
    for i in range(4):
        g, gz = (("-25", "25")[i % 2], zs[i // 2])
        bn = "BOLT_NUM_%s_%d" % (name[-1], i)
        nn = "NUT_NUM_%s_%d" % (name[-1], i)
        if axis == "Y":   # head on plate outer (+Y) face, shaft -Y
            hp = {"Placement.Base.x": g,
                  "Placement.Base.y":
                  "(%s + Parameters.plate_num_t + Parameters.bolt_head_h)"
                  % WOF,
                  "Placement.Base.z": gz}
            npos = {"Placement.Base.x": g,
                    "Placement.Base.y": "(%s - Parameters.nut4_h)" % CVO,
                    "Placement.Base.z": gz}
            pax = "-Y"
        else:             # head inside the channel cavity, shaft
            # +X through wall + plate -> nut on the plate outer face
            hp = {"Placement.Base.x":
                  "(-Parameters.cross_x_off - Parameters.rail_size / 2 "
                  "+ Parameters.rail_wall + Parameters.bolt_head_h)",
                  "Placement.Base.y": g,
                  "Placement.Base.z": gz}
            npos = {"Placement.Base.x":
                    "(-Parameters.cross_x_off - Parameters.rail_size / 2 "
                    "- Parameters.plate_num_t - Parameters.nut4_h)",
                    "Placement.Base.y": g,
                    "Placement.Base.z": gz}
            pax = "-X"
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "8", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h", hp, pax)
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore", npos, pax.replace("-", ""))
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        _em(ctx, bn, nn)       # thread embed into the terminal nut
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "numplate", [plate.Name, member], bolts, nuts)


def _pan_bracket(doc, ctx, sgn, idx):
    """L-bracket: leg flush on the rail inner wall face BELOW the mount
    plate's bottom edge + foot flush under the pan. 2 leg bolts ->
    cavity nuts; 1 foot bolt up through foot+pan -> pan-top nut."""
    name = "PAN_BRKT_%s%d" % ("L" if sgn > 0 else "R", idx)
    rail = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
    bx = ("-70", "-40", "-11")[idx]
    # leg z-band [16.5, 23.3] clears the mount plate's bottom edge 23.51
    LZ0 = "(Parameters.pan_z - Parameters.pan_thk / 2 - 9.17)"
    if sgn > 0:
        leg_y = "(%s - 4)" % WII            # band [132.02, 136.02]
        foot_y = "(%s - 43.5)" % WII        # band [92.52, 132.52]
        hole_y = "(%s - 5)" % WII
        fy = "(%s - 18)" % WII              # 118.02 on the pan
        nut_face = CVI
    else:
        leg_y = "(-%s)" % WII               # band [-136.02, -132.02]
        foot_y = "(-(%s) + 3.5)" % WII      # band [-132.52, -92.52]
        hole_y = "(-(%s) - 5)" % WII
        fy = "(-(%s) + 18)" % WII
        nut_face = "-(%s)" % CVI
    leg = pk.tool_box(
        doc, name + "_LEG",
        {"Length": "28", "Width": "4", "Height": "6.8"},
        {"Placement.Base.x": "(%s - 14)" % bx,
         "Placement.Base.y": leg_y,
         "Placement.Base.z": LZ0})
    foot = pk.tool_box(
        doc, name + "_FOOT",
        {"Length": "28", "Width": "40", "Height": "4"},
        {"Placement.Base.x": "(%s - 14)" % bx,
         "Placement.Base.y": foot_y,
         "Placement.Base.z":
         "(Parameters.pan_z - Parameters.pan_thk / 2 - 4)"})
    tools = []
    for j, xoff in enumerate(("-4", "4")):
        tools.append(pk.tool_cyl(
            doc, "%s_LB%d" % (name, j),
            {"Radius": "Parameters.grid_hole_d / 2", "Height": "10"},
            {"Placement.Base.x": "(%s + %s)" % (bx, xoff),
             "Placement.Base.y": hole_y,
             "Placement.Base.z": "(%s + 3.5)" % LZ0},
            pk.axis_rot("Y")))
    tools.append(pk.tool_cyl(
        doc, name + "_FB",
        {"Radius": "Parameters.grid_hole_d / 2", "Height": "10"},
        {"Placement.Base.x": bx,
         "Placement.Base.y": fy,
         "Placement.Base.z":
         "(Parameters.pan_z - Parameters.pan_thk / 2 - 6)"}))
    brkt = pk.cut(doc, name, name + "_Lbracket_UNVERIFIED",
                  "UNVERIFIED - pan mount L-bracket",
                  pk.fuse(doc, pk.TOOL_PREFIX + name + "_FU", name + "_fu",
                          "UNVERIFIED - bracket fuse", leg, foot), tools)
    _s(ctx, brkt)
    _fp(ctx, brkt.Name, rail)
    _fp(ctx, brkt.Name, "BELLY_PAN")
    _bom(ctx, "frame", "pan mount L-bracket", "aluminum", "30x40x4",
         "UNVERIFIED", [brkt.Name])
    # leg bolts x2: head on leg inner face -> leg + wall -> cavity nut
    bolts, nuts = [], []
    for j, xoff in enumerate(("-4", "4")):
        bnz = "(%s + 3.5)" % LZ0
        bxj = "(%s + %s)" % (bx, xoff)
        bn = "BOLT_PANB_%s%d_%d" % ("L" if sgn > 0 else "R", idx, j)
        nn = "NUT_PANB_%s%d_%d" % ("L" if sgn > 0 else "R", idx, j)
        if sgn > 0:
            hp = {"Placement.Base.x": bxj, "Placement.Base.y":
                  "(%s - 4 - Parameters.bolt_head_h)" % WII,
                  "Placement.Base.z": bnz}
            npos = {"Placement.Base.x": bxj, "Placement.Base.y": CVI,
                    "Placement.Base.z": bnz}
            ax = "Y"
        else:
            hp = {"Placement.Base.x": bxj,
                  "Placement.Base.y":
                  "(-(%s) + 4 + Parameters.bolt_head_h)" % WII,
                  "Placement.Base.z": bnz}
            npos = {"Placement.Base.x": bxj,
                    "Placement.Base.y": "-(%s) - Parameters.nut4_h" % CVI,
                    "Placement.Base.z": bnz}
            ax = "-Y"
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "12", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h", hp, ax)
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore", npos, "Y")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "panbrkt_wall", [brkt.Name, rail], bolts, nuts)
    # foot bolt: head under the foot tab -> foot + pan -> nut on top
    bn2 = "BOLT_PANF_%s%d" % ("L" if sgn > 0 else "R", idx)
    nn2 = "NUT_PANF_%s%d" % ("L" if sgn > 0 else "R", idx)
    pk.bolt(doc, bn2, bn2 + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
            "Parameters.bolt_d", "11", "Parameters.bolt_head_d",
            "Parameters.bolt_head_h",
            {"Placement.Base.x": bx, "Placement.Base.y": fy,
             "Placement.Base.z":
             "(Parameters.pan_z - Parameters.pan_thk / 2 - 4 - "
             "Parameters.bolt_head_h)"}, "Z")
    pk.hex_nut(doc, nn2, nn2 + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
               "Parameters.nut4_wrench", "Parameters.nut4_h",
               "Parameters.nut4_bore",
               {"Placement.Base.x": bx, "Placement.Base.y": fy,
                "Placement.Base.z":
                "(Parameters.pan_z + Parameters.pan_thk / 2)"}, "Z")
    _s(ctx, doc.getObject(bn2))
    _s(ctx, doc.getObject(nn2))
    _jm(ctx, "panbrkt_pan", [brkt.Name, "BELLY_PAN"], [bn2], [nn2])


def _pan_holes():
    """All through-holes in the belly pan, (x_expr, y_expr, dia_expr).

    Order matches the fasteners that ride them: bracket feet, strap
    feet, hub feet, switch bracket, pod mount blocks, shelf standoffs,
    wire clips.
    """
    holes = []
    # pan bracket foot bolts (3 stations x 2 sides)
    for bx in ("-70", "-40", "-11"):
        holes.append((bx, "(%s - 18)" % WII, "Parameters.grid_hole_d"))
        holes.append((bx, "(-(%s) + 18)" % WII, "Parameters.grid_hole_d"))
    # battery strap foot bolts (2 straps x 2 feet)
    for sx in ("(Parameters.batt_x - Parameters.batt_l / 2 + 10 + "
               "Parameters.strap_w / 2)",
               "(Parameters.batt_x + Parameters.batt_l / 2 - 10 - "
               "Parameters.strap_w / 2)"):
        for fy2 in ("(Parameters.batt_y - Parameters.batt_w / 2 "
                    "- Parameters.strap_t - Parameters.strap_foot / 2)",
                    "(Parameters.batt_y + Parameters.batt_w / 2 "
                    "+ Parameters.strap_t + Parameters.strap_foot / 2)"):
            holes.append((sx, fy2, "Parameters.grid_hole_d"))
    # ctrl-hub foot bolts (4; the exp hub mounts on the shelf)
    for hx in ("(Parameters.ctrl_x - 40)", "(Parameters.ctrl_x + 40)"):
        for hs in ("(Parameters.ehub_w / 2 + 7.5)",
                   "(-Parameters.ehub_w / 2 - 7.5)"):
            holes.append((hx, "(Parameters.ctrl_y + %s)" % hs,
                          "Parameters.grid_hole_d"))
    # switch bracket foot bolts
    for sx in ("(Parameters.sw_x - 10)", "(Parameters.sw_x + 10)"):
        holes.append((sx, "(Parameters.sw_y - 5)",
                      "Parameters.grid_hole_d"))
    # pod mount block bolts (2 per pod)
    for px, py, dpy in (
            ("Parameters.odo_pod_x", "Parameters.odo_pod_lat", "-21"),
            ("Parameters.odo_pod_x", "(-Parameters.odo_pod_lat)", "+21")):
        for dx in ("-22", "-14"):
            holes.append(("(%s + %s)" % (px, dx), "(%s %s)" % (py, dpy),
                          "Parameters.grid_hole_d"))
    for dy in ("-26", "-10"):
        holes.append(("(Parameters.odo_pod_lon_x + 21)", dy,
                      "Parameters.grid_hole_d"))
    # shelf standoff bolts
    for sx in ("(Parameters.shelf_x_lo + 15)", "-30"):
        for sy in ("-35", "35"):
            holes.append((sx, sy, "Parameters.grid_hole_d"))
    # wire clip screws
    for cx, cy in (("150", "0"), ("-60", "-95"), ("-160", "-40"),
                   ("40", "-100")):
        holes.append((cx, cy, "3.5"))
    return holes


def _belly_pan(doc, ctx):
    tools = []
    # pod wheel slots so the O48 dead wheels clear the pan
    # pod slots cover wheel + arm bands and the wheel-pin nut zone
    for i, (posx, posy, sx_, sy_) in enumerate((
            ("(Parameters.odo_pod_x - 28)",
             "(Parameters.odo_pod_lat - 16)", "56", "30"),
            ("(Parameters.odo_pod_x - 28)",
             "(-Parameters.odo_pod_lat - 14)", "56", "30"),
            ("(Parameters.odo_pod_lon_x - 16)", "-28", "32", "56"))):
        tools.append(pk.tool_box(
            doc, "PAN_SLOT%d" % i,
            {"Length": sx_, "Width": sy_, "Height":
             "(Parameters.pan_thk + 2)"},
            {"Placement.Base.x": posx,
             "Placement.Base.y": posy,
             "Placement.Base.z":
             "(Parameters.pan_z - Parameters.pan_thk / 2 - 1)"}))
    # clearance windows under the motor clamps (clamp bottoms sit
    # below the pan top plane)
    for i, wx_ in enumerate((WXP, WXN)):
        for sgn_ in (1, -1):
            tools.append(pk.tool_box(
                doc, "PAN_CLAMP%d_%s" % (i, "L" if sgn_ > 0 else "R"),
                {"Length": "76", "Width": "33", "Height":
                 "(Parameters.pan_thk + 2)"},
                {"Placement.Base.x": "(%s - 38)" % wx_,
                 "Placement.Base.y":
                 ("102" if sgn_ > 0 else "-135"),
                 "Placement.Base.z":
                 "(Parameters.pan_z - Parameters.pan_thk / 2 - 1)"}))
    for i, (hx, hy, hd) in enumerate(_pan_holes()):
        tools.append(pk.tool_cyl(
            doc, "PAN_HOLE%02d" % i,
            {"Radius": "(%s) / 2" % hd, "Height": "8"},
            {"Placement.Base.x": hx,
             "Placement.Base.y": hy,
             "Placement.Base.z":
             "(Parameters.pan_z - Parameters.pan_thk / 2 - 1)"}))
    blk = pk.tool_box(
        doc, "BELLY_PAN_BLK",
        {"Length": "Parameters.pan_len", "Width": "Parameters.pan_w",
         "Height": "Parameters.pan_thk"},
        {"Placement.Base.x":
         "(Parameters.pan_x_c - Parameters.pan_len / 2)",
         "Placement.Base.y": "(-Parameters.pan_w / 2)",
         "Placement.Base.z":
         "(Parameters.pan_z - Parameters.pan_thk / 2)"})
    pan = pk.cut(doc, "BELLY_PAN", "BELLY_PAN_sheet_UNVERIFIED",
                 "UNVERIFIED - belly pan with pod slots + bolt holes",
                 blk, tools)
    _s(ctx, pan)
    _bom(ctx, "frame", "belly pan sheet", "polycarb", "350x269x2",
         "UNVERIFIED", [pan.Name])
    for sgn in (1, -1):
        for i in range(3):
            _pan_bracket(doc, ctx, sgn, i)


def _deck(doc, ctx):
    for sgn in (1, -1):
        name = "DECK_L" if sgn > 0 else "DECK_R"
        if sgn > 0:
            y0 = "Parameters.deck_in_off"
        else:
            y0 = "-(%s)" % WOF
        lat = _y(RL, sgn)
        bores = [("Parameters.grid_hole_d",
                  {"Placement.Base.x": px, "Placement.Base.y": lat,
                   "Placement.Base.z":
                   "(Parameters.deck_z - Parameters.deck_thk / 2 - 1)"},
                  "Z", "Parameters.deck_thk + 2")
                 for px in ("-150", "-60", "30", "110")]
        # sprint-03: tower foot/cap/gusset-foot bolt rows
        if sgn > 0:
            tw_rows = (
                (("-160", "-124", "-88", "-52"),
                 "(Parameters.tower_lat_off - 5.8)"),
                (("-168", "-156", "-18", "-10"),
                 "(Parameters.tower_lat_off - 22.8)"),
                (("-172", "-158", "-22", "-8"),
                 "(Parameters.tower_lat_off - 12.8)"))
        else:
            tw_rows = (
                (("-160", "-140", "-124", "-88"),
                 "-(Parameters.tower_lat_off - 5.8)"),
                (("-160", "-140", "-124", "-88"),
                 "-(Parameters.tower_lat_off - 22.8)"),
                (("-172", "-158", "-22", "-8"),
                 "-(Parameters.tower_lat_off - 12.8)"))
        for xs, wy_ in tw_rows:
            for px in xs:
                bores.append((
                    "Parameters.grid_hole_d",
                    {"Placement.Base.x": px, "Placement.Base.y": wy_,
                     "Placement.Base.z":
                     "(Parameters.deck_z - Parameters.deck_thk / 2 - 1)"},
                    "Z", "Parameters.deck_thk + 2"))
        tools = []
        if sgn > 0:
            # shelf-riser bottom bolts through the L deck
            for sx in ("(Parameters.shelf_x_lo + 10)",
                       "(Parameters.shelf_x_hi - 10)"):
                for sy in ("(Parameters.shelf_y_lo + 8)",
                           "(Parameters.shelf_y_hi - 8)"):
                    bores.append((
                        "Parameters.grid_hole_d",
                        {"Placement.Base.x": sx, "Placement.Base.y": sy,
                         "Placement.Base.z":
                         "(Parameters.deck_z - Parameters.deck_thk / 2 "
                         "- 1)"},
                        "Z", "Parameters.deck_thk + 2"))
        else:
            # sprint-02 feed-motor/plate clearance notch in the R deck
            tools.append(pk.tool_box(
                doc, "TOOL_%s_FM" % name,
                {"Length": "66", "Width": "68", "Height": "8"},
                {"Placement.Base.x": "-70",
                 "Placement.Base.y": "-134",
                 "Placement.Base.z": "80"}))
        # column flange posts pass through the deck edges
        tools.append(pk.tool_box(
            doc, "TOOL_%s_CPA" % name,
            {"Length": "58", "Width": "22", "Height": "8"},
            {"Placement.Base.x": "-128",
             "Placement.Base.y": "62" if sgn > 0 else "-84",
             "Placement.Base.z": "80"}))
        # intake cheek towers pass through both decks (pivot clearance)
        tools.append(pk.tool_box(
            doc, "TOOL_%s_CK" % name,
            {"Length": "56", "Width": "14", "Height": "8"},
            {"Placement.Base.x": "108",
             "Placement.Base.y": "126" if sgn > 0 else "-140",
             "Placement.Base.z": "80"}))
        panel0 = pk.bored_plate(
            doc, "TOOL_" + name + "_P0", name + "_p0",
            "UNVERIFIED - deck panel pre-notch",
            {"Length": "(Parameters.deck_x_hi - Parameters.deck_x_lo)",
             "Width": "(%s - Parameters.deck_in_off)" % WOF,
             "Height": "Parameters.deck_thk"},
            {"Placement.Base.x": "Parameters.deck_x_lo",
             "Placement.Base.y": y0,
             "Placement.Base.z":
             "(Parameters.deck_z - Parameters.deck_thk / 2)"},
            bores=bores)
        panel = pk.cut(doc, name, name + "_deck_panel_UNVERIFIED",
                       "UNVERIFIED - deck panel on rail-web standoffs",
                       panel0, tools)
        _s(ctx, panel)
        _bom(ctx, "frame", "deck panel", "polycarb", "294x118x3",
             "UNVERIFIED", [panel.Name])
        rail = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
        for i, px in enumerate(("-150", "-60", "30", "110")):
            _deck_post(doc, ctx, sgn, i, px, panel.Name, rail)


def _deck_post(doc, ctx, sgn, idx, px, panel, rail):
    name = "DECK_POST_%s%d" % ("L" if sgn > 0 else "R", idx)
    lat = _y(RL, sgn)
    post = pk.standoff_hex(
        doc, name, name + "_hexstandoff_O10_UNVERIFIED",
        "UNVERIFIED - deck standoff",
        "Parameters.deck_post_d",
        "(Parameters.deck_z - Parameters.deck_thk / 2 - %s)" % RAIL_TOP,
        {"Placement.Base.x": px, "Placement.Base.y": lat,
         "Placement.Base.z": RAIL_TOP},
        tap_d="Parameters.tap_drill", tap_depth="8")
    _s(ctx, post)
    _fp(ctx, post.Name, rail)
    _fp(ctx, post.Name, panel)
    _bom(ctx, "frame", "deck standoff O10 hex", "aluminum", "O10x20",
         "UNVERIFIED", [post.Name])
    bn = "BOLT_DP_B_%s%d" % ("L" if sgn > 0 else "R", idx)
    pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
            "Parameters.bolt_d", "10", "Parameters.bolt_head_d",
            "Parameters.bolt_head_h",
            {"Placement.Base.x": px, "Placement.Base.y": lat,
             "Placement.Base.z":
             "(%s - Parameters.bolt_head_h)" % WEB_I}, "Z")
    _s(ctx, doc.getObject(bn))
    tn = "BOLT_DP_T_%s%d" % ("L" if sgn > 0 else "R", idx)
    pk.bolt(doc, tn, tn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
            "Parameters.bolt_d", "10", "Parameters.bolt_head_d",
            "Parameters.bolt_head_h",
            {"Placement.Base.x": px, "Placement.Base.y": lat,
             "Placement.Base.z":
             "(Parameters.deck_z + Parameters.deck_thk / 2 + "
             "Parameters.bolt_head_h)"}, "-Z")
    _s(ctx, doc.getObject(tn))
    _jm(ctx, "deckpost_web", [post.Name, rail], [bn], [],
        terminal=post.Name)
    _jm(ctx, "deckpost_panel", [panel, post.Name], [tn], [],
        terminal=post.Name)


def build_frame(doc, ctx):
    for sgn in (1, -1):
        _rail(doc, ctx, sgn)
    _crossmember(doc, ctx)
    _crown(doc, ctx)
    for sgn in (1, -1):
        _crown_post(doc, ctx, sgn)
        _gusset(doc, ctx, sgn)
        _tie_plate(doc, ctx, sgn)
    _belly_pan(doc, ctx)
    _deck(doc, ctx)
    _mount_plate(doc, ctx, 1)
    _mount_plate(doc, ctx, -1)
    # recessed end plugs
    for sgn in (1, -1):
        rail = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
        for tag, xe in (("F", "(Parameters.chassis_sq / 2 - "
                              "Parameters.endcap_t)"),
                        ("B", "(-Parameters.chassis_sq / 2)")):
            name = "ENDCAP_%s%s" % (tag, "L" if sgn > 0 else "R")
            ybase = ("(%s - Parameters.rail_size / 2)" % RL if sgn > 0
                     else "(-%s - Parameters.rail_size / 2)" % RL)
            _endcap(doc, ctx, name,
                    {"Placement.Base.x": xe,
                     "Placement.Base.y": ybase,
                     "Placement.Base.z": RAIL_Z0},
                    "X", rail)
    # XB crossmember mouths still open -> shortened plug that ends
    # before the under-gusset's wall leg; CR mouths are closed by the
    # crown posts themselves (no open mouth to cap).
    for sgn in (1, -1):
        name = "ENDCAP_XB_%s" % ("L" if sgn > 0 else "R")
        _endcap(doc, ctx, name,
                {"Placement.Base.x":
                 "(-Parameters.cross_x_off - Parameters.rail_size / 2)",
                 "Placement.Base.y":
                 "(Parameters.cross_half_len - Parameters.endcap_t)"
                 if sgn > 0 else "(-Parameters.cross_half_len)",
                 "Placement.Base.z": RAIL_Z0},
                "Y", "FRAME_CROSS_B", short=True)
        _fp(ctx, name, "FRAME_RAIL_%s" % ("L" if sgn > 0 else "R"))
    _number_plate(
        doc, ctx, "PLATE_NUM_L", "FRAME_RAIL_L",
        {"Placement.Base.x": "-45.5",
         "Placement.Base.y": WOF,
         "Placement.Base.z":
         "(Parameters.rail_elev_z + Parameters.rail_size / 2 - "
         "Parameters.plate_num_h)"}, "Y")
    _number_plate(
        doc, ctx, "PLATE_NUM_B", "FRAME_CROSS_B",
        {"Placement.Base.x":
         "(-Parameters.cross_x_off - Parameters.rail_size / 2 - "
         "Parameters.plate_num_t)",
         "Placement.Base.y": "-45.5",
         "Placement.Base.z":
         "(Parameters.rail_elev_z + Parameters.rail_size / 2 - "
         "Parameters.plate_num_h)"}, "X")


# =====================================================================
# DRIVETRAIN
# =====================================================================
def _wheel_carrier(doc, ctx, wtag, sx, sy):
    carrier = doc.addObject("App::Part", "WHEEL_ASSY_" + wtag)
    pk.stamp(carrier, "WHEEL_ASSY_%s_carrier_VENDOR-PENDING" % wtag,
             "VENDOR-PENDING - goBILDA 96mm mecanum assembly")
    pk.bind(carrier, {
        "Placement.Base.x": WXP if sx > 0 else WXN,
        "Placement.Base.y": WLAT if sy > 0 else "-" + WLAT,
        "Placement.Base.z": AXZ})
    _s(ctx, carrier)
    return carrier


def _wheel_hub(doc, ctx, wtag):
    """Hub: cyl O26 x hub_w with real hex REX bore + pinch tap."""
    hb = pk.tool_cyl(
        doc, "WHEEL_HUB_%s_BLK" % wtag,
        {"Radius": "Parameters.hub_dia / 2", "Height": "Parameters.hub_w"},
        {"Placement.Base.y": "(-Parameters.hub_w / 2)"},
        pk.axis_rot("Y"))
    ht = pk.tool_prism(
        doc, "WHEEL_HUB_%s_HEX" % wtag, 6,
        "(Parameters.hub_hex_af / 2 / cos(30 deg))",
        "(Parameters.hub_w + 2)",
        {"Placement.Base.y": "(-Parameters.hub_w / 2 - 1)"},
        pk.axis_rot("Y"))
    ptap = pk.tool_cyl(
        doc, "WHEEL_HUB_%s_TAP" % wtag,
        {"Radius": "Parameters.tap_drill / 2",
         "Height": "(Parameters.hub_dia / 2 + 1)"},
        {"Placement.Base.x": "0",
         "Placement.Base.z": "(Parameters.rex_af / 2 - 1)"})
    hub = pk.cut(doc, "WHEEL_HUB_" + wtag,
                 "WHEEL_HUB_%s_O26_hexbore_VENDOR-PENDING" % wtag,
                 "VENDOR-PENDING - mecanum hub, REX hex bore",
                 hb, [ht, ptap])
    _s(ctx, hub)
    return hub


def _wheel_plates(doc, ctx, wtag):
    for tag, y0 in (("IN", "(-Parameters.wheel_width / 2)"),
                    ("OUT", "(Parameters.wheel_width / 2 - "
                            "Parameters.wplate_thk)")):
        pl = pk.bore_cyl(
            doc, "WHEEL_PLATE_%s_%s" % (wtag, tag),
            "WHEEL_PLATE_%s_%s_O92_VENDOR-PENDING" % (wtag, tag),
            "VENDOR-PENDING - mecanum side plate",
            "Parameters.wplate_dia", "Parameters.wplate_thk",
            "Parameters.plate_bore",
            {"Placement.Base.y": y0}, "Y",
            chamfer_l=0.8, chamfer_min_r=40.0)
        _s(ctx, pl)


def _wheel_rollers(doc, ctx, wtag):
    pitch = float(ctx["sheet"].get("mec_roll_pitch"))
    n = int(ctx["sheet"].get("roller_count"))
    solids = []
    for k in range(n):
        frm, fused = pk.roller_subassy(
            doc, wtag, k, pitch, SLANT[wtag],
            "VENDOR-PENDING - mecanum roller",
            "goBILDA 96mm mecanum roller")
        solids.append((frm, fused))
    return solids


def build_wheel(doc, ctx, wtag, sx, sy):
    """Complete wheel assembly under WHEEL_ASSY_<wtag> carrier."""
    carrier = _wheel_carrier(doc, ctx, wtag, sx, sy)
    hub = _wheel_hub(doc, ctx, wtag)
    pk.group_add(carrier, hub)
    _wheel_plates(doc, ctx, wtag)
    for tag in ("IN", "OUT"):
        pl = doc.getObject("WHEEL_PLATE_%s_%s" % (wtag, tag))
        pk.group_add(carrier, pl)
        _fp(ctx, hub.Name, pl.Name)
        _jl(ctx, pl.Name, "AXLE_" + wtag)
    for frm, fused in _wheel_rollers(doc, ctx, wtag):
        pk.group_add(carrier, frm)
        _s(ctx, fused)
        _em(ctx, fused.Name, "WHEEL_PLATE_%s_IN" % wtag)
        _em(ctx, fused.Name, "WHEEL_PLATE_%s_OUT" % wtag)
        ctx["ground"].append(fused.Name)
    # pinch bolt: radial screw tapped into hub wall, tip on shaft flat
    bn = "BOLT_HUB_" + wtag
    b = pk.bolt(doc, bn, bn + "_M4_pinch_UNVERIFIED",
                "UNVERIFIED - hub pinch setscrew", "Parameters.bolt_d",
                "(Parameters.hub_dia / 2 - Parameters.rex_af / 2 + 2)",
                "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                {"Placement.Base.x": "0", "Placement.Base.y": "0",
                 "Placement.Base.z":
                 "(Parameters.hub_dia / 2 + Parameters.bolt_head_h)"},
                "-Z")
    pk.group_add(carrier, b)
    _s(ctx, b)
    _em(ctx, b.Name, hub.Name)
    _em(ctx, b.Name, "AXLE_" + wtag)   # tip bites the shaft flat
    _jl(ctx, hub.Name, "AXLE_" + wtag)
    _jm(ctx, "hub_pinch", [b.Name, hub.Name, "AXLE_" + wtag], [bn], [],
        terminal=hub.Name)
    ctx["carriers"].append((carrier.Name, "AXLE_" + wtag))
    return carrier


def _axle(doc, ctx, wtag, sx, sy):
    """REX hex live axle + M8 threaded tip. Tail seats in the motor
    socket; shaft carries bearings, hub, washer, nut."""
    if sy > 0:
        tail = "(%s - 6.5)" % MPL_I        # 6.5 into the 8-deep socket
        axis = "Y"
    else:
        tail = "(-(%s) + 6.5)" % MPL_I
        axis = "-Y"
    ax = pk.hex_shaft(
        doc, "AXLE_" + wtag,
        "AXLE_%s_8mmREX_M8tip_VENDOR-PENDING" % wtag,
        "VENDOR-PENDING - goBILDA 8mm REX shaft, M8 tip",
        "Parameters.rex_crad", "77",
        {"Placement.Base.x": WXP if sx > 0 else WXN,
         "Placement.Base.y": tail,
         "Placement.Base.z": AXZ},
        axis, tip_d="Parameters.shaft_tip_d",
        tip_len="Parameters.shaft_tip_len")
    _s(ctx, ax)
    _bom(ctx, "drivetrain", "8mm REX live axle, M8 tip", "steel",
         "L=112", "VENDOR-PENDING", [ax.Name])
    return ax


def _bearing(doc, ctx, name, rail, wx, sy, inner):
    """Flange bearing block flush on a rail-wall cavity face; pilot
    nests into the wall's axle clearance bore."""
    if inner:
        # cavity-side face at CVI; block extends toward cavity center
        if sy > 0:
            pos_y = CVI
            pdir = -1
        else:
            pos_y = "(-%s - Parameters.bear_t)" % CVI
            pdir = 1
        face = CVI if sy > 0 else "-(%s)" % CVI
    else:
        if sy > 0:
            pos_y = "(%s - Parameters.bear_t)" % CVO
            pdir = 1
        else:
            pos_y = "-(%s)" % CVO
            pdir = -1
        face = CVO if sy > 0 else "-(%s)" % CVO
    brg = pk.flange_bearing(
        doc, name, name + "_flangeblock_26x6_VENDOR-PENDING",
        "VENDOR-PENDING - flange bearing block",
        "Parameters.bear_w", "Parameters.bear_t", "Parameters.bear_h",
        "Parameters.bear_bore", "Parameters.bear_pilot_d",
        "Parameters.bear_pilot_l",
        {"Placement.Base.x": "(%s - Parameters.bear_w / 2)" % wx,
         "Placement.Base.y": pos_y,
         "Placement.Base.z":
         "(Parameters.wheel_dia / 2 - Parameters.bear_h / 2)"},
        "Y", bolt_d="Parameters.bear_bolt_d",
        bolt_off="Parameters.bear_bolt_off", pilot_dir=pdir)
    _s(ctx, brg)
    _fp(ctx, brg.Name, rail)
    _cn(ctx, brg.Name + "_pilot", rail) if False else None
    _bom(ctx, "drivetrain", "flange bearing block", "aluminum",
         "26x26x6 O9.6 bore O15.6 pilot", "VENDOR-PENDING", [brg.Name])
    return brg


def _motor(doc, ctx, name, wx, sy):
    """Gearbox motor: can + gb housing, hex socket bore + 4 face taps.
    Face plane flush on the mount plate's inner face."""
    face = MPL_I if sy > 0 else "-(%s)" % MPL_I
    m = pk.motor_unit(
        doc, name, name + "_5203class_gb_VENDOR-PENDING",
        "VENDOR-PENDING - 5203-class gearbox motor (D12)",
        "Parameters.motor_dia", "Parameters.motor_len",
        "Parameters.motor_gb_dia", "Parameters.motor_gb_l",
        "Parameters.sock_hex_af", "Parameters.sock_depth",
        "Parameters.tap_drill", "8", "Parameters.motor_bolt_off",
        {"Placement.Base.x": wx,
         "Placement.Base.y": face,
         "Placement.Base.z": AXZ},
        direction=(1 if sy > 0 else -1),
        tap_off_z="Parameters.motor_bolt_dz",
        vendor="5203-class planetary gearmotor")
    _s(ctx, m)
    plate = "MOUNT_PLATE_%s" % ("L" if sy > 0 else "R")
    _fp(ctx, m.Name, plate)
    _bom(ctx, "drivetrain", "5203-class gearbox motor", "motor",
         "O36 can / O40 gb", "VENDOR-PENDING", [m.Name])
    return m


def _clamp_pair(doc, ctx, wtag, wx, sy):
    """Two split-ring clamps gripping the gearbox housing; shared
    through-bolts pass both clamps + plate + wall -> cavity nuts."""
    plate = "MOUNT_PLATE_%s" % ("L" if sy > 0 else "R")
    rail = "FRAME_RAIL_L" if sy > 0 else "FRAME_RAIL_R"
    names = []
    # clamp2 flush on plate inner face; clamp1 flush on clamp2
    for i, yref in enumerate(("2", "1")):
        name = "CLAMP_%s_%s" % (wtag, yref)
        if sy > 0:
            pos_y = ("(%s - %d * Parameters.clamp_w)" % (MPL_I, i + 1))
        else:
            pos_y = ("(-%s + %d * Parameters.clamp_w)" % (MPL_I, i))
        cl = pk.clamp_block(
            doc, name, name + "_splitring_UNVERIFIED",
            "UNVERIFIED - split-ring motor clamp",
            "Parameters.clamp_w", "(Parameters.motor_gb_dia + 0.5)",
            "Parameters.clamp_ear", "Parameters.grid_hole_d",
            wx, pos_y, AXZ,
            ("(%s - 14)" % AXZ, "(%s + 14)" % AXZ))
        _s(ctx, cl)
        names.append(cl.Name)
        _cn(ctx, cl.Name, "MOTOR_" + wtag)
        _bom(ctx, "drivetrain", "motor clamp block", "aluminum",
             "O40.5 bore + ears", "UNVERIFIED", [cl.Name])
    _fp(ctx, names[0], plate)
    _fp(ctx, names[1], names[0])
    # shared ear bolts: head countersunk in clamp1 face? no - button
    # head on the chassis-side face of clamp1, shaft +Y through both
    # clamps, plate, wall -> nut in cavity
    bolts, nuts = [], []
    for i, su in enumerate((-1, 1)):
        bx = ("(%s + %d * (Parameters.motor_gb_dia / 2 + 0.25 + "
              "Parameters.clamp_ear / 2))" % (wx, su))
        for j, bz in enumerate(("(%s - 14)" % AXZ,
                               "(%s + 14)" % AXZ)):
            bn = "BOLT_CLMP_%s_%d_%d" % (wtag, i, j)
            nn = "NUT_CLMP_%s_%d_%d" % (wtag, i, j)
            if sy > 0:
                hp = {"Placement.Base.x": bx, "Placement.Base.y":
                      "(%s - 2 * Parameters.clamp_w - "
                      "Parameters.bolt_head_h)" % MPL_I,
                      "Placement.Base.z": bz}
                npos = {"Placement.Base.x": bx, "Placement.Base.y": CVI,
                        "Placement.Base.z": bz}
                ax = "Y"
            else:
                hp = {"Placement.Base.x": bx, "Placement.Base.y":
                      "(-%s + 2 * Parameters.clamp_w + "
                      "Parameters.bolt_head_h)" % MPL_I,
                      "Placement.Base.z": bz}
                npos = {"Placement.Base.x": bx,
                        "Placement.Base.y":
                        "-(%s) - Parameters.nut4_h" % CVI,
                        "Placement.Base.z": bz}
                ax = "-Y"
            pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                    "Parameters.bolt_d",
                    "(2 * Parameters.clamp_w + Parameters.mplate_t + "
                    "Parameters.rail_wall + Parameters.nut4_h + 1)",
                    "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                    hp, ax)
            pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED",
                       "UNVERIFIED - M4 nut",
                       "Parameters.nut4_wrench", "Parameters.nut4_h",
                       "Parameters.nut4_bore", npos, "Y")
            _s(ctx, doc.getObject(bn))
            _s(ctx, doc.getObject(nn))
            bolts.append(bn)
            nuts.append(nn)
    _jm(ctx, "clamp_wall", [names[0], names[1], plate, rail],
        bolts, nuts)


def build_corner(doc, ctx, wtag, sx, sy):
    """One drivetrain corner: wheel assy, axle, bearings, motor,
    clamps, cavity + outboard shaft hardware, all fasteners."""
    wx = WXP if sx > 0 else WXN
    rail = "FRAME_RAIL_L" if sy > 0 else "FRAME_RAIL_R"
    plate = "MOUNT_PLATE_%s" % ("L" if sy > 0 else "R")
    carrier = build_wheel(doc, ctx, wtag, sx, sy)
    _axle(doc, ctx, wtag, sx, sy)
    # bearings
    b_in = _bearing(doc, ctx, "BRG_IN_" + wtag, rail, wx, sy, True)
    b_out = _bearing(doc, ctx, "BRG_OUT_" + wtag, rail, wx, sy, False)
    _jl(ctx, "AXLE_" + wtag, b_in.Name)
    _jl(ctx, "AXLE_" + wtag, b_out.Name)
    # bearing bolts -> rivnuts seated in the wall bores
    for tag, brg in (("IN", b_in), ("OUT", b_out)):
        bolts, nuts = [], []
        for i, su in enumerate((-1, 1)):
            for j, sv in enumerate((-1, 1)):
                bx = "(%s + %d * Parameters.bear_bolt_off)" % (wx, su)
                bz = "(%s + %d * Parameters.bear_bolt_off)" % (AXZ, sv)
                bn = "BOLT_BRG_%s_%s_%d%d" % (tag, wtag, i, j)
                rn = "NUT_RIV_%s_%s_%d%d" % (tag, wtag, i, j)
                # rivnut body seated in the wall bore (min-y corner pos)
                if tag == "IN":
                    rv_y = ("(%s - 0.2)" % WII if sy > 0 else
                            "(-%s)" % CVI)
                else:
                    rv_y = ("(%s)" % CVO if sy > 0 else
                            "(-(%s))" % WOF)
                npos = {"Placement.Base.x": bx,
                        "Placement.Base.y": rv_y,
                        "Placement.Base.z": bz}
                rv = _rivnut(doc, rn, npos)
                _s(ctx, rv)
                _cn(ctx, rn, rail)
                # bolt head on the block's cavity-side face, shaft
                # through block bore + wall into the rivnut
                if tag == "IN":
                    if sy > 0:
                        face = "(%s + Parameters.bear_t + " \
                               "Parameters.bolt_head_h)" % CVI
                        ax = "-Y"
                        sl = "(Parameters.bear_t + Parameters.rail_wall + 1)"
                    else:
                        face = "(-(%s) - Parameters.bear_t - " \
                               "Parameters.bolt_head_h)" % CVI
                        ax = "Y"
                        sl = "(Parameters.bear_t + Parameters.rail_wall + 1)"
                else:
                    if sy > 0:
                        face = "(%s - Parameters.bear_t - " \
                               "Parameters.bolt_head_h)" % CVO
                        ax = "Y"
                        sl = ("(Parameters.bear_t + Parameters.rail_wall "
                              "- 0.3)")
                    else:
                        face = "(-(%s) + Parameters.bear_t + " \
                               "Parameters.bolt_head_h)" % CVO
                        ax = "-Y"
                        sl = ("(Parameters.bear_t + Parameters.rail_wall "
                              "- 0.3)")
                hp = {"Placement.Base.x": bx, "Placement.Base.z": bz,
                      "Placement.Base.y": face}
                pk.bolt(doc, bn, bn + "_M4_UNVERIFIED",
                        "UNVERIFIED - M4 bolt", "Parameters.bolt_d", sl,
                        "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                        hp, ax)
                _s(ctx, doc.getObject(bn))
                bolts.append(bn)
                nuts.append(rn)
                _em(ctx, bn, rn)      # thread embed in rivnut
                _jl(ctx, bn, brg.Name)  # bolt rides the bearing bores
        _jm(ctx, "bearing_" + tag, [brg.Name, rail], bolts, nuts)
    # motor
    m = _motor(doc, ctx, "MOTOR_" + wtag, wx, sy)
    _jl(ctx, "AXLE_" + wtag, m.Name)          # axle tail in socket
    # motor face bolts: flat heads countersunk into the plate's outer
    # face (wall side), shaft through plate -> motor face tap
    bolts = []
    for i, su in enumerate((-1, 1)):
        for j, sv in enumerate((-1, 1)):
            bx = "(%s + %d * Parameters.motor_bolt_off)" % (wx, su)
            bz = "(%s + %d * Parameters.motor_bolt_dz)" % (AXZ, sv)
            bn = "BOLT_MTR_%s_%d%d" % (wtag, i, j)
            if sy > 0:
                hp = {"Placement.Base.x": bx,
                      "Placement.Base.y": MPL_O,
                      "Placement.Base.z": bz}
                ax = "-Y"
            else:
                hp = {"Placement.Base.x": bx,
                      "Placement.Base.y": "-(%s)" % MPL_O,
                      "Placement.Base.z": bz}
                ax = "Y"
            fh = _flathead(doc, bn, "UNVERIFIED - M4 flat head",
                           "(Parameters.mplate_t + 4)", hp, ax)
            _s(ctx, fh)
            bolts.append(bn)
            _em(ctx, bn, m.Name)     # thread embed in motor face tap
            _cn(ctx, bn, plate)      # head nested in plate countersink
    _jm(ctx, "motor_face", [m.Name, plate], bolts, [],
        terminal=m.Name)
    # cavity shaft hardware: washer + collar + pinion on the axle
    if sy > 0:
        wpos = "(%s + Parameters.bear_t)" % CVI
        cpos = ("(%s + Parameters.bear_t + Parameters.washer_t)" % CVI)
        ppos = ("(%s + Parameters.bear_t + Parameters.washer_t + "
                "Parameters.collar_w + 1)" % CVI)
    else:
        wpos = ("(-%s - Parameters.bear_t - Parameters.washer_t)" % CVI)
        cpos = ("(-%s - Parameters.bear_t - Parameters.washer_t - "
                "Parameters.collar_w)" % CVI)
        ppos = ("(-%s - Parameters.bear_t - Parameters.washer_t - "
                "Parameters.collar_w - 1 - Parameters.pinion_w)" % CVI)
    wsh = pk.bore_cyl(
        doc, "WSH_AXLE_" + wtag, "WSH_AXLE_%s_O16_UNVERIFIED" % wtag,
        "UNVERIFIED - shaft washer", "Parameters.washer_d",
        "Parameters.washer_t", "Parameters.washer_bore",
        {"Placement.Base.x": wx, "Placement.Base.y": wpos,
         "Placement.Base.z": AXZ}, "Y")
    _s(ctx, wsh)
    col = pk.bore_cyl(
        doc, "COLLAR_" + wtag, "COLLAR_%s_O18_UNVERIFIED" % wtag,
        "UNVERIFIED - shaft collar", "Parameters.collar_d",
        "Parameters.collar_w", "Parameters.collar_bore",
        {"Placement.Base.x": wx, "Placement.Base.y": cpos,
         "Placement.Base.z": AXZ}, "Y")
    _s(ctx, col)
    pin = pk.bore_cyl(
        doc, "PINION_" + wtag, "PINION_%s_15T_hub_UNVERIFIED" % wtag,
        "VENDOR-PENDING - output coupling hub (pinion)",
        "Parameters.pinion_d", "Parameters.pinion_w",
        "Parameters.pinion_bore",
        {"Placement.Base.x": wx, "Placement.Base.y": ppos,
         "Placement.Base.z": AXZ}, "Y")
    _s(ctx, pin)
    _fp(ctx, wsh.Name, b_in.Name)
    _fp(ctx, col.Name, wsh.Name)
    for nm in (wsh, col, pin):
        _jl(ctx, "AXLE_" + wtag, nm.Name)
    _bom(ctx, "drivetrain", "shaft washer/collar/pinion", "steel",
         "O16/18/17", "UNVERIFIED", [wsh.Name, col.Name, pin.Name])
    # outboard nylock directly on the wheel plate face (thin M8
    # nylock; a separate washer would push the stack outside ENV_START)
    if sy > 0:
        no = "(%s + Parameters.wheel_width / 2)" % WLAT
    else:
        no = ("(-%s - Parameters.wheel_width / 2 - Parameters.nut8_h)"
              % WLAT)
    nut = pk.hex_nut(
        doc, "NUT_AXLE_" + wtag, "NUT_AXLE_%s_M8nylock_UNVERIFIED" % wtag,
        "UNVERIFIED - M8 thin nylock axle nut", "Parameters.nut8_wrench",
        "Parameters.nut8_h", "Parameters.nut8_bore",
        {"Placement.Base.x": wx, "Placement.Base.y": no,
         "Placement.Base.z": AXZ}, "Y")
    _s(ctx, nut)
    _fp(ctx, nut.Name,
        "WHEEL_PLATE_%s_%s" % (wtag, "OUT" if sy > 0 else "IN"))
    _em(ctx, nut.Name, "AXLE_" + wtag)   # thread embed on the tip
    _bom(ctx, "drivetrain", "M8 thin nylock axle nut", "steel",
         "M8 nylock h5", "UNVERIFIED", [nut.Name])
    # clamps (2 shared ear bolts per corner)
    _clamp_pair(doc, ctx, wtag, wx, sy)
    # the outer clamp's ear face grazes the mount-plate bolt head at
    # the corner station (real contact ~2mm2)
    mpl_bolt = {"FL": "BOLT_MPL_L_3", "RL": "BOLT_MPL_L_0",
                "FR": "BOLT_MPL_R_3", "RR": "BOLT_MPL_R_0"}[wtag]
    _cn(ctx, "CLAMP_%s_2" % wtag, mpl_bolt)
    return carrier


def build_drivetrain(doc, ctx):
    for wtag, sx, sy in CORNERS:
        build_corner(doc, ctx, wtag, sx, sy)


def _mount_plate(doc, ctx, sy):
    """Motor mount plate flush on the rail inner wall face; carries
    shaft bores, motor-bolt countersinks (outer face), plate-bolt
    countersinks (inner face), nut counterbores, clamp + grid holes."""
    name = "MOUNT_PLATE_L" if sy > 0 else "MOUNT_PLATE_R"
    rail = "FRAME_RAIL_L" if sy > 0 else "FRAME_RAIL_R"
    # bore-tool base plane: 1mm before the plate's min-y face
    pb = "(%s - 1)" % MPL_I if sy > 0 else "(-(%s) - 1)" % MPL_O
    tools = []
    for wx in (WXN, WXP):
        tag = ("P" if wx == WXP else "N")
        tools.append(pk.tool_cyl(
            doc, "%s_SHAFT_%s" % (name, tag),
            {"Radius": "Parameters.mplate_bore / 2",
             "Height": "(Parameters.mplate_t + 2)"},
            {"Placement.Base.x": wx,
             "Placement.Base.y": pb,
             "Placement.Base.z": AXZ}, pk.axis_rot("Y")))
        # motor flat-head countersinks (open on plate OUTER face)
        for su in (-1, 1):
            for sv in (-1, 1):
                bx = "(%s + %d * Parameters.motor_bolt_off)" % (wx, su)
                bz = "(%s + %d * Parameters.motor_bolt_dz)" % (AXZ, sv)
                tools.append(pk.tool_cyl(
                    doc, "%s_MB_%s_%d%d" % (name, tag, su, sv),
                    {"Radius": "Parameters.grid_hole_d / 2",
                     "Height": "(Parameters.mplate_t + 2)"},
                    {"Placement.Base.x": bx,
                     "Placement.Base.y": pb,
                     "Placement.Base.z": bz}, pk.axis_rot("Y")))
                tools.append(_sink_tool(
                    doc, "%s_SINK_%s_%d%d" % (name, tag, su, sv),
                    {"Placement.Base.x": bx,
                     "Placement.Base.y":
                     MPL_O if sy > 0 else "-(%s)" % MPL_O,
                     "Placement.Base.z": bz},
                    "-Y" if sy > 0 else "Y"))
        # bearing-bolt nut counterbores O10 (plate clears the rivnuts)
        for su in (-1, 1):
            for sv in (-1, 1):
                bx = "(%s + %d * Parameters.bear_bolt_off)" % (wx, su)
                bz = "(%s + %d * Parameters.bear_bolt_off)" % (AXZ, sv)
                tools.append(pk.tool_cyl(
                    doc, "%s_NB_%s_%d%d" % (name, tag, su, sv),
                    {"Radius": "5.0",
                     "Height": "(Parameters.mplate_t + 2)"},
                    {"Placement.Base.x": bx,
                     "Placement.Base.y": pb,
                     "Placement.Base.z": bz}, pk.axis_rot("Y")))
        # clamp ear bolt holes (two z rows)
        for su in (-1, 1):
            for j, bz in enumerate(("(%s - 14)" % AXZ,
                                   "(%s + 14)" % AXZ)):
                bx = ("(%s + %d * (Parameters.motor_gb_dia / 2 + 0.25 + "
                      "Parameters.clamp_ear / 2))" % (wx, su))
                tools.append(pk.tool_cyl(
                    doc, "%s_CL_%s_%d_%d" % (name, tag, su, j),
                    {"Radius": "Parameters.grid_hole_d / 2",
                     "Height": "(Parameters.mplate_t + 2)"},
                    {"Placement.Base.x": bx,
                     "Placement.Base.y": pb,
                     "Placement.Base.z": bz}, pk.axis_rot("Y")))
    if sy < 0:
        # intake motor plate bolt bores: 8 stations matching the wall
        for i, (bx, bz) in enumerate(
                (("-26", "-9"), ("-18", "-9"), ("-36", "-5"),
                 ("-30", "3"), ("-26", "13"), ("-36", "13"),
                 ("-18", "9"), ("-14", "17"))):
            tools.append(pk.tool_cyl(
                doc, "%s_IMP%d" % (name, i),
                {"Radius": "Parameters.grid_hole_d / 2",
                 "Height": "(Parameters.mplate_t + 2)"},
                {"Placement.Base.x":
                 "(Parameters.int_motor_x + %s)" % bx,
                 "Placement.Base.y": pb,
                 "Placement.Base.z":
                 "(Parameters.int_motor_z + %s)" % bz},
                pk.axis_rot("Y")))
        # motor face bolt shafts pass the plate into the face taps
        for i, (su, sv) in enumerate(
                ((-1, -1), (-1, 1), (1, -1), (1, 1))):
            tools.append(pk.tool_cyl(
                doc, "%s_IMT%d" % (name, i),
                {"Radius": "2.2",
                 "Height": "(Parameters.mplate_t + 2)"},
                {"Placement.Base.x":
                 "(Parameters.int_motor_x + %d * 8)" % su,
                 "Placement.Base.y": pb,
                 "Placement.Base.z":
                 "(Parameters.int_motor_z + %d * "
                  "Parameters.motor_bolt_dz)" % sv},
                pk.axis_rot("Y")))
    # plate->wall bolt grid holes + inner-face countersinks
    for i, (bx, bz) in enumerate(PLATE_HOLES):
        if True:
            tools.append(pk.tool_cyl(
                doc, "%s_G%d" % (name, i),
                {"Radius": "Parameters.grid_hole_d / 2",
                 "Height": "(Parameters.mplate_t + 2)"},
                {"Placement.Base.x": bx,
                 "Placement.Base.y": pb,
                 "Placement.Base.z": bz}, pk.axis_rot("Y")))
            tools.append(_sink_tool(
                doc, "%s_GS%d" % (name, i),
                {"Placement.Base.x": bx,
                 "Placement.Base.y":
                 MPL_I if sy > 0 else "-(%s)" % MPL_I,
                 "Placement.Base.z": bz},
                "Y" if sy > 0 else "-Y"))
    if sy > 0:
        ppos = MPL_I
    else:
        ppos = "(-%s)" % WII
    blk = pk.tool_box(
        doc, name + "_BLK",
        {"Length": "Parameters.mplate_len", "Width": "Parameters.mplate_t",
         "Height": "Parameters.mplate_h"},
        {"Placement.Base.x": "(-Parameters.mplate_len / 2)",
         "Placement.Base.y": ppos,
         "Placement.Base.z":
         "(Parameters.wheel_dia / 2 - Parameters.mplate_h / 2)"})
    pl = pk.cut(doc, name, name + "_motorplate_UNVERIFIED",
                "UNVERIFIED - motor mount plate", blk, tools)
    _s(ctx, pl)
    _fp(ctx, pl.Name, rail)
    _bom(ctx, "drivetrain", "motor mount plate", "aluminum",
         "348.5x48.3x3.05", "UNVERIFIED", [pl.Name])
    # plate -> wall bolts: flat heads in the plate inner face, shaft
    # through plate + wall -> nut in the cavity
    bolts, nuts = [], []
    for i, (bx, bz) in enumerate(PLATE_HOLES):
        if True:
            bn = "BOLT_MPL_%s_%d" % (name[-1], i)
            nn = "NUT_MPL_%s_%d" % (name[-1], i)
            if sy > 0:
                hp = {"Placement.Base.x": bx,
                      "Placement.Base.y": MPL_I,
                      "Placement.Base.z": bz}
                npos = {"Placement.Base.x": bx,
                        "Placement.Base.y": CVI,
                        "Placement.Base.z": bz}
                ax = "Y"
            else:
                hp = {"Placement.Base.x": bx,
                      "Placement.Base.y": "-(%s)" % MPL_I,
                      "Placement.Base.z": bz}
                npos = {"Placement.Base.x": bx,
                        "Placement.Base.y":
                        "-(%s) - Parameters.nut4_h" % CVI,
                        "Placement.Base.z": bz}
                ax = "-Y"
            fh = _flathead(doc, bn, "UNVERIFIED - M4 flat head",
                           "(Parameters.mplate_t + Parameters.rail_wall "
                           "+ Parameters.nut4_h)", hp, ax)
            _s(ctx, fh)
            pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED",
                       "UNVERIFIED - M4 nut", "Parameters.nut4_wrench",
                       "Parameters.nut4_h", "Parameters.nut4_bore",
                       npos, "Y")
            _s(ctx, doc.getObject(nn))
            bolts.append(bn)
            nuts.append(nn)
            _em(ctx, bn, nn)
    _jm(ctx, "mplate_rail", [pl.Name, rail], bolts, nuts)


# =================================================================
# odometry pods
# =====================================================================
def _odo_pod(doc, ctx, tag, px, py, axis, pdir):
    """Dead-wheel pod. axis='Y': wheel axle along Y (side pods);
    axis='X': axle along X (rear pod). pdir: +1/-1 = which side of the
    wheel center the arm/block sit on along the pin axis (inboard).

    mount block bolted under the pan; vertical arm plate pivoted to
    the block on an M6 pivot pin (nut retained on the block's far
    face); wheel rides a second M6 pin (embedded tail in the block,
    M6 nut on the wheel's outboard face); preload strut between block
    and arm; encoder board screwed to the arm's wheel-side face.

    Pin-axis bands (c = wheel-center coord along the pin axis):
      d=-1: block [c-27,c-15] arm [c-15,c-11] wheel [c-8,c+8]
            wpin [c-20,c+13] wnut [c+8,c+13] pnut [c-32,c-27]
            ppin [c-32,c-10.8]
      d=+1: block [c+15,c+27] arm [c+11,c+15] wheel [c-8,c+8]
            wpin [c-13,c+20] wnut [c-13,c-8] pnut [c+27,c+32]
            ppin [c+10.8,c+32]
    """
    block = "ODO_MOUNT_" + tag
    arm = "ODO_ARM_" + tag
    wheel = "ODO_WHEEL_" + tag
    pin = "ODO_AXLE_" + tag
    pin2 = "ODO_PIVOT_" + tag
    enc = "ODO_ENC_" + tag
    wz = "(Parameters.odo_wheel_d / 2)"
    comp = "y" if axis == "Y" else "x"
    d = pdir
    c = py if axis == "Y" else px
    arm_lo = "(%s %+d)" % (c, 11 if d > 0 else -15)
    blk_lo = "(%s %+d)" % (c, 15 if d > 0 else -27)
    # ---- mount block under the pan; 2 blind taps on the top face
    if axis == "Y":
        bpos = {"Placement.Base.x": "(%s - 26)" % px,
                "Placement.Base.y": blk_lo,
                "Placement.Base.z":
                "(Parameters.pan_z - Parameters.pan_thk / 2 - "
                "Parameters.odo_block_h)"}
        bdims = {"Length": "18", "Width": "12",
                 "Height": "Parameters.odo_block_h"}
        mb = [("(%s - 24)" % px, "(%s %+d)" % (py, 21 * d)),
              ("(%s - 10)" % px, "(%s %+d)" % (py, 21 * d))]
    else:
        bpos = {"Placement.Base.x": blk_lo,
                "Placement.Base.y": "(%s - 33)" % py,
                "Placement.Base.z":
                "(Parameters.pan_z - Parameters.pan_thk / 2 - "
                "Parameters.odo_block_h)"}
        bdims = {"Length": "12", "Width": "26",
                 "Height": "Parameters.odo_block_h"}
        mb = [("(%s %+d)" % (px, 21 * d), "(%s - 26)" % py),
              ("(%s %+d)" % (px, 21 * d), "(%s - 10)" % py)]
    taps = [("Parameters.tap_drill",
             {"Placement.Base.x": mx, "Placement.Base.y": my,
              "Placement.Base.z":
              "(Parameters.pan_z - Parameters.pan_thk / 2 - 10)"},
             "Z", "10") for mx, my in mb]
    blk = pk.tapped_block(doc, block, block + "_UNVERIFIED",
                          "UNVERIFIED - odometry mount block",
                          bdims, bpos, tap_bores=taps)
    _s(ctx, blk)
    _fp(ctx, blk.Name, "BELLY_PAN")
    _bom(ctx, "odometry", "pod mount block", "aluminum", "16x12x12",
         "UNVERIFIED", [blk.Name])
    bolts = []
    for i, (mx, my) in enumerate(mb):
        bn = "BOLT_ODO_%s_%d" % (tag, i)
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "10", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h",
                {"Placement.Base.x": mx, "Placement.Base.y": my,
                 "Placement.Base.z":
                 "(Parameters.pan_z + Parameters.pan_thk / 2 + "
                 "Parameters.bolt_head_h)"}, "-Z")
        _s(ctx, doc.getObject(bn))
        bolts.append(bn)
    _jm(ctx, "odo_mount", [blk.Name, "BELLY_PAN"], bolts, [],
        terminal=blk.Name)
    # ---- arm plate (4 thk): wheel-pin + pivot bores + 2 enc taps
    if axis == "Y":
        a_dims = {"Length": "50", "Width": "4", "Height": "22"}
        a_pos = {"Placement.Base.x": "(%s - 26)" % px,
                 "Placement.Base.y": arm_lo,
                 "Placement.Base.z": "6"}
        arm_bores = []
        for bx, bz in ((px, wz), ("(%s - 18)" % px, "19")):
            arm_bores.append((
                "(Parameters.odo_pin_d + 0.4)",
                {"Placement.Base.x": bx,
                 "Placement.Base.y": "(%s - 1)" % arm_lo,
                 "Placement.Base.z": bz}, "Y", "6"))
        enc_tap_y = "(%s %+d)" % (py, -14 if d < 0 else 11)
        for ex, ez in (("(%s + 8)" % px, "14"),
                       ("(%s + 16)" % px, "18")):
            arm_bores.append((
                "Parameters.tap_drill",
                {"Placement.Base.x": ex,
                 "Placement.Base.y": enc_tap_y,
                 "Placement.Base.z": ez}, "Y", "3"))
    else:
        a_dims = {"Length": "4", "Width": "52", "Height": "19.7"}
        a_pos = {"Placement.Base.x": arm_lo,
                 "Placement.Base.y": "(%s - 26)" % py,
                 "Placement.Base.z": "6"}
        arm_bores = []
        for by, bz in ((py, wz), ("(%s - 18)" % py, "19")):
            arm_bores.append((
                "(Parameters.odo_pin_d + 0.4)",
                {"Placement.Base.x": "(%s - 1)" % arm_lo,
                 "Placement.Base.y": by,
                 "Placement.Base.z": bz}, "X", "6"))
        enc_tap_x = "(%s %+d)" % (px, -14 if d < 0 else 11)
        for ey, ez in (("(%s - 6)" % py, "12"),
                       ("(%s - 0)" % py, "18")):
            arm_bores.append((
                "Parameters.tap_drill",
                {"Placement.Base.x": enc_tap_x,
                 "Placement.Base.y": ey,
                 "Placement.Base.z": ez}, "X", "3"))
    arm_o = pk.bored_plate(doc, arm, arm + "_pivotarm_UNVERIFIED",
                           "UNVERIFIED - odometry swing arm",
                           a_dims, a_pos, bores=arm_bores)
    _s(ctx, arm_o)
    _fp(ctx, arm_o.Name, blk.Name)
    _bom(ctx, "odometry", "odo swing arm", "aluminum", "52x4x20",
         "UNVERIFIED", [arm_o.Name])
    # ---- wheel disc
    wpos = ({"Placement.Base.x": px,
             "Placement.Base.y": "(%s - Parameters.odo_wheel_w / 2)" % py,
             "Placement.Base.z": wz}
            if axis == "Y" else
            {"Placement.Base.x":
             "(%s - Parameters.odo_wheel_w / 2)" % px,
             "Placement.Base.y": py,
             "Placement.Base.z": wz})
    wl = pk.bore_cyl(doc, wheel, wheel + "_O48x16_VENDOR-PENDING",
                     "VENDOR-PENDING - 48mm odometry wheel",
                     "Parameters.odo_wheel_d", "Parameters.odo_wheel_w",
                     "(Parameters.odo_pin_d + 0.4)", wpos, axis)
    _s(ctx, wl)
    ctx["ground"].append(wl.Name)
    _bom(ctx, "odometry", "48mm dead wheel", "polyurethane", "O48x16",
         "VENDOR-PENDING", [wl.Name])
    # ---- pins
    def _pin(nm, lo, ln, at, atz):
        pp = {"Placement.Base.z": atz}
        pp["Placement.Base." + comp] = lo
        pp["Placement.Base." + ("x" if comp == "y" else "y")] = at
        p = pk.shaft(doc, nm, nm + "_M6pin_UNVERIFIED",
                     "UNVERIFIED - M6 pin",
                     "Parameters.odo_pin_d", ln, pp, axis)
        _s(ctx, p)
        return p
    wp_lo = "(%s %+d)" % (c, -13 if d > 0 else -20)
    pp_lo = "(%s %+d)" % (c, 10.8 if d > 0 else -32)
    wpin = _pin(pin, wp_lo, "33", px if axis == "Y" else py, wz)
    ppin = _pin(pin2, pp_lo, "21.2",
                ("(%s - 18)" % px) if axis == "Y"
                else ("(%s - 18)" % py), "19")
    _jl(ctx, wpin.Name, wl.Name)
    _jl(ctx, wpin.Name, arm_o.Name)
    _em(ctx, wpin.Name, blk.Name)
    _em(ctx, wpin.Name, "BELLY_PAN")   # tail crown bites the slot edge
    _jl(ctx, ppin.Name, arm_o.Name)
    _em(ctx, ppin.Name, blk.Name)
    # nuts: wheel-pin nut on the wheel outboard face; pivot nut on the
    # block's far face
    wn_off, pn_off = (8, -32) if d < 0 else (-13, 27)
    nuts = []
    for k, (pn, noff, nat, natz) in enumerate((
            (pin, wn_off, px if axis == "Y" else py, wz),
            (pin2, pn_off,
             ("(%s - 18)" % px) if axis == "Y" else "(%s - 18)" % py,
             "19"))):
        nn = "NUT_%s" % pn
        np_ = {"Placement.Base.z": natz}
        np_["Placement.Base." + comp] = "(%s %+d)" % (c, noff)
        np_["Placement.Base." + ("x" if comp == "y" else "y")] = nat
        n = pk.hex_nut(doc, nn, nn + "_M6_UNVERIFIED",
                       "UNVERIFIED - M6 nut", "Parameters.nut6_wrench",
                       "Parameters.nut6_h", "Parameters.nut6_bore",
                       np_, axis)
        _s(ctx, n)
        _em(ctx, nn, pn)
        nuts.append(nn)
    _jm(ctx, "odo_wheelpin", [wl.Name, arm_o.Name, block], [pin],
        [nuts[0]])
    _jm(ctx, "odo_pivot", [arm_o.Name, blk.Name], [pin2], [nuts[1]])
    # ---- preload strut + encoder board
    _odo_spring(doc, ctx, tag, px, py, axis, d, blk.Name, arm_o.Name)
    if axis == "Y":
        epos = {"Placement.Base.x": "(%s + 4)" % px,
                "Placement.Base.y": "(%s %+d)" % (py, -11 if d < 0 else 9),
                "Placement.Base.z": "10"}
        edims = {"Length": "16", "Width": "2", "Height": "12"}
    else:
        epos = {"Placement.Base.x": "(%s %+d)" % (px, -11 if d < 0 else 9),
                "Placement.Base.y": "(%s - 8)" % py,
                "Placement.Base.z": "9"}
        edims = {"Length": "2", "Width": "16", "Height": "12"}
    en = pk.plate(doc, enc, enc + "_encoder_pcb_UNVERIFIED",
                  "UNVERIFIED - pod encoder board", edims, epos)
    _s(ctx, en)
    _fp(ctx, en.Name, arm_o.Name)
    _bom(ctx, "odometry", "pod encoder board", "pcb", "16x2x12",
         "UNVERIFIED", [en.Name])
    # countersunk M3 selftaps through the board into the arm face taps
    for i, (eg, ez) in enumerate((("(%s + 8)" % (px if axis == "Y"
                                               else py), "14"),
                                  ("(%s + 16)" % (px if axis == "Y"
                                                  else py), "18"))):
        if axis == "X":
            eg = "(%s - %d)" % (py, (6, 0)[i])
            ez = ("12", "18")[i]
        sn = "SCRW_ENC_%s_%d" % (tag, i)
        if axis == "Y":
            hp = {"Placement.Base.x": eg, "Placement.Base.z": ez,
                  "Placement.Base.y": "(%s %+d)" % (py, -9 if d < 0
                                                  else 9)}
            sax = "-Y" if d < 0 else "Y"
        else:
            hp = {"Placement.Base.x": "(%s %+d)" % (px, -9 if d < 0
                                                  else 9),
                  "Placement.Base.y": eg, "Placement.Base.z": ez}
            sax = "-X" if d < 0 else "X"
        pk.bolt(doc, sn, sn + "_M3_selftap_UNVERIFIED",
                "UNVERIFIED - M3 selftap", "3", "5.5", "6", "1.8",
                hp, sax)
        _s(ctx, doc.getObject(sn))
        _em(ctx, sn, arm_o.Name)
        _em(ctx, sn, en.Name)
        _em(ctx, sn, block)


def _odo_spring(doc, ctx, tag, px, py, axis, d, block, arm):
    """Preload strut: seat pads on the block end face and the arm free
    end face (declared contacts), wire body between the pad outers."""
    spring = "ODO_SPRING_" + tag
    sheet = ctx["sheet"]
    pxv = pk.pval(sheet, "odo_pod_x") if "odo_pod_x" in px else         pk.pval(sheet, "odo_pod_lon_x")
    pyv = pk.pval(sheet, "odo_pod_lat") if "odo_pod_lat" in py else 0.0
    if py.strip().startswith("(-"):
        pyv = -pyv
    pan_b = pk.pval(sheet, "pan_z") - pk.pval(sheet, "pan_thk") / 2
    blk_z = pan_b - pk.pval(sheet, "odo_block_h")
    if axis == "Y":
        arm_y = pyv + (11 if d > 0 else -15)     # arm band lo
        arm_mid = arm_y + 2
        pa_y = arm_mid - 9 if d < 0 else arm_mid + 5
        pa = pk.plate(
            doc, "TOOL_" + spring + "_PA", spring + "_padA_UNVERIFIED",
            "UNVERIFIED - strut seat pad on pan underside",
            {"Length": "6", "Width": "4", "Height": "2"},
            {"Placement.Base.x": str(pxv + 10),
             "Placement.Base.y": str(pa_y),
             "Placement.Base.z": str(pan_b - 2)})
        pb = pk.plate(
            doc, "TOOL_" + spring + "_PB", spring + "_padB_UNVERIFIED",
            "UNVERIFIED - strut seat pad on arm top",
            {"Length": "6", "Width": "4", "Height": "2"},
            {"Placement.Base.x": str(pxv + 17),
             "Placement.Base.y": str(arm_mid - 2),
             "Placement.Base.z": "28"})
        p1 = (pxv + 13, pa_y + 2, pan_b - 2)
        pm = (pxv + 18, pyv + 15.54 * d, pan_b - 2)
        p2 = (pxv + 20, arm_mid, 30.0)
    else:
        arm_x = pxv + (11 if d > 0 else -15)
        arm_mid = arm_x + 2
        pa = pk.plate(
            doc, "TOOL_" + spring + "_PA", spring + "_padA_UNVERIFIED",
            "UNVERIFIED - strut seat pad on pan underside",
            {"Length": "4", "Width": "6", "Height": "2"},
            {"Placement.Base.x": str(arm_mid - 2),
             "Placement.Base.y": str(pyv + 32),
             "Placement.Base.z": str(pan_b - 2)})
        pb = pk.plate(
            doc, "TOOL_" + spring + "_PB", spring + "_padB_UNVERIFIED",
            "UNVERIFIED - strut seat pad on arm top",
            {"Length": "4", "Width": "6", "Height": "2"},
            {"Placement.Base.x": str(arm_mid - 2),
             "Placement.Base.y": str(pyv + 18),
             "Placement.Base.z": "28"})
        p1 = (arm_mid, pyv + 35, pan_b - 2)
        pm = (arm_mid, pyv + 28, pan_b - 2)
        p2 = (arm_mid, pyv + 21, 30.0)
    s1 = pk.wire_seg(doc, "TOOL_" + spring + "_S1",
                       spring + "_body1",
                       "UNVERIFIED - pod preload strut", 8.0,
                       p1, pm)
    s2 = pk.wire_seg(doc, "TOOL_" + spring + "_S2", spring + "_body2",
                       "UNVERIFIED - pod preload strut", 8.0,
                       pm, p2)
    fused = pk.fuse(doc, spring, spring + "_strut_UNVERIFIED",
                    "UNVERIFIED - pod preload strut", pa,
                    [pb, s1, s2])
    _s(ctx, fused)
    _fp(ctx, fused.Name, "BELLY_PAN")
    _fp(ctx, fused.Name, arm)
    _cn(ctx, fused.Name, "BELLY_PAN")
    _cn(ctx, fused.Name, arm)
    _bom(ctx, "odometry", "pod preload strut", "steel+delrin",
         "O8 spring", "UNVERIFIED", [fused.Name])


def build_pods(doc, ctx):
    _odo_pod(doc, ctx, "LAT_L", "Parameters.odo_pod_x",
             "Parameters.odo_pod_lat", "Y", -1)
    _odo_pod(doc, ctx, "LAT_R", "Parameters.odo_pod_x",
             "(-Parameters.odo_pod_lat)", "Y", 1)
    _odo_pod(doc, ctx, "LON", "Parameters.odo_pod_lon_x", "0", "X", 1)


# =====================================================================
# electronics (also built inside the electronics file)
# =====================================================================
def _hub_block(doc, ctx, name, dims, pos, face_to, bolts_into, bom_row):
    """Rectangular electronic brick on 4 feet with through-bolt holes."""
    o = pk.plate(doc, name, name + "_brick_UNVERIFIED",
                 "UNVERIFIED - electronics brick", dims, pos)
    _s(ctx, o)
    _fp(ctx, o.Name, face_to)
    _bom(ctx, bom_row[0], bom_row[1], bom_row[2], bom_row[3],
         bom_row[4], [o.Name])
    return o


def _coplanar_elec(doc, ctx):
    """ASM4: coincident-face pairs the fastener census must see."""
    _cn(ctx, "BOLT_STRAP_0_0", "WIRE_SW_CTRL")
    _cn(ctx, "BATT_STRAP_0", "SWITCH_BRKT")

    _fp(ctx, "BOLT_SO_T_0", "HUB_EXP")
    _fp(ctx, "BOLT_SO_T_2", "HUB_EXP")
    _fp(ctx, "DECK_POST_L0", "BOLT_SO_B_1")
    _fp(ctx, "BOLT_DP_T_L0", "STANDOFF_1")
    # master-scope pairs (subsystem builds drop missing names)
    _fp(ctx, "BRG_OUT_FR", "CHAIN_GUARD")
    _fp(ctx, "BOLT_MPL_R_11", "CLAMP_FR_2")
    _fp(ctx, "BOLT_MPL_L_11", "CLAMP_FL_2")
    _em(ctx, "BOLT_MPL_R_3", "INT_MOTOR")
    for i in range(4):
        _fp(ctx, "ELEC_SHELF", "BOLT_SO_T_%d" % i)
    _fp(ctx, "FEED_MTR_PLATE", "BOLT_FSO_0")
    _fp(ctx, "FEED_MTR_PLATE", "BOLT_FSO_1")
    _fp(ctx, "FEED_MTR_PLATE", "FEED_MTR_SHAFT")
    # encoder wire rides over/behind real geometry on its way to the hub
    _em(ctx, "WIRE_ENC_LON", "MOTOR_RL")
    _em(ctx, "WIRE_ENC_LON", "ELEC_SHELF")
    _em(ctx, "WIRE_ENC_LON", "SCRW_ENC_LON_1")
    _em(ctx, "WIRE_ENC_LON", "ODO_ARM_LON")


def _battery(doc, ctx):
    b = pk.plate(doc, "BATTERY",
                 "BATTERY_3000mAh_pack_VENDOR-PENDING",
                 "VENDOR-PENDING - 3000mAh 12V pack (D12)",
                 {"Length": "Parameters.batt_l",
                  "Width": "Parameters.batt_w",
                  "Height": "Parameters.batt_h"},
                 {"Placement.Base.x":
                  "(Parameters.batt_x - Parameters.batt_l / 2)",
                  "Placement.Base.y":
                  "(Parameters.batt_y - Parameters.batt_w / 2)",
                  "Placement.Base.z":
                  "(Parameters.pan_z + Parameters.pan_thk / 2)"})
    _s(ctx, b)
    _fp(ctx, b.Name, "BELLY_PAN")
    _bom(ctx, "electronics", "3000mAh 12V battery", "battery",
         "75x45x22", "VENDOR-PENDING", [b.Name])
    return b


def _strap(doc, ctx, idx):
    """Battery strap: U-band over the pack + foot tabs bolted to pan."""
    name = "BATT_STRAP_%d" % idx
    sx = ("(Parameters.batt_x - Parameters.batt_l / 2 + 10)" if idx == 0
          else "(Parameters.batt_x + Parameters.batt_l / 2 - 10 - "
                "Parameters.strap_w)")
    strap = pk.strap_u(
        doc, name, name + "_strap_UNVERIFIED",
        "UNVERIFIED - battery strap",
        "Parameters.strap_w",
        "(Parameters.batt_w + 2 * Parameters.strap_t)",
        "(Parameters.batt_h + Parameters.strap_t)",
        "Parameters.strap_t",
        "Parameters.strap_foot", "Parameters.grid_hole_d",
        {"Placement.Base.x": sx,
         "Placement.Base.y":
         "(Parameters.batt_y - Parameters.batt_w / 2 - "
         "Parameters.strap_t - Parameters.strap_foot)",
         "Placement.Base.z":
         "(Parameters.pan_z + Parameters.pan_thk / 2)"})
    _s(ctx, strap)
    _fp(ctx, strap.Name, "BELLY_PAN")
    _em(ctx, strap.Name, "BATTERY")
    _bom(ctx, "electronics", "battery strap", "nylon", "wrap",
         "UNVERIFIED", [strap.Name])
    bolts, nuts = [], []
    for i, sgn in enumerate((-1, 1)):
        bn = "BOLT_STRAP_%d_%d" % (idx, i)
        nn = "NUT_STRAP_%d_%d" % (idx, i)
        by = ("(Parameters.batt_y - Parameters.batt_w / 2 - "
              "Parameters.strap_t - Parameters.strap_foot / 2)"
              if sgn < 0 else
              "(Parameters.batt_y + Parameters.batt_w / 2 + "
              "Parameters.strap_t + Parameters.strap_foot / 2)")
        bx = "(%s + Parameters.strap_w / 2)" % sx
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "10", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h",
                {"Placement.Base.x": bx,
                 "Placement.Base.y": by,
                 "Placement.Base.z":
                 "(Parameters.pan_z + Parameters.pan_thk / 2 + 3 + "
                 "Parameters.bolt_head_h)"}, "-Z")
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore",
                   {"Placement.Base.x": bx,
                    "Placement.Base.y": by,
                    "Placement.Base.z":
                    "(Parameters.pan_z - Parameters.pan_thk / 2 - "
                    "Parameters.nut4_h)"}, "Z")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "strap_pan", [strap.Name, "BELLY_PAN"], bolts, nuts)


def _shelf(doc, ctx):
    # riser panel on DECK_L carrying the expansion hub: four standoffs
    # bolt up through the deck, hub feet through-bolt the shelf
    sxy = [("(Parameters.shelf_x_lo + 10)",
            "(Parameters.shelf_y_lo + 8)"),
           ("(Parameters.shelf_x_lo + 10)",
            "(Parameters.shelf_y_hi - 8)"),
           ("(Parameters.shelf_x_hi - 10)",
            "(Parameters.shelf_y_lo + 8)"),
           ("(Parameters.shelf_x_hi - 10)",
            "(Parameters.shelf_y_hi - 8)")]
    bores = [("Parameters.grid_hole_d",
              {"Placement.Base.x": sx, "Placement.Base.y": sy,
               "Placement.Base.z":
               "(Parameters.shelf_z - Parameters.shelf_thk / 2 - 1)"},
              "Z", "Parameters.shelf_thk + 2") for sx, sy in sxy]
    # expansion-hub foot bolt holes through the shelf
    for fx in ("(Parameters.exp_x - 40)", "(Parameters.exp_x + 40)"):
        for fy in ("(Parameters.exp_y - 38)", "(Parameters.exp_y + 38)"):
            bores.append((
                "Parameters.grid_hole_d",
                {"Placement.Base.x": fx, "Placement.Base.y": fy,
                 "Placement.Base.z":
                 "(Parameters.shelf_z - Parameters.shelf_thk / 2 - 1)"},
                "Z", "Parameters.shelf_thk + 2"))
    sh = pk.bored_plate(doc, "ELEC_SHELF", "ELEC_SHELF_tray_UNVERIFIED",
                        "UNVERIFIED - electronics riser shelf",
                        {"Length": "(Parameters.shelf_x_hi - "
                         "Parameters.shelf_x_lo)",
                         "Width": "(Parameters.shelf_y_hi - "
                                  "Parameters.shelf_y_lo)",
                         "Height": "Parameters.shelf_thk"},
                        {"Placement.Base.x": "Parameters.shelf_x_lo",
                         "Placement.Base.y": "Parameters.shelf_y_lo",
                         "Placement.Base.z":
                         "(Parameters.shelf_z - Parameters.shelf_thk / 2)"},
                        bores=bores)
    _s(ctx, sh)
    _bom(ctx, "electronics", "electronics shelf", "polycarb",
         "86x128x2", "UNVERIFIED", [sh.Name])
    # 4 standoffs pan->shelf with bolts both ends
    for i, (sx, sy) in enumerate(sxy):
        sn = "STANDOFF_%d" % i
        so = pk.standoff_hex(
            doc, sn, sn + "_standoff_UNVERIFIED",
            "UNVERIFIED - shelf riser standoff on the deck",
            "Parameters.standoff_d",
            "(Parameters.shelf_z - Parameters.shelf_thk / 2 - "
            "Parameters.deck_z - Parameters.deck_thk / 2)",
            {"Placement.Base.x": sx,
             "Placement.Base.y": sy,
             "Placement.Base.z":
             "(Parameters.deck_z + Parameters.deck_thk / 2)"},
            tap_d="Parameters.tap_drill", tap_depth="8")
        _s(ctx, so)
        _fp(ctx, so.Name, "DECK_L")
        _fp(ctx, so.Name, "ELEC_SHELF")
        _bom(ctx, "electronics", "shelf standoff", "aluminum", "O8x31",
             "UNVERIFIED", [so.Name])
        bn = "BOLT_SO_B_%d" % i
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "9", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h",
                {"Placement.Base.x": sx,
                 "Placement.Base.y": sy,
                 "Placement.Base.z":
                 "(Parameters.deck_z - Parameters.deck_thk / 2 - "
                 "Parameters.bolt_head_h)"}, "Z")
        _s(ctx, doc.getObject(bn))
        tn = "BOLT_SO_T_%d" % i
        pk.bolt(doc, tn, tn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "9", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h",
                {"Placement.Base.x": sx,
                 "Placement.Base.y": sy,
                 "Placement.Base.z":
                 "(Parameters.shelf_z + Parameters.shelf_thk / 2 + "
                 "Parameters.bolt_head_h)"}, "-Z")
        _s(ctx, doc.getObject(tn))
        _jm(ctx, "shelf_so", [so.Name, "DECK_L"],
            [bn, tn], [], terminal=so.Name)
        if i in (0, 2):
            _fp(ctx, "BOLT_SO_T_%d" % i, "HUB_EXP")
        if i == 1:
            _fp(ctx, "BOLT_SO_B_%d" % i, "DECK_POST_L0")
            _fp(ctx, "BOLT_DP_T_L0", so.Name)


def _switch_bracket(doc, ctx):
    """Main switch: L-bracket (foot on pan + face plate) + switch body
    self-tapped onto the face."""
    brkt = "SWITCH_BRKT"
    foot = pk.tool_box(
        doc, brkt + "_FT",
        {"Length": "30", "Width": "20", "Height": "3"},
        {"Placement.Base.x": "(Parameters.sw_x - 15)",
         "Placement.Base.y": "(Parameters.sw_y - 10)",
         "Placement.Base.z":
         "(Parameters.pan_z + Parameters.pan_thk / 2)"})
    face = pk.tool_box(
        doc, brkt + "_FC",
        {"Length": "30", "Width": "3", "Height": "24"},
        {"Placement.Base.x": "(Parameters.sw_x - 15)",
         "Placement.Base.y": "(Parameters.sw_y - 3)",
         "Placement.Base.z":
         "(Parameters.pan_z + Parameters.pan_thk / 2)"})
    tools = []
    for i, dx in enumerate(("-10", "10")):
        tools.append(pk.tool_cyl(
            doc, "%s_H%d" % (brkt, i),
            {"Radius": "Parameters.grid_hole_d / 2", "Height": "6"},
            {"Placement.Base.x": "(Parameters.sw_x + %s)" % dx,
             "Placement.Base.y": "(Parameters.sw_y - 5)",
             "Placement.Base.z":
             "(Parameters.pan_z + Parameters.pan_thk / 2 - 1)"}))
    for i, (dx, dz) in enumerate((("-8", "14"), ("8", "22"))):
        tools.append(pk.tool_cyl(
            doc, "%s_T%d" % (brkt, i),
            {"Radius": "Parameters.grid_hole_d / 2", "Height": "5"},
            {"Placement.Base.x": "(Parameters.sw_x + %s)" % dx,
             "Placement.Base.y": "(Parameters.sw_y - 3.5)",
             "Placement.Base.z":
             "(Parameters.pan_z + Parameters.pan_thk / 2 + %s)" % dz},
            pk.axis_rot("Y")))
    bk = pk.cut(doc, brkt, brkt + "_Lbracket_UNVERIFIED",
                "UNVERIFIED - main switch L-bracket",
                pk.fuse(doc, pk.TOOL_PREFIX + brkt + "_FU",
                        brkt + "_fu", "UNVERIFIED - bracket fuse",
                        foot, face), tools)
    _s(ctx, bk)
    _fp(ctx, bk.Name, "BELLY_PAN")
    _bom(ctx, "electronics", "switch bracket", "aluminum", "L30x20x24",
         "UNVERIFIED", [bk.Name])
    bolts, nuts = [], []
    for i, dx in enumerate(("-10", "10")):
        bn = "BOLT_SW_%d" % i
        nn = "NUT_SW_%d" % i
        pk.bolt(doc, bn, bn + "_M4_UNVERIFIED", "UNVERIFIED - M4 bolt",
                "Parameters.bolt_d", "10", "Parameters.bolt_head_d",
                "Parameters.bolt_head_h",
                {"Placement.Base.x": "(Parameters.sw_x + %s)" % dx,
                 "Placement.Base.y": "(Parameters.sw_y - 5)",
                 "Placement.Base.z":
                 "(Parameters.pan_z + Parameters.pan_thk / 2 + 3 + "
                 "Parameters.bolt_head_h)"}, "-Z")
        pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED", "UNVERIFIED - M4 nut",
                   "Parameters.nut4_wrench", "Parameters.nut4_h",
                   "Parameters.nut4_bore",
                   {"Placement.Base.x": "(Parameters.sw_x + %s)" % dx,
                    "Placement.Base.y": "(Parameters.sw_y - 5)",
                    "Placement.Base.z":
                    "(Parameters.pan_z - Parameters.pan_thk / 2 - "
                    "Parameters.nut4_h)"}, "Z")
        _s(ctx, doc.getObject(bn))
        _s(ctx, doc.getObject(nn))
        bolts.append(bn)
        nuts.append(nn)
    _jm(ctx, "switch_brkt", [bk.Name, "BELLY_PAN"], bolts, nuts)
    sw = pk.plate(
        doc, "MAIN_SWITCH", "MAIN_SWITCH_toggle_UNVERIFIED",
        "UNVERIFIED - main power switch on bracket face",
        {"Length": "Parameters.sw_l", "Width": "Parameters.sw_w",
         "Height": "Parameters.sw_h"},
        {"Placement.Base.x":
         "(Parameters.sw_x - Parameters.sw_l / 2)",
         "Placement.Base.y": "(Parameters.sw_y - 3 - Parameters.sw_w)",
         "Placement.Base.z":
         "(Parameters.pan_z + Parameters.pan_thk / 2 + 9)"})
    _s(ctx, sw)
    _fp(ctx, sw.Name, brkt)
    _bom(ctx, "electronics", "main power switch", "switch",
         "15x9x13", "UNVERIFIED", [sw.Name])
    # 2 self-tap screws through the bracket face into the switch body
    # (heads on the bracket's rear face, tips embed in the switch)
    for i, (dx, dz) in enumerate((("-8", "12"), ("8", "18"))):
        sn = "SCRW_SW_%d" % i
        pk.bolt(doc, sn, sn + "_M3_selftap_UNVERIFIED",
                "UNVERIFIED - M3 selftap", "3", "6", "6", "1.8",
                {"Placement.Base.x": "(Parameters.sw_x + %s)" % dx,
                 "Placement.Base.y": "(Parameters.sw_y + 1.8)",
                 "Placement.Base.z":
                 "(Parameters.pan_z + Parameters.pan_thk / 2 + %s)" % dz},
                "-Y")
        _s(ctx, doc.getObject(sn))
        _em(ctx, sn, sw.Name)
        _em(ctx, sn, brkt)


def _hubs(doc, ctx):
    """REV hubs on 4 feet: block + 2 fused side tabs; through-bolts
    pass foot tab + pan -> nut under the pan. The ctrl hub is rotated
    90deg (ehub_w along X, hub_l along Y) so it fits the pan's free
    center lane between the motor columns."""
    hubs = {}
    for tag, hx, hy in (("C", "Parameters.ctrl_x", "Parameters.ctrl_y"),
                        ("E", "Parameters.exp_x", "Parameters.exp_y")):
        name = "HUB_CTRL" if tag == "C" else "HUB_EXP"
        shelf_tag = tag == "E"
        rot = tag == "C"
        base_z = ("(Parameters.shelf_z + Parameters.shelf_thk / 2)"
                  if shelf_tag else
                  "(Parameters.pan_z + Parameters.pan_thk / 2)")
        if rot:
            bd = {"Length": "Parameters.ehub_w",
                  "Width": "Parameters.hub_l",
                  "Height": "Parameters.hub_h"}
            bp = {"Placement.Base.x":
                  "(%s - Parameters.ehub_w / 2)" % hx,
                  "Placement.Base.y":
                  "(%s - Parameters.hub_l / 2)" % hy,
                  "Placement.Base.z": base_z}
            fd = {"Length": "10", "Width": "Parameters.hub_l",
                  "Height": "3"}
            f1p = {"Placement.Base.x":
                   "(%s - Parameters.ehub_w / 2 - 7)" % hx,
                   "Placement.Base.y": bp["Placement.Base.y"],
                   "Placement.Base.z": base_z}
            f2p = {"Placement.Base.x":
                   "(%s + Parameters.ehub_w / 2 - 3)" % hx,
                   "Placement.Base.y": bp["Placement.Base.y"],
                   "Placement.Base.z": base_z}
        else:
            bd = {"Length": "Parameters.hub_l",
                  "Width": "Parameters.ehub_w",
                  "Height": "Parameters.hub_h"}
            bp = {"Placement.Base.x":
                  "(%s - Parameters.hub_l / 2)" % hx,
                  "Placement.Base.y":
                  "(%s - Parameters.ehub_w / 2)" % hy,
                  "Placement.Base.z": base_z}
            fd = {"Length": "Parameters.hub_l", "Width": "10",
                  "Height": "3"}
            f1p = {"Placement.Base.x": bp["Placement.Base.x"],
                   "Placement.Base.y":
                   "(%s - Parameters.ehub_w / 2 + 0.5)" % hy,
                   "Placement.Base.z": base_z}
            f2p = {"Placement.Base.x": bp["Placement.Base.x"],
                   "Placement.Base.y":
                   "(%s + Parameters.ehub_w / 2 - 10.5)" % hy,
                   "Placement.Base.z": base_z}
        blk = pk.tool_box(doc, name + "_BLK", bd, bp)
        f1 = pk.tool_box(doc, name + "_F0", fd, f1p)
        f2 = pk.tool_box(doc, name + "_F1", fd, f2p)
        hub = pk.fuse(
            doc, name, name + "_hubfeet_VENDOR-PENDING",
            "VENDOR-PENDING - REV hub with foot tabs", blk, [f1, f2])
        _s(ctx, hub)
        _fp(ctx, hub.Name, "ELEC_SHELF" if shelf_tag else "BELLY_PAN")
        _bom(ctx, "electronics", "REV hub (ctrl)" if tag == "C" else
             "REV hub (exp)", "hub", "142x79x29", "VENDOR-PENDING",
             [hub.Name])
        hubs[tag] = hub
        bolts, nuts = [], []
        fdy = "-38" if shelf_tag else "-44.5"
        fdy2 = "38" if shelf_tag else "44.5"
        grid = (("-40", fdy), ("40", fdy), ("-40", fdy2),
                ("40", fdy2))
        for i, (dx, dy) in enumerate(grid):
            bn = "BOLT_HUB_%s_%d" % (tag, i)
            nn = "NUT_HUB_%s_%d" % (tag, i)
            pk.bolt(doc, bn, bn + "_M4_UNVERIFIED",
                    "UNVERIFIED - M4 hub foot bolt",
                    "Parameters.bolt_d", "10",
                    "Parameters.bolt_head_d", "Parameters.bolt_head_h",
                    {"Placement.Base.x": "(%s + %s)" % (hx, dx),
                     "Placement.Base.y": "(%s + %s)" % (hy, dy),
                     "Placement.Base.z":
                     "(%s + 3 + Parameters.bolt_head_h)" % base_z}, "-Z")
            pk.hex_nut(doc, nn, nn + "_M4_UNVERIFIED",
                       "UNVERIFIED - M4 nut", "Parameters.nut4_wrench",
                       "Parameters.nut4_h", "Parameters.nut4_bore",
                       {"Placement.Base.x": "(%s + %s)" % (hx, dx),
                        "Placement.Base.y": "(%s + %s)" % (hy, dy),
                        "Placement.Base.z":
                        "(%s - 2 - Parameters.nut4_h)" % base_z}, "Z")
            _s(ctx, doc.getObject(bn))
            _s(ctx, doc.getObject(nn))
            bolts.append(bn)
            nuts.append(nn)
        _jm(ctx, "hub_mount",
            [hub.Name, "ELEC_SHELF" if shelf_tag else "BELLY_PAN"],
            bolts, nuts)


def _wire(doc, ctx, name, points, dia="3"):
    w = pk.wire_bundle(doc, name, name + "_wirerun_UNVERIFIED",
                       "UNVERIFIED - wire run", float(dia), points)
    _s(ctx, w)
    _bom(ctx, "electronics", "wire run", "wire", "O%s" % dia,
         "UNVERIFIED", [w.Name])
    return w


def _clip(doc, ctx, name, pos, member):
    c = pk.plate(doc, name, name + "_cableclip_UNVERIFIED",
                 "UNVERIFIED - adhesive cable clip",
                 {"Length": "12", "Width": "12", "Height": "4"}, pos)
    _s(ctx, c)
    _fp(ctx, c.Name, member)
    _bom(ctx, "electronics", "adhesive cable clip", "nylon", "12x12x4",
         "UNVERIFIED", [c.Name])


def _wiring(doc, ctx):
    """Sprint-01 wiring subset: battery->switch->hub trunks, RS485 hub
    link, 4 motor leads, 3 encoder leads, clip anchors."""
    # battery pack [20,160]x[5,75]; switch face at (-158,-80);
    # ctrl hub on the pan (y>=45.5 face); exp hub on the shelf (z>=86.3)
    # battery pack [-5,135]x[-35,35]; switch at (-115,0); ctrl hub
    # rotated at (-48.5,0): x[-95,-2] y[-71,71], +y face = wiring edge
    wb = _wire(doc, ctx, "WIRE_BATT_SW", [
        (60.0, -20.0, 55.0), (70.0, -30.0, 38.0),
        (45.0, -44.0, 36.0), (52.0, -48.0, 36.0)], dia="4")
    _em(ctx, wb.Name, "BATTERY")
    _cn(ctx, wb.Name, "SWITCH_BRKT")
    wc = _wire(doc, ctx, "WIRE_SW_CTRL", [
        (-60.0, -30.0, 48.0), (-50.0, -45.0, 55.0),
        (-44.0, -52.0, 60.0), (-40.0, -55.0, 64.0),
        (-10.0, -59.0, 62.0), (20.0, -62.0, 55.0),
        (40.0, -63.0, 48.0), (50.0, -62.0, 44.0)], dia="4")
    _em(ctx, wc.Name, "HUB_CTRL")
    _em(ctx, "BOLT_MPL_R_7", "INT_MOTOR")
    _em(ctx, wc.Name, "MAIN_SWITCH")
    _cn(ctx, wc.Name, "SWITCH_BRKT")
    wr = _wire(doc, ctx, "WIRE_HUB_RS485", [
        (-50.0, -40.0, 50.0), (-85.0, -30.0, 72.0),
        (-136.0, 2.0, 92.0), (-130.0, 55.0, 100.0),
        (-110.0, 80.0, 100.0)], dia="3")
    _em(ctx, wr.Name, "HUB_CTRL")
    _em(ctx, wr.Name, "HUB_EXP")
    _em(ctx, wr.Name, "ELEC_SHELF")
    for wtag, wx, wy in (("FL", 127.0, 100.0), ("RL", -127.0, 100.0),
                         ("FR", 127.0, -100.0), ("RR", -127.0, -100.0)):
        ym = 73.0 if wy > 0 else -73.0
        pts = [
            (wx + (-16.0 if wx > 0 else 16.0), wy * 1.10, 48.0),
            (wx * 0.85, wy * 0.95, 45.0)]
        if wx < 0:
            # rear corners detour around the rear column posts
            pts += [(-112.0, wy * 0.62, 44.0),
                    (-96.0, wy * 0.60, 41.0),
                    (-60.0, wy * 0.56, 38.0)]
        else:
            pts += [(wx * 0.80, wy * 0.75, 42.0),
                    (wx * 0.63, wy * 0.56, 40.0)]
        pts += [
            (wx * 0.40, wy * 0.44, 37.0),
            (10.0, wy * 0.50, 36.0),
            (-20.0, wy * 0.40, 36.0),
            (-60.0, wy * 0.38, 40.0),
            (-110.0, wy * 0.37, 42.0),
            (-95.0, wy * 0.38, 45.0)]
        wm = _wire(doc, ctx, "WIRE_MTR_%s" % wtag, pts)
        _em(ctx, wm.Name, "MOTOR_" + wtag)
        _em(ctx, wm.Name, "HUB_CTRL")
        _cn(ctx, wm.Name, "CLAMP_%s_1" % wtag)
        _cn(ctx, wm.Name, "BOLT_CLMP_%s_1_0" % wtag)
        _cn(ctx, wm.Name, "BOLT_CLMP_%s_0_0" % wtag)
    el = _wire(doc, ctx, "WIRE_ENC_LAT_L", [
        (42.0, 107.6, 20.0), (42.0, 107.6, 32.0), (60.0, 105.0, 60.0),
        (122.0, 99.0, 84.0), (130.0, 96.0, 95.0),
        (-85.0, 80.0, 100.0)], dia="1.5")
    _em(ctx, el.Name, "ODO_ENC_LAT_L")
    _em(ctx, el.Name, "HUB_EXP")
    _cn(ctx, el.Name, "ODO_MOUNT_LAT_L")
    _cn(ctx, el.Name, "SCRW_ENC_LAT_L_0")
    er = _wire(doc, ctx, "WIRE_ENC_LAT_R", [
        (42.0, -107.6, 20.0), (42.0, -107.6, 32.0), (60.0, -105.0, 60.0),
        (122.0, -99.0, 84.0), (130.0, -96.0, 95.0),
        (-85.0, -80.0, 95.0), (-125.0, -40.0, 95.0),
        (-125.0, 50.0, 100.0), (-110.0, 75.0, 100.0)], dia="1.5")
    _em(ctx, er.Name, "ODO_ENC_LAT_R")
    _em(ctx, er.Name, "HUB_EXP")
    _cn(ctx, er.Name, "ODO_MOUNT_LAT_R")
    _cn(ctx, er.Name, "SCRW_ENC_LAT_R_0")
    eo = _wire(doc, ctx, "WIRE_ENC_LON", [
        (-150.0, -2.0, 15.0), (-150.5, 14.0, 18.0), (-147.0, 40.0, 30.0),
        (-144.0, 52.0, 42.0), (-141.0, 62.0, 58.0), (-136.0, 70.0, 66.0),
        (-126.0, 78.0, 80.0), (-116.0, 84.0, 92.0),
        (-108.0, 86.0, 98.0)], dia="1.5")
    _em(ctx, eo.Name, "ODO_ENC_LON")
    _em(ctx, eo.Name, "HUB_EXP")
    # A5 loom: wires lie on the pan and bundle together; routed tubes
    # tuck into surfaces and each other -> declared embeds
    _wnames = ["WIRE_BATT_SW", "WIRE_SW_CTRL", "WIRE_HUB_RS485",
               "WIRE_MTR_FL", "WIRE_MTR_FR", "WIRE_MTR_RL",
               "WIRE_MTR_RR", "WIRE_ENC_LAT_L", "WIRE_ENC_LAT_R",
               "WIRE_ENC_LON"]
    for _wi in _wnames:
        _em(ctx, _wi, "BELLY_PAN")
    for _a in range(len(_wnames)):
        for _b in range(_a + 1, len(_wnames)):
            _em(ctx, _wnames[_a], _wnames[_b])
    _cn(ctx, "BATT_STRAP_0", "WIRE_BATT_SW")
    _cn(ctx, "BATT_STRAP_1", "WIRE_BATT_SW")
    for i, (cx, cy) in enumerate(((152.0, 0.0), (-40.0, -80.0),
                                  (-40.0, -95.0), (36.0, -80.0))):
        _clip(doc, ctx, "CLIP_%d" % i,
              {"Placement.Base.x": str(cx - 6),
               "Placement.Base.y": str(cy - 6),
               "Placement.Base.z":
               "(Parameters.pan_z + Parameters.pan_thk / 2)"},
              "BELLY_PAN")


def build_electronics(doc, ctx):
    _battery(doc, ctx)
    _strap(doc, ctx, 0)
    _strap(doc, ctx, 1)
    _shelf(doc, ctx)
    _switch_bracket(doc, ctx)
    _hubs(doc, ctx)
    _wiring(doc, ctx)
    _coplanar_elec(doc, ctx)


# =====================================================================
# envelope marker + populate entry points
# =====================================================================
def _env(doc, ctx):
    env = pk.box(doc, "ENV_START", "ENV_START_457.2cube_VERIFIED",
                 "VERIFIED - FTC 18in start volume (R102)",
                 {"Length": "Parameters.start_cube",
                  "Width": "Parameters.start_cube",
                  "Height": "Parameters.start_cube"},
                 {"Placement.Base.x": "(-Parameters.start_cube / 2)",
                  "Placement.Base.y": "(-Parameters.start_cube / 2)",
                  "Placement.Base.z": "0"})
    ctx["env"] = env.Name


def _sheet(doc):
    from robot_params import populate_sheet
    return populate_sheet(doc)


def populate_drivebase(doc, ctx):
    """Frame + drivetrain + pods + deck content for drivebase.FCStd."""
    ctx["sheet"] = _sheet(doc)
    build_frame(doc, ctx)
    build_drivetrain(doc, ctx)
    build_pods(doc, ctx)
    _env(doc, ctx)


def populate_electronics_frame_ctx(doc, ctx):
    """Frame context needed inside electronics.FCStd: rails + pan +
    brackets (identical builders -> DET3-identical solids)."""
    for sgn in (1, -1):
        _rail(doc, ctx, sgn)
    _belly_pan(doc, ctx)


def populate_electronics(doc, ctx):
    """Electronics tray + wiring for electronics.FCStd."""
    ctx["sheet"] = _sheet(doc)
    populate_electronics_frame_ctx(doc, ctx)
    build_electronics(doc, ctx)
    _env(doc, ctx)


def populate_master(doc, ctx):
    """Full assembly for master_robot.FCStd (sprints 01-03)."""
    ctx["sheet"] = _sheet(doc)
    build_frame(doc, ctx)
    build_drivetrain(doc, ctx)
    build_pods(doc, ctx)
    build_electronics(doc, ctx)
    try:
        import dt_path
        dt_path.build_intake(doc, ctx)
        dt_path.build_hopper(doc, ctx)
    except ImportError:
        pass
    try:
        import dt_turret
        dt_turret.build_turret(doc, ctx)
    except ImportError:
        pass
    try:
        import dt_lift
        dt_lift.build_lift(doc, ctx)
    except ImportError:
        pass
    _env(doc, ctx)


# =====================================================================
# BUILD TAIL -- shared by the three wrapper scripts
# =====================================================================
import json  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = ROOT / "cad"
EXPORTS = ROOT / "exports"
META_DIR = EXPORTS / "meta"

_SUBSYS_GROUPS = (
    ("GRP_ENVELOPE", ("ENV_",)),
    ("GRP_INTAKE", ("ROLLER_LOW", "ROLLER_TOP", "ROLLER_SHAFT",
                    "STAR_SHAFT", "JACK_SHAFT", "INT_", "FLOAT_",
                    "SPRING_POST_", "TORSION_", "PIVOT_", "SPROCKET_",
                    "CHAIN_", "MASTER_LINK", "BELT_", "TENS_",
                    "THROAT_")),
    ("GRP_DRIVEBASE", ("WHEEL_", "ROLLER_", "AXLE_", "BRG_", "MOTOR_",
                       "MOUNT_PLATE_", "PINION_", "CLAMP_", "COLLAR_",
                       "WSH_", "NUT_AXLE_")),
    ("GRP_FRAME", ("FRAME_", "CROWN_POST_", "GUSSET_", "TIE_", "ENDCAP_",
                   "PLATE_NUM_", "BELLY_PAN", "PAN_BRKT_", "DECK_")),
    ("GRP_HOPPER", ("HOP_", "AGIT_", "FEED_", "COL_", "GATE_", "DIV_",
                    "PORT_", "SNSR_", "SPUR_")),
    ("GRP_PODS", ("ODO_",)),
    ("GRP_TURRET", ("TOWER_", "TURRET_DECK", "LAZY_SUSAN_",
                    "YAW_SERVO", "YAW_TRAY", "YAW_PINION",
                    "YAW_SHAFT", "HALL_")),
    ("GRP_TURRET_ROT", ("TURRET_PLATE", "TURRET_TOP_BRACE", "RING_",
                        "LAUNCH_", "FLY_", "FLYWHEEL_", "HOOD",
                        "NIP_", "VSN_", "CAM_MOUNT", "CAM_LED",
                        "YAW_MAGNET", "WIRE_FLY_", "WIRE_HOOD_",
                        "WIRE_CAM_")),
    ("GRP_LIFT", ("LIFT_", "S1_", "S2_", "CRADLE_", "TILT_",
                  "LOAD_CHUTE", "CHUTE_", "WINCH_", "ROPE_",
                  "STOP_COLLAR_", "WIRE_WINCH", "WIRE_TILT",
                  "WIRE_YAW_SV")),
    ("GRP_ELECTRONICS", ("BATTERY", "BATT_STRAP", "ELEC_SHELF",
                         "STANDOFF_", "HUB_", "SWITCH_", "MAIN_SWITCH",
                         "WIRE_", "CLIP_", "ZIP_", "CONN_", "SCRW_")),
    ("GRP_FASTENERS", ("BOLT_", "NUT_", "SCRW_", "RIVNUT_",
                       "WASHER_")),
    ("GRP_TOOLS", ("TOOL_", "VOL_", "AXIS_", "REF_")),
)


def finish_doc(doc, ctx, target, tag):
    """recompute -> validate shapes -> group -> save -> meta json."""
    ctx["doc"] = doc
    # construction tools carry the status token too (PROV honesty)
    for o in doc.Objects:
        if not o.Name.startswith("TOOL_"):
            continue
        if not any(t in o.Label
                   for t in ("UNVERIFIED", "VENDOR-PENDING", "VERIFIED")):
            o.Label = o.Label + "_UNVERIFIED"
        if not getattr(o, "DataStatus", None):
            if "DataStatus" not in o.PropertiesList:
                try:
                    o.addProperty("App::PropertyString", "DataStatus",
                                  "Provenance")
                except Exception:
                    pass
            try:
                o.DataStatus = "UNVERIFIED - construction tool"
            except Exception:
                pass
    doc.recompute(None, True, True)
    bad, nulls = [], []
    for o in doc.Objects:
        if not hasattr(o, "Shape"):
            continue
        try:
            sh = o.Shape
        except Exception:
            continue
        if sh is None or sh.isNull():
            nulls.append(o.Name)
        elif not sh.isValid():
            bad.append(o.Name)
    if bad or nulls:
        raise RuntimeError("invalid=%s nulls=%s" % (bad, nulls))

    groups = {}
    for gname, _pf in _SUBSYS_GROUPS:
        g = doc.addObject("App::Part", gname)
        g.Label = gname
        groups[gname] = g
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o.TypeId == "App::Origin":
            continue
        if o.Name.startswith("GRP_"):
            continue
        if o.getParentGeoFeatureGroup() is not None:
            continue
        for gname, prefixes in _SUBSYS_GROUPS:
            if o.Name.startswith(prefixes):
                pk.group_add(groups[gname], o)
                break
    doc.recompute(None, True, True)

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    doc.saveAs(str(target))
    for bak in target.parent.glob(target.stem + ".*.FCBak"):
        bak.unlink()
    print("SAVED %s: objects=%d solids=%d"
          % (target.name, len(doc.Objects), len(ctx["solids"])))
    emit_meta(ctx, tag)
    return target


def _gshape(o):
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    return s


def reclassify_pairs(ctx):
    """Honest declaration pass: measure each declared pair against the
    geometry and move it to the class it actually belongs to."""
    doc = ctx["doc"]
    by = {o.Name: o for o in doc.Objects}

    def shapes(a, b):
        return _gshape(by[a]), _gshape(by[b])

    embeds, moved_to_contact, dropped = [], [], []
    for a, b in ctx["embeds"]:
        if a not in by or b not in by:
            dropped.append((a, b))
            continue
        sa, sb = shapes(a, b)
        if sa.common(sb).Volume >= 0.5:
            embeds.append((a, b))
        elif sa.distToShape(sb)[0] <= 1.0:
            moved_to_contact.append((a, b))
        else:
            dropped.append((a, b))
    ctx["embeds"] = embeds

    known = {tuple(sorted(p)) for p in ctx["faces"]}
    known |= {tuple(sorted(p)) for p in ctx["journals"]}
    contacts = list(moved_to_contact)
    for a, b in ctx["contacts"]:
        if tuple(sorted((a, b))) in known:
            continue
        if a not in by or b not in by:
            dropped.append((a, b))
            continue
        sa, sb = shapes(a, b)
        if sa.distToShape(sb)[0] <= 1.0:
            contacts.append((a, b))
        else:
            dropped.append((a, b))
    seen = set()
    ctx["contacts"] = [p for p in contacts
                       if not (tuple(sorted(p)) in seen
                               or seen.add(tuple(sorted(p))))]
    ctx["dropped"] = dropped
    print("DECL: %d embed->contact, %d dropped"
          % (len(moved_to_contact), len(dropped)))


def emit_meta(ctx, tag):
    """Write exports/meta/<tag>.json: the declared-pair tables and the
    object census the selfcheck reads back."""
    META_DIR.mkdir(parents=True, exist_ok=True)
    if ctx.get("doc") is not None:
        reclassify_pairs(ctx)
    out = {
        "solids": list(ctx["solids"]),
        "joints": ctx["joints"],
        "faces": ctx["faces"],
        "embeds": ctx["embeds"],
        "journals": ctx["journals"],
        "contacts": ctx["contacts"],
        "ground": ctx["ground"],
        "bom": ctx["bom"],
        "dropped": ctx.get("dropped", []),
    }
    dst = META_DIR / ("%s.json" % tag)
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("META %s" % dst.name)


def _status_of(o):
    st = getattr(o, "DataStatus", "") or ""
    for tok in ("UNVERIFIED", "VENDOR-PENDING", "VERIFIED"):
        if tok in st or tok in o.Label:
            return tok
    return "UNVERIFIED"


def bom_autofill(ctx):
    """Every exportable solid must appear in the BOM. Explicit _bom
    rows come first; untraced objects (mostly fasteners) are grouped
    by class + spec parsed from their labels."""
    traced = set()
    for row in ctx["bom"]:
        traced.update(row["members"])
    doc = ctx.get("doc")
    objs = [o for o in doc.Objects
            if o.Name in set(ctx["solids"])] if doc else []
    auto = {}
    for o in objs:
        if o.Name in traced:
            continue
        p = o.getParentGeoFeatureGroup()
        grp = ""
        while p is not None:
            if p.Name.startswith("GRP_"):
                grp = p.Name
                break
            p = p.getParentGeoFeatureGroup()
        cls = o.Name.split("_")[0]
        stem = __import__("re").sub(r"(_\d+)+$", "", o.Name)
        sub = {"GRP_DRIVEBASE": "drivetrain", "GRP_ELECTRONICS":
               "electronics", "GRP_FRAME": "frame", "GRP_PODS":
               "odometry", "GRP_INTAKE": "intake", "GRP_HOPPER":
               "hopper", "GRP_TURRET": "turret", "GRP_TURRET_ROT":
               "turret", "GRP_LIFT": "lift", "GRP_FASTENERS":
               "fasteners"}.get(grp, cls.lower())
        desc = o.Label.split(" - ")[-1] if " - " in o.Label else cls
        mat = ("steel" if cls in ("BOLT", "NUT", "SCRW", "RIVNUT",
               "WSH", "COLLAR", "PINION", "AXLE") else "aluminum"
               if cls in ("CLAMP", "GUSSET", "BRG", "MOUNT", "ODO")
               else "steel")
        key = (sub, desc, stem, mat, _status_of(o))
        auto.setdefault(key, []).append(o.Name)
    rows = []
    for (sub, desc, stem, mat, st), names in sorted(auto.items()):
        spec = ("%s x%d" % (stem, len(names))
                if len(names) > 1 else stem)
        rows.append({"subsys": sub, "spec": spec, "material": mat,
                     "dims": "-", "status": st, "members": names})
    return rows


def write_exports_tables(ctx):
    """bom.csv + parameters.csv + mount_graph.json (master scope)."""
    (EXPORTS / "bom").mkdir(parents=True, exist_ok=True)
    agg = {}
    for row in list(ctx["bom"]) + bom_autofill(ctx):
        key = (row["subsys"], row["spec"], row["material"],
               row["dims"], row["status"])
        if key not in agg:
            agg[key] = {"qty": 0, "parts": []}
        agg[key]["qty"] += len(row["members"])
        agg[key]["parts"] += row["members"]
    lines = ["subsystem,description,material,spec,status,qty,objects"]
    for (sub, desc, mat, spec, st), v in sorted(agg.items()):
        lines.append('%s,"%s",%s,%s,%s,%d,"%s"'
                     % (sub, desc, mat, spec, st, v["qty"],
                        " ".join(v["parts"])))
    (EXPORTS / "bom" / "bom.csv").write_text("\n".join(lines) + "\n",
                                           encoding="utf-8")

    from robot_params import PARAMS, DERIVED
    lines = ["alias,value,unit,status,source"]
    for alias, val, unit, status, note in PARAMS:
        lines.append('%s,%s,%s,%s,"%s"'
                     % (alias, val, unit, status, note.replace('"', "'")))
    sheet = ctx.get("doc") and ctx["doc"].getObject("Parameters")
    for alias, expr, status, note in DERIVED:
        try:
            val = ("%.4f" % float(sheet.get(alias))) if sheet else expr
        except Exception:
            val = expr
        lines.append('%s,%s,mm,%s,"%s"'
                     % (alias, val, status, note.replace('"', "'")))
    (EXPORTS / "bom" / "parameters.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    edges = []
    for a, b in ctx["embeds"]:
        edges.append({"a": a, "b": b, "type": "embed"})
    for a, b in ctx["faces"]:
        edges.append({"a": a, "b": b, "type": "face"})
    for a, b in ctx["journals"]:
        edges.append({"a": a, "b": b, "type": "journal"})
    for a, b in ctx["contacts"]:
        edges.append({"a": a, "b": b, "type": "contact"})
    for j in ctx["joints"]:
        ms = j["members"]
        hw = list(j.get("bolts", [])) + list(j.get("nuts", []))
        for i in range(len(ms)):
            for k in range(i + 1, len(ms)):
                edges.append({"a": ms[i], "b": ms[k], "type": "fastener",
                              "joint": j["id"]})
        for h in hw:
            for mem in ms:
                edges.append({"a": h, "b": mem, "type": "fastener",
                              "joint": j["id"]})
    for cn, axl in ctx.get("carriers", []):
        edges.append({"a": cn, "b": axl, "type": "carrier"})
        for bt in j["bolts"] + j["nuts"]:
            for m in ms:
                edges.append({"a": bt, "b": m, "type": "fastener",
                              "joint": j["id"]})
    graph = {
        "roots": ctx["ground"],
        "nodes": ctx["solids"],
        "edges": edges,
    }
    (EXPORTS / "mount_graph.json").write_text(
        json.dumps(graph, indent=1), encoding="utf-8")
    print("EXPORTS bom.csv parameters.csv mount_graph.json")

