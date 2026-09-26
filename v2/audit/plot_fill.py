"""Filled (even-odd) plot of one object's cuts; grid of panels. python plot_fill.py cuts.json obj out.png u v u0 v0 id1 id2 ..."""
import json, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from section_tools import loops_from_segments
C = json.load(open(sys.argv[1])); obj = sys.argv[2]; out = sys.argv[3]
IX = {"x": 0, "y": 1, "z": 2}; u, v = IX[sys.argv[4]], IX[sys.argv[5]]; u0, v0 = float(sys.argv[6]), float(sys.argv[7])
ids = sys.argv[8:]
n = len(ids); cols = min(3, n); rows = (n + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(7 * cols, 3.2 * rows), dpi=100, squeeze=False)
for k, cid in enumerate(ids):
    ax = axs[k // cols][k % cols]
    segs = C[cid].get(obj, [])
    S = [(((a[u] - u0) * 1000, (a[v] - v0) * 1000), ((b[u] - u0) * 1000, (b[v] - v0) * 1000)) for a, b in segs]
    L = loops_from_segments(S, 1e-4)
    verts, codes = [], []
    for l in L:
        verts += l + [l[0]]; codes += [Path.MOVETO] + [Path.LINETO] * (len(l) - 1) + [Path.CLOSEPOLY]
    if verts:
        ax.add_patch(PathPatch(Path(verts, codes), facecolor="#9ab", edgecolor="k", lw=0.6))
        xs = [p[0] for p in verts]; ys = [p[1] for p in verts]
        ax.set_xlim(min(xs) - 3, max(xs) + 3); ax.set_ylim(min(ys) - 3, max(ys) + 3)
    ax.set_aspect("equal"); ax.grid(True, lw=0.3); ax.minorticks_on(); ax.grid(True, which="minor", lw=0.1)
    ax.set_title(cid, fontsize=9)
fig.tight_layout(); fig.savefig(out); print("saved", out)
