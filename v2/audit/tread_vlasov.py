"""Method 2 (hand / closed-form): thin-walled beam (Vlasov) for the tread, independent of the shell FE.
Unsymmetric bending (exact polygon Ix, Iz, Ixz) + non-uniform torsion (J, Iw, shear centre from thinwall.py)
with fork supports at the pin bearings (twist and both translations restrained, warping free).
Solved by finite differences along the span (supports y=10.49 and 1226.5, load on the profile 17.5..1212.5)."""
import math, json
import numpy as np
from section_tools import section
from thinwall import props

E, NU = 70000.0, 0.3
G = E / (2 * (1 + NU))
RHO_W = 2.70e-9 * 9810.0
Y0, Y1 = 10.49, 1226.5
L = Y1 - Y0
PROFILE = [(0, 0), (50, 0), (50, 17.5), (45, 17.5), (45, 5), (5, 5), (5, 45), (275, 45), (275, 30), (252.51, 30), (252.51, 25),
           (280, 25), (280, 50), (0, 50)]
ex = section([PROFILE])
tw = props([(47.5, 17.5), (47.5, 2.5), (2.5, 2.5), (2.5, 47.5), (277.5, 47.5), (277.5, 27.5), (252.5, 27.5)], 5.0)
A, xc, zc = ex["A"], ex["cx"], ex["cy"]
Ix, Iz, Ixz = ex["Ix"], ex["Iy"], ex["Ixy"]        # Ix: about horizontal axis (vertical bending)
xs, zs, J, Iw = tw["xs"], tw["zs"], tw["J"], tw["Iw"]


def solve(loads, n=1216):
    """loads: list of (y_from, y_to, w_N_per_mm, x_load) vertical (downward) line loads on the span.
    returns arrays y, vertical deflection of the shear centre (z), lateral (x), twist phi (rad, + = front goes down)."""
    y = np.linspace(Y0, Y1, n + 1); h = y[1] - y[0]
    w = np.zeros_like(y); m = np.zeros_like(y)
    for a, b, q, xl in loads:
        on = (y >= a) & (y <= b)
        w[on] += q; m[on] += q * (xl - xs)          # torque about the shear centre (front-down positive)
    # bending: M(y) from simply supported beam under w (numerical), then curvatures (unsymmetric)
    R0 = np.trapz(w * (Y1 - y), y) / L
    V = R0 - np.concatenate([[0], np.cumsum((w[1:] + w[:-1]) / 2 * h)])
    M = np.concatenate([[0], np.cumsum((V[1:] + V[:-1]) / 2 * h)])       # sagging positive
    det = Ix * Iz - Ixz ** 2
    kz = M * Iz / (E * det)                          # vertical curvature (w'' = -M Iz/(E det))
    kx = -M * Ixz / (E * det)                        # coupled lateral curvature
    def integrate(k):                                # u'' = -k, u(0)=u(L)=0
        s1 = np.concatenate([[0], np.cumsum((k[1:] + k[:-1]) / 2 * h)])
        s2 = np.concatenate([[0], np.cumsum((s1[1:] + s1[:-1]) / 2 * h)])
        u = -s2; u -= u[-1] * (y - Y0) / L
        return u
    vz = -integrate(-kz) * 1.0; vz = -np.abs(vz) if vz.min() >= 0 else vz
    vx = integrate(kx)
    # torsion: E Iw phi'''' - G J phi'' = m ; phi = phi'' = 0 at both ends. Solve as two 2nd-order eqs:
    # let B = -E Iw phi'' (bimoment); T = total torque: T' = -m ; with fork ends: phi(0)=phi(L)=0, B(0)=B(L)=0
    N = len(y); Dn = N - 2
    D2 = (np.diag(-2 * np.ones(Dn)) + np.diag(np.ones(Dn - 1), 1) + np.diag(np.ones(Dn - 1), -1)) / h ** 2
    # E Iw D2 D2 phi - G J D2 phi = m with phi=0, phi''=0 at ends -> D2 with Dirichlet ghost gives exactly that
    K = E * Iw * D2 @ D2 - G * J * D2
    phi = np.zeros(N); phi[1:-1] = np.linalg.solve(K, m[1:-1])
    phi_pp = np.zeros(N); phi_pp[1:-1] = D2 @ phi[1:-1]
    B = -E * Iw * phi_pp                               # bimoment
    return dict(y=y, M=M, vz=vz, vx=vx, phi=phi, B=B, m=m)


