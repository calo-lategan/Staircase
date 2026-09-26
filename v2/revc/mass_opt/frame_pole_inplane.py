"""Mass study (26 Sep 2026): in-plane (side-frame) forces in the barrier poles for the INSIDE-RAIL scheme, so that a lighter
pole section (I / box) is not chosen on the barrier check alone. Same model and loads as v2/final/side_frame.py and
v2/revc/frame_after.py (ULS crowd, tread-FE pin forces); changes vs frame_after:
  * VERTICAL_AT_UPPER both False (poles_barrier.md C3: vertical lock only at the lower rail) and True (lock at both rails,
    as final/component_checks_final.py and frame_sls_final.py actually ran it; the 5.9 kN latch force comes from True)
  * rails 70 deep, widened webs per poles_barrier.md C3 (right inv. U 82, left U 94 outside, 5 mm walls)
  * pole in-plane section varied: solid 25 x 55 (Rev C) vs custom I / box sections (25 along the stair).
Reports max in-plane pole moment and the slot/latch forces. Output: mass_opt/frame_pole_inplane.json
Does not modify any repo file (imports side_frame from v2/final, patches module globals in memory only)."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); FIN = os.path.join(HERE, "..", "..", "final")
sys.path.insert(0, FIN); os.chdir(FIN)
import side_frame as SF

for key, W, web_top in (("Lo_L", 94, False), ("Up_L", 94, False), ("Lo_R", 82, True), ("Up_R", 82, True)):
    A, I, _ = SF.usec(W, 70, 5, web_top); SF.SEC[key] = dict(A=A, I=I)
C = json.load(open("tread2_cases.json"))
U = C["ULS crowd"]["pins"]

def forces(side):
    return {i: {k: (-U[f"{side}_{k}"][0], -U[f"{side}_{k}"][2]) for k in ("rear", "front")} for i in range(6)}

POLES = {  # in-plane: bending about the across-stair axis -> the 25 mm (along-stair) dimension is the depth
    "solid 25x55 (Rev C)": dict(A=25 * 55, I=55 * 25 ** 3 / 12, W=55 * 25 ** 2 / 6),
    "I 25x75 tf6 tw4": dict(A=2 * 25 * 6 + 4 * 63, I=2 * 6 * 25 ** 3 / 12 + 63 * 4 ** 3 / 12, W=(2 * 6 * 25 ** 3 / 12 + 63 * 4 ** 3 / 12) / 12.5),
    "box 25x70 tf6 tw3": dict(A=25 * 70 - 19 * 58, I=(70 * 25 ** 3 - 58 * 19 ** 3) / 12, W=(70 * 25 ** 3 - 58 * 19 ** 3) / 12 / 12.5),
}
out = {"note": "ULS crowd, in-plane pole moments (N mm), slot H forces (N)", "cases": {}}
for pname, sec in POLES.items():
    for side in ("L", "R"):
        SF.SEC["pole_" + side] = dict(A=sec["A"], I=sec["I"])
    for vu in (False, True):
      SF.VERTICAL_AT_UPPER = vu
      for slide in (False, True):
        for side in ("L", "R"):
            r = SF.run(side, forces(side), factor_sw=1.35, base_slides=slide)
            Mmax = max(max(abs(p[4]), abs(p[5])) for p in r["pole_forces"])
            Nmax = max(abs(p[2]) for p in r["pole_forces"])
            key = f"{pname} | vert.lock {'both rails' if vu else 'lower only'} | {side} {'base slides' if slide else 'base pinned'}"
            out["cases"][key] = dict(M_inplane_max_Nmm=Mmax, N_max=Nmax, sigma_MPa=Mmax / sec["W"], util_inplane_alone=Mmax / sec["W"] / (250 / 1.1),
                                     uz_max_ULS_mm=r["disp_max"][0])
            print(f"{key:<48} M_in {Mmax/1e3:7.1f} kNmm  N {Nmax/1e3:5.2f} kN  sigma {Mmax/sec['W']:6.1f} MPa  util {Mmax/sec['W']/227.3:4.2f}  uz {r['disp_max'][0]:7.1f} mm")
json.dump(out, open(os.path.join(HERE, "frame_pole_inplane.json"), "w"), indent=1)
