"""Shell FE of the as-modelled tread (OpenSees ASDShellQ4), tread-local mm: x 0 (back) -> 280 (front), y along the
span, z 0 (bottom) -> 50 (top). Profile mid-surface chain, 5 mm everywhere; end caps (5 mm) at y=17.5 / 1212.5 closing
the back box and the band under the deck (x 47.5-277.5, z 27.5-47.5); four pins as beams from the cap to the rail-wall
bearing points (left y=10.49, right y=1226.5), welded over their pin footprint (rigid spider r <= d/2);
supports: each pin bearing fixed in x and z (y at the left rear only), rotations free.
Load functions receive an element record and return a downward pressure (N/mm2) on that element."""
import math, json, sys
import numpy as np
import openseespy.opensees as ops

E, NU, T = 70000.0, 0.3, 5.0
G = E / (2 * (1 + NU))
RHO_W = 2.70e-9 * 9810.0            # N/mm3 (aluminium 2700 kg/m3)
CHAIN = [(2.5, 2.5), (2.5, 47.5), (277.5, 47.5), (277.5, 2.5), (2.5, 2.5)]      # closed box (bottom plate 3 mm)
SHELL = "ShellMITC4"          # linear MITC4: one linear step is in exact equilibrium (checked)
SEG_NAMES = ["rear wall", "deck", "front web", "bottom plate"]
Y_CAP = (17.5, 1212.5)
Y_BEAR = (10.49, 1226.5)
PINS = {"L_rear": dict(x=25.0, z=12.5, d=10.73, y_cap=17.5, y_b=10.49), "L_front": dict(x=225.0, z=37.5, d=10.0, y_cap=17.5, y_b=10.49),
        "R_rear": dict(x=25.0, z=12.5, d=10.0, y_cap=1212.5, y_b=1226.5), "R_front": dict(x=225.0, z=37.5, d=10.0, y_cap=1212.5, y_b=1226.5)}


