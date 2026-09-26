"""Headless shaded PNG renders of the BIOBUZZ master assembly.

Companion to render_views.py: same exportable object set, same views,
same subsystem palette -- but rasterized through a real z-buffer instead
of painter's-algorithm SVG, so interpenetrating solids occlude
correctly and the image looks like an actual shaded view rather than
wireframe soup. Visible (silhouette/sharp) edges are overlaid as thin
dark lines. PNGs are written without any external dependency (zlib
only). Output is an honest preview of placeholder geometry.

Run:  freecadcmd.exe scripts/freecad/render_png.py
All paths resolve relative to this file (project_root/scripts/freecad/).
"""
import math
import struct
import sys
import traceback
import zlib
from pathlib import Path

import numpy as np

import FreeCAD as App

try:
    from PIL import Image, ImageDraw, ImageFont
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "cad" / "master_robot.FCStd"
DRIVEBASE = ROOT / "cad" / "drivebase" / "drivebase.FCStd"
ELECTRONICS = ROOT / "cad" / "electronics" / "electronics.FCStd"
OUT_DIR = ROOT / "exports" / "renders"
EXCLUDE_PREFIX = ("ENV_", "AXIS_", "REF_", "VOL_", "TOOL_")
EXCLUDE_TYPES = ("App::Part", "App::Origin")

IMG_W, IMG_H = 1600, 1100
MARGIN = 30
BG = (250, 250, 247)

SUBSYS = (
    (("FRAME_", "RAIL_", "BELLY_PAN", "PAN_BRKT_", "TIE_", "GUSSET_",
      "ENDCAP_", "CROWN_POST_", "PLATE_NUM_", "DECK_"), "#8b9199"),
    (("WHEEL_HUB_", "WHEEL_PLATE_", "ROLLER_", "WHEEL_ASSY_"),
     "#3a3a40"),
    (("AXLE_", "BRG_", "COLLAR_", "WASHER_", "WSH_", "PINION_",
      "NUT_AXLE_", "MOUNT_PLATE_"), "#b8bfc8"),
    (("MOTOR_", "CLAMP_"), "#d9a520"),
    (("ODO_",), "#2f6fd6"),
    (("BATTERY", "BATT_STRAP"), "#2f9e5f"),
    (("HUB_", "ELEC_SHELF", "STANDOFF_", "SWITCH_", "MAIN_SWITCH"),
     "#e8890c"),
    (("WIRE_", "CLIP_", "ZIP_", "CONN_"), "#c23b3b"),
    (("BOLT_", "NUT_", "SCRW_", "RIVNUT_"), "#777788"),
)
OTHER = "#7a7a80"


def subsystem(name):
    for prefixes, color in SUBSYS:
        if name.startswith(prefixes):
            return color
    return OTHER


def norm(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / n, v[1] / n, v[2] / n)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


SQ = 1.0 / math.sqrt(3.0)
VIEWS = {
    "front": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "side": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "top": ((1, 0, 0), (0, 1, 0), (0, 0, -1)),
    "iso": (norm(cross((0, 0, 1), (SQ, SQ, SQ))),
            norm(cross((SQ, SQ, SQ), cross((0, 0, 1), (SQ, SQ, SQ)))),
            (SQ, SQ, SQ)),
}


def _consumed(doc):
    out = set()

    def add(x):
        if x is None or x.Name in out:
            return
        out.add(x.Name)
        for p in ("Links", "Group"):
            g = getattr(x, p, None)
            if g is None:
                continue
            for y in (g if isinstance(g, (list, tuple)) else (g,)):
                add(y)

    for o in doc.Objects:
        if o.TypeId in ("Part::Fuse", "Part::Cut", "Part::Chamfer",
                        "Part::Common", "Part::MultiFuse"):
            for p in ("Base", "Tool", "Shapes"):
                t = getattr(o, p, None)
                if t is None:
                    continue
                for x in (t if isinstance(t, (list, tuple)) else (t,)):
                    add(x)
    return out


