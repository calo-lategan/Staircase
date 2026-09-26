"""Plot thickness maps (colour = material thickness through the part along the view axis), with window option."""
import json, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
Z = np.load(sys.argv[1]); M = json.load(open(sys.argv[1].replace(".npz", ".json")))
mid, out = sys.argv[2], sys.argv[3]
win = [float(x) for x in sys.argv[4:8]] if len(sys.argv) > 7 else None
m = M[mid]; TH = Z[mid + "__TH"]
nv, nu = TH.shape
ext = [m["u0"], m["u0"] + nu * m["du"], m["v0"], m["v0"] + nv * m["dv"]]
if win:
    i0 = max(0, int((win[0] - m["u0"]) / m["du"])); i1 = min(nu, int((win[1] - m["u0"]) / m["du"]))
    j0 = max(0, int((win[2] - m["v0"]) / m["dv"])); j1 = min(nv, int((win[3] - m["v0"]) / m["dv"]))
    TH = TH[j0:j1, i0:i1]; ext = [m["u0"] + i0 * m["du"], m["u0"] + i1 * m["du"], m["v0"] + j0 * m["dv"], m["v0"] + j1 * m["dv"]]
w = ext[1] - ext[0]; h = ext[3] - ext[2]
fig, ax = plt.subplots(figsize=(min(24, max(8, 0.06 * w + 2)), min(14, max(3, 0.06 * h * (min(24, max(8, 0.06 * w + 2)) / max(1e-9, 0.06 * w + 2)) + 1.5))), dpi=110)
vals = sorted(set(np.round(TH[TH > 0], 1).tolist()))
im = ax.imshow(TH, origin="lower", extent=ext, cmap="viridis", interpolation="nearest", aspect="equal")
cb = fig.colorbar(im, ax=ax, fraction=0.02); cb.set_label(f"thickness along {m['ax']} (mm)")
ax.set_xlabel(f"{m['u']} (mm, world)"); ax.set_ylabel(f"{m['v']} (mm, world)"); ax.set_title(f"{mid}  objects={','.join(m['objects'])}")
ax.minorticks_on(); ax.grid(True, lw=0.3, color="w", alpha=0.4)
fig.tight_layout(); fig.savefig(out); print("saved", out, "distinct thickness values (top 12 by area):")
u, c = np.unique(np.round(TH[TH > 0], 1), return_counts=True)
print(sorted(zip(c, u), reverse=True)[:12])
