"""Print the exact cross-section loops (local mm, rounded) of named parts at chosen stations."""
import json, sys
from section_tools import loops_from_segments, section
cfg = sys.argv[1]; P = json.load(open(f"sections_{cfg}.json"))
PL = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}
for spec in sys.argv[2:]:
    name, axis, st = spec.split(":")
    p = P[name]; c = p["cuts"][axis][st]; i, j = PL[axis]
    segs = [((a[i] * 1000, a[j] * 1000), (b[i] * 1000, b[j] * 1000)) for a, b in c["segs"]]
    L = loops_from_segments(segs, tol=1e-4)
    s = section(L)
    x0 = min(q[0] for l in L for q in l); y0 = min(q[1] for l in L for q in l)
    print(f"\n### {name} cut {axis}={c['pos']:.5f} (st {st}) plane axes {'xyz'[i]},{'xyz'[j]} origin ({x0:.2f},{y0:.2f}) mm")
    print(f"    A={s['A']:.1f} Ix={s['Ix']:.0f} Iy={s['Iy']:.0f} cy={s['cy']-y0:.2f} cx={s['cx']-x0:.2f} w={s['w']:.2f} h={s['h']:.2f} loops={[(d['n'], round(d['area'],1), d['hole']) for d in s['loops']]}")
    for l in L:
        # drop collinear midpoints for readability
        pts = [(round(q[0] - x0, 2), round(q[1] - y0, 2)) for q in l]
        print("    ", pts)
