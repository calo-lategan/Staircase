"""Parametric shell FE of an L-envelope step (owner correction 26 Sep 2026).
Envelope (tread-local mm): x 0 (back face) -> 280 (front face), y along the span, z 0 (underside of the back member) -> 50
(walking surface).  Available: the 25 mm walking-surface zone z 25-50 over the full 280, plus a 50 x 50 back member x 0-50,
z 0-50.  Keep-out: x 50-280, z 0-25 (an optional front lip may be switched on as an owner option).
End plates (xz-plane shells, 8 mm, full 280 x 50) at y 17.5 / 1212.5; pins as in the final model (rear x 25 z 12.5,
front x 225 z 37.5), each pin a beam from the end-plate node to the rail-wall bearing, rigid links to the end-plate
nodes within the pin radius (same scheme as v2/final/tread_grating.py / tread_box2.py, which balance exactly).

Parts (all ShellMITC4 on one conforming grid, linear elastic, shared nodes = rigid joint):
  box      closed 50 x 50 back member: rear wall, front wall (x 50), bottom, top (= skin level), optional mid web z 25
  skin     slotted top skin z 50 - ts/2 from the box to the nosing (slots explicit: rows of slots long in y)
  ribs     transverse ribs (xz-plane webs) at pitch p_r from the box front wall to the nosing, bottom bulb as a beam
           option rib_through_box: the rib continues inside the box as a full-depth diaphragm
  nosing   55 x 25 closed nosing: front wall, inner wall at x 225, bottom plate, top = solid skin (contrast strip)
  grating  (mode 'grating') no skin in the open zone: ribs become bearing bars with a serrated top flange (beam),
           longitudinal cross rods (beams, translation-only link to each bar = swaged / press-locked, no moment)
Loads on the solid top material only (a 200 x 200 test pad bears on metal, not on the holes)."""
import math, json, time
import numpy as np
import openseespy.opensees as ops

E, NU = 70000.0, 0.3
G = E / (2 * (1 + NU))
RHO = 2.70e-9
RHO_W = RHO * 9810.0
Y0, Y1 = 17.5, 1212.5
L_SPAN_PINS = 1226.5 - 10.75           # 1,215.75 between pin bearings


def pins_def(d=16.0):
    return {"L_rear": dict(x=25.0, z=12.5, d=d, y_cap=Y0, y_b=10.75), "L_front": dict(x=225.0, z=37.5, d=d, y_cap=Y0, y_b=10.75),
            "R_rear": dict(x=25.0, z=12.5, d=d, y_cap=Y1, y_b=1226.5), "R_front": dict(x=225.0, z=37.5, d=d, y_cap=Y1, y_b=1226.5)}


DEFAULT = dict(
    mode="skin",            # 'skin' (slotted skin + ribs) or 'grating' (bearing bars + cross rods, no skin)
    tb=3.0, tb_top=3.0, box_mid=False, t_mid=2.0, box_w=50.0,
    ts=2.5,                 # skin thickness
    ws=10.0, wsol=10.0, Lb=15.0, slot_x0=None, slot_x1=None,   # slot width (x), solid strip between rows, bridge at each rib
    p_r=60.0, tr=2.5, rib_through_box=False, bulb=(10.0, 3.0),  # rib pitch, web t, bottom flange b x t (None = none)
    rib_x1=None,            # rib front end (default: nosing inner wall)
    tn=2.5, nose_w=55.0, lip=0.0, t_lip=3.0,                    # nosing walls, width, optional lip below z 25 (owner option)
    t_cap=8.0,
    longs=(),               # extra longitudinal T-stiffeners under the skin: (x, depth, t)
    # grating mode
    bar_top=(10.0, 2.5),    # serrated top flange b x t on each bearing bar
    rods=(),                # x positions of longitudinal cross rods
    rod_d=6.0, rod_z=None,
    pin_d=16.0, h=5.0, hy=10.0,
    bulb_shell=True,
    box_diag=0.0,           # >0: internal diagonal web (t) from the rib-foot node on the box front wall to the rear-top corner        # rib bottom flange as a shell strip (b wide) instead of a beam
)


