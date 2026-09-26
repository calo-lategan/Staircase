"""Component checks of the FINAL model (25.9.2026 IFC, standard state), EN 1999-1-1 (6082-T6, t <= 5: f_o 250, f_u 290;
bar/rod: f_o 250, f_u 295), gM1 1.1, gM2 = gMp 1.25. Forces: side-frame envelope (base pinned / base sliding) from
side_frame.py with the tread-FE pin forces; barrier loads per the sheet (R142 3.0 kN/m @ top rail, R143 1.25 kN,
R179 1.5 kN post, R178 1.0 kN/m vertical). All geometry measured in the IFC (see parts_final.json / cuts)."""
import json, math
import numpy as np
import side_frame as SF, run_side_frame as R

F0, FU, F0B, FUB, GM1, GM2 = 250.0, 290.0, 250.0, 295.0, 1.1, 1.25
FD = F0 / GM1
rows = []
COND = ["slides"]
def add(item, ref, check, value, limit, unit, note=""):
    u = value / limit if limit else float("inf")
    rows.append(dict(base=COND[0], item=item, ref=ref, check=check, value=round(value, 1), limit=round(limit, 1), unit=unit, util=round(u, 2),
                     status="PASS" if u <= 1.0 else "FAIL", note=note))

# ---------------- frame envelope, per base condition
# "slides": jacks on footplates with no fixing (as drawn) -> no horizontal reaction at the base.
# "held": base pegged/bolted -> large horizontal couple AND uplift at the top hooks (needs a keeper; not drawn).
SF.VERTICAL_AT_UPPER = True
# hook plates as drawn: which directions the plate itself can bear on (inner contour within 13.6 mm of the axle centre)
_HC = json.load(open("cuts_hooks.json")); _AX = {"base": (9636.057, -89.372), "top": (8135.799, 960.600)}
def _cover(hid, key):
    cx, cz = _AX[key]; cov = set()
    for (p, q) in _HC[hid][hid]:
        for t in [i / 20 for i in range(21)]:
            x = (p[0] + (q[0] - p[0]) * t) * 1000; z = (p[2] + (q[2] - p[2]) * t) * 1000
            if math.hypot(x - cx, z - cz) < 13.6: cov.add(int(math.floor(math.degrees(math.atan2(z - cz, x - cx)))) % 360)
    return cov
HOOKS = {"L": {"base": _cover("E8541_L07", "base"), "top": _cover("E8522_L07", "top")},
         "R": {"base": _cover("E11170_L07", "base"), "top": _cover("E11386_L07", "top")}}
def _needs_lock(side, key, f):
    ang = math.degrees(math.atan2(f[1], f[0])) % 360
    return not all(int(ang + k) % 360 in HOOKS[side][key] for k in (-3, 0, 3))
ENVS = {}
for cond, slide in (("slides", True), ("held", False)):
    env = dict(R_base=0, R_top=0, link=0, latch=0, uplift_top=0, H_base=0, V_base=0, lock_base=0, lock_top=0)
    for side in ("L", "R"):
        for only in (None, {3, 4, 5}, {0, 1, 2}):
            out = SF.run(side, R.pf("ULS crowd", side, only), bracket_rigid=True, base_slides=slide)
            rb, rt = out["reactions"]["base"], out["reactions"]["top"]
            env["R_base"] = max(env["R_base"], math.hypot(*rb)); env["R_top"] = max(env["R_top"], math.hypot(*rt))
            env["H_base"] = max(env["H_base"], abs(rb[0])); env["V_base"] = max(env["V_base"], rb[1])
            env["uplift_top"] = max(env["uplift_top"], -rt[1])
            if _needs_lock(side, "base", rb): env["lock_base"] = max(env["lock_base"], math.hypot(*rb))
            if _needs_lock(side, "top", rt): env["lock_top"] = max(env["lock_top"], math.hypot(*rt))
            env["link"] = max(env["link"], max(abs(v) for v in out["links"].values()))
            env["latch"] = max(env["latch"], max(abs(p[2]) for p in out["pole_forces"]))
    ENVS[cond] = env
    print(f"frame envelope, base {cond} (ULS crowd, per side):", {k: round(v) for k, v in env.items()})

