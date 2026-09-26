"""partkit.py -- shared component-fidelity part-kit (BIOBUZZ rehaul).

One modeling vocabulary for every build script: real FreeCAD document
objects wired as parametric feature DAGs (Part::Box/Cylinder ->
Part::Cut/Fuse -> Part::Fillet/Chamfer). Every dimensional property and
placement is expression-bound to the document's `Parameters` sheet.

Conventions:
- Intermediate solids (blanks, cutters, bore tools, pre-soften
  features) carry the reserved prefix ``TOOL_``: excluded from
  renders/exports/leaf scans but still stamped with DataStatus.
- Fillet/chamfer edge sets are chosen by GEOMETRIC PREDICATE on the
  base shape (direction/length/radius), never caller-supplied index
  literals -- literal indices go stale under parametric resize.
  Part::Fillet/Chamfer keep radii inside the Edges tuples (no bindable
  Radius property), so radii are baked from alias values at build
  time; a rebuild re-runs the predicate and stays correct.
- Slanted parts (mecanum rollers): a carrier App::Part owns the bound
  slant angle (Placement.Rotation.Angle <- Parameters.mec_roll_slant)
  and the child solid carries the fixed axis-orientation rotation.
- Objects consumed by a feature DAG must NOT join a carrier group:
  their Shape is read in their own placement; only the final feature
  joins the carrier (which applies the carrier transform once).
"""
import math

import FreeCAD as App
import Part  # noqa: F401  registers Part::* types

TOOL_PREFIX = "TOOL_"
_ROT = {"Y": (-90, (1, 0, 0)), "X": (90, (0, 1, 0)), "Z": (0, (0, 0, 1))}
_AXIS_COMP = {"X": "x", "Y": "y", "Z": "z"}


def axis_rot(axis):
    """Rotation taking a cylinder's +Z axis onto the named world axis."""
    deg, vec = _ROT[axis]
    return App.Rotation(App.Vector(*vec), deg) if deg else App.Rotation()


# --------------------------------------------------------------------
# stamping + binding
# --------------------------------------------------------------------
def stamp(o, label, status, vendor=None):
    o.Label = label
    if "DataStatus" not in o.PropertiesList:
        o.addProperty("App::PropertyString", "DataStatus", "Status",
                      "verification state of this solid")
    o.DataStatus = status
    if vendor:
        o.addProperty("App::PropertyString", "VendorRef", "Vendor",
                      "vendor reference, pending verification")
        o.VendorRef = vendor
    return o


def bind(o, mapping):
    for prop, expr in mapping.items():
        if expr is not None and expr != "":
            o.setExpression(prop, expr)
    return o


def group_add(part, *objs):
    part.Group = list(part.Group) + [o for o in objs if o not in part.Group]


def pval(sheet, alias):
    """Numeric value of a Parameters alias (for baked edge radii)."""
    return float(sheet.get(alias))


# --------------------------------------------------------------------
# primitives (exportable) and tools (TOOL_ intermediates)
# --------------------------------------------------------------------
def _bind_zeros(o, pos):
    """Any Placement.Base component the caller did not bind is bound to
    the literal "0" -- an explicit bound constant, not a free input."""
    for comp in ("x", "y", "z"):
        if "Placement.Base." + comp not in (pos or {}):
            o.setExpression("Placement.Base." + comp, "0")


def box(doc, name, label, status, dims=None, pos=None, rot=None,
        vendor=None):
    o = doc.addObject("Part::Box", name)
    stamp(o, label, status, vendor)
    bind(o, dims or {})
    bind(o, pos or {})
    _bind_zeros(o, pos)
    if rot is not None:
        o.Placement.Rotation = rot
    return o


def cyl(doc, name, label, status, dims=None, pos=None, rot=None,
        vendor=None):
    o = doc.addObject("Part::Cylinder", name)
    stamp(o, label, status, vendor)
    bind(o, dims or {})
    bind(o, pos or {})
    if rot is not None:
        o.Placement.Rotation = rot
    _bind_zeros(o, pos)
    return o


def _tool_name(name):
    return name if name.startswith(TOOL_PREFIX) else TOOL_PREFIX + name


