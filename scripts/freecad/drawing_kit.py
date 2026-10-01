"""drawing_kit.py -- shared engineering-drawing kit (BIOBUZZ rehaul).

One vocabulary for generating dimensioned drawing sheets and flat
profiles from the parametric FCStd documents:

- ``exportable`` / ``world_shape`` mirror export_step.py's object scan:
  solids consumed by a feature DAG (Base/Tool/Shapes) are skipped so the
  leaf part is what gets drawn; ENV_/TOOL_/AXIS_/REF_/VOL_ are excluded.
- ``sheet_for_part`` builds a real TechDraw page (DrawPage +
  DrawSVGTemplate + three DrawViewPart projections + extent
  DrawViewDimensions) in the source document, pulls each view's edge
  geometry via ``TechDraw.viewPartAsSvg``, then composes the published
  sheet SVG around it (frame, title block, view layout, extent-dimension
  callouts). PDF is the same SVG rendered through QSvgRenderer ->
  QPdfWriter. FreeCAD 1.1 has no headless page-level export
  (writePageAsSvg/Pdf are GUI-side), so the exported sheet is composed
  here; the TechDraw page objects stay in the document tree for anyone
  who later saves a drawing FCStd.
- ``flat_profile_dxf`` rotates a plate's face normal onto +Z and emits
  an R12 DXF via ``TechDraw.projectToDXF``.

Nothing here hardcodes part lists: parts are enumerated from each
document at run time and identical parts (same world-space bounding
box + volume) collapse into one sheet carrying a QTY callout.

Stdlib + FreeCAD-bundled modules only (TechDraw, Part, PySide6/QtSvg).
"""
import math
import re
import xml.sax.saxutils

import FreeCAD as App
import Part  # noqa: F401  registers Part::* types
import TechDraw

EXCLUDE_PREFIX = ("ENV_", "TOOL_", "AXIS_", "REF_", "VOL_")
EXCLUDE_TYPES = ("App::Part", "App::Origin")

# Orthographic views: (name, Direction, XDirection). Direction is the
# outward normal of the viewed face (TechDraw convention), matching the
# render_png.py camera table: front = -Y face (X horiz, Z vert),
# top = +Z face (X horiz, Y vert), right = +X face (Y horiz, Z vert).
VIEWS = (
    ("FRONT", (0, -1, 0), (1, 0, 0)),
    ("TOP", (0, 0, 1), (1, 0, 0)),
    ("RIGHT", (1, 0, 0), (0, 1, 0)),
)

# A4 landscape, mm
SHEET_W, SHEET_H = 297.0, 210.0
BORDER = 6.0
# view cells: (x0, y0, x1, y1) inside the border, y measured down
VIEW_CELLS = {
    "TOP": (10.0, 12.0, 175.0, 82.0),
    "FRONT": (10.0, 86.0, 175.0, 160.0),
    "RIGHT": (180.0, 86.0, 287.0, 160.0),
}
VIEW_LABEL = {"TOP": "TOP", "FRONT": "FRONT", "RIGHT": "RIGHT SIDE"}

DIM_GAP = 4.0          # gap between view extent and dimension line
DIM_TXT_H = 3.2        # dimension text height (mm)

# plate detection: a part is a flat plate when its smallest bbox dim is
# thin relative to both larger dims, or its name says so and it is still
# reasonably thin.
PLATE_MAX_THICK = 20.0
PLATE_ASPECT = 4.0
PLATE_NAME_RE = re.compile(
    r"(deck|plate|pan|cheek|brkt|bracket|shelf|panel|wall|flange|"
    r"disc|disk|shim|spacer|gusset|brace|mount|frame|cover|lid|"
    r"faceplate|skid|bumper|apron|board|sheet)", re.IGNORECASE)
