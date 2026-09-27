"""Rev C FINAL supports (27 Sep 2026): every support check, the dimension table and the part masses.
Inputs: frame_supports.json (in-plane reactions, this folder), hook_fe.json, ring_fe.json (local FE, this folder),
rail geometry (v2/revc/rails), sheet rows (v2/spec/sheet_2026-09-23_events.txt, R = line - 1).
Writes supports_checks_loads.json (hold-down / keeper design loads, read by hook_fe.py) and supports_final.json.
Run order: frame_supports.py -> supports_checks.py -> hook_fe.py -> ring_fe.py -> supports_checks.py
Tags in the output: [C] computed here or in the cited script, [E] estimate / assumption (stated)."""
import json, math, os, sys
sys.dont_write_bytecode = True           # do not leave __pycache__ in v2/revc/rails
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frame_supports as FS

J = lambda n: json.load(open(os.path.join(HERE, n))) if os.path.exists(os.path.join(HERE, n)) else None
FR = J("frame_supports.json"); R = FR["reactions"]
HOOK = J("hook_fe.json"); RING = J("ring_fe.json")
rows = []
def chk(item, check, Ed, Rd, unit, ref, tag, note="", status=None):
    u = Ed / Rd if Rd else float("inf")
    rows.append(dict(item=item, check=check, Ed=round(Ed, 2), Rd=round(Rd, 2), unit=unit, util=round(u, 2),
                     status=status or ("PASS" if u <= 1.0 else "FAIL"), ref=ref, tag=tag, note=note))
    return u

# ------------------------------------------------------------------ materials
S355 = dict(fy=355.0, fu=470.0, g0=1.0, g2=1.25)
AL = dict(fo=250.0, fu=290.0, g1=1.1, g2=1.25)
B88 = dict(fy=640.0, fu=800.0); A480 = dict(fy=600.0, fu=800.0)

# ------------------------------------------------------------------ geometry (global x along the flight, y across, z up)
XB, ZB = FS.AXLE_BASE; XT, ZT = FS.AXLE_TOP
Y_PINLEG = 605.5                     # pin-leg step-side face from the stair centre line (steps 1,209 over the end blocks + 1 mm pads)
FORK_OFF = 10.0                      # fork centre outboard of the pin-leg face (straddles pin leg 6 + bulb <= 14)
A_HALF = Y_PINLEG + FORK_OFF         # support half spacing: 615.5 -> jack / bracket centres 1,231 apart
Y_CL = -17712.0                      # stair centre line in the IFC (steps E840_D03 -18,330 .. -17,094)
JAW_T, JAW_GAP = 8.0, 24.0
COLLAR_W, COLLAR_GAP, AXLE_END = 25.0, 1.0, 10.0
half_len = A_HALF + JAW_GAP / 2 + JAW_T + COLLAR_GAP + COLLAR_W + AXLE_END
AXLE_L = 2 * half_len
PITCH_Z = lambda x: 50.0 + 175.0 / 250.0 * (9788.8 - x)      # nosing (pitch) line
X_POLES = [8396.8, 8646.8, 8896.8, 9146.8, 9396.8, 9646.8]
XM = sum(X_POLES) / 6
Z_TOPRAIL = PITCH_Z(XM) + 1100.0                             # R63 raise to 1,100 above the pitch line
Z_DECK = PITCH_Z(XM) - 25.0
LINE_Z = lambda x: ZB + (XB - x) * (ZT - ZB) / (XB - XT)     # support line (base axle -> top axle)

# ------------------------------------------------------------------ actions
Q_CROWD_K = 7.5 * 1.2 * 0.25 * 6 / 1.0                      # kN, 6 treads x 0.25 going x 1.2 m (R: 7.5 kN/m2)
L_BAR = 6 * 250.0 / math.cos(math.radians(35)) / 1000       # m of barrier per side (6 poles x 305.2)
BAR = {w: 1.5 * w * L_BAR for w in (3.0, 5.0)}               # ULS barrier resultant per unit, kN (R142)
SWAY_Y = 1.5 * 0.10 * Q_CROWD_K                              # R176 10 % of vertical imposed, ULS, kN
G_UNIT = FS.UNIT_KG * 9.81 / 1000
# wind (R150/R151/R181): peak velocity pressure ASSUMED (site value not in the repo)
QP_STORM, QP_OWS, CF, ETA_LEE = 0.85, 0.20, 2.0, 0.8
WIND_PARTS = [  # (name, projected area per side m2, height above the support line at mid-flight mm) [E] from the Rev C geometry
    ("lower rail (60-68 deep incl. lip)", 0.066 * (1728.5 + 30) / 1000, 37.0),
    ("upper rail (49-62 deep)", 0.056 * 1.85, 180.0),
    ("6 box poles 25 wide x 1,344", 6 * 0.025 * 1.344, 690.0),
    ("top rail D40 x 1,750", 0.040 * 1.75, Z_TOPRAIL - LINE_Z(XM)),
    ("handrail D40 x 1,750", 0.040 * 1.75, PITCH_Z(XM) + 903 - LINE_Z(XM)),
    ("6 step ends (L 280x25 + 50x50)", 6 * (0.28 * 0.025 + 0.05 * 0.05), 260.0),
]
A_SIDE = sum(p[1] for p in WIND_PARTS); ZW = sum(p[1] * p[2] for p in WIND_PARTS) / A_SIDE
FW_K = lambda qp: qp * CF * A_SIDE * (1 + ETA_LEE)                   # kN, both sides, lateral
FUP_K = lambda qp: qp * 0.5 * 6 * 0.28 * 1.2                         # kN, uplift on the treads, c 0.5 [E]


