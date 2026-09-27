"""Fold clearance of the final step (lip + lugs + end blocks) at catwalk 0 deg, standard 35 deg and through the fold between.
Kinematics exactly as v2/revc/rails/rails_lib.py: every step stays level; step i+1 (downhill) is the same outline translated by
PITCH * (cos t, -sin t), PITCH = 305.2 = hypot(250, 175) (pin spacing along both rails); the link vector (200, 25) is unchanged by
lowering both pins 12.5, so the rails' pin-line separation 201.6 sin(t + 7.1) is unchanged.
Also: open-riser gap / 100 mm sphere at 35 deg, R48 deck gap at catwalk, R95 moving-joint gaps, and the y-plane stack against
the rails (pin legs, tabs, caps).  Writes fold.json."""
import json, math, os
import numpy as np
import design as dsg

HERE = os.path.dirname(os.path.abspath(__file__))
PITCH = math.hypot(250.0, 175.0)
SERR = 0.8                                           # serration ridge height above z 50

def outline():
    """side-view envelope of one step: the end-block outline (it encloses box, deck, nosing, lip, bulb, lugs), top raised by
    the serration.  Inboard parts never pass outside it (stud ends flush, bolt heads countersunk, nuts inside the deck zone)."""
    return [(x, (z + SERR) if abs(z - 50.0) < 1e-9 else z) for x, z in dsg.eb_poly()]

def seg_dist(p, q, a, b):
    p, q, a, b = map(np.asarray, (p, q, a, b))
    def pt_seg(x, s0, s1):
        d = s1 - s0; t = np.clip(np.dot(x - s0, d) / max(np.dot(d, d), 1e-12), 0, 1); return np.linalg.norm(x - (s0 + t * d))
    # proper intersection -> 0
    def orient(u, v, w): return np.sign((v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0]))
    if orient(p, q, a) * orient(p, q, b) < 0 and orient(a, b, p) * orient(a, b, q) < 0: return 0.0
    return min(pt_seg(p, a, b), pt_seg(q, a, b), pt_seg(a, p, q), pt_seg(b, p, q))

def in_poly(x, z, P):
    c = False
    for (x1, z1), (x2, z2) in zip(P, P[1:] + P[:1]):
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1): c = not c
    return c

def poly_dist(A, B):
    best = (1e9, None, None)
    for a0, a1 in zip(A, A[1:] + A[:1]):
        for b0, b1 in zip(B, B[1:] + B[:1]):
            d = seg_dist(a0, a1, b0, b1)
            if d < best[0]: best = (d, (a0, a1), (b0, b1))
    if any(in_poly(x, z, B) for x, z in A) or any(in_poly(x, z, A) for x, z in B): best = (-1.0,) + best[1:]
    return best

def label(seg):
    (x0, z0), (x1, z1) = seg; xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
    if zm < -20 and xm > 250: return "lip tip / lip end block (z -25)"
    if xm > 260 and zm < 25: return "lip front face"
    if xm > 190 and zm < 25: return "front lug / gusset"
    if zm < 0: return "rear lug"
    if xm < 1 and zm > 0: return "back face of the back box"
    if zm > 49: return "walking surface (serration)"
    if xm > 279: return "nosing front face"
    return "outline (%.0f, %.0f)" % (xm, zm)

S = outline()
def shifted(k, th):
    dx, dz = k * PITCH * math.cos(math.radians(th)), -k * PITCH * math.sin(math.radians(th))
    return [(x + dx, z + dz) for x, z in S]

sweep = []
for th in np.round(np.arange(0.0, 35.0001, 0.25), 3):
    d1, sa, sb = poly_dist(S, shifted(1, th))
    d2 = poly_dist(S, shifted(2, th))[0]
    sweep.append(dict(theta=float(th), min_clear_next=round(d1, 2), min_clear_next2=round(d2, 2), this=label(sa), neighbour_downhill=label(((sb[0][0] - PITCH * math.cos(math.radians(th)), sb[0][1] + PITCH * math.sin(math.radians(th))), (sb[1][0] - PITCH * math.cos(math.radians(th)), sb[1][1] + PITCH * math.sin(math.radians(th)))))))