def _grid(keys, lo, hi, step):
    keys = sorted(set(round(k, 4) for k in keys if lo - 1e-9 <= k <= hi + 1e-9) | {round(lo, 4), round(hi, 4)})
    out = [keys[0]]
    for a, b in zip(keys[:-1], keys[1:]):
        n = max(1, int(math.ceil((b - a) / step - 1e-9)))
        out += [round(a + (b - a) * i / n, 4) for i in range(1, n + 1)]
    return sorted(set(out))


def geometry(D):
    """key coordinates of the section"""
    g = {}
    g["x_r"] = D["tb"] / 2; g["x_f"] = D["box_w"] - D["tb"] / 2; g["z_b"] = D["tb"] / 2
    g["z_top"] = 50.0 - D["ts"] / 2
    g["x_n"] = 280.0 - D["tn"] / 2; g["x_ni"] = 280.0 - D["nose_w"]
    g["z_nb"] = 25.0 + D["tn"] / 2
    bt = D["bulb"][1] if D["bulb"] else 0.0
    g["z_rb"] = 25.0 + bt / 2 if D["bulb"] else 25.0 + D["tr"] / 2
    g["rib_x0"] = g["x_f"]; g["rib_x1"] = D["rib_x1"] or g["x_ni"]
    # rib positions: symmetric about mid-span, first rib half a pitch from the end plate
    n = int(math.floor((Y1 - Y0) / D["p_r"] + 1e-9))
    span = (Y1 - Y0); off = (span - (n - 1) * D["p_r"]) / 2 if n > 0 else span / 2
    g["ribs"] = [round(Y0 + off + k * D["p_r"], 4) for k in range(n)]
    sx0 = D["slot_x0"] if D["slot_x0"] is not None else g["x_f"] + D["tb"] / 2 + 6.0
    sx1 = D["slot_x1"] if D["slot_x1"] is not None else g["x_ni"] - 6.0
    rows = []
    x = sx0
    while x + D["ws"] <= sx1 + 1e-9:
        rows.append((round(x, 4), round(x + D["ws"], 4))); x += D["ws"] + D["wsol"]
    # centre the rows in the available band
    if rows:
        shift = (sx1 - rows[-1][1]) / 2
        rows = [(round(a + shift, 4), round(b + shift, 4)) for a, b in rows]
    g["slot_rows"] = rows
    # slots in y: between ribs, bridge Lb centred on each rib; also a bridge next to the end plates
    ys_slots = []
    edges = [Y0] + g["ribs"] + [Y1]
    for a, b in zip(edges[:-1], edges[1:]):
        ya = a + D["Lb"] / 2; yb = b - D["Lb"] / 2
        if a == Y0: ya = a + max(D["Lb"], 20.0)
        if b == Y1: yb = b - max(D["Lb"], 20.0)
        if yb - ya >= 15.0: ys_slots.append((round(ya, 4), round(yb, 4)))
    g["slot_ys"] = ys_slots
    return g


def open_area(D, g=None):
    g = g or geometry(D)
    if D["mode"] == "grating":
        bt = D["bar_top"][0]
        clear_y = D["p_r"] - bt
        xa, xb = g["x_f"] + D["tb"] / 2, g["x_ni"]
        rods = sorted(D["rods"])
        return clear_y * (xb - xa - len(rods) * D["rod_d"]) * len(g["ribs"]) / (280.0 * (Y1 - Y0))
    a = sum(b - a for a, b in g["slot_rows"]) * sum(b - a for a, b in g["slot_ys"])
    return a / (280.0 * (Y1 - Y0))


