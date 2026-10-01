import FreeCAD as App, math
CHUTE_PTS = [(-66,56,204), (-96,115,168), (-127,178,140)]
def frame(p0,p1):
    d=App.Vector(p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2]); L=d.Length
    dx=App.Vector(d); dx.normalize()
    wy=App.Vector(0,0,1).cross(dx); wy.normalize()
    nz=dx.cross(wy); nz.normalize()
    return dx,wy,nz,L
d1,w1,n1,L1 = frame(CHUTE_PTS[0],CHUTE_PTS[1])
d2,w2,n2,L2 = frame(CHUTE_PTS[1],CHUTE_PTS[2])
print("L2",round(L2,2),"d2",[round(v,3) for v in (d2.x,d2.y,d2.z)],
      "w2",[round(v,3) for v in (w2.x,w2.y,w2.z)])
p1 = App.Vector(*CHUTE_PTS[1])
s17=App.Vector(-122,128.5,143); s16=App.Vector(-122.0,184.1,169.9)
for t in (0.6,0.7,0.8,0.85,0.9,0.95,1.0,1.05,1.1):
    pt = p1 + d2*(L2*t) + w2*47 + n2*18
    # screw runs -Z from pt.z+2, len 16 -> tip at pt.z-14; cylinder r~2.8
    d17h = math.hypot(pt.x+122, pt.y-128.5)
    # min 3D distance from ball center to screw axis segment
    zlo,zhi = pt.z-14, pt.z+2
    def d3(c):
        zc = min(max(c.z,zlo),zhi)
        return math.sqrt((pt.x-c.x)**2+(pt.y-c.y)**2+(zc-c.z)**2)
    print("t=%.2f pt(%.1f,%.1f,%.1f) horizS17=%.1f 3dS17=%.1f 3dS16=%.1f"%(
        t,pt.x,pt.y,pt.z,d17h,d3(s17),d3(s16)))
# check lip coverage: lip starts edge = p1+d2*3, len L2+8 -> along 3..L2+8
print("lip along range 3..",round(L2+8,1))
