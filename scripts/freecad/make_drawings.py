"""make_drawings.py -- engineering-drawing exporter (BIOBUZZ rehaul).

Opens every subsystem FCStd (and the master), finds each document's
exportable parts the same way export_step.py does, groups identical
geometry, then emits per unique part:

  exports/drawings/<doc>_<part>.pdf  - A4 landscape sheet: front/top/
                                     right TechDraw views, overall
                                     extent-dimension callouts, title
                                     block (part, material, qty, rev)
  exports/drawings/<doc>_<part>.svg  - same sheet, editable vector
  exports/drawings/dxf/<doc>_<part>.dxf
                                   - flat profile for plate-like parts
                                     (deck/base/cheek/bracket geometry)

  exports/drawings/manifest.json    - machine-readable per-part report

Fully parameter-driven: part lists come from the documents, not a
hardcoded manifest, so re-running after a geometry change produces the
updated set.

Usage (freecadcmd does not forward argv to the script, so selection is
by environment variable):
  DRAWINGS_DOCS=drivebase,master_robot  limit to these docs
                                        (default: all that exist)
  DRAWINGS_PLATES_ONLY=1                sheets only for flat plates
  DRAWINGS_MAX=N                        cap sheets per doc (smoke test)

Run:  freecadcmd scripts/freecad/make_drawings.py
"""
import json
import os
import re
import sys
import traceback
from pathlib import Path

import FreeCAD as App

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drawing_kit as dk  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad"
OUT = ROOT / "exports" / "drawings"
DXF_DIR = OUT / "dxf"
BOM_CSV = ROOT / "exports" / "bom" / "bom.csv"

DOCS = {
    "drivebase": CAD / "drivebase" / "drivebase.FCStd",
    "electronics": CAD / "electronics" / "electronics.FCStd",
    "hopper": CAD / "hopper" / "hopper.FCStd",
    "intake": CAD / "intake" / "intake.FCStd",
    "lift": CAD / "lift" / "lift.FCStd",
    "turret": CAD / "turret" / "turret.FCStd",
    "master_robot": CAD / "master_robot.FCStd",
}


def parse_env():
    docs = [d.strip() for d in
            os.environ.get("DRAWINGS_DOCS", "").split(",") if d.strip()]
    plates_only = os.environ.get("DRAWINGS_PLATES_ONLY", "") \
        not in ("", "0", "false", "no")
    max_n = os.environ.get("DRAWINGS_MAX", "").strip()
    return docs, plates_only, int(max_n) if max_n else None


def safe_name(name):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def sheet_one(doc, doc_tag, group, meta_fields, out_dir, dxf_dir):
    """One unique part -> sheet PDF+SVG (+ DXF when plate-like)."""
    o = group["objects"][0]
    shape = group["shape"]
    names = [x.Name for x in group["objects"]]
    tag = "%s_%s" % (doc_tag, safe_name(o.Name))
    meta = dk.part_meta(o, meta_fields)
    meta["_names"] = names
    meta["_sheet_no"] = group.get("_sheet_no", 1)
    meta["_sheet_cnt"] = group.get("_sheet_cnt", 1)
    plate = dk.is_plate(o.Name, shape)

    page = views = None
    svg_groups, extents = {}, {}
    try:
        fields = {"PART_NAME": dk.family_name(names)
                  if len(names) > 1 else meta["label"][:60],
                  "MATERIAL": meta["material"], "SPEC": meta["spec"],
                  "QTY": str(len(names)), "REV": dk.REV,
                  "SCALE": dk.scale_text(dk.estimate_scale(shape)),
                  "SHEET": "%d/%d" % (meta["_sheet_no"],
                                      meta["_sheet_cnt"]),
                  "DOC": doc_tag, "STATUS": meta["status"]}
        page, views = dk.make_page(doc, o, tag, fields)
        for vn, *_ in dk.VIEWS:
            v = views[vn]
            svg_groups[vn] = dk.view_edges_svg(v)
            extents[vn] = dk.view_extent(v)
    finally:
        if page is not None:
            dk.remove_page(doc, page)

    sheet_svg, scale = dk.compose_sheet_svg(
        svg_groups, extents, meta, doc_tag, len(names))
    svg_path = out_dir / ("%s.svg" % tag)
    pdf_path = out_dir / ("%s.pdf" % tag)
    svg_path.write_text(sheet_svg, encoding="utf-8")
    dk.write_pdf(sheet_svg, pdf_path)

    dxf_path = None
    if plate:
        dxf_dir.mkdir(parents=True, exist_ok=True)
        dxf_path = dxf_dir / ("%s.dxf" % tag)
        dxf_path.write_text(dk.flat_profile_dxf(shape),
                            encoding="utf-8")
    return meta, plate, svg_path, pdf_path, dxf_path, scale


