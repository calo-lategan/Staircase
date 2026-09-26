"""Method 2 (independent of OpenSees): plane grillage of the final tread, own numpy direct-stiffness code, 3 DOF per node
(w vertical, rx about x, ry about y). Longitudinal members along y: back J, flat 1, flat 2, front L (own section
properties, exact polygons); 60 transverse bars 3 x 25 along x; end plates = stiff transverse beams at y = 17.5 / 1218.5
joining J and L (the flats stop short of the end plates). Supports at the pins: rear (x 25, J) and front (x 225, end
plate band) at y = 10.5 / 1225.5 via the pin stubs (stiff). Loads applied as nodal forces on the bars."""
import math, json
import numpy as np
from section_tools import section

E, NU = 70000.0, 0.3
G = E / (2 * (1 + NU))
RHO_W = 2.70e-9 * 9810.0

def props(poly):
    s = section([poly]); return s

J_POLY = [(0, 0), (50, 0), (50, 17.5), (45, 17.5), (45, 5), (5, 5), (5, 50), (0, 50)]
L_POLY = [(275, 25), (280, 25), (280, 50), (275, 50), (275, 30), (252.5, 30), (252.5, 25)]
Jp, Lp = props(J_POLY), props(L_POLY)
J_tJ = (50 + 45 + 12.5) * 5 ** 3 / 3        # open-section torsion (centre-line lengths)
L_tJ = (25 + 22.5) * 5 ** 3 / 3
FLAT = dict(I=2.7 * 25 ** 3 / 12, J=25 * 2.7 ** 3 / 3 * (1 - 0.63 * 2.7 / 25), A=2.7 * 25)
BAR = dict(I=3 * 25 ** 3 / 12, J=25 * 27 / 3 * (1 - 0.63 * 3 / 25), A=75.0)
XJ, XF1, XF2, XL = Jp["cx"], 83.65, 190.8, Lp["cx"]
BAR_Y = [25.0 + 20.0 * k for k in range(60)]