def tool_box(doc, name, dims, pos=None, rot=None):
    return box(doc, _tool_name(name),
               "%s_construction_tool" % _tool_name(name),
               "UNVERIFIED - part-kit construction tool", dims, pos, rot)


def tool_cyl(doc, name, dims, pos=None, rot=None):
    return cyl(doc, _tool_name(name),
               "%s_construction_tool" % _tool_name(name),
               "UNVERIFIED - part-kit construction tool", dims, pos, rot)


def tool_compound(doc, name, links):
    o = doc.addObject("Part::Compound", _tool_name(name))
    stamp(o, "%s_tool_compound" % _tool_name(name),
          "UNVERIFIED - part-kit tool compound")
    o.Links = links
    return o


# --------------------------------------------------------------------
# feature DAG nodes
# --------------------------------------------------------------------
def _as_tool(doc, name, tools):
    if isinstance(tools, (list, tuple)):
        return tool_compound(doc, name + "_TOOLS", list(tools))
    return tools


def cut(doc, name, label, status, base, tools):
    o = doc.addObject("Part::Cut", name)
    stamp(o, label, status)
    o.Base = base
    o.Tool = _as_tool(doc, name, tools)
    return o


def fuse(doc, name, label, status, base, tools):
    o = doc.addObject("Part::Fuse", name)
    stamp(o, label, status)
    o.Base = base
    o.Tool = _as_tool(doc, name, tools)
    return o


def common(doc, name, label, status, base, tools):
    o = doc.addObject("Part::Common", name)
    stamp(o, label, status)
    o.Base = base
    o.Tool = _as_tool(doc, name, tools)
    return o


# --------------------------------------------------------------------
# edge predicates + fillet/chamfer
# --------------------------------------------------------------------
def pred_axis(axis, min_len=0.0):
    """Straight edges parallel to `axis` (unit tuple) and >= min_len."""
    ax = App.Vector(*axis).normalize()

    def p(e):
        try:
            d = e.Curve.Direction
        except Exception:
            return False
        return d is not None and abs(d * ax) > 0.99 and e.Length >= min_len
    return p


def pred_circle(min_r=0.0):
    """Full-circle edges (rim candidates) with radius >= min_r."""
    def p(e):
        try:
            r = e.Curve.Radius
        except Exception:
            return False
        return (r >= min_r
                and abs(e.Length - 2 * math.pi * r) < 0.5)
    return p


def _select_edges(shape, pred):
    sel = []
    for i, e in enumerate(shape.Edges):
        try:
            if pred(e):
                sel.append(i + 1)
        except Exception:
            continue
    return sel


def fillet(doc, name, label, status, base, radius, pred):
    """Part::Fillet on base edges chosen by predicate (1-based indices
    resolved here at build time -- never caller literals)."""
    o = doc.addObject("Part::Fillet", name)
    stamp(o, label, status)
    o.Base = base
    doc.recompute()
    idx = _select_edges(base.Shape, pred)
    if not idx:
        raise RuntimeError("fillet %s: predicate matched no edges" % name)
    o.Edges = [(i, radius, radius) for i in idx]
    return o


def chamfer(doc, name, label, status, base, length, pred):
    o = doc.addObject("Part::Chamfer", name)
    stamp(o, label, status)
    o.Base = base
    doc.recompute()
    idx = _select_edges(base.Shape, pred)
    if not idx:
        raise RuntimeError("chamfer %s: predicate matched no edges" % name)
    o.Edges = [(i, length, length) for i in idx]
    return o


# --------------------------------------------------------------------
# components
# --------------------------------------------------------------------
def plate(doc, name, label, status, dims, pos, rot=None,
          fillet_r=None, chamfer_l=None, edge_pred=None):
    """Plate: TOOL_ blank -> optional fillet/chamfer = final `name`.

    Returns the final feature. dims/pos are expression maps; radii are
    numbers (baked into the edge tuples per module docstring).
    """
    if not fillet_r and not chamfer_l:
        # no softening: the blank IS the part, under the public name
        return box(doc, name, label, status, dims, pos, rot)
    blk = tool_box(doc, name + "_BLK", dims, pos, rot)
    if fillet_r:
        return fillet(doc, name, label, status, blk, fillet_r,
                      edge_pred or pred_axis((0, 0, 1)))
    return chamfer(doc, name, label, status, blk, chamfer_l,
                   edge_pred or pred_axis((0, 0, 1)))


