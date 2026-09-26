"""AS-IS datasheet ratings - the staircase exactly as modelled (IFC 22-09-2026 / RIGGED2.blend), in the
material now baked into the IFC: EN AW-6082-T6 throughout (f0 260 MPa t<=5 / 250 MPa t>5, gM1 1.1, E 70 GPa).
Loads = Aug-2026 EVENTS sheet (v2/spec/sheet_2026-09-23_events.txt), same FE + hand-calc functions as
v2/loadtest (loadtest_latest.py, lightweight_events_2026.py). Nothing in the model is changed.

Every rating is the largest characteristic load that keeps ALL of its checks <= 1.0:
  UDL   : side girder (locked Vierendeel FE, ULS 1.35G+1.5Q, load patterns all/low/high) + girder SLS L/250
          + tread bending / deflection
  point : tread bending under a 200x200 patch (ULS) + tread deflection L/100 & 25 mm
  line  : barrier grillage (posts fixed at the guide rail, rails continuous), ULS
Run: uvx --with numpy python v2/datasheet/asis_ratings.py   -> asis_ratings.json
"""
import math, json, os, sys, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "loadtest"))
import loadtest_latest as LT
import lightweight_events_2026 as LW

G, GG, GQ, GM1 = 9.81, LW.GG, LW.GQ, LW.GM1
SPAN, L_TREAD, P_FRAME = LT.SPAN, LT.L_TREAD, LT.P_FRAME
SEC = LT.SEC
Q_REQ, PT_REQ, LINE_REQ, POST_REQ = 7.5, 4.0, 3.0, 1.5          # Aug-2026 R113/R114/R142/R179

# ------------------------------------------------------------------ as-is sections (measured) + governing thickness
lo_R = dict(SEC["bar_R_lo"], t=20.0)      # solid guide bars (t > 5 -> f0 250)
up_R = dict(SEC["bar_R_up"], t=20.0)
lo_L = dict(SEC["bar_L_lo"], t=20.0)
up_L = dict(SEC["bar_L_up"], t=20.0)
post = dict(SEC["post"], t=10.0)          # 25 x 10 flat, weak axis resists the barrier load
guard = dict(SEC["guard"], t=3.8)         # 25 x 25 hollow (A 324.6 -> ~3.8 wall)
hand = dict(SEC["cyan"], t=25.0)          # 25 x 25 solid
TREAD = dict(LW.CURRENT_TREAD)            # 280 x 50 extrusion
sw = LT.self_weight("B")                  # density 2700 for everything = all-aluminium
MASS = sw["TOTAL"]
HR_SIDE_N = sw["_handrail_per_side"] * G
TREAD_A = SEC["tread"]["A"]


def fyd(sec):
    return LW.f0(sec["t"]) / GM1


def bisect(ok, hi=30.0, n=34):
    lo_q = 0.0
    if not ok(1e-6):
        return 0.0
    for _ in range(n):
        q = (lo_q + hi) / 2
        if ok(q):
            lo_q = q
        else:
            hi = q
    return lo_q


# ------------------------------------------------------------------ 1. side girder
def girder_uls(lock, q_kn, lo, up):
    q = q_kn * 1e-3
    worst = 0.0
    for pat in ("all", "low", "high"):
        r = LW.girder_fe(lock, lo, up, TREAD_A, HR_SIDE_N, q, pat, False, factor=(GG, GQ))
        worst = max(worst, r["lower"] / fyd(lo), r["upper"] / fyd(up))
    return worst


def girder_sls(lock, q_kn, lo, up):
    r = LW.girder_fe(lock, lo, up, TREAD_A, HR_SIDE_N, q_kn * 1e-3, "all", False)
    return r["defl"] / (SPAN / LW.L_OVER)


girder = {}
for lock in LT.LOCKS:
    g = {}
    for side, (lo, up) in (("R (25 wide, governs)", (lo_R, up_R)), ("L (35 wide)", (lo_L, up_L))):
        g[side] = dict(
            uls_rating_kN_m2=round(bisect(lambda q: girder_uls(lock, q, lo, up) <= 1.0), 2),
            sls_rating_kN_m2=round(bisect(lambda q: girder_sls(lock, q, lo, up) <= 1.0), 2),
            util_at_7_5_uls=round(girder_uls(lock, Q_REQ, lo, up), 2),
            util_at_7_5_sls=round(girder_sls(lock, Q_REQ, lo, up), 2),
            self_weight_only_uls=round(girder_uls(lock, 0.0, lo, up), 3),
        )
    person = max(LW.girder_fe(lock, lo_R, up_R, 0.0, 0.0, 0.0, "all", False, point=(i, LW.PERSON))["defl"] for i in range(6))
    g["person_1kN_defl_mm"] = round(person, 1)
    girder[lock] = g