class Grillage:
    def __init__(self):
        self.X, self.els, self.fix = [], [], {}
    def node(self, x, y):
        for i, (a, b) in enumerate(self.X):
            if abs(a - x) < 1e-6 and abs(b - y) < 1e-6: return i
        self.X.append((x, y)); return len(self.X) - 1
    def el(self, i, j, EI, GJ, rel_i=False, rel_j=False):
        self.els.append((i, j, EI, GJ, rel_i, rel_j))
    def solve(self, F):
        n = len(self.X); K = np.zeros((3 * n, 3 * n))
        for i, j, EI, GJ, rel_i, rel_j in self.els:
            (x1, y1), (x2, y2) = self.X[i], self.X[j]
            L = math.hypot(x2 - x1, y2 - y1); c, s = (x2 - x1) / L, (y2 - y1) / L
            k = np.zeros((6, 6))                      # local DOF: w, torsion (about member axis), bending rotation
            a = 12 * EI / L ** 3; b = 6 * EI / L ** 2; d4 = 4 * EI / L; d2 = 2 * EI / L; t = GJ / L
            idx = [0, 1, 2, 3, 4, 5]
            k[np.ix_([0, 2, 3, 5], [0, 2, 3, 5])] = [[a, b, -a, b], [b, d4, -b, d2], [-a, -b, a, -b], [b, d2, -b, d4]]
            k[1, 1] = k[4, 4] = t; k[1, 4] = k[4, 1] = -t
            # rotation: local torsion axis along the member (c,s), bending rotation about the perpendicular (-s,c)
            T = np.zeros((6, 6))
            for o in (0, 3):
                T[o, o] = 1
                T[o + 1, o + 1], T[o + 1, o + 2] = c, s          # torsion = rx*c + ry*s
                T[o + 2, o + 1], T[o + 2, o + 2] = -s, c         # bending rotation = -rx*s + ry*c
            rel = ([1, 2] if rel_i else []) + ([4, 5] if rel_j else [])   # release torsion + bending rotation at the end(s)
            if rel:                                   # static condensation of the released local DOFs
                keep = [d for d in range(6) if d not in rel]
                kii = k[np.ix_(rel, rel)] + np.eye(len(rel)) * 1e-9 * max(1.0, EI / L)
                kc = k[np.ix_(keep, keep)] - k[np.ix_(keep, rel)] @ np.linalg.solve(kii, k[np.ix_(rel, keep)])
                k = np.zeros((6, 6)); k[np.ix_(keep, keep)] = kc
            kg = T.T @ k @ T
            dofs = [3 * i, 3 * i + 1, 3 * i + 2, 3 * j, 3 * j + 1, 3 * j + 2]
            K[np.ix_(dofs, dofs)] += kg
        free = [d for d in range(3 * n) if d not in self.fix]
        U = np.zeros(3 * n)
        U[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
        R = K @ U - F
        return U, R


def build_and_solve(bar_line_load, bar_end_hinges=False):
    g = Grillage()
    ys = sorted(set([17.5, 1218.5] + BAR_Y + [y + 10.0 for y in BAR_Y[:-1]]))
    lines = {}
    for name, x, EI, GJ in (("J", XJ, E * Jp["Ix"], G * J_tJ), ("L", XL, E * Lp["Ix"], G * L_tJ)):
        nd = [g.node(x, y) for y in ys]; lines[name] = nd
        for a, b in zip(nd[:-1], nd[1:]): g.el(a, b, EI, GJ)
    for name, x in (("F1", XF1), ("F2", XF2)):
        nd = [g.node(x, y) for y in BAR_Y]; lines[name] = nd
        for a, b in zip(nd[:-1], nd[1:]): g.el(a, b, E * FLAT["I"], G * FLAT["J"])
    F = None
    loads = {}
    for yb in BAR_Y:
        xs = [XJ, XF1, XF2, XL]
        nd = [g.node(x, yb) for x in xs]
        for k_, (a, b) in enumerate(zip(nd[:-1], nd[1:])):
            g.el(a, b, E * BAR["I"], G * BAR["J"], rel_i=bar_end_hinges and k_ == 0, rel_j=bar_end_hinges and k_ == len(xs) - 2)
        # bar line load -> lumped to its nodes (bar spans x 2.5..277.5; ends lumped to J/L lines)
        for (xa, xb), (na, nb) in zip(zip(xs[:-1], xs[1:]), zip(nd[:-1], nd[1:])):
            P = bar_line_load(yb, xa, xb) * (xb - xa)
            loads[na] = loads.get(na, 0.0) + P / 2; loads[nb] = loads.get(nb, 0.0) + P / 2
    # end plates: stiff transverse beams joining J and L, with the pins as supports
    for ye, yb in ((17.5, 10.5), (1218.5, 1225.5)):
        nJ, nL = g.node(XJ, ye), g.node(XL, ye)
        pr, pf = g.node(25.0, ye), g.node(225.0, ye)
        EIc = E * 5 * 20 ** 3 / 12 * 20        # band acting as a stiff beam in its plane is rigid for vertical load: use large EI
        for a, b in ((nJ, pr), (pr, pf), (pf, nL)): g.el(a, b, E * 1e8, G * 1e8)
        sr, sf = g.node(25.0, yb), g.node(225.0, yb)
        g.el(pr, sr, E * 491 * 2, G * 982 * 2); g.el(pf, sf, E * 491 * 2, G * 982 * 2)
        g.fix[3 * sr] = 0; g.fix[3 * sf] = 0
    n = len(g.X); Fv = np.zeros(3 * n)
    for nd, P in loads.items(): Fv[3 * nd] -= P
    # self weight of the frame members (J, L) and flats lumped along their lines
    for name, A in (("J", Jp["A"]), ("L", Lp["A"]), ("F1", FLAT["A"]), ("F2", FLAT["A"])):
        nd = lines[name]
        for a, b in zip(nd[:-1], nd[1:]):
            L = abs(g.X[b][1] - g.X[a][1]); P = RHO_W * A * L
            Fv[3 * a] -= P / 2; Fv[3 * b] -= P / 2
    U, R = g.solve(Fv)
    def w_at(name, y):
        nd = min(lines[name], key=lambda i: abs(g.X[i][1] - y)); return U[3 * nd]
    return dict(L=w_at("L", 618), J=w_at("J", 618), F1=w_at("F1", 618), F2=w_at("F2", 618), load=-Fv[0::3].sum(), react=-sum(R[3 * i] for i in range(n) if 3 * i in g.fix))


if __name__ == "__main__":
    print(f"J member: A={Jp['A']:.1f} centroid=({Jp['cx']:.2f},{Jp['cy']:.2f}) Ix={Jp['Ix']:.0f} Iz={Jp['Iy']:.0f} Ixz={Jp['Ixy']:.0f} J_t={J_tJ:.0f}")
    print(f"L member: A={Lp['A']:.1f} centroid=({Lp['cx']:.2f},{Lp['cy']:.2f}) Ix={Lp['Ix']:.0f} Iz={Lp['Iy']:.0f} Ixz={Lp['Ixy']:.0f} J_t={L_tJ:.0f}")
    print(f"flat 25x2.7: I={FLAT['I']:.0f}; bar 25x3: I={BAR['I']:.0f}")
    q = 7.5e-3
    for hinges in (False, True):
        r = build_and_solve(lambda yb, xa, xb: q * 250 / 275 * 20, bar_end_hinges=hinges)
        print(f"SLS crowd, bar ends {'pinned' if hinges else 'rigid to J/L torsion'}: mid-span deflection  front L {r['L']:.2f}  flat2 {r['F2']:.2f}  flat1 {r['F1']:.2f}  back J {r['J']:.2f} mm   (load {r['load']:.1f} N, reactions {r['react']:.1f} N)")
