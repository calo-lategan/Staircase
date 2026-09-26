"""Pin-to-hole alignment at the rail inner-wall planes, every tread, every state."""
import json, math, sys
from section_tools import loops_from_segments, poly_props
P = json.load(open("sections_SINGLE_CATWALK.json"))
TREAD = {n: p["bone"] for n, p in P.items() if p["dims_mm"] == [280.0, 1236.0, 50.0]}
RAILS = {"MainRig_037": "Lo_L", "MainRig_026": "Up_L", "MainRig_179": "Lo_R", "MainRig_118": "Up_R"}


def circles(segs):
    S = [((a[0] * 1000, a[2] * 1000), (b[0] * 1000, b[2] * 1000)) for a, b in segs]
    out = []
    for l in loops_from_segments(S, tol=1e-4):
        a, sx, sy, *_ = poly_props(l)
        if abs(a) < 1e-6 or len(l) < 12:
            continue
        cx, cy = sx / a, sy / a
        r = [math.hypot(p[0] - cx, p[1] - cy) for p in l]
        if max(r) - min(r) < 0.08 * max(r):
            out.append((cx, cy, 2 * max(r), 2 * math.sqrt(abs(a) / math.pi)))   # centre, circumscribed d, area-equivalent d
    return out


res = {}
for cfg in ["SINGLE_CATWALK", "SINGLE_STANDARD", "SINGLE_STEEP"]:
    C = json.load(open(f"cuts_pins_{cfg}.json"))
    print(f"\n######## {cfg}")
    for plane in ["L_inner", "R_inner"]:
        cut = C[plane]
        holes = [(RAILS[n], c) for n in RAILS if n in cut for c in circles(cut[n])]
        for tn in sorted(TREAD, key=lambda n: TREAD[n]):
            if tn not in cut:
                continue
            for pc in circles(cut[tn]):
                best = min(holes, key=lambda h: math.hypot(h[1][0] - pc[0], h[1][1] - pc[1])) if holes else None
                if not best:
                    print(f"  {plane} {TREAD[tn]} pin d={pc[3]:.2f}: NO HOLE"); continue
                rail, hc = best
                off = math.hypot(hc[0] - pc[0], hc[1] - pc[1])
                interf = off + pc[3] / 2 - hc[3] / 2          # >0 : pin material outside the hole (clash)
                print(f"  {plane} {TREAD[tn]:<6} pin d={pc[3]:5.2f} @({pc[0]:9.2f},{pc[1]:8.2f})  -> {rail} hole d={hc[3]:5.2f}  offset={off:5.2f} mm  "
                      f"{'CLASH %.2f mm' % interf if interf > 0.05 else 'fits, radial clearance %.2f' % (-interf)}")
                res.setdefault(cfg, []).append(dict(plane=plane, tread=TREAD[tn], pin_d=pc[3], rail=rail, hole_d=hc[3], offset=off, interference=interf))
json.dump(res, open("pin_alignment.json", "w"), indent=1)
