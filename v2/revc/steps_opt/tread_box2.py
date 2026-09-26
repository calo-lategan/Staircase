"""Closed-box step options, shell FE (OpenSees ShellMITC4, linear, exact equilibrium). Corrects tread_fe_box.py, which
loaded the bottom plate (its load functions picked segment 3 after the chain was re-ordered) and computed every stress
with t = 5 mm. Here each plate has its own thickness, loads go on the top plate (deck) only, and stresses use the
element's own t. Optional internal webs (full height, deck to bottom plate). End plates 5 mm at y 17.5 / 1212.5 close
the box; four pins as in the final model (left y_b 10.75, right 1226.5, lever through washer + spacer).
Tread-local mm: x 0 (back) -> 280 (front), y along the span, z 0 (bottom) -> 50 (walking surface).
HAZ: for a welded build (bent sheet + welded seams) the seams are at the four box corners and at the internal webs;
EN 1999-1-1 6082-T6 f_o,haz = 125 MPa -> stresses within 25 mm of a seam are checked against 125/1.1."""
import math, json, sys
import numpy as np
import openseespy.opensees as ops

E, NU = 70000.0, 0.3
G = E / (2 * (1 + NU))
RHO_W = 2.70e-9 * 9810.0
Y_CAP = (17.5, 1212.5)
PINS = {"L_rear": dict(x=25.0, z=12.5, d=10.73, y_cap=17.5, y_b=10.75), "L_front": dict(x=225.0, z=37.5, d=10.0, y_cap=17.5, y_b=10.75),
        "R_rear": dict(x=25.0, z=12.5, d=10.0, y_cap=1212.5, y_b=1226.5), "R_front": dict(x=225.0, z=37.5, d=10.0, y_cap=1212.5, y_b=1226.5)}
FD, FD_HAZ = 250.0 / 1.1, 125.0 / 1.1


def build(t_top, t_bot, t_wall, webs=(), t_web=None, h=2.5, hy=10.0, t_cap=5.0):
    """webs: x positions (on the 2.5 grid) of internal full-height webs"""
    ops.wipe(); ops.model("basic", "-ndm", 3, "-ndf", 6)
    tags = {}
    def sec(t):
        if t not in tags:
            tags[t] = len(tags) + 1; ops.section("ElasticMembranePlateSection", tags[t], E, NU, t, 0.0)
        return tags[t]
    nodes, ntag, etag, elems = {}, [0], [0], {}
    def node(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in nodes:
            ntag[0] += 1; ops.node(ntag[0], x, y, z); nodes[k] = ntag[0]
        return nodes[k]
    x0, x1, z0, z1 = 2.5, 277.5, 2.5, 47.5           # mid-surface box
    ny = int(round((Y_CAP[1] - Y_CAP[0]) / hy)); ys = [Y_CAP[0] + (Y_CAP[1] - Y_CAP[0]) * j / ny for j in range(ny + 1)]
    xs = [x0 + h * k for k in range(int(round((x1 - x0) / h)) + 1)]
    zs = [z0 + h * k for k in range(int(round((z1 - z0) / h)) + 1)]
    plates = [("deck", [(x, z1) for x in xs], t_top), ("bottom", [(x, z0) for x in xs], t_bot),
              ("rear wall", [(x0, z) for z in zs], t_wall), ("front web", [(x1, z) for z in zs], t_wall)]
    for xw in webs:
        plates.append((f"web x{xw:g}", [(xw, z) for z in zs], t_web or t_wall))
    for part, line, t in plates:
        st = sec(t)
        for j in range(ny):
            for i in range(len(line) - 1):
                (xa, za), (xb, zb) = line[i], line[i + 1]
                n1 = node(xa, ys[j], za); n2 = node(xa, ys[j + 1], za); n3 = node(xb, ys[j + 1], zb); n4 = node(xb, ys[j], zb)
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, st)
                elems[etag[0]] = dict(kind="plate", part=part, t=t, xm=(xa + xb) / 2, zm=(za + zb) / 2, ym=(ys[j] + ys[j + 1]) / 2,
                                      x0=min(xa, xb), x1=max(xa, xb), y0=ys[j], y1=ys[j + 1], area=math.dist((xa, za), (xb, zb)) * (ys[j + 1] - ys[j]))
    stc = sec(t_cap)
    for yc in Y_CAP:
        for i in range(len(xs) - 1):
            for k in range(len(zs) - 1):
                n1 = node(xs[i], yc, zs[k]); n2 = node(xs[i + 1], yc, zs[k]); n3 = node(xs[i + 1], yc, zs[k + 1]); n4 = node(xs[i], yc, zs[k + 1])
                etag[0] += 1; ops.element("ShellMITC4", etag[0], n1, n2, n3, n4, stc)
                elems[etag[0]] = dict(kind="cap", part="end plate", t=t_cap, xm=(xs[i] + xs[i + 1]) / 2, zm=(zs[k] + zs[k + 1]) / 2, ym=yc, area=h * h)
    pin_nodes = {}
    ops.geomTransf("Linear", 1, 0.0, 0.0, 1.0)
    for name, p in PINS.items():
        c = node(p["x"], p["y_cap"], p["z"]); b = node(p["x"], p["y_b"], p["z"])
        d = p["d"]; A = math.pi * d * d / 4; I = math.pi * d ** 4 / 64
        etag[0] += 1; ops.element("elasticBeamColumn", etag[0], c, b, A, E, G, 2 * I, I, I, 1)
        for (kx, ky, kz), tg in list(nodes.items()):
            if tg != c and abs(ky - p["y_cap"]) < 1e-6 and math.hypot(kx - p["x"], kz - p["z"]) <= d / 2 + 1e-6:
                etag[0] += 1; ops.geomTransf("Linear", 1000 + etag[0], 0.0, 1.0, 0.0)
                ops.element("elasticBeamColumn", etag[0], c, tg, 1000.0, E * 100, G * 100, 1e6, 1e6, 1e6, 1000 + etag[0])
        pin_nodes[name] = (c, b)
    return nodes, elems, pin_nodes, ys, [x0, x1] + list(webs)


