"""Owner's idea: a cross-lattice grating cut from one plate (bars both ways, 25 deep, one piece) in the existing J + L
frame, same outer size. Modelled on the validated final-tread FE (tread_fe2.py): the longitudinal lattice bars are shells
(like the flats) at chosen x positions, joined to the end plates; the transverse bars stay as before (3 x 25 at 20 mm).
Cut from one piece = rigid joints at every crossing (shared nodes)."""
import json, sys
import tread_fe2 as TF
Q, P4, PERSON, GG, GQ, YMID = 7.5e-3, 4000.0, 1000.0, 1.35, 1.5, 618.0      # same as tread2_cases.py (not imported: it runs on import)
def scaled(f, k): return lambda yb, x0, x1: k * (f(yb, x0, x1) or 0.0)
PY_CASES = {"SLS crowd 7.5 kN/m2": (TF.udl(Q), 1.0), "ULS crowd": (scaled(TF.udl(Q), GQ), GG),
            "SLS person 1 kN at nosing (100x100)": (TF.patch(PERSON, 225.0, YMID, 100.0, 100.0), 1.0),
            "SLS 4 kN patch front, mid-span": (TF.patch(P4, 175.0, YMID), 1.0), "ULS 4 kN patch front, mid-span": (TF.patch(GQ * P4, 175.0, YMID), GG),
            "ULS 4 kN patch centre, mid-span": (TF.patch(GQ * P4, 140.0, YMID), GG), "ULS 4 kN patch front, at left end": (TF.patch(GQ * P4, 175.0, 125.0), GG)}
FD = 250 / 1.1
import os
VARIANTS_ALL = {
    "L20 lattice 20 x 20 (13 long bars 3 x 25)": [20.0 + 20.0 * k for k in range(13)],
    "L40 lattice 20 x 40 (7 long bars 3 x 25)": [25.0 + 40.0 * k for k in range(7)],
    "L10 lattice 20 x 10 (24 long bars 3 x 25)": [15.0 + 10.0 * k for k in range(24)],
}
ONLY = [x for x in os.environ.get("ONLY", "").split("|") if x]
VARIANTS = {k: v for k, v in VARIANTS_ALL.items() if not ONLY or k in ONLY}
if __name__ == "__main__":
    out = json.load(open("tread_lattice.json")) if os.path.exists("tread_lattice.json") else {}
    for name, xs in VARIANTS.items():
        TF.FLAT_X = tuple(round(x, 4) for x in xs); TF.FLAT_T = 3.0; TF.FLATS_JOINED = True
        rr = {}
        for cn in ("ULS 4 kN patch front, mid-span", "ULS 4 kN patch centre, mid-span", "ULS 4 kN patch front, at left end", "ULS crowd",
                   "SLS 4 kN patch front, mid-span", "SLS crowd 7.5 kN/m2", "SLS person 1 kN at nosing (100x100)"):
            fn, swf = PY_CASES[cn]
            r = TF.solve(fn, sw_factor=swf, label=cn); vb = r["vm_max_body"]
            rr[cn] = dict(lip=r["uz_mid_lip_top"], uz_min=r["uz_min"], twist=r["twist_mid_deg"], vm=vb[0], where=vb[7:11], bar=r["bar_max"][0],
                          flat=r["vm_by_part"].get("flat", [0])[0], eq=r["equilibrium"])
            print(f"{name[:30]:<30} {cn:<36} lip {r['uz_mid_lip_top']:7.2f} min {r['uz_min']:7.2f} twist {r['twist_mid_deg']:5.2f} vm {vb[0]:6.1f} ({vb[7]}) "
                  f"u {vb[0] / FD:.2f} | cross bars {r['bar_max'][0]:.0f} | long bars {rr[cn]['flat']:.0f} | eq {r['equilibrium']['Fz_support']:.0f}/{r['equilibrium']['Fz_load']:.0f}", flush=True)
        out[name] = dict(x=xs, cases=rr, mass_extra_kg=len(xs) * 3 * 25 * 1195 * 2.7e-6)
        json.dump(out, open("tread_lattice.json", "w"), indent=1, default=str)
