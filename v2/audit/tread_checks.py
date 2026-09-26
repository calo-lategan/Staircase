"""EN 1999-1-1 checks for the as-modelled tread, from the validated shell FE (tread_cases.json) cross-checked by the
Vlasov thin-walled calculation (tread_vlasov.py). Material EN AW-6082-T6, all parts t = 5 mm.
EN 1999-1-1 Table 3.2b (extruded profiles, t <= 5): f_o = 250, f_u = 290 ; HAZ f_o,haz = 125, f_u,haz = 185.
Pins (extruded bar D <= 20): f_op = 250, f_up = 295.  gM1 = 1.10, gM2 = gMp = gMw = 1.25.
Span between pin bearings L = 1226.5 - 10.49 = 1216.0 mm."""
import json, math

F0, FU, F0_HAZ, FU_HAZ = 250.0, 290.0, 125.0, 185.0
F0P, FUP = 250.0, 295.0
GM1, GM2, GMP = 1.10, 1.25, 1.25
L = 1226.5 - 10.49
C = json.load(open("tread_cases.json"))

rows = []
def add(ref, check, value, limit, unit, util, note=""):
    rows.append(dict(ref=ref, check=check, value=round(value, 2), limit=round(limit, 2), unit=unit, util=round(util, 3),
                     status="PASS" if util <= 1.0 else "FAIL", note=note))

# ---------------------------------------------------------------- T1 strength of the profile (ULS, body, away from the welded ends)
fd = F0 / GM1
for k, v in C.items():
    if not k.startswith("ULS"):
        continue
    vm = v["vm_max_body"]
    add("R113/R114" if "patch" in k else "R113/R128", f"Profile stress (von Mises), {k}", vm[0], fd, "MPa", vm[0] / fd,
        f"peak at x={vm[11]} y={vm[12]} z={vm[13]} ({['upturn','bottom flange','rear wall','deck','front lip','return'][vm[10]]})")

# deck class 4 (EN 1999-1-1 6.1.4/6.1.5): internal element b = 270 (between rear wall and lip), beta = b/t = 54
beta = 270.0 / 5.0; eps = math.sqrt(250.0 / F0)
rho_c = min(1.0, 32.0 / (beta / eps) - 220.0 / (beta / eps) ** 2)        # class A, unwelded, internal part
dm = min(((v["deck_membrane_min"][4], k) for k, v in C.items() if k.startswith("ULS")))
add("EN1999 6.1.5", f"Deck mid-plane compression vs class-4 local buckling (rho_c f_o/gM1), {dm[1]}", abs(dm[0]), rho_c * fd, "MPa",
    abs(dm[0]) / (rho_c * fd), f"beta = b/t = {beta:.0f} > 22 eps -> class 4, rho_c = {rho_c:.3f}, t_eff = {5*rho_c:.2f} mm")
dv = max(((v["deck_vm_max"][0], k, v["deck_vm_max"]) for k, v in C.items() if k.startswith("ULS")))
add("R114", f"Deck local plate bending under the patch (von Mises at the surface), {dv[1]}", dv[0], fd, "MPa", dv[0] / fd,
    f"5 mm deck spanning 275 mm between the rear wall and the front lip; at x={dv[2][11]} y={dv[2][12]}")

# ---------------------------------------------------------------- T2 deflection (SLS)
d = C["SLS crowd 7.5 kN/m2"]
add("R115", "Crowd 7.5 kN/m2: deflection at the nosing (front lip) vs L/250", abs(d["uz_mid_front_lip"]), L / 250, "mm",
    abs(d["uz_mid_front_lip"]) / (L / 250), f"back edge {abs(d['uz_mid_back']):.2f} mm; twist {d['twist_mid_deg']:.2f} deg (open section twists)")
