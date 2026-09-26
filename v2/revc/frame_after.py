"""Rev C: side-frame SLS sag and first vertical frequency AFTER the Rev C changes (rails about 70 deep, same widths, 5 mm walls).
Same model and loads as final/frame_sls_final.py (tread-FE pin forces, OpenSees 2D frame); only the rail sections change.
Poles keep 25 along the stair (in-plane), so their in-plane stiffness is unchanged. Output: revc/frame_after.json"""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); FIN = os.path.join(HERE, "..", "final")
sys.path.insert(0, FIN); os.chdir(FIN)
import side_frame as SF
SF.VERTICAL_AT_UPPER = True
DEPTH = 70
for key, W, web_top in (("Lo_L", 35, False), ("Up_L", 35, False), ("Lo_R", 25, True), ("Up_R", 25, True)):
    A, I, _ = SF.usec(W, DEPTH, 5, web_top); SF.SEC[key] = dict(A=A, I=I)
C = json.load(open("tread2_cases.json"))
S, U = C["SLS crowd 7.5 kN/m2"]["pins"], C["ULS crowd"]["pins"]
def parts(side):
    out = {}
    for k in ("rear", "front"):
        s, u = np.array(S[f"{side}_{k}"]), np.array(U[f"{side}_{k}"]); g = (1.5 * s - u) / 0.15; out[k] = (g, s - g)
    return out
res = {"sections": {k: SF.SEC[k] for k in ("Lo_L", "Up_L", "Lo_R", "Up_R")}, "limit_mm": 1831 / 250}
for slide in (False, True):
    for side in ("L", "R"):
        pr = parts(side)
        forces = lambda fg, fq: {i: {k: (-(fg * pr[k][0] + fq * pr[k][1])[0], -(fg * pr[k][0] + fq * pr[k][1])[2]) for k in ("rear", "front")} for i in range(6)}
        d = SF.run(side, forces(1.0, 1.0), factor_sw=1.0, base_slides=slide)["disp_max"][0]
        df = SF.run(side, forces(1.0, 0.3), factor_sw=1.0, base_slides=slide)["disp_max"][0]
        key = f"{side} {'base slides' if slide else 'base pinned'}"
        res[key] = dict(defl_sls=d, util=d / (1831 / 250), f1=17.75 / math.sqrt(max(df, 1e-6)))
        print(f"{key:<16} SLS {d:6.2f} mm  util {d / 7.324:4.2f}  f1 ~ {res[key]['f1']:5.1f} Hz")
json.dump(res, open(os.path.join(HERE, "frame_after.json"), "w"), indent=1)
