import sys, math
sys.path.insert(0, r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad")
import FreeCAD as App
from dt_lift import CHUTE_PTS, _frame_for
import FreeCAD
p0, p1, p2 = CHUTE_PTS
import FreeCAD as A
def vec(*a): return A.Vector(*a)
d1, w1, n1, L1 = _frame_for(p0, p1)
d2, w2, n2, L2 = _frame_for(p1, p2)
S17 = (-122, 128.5, 143)
def dist(pt, c):
    return math.sqrt(sum((pt[i]-c[i])**2 for i in range(3)))
# screw pts: p_s + d*(L*t) + w*(47 or -47) + n*18 ; side L => +47, R => -47
for tag, ps, d_, w_, n_, L_, woff in (
    ("L1", p0, d1, w1, n1, L1, 47), ("L2", p1, d2, w2, n2, L2, 47),
    ("R1", p0, d1, w1, n1, L1, -47), ("R2", p1, d2, w2, n2, L2, -47)):
    print(tag, "len", round(L_,1))
    for t in (0.05, 0.15, 0.3, 0.5, 0.7, 0.85, 0.95):
        pt = A.Vector(*ps) + d_*(L_*t) + w_*woff + n_*18
        print("  t=%.2f pt=(%.1f,%.1f,%.1f) dS17=%.1f" % (t, pt.x, pt.y, pt.z, dist((pt.x,pt.y,pt.z), S17)))
