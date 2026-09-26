"""ALL-ALUMINIUM actionable upgrade spec (material decision 2026-09-23: everything aluminium).
Structure EN AW-6061-T6 (f0 240 MPa, gM1 1.1, E 69 GPa), treads EN AW-6082-T6 (unchanged).
Sizes every failing member, re-runs the FULL 11-state check suite with the changes, and extracts the
connection demands (post base, lock pin, hooks, anchors, joint trestle) for the change list.
Run: uvx --with numpy python v2/loadtest/upgrade_spec_alu.py   -> upgrade_spec_alu.json
"""
import copy, json, math, os
import loadtest_latest as L

HERE = os.path.dirname(os.path.abspath(__file__))
b = "B"
S = L.BASIS[b]["s"]
fy = S["fy"] / S["gM"]                       # 218.2 MPa design
KEEP = copy.deepcopy(L.SEC)
W_R, W_L = 25.0, 35.0                        # existing bar widths (R female 25, L male 35) - kept


def shs(bo, t):
    I = (bo ** 4 - (bo - 2 * t) ** 4) / 12
    return dict(A=bo * bo - (bo - 2 * t) ** 2, I=I, c=bo / 2, J=4 * ((bo - t) ** 2) ** 2 * t / (4 * (bo - t)), W=I / (bo / 2))


H_UP = 35.0     # upper bars: solid, grow UP 15 mm (4.5 mm left under the tread ends at catwalk)


def apply(h_lo, post, hook, axle=None):
    L.SEC.clear(); L.SEC.update(copy.deepcopy(KEEP))
    for k, w in (("bar_R_lo", W_R), ("bar_L_lo", W_L)):
        L.SEC[k].update(A=w * h_lo, I=w * h_lo ** 3 / 12, c=h_lo / 2)
    for k, w in (("bar_R_up", W_R), ("bar_L_up", W_L)):
        L.SEC[k].update(A=w * H_UP, I=w * H_UP ** 3 / 12, c=H_UP / 2)
    p = shs(*post); L.SEC["post"].update(A=p["A"], I=p["I"], c=p["c"], J=p["J"])
    L.SEC["hook"].update(t=hook[0], w=hook[1])
    if axle:
        od, idd = axle
        L.SEC["axle"].update(OD=od, ID=idd, A=math.pi / 4 * (od ** 2 - idd ** 2), I=math.pi / 64 * (od ** 4 - idd ** 4))


def girder_ok(h):
    sec = dict(A=W_R * h, I=W_R * h ** 3 / 12, c=h / 2, L=KEEP["bar_R_lo"]["L"])  # (search helper, unused)
    wst = L.SEC["tread"]["A"] * L.BASIS[b]["t"]["rho"] * L.G
    hr = L.self_weight(b)["_handrail_per_side"] * L.G
    worst = dict(u=0.0, d=0.0)
    for lock in L.LOCKS:
        u = L.girder_utils(lock, b, L.Q_UDL, lo=sec)["locked_fe"]
        r, _ = L.side_frame_fe(lock, b, L.Q_UDL, wst, hr, L.SEC["bar_R_up"], sec, "locked")
        d = max(abs(r["u"][1::3]))
        worst = dict(u=max(worst["u"], u), d=max(worst["d"], d / L.defl_lim(L.SPAN)))
    return worst


def hook_width(V, t):
    w = 5.0
    while w < 120:
        e = L.SEC["axle"]["OD"] / 2 + w / 2
        if V / (t * w) + V * e / (t * w * w / 6) <= fy:
            return w
        w += 0.5
    return None


# ------------------------------------------------ 1. post: lightest aluminium SHS for 1.25 kN point at tallest guardrail
h_guard = max(Lk["guard"] for Lk in L.LOCKS.values())
M_post = L.GAMMA_Q * L.H_PT * h_guard
post = None
for bo, t in ((40, 3), (40, 4), (50, 3), (50, 4), (50, 5), (60, 4), (60, 5)):
    if shs(bo, t)["W"] * fy >= M_post:
        post = (float(bo), float(t)); break