def solve(cfg, load_fn, sw_factor=1.0, label=""):
    nodes, elems, pins, ys, seams = build(**cfg)
    for name, (c, b) in pins.items():
        ops.fix(b, 1, 1 if name == "L_rear" else 0, 1, 0, 0, 0)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    F = {}
    for et, e in elems.items():
        f = RHO_W * e["t"] * e["area"] * sw_factor + ((load_fn(e) or 0.0) * e["area"] if e["part"] == "deck" else 0.0)
        for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + f / 4
    for n, fz in F.items(): ops.load(n, 0.0, 0.0, -fz, 0.0, 0.0, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.algorithm("Linear"); ops.integrator("LoadControl", 1.0); ops.analysis("Static")
    ok = ops.analyze(1); ops.reactions()
    res = dict(label=label, ok=ok, n_nodes=len(nodes))
    Fz_sup = sum(ops.nodeReaction(b)[2] for c, b in pins.values()); res["equilibrium"] = dict(Fz_support=round(Fz_sup, 1), Fz_load=round(sum(F.values()), 1))
    ymid = min(ys, key=lambda y: abs(y - 618.0))
    def uz(x, z, y): k = min(nodes, key=lambda kk: abs(kk[0] - x) + abs(kk[1] - y) + abs(kk[2] - z)); return ops.nodeDisp(nodes[k])[2]
    res["nosing_mid"] = uz(277.5, 47.5, ymid); res["back_mid"] = uz(2.5, 47.5, ymid)
    res["uz_min"] = min(ops.nodeDisp(t)[2] for t in nodes.values())
    res["twist_deg"] = math.degrees(math.atan2(res["back_mid"] - res["nosing_mid"], 275.0))
    worst, worst_haz, by_part = (0, None), (0, None), {}
    for et, e in elems.items():
        r = ops.eleResponse(et, "stresses")
        if not r or not (40 < e["ym"] < 1190): continue
        t = e["t"]
        for gp in np.array(r).reshape(-1, 8):
            N11, N22, N12, M11, M22, M12 = gp[:6]
            for s in (1, -1):
                s11 = N11 / t + s * 6 * M11 / t ** 2; s22 = N22 / t + s * 6 * M22 / t ** 2; s12 = N12 / t + s * 6 * M12 / t ** 2
                vm = math.sqrt(s11 * s11 + s22 * s22 - s11 * s22 + 3 * s12 * s12)
                rec = (round(vm, 1), e["part"], round(e["xm"], 1), round(e["ym"], 1), round(e["zm"], 1), round(N22 / t, 1))
                if vm > worst[0]: worst = (vm, rec)
                if vm > by_part.get(e["part"], (0,))[0]: by_part[e["part"]] = rec
                near = min(abs(e["xm"] - xs_) for xs_ in seams) <= 25.0 or e["part"] in ("rear wall", "front web") or e["part"].startswith("web")
                if near and vm > worst_haz[0]: worst_haz = (vm, rec)
    res["vm_max"] = worst[1]; res["util"] = worst[0] / FD
    res["vm_max_haz"] = worst_haz[1]; res["util_haz"] = worst_haz[0] / FD_HAZ
    res["vm_by_part"] = by_part
    res["pins"] = {n: [round(v, 1) for v in ops.nodeReaction(b)[:3]] for n, (c, b) in pins.items()}
    return res


def udl(q, going=250.0): return lambda e: q * going / 275.0            # crowd on the plan going, spread over the 275 mm deck
def patch(P, xc, yc, a=200.0, b=200.0):
    def f(e):
        ox = max(0.0, min(e["x1"], xc + a / 2) - max(e["x0"], xc - a / 2)); oy = max(0.0, min(e["y1"], yc + b / 2) - max(e["y0"], yc - b / 2))
        return P / (a * b) * ox * oy / e["area"] if e["area"] else 0.0
    return f

CASES = {
    "ULS 4 kN front, mid-span": (patch(6000.0, 177.5, 618.0), 1.35), "ULS 4 kN centre, mid-span": (patch(6000.0, 140.0, 618.0), 1.35),
    "ULS 4 kN front, at the end": (patch(6000.0, 177.5, 125.0), 1.35), "ULS crowd": (lambda e: 1.5 * udl(7.5e-3)(e), 1.35),
    "SLS 4 kN front, mid-span": (patch(4000.0, 177.5, 618.0), 1.0), "SLS crowd": (udl(7.5e-3), 1.0),
    "SLS person 1 kN at the nosing": (patch(1000.0, 227.5, 618.0, 100.0, 100.0), 1.0),
}
OPTIONS = {
    "B1 box 5 top / 3 bottom / 5 walls": dict(t_top=5.0, t_bot=3.0, t_wall=5.0),
    "B2 box 4 / 2 / 3, one mid web 3": dict(t_top=4.0, t_bot=2.0, t_wall=3.0, webs=(140.0,), t_web=3.0),
    "B3 box 3 / 2 / 3, one mid web 3": dict(t_top=3.0, t_bot=2.0, t_wall=3.0, webs=(140.0,), t_web=3.0),
    "B4 box 3 / 2 / 2, two webs 2": dict(t_top=3.0, t_bot=2.0, t_wall=2.0, webs=(95.0, 185.0), t_web=2.0),
}
def mass_per_step(cfg, L=1195.0):
    A = 275 * cfg["t_top"] + 275 * cfg["t_bot"] + 2 * 45 * cfg["t_wall"] + len(cfg.get("webs", ())) * 45 * (cfg.get("t_web") or cfg["t_wall"])
    return A * L * 2.7e-6 + 2 * 275 * 45 * 5 * 2.7e-6

if __name__ == "__main__":
    only = sys.argv[1:] or list(OPTIONS)
    out = json.load(open("tread_box2.json")) if len(sys.argv) > 1 else {}
    for name in only:
        cfg = OPTIONS[name]; rr = {}
        for cn, (fn, swf) in CASES.items():
            r = solve(cfg, fn, swf, cn); rr[cn] = r
            print(f"{name[:34]:<34} {cn:<30} ok={r['ok']} eq {r['equilibrium']['Fz_support']:.0f}/{r['equilibrium']['Fz_load']:.0f}  nosing {r['nosing_mid']:6.2f}  min {r['uz_min']:6.2f}  "
                  f"twist {r['twist_deg']:5.2f}  vm {r['vm_max'][0]:6.1f} ({r['vm_max'][1]}) u {r['util']:.2f} | HAZ u {r['util_haz']:.2f}", flush=True)
        out[name] = dict(cfg=cfg, mass_kg=mass_per_step(cfg), cases=rr)
        json.dump(out, open("tread_box2.json", "w"), indent=1, default=str)