def component_rows(cond, env):
    # ---------------- axle O25 x 2.5 tube on the base jacks (jacks at y -18404 / -17031; hooks at y -18334 / -17093)
    D, t = 25.0, 2.5; A_ax = math.pi / 4 * (D ** 2 - (D - 2 * t) ** 2); I_ax = math.pi / 64 * (D ** 4 - (D - 2 * t) ** 4); W_ax = I_ax / (D / 2)
    a_L, a_R = 70.0, 62.0                     # hook offset from the jack supports (measured)
    M_ax = env["R_base"] * max(a_L, a_R)
    add("Base axle O25x2.5", "R147/R160", "Bending at the hook (hook 70 mm inboard of the jack)", M_ax / W_ax, FD, "MPa",
        f"R = {env['R_base']:.0f} N per side; W = {W_ax:.0f} mm3. The model has two overlapping tubes at every axle position (duplicates)")
    Vpl = 2 * A_ax / math.pi * F0 / math.sqrt(3) / GM1
    add("Base axle O25x2.5", "R147", "Shear", env["R_base"], Vpl, "N")
    M_top = env["R_top"] * 70.0
    add("Top axle O25x2.5", "R147", "Bending at the hook on the landing brackets", M_top / W_ax, FD, "MPa", f"R = {env['R_top']:.0f} N; bracket span assumed like the base")

    # ---------------- hooks: 10 mm plates, ring below the axle ~22 mm wide (measured outline); curved-beam throat
    t_h, b_h, r_i = 10.0, 22.0, 12.8
    r_c = r_i + b_h / 2
    A_h, W_h = t_h * b_h, t_h * b_h ** 2 / 6
    k_curv = 1 + (b_h / 2) / (3 * r_c) * 2          # Winkler inner-fibre factor (approx.)
    for nm, Rr in (("base", env["R_base"]), ("top", env["R_top"])):
        sig = Rr / A_h + k_curv * Rr * r_c / W_h
        add(f"Hook plate 10 mm ({nm})", "R150/R170", "Throat: N/A + M/W (curved beam, M = R x r_centroid)", sig, FD, "MPa",
            "approximate (hand): a plane-stress FE of the hook with contact is recommended for the final sign-off")
        Fb = 1.5 * t_h * D * F0 / GM2
        add(f"Hook plate 10 mm ({nm})", "R170", "Bearing of the axle on the hook", Rr, Fb, "N")

    # ---------------- base jacks: threaded rod O24 (M24 stress area 353 mm2), footplate 100 x 100 x 5
    Ns = env["V_base"]              # vertical component (the held case also pushes the jack 10.9 kN sideways - see note)
    add("Base jack rod M24", "R147/R174", "Axial (stress area 353 mm2)", Ns / 353.0, FD, "MPa")
    p = Ns / (100 * 100); c = (100 - 24) / 2
    m = p * c ** 2 / 2
    add("Footplate 100x100x5", "R73/R174", "Plate bending as a cantilever from the rod (uniform ground pressure)", 6 * m / 5 ** 2, FD, "MPa",
        f"ground pressure {p:.2f} MPa; R73 recommends 150x150 base plates")
    if env["H_base"] > 1.0:
        H, V, lev = env["H_base"], env["V_base"], 30.0         # axle centre about 30 mm above the footplate (measured)
        Wr = math.pi * 21.2 ** 3 / 32                             # M24: stress area 353 mm2 -> d_eq 21.2 mm
        add("Base jack rod M24", "R147/R174", "Axial + bending from the sideways base force (base held)", V / 353.0 + H * lev / Wr, F0B / GM1, "MPa",
            f"H = {H:.0f} N at {lev:.0f} mm above the footplate")
        B = 100.0; ecc = H * lev / V
        pmax = V / B ** 2 * (1 + 6 * ecc / B) if ecc <= B / 6 else 2 * V / (3 * (B / 2 - ecc) * B)
        add("Footplate 100x100x5", "R73/R174", "Plate bending with the rod moment (base held, uneven ground pressure)", 6 * (pmax * c ** 2 / 2) / 5 ** 2, FD, "MPa",
            f"eccentricity {ecc:.0f} mm, peak ground pressure {pmax:.2f} MPa")
        add("Base held by friction alone", "R147/R174", "Friction coefficient needed at the footplate (H / V)", H / V, 0.5, "-",
            "aluminium on timber or concrete is about 0.4-0.5; above that the base needs pegs or a fixing to the scaffold")

    # ---------------- top landing brackets: 137/140 square x 5 plates, O20 pins, wing clamps
    Rt = env["R_top"]
    Fv20 = 0.6 * math.pi * 10 ** 2 * FUB / GM2
    add("Top bracket pin O20", "R170", "Pin shear (single shear)", Rt, Fv20, "N")
    add("Top bracket plate 5 mm", "R170", "Pin bearing on the 5 mm plate", Rt, 1.5 * 5 * 20 * F0 / GM2, "N",
        "the bracket's fixing to the landing / cabin is not modelled: the anchor design must follow from this reaction")

    # ---------------- latch pins O2 (cross pins through the pole above / below the webs)
    Fv2 = 2 * 0.6 * math.pi * 1.0 ** 2 * FUB / GM2
    add("Latch pins O2 (per pole)", "R78/R104", "Vertical transfer between the rails through the pole (double shear)", env["latch"], Fv2, "N",
        "without these pins the side frame is a mechanism (0.55-0.68 m deflection at ULS)")

    # ---------------- tread pins with the frame link force added (link force passes pin to pin)
    Fv10 = 0.6 * math.pi * 25 * FUB / GM2; W10 = math.pi * 10 ** 3 / 32; M10 = 1.5 * W10 * F0B / GM2
    Vt = env["link"] + 1300.0
    add("Tread pins O10 (with link force)", "R170", "Shear: link force + tread reaction", Vt, Fv10, "N", f"link {env['link']:.0f} N (top tread)")
    add("Tread pins O10 (with link force)", "R170", "Bending, lever 6.75 mm (left) - 14 mm (right)", Vt * 14.0, M10, "Nmm")

    # ---------------- barrier (per side): poles RHS 25 (along the stair) x 10 (across) x 2 wall, pitch 250 mm (plan)
    Ipole_w, c_w = 1706.0, 5.0
    Wp = Ipole_w / c_w
    spacing_slope = 250.0 / math.cos(math.radians(35))       # 305 mm along the flight
    h_arm = 1050.0                                            # upper rail web to the top rail (measured at x = 9397)
    for ref, desc, Hk in (("R142", "Line load 3.0 kN/m at the top rail", 3.0 * spacing_slope), ("R143", "Point load 1.25 kN at the top rail over a pole", 1250.0),
                          ("R179", "Post load 1.5 kN at the top of a pole", 1500.0), ("R142 (5.0)", "Viewing crowd 5.0 kN/m", 5.0 * spacing_slope)):
        Mp = 1.5 * Hk * h_arm
        add("Pole RHS 25x10x2", ref, f"{desc}: bending across the stair", Mp / Wp, FD, "MPa", f"H_k = {Hk:.0f} N per pole, arm {h_arm:.0f} mm, W = {Wp:.0f} mm3")
    # top rail U 25x25x5 spanning 305 mm between posts, vertical 1.0 kN/m (R178) and horizontal 3.0 kN/m (R142)
    Wu = 18947 / 12.5
    add("Top rail U25x25x5", "R178", "Vertical 1.0 kN/m, span 305 (continuous, wL2/10)", 1.5 * 1.0 * spacing_slope ** 2 / 10 / Wu, FD, "MPa")
    add("Top rail U25x25x5", "R142", "Horizontal 3.0 kN/m, span 305", 1.5 * 3.0 * spacing_slope ** 2 / 10 / (26926 / 12.5), FD, "MPa")
    # handrail brackets: bent flats 15 x 5 (measured 15 mm), zig-zag, carrying the handrail load over 57 mm offset
    Wb = 5 * 15 ** 2 / 6
    add("Handrail bracket 15x5 bent flat", "R143", "1.25 kN on the handrail at a bracket: bending over the 57 mm offset", 1.5 * 1250 * 57 / Wb, FD, "MPa",
        "bracket thickness 5 mm assumed (15 mm measured width); zig-zag path makes it softer still")


for cond, env in ENVS.items():
    COND[0] = cond
    component_rows(cond, env)
json.dump(dict(envelopes=ENVS, envelope=ENVS["held"], rows=rows), open("component_checks_final.json", "w"), indent=1)
w = max(len(r["item"] + r["check"]) for r in rows) + 3
for r in rows:
    print(f"{r['base']:<6} {r['status']:<5} {r['util']:6.2f}  {r['ref']:<11} {(r['item'] + ' - ' + r['check']):<{w}} {r['value']:>10} / {r['limit']:<9} {r['unit']:<4} {r['note']}")