def channel_u(doc, name, label, status, pos0, L, S, W, open_face,
              axis="X", flange_holes=None, web_holes=None, notches=None):
    """U-channel extrusion along `axis`, square section S x S, wall W.

    pos0: (c0, c1, c2) expr strings for the OUTER box min corner
    (axis order X -> (x,y,z), Y -> (x,y,z); the rail runs along `axis`).
    open_face: for axis=X: '+Y' (web at y0) or '-Y' (web at y0+S-W);
        for axis=Y: '+X' (web at x0) or '-X' (web at x0+S-W).
    flange_holes: dict(count, dia, pitch, start, line) -> through-cuts
        in the TOP flange, `line` = expr for the flange-center coord.
    web_holes: dict(count, dia, pitch, start, z) -> through-cuts in the
        web wall.
    notches: list of center-exprs along the rail axis -> top-edge
        clearance slots through the whole section.
    """
    if axis == "X":
        dims = {"Length": L, "Width": S, "Height": S}
        pos = {"Placement.Base.x": pos0[0], "Placement.Base.y": pos0[1],
               "Placement.Base.z": pos0[2]}
    else:
        dims = {"Length": S, "Width": L, "Height": S}
        pos = {"Placement.Base.x": pos0[0], "Placement.Base.y": pos0[1],
               "Placement.Base.z": pos0[2]}
    outer = tool_box(doc, name + "_OUT", dims, pos)
    tools = []
    # interior void: leaves web + two flanges, opens on open_face
    # (void spans the open face; web remains on the opposite side)
    if axis == "X":
        inw = ("(%s) + %s" % (pos0[1], W) if open_face == "+Y"
               else pos0[1])
        inner = tool_box(
            doc, name + "_INNER",
            {"Length": L, "Width": "(%s) - %s" % (S, W),
             "Height": "(%s) - 2 * %s" % (S, W)},
            {"Placement.Base.x": pos0[0], "Placement.Base.y": inw,
             "Placement.Base.z": "(%s) + %s" % (pos0[2], W)})
    else:
        inw = ("(%s) + %s" % (pos0[0], W) if open_face == "+X"
               else pos0[0])
        inner = tool_box(
            doc, name + "_INNER",
            {"Length": "(%s) - %s" % (S, W), "Width": L,
             "Height": "(%s) - 2 * %s" % (S, W)},
            {"Placement.Base.x": inw, "Placement.Base.y": pos0[1],
             "Placement.Base.z": "(%s) + %s" % (pos0[2], W)})
    tools.append(inner)
    # top-flange hole row (vertical Ø cuts through the top wall)
    if flange_holes:
        for i in range(flange_holes["count"]):
            c = "(%s) + %s + %d * %s" % (
                pos0[0] if axis == "X" else pos0[1],
                flange_holes["start"], i, flange_holes["pitch"])
            hp = {"Placement.Base.z":
                  "(%s) + %s - %s - 1" % (pos0[2], S, W)}
            if axis == "X":
                hp["Placement.Base.x"] = c
                hp["Placement.Base.y"] = flange_holes["line"]
            else:
                hp["Placement.Base.x"] = flange_holes["line"]
                hp["Placement.Base.y"] = c
            tools.append(tool_cyl(
                doc, "%s_FH%02d" % (name, i),
                {"Radius": "%s / 2" % flange_holes["dia"],
                 "Height": "%s + 2" % W}, hp))
    # web hole row (through the closed wall)
    if web_holes:
        for i in range(web_holes["count"]):
            c = "(%s) + %s + %d * %s" % (
                pos0[0] if axis == "X" else pos0[1],
                web_holes["start"], i, web_holes["pitch"])
            if axis == "X":
                wy = (pos0[1] if open_face == "+Y"
                      else "(%s) + %s - %s" % (pos0[1], S, W))
                wp = {"Placement.Base.x": c,
                      "Placement.Base.y": "(%s) - 1" % wy,
                      "Placement.Base.z": web_holes["z"]}
            else:
                wx = (pos0[0] if open_face == "+X"
                      else "(%s) + %s - %s" % (pos0[0], S, W))
                wp = {"Placement.Base.x": "(%s) - 1" % wx,
                      "Placement.Base.y": c,
                      "Placement.Base.z": web_holes["z"]}
            tools.append(tool_cyl(
                doc, "%s_WH%02d" % (name, i),
                {"Radius": "%s / 2" % web_holes["dia"],
                 "Height": "%s + 2" % W}, wp,
                axis_rot("Y") if axis == "X" else axis_rot("X")))
    # top-edge notches across the whole section (shaft clearance)
    for j, nx in enumerate(notches or []):
        np_ = {"Placement.Base.z":
               "(%s) + %s - Parameters.notch_d + 0.01" % (pos0[2], S)}
        if axis == "X":
            np_["Placement.Base.x"] = ("(%s) - Parameters.notch_w / 2"
                                       % nx)
            np_["Placement.Base.y"] = pos0[1]
            nd = {"Length": "Parameters.notch_w", "Width": S,
                  "Height": "Parameters.notch_d"}
        else:
            np_["Placement.Base.x"] = pos0[0]
            np_["Placement.Base.y"] = ("(%s) - Parameters.notch_w / 2"
                                       % nx)
            nd = {"Length": S, "Width": "Parameters.notch_w",
                  "Height": "Parameters.notch_d"}
        tools.append(tool_box(doc, "%s_NOTCH%d" % (name, j), nd, np_))
    return cut(doc, name, label, status, outer, tools)


