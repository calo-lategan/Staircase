"""List closed loops of each object in a cut, inside a window, in a local frame (mm): centre, size, area, and a
circle fit (for pins/holes). python loops_in_window.py cuts.json id u v u0 v0 umin umax vmin vmax (window in local mm)"""
import json, sys, math
from section_tools import loops_from_segments, poly_props
cuts = json.load(open(sys.argv[1])); cid = sys.argv[2]
IX = {"x": 0, "y": 1, "z": 2}
u, v = IX[sys.argv[3]], IX[sys.argv[4]]
u0, v0 = float(sys.argv[5]), float(sys.argv[6])
umin, umax, vmin, vmax = [float(a) for a in sys.argv[7:11]]
for name, segs in sorted(cuts[cid].items()):
    S = [(((a[u] - u0) * 1000, (a[v] - v0) * 1000), ((b[u] - u0) * 1000, (b[v] - v0) * 1000)) for a, b in segs]
    S = [s for s in S if umin <= (s[0][0] + s[1][0]) / 2 <= umax and vmin <= (s[0][1] + s[1][1]) / 2 <= vmax]
    if not S:
        continue
    L = loops_from_segments(S, tol=1e-4)
    used = sum(len(l) for l in L)
    print(f"{name}: {len(S)} segs, {len(L)} loops")
    for l in L:
        a, sx, sy, *_ = poly_props(l)
        cx, cy = (sx / a, sy / a) if abs(a) > 1e-9 else (sum(p[0] for p in l) / len(l), sum(p[1] for p in l) / len(l))
        us = [p[0] for p in l]; vs = [p[1] for p in l]
        r = [math.hypot(p[0] - cx, p[1] - cy) for p in l]
        circ = (max(r) - min(r)) < 0.08 * max(r) and len(l) > 10
        tag = f"CIRCLE d={2*sum(r)/len(r):.2f} (r {min(r):.2f}-{max(r):.2f})" if circ else ""
        print(f"   loop n={len(l):3d} A={abs(a):9.2f} c=({cx:8.2f},{cy:7.2f}) {sys.argv[3]}[{min(us):8.2f},{max(us):8.2f}] {sys.argv[4]}[{min(vs):7.2f},{max(vs):7.2f}] {tag}")
    # open chains (unclosed) summary
