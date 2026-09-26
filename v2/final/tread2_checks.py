"""EN 1999-1-1 checks of the FINAL tread from tread2_cases.json (FE, validated: exact equilibrium, shell-bar variant within
3 %, independent branched-section Vlasov within 12 %). 6082-T6, t <= 5: f_o 250, f_u 290; gM1 1.1, gM2 = gMp 1.25.
Span between pin bearings L = 1215 mm."""
import json, math
F0, FU, F0P, FUP, GM1, GMP = 250.0, 290.0, 250.0, 295.0, 1.1, 1.25
L = 1226.5 - 10.75
C = json.load(open("tread2_cases.json"))
fd = F0 / GM1
rows = []
def add(ref, check, value, limit, unit, note=""):
    u = value / limit
    rows.append(dict(ref=ref, check=check, value=round(value, 2), limit=round(limit, 2), unit=unit, util=round(u, 3), status="PASS" if u <= 1 else "FAIL", note=note))

for k, v in C.items():
    if k.startswith("ULS"):
        vb = v["vm_max_body"]
        add("R113" if "crowd" in k else "R114", f"Frame stress (von Mises) - {k}", vb[0], fd, "MPa", f"at {vb[7]} x={vb[8]} y={vb[9]} z={vb[10]}")
        add("R113" if "crowd" in k else "R114", f"Grating bar 3x25 stress - {k}", v["bar_max"][0], fd, "MPa", f"bar at y={v['bar_max'][1]['bar_y']}")
        fl = v["vm_by_part"].get("flat")
        if fl: add("R113" if "crowd" in k else "R114", f"Flat 2.7x25 stress - {k}", fl[0], fd, "MPa", f"flat x={fl[8]} y={fl[9]}; sigma_long {fl[1]:.0f} MPa (compression at the top edge)")
d = C["SLS crowd 7.5 kN/m2"]
add("R115", "Crowd 7.5 kN/m2: nosing deflection vs L/250", abs(d["uz_mid_lip_top"]), L / 250, "mm", f"twist {d['twist_mid_deg']:.2f} deg; back edge {abs(d['uz_mid_rearwall_top']):.2f} mm")
p = C["SLS person 1 kN at nosing (100x100)"]
add("R115", "One person 1 kN at the nosing: deflection < 10 mm", abs(p["uz_min"]), 10.0, "mm")
for pos in ("front", "centre", "back"):
    q = C[f"SLS 4 kN patch {pos}, mid-span"]
    add("R115 / EN 12811", f"4 kN patch ({pos}): deflection vs L/100 (and <= 25 mm)", abs(q["uz_min"]), min(L / 100, 25), "mm", f"twist {q['twist_mid_deg']:.1f} deg")
# pins (same geometry as before): worst ULS resultant per pin
lever = {"L_rear": 6.75, "L_front": 6.75, "R_rear": 14.0, "R_front": 14.0}   # end-plate mid-plane -> rail-wall mid-plane
e_sc = {"L_rear": 15.0, "L_front": 15.0, "R_rear": 10.0, "R_front": 10.0}
worst = {}
for k, v in C.items():
    if not k.startswith("ULS"): continue
    for pn, (fx, fy, fz) in v["pins"].items():
        V = math.hypot(fx, fz)
        if V > worst.get(pn, (0,))[0]: worst[pn] = (V, fx, fz, k)
d_ = 10.0; A = math.pi * d_ ** 2 / 4; W = math.pi * d_ ** 3 / 32
FvRd = 0.6 * A * FUP / GMP; MRd = 1.5 * W * F0P / GMP; FbRd = 1.5 * 5 * d_ * F0 / GMP
for pn, (V, fx, fz, k) in worst.items():
    Mc = V * lever[pn]; Mt = math.hypot(fz * (lever[pn] + e_sc[pn]), fx * lever[pn])
    add("R170", f"Pin {pn} shear ({k})", V, FvRd, "N")
    add("R170", f"Pin {pn} bearing on the 5 mm rail wall", V, FbRd, "N")
    add("R170", f"Pin {pn} bending, cap -> wall lever {lever[pn]} mm", Mc, MRd, "Nmm")
    add("R170", f"Pin {pn} bending incl. rail torsion (+{e_sc[pn]} mm)", Mt, MRd, "Nmm", "upper bound: the pin holds the rail's twist")
json.dump(rows, open("tread2_checks.json", "w"), indent=1)
w = max(len(r["check"]) for r in rows)
for r in rows:
    print(f"{r['status']:<5} {r['util']:6.2f}  {r['ref']:<16} {r['check']:<{w}} {r['value']:>10} / {r['limit']:<8} {r['unit']:<4} {r['note']}")
