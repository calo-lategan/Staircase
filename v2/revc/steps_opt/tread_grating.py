"""Open-grating step options that keep holes for drainage and grip, same outside size (280 deep x 50 thick x 1,200).
Bearing bars run ALONG the step (the 1.2 m span between the rails); cross bars 3 x 25 on top at 50 mm run front to back.
Cut from one plate (or slotted and welded) = shared nodes at every crossing. End plates 5 mm at y 17.5 / 1212.5 carry
the four pins exactly as in the final model. Shell FE (ShellMITC4, linear, exact equilibrium); loads on the bar tops
(z = 50), shared between the bearing-bar tops inside the loaded area. 6082-T6 f_o 250 / 1.1.
Tread-local mm: x 0 (back) -> 280 (front), y along the span, z 0 (bottom) -> 50 (walking surface)."""
import math, json, sys, os
import numpy as np
import openseespy.opensees as ops
E, NU = 70000.0, 0.3
G = E / (2 * (1 + NU)); RHO_W = 2.70e-9 * 9810.0; FD = 250.0 / 1.1
Y_CAP = (17.5, 1212.5)
PINS = {"L_rear": dict(x=25.0, z=12.5, d=10.73, y_cap=17.5, y_b=10.75), "L_front": dict(x=225.0, z=37.5, d=10.0, y_cap=17.5, y_b=10.75),
        "R_rear": dict(x=25.0, z=12.5, d=10.0, y_cap=1212.5, y_b=1226.5), "R_front": dict(x=225.0, z=37.5, d=10.0, y_cap=1212.5, y_b=1226.5)}

def build(bars, cross_pitch=50.0, cross_t=3.0, cross_z0=25.0, hy=10.0, h=2.5):
    """bars: list of (x, t, z0) bearing bars (z0 -> 50); cross bars: y pitch, from the first to the last bearing bar"""
    ops.wipe(); ops.model("basic", "-ndm", 3, "-ndf", 6)
    tags = {}
    def sec(t):
        if t not in tags: tags[t] = len(tags) + 1; ops.section("ElasticMembranePlateSection", tags[t], E, NU, t, 0.0)
        return tags[t]
    nodes, ntag, etag, elems = {}, [0], [0], {}
    def node(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in nodes: ntag[0] += 1; ops.node(ntag[0], x, y, z); nodes[k] = ntag[0]
        return nodes[k]
    xb = [b[0] for b in bars]
    cy = [Y_CAP[0] + cross_pitch / 2 + cross_pitch * k for k in range(int((Y_CAP[1] - Y_CAP[0]) / cross_pitch))]
    ys = sorted(set([round(Y_CAP[0] + (Y_CAP[1] - Y_CAP[0]) * j / int(round((Y_CAP[1] - Y_CAP[0]) / hy)), 4) for j in range(int(round((Y_CAP[1] - Y_CAP[0]) / hy)) + 1)] + [round(c, 4) for c in cy]))
    zs = [h * k for k in range(int(round(50 / h)) + 1)]
    xs = sorted(set([round(v, 4) for v in [2.5 * k for k in range(113)] + xb + [25.0, 225.0]]))
    xs = [x for x in xs if 0 <= x <= 280]
    for (x, t, z0) in bars:                                   # bearing bars: plates in the y-z plane at x
        st = sec(t); zz = [z for z in zs if z >= z0 - 1e-9]
        for j in range(len(ys) - 1):
            for k in range(len(zz) - 1):
                n1 = node(x, ys[j], zz[k]); n2 = node(x, ys[j + 1], zz[k]); n3 = node(x, ys[j + 1], zz[k + 1]); n4 = node(x, ys[j], zz[k + 1])
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, st)
                elems[etag[0]] = dict(kind="bar", part=f"bearing bar x{x:g}", t=t, xm=x, ym=(ys[j] + ys[j + 1]) / 2, zm=(zz[k] + zz[k + 1]) / 2, area=(ys[j + 1] - ys[j]) * (zz[k + 1] - zz[k]))
    stc = sec(cross_t); xin = [x for x in xs if xb[0] - 1e-9 <= x <= xb[-1] + 1e-9]; zc = [z for z in zs if z >= cross_z0 - 1e-9]
    for y in cy:                                              # cross bars: plates in the x-z plane at y
        for i in range(len(xin) - 1):
            for k in range(len(zc) - 1):
                n1 = node(xin[i], y, zc[k]); n2 = node(xin[i + 1], y, zc[k]); n3 = node(xin[i + 1], y, zc[k + 1]); n4 = node(xin[i], y, zc[k + 1])
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, stc)
                elems[etag[0]] = dict(kind="cross", part="cross bar", t=cross_t, xm=(xin[i] + xin[i + 1]) / 2, ym=y, zm=(zc[k] + zc[k + 1]) / 2, area=(xin[i + 1] - xin[i]) * (zc[k + 1] - zc[k]))
    st5 = sec(5.0)
    for yc in Y_CAP:                                          # end plates, full 280 x 50
        for i in range(len(xs) - 1):
            for k in range(len(zs) - 1):
                n1 = node(xs[i], yc, zs[k]); n2 = node(xs[i + 1], yc, zs[k]); n3 = node(xs[i + 1], yc, zs[k + 1]); n4 = node(xs[i], yc, zs[k + 1])
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, st5)
                elems[etag[0]] = dict(kind="cap", part="end plate", t=5.0, xm=(xs[i] + xs[i + 1]) / 2, ym=yc, zm=(zs[k] + zs[k + 1]) / 2, area=(xs[i + 1] - xs[i]) * (zs[k + 1] - zs[k]))
    ops.geomTransf("Linear", 1, 0.0, 0.0, 1.0); pin_nodes = {}
    for name, p in PINS.items():
        c = node(p["x"], p["y_cap"], p["z"]); b = node(p["x"], p["y_b"], p["z"])
        d = p["d"]; A = math.pi * d * d / 4; I = math.pi * d ** 4 / 64
        etag[0] += 1; ops.element("elasticBeamColumn", etag[0], c, b, A, E, G, 2 * I, I, I, 1)
        for (kx, ky, kz), tg in list(nodes.items()):
            if tg != c and abs(ky - p["y_cap"]) < 1e-6 and math.hypot(kx - p["x"], kz - p["z"]) <= d / 2 + 1e-6:
                etag[0] += 1; ops.geomTransf("Linear", 1000 + etag[0], 0.0, 1.0, 0.0)
                ops.element("elasticBeamColumn", etag[0], c, tg, 1000.0, E * 100, G * 100, 1e6, 1e6, 1e6, 1000 + etag[0])
        pin_nodes[name] = (c, b)
    tops = sorted(set((kx, ky) for (kx, ky, kz) in nodes if abs(kz - 50) < 1e-6 and any(abs(kx - x) < 1e-6 for x in xb) and Y_CAP[0] < ky < Y_CAP[1]))
    return nodes, elems, pin_nodes, ys, xb, tops