def lat_supports(P, xP, zP, cond, r):
    """support forces ON THE STAIR (kN) for a lateral force P (+y) at (xP, zP).
    cond 'ground': base z only (jacks), top x, y, z; 'scaffold': base and top x, y, z (couplers + bracket).
    r = share of the overturning couple taken by the base pair relative to the top pair (D_base = r D_top)."""
    pts = {"BL": (XB, -A_HALF, ZB), "BR": (XB, A_HALF, ZB), "TL": (XT, -A_HALF, ZT), "TR": (XT, A_HALF, ZT)}
    unk = [("BL", 2), ("BR", 2), ("TL", 0), ("TL", 1), ("TL", 2), ("TR", 0), ("TR", 1), ("TR", 2)]
    if cond == "scaffold": unk = [("BL", 0), ("BL", 1)] + unk[:1] + [("BR", 0), ("BR", 1)] + unk[1:]
    n = len(unk); A = []; b = []
    e = np.eye(3)
    for k in range(3):                                   # force equilibrium
        A.append([1.0 if d == k else 0.0 for (p, d) in unk]); b.append(-(P if k == 1 else 0.0))
    rP = np.array([xP, 0.0, zP]); FP = np.array([0.0, P, 0.0]); MP = np.cross(rP, FP)
    for k in range(3):                                   # moment equilibrium about the origin
        A.append([np.cross(np.array(pts[p]), e[d])[k] for (p, d) in unk]); b.append(-MP[k])
    idx = {u: i for i, u in enumerate(unk)}
    def row(coefs, rhs=0.0):
        rr = [0.0] * n
        for u, c in coefs.items(): rr[idx[u]] += c
        A.append(rr); b.append(rhs)
    row({("TL", 1): 1, ("TR", 1): -1})                   # equal lateral split between the two top brackets
    row({("BR", 2): 1, ("BL", 2): -1, ("TR", 2): -r, ("TL", 2): r})
    if cond == "scaffold":
        row({("BL", 1): 1, ("BR", 1): -1})
        row({("BL", 1): 1, ("BR", 1): 1}, -P * (xP - XT) / (XB - XT))     # lever rule along the flight
        row({("BL", 0): 1}); row({("BR", 0): 1}); row({("TL", 0): 1})      # lateral load: no x-forces (lever rule already balances Mz)
    sol, res, rank, sv = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)
    assert np.allclose(np.array(A) @ sol, np.array(b), atol=1e-6 * max(1.0, abs(P))), "lateral statics inconsistent"
    out = {p: [0.0, 0.0, 0.0] for p in pts}
    for (p, d), v in zip(unk, sol): out[p][d] = float(v)
    return out


def frame_supports_kN(key_L, key_R):
    """in-plane frame reactions (per side) -> support forces on the stair (kN)"""
    a, b = R[key_L], R[key_R]
    return {"BL": [a["base_H"] / 1e3, 0.0, a["base_V"] / 1e3], "TL": [a["top_H"] / 1e3, 0.0, a["top_V"] / 1e3],
            "BR": [b["base_H"] / 1e3, 0.0, b["base_V"] / 1e3], "TR": [b["top_H"] / 1e3, 0.0, b["top_V"] / 1e3]}


def addf(*ds):
    out = {}
    for d in ds:
        for k, v in d.items(): out[k] = [x + y for x, y in zip(out.get(k, [0, 0, 0]), v)]
    return out


def scale(d, f): return {k: [x * f for x in v] for k, v in d.items()}


COMBOS = {}
for cond, fr in (("ground", "slides"), ("ground (friction mu 0.5 = held)", "held"), ("scaffold", "held")):
    base = "ground" if cond.startswith("ground") else "scaffold"
    for r_lab, r in (("r1", 1.0), ("r0", 0.0)):
        if base == "scaffold" and r == 0.0: continue
        crowd = frame_supports_kN(f"L | ULS crowd all | base {fr}", f"R | ULS crowd all | base {fr}")
        g09 = scale(frame_supports_kN(f"L | G only | base {fr}", f"R | G only | base {fr}"), 0.9)
        for w in (5.0, 3.0):
            for sgn in (1, -1):
                lat = lat_supports(sgn * BAR[w], XM, Z_TOPRAIL, base, r)
                COMBOS[f"{cond} | {r_lab} | STR crowd + barrier {w} kN/m {'+y' if sgn > 0 else '-y'}"] = addf(crowd, lat)
                COMBOS[f"{cond} | {r_lab} | EQU 0.9G + barrier {w} kN/m {'+y' if sgn > 0 else '-y'}"] = addf(g09, lat)
        for sgn in (1, -1):
            COMBOS[f"{cond} | {r_lab} | STR crowd + sway R176 {'+y' if sgn > 0 else '-y'}"] = addf(crowd, lat_supports(sgn * SWAY_Y, XM, Z_DECK, base, r))
            wl = lat_supports(sgn * 1.5 * FW_K(QP_STORM), XM, LINE_Z(XM) + ZW, base, r)
            up = 1.5 * FUP_K(QP_STORM)
            upl = {"BL": [0, 0, -up / 4], "BR": [0, 0, -up / 4], "TL": [0, 0, -up / 4], "TR": [0, 0, -up / 4]}
            COMBOS[f"{cond} | {r_lab} | EQU 0.9G + wind storm {'+y' if sgn > 0 else '-y'}"] = addf(g09, wl, upl)
            COMBOS[f"{cond} | {r_lab} | STR crowd + wind OWS {'+y' if sgn > 0 else '-y'}"] = addf(crowd, lat_supports(sgn * 1.5 * 0.6 * FW_K(QP_OWS), XM, LINE_Z(XM) + ZW, base, r))


