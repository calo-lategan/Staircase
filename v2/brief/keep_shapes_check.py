"""User decisions 2026-09-23: keep the U-shaped guide rails, keep all 12 flat poles (pin = bottom of the pole), no middle
rail / toe board / feet (scaffolding supports the unit). Finds the sizes each part needs for the Aug-2026 sheet.
Run: uvx --with numpy python v2/brief/keep_shapes_check.py  -> keep_shapes_check.json
"""
import sys, os, math, json, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "loadtest"))
import loadtest_latest as LT
import lightweight_events_2026 as LW

G, GG, GQ, GM1 = 9.81, LW.GG, LW.GQ, LW.GM1
SPAN = LT.SPAN
TREAD = LW.tread_plank(depth=40, skin=1.8, webs=5, down=(35.0, 2.0))       # change 1 (kept)
HR_SIDE_N = LT.self_weight("B")["_handrail_per_side"] * G * 1.6              # allowance for thicker poles


def inv_u(h, t, b=25.0):
    """right rail: inverted U, outer width b fixed (must nest), legs and top web thickness t, depth h"""
    t = min(t, b / 2)
    s = LW.rects([(b, t, h - t / 2), (t, h - t, (h - t) / 2), (t, h - t, (h - t) / 2)])
    s.update(t=t, L=1845.0, label=f"inverted U 25 x {h:g}, {t:g} mm walls")
    return s


def u_chan(slot_depth, t, slot=25.0):
    """left rail: U open on top, 25 mm slot kept (the right rail nests in it), walls + base thickness t"""
    H = slot_depth + t
    s = LW.rects([(t, H, H / 2), (t, H, H / 2), (slot, t, t / 2)])
    s.update(t=t, L=1845.0, label=f"U {slot + 2 * t:g} x {H:g}, {t:g} mm walls, 25 slot")
    return s


def fyd(sec):
    return LW.f0(sec["t"]) / GM1


def girder(lo, up, q=7.5e-3, cases=("standard", "catwalk_ends", "catwalk_mid")):
    """utilisations (max of stress ULS with load patterns, deflection L/250, 10 mm under one person) + steep crew"""
    res = {}
    spec = {"standard": ("STANDARD", False), "catwalk_ends": ("CATWALK", False), "catwalk_mid": ("CATWALK", True)}
    for name in cases:
        lock, mid = spec[name]
        s = 0.0
        for pat in ("all", "low", "high"):
            r = LW.girder_fe(lock, lo, up, TREAD["A"], HR_SIDE_N, q, pat, mid, factor=(GG, GQ))
            s = max(s, r["lower"] / fyd(lo), r["upper"] / fyd(up))
        d = LW.girder_fe(lock, lo, up, TREAD["A"], HR_SIDE_N, q, "all", mid)["defl"] / (SPAN / (2 if mid else 1) / 250)
        p = max(LW.girder_fe(lock, lo, up, 0.0, 0.0, 0.0, "all", mid, point=(i, 1000.0))["defl"] for i in (1, 2, 3)) / 10.0
        res[name] = round(max(s, d, p), 3)
        res[name + "_parts"] = dict(stress=round(s, 3), defl_L250=round(d, 3), person=round(p, 3))
    st = LW.girder_fe("STEEP", lo, up, TREAD["A"], HR_SIDE_N, 0.0, "all", False, point=(2, 2 * 2700.0), factor=(GG, GQ))
    res["steep_crew"] = round(max(st["lower"] / fyd(lo), st["upper"] / fyd(up)), 3)
    return res


def need_lower(make, t, h_up, cases, q):
    """smallest lower-rail depth (mm) that passes, upper rail fixed; bisection (deeper = stronger)"""
    def ok(h):
        g = girder(make(h, t), make(h_up, t), q, cases)
        return all(g[c] <= 1.0 for c in cases) and g["steep_crew"] <= 1.0
    lo_h, hi_h = 20, 220
    if not ok(hi_h):
        return None
    while hi_h - lo_h > 1:
        mid = (lo_h + hi_h) // 2
        if ok(mid):
            hi_h = mid
        else:
            lo_h = mid
    return hi_h


