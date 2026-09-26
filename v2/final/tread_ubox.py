"""Owner's sketch (27 Sep): keep the J (back, 50 deep) and the L (front edge), and add a top plate at the walking
surface and a plate at mid-depth (z 25) across the full 280 mm, so the upper 25 mm becomes a closed box. The grating
bars (front to back) sit inside the box as ribs between the two plates. Holes for drainage and grip go in both plates.
Shell FE (ShellMITC4, linear); loads on the top plate; stresses with each plate's own thickness; the four pins and the
end plates as in the final model. Tread-local mm: x 0 back -> 280 front, y along the span, z 0 bottom -> 50 top."""
import math, json, sys, os
import numpy as np
import openseespy.opensees as ops
E, NU = 70000.0, 0.3
G = E / (2 * (1 + NU)); RHO_W = 2.70e-9 * 9810.0; FD = 250.0 / 1.1; FDH = 125.0 / 1.1
Y_CAP = (17.5, 1212.5)
PINS = {"L_rear": dict(x=25.0, z=12.5, d=10.73, y_cap=17.5, y_b=10.75), "L_front": dict(x=225.0, z=37.5, d=10.0, y_cap=17.5, y_b=10.75),
        "R_rear": dict(x=25.0, z=12.5, d=10.0, y_cap=1212.5, y_b=1226.5), "R_front": dict(x=225.0, z=37.5, d=10.0, y_cap=1212.5, y_b=1226.5)}

def build(t_top, t_mid, rib_t, rib_pitch, upturn_to=17.5, flats=True, hy=10.0, h=2.5):
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
    ry = [Y_CAP[0] + rib_pitch / 2 + rib_pitch * k for k in range(int((Y_CAP[1] - Y_CAP[0]) / rib_pitch))] if rib_pitch else []
    n_y = int(round((Y_CAP[1] - Y_CAP[0]) / hy))
    ys = sorted(set([round(Y_CAP[0] + (Y_CAP[1] - Y_CAP[0]) * j / n_y, 4) for j in range(n_y + 1)] + [round(v, 4) for v in ry]))
    def seg(p0, p1):
        n = max(1, int(round(math.dist(p0, p1) / h))); return [(p0[0] + (p1[0] - p0[0]) * k / n, p0[1] + (p1[1] - p0[1]) * k / n) for k in range(n + 1)]
    plates = [("top plate", seg((2.5, 50), (277.5, 50)), t_top), ("mid plate", seg((2.5, 25), (277.5, 25)), t_mid),
              ("rear wall (J)", seg((2.5, 2.5), (2.5, 50)), 5.0), ("J bottom", seg((2.5, 2.5), (47.5, 2.5)), 5.0),
              ("J upturn", seg((47.5, 2.5), (47.5, upturn_to)), 5.0), ("front lip (L)", seg((277.5, 25), (277.5, 50)), 5.0)]
    if flats: plates += [("flat", seg((82.5, 25), (82.5, 50)), 2.7), ("flat", seg((190.0, 25), (190.0, 50)), 2.7)]
    for part, line, t in plates:
        st = sec(t)
        for j in range(len(ys) - 1):
            for i in range(len(line) - 1):
                (xa, za), (xb, zb) = line[i], line[i + 1]
                n1 = node(xa, ys[j], za); n2 = node(xa, ys[j + 1], za); n3 = node(xb, ys[j + 1], zb); n4 = node(xb, ys[j], zb)
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, st)
                elems[etag[0]] = dict(kind="plate", part=part, t=t, xm=(xa + xb) / 2, zm=(za + zb) / 2, ym=(ys[j] + ys[j + 1]) / 2,
                                      x0=min(xa, xb), x1=max(xa, xb), y0=ys[j], y1=ys[j + 1], area=math.dist((xa, za), (xb, zb)) * (ys[j + 1] - ys[j]))
    xs = [2.5 + h * k for k in range(int(round(275 / h)) + 1)]; zb_ = [25.0 + h * k for k in range(int(round(25 / h)) + 1)]
    if rib_pitch:
        st = sec(rib_t)
        for y in ry:                                        # ribs = grating bars inside the box (front to back)
            for i in range(len(xs) - 1):
                for k in range(len(zb_) - 1):
                    n1 = node(xs[i], y, zb_[k]); n2 = node(xs[i + 1], y, zb_[k]); n3 = node(xs[i + 1], y, zb_[k + 1]); n4 = node(xs[i], y, zb_[k + 1])
                    etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, st)
                    elems[etag[0]] = dict(kind="rib", part="rib", t=rib_t, xm=(xs[i] + xs[i + 1]) / 2, ym=y, zm=(zb_[k] + zb_[k + 1]) / 2, area=h * h)
    st5 = sec(5.0)
    for yc in Y_CAP:                                        # end plates: back box (x 2.5-47.5, z 2.5-50) + box band (x 47.5-277.5, z 25-50)
        for (x0, x1, z0, z1) in ((2.5, 47.5, 2.5, 50.0), (47.5, 277.5, 25.0, 50.0)):
            xg = [x0 + h * k for k in range(int(round((x1 - x0) / h)) + 1)]; zg = [z0 + h * k for k in range(int(round((z1 - z0) / h)) + 1)]
            for i in range(len(xg) - 1):
                for k in range(len(zg) - 1):
                    n1 = node(xg[i], yc, zg[k]); n2 = node(xg[i + 1], yc, zg[k]); n3 = node(xg[i + 1], yc, zg[k + 1]); n4 = node(xg[i], yc, zg[k + 1])
                    etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, st5)
                    elems[etag[0]] = dict(kind="cap", part="end plate", t=5.0, xm=(xg[i] + xg[i + 1]) / 2, ym=yc, zm=(zg[k] + zg[k + 1]) / 2, area=h * h)
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
    return nodes, elems, pin_nodes, ys