# fasteners are never "plates" even when their head geometry is
# disc-like, and neither are thin flexible parts (belts, cables, chain)
# whose bounding box alone would pass the thin+wide test
PLATE_EXCLUDE_RE = re.compile(
    r"^(BOLT|NUT|SCRW|WSH|RIVET|RIVNUT|BHCS|SBHCS|SHCS|FHCS|SETSCR|"
    r"HEXNUT|LOCKNUT|STANDOFF|BELT|CABLE|CHAIN|ROPE|WIRE|SPRING|"
    r"ELASTIC|STRAP|TUBE|HOSE|ZIP|TIE)_", re.IGNORECASE)

# material fallback when bom.csv has no line for the object (mirrors
# dt_build.bom_autofill's class-prefix table)
MATERIAL_BY_CLASS = {
    "BOLT": "steel", "NUT": "steel", "SCRW": "steel", "RIVNUT": "steel",
    "WSH": "steel", "COLLAR": "steel", "PINION": "steel",
    "AXLE": "steel", "SHAFT": "steel", "SPROCKET": "steel",
    "CLAMP": "aluminum", "GUSSET": "aluminum", "BRG": "aluminum",
    "MOUNT": "aluminum", "ODO": "aluminum", "RAIL": "aluminum",
    "CHANNEL": "aluminum", "PLATE": "aluminum", "DECK": "aluminum",
    "BRKT": "aluminum", "PANEL": "polycarb", "WALL": "polycarb",
    "PAN": "polycarb", "SHELF": "polycarb", "DIV": "polycarb",
    "WHEEL": "rubber", "ROLLER": "rubber",
}

REV = "A"
UNITS_NOTE = "ALL DIMENSIONS IN MILLIMETERS"
PROJ_NOTE = "THIRD-ANGLE PROJECTION"
DISCLAIMER = "PROTOTYPE / VERIFY BEFORE MANUFACTURING"


# --------------------------------------------------------------------
# document scan (same rules as export_step.py)
# --------------------------------------------------------------------
def _consumed_add(x, out):
    out.add(x.Name)
    for p in ("Links", "Group"):
        g = getattr(x, p, None)
        if g is None:
            continue
        for y in (g if isinstance(g, (list, tuple)) else (g,)):
            if y is not None:
                _consumed_add(y, out)


def exportable(doc):
    """Final (non-consumed) solid objects worth drawing."""
    consumed = set()
    for o in doc.Objects:
        if o.TypeId in ("Part::Fuse", "Part::Cut", "Part::Chamfer",
                        "Part::Common", "Part::MultiFuse"):
            for p in ("Base", "Tool", "Shapes"):
                t = getattr(o, p, None)
                if t is None:
                    continue
                for x in (t if isinstance(t, (list, tuple)) else (t,)):
                    if x is not None:
                        _consumed_add(x, consumed)
    return [o for o in doc.Objects
            if hasattr(o, "Shape") and not o.Shape.isNull()
            and o.Shape.Volume > 0
            and o.TypeId not in EXCLUDE_TYPES
            and not o.Name.startswith(EXCLUDE_PREFIX)
            and o.Name not in consumed]


def world_shape(o):
    """Shape in world coordinates (carrier placements baked in)."""
    s = o.Shape.copy()
    s.Placement = o.getGlobalPlacement()
    try:
        s = s.removeSplitter()
    except Exception:
        pass
    return s


# --------------------------------------------------------------------
# part grouping + metadata
# --------------------------------------------------------------------
def signature(shape):
    """Dedup key: sorted bbox extents + volume + topo counts, all
    rounded to 0.1 mm. Face/edge counts keep parts with the same
    envelope but different holes/profiles on separate sheets;
    mirrored pairs still share a sheet intentionally (one flat
    profile, cut once and flipped)."""
    b = shape.BoundBox
    dims = (b.XLength, b.YLength, b.ZLength)
    return tuple(sorted(round(d, 1) for d in dims)) + (
        round(shape.Volume, 1), len(shape.Faces), len(shape.Edges))


