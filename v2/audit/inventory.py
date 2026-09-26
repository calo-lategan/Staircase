"""Part inventory from the section survey: mid-length section of every part (area, holes, outer size, wall
thickness estimate), how the section changes along the part (holes / slots / end features)."""
import json, sys, math
from collections import defaultdict
from section_tools import loops_from_segments, section
cfg = sys.argv[1]
P = json.load(open(f"sections_{cfg}.json"))
PL = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}      # in-plane coordinates for a cut normal to the axis


def sec_at(p, axis, st):
    c = p["cuts"][axis].get(st)
    if not c or not c["segs"]:
        return None
    i, j = PL[axis]
    segs = [((a[i] * 1000, a[j] * 1000), (b[i] * 1000, b[j] * 1000)) for a, b in c["segs"]]
    L = loops_from_segments(segs, tol=1e-4)
    if not L:
        return None
    try:
        s = section(L)
    except ZeroDivisionError:
        return None
    s["nloops"] = len(L); s["nholes"] = sum(1 for d in s["loops"] if d["hole"])
    return s


rows = []
for n, p in sorted(P.items()):
    ax = p["long_axis"]
    mid = sec_at(p, ax, "0.5")
    along = []
    for st in sorted(p["cuts"][ax], key=float):
        s = sec_at(p, ax, st)
        along.append((float(st), round(s["A"], 1) if s else None, s["nholes"] if s else None))
    rows.append(dict(name=n, role=p["role"], var=p["variant"], side=p["side"], bone=p["bone"], dims=p["dims_mm"], ax=ax,
                     closed=p["closed"], vol=p["volume_mm3"],
                     A=round(mid["A"], 1) if mid else None, w=round(mid["w"], 2) if mid else None, h=round(mid["h"], 2) if mid else None,
                     holes=mid["nholes"] if mid else None, Ix=round(mid["Ix"]) if mid else None, Iy=round(mid["Iy"]) if mid else None,
                     along=along))
json.dump(rows, open(f"inventory_{cfg}.json", "w"), indent=1)
by = defaultdict(list)
for r in rows:
    by[(r["role"], r["var"])].append(r)
for k, rs in sorted(by.items(), key=lambda kv: str(kv[0])):
    print(f"\n== role={k[0]} variant={k[1]}  n={len(rs)}")
    for r in rs:
        var = sorted(set(a for _, a, _ in r["along"] if a is not None))
        print(f"  {r['name']:<14} side={r['side']} bone={r['bone']:<18} dims={r['dims']} ax={r['ax']} closed={r['closed']} "
              f"vol={r['vol']} A_mid={r['A']} [{r['w']}x{r['h']}] holes={r['holes']} Ix={r['Ix']} Iy={r['Iy']} A_along(min/max)={min(var) if var else None}/{max(var) if var else None}")
