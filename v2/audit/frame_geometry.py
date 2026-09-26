"""Side-frame geometry per state, measured in the posed model: axle centres, tread pin centres (rear = lower rail,
front = upper rail), pole crossing points on each rail web, rail axis lines. Output frame_geometry.json (world mm)."""
import json, math
import numpy as np
from section_tools import loops_from_segments, poly_props
TREADS = ["MainRig_061", "MainRig_079", "MainRig_096", "MainRig_019", "MainRig_030", "MainRig_042"]     # Tread0..5
out = {}
LC = json.load(open("lock_cuts.json"))
for cfg in ["SINGLE_CATWALK", "SINGLE_STANDARD", "SINGLE_STEEP"]:
    S = json.load(open(f"sections_{cfg}.json"))
    C = json.load(open(f"cuts_pins_{cfg}.json"))
    g = {}
    for ax in ("MainRig_006", "MainRig_010"):
        lo, hi = S[ax]["lo"], S[ax]["hi"]
        g[ax] = [(lo[0] + hi[0]) / 2 * 1000, (lo[2] + hi[2]) / 2 * 1000]
    for side, plane in (("L", "L_inner"), ("R", "R_inner")):
        pins = []
        for i, tn in enumerate(TREADS):
            segs = C[plane].get(tn, [])
            L = loops_from_segments([((a[0] * 1000, a[2] * 1000), (b[0] * 1000, b[2] * 1000)) for a, b in segs], tol=1e-4)
            cs = []
            for l in L:
                A, sx, sz, *_ = poly_props(l)
                if abs(A) > 20: cs.append((sx / A, sz / A, 2 * math.sqrt(abs(A) / math.pi)))
            cs.sort(key=lambda c: c[1])               # lower z = rear pin
            if len(cs) == 2:
                pins.append(dict(tread=i, rear=cs[0][:2], front=cs[1][:2], d_rear=cs[0][2], d_front=cs[1][2]))
        g[f"pins_{side}"] = pins
    # pole crossings (centre of the pin footprint at each rail web), world X,Z
    for rn, e in LC[cfg].items():
        U, W, V, c, lo = [np.array(e["frame"][k]) for k in ("U", "W", "V", "c", "lo")]
        pts = []
        wr = 35.0 if rn in ("MainRig_037", "MainRig_026") else 25.0
        for pn, pe in e["pins"].items():
            P = np.array([p for s in pe["segs"] for p in s])
            if P[:, 1].min() < -1 or P[:, 1].max() > wr + 1: continue
            um, wm = P[:, 0].mean() / 1000 + lo[0], P[:, 1].mean() / 1000 + lo[1]
            hi_v = e["frame"]["hi"][2]; lo_v = lo[2]
            vpos = lo_v + 0.0025 if rn in ("MainRig_037", "MainRig_026") else hi_v - 0.0025
            X = c + U * um + W * wm + V * vpos
            pts.append(dict(pin=pn, role=pe["role"], X=X[0] * 1000, Z=X[2] * 1000, u_len=float(P[:, 0].max() - P[:, 0].min())))
        pts.sort(key=lambda p: p["X"])
        # rail axis line from the frame: point c, direction U (world X,Z)
        g[f"rail_{rn}"] = dict(poles=pts, c=[c[0] * 1000, c[2] * 1000], U=[U[0], U[2]], lo_u=lo[0] * 1000, hi_u=e["frame"]["hi"][0] * 1000)
    out[cfg] = g
    print(cfg, "axles", {k: [round(v, 1) for v in g[k]] for k in ("MainRig_006", "MainRig_010")})
    for side in "LR":
        print(f"  pins {side}:", [(p["tread"], tuple(round(v, 1) for v in p["rear"]), tuple(round(v, 1) for v in p["front"])) for p in g[f"pins_{side}"]])
    for rn in ("MainRig_037", "MainRig_026", "MainRig_179", "MainRig_118"):
        r = g[f"rail_{rn}"]
        print(f"  {rn} dir {np.degrees(np.arctan2(r['U'][1], r['U'][0])):.2f} deg, poles:", [(p["pin"], round(p["X"], 1), round(p["Z"], 1)) for p in r["poles"]])
json.dump(out, open("frame_geometry.json", "w"), indent=1)