# ------------------------------------------------------------------ 2. tread (280 x 50 extrusion, spans 1241 between rails)
tc = LW.check_tread(TREAD)
W_t = TREAD["I"] / TREAD["c"]
EI_t = LW.E * TREAD["I"]
w_self_t = TREAD["A"] * LW.RHO * G
L = L_TREAD
fy_t = LW.f0(TREAD["t"]) / GM1


def tread_udl_rating(gp):
    q_b = (W_t * fy_t * 8 / L ** 2 - GG * w_self_t) / (GQ * gp)
    q_d = (L / LW.L_OVER) * 384 * EI_t / (5 * gp * L ** 4)
    return min(q_b, q_d) * 1e3, q_b * 1e3, q_d * 1e3


p_b = (W_t * fy_t - GG * w_self_t * L * L / 8) * 4 / (GQ * L)
p_d = min(L / 100, 25.0) * 48 * EI_t / L ** 3
tread = dict(section="280 x 50 extruded plank (A 2125 mm2, I 0.567e6 mm4)", mass_each_kg=round(tc["mass_kg"], 2),
             util_aug2026={k: round(v, 3) for k, v in tc["util"].items()},
             point_rating_kN=round(min(p_b, p_d) / 1e3, 2), point_bending_kN=round(p_b / 1e3, 2),
             point_defl_kN=round(p_d / 1e3, 2), person_defl_mm=round(LW.PERSON * L ** 3 / (48 * EI_t), 1),
             open_riser_gap_mm=tc["open_riser_gap_mm"], deck_gap_mm=tc["deck_gap_mm"])
tread_udl = {}
for lock, Lk in LT.LOCKS.items():
    gp = P_FRAME * math.cos(math.radians(Lk["theta"]))
    r, rb, rd = tread_udl_rating(gp)
    tread_udl[lock] = dict(rating_kN_m2=round(r, 2), bending=round(rb, 2), defl_L250=round(rd, 2))
tread["udl_rating"] = tread_udl

# ------------------------------------------------------------------ 3. barrier (6 posts per side, 25x10 flats, guard + handrail)
barrier = {}
for lock, Lk in LT.LOCKS.items():
    rails = {"guard": (Lk["guard"], guard), "hand": (Lk["hand"], hand)}
    r_line = LW.barrier_fe(lock, [0, 1, 2, 3, 4, 5], post, rails, 0.0, "line", LW.H_LINE)
    r_post = LW.barrier_fe(lock, [0, 1, 2, 3, 4, 5], post, rails, 0.0, "post")
    u_line = max(r_line["M_post"] / (post["I"] / post["c"] * fyd(post)),
                 *(m / ({"guard": guard, "hand": hand}[t.split(":")[1]]["I"] / {"guard": guard, "hand": hand}[t.split(":")[1]]["c"]
                        * fyd({"guard": guard, "hand": hand}[t.split(":")[1]])) for t, m in r_line["M_rail"].items()))
    u_post = r_post["M_post"] / (post["I"] / post["c"] * fyd(post))
    barrier[lock] = dict(line_util_at_3kN_m=round(u_line, 2), line_rating_kN_m=round(LW.H_LINE / u_line, 2),
                         post_util_at_1_5kN=round(u_post, 2), post_point_rating_kN=round(1.5 / u_post, 2),
                         top_defl_mm_at_rating=round(r_line["w_top"] / u_line / GQ, 0),
                         guard_height_mm=Lk["guard"], hand_height_mm=Lk["hand"])

# ------------------------------------------------------------------ 4. connections
fy_hook = LW.f0(SEC["hook"]["t"]) / GM1
t_h, w_h = SEC["hook"]["t"], SEC["hook"]["w"]
e_h = SEC["axle"]["OD"] / 2 + w_h / 2
hook_cap = fy_hook / (1 / (t_h * w_h) + e_h / (t_h * w_h * w_h / 6))


def top_reaction(lock, q_kn, fac=(GG, GQ)):
    """per-side top support reaction of the side girder (simply supported, lumped tread loads)"""
    Lk = LT.LOCKS[lock]; c = math.cos(math.radians(Lk["theta"])); gp = P_FRAME * c
    pd = (fac[1] * q_kn * 1e-3 * gp + fac[0] * w_self_t) * L_TREAD / 2 + fac[0] * HR_SIDE_N / 6
    loads = [(s, pd * c) for s in Lk["st"]]
    for k in range(12):
        loads.append((SPAN * (k + 0.5) / 12, fac[0] * (lo_R["A"] + up_R["A"]) * LW.RHO * G * SPAN / 12 * c))
    _, _, RA, RB = LT.ss_point_loads(SPAN, loads, 1.0, n=200)
    return RB


hooks = {}
for lock in ("STANDARD", "STEEP"):
    R0, R1 = top_reaction(lock, 0.0), top_reaction(lock, 1.0)
    q_hook = max(0.0, (hook_cap - R0) / (R1 - R0))
    hooks[lock] = dict(capacity_kN=round(hook_cap / 1e3, 2), demand_at_7_5_kN=round(top_reaction(lock, Q_REQ) / 1e3, 2),
                       util=round(top_reaction(lock, Q_REQ) / hook_cap, 2), udl_rating_kN_m2=round(q_hook, 2))