def build(h=5.0, hy=5.0, caps=True, yfine=None):
    ops.wipe(); ops.model("basic", "-ndm", 3, "-ndf", 6)
    ops.section("ElasticMembranePlateSection", 1, E, NU, T, 0.0)
    ops.section("ElasticMembranePlateSection", 2, E, NU, 3.0, 0.0)
    nodes = {}
    ntag = [0]

    def node(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in nodes:
            ntag[0] += 1; ops.node(ntag[0], x, y, z); nodes[k] = ntag[0]
        return nodes[k]
    prof, pseg = [], []
    for si, (a, b) in enumerate(zip(CHAIN[:-1], CHAIN[1:])):
        L = math.dist(a, b); n = max(1, int(round(L / h)))
        for k in range(n):
            prof.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)); pseg.append(si)
    if CHAIN[-1] != CHAIN[0]: prof.append(CHAIN[-1])
    else: prof.append(CHAIN[0])
    ny = int(round((Y_CAP[1] - Y_CAP[0]) / hy)); ys = [Y_CAP[0] + (Y_CAP[1] - Y_CAP[0]) * j / ny for j in range(ny + 1)]
    if yfine:                                   # (y_from, y_to, pitch): local refinement band
        a, b, p = yfine
        ys = sorted(set([y for y in ys if not (a < y < b)] + [a + k * p for k in range(int(round((b - a) / p)) + 1)]))
    etag = [0]; elems = {}
    for j in range(ny):
        for i in range(len(prof) - 1):
            (x0, z0), (x1, z1) = prof[i], prof[i + 1]
            n1 = node(x0, ys[j], z0); n2 = node(x0, ys[j + 1], z0); n3 = node(x1, ys[j + 1], z1); n4 = node(x1, ys[j], z1)
            etag[0] += 1; ops.element(SHELL, etag[0], n1, n2, n3, n4, 2 if pseg[i] == 3 else 1)
            elems[etag[0]] = dict(kind="prof", seg=pseg[i], xm=(x0 + x1) / 2, zm=(z0 + z1) / 2, ym=(ys[j] + ys[j + 1]) / 2,
                                  x0=x0, x1=x1, y0=ys[j], y1=ys[j + 1], area=math.dist(prof[i], prof[i + 1]) * (ys[j + 1] - ys[j]))
    if caps:
        g = h              # cap grid = profile pitch: every cap edge node coincides with a profile node (no ties)
        for yc in Y_CAP:
            def quad(x0, x1, z0, z1):
                nx_, nz_ = int(round((x1 - x0) / g)), int(round((z1 - z0) / g))
                for a in range(nx_):
                    for b in range(nz_):
                        xa, xb = x0 + a * g, x0 + (a + 1) * g; za, zb = z0 + b * g, z0 + (b + 1) * g
                        n1 = node(xa, yc, za); n2 = node(xb, yc, za); n3 = node(xb, yc, zb); n4 = node(xa, yc, zb)
                        etag[0] += 1; ops.element(SHELL, etag[0], n1, n2, n3, n4, 1)
                        elems[etag[0]] = dict(kind="cap", xm=(xa + xb) / 2, zm=(za + zb) / 2, ym=yc, area=g * g)
            quad(2.5, 277.5, 2.5, 47.5)
        # hanging cap nodes on profile lines (odd 2.5 mm nodes between two 5 mm profile nodes): tie to the profile line
        prof_keys = set((round(x, 4), round(z, 4)) for x, z in prof)
        for yc in Y_CAP:
            for (kx, ky, kz), tg in list(nodes.items()):
                if abs(ky - yc) > 1e-6 or (kx, kz) in prof_keys:
                    continue
                on = None
                for (a, b) in zip(prof[:-1], prof[1:]):
                    ab = (b[0] - a[0], b[1] - a[1]); L2 = ab[0] ** 2 + ab[1] ** 2
                    s = ((kx - a[0]) * ab[0] + (kz - a[1]) * ab[1]) / L2
                    if 0 < s < 1 and abs((kx - a[0]) * ab[1] - (kz - a[1]) * ab[0]) / math.sqrt(L2) < 1e-6:
                        on = (a, b); break
                if on:
                    ta = nodes[(round(on[0][0], 4), round(yc, 4), round(on[0][1], 4))]
                    ops.equalDOF(ta, tg, 1, 2, 3)
    ops.geomTransf("Linear", 1, 0.0, 0.0, 1.0)
    pin_nodes = {}
    for name, p in PINS.items():
        c = node(p["x"], p["y_cap"], p["z"]); bnode = node(p["x"], p["y_b"], p["z"])
        d = p["d"]; A = math.pi * d * d / 4; I = math.pi * d ** 4 / 64; J = 2 * I
        etag[0] += 1; ops.element("elasticBeamColumn", etag[0], c, bnode, A, E, G, J, I, I, 1)
        # weld over the pin footprint: very stiff short beams from the pin centre to the cap nodes within r <= d/2
        # (elements instead of rigidLink constraints, so no constraint-handler artefacts in the reactions)
        for (kx, ky, kz), tg in list(nodes.items()):
            if tg != c and abs(ky - p["y_cap"]) < 1e-6 and math.hypot(kx - p["x"], kz - p["z"]) <= d / 2 + 1e-6:
                etag[0] += 1
                ops.geomTransf("Linear", 1000 + etag[0], 0.0, 1.0, 0.0)
                ops.element("elasticBeamColumn", etag[0], c, tg, 1000.0, E * 100, G * 100, 1e6, 1e6, 1e6, 1000 + etag[0])
        pin_nodes[name] = (c, bnode)
    return nodes, elems, pin_nodes, prof, ys