def exportable(doc):
    out = []
    consumed = _consumed(doc)
    for o in doc.Objects:
        if o.Name in consumed:
            continue
        if not hasattr(o, "Shape") or o.TypeId in EXCLUDE_TYPES \
                or o.Name.startswith(EXCLUDE_PREFIX):
            continue
        if o.Shape.isNull() or o.Shape.Volume <= 0:
            continue
        # globalized copy: carrier children carry their group's
        # placement chain (App::Part transforms are not in .Shape)
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        out.append((o.Name, s))
    return out


def visible_edges(shape, w):
    """Silhouette + sharp-front edges only (same rule as the SVG pass)."""
    edge_map = {}
    for f in shape.Faces:
        for e in f.Edges:
            key = e.hashCode() if hasattr(e, "hashCode") else id(e)
            edge_map.setdefault(key, []).append((e, f))
    polys = []
    for lst in edge_map.values():
        e = lst[0][0]
        draw = True
        try:
            norms = [f.normalAt(*f.Surface.parameter(e.CenterOfMass))
                     for _e, f in lst]
            front = [n.x * w[0] + n.y * w[1] + n.z * w[2] > 0.0
                     for n in norms]
            if len(norms) >= 2:
                if front[0] != front[1]:
                    draw = True
                elif front[0] and front[1]:
                    dd = (norms[0].x * norms[1].x + norms[0].y * norms[1].y
                          + norms[0].z * norms[1].z)
                    draw = dd < 0.90
                else:
                    draw = False
            else:
                draw = front[0]
        except Exception:
            draw = True
        if not draw:
            continue
        ds = e.discretize(QuasiDeflection=0.3)
        if len(ds) >= 2:
            polys.append(ds)
    return polys


def collect(objs, u, v, w):
    """Project tessellated triangles + visible edges to view space."""
    tris = []   # (u0,v0,d0, u1,v1,d1, u2,v2,d2, r,g,b)
    lines = []  # ([(u,v,d),...])  -- d kept for depth-tested overlay
    for name, shape in objs:
        color_hex = subsystem(name)
        cr, cg, cb = (int(color_hex[i:i + 2], 16) for i in (1, 3, 5))
        verts, faces = shape.tessellate(0.5)
        for f in faces:
            p = [verts[i] for i in f]
            n = norm(cross((p[1][0] - p[0][0], p[1][1] - p[0][1],
                           p[1][2] - p[0][2]),
                           (p[2][0] - p[0][0], p[2][1] - p[0][1],
                            p[2][2] - p[0][2])))
            light = abs(n[0] * w[0] + n[1] * w[1] + n[2] * w[2])
            shade = 0.5 + 0.5 * light
            col = (int(cr * shade), int(cg * shade), int(cb * shade))
            tris.append(tuple(
                coord for pp in p
                for coord in (pp[0] * u[0] + pp[1] * u[1] + pp[2] * u[2],
                              pp[0] * v[0] + pp[1] * v[1] + pp[2] * v[2],
                              -(pp[0] * w[0] + pp[1] * w[1] + pp[2] * w[2]))
            ) + col)
        for ds in visible_edges(shape, w):
            lines.append([(pp[0] * u[0] + pp[1] * u[1] + pp[2] * u[2],
                           pp[0] * v[0] + pp[1] * v[1] + pp[2] * v[2],
                           -(pp[0] * w[0] + pp[1] * w[1] + pp[2] * w[2]))
                          for pp in ds])
    return tris, lines