def env(filter_fn, sup, comp, fn=max):
    vals = [(v[sup][comp], k) for k, v in COMBOS.items() if filter_fn(k)]
    return fn(vals)


# ------------------------------------------------------------------ hold-down / keeper design loads (EQU, 5.0 kN/m barrier governs)
def worst_uplift(sups, filt):
    return max(((-v[s][2], k, s) for k, v in COMBOS.items() if filt(k) for s in sups), key=lambda t: t[0])

T_base = worst_uplift(("BL", "BR"), lambda k: "| r1 |" in k)
T_top_r1 = worst_uplift(("TL", "TR"), lambda k: "| r1 |" in k)
T_top_r0 = worst_uplift(("TL", "TR"), lambda k: "| r0 |" in k)
T_base_30 = worst_uplift(("BL", "BR"), lambda k: "| r1 |" in k and "barrier 5.0" not in k)
T_top_r0_30 = worst_uplift(("TL", "TR"), lambda k: "| r0 |" in k and "barrier 5.0" not in k)
pull_top = max(((-(v["top_H"]), k) for k, v in R.items() if "ULS" in k), key=lambda t: t[0])   # stair pulling away from the landing
PULL_CASE = R[pull_top[1]]
keeper_design = {"base": [0.0, -round(T_base[0] * 1e3, 0)], "top": [0.0, -round(max(T_top_r1[0], 0) * 1e3, 0)],
                 "top_pull": [PULL_CASE["top_H"], PULL_CASE["top_V"]]}
json.dump(dict(keeper_design=keeper_design, note="force ON THE RAIL from the keeper pin (global x, z), N; base/top = EQU uplift with r = 1 (base anchored)"),
          open(os.path.join(HERE, "supports_checks_loads.json"), "w"), indent=1)

# ------------------------------------------------------------------ 1. frame reactions, friction, hook angles
EU, EQ = FR["envelope_ULS"], FR["envelope_EQU"]
OUT = dict(geometry={}, loads={}, checks=None)
OUT["loads"] = dict(
    in_plane_envelope_ULS=EU, in_plane_envelope_EQU=EQ, friction=FR["friction"],
    barrier_ULS_kN=dict((f"{w} kN/m", round(v, 2)) for w, v in BAR.items()), barrier_length_m=round(L_BAR, 3),
    sway_R176_ULS_kN=round(SWAY_Y, 2), wind=dict(qp_storm_kPa=QP_STORM, qp_OWS_kPa=QP_OWS, cf=CF, eta_leeward=ETA_LEE,
    area_per_side_m2=round(A_SIDE, 3), centroid_above_support_line_mm=round(ZW), Fw_k_storm_kN=round(FW_K(QP_STORM), 2),
    uplift_treads_k_kN=round(FUP_K(QP_STORM), 2), parts=[(p[0], round(p[1], 3), round(p[2])) for p in WIND_PARTS]),
    lever_barrier_above_support_line_mm=round(Z_TOPRAIL - LINE_Z(XM)), hold_down=dict(
        base_per_jack_kN=[round(T_base[0], 2), T_base[1], T_base[2]], top_per_bracket_r1_kN=[round(T_top_r1[0], 2), T_top_r1[1], T_top_r1[2]],
        top_per_bracket_if_base_not_anchored_kN=[round(T_top_r0[0], 2), T_top_r0[1], T_top_r0[2]],
        base_per_jack_barrier3_or_wind_kN=[round(T_base_30[0], 2), T_base_30[1]], top_if_base_not_anchored_barrier3_or_wind_kN=[round(T_top_r0_30[0], 2), T_top_r0_30[1]]),
    keeper_design_N=keeper_design, pull_out_top_case=[pull_top[1], PULL_CASE["top_H"], PULL_CASE["top_V"]])
# support-force envelopes per support type (kN, on the stair)
def envsup(sups, filt):
    vals = [(v[s], k, s) for k, v in COMBOS.items() if filt(k) for s in sups]
    return dict(z_max=max(vals, key=lambda t: t[0][2]), z_min=min(vals, key=lambda t: t[0][2]),
                x_max=max(vals, key=lambda t: t[0][0]), x_min=min(vals, key=lambda t: t[0][0]),
                y_abs=max(vals, key=lambda t: abs(t[0][1])), h_res=max(vals, key=lambda t: math.hypot(t[0][0], t[0][1])))
OUT["loads"]["support_envelopes"] = {
    "base ground (r1)": envsup(("BL", "BR"), lambda k: k.startswith("ground") and "| r1 |" in k),
    "base scaffold": envsup(("BL", "BR"), lambda k: k.startswith("scaffold")),
    "top, base anchored/scaffold (r1)": envsup(("TL", "TR"), lambda k: "| r1 |" in k),
    "top, base NOT anchored (r0)": envsup(("TL", "TR"), lambda k: "| r0 |" in k)}

# hook coverage: base saddle covers 0..145 deg (downhill tab trimmed to vertical entry is NOT needed: the saddle is
# mid-rail, coverage -35..145), top saddle -35..145; reactions outside go to the keeper
chk("Base hook (saddle over the axle)", "Reaction angle inside the saddle (-35..145 deg, 5 deg margin)", max(EU["held"]["ang_base"][1], EQ["held"]["ang_base"][1]), 140.0, "deg", "R147/R170", "[C]",
    f"range {EU['held']['ang_base']} (held), 90 (slides); the keeper takes nothing in the crowd cases")
