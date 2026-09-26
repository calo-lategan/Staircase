import json, math
import numpy as np
from section_tools import loops_from_segments, poly_props
R = json.load(open("lock_cuts_final.json"))
W_RAIL = {"E8505_I02": 35.0, "E9366_A02": 35.0, "E11379_J04": 25.0, "E9226_I02": 25.0}
TH = {"STANDARD": 35.0}
out = {}
for cfg, rails in R.items():
    print(f"\n######## {cfg}")
    th = math.radians(TH[cfg])
    for rn, e in rails.items():
        Wr = W_RAIL[rn]
        loops = loops_from_segments([tuple(map(tuple, s)) for s in e["rail"]], tol=1e-3)
        slots = []
        for l in loops:
            us = [p[0] for p in l]; ws = [p[1] for p in l]
            a = abs(poly_props(l)[0])
            if 3 < a < 2000 and max(ws) - min(ws) < 15 and 5 < max(us) - min(us) < 60:
                slots.append((min(us), max(us), min(ws), max(ws), a))
        slots.sort()
        pins = []
        for pn, pe in e["pins"].items():
            pts = np.array([p for s in pe["segs"] for p in s])
            if pts[:, 1].min() < -1 or pts[:, 1].max() > Wr + 1:
                continue                                  # pin of the other side
            pins.append((pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max(), pn, pe["role"], pe["variant"]))
        pins.sort()
        print(f"  {rn}: {len(slots)} slot loops, {len(pins)} pins in the web plane (+/- {2.5*math.tan(th):.2f} mm through half the web)")
        rows = []
        for p in pins:
            ext = 2.5 * math.tan(th)
            pu0, pu1 = p[0] - ext, p[1] + ext
            host = [s for s in slots if s[0] - 2 <= (p[0] + p[1]) / 2 <= s[1] + 2]
            if host:
                s = host[0]
                g_lo, g_hi = pu0 - s[0], s[1] - pu1
                gw_lo, gw_hi = p[2] - s[2], s[3] - p[3]
                txt = f"slot u[{s[0]:7.2f},{s[1]:7.2f}] len {s[1]-s[0]:5.2f} | pin u[{p[0]:7.2f},{p[1]:7.2f}] ({p[1]-p[0]:5.2f} at mid, {pu1-pu0:5.2f} through web) | gap low-u {g_lo:6.2f} high-u {g_hi:6.2f} | w gaps {gw_lo:5.2f}/{gw_hi:5.2f}"
                rows.append(dict(pin=p[4], role=p[5], variant=p[6], slot=s[:4], pin_u=(p[0], p[1]), through=(pu0, pu1), gap_low=g_lo, gap_high=g_hi, gw=(gw_lo, gw_hi)))
            else:
                txt = f"NO SLOT FOUND around u {(p[0]+p[1])/2:.1f} (pin u[{p[0]:.2f},{p[1]:.2f}] w[{p[2]:.2f},{p[3]:.2f}])"
                rows.append(dict(pin=p[4], role=p[5], variant=p[6], slot=None, pin_u=(p[0], p[1])))
            print(f"     {p[4]:<11} {p[5]}/{p[6]:<8} {txt}")
        out.setdefault(cfg, {})[rn] = rows
json.dump(out, open("lock_analysis_final.json", "w"), indent=1)
