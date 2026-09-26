"""J-slot / notch geometry from wall mid-plane slices: take the wall outline polyline near each pin station,
fit the seat circle (points of the outline within r~5-7 of the pin centre) and the entry slot edge lines."""
import json, math, sys
import numpy as np
from section_tools import loops_from_segments
C = json.load(open("cuts_pins_SINGLE_CATWALK.json"))
AL = json.load(open("pin_alignment.json"))["SINGLE_CATWALK"]
def outline(cid, obj):
    segs = C[cid][obj]
    return [((a[0] * 1000, a[2] * 1000), (b[0] * 1000, b[2] * 1000)) for a, b in segs]
def fit_circle(P):
    P = np.array(P); A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]; b = (P ** 2).sum(1)
    x, *_ = np.linalg.lstsq(A, b, rcond=None); r = math.sqrt(x[2] + x[0] ** 2 + x[1] ** 2)
    res = np.abs(np.hypot(P[:, 0] - x[0], P[:, 1] - x[1]) - r)
    return x[0], x[1], r, res.max()
# pin centres (world mm, x,z) per rail from the pin alignment of the catwalk state
pins = {}
for r in AL:
    pass
import re
PC = json.load(open("cuts_pins_SINGLE_CATWALK.json"))
for cid, obj, zc in [("L_outer", "MainRig_037", 5012.5), ("L_outer", "MainRig_026", 5037.5), ("R_outer", "MainRig_118", 5037.5), ("R_outer", "MainRig_179", 5012.5),
                     ("L_inner", "MainRig_037", 5012.5), ("L_inner", "MainRig_026", 5037.5), ("R_inner", "MainRig_118", 5037.5), ("R_inner", "MainRig_179", 5012.5)]:
    if obj not in C[cid]:
        print(cid, obj, "not cut"); continue
    S = outline(cid, obj)
    pts = np.array([p for s in S for p in s])
    print(f"\n=== {obj} @ {cid}: {len(S)} segments")
    # candidate seat regions: cluster points around z=zc +-8 with x spacing ~305
    near = pts[np.abs(pts[:, 1] - zc) < 9]
    xs = np.sort(np.unique(np.round(near[:, 0] / 50) * 50))
    groups = []
    for x in np.unique(np.round(near[:, 0] / 305.16)):
        g = near[np.abs(near[:, 0] / 305.16 - x) < 0.2]
        if len(g) > 10: groups.append(g)
    for g in groups:
        cx0 = np.median(g[:, 0])
        # iterative circle fit: keep points within 3.5..7 mm of the current centre
        c = (cx0, zc)
        for _ in range(6):
            d = np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1])
            sel = pts[(d > 3.0) & (d < 7.5)]
            if len(sel) < 6: break
            cx, cz, r, e = fit_circle(sel)
            # keep only points close to the fitted circle
            sel2 = sel[np.abs(np.hypot(sel[:, 0] - cx, sel[:, 1] - cz) - r) < 0.3]
            if len(sel2) < 6: break
            cx, cz, r, e = fit_circle(sel2); c = (cx, cz)
        # arc span: angles of points on the circle
        on = pts[np.abs(np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1]) - r) < 0.15]
        ang = np.degrees(np.arctan2(on[:, 1] - c[1], on[:, 0] - c[0]))
        # entry: outline segments that leave the circle upward (z > cz + r*0.3), within 20 mm in x
        up = [s for s in S if min(s[0][1], s[1][1]) > c[1] - 1 and abs((s[0][0] + s[1][0]) / 2 - c[0]) < 25 and abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]) > 1.5
              and min(math.hypot(p[0] - c[0], p[1] - c[1]) for p in s) > r - 0.2]
        lines = []
        for s in up:
            dx, dz = s[1][0] - s[0][0], s[1][1] - s[0][1]
            if abs(dz) > 1.0:
                lines.append((round(math.degrees(math.atan2(abs(dz), dx if dz > 0 else -dx)), 1), round(s[0][0], 2), round(s[0][1], 2), round(s[1][0], 2), round(s[1][1], 2)))
        print(f"   seat centre ({c[0]:.2f}, {c[1]:.2f}) d={2*r:.2f}  fit err {e:.3f}  arc pts {len(on)} angles {ang.min():.0f}..{ang.max():.0f}  entry edges: {lines[:4]}")