def group_identical(objs):
    """[{sig, objects:[o,...], shape}] -- identical parts share a sheet."""
    groups = {}
    order = []
    for o in objs:
        s = world_shape(o)
        sig = signature(s)
        if sig not in groups:
            groups[sig] = {"sig": sig, "objects": [], "shape": s}
            order.append(sig)
        groups[sig]["objects"].append(o)
    return [groups[k] for k in order]


def family_name(names):
    """Common prefix of the instance names, cut back to a '_' boundary."""
    if len(names) == 1:
        return names[0]
    pfx = names[0]
    for n in names[1:]:
        while not n.startswith(pfx) and pfx:
            pfx = pfx[:-1]
    pfx = pfx.rstrip("_0123456789")
    return (pfx + "_*") if pfx else names[0]


def is_plate(name, shape):
    if PLATE_EXCLUDE_RE.match(name):
        return False
    b = shape.BoundBox
    dims = sorted((b.XLength, b.YLength, b.ZLength))
    thin, mid, big = dims
    if thin <= 0.01:
        return False
    if mid >= PLATE_ASPECT * thin and thin <= PLATE_MAX_THICK:
        return True
    return bool(PLATE_NAME_RE.search(name)) and thin <= PLATE_MAX_THICK


def part_meta(obj, bom=None):
    """Title-block fields from object properties + optional bom.csv row."""
    status = getattr(obj, "DataStatus", "") or "UNVERIFIED"
    label = getattr(obj, "Label", obj.Name)
    material = None
    spec = None
    if bom and obj.Name in bom:
        row = bom[obj.Name]
        material = row.get("material") or None
        spec = row.get("spec") or None
        if not material or material == "-":
            material = None
    if material is None:
        for cls, mat in MATERIAL_BY_CLASS.items():
            if obj.Name.startswith(cls + "_") or obj.Name == cls:
                material = mat
                break
    if material is None:
        material = "TBD"
    vendor = getattr(obj, "VendorRef", "") or ""
    return {"name": obj.Name, "label": label, "status": status,
            "material": material, "spec": spec or "",
            "vendor": vendor}


def load_bom(path):
    """exports/bom/bom.csv -> {object_name: row}; tolerant if absent."""
    import csv
    bom = {}
    try:
        with open(str(path), newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                for name in (row.get("objects") or "").split():
                    name = name.strip()
                    if name:
                        bom[name] = row
    except OSError:
        pass
    return bom


# --------------------------------------------------------------------
# TechDraw views
# --------------------------------------------------------------------
# repo-local A4 template (portable across FreeCAD installs; the bundled
# ISO blank template is the fallback)
TEMPLATE_PATH = str(
    __import__("pathlib").Path(__file__).resolve().with_name(
        "drawing_template_A4.svg"))


def _fallback_template():
    import os
    for root in (getattr(App, "getResourceDir", lambda: "")(),
                 os.path.join(getattr(App, "getHomePath", lambda: "")(),
                              "..", "share")):
        c = os.path.join(root,
                         "Mod/TechDraw/Templates/ISO/"
                         "A4_Landscape_blank.svg")
        if os.path.exists(c):
            return c
    raise RuntimeError("no usable TechDraw template found")


def blank_template_path():
    import os
    return TEMPLATE_PATH if os.path.exists(TEMPLATE_PATH) \
        else _fallback_template()


def make_page(doc, source_obj, tag, fields=None):
    """Real TechDraw page for one part: template + front/top/right views
    + horizontal/vertical extent dims on the front view. `fields` fills
    the template's freecad:editable title-block texts. Returns
    (page, {viewname: viewobj})."""
    page = doc.addObject("TechDraw::DrawPage", "PAGE_" + tag)
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "T_" + tag)
    tmpl.Template = blank_template_path()
    page.Template = tmpl
    for k, v in (fields or {}).items():
        try:
            tmpl.setEditFieldContent(k, str(v))
        except Exception:
            pass
    views = {}
    for vn, dirv, xdir in VIEWS:
        v = doc.addObject("TechDraw::DrawViewPart",
                          "V_%s_%s" % (vn, tag))
        v.Source = [source_obj]
        v.Direction = App.Vector(*dirv)
        v.XDirection = App.Vector(*xdir)
        v.HardHidden = True
        v.SmoothHidden = True
        v.IsoHidden = True
        page.addView(v)
        views[vn] = v
    doc.recompute()
    for v in views.values():
        try:
            v.requestPaint()
        except Exception:
            pass
    front = views["FRONT"]
    for direction in (0, 1):
        try:
            dim = TechDraw.makeExtentDim(front, [], direction)
            page.addView(dim)
        except Exception:
            pass
    try:
        doc.recompute()
    except Exception:
        pass
    return page, views


