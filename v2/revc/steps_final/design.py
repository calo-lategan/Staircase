"""FINAL step geometry (27 Sep 2026) - single source for the FE, the fold check, the hand checks and the drawing table.
Tread-local axes as in v2/revc/steps_opt: x 0 = back face -> 280 = front face (nosing), z 0 = underside of the back box ->
50 = walking surface (serration adds +0.8), y along the span; end-block outer faces at y 14.5 / 1210.5 (the old end-plate
outer faces), pin-bearing (rail pin-leg) faces at y 13.5 / 1211.5 (1 mm pad).
Pins: BOTH moved down 12.5 mm (link vector (200, 25) unchanged, so the rails' kinematics, tabs, notches and slots are
unchanged): rear (25, 0.0), front (225, 25.0)."""
import math

PIN_REAR = (25.0, 0.0)
PIN_FRONT = (225.0, 25.0)
DZ_PINS = -12.5                     # vs rail_design.md (25, 12.5) / (225, 37.5)
LIP = 50.0                          # lip depth below z 25 -> lip bottom z -25
R_FRONT_LUG = 30.0                  # front lug outline radius about the front pin
R_REAR_LUG = 23.0                   # rear lug outline radius about the rear pin
LIP_BULB = (10.0, 3.0)              # flange at the lip tip, pointing back
T_LIP = 2.5
EB_T = dict(rear=16.0, web=6.0, front=16.0)
EB_X = dict(rear_end=55.0, front_start=195.0)


def arc(c, r, a0, a1, n=12):
    return [(round(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), 3),
             round(c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)), 3)) for k in range(n + 1)]


def eb_poly(lip=LIP, rf=R_FRONT_LUG, rr=R_REAR_LUG, lip_bulb=LIP_BULB, gusset=True):
    """end-block outline (counter-clockwise), side view"""
    zb = 25.0 - lip
    p = [(0.0, 50.0), (0.0, 0.0)]
    p += arc(PIN_REAR, rr, 180.0, 360.0)                    # rear lug (below the back box)
    p += [(50.0, 0.0), (50.0, 25.0), (PIN_FRONT[0] - rf, 25.0)]
    if gusset:
        p += arc(PIN_FRONT, rf, 180.0, 300.0)[1:]           # front lug round the stud
        p += [(280.0 - lip_bulb[0] - 3.0, zb), (280.0, zb)]  # gusset to the lip tip (lip end block)
    else:
        p += arc(PIN_FRONT, rf, 180.0, 360.0)[1:] + [(280.0, 25.0)]
    p += [(280.0, 50.0)]
    # drop consecutive duplicates
    out = []
    for q in p:
        if not out or math.dist(out[-1], q) > 1e-6: out.append(q)
    return out


def poly_area(p):
    return abs(sum(x1 * z2 - x2 * z1 for (x1, z1), (x2, z2) in zip(p, p[1:] + p[:1]))) / 2


def clip_x(p, x0, x1):
    """Sutherland-Hodgman clip of polygon p to x0 <= x <= x1"""
    def clip(poly, keep, inter):
        out = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            if keep(b):
                if not keep(a): out.append(inter(a, b))
                out.append(b)
            elif keep(a): out.append(inter(a, b))
        return out
    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))
    q = clip(p, lambda v: v[0] >= x0, ix(x0))
    return clip(q, lambda v: v[0] <= x1, ix(x1)) if q else q


def eb_zones():
    return [(0.0, EB_X["rear_end"], EB_T["rear"]), (EB_X["rear_end"], EB_X["front_start"], EB_T["web"]), (EB_X["front_start"], 280.0, EB_T["front"])]


def eb_mass_kg(poly=None, holes=()):
    poly = poly or eb_poly(); m = 0.0
    for x0, x1, t in eb_zones():
        m += poly_area(clip_x(poly, x0, x1)) * t
    m -= sum(math.pi * d * d / 4 * t for d, t in holes)
    return m * 2.7e-6


# C8 (step_optimisation.md) + lip + end blocks + lowered pins
C8 = {"slot_dir": "x", "rib_through_box": False, "ws": 10.0, "wsol": 8.0, "Ls": 40.0, "Lbx": 10.0, "b_r": 12.0,
      "box_diag": 2.5, "tb": 2.5, "tb_front": 4.0, "tb_bot": 3.5, "tb_top": 3.0, "ts": 2.0, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0,
      "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [12.0, 3.0], "t_cap": 6.0}


def final_cfg(**over):
    D = dict(C8)
    D.update(lip=LIP, t_lip=T_LIP, lip_bulb=list(LIP_BULB), pin_rear_z=PIN_REAR[1], pin_front_z=PIN_FRONT[1],
             eb_poly=eb_poly(over.get("lip", LIP), lip_bulb=over.get("lip_bulb", LIP_BULB)), eb_zones=eb_zones())
    D.update(over)
    return D


if __name__ == "__main__":
    p = eb_poly(); print(len(p), "vertices; area", round(poly_area(p)), "mm2; EB mass/end", round(eb_mass_kg(), 3), "kg")
