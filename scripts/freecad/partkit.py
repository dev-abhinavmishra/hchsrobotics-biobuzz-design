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

# roller frame construction angle offset; must match the
# mec_roll_phase Parameters alias (baked rotation -- not live)
_PHASE_OFFSET_DEG = 18.0
_ROT = {"Y": (-90, (1, 0, 0)), "X": (90, (0, 1, 0)), "Z": (0, (0, 0, 1)),
        "-Y": (90, (1, 0, 0)), "-X": (-90, (0, 1, 0)),
        "-Z": (180, (1, 0, 0))}
_AXIS_COMP = {"X": "x", "Y": "y", "Z": "z",
              "-Y": "y", "-X": "x", "-Z": "z"}


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
               "%s_construction_tool_UNVERIFIED" % _tool_name(name),
               "UNVERIFIED - part-kit construction tool", dims, pos, rot)


def tool_cyl(doc, name, dims, pos=None, rot=None):
    return cyl(doc, _tool_name(name),
               "%s_construction_tool_UNVERIFIED" % _tool_name(name),
               "UNVERIFIED - part-kit construction tool", dims, pos, rot)


def tool_compound(doc, name, links):
    o = doc.addObject("Part::Compound", _tool_name(name))
    stamp(o, "%s_tool_compound_UNVERIFIED" % _tool_name(name),
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
    th = math.radians(idx * pitch_deg) + math.radians(
        _PHASE_OFFSET_DEG)
    frm = doc.addObject("App::Part", name)
    stamp(frm, name + "_slant_frame", status)
    frm.Placement.Rotation = App.Rotation(
        App.Vector(math.cos(th), 0.0, math.sin(th)), 0.0)
    frm.setExpression("Placement.Rotation.Angle",
                      "%sParameters.mec_roll_slant"
                      % ("" if sgn > 0 else "-"))
    bind(frm, {
        "Placement.Base.x":
            ("Parameters.mec_roll_rad * cos(%d * "
             "Parameters.mec_roll_pitch + Parameters.mec_roll_phase)"
             % idx),
        "Placement.Base.z":
            ("Parameters.mec_roll_rad * sin(%d * "
             "Parameters.mec_roll_pitch + Parameters.mec_roll_phase)"
             % idx),
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


# ====================================================================
# Sprint-01 overhaul extensions
# ====================================================================
def prism(doc, name, label, status, n, crad, length, pos=None, rot=None,
          vendor=None):
    """Part::Prism (regular n-gon extruded along local +Z).
    crad/length are expression strings; placements bind as usual."""
    o = doc.addObject("Part::Prism", name)
    stamp(o, label, status, vendor)
    o.Polygon = int(n)
    bind(o, {"Circumradius": crad, "Height": length})
    bind(o, pos or {})
    _bind_zeros(o, pos)
    if rot is not None:
        o.Placement.Rotation = rot
    return o


def tool_prism(doc, name, n, crad, length, pos=None, rot=None):
    return prism(doc, _tool_name(name),
                 "%s_construction_tool_UNVERIFIED" % _tool_name(name),
                 "UNVERIFIED - part-kit construction tool",
                 n, crad, length, pos, rot)


def hex_shaft(doc, name, label, status, crad, length, tail_pos, axis="Y",
              tip_d=None, tip_len=None, vendor=None):
    """8mm REX-style hex shaft; optional turned/threaded round tip fused
    on the outboard end. tail_pos = expr map of the prism base corner
    (min point on `axis`). Returns the fused (or bare) shaft solid."""
    sh = tool_prism(doc, name + "_HEX", 6, crad, length, tail_pos,
                    axis_rot(axis))
    if tip_d is None:
        return _rename_last(doc, sh, name, label, status, vendor)
    comp = _AXIS_COMP[axis]
    tpos = dict(tail_pos)
    if axis.startswith("-"):
        tpos["Placement.Base." + comp] = "(%s) - %s" % (
            tail_pos["Placement.Base." + comp], length)
    else:
        tpos["Placement.Base." + comp] = "(%s) + %s" % (
            tail_pos["Placement.Base." + comp], length)
    tip = tool_cyl(doc, name + "_TIP",
                   {"Radius": "(%s) / 2" % tip_d, "Height": tip_len},
                   tpos, axis_rot(axis))
    f = fuse(doc, name, label, status, sh, tip)
    if vendor:
        f.addProperty("App::PropertyString", "VendorRef", "Vendor",
                      "vendor reference, pending verification")
        f.VendorRef = vendor
    return f


def _rename_last(doc, obj, name, label, status, vendor):
    """Re-stamp an existing tool object under a public name."""
    obj.Name = name
    stamp(obj, label, status, vendor)
    return obj


def hex_nut(doc, name, label, status, wrench, h, bore, pos, axis="Y"):
    """Hex nut (6-gon prism, wrench flats = `wrench` across-flats) with a
    real thread-core bore. pos = min-corner expr map of the blank."""
    af_crad = "(%s) / 2 / cos(30 deg)" % wrench
    blk = tool_prism(doc, name + "_BLK", 6, af_crad, h, pos,
                     axis_rot(axis))
    comp = _AXIS_COMP[axis]
    tpos = dict(pos)
    tpos["Placement.Base." + comp] = "(%s) - 1" % pos[
        "Placement.Base." + comp]
    t = tool_cyl(doc, name + "_BORE",
                 {"Radius": "(%s) / 2" % bore, "Height": "(%s) + 2" % h},
                 tpos, axis_rot(axis))
    return cut(doc, name, label, status, blk, t)


def bolt(doc, name, label, status, shaft_d, length, head_d, head_h,
         pos, axis="Y"):
    """Button-head bolt pointing along `axis` (+Y/-Y/+Z/-Z): `pos` is the
    expr map for the HEAD's outer (entry-side) face corner; the shaft
    runs from the head toward +axis for `length`, so the bolt occupies
    [head_face, head_face + head_h + length] along axis for +axes and
    [head_face - head_h - length, head_face] for -axes."""
    sgn = 1 if not axis.startswith("-") else -1
    comp = _AXIS_COMP[axis]
    hpos = dict(pos)
    spos = dict(pos)
    if sgn > 0:
        # head occupies [p, p+head_h]; shaft [p+head_h, p+head_h+len]
        spos["Placement.Base." + comp] = "(%s) + %s" % (
            pos["Placement.Base." + comp], head_h)
    else:
        # cylinder base extrudes -axis: head [p-head_h, p] (base at p);
        # shaft [p-head_h-len, p-head_h] (base at p-head_h)
        hpos["Placement.Base." + comp] = pos["Placement.Base." + comp]
        spos["Placement.Base." + comp] = "(%s) - %s" % (
            pos["Placement.Base." + comp], head_h)
    sh = tool_cyl(doc, name + "_SH",
                  {"Radius": "(%s) / 2" % shaft_d, "Height": length},
                  spos, axis_rot(axis))
    hd = tool_cyl(doc, name + "_HD",
                  {"Radius": "(%s) / 2" % head_d, "Height": head_h},
                  hpos, axis_rot(axis))
    tok = status.split(" ")[0] if status else ""
    if tok and tok not in label:
        label = label + "_" + tok
    return fuse(doc, name, label, status, sh, hd)


def tapped_block(doc, name, label, status, dims, pos, tap_bores=()):
    """Solid block with blind tap-drill bores (threaded member).
    tap_bores: iterable of (dia_expr, pos_dict, axis, depth_expr); each
    is a blind bore into the block face."""
    if not tap_bores:
        return box(doc, name, label, status, dims, pos)
    blk = tool_box(doc, name + "_BLK", dims, pos)
    tools = [tool_cyl(doc, "%s_TAP%02d" % (name, i),
                      {"Radius": "(%s) / 2" % dia, "Height": depth},
                      bp, axis_rot(ax))
             for i, (dia, bp, ax, depth) in enumerate(tap_bores)]
    return cut(doc, name, label, status, blk, tools)


def channel_open(doc, name, label, status, pos0, L, S, W, axis="X",
                 wall_rows=(), web_rows=(), bores=()):
    """Open-down (inverted-Pi) channel along `axis`, square S x S, wall W.

    pos0: (c0, c1, c2) expr strings for the OUTER box min corner.
    For axis=X the two vertical walls face +/-Y and the web caps the top
    (+Z); for axis=Y the walls face +/-X. Mouth opens at z0 (down).
    wall_rows: dicts(count, dia, pitch, start, z) -- hole rows pierced
        through BOTH side walls (each entry cuts each wall).
    web_rows: dicts(count, dia, pitch, start, line) -- vertical holes
        through the top web; `line` = expr for the web-center coord.
    bores: iterable of (dia_expr, pos_dict, hole_axis, height_expr) --
        caller-specified extra cuts (axle bores, bolt patterns).
    """
    if axis == "X":
        dims = {"Length": L, "Width": S, "Height": S}
    else:
        dims = {"Length": S, "Width": L, "Height": S}
    pos = {"Placement.Base.x": pos0[0], "Placement.Base.y": pos0[1],
           "Placement.Base.z": pos0[2]}
    outer = tool_box(doc, name + "_OUT", dims, pos)
    tools = []
    # cavity: side walls + top web survive; mouth opens downward
    if axis == "X":
        inner = tool_box(
            doc, name + "_INNER",
            {"Length": "(%s) + 2" % L, "Width": "(%s) - 2 * %s" % (S, W),
             "Height": "(%s) - %s" % (S, W)},
            {"Placement.Base.x": "(%s) - 1" % pos0[0],
             "Placement.Base.y": "(%s) + %s" % (pos0[1], W),
             "Placement.Base.z": pos0[2]})
    else:
        inner = tool_box(
            doc, name + "_INNER",
            {"Length": "(%s) - 2 * %s" % (S, W), "Width": "(%s) + 2" % L,
             "Height": "(%s) - %s" % (S, W)},
            {"Placement.Base.x": "(%s) + %s" % (pos0[0], W),
             "Placement.Base.y": "(%s) - 1" % pos0[1],
             "Placement.Base.z": pos0[2]})
    tools.append(inner)
    # wall rows: pierce each of the two side walls
    for r_i, row in enumerate(wall_rows):
        for i in range(row["count"]):
            c = "(%s) + %s + %d * %s" % (
                pos0[0] if axis == "X" else pos0[1],
                row["start"], i, row["pitch"])
            for w_i in (0, 1):
                hp = {"Placement.Base.z": row["z"]}
                if axis == "X":
                    hp["Placement.Base.x"] = c
                    hp["Placement.Base.y"] = (
                        "(%s) - 1" % pos0[1] if w_i == 0 else
                        "(%s) + %s - %s - 1" % (pos0[1], S, W))
                    rot = axis_rot("Y")
                else:
                    hp["Placement.Base.y"] = c
                    hp["Placement.Base.x"] = (
                        "(%s) - 1" % pos0[0] if w_i == 0 else
                        "(%s) + %s - %s - 1" % (pos0[0], S, W))
                    rot = axis_rot("X")
                tools.append(tool_cyl(
                    doc, "%s_W%d_%02d_%02d" % (name, r_i, i, w_i),
                    {"Radius": "(%s) / 2" % row["dia"],
                     "Height": "(%s) + 2" % W}, hp, rot))
    # web rows: vertical through the top web
    for r_i, row in enumerate(web_rows):
        for i in range(row["count"]):
            c = "(%s) + %s + %d * %s" % (
                pos0[0] if axis == "X" else pos0[1],
                row["start"], i, row["pitch"])
            hp = {"Placement.Base.z":
                  "(%s) + %s - %s - 1" % (pos0[2], S, W)}
            if axis == "X":
                hp["Placement.Base.x"] = c
                hp["Placement.Base.y"] = row["line"]
            else:
                hp["Placement.Base.x"] = row["line"]
                hp["Placement.Base.y"] = c
            tools.append(tool_cyl(
                doc, "%s_WH%d_%02d" % (name, r_i, i),
                {"Radius": "(%s) / 2" % row["dia"],
                 "Height": "(%s) + 2" % W}, hp))
    for i, (dia, bp, ax, h) in enumerate(bores):
        tools.append(tool_cyl(doc, "%s_BORE%02d" % (name, i),
                              {"Radius": "(%s) / 2" % dia, "Height": h},
                              bp, axis_rot(ax)))
    return cut(doc, name, label, status, outer, tools)


def flange_bearing(doc, name, label, status, w, t, h, bore_d, pilot_d,
                   pilot_l, pos, axis="Y", bolt_d=None, bolt_off=None,
                   pilot_dir=1):
    """Flanged bearing block: plate + pilot boss fused, real through
    bore, optional 4-hole bolt square. pos = plate min-corner expr map.
    pilot_dir=+1: pilot extends +axis from the plate's +axis face;
    -1: pilot extends -axis from the plate's min face (into the wall)."""
    blk = tool_box(doc, name + "_BLK",
                   {"Length": w, "Width": t, "Height": h}, pos)
    comp = _AXIS_COMP[axis]
    cx = "(%s) + %s / 2" % (pos["Placement.Base.x"], w)
    cz = "(%s) + %s / 2" % (pos["Placement.Base.z"], h)
    ppos = dict(pos)
    ppos["Placement.Base.x"] = cx
    ppos["Placement.Base.z"] = cz
    if pilot_dir > 0:
        ppos["Placement.Base." + comp] = "(%s) + %s" % (
            pos["Placement.Base." + comp], t)
    else:
        ppos["Placement.Base." + comp] = "(%s) - %s" % (
            pos["Placement.Base." + comp], pilot_l)
    boss = tool_cyl(doc, name + "_PILOT",
                    {"Radius": "(%s) / 2" % pilot_d, "Height": pilot_l},
                    ppos, axis_rot(axis))
    body = fuse(doc, _tool_name(name + "_BODY"), label + "_body", status,
                blk, boss)
    comp_p = _bolt_tools(doc, name, t, w, h, bolt_d, bolt_off, pos,
                         axis) if bolt_d and bolt_off else []
    bpos = dict(pos)
    bpos["Placement.Base.x"] = cx
    bpos["Placement.Base.z"] = cz
    if pilot_dir > 0:
        bpos["Placement.Base." + comp] = "(%s) - 1" % (
            pos["Placement.Base." + comp])
    else:
        bpos["Placement.Base." + comp] = "(%s) - %s - 1" % (
            pos["Placement.Base." + comp], pilot_l)
    bore = tool_cyl(doc, name + "_BORE",
                    {"Radius": "(%s) / 2" % bore_d,
                     "Height": "(%s) + %s + 2" % (t, pilot_l)},
                    bpos, axis_rot(axis))
    return cut(doc, name, label, status, body, [bore] + comp_p)


def motor_unit(doc, name, label, status, body_d, body_l, gb_d, gb_l,
               sock_af, sock_depth, tap_d, tap_depth, tap_off,
               face_pos, vendor=None, direction=1, tap_off_z=None):
    """Gearbox motor, single exportable solid: can + gearbox housing
    fused, real hex socket bore + blind tap-drill holes cut into the
    face. face_pos = expr map of the FACE PLANE (the mount face);
    direction=+1: body extends -Y (inboard) from the face;
    direction=-1: body extends +Y."""
    comp = "y"
    if direction > 0:
        can_y = "(%s - %s - %s)" % (face_pos["Placement.Base.y"],
                                    gb_l, body_l)
        gb_y = "(%s - %s)" % (face_pos["Placement.Base.y"], gb_l)
    else:
        can_y = "(%s + %s)" % (face_pos["Placement.Base.y"], gb_l)
        gb_y = face_pos["Placement.Base.y"]
    can_pos = dict(face_pos)
    can_pos["Placement.Base.y"] = can_y
    gb_pos = dict(face_pos)
    gb_pos["Placement.Base.y"] = gb_y
    can = tool_cyl(doc, name + "_CAN",
                   {"Radius": "(%s) / 2" % body_d, "Height": body_l},
                   can_pos, axis_rot("Y"))
    gb = tool_cyl(doc, name + "_GB",
                  {"Radius": "(%s) / 2" % gb_d, "Height": gb_l},
                  gb_pos, axis_rot("Y"))
    m = fuse(doc, _tool_name(name + "_BODY"), label + "_body", status,
             can, gb)
    # socket bore: hex prism through the face into the gearbox
    if direction > 0:
        sock_y = "(%s - %s - 1)" % (face_pos["Placement.Base.y"],
                                    sock_depth)
    else:
        sock_y = "(%s - 1)" % face_pos["Placement.Base.y"]
    sock_pos = dict(face_pos)
    sock_pos["Placement.Base.y"] = sock_y
    s_sock = tool_prism(
        doc, name + "_SOCK", 6,
        "(%s) / 2 / cos(30 deg)" % sock_af, "(%s) + 2" % sock_depth,
        sock_pos,
        axis_rot("Y"))
    taps = []
    for i, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        if direction > 0:
            ty = "(%s - %s)" % (face_pos["Placement.Base.y"], tap_depth)
        else:
            ty = face_pos["Placement.Base.y"]
        tp = {"Placement.Base.x":
              "(%s) + %d * %s" % (face_pos["Placement.Base.x"], sx,
                                  tap_off),
              "Placement.Base.y": ty,
              "Placement.Base.z":
              "(%s) + %d * %s" % (face_pos["Placement.Base.z"], sz,
                                  tap_off_z or tap_off)}
        taps.append(tool_cyl(doc, "%s_TAP%02d" % (name, i),
                             {"Radius": "(%s) / 2" % tap_d,
                              "Height": tap_depth}, tp, axis_rot("Y")))
    f = cut(doc, name, label, status, m, [s_sock] + taps)
    if vendor:
        f.addProperty("App::PropertyString", "VendorRef", "Vendor",
                      "vendor reference, pending verification")
        f.VendorRef = vendor
    return f


def clamp_block(doc, name, label, status, w, bore_d, ear, bolt_d,
                center_x, pos_y, center_z, ear_zs=None):
    """Split-ring motor clamp gripping a Y-axis motor can: block with a
    through bore Øbore_d centered at (center_x, *, center_z), two ear
    tabs in X with vertical bolt holes.
    center_x/center_z: expr strings for the bore axis position;
    pos_y: expr for the block's min-Y corner."""
    blk = tool_box(
        doc, name + "_BLK",
        {"Length": "2 * %s + %s" % (ear, bore_d),
         "Width": w, "Height": "(%s) + 10" % bore_d},
        {"Placement.Base.x": "(%s) - %s - (%s) / 2" % (
            center_x, ear, bore_d),
         "Placement.Base.y": pos_y,
         "Placement.Base.z": "(%s) - (%s) / 2 - 5" % (center_z, bore_d)})
    bore = tool_cyl(
        doc, name + "_BORE",
        {"Radius": "(%s) / 2" % bore_d, "Height": "(%s) + 2" % w},
        {"Placement.Base.x": center_x,
         "Placement.Base.y": "(%s) - 1" % pos_y,
         "Placement.Base.z": center_z}, axis_rot("Y"))
    tools = [bore]
    if ear_zs is None:
        ear_zs = (center_z,)
    for i, su in enumerate((-1, 1)):
        for j, ez in enumerate(ear_zs):
            ep = {"Placement.Base.x":
                  "(%s) + %d * ((%s) / 2 + (%s) / 2)" % (
                      center_x, su, bore_d, ear),
                  "Placement.Base.y": "(%s) - 1" % pos_y,
                  "Placement.Base.z": ez}
            tools.append(tool_cyl(doc, "%s_EAR%d_%d" % (name, i, j),
                                  {"Radius": "(%s) / 2" % bolt_d,
                                   "Height": "(%s) + 2" % w}, ep,
                                  axis_rot("Y")))
    return cut(doc, name, label, status, blk, tools)


def standoff_hex(doc, name, label, status, dia, height, pos, tap_d=None,
                 tap_depth=None):
    """Hex standoff post; optional blind tap bores on both faces
    (top and bottom) for machine screws."""
    af_crad = "(%s) / 2 / cos(30 deg)" % dia
    if not tap_d:
        return prism(doc, name, label, status, 6, af_crad, height, pos)
    blk = tool_prism(doc, name + "_BLK", 6, af_crad, height, pos)
    tools = []
    for i, zp in enumerate(("(%s) - 1" % pos["Placement.Base.z"],
                          "(%s) + %s - (%s) + 1" % (pos["Placement.Base.z"],
                                                   height, tap_depth))):
        tp = dict(pos)
        tp["Placement.Base.z"] = zp
        tools.append(tool_cyl(doc, "%s_TAP%d" % (name, i),
                              {"Radius": "(%s) / 2" % tap_d,
                               "Height": tap_depth}, tp))
    return cut(doc, name, label, status, blk, tools)


def strap_u(doc, name, label, status, strap_w, span_w, h, thk, foot_l,
            bolt_d, pos):
    """Battery strap wrapping a pack along Y: top band + two vertical
    legs + outward foot tabs bolted down. pos = min-corner map of the
    whole strap footprint INCLUDING the feet tabs; the U-channel legs
    sit at pos.y+foot_l .. +span_w so the band hugs the pack faces
    when span_w = pack_w + 2*thk."""
    py, pz = pos["Placement.Base.y"], pos["Placement.Base.z"]
    parts = [
        tool_box(doc, name + "_TOP",
                 {"Length": strap_w, "Width": span_w, "Height": thk},
                 {"Placement.Base.x": pos["Placement.Base.x"],
                  "Placement.Base.y": "(%s) + %s" % (py, foot_l),
                  "Placement.Base.z": "(%s) + %s - %s" % (pz, h, thk)})]
    for i in range(2):
        parts.append(tool_box(
            doc, "%s_LEG%d" % (name, i),
            {"Length": strap_w, "Width": thk,
             "Height": "(%s) - %s" % (h, thk)},
            {"Placement.Base.x": pos["Placement.Base.x"],
             "Placement.Base.y":
             "(%s) + %s + %d * (%s - %s)" % (py, foot_l, i, span_w, thk),
             "Placement.Base.z": pz}))
        parts.append(tool_box(
            doc, "%s_FT%d" % (name, i),
            {"Length": strap_w, "Width":
             "(%s) + %s" % (foot_l, thk), "Height": "3"},
            {"Placement.Base.x": pos["Placement.Base.x"],
             "Placement.Base.y":
             ("(%s)" % py if i == 0 else
              "(%s) + %s + %s - %s" % (py, foot_l, span_w, thk)),
             "Placement.Base.z": pz}))
    body = fuse(doc, _tool_name(name + "_B"), label + "_band", status,
                parts[0], parts[1:])
    tools = []
    for i in range(2):
        bp = {"Placement.Base.x":
              "(%s) + %s / 2" % (pos["Placement.Base.x"], strap_w),
              "Placement.Base.y":
              ("(%s) + %s / 2" % (py, foot_l) if i == 0 else
               "(%s) + %s + %s + %s / 2" % (py, foot_l, span_w, foot_l)),
              "Placement.Base.z": "(%s) - 1" % pz}
        tools.append(tool_cyl(doc, "%s_HOLE%d" % (name, i),
                              {"Radius": "(%s) / 2" % bolt_d,
                               "Height": "6"}, bp))
    return cut(doc, name, label, status, body, tools)


def wire_seg(doc, name, label, status, dia, p0, p1):
    """One wire segment between numeric endpoints -> returns the raw
    cylinder (caller fuses). Internal helper for wire_bundle()."""
    import Part as _P
    v = App.Vector(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    L = v.Length
    if L < 1e-6:
        return None
    zaxis = App.Vector(0, 0, 1)
    vv = App.Vector(v)
    vv.normalize()
    rot = App.Rotation(zaxis, vv)
    o = doc.addObject("Part::Cylinder", name)
    tok = status.split(" ")[0] if status else ""
    stamp(o, label + ("_seg_" + tok if tok else "_seg"), status)
    o.Radius = dia / 2.0
    o.Height = L
    base = App.Vector(*p0)
    o.Placement = App.Placement(base, rot)
    return o


def wire_bundle(doc, name, label, status, dia, points):
    """Fused polyline wire run (numeric points). Wires are harness
    geometry, not parametric structure; positions bake at build time and
    the bundle is stamped exportable."""
    segs = []
    for i in range(len(points) - 1):
        s = wire_seg(doc, TOOL_PREFIX + "%s_S%02d" % (name, i),
                     label, status, dia, points[i], points[i + 1])
        if s is not None:
            segs.append(s)
    if not segs:
        raise RuntimeError("wire_bundle %s: no segments" % name)
    if len(segs) == 1:
        return _rename_last(doc, segs[0], name, label, status, None)
    return fuse(doc, name, label, status, segs[0], segs[1:])


def endcap(doc, name, label, status, S, W, t, pilot, pos, axis="X",
           bolt_d=None):
    """Channel end cap: face plate + pilot that nests into the channel
    mouth (pilot is a declared-contact press fit)."""
    if axis == "X":
        dims = {"Length": t, "Width": S, "Height": S}
        pdims = {"Length": pilot, "Width": "(%s) - 2 * %s - 0.4" % (S, W),
                 "Height": "(%s) - %s - 0.4" % (S, W)}
        ppos = {"Placement.Base.x":
                "(%s) + %s" % (pos["Placement.Base.x"], t),
                "Placement.Base.y":
                "(%s) + %s + 0.2" % (pos["Placement.Base.y"], W),
                "Placement.Base.z":
                "(%s) + 0.2" % pos["Placement.Base.z"]}
    else:
        dims = {"Length": S, "Width": t, "Height": S}
        pdims = {"Length": "(%s) - 2 * %s - 0.4" % (S, W),
                 "Width": pilot,
                 "Height": "(%s) - %s - 0.4" % (S, W)}
        ppos = {"Placement.Base.x":
                "(%s) + %s + 0.2" % (pos["Placement.Base.x"], W),
                "Placement.Base.y":
                "(%s) + %s" % (pos["Placement.Base.y"], t),
                "Placement.Base.z":
                "(%s) + 0.2" % pos["Placement.Base.z"]}
    face = tool_box(doc, name + "_FACE", dims, pos)
    pil = tool_box(doc, name + "_PILOT", pdims, ppos)
    return fuse(doc, name, label, status, face, pil)

