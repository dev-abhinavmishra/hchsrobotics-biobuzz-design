# Coordinate system — BIOBUZZ-Robot

One convention shared by every FCStd in this repository and by all
documentation.

## Origin and ground plane

- **Origin (0,0,0)** sits at the **center of the robot footprint on the tile
  surface**.
- **Z = 0 is the tile top face** (the ground plane the robot sits on).

## Axes

- **+X** — robot forward direction.
- **+Y** — robot left.
- **+Z** — up (away from the tiles).

Right-handed frame: X cross Y = Z.

## How the convention appears in the models

- `ENV_START` (the 457.2 mm start cube, R102) is centered on the XY origin and
  its base sits at Z = 0 — the robot must fit inside it before a match.
- `ENV_EXPANSION` (457.2 × 609.6 × 736.5 mm, R105) is also centered on XY with
  its base at Z = 0 and its height along +Z, matching the rule that the
  736.5 mm dimension stays vertical.
- Wheel placeholders stand on the ground: `BoundBox.ZMin` ≈ 0 because their
  centers are placed at `Z = wheel_dia / 2`.
- The `COORD_REF` App::Part in `master_robot.FCStd` contains three thin
  axis-indicator solids (`AXIS_X`, `AXIS_Y`, `AXIS_Z`) that emanate from the
  world origin along +X, +Y, +Z so the frame is visible inside the model;
  each `App::Part` also keeps its FreeCAD `Origin` feature.
- Mirrored placements use signed expressions: front/right wheels at
  `+wheel_x_offset` / `−wheel_y_offset` bases, etc., so symmetry is explicit.

## Why this convention

Centering the origin on the footprint makes the four mirrored wheel/motor
quadrants symmetric (±a, ±b), and putting Z = 0 on the tile makes "does it
touch the ground" checks read directly off BoundBox values. See
`docs/robot-parameters.md` for the bound values that place geometry in this
frame.