def remove_page(doc, page):
    for v in list(page.Views):
        try:
            doc.removeObject(v.Name)
        except Exception:
            pass
    for o in (page, page.Template):
        try:
            doc.removeObject(o.Name)
        except Exception:
            pass


def view_edges_svg(view):
    """viewPartAsSvg output with hidden-edge groups restyled dashed."""
    svg = TechDraw.viewPartAsSvg(view) or ""
    # TechDraw emits visible edges in the first <g> (stroke-width 0.7)
    # and hidden edges in later <g>s (stroke-width 0.35); mark the thin
    # groups dashed so the sheet reads like an engineering drawing.
    svg = svg.replace('stroke-width="0.35"',
                      'stroke-width="0.35" stroke-dasharray="2.4 1.2"')
    return svg


def view_extent(view):
    """(u_min, u_max, v_min, v_max) in view-space mm over all edges."""
    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")
    edges = view.getVisibleEdges()
    try:
        edges = edges + view.getHiddenEdges()
    except Exception:
        pass
    for e in edges:
        try:
            b = e.BoundBox
        except Exception:
            continue
        xmin = min(xmin, b.XMin)
        xmax = max(xmax, b.XMax)
        ymin = min(ymin, b.YMin)
        ymax = max(ymax, b.YMax)
    if xmin > xmax:
        # vertex fallback
        for p in list(view.getVisibleVertexes()):
            xmin = min(xmin, p.x)
            xmax = max(xmax, p.x)
            ymin = min(ymin, p.y)
            ymax = max(ymax, p.y)
    if xmin > xmax:
        xmin = xmax = ymin = ymax = 0.0
    return xmin, xmax, ymin, ymax


# --------------------------------------------------------------------
# flat profiles (DXF)
# --------------------------------------------------------------------
def largest_planar_normal(shape):
    """Unit normal of the biggest planar face, or the thin bbox axis."""
    best = None
    best_area = 0.0
    for f in shape.Faces:
        try:
            surf = f.Surface
            if getattr(surf, "TypeId", "") != "Part::GeomPlane":
                continue
            a = f.Area
        except Exception:
            continue
        if a > best_area:
            best_area = a
            best = f
    if best is not None:
        try:
            u, v = best.Surface.parameter(best.CenterOfMass)
            n = best.normalAt(u, v)
            if n.Length > 1e-9:
                return App.Vector(n).normalize()
        except Exception:
            pass
    b = shape.BoundBox
    dims = sorted(((b.XLength, (1, 0, 0)), (b.YLength, (0, 1, 0)),
                   (b.ZLength, (0, 0, 1))))
    return App.Vector(*dims[0][1])


_DXF_HEAD = ("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n"
             "$INSUNITS\n70\n4\n0\nENDSEC\n"
             "0\nSECTION\n2\nENTITIES\n")
_DXF_TAIL = "0\nENDSEC\n0\nEOF\n"