def solve(load_fn, h=5.0, hy=5.0, sw_factor=1.0, label="", point_loads=(), yfine=None):
    nodes, elems, pins, prof, ys = build(h, hy, yfine=yfine)
    for name, (c, b) in pins.items():
        ops.fix(b, 1, 1 if name == "L_rear" else 0, 1, 0, 0, 0)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    F = {}
    for et, e in elems.items():
        nd = ops.eleNodes(et)
        f = RHO_W * T * e["area"] * sw_factor + (load_fn(e) or 0.0) * e["area"]
        for n in nd:
            F[n] = F.get(n, 0.0) + f / 4
    for n, fz in F.items():
        ops.load(n, 0.0, 0.0, -fz, 0.0, 0.0, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.algorithm("Linear"); ops.integrator("LoadControl", 1.0); ops.analysis("Static")
    ok = ops.analyze(1)
    ops.reactions()
    res = dict(label=label, ok=ok, n_nodes=len(nodes), n_elems=len(elems), total_load_N=round(sum(F.values()), 1))
    ymid = min(ys, key=lambda y: abs(y - 618.5))

    def disp(x, z, y):
        k = min(nodes, key=lambda kk: abs(kk[0] - x) + abs(kk[1] - y) + abs(kk[2] - z)); return ops.nodeDisp(nodes[k])
    res["uz_mid_front_lip"] = disp(277.5, 47.5, ymid)[2]; res["uz_mid_back"] = disp(2.5, 47.5, ymid)[2]
    res["uz_mid_deck140"] = disp(140.0, 47.5, ymid)[2]; res["ux_mid_deck140"] = disp(140.0, 47.5, ymid)[0]
    res["uz_min"] = min(ops.nodeDisp(t)[2] for t in nodes.values())
    res["twist_mid_deg"] = math.degrees(math.atan2(res["uz_mid_back"] - res["uz_mid_front_lip"], 275.0))
    rows = []
    for et, e in elems.items():
        r = ops.eleResponse(et, "stresses")
        if not r:
            continue
        r = np.array(r).reshape(-1, 8)
        for gp in r:
            N11, N22, N12, M11, M22, M12 = gp[:6]
            for s in (+1, -1):
                s11 = N11 / T + s * 6 * M11 / T ** 2; s22 = N22 / T + s * 6 * M22 / T ** 2; s12 = N12 / T + s * 6 * M12 / T ** 2
                vm = math.sqrt(s11 * s11 + s22 * s22 - s11 * s22 + 3 * s12 * s12)
                rows.append((vm, s11, s22, s12, N11 / T, 6 * M11 / T ** 2, N22 / T, 6 * M22 / T ** 2, et, e["kind"], e.get("seg"),
                             round(e["xm"], 1), round(e["ym"], 1), round(e["zm"], 1), s))
    rows.sort(key=lambda r: -r[0])
    body = [w for w in rows if w[9] == "prof" and 40 < w[12] < 1190]
    res["vm_max_all"] = rows[0]
    res["vm_max_body"] = body[0]
    by_seg = {}
    for w in body:
        by_seg.setdefault(SEG_NAMES[w[10]], w)
    res["vm_max_by_segment"] = by_seg
    res["pins"] = {n: [round(v, 1) for v in ops.nodeReaction(b)[:3]] for n, (c, b) in pins.items()}
    res["_rows"] = rows
    return res


def udl_fn(q, trib=305.2 / 280.0):
    return lambda e: q * trib if e["kind"] == "prof" and e.get("seg") == 3 else 0.0


def patch_fn(P, xc, yc, a=200.0, b=200.0):
    """P (N) spread over a x b centred at (xc, yc) on the deck, by overlap area with each deck element"""
    def f(e):
        if e["kind"] != "prof" or e.get("seg") != 3:
            return 0.0
        ox = max(0.0, min(e["x1"], xc + a / 2) - max(e["x0"], xc - a / 2)) if e["x1"] > e["x0"] else max(0.0, min(e["x0"], xc + a / 2) - max(e["x1"], xc - a / 2))
        oy = max(0.0, min(e["y1"], yc + b / 2) - max(e["y0"], yc - b / 2))
        return P / (a * b) * ox * oy / e["area"] if e["area"] else 0.0
    return f


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "udl_char"
    if case == "udl_char":
        r = solve(udl_fn(7.5e-3), label="crowd 7.5 kN/m2 (char) + self weight")
    elif case == "patch_mid_char":
        r = solve(patch_fn(4000.0, 140.0, 618.5), label="4 kN on 200x200 at mid-span, mid-depth (char) + SW")
    r.pop("_rows", None)
    print(json.dumps(r, indent=1, default=str))