chk("Top hook (saddle over the axle)", "Crowd-case reaction angle inside the saddle (5 deg margin)", EU["slides"]["ang_top"][1], 140.0, "deg", "R147/R170", "[C]",
    "slides +sway 139 deg is 6 deg inside the 145 edge (friction covers it); the -90 (uplift, 0.7 kN, person on tread 0) and 157 deg (pull 2.9 kN, base held + person on tread 0) cases go to the keeper")

# ------------------------------------------------------------------ 2. hook FE (plane stress) and bearing
if HOOK:
    for side in ("L", "R"):
        for end in ("base", "top"):
            hs = [h for h in HOOK if h["side"] == side and h["end"] == end and h["contact"]]
            if hs:
                w = max(hs, key=lambda h: h["util_net"])
                chk(f"Hook {end} {side} ({'A_lo' if side == 'L' else 'B_lo'}) - rail end with saddle", "Plane-stress FE von Mises (>= 2 mm from contact)", w["vm_net"], 250 / 1.1, "MPa",
                    "R147/R170", "[C] hook_fe.py", f"peak at contact {w['vm_peak']} MPa (local bearing, see pin-bearing row); contact arc {w['contact_arc_deg']}")
            ks = [h for h in HOOK if h["side"] == side and h["end"] == end and h["keeper_load"] is not None]
            if ks:
                w = max(ks, key=lambda h: h["util_net"])
                chk(f"Hook {end} {side} - keeper hole region", "Plane-stress FE von Mises, keeper load", w["vm_net"], 250 / 1.1, "MPa", "R78/R150", "[C] hook_fe.py", f"keeper load {w['keeper_load']} N")
Rb = EU["held"]["R_base"]; Rt = EU["held"]["R_top"]
Fb_leg = 1.5 * 6 * 48.3 * AL["fo"] / AL["g2"]
chk("Hook saddle (6 mm pin leg) on the D48.3 tube", "Pin-type bearing 1.5 t d f_o / gamma_Mp (EN 1999-1-1 Tab 8.8)", Rb / 1e3, Fb_leg / 1e3, "kN", "R170", "[C]")

# ------------------------------------------------------------------ 3. axles
def tube(D, t):
    A = math.pi / 4 * (D ** 2 - (D - 2 * t) ** 2); I = math.pi / 64 * (D ** 4 - (D - 2 * t) ** 4)
    return A, I / (D / 2), (D ** 3 - (D - 2 * t) ** 3) / 6
A_ax, W_ax, Wpl_ax = tube(48.3, 4.0)
# in the fork: simply supported between the jaw centres (32 apart), hook (pin-leg centre) 7 mm off the fork centre
span = JAW_GAP + JAW_T; xa = span / 2 - (FORK_OFF - 3.0); M_fork = lambda Rr: Rr * xa * (span - xa) / span
chk("Base axle 48.3x4 S355J2H (EN 10219)", "Bending in the fork (jaws 32 c/c, hook 7 off centre)", M_fork(Rb) / 1e6, Wpl_ax * S355["fy"] / 1e6, "kNm", "R147", "[C]",
    f"R = {Rb / 1e3:.1f} kN; the Rev C 70 mm lever is gone (supports review M1)")
# scaffold case: coupler 60 mm inboard of the fork centre takes H (in plane) -> axle bending fork-to-coupler
H_sc = max(math.hypot(v[s][0], v[s][1]) for k, v in COMBOS.items() if k.startswith("scaffold") for s in ("BL", "BR"))
chk("Base axle 48.3x4 S355", "Scaffold case: bending fork -> coupler (60 mm), H resultant", H_sc * 0.060, Wpl_ax * S355["fy"] / 1e6, "kNm", "R147/R170", "[C]")
chk("Top axle 48.3x4 6082-T6", "Bending in the fork", M_fork(Rt) / 1e6, Wpl_ax * AL["fo"] / AL["g1"] / 1e6, "kNm", "R147", "[C]")
if RING:
    for end, mat in (("base", "steel"), ("top", "6082")):
        rs = [r for r in RING if r["end"] == end and r["material"].startswith(mat) and r["L_eff"] == 30.0]
        ri = [r for r in rs if r.get("insert")]; rn = [r for r in rs if not r.get("insert")]
        if rn:
            w = max(rn, key=lambda r: r["util_plastic"])
            chk(f"{end.capitalize()} axle tube, local crushing WITHOUT insert", "Ring bending (L_eff 30), N/N_pl + M/M_pl", w["util_plastic"], 1.0, "-", "R147/R170", "[C] ring_fe.py",
                "supports review M2 confirmed: plain tube fails -> insert required")
        if ri:
            w = max(ri, key=lambda r: r["util_plastic"])
            chk(f"{end.capitalize()} axle tube WITH solid insert D40 x 90", "Ring bending (L_eff 30), N/N_pl + M/M_pl", w["util_plastic"], 1.0, "-", "R147/R170", "[C] ring_fe.py")
chk("Insert D40x90 6082-T6 (in both axles)", "Bearing under hook + jaws (22 mm long x 20 mm chord)", Rb / (22 * 20), AL["fo"] / AL["g1"], "MPa", "R170", "[C]")
# insert: solid D40 bar in D40.3 bore, bearing only; roll pin D8 through tube + insert at the fork centre (M there ~0.1 kNm)
chk("Insert D40 x 90 + roll pin D8 (axle hole at the fork centre)", "Axle net section at the D8.5 hole, M in the fork", M_fork(Rb) / 1e6,
    (Wpl_ax - 2 * 4.0 * 8.5 * (48.3 - 4.0) / 2) * S355["fy"] / 1e6, "kNm", "R147", "[C]", "hole where the moment is ~0.08 kNm - allowed here, unlike Rev C (M1)")

