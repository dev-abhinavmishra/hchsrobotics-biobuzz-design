import sys, FreeCAD as App
gold = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\_gold\turret.FCStd")
new = App.openDocument(r"C:\Users\pmsma\Downloads\BIOBUZZ-Robot\cad\turret\turret.FCStd")
gd = {o.Name: o for o in gold.Objects}
nd = {o.Name: o for o in new.Objects}
only_g = sorted(set(gd) - set(nd)); only_n = sorted(set(nd) - set(gd))
print("ONLY_IN_GOLD:", only_g)
print("ONLY_IN_NEW:", only_n)
diffs = []
for n in sorted(set(gd) & set(nd)):
    g, o = gd[n], nd[n]
    ge = {k: v for k, v in getattr(g, "ExpressionEngine", [])}
    oe = {k: v for k, v in getattr(o, "ExpressionEngine", [])}
    if ge != oe:
        diffs.append((n, ge, oe))
print("EXPR_DIFFS:", len(diffs))
for n, ge, oe in diffs:
    ks = set(ge) | set(oe)
    ch = [(k, ge.get(k), oe.get(k)) for k in sorted(ks) if ge.get(k) != oe.get(k)]
    print("  %s: %s" % (n, ch))