def raster(tris, lines):
    """Z-buffer rasterization: correct occlusion even for intersecting
    solids. depth stored negated so nearer = larger."""
    us = [t[i * 3] for t in tris for i in range(3)]
    vs = [t[i * 3 + 1] for t in tris for i in range(3)]
    u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    scale = min((IMG_W - 2 * MARGIN) / (u1 - u0),
                (IMG_H - 2 * MARGIN) / (v1 - v0))
    ox = (IMG_W - (u1 - u0) * scale) / 2 - u0 * scale
    oy = (IMG_H - (v1 - v0) * scale) / 2 - v0 * scale

    def px(uu, vv):
        return uu * scale + ox, IMG_H - (vv * scale + oy)  # flip v

    img = np.empty((IMG_H, IMG_W, 3), dtype=np.uint8)
    img[:, :] = BG
    zbuf = np.full((IMG_H, IMG_W), -np.inf)

    for t in tris:
        x0, y0 = px(t[0], t[1])
        x1, y1 = px(t[3], t[4])
        x2, y2 = px(t[6], t[7])
        xmin = max(int(min(x0, x1, x2)), 0)
        xmax = min(int(max(x0, x1, x2)) + 1, IMG_W - 1)
        ymin = max(int(min(y0, y1, y2)), 0)
        ymax = min(int(max(y0, y1, y2)) + 1, IMG_H - 1)
        if xmin > xmax or ymin > ymax:
            continue
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            continue
        xs = np.arange(xmin, xmax + 1)
        ys = np.arange(ymin, ymax + 1)
        XX, YY = np.meshgrid(xs, ys)
        a = ((y1 - y2) * (XX - x2) + (x2 - x1) * (YY - y2)) / den
        b = ((y2 - y0) * (XX - x2) + (x0 - x2) * (YY - y2)) / den
        c = 1.0 - a - b
        mask = (a >= 0) & (b >= 0) & (c >= 0)
        if not mask.any():
            continue
        dd = a * t[2] + b * t[5] + c * t[8]
        sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        upd = mask & (dd > sub)
        sub[upd] = dd[upd]
        img[ymin:ymax + 1, xmin:xmax + 1][upd] = (t[9], t[10], t[11])

    # visible-edge overlay, 1 px dark lines -- depth-tested against the
    # triangle z-buffer (edge bias = tessellation deflection + epsilon)
    EDGE_BIAS = 0.6
    for ln in lines:
        pts = [(px(uu, vv), dd) for uu, vv, dd in ln]
        for (p0, d0), (p1, d1) in zip(pts, pts[1:]):
            xa, ya = p0
            xb, yb = p1
            n = int(max(abs(xb - xa), abs(yb - ya))) + 1
            if n > 4000:
                continue
            lx = np.linspace(xa, xb, n).astype(int)
            ly = np.linspace(ya, yb, n).astype(int)
            ld = np.linspace(d0, d1, n)
            ok = (lx >= 0) & (lx < IMG_W) & (ly >= 0) & (ly < IMG_H)
            lx, ly, ld = lx[ok], ly[ok], ld[ok]
            vis = ld > zbuf[ly, lx] - EDGE_BIAS
            img[ly[vis], lx[vis]] = (30, 30, 38)
    return img


def annotate(img, tag, view):
    """Title + PROTOTYPE watermark strip (matches the SVG labeling)."""
    if not HAVE_PIL:
        return img
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    try:
        f_big = ImageFont.load_default(size=34)
        f_small = ImageFont.load_default(size=22)
    except TypeError:  # older PIL: fixed-size default font
        f_big = f_small = ImageFont.load_default()
    # header strip
    d.rectangle([0, 0, IMG_W, 52], fill=(245, 245, 242))
    d.text((14, 10), "BIOBUZZ %s -- %s view" % (tag, view),
           fill=(30, 30, 38), font=f_big)
    # footer watermark
    d.rectangle([0, IMG_H - 44, IMG_W, IMG_H], fill=(245, 235, 225))
    d.text((14, IMG_H - 36),
           "PROTOTYPE / VERIFY BEFORE MANUFACTURING -- placeholder "
           "geometry, not a drawing", fill=(140, 40, 30), font=f_small)
    return np.asarray(im)


def write_png(path, img):
    h, w, _ = img.shape
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6))
           + chunk(b"IEND", b""))
    Path(path).write_bytes(png)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log = []
    for src, tag in ((MASTER, "master"), (DRIVEBASE, "drivebase"),
                     (ELECTRONICS, "electronics")):
        doc = App.openDocument(str(src))
        doc.recompute()
        objs = exportable(doc)
        for view, (u, v, w) in VIEWS.items():
            tris, lines = collect(objs, u, v, w)
            img = annotate(raster(tris, lines), tag, view)
            path = OUT_DIR / ("%s_%s.png" % (tag, view))
            write_png(path, img)
            msg = "PNG: %s tris=%d edges=%d -> %s" % (
                view, len(tris), len(lines), path.name)
            print(msg)
            sys.stdout.flush()
            log.append(msg)
        App.closeDocument(doc.Name)
    with open(OUT_DIR / "render_log.txt", "a", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\n")
    print("PNG: DONE")
    sys.stdout.flush()


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