def solve(bars, load, swf=1.0, label="", **kw):
    """load: ('patch', P, xc, yc, a, b) or ('udl', q)"""
    nodes, elems, pins, ys, xb, tops = build(bars, **kw)
    for pn, (c, b) in pins.items(): ops.fix(b, 1, 1 if pn == "L_rear" else 0, 1, 0, 0, 0)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    F = {}
    for et, e in elems.items():
        f = RHO_W * e["t"] * e["area"] * swf
        for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + f / 4
    ydy = {}
    ysorted = ys
    for i, y in enumerate(ysorted):
        lo = (y - ysorted[i - 1]) / 2 if i > 0 else 0.0; hi = (ysorted[i + 1] - y) / 2 if i < len(ysorted) - 1 else 0.0; ydy[round(y, 4)] = lo + hi
    xw = {}
    for i, x in enumerate(xb):                                 # tributary width of each bearing bar across the step
        lo = (x - xb[i - 1]) / 2 if i > 0 else x; hi = (xb[i + 1] - x) / 2 if i < len(xb) - 1 else 280 - x; xw[x] = lo + hi
    if load[0] == "udl":
        q = load[1] * 250.0 / 280.0                             # crowd on the going, spread over the 280 depth
        for (x, y) in tops: n = nodes[(round(x, 4), round(y, 4), 50.0)]; F[n] = F.get(n, 0.0) + q * xw[x] * ydy[round(y, 4)]
    else:
        _, P, xc, yc, a, b = load
        sel = [(x, y) for (x, y) in tops if abs(x - xc) <= a / 2 and abs(y - yc) <= b / 2]
        wsum = sum(ydy[round(y, 4)] for x, y in sel)
        for (x, y) in sel: n = nodes[(round(x, 4), round(y, 4), 50.0)]; F[n] = F.get(n, 0.0) + P * ydy[round(y, 4)] / wsum
    for n, fz in F.items(): ops.load(n, 0.0, 0.0, -fz, 0.0, 0.0, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack"); ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0); ops.analysis("Static"); ok = ops.analyze(1); ops.reactions()
    res = dict(label=label, ok=ok, eq=[round(sum(ops.nodeReaction(b)[2] for c, b in pins.values()), 1), round(sum(F.values()), 1)])
    res["uz_min"] = min(ops.nodeDisp(t)[2] for t in nodes.values())
    ymid = min(ys, key=lambda y: abs(y - 618.0))
    def uz(x, z): return ops.nodeDisp(nodes[min(nodes, key=lambda k: abs(k[0] - x) + abs(k[1] - ymid) + abs(k[2] - z))])[2]
    res["front_mid"] = uz(xb[-1], 50.0); res["back_mid"] = uz(xb[0], 50.0)
    res["twist_deg"] = math.degrees(math.atan2(res["back_mid"] - res["front_mid"], xb[-1] - xb[0]))
    worst, worst_end = (0, None), (0, None)
    for et, e in elems.items():
        if e["kind"] == "cap": continue
        r = ops.eleResponse(et, "stresses")
        if not r: continue
        t = e["t"]; vm = 0.0
        for gp in np.array(r).reshape(-1, 8):
            N11, N22, N12, M11, M22, M12 = gp[:6]
            for s in (1, -1):
                a_ = N11 / t + s * 6 * M11 / t ** 2; b_ = N22 / t + s * 6 * M22 / t ** 2; c_ = N12 / t + s * 6 * M12 / t ** 2
                vm = max(vm, math.sqrt(a_ * a_ + b_ * b_ - a_ * b_ + 3 * c_ * c_))
        rec = (round(vm, 1), e["part"], round(e["xm"], 1), round(e["ym"], 1), round(e["zm"], 1))
        if 40 < e["ym"] < 1190:
            if vm > worst[0]: worst = (vm, rec)
        elif vm > worst_end[0]: worst_end = (vm, rec)            # within 25 mm of the end-plate welds
    res["vm"] = worst[1]; res["util"] = worst[0] / FD
    res["vm_end"] = worst_end[1]; res["util_end_haz"] = worst_end[0] / (125.0 / 1.1)
    res["pins"] = {n: [round(v, 1) for v in ops.nodeReaction(b)[:3]] for n, (c, b) in pins.items()}
    return res

CASES = {"ULS 4 kN front, mid-span": (("patch", 6000.0, 177.5, 618.0, 200.0, 200.0), 1.35), "ULS 4 kN centre, mid-span": (("patch", 6000.0, 140.0, 618.0, 200.0, 200.0), 1.35),
         "ULS 4 kN front, at the end": (("patch", 6000.0, 177.5, 125.0, 200.0, 200.0), 1.35), "ULS crowd": (("udl", 1.5 * 7.5e-3), 1.35),
         "SLS 4 kN front, mid-span": (("patch", 4000.0, 177.5, 618.0, 200.0, 200.0), 1.0), "SLS crowd": (("udl", 7.5e-3), 1.0),
         "SLS person 1 kN at the nosing": (("patch", 1000.0, 227.5, 618.0, 100.0, 100.0), 1.0)}
def layout(pitch, t_in=3.0, z0_in=0.0, t_edge=5.0):
    n = int(round(275 / pitch)); xs = [2.5 + 275 * k / n for k in range(1, n)]
    return [(2.5, t_edge, 0.0)] + [(round(x, 2), t_in, z0_in) for x in xs] + [(277.5, t_edge, 0.0)]
OPTIONS = {
    "G1 grating: bars 3 x 50 at 34 mm along the step": layout(34.4),
    "G2 grating: bars 3 x 50 at 46 mm along the step": layout(45.8),
    "G3 grating: bars 3 x 40 at 34 mm along the step": layout(34.4, 3.0, 10.0),
    "G4 grating: bars 3 x 50 at 34 mm, 8 mm nosing bar": layout(34.4)[:-1] + [(276.0, 8.0, 0.0)],
    "G5 grating: bars 3 x 50 at 46 mm, 8 mm nosing bar": layout(45.8)[:-1] + [(276.0, 8.0, 0.0)],
}
def mass(bars, cross_pitch=50.0):
    L = 1195.0
    m = sum(t * (50 - z0) * L for x, t, z0 in bars) + int(L / cross_pitch) * 3 * 25 * 275 + 2 * 280 * 50 * 5
    return m * 2.7e-6

if __name__ == "__main__":
    names = [n for n in OPTIONS if not sys.argv[1:] or n in sys.argv[1:]]
    out = json.load(open("tread_grating.json")) if os.path.exists("tread_grating.json") else {}
    for name in names:
        bars = OPTIONS[name]; rr = {}
        for cn, (ld, swf) in CASES.items():
            r = solve(bars, ld, swf, cn); rr[cn] = r
            print(f"{name[:40]:<40} {cn:<30} ok={r['ok']} eq {r['eq']}  front {r['front_mid']:6.2f}  min {r['uz_min']:6.2f}  twist {r['twist_deg']:5.2f}  "
                  f"vm {r['vm']} u {r['util']:.2f} | ends (weld zone) u {r['util_end_haz']:.2f}", flush=True)
        out[name] = dict(bars=bars, mass_kg=mass(bars), cases=rr)
        json.dump(out, open("tread_grating.json", "w"), indent=1, default=str)