# ------------------------------------------------------------------ 4. collars and lateral path
lat_base_sc = max(abs(v[s][1]) for k, v in COMBOS.items() if k.startswith("scaffold") for s in ("BL", "BR")) * 2   # one collar may carry both sides
Fp_M10 = 40e3 / (0.2 * 10.0)            # N, preload from 40 Nm, k = 0.2
slip_collar = 0.2 * 2 * 2 * Fp_M10 / 1.25
chk("Axle collar (split, 2 x M10 8.8 @ 40 Nm)", "Slip, scaffold case (whole base lateral through one collar)", lat_base_sc, slip_collar / 1e3, "kN", "R170/R78", "[E]",
    "mu 0.2, total normal = 2 x bolt force; confirm by a slip test (target >= 1.5 x demand)")
# ------------------------------------------------------------------ 5. keeper pins (D12 A4-80, double shear clevis, spacer bush)
Fk = max(T_base[0], T_top_r1[0], math.hypot(PULL_CASE["top_H"], PULL_CASE["top_V"]) / 1e3) * 1e3
b_, c_, a_ = 6.0, 1.0, JAW_T
M_k = Fk / 8 * (b_ + 4 * c_ + 2 * a_); W12 = math.pi * 12 ** 3 / 32
MRd = 1.5 * W12 * A480["fy"] / 1.0; FvRd = 0.6 * math.pi * 36 * A480["fu"] / 1.25
chk("Keeper pin D12 A4-80 (base and top)", "Bending EN 1993-1-8 Tab 3.10: M = F/8 (b + 4c + 2a)", M_k / 1e3, MRd / 1e3, "kNmm", "R78/R150/R170", "[C]",
    f"F = {Fk / 1e3:.1f} kN (governing hold-down); b 6 (pin leg), c 1 (spacer bush D16x2 on the outboard side), a 8 (jaws)")
chk("Keeper pin D12 A4-80", "Shear per plane", Fk / 2 / 1e3, FvRd / 1e3, "kN", "R170", "[C]")
chk("Keeper pin D12", "Combined (M/M_Rd)^2 + (V/V_Rd)^2", (M_k / MRd) ** 2 + (Fk / 2 / FvRd) ** 2, 1.0, "-", "R170", "[C]")
chk("Keeper hole D12.5 in the 6 mm pin leg", "Bearing 1.5 t d f_o / gamma_Mp", Fk / 1e3, 1.5 * 6 * 12 * AL["fo"] / AL["g2"] / 1e3, "kN", "R170", "[C]")
chk("Keeper hole in the 8 mm steel jaw", "Bearing 1.5 t d f_y / gamma_M0 (pin, EN 1993-1-8 Tab 3.10)", Fk / 2 / 1e3, 1.5 * 8 * 12 * S355["fy"] / 1e3, "kN", "R170", "[C]")
a_req = Fk * AL["g2"] / (2 * 6 * AL["fo"]) + 2 * 12.5 / 3
chk("Keeper hole D12.5, edge to the rail far face", "EN 1999-1-1 Tab 8.8 a >= F gamma / 2 t f_o + 2 d0/3", a_req, 60.0 - 36.0 - 6.25, "mm", "R170", "[C]")

# ------------------------------------------------------------------ 6. jacks (ground case), footplate, sole boards, ground
V_jack = max(v[s][2] for k, v in COMBOS.items() if k.startswith("ground") and "STR" in k and "| r1 |" in k for s in ("BL", "BR"))
V_jack_SLS = max(R[f"{sd} | SLS crowd | base {c}"]["base_V"] for sd in ("L", "R") for c in ("held", "slides")) / 1e3 + \
             max(v[s][2] for k, v in COMBOS.items() if k.startswith("ground | r1 | STR crowd + barrier 5.0") for s in ("BL", "BR")) / 1.5 * 0
lat_sls = lat_supports(BAR[5.0] / 1.5, XM, Z_TOPRAIL, "ground", 1.0)
V_jack_SLS = max(R[f"{sd} | SLS crowd | base {c}"]["base_V"] for sd in ("L", "R") for c in ("held", "slides")) / 1e3 + max(lat_sls["BL"][2], lat_sls["BR"][2])
MU = 0.5
H_jack = MU * V_jack
ROD = dict(d=36.0, As=817.0, d3=31.093)
E_MAX = 82.0                     # max exposed thread between the lock nut (on the plate) and the fork base; nut M36 welded UNDER the plate
FORK_BASE, SEAT = 12.0, 2.0
lever = E_MAX + FORK_BASE + SEAT + 24.15
W3 = math.pi * ROD["d3"] ** 3 / 32; Wpl3 = ROD["d3"] ** 3 / 6
sig = V_jack * 1e3 / ROD["As"] + H_jack * 1e3 * lever / Wpl3
chk("Jack spindle M36 8.8 (steel), max extension 82 (axle 150 above plate underside)", "N/A_s + M/W_pl(d3), H = 0.5 V at the head", sig, B88["fy"], "MPa", "R147/R74/R174", "[C]",
    f"V {V_jack:.1f} kN (crowd + 5.0 kN/m barrier, compression side), H {H_jack:.1f} kN, lever {lever:.0f} mm")
