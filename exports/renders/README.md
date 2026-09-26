# exports/renders — BIOBUZZ-Robot

Rendered previews of the placeholder master assembly:

- `master_{front,side,top,iso}.svg` — shaded vector renders
  (`render_views.py`): painted facets, per-subsystem colors,
  silhouette/sharp-edge overlay, legend.
- `master_{front,side,top,iso}.png` — shaded raster renders
  (`render_png.py`): z-buffered so interpenetrating solids occlude
  correctly; same palette and views as the SVGs.
- `fc_screenshot.png` — reference capture of the styled GUI view
  (`cad/master_robot_view.FCStd`, produced by `make_view_copy.py`).
- `render_log.txt`, `view_log.txt` — script run logs.

Every file in this folder is prototype material:
**PROTOTYPE / VERIFY BEFORE MANUFACTURING**
