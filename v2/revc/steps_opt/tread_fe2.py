"""Shell + beam FE of the FINAL tread (25.9.2026 IFC), tread-local mm: x 0 (back face) -> 280 (front), y along the span
(0 = left end of the frame incl. pins), z 0 (bottom) -> 50 (walking surface).
Measured geometry (final/cut_final.py, endcap_map.py):
  back member (J): rear wall x 0-5 z 0-50, bottom flange z 0-5 x 0-50, upturn x 45-50 z 0-17.5   (5 mm)
  front member (L): lip x 275-280 z 25-50, return z 25-30 x 252.5-280                            (5 mm)
  NO top deck. End plates 5 mm at y 15-20 / 1216-1221: back-box closure + 20 mm band z 30-50 across the full depth.
  grating: 60 transverse bars 3 x 25 (z 25-50), 270 long (x 5-275), y centres 25 + 20 k (k = 0..59), welded to the rear
  wall and the lip; 2 longitudinal flats 2.7 x 25 at x = 83.65 and 190.8, y 26.5-1203.5 (NOT connected to the end plates),
  welded to every bar.  Pins as before: rear O10.7 (left) / O10 (right) at (25, 12.5); front O10 at (225, 37.5).
Supports: pin bearings at the rail inner-wall mid-planes (left y = 10.5, right y = 1225.5), fixed in x and z.
MITC4 shells (linear, exact equilibrium) + elasticBeamColumn bars."""
import math, json, sys
import numpy as np
import openseespy.opensees as ops

E, NU, T = 70000.0, 0.3, 5.0
G = E / (2 * (1 + NU))
RHO_W = 2.70e-9 * 9810.0
J_CHAIN = [(47.5, 17.5), (47.5, 2.5), (2.5, 2.5), (2.5, 50.0)]
L_CHAIN = [(277.5, 50.0), (277.5, 27.5), (252.5, 27.5)]
SEG = ["upturn", "bottom flange", "rear wall", "front lip", "return"]
Y_CAP = (17.5, 1212.5)          # end plates 15-20 and 1210-1215 (measured, cuts_t0ends)
BAR_Y = [25.0 + 20.0 * k for k in range(60)]
FLAT_X = (83.65, 190.8)
FLAT_T = 2.7
FLATS_JOINED = False           # True: flats run to the end plates and are welded to them over z 30-50 (owner: "it will be joined")
BAR_B, BAR_H = 3.0, 25.0
# bearings = rail inner-wall mid-planes: left wall local y 8.5-13.0 (mid 10.75), right wall 1224-1229 (mid 1226.5)
PINS = {"L_rear": dict(x=25.0, z=12.5, d=10.73, y_cap=17.5, y_b=10.75), "L_front": dict(x=225.0, z=37.5, d=10.0, y_cap=17.5, y_b=10.75),
        "R_rear": dict(x=25.0, z=12.5, d=10.0, y_cap=1212.5, y_b=1226.5), "R_front": dict(x=225.0, z=37.5, d=10.0, y_cap=1212.5, y_b=1226.5)}


def ygrid():
    ys = set([Y_CAP[0], Y_CAP[1], 20.0, 1210.0])
    y = 25.0
    while y <= 1205.0 + 1e-9:
        ys.add(round(y, 4)); y += 5.0
    return sorted(ys)