Lcr = 2 * (lever + 15 + 24)        # cantilever from the boss (K = 2)
lam = Lcr / (ROD["d3"] / 4) / (93.9 * math.sqrt(235 / B88["fy"])); phi = 0.5 * (1 + 0.49 * (lam - 0.2) + lam ** 2); chi = min(1.0, 1 / (phi + math.sqrt(phi ** 2 - lam ** 2)))
chk("Jack spindle M36", "Buckling K = 2 (curve c) + bending", V_jack * 1e3 / (chi * ROD["As"] * B88["fy"]) + H_jack * 1e3 * lever / (Wpl3 * B88["fy"]), 1.0, "-", "R74", "[C]", f"lambda {lam:.2f}, chi {chi:.2f}")
# fork base weld: rod screwed into the M36 tapped fork base and fillet a6 all round on top (weld group = ring r 18)
aw = 6.0; r_w = 18.0 + aw / 2
Aw = 2 * math.pi * r_w * aw; Ww = math.pi * r_w ** 2 * aw
M_w = H_jack * 1e3 * (SEAT + 24.15 + FORK_BASE / 2)
sw = math.sqrt((V_jack * 1e3 / Aw + M_w / Ww) ** 2 + 3 * (H_jack * 1e3 / Aw) ** 2 * 0 + 2 * (H_jack * 1e3 / Aw) ** 2)
chk("Fork base to spindle weld a6 all round (S355)", "Simplified resultant <= f_u / (sqrt3 beta gamma_M2)", sw, S355["fu"] / (math.sqrt(3) * 0.9 * 1.25), "MPa", "EN 1993-1-8 4.5.3.3", "[C]",
    "the thread engagement (36 mm) carries the axial load; the weld carries H and M")
# fork jaws: two 8 mm S355 plates, each takes R/2 in bearing + bending from the notch to the base
jaw_M = Rb / 2 * 30.0; jaw_W = 8 * 60 ** 2 / 6
chk("Fork jaw 8 mm S355 (60 deep below the notch)", "Bending R/2 x 30 mm", jaw_M / jaw_W, S355["fy"], "MPa", "R147", "[C]")
# base plate 250 x 250 x 12 S355 (R73 >= 150 x 150) on the sole boards; cantilever from the welded M36 nut (60 a/f)
B = 250.0; tp = 12.0; c = (B - 60.0) / 2
h_tot = 150.0          # plate underside to axle centre at max extension
e = H_jack * h_tot / V_jack
pmax = V_jack * 1e3 / B ** 2 * (1 + 6 * e / B) if e <= B / 6 else 2 * V_jack * 1e3 / (3 * (B / 2 - e) * B)
chk("Jack base plate 250x250x12 S355 (R73)", "Plate bending from the nut, peak pressure over the whole cantilever", 6 * (pmax * c ** 2 / 2) / tp ** 2, S355["fy"], "MPa", "R73/R174", "[C]",
    f"e = {e:.0f} mm (H x h / V, H = 0.5 V, h 150), p_max {pmax:.2f} MPa on the board")
chk("Jack tipping on its own plate", "e <= (B/2)/1.5", e, B / 2 / 1.5, "mm", "R149", "[C]")
chk("Base plate on timber sole boards (C24)", "Bearing perpendicular to grain (k_c90 1.5, k_mod 0.9, gamma_M 1.3)", pmax, 2.5 * 1.5 * 0.9 / 1.3, "MPa", "R76", "[C]")
# sole boards: 2 scaffold boards 225 x 38 x 600 side by side (450 x 600), jack plate screwed to them
Bb, Lb = 450.0, 600.0; h_g = h_tot + 38.0
e_g = MU * h_g
p_g = V_jack_SLS * 1e3 / (Bb * Lb) * (1 + 6 * e_g / Bb) if e_g <= Bb / 6 else 2 * V_jack_SLS * 1e3 / (3 * (Bb / 2 - e_g) * Lb)
OUT["loads"]["ground_bearing"] = dict(V_SLS_kN=round(V_jack_SLS, 2), board_mm=[Bb, Lb], ecc_mm=round(e_g), p_max_kPa=round(p_g * 1e3), p_mean_kPa=round(V_jack_SLS * 1e3 / (Bb * Lb) * 1e3))
chk("Ground under 2 sole boards 450x600 (R174)", "Peak SLS pressure vs required allowable 150 kPa (site to confirm)", p_g * 1e3, 150.0, "kPa", "R174/R76", "[C]/[E]",
    "150 kPa = firm ground; on turf/soft ground use a bigger spreader or site-tested bearing")
chk("Sole boards (resultant inside the boards)", "e = mu h <= (B/2)/1.5", e_g, Bb / 2 / 1.5, "mm", "R149/R76", "[C]")
# hold-down at the base (ground case): stakes through the plate
chk("Base hold-down per jack (ground, 5.0 kN/m barrier EQU)", "REQUIRED anchor capacity (stakes / anchors through the base plate)", T_base[0], T_base[0], "kN", "R150/R181", "[C]",
    "site-tested stakes on soil (4 x D20 x 750 typical) or 2 x M12 anchors on hard standing; if no anchors: the top brackets take all (r0) - see landing rows", status="REQ")
# ------------------------------------------------------------------ 7. scaffold clamped case: EN 74-1 couplers
F_cpl = 15.0 / 1.5
H_sc_jack = max(math.hypot(v[s][0], v[s][1]) for k, v in COMBOS.items() if k.startswith("scaffold") for s in ("BL", "BR"))
chk("Scaffold case: 2 x EN 74-1 class B right-angle couplers per jack on the steel axle", "Slip (F_s,k 15 kN / gamma_M 1.5 each)", H_sc_jack, 2 * F_cpl, "kN", "R78/R170", "[C]",
    "one coupler each side of the fork within 100 mm; to a scaffold standard or ledger at axle level")