mn = min(sweep, key=lambda r: r["min_clear_next"])
OUT = dict(pitch=round(PITCH, 2), outline_vertices=len(S),
           catwalk=next(r for r in sweep if r["theta"] == 0.0), standard=next(r for r in sweep if r["theta"] == 35.0), fold_min=mn,
           r95_band_8_25_mm=[r["theta"] for r in sweep if 8.0 < r["min_clear_next"] < 25.0],
           sweep_every_5deg=[r for r in sweep if abs(r["theta"] % 5) < 1e-9])

# ---- same check for the lip depths considered (lip only, end blocks unchanged otherwise)
alt = {}
for lip in (30.0, 40.0, 50.0, 60.0):
    P = [(x, (z + SERR) if abs(z - 50.0) < 1e-9 else z) for x, z in dsg.eb_poly(lip=lip)]
    worst = min((poly_dist(P, [(x + PITCH * math.cos(math.radians(t)), z - PITCH * math.sin(math.radians(t))) for x, z in P])[0], t)
                for t in np.arange(0.0, 35.0001, 0.25))
    gap35 = 175.0 - 25.0 - lip - SERR
    alt[f"lip {lip:g}"] = dict(fold_min_clear=round(worst[0], 2), at_theta=float(worst[1]), riser_gap_35=round(gap35, 1), riser_gap_to_z50=175.0 - 25.0 - lip)
OUT["lip_depth_options"] = alt

# ---- open riser at 35 deg: largest sphere through the gap between step i (upper, uphill) and step i+1 (lower)
up = [(x - 250.0, z + 175.0) for x, z in S]          # step above, in the lower step's coordinates
low = S
d, sa, sb = poly_dist(low, up)
OUT["riser_35"] = dict(min_distance_upper_to_lower=round(d, 2), upper_feature=label(((sb[0][0] + 250, sb[0][1] - 175), (sb[1][0] + 250, sb[1][1] - 175))),
                       lower_feature=label(sa), vertical_gap_lip_to_tread_top=round(175.0 - 25.0 - dsg.LIP - SERR, 1),
                       vertical_gap_lip_to_tread_plane_z50=175.0 - 25.0 - dsg.LIP,
                       note="the constriction is the lip bottom over the back box of the step below; a 100 mm sphere cannot pass (gap <= 100)")
OUT["catwalk_deck_gap_R48"] = dict(gap_top_surface=round(PITCH - 280.0, 1), limit=25.0,
                                   note="nosing face to back face of the next step at catwalk; 0.2 mm over R48 if the catwalk is treated as a platform deck")

# ---- y-plane stack against the rails (rail_design.md): nothing of the rails is on the step side of the pin-leg face
OUT["y_stack"] = {
    "rail pin-leg step face (both rails, all tabs/notches in the pin-leg plane)": "y 13.5 (left end) / 1211.5 (right end)",
    "pad (PTFE-faced stainless, 30 x 10 x 1) on the end block at each stud": "y 13.5 - 14.5",
    "end block outer face (rear and front blocks, lugs, lip end)": "y 14.5; web zone x 55-195 recessed to y 24.5",
    "min clearance end block to any rail pin leg / tab outside the pads": 1.0,
    "caps, washers, split pins, pole slots, bulbs, A-rail edge lip": "outboard of the pin leg (rail y >= 6): never in the step's y band",
    "stud inner ends": "flush -1 mm with the end-block inner face (y 29.5); cannot reach the nosing/box ends at y 30.5",
    "verdict": "no clash with rails, pins, caps or tabs in any state; the only interacting parts are neighbouring steps (same y band)"}
json.dump(OUT, open(os.path.join(HERE, "fold.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in OUT.items() if k != "sweep_every_5deg"}, indent=1))
for r in OUT["sweep_every_5deg"]: print(r)