# ------------------------------------------------ 2. lower guide bar depth (stress ULS + deflection SLS, all locks)
apply(20.0, post, (10.0, 20.0))
h_lo = 50.0     # lower bars: solid, grow DOWN 29.5 mm (5.2 mm ground clearance at catwalk; fit_search_alu.py)
# ------------------------------------------------ 3. hooks + axle: run once to get the governing reactions
apply(h_lo, post, (10.0, 20.0))
L.UPGRADED = True
rows0, sw0 = L.run(b)
L.UPGRADED = False
V_hook = max(float(r["note"].split("hook load ")[1].split(" kN")[0]) * 1e3 for r in rows0 if r["check"].startswith("Top hook"))
hook_opts = {f"{t:.0f} mm plate": hook_width(V_hook, t) for t in (8.0, 10.0, 12.0)}
twin_w = hook_width(V_hook / 2, 5.0)          # twin 5 mm hooks, one on each skin of the plate sandwich
hook = (10.0, math.ceil(hook_opts["10 mm plate"]))
axle_u = max(r["util"] for r in rows0 if r["check"].startswith("Axle"))
axle = None
if axle_u > 1.0:
    for od, t in ((25.4, 3.0), (25.4, 4.0), (25.4, 6.35)):
        axle = (od, od - 2 * t)
        apply(h_lo, post, hook, axle)
        L.UPGRADED = True
        rr, _ = L.run(b); L.UPGRADED = False
        if max(r["util"] for r in rr if r["check"].startswith("Axle")) <= 1.0:
            break
# ------------------------------------------------ 4. FULL re-run with the final aluminium spec
apply(h_lo, post, hook, axle)
L.UPGRADED = True
rows, sw = L.run(b)
L.UPGRADED = False
code = [r for r in rows if r["result"] in ("PASS", "FAIL")]
fails = [r for r in code if r["result"] == "FAIL"]


def worst(prefix, rr):
    m = [r for r in rr if r["check"].startswith(prefix) and r["result"] in ("PASS", "FAIL")]
    return round(max(r["util"] for r in m), 3) if m else None


asis = [r for r in L.run(b)[0]] if False else None
# as-modelled aluminium rows (sections restored)
L.SEC.clear(); L.SEC.update(copy.deepcopy(KEEP))
rows_asis, sw_asis = L.run(b)
apply(h_lo, post, hook, axle)

# ------------------------------------------------ 5. connection demands with the final spec
wst = L.SEC["tread"]["A"] * L.BASIS[b]["t"]["rho"] * L.G
hr = sw["_handrail_per_side"] * L.G
lock_pin = {}
for lock, Lk in L.LOCKS.items():
    r, _ = L.side_frame_fe(lock, b, L.Q_UDL * L.GAMMA_Q, wst * L.GAMMA_G, hr * L.GAMMA_G,
                           L.SEC["bar_R_up"], L.SEC["bar_R_lo"], "locked")
    Mj = max(abs(f["M1"]) for f in r["forces"] if f["tag"] == "tread")
    lever = L.LINK[0] / 2 / math.cos(math.radians(Lk["theta"]))       # rear pin -> mini along the bar
    Fp = Mj / lever
    lock_pin[lock] = dict(M_joint_kNm=round(Mj / 1e6, 3), lever_mm=round(lever, 1), pin_force_kN=round(Fp / 1e3, 2))
Fp_max = max(v["pin_force_kN"] for v in lock_pin.values()) * 1e3
mini_shear_u = Fp_max / (L.SEC["mini"]["A"] * fy / math.sqrt(3))
mini_bearing_u = Fp_max / (2 * 5.0 * 10.0 * 1.5 * fy)          # 10 mm pin on 2 x 5 mm aluminium skins
gg = {lock: L.barrier_grillage(lock, b, "line_guard")["M_post"] for lock in L.LOCKS}
M_base = max(M_post, max(gg.values()))
# example base detail: 2 bolts through both guide bars at 100 mm lever -> bolt shear force
F_bolt = M_base / 100.0
bolt_M12 = 0.6 * 800 * 84.3 / 1.25                              # A4-80 M12 single shear (EN 1993-1-8)
t_bear = F_bolt / (2.5 * 0.7 * 260.0 * 12.0 / 1.25)             # EN 1999-1-1 8.5.5 bearing, alu fu 260
anchor = [r["note"] for r in rows if r["check"].startswith("Overturning: 4") and r["state"] == "SINGLE_CATWALK"][0]
anchor_wide = [r["note"] for r in rows if r["check"].startswith("Overturning: 4") and r["state"] == "WIDE_CATWALK_FULL"][0]
trestle = [r["note"] for r in rows if r["check"].startswith("Joint WITH") and r["state"] == "DOUBLE_CATWALK"]
freq = [r for r in rows if r["check"].startswith("Vertical natural") and r["state"] == "SINGLE_CATWALK"][0]