def build(D):
    D = {**DEFAULT, **D}
    g = geometry(D)
    ops.wipe(); ops.model("basic", "-ndm", 3, "-ndf", 6)
    tags = {}

    def sec(t):
        t = round(t, 4)
        if t not in tags:
            tags[t] = len(tags) + 1; ops.section("ElasticMembranePlateSection", tags[t], E, NU, t, 0.0)
        return tags[t]
    nodes, ntag, etag, elems, beams = {}, [0], [0], {}, {}

    def node(x, y, z):
        k = (round(x, 4), round(y, 4), round(z, 4))
        if k not in nodes:
            ntag[0] += 1; ops.node(ntag[0], x, y, z); nodes[k] = ntag[0]
        return nodes[k]
    h, hy = D["h"], D["hy"]
    grating = D["mode"] == "grating"
    bt_top = D["bar_top"]
    # ---- grids
    xkeys = [0.0, 280.0, g["x_r"], g["x_f"], g["x_n"], g["x_ni"], 25.0, 225.0, g["rib_x1"]]
    for a, b in g["slot_rows"]: xkeys += [a, b]
    for (xl, dl, tl) in D["longs"]: xkeys.append(xl)
    xkeys += list(D["rods"])
    xs = _grid(xkeys, 0.0, 280.0, h)
    zkeys = [0.0, 50.0, g["z_b"], g["z_top"], 25.0, g["z_rb"], g["z_nb"], 12.5, 37.5]
    if D["lip"]: zkeys.append(25.0 - D["lip"])
    for (xl, dl, tl) in D["longs"]: zkeys.append(g["z_top"] - dl)
    if D["rods"]: zkeys.append(D["rod_z"] if D["rod_z"] is not None else g["z_top"] - 8.0)
    zs = _grid(zkeys, min([0.0] + [25.0 - D["lip"]]), 50.0, h)
    ykeys = [Y0, Y1] + g["ribs"]
    for a, b in g["slot_ys"]: ykeys += [a, b]
    if grating:
        for yr in g["ribs"]: ykeys += [yr - bt_top[0] / 2, yr + bt_top[0] / 2]
    if D["bulb"] and D["bulb_shell"]:
        for yr in g["ribs"]: ykeys += [yr - D["bulb"][0] / 2, yr + D["bulb"][0] / 2]
    ys = _grid(ykeys, Y0, Y1, hy)

    def sub(lst, lo, hi): return [v for v in lst if lo - 1e-9 <= v <= hi + 1e-9]

    def quad(p1, p2, p3, p4, t, info):
        n = [node(*p) for p in (p1, p2, p3, p4)]
        etag[0] += 1; ops.element("ShellMITC4", etag[0], *n, sec(t))
        elems[etag[0]] = dict(t=t, **info)

    def plate_yz(x, z0, z1, t, part, y0=Y0, y1=Y1):
        zz = sub(zs, z0, z1); yy = sub(ys, y0, y1)
        for j in range(len(yy) - 1):
            for k in range(len(zz) - 1):
                quad((x, yy[j], zz[k]), (x, yy[j + 1], zz[k]), (x, yy[j + 1], zz[k + 1]), (x, yy[j], zz[k + 1]), t,
                     dict(part=part, xm=x, ym=(yy[j] + yy[j + 1]) / 2, zm=(zz[k] + zz[k + 1]) / 2, x0=x, x1=x, y0=yy[j], y1=yy[j + 1],
                          area=(yy[j + 1] - yy[j]) * (zz[k + 1] - zz[k]), top=False))

    def plate_xy(z, x0, x1, t, part, hole=None, top=False, y0=Y0, y1=Y1, tfun=None):
        xx = sub(xs, x0, x1); yy = sub(ys, y0, y1)
        for i in range(len(xx) - 1):
            for j in range(len(yy) - 1):
                xm, ym = (xx[i] + xx[i + 1]) / 2, (yy[j] + yy[j + 1]) / 2
                if hole and hole(xm, ym): continue
                tt = tfun(xm, ym) if tfun else t
                if tt is None: continue
                quad((xx[i], yy[j], z), (xx[i + 1], yy[j], z), (xx[i + 1], yy[j + 1], z), (xx[i], yy[j + 1], z), tt,
                     dict(part=part, xm=xm, ym=ym, zm=z, x0=xx[i], x1=xx[i + 1], y0=yy[j], y1=yy[j + 1],
                          area=(xx[i + 1] - xx[i]) * (yy[j + 1] - yy[j]), top=top))

    def plate_xz(y, x0, x1, z0, z1, t, part, zfun=None):
        xx = sub(xs, x0, x1)
        for i in range(len(xx) - 1):
            ztop = z1
            zz = sub(zs, z0, ztop)
            for k in range(len(zz) - 1):
                quad((xx[i], y, zz[k]), (xx[i + 1], y, zz[k]), (xx[i + 1], y, zz[k + 1]), (xx[i], y, zz[k + 1]), t,
                     dict(part=part, xm=(xx[i] + xx[i + 1]) / 2, ym=y, zm=(zz[k] + zz[k + 1]) / 2, x0=xx[i], x1=xx[i + 1], y0=y, y1=y,
                          area=(xx[i + 1] - xx[i]) * (zz[k + 1] - zz[k]), top=False))

    # ---- back box
    plate_yz(g["x_r"], g["z_b"], g["z_top"], D["tb"], "box rear wall")
    plate_yz(g["x_f"], g["z_b"], g["z_top"], D["tb"], "box front wall")
    plate_xy(g["z_b"], g["x_r"], g["x_f"], D["tb"], "box bottom")
    plate_xy(g["z_top"], g["x_r"], g["x_f"], D["tb_top"], "box top", top=True)
    if D["box_mid"]:
        plate_xy(25.0, g["x_r"], g["x_f"], D["t_mid"], "box mid web")
    if D["box_diag"]:
        p0 = (g["x_f"], g["z_rb"]); p1 = (g["x_r"], g["z_top"])
        nseg = max(2, int(round(math.dist(p0, p1) / h)))
        pts = [(p0[0] + (p1[0] - p0[0]) * k / nseg, p0[1] + (p1[1] - p0[1]) * k / nseg) for k in range(nseg + 1)]
        for j in range(len(ys) - 1):
            for k in range(nseg):
                (xa, za), (xb, zb) = pts[k], pts[k + 1]
                quad((xa, ys[j], za), (xa, ys[j + 1], za), (xb, ys[j + 1], zb), (xb, ys[j], zb), D["box_diag"],
                     dict(part="box diagonal web", xm=(xa + xb) / 2, ym=(ys[j] + ys[j + 1]) / 2, zm=(za + zb) / 2, x0=min(xa, xb), x1=max(xa, xb),
                          y0=ys[j], y1=ys[j + 1], area=math.dist(pts[k], pts[k + 1]) * (ys[j + 1] - ys[j]), top=False))
    # ---- nosing (closed 55 x 25), optional lip below z 25 (owner option)
    plate_yz(g["x_n"], g["z_nb"] if not D["lip"] else 25.0 - D["lip"], g["z_top"], D["tn"], "nosing front wall")
    if D["lip"]:
        pass  # front wall above already runs down to 25 - lip (lip thickness taken = tn)
    plate_yz(g["x_ni"], g["z_nb"], g["z_top"], D["tn"], "nosing inner wall")
    plate_xy(g["z_nb"], g["x_ni"], g["x_n"], D["tn"], "nosing bottom")
    plate_xy(g["z_top"], g["x_ni"], g["x_n"], max(D["tn"], D["ts"]), "nosing top", top=True)
    # ---- deck
    rows = g["slot_rows"]; sy = g["slot_ys"]
    def hole(xm, ym):
        return any(a < xm < b for a, b in rows) and any(c < ym < d for c, d in sy)
    if not grating:
        plate_xy(g["z_top"], g["x_f"], g["x_ni"], D["ts"], "skin", hole=hole, top=True)
    else:
        # bar top flanges modelled as shells (b wide, centred on each bar) so the pad bears on them
        def tfl(xm, ym):
            return bt_top[1] if any(abs(ym - yr) < bt_top[0] / 2 for yr in g["ribs"]) else None
        plate_xy(g["z_top"], g["x_f"], g["x_ni"], bt_top[1], "bar top flange", top=True, tfun=tfl)
    for yr in g["ribs"]:
        plate_xz(yr, g["rib_x0"], g["rib_x1"], g["z_rb"], g["z_top"], D["tr"], "rib web" if not grating else "bearing bar web")
        if D["rib_through_box"]:
            plate_xz(yr, g["x_r"], g["x_f"], g["z_b"], g["z_top"], D["tr"], "rib diaphragm in box")
    for (xl, dl, tl) in D["longs"]:
        plate_yz(xl, g["z_top"] - dl, g["z_top"], tl, f"long stiffener x{xl:g}")
    # ---- end plates (full 280 x 50)
    for yc in (Y0, Y1):
        plate_xz(yc, 0.0, 280.0, 0.0, 50.0, D["t_cap"], "end plate")
    # ---- beams: rib bulbs, cross rods
    ops.geomTransf("Linear", 1, 0.0, 0.0, 1.0)      # members along x (local z = global z)
    ops.geomTransf("Linear", 2, 0.0, 0.0, 1.0)      # members along y
    if D["bulb"] and D["bulb_shell"]:
        for yr in g["ribs"]:
            plate_xy(g["z_rb"], g["rib_x0"], g["rib_x1"], D["bulb"][1], "rib bottom flange", y0=yr - D["bulb"][0] / 2, y1=yr + D["bulb"][0] / 2)
    elif D["bulb"]:
        b_, t_ = D["bulb"]; A = b_ * t_; Iy = b_ * t_ ** 3 / 12; Iz = t_ * b_ ** 3 / 12; J = b_ * t_ ** 3 / 3
        for yr in g["ribs"]:
            xx = sub(xs, g["rib_x0"], g["rib_x1"])
            for i in range(len(xx) - 1):
                n1 = node(xx[i], yr, g["z_rb"]); n2 = node(xx[i + 1], yr, g["z_rb"])
                etag[0] += 1; ops.element("elasticBeamColumn", etag[0], n1, n2, A, E, G, J, Iy, Iz, 1)
                beams[etag[0]] = dict(part="rib bulb", A=A, Wy=b_ * t_ ** 2 / 6, Wz=t_ * b_ ** 2 / 6, L=xx[i + 1] - xx[i], xm=(xx[i] + xx[i + 1]) / 2, ym=yr)
    if D["rods"]:
        d = D["rod_d"]; A = math.pi * d * d / 4; I = math.pi * d ** 4 / 64
        zr = D["rod_z"] if D["rod_z"] is not None else g["z_top"] - 8.0
        for xr in D["rods"]:
            rn = []
            for yv in ys:
                k = (round(xr, 4), round(yv, 4), round(zr, 4))
                ntag[0] += 1; ops.node(ntag[0], xr, yv, zr); rn.append(ntag[0])
                # translation-only link to the bar web node (swaged / press-locked crossing) where a bar is
                if any(abs(yv - yr) < 1e-6 for yr in g["ribs"]):
                    ops.equalDOF(node(xr, yv, zr), ntag[0], 1, 2, 3)
            for i in range(len(rn) - 1):
                etag[0] += 1; ops.element("elasticBeamColumn", etag[0], rn[i], rn[i + 1], A, E, G, 2 * I, I, I, 2)
                beams[etag[0]] = dict(part="cross rod", A=A, Wy=math.pi * d ** 3 / 32, Wz=math.pi * d ** 3 / 32, L=ys[i + 1] - ys[i], xm=xr, ym=(ys[i] + ys[i + 1]) / 2)
            # rod ends into the end plates (pinned)
            ops.equalDOF(node(xr, Y0, zr), rn[0], 1, 2, 3); ops.equalDOF(node(xr, Y1, zr), rn[-1], 1, 2, 3)
    # ---- pins
    pin_nodes = {}
    for name, p in pins_def(D["pin_d"]).items():
        c = node(p["x"], p["y_cap"], p["z"]); ntag[0] += 1; ops.node(ntag[0], p["x"], p["y_b"], p["z"]); b = ntag[0]
        d = p["d"]; A = math.pi * d * d / 4; I = math.pi * d ** 4 / 64
        etag[0] += 1; ops.geomTransf("Linear", 3 + etag[0], 0.0, 0.0, 1.0)
        ops.element("elasticBeamColumn", etag[0], c, b, A, E, G, 2 * I, I, I, 3 + etag[0])
        for (kx, ky, kz), tg in list(nodes.items()):
            if tg != c and abs(ky - p["y_cap"]) < 1e-6 and math.hypot(kx - p["x"], kz - p["z"]) <= d / 2 + 1e-6:
                etag[0] += 1; ops.geomTransf("Linear", 100000 + etag[0], 0.0, 1.0, 0.0)
                ops.element("elasticBeamColumn", etag[0], c, tg, 1000.0, E * 100, G * 100, 1e6, 1e6, 1e6, 100000 + etag[0])
        pin_nodes[name] = (c, b)
    return D, g, nodes, elems, beams, pin_nodes, ys