def process_doc(doc_tag, fcstd_path, bom, plates_only, max_n, log):
    doc = App.openDocument(str(fcstd_path))
    doc.recompute()
    objs = dk.exportable(doc)
    groups = dk.group_identical(objs)
    todo = [g for g in groups
            if not plates_only
            or dk.is_plate(g["objects"][0].Name, g["shape"])]
    if max_n is not None:
        todo = todo[:max_n]
    entries = []
    for made, g in enumerate(todo):
        o = g["objects"][0]
        g["_sheet_no"] = made + 1
        g["_sheet_cnt"] = len(todo)
        try:
            meta, plate, svg, pdf, dxf, scale = sheet_one(
                doc, doc_tag, g, bom, OUT, DXF_DIR)
            b = g["shape"].BoundBox
            entries.append({
                "doc": doc_tag, "part": o.Name,
                "instances": [x.Name for x in g["objects"]],
                "qty": len(g["objects"]),
                "label": meta["label"], "material": meta["material"],
                "status": meta["status"], "plate": plate,
                "bbox_mm": [round(b.XLength, 2), round(b.YLength, 2),
                            round(b.ZLength, 2)],
                "scale": scale,
                "sheet_svg": str(svg.relative_to(ROOT)),
                "sheet_pdf": str(pdf.relative_to(ROOT)),
                "dxf": str(dxf.relative_to(ROOT)) if dxf else None,
            })
            line = ("%s | %-28s qty=%-3d plate=%-5s %sx%sx%s -> %s"
                    % (doc_tag, o.Name[:28], len(g["objects"]), plate,
                       round(b.XLength, 1), round(b.YLength, 1),
                       round(b.ZLength, 1), svg.name))
            print(line)
            sys.stdout.flush()
            log.append(line)
        except Exception as e:
            line = "%s | %-28s FAILED %r" % (doc_tag, o.Name, e)
            print(line)
            sys.stdout.flush()
            log.append(line)
            entries.append({"doc": doc_tag, "part": o.Name,
                            "error": repr(e)})
    App.closeDocument(doc.Name)
    return entries


def main():
    docs_filter, plates_only, max_n = parse_env()
    OUT.mkdir(parents=True, exist_ok=True)
    DXF_DIR.mkdir(parents=True, exist_ok=True)
    # drop stale outputs so parts that disappeared or stopped
    # qualifying as plates do not leave orphan manufacturing files
    for stale in list(OUT.glob("*.pdf")) + list(OUT.glob("*.svg")) \
            + list(DXF_DIR.glob("*.dxf")):
        stale.unlink()
    bom = dk.load_bom(BOM_CSV)
    manifest = {"generated_by": "make_drawings.py", "docs": {},
                "parts": []}
    log = []
    for tag, path in DOCS.items():
        if docs_filter and tag not in docs_filter:
            continue
        if not path.exists():
            line = "%s | MISSING %s" % (tag, path)
            print(line)
            log.append(line)
            continue
        entries = process_doc(tag, path, bom, plates_only, max_n, log)
        manifest["docs"][tag] = {
            "fcstd": str(path.relative_to(ROOT)),
            "parts": len(entries),
            "plates": sum(1 for e in entries if e.get("plate")),
            "errors": sum(1 for e in entries if "error" in e),
        }
        manifest["parts"] += entries
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    (OUT / "manifest.txt").write_text("\n".join(log) + "\n",
                                    encoding="utf-8")
    n_err = sum(d.get("errors", 0) for d in manifest["docs"].values())
    print("DRAWINGS: docs=%d parts=%d dxf=%d errors=%d -> %s"
          % (len(manifest["docs"]), len(manifest["parts"]),
             sum(1 for e in manifest["parts"] if e.get("dxf")),
             n_err, OUT))
    sys.stdout.flush()
    # an incomplete run is a failed run: batch jobs read the exit code
    sys.exit(1 if n_err else 0)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)