def flat_profile_dxf(shape):
    """DXF string of the part's flat profile: largest planar face is
    rotated onto +Z, the shape is shifted so its projected bounding box
    sits at the origin, then edges are projected to XY ENTITIES."""
    n = largest_planar_normal(shape)
    rot = App.Rotation(n, App.Vector(0, 0, 1))
    s = shape.copy()
    # premultiply the alignment rotation onto the part's own placement
    # so a plate mounted at an angle still lands flat on the XY plane
    s.Placement = App.Placement(App.Vector(), rot) * s.Placement
    b = s.BoundBox
    s.translate(App.Vector(-b.XMin, -b.YMin, -b.ZMin))
    body = TechDraw.projectToDXF(s, App.Vector(0, 0, 1), "ALGO")
    return _DXF_HEAD + body + _DXF_TAIL


# --------------------------------------------------------------------
# sheet composition (SVG -> PDF)
# --------------------------------------------------------------------
def _fmt(v):
    """Dimension text: integers stay integers, else one decimal."""
    r = round(v, 1)
    if abs(r - round(r)) < 0.05:
        return str(int(round(r)))
    return ("%.1f" % r).rstrip("0").rstrip(".")


def _esc(t):
    return xml.sax.saxutils.escape(str(t))


def _dim_h(x0, x1, y, text, mid_y_offset=0.9):
    """Horizontal dimension line between x0..x1 at sheet y, arrowheads
    at the tips pointing outward to the measured extent."""
    out = [
        '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" '
        'stroke="#1a5276" stroke-width="0.25"/>' % (x0, y, x1, y),
        '<path d="M %.2f %.2f L %.2f %.2f L %.2f %.2f z" fill="#1a5276"/>'
        % (x0, y, x0 + 1.6, y - 0.55, x0 + 1.6, y + 0.55),
        '<path d="M %.2f %.2f L %.2f %.2f L %.2f %.2f z" fill="#1a5276"/>'
        % (x1, y, x1 - 1.6, y - 0.55, x1 - 1.6, y + 0.55),
        '<text x="%.2f" y="%.2f" font-size="%.1f" fill="#1a5276" '
        'text-anchor="middle" font-family="sans-serif">%s</text>'
        % ((x0 + x1) / 2.0, y - mid_y_offset, DIM_TXT_H, _esc(text)),
    ]
    return "".join(out)


def _dim_v(x, y0, y1, text):
    """Vertical dimension line at sheet x between y0..y1 (y0 < y1)."""
    out = [
        '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" '
        'stroke="#1a5276" stroke-width="0.25"/>' % (x, y0, x, y1),
        '<path d="M %.2f %.2f L %.2f %.2f L %.2f %.2f z" fill="#1a5276"/>'
        % (x, y0, x - 0.55, y0 + 1.6, x + 0.55, y0 + 1.6),
        '<path d="M %.2f %.2f L %.2f %.2f L %.2f %.2f z" fill="#1a5276"/>'
        % (x, y1, x - 0.55, y1 - 1.6, x + 0.55, y1 - 1.6),
        '<text x="%.2f" y="%.2f" font-size="%.1f" fill="#1a5276" '
        'text-anchor="middle" font-family="sans-serif" '
        'transform="rotate(-90 %.2f %.2f)">%s</text>'
        % (x - 0.9, (y0 + y1) / 2.0, DIM_TXT_H,
           x - 0.9, (y0 + y1) / 2.0, _esc(text)),
    ]
    return "".join(out)


