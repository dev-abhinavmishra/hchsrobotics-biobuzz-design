"""Interference probe v3: populate, check undeclared pairs, print common
bbox so fixes can be aimed."""
import sys
sys.path.insert(0, r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad")
import FreeCAD as App
import dt_build

doc = App.newDocument("probe")
ctx = dt_build.new_ctx()
dt_build.populate_drivebase(doc, ctx)
doc.recompute(None, True, True)

declared = set()
for a, b in ctx["embeds"] + ctx["faces"] + ctx["contacts"] + ctx["journals"]:
    declared.add(frozenset((a, b)))
for j in ctx["joints"]:
    ms = j["members"] + j["bolts"] + j["nuts"]
    for i in range(len(ms)):
        for k in range(i + 1, len(ms)):
            declared.add(frozenset((ms[i], ms[k])))

objs = []
for nm in ctx["solids"]:
    if nm == "ENV_START":
        continue
    o = doc.getObject(nm)
    if o is None:
        continue
    try:
        sh = o.Shape
    except Exception:
        continue
    if sh is None or sh.isNull() or sh.Volume <= 0:
        continue
    sh2 = sh.copy()
    sh2.transformShape(o.getGlobalPlacement().toMatrix())
    objs.append((nm, sh2))
print("solids:", len(objs), "declared:", len(declared))

pairs = []
for i in range(len(objs)):
    n1, s1 = objs[i]
    b1 = s1.BoundBox
    for j in range(i + 1, len(objs)):
        n2, s2 = objs[j]
        if frozenset((n1, n2)) in declared:
            continue
        b2 = s2.BoundBox
        if (b1.XMin < b2.XMax + 0.01 and b1.XMax > b2.XMin - 0.01 and
                b1.YMin < b2.YMax + 0.01 and b1.YMax > b2.YMin - 0.01 and
                b1.ZMin < b2.ZMax + 0.01 and b1.ZMax > b2.ZMin - 0.01):
            pairs.append((n1, n2, s1, s2))
print("candidates:", len(pairs))

hits = []
for n1, n2, s1, s2 in pairs:
    try:
        c = s1.common(s2)
        if c is not None and not c.isNull() and c.Volume > 0.5:
            hits.append((c.Volume, n1, n2, c.BoundBox))
    except Exception:
        pass
hits.sort(key=lambda h: -h[0])
print("UNDECLARED OVERLAPS >0.5mm3:", len(hits))
for v, a, b, bb in hits:
    print("%9.1f %-22s %-22s X[%.0f,%.0f] Y[%.0f,%.0f] Z[%.1f,%.1f]"
          % (v, a, b, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