p = C["SLS person 1 kN at nosing, mid-span (100x100)"]
add("R115", "One person 1 kN at the nosing: deflection < 10 mm", abs(p["uz_min"]), 10.0, "mm", abs(p["uz_min"]) / 10.0)
for pos in ("front", "centre", "back"):
    q = C[f"SLS 4 kN patch {pos}, mid-span"]
    lim = min(L / 100, 25.0)
    add("R115 (EN 12811)", f"4 kN patch ({pos}): deflection vs L/100 and 25 mm", abs(q["uz_min"]), lim, "mm", abs(q["uz_min"]) / lim)

# ---------------------------------------------------------------- T3 pins (EN 1999-1-1 8.5.14 / Table 8.8 pin connections)
d_pin = {"L_rear": 10.73, "L_front": 10.0, "R_rear": 10.0, "R_front": 10.0}
lever = {"L_rear": 17.5 - 10.49, "L_front": 17.5 - 10.49, "R_rear": 1226.5 - 1212.5, "R_front": 1226.5 - 1212.5}   # cap mid-plane -> rail wall mid-plane
e_sc = {"L_rear": 15.0, "L_front": 15.0, "R_rear": 10.0, "R_front": 10.0}    # wall mid-plane -> rail shear centre (U 35 / inv. U 25): rail torsion held by the pin
worst = {}
for k, v in C.items():
    if not k.startswith("ULS"):
        continue
    for pn, (fx, fy, fz) in v["pins"].items():
        V = math.hypot(fx, fz)
        if V > worst.get(pn, (0,))[0]:
            worst[pn] = (V, fx, fz, k)
pin_res = {}
for pn, (V, fx, fz, k) in worst.items():
    d = 10.0                                    # hole O10: bearing and the fitted pin diameter
    A = math.pi * d * d / 4; W = math.pi * d ** 3 / 32
    FvRd = 0.6 * A * FUP / GMP
    MRd = 1.5 * W * F0P / GMP
    FbRd = 1.5 * 5.0 * d * min(F0, F0P) / GMP
    M_cant = V * lever[pn]
    M_tot = math.hypot(fz * (lever[pn] + e_sc[pn]), fx * lever[pn])
    inter = (M_tot / MRd) ** 2 + (V / FvRd) ** 2
    pin_res[pn] = dict(case=k, V=V, M_cantilever=M_cant, M_with_rail_torsion=M_tot)
    add("R170 / EN1999 T8.8", f"Pin {pn} shear ({k})", V, FvRd, "N", V / FvRd)
    add("R170 / EN1999 T8.8", f"Pin {pn} bearing on the 5 mm rail wall", V, FbRd, "N", V / FbRd)
    add("R170 / EN1999 T8.8", f"Pin {pn} bending, cantilever cap->wall ({lever[pn]:.1f} mm) only", M_cant, MRd, "Nmm", M_cant / MRd)
    add("R170 / EN1999 T8.8", f"Pin {pn} bending incl. rail-torsion restraint (+{e_sc[pn]:.0f} mm to the rail shear centre)", M_tot, MRd, "Nmm", M_tot / MRd,
        "the U-channel has almost no torsional stiffness (J ~ 3,100 mm4), so the offset of the pin load from its shear centre is held by the pin")
    add("R170 / EN1999 T8.8", f"Pin {pn} shear + bending interaction", inter, 1.0, "-", inter)
    if pn.startswith("R"):
        a_req = V * GMP / (2 * 5.0 * F0) + 2 * 10.0 / 3
        add("EN1999 T8.8 geometry", f"Right rail wall hole: edge distance below the O10 hole to the free bottom edge ({pn})", 2.5, a_req, "mm",
            a_req / 2.5, "inverted-U right rails: the pin pushes down toward the free edge; only 2.5 mm of wall below the hole")
json.dump(dict(rows=rows, pins=pin_res, rho_c=rho_c), open("tread_checks.json", "w"), indent=1)
w = max(len(r["check"]) for r in rows)
for r in rows:
    print(f"{r['status']:<5} {r['util']:6.2f}  {r['ref']:<20} {r['check']:<{w}}  {r['value']:>10} / {r['limit']:<9} {r['unit']:<4} {r['note']}")