def _title_block(meta, doc_tag, qty, scale_txt, sheet_no, sheet_cnt):
    """Title block cells, bottom-right of the sheet."""
    x0, y0, x1, y1 = 195.0, 160.0, 291.0, 204.0
    rows = [
        (y0, y0 + 14),      # part name
        (y0 + 14, y0 + 22),  # material / spec
        (y0 + 22, y0 + 30),  # qty / rev / scale
        (y0 + 30, y1),      # doc / sheet / date
    ]
    s = ['<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none"'
         ' stroke="#000" stroke-width="0.5"/>' % (x0, y0, x1 - x0, y1 - y0)]
    for ry0, ry1 in rows[1:]:
        s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                 'stroke="#000" stroke-width="0.3"/>'
                 % (x0, ry0, x1, ry0))
    def txt(x, y, t, size=3.0, anchor="start", bold=False, color="#000"):
        return ('<text x="%.1f" y="%.1f" font-size="%.1f" fill="%s" '
                'font-family="sans-serif" text-anchor="%s"%s>%s</text>'
                % (x, y, size, color, anchor,
                   ' font-weight="bold"' if bold else "", _esc(t)))
    title = meta["name"] or meta["label"]
    if qty > 1:
        title = "%s  x%d" % (family_name(meta["_names"]), qty)
    s.append(txt(x0 + 2, y0 + 4, "PART", 2.0, color="#555"))
    # shrink the part-name font until it fits the ~92 mm cell
    nfs = min(4.2, 56.0 / max(len(title), 1))
    s.append(txt(x0 + 2, y0 + 11, title[:64], nfs, bold=True))
    mat = "MATERIAL: %s" % meta["material"]
    if meta.get("spec"):
        mat += "   SPEC: %s" % meta["spec"]
    s.append(txt(x0 + 2, rows[1][0] + 5.5, mat[:60], 2.8))
    s.append(txt(x0 + 2, rows[2][0] + 5.5, "QTY %d" % qty, 2.8))
    s.append(txt(x0 + 24, rows[2][0] + 5.5, "REV %s" % REV, 2.8))
    s.append(txt(x0 + 42, rows[2][0] + 5.5, "SCALE %s" % scale_txt, 2.8))
    s.append(txt(x0 + 2, rows[3][0] + 5.0,
                 "BIOBUZZ FTC  |  %s  |  SHEET %d/%d  |  %s"
                 % (doc_tag, sheet_no, sheet_cnt,
                    meta["status"][:24]), 2.6))
    return "".join(s)


_NICE_SHRINK = (1, 0.8, 0.5, 0.4, 0.25, 0.2, 0.1, 0.05, 0.02, 0.01)
_NICE_GROW = (1, 2, 5, 10)


def _nice_scale(raw):
    for s in _NICE_SHRINK:
        if s <= raw:
            return s
    g = 1
    for cand in _NICE_GROW:
        if cand <= raw:
            g = cand
    return g


def scale_text(s):
    # %g keeps fractional ratios honest (1/0.4 -> "1:2.5", not "1:2")
    return ("%g:1" % s) if s >= 1 else ("1:%g" % (1.0 / s))


# world-axis indexes each view's projected width/height read from
_VIEW_AXES = {"FRONT": (0, 2), "TOP": (0, 1), "RIGHT": (1, 2)}


def estimate_scale(shape):
    """Sheet scale predicted from the part's projected bboxes, same
    fit math compose_sheet_svg applies to real view extents. Close
    enough for the in-document template's SCALE field."""
    b = shape.BoundBox
    d = (b.XLength, b.YLength, b.ZLength)
    fit = float("inf")
    for vn, *_ in VIEWS:
        w = max(d[_VIEW_AXES[vn][0]], 0.1)
        h = max(d[_VIEW_AXES[vn][1]], 0.1)
        cx0, cy0, cx1, cy1 = VIEW_CELLS[vn]
        fit = min(fit, (cx1 - cx0 - 16) / w, (cy1 - cy0 - 28) / h)
    return _nice_scale(fit if fit != float("inf") else 1.0)


