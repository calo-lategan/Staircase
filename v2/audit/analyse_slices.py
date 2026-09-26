import json, sys, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from section_tools import loops_from_segments, section
src, png = sys.argv[1], sys.argv[2]
D = json.load(open(src))
plane = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}
out = {}
n = sum(len(v["cuts"]) for v in D.values())
cols = 4; rows = (n + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
axs = axs.flatten() if n > 1 else [axs]
k = 0
for key, v in D.items():
    i, j = plane[v["axis"]]
    for st, c in v["cuts"].items():
        segs = [[(p[i] * 1000, p[j] * 1000) for p in s] for s in c["segs"]]
        ax = axs[k]; k += 1
        for s in segs:
            ax.plot([s[0][0], s[1][0]], [s[0][1], s[1][1]], "k-", lw=0.7)
        loops = loops_from_segments(segs, tol=1e-3)
        try:
            S = section(loops)
            out[f"{key}@{st}"] = {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in S.items()}
            ax.plot(S["cx"], S["cy"], "r+")
            ax.set_title(f"{key} @{st}  A={S['A']:.0f} Ix={S['Ix']:.0f}\nw={S['w']:.1f} h={S['h']:.1f} ctop={S['c_top']:.1f} cbot={S['c_bot']:.1f} loops={len(loops)}", fontsize=8)
        except Exception as ex:
            ax.set_title(f"{key} @{st} ERR {ex}", fontsize=8)
        ax.set_aspect("equal"); ax.grid(alpha=.3)
        if segs:
            xs=[q[0] for s in segs for q in s]; ys=[q[1] for s in segs for q in s]
            ax.set_xlim(min(xs)-5, max(xs)+5); ax.set_ylim(min(ys)-5, max(ys)+5)
for a in axs[k:]:
    a.axis("off")
plt.tight_layout(); plt.savefig(png, dpi=70)
json.dump(out, open(src.replace(".json", "_props.json"), "w"), indent=1)
for kk, vv in out.items():
    print(kk, {x: vv[x] for x in ("A", "Ix", "Iy", "w", "h", "c_top", "c_bot")}, "loops", [(l["n"], round(l["area"]), l["hole"]) for l in vv["loops"]])