def build(h=2.5, bar_shells=False):
    ops.wipe(); ops.model("basic", "-ndm", 3, "-ndf", 6)
    ops.section("ElasticMembranePlateSection", 1, E, NU, T, 0.0)
    ops.section("ElasticMembranePlateSection", 2, E, NU, FLAT_T, 0.0)
    ops.section("ElasticMembranePlateSection", 3, E, NU, BAR_B, 0.0)
    nodes, ntag, etag, elems = {}, [0], [0], {}

    def node(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in nodes:
            ntag[0] += 1; ops.node(ntag[0], x, y, z); nodes[k] = ntag[0]
        return nodes[k]
    ys = ygrid()
    # frame shells
    for chain, base in ((J_CHAIN, 0), (L_CHAIN, 3)):
        prof, pseg = [], []
        for si, (a, b) in enumerate(zip(chain[:-1], chain[1:])):
            n = max(1, int(round(math.dist(a, b) / h)))
            for k in range(n):
                prof.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)); pseg.append(base + si)
        prof.append(chain[-1])
        for j in range(len(ys) - 1):
            for i in range(len(prof) - 1):
                (x0, z0), (x1, z1) = prof[i], prof[i + 1]
                n1 = node(x0, ys[j], z0); n2 = node(x0, ys[j + 1], z0); n3 = node(x1, ys[j + 1], z1); n4 = node(x1, ys[j], z1)
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, 1)
                elems[etag[0]] = dict(kind="frame", seg=pseg[i], xm=(x0 + x1) / 2, zm=(z0 + z1) / 2, ym=(ys[j] + ys[j + 1]) / 2,
                                      area=math.dist(prof[i], prof[i + 1]) * (ys[j + 1] - ys[j]), t=T)
    # end plates (5 mm): back box x 2.5-47.5 z 2.5-50 ; band x 47.5-277.5 z 30-50
    for yc in Y_CAP:
        for (x0, x1, z0, z1) in ((2.5, 47.5, 2.5, 50.0), (47.5, 277.5, 30.0, 50.0)):
            nx_, nz_ = int(round((x1 - x0) / h)), int(round((z1 - z0) / h))
            xs_ = [x0 + a * h for a in range(nx_ + 1)]
            if FLATS_JOINED and x0 > 40:                 # plate nodes on the flat lines so the welds share nodes
                xs_ = sorted(set(round(v, 4) for v in xs_ + list(FLAT_X)))
            for a in range(len(xs_) - 1):
                for b in range(nz_):
                    xa, xb = xs_[a], xs_[a + 1]; za, zb = z0 + b * h, z0 + (b + 1) * h
                    n1 = node(xa, yc, za); n2 = node(xb, yc, za); n3 = node(xb, yc, zb); n4 = node(xa, yc, zb)
                    etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, 1)
                    elems[etag[0]] = dict(kind="cap", xm=(xa + xb) / 2, zm=(za + zb) / 2, ym=yc, area=(xb - xa) * (zb - za), t=T)
    # longitudinal flats (2.7 mm shells in the y-z plane), y from the first to the last bar
    fy = [y for y in ys if BAR_Y[0] - 1e-9 <= y <= BAR_Y[-1] + 1e-9]
    if FLATS_JOINED:                                    # flats run into the end plates (y 17.5 / 1212.5 mid-planes)
        fy = [y for y in ys if Y_CAP[0] - 1e-9 <= y <= Y_CAP[1] + 1e-9]
    fz = [25.0 + (5.0 if bar_shells else h) * k for k in range(int(round(25.0 / (5.0 if bar_shells else h))) + 1)]
    for xf in FLAT_X:
        for j in range(len(fy) - 1):
            for k in range(len(fz) - 1):
                n1 = node(xf, fy[j], fz[k]); n2 = node(xf, fy[j + 1], fz[k]); n3 = node(xf, fy[j + 1], fz[k + 1]); n4 = node(xf, fy[j], fz[k + 1])
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, 2)
                elems[etag[0]] = dict(kind="flat", xm=xf, zm=(fz[k] + fz[k + 1]) / 2, ym=(fy[j] + fy[j + 1]) / 2, area=(fy[j + 1] - fy[j]) * h, t=FLAT_T)
    # grating bars: beams at z = 37.5, x from 2.5 to 277.5 (nodes every h + at the flats)
    ops.geomTransf("Linear", 1, 0.0, 0.0, 1.0)              # bars along x: local z = global z
    A_b = BAR_B * BAR_H; Iy_b = BAR_B * BAR_H ** 3 / 12; Iz_b = BAR_H * BAR_B ** 3 / 12
    J_b = BAR_H * BAR_B ** 3 / 3 * (1 - 0.63 * BAR_B / BAR_H)
    bx = sorted(set([round(2.5 + h * k, 4) for k in range(int(round(275 / h)) + 1)] + list(FLAT_X)))
    bars = {}
    ops.geomTransf("Linear", 2, 1.0, 0.0, 0.0)              # stiff weld links (vertical): local z = global x
    if bar_shells:
        bxs = sorted(set([round(2.5 + 5.0 * k, 4) for k in range(56)] + [277.5] + list(FLAT_X)))
        for yb in BAR_Y:
            for i in range(len(bxs) - 1):
                for k in range(len(fz) - 1):
                    n1 = node(bxs[i], yb, fz[k]); n2 = node(bxs[i + 1], yb, fz[k]); n3 = node(bxs[i + 1], yb, fz[k + 1]); n4 = node(bxs[i], yb, fz[k + 1])
                    etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, 3)
                    elems[etag[0]] = dict(kind="barshell", y=yb, xm=(bxs[i] + bxs[i + 1]) / 2, zm=(fz[k] + fz[k + 1]) / 2, ym=yb,
                                          x0=bxs[i], x1=bxs[i + 1], ztop=fz[k + 1], area=(bxs[i + 1] - bxs[i]) * (fz[k + 1] - fz[k]), t=BAR_B)
    for yb in ([] if bar_shells else BAR_Y):
        bn = [node(x, yb, 37.5) for x in bx]
        bars[yb] = (bx, bn)
        for i in range(len(bn) - 1):
            etag[0] += 1; ops.element("elasticBeamColumn", etag[0], bn[i], bn[i + 1], A_b, E, G, J_b, Iy_b, Iz_b, 1)
            elems[etag[0]] = dict(kind="bar", y=yb, x0=bx[i], x1=bx[i + 1], area=0.0)
        # welds over the bar height to the rear wall (x=2.5), the lip (x=277.5) and each flat
        for xw in (2.5, 277.5) + FLAT_X:
            c = node(xw, yb, 37.5)
            for zz in fz:
                if abs(zz - 37.5) < 1e-6: continue
                o = node(xw, yb, zz)
                etag[0] += 1; ops.element("elasticBeamColumn", etag[0], c, o, 500.0, E, G, 1e5, 1e5, 1e5, 2)
    # pins
    ops.geomTransf("Linear", 3, 0.0, 0.0, 1.0)
    pin_nodes = {}
    for name, p in PINS.items():
        c = node(p["x"], p["y_cap"], p["z"]); b = node(p["x"], p["y_b"], p["z"])
        d = p["d"]; A = math.pi * d * d / 4; I = math.pi * d ** 4 / 64
        etag[0] += 1; ops.element("elasticBeamColumn", etag[0], c, b, A, E, G, 2 * I, I, I, 3)
        for (kx, ky, kz), tg in list(nodes.items()):
            if tg != c and abs(ky - p["y_cap"]) < 1e-6 and math.hypot(kx - p["x"], kz - p["z"]) <= d / 2 + 1e-6:
                etag[0] += 1
                ops.geomTransf("Linear", 1000 + etag[0], 0.0, 1.0, 0.0)
                ops.element("elasticBeamColumn", etag[0], c, tg, 1000.0, E * 100, G * 100, 1e6, 1e6, 1e6, 1000 + etag[0])
        pin_nodes[name] = (c, b)
    return nodes, elems, pin_nodes, bars, dict(A=A_b, Iy=Iy_b, Iz=Iz_b, J=J_b)