T_sc = max(-v[s][2] for k, v in COMBOS.items() if k.startswith("scaffold") for s in ("BL", "BR"))
chk("Scaffold case couplers", "Uplift (pull-apart) per jack vs 2 x 10 kN (supplier value to confirm)", max(T_sc, 0.0), 20.0, "kN", "R150/R170", "[E]")
# ------------------------------------------------------------------ 8. landing bracket (steel S355, 4 x M12 8.8 through-bolts)
def bracket_forces(filt):
    out = []
    for k, v in COMBOS.items():
        if not filt(k): continue
        for s in ("TL", "TR"):
            fx, fy, fz = v[s]           # on the stair; on the bracket = minus
            out.append((k, s, -fx, -fy, -fz))
    return out
BF = bracket_forces(lambda k: True)
ecc_x = 38.0 + 12.0                        # axle centre to the landing face (plate front 38 + plate 12)
bolt_y, bolt_z = 110.0, 150.0
Ft = []; Fv = []
for (k, s, bx, by, bz) in BF:
    # bx > 0: bracket pushed away from the landing (x+ is away from the face? the landing face is at x 8,100, stair at larger x)
    pull = max(bx, 0.0)                    # force pulling the plate off the face
    My = bz * ecc_x                        # vertical load x offset -> top/bottom bolt rows
    Mz = by * ecc_x                        # lateral load x offset -> left/right bolt columns
    t_row = pull / 4 + abs(My) / bolt_z / 2 + abs(Mz) / bolt_y / 2
    Ft.append((t_row, k, s)); Fv.append((math.hypot(by, bz) / 4, k, s))
ft = max(Ft); fv = max(Fv)
FtRd = 0.9 * 800 * 84.3 / 1.25; FvRd12 = 0.6 * 800 * 84.3 / 1.25
chk("Landing bracket bolts 4 x M12 8.8 (through-bolts, washers)", "Tension per bolt", ft[0], FtRd / 1e3, "kN", "R170/R150", "[C]", ft[1] + " " + ft[2])
chk("Landing bracket bolts", "Shear per bolt", fv[0], FvRd12 / 1e3, "kN", "R170", "[C]")
chk("Landing bracket bolts", "Combined F_v/F_v,Rd + F_t/(1.4 F_t,Rd)", fv[0] / (FvRd12 / 1e3) + ft[0] / (1.4 * FtRd / 1e3), 1.0, "-", "EN 1993-1-8 Tab 3.4", "[C]")
Rmax_br = max(math.sqrt(bx * bx + by * by + bz * bz) for (k, s, bx, by, bz) in BF)
chk("Landing bracket jaw 8 mm S355", "Bending, R/2 at 40 mm from the back plate weld (jaw 110 deep)", Rmax_br * 1e3 / 2 * 40.0 / (8 * 110 ** 2 / 6), S355["fy"], "MPa", "R170", "[C]")
chk("Landing bracket jaw-to-plate fillet welds a5 both sides", "Resultant stress (weld length 2 x 110 per jaw)", Rmax_br * 1e3 / 2 / (2 * 110 * 5) * math.sqrt(3) + Rmax_br * 1e3 / 2 * 40 / (2 * 5 * 110 ** 2 / 6), S355["fu"] / (0.9 * 1.25), "MPa", "EN 1993-1-8", "[C]")
chk("Back plate 12 mm S355", "Bending between bolt rows (prying, bolt tension x 20 mm)", ft[0] * 1e3 * 20.0 / (80 * 12 ** 2 / 6), S355["fy"], "MPa", "R170", "[C]")
chk("Old wing clamps (IFC)", "Not rated - not accepted for any anchor force", 1.0, 1.0, "-", "R78", "[C]", "replace with bolts or EN 74 couplers", status="REPLACED")

# ------------------------------------------------------------------ 9. overturning / sliding of the unit (free-standing = no ties)
Mres = G_UNIT * A_HALF / 1e3
for lab, H, z in (("barrier 5.0 kN/m (char)", BAR[5.0] / 1.5, Z_TOPRAIL - LINE_Z(XM)), ("barrier 3.0 kN/m (char)", BAR[3.0] / 1.5, Z_TOPRAIL - LINE_Z(XM)),
                  ("storm wind (char)", FW_K(QP_STORM), ZW)):
    Mov = H * z / 1e3 + (FUP_K(QP_STORM) * A_HALF / 1e3 if "wind" in lab else 0.0)
    chk(f"Free-standing unit, no ties: {lab}", "Overturning FoS = M_res / M_ov >= 1.5 (R149)", 1.5, Mres / Mov, "-", "R149/R181", "[C]",
        f"M_ov {Mov:.2f} kNm vs M_res {Mres:.2f} kNm (G at the centre line, 1.231 track) -> ties REQUIRED")
Fslide = FW_K(QP_STORM); Rslide = 0.3 * (G_UNIT - FUP_K(QP_STORM))
chk("Free-standing unit, storm wind", "Sliding FoS mu 0.3 (R149)", 1.5, max(Rslide, 1e-6) / Fslide, "-", "R149/R181", "[C]", "-> top brackets bolted, base anchored or scaffold-clamped")
# EQU with the ties
chk("Tied unit, EQU 0.9G + 1.5W storm", "Top bracket hold-down, base anchored (r1)", max(-v[s][2] for k, v in COMBOS.items() if "wind storm" in k and "| r1 |" in k for s in ("TL", "TR")), FtRd * 4 / 1e3, "kN", "R181", "[C]")

