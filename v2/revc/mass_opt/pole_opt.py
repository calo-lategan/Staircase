"""Mass study (26 Sep 2026): minimum-mass barrier pole for the LOCKED inside-rail scheme (12 poles through both guide
rails, removed before folding). Checks per pole, EN 1999-1-1, gM1 1.1:
  * barrier bending across the stair at the upper-rail crossing: governing sheet load R179 1.5 kN post at the top rail
    (R142 3.0 kN/m x 305 mm x 1.13 continuity = 1.03 kN and R143 1.25 kN are lower); gamma_Q 1.5;
    arm 1,137 mm = 1,050 (barrier_path_check.py) + 87 (R63 raise, supports.md F6). Target util <= 0.90.
    Sensitivity: R142 5.0 kN/m viewing x 1.13 = 1.72 kN (not an owner load, reported only).
  * along-stair post load (poles_barrier.md A14): 1.5 kN shared by the 6 poles through the top rail -> 0.25 kN per pole
    (ESTIMATE of the sharing, not modelled) -> W_along target.
  * slot bearing: couple force F = M/167 at the upper slot bears on the 25-wide face; face wall plate bending (estimate).
  * local buckling class (EN 1999-1-1 Table 6.2, buckling class A, eps = sqrt(250/f0)); walls >= 2.5 mm (extrusion, estimate).
  * in-plane side-frame action: frame_pole_inplane.py shows <= 32 kNmm / 6 kN with the vertical lock at BOTH rails -> not governing.
Pole length (inside scheme): 40 below the lower-rail web (latch) + 167 between the rail crossings + 1,137 cantilever = 1,344.
Rail-width penalty: each mm of pole depth across the stair widens the 4 rail webs (5 mm, 1,761 + 1,849 mm per side) -> 0.0975 kg.
Output: mass_opt/pole_opt.json"""
import json, math, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
RHO = 2.7e-6
GAM, ARM, S_CROSS, L_BELOW = 1.5, 1137.0, 167.0, 40.0
L_POLE = L_BELOW + S_CROSS + ARM
P = {"R179 1.5 kN post": 1500.0, "R142 3.0 kN/m x1.13": 3.0 * 250 / math.cos(math.radians(35)) * 1.13, "R143 1.25 kN": 1250.0}
P_GOV = max(P.values()); P_VIEW = 5.0 * 250 / math.cos(math.radians(35)) * 1.13
M_ED = GAM * P_GOV * ARM; M_VIEW = GAM * P_VIEW * ARM
M_ALONG = GAM * (1500.0 / 6) * ARM
U_T = 0.90
RAIL_KG_PER_MM = 2 * (1761 + 1849) * 5 * RHO
MAT = {"6082-T651 plate (t 12.5-100)": 240.0, "6082-T6 extrusion (t<=5)": 250.0, "6005A-T6 extrusion (t<=5)": 225.0,
       "7020-T651 plate": 280.0, "7020-T6 extrusion": 290.0}

def box(D, tf, tw, b=25.0):
    I = (b * D ** 3 - (b - 2 * tw) * (D - 2 * tf) ** 3) / 12; Ia = (D * b ** 3 - (D - 2 * tf) * (b - 2 * tw) ** 3) / 12
    A = b * D - (b - 2 * tw) * (D - 2 * tf); return A, I / (D / 2), Ia / (b / 2), I
def ibeam(D, tf, tw, b=25.0):
    I = (b * D ** 3 - (b - tw) * (D - 2 * tf) ** 3) / 12; Ia = (2 * tf * b ** 3 + (D - 2 * tf) * tw ** 3) / 12
    A = 2 * b * tf + (D - 2 * tf) * tw; return A, I / (D / 2), Ia / (b / 2), I

def face_bearing_util(tf, clear, fd, F):
    """end wall of width `clear` loaded by the slot-edge line (6 mm tall contact), simply supported/fixed average (k=10),
    effective height 6 + clear (45 deg spread). ESTIMATE."""
    q = F / clear; m = q * clear ** 2 / 10 / (6 + clear); return m / (tf ** 2 / 4 * fd)

