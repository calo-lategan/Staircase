"""Rev C guide rails: every check for the rail family in rails_lib.py. Writes rail_design.json next to this file.
Run from anywhere:  python3 v2/revc/rails/run_rails.py
Sections: A kinematics/geometry, B side frame (in-plane), C barrier (lateral, torsion, pin pull), D pins/caps/edges,
E combination, F local slot ligament, G mass. Every number in rail_design.md comes from the JSON written here."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rails_lib as L
import frame_rails as F

OUT = {}
SIDES = ("L", "R")
KIND = L.RAIL_OF
fx = lambda v, n=2: round(float(v), n)

# ================================================================== A. kinematics and geometry
G = F.G
X_REAR0 = F.REAR0[0]
POLES_X = {s: [p["x"] for p in G[s]["poles"]] for s in SIDES}
n_web = lambda kind: L.DEPTH[kind] - L.T_WEB / 2            # web mid-plane, n_away
N_BULB = L.H_BULB / 2                                        # lateral bearing resultant on the bulb (n_away)

def cross_s(x_rel, theta, lev, n_away):
    """s where the vertical line x (relative to tread-0 rear pin) meets the line n_away of rail lev"""
    p0 = L.from_rail(0.0, n_away, theta, lev); u, nu = L.frame_state(theta)
    return (x_rel - p0[0]) / u[0]

def pole_footprint_gap(s_web, n_w, theta, lev, s_pin, r_cap):
    """clear distance between a vertical 25-along pole (crossing the web at s_web) and a cap disc at (s_pin, n=12.5)
    inside the rail interior; sampled over the rail depth"""
    u, nu = L.frame_state(theta); x_web = L.from_rail(s_web, n_w, theta, lev)[0]
    best = 1e9
    for n in np.linspace(L.C_PIN - r_cap, L.C_PIN + r_cap, 41):
        sc = cross_s(x_web, theta, lev, n); half = 12.5 / math.cos(math.radians(theta))
        dn = abs(n - L.C_PIN); chord = math.sqrt(max(r_cap ** 2 - dn ** 2, 0.0))
        best = min(best, max(0.0, abs(sc - s_pin) - half - chord) if abs(sc - s_pin) > half + chord else -(half + chord - abs(sc - s_pin)))
    return best

def geometry():
    g = {"pin_line_separation": {k: fx(L.sep(v), 1) for k, v in L.STATES.items()},
         "tip_gap": {k: fx(L.sep(v) - 2 * L.C_PIN, 1) for k, v in L.STATES.items()}}
    # --- pole slots: standard slots are defined by the stair; the pole re-uses the LOWER slot in every state
    slots = {}
    for side in SIDES:
        klo, kup = KIND[(side, "lo")], KIND[(side, "up")]
        rows = []
        for x in POLES_X[side]:
            xr = x - X_REAR0
            s_lo = cross_s(xr, 35.0, "lo", n_web(klo))
            s_lo_len = F.G[side]["rail_lo"]
            rec = dict(x=fx(x, 1), s_lo_web=fx(s_lo, 1))
            p_lo = L.from_rail(s_lo, n_web(klo), 35.0, "lo")
            for st, th in L.STATES.items():
                pl = L.from_rail(s_lo, n_web(klo), th, "lo")                 # same lower slot
                rec[f"s_up_web_{st}"] = fx(cross_s(pl[0], th, "up", n_web(kup)), 1)
                rec[f"vert_webs_{st}"] = fx(L.from_rail(cross_s(pl[0], th, "up", n_web(kup)), n_web(kup), th, "up")[1] - pl[1], 1)
            rows.append(rec)
        slots[side] = rows
    g["slots"] = slots
    # --- caps vs pole in every state (pins at s = i*PITCH on both rails in their own frames)
    capchk = []
    r_cap = L.CAP_OD / 2 + 1.0                       # cap + washer edge
    for side in SIDES:
        for lev in ("lo", "up"):
            kind = KIND[(side, lev)]
            for rec in slots[side]:
                for st, th in L.STATES.items():
                    s_web = rec["s_lo_web"] if lev == "lo" else rec[f"s_up_web_{st}"]
                    gaps = [pole_footprint_gap(s_web, n_web(kind), th, lev, i * L.PITCH, r_cap) for i in range(-1, 8)]
                    capchk.append(dict(side=side, lev=lev, state=st, x=rec["x"], min_gap=fx(min(gaps), 1)))
    g["cap_pole_min_gap"] = min(c["min_gap"] for c in capchk)
    g["cap_pole_worst"] = min(capchk, key=lambda c: c["min_gap"])
    # --- catwalk interleave: tab positions of one rail expressed on the other rail
    th = 0.0
    lo_tabs_on_up = [L.to_rail(L.from_rail(i * L.PITCH, 0.0, th, "lo"), th, "up")[0] for i in range(6)]
    up_tabs_on_lo = [L.to_rail(L.from_rail(i * L.PITCH, 0.0, th, "up"), th, "lo")[0] for i in range(6)]
    g["tab"] = dict(radius=fx(L.TAB_R, 1), width=fx(L.TAB_W, 1), reach_beyond_touching_plane=fx(L.TAB_H, 1),
                    notch_depth=fx(L.NOTCH_DEPTH, 1), notch_width=fx(L.NOTCH_W, 1),
                    notch_centres_upper_rail_s=[fx(v, 1) for v in lo_tabs_on_up], notch_centres_lower_rail_s=[fx(v, 1) for v in up_tabs_on_lo],
                    notch_to_own_hole_min=fx(min(min(abs(a - i * L.PITCH) for i in range(6)) for a in lo_tabs_on_up + up_tabs_on_lo) - L.NOTCH_W / 2 - L.HOLE_D / 2, 1))
    # fold-out: relative along-rail drift of a lower tab w.r.t. its notch while the tip gap opens to the tab reach
    drift = []
    for thd in np.linspace(0, 12, 121):
        s_now = L.to_rail(L.from_rail(0.0, 0.0, thd, "lo"), thd, "up")[0]
        gap = L.sep(thd) - 2 * L.C_PIN
        drift.append((thd, gap, s_now - lo_tabs_on_up[0]))
    clear = next(d for d in drift if d[1] >= L.NOTCH_DEPTH + 0.5)
    g["fold_out"] = dict(angle_tabs_clear_deg=fx(clear[0], 1), drift_at_clear_mm=fx(abs(clear[2]), 2), notch_side_clearance=L.NOTCH_CLR)
    # --- neighbour's step end (owner L envelope) reach into each rail zone (for the nested left rail's outer leg)
    def env_pts():
        pts = []
        for x in np.linspace(0, 280, 57):
            for z in np.linspace(25, 50, 6): pts.append((x, z))
        for x in np.linspace(0, 50, 11):
            for z in np.linspace(0, 25, 6): pts.append((x, z))
        return pts
    reach = {}
    for st, thd in L.STATES.items():
        for lev in ("lo", "up"):
            nmax = -1e9
            for i in range(6):
                for (x, z) in env_pts():
                    rp = L.from_rail(i * L.PITCH, L.C_PIN, thd, "lo")          # tread i rear pin (on the lower pin line)
                    p = rp + np.array([x - L.REAR[0], z - L.REAR[1]])
                    s, n = L.to_rail(p, thd, lev)
                    nmax = max(nmax, n)
            reach[f"{lev}_{st}"] = fx(nmax, 1)
    g["step_end_reach_n_away"] = reach
    g["A_lo_outer_leg_start"] = L.N_OUT_LO_A
    g["A_lo_outer_leg_clear"] = fx(L.N_OUT_LO_A - max(v for k, v in reach.items() if k.startswith("lo")), 1)
    # --- ground clearance at the base end (standard state, measured rail end x)
    base = {}
    for side in SIDES:
        kind = KIND[(side, "lo")]; x_end = F.G[side]["rail_lo"]["a"][0]
        far = L.DEPTH[kind]
        s_end = cross_s(x_end - X_REAR0, 35.0, "lo", L.C_PIN)
        # lowest corner of a square-cut end at s_end: far face
        p = L.from_rail(s_end, far, 35.0, "lo") + F.REAR0
        base[side] = dict(end_x=fx(x_end, 1), z_far_corner=fx(p[1], 1), clear_to_footplate_top=fx(p[1] - (-119.9), 1),
                          clear_to_ground=fx(p[1] - (-124.9), 1))
        # where the far face crosses the footplate top + 10 mm: trim point
        for s in np.linspace(s_end, s_end + 300, 3001):
            q = L.from_rail(s, far, 35.0, "lo") + F.REAR0
            if q[1] >= -119.9 + 10.0:
                base[side]["trim_far_face_to_x"] = fx(q[0], 1); base[side]["trim_len_along_rail"] = fx(s - s_end, 1); break
        pa = F.AXLE_BASE; c = np.array(pa) - F.REAR0
        base[side]["axle_centre_n_away"] = fx(L.to_rail(c, 35.0, "lo")[1], 1)
    g["base_end"] = base
    return g

OUT["geometry"] = geometry()

# ================================================================== B. side frame (in-plane)
CASES = [("ULS crowd", None, "crowd all"), ("ULS crowd", {0, 1, 2}, "crowd lower 3"), ("ULS crowd", {3, 4, 5}, "crowd upper 3")]
PATCH = [k for k in F.C if k.startswith("ULS 4 kN")]

def station_type(side, lev, s, s_slots, notch_c):
    kinds = []
    if any(abs(s - i * L.PITCH) <= L.HOLE_D / 2 + 2 for i in range(6)): kinds.append("hole")
    if any(abs(s - c) <= L.NOTCH_W / 2 + 1 for c in notch_c): kinds.append("notch")
    slot_len = (L.SLOT_UP if lev == "up" else L.SLOT_LO)[1]
    if any(abs(s - c) <= slot_len / 2 + 1 for c in s_slots): kinds.append("slot")
    return kinds or ["gross"]

SECS = {k: L.sections(k) for k in ("A_lo", "B_lo", "A_up", "B_up")}
PROPS = {k: {n: s.props() for n, s in v.items()} for k, v in SECS.items()}

def slot_positions(side, lev):
    rows = OUT["geometry"]["slots"][side]
    if lev == "lo": return [r["s_lo_web"] for r in rows]
    return sorted(set(r[f"s_up_web_{st}"] for r in rows for st in L.STATES))

def notch_positions(lev):
    t = OUT["geometry"]["tab"]
    return t["notch_centres_upper_rail_s"] if lev == "up" else t["notch_centres_lower_rail_s"]

def inplane_check(side, out, label):
    res = {}
    for lev in ("lo", "up"):
        kind = KIND[(side, lev)]; ss, nc = slot_positions(side, lev), notch_positions(lev)
        worst = (0.0, None)
        for s, N, M in out["rail_" + lev]:
            for t in station_type(side, lev, s, ss, nc):
                p = PROPS[kind][t]
                sig = abs(N) / p["A"] + abs(M) / min(p["W_tip"], p["W_far"])
                if sig > worst[0]: worst = (sig, dict(s=fx(s, 0), N=fx(N, 0), M=fx(M, 0), section=t))
        res[lev] = dict(sigma=fx(worst[0], 1), util=fx(worst[0] / L.FD, 3), **worst[1])
    return res

frame = {"lock_lower_only_mechanism": {}, "uls": {}, "sls": {}, "pins": [], "lock_forces": []}
for side in SIDES:
    o = F.run(side, F.pin_forces("ULS crowd", side), base_slides=False, lock_upper=False)
    frame["lock_lower_only_mechanism"][side] = fx(o["disp_max"], 0)
env = {}
for side in SIDES:
    for slide in (False, True):
        for case, only, lab in CASES:
            fo = F.pin_forces(case, side, only); o = F.run(side, fo, base_slides=slide, lock_upper=True)
            key = f"{side} | {lab} | {'base slides' if slide else 'base held'}"
            frame["uls"][key] = inplane_check(side, o, key)
            frame["uls"][key]["links_kN"] = [fx(v / 1e3, 2) for v in o["links"].values()]
            for pr in F.pin_resultants(o, fo): frame["pins"].append(dict(case=key, **pr))
            for pf in o["pole_rail"]: frame["lock_forces"].append(dict(case=key, **pf))
            env[key] = o
        # tread point loads: 4 kN patch on each tread in turn (crowd elsewhere not added: separate case)
        for case in PATCH:
            for i in range(6):
                p = F.C[case]["pins"]; r, f = p[f"{side}_rear"], p[f"{side}_front"]
                fo = {j: ({"rear": (-r[0], -r[2]), "front": (-f[0], -f[2])} if j == i else {"rear": (0, 0), "front": (0, 0)}) for j in range(6)}
                o = F.run(side, fo, base_slides=slide, lock_upper=True)
                key = f"{side} | {case} on tread {i} | {'base slides' if slide else 'base held'}"
                for pr in F.pin_resultants(o, fo): frame["pins"].append(dict(case=key, **pr))
                ic = inplane_check(side, o, key)
                frame["uls"][key] = ic
# SLS sag and frequency (as frame_after.py: G + Q and G + 0.3 Q, self weight factor 1.0)
S, U_ = F.C["SLS crowd 7.5 kN/m2"]["pins"], F.C["ULS crowd"]["pins"]
for side in SIDES:
    for slide in (False, True):
        parts = {}
        for k in ("rear", "front"):
            s_, u_ = np.array(S[f"{side}_{k}"]), np.array(U_[f"{side}_{k}"]); gq = (1.5 * s_ - u_) / 0.15; parts[k] = (gq, s_ - gq)
        mk = lambda fg, fq: {i: {k: (-(fg * parts[k][0] + fq * parts[k][1])[0], -(fg * parts[k][0] + fq * parts[k][1])[2]) for k in ("rear", "front")} for i in range(6)}
        d = F.run(side, mk(1.0, 1.0), factor_sw=1.0, base_slides=slide, lock_upper=True)["disp_max"]
        df = F.run(side, mk(1.0, 0.3), factor_sw=1.0, base_slides=slide, lock_upper=True)["disp_max"]
        frame["sls"][f"{side} {'base slides' if slide else 'base held'}"] = dict(sag=fx(d, 2), limit=fx(1831 / 250, 2), util=fx(d / (1831 / 250), 3), f1=fx(17.75 / math.sqrt(df), 1))
worst_in = {}
for lev in ("lo", "up"):
    for side in SIDES:
        rows = [(v[lev]["util"], k, v[lev]) for k, v in frame["uls"].items() if k.startswith(side)]
        u, k, v = max(rows, key=lambda r: r[0]); worst_in[f"{side}_{lev}"] = dict(case=k, **v)
frame["worst_inplane"] = worst_in
pmax = max(frame["pins"], key=lambda p: max(p["lo_abs"], p["up_abs"]))
frame["pin_force_max"] = dict(N=fx(max(pmax["lo_abs"], pmax["up_abs"]), 0), case=pmax["case"], tread=pmax["i"])
lk = max(frame["lock_forces"], key=lambda r: abs(r["Fz"]))
frame["fold_lock_max"] = dict(Fz_kN=fx(abs(lk["Fz"]) / 1e3, 2), Fx_kN=fx(abs(lk["Fx"]) / 1e3, 2), lev=lk["lev"], case=lk["case"])
frame["fold_lock_max_by_level"] = {lev: fx(max(abs(r["Fz"]) for r in frame["lock_forces"] if r["lev"] == lev) / 1e3, 2) for lev in ("lo", "up")}
frame["fold_lock_x_by_level"] = {lev: fx(max(abs(r["Fx"]) for r in frame["lock_forces"] if r["lev"] == lev) / 1e3, 2) for lev in ("lo", "up")}
frame["pins"] = sorted(frame["pins"], key=lambda p: -max(p["lo_abs"], p["up_abs"]))[:12]
frame["lock_forces"] = None
OUT["frame"] = frame

# ================================================================== C. barrier: couple, lateral bending, torsion, pin pull
HK = {"R142 5.0 kN/m viewing": 5.0 * 250 / math.cos(math.radians(35)), "R142 3.0 kN/m": 3.0 * 250 / math.cos(math.radians(35)),
      "R179 1.5 kN post": 1500.0, "R143 1.25 kN": 1250.0}
CONT = {"R142 5.0 kN/m viewing": 1.13, "R142 3.0 kN/m": 1.13, "R179 1.5 kN post": 1.0, "R143 1.25 kN": 1.0}
K05 = {s: next(h for h in G[s]["hand_rails"] if h["mat"].startswith("K05")) for s in SIDES}
def zline(h, x):
    (x0, z0), (x1, z1) = h["a"], h["b"]; return z0 + (z1 - z0) * (x - x0) / (x1 - x0)

def lateral_beam(kind, lev, side, loads, s0, s1):
    """continuous beam in lateral bending: supports at the 6 pins (+ both ends of the lower rail: hook/axle collars).
    loads: list of (s, P) with P > 0 = pushed AWAY from the steps. Returns M(s), reactions at pins (>0 = pin pulled)."""
    I = PROPS[kind]["gross"]["In"]; EI = L.E_AL * I
    xs = sorted(set(list(np.arange(min(s0, s1), max(s0, s1), 5.0)) + [max(s0, s1)] + [i * L.PITCH for i in range(6)] + [s for s, _ in loads]))
    xs = np.array(xs); n = len(xs); K = np.zeros((2 * n, 2 * n)); Fv = np.zeros(2 * n)
    for e in range(n - 1):
        l = xs[e + 1] - xs[e]
        k = EI / l ** 3 * np.array([[12, 6 * l, -12, 6 * l], [6 * l, 4 * l * l, -6 * l, 2 * l * l], [-12, -6 * l, 12, -6 * l], [6 * l, 2 * l * l, -6 * l, 4 * l * l]])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]; K[np.ix_(idx, idx)] += k
    for s, P in loads: Fv[2 * int(np.argmin(abs(xs - s)))] += P
    sup = [int(np.argmin(abs(xs - i * L.PITCH))) for i in range(6)]
    if lev == "lo": sup += [0, n - 1]
    fixed = [2 * j for j in sup]; free = [d for d in range(2 * n) if d not in fixed]
    u = np.zeros(2 * n); u[free] = np.linalg.solve(K[np.ix_(free, free)], Fv[free])
    R = K @ u - Fv
    Mx = []
    for e in range(n - 1):
        l = xs[e + 1] - xs[e]; v1, t1, v2, t2 = u[2 * e:2 * e + 4]
        Mx.append((xs[e], EI * (-6 / l ** 2 * v1 - 4 / l * t1 + 6 / l ** 2 * v2 - 2 / l * t2)))
    pins = {i: -R[2 * sup[i]] for i in range(6)}          # reaction force the pin must give; >0: pin pulls the rail toward the step
    return dict(M=Mx, pins=pins, ends=[-R[2 * j] for j in sup[6:]], defl=float(max(abs(u[0::2]))))

def barrier():
    res = {"cases": {}}
    for side in SIDES:
        klo, kup = KIND[(side, "lo")], KIND[(side, "up")]
        rl = F.G[side]
        s_lo0 = cross_s(rl["rail_lo"]["a"][0] - X_REAR0, 35.0, "lo", L.C_PIN); s_lo1 = cross_s(rl["rail_lo"]["b"][0] - X_REAR0, 35.0, "lo", L.C_PIN)
        s_up0 = cross_s(rl["rail_up"]["a"][0] - X_REAR0, 35.0, "up", L.C_PIN); s_up1 = cross_s(rl["rail_up"]["b"][0] - X_REAR0, 35.0, "up", L.C_PIN)
        for hk, H in HK.items():
            for direction in ("outward", "inward"):
                Hd = 1.5 * H * CONT[hk]
                # bearing levels (n_away): outward -> upper at its far web, lower at its bulb; inward -> upper bulb, lower far web
                n_up_b = n_web(kup) if direction == "outward" else N_BULB
                n_lo_b = N_BULB if direction == "outward" else n_web(klo)
                loads_up, loads_lo, poles = [], [], []
                for x in POLES_X[side]:
                    xr = x - X_REAR0
                    s_u = cross_s(xr, 35.0, "up", n_up_b); s_l = cross_s(xr, 35.0, "lo", n_lo_b)
                    zu = (L.from_rail(s_u, n_up_b, 35.0, "up") + F.REAR0)[1]; zl = (L.from_rail(s_l, n_lo_b, 35.0, "lo") + F.REAR0)[1]
                    L1 = zline(K05[side], x) - zu; sv = zu - zl
                    on_lo = min(s_lo0, s_lo1) <= s_l <= max(s_lo0, s_lo1)
                    if not on_lo: continue                     # bottom pole: no lower-rail crossing (poles review A8) - separate detail
                    Fu = Hd * (1 + L1 / sv); Fl = Hd * L1 / sv
                    # sign: outward load pushes the UPPER rail away from the steps (+), the LOWER rail toward the steps (-)
                    sg = 1 if direction == "outward" else -1
                    loads_up.append((s_u, sg * Fu)); loads_lo.append((s_l, -sg * Fl))
                    e_up = (n_up_b - L.C_PIN); e_lo = (n_lo_b - L.C_PIN)
                    poles.append(dict(x=fx(x, 1), L1=fx(L1, 0), s_vert=fx(sv, 0), F_up=fx(Fu / 1e3, 2), F_lo=fx(Fl / 1e3, 2),
                                      T_up=fx(sg * Fu * e_up / 1e3, 1), T_lo=fx(-sg * Fl * e_lo / 1e3, 1), s_up=s_u, s_lo=s_l))
                bu = lateral_beam(kup, "up", side, loads_up, s_up0, s_up1); bl = lateral_beam(klo, "lo", side, loads_lo, s_lo0, s_lo1)
                # torsion: each pole's torque split to the two adjacent pins (simple-span share); rocking lever on the tab pad
                def torque_to_pins(tlist):
                    tp = {i: 0.0 for i in range(6)}
                    for s, T in tlist:
                        i0 = int(math.floor(s / L.PITCH)); i1 = i0 + 1
                        if i0 < 0: tp[0] += T; continue
                        if i1 > 5: tp[5] += T; continue
                        a = s - i0 * L.PITCH; tp[i0] += T * (L.PITCH - a) / L.PITCH; tp[i1] += T * a / L.PITCH
                    return tp
                Tup = torque_to_pins([(p["s_up"], p["T_up"] * 1e3) for p in poles]); Tlo = torque_to_pins([(p["s_lo"], p["T_lo"] * 1e3) for p in poles])
                lever = L.TAB_R - 5.0
                key = f"{side} | {hk} | {direction}"
                rec = dict(poles=[{k: v for k, v in p.items() if not k.startswith("s_")} for p in poles])
                for lev, b, Tp, kind in (("up", bu, Tup, kup), ("lo", bl, Tlo, klo)):
                    Mmax = max(abs(m) for _, m in b["M"])
                    pull = {i: max(0.0, b["pins"][i]) for i in range(6)}
                    cap = {i: pull[i] + abs(Tp[i]) / lever for i in range(6)}
                    rec[lev] = dict(M_lat_max=fx(Mmax / 1e6, 3), pin_pull_max_kN=fx(max(pull.values()) / 1e3, 2), pin_push_max_kN=fx(max(0, -min(b["pins"].values())) / 1e3, 2),
                                    T_pin_max_kNmm=fx(max(abs(v) for v in Tp.values()) / 1e3, 1), cap_tension_max_kN=fx(max(cap.values()) / 1e3, 2),
                                    rock_lever=fx(lever, 1), defl_lat=fx(b["defl"], 2), M=b["M"])
                res["cases"][key] = rec
    return res

BAR = barrier()

# ================================================================== D. pins, caps, edges, bearing, end block
DUP = dict(fy=450.0, fu=650.0, gM0=1.1, gM2=1.25)           # 1.4462 duplex bar, EN 10088-3 (Rp0.2 >= 450), EN 1993-1-4 factors
def pin_checks():
    V = OUT["frame"]["pin_force_max"]["N"]
    out = {}
    d = L.PIN_D; A = math.pi * d * d / 4; W = math.pi * d ** 3 / 32
    MRd = 1.5 * W * DUP["fy"] / DUP["gM0"]; FvRd = 0.6 * A * DUP["fu"] / DUP["gM2"]
    for side, bulb in (("L", L.BULB_A), ("R", L.BULB_B)):
        t_leg = L.T_LEG + bulb
        for model, lever in (("stud fixed in step end block", L.PAD + t_leg / 2), ("pin in 8 mm end plate (simply bearing)", 4.0 + L.PAD + t_leg / 2)):
            M = V * lever
            out[f"{side} | {model}"] = dict(lever=fx(lever, 2), M_kNmm=fx(M / 1e3, 1), bending=fx(M / MRd, 3), shear=fx(V / FvRd, 3),
                                            interaction=fx((M / MRd) ** 2 + (V / FvRd) ** 2, 3))
        # bearing on the aluminium leg (EN 1999-1-1 T8.8: 1.5 t d f0 / gMp)
        out[f"{side} | bearing on rail leg"] = dict(t=t_leg, util=fx(V / (1.5 * t_leg * d * L.F0 / L.GMP), 3))
    return out

def edge_checks():
    """hole edge to the leg tip (touching plane) incl. tab: T8.8 with the force component toward the tip, and the
    rule 'metal all round >= a_req for the full resultant' used to size the tab"""
    rows = []
    for p in OUT["frame"]["pins"]:
        pass
    # recompute worst force components toward the tip over all stored pins (top 12 by magnitude) + full resultant
    V = OUT["frame"]["pin_force_max"]["N"]
    for side, bulb in (("L", L.BULB_A), ("R", L.BULB_B)):
        t = L.T_LEG + bulb
        a_req = L.t88_a(V, t, L.HOLE_D); a_have_tip = L.C_PIN - L.HOLE_D / 2; a_have_tab = L.TAB_R - L.HOLE_D / 2
        rows.append(dict(side=side, t=t, a_req_full_resultant=fx(a_req, 2), a_at_tab=fx(a_have_tab, 2), util_tab=fx(a_req / a_have_tab, 3),
                         a_between_tabs_tip=fx(a_have_tip, 2)))
    return rows

def cap_checks():
    """locking cap on the pin end inside the rail, cross-pin through cap + pin. Axial pull = barrier pin pull + rocking."""
    Tmax = max(max(c["up"]["cap_tension_max_kN"], c["lo"]["cap_tension_max_kN"]) for c in BAR["cases"].values()) * 1e3
    Tcase = max(BAR["cases"].items(), key=lambda kv: max(kv[1]["up"]["cap_tension_max_kN"], kv[1]["lo"]["cap_tension_max_kN"]))[0]
    d = L.PIN_D; out = dict(design_pull_kN=fx(Tmax / 1e3, 2), governing_case=Tcase)
    # variant 1 (owner): plain cap + cross pin carrying the pull in double shear
    for dc in (6.0, 8.0):
        Av = math.pi * dc * dc / 4
        FvRd = 2 * 0.6 * Av * DUP["fu"] / DUP["gM2"]
        net = math.pi * d * d / 4 - (dc + 0.2) * d
        FtRd = 0.9 * net * DUP["fu"] / DUP["gM2"]
        cap_OD, cap_len = L.CAP_OD, 22.0
        wall = (cap_OD - d - 0.5) / 2
        bear_cap = 2 * 1.5 * wall * dc * DUP["fy"] / DUP["gM0"]
        tear_cap = 2 * 2 * (8.0 - dc / 2) * wall * 0.6 * DUP["fu"] / DUP["gM2"]      # two walls, two shear planes, end distance 8 from cross-hole centre to cap end
        tear_pin = 2 * (10.0 - dc / 2) * d * 0.6 * DUP["fu"] / DUP["gM2"] * 0.5       # pin end beyond the cross hole (10 mm), two planes, conservative 0.5 (round bar)
        out[f"plain cap, cross pin D{dc:g}"] = dict(cross_pin_double_shear=fx(Tmax / FvRd, 3), pin_net_tension_at_cross_hole=fx(Tmax / FtRd, 3),
                                                   cap_wall_bearing=fx(Tmax / bear_cap, 3), cap_end_tearout=fx(Tmax / tear_cap, 3), pin_end_tearout=fx(Tmax / tear_pin, 3))
    # variant 2 (recommended): threaded cap nut M16 (1.4462 pin threaded beyond the leg), cross pin D4 locks rotation only
    As = 157.0; FtRd = 0.9 * As * DUP["fu"] / DUP["gM2"]; net_x = As - 4.2 * 13.5
    out["threaded cap M16 + D4 cross pin (locking only)"] = dict(thread_tension=fx(Tmax / FtRd, 3), thread_tension_at_cross_hole=fx(Tmax / (0.9 * net_x * DUP["fu"] / DUP["gM2"]), 3),
                                                                   note="cross pin carries no axial load; cap tightened to 20 Nm before the cross hole is lined up (castle slots every 60 deg)")
    # cap / washer bearing on the aluminium bulb face and pull-through of the leg
    wash_OD = 30.0; Ab = math.pi / 4 * (wash_OD ** 2 - L.HOLE_D ** 2)
    out["washer bearing on bulb"] = fx(Tmax / Ab / (1.5 * L.F0 / L.GMP), 3)
    tmin = L.T_LEG + L.BULB_B
    out["pull-through of leg (punching, t=14)"] = fx(Tmax / (math.pi * wash_OD * tmin * L.F0 / math.sqrt(3) / L.GMP), 3)
    return out

PIN = pin_checks(); EDGE = edge_checks(); CAP = cap_checks()

# ================================================================== E. combination in-plane + lateral (EN 1990 6.10, psi0 = 0.7)
def combos():
    out = {}
    for side in SIDES:
        for lev in ("lo", "up"):
            kind = KIND[(side, lev)]
            ip = OUT["frame"]["worst_inplane"][f"{side}_{lev}"]
            best = (0, None)
            for key, c in BAR["cases"].items():
                if not key.startswith(side) or not key.split(" | ")[1].startswith("R142 5.0"): continue
                for s, M in c[lev]["M"]:
                    for t in station_type(side, lev, s, slot_positions(side, lev), notch_positions(lev)):
                        p = PROPS[kind][t]; sl = abs(M) / min(p["Wlat_in"], p["Wlat_out"])
                        # in-plane stress at that section type (worst along the rail, conservative: same station not required)
                        sip = ip["sigma"] * (PROPS[kind][ip["section"]]["W_tip"] / p["W_tip"] if t != ip["section"] else 1.0)
                        for name, v in (("crowd lead", sip + 0.7 * sl), ("barrier lead", 0.7 * sip + sl)):
                            if v > best[0]: best = (v, dict(case=key, s=fx(s, 0), section=t, sigma_inplane=fx(sip, 1), sigma_lat=fx(sl, 1), combo=name))
            out[f"{side}_{lev}"] = dict(sigma=fx(best[0], 1), util=fx(best[0] / L.FD, 3), **best[1])
    return out
COMB = combos()

# ================================================================== F. local: web ligament at the upper slot (pole push), shoulder on the lower web
def ligament():
    out = {}
    for side, kind in (("L", "A_up"), ("R", "B_up")):
        a = kind[0]; sy = L.SLOT_Y[a]; W = L.W_A_WEB_UP if a == "A" else L.W_B
        b = W - sy[1]                                             # ligament from slot edge to the free edge (outer)
        # outer chord = web ligament (t_web x b) + lip (t_web wide x LIP_H) at the edge; bending about n (in the web plane)
        rects = [(0, 0, b, L.T_WEB), (b - L.T_WEB, L.T_WEB, b, L.T_WEB + L.LIP_H)]
        A = sum((y1 - y0) * (z1 - z0) for y0, z0, y1, z1 in rects); yc = sum((y1 - y0) * (z1 - z0) * (y0 + y1) / 2 for y0, z0, y1, z1 in rects) / A
        I = sum((z1 - z0) * (y1 - y0) ** 3 / 12 + (y1 - y0) * (z1 - z0) * ((y0 + y1) / 2 - yc) ** 2 for y0, z0, y1, z1 in rects)
        Wm = I / max(yc, b - yc)
        Fu = max(p["F_up"] for k, c in BAR["cases"].items() if k.startswith(side) and "5.0" in k and "outward" in k for p in c["poles"]) * 1e3
        Ls = L.SLOT_UP[1]
        M = Fu * Ls / 12                                          # fixed-ended chord, load spread over the pole's bearing length (~ slot length)
        out[side] = dict(ligament_b=fx(b, 1), chord_W=fx(Wm, 0), F_up_kN=fx(Fu / 1e3, 2), M_kNmm=fx(M / 1e3, 1), sigma=fx(M / Wm, 1), util=fx(M / Wm / L.FD, 3),
                         bearing_on_slot_edge=fx(Fu / (L.T_WEB * 25.0) / (1.5 * L.F0 / L.GMP), 3), status="estimate (fixed-ended chord, no shell FE)")
    # shoulder on the lower web: fold-lock force + pole weight into two 10 mm ledges beside the 36 slot, web plate strip
    Fz = OUT["frame"]["fold_lock_max_by_level"]["lo"] * 1e3
    b_span = 18.0                                                # ledge centre to nearest leg/bulb face, cantilever-ish plate strip
    w_eff = 25.0 + 2 * b_span                                    # effective width along the rail
    M = Fz / 2 * b_span / 2
    out["lower web under shoulder"] = dict(Fz_kN=fx(Fz / 1e3, 2), util=fx(M / (w_eff * L.T_WEB ** 2 / 6) / L.FD, 3), status="estimate")
    return out
LIG = ligament()

# ================================================================== G. mass
def mass():
    Lr = {"lo": 1780.0, "up": 1850.0}
    m = {}
    for side in SIDES:
        for lev in ("lo", "up"):
            k = KIND[(side, lev)]; m[k] = fx(PROPS[k]["gross"]["A"] * Lr[lev] * 2.7e-6, 2)
    m["total_4_rails"] = fx(sum(v for kk, v in m.items()), 2)
    m["rev_c_after_changes_rails"] = 14.65
    return m
MASS = mass()

# ------------------------------------------------------------------ write
OUT["sections"] = {k: {n: {q: fx(v, 1) for q, v in p.items()} for n, p in v.items()} for k, v in PROPS.items()}
OUT["classes"] = {k: {e: dict(beta=fx(r["beta"], 2), cls=r["class"], rho=fx(r["rho"], 3)) for e, r in L.classify(k).items()} for k in PROPS}
OUT["barrier"] = {k: {kk: ({q: w for q, w in vv.items() if q != "M"} if isinstance(vv, dict) else vv) for kk, vv in v.items()} for k, v in BAR["cases"].items()}
OUT["pins"] = PIN; OUT["edges"] = EDGE; OUT["caps"] = CAP; OUT["combined"] = COMB; OUT["local"] = LIG; OUT["mass"] = MASS
OUT["params"] = {k: (fx(v, 3) if isinstance(v, float) else v) for k, v in vars(L).items() if k.isupper() and isinstance(v, (int, float, tuple))}
json.dump(OUT, open(os.path.join(HERE, "rail_design.json"), "w"), indent=1, default=float)
print(json.dumps({k: OUT[k] for k in ("geometry",)}, indent=1, default=float)[:6000])
print(json.dumps(OUT["frame"]["worst_inplane"], indent=1)); print(json.dumps(OUT["frame"]["sls"], indent=1))
print("pin max", OUT["frame"]["pin_force_max"], "lock", OUT["frame"]["fold_lock_max"], OUT["frame"]["fold_lock_max_by_level"], OUT["frame"]["fold_lock_x_by_level"])
print("mechanism", OUT["frame"]["lock_lower_only_mechanism"])
for k, v in OUT["barrier"].items():
    if "5.0" in k or "1.25" in k: print(k, {q: v[q] for q in ("up", "lo")})
print(json.dumps(PIN, indent=1)); print(EDGE); print(json.dumps(CAP, indent=1)); print(json.dumps(COMB, indent=1)); print(json.dumps(LIG, indent=1)); print(MASS)
