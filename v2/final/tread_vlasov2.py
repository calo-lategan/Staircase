"""Method 2 (analytical, independent of the FE): the final tread as a thin-walled section made of DISCONNECTED branches
(back J, front L, two flats) held in a common rigid cross-section shape by the grating bars (no longitudinal shear
connection between branches, the grating has no deck). Kinematics per section: vertical w, lateral u, twist phi about
the y axis (point (x,z) moves dx = phi*z, dz = -phi*x). Each branch bends about its own centroid:
  w_i = w - phi*x_i ,  u_i = u + phi*z_i
  U = 1/2 E sum_i [Ix_i w_i''^2 + Iz_i u_i''^2 + 2 Ixz_i w_i'' u_i''] + 1/2 G J phi'^2   (J = sum of St Venant)
Simply supported / fork ends at the pins (w = u = phi = 0, free warping): exact sine-series solution, mode by mode."""
import math, json
import numpy as np
from section_tools import section

E, NU = 70000.0, 0.3
G = E / (2 * (1 + NU))
RHO_W = 2.70e-9 * 9810.0
L = 1226.5 - 10.75           # pin bearing to pin bearing

def branch(poly, Jt):
    s = section([poly])
    return dict(A=s["A"], x=s["cx"], z=s["cy"], Ix=s["Ix"], Iz=s["Iy"], Ixz=s["Ixy"], J=Jt)

BR = {
    "J": branch([(0, 0), (50, 0), (50, 17.5), (45, 17.5), (45, 5), (5, 5), (5, 50), (0, 50)], (50 + 45 + 12.5) * 125 / 3),
    "L": branch([(275, 25), (280, 25), (280, 50), (275, 50), (275, 30), (252.5, 30), (252.5, 25)], (25 + 22.5) * 125 / 3),
    "F1": branch([(82.3, 25), (85.0, 25), (85.0, 50), (82.3, 50)], 25 * 2.7 ** 3 / 3 * (1 - 0.63 * 2.7 / 25)),
    "F2": branch([(189.45, 25), (192.15, 25), (192.15, 50), (189.45, 50)], 25 * 2.7 ** 3 / 3 * (1 - 0.63 * 2.7 / 25)),
}
BAR_A = 75.0
J_tot = sum(b["J"] for b in BR.values())


def solve(loads, nmodes=199):
    """loads: list of (y0, y1, p N/mm downward, x_q) line loads along the span (y measured from the left bearing).
    returns function giving (w, u, phi) at y and the arrays."""
    K = np.zeros((3, 3)); coef = []
    for n in range(1, nmodes + 1, 1):
        lam = n * math.pi / L
        # stiffness per mode (energy * 2 / (L/2)): generalised coordinates (a, b, c) for w, u, phi amplitudes
        K = np.zeros((3, 3))
        for b in BR.values():
            # w_i'' = -(a - c x_i) lam^2 sin ; u_i'' = -(b + c z_i) lam^2 sin
            vw = np.array([1.0, 0.0, -b["x"]]); vu = np.array([0.0, 1.0, b["z"]])
            K += E * lam ** 4 * (b["Ix"] * np.outer(vw, vw) + b["Iz"] * np.outer(vu, vu) + b["Ixz"] * (np.outer(vw, vu) + np.outer(vu, vw)))
        K[2, 2] += G * J_tot * lam ** 2
        K *= L / 2
        F = np.zeros(3)
        for (y0, y1, p, xq) in loads:
            # int p sin(lam y) dy over [y0, y1]  (downward p does work -p*dz, dz = w - phi*xq)
            s = (math.cos(lam * y0) - math.cos(lam * y1)) / lam
            F += np.array([-p * s, 0.0, p * xq * s])
        coef.append(np.linalg.solve(K, F))
    coef = np.array(coef)
    def at(y):
        s = np.array([math.sin((n + 1) * math.pi * y / L) for n in range(len(coef))])
        return coef.T @ s
    return at


if __name__ == "__main__":
    for k, b in BR.items():
        print(f"{k:<3} A={b['A']:7.1f} centroid=({b['x']:7.2f},{b['z']:6.2f}) Ix={b['Ix']:9.0f} Iz={b['Iz']:9.0f} Ixz={b['Ixz']:9.0f} J={b['J']:6.0f}")
    q = 7.5e-3
    # crowd on the bars: p per mm along y = q * 250 (going), distributed across x 2.5..277.5 -> resultant at x = 140; bars' length along y 15..1216
    ybar0, ybar1 = 15.0 - 10.75, 1215.0 - 10.75
    loads = [(ybar0, ybar1, q * 250.0, 140.0)]
    # self weight of branches and bars (vertical, at their centroids)
    loads += [(ybar0, ybar1, RHO_W * b["A"], b["x"]) for b in BR.values()]
    loads += [(ybar0, ybar1, RHO_W * BAR_A * 275 / 20, 140.0)]
    at = solve(loads)
    w, u, phi = at(L / 2)
    print(f"\nSLS crowd, mid-span: w={w:.3f}  u={u:.3f}  phi={math.degrees(phi):.3f} deg")
    for nm, x, z in (("lip top", 277.5, 50), ("rear wall top", 2.5, 50), ("flat1 top", 83.65, 50), ("flat2 top", 190.8, 50)):
        print(f"   {nm:<14} vertical {w - phi * x:8.3f}  lateral {u + phi * z:7.3f}")
    print("FE (shell/beam bars):  lip top -17.96 (lat 1.05)  rear wall top -4.74 (lat 1.06)  flat1 -8.66  flat2 -13.82")