def udl(q): return lambda e: q * 250.0 / 275.0
def patch(P, xc, yc, a=200.0, b=200.0):
    def f(e):
        ox = max(0.0, min(e["x1"], xc + a / 2) - max(e["x0"], xc - a / 2)); oy = max(0.0, min(e["y1"], yc + b / 2) - max(e["y0"], yc - b / 2))
        return P / (a * b) * ox * oy / e["area"] if e["area"] else 0.0
    return f
CASES = {"ULS 4 kN front, mid-span": (patch(6000.0, 177.5, 618.0), 1.35), "ULS 4 kN centre, mid-span": (patch(6000.0, 140.0, 618.0), 1.35),
         "ULS 4 kN front, at the end": (patch(6000.0, 177.5, 125.0), 1.35), "ULS crowd": (lambda e: 1.5 * udl(7.5e-3)(e), 1.35),
         "SLS 4 kN front, mid-span": (patch(4000.0, 177.5, 618.0), 1.0), "SLS crowd": (udl(7.5e-3), 1.0),
         "SLS person 1 kN at the nosing": (patch(1000.0, 227.5, 618.0, 100.0, 100.0), 1.0)}
OPTIONS = {
    "U1 your box: top 3, mid 2, grating ribs 3 at 20": dict(t_top=3.0, t_mid=2.0, rib_t=3.0, rib_pitch=20.0),
    "U2 your box: top 3, mid 2, ribs 2 at 60": dict(t_top=3.0, t_mid=2.0, rib_t=2.0, rib_pitch=60.0),
    "U3 your box: top 2, mid 2, ribs 2 at 60": dict(t_top=2.0, t_mid=2.0, rib_t=2.0, rib_pitch=60.0),
}
def mass(cfg, L=1195.0):
    A = 537.5 + 237.5 - 27.5 * 5 + 275 * cfg["t_top"] + 275 * cfg["t_mid"] + 2 * 25 * 2.7
    n_r = int((Y_CAP[1] - Y_CAP[0]) / cfg["rib_pitch"]) if cfg["rib_pitch"] else 0
    return (A * L + n_r * cfg["rib_t"] * 25 * 275 + 2 * (45 * 47.5 + 230 * 25) * 5) * 2.7e-6