def shaft(doc, name, label, status, dia, length, pos, axis="Y"):
    return cyl(doc, name, label, status,
               {"Radius": "%s / 2" % dia, "Height": length}, pos,
               axis_rot(axis))


def bore_cyl(doc, name, label, status, od, wd, bore, pos, axis="Y",
             chamfer_l=None, chamfer_min_r=20.0):
    """Cylinder with coaxial through-bore; optional rim chamfer.
    pos = expr map of the blank's min corner (`axis` comp = bore dir).
    """
    outer = tool_cyl(doc, name + "_BLK",
                     {"Radius": "%s / 2" % od, "Height": wd}, pos,
                     axis_rot(axis))
    comp = _AXIS_COMP[axis]
    tpos = dict(pos)
    tpos["Placement.Base." + comp] = "(%s) - 1" % (
        pos["Placement.Base." + comp])
    t = tool_cyl(doc, name + "_BORE",
                 {"Radius": "%s / 2" % bore, "Height": "(%s) + 2" % wd},
                 tpos, axis_rot(axis))
    if not chamfer_l:
        return cut(doc, name, label, status, outer, t)
    bored = cut(doc, _tool_name(name + "_BRD"), label + "_bored", status,
                outer, t)
    return chamfer(doc, name, label, status, bored, chamfer_l,
                   pred_circle(chamfer_min_r))


def _bore_tool(doc, name, t, w, h, bore_d, pos, axis="Y"):
    comp = _AXIS_COMP[axis]
    dims = {"x": w, "y": t, "z": h}
    p = {}
    for a in ("x", "y", "z"):
        if a == comp:
            p["Placement.Base." + a] = "(%s) - 1" % pos["Placement.Base." + a]
        else:
            p["Placement.Base." + a] = "(%s) + %s / 2" % (
                pos["Placement.Base." + a], dims[a])
    return tool_cyl(doc, name + "_BORE",
                    {"Radius": "%s / 2" % bore_d,
                     "Height": "(%s) + 2" % t}, p, axis_rot(axis))


