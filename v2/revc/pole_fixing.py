"""Rev C: pole-to-rail fixing. The pole is a cantilever held by a couple at the two rail crossings: the moment is largest at the
UPPER rail and about zero at the LOWER rail. A bolt hole through the pole's depth at the upper rail removes most of the section,
so the upper fixing must be a strap round the pole, and only the lower fixing a through-pin. Same demand as after_changes.py.
Output: revc/pole_fixing.json"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
AC = json.load(open(os.path.join(HERE, "after_changes.json")))
F = AC["pole_fix"]["F_kN"] * 1000                      # couple force at each rail crossing, N (5.0 kN/m viewing, ULS)
FL = 5891.794209530463 / 2 * 2                         # rail-to-rail lock force per pole at the lower rail (final_results latch, per pole)
d0 = 17.0                                              # Ø16 pin in a Ø17 hole
Wg1 = 25 * 55 ** 2 / 6; Wreq = AC["poles"]["R1_tapered_solid_25x55"]["util"] * Wg1
def rhsI(b, h, t): return (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12
Ig2 = rhsI(40, 80, 3); Wg2 = Ig2 / 40
In2 = Ig2 - 2 * (d0 * 3 * (40 - 1.5) ** 2 + d0 * 3 ** 3 / 12); Wn2 = In2 / 40
out = {
    "demand_W_mm3": Wreq,
    "R1_solid_25x55": dict(gross=Wreq / Wg1, hole_at_upper_rail=Wreq / ((25 - d0) * 55 ** 2 / 6)),
    "R2_rhs_80x40x3": dict(gross=Wreq / Wg2, hole_at_upper_rail=Wreq / Wn2),
}
# strap at the upper rail: 2 x M12 A4-70 in tension through the 5 mm rail wall (Ø24 washers)
Ft = 0.9 * 700 * 84.3 / 1.25; Bp = 0.6 * math.pi * 21 * 5 * 290 / 1.25
strap_A = 2 * 5 * 40
out["strap_upper"] = dict(F_kN=F / 1000, bolt_tension=F / 2 / Ft, pull_through_5mm_wall=F / 2 / Bp, strap_5x40_6082=F / (strap_A * 250 / 1.1))
# through-pin at the lower rail: couple force + lock force (vector), Ø16 6082-T6, single shear; bearing on the 5 mm rail wall / 2 x 3 mm RHS
V = math.hypot(F, FL)
out["pin_lower"] = dict(V_kN=V / 1000, shear=V / (0.6 * math.pi * 64 * 295 / 1.25), bearing_rail_5mm=V / (1.5 * 5 * 16 * 250 / 1.25),
                        bearing_rhs_2x3mm=V / (2 * 1.5 * 3 * 16 * 250 / 1.25))
# cross-pin at the upper rail: Ø12 through the pole along the stair, at mid-depth (on the pole's neutral axis for the barrier push),
# through both strap legs; carries the rail-to-rail lock force (double shear). Section loss at the neutral axis is negligible.
FLk = FL
out["crosspin_upper"] = dict(F_kN=FLk / 1000, double_shear=FLk / (2 * 0.6 * math.pi * 36 * 295 / 1.25),
                             bearing_solid_25=FLk / (1.5 * 25 * 12 * 250 / 1.25), bearing_rhs_2x3mm=FLk / (2 * 1.5 * 3 * 12 * 250 / 1.25),
                             section_loss_solid=(25 * 13 ** 3 / 12) / (25 * 55 ** 3 / 12), section_loss_rhs=(2 * 3 * 13 ** 3 / 12) / rhsI(40, 80, 3))
# route 2 rails if bent from 5083-H111 sheet instead of 6082-T6 extrusion (f0 125 instead of 250)
out["rails_in_5083"] = dict(net=AC["rails"]["util_net"] * 2, lateral_right=AC["rails"]["lateral_right"] * 2)
json.dump(out, open(os.path.join(HERE, "pole_fixing.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
