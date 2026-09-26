"""Headless colored renders of the BIOBUZZ master assembly -> SVG.

freecadcmd has no GUI renderer, so this rasterizes nothing: it tessellates
each exported solid, projects the facets orthographically (front XZ /
side YZ / top XY / isometric az45 el35.264), paints them far-to-near
(painter's algorithm) with a per-subsystem fill color and a simple
directional shade, then overlays the discretized edges as wireframe.
Honest preview of placeholder geometry, labeled PROTOTYPE.

Run:  freecadcmd.exe scripts/freecad/render_views.py
All paths resolve relative to this file (project_root/scripts/freecad/).
"""
import math
import sys
import traceback
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "cad" / "master_robot.FCStd"
OUT_DIR = ROOT / "exports" / "renders"
EXCLUDE_PREFIX = ("ENV_", "AXIS_", "REF_", "VOL_", "TOOL_")
EXCLUDE_TYPES = ("App::Part", "App::Origin")
LABEL = "PROTOTYPE - placeholder geometry only / VERIFY BEFORE MANUFACTURING"
PAPER_W = 1400  # px canvas width; height follows true aspect ratio

# per-subsystem fill colors (name prefix -> hex)
SUBSYS = (
    (("FRAME_", "RAIL_", "BELLY_PAN", "REAR_DECK"), "#8b9199",
     "chassis frame+sheets"),
    (("WHEEL_", "ROLLER_"), "#3a3a40", "drivebase wheels+rollers"),
    (("SHAFT_", "BEARING_", "MOUNT_MOTOR_"), "#b8bfc8",
     "shafts/bearing/motor mounts"),
    (("MOTOR_",), "#d9a520", "drive motors"),
    (("BATTERY",), "#2f9e5f", "battery"),
    (("ELECTRONICS", "ELEC_RAIL"), "#e8890c", "electronics"),
    (("INTAKE_", "PIVOT_MOUNT", "MECH_INTAKE", "MECH_ROLLER"),
     "#2f6fd6", "intake"),
    (("CHANNEL_", "DIVERTER_", "MECH_CHANNEL", "MECH_DIVERTER"), "#2aa3a3", "transfer"),
    (("MECH_SHOOTER", "MECH_FLYWHEEL", "STUB_SHAFT", "POST_SHOOTER",
      "SHOOTER_FLOOR", "SHOOTER_SIDE"), "#c23b3b", "shooter"),
    (("MECH_LIFTER", "MECH_STAGE", "MECH_CARRIAGE", "MECH_CRADLE",
      "CRADLE_LIP", "STAGE_GUIDE", "LIFTER_BASE", "LIFTER_PED"),
     "#8a5fc0", "lifter"),
)


def subsystem(name):
    for prefixes, color, label in SUBSYS:
        if name.startswith(prefixes):
            return color, label
    return "#777777", "structure/other"


def norm(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / n, v[1] / n, v[2] / n)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


# view -> (u_vec, v_vec, depth_vec, note)
SQ = 1.0 / math.sqrt(3.0)
VIEWS = {
    "front": ((1, 0, 0), (0, 0, 1), (0, -1, 0),
              "orthographic front XZ (looking -Y)"),
    "side": ((0, 1, 0), (0, 0, 1), (1, 0, 0),
             "orthographic side YZ (looking +X)"),
    "top": ((1, 0, 0), (0, 1, 0), (0, 0, -1),
            "orthographic top XY (looking -Z)"),
    "iso": (norm(cross((0, 0, 1), (SQ, SQ, SQ))),
            norm(cross((SQ, SQ, SQ), cross((0, 0, 1), (SQ, SQ, SQ)))),
            (SQ, SQ, SQ),
            "isometric orthographic az=45deg el=35.264deg (atan(1/sqrt2))"),
}


def exportable(doc):
    out = []
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o.TypeId in EXCLUDE_TYPES \
                or o.Name.startswith(EXCLUDE_PREFIX):
            continue
        if o.Shape.isNull() or o.Shape.Volume <= 0:
            continue
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        out.append((o.Name, s))
    return out


def visible_edges(shape, w):
    """Edge polylines worth drawing: silhouette edges (one adjacent face
    front-facing, one back-facing) and sharp edges between two
    front-facing faces (dihedral > ~25 deg). Hidden, interior, and
    coplanar-seam edges are skipped -- drawing every edge of every solid
    was what made earlier renders look like buggy wireframe soup."""
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
                    draw = True  # silhouette
                elif front[0] and front[1]:
                    dd = (norms[0].x * norms[1].x + norms[0].y * norms[1].y
                          + norms[0].z * norms[1].z)
                    draw = dd < 0.90  # sharp edge between visible faces
                else:
                    draw = False  # back-facing edge
            else:
                draw = front[0]  # boundary edge
        except Exception:
            draw = True  # keep the edge rather than lose geometry
        if not draw:
            continue
        ds = e.discretize(QuasiDeflection=0.3)
        if len(ds) >= 2:
            polys.append(ds)
    return polys