def solve(cfg, load_fn, swf, label=""):
    nodes, elems, pins, ys = build(**cfg)
    for pn, (c, b) in pins.items(): ops.fix(b, 1, 1 if pn == "L_rear" else 0, 1, 0, 0, 0)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    F = {}
    for et, e in elems.items():
        f = RHO_W * e["t"] * e["area"] * swf + ((load_fn(e) or 0.0) * e["area"] if e["part"] == "top plate" else 0.0)
        for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + f / 4
    for n, fz in F.items(): ops.load(n, 0.0, 0.0, -fz, 0.0, 0.0, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack"); ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0); ops.analysis("Static"); ok = ops.analyze(1); ops.reactions()
    res = dict(label=label, ok=ok, eq=[round(sum(ops.nodeReaction(b)[2] for c, b in pins.values()), 1), round(sum(F.values()), 1)])
    ymid = min(ys, key=lambda y: abs(y - 618.0))
    def uz(x, z): return ops.nodeDisp(nodes[min(nodes, key=lambda k: abs(k[0] - x) + abs(k[1] - ymid) + abs(k[2] - z))])[2]
    res["nosing_mid"] = uz(277.5, 50.0); res["back_mid"] = uz(2.5, 50.0); res["uz_min"] = min(ops.nodeDisp(t)[2] for t in nodes.values())
    res["twist_deg"] = math.degrees(math.atan2(res["back_mid"] - res["nosing_mid"], 275.0))
    worst, by_part = (0, None), {}
    for et, e in elems.items():
        if e["kind"] == "cap" or not (40 < e["ym"] < 1190): continue
        r = ops.eleResponse(et, "stresses")
        if not r: continue
        t = e["t"]; vm = 0.0
        for gp in np.array(r).reshape(-1, 8):
            N11, N22, N12, M11, M22, M12 = gp[:6]
            for s in (1, -1):
                a_ = N11 / t + s * 6 * M11 / t ** 2; b_ = N22 / t + s * 6 * M22 / t ** 2; c_ = N12 / t + s * 6 * M12 / t ** 2
                vm = max(vm, math.sqrt(a_ * a_ + b_ * b_ - a_ * b_ + 3 * c_ * c_))
        rec = (round(vm, 1), e["part"], round(e["xm"], 1), round(e["ym"], 1), round(e["zm"], 1))
        if vm > worst[0]: worst = (vm, rec)
        if vm > by_part.get(e["part"], (0,))[0]: by_part[e["part"]] = rec
    res["vm"] = worst[1]; res["util"] = worst[0] / FD; res["by_part"] = by_part
    res["pins"] = {n: [round(v, 1) for v in ops.nodeReaction(b)[:3]] for n, (c, b) in pins.items()}
    return res

if __name__ == "__main__":
    names = [n for n in OPTIONS if not sys.argv[1:] or n in sys.argv[1:]]
    out = json.load(open("tread_ubox.json")) if os.path.exists("tread_ubox.json") else {}
    for name in names:
        cfg = OPTIONS[name]; rr = {}
        for cn, (fn, swf) in CASES.items():
            r = solve(cfg, fn, swf, cn); rr[cn] = r
            print(f"{name[:42]:<42} {cn:<30} ok={r['ok']} eq {r['eq']} nosing {r['nosing_mid']:6.2f} min {r['uz_min']:6.2f} twist {r['twist_deg']:5.2f} vm {r['vm']} u {r['util']:.2f}", flush=True)
        out[name] = dict(cfg=cfg, mass_kg=mass(cfg), cases=rr)
        json.dump(out, open("tread_ubox.json", "w"), indent=1, default=str)
