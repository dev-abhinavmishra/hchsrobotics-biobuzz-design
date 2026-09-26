# BIOBUZZ prototype export manifest

**PROTOTYPE / VERIFY BEFORE MANUFACTURING**

Every artifact listed here is placeholder-grade prototype geometry
for packaging review. NOT manufacturing data. All assumed values
are UNVERIFIED or VENDOR-PENDING (see `docs/robot-parameters.md`).

## Artifacts

- `prototype_stl/master_robot_PROTOTYPE.stl` - PROTOTYPE / VERIFY BEFORE MANUFACTURING
- `prototype_step/master_robot_PROTOTYPE.step` - PROTOTYPE / VERIFY BEFORE MANUFACTURING
- `renders/master_{front,side,top,iso}.svg` - PROTOTYPE / VERIFY BEFORE MANUFACTURING

## Export set (127 solids, units mm)

Robot leaf solids from `cad/master_robot.FCStd` only. Excluded:
`ENV_*`/`AXIS_*`/`REF_*` non-physical references, `VOL_*`
packaging reserves, `TOOL_*` construction intermediates, and
`App::Part`/`App::Origin` containers. Shapes are exported in
world coordinates (carrier-chain placements applied).

- `BATTERY`
- `BEARING_FL`
- `BEARING_FR`
- `BEARING_RL`
- `BEARING_RR`
- `BELLY_PAN`
- `CHANNEL_FLOOR`
- `CHANNEL_SUPP_B`
- `CHANNEL_SUPP_F`
- `CHANNEL_WALL_L`
- `CHANNEL_WALL_R`
- `CRADLE_LIP`
- `DIVERTER_AXLE`
- `DIVERTER_BUSH_L`
- `DIVERTER_BUSH_R`
- `DIVERTER_HORN`
- `DIVERTER_PADDLE`
- `DIVERTER_SERVO`
- `ELECTRONICS`
- `ELEC_RAIL_L`
- `ELEC_RAIL_R`
- `FRAME_RAIL_B`
- `FRAME_RAIL_F`
- `FRAME_RAIL_L`
- `FRAME_RAIL_R`
- `INTAKE_AXLE_L`
- `INTAKE_AXLE_R`
- `INTAKE_BEARING_L`
- `INTAKE_BEARING_R`
- `INTAKE_CHEEK_L`
- `INTAKE_CHEEK_R`
- `INTAKE_LIP`
- `INTAKE_MOTOR`
- `INTAKE_MOTOR_BRKT`
- `INTAKE_MOUNT_L`
- `INTAKE_MOUNT_R`
- `INTAKE_ROLLER`
- `INTAKE_ROLLER_SHAFT`
- `LIFTER_BASE`
- `LIFTER_PED`
- `MECH_CARRIAGE`
- `MECH_CRADLE`
- `MECH_FLYWHEEL_L`
- `MECH_FLYWHEEL_R`
- `MECH_LIFTER_STOWED`
- `MECH_SHOOTER_BODY`
- `MECH_SHOOTER_HOOD`
- `MECH_STAGE_1`
- `MECH_STAGE_2`
- `MECH_STAGE_3`
- `MOTOR_FL`
- `MOTOR_FR`
- `MOTOR_RL`
- `MOTOR_RR`
- `MOUNT_MOTOR_FL`
- `MOUNT_MOTOR_FR`
- `MOUNT_MOTOR_RL`
- `MOUNT_MOTOR_RR`
- `PIVOT_MOUNT_L`
- `PIVOT_MOUNT_R`
- `POST_SHOOTER_L`
- `POST_SHOOTER_R`
- `REAR_DECK_L`
- `REAR_DECK_R`
- `ROLLER_FL_00_B`
- `ROLLER_FL_01_B`
- `ROLLER_FL_02_B`
- `ROLLER_FL_03_B`
- `ROLLER_FL_04_B`
- `ROLLER_FL_05_B`
- `ROLLER_FL_06_B`
- `ROLLER_FL_07_B`
- `ROLLER_FL_08_B`
- `ROLLER_FL_09_B`
- `ROLLER_FR_00_B`
- `ROLLER_FR_01_B`
- `ROLLER_FR_02_B`
- `ROLLER_FR_03_B`
- `ROLLER_FR_04_B`
- `ROLLER_FR_05_B`
- `ROLLER_FR_06_B`
- `ROLLER_FR_07_B`
- `ROLLER_FR_08_B`
- `ROLLER_FR_09_B`
- `ROLLER_RL_00_B`
- `ROLLER_RL_01_B`
- `ROLLER_RL_02_B`
- `ROLLER_RL_03_B`
- `ROLLER_RL_04_B`
- `ROLLER_RL_05_B`
- `ROLLER_RL_06_B`
- `ROLLER_RL_07_B`
- `ROLLER_RL_08_B`
- `ROLLER_RL_09_B`
- `ROLLER_RR_00_B`
- `ROLLER_RR_01_B`
- `ROLLER_RR_02_B`
- `ROLLER_RR_03_B`
- `ROLLER_RR_04_B`
- `ROLLER_RR_05_B`
- `ROLLER_RR_06_B`
- `ROLLER_RR_07_B`
- `ROLLER_RR_08_B`
- `ROLLER_RR_09_B`
- `SHAFT_FL`
- `SHAFT_FR`
- `SHAFT_RL`
- `SHAFT_RR`
- `SHOOTER_FLOOR`
- `SHOOTER_SIDE_L`
- `SHOOTER_SIDE_R`
- `STAGE_GUIDE_L`
- `STAGE_GUIDE_R`
- `STUB_SHAFT_L`
- `STUB_SHAFT_R`
- `WHEEL_HUB_FL`
- `WHEEL_HUB_FR`
- `WHEEL_HUB_RL`
- `WHEEL_HUB_RR`
- `WHEEL_PLATE_FL_IN`
- `WHEEL_PLATE_FL_OUT`
- `WHEEL_PLATE_FR_IN`
- `WHEEL_PLATE_FR_OUT`
- `WHEEL_PLATE_RL_IN`
- `WHEEL_PLATE_RL_OUT`
- `WHEEL_PLATE_RR_IN`
- `WHEEL_PLATE_RR_OUT`

## Validation

- STL facets: 174216
- STL bbox: (-210.0, -195.0, -0.0) - (228.6, 195.0, 640.0)
- STEP re-import solids: 130

Regenerate with:

    "C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" scripts\freecad\export_prototypes.py
