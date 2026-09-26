"""Frame SLS deflection (crowd, G + Q) and first vertical frequency estimate f1 = 17.75/sqrt(d[G+0.3Q] mm) per side and base
condition, from the tread-FE pin forces split into G and Q (tread2_cases.json: SLS = G + Q, ULS = 1.35 G + 1.5 Q)."""
import json, math
import numpy as np
import side_frame as SF
SF.VERTICAL_AT_UPPER = True
C = json.load(open("tread2_cases.json"))
S, U = C["SLS crowd 7.5 kN/m2"]["pins"], C["ULS crowd"]["pins"]
def parts(side):
    out = {}
    for k in ("rear", "front"):
        s, u = np.array(S[f"{side}_{k}"]), np.array(U[f"{side}_{k}"])
        g = (1.5 * s - u) / 0.15; q = s - g
        out[k] = (g, q)
    return out
res = {}
for slide in (False, True):
    for side in ("L", "R"):
        pr = parts(side)
        def forces(fg, fq):
            return {i: {k: (-(fg * pr[k][0] + fq * pr[k][1])[0], -(fg * pr[k][0] + fq * pr[k][1])[2]) for k in ("rear", "front")} for i in range(6)}
        d_sls = SF.run(side, forces(1.0, 1.0), factor_sw=1.0, base_slides=slide)["disp_max"][0]
        d_f = SF.run(side, forces(1.0, 0.3), factor_sw=1.0, base_slides=slide)["disp_max"][0]
        f1 = 17.75 / math.sqrt(max(d_f, 1e-6))
        key = f"{side} {'base slides' if slide else 'base pinned'}"
        res[key] = dict(defl_sls=d_sls, defl_G03Q=d_f, f1=f1)
        print(f"{key:<16} SLS {d_sls:6.2f} mm (L/250 = {1831/250:.2f}) | G+0.3Q {d_f:5.2f} mm -> f1 ~ {f1:5.2f} Hz")
json.dump(res, open("frame_sls_final.json", "w"), indent=1)