# ------------------------------------------------------------------ 10. rails with the moved supports
chk("Rails in-plane (new support positions), conservative weakest-section envelope", "max |N|/A + |M|/W", FR["rail_inplane_max"]["new"], FR["rail_inplane_max"]["fd"], "MPa", "R147", "[C] frame_supports.py",
    f"same formula on the rail agent's supports: {FR['rail_inplane_max']['rev_c']} MPa (shorter span helps)")

OUT["checks"] = rows
# ------------------------------------------------------------------ dimension table and masses
kg_m = lambda A, rho: A * rho * 1e-9
OUT["geometry"] = dict(
    base_axle_centre=dict(x=round(XB, 1), z=round(ZB, 1), above_ground=125.0, lower_rail_s=FS.S_BASE, n=FS.N_SADDLE,
                          moved_from=[9636.1, -89.4], note="188 mm up the rail from Rev C; 125 above the ground (z -125)"),
    top_axle_centre=dict(x=round(XT, 1), z=round(ZT, 1), lower_rail_s=FS.S_TOP, n=FS.N_SADDLE, moved_from=[8135.8, 960.6]),
    support_centres_y=dict(left=round(Y_CL - A_HALF, 1), right=round(Y_CL + A_HALF, 1), spacing=round(2 * A_HALF, 1),
                           rev_c=[-18404, -17031], note="1,373 no longer possible: the old jack centres fall inside the new 108/115 rail channels"),
    axle_length=round(AXLE_L), axle_half=round(half_len, 1),
    collar_positions_from_CL=[round(A_HALF + JAW_GAP / 2 + JAW_T + COLLAR_GAP, 1), round(A_HALF + JAW_GAP / 2 + JAW_T + COLLAR_GAP + COLLAR_W, 1)],
    fork=dict(jaw_t=JAW_T, gap=JAW_GAP, inner_faces_from_pin_leg=[-2.0, 22.0], seat_radius=24.5),
    lower_rail_cuts=dict(base_end_s=-30.0, top_end="vertical cut at x = top axle - 22 (s 1,724.6 at n 0, 1,682.9 at n 60)",
                         saddle="R 24.5 (D49.0 +0.3/0), centre n 60, s 46 (base) / 1,656 (top), through pin leg + bulb",
                         keeper_hole="D12.5 at n 36, s 82 (base, uphill) / s 1,620 (top, downhill)",
                         web_window="web y 6..70 over s_c +-45; y 6..32 over s_c+45..s_c+58 (base) / s_c-58..s_c-45 (top)",
                         A_only="pin leg trimmed to n 60 over the window (A pin leg runs to 61)"),
    lever_barrier_mm=round(Z_TOPRAIL - LINE_Z(XM)))
m_st = kg_m(A_ax, 7850) * AXLE_L; m_al = kg_m(A_ax, 2700) * AXLE_L
m_ins_al = math.pi / 4 * 40 ** 2 * 90 * 2.7e-6
m_col_al = math.pi / 4 * (70 ** 2 - 48.3 ** 2) * 25 * 2.7e-6
m_keep = 4 * (math.pi / 4 * 12 ** 2 * 60 * 7.9e-6 + 0.015)
d_rail = (0.027 * 4.38 + 0.053 * 3.81) - 4 * (64 * 90 + 26 * 13) * 7 * 2.7e-6
m_jack = 0.250 * 0.250 * 0.012 * 7850 + 1018 * 150 * 7.85e-6 + 2 * 0.28 + 80 * 60 * 12 * 7.85e-6 + 2 * (8 * 110 * 120 - math.pi * 24.5 ** 2 / 2 * 8) * 7.85e-6
m_br = 0.012 * 0.160 * 0.200 * 7850 + 2 * 8 * 110 * 110 * 7.85e-6
OUT["masses_kg"] = {
    "base axle 48.3x4 S355 x %d [C]" % round(AXLE_L): round(m_st, 2), "top axle 48.3x4 6082-T6 x %d [C]" % round(AXLE_L): round(m_al, 2),
    "inserts 4 x 6082-T6 D40x90 [C]": round(4 * m_ins_al, 2), "collars 4 x 6082-T6 split OD70x25 [C]": round(4 * m_col_al, 2),
    "keeper pins 4 x D12x60 A4 + R-clips + bushes [E]": round(m_keep, 2), "rail hooks (net change in the lower rails) [C]": round(d_rail, 2),
    "unit subtotal (carried) [C/E]": round(m_st + m_al + 4 * m_ins_al + 4 * m_col_al + m_keep + d_rail, 2),
    "vs mass budget OPT: axles 4.4 + hooks 2.0 + collars ~1.0 + keeper pins 0.3 [mass_budget.md]": 7.7,
    "jack each (site kit, steel) [C]": round(m_jack, 2), "landing bracket each (steel) [C]": round(m_br, 2)}
json.dump(OUT, open(os.path.join(HERE, "supports_final.json"), "w"), indent=1)
w = max(len(r["item"] + r["check"]) for r in rows) + 3
for r in rows:
    print(f"{r['status']:<5} {r['util']:6.2f}  {(r['item'] + ' - ' + r['check']):<{w}} {r['Ed']:>9} / {r['Rd']:<9} {r['unit']:<5} {r['tag']}")
print(json.dumps(dict(geometry=OUT["geometry"], hold=OUT["loads"]["hold_down"], ground=OUT["loads"]["ground_bearing"], masses=OUT["masses_kg"]), indent=1))
