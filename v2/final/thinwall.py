"""Thin-walled OPEN section properties from a centreline chain (Vlasov): A, centroid, Ix/Iz/Ixz, principal angle,
shear centre, St Venant J, warping constant Iw, sectorial coordinate. Units mm.
section = [(x0,z0),(x1,z1),...] chain points (one open branchless chain), t = thickness per segment (list or scalar)."""
import math
import numpy as np


def props(chain, t, n_sub=40):
    P = np.array(chain, float); nseg = len(P) - 1
    ts = np.full(nseg, t, float) if np.isscalar(t) else np.array(t, float)
    # subdivide for numerical integration (exact for linear/quadratic integrands with Simpson; we use fine midpoint)
    pts, tt, ds = [], [], []
    for i in range(nseg):
        a, b = P[i], P[i + 1]; L = np.linalg.norm(b - a)
        for k in range(n_sub):
            s0, s1 = k / n_sub, (k + 1) / n_sub
            pts.append((a + (b - a) * s0, a + (b - a) * s1)); tt.append(ts[i]); ds.append(L / n_sub)
    tt = np.array(tt); ds = np.array(ds)
    mid = np.array([(p + q) / 2 for p, q in pts])
    dA = tt * ds
    A = dA.sum()
    xc, zc = (mid[:, 0] * dA).sum() / A, (mid[:, 1] * dA).sum() / A
    # second moments incl. own-segment inertia (thin strips): use exact strip formula per sub-segment
    Ixx = Izz = Ixz = 0.0
    for (p, q), ti, dsi in zip(pts, tt, ds):
        x0, z0 = p[0] - xc, p[1] - zc; x1, z1 = q[0] - xc, q[1] - zc
        Ixx += ti * dsi * (z0 * z0 + z0 * z1 + z1 * z1) / 3      # int z^2 dA along a straight strip
        Izz += ti * dsi * (x0 * x0 + x0 * x1 + x1 * x1) / 3
        Ixz += ti * dsi * (2 * x0 * z0 + x0 * z1 + x1 * z0 + 2 * x1 * z1) / 6
    # sectorial coordinate w.r.t. pole B (centroid) starting at chain start
    def sectorial(pole):
        w = [0.0]; acc = 0.0
        for (p, q) in pts:
            r0 = p - pole; r1 = q - pole
            acc += (r0[0] * r1[1] - r0[1] * r1[0])       # 2 x swept area (signed)
            w.append(acc)
        w = np.array(w)
        return (w[:-1] + w[1:]) / 2                        # mid-point values
    wB = sectorial(np.array([xc, zc]))
    xm, zm = mid[:, 0] - xc, mid[:, 1] - zc
    Iwx = (wB * zm * dA).sum(); Iwz = (wB * xm * dA).sum()
    det = Ixx * Izz - Ixz ** 2
    # shear centre relative to centroid (Vlasov): x_s = (Izz*Iwz ... ) using standard formulas with product inertia
    xs = (Iwx * Izz - Iwz * Ixz) / det * 1.0
    zs = -(Iwz * Ixx - Iwx * Ixz) / det * 1.0
    # sign convention check done by validation (channel); recompute sectorial about shear centre & normalise
    S = np.array([xc + xs, zc + zs])
    wS = sectorial(S)
    w0 = (wS * dA).sum() / A
    wn = wS - w0
    Iw = (wn ** 2 * dA).sum()
    J = sum(ti ** 3 * dsi / 3 for ti, dsi in zip(tt, ds))
    alpha = 0.5 * math.atan2(-2 * Ixz, Izz - Ixx)
    I1 = (Ixx + Izz) / 2 + math.hypot((Ixx - Izz) / 2, Ixz); I2 = (Ixx + Izz) / 2 - math.hypot((Ixx - Izz) / 2, Ixz)
    zmin, zmax = P[:, 1].min(), P[:, 1].max()
    return dict(A=A, xc=xc, zc=zc, Ix=Ixx, Iz=Izz, Ixz=Ixz, I1=I1, I2=I2, alpha_deg=math.degrees(alpha),
                xs=S[0], zs=S[1], J=J, Iw=Iw, len=ds.sum())


if __name__ == "__main__":
    # validation: channel h=100 (centreline), b=50, t=5 (web t=5): shear centre e = 3 b^2 / (6 b + h) from web (flange t = web t)
    h, b, t = 100.0, 50.0, 5.0
    ch = [(b, h), (0, h), (0, 0), (b, 0)]
    p = props(ch, t)
    e_theory = 3 * b * b / (6 * b + h)
    Iw_theory = t * b ** 3 * h ** 2 / 12 * (3 * b + 2 * h) / (6 * b + h)
    Ix_theory = t * h ** 3 / 12 + 2 * b * t * (h / 2) ** 2
    print("channel: xs", round(p["xs"], 3), "expected", round(-e_theory, 3), "| Iw", round(p["Iw"]), "expected", round(Iw_theory), "| Ix", round(p["Ix"]), "expected", round(Ix_theory), "| J", round(p["J"]), "expected", round((2 * b + h) * t ** 3 / 3))
    # tread centreline chain (tread-local x from back face, z from bottom): upturn tip -> bottom -> rear wall -> deck -> lip -> return tip
    tread = [(47.5, 17.5), (47.5, 2.5), (2.5, 2.5), (2.5, 47.5), (277.5, 47.5), (277.5, 27.5), (252.5, 27.5)]
    q = props(tread, 5.0)
    print({k: round(v, 2) for k, v in q.items()})