def mass(D, elems=None, beams=None):
    """mass from the model (shell mid-surface areas x t + beams) - kg"""
    m = sum(e["t"] * e["area"] for e in elems.values()) + sum(b["A"] * b["L"] for b in beams.values())
    return m * RHO * 1e3


def solve(D, load, swf=1.0, label="", want_modes=False):
    """load: ('patch', P, xc, yc, a, b) | ('udl', q) | ('none',)"""
    D, g, nodes, elems, beams, pins, ys = build(D)
    for pn, (c, b) in pins.items():
        ops.fix(b, 1, 1 if pn == "L_rear" else 0, 1, 0, 0, 0)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    F = {}
    for et, e in elems.items():
        f = RHO_W * e["t"] * e["area"] * swf
        for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + f / 4
    for et, b in beams.items():
        f = RHO_W * b["A"] * b["L"] * swf
        for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + f / 2
    tops = [(et, e) for et, e in elems.items() if e["top"]]
    if load[0] == "udl":
        total = load[1] * 250.0 * (Y1 - Y0)
        atot = sum(e["area"] for _, e in tops)
        for et, e in tops:
            for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + total * e["area"] / atot / 4
    elif load[0] == "patch":
        _, P, xc, yc, a, b = load
        ov = []
        for et, e in tops:
            ox = max(0.0, min(e["x1"], xc + a / 2) - max(e["x0"], xc - a / 2)); oy = max(0.0, min(e["y1"], yc + b / 2) - max(e["y0"], yc - b / 2))
            if ox * oy > 0: ov.append((et, ox * oy))
        s = sum(v for _, v in ov)
        for et, v in ov:
            for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + P * v / s / 4
    for n, fz in F.items(): ops.load(n, 0.0, 0.0, -fz, 0.0, 0.0, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack"); ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0); ops.analysis("Static"); ok = ops.analyze(1); ops.reactions()
    res = dict(label=label, ok=ok, n_nodes=len(nodes), n_elems=len(elems) + len(beams))
    res["eq"] = [round(sum(ops.nodeReaction(b)[2] for c, b in pins.values()), 1), round(sum(F.values()), 1)]
    res["uz_min"] = min(ops.nodeDisp(t)[2] for t in nodes.values())
    ymid = min(ys, key=lambda y: abs(y - 615.0))
    def uz(x, z): return ops.nodeDisp(nodes[min(nodes, key=lambda k: abs(k[0] - x) + abs(k[1] - ymid) + abs(k[2] - z))])[2]
    res["front_mid"] = uz(280.0, 50.0); res["back_mid"] = uz(0.0, 50.0)
    res["twist_deg"] = math.degrees(math.atan2(res["back_mid"] - res["front_mid"], 280.0))
    by_part = {}
    for et, e in elems.items():
        r = ops.eleResponse(et, "stresses")
        if not r: continue
        t = e["t"]; vm = 0.0
        for gp in np.array(r).reshape(-1, 8):
            N11, N22, N12, M11, M22, M12 = gp[:6]
            for s in (1, -1):
                a_ = N11 / t + s * 6 * M11 / t ** 2; b_ = N22 / t + s * 6 * M22 / t ** 2; c_ = N12 / t + s * 6 * M12 / t ** 2
                vm = max(vm, math.sqrt(a_ * a_ + b_ * b_ - a_ * b_ + 3 * c_ * c_))
        zone = "end" if (e["ym"] < Y0 + 30 or e["ym"] > Y1 - 30) and e["part"] != "end plate" else "body"
        key = e["part"] + ("" if zone == "body" else " (within 30 of end plate)")
        if e["part"] == "end plate":
            near_pin = any(math.hypot(e["xm"] - p["x"], e["zm"] - p["z"]) < 20 for p in pins_def(D["pin_d"]).values())
            if near_pin: key = "end plate (pin zone, rigid-link peak)"
        if vm > by_part.get(key, (0,))[0]:
            by_part[key] = (round(vm, 1), round(e["xm"], 1), round(e["ym"], 1), round(e["zm"], 1))
    for et, b in beams.items():
        f = ops.eleResponse(et, "localForces")
        s = max(abs(f[0]) / b["A"] + abs(f[4]) / b["Wy"] + abs(f[5]) / b["Wz"], abs(f[6]) / b["A"] + abs(f[10]) / b["Wy"] + abs(f[11]) / b["Wz"])
        if s > by_part.get(b["part"], (0,))[0]:
            by_part[b["part"]] = (round(s, 1), round(b["xm"], 1), round(b["ym"], 1), None)
    res["by_part"] = by_part
    res["pins"] = {n: [round(v, 1) for v in ops.nodeReaction(b)[:3]] for n, (c, b) in pins.items()}
    res["mass_model_kg"] = mass(D, elems, beams)
    res["open_area"] = open_area(D, g)
    if want_modes:
        # lumped mass from self-weight (+ extra), first vertical mode
        pass
    return res


CASES = {
    "ULS 4 kN front, mid-span": (("patch", 6000.0, 180.0, 615.0, 200.0, 200.0), 1.35),
    "ULS 4 kN centre, mid-span": (("patch", 6000.0, 140.0, 615.0, 200.0, 200.0), 1.35),
    "ULS 4 kN back, mid-span": (("patch", 6000.0, 100.0, 615.0, 200.0, 200.0), 1.35),
    "ULS 4 kN front, at the end": (("patch", 6000.0, 180.0, 117.5, 200.0, 200.0), 1.35),
    "ULS crowd": (("udl", 1.5 * 7.5e-3), 1.35),
    "SLS 4 kN front, mid-span": (("patch", 4000.0, 180.0, 615.0, 200.0, 200.0), 1.0),
    "SLS crowd": (("udl", 7.5e-3), 1.0),
    "SLS person 1 kN at the nosing": (("patch", 1000.0, 230.0, 615.0, 100.0, 100.0), 1.0),
}
SCREEN = ["ULS 4 kN front, mid-span", "SLS 4 kN front, mid-span", "SLS crowd", "ULS 4 kN front, at the end"]
LIM = dict(sls4=L_SPAN_PINS / 100, crowd=L_SPAN_PINS / 250, person=10.0)


def run(D, cases=None, verbose=True):
    out = {}
    for cn in (cases or list(CASES)):
        ld, swf = CASES[cn]
        t0 = time.time(); r = solve(D, ld, swf, cn); r["sec"] = round(time.time() - t0, 1); out[cn] = r
        if verbose:
            worst = max(r["by_part"].items(), key=lambda kv: kv[1][0] if "rigid-link" not in kv[0] else 0)
            print(f"  {cn:<32} eq {r['eq']} front {r['front_mid']:7.2f} min {r['uz_min']:7.2f} twist {r['twist_deg']:5.2f}  "
                  f"worst {worst[0]} {worst[1]}  ({r['sec']} s)", flush=True)
    return out


if __name__ == "__main__":
    import sys
    D = dict(DEFAULT)
    r = run(D, SCREEN)
    print(json.dumps({k: dict(by_part=v["by_part"], mass=v["mass_model_kg"], open=v["open_area"]) for k, v in r.items()}, indent=1))
