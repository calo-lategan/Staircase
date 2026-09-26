import bpy, collections
from mathutils import Vector
out = []
def wbb(o):
    ps = [o.matrix_world @ Vector(v) for v in o.bound_box]
    return [min(p[i] for p in ps) for i in range(3)], [max(p[i] for p in ps) for i in range(3)]
for cname in ("Unsorted", "IfcSite/Unnamed", "MainStaircase_Source"):
    col = bpy.data.collections[cname]
    cells = collections.defaultdict(list)
    for o in col.objects:
        if o.type != 'MESH': continue
        lo, hi = wbb(o)
        c = [(lo[i]+hi[i])/2 for i in range(3)]
        cells[(round(c[0]/2)*2, round(c[1]/2)*2)].append((o, lo, hi))
    out.append(f"== {cname}")
    for k in sorted(cells, key=lambda k: -len(cells[k])):
        L = cells[k]
        lo = [min(x[1][i] for x in L) for i in range(3)]; hi = [max(x[2][i] for x in L) for i in range(3)]
        names = collections.Counter(x[0].name.split(".")[0][:28] for x in L).most_common(4)
        out.append(f"cell{k}: n={len(L)} bb={[round(v,2) for v in lo]}..{[round(v,2) for v in hi]} {names}")
open("_probe5.txt","w").write("\n".join(out))
