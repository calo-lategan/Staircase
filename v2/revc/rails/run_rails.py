"""Rev C guide rails (H family, rails_lib.py): every check. Writes rail_design_<pole>.json next to this file.
  python3 v2/revc/rails/run_rails.py              (production box pole 25 x 80)
  POLE=plate55 python3 v2/revc/rails/run_rails.py (prototype plate pole 25 x 55)
Sections: A kinematics/geometry, B side frame (in-plane), C barrier (lateral, pin pull, small torque), D pins/caps/edges,
E combination, F local slot ligament + shoulder, G mass."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rails_lib as L
import frame_rails as F

OUT = {"pole": L.POLE_KEY, "pole_note": L.POLE["note"]}
SIDES = ("L", "R")
fx = lambda v, n=2: round(float(v), n)
G = F.G
X_REAR0 = F.REAR0[0]
POLES_X = {s: [p["x"] for p in G[s]["poles"]] for s in SIDES}
SEC = L.sections()
SEC["notch+slot_up"] = SEC["slot_up"].cut(-1, -1, L.T_P + 0.01, L.NOTCH_DEPTH)
SEC["notch+slot_lo"] = SEC["slot_lo"].cut(-1, -1, L.T_P + 0.01, L.NOTCH_DEPTH)
PROPS = {k: v.props() for k, v in SEC.items()}

def cross_s(x_rel, theta, lev, n_away):
    p0 = L.from_rail(0.0, n_away, theta, lev); u, nu = L.frame_state(theta)
    return (x_rel - p0[0]) / u[0]

# ================================================================== A. kinematics and geometry
def cap_gap(s_flange, theta, lev, s_pin):
    """clear distance, in the rail's side plane, between a vertical 25-along pole crossing the mid flange at s_flange
    and the cap + washer disc (radius 15) round a pin at (s_pin, n = 12.5)"""
    r = 15.0; x_f = L.from_rail(s_flange, L.N_MF, theta, lev)[0]; half = 12.5 / math.cos(math.radians(theta))
    best = 1e9
    for n in np.linspace(L.C_PIN - r, L.C_PIN + r, 61):
        sc = cross_s(x_f, theta, lev, n); dn = abs(n - L.C_PIN); chord = math.sqrt(max(r * r - dn * dn, 0.0))
        best = min(best, abs(sc - s_pin) - half - chord)
    return best

def geometry():
    g = {"pin_line_separation": {k: fx(L.sep(v), 1) for k, v in L.STATES.items()},
         "tip_gap": {k: fx(L.sep(v) - 2 * L.C_PIN, 1) for k, v in L.STATES.items()},
         "slot_len": {k: fx(v, 1) for k, v in L.SLOT_LEN.items()}}
    slots = {}
    for side in SIDES:
        rows = []
        for x in POLES_X[side]:
            xr = x - X_REAR0
            s_up = cross_s(xr, 35.0, "up", L.N_MF); s_lo = cross_s(xr, 35.0, "lo", L.N_MF)
            pu0 = L.from_rail(s_up, L.N_MF, 0.0, "up"); s_lo_cw = cross_s(pu0[0], 0.0, "lo", L.N_MF)      # catwalk: same upper slot
            pl9 = L.from_rail(s_lo, L.N_MF, 49.4, "lo"); s_up_st = cross_s(pl9[0], 49.4, "up", L.N_MF)    # steep: same lower slot
            rec = dict(x=fx(x, 1), up_std_cw=fx(s_up, 1), up_steep=fx(s_up_st, 1), lo_std_steep=fx(s_lo, 1), lo_catwalk=fx(s_lo_cw, 1))
            use = {"standard": (s_lo, s_up), "catwalk": (s_lo_cw, s_up), "steep": (s_lo, s_up_st)}
            for st, th in L.STATES.items():
                sl, su = use[st]
                rec[f"vert_between_flanges_{st}"] = fx(L.from_rail(su, L.N_MF, th, "up")[1] - L.from_rail(sl, L.N_MF, th, "lo")[1], 1)
                rec[f"cap_gap_up_{st}"] = fx(min(cap_gap(su, th, "up", i * L.PITCH) for i in range(-1, 8)), 1)
                rec[f"cap_gap_lo_{st}"] = fx(min(cap_gap(sl, th, "lo", i * L.PITCH) for i in range(-1, 8)), 1)
            lu = [(s_up, L.UP_SLOTS["standard+catwalk"]), (s_up_st, L.UP_SLOTS["steep"])]
            ll = [(s_lo, L.LO_SLOTS["standard+steep"]), (s_lo_cw, L.LO_SLOTS["catwalk"])]
            gap2 = lambda a, b: abs(a[0] - b[0]) - a[1] / 2 - b[1] / 2
            rec["upper_slots_web_between"] = fx(gap2(*lu), 1); rec["lower_slots_web_between"] = fx(gap2(*ll), 1)
            def cut_gap(sp): return min(abs(sp[0] - i * L.PITCH) - sp[1] / 2 - L.CAP_CUT[0] / 2 for i in range(-1, 8))
            rec["upper_slots_to_cap_cut"] = fx(min(cut_gap(a) for a in lu), 1); rec["lower_slots_to_cap_cut"] = fx(min(cut_gap(a) for a in ll), 1)
            rec["_up"] = lu; rec["_lo"] = ll
            rows.append(rec)
        slots[side] = rows
    g["slots"] = slots
    allgaps = [r[k] for s in SIDES for r in slots[s] for k in r if k.startswith("cap_gap")]
    g["cap_pole_min_gap"] = min(allgaps)
    # catwalk interleave
    lo_tabs_on_up = [L.to_rail(L.from_rail(i * L.PITCH, 0.0, 0.0, "lo"), 0.0, "up")[0] for i in range(6)]
    up_tabs_on_lo = [L.to_rail(L.from_rail(i * L.PITCH, 0.0, 0.0, "up"), 0.0, "lo")[0] for i in range(6)]
    g["tab"] = dict(radius=fx(L.TAB_R, 1), width=fx(L.TAB_W, 1), reach_beyond_touching_plane=fx(L.TAB_H, 1),
                    notch_depth=fx(L.NOTCH_DEPTH, 1), notch_width=fx(L.NOTCH_W, 1),
                    notch_centres_upper_rail_s=[fx(v, 1) for v in lo_tabs_on_up], notch_centres_lower_rail_s=[fx(v, 1) for v in up_tabs_on_lo],
                    notch_to_own_hole_min=fx(min(min(abs(a - i * L.PITCH) for i in range(6)) for a in lo_tabs_on_up + up_tabs_on_lo) - L.NOTCH_W / 2 - L.HOLE_D / 2, 1))
    ng = []
    for side in SIDES:
        for r in slots[side]:
            for sp in r["_up"]: ng.append((min(abs(sp[0] - c) for c in lo_tabs_on_up) - L.NOTCH_W / 2 - sp[1] / 2, side, "upper", fx(sp[0], 1)))
            for sp in r["_lo"]: ng.append((min(abs(sp[0] - c) for c in up_tabs_on_lo) - L.NOTCH_W / 2 - sp[1] / 2, side, "lower", fx(sp[0], 1)))
    w = min(ng); g["tab"]["notch_to_slot_min"] = dict(gap=fx(w[0], 1), side=w[1], rail=w[2], slot_s=w[3],
        note="notch is in the pin wall (n 0-%.1f), slot in the mid flange (n %.1f-%.1f): different elements; a negative gap means both cuts share one station - checked as section 'notch+slot'" % (L.NOTCH_DEPTH, L.N_MF0, L.N_MF0 + L.T_MF))
    drift = []
    for thd in np.linspace(0, 12, 241):
        s_now = L.to_rail(L.from_rail(0.0, 0.0, thd, "lo"), thd, "up")[0]
        drift.append((thd, L.sep(thd) - 2 * L.C_PIN, s_now - lo_tabs_on_up[0]))
    clear = next(d for d in drift if d[1] >= L.NOTCH_DEPTH + 0.5)
    g["fold_out"] = dict(angle_tabs_clear_deg=fx(clear[0], 2), drift_at_clear_mm=fx(abs(clear[2]), 2), notch_side_clearance=L.NOTCH_CLR,
                         max_drift_before_clear=fx(max(abs(d[2]) for d in drift if d[0] <= clear[0]), 2))
    # base end: lowest point of the lower rail (far edge, n = D) near the base axle, measured end x
    base = {}
    for side in SIDES:
        x_end = F.G[side]["rail_lo"]["a"][0]
        s_end = cross_s(x_end - X_REAR0, 35.0, "lo", L.C_PIN)
        c = np.array(F.AXLE_BASE) - F.REAR0; s_ax, n_ax = L.to_rail(c, 35.0, "lo")
        p = L.from_rail(s_end, L.D, 35.0, "lo") + F.REAR0
        rec = dict(end_x_measured=fx(x_end, 1), z_far_corner_at_measured_end=fx(p[1], 1), clear_to_footplate_top=fx(p[1] + 119.9, 1),
                   axle_centre_s=fx(s_ax, 1), axle_centre_n_away=fx(n_ax, 1))
        # rail must stop short of the D48.3 axle (+2 mm): square end at s_cut
        s_cut = s_ax + math.sqrt(max(0.0, (24.15 + 2.0) ** 2 - 0.0)) if False else None
        # square end (normal to the rail) that clears the axle circle r 26.2 anywhere in the band n = -12.5..D
        for s in np.arange(s_ax, s_ax + 150, 0.5):
            if all(np.hypot(s - s_ax, n - n_ax) > 26.2 for n in np.linspace(0, L.D, 91)):
                s_cut = s; break
        q = L.from_rail(s_cut, L.D, 35.0, "lo") + F.REAR0; q0 = L.from_rail(s_cut, 0.0, 35.0, "lo") + F.REAR0
        rec.update(end_cut_s=fx(s_cut, 1), end_cut_x_far=fx(q[0], 1), z_far_corner_at_cut=fx(q[1], 1), clear_far_corner_to_footplate=fx(q[1] + 119.9, 1),
                   end_cut_x_tip=fx(q0[0], 1), cut_back_along_rail_from_measured_end=fx(s_cut - s_end, 1),
                   note="square end normal to the rail, 2 mm clear of the D48.3 axle; hook plate (supports review) bridges to the axle")
        base[side] = rec
    g["base_end"] = base
    return g

OUT["geometry"] = geometry()

# ================================================================== B. side frame (in-plane)
CASES = [("ULS crowd", None, "crowd all"), ("ULS crowd", {0, 1, 2}, "crowd lower 3"), ("ULS crowd", {3, 4, 5}, "crowd upper 3")]
PATCH = [k for k in F.C if k.startswith("ULS 4 kN")]
SLOTS_LO = {s: [sp for r in OUT["geometry"]["slots"][s] for sp in r["_lo"]] for s in SIDES}
SLOTS_UP = {s: [sp for r in OUT["geometry"]["slots"][s] for sp in r["_up"]] for s in SIDES}
for s_ in SIDES:
    for r in OUT["geometry"]["slots"][s_]:
        r.pop("_lo"); r.pop("_up")
NOTCH = {"up": OUT["geometry"]["tab"]["notch_centres_upper_rail_s"], "lo": OUT["geometry"]["tab"]["notch_centres_lower_rail_s"]}

def station_types(side, lev, s):
    kinds = []
    if any(abs(s - i * L.PITCH) <= L.CAP_CUT[0] / 2 + 1 for i in range(6)): kinds.append("hole")
    nt = any(abs(s - c) <= L.NOTCH_W / 2 + 1 for c in NOTCH[lev])
    sl = any(abs(s - c) <= ln / 2 + 1 for c, ln in (SLOTS_UP[side] if lev == "up" else SLOTS_LO[side]))
    if nt and sl: kinds.append("notch+slot_" + lev)
    elif nt: kinds.append("notch")
    elif sl: kinds.append("slot_" + lev)
    return kinds or ["gross"]

def inplane_check(side, out):
    res = {}
    for lev in ("lo", "up"):
        worst = (0.0, None)
        for s, N, M in out["rail_" + lev]:
            for t in station_types(side, lev, s):
                p = PROPS[t]; sig = abs(N) / p["A"] + abs(M) / min(p["W_tip"], p["W_far"])
                if sig > worst[0]: worst = (sig, dict(s=fx(s, 0), N=fx(N, 0), M=fx(M, 0), section=t))
        res[lev] = dict(sigma=fx(worst[0], 1), util=fx(worst[0] / L.FD, 3), **worst[1])
    return res

frame = {"lock_lower_only": {}, "uls": {}, "sls": {}, "pins": [], "lock_forces": []}
for side in SIDES:
    o = F.run(side, F.pin_forces("ULS crowd", side), lock_upper=False)
    frame["lock_lower_only"][side] = dict(max_displacement_mm=fx(o["disp_max"], 0), note="mechanism - not a valid lock")
for side in SIDES:
    for slide in (False, True):
        bl = "base slides" if slide else "base held"
        for case, only, lab in CASES:
            fo = F.pin_forces(case, side, only); o = F.run(side, fo, base_slides=slide)
            key = f"{side} | {lab} | {bl}"
            frame["uls"][key] = inplane_check(side, o); frame["uls"][key]["links_kN"] = [fx(v / 1e3, 2) for v in o["links"].values()]
            for pr in F.pin_resultants(o, fo): frame["pins"].append(dict(case=key, **pr))
            for pf in o["pole_rail"]: frame["lock_forces"].append(dict(case=key, **pf))
        for case in PATCH:
            for i in range(6):
                p = F.C[case]["pins"]; r, f = p[f"{side}_rear"], p[f"{side}_front"]
                fo = {j: ({"rear": (-r[0], -r[2]), "front": (-f[0], -f[2])} if j == i else {"rear": (0, 0), "front": (0, 0)}) for j in range(6)}
                o = F.run(side, fo, base_slides=slide); key = f"{side} | {case} on tread {i} | {bl}"
                for pr in F.pin_resultants(o, fo): frame["pins"].append(dict(case=key, **pr))
                frame["uls"][key] = inplane_check(side, o)
S_, U_ = F.C["SLS crowd 7.5 kN/m2"]["pins"], F.C["ULS crowd"]["pins"]
for side in SIDES:
    for slide in (False, True):
        parts = {}
        for k in ("rear", "front"):
            s_, u_ = np.array(S_[f"{side}_{k}"]), np.array(U_[f"{side}_{k}"]); gq = (1.5 * s_ - u_) / 0.15; parts[k] = (gq, s_ - gq)
        mk = lambda fg, fq: {i: {k: (-(fg * parts[k][0] + fq * parts[k][1])[0], -(fg * parts[k][0] + fq * parts[k][1])[2]) for k in ("rear", "front")} for i in range(6)}
        d = F.run(side, mk(1.0, 1.0), factor_sw=1.0, base_slides=slide)["disp_max"]
        df = F.run(side, mk(1.0, 0.3), factor_sw=1.0, base_slides=slide)["disp_max"]
        frame["sls"][f"{side} {'base slides' if slide else 'base held'}"] = dict(sag=fx(d, 2), limit=fx(1831 / 250, 2), util=fx(d / (1831 / 250), 3), f1=fx(17.75 / math.sqrt(df), 1))
worst_in = {}
for lev in ("lo", "up"):
    for side in SIDES:
        rows = [(v[lev]["util"], k, v[lev]) for k, v in frame["uls"].items() if k.startswith(side)]
        u, k, v = max(rows, key=lambda r: r[0]); worst_in[f"{side}_{lev}"] = dict(case=k, **v)
frame["worst_inplane"] = worst_in
pmax = max(frame["pins"], key=lambda p: max(p["lo_abs"], p["up_abs"]))
frame["pin_force_max"] = dict(N=fx(max(pmax["lo_abs"], pmax["up_abs"]), 0), case=pmax["case"], tread=pmax["i"])
# largest force component pushing a pin toward its rail's touching plane (tip): lower rail +n_up, upper rail -n_up
tipward = []
for p in frame["pins"]:
    tipward.append(p["lo"][1]); tipward.append(-p["up"][1])
frame["pin_force_toward_tip_max"] = fx(max(tipward), 0)
frame["fold_lock_Fz_max_kN"] = {lev: fx(max(abs(r["Fz"]) for r in frame["lock_forces"] if r["lev"] == lev) / 1e3, 2) for lev in ("lo", "up")}
frame["fold_lock_Fx_max_kN"] = {lev: fx(max(abs(r["Fx"]) for r in frame["lock_forces"] if r["lev"] == lev) / 1e3, 2) for lev in ("lo", "up")}
frame["pins"] = sorted(frame["pins"], key=lambda p: -max(p["lo_abs"], p["up_abs"]))[:8]
frame["lock_forces"] = None
OUT["frame"] = frame

# ================================================================== C. barrier
HK = {"R142 5.0 kN/m viewing": 5.0 * 250 / math.cos(math.radians(35)), "R142 3.0 kN/m": 3.0 * 250 / math.cos(math.radians(35)),
      "R179 1.5 kN post": 1500.0, "R143 1.25 kN": 1250.0}
CONT = {"R142 5.0 kN/m viewing": 1.13, "R142 3.0 kN/m": 1.13, "R179 1.5 kN post": 1.0, "R143 1.25 kN": 1.0}
K05 = {s: next(h for h in G[s]["hand_rails"] if h["mat"].startswith("K05")) for s in SIDES}
def zline(h, x):
    (x0, z0), (x1, z1) = h["a"], h["b"]; return z0 + (z1 - z0) * (x - x0) / (x1 - x0)

def lateral_beam(lev, loads, s0, s1):
    """continuous beam in lateral bending over the 6 pins (+ both hook ends of the lower rail). loads (s, P), P > 0 =
    pushed away from the steps. Returns M(s), pin reactions (> 0: the pin pulls the rail toward the step)."""
    EI = L.E_AL * PROPS["gross"]["In"]
    xs = sorted(set(list(np.arange(min(s0, s1), max(s0, s1), 5.0)) + [max(s0, s1)] + [i * L.PITCH for i in range(6)] + [s for s, _ in loads]))
    xs = np.array(xs); n = len(xs); K = np.zeros((2 * n, 2 * n)); Fv = np.zeros(2 * n)
    for e in range(n - 1):
        l = xs[e + 1] - xs[e]
        k = EI / l ** 3 * np.array([[12, 6 * l, -12, 6 * l], [6 * l, 4 * l * l, -6 * l, 2 * l * l], [-12, -6 * l, 12, -6 * l], [6 * l, 2 * l * l, -6 * l, 4 * l * l]])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]; K[np.ix_(idx, idx)] += k
    for s, P in loads: Fv[2 * int(np.argmin(abs(xs - s)))] += P
    sup = [int(np.argmin(abs(xs - i * L.PITCH))) for i in range(6)] + ([0, n - 1] if lev == "lo" else [])
    fixed = [2 * j for j in sup]; free = [d for d in range(2 * n) if d not in fixed]
    u = np.zeros(2 * n); u[free] = np.linalg.solve(K[np.ix_(free, free)], Fv[free]); R = K @ u - Fv
    Mx = []
    for e in range(n - 1):
        l = xs[e + 1] - xs[e]; v1, t1, v2, t2 = u[2 * e:2 * e + 4]
        Mx.append((xs[e], EI * (-6 / l ** 2 * v1 - 4 / l * t1 + 6 / l ** 2 * v2 - 2 / l * t2)))
    return dict(M=Mx, pins={i: -R[2 * sup[i]] for i in range(6)}, defl=float(max(abs(u[0::2]))))

N_S = -7.0; N_C = L.C_PIN + 15.0         # rocking: step pad contact on the tab (n = -7) and the far edge of the D30 cap washer
def barrier():
    res = {}
    for side in SIDES:
        rl = F.G[side]
        s_lo0 = cross_s(rl["rail_lo"]["a"][0] - X_REAR0, 35.0, "lo", L.C_PIN); s_lo1 = cross_s(rl["rail_lo"]["b"][0] - X_REAR0, 35.0, "lo", L.C_PIN)
        s_up0 = cross_s(rl["rail_up"]["a"][0] - X_REAR0, 35.0, "up", L.C_PIN); s_up1 = cross_s(rl["rail_up"]["b"][0] - X_REAR0, 35.0, "up", L.C_PIN)
        for hk, H in HK.items():
            for direction in ("outward", "inward"):
                Hd = 1.5 * H * CONT[hk]; sg = 1 if direction == "outward" else -1
                lu, ll, poles = [], [], []
                for x in POLES_X[side]:
                    xr = x - X_REAR0
                    s_u = cross_s(xr, 35.0, "up", L.N_MF); s_l = cross_s(xr, 35.0, "lo", L.N_MF)
                    if not (min(s_lo0, s_lo1) <= s_l <= max(s_lo0, s_lo1)): continue      # bottom pole: no lower crossing (poles review A8)
                    zu = (L.from_rail(s_u, L.N_MF, 35.0, "up") + F.REAR0)[1]; zl = (L.from_rail(s_l, L.N_MF, 35.0, "lo") + F.REAR0)[1]
                    L1 = zline(K05[side], x) - zu; sv = zu - zl
                    Fu = Hd * (1 + L1 / sv); Fl = Hd * L1 / sv
                    lu.append((s_u, sg * Fu)); ll.append((s_l, -sg * Fl))
                    poles.append(dict(x=fx(x, 1), L1=fx(L1, 0), s_vert=fx(sv, 0), F_up=fx(Fu / 1e3, 2), F_lo=fx(Fl / 1e3, 2), s_u=s_u, s_l=s_l, Fu=sg * Fu, Fl=-sg * Fl))
                bu = lateral_beam("up", lu, s_up0, s_up1); bl = lateral_beam("lo", ll, s_lo0, s_lo1)
                def torque_to_pins(tl):
                    tp = {i: 0.0 for i in range(6)}
                    for s, T in tl:
                        i0 = int(math.floor(s / L.PITCH))
                        if i0 < 0: tp[0] += T; continue
                        if i0 >= 5: tp[5] += T; continue
                        a = s - i0 * L.PITCH; tp[i0] += T * (L.PITCH - a) / L.PITCH; tp[i0 + 1] += T * a / L.PITCH
                    return tp
                Tu = torque_to_pins([(p["s_u"], p["Fu"] * L.E_TORQUE) for p in poles]); Tl = torque_to_pins([(p["s_l"], p["Fl"] * L.E_TORQUE) for p in poles])
                rec = dict(poles=[{k: v for k, v in p.items() if k in ("x", "L1", "s_vert", "F_up", "F_lo")} for p in poles])
                for lev, b, Tp in (("up", bu, Tu), ("lo", bl, Tl)):
                    pull = {i: b["pins"][i] for i in range(6)}
                    # pin/cap tension P and pad compression S >= 0: -P + S = -R, P(n_c-12.5) + S(12.5-n_s) >= T  ->  P = max(R, (T + R(12.5-n_s))/(n_c-n_s))
                    cap = {i: (max(pull[i], (abs(Tp[i]) + pull[i] * (L.C_PIN - N_S)) / (N_C - N_S)) if pull[i] > 0
                               else max(0.0, (abs(Tp[i]) + pull[i] * (L.C_PIN - N_S)) / (N_C - N_S))) for i in range(6)}
                    rec[lev] = dict(M_lat_max_kNm=fx(max(abs(m) for _, m in b["M"]) / 1e6, 3), pin_pull_max_kN=fx(max(0, max(pull.values())) / 1e3, 2),
                                    pin_push_max_kN=fx(max(0, -min(pull.values())) / 1e3, 2), T_pin_max_kNmm=fx(max(abs(v) for v in Tp.values()) / 1e3, 1),
                                    cap_tension_max_kN=fx(max(cap.values()) / 1e3, 2), defl_lat_mm=fx(b["defl"], 2), M=b["M"])
                res[f"{side} | {hk} | {direction}"] = rec
    return res
BAR = barrier()

# ================================================================== D. pins, caps, edges
DUP = dict(fy=450.0, fu=650.0, gM0=1.1, gM2=1.25)
def pin_checks():
    V = OUT["frame"]["pin_force_max"]["N"]; d = L.PIN_D; A = math.pi * d * d / 4; Wp = math.pi * d ** 3 / 32
    MRd = 1.5 * Wp * DUP["fy"] / DUP["gM0"]; FvRd = 0.6 * A * DUP["fu"] / DUP["gM2"]
    out = {"V_design_N": V}
    for model, lever in (("stud fixed in step end block", L.PAD + L.T_P / 2), ("pin in 8 mm end plate, simply bearing", 4.0 + L.PAD + L.T_P / 2)):
        M = V * lever
        out[model] = dict(lever=fx(lever, 2), M_kNmm=fx(M / 1e3, 1), bending=fx(M / MRd, 3), shear=fx(V / FvRd, 3), interaction=fx((M / MRd) ** 2 + (V / FvRd) ** 2, 3))
    # same checks for a 6082-T6 D16 pin (owner option) and a 6082-T6 D20 pin
    for dd, lab in ((16.0, "6082-T6 D16"), (20.0, "6082-T6 D20")):
        Wa = math.pi * dd ** 3 / 32; MRa = 1.5 * Wa * 250 / 1.25; Fva = 0.6 * math.pi * dd * dd / 4 * 295 / 1.25
        out[f"{lab} (stud, lever {L.PAD + L.T_P / 2:g})"] = dict(bending=fx(V * (L.PAD + L.T_P / 2) / MRa, 3), shear=fx(V / Fva, 3))
    out["bearing on 6 mm pin wall (T8.8 1.5 t d f0/gMp)"] = fx(V / (1.5 * L.T_P * d * L.F0 / L.GMP), 3)
    return out

def edge_checks():
    V = OUT["frame"]["pin_force_max"]["N"]; Ft = max(0.0, OUT["frame"]["pin_force_toward_tip_max"])
    a_tab = L.TAB_R - L.HOLE_D / 2
    return dict(t=L.T_P, a_req_full_resultant=fx(L.t88_a(V, L.T_P, L.HOLE_D), 2), a_at_tab=fx(a_tab, 2), util_at_tab=fx(L.t88_a(V, L.T_P, L.HOLE_D) / a_tab, 3),
                force_toward_tip_max_N=fx(Ft, 0), a_req_toward_tip=fx(L.t88_a(Ft, L.T_P, L.HOLE_D), 2) if Ft > 0 else 0.0,
                a_between_tabs_to_tip=fx(L.C_PIN - L.HOLE_D / 2, 2),
                note="between tabs the pin wall ends 4 mm below the hole; the tab (radius TAB_R) gives the edge metal at every pin")

def cap_checks():
    Tmax = max(max(c["up"]["cap_tension_max_kN"], c["lo"]["cap_tension_max_kN"]) for k, c in BAR.items() if "5.0" in k and "outward" in k) * 1e3
    Tcase = max(((k, max(c["up"]["cap_tension_max_kN"], c["lo"]["cap_tension_max_kN"])) for k, c in BAR.items() if "5.0" in k and "outward" in k), key=lambda t: t[1])[0]
    Tin = max(max(c["up"]["cap_tension_max_kN"], c["lo"]["cap_tension_max_kN"]) for k, c in BAR.items() if "R143" in k and "inward" in k) * 1e3
    d = L.PIN_D
    out = dict(design_pull_kN=fx(Tmax / 1e3, 2), governing_case=Tcase, inward_R143_pull_kN=fx(Tin / 1e3, 2))
    for dc in (6.0, 8.0):
        FvRd = 2 * 0.6 * math.pi * dc * dc / 4 * DUP["fu"] / DUP["gM2"]
        net = math.pi * d * d / 4 - (dc + 0.2) * d; FtRd = 0.9 * net * DUP["fu"] / DUP["gM2"]
        wall = (L.CAP_OD - d - 0.5) / 2
        bear = 2 * 1.5 * wall * dc * DUP["fy"] / DUP["gM0"]
        tear_cap = 2 * 2 * (8.0 - dc / 2) * wall * 0.6 * DUP["fu"] / DUP["gM2"]
        out[f"owner detail: plain cap + cross pin D{dc:g} (carries the pull)"] = dict(cross_pin_double_shear=fx(Tmax / FvRd, 3), pin_net_tension_at_cross_hole=fx(Tmax / FtRd, 3),
                                                                                    cap_wall_bearing=fx(Tmax / bear, 3), cap_end_tearout_8mm=fx(Tmax / tear_cap, 3))
    As = 157.0; FtRd = 0.9 * As * DUP["fu"] / DUP["gM2"]; net_x = As - 4.2 * 13.5
    out["recommended: castle cap nut M16 on the pin's threaded end + D4 cross pin (locking only)"] = dict(thread_tension=fx(Tmax / FtRd, 3), thread_tension_at_cross_hole=fx(Tmax / (0.9 * net_x * DUP["fu"] / DUP["gM2"]), 3),
        nut_thread_strip="castle nut M16 A4-80 / duplex, m = 0.8 d: full strength of the bolt (EN ISO 898-2 logic)", pin_cross_hole_outside_bending_zone=True)
    Ab = math.pi / 4 * (30.0 ** 2 - L.HOLE_D ** 2)
    out["D30 washer bearing on 6 mm pin wall"] = fx(Tmax / Ab / (1.5 * L.F0 / L.GMP), 3)
    out["pull-through, 6 mm wall, D30 washer (punching)"] = fx(Tmax / (math.pi * 30.0 * L.T_P * L.F0 / math.sqrt(3) / L.GMP), 3)
    return out

PIN = pin_checks(); EDGE = edge_checks(); CAP = cap_checks()

# ================================================================== E. combination (EN 1990 6.10: crowd + psi0 barrier, barrier + psi0 crowd)
def combos():
    out = {}
    for side in SIDES:
        for lev in ("lo", "up"):
            ip_all = {k: v[lev] for k, v in OUT["frame"]["uls"].items() if k.startswith(side) and "crowd" in k}
            ip = max(ip_all.values(), key=lambda v: v["util"])
            best = (0, None)
            for key, c in BAR.items():
                if not key.startswith(side) or "5.0" not in key: continue
                for s, M in c[lev]["M"]:
                    for t in station_types(side, lev, s):
                        p = PROPS[t]; sl = abs(M) / min(p["Wlat_in"], p["Wlat_out"])
                        sip = ip["sigma"] * (PROPS[ip["section"]]["W_tip"] / p["W_tip"]) if t != ip["section"] else ip["sigma"]
                        for name, v in (("crowd leads", sip + 0.7 * sl), ("barrier leads", 0.7 * sip + sl)):
                            if v > best[0]: best = (v, dict(case=key, s=fx(s, 0), section=t, sigma_inplane_uls_crowd=fx(sip, 1), sigma_lateral=fx(sl, 1), combo=name))
            out[f"{side}_{lev}"] = dict(sigma=fx(best[0], 1), util=fx(best[0] / L.FD, 3), **best[1],
                                        note="in-plane stress = worst crowd case anywhere on the rail, put at this section (conservative)")
    return out
COMB = combos()

# ================================================================== F. local checks at the slots
def local():
    out = {}
    Fu = max(p["F_up"] for k, c in BAR.items() if "5.0" in k and "outward" in k for p in c["poles"]) * 1e3
    # outer chord beside the upper slot: mid-flange ligament (LIG x T_MF) + outer wall (T_O x D) as an L, bending in the
    # flange plane (about the n axis), fixed at the slot ends, pole bearing spread over its 25/cos35 = 30.5 face
    rects = [(0, 0, L.LIG_OUT, L.T_MF), (L.LIG_OUT, -L.N_MF0, L.LIG_OUT + L.T_O, L.D - L.N_MF0)]
    A = sum((y1 - y0) * (z1 - z0) for y0, z0, y1, z1 in rects); yc = sum((y1 - y0) * (z1 - z0) * (y0 + y1) / 2 for y0, z0, y1, z1 in rects) / A
    I = sum((z1 - z0) * (y1 - y0) ** 3 / 12 + (y1 - y0) * (z1 - z0) * ((y0 + y1) / 2 - yc) ** 2 for y0, z0, y1, z1 in rects)
    Wc = I / max(yc, L.LIG_OUT + L.T_O - yc)
    for lab, Ls, FF in (("standard slot, R142 5.0 kN/m", L.UP_SLOTS["standard+catwalk"], Fu),
                        ("steep slot, R143 1.25 kN (crew stair)", L.UP_SLOTS["steep"], max(p["F_up"] for k, c in BAR.items() if "R143" in k and "outward" in k for p in c["poles"]) * 1e3)):
        M = FF * Ls / 12
        out[f"upper slot outer chord, {lab}"] = dict(F_kN=fx(FF / 1e3, 2), slot_len=fx(Ls, 1), chord_W=fx(Wc, 0), M_kNmm=fx(M / 1e3, 1),
                                                    util=fx(M / Wc / L.FD, 3), status="estimate: fixed-ended chord (outer ligament + outer wall), load over the slot")
    out["pole bearing on slot edge (6082)"] = fx(Fu / (L.T_MF / math.cos(math.radians(35)) * 25.0) / (1.5 * L.F0 / L.GMP), 3)
    # tongue bearing at the lower slot (lower rail push) on the mid flange
    Fl = max(p["F_lo"] for k, c in BAR.items() if "5.0" in k and "outward" in k for p in c["poles"]) * 1e3
    out["tongue bearing on lower slot edge"] = fx(Fl / (L.T_MF / math.cos(math.radians(35)) * 25.0) / (1.5 * L.F0 / L.GMP), 3)
    # lower mid flange strip beside the tongue slot under the shoulder (fold lock Fz): cantilever from the wall
    Fz = OUT["frame"]["fold_lock_Fz_max_kN"]["lo"] * 1e3
    b = (L.W_INT - L.SLOT_LO_W) / 2; w = 25.0 / math.cos(math.radians(35)) + 2 * b
    Mz = Fz / 2 * b / 2
    out["lower mid flange under the shoulder"] = dict(Fz_kN=fx(Fz / 1e3, 2), strip_b=fx(b, 1), util=fx(Mz / (w * L.T_MF ** 2 / 6) / L.FD, 3), status="estimate")
    Fzu = OUT["frame"]["fold_lock_Fz_max_kN"]["up"] * 1e3
    out["upper mid flange on the upper latch (2 x D10 under the flange, 8 mm from slot)"] = dict(Fz_kN=fx(Fzu / 1e3, 2),
        util=fx((Fzu / 2 * 8.0) / ((25 + 2 * 8) * L.T_MF ** 2 / 6) / L.FD, 3), status="estimate")
    return out
LOC = local()

# ================================================================== G. mass
Lr = {"lo": 1780.0, "up": 1850.0}
MASS = dict(section_area_mm2=fx(PROPS["gross"]["A"], 0), kg_per_m=fx(PROPS["gross"]["A"] * 2.7e-3, 2),
            four_rails_kg=fx(PROPS["gross"]["A"] * 2 * (Lr["lo"] + Lr["up"]) * 2.7e-6, 2),
            machining_removed_kg=fx(2 * 6 * 2 * (L.NOTCH_W * L.NOTCH_DEPTH * L.T_P + L.SLOT_UP_W * 45 * L.T_MF) * 2.7e-6, 2),
            rev_c_after_changes_rails_kg=14.65)

OUT["sections"] = {k: {q: fx(v, 1) for q, v in p.items()} for k, p in PROPS.items()}
OUT["classes"] = {e: dict(b=fx(r["b"], 1), t=r["t"], beta=fx(r["beta"], 2), cls=r["class"], rho=fx(r["rho"], 3)) for e, r in L.classify().items()}
OUT["barrier"] = {k: {kk: ({q: w for q, w in vv.items() if q != "M"} if isinstance(vv, dict) else vv) for kk, vv in v.items()} for k, v in BAR.items()}
OUT["pins"] = PIN; OUT["edges"] = EDGE; OUT["caps"] = CAP; OUT["combined"] = COMB; OUT["local"] = LOC; OUT["mass"] = MASS
OUT["params"] = {k: (fx(v, 3) if isinstance(v, float) else v) for k, v in vars(L).items() if k.isupper() and isinstance(v, (int, float, tuple, str))}
fn = os.path.join(HERE, f"rail_design_{L.POLE_KEY}.json")
json.dump(OUT, open(fn, "w"), indent=1, default=float)
if __name__ == "__main__":
    q = lambda o: json.dumps(o, indent=1, default=float)
    print("PARAMS W", L.W, "D", L.D, "W_INT", L.W_INT, "N_MF", L.N_MF, "TAB_R", round(L.TAB_R, 1), "NOTCH", round(L.NOTCH_DEPTH, 1))
    g = OUT["geometry"]; print(q({k: g[k] for k in g if k != "slots"})); print(q(g["slots"]["L"][:2]))
    print(q(OUT["frame"]["worst_inplane"])); print(q(OUT["frame"]["sls"]))
    print("pin max", OUT["frame"]["pin_force_max"], "tipward", OUT["frame"]["pin_force_toward_tip_max"], "lock", OUT["frame"]["fold_lock_Fz_max_kN"], OUT["frame"]["fold_lock_Fx_max_kN"], "lower-only", OUT["frame"]["lock_lower_only"])
    for k, v in OUT["barrier"].items():
        if "5.0" in k or "R143" in k: print(k, {z: v[z] for z in ("up", "lo")})
    print(q(PIN)); print(q(EDGE)); print(q(CAP)); print(q(COMB)); print(q(LOC)); print(MASS); print(q(OUT["classes"])); print(q(OUT["sections"]))
