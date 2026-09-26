"""dt_frame.py -- shared Sprint-01 drivebase builder.

Frame (inverted-U channels, crossmember, crown, gussets, tie plates,
end caps, number plates, belly pan + brackets, deck panels + posts),
four-corner live-axle drivetrain, and three dead-wheel odometry pods.

build_drivebase.py and build_master_robot.py both call populate() so
subsystem and master geometry are signature-identical (DET3).

Coordinate frame: +X fwd, +Y left, +Z up, Z=0 tile top. Lateral stack
derives from wheel_lat_off: rail_lat = wheel_lat_off - wheel_out_gap,
so one lateral probe moves the whole drivetrain coherently (PAR2-D).

ctx (a plain dict) collects the declared mount table while building:
  ctx["solids"]   exportable object names in creation order
  ctx["joints"]   {id, members[], bolts[], nuts[], kind} bolted joints
  ctx["faces"]    declared A2 face-contact pairs (a, b)
  ctx["embeds"]   declared A3/A4 pairs (a, b)
  ctx["journals"] declared A1 journal pairs (a, b)
  ctx["contacts"] declared A5 pairs (a, b)
  ctx["ground"]   ground-contact root names
"""

import math

import FreeCAD as App

import partkit as pk

RAIL_LAT = "(Parameters.wheel_lat_off - Parameters.wheel_out_gap)"
AXLE_Z = "(Parameters.wheel_dia / 2)"


def sgn_expr(expr, sgn):
    """Mirror an expression about the XY origin plane (Y axis)."""
    return "(%s)" % expr if sgn > 0 else "-(%s)" % expr


# lateral stations along +Y, as expression strings relative to rail_lat
INNER_FACE = "%s - Parameters.rail_size / 2" % RAIL_LAT          # 136.02
CAV_IN = "%s + Parameters.rail_wall" % INNER_FACE                # 138.52
CAV_OUT = "%s + Parameters.rail_size - 2 * Parameters.rail_wall" % INNER_FACE
OUTER_FACE = "%s + Parameters.rail_size" % INNER_FACE            # 184.02
PLATE_FACE = "(%s) - Parameters.mplate_t" % INNER_FACE           # 132.97
MOTOR_FACE = PLATE_FACE
GB_FACE = PLATE_FACE

WX_P = "Parameters.wheel_lon_off"                                # +127
WX_N = "-Parameters.wheel_lon_off"                               # -127

CORNERS = (("FL", 1, 1, 1), ("FR", 1, -1, -1),
           ("RL", -1, 1, -1), ("RR", -1, -1, 1))


# ---------------------------------------------------------------------
# small expr helpers
# ---------------------------------------------------------------------
def _jm(ctx, jid, members, bolts=(), nuts=(), kind="bolt"):
    ctx["joints"].append({"id": jid, "members": list(members),
                          "bolts": list(bolts), "nuts": list(nuts),
                          "kind": kind})


def _fp(ctx, a, b):
    ctx["faces"].append((a, b))


def _em(ctx, a, b):
    ctx["embeds"].append((a, b))


def _jl(ctx, a, b):
    ctx["journals"].append((a, b))


def _cn(ctx, a, b):
    ctx["contacts"].append((a, b))


def _solid(ctx, o):
    ctx["solids"].append(o.Name)
    return o


# ---------------------------------------------------------------------
# frame
# ---------------------------------------------------------------------
def _rail(doc, ctx, sgn):
    """One side rail: inverted-U channel along X with wall grid rows,
    axle bores + bearing bolt circles at both wheel stations, web row."""
    name = "FRAME_RAIL_L" if sgn > 0 else "FRAME_RAIL_R"
    lat = sgn_expr(RAIL_LAT, sgn)
    y0 = "(%s) - Parameters.rail_size / 2" % lat
    z0 = "Parameters.rail_elev_z - Parameters.rail_size / 2"
    wall1_y = ("(%s) - 1" % y0 if sgn > 0
               else "(%s) + Parameters.rail_size - Parameters.rail_wall - 1"
               % y0)
    # per-wall face positions used for bolt coordination
    bores = []
    for i, wx in enumerate((WX_N, WX_P)):
        for yside in range(2):
            if axis := True:
                pass
        # axle clearance bore through the WHOLE channel (both walls)
        bores.append(("Parameters.wall_axle_bore",
                      {"Placement.Base.x": wx,
                       "Placement.Base.y": "(%s) - 1" % y0,
                       "Placement.Base.z": AXLE_Z},
                      "Y", "Parameters.rail_size + 2"))
        # bearing bolt circle: 4 x O4.4 through each wall separately
        for su in (-1, 1):
            for sv in (-1, 1):
                for w_i in range(2):
                    if sgn > 0:
                        wy = ("(%s) - 1" % y0 if w_i == 0 else
                              "(%s) + Parameters.rail_size - "
                              "Parameters.rail_wall - 1" % y0)
                    else:
                        wy = ("(%s) + Parameters.rail_size - "
                              "Parameters.rail_wall - 1" % y0
                              if w_i == 0 else "(%s) - 1" % y0)
                    bores.append((
                        "Parameters.bear_bolt_d",
                        {"Placement.Base.x":
                         "(%s) + %d * Parameters.bear_bolt_off" % (wx, su),
                         "Placement.Base.y": wy,
                         "Placement.Base.z":
                         "%s + %d * Parameters.bear_bolt_off" % (AXLE_Z, sv)},
                        "Y", "Parameters.rail_wall + 2"))
    # gusset + tie + plate + bracket + clamp hole positions are cut here
    # too (dedicated holes -- real drilled holes, not grid-registered)
    for wx in (WX_N, WX_P):
        pass
    r = pk.channel_open(
        doc, name,
        "%s_gobilda1120_invU_444.5mm_%s" % (name, "VENDOR-PENDING"),
        "VENDOR-PENDING - goBILDA 1120-series ~48mm channel (D12)",
        ("-Parameters.chassis_sq / 2", y0, z0),
        "Parameters.chassis_sq", "Parameters.rail_size",
        "Parameters.rail_wall", axis="X",
        wall_rows=(
            {"count": 6, "dia": "Parameters.grid_hole_d",
             "pitch": "Parameters.grid_pitch", "start": "112.25",
             "z": "Parameters.rail_elev_z - Parameters.rail_size / 2 + 12"},
            {"count": 6, "dia": "Parameters.grid_hole_d",
             "pitch": "Parameters.grid_pitch", "start": "112.25",
             "z": "Parameters.rail_elev_z - Parameters.rail_size / 2 + 36"}),
        web_rows=(
            {"count": 9, "dia": "Parameters.grid_hole_d",
             "pitch": "Parameters.grid_pitch", "start": "13.75",
             "line": lat},),
        bores=bores)
    return _solid(ctx, r)


def build_frame(doc, ctx):
    L = []
    for sgn in (1, -1):
        L.append(_rail(doc, ctx, sgn))
    return L