def compose_sheet_svg(part_svg_by_view, extents, meta, doc_tag, qty):
    """Compose the A4 sheet: frame, three scaled views, extent-dimension
    callouts on each view, view captions, title block, notes strip."""
    scale = float("inf")
    for vn, *_ in VIEWS:
        ex = extents.get(vn)
        if not ex:
            continue
        w = max(ex[1] - ex[0], 0.1)
        h = max(ex[3] - ex[2], 0.1)
        cx0, cy0, cx1, cy1 = VIEW_CELLS[vn]
        # each cell keeps ~8 mm side margins and ~20 mm at its bottom
        # for the extent-dim callout plus the view caption
        fit = min((cx1 - cx0 - 16) / w, (cy1 - cy0 - 28) / h)
        scale = min(scale, fit)
    if scale == float("inf"):
        scale = 1.0
    scale = _nice_scale(scale)
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="297mm" '
        'height="210mm" viewBox="0 0 297 210">',
        '<rect x="0" y="0" width="297" height="210" fill="#ffffff"/>',
        '<rect x="6" y="6" width="285" height="198" fill="none" '
        'stroke="#000" stroke-width="0.5"/>',
    ]
    for vn, *_ in VIEWS:
        svg_g = part_svg_by_view.get(vn)
        ex = extents.get(vn)
        if not svg_g or not ex:
            continue
        x0, y0, x1, y1 = VIEW_CELLS[vn]
        uw, uh = ex[1] - ex[0], ex[3] - ex[2]
        # center of the part in view coords -> center of its cell
        cu, cv = (ex[0] + ex[1]) / 2.0, (ex[2] + ex[3]) / 2.0
        tx, ty = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        out.append('<g transform="translate(%.2f %.2f) scale(%.4f %.4f)">'
                   % (tx, ty, scale, -scale))
        out.append(svg_g)
        out.append("</g>")
        # dimensioned extents: horizontal below view, vertical left
        su0 = tx + (ex[0] - cu) * scale
        su1 = tx + (ex[1] - cu) * scale
        sv0 = ty - (ex[3] - cv) * scale   # v grows up -> y flips
        sv1 = ty - (ex[2] - cv) * scale
        out.append(_dim_h(su0, su1, sv1 + DIM_GAP + 3.2,
                          _fmt(uw)))
        out.append(_dim_v(su0 - DIM_GAP - 4.2, sv0, sv1, _fmt(uh)))
        # caption inside the cell's bottom edge: the RIGHT cell shares
        # its lower band with the title block, so captions cannot go
        # below the cell
        out.append('<text x="%.1f" y="%.1f" font-size="3.4" '
                   'font-family="sans-serif" fill="#000" '
                   'text-anchor="middle">%s</text>'
                   % (tx, y1 - 2.6, VIEW_LABEL[vn]))
    # notes strip (bottom-left region)
    ny = 196.0
    out.append('<text x="10" y="%.1f" font-size="2.8" '
               'font-family="sans-serif" fill="#333">%s  |  %s  |  '
               'views carry overall extent callouts</text>'
               % (ny, UNITS_NOTE, PROJ_NOTE))
    out.append('<text x="10" y="%.1f" font-size="2.8" '
               'font-family="sans-serif" fill="#8a2b2b">%s</text>'
               % (ny + 4.2, DISCLAIMER))
    out.append(_title_block(meta, doc_tag, qty, scale_text(scale),
                            meta.get("_sheet_no", 1),
                            meta.get("_sheet_cnt", 1)))
    out.append("</svg>")
    return "".join(out), scale


def write_pdf(svg_text, pdf_path):
    """SVG -> vector PDF via QtSvg + QPdfWriter (headless-safe)."""
    from PySide6 import QtGui, QtSvg, QtCore  # noqa: delayed Qt import
    QtCore.QCoreApplication.instance() or QtGui.QGuiApplication([])
    r = QtSvg.QSvgRenderer(QtCore.QByteArray(svg_text.encode("utf-8")))
    if not r.isValid():
        raise RuntimeError("QSvgRenderer rejected sheet SVG")
    pw = QtGui.QPdfWriter(str(pdf_path))
    pw.setPageSize(QtGui.QPageSize(QtGui.QPageSize.PageSizeId.A4))
    pw.setPageOrientation(QtGui.QPageLayout.Orientation.Landscape)
    pw.setResolution(96)
    p = QtGui.QPainter(pw)
    r.render(p)
    p.end()
