"""Edge distance (EN 1999-1-1 T8.8: a >= F gMp/(2 t f0) + 2 d0/3, a = hole edge to free edge) at the Lo_R leg holes
(O10 hole, centre 12.5 above the free edge -> a = 7.5 mm), with the frame link force added to the tread reaction."""
import math, json
import numpy as np
import side_frame as SF, run_side_frame as R
SF.VERTICAL_AT_UPPER = True
G = SF.G["R"]["rail_lo"]; a, b = np.array(G["a"]), np.array(G["b"]); u = (b - a) / np.linalg.norm(b - a)
n = np.array([u[1], -u[0]]); n_down = n if n[1] < 0 else -n
e = np.array([200.0, 25.0]); e /= np.linalg.norm(e)          # rear pin -> front pin
C = json.load(open("tread2_cases.json"))
fz_rear = C["ULS crowd"]["pins"]["R_rear"][2]                  # tread vertical reaction at the right rear pin, ULS crowd
worst = []
for slide in (False, True):
    for only in (None, {0, 1, 2}, {3, 4, 5}):
        out = SF.run("R", R.pf("ULS crowd", "R", only), bracket_rigid=True, base_slides=slide)
        for k, N in out["links"].items():
            i = int(k.replace("tread", ""))
            fz = fz_rear if (only is None or i in only) else 0.0
            F = N * e + np.array([0.0, -fz])
            worst.append((float(F @ n_down), slide, sorted(only) if only else "all", i, round(N)))
worst.sort(reverse=True)
for Fp, slide, only, i, N in worst[:6]:
    a_req = max(Fp, 0) * 1.25 / (2 * 5 * 250) + 20 / 3
    print(f"tread {i} loaded {only} slide={slide}: link {N} N, F toward edge {Fp:.0f} N -> a_req {a_req:.2f} vs 7.5 mm, util {a_req / 7.5:.2f}")
json.dump([dict(F_perp=w[0], slide=w[1], loaded=w[2], tread=w[3], link=w[4]) for w in worst[:6]], open("lo_r_edge_check.json", "w"), indent=1)