def _bolt_tools(doc, name, t, w, h, bolt_d, bolt_off, pos, axis="Y"):
    tools = []
    comp = _AXIS_COMP[axis]
    u, v = {"Y": ("x", "z"), "X": ("y", "z"), "Z": ("x", "y")}[axis]
    dims = {"x": w, "y": t, "z": h}
    n = 0
    for su in (-1, 1):
        for sv in (-1, 1):
            p = {}
            for a in ("x", "y", "z"):
                if a == comp:
                    p["Placement.Base." + a] = "(%s) - 1" % (
                        pos["Placement.Base." + a])
                elif a == u:
                    p["Placement.Base." + a] = (
                        "(%s) + %s / 2 + %d * %s"
                        % (pos["Placement.Base." + a], dims[u], su,
                           bolt_off))
                else:
                    p["Placement.Base." + a] = (
                        "(%s) + %s / 2 + %d * %s"
                        % (pos["Placement.Base." + a], dims[v], sv,
                           bolt_off))
            tools.append(tool_cyl(
                doc, "%s_B%02d" % (name, n),
                {"Radius": "%s / 2" % bolt_d, "Height": "(%s) + 2" % t},
                p, axis_rot(axis)))
            n += 1
    return tools


def bearing_block(doc, name, label, status, w, t, h, bore_d, pos,
                  axis="Y", bolt_d=None, bolt_off=None, fillet_r=None):
    """Flange bearing/mount block: plate + center bore + optional bolt
    holes and edge fillet. Face normal = `axis`."""
    blk = tool_box(doc, name + "_BLK",
                   {"Length": w, "Width": t, "Height": h}, pos)
    last = blk
    if fillet_r:
        ax = {"Y": (0, 1, 0), "X": (1, 0, 0), "Z": (0, 0, 1)}[axis]
        last = fillet(doc, _tool_name(name + "_FIL"),
                      label + "_pre_bore", status,
                      blk, fillet_r, pred_axis(ax))
    tools = [_bore_tool(doc, name, t, w, h, bore_d, pos, axis)]
    if bolt_d and bolt_off:
        tools += _bolt_tools(doc, name, t, w, h, bolt_d, bolt_off, pos,
                             axis)
    return cut(doc, name, label, status, last, tools)


def face_plate(doc, name, label, status, w, t, h, bore_d, pos,
               axis="Y", bolt_d=None, bolt_off=None, fillet_r=None):
    """Mount/face plate: filleted plate + center bore + bolt holes."""
    return bearing_block(doc, name, label, status, w, t, h, bore_d, pos,
                         axis, bolt_d, bolt_off, fillet_r)


def pred_not_axis(axis, max_dot=0.5):
    """Edge predicate: selects edges whose direction is NOT parallel to
    `axis` (abs(dot) < max_dot). Complement of pred_axis -- used to catch
    a plate's long perimeter rim while skipping its through-thickness
    corner edges."""
    def _p(e):
        try:
            d = e.tangentAt(e.FirstParameter) if hasattr(
                e, "tangentAt") else e.Curve.Direction
        except Exception:
            return False
        n = math.sqrt(d.x ** 2 + d.y ** 2 + d.z ** 2)
        if n < 1e-9:
            return False
        return (abs(d.x * axis[0] + d.y * axis[1] + d.z * axis[2]) / n
                < max_dot)
    return _p


def bored_plate(doc, name, label, status, dims, pos, rot=None,
                bores=(), chamfer_l=None, chamfer_pred=None):
    """Arbitrary plate: box -> bore cuts -> optional chamfer.

    bores: iterable of (dia_expr, pos_dict, axis, height_expr); each
    becomes a through-cut cylinder tool named TOOL_<name>_BORE<k>. The
    mid-DAG cut gets a TOOL_ name when a chamfer follows; otherwise the
    cut (or the plain box) carries the final name.
    """
    if not bores and chamfer_l is None:
        return box(doc, name, label, status, dims, pos, rot)
    blk = tool_box(doc, name + "_BLK", dims, pos, rot)
    if not bores:
        return chamfer(doc, name, label, status, blk, chamfer_l,
                       chamfer_pred or pred_axis((0, 0, 1)))
    tools = [
        tool_cyl(doc, "%s_BORE%02d" % (name, i),
                 {"Radius": "(%s) / 2" % dia, "Height": h},
                 bp, axis_rot(ax))
        for i, (dia, bp, ax, h) in enumerate(bores)]
    if chamfer_l is None:
        return cut(doc, name, label, status, blk, tools)
    mid = cut(doc, _tool_name(name + "_CUT"), label, status, blk, tools)
    return chamfer(doc, name, label, status, mid, chamfer_l,
                   chamfer_pred or pred_axis((0, 0, 1)))