def solve(load_fn, sw_factor=1.0, label="", h=2.5, bar_shells=False):
    """load_fn(bar_y, x0, x1) -> downward line load (N/mm) on that bar segment (walking-surface load on the bars)"""
    nodes, elems, pins, bars, bsec = build(h, bar_shells)
    for name, (c, b) in pins.items():
        ops.fix(b, 1, 1 if name == "L_rear" else 0, 1, 0, 0, 0)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    F = {}
    for et, e in elems.items():
        nd = ops.eleNodes(et)
        if e["kind"] in ("frame", "cap", "flat"):
            f = RHO_W * e["t"] * e["area"] * sw_factor
            for n in nd: F[n] = F.get(n, 0.0) + f / 4
        elif e["kind"] == "barshell":
            f = RHO_W * e["t"] * e["area"] * sw_factor
            for n in nd: F[n] = F.get(n, 0.0) + f / 4
            if abs(e["ztop"] - 50.0) < 1e-6:          # walking load on the top edge of the bar
                P = (load_fn(e["y"], e["x0"], e["x1"]) or 0.0) * (e["x1"] - e["x0"])
                ntop = [n for n in nd if abs(ops.nodeCoord(n)[2] - 50.0) < 1e-6]
                for n in ntop: F[n] = F.get(n, 0.0) + P / len(ntop)
        elif e["kind"] == "bar":
            L = e["x1"] - e["x0"]
            f = RHO_W * bsec["A"] * L * sw_factor + (load_fn(e["y"], e["x0"], e["x1"]) or 0.0) * L
            for n in nd: F[n] = F.get(n, 0.0) + f / 2
    for n, fz in F.items():
        ops.load(n, 0.0, 0.0, -fz, 0.0, 0.0, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.algorithm("Linear"); ops.integrator("LoadControl", 1.0); ops.analysis("Static")
    ok = ops.analyze(1); ops.reactions()
    res = dict(label=label, ok=ok, n_nodes=len(nodes), n_elems=len(elems), total_load_N=round(sum(F.values()), 1))
    ymid = 618.0
    def disp(x, z, y):
        k = min(nodes, key=lambda kk: abs(kk[0] - x) + abs(kk[1] - y) + abs(kk[2] - z)); return ops.nodeDisp(nodes[k])
    res["uz_mid_lip_top"] = disp(277.5, 50.0, ymid)[2]; res["uz_mid_rearwall_top"] = disp(2.5, 50.0, ymid)[2]
    res["uz_mid_flat1"] = disp(FLAT_X[0], 50.0, ymid)[2]; res["uz_mid_flat2"] = disp(FLAT_X[1], 50.0, ymid)[2]
    res["uz_min"] = min(ops.nodeDisp(t)[2] for t in nodes.values())
    res["twist_mid_deg"] = math.degrees(math.atan2(res["uz_mid_rearwall_top"] - res["uz_mid_lip_top"], 275.0))
    # equilibrium check (support moment about the y axis through the rear pin line vs applied)
    My_sup = 0.0; Fz_sup = 0.0
    for name, (c, b) in pins.items():
        R = ops.nodeReaction(b); x, y, z = ops.nodeCoord(b)
        My_sup += (z - 12.5) * R[0] - (x - 25) * R[2]; Fz_sup += R[2]
    My_load = sum(-(ops.nodeCoord(n)[0] - 25) * fz for n, fz in F.items())
    res["equilibrium"] = dict(Fz_support=round(Fz_sup, 2), Fz_load=round(sum(F.values()), 2), My_support=round(My_sup, 1), My_load=round(My_load, 1))
    # shell stresses
    rows = []
    for et, e in elems.items():
        if e["kind"] not in ("frame", "cap", "flat", "barshell"): continue
        r = ops.eleResponse(et, "stresses")
        if not r: continue
        t = e["t"]
        for gp in np.array(r).reshape(-1, 8):
            N11, N22, N12, M11, M22, M12 = gp[:6]
            for s in (+1, -1):
                s11 = N11 / t + s * 6 * M11 / t ** 2; s22 = N22 / t + s * 6 * M22 / t ** 2; s12 = N12 / t + s * 6 * M12 / t ** 2
                vm = math.sqrt(s11 * s11 + s22 * s22 - s11 * s22 + 3 * s12 * s12)
                rows.append((vm, s11, s22, s12, N11 / t, et, e["kind"], SEG[e["seg"]] if e["kind"] == "frame" else e["kind"],
                             round(e["xm"], 1), round(e["ym"], 1), round(e["zm"], 1)))
    rows.sort(key=lambda r: -r[0])
    body = [w for w in rows if w[6] in ("frame", "flat", "barshell") and 45 < w[9] < 1190]
    res["vm_max_body"] = body[0] if body else None
    res["vm_max_all"] = rows[0]
    res["vm_by_part"] = {}
    for w in body:
        res["vm_by_part"].setdefault(w[7], w)
    # bar stresses: bending about the strong axis + weak axis + axial
    bmax = (0, None)
    for et, e in elems.items():
        if e["kind"] != "bar": continue
        f = ops.eleResponse(et, "localForces")          # [N1 Vy1 Vz1 T1 My1 Mz1 N2 Vy2 Vz2 T2 My2 Mz2]
        for (N, My, Mz, Tq) in ((f[0], f[4], f[5], f[3]), (f[6], f[10], f[11], f[9])):
            s = abs(N) / bsec["A"] + abs(My) / (bsec["Iy"] / (BAR_H / 2)) + abs(Mz) / (bsec["Iz"] / (BAR_B / 2))
            if s > bmax[0]:
                bmax = (s, dict(bar_y=e["y"], x=e["x0"], N=N, My=My, Mz=Mz, T=Tq))
    res["bar_max"] = bmax
    res["pins"] = {n: [round(v, 1) for v in ops.nodeReaction(b)[:3]] for n, (c, b) in pins.items()}
    return res


def udl(q, trib_y=20.0, bar_len=275.0, going=250.0):
    """crowd q (N/mm2) over the plan area of the going: per bar line load = q * going/275 * 20 mm"""
    return lambda yb, x0, x1: q * going / bar_len * trib_y


def patch(P, xc, yc, a=200.0, b=200.0):
    """P (N) on an a (x) by b (y) patch: bars whose 20 mm strip overlaps the patch get P/(a b) * overlap"""
    def f(yb, x0, x1):
        oy = max(0.0, min(yb + 10, yc + b / 2) - max(yb - 10, yc - b / 2))
        ox0, ox1 = max(x0, xc - a / 2), min(x1, xc + a / 2)
        if oy <= 0 or ox1 <= ox0: return 0.0
        return P / (a * b) * oy * (ox1 - ox0) / (x1 - x0)
    return f


if __name__ == "__main__":
    r = solve(udl(7.5e-3), label="SLS crowd 7.5 kN/m2 (going 250) + SW")
    print(json.dumps({k: v for k, v in r.items()}, indent=1, default=str))