fy_ax = LW.f0(2.74) / GM1
axle_shear_cap = SEC["axle"]["A"] * fy_ax / math.sqrt(3) / 2 / 1e3       # per side (two shear planes -> x2 over 2 sides)
mini_shear_cap = SEC["mini"]["A"] * fyd(post) / math.sqrt(3) / 1e3

# ------------------------------------------------------------------ 5. stability / dynamics (free-standing catwalk)
W_unit = MASS * G
M_ot = LW.H_LINE * LT.RAIL_LEN * (150 + LT.LOCKS["CATWALK"]["guard"])
FoS = W_unit * LT.W_PITCH / 2 / M_ot
ballast = max(0.0, (1.5 * M_ot - W_unit * LT.W_PITCH / 2) / (G * LT.W_PITCH / 2))
f1 = LW.girder_fe("STANDARD", lo_R, up_R, TREAD_A, HR_SIDE_N, 0.0, "all", False)
f1_std = 17.75 / math.sqrt(max(f1["defl"], 1e-6))
f1c = LW.girder_fe("CATWALK", lo_R, up_R, TREAD_A, HR_SIDE_N, 0.0, "all", False)
f1_cat = 17.75 / math.sqrt(max(f1c["defl"], 1e-6))

# ------------------------------------------------------------------ 6. state summary (governing UDL / persons)
DIMS = json.load(open(os.path.join(HERE, "state_dims.json")))
state_rows = []
for key, d in DIMS.items():
    lock = {0.0: "CATWALK", 35.0: "STANDARD", 49.4: "STEEP"}[d["deg"]]
    gR = girder[lock]["R (25 wide, governs)"]
    cands = {"side girder ULS": gR["uls_rating_kN_m2"], "side girder SLS L/250": gR["sls_rating_kN_m2"],
             "tread": tread_udl[lock]["rating_kN_m2"]}
    if lock != "CATWALK" or d["layout"] in ("BAR", "DOUBLE"):
        if lock in hooks and d["layout"] in ("BAR", "DOUBLE", "SINGLE", "WIDE"):
            cands["top hooks"] = hooks[lock]["udl_rating_kN_m2"]
    gov = min(cands, key=cands.get)
    q = cands[gov]
    units = 2 if d["layout"] in ("DOUBLE", "WIDE") else 1
    plan_area = units * (LT.L_TREAD / 1000) * (6 * P_FRAME / 1000) * math.cos(math.radians(d["deg"])) if d["deg"] else units * 1.241 * 1.831
    state_rows.append(dict(key=key, label=d["label"], group=d["group"], deg=d["deg"], layout=d["layout"], units=units,
                           L_mm=d["L"], W_mm=d["W"], H_mm=round((d["zmax"] - d["zmin"]) * 1000),
                           udl_rating_kN_m2=round(q, 2), governs=gov, candidates={k: round(v, 2) for k, v in cands.items()},
                           util_vs_7_5=round(Q_REQ / q, 1) if q > 0 else None,
                           persons_at_rating=int(q * plan_area / 0.8) if q > 0 else 0,
                           mass_kg=round(MASS * units - (sw["_handrail_per_side"] if d["layout"] == "WIDE" else 0.0), 1)))  # nested: one inner handrail set spare

out = dict(
    basis="as modelled (IFC 22-09-2026), EN AW-6082-T6 throughout, Aug-2026 events loads, EN 1990 1.35G + 1.5Q",
    mass_per_unit_kg=round(MASS, 1), mass_breakdown={k: round(v, 2) for k, v in sw.items() if not k.startswith("_")},
    girder=girder, tread=tread, barrier=barrier, hooks=hooks,
    axle_shear_capacity_per_side_kN=round(axle_shear_cap, 1), lock_pin_shear_capacity_kN=round(mini_shear_cap, 1),
    catwalk_overturning=dict(FoS=round(FoS, 2), required=1.5, ballast_or_anchor_kg=round(ballast)),
    frequency=dict(standard_Hz=round(f1_std, 1), catwalk_Hz=round(f1_cat, 1), required_Hz=6.0),
    states=state_rows,
)
json.dump(out, open(os.path.join(HERE, "asis_ratings.json"), "w"), indent=1)
print(json.dumps({k: out[k] for k in ("mass_per_unit_kg", "girder", "hooks", "barrier", "catwalk_overturning", "frequency")}, indent=1))
print(json.dumps({k: v for k, v in tread.items() if k != "util_aug2026"}, indent=1))
for r in state_rows:
    print(r["key"], r["udl_rating_kN_m2"], r["governs"], r["persons_at_rating"], r["candidates"])