def l_bracket(doc, name, label, status, leg_dims, leg_pos, foot_dims,
              foot_pos, bolts=None):
    """L-bracket: riser plate + foot plate fused (real L profile).

    legs are ordinary (dims, pos) expression dicts; `bolts` = optional
    iterable of (dia_expr, pos_dict, axis, height_expr) bore specs cut
    through BOTH legs' union result.
    """
    leg = tool_box(doc, name + "_LEG", leg_dims, leg_pos)
    foot = tool_box(doc, name + "_FOOT", foot_dims, foot_pos)
    if not bolts:
        return fuse(doc, name, label, status, leg, foot)
    lsh = fuse(doc, _tool_name(name + "_L"), label, status, leg, foot)
    tools = [
        tool_cyl(doc, "%s_B%02d" % (name, i),
                 {"Radius": "(%s) / 2" % dia, "Height": h},
                 bp, axis_rot(ax))
        for i, (dia, bp, ax, h) in enumerate(bolts)]
    return cut(doc, name, label, status, lsh, tools)


def ribbed_roller(doc, name, label, status, od, length, bore, pos,
                  center, ribs=None):
    """Intake roller on a Y-axis: bored tube + radial grip ribs fused.

    pos: placement dict for the tube (axis=Y, base = one end cap).
    center: {"x","z"} exprs for the roller axis world position -- the
    ribs' rotated bases are composed against it.
    ribs = dict(count, w, h, inset) -> `count` boxes around the axis at
    od/2 (0.5 mm embed), axial span `length - 2*inset`. Rib rotations are
    construction constants (derived pitch), same convention as the
    mecanum carrier frame axes.
    """
    tube_name = _tool_name(name + "_TUBE") if ribs else name
    tube = bore_cyl(doc, tube_name, label, status, od, length, bore,
                    pos, "Y")
    if not ribs:
        return tube
    n = int(ribs["count"])
    rk = []
    for k in range(n):
        ang = k * 360.0 / n
        # rib local frame: X tangential (rib_w), Y axial (rib span),
        # Z radial (rib_h) with base z = od/2 - 0.5 (embed into tube);
        # R_y(ang) maps local (x,z) -> (x cos + z sin, -x sin + z cos)
        rx = ("(%s) - (%s) / 2 * cos(%f deg)"
              " + ((%s) / 2 - 0.5) * sin(%f deg)"
              % (center["x"], ribs["w"], ang, od, ang))
        ry = "(%s) + %s" % (pos["Placement.Base.y"], ribs["inset"])
        rz = ("(%s) + (%s) / 2 * sin(%f deg)"
              " + ((%s) / 2 - 0.5) * cos(%f deg)"
              % (center["z"], ribs["w"], ang, od, ang))
        r = tool_box(doc, "%s_RIB%02d" % (name, k),
                     {"Length": ribs["w"],
                      "Width": "(%s) - 2 * %s" % (length, ribs["inset"]),
                      "Height": ribs["h"]},
                     {"Placement.Base.x": rx, "Placement.Base.y": ry,
                      "Placement.Base.z": rz})
        r.Placement.Rotation = App.Rotation(App.Vector(0, 1, 0), ang)
        rk.append(r)
    return fuse(doc, name, label, status, tube, rk)