def search(make, t_list, h_up_list, cases, q):
    rows = []
    for t in t_list:
        for h_up in h_up_list:
            h_lo = need_lower(make, t, h_up, cases, q)
            if h_lo is None:
                continue
            lo, up = make(h_lo, t), make(h_up, t)
            g = girder(lo, up, q, cases)
            rows.append(dict(walls_mm=t, lower=lo["label"], upper=up["label"],
                             mass_2bars_kg=round((lo["A"] * 1778.7 + up["A"] * 1845.1) * LW.RHO, 2),
                             util={c: g[c] for c in cases}, steep_crew=g["steep_crew"]))
    return sorted(rows, key=lambda r: r["mass_2bars_kg"])


out = {"now": {}}
out["now"]["right rails (approx. inverted U 25x21 / 25x20, 5 mm)"] = girder(inv_u(21.0, 5.0), inv_u(20.0, 5.0))
out["now"]["left channels (U 35x25, 5 mm)"] = girder(u_chan(20.0, 5.0), u_chan(20.0, 5.0))
H_UP = (20, 25, 30, 40, 50)
for q_name, q in (("7.5 kN/m2 (sheet target)", 7.5e-3), ("5.0 kN/m2 (lower end of the event band)", 5.0e-3)):
    out[q_name] = {
        "right rails, catwalk supported mid-span by the scaffold": search(inv_u, (5.0, 6.0, 8.0), H_UP, ("standard", "catwalk_mid"), q)[:4],
        "right rails, catwalk supported at its ends only": search(inv_u, (5.0, 6.0, 8.0), H_UP, ("standard", "catwalk_ends"), q)[:4],
        "left channels, catwalk supported mid-span by the scaffold": search(lambda h, t: u_chan(h - t, t), (5.0, 6.0, 8.0), H_UP, ("standard", "catwalk_mid"), q)[:4],
        "left channels, catwalk supported at its ends only": search(lambda h, t: u_chan(h - t, t), (5.0, 6.0, 8.0), H_UP, ("standard", "catwalk_ends"), q)[:4],
    }
    print(q_name, "done", flush=True)

# ---------------------------------------------------------------- poles: keep 6 per side, flat b (along the stair) x t (sideways)
guard = dict(LT.SEC["guard"], t=3.8)
hand = dict(LT.SEC["cyan"], t=25.0)


def flat(b, t):
    s = LW.rects([(b, t, t / 2)])
    s.update(t=max(b, t) if max(b, t) > 5 else 5.0, J=b * t ** 3 / 3 if b >= t else t * b ** 3 / 3)
    return s


def pole_util(b, t, cases):
    post = flat(b, t)
    u = 0.0
    for lock in LT.LOCKS:
        rails = {"guard": (LT.LOCKS[lock]["guard"], guard), "hand": (LT.LOCKS[lock]["hand"], hand)}
        for case in cases:
            r = LW.barrier_fe(lock, [0, 1, 2, 3, 4, 5], post, rails, 0.0, case)
            u = max(u, r["M_post"] / (post["I"] / post["c"] * LW.f0(min(b, t)) / GM1))
    return u


poles = {}
for b in (25.0, 40.0, 60.0):
    for label, cases in (("3.0 kN/m crowd push + 1.5 kN post + 1.25 kN rail", ("line", "post", "mid")),
                         ("point loads only: 1.5 kN post + 1.25 kN rail", ("post", "mid"))):
        lo_t, hi_t = 5.0, 120.0
        while hi_t - lo_t > 0.5:
            mid_t = (lo_t + hi_t) / 2
            if pole_util(b, mid_t, cases) <= 1.0:
                hi_t = mid_t
            else:
                lo_t = mid_t
        need = round(hi_t, 1)
        poles.setdefault(f"width along the stair {b:g} mm", {})[label] = need
poles["now (25 x 10)"] = dict(line=round(pole_util(25, 10, ("line",)), 2), post=round(pole_util(25, 10, ("post",)), 2),
                              rail_point=round(pole_util(25, 10, ("mid",)), 2))
out["poles, 6 per side, thickness needed in the push direction (mm)"] = poles
json.dump(out, open(os.path.join(HERE, "keep_shapes_check.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