def facets(objs, u, v, w):
    """[(depth, fill, [(u,v),..]), ...] + edge polylines for overlay."""
    tris = []
    edges = []
    for name, shape in objs:
        color, _grp = subsystem(name)
        verts, faces = shape.tessellate(0.5)
        for f in faces:
            p = [verts[i] for i in f]
            n = norm(cross((p[1][0] - p[0][0], p[1][1] - p[0][1],
                           p[1][2] - p[0][2]),
                           (p[2][0] - p[0][0], p[2][1] - p[0][1],
                            p[2][2] - p[0][2])))
            light = abs(n[0] * w[0] + n[1] * w[1] + n[2] * w[2])
            shade = 0.55 + 0.45 * light
            c = tuple(int(int(color[i:i + 2], 16) * shade)
                      for i in (1, 3, 5))
            fill = "#%02x%02x%02x" % c
            pts = [(pp[0] * u[0] + pp[1] * u[1] + pp[2] * u[2],
                    pp[0] * v[0] + pp[1] * v[1] + pp[2] * v[2])
                   for pp in p]
            dep = sum(pp[0] * w[0] + pp[1] * w[1] + pp[2] * w[2]
                      for pp in p) / 3.0
            tris.append((dep, fill, pts))
        for ds in visible_edges(shape, w):
            edges.append([(pp[0] * u[0] + pp[1] * u[1] + pp[2] * u[2],
                           pp[0] * v[0] + pp[1] * v[1] + pp[2] * v[2])
                          for pp in ds])
    tris.sort(key=lambda t: -t[0])  # far (high depth) drawn first
    return tris, edges


def render_svg(tris, edges, view, note, path):
    us = [p[0] for t in tris for p in t[2]]
    vs = [p[1] for t in tris for p in t[2]]
    u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    span_u, span_v = u1 - u0, v1 - v0
    scale = PAPER_W / span_u
    margin = 20
    legend_h = 20 * (len(SUBSYS) + 1) + 30
    h = int(span_v * scale) + 2 * margin + legend_h + 20

    def tx(p):
        return ("%.2f,%.2f" % ((p[0] - u0) * scale + margin,
                               (v1 - p[1]) * scale + margin))

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" '
             'width="%d" height="%d" viewBox="0 0 %d %d">'
             % (PAPER_W, h, PAPER_W, h),
             '<rect width="100%" height="100%" fill="#fbfbf8"/>']
    for _dep, fill, pts in tris:
        d = "M " + " L ".join(tx(p) for p in pts) + " Z"
        # facet edge in the same hue darkened: defines surfaces without
        # the old everything-wireframe noise
        r, g, b = (int(fill[i:i + 2], 16) for i in (1, 3, 5))
        edge_c = "#%02x%02x%02x" % (r * 3 // 5, g * 3 // 5, b * 3 // 5)
        parts.append('<path d="%s" fill="%s" stroke="%s" '
                     'stroke-width="0.3" stroke-opacity="0.45"/>'
                     % (d, fill, edge_c))
    for ln in edges:
        d = "M " + " L ".join(tx(p) for p in ln)
        parts.append('<path d="%s" fill="none" stroke="#14141c" '
                     'stroke-width="0.7" stroke-opacity="0.8"/>' % d)
    y0 = h - legend_h - 4
    parts.append('<text x="20" y="%d" font-family="monospace" '
                 'font-size="16" fill="#333">BIOBUZZ master_robot %s - %s'
                 '</text>' % (y0, view, note))
    parts.append('<text x="20" y="%d" font-family="monospace" '
                 'font-size="16" fill="#933">%s</text>' % (y0 + 20, LABEL))
    ly = y0 + 40
    for _pf, color, grp in SUBSYS:
        parts.append('<rect x="20" y="%d" width="14" height="14" '
                     'fill="%s" stroke="#333" stroke-width="0.5"/>'
                     % (ly - 11, color))
        parts.append('<text x="42" y="%d" font-family="monospace" '
                     'font-size="13" fill="#333">%s</text>' % (ly, grp))
        ly += 20
    parts.append("</svg>")
    Path(path).write_text("\n".join(parts) + "\n", encoding="utf-8")
    return len(tris), len(edges), span_u / span_v


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = App.openDocument(str(MASTER))
    doc.recompute()
    objs = exportable(doc)
    log = []
    for view, (u, v, w, note) in VIEWS.items():
        tris, edges = facets(objs, u, v, w)
        nt, ne, aspect = render_svg(tris, edges, view, note,
                                  OUT_DIR / ("master_%s.svg" % view))
        msg = ("RENDER: %s tris=%d edges=%d aspect=%.3f"
               % (view, nt, ne, aspect))
        print(msg)
        sys.stdout.flush()
        log.append(msg)
        if view == "iso":
            log.append("RENDER: iso projection az=45 el=35.264deg "
                       "(atan(1/sqrt2)) orthographic")
    App.closeDocument(doc.Name)
    (OUT_DIR / "render_log.txt").write_text("\n".join(log) + "\n",
                                            encoding="utf-8")
    print("RENDER: DONE")
    sys.stdout.flush()


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
