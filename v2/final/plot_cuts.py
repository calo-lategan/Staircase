"""Plot plane cuts: python plot_cuts.py cuts.json out.png id u_axis v_axis umin umax vmin vmax [label objs]"""
import json, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
cuts = json.load(open(sys.argv[1])); out = sys.argv[2]; cid = sys.argv[3]
IX = {"x": 0, "y": 1, "z": 2}
u, v = IX[sys.argv[4]], IX[sys.argv[5]]
umin, umax, vmin, vmax = [float(a) for a in sys.argv[6:10]]
res = cuts[cid]
w = (umax - umin); h = (vmax - vmin)
fig, ax = plt.subplots(figsize=(min(26, max(6, 16 * w / max(w, h))), min(26, max(4, 16 * h / max(w, h)))), dpi=110)
cols = plt.cm.tab20.colors
for k, (name, segs) in enumerate(sorted(res.items())):
    L = [[((a[u] - umin) * 1000, (a[v] - vmin) * 1000), ((b[u] - umin) * 1000, (b[v] - vmin) * 1000)] for a, b in segs]
    L = [s for s in L if min(s[0][0], s[1][0]) < w * 1000 + 5 and max(s[0][0], s[1][0]) > -5]
    if not L:
        continue
    ax.add_collection(LineCollection(L, colors=[cols[k % 20]], linewidths=1.0))
    xs = [p[0] for s in L for p in s]; ys = [p[1] for s in L for p in s]
    cx = min(max(sum(xs) / len(xs), 0), w * 1000); cy = min(max(sum(ys) / len(ys), 0), h * 1000)
    ax.text(cx, cy, name.replace("MainRig_", "M"), fontsize=6, color=cols[k % 20])
ax.set_xlim(0, w * 1000); ax.set_ylim(0, h * 1000); ax.set_aspect("equal")
ax.set_xlabel(f"{'xyz'[u]} - {umin} (mm)"); ax.set_ylabel(f"{'xyz'[v]} - {vmin} (mm)")
ax.grid(True, lw=0.3); ax.minorticks_on(); ax.grid(True, which="minor", lw=0.1)
ax.set_title(f"{cid}")
fig.tight_layout(); fig.savefig(out); print("saved", out)