def roller_subassy(doc, wtag, idx, pitch_deg, sgn, status, vendor=None):
    """One mecanum roller: carrier App::Part + fused body+pin child.

    Carrier: position = roller center in WHEEL-LOCAL coords (the
    WHEEL_ASSY carrier positions it); rotation axis = radial direction
    at pitch idx*pitch (baked -- encodes construction pitch), .Angle
    bound to +/-Parameters.mec_roll_slant (live slant).
    Child ROLLER_<w>_<i>_B = Fuse(body cyl + concentric pin cyl) in
    frame-local coords; pin ends seat into the wheel face plates.
    """
    name = "ROLLER_%s_%02d" % (wtag, idx)
    th = math.radians(idx * pitch_deg)
    frm = doc.addObject("App::Part", name)
    stamp(frm, name + "_slant_frame", status)
    frm.Placement.Rotation = App.Rotation(
        App.Vector(math.cos(th), 0.0, math.sin(th)), 0.0)
    frm.setExpression("Placement.Rotation.Angle",
                      "%sParameters.mec_roll_slant"
                      % ("" if sgn > 0 else "-"))
    bind(frm, {
        "Placement.Base.x":
            "Parameters.mec_roll_rad * cos(%d * Parameters.mec_roll_pitch)"
            % idx,
        "Placement.Base.z":
            "Parameters.mec_roll_rad * sin(%d * Parameters.mec_roll_pitch)"
            % idx,
        "Placement.Base.y": "0"})
    body = tool_cyl(doc, name + "_BT",
                    {"Radius": "Parameters.mec_roll_dia / 2",
                     "Height": "Parameters.mec_roll_len"},
                    {"Placement.Base.y": "-Parameters.mec_roll_len / 2"},
                    axis_rot("Y"))
    pin = tool_cyl(doc, name + "_PT",
                   {"Radius": "Parameters.mec_pin_dia / 2",
                    "Height": "Parameters.mec_pin_len"},
                   {"Placement.Base.y": "-Parameters.mec_pin_len / 2"},
                   axis_rot("Y"))
    fused = fuse(doc, name + "_B",
                 "%s_B_O14_roller_axle_pin_VENDOR-PENDING" % name,
                 status, body, pin)
    if vendor:
        fused.addProperty("App::PropertyString", "VendorRef", "Vendor",
                          "vendor reference, pending verification")
        fused.VendorRef = vendor
    frm.Group = [fused]
    return frm, fused


def mecanum_wheel(doc, wtag, sgn, status, vendor, pitch_deg,
                  roller_count=10):
    """Mecanum wheel assembly inside a WHEEL_ASSY_<wtag> carrier.

    Caller binds the carrier placement to the wheel center (axis = local
    +Y; -Y faces the chassis). Children are wheel-local: hub (bored),
    2 face plates (bored, rim-chamfered), `roller_count` roller
    subassemblies at the X-pattern slant sign `sgn` (local convention:
    +1 = front-diagonal slant; carrier rotation handles mirroring).
    Returns (carrier, exportable-solids list).
    """
    carrier = doc.addObject("App::Part", "WHEEL_ASSY_" + wtag)
    stamp(carrier, "WHEEL_ASSY_%s_mecanum_carrier" % wtag, status)
    solids = []
    hub = bore_cyl(doc, "WHEEL_HUB_" + wtag,
                   "WHEEL_HUB_%s_O26_hub_REXbore_VENDOR-PENDING" % wtag,
                   status, "Parameters.hub_dia", "Parameters.hub_w",
                   "Parameters.bore_dia",
                   {"Placement.Base.y": "-Parameters.hub_w / 2"},
                   "Y")
    solids.append(hub)
    for tag, yexpr in (
            ("IN", "-Parameters.wheel_width / 2 + Parameters.wplate_gap"),
            ("OUT", "Parameters.wheel_width / 2 - Parameters.wplate_gap"
                    " - Parameters.wplate_thk")):
        pl = bore_cyl(doc, "WHEEL_PLATE_%s_%s" % (wtag, tag),
                      "WHEEL_PLATE_%s_%s_O92_disc_chamfered_UNVERIFIED"
                      % (wtag, tag), status,
                      "Parameters.wplate_dia", "Parameters.wplate_thk",
                      "Parameters.plate_bore",
                      {"Placement.Base.y": yexpr}, "Y",
                      chamfer_l=1.0, chamfer_min_r=30.0)
        solids.append(pl)
    group_add(carrier, *solids)
    for k in range(roller_count):
        frm, fused = roller_subassy(doc, wtag, k, pitch_deg, sgn, status,
                                    vendor)
        group_add(carrier, frm)
        solids.append(fused)
    return carrier, solids