def optimise(kind, f0):
    fd = f0 / 1.1; eps = math.sqrt(250 / f0); best = None; rows = []
    for D in np.arange(55, 101, 5):
        for tf in np.arange(4, 12.01, 0.5):
            for tw in np.arange(2.5, 6.01, 0.5):
                A, W, Wa, I = (box if kind == "box" else ibeam)(D, tf, tw)
                u = M_ED / (W * fd); ua = M_ALONG / (Wa * fd); F = M_ED / S_CROSS
                clear = 25 - 2 * tw if kind == "box" else (25 - tw) / 2 * 2
                ub = face_bearing_util(tf, clear, fd, F) if kind == "box" else (F / 2 * ((25 - tw) / 4)) / (6 + (25 - tw)) / (tf ** 2 / 4 * fd)
                # class: box flange internal (uniform compression) b/t; box web internal bending eta 0.4; I flange outstand
                if kind == "box":
                    cls_ok = (25 - 2 * tw) / tf <= 22 * eps and 0.4 * (D - 2 * tf) / tw <= 22 * eps
                else:
                    cls_ok = ((25 - tw) / 2) / tf <= 6 * eps and 0.4 * (D - 2 * tf) / tw <= 22 * eps
                if u <= U_T and ua <= 1.0 and ub <= 1.0 and cls_ok:
                    m12 = 12 * A * L_POLE * RHO; pen = RAIL_KG_PER_MM * (D - 55)
                    r = dict(D=float(D), tf=float(tf), tw=float(tw), A=A, W=W, W_along=Wa, util=u, util_view_5kNm=M_VIEW / (W * fd), util_along=ua,
                             util_face=ub, mass12=m12, rail_penalty=pen, total=m12 + pen,
                             tip_defl_sls_3kNm_mm=(3.0 * 250 / math.cos(math.radians(35))) * ARM ** 3 / (3 * 70000 * I))
                    rows.append(r)
                    if best is None or r["total"] < best["total"]: best = r
    return best, sorted(rows, key=lambda r: r["total"])[:5]

def solid_taper(f0, D0=None, taper_between_rails=False, dmin=17.0, top=(60.0, 30.0), tongue=(40.0, 35.0)):
    fd = f0 / 1.1
    D0_req = math.sqrt(6 * M_ED / (U_T * fd) / 25)
    D0 = D0 or math.ceil(D0_req)
    hs = np.linspace(0, ARM, 2001); D = np.maximum(dmin, D0 * np.sqrt(np.clip(1 - hs / ARM, 0, 1)))
    D[hs >= ARM - top[0]] = np.maximum(D[hs >= ARM - top[0]], top[1])
    cant = np.trapezoid(D, hs)
    if taper_between_rails:     # M falls linearly to 0 at the lower crossing; keep >= 35 for the lower slot / latch
        zs = np.linspace(0, S_CROSS, 401); Dz = np.maximum(35.0, D0 * np.sqrt(1 - zs / S_CROSS)); rail = np.trapezoid(Dz, zs)
    else:
        rail = D0 * S_CROSS
    A_prof = cant + rail + tongue[0] * tongue[1]
    m = 25 * A_prof * RHO
    I0 = 25 * D0 ** 3 / 12
    return dict(f0=f0, D0=D0, D0_req_at_0p90=D0_req, util=M_ED / (25 * D0 ** 2 / 6 * fd), util_view_5kNm=M_VIEW / (25 * D0 ** 2 / 6 * fd),
                util_along=M_ALONG / (D0 * 25 ** 2 / 6 * fd), mass_each=m, mass12=12 * m, rail_penalty=RAIL_KG_PER_MM * (D0 - 55),
                total=12 * m + RAIL_KG_PER_MM * (D0 - 55))