out = dict(
    basis=L.BASIS[b]["name"], fy_design_MPa=round(fy, 1),
    checks=dict(total=len(code), fail=len(fails), fails=[(r["state"], r["check"], r["util"]) for r in fails],
                as_modelled_fail=sum(1 for r in rows_asis if r["result"] == "FAIL"),
                as_modelled_total=sum(1 for r in rows_asis if r["result"] in ("PASS", "FAIL"))),
    upper_bar=dict(depth_mm=H_UP, widths_mm=[W_R, W_L]),
    fit=dict(ground_clearance_catwalk_mm=round(34.7 - (h_lo - 20.45), 1), tread_clearance_catwalk_mm=round(19.5 - (H_UP - 20.0), 1)),
    lower_bar=dict(depth_mm=h_lo, widths_mm=[W_R, W_L], util_before=worst("FE: girder stress", rows_asis),
                   util_after=worst("FE: girder stress", rows), defl_before=worst("FE: girder deflection", rows_asis),
                   defl_after=worst("FE: girder deflection", rows)),
    post=dict(section=f"SHS {post[0]:.0f}x{post[0]:.0f}x{post[1]:.0f}", W_mm3=round(shs(*post)["W"]),
              util_before=worst("Post bending, 1.25", rows_asis), util_after=worst("Post bending, 1.25", rows),
              line_before=worst("FE grillage: post moment, 3.0", rows_asis), line_after=worst("FE grillage: post moment, 3.0", rows)),
    post_base=dict(M_Ed_kNm=round(M_base / 1e6, 2), mini_as_base_MRd_kNm=round(L.SEC["mini"]["I"] / L.SEC["mini"]["c"] * fy / 1e6, 3),
                   bolt_force_kN_at_100mm=round(F_bolt / 1e3, 1), M12_A4_80_shear_kN=round(bolt_M12 / 1e3, 1),
                   min_alu_plate_for_bearing_mm=round(t_bear, 1)),
    lock_pin=dict(per_lock=lock_pin, shear_util=round(mini_shear_u, 3), bearing_util=round(mini_bearing_u, 3)),
    hooks=dict(V_ULS_kN=round(V_hook / 1e3, 2), throat_for_plate=hook_opts, twin_5mm_throat=twin_w,
               chosen=f"{hook[0]:.0f} mm plate, {hook[1]:.0f} mm throat",
               util_before=worst("Top hook", rows_asis), util_after=worst("Top hook", rows)),
    axle=dict(util_before=worst("Axle", rows_asis), util_after=worst("Axle", rows),
              change=None if axle is None else f"tube {axle[0]} OD x {(axle[0]-axle[1])/2:.2f} wall"),
    upper_bar_util_after=round(max(L.girder_utils(k, b, L.Q_UDL)["locked_fe"] for k in L.LOCKS), 3),
    treads=dict(util=worst("Tread bending", rows), defl=worst("Tread deflection", rows)),
    guardrail=dict(util_before=worst("Guardrail bending", rows_asis), util_after=worst("Guardrail bending", rows)),
    anchors=dict(single=anchor, wide=anchor_wide),
    trestle=trestle, frequency_Hz=round(freq["capacity"], 2),
    weight_kg=dict(before=round(sw_asis["TOTAL"], 1), after=round(sw["TOTAL"], 1)),
    ratings_after_kN_m2=L.rating(b),
)
L.SEC.clear(); L.SEC.update(copy.deepcopy(KEEP))
with open(os.path.join(HERE, "upgrade_spec_alu.json"), "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out, indent=1))
