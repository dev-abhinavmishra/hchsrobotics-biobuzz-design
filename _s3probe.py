import sys
sys.path.insert(0, r'C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad')
import FreeCAD as App

doc = App.openDocument(
    r'C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\master_robot.FCStd')
doc.recompute()

for n in ('DECK_L', 'DECK_R', 'FRAME_RAIL_L', 'FRAME_RAIL_R',
          'FEED_COLUMN', 'COL_FLANGE', 'HOP_WALL_L', 'HOP_WALL_R',
          'INT_CHEEK_L', 'INT_CHEEK_R', 'BELLY_PAN', 'ELEC_SHELF',
          'AXIS_TURRET', 'REF_DECK_IFACE', 'REF_DIV_PORT',
          'GATE_SERVO', 'DIV_SERVO', 'AGIT_SERVO', 'PORT_FLANGE',
          'HUB_CTRL', 'HUB_EXP'):
    o = doc.getObject(n)
    if o is None:
        print(n, 'MISSING')
        continue
    b = o.Shape.BoundBox
    print('%-16s x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]'
          % (n, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))