def castellated(f0, D0=60.0, c_min=10.0, post=25.0, pitch=100.0):
    """waterjet plate pole with a row of NA slots: two chords 25 x c + posts 25 wide at `pitch`; chords sized for
    axial = M/(25 c (D-c)) plus Vierendeel V/2 x (pitch-post)/2 on 25 c^2/6; depth follows sqrt taper from D0; solid
    where the slot would be < 25 tall. ESTIMATE (no FE of the posts/corners)."""
    fd = f0 / 1.1 * U_T; V = GAM * P_GOV; hs = np.linspace(0, ARM, 1201); A = []
    for h in hs:
        M = GAM * P_GOV * (ARM - h); D = max(17.0, D0 * math.sqrt(max(0.0, 1 - h / ARM)))
        if h >= ARM - 60: D = max(D, 30.0)
        As = 25 * D; best = As
        for c in np.arange(c_min, D / 2, 0.5):
            hole = D - 2 * c
            if hole < 25: break
            s = M / (25 * c * (D - c)) + (V / 2 * (pitch - post) / 2) / (25 * c * c / 6)
            if s <= fd:
                best = min(best, 2 * 25 * c + 25 * hole * post / pitch); break
        A.append(best)
    cant = np.trapezoid(A, hs); rail = 25 * D0 * S_CROSS; tongue = 25 * 35 * 40
    m = (cant + rail + tongue) * RHO
    return dict(f0=f0, D0=D0, mass_each=m, mass12=12 * m, rail_penalty=RAIL_KG_PER_MM * (D0 - 55), total=12 * m + RAIL_KG_PER_MM * (D0 - 55))

out = dict(basis=dict(M_Ed_Nmm=M_ED, P_gov_N=P_GOV, loads_N=P, M_view_5kNm_Nmm=M_VIEW, M_along_Nmm=M_ALONG, arm=ARM, L_pole=L_POLE,
                      util_target=U_T, rail_kg_per_mm_depth=RAIL_KG_PER_MM))
out["solid_RevC_reviewed_25x55_6082plate"] = solid_taper(240.0, D0=55)
out["solid_25xD_6082plate_u0.90"] = solid_taper(240.0)
out["solid_25xD_6082plate_u0.90_taper_between_rails"] = solid_taper(240.0, taper_between_rails=True)
out["solid_25xD_7020plate_u0.90_taper_between_rails"] = solid_taper(280.0, taper_between_rails=True)
out["castellated_plate_6082_D60"] = castellated(240.0, 60.0)
out["castellated_plate_6082_D70"] = castellated(240.0, 70.0)
for kind in ("box", "I"):
    for mn, f0 in (("6082-T6 extrusion (t<=5)", 250.0), ("6005A-T6 extrusion (t<=5)", 225.0), ("7020-T6 extrusion", 290.0)):
        b, top5 = optimise(kind, f0)
        out[f"{kind} custom extrusion {mn}"] = dict(best=b, next=top5[1:])
# stock RHS for reference (slot 50+ along the rail -> rails need 10 mm ligaments + thicker legs; poles_barrier C2)
for name, (bx, h, t) in {"stock RHS 80 across x 40 along x 3": (40, 80, 3), "stock RHS 60 across x 40 along x 4": (40, 60, 4)}.items():
    A = bx * h - (bx - 2 * t) * (h - 2 * t); I = (bx * h ** 3 - (bx - 2 * t) * (h - 2 * t) ** 3) / 12
    out[name] = dict(util=M_ED / (I / (h / 2) * 250 / 1.1), mass12=12 * A * L_POLE * RHO, rail_penalty=RAIL_KG_PER_MM * (h - 55),
                     note="slot along the rail (bx+1)/cos35 >= 50 -> Vierendeel 0.78-0.89 at 8 mm ligaments (poles_barrier C2); +legs")
json.dump(out, open(os.path.join(HERE, "pole_opt.json"), "w"), indent=1)
for k, v in out.items():
    if k == "basis": print(k, {a: (round(b) if isinstance(b, float) else b) for a, b in v.items() if a != "loads_N"}); continue
    b = v.get("best", v)
    print(f"{k:<52} " + "  ".join(f"{a}={b[a]:.3g}" for a in ("D", "tf", "tw", "D0", "util", "util_view_5kNm", "util_along", "util_face", "mass12", "rail_penalty", "total", "tip_defl_sls_3kNm_mm") if a in b))