def point_disp(r, x, iy):
    """vertical displacement of the section point at horizontal position x (twist about the shear centre)"""
    return r["vz"][iy] - r["phi"][iy] * (x - xs)


def sectorial_at(pt):
    """normalised sectorial coordinate at a chain point (reuse thinwall integration)"""
    chain = [(47.5, 17.5), (47.5, 2.5), (2.5, 2.5), (2.5, 47.5), (277.5, 47.5), (277.5, 27.5), (252.5, 27.5)]
    S = np.array([xs, zs]); pts = []
    for a, b in zip(chain[:-1], chain[1:]):
        for k in range(200):
            p = np.array(a) + (np.array(b) - np.array(a)) * k / 200; q = np.array(a) + (np.array(b) - np.array(a)) * (k + 1) / 200
            pts.append((p, q))
    w = [0.0]; dA = []; mids = []
    for p, q in pts:
        r0, r1 = p - S, q - S
        w.append(w[-1] + (r0[0] * r1[1] - r0[1] * r1[0])); dA.append(5.0 * np.linalg.norm(q - p)); mids.append((p + q) / 2)
    w = np.array(w); wm = (w[:-1] + w[1:]) / 2; dA = np.array(dA)
    w0 = (wm * dA).sum() / dA.sum()
    mids = np.array(mids)
    i = np.argmin(np.hypot(mids[:, 0] - pt[0], mids[:, 1] - pt[1]))
    return wm[i] - w0


if __name__ == "__main__":
    print(f"exact section: A={A:.1f} centroid=({xc:.2f},{zc:.2f}) Ix={Ix:.0f} Iz={Iz:.0f} Ixz={Ixz:.0f}")
    print(f"thin-walled: shear centre=({xs:.2f},{zs:.2f}) J={J:.0f} Iw={Iw:.3e} k=L*sqrt(GJ/EIw)={L*math.sqrt(G*J/(E*Iw)):.3f}")
    Q = 7.5e-3; trib = 305.2 / 280.0
    w_crowd = Q * trib * 275.0            # N/mm on the deck (FE loads the 275 mm mid-surface width)
    w_sw = RHO_W * A
    r = solve([(17.5, 1212.5, w_crowd, 140.0), (17.5, 1212.5, w_sw, xc)])
    im = len(r["y"]) // 2
    print(f"\nSLS crowd 7.5 kN/m2 + SW (w={w_crowd + w_sw:.3f} N/mm):")
    for nm, x in (("front lip (x=277.5)", 277.5), ("deck middle (x=140)", 140.0), ("back (x=2.5)", 2.5)):
        print(f"   vertical deflection at mid-span, {nm}: {point_disp(r, x, im):7.3f} mm")
    print(f"   twist at mid-span: {math.degrees(r['phi'][im]):.3f} deg ; shear-centre vertical {r['vz'][im]:.3f} ; lateral {r['vx'][im]:.3f}")
    # longitudinal stresses at mid-span: bending (unsymmetric) + warping B*w/Iw
    M, B = r["M"][im], r["B"][im]
    det = Ix * Iz - Ixz ** 2
    for nm, (x, z) in (("return tip (252.5,27.5)", (252.5, 27.5)), ("front lip bottom (277.5,27.5)", (277.5, 27.5)), ("bottom flange back (2.5,2.5)", (2.5, 2.5)),
                       ("upturn tip (47.5,17.5)", (47.5, 17.5)), ("deck front (277.5,47.5)", (277.5, 47.5)), ("deck back (2.5,47.5)", (2.5, 47.5))):
        sb = M * (Iz * (zc - z) + Ixz * (x - xc)) / det      # tension positive below the neutral axis (sagging)
        wn = sectorial_at((x, z)); sw = -B * wn / Iw        # omega is CCW (front-up) positive; phi here is front-down positive
        print(f"   {nm:<32} bending {sb:7.2f}  warping {sw:7.2f}  total {sb + sw:7.2f} MPa   (omega_n={wn:.0f})")
    json.dump(dict(A=A, Ix=Ix, Iz=Iz, Ixz=Ixz, xs=xs, zs=zs, J=J, Iw=Iw), open("tread_vlasov_props.json", "w"), indent=1)
