"""Barrier load path with a strong pole (F4): pole bending at the upper-rail crossing -> a couple of sideways forces on
the upper and lower rail (vertical spacing s between the crossings) -> each rail bends sideways between the step pins
(lateral supports) -> steps carry it across. Also sizes the solid pole (uniform and tapered) with ~15 % headroom.
6082-T6: f_o 250 (t <= 5 extrusion walls; bar f_o 250), gM1 1.1. Loads per the sheet: R142 3.0 kN/m (5.0 viewing),
R143 1.25 kN, R179 1.5 kN post; ULS factor 1.5; arm 1,050 from the upper rail to the top rail; poles 250 plan / 305 slope."""
import json, math
FD = 250 / 1.1
spacing = 250 / math.cos(math.radians(35))
H = {"R142 3.0 kN/m": 3.0 * spacing, "R143 1.25 kN": 1250.0, "R179 1.5 kN post": 1500.0, "R142 5.0 kN/m viewing": 5.0 * spacing}
ARM = 1050.0
def rects(rs):
    """lateral W: bending about the rail's vertical axis -> use the across-stair coordinate (first) of each rectangle"""
    rs = [(y0, x0, y1, x1) for x0, y0, x1, y1 in rs]            # swap so the formula below works on the across coordinate
    A = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in rs)
    cy = sum((x1 - x0) * (y1 - y0) * (y0 + y1) / 2 for x0, y0, x1, y1 in rs) / A
    I = sum((x1 - x0) * (y1 - y0) ** 3 / 12 + (x1 - x0) * (y1 - y0) * ((y0 + y1) / 2 - cy) ** 2 for x0, y0, x1, y1 in rs)
    ys = [y for r in rs for y in (r[1], r[3])]
    return I / max(max(ys) - cy, cy - min(ys))
# lateral section modulus (bending about the rail's vertical axis): rectangles as (y0, z0, y1, z1) with y across the stair
RAILS = {
    "left rails U 35 x 25 x 5 (now)": rects([(0, 0, 5, 25), (30, 0, 35, 25), (0, 0, 35, 5)]),
    "right lower inv. U 25 x 25 x 5 (now)": rects([(0, 0, 5, 25), (20, 0, 25, 25), (0, 20, 25, 25)]),
    "right upper inv. U 25 x 20 x 5 (now)": rects([(0, 0, 5, 20), (20, 0, 25, 20), (0, 15, 25, 20)]),
    "left rails U 35 x 65 x 5 (F2)": rects([(0, 0, 5, 65), (30, 0, 35, 65), (0, 0, 35, 5)]),
    "right rails inv. U 25 x 65 x 5 (F2)": rects([(0, 0, 5, 65), (20, 0, 25, 65), (0, 60, 25, 65)]),
}
# crossings: vertical distance between the two rail webs at a pole, and the pole's position between the step pins along each rail
s_cross = 167.0
a_lo, b_lo = 138.0, 167.0          # along the lower rail: pole to the neighbouring rear pins (slope mm)
a_up, b_up = 106.0, 199.0          # along the upper rail: pole to the neighbouring front pins
out = dict(pole={}, rails={}, couple={})
for k, h in H.items():
    M = 1.5 * h * ARM
    F = M / s_cross
    out["couple"][k] = dict(M_kNm=M / 1e6, F_kN=F / 1e3)
    for rn, W in RAILS.items():
        a, b = (a_up, b_up) if "upper" in rn else (a_lo, b_lo)
        Ml = F * a * b / (a + b)                          # simply supported between step pins (conservative)
        out["rails"].setdefault(rn, {})[k] = round(Ml / W / FD, 2)
    for D in (39, 45, 51, 55, 60):
        out["pole"].setdefault(f"solid 25 x {D}", {})[k] = round(M / (25 * D * D / 6) / FD, 2)
L = 1138.0
for D0 in (55,):
    # tapered: full D0 from the bottom through both rails (lock end + 250 mm), then depth ~ sqrt of the moment, min 15
    import numpy as np
    hs = np.linspace(0, ARM, 200); D = np.maximum(15.0, D0 * np.sqrt(1 - hs / ARM))
    A_taper = 25 * (np.trapz(D, hs) + D0 * (L - ARM))
    out["pole_mass_12_kg"] = dict(uniform_25x55=12 * 25 * 55 * L * 2.7e-6, tapered_25x55_to_15=12 * A_taper * 2.7e-6, now_rhs=12 * 124 * L * 2.7e-6)
json.dump(out, open("barrier_path_check.json", "w"), indent=1)
print(json.dumps(out, indent=1))
