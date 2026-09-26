"""Side frame of the FINAL standard stair (2D X-Z, OpenSees, 3 DOF/node), one side at a time, all geometry measured
(frame_geometry_final.json): lower rail (hooked on the base axle and the top axle), upper rail (no own support),
6 treads as pinned links rear pin (lower rail) -> front pin (upper rail) loaded with the tread-FE pin forces,
poles through the rail webs (slot = horizontal restraint only; vertical sliding; latch pins ignored),
handrail frame: poles -> handrail H04 via brackets and top rail K05 via top posts (pivot = pin).
Supports: base axle and top axle pinned (hooks); variant 'base_slides' frees the base horizontally."""
import json, math, sys
import numpy as np
import openseespy.opensees as ops

E = 70000.0
G = json.load(open("frame_geometry_final.json"))
SEC = {  # gross sections (measured): A, I in-plane (bending in the side plane), W top/bottom for info
    "Lo_L": dict(A=375.0, I=21615.0), "Up_L": dict(A=375.0, I=21615.0),
    "Lo_R": dict(A=325.0, I=None), "Up_R": dict(A=275.0, I=9891.0),
    "pole_L": dict(A=40 * 25.0, I=40 * 25.0 ** 3 / 12), "pole_R": dict(A=30 * 25.0, I=30 * 25.0 ** 3 / 12),
    "lower_L": dict(A=50 * 25.0, I=50 * 25.0 ** 3 / 12), "lower_R": dict(A=52.84 * 25.0, I=52.84 * 25.0 ** 3 / 12),
    "U25": dict(A=325.0, I=18948.0),     # handrail H04 / top rail K05: U 25x25x5 (web vertical -> weak value, conservative)
    "bracket": dict(A=15 * 5.0, I=5 * 15.0 ** 3 / 12), "link": dict(A=1e5, I=1e8),
}
# U 25x25x5 inverted (Lo_R): web 25x5 at top, walls 5x20
def usec(W, H, t, web_top):
    rects = [(0, H - t, W, H), (0, 0, t, H - t), (W - t, 0, W, H - t)] if web_top else [(0, 0, W, t), (0, t, t, H), (W - t, t, W, H)]
    A = sum((x1 - x0) * (z1 - z0) for x0, z0, x1, z1 in rects); zc = sum((x1 - x0) * (z1 - z0) * (z0 + z1) / 2 for x0, z0, x1, z1 in rects) / A
    I = sum((x1 - x0) * (z1 - z0) ** 3 / 12 + (x1 - x0) * (z1 - z0) * ((z0 + z1) / 2 - zc) ** 2 for x0, z0, x1, z1 in rects)
    return A, I, zc
A_, I_, _ = usec(25, 25, 5, True); SEC["Lo_R"] = dict(A=A_, I=I_)

VERTICAL_AT_LOWER, VERTICAL_AT_UPPER = True, False
TREADS = [dict(i=i, back=9508.8 - 250 * i, z0=175.0 * i) for i in range(6)]
AXLE_BASE = (9636.1, -89.4); AXLE_TOP = (8135.8, 960.6)


def build(side, pins_by_tread, base_slides=False, bracket_rigid=True):
    g = G[side]
    ops.wipe(); ops.model("basic", "-ndm", 2, "-ndf", 3)
    ops.geomTransf("Linear", 1)
    nodes = []; ntag = [0]; etag = [0]; els = {}
    def node(x, z):
        ntag[0] += 1; ops.node(ntag[0], x, z); nodes.append((ntag[0], x, z)); return ntag[0]
    def beam(i, j, sec, tag):
        etag[0] += 1; s = SEC[sec]; ops.element("elasticBeamColumn", etag[0], i, j, s["A"], E, s["I"], 1); els[etag[0]] = dict(tag=tag, sec=sec, i=i, j=j)
    def truss(i, j, A, tag):
        etag[0] += 1; ops.uniaxialMaterial("Elastic", 100000 + etag[0], E); ops.element("Truss", etag[0], i, j, A, 100000 + etag[0]); els[etag[0]] = dict(tag=tag, sec="truss", i=i, j=j)
    lo, up = g["rail_lo"], g["rail_up"]
    rails = {}
    for key, r, sec in (("lo", lo, "Lo_" + side), ("up", up, "Up_" + side)):
        a, b = np.array(r["a"]), np.array(r["b"]); u = (b - a) / np.linalg.norm(b - a)
        rails[key] = dict(a=a, b=b, u=u, L=np.linalg.norm(b - a), sec=sec, stations={})
    # stations on each rail: projections of pins, pole crossings, ends, and a 25 mm fill
    def proj(r, p):
        return float((np.array(p) - r["a"]) @ r["u"])
    pts = {"lo": set([0.0, rails["lo"]["L"]]), "up": set([0.0, rails["up"]["L"]])}
    for t in TREADS:
        rear = (t["back"] + 25.0, t["z0"] + 12.5); front = (t["back"] + 225.0, t["z0"] + 37.5)
        pts["lo"].add(round(proj(rails["lo"], rear), 3)); pts["up"].add(round(proj(rails["up"], front), 3))
    poles = g["poles"]
    for p in poles:
        for key in ("lo", "up"):
            r = rails[key]
            # crossing of the vertical pole line x = p.x with the rail axis
            s = (p["x"] - r["a"][0]) / r["u"][0]
            if 0 <= s <= r["L"]: pts[key].add(round(s, 3))
    for key in ("lo", "up"):
        r = rails[key]; ss = sorted(pts[key]); full = []
        for s0, s1 in zip(ss[:-1], ss[1:]):
            n = max(1, int(math.ceil((s1 - s0) / 25.0)))
            full += [s0 + (s1 - s0) * k / n for k in range(n)]
        full.append(ss[-1])
        tags = []
        for s in full:
            xy = r["a"] + r["u"] * s; tg = node(xy[0], xy[1]); r["stations"][round(s, 3)] = tg; tags.append((s, tg))
        for (s0, t0), (s1, t1) in zip(tags[:-1], tags[1:]):
            beam(t0, t1, r["sec"], f"rail_{key}")
        r["tags"] = tags
    def at(key, s):
        r = rails[key]; best = min(r["tags"], key=lambda st: abs(st[0] - s)); return best[1]
    # supports via hooks: rigid links from the lower-rail ends to the axle centres
    nb = node(*AXLE_BASE); nt = node(*AXLE_TOP)
    beam(at("lo", 0.0), nb, "link", "hook_base"); beam(at("lo", rails["lo"]["L"]), nt, "link", "hook_top")
    ops.fix(nb, 0 if base_slides else 1, 1, 0); ops.fix(nt, 1, 1, 0)
    # treads: pinned links rear -> front with rigid offsets from the rail axes to the pin points
    link_tags = []
    for t in TREADS:
        rear = (t["back"] + 25.0, t["z0"] + 12.5); front = (t["back"] + 225.0, t["z0"] + 37.5)
        nr, nf = node(*rear), node(*front)
        beam(at("lo", proj(rails["lo"], rear)), nr, "link", "offset"); beam(at("up", proj(rails["up"], front)), nf, "link", "offset")
        # the tread end as a two-pin link (truss) between the pins; release rotations at the pin points
        nr2, nf2 = node(*rear), node(*front)
        ops.equalDOF(nr, nr2, 1, 2); ops.equalDOF(nf, nf2, 1, 2)
        truss(nr2, nf2, 1e4, f"tread{t['i']}")
        link_tags.append((t["i"], nr, nf))
        # rotational stability of nr2/nf2 (truss nodes have a free rotation DOF): fix it
        ops.fix(nr2, 0, 0, 1); ops.fix(nf2, 0, 0, 1)
    # poles: vertical beams from the lower-part bottom to the top post; slot connections at the rail crossings
    pole_info = []
    hr = {h["mat"][:3]: h for h in g["hand_rails"]}
    H04, K05 = hr["H04"], hr["K05"]
    def line_z(h, x):
        (x0, z0), (x1, z1) = h["a"], h["b"]; return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    hr_nodes = {"H04": [], "K05": []}
    for p in poles:
        x = p["x"]
        crossings = {}
        for key in ("lo", "up"):
            r = rails[key]; s = (x - r["a"][0]) / r["u"][0]
            if 0 <= s <= r["L"]: crossings[key] = (s, r["a"][1] + r["u"][1] * s)
        zb = min(p["zlo"], crossings.get("lo", (0, p["zlo"]))[1] - 60.0)
        zH, zK = line_z(H04, x), line_z(K05, x)
        levels = sorted(set([round(zb, 3), round(p["zhi"], 3), round(zH, 3), round(zK, 3)] + [round(c[1], 3) for c in crossings.values()]))
        ptags = [(z, node(x, z)) for z in levels]
        for (z0, t0), (z1, t1) in zip(ptags[:-1], ptags[1:]):
            beam(t0, t1, "pole_" + side, "pole")
        def pnode(z): return min(ptags, key=lambda zt: abs(zt[0] - z))[1]
        for key, (s, zc) in crossings.items():
            # slot: horizontal restraint; the latch pins (O2) hold the pole vertically at the LOWER web only
            if key == "lo" and VERTICAL_AT_LOWER: ops.equalDOF(at(key, s), pnode(zc), 1, 2)
            elif key == "up" and VERTICAL_AT_UPPER: ops.equalDOF(at(key, s), pnode(zc), 1, 2)
            else: ops.equalDOF(at(key, s), pnode(zc), 1)
        # handrail (bracket) and top rail (top post pivot)
        hH = node(x, zH); hK = node(x, zK)
        if bracket_rigid: ops.equalDOF(pnode(zH), hH, 1, 2, 3)       # bracket: rigid in the side plane (upper bound)
        else: ops.equalDOF(pnode(zH), hH, 1, 2)                      # bracket: pinned (lower bound)
        ops.equalDOF(pnode(zK), hK, 1, 2)                    # top-post pivot pin
        hr_nodes["H04"].append((x, hH)); hr_nodes["K05"].append((x, hK))
        pole_info.append(dict(x=x, crossings={k: pnode(v[1]) for k, v in crossings.items()}, rails={k: at(k, v[0]) for k, v in crossings.items()}))
    for key in ("H04", "K05"):
        ns = sorted(hr_nodes[key])
        for (x0, t0), (x1, t1) in zip(ns[:-1], ns[1:]):
            beam(t0, t1, "U25", key)
    return dict(rails=rails, link_tags=link_tags, pole_info=pole_info, nb=nb, nt=nt, els=els)


def run(side, pin_forces, factor_sw=1.35, base_slides=False, bracket_rigid=True, label=""):
    """pin_forces: {tread_i: {"rear": (Fx, Fz), "front": (Fx, Fz)}} forces FROM the tread ON the rails (N), per side"""
    m = build(side, pin_forces, base_slides, bracket_rigid)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    for (i, nr, nf) in m["link_tags"]:
        f = pin_forces[i]
        ops.load(nr, f["rear"][0], f["rear"][1], 0.0); ops.load(nf, f["front"][0], f["front"][1], 0.0)
    # self weight of rails, poles, hand rails (lumped at element ends)
    rho_g = 2.70e-9 * 9810.0 * factor_sw
    for et, e in m["els"].items():
        if e["sec"] in ("link", "truss"): continue
        (xi, zi), (xj, zj) = ops.nodeCoord(e["i"]), ops.nodeCoord(e["j"])
        w = rho_g * SEC[e["sec"]]["A"] * math.hypot(xj - xi, zj - zi) / 2
        ops.load(e["i"], 0.0, -w, 0.0); ops.load(e["j"], 0.0, -w, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.algorithm("Linear"); ops.integrator("LoadControl", 1.0); ops.analysis("Static")
    ok = ops.analyze(1); ops.reactions()
    out = dict(label=label, ok=ok, side=side)
    # rail internal forces
    for key in ("lo", "up"):
        r = m["rails"][key]; rows = []
        for et, e in m["els"].items():
            if e["tag"] != f"rail_{key}": continue
            f = ops.eleResponse(et, "localForce")      # [N1 V1 M1 N2 V2 M2]
            xi = ops.nodeCoord(e["i"]); s = float((np.array(xi) - r["a"]) @ r["u"])
            rows.append((s, f[0], f[2], -f[5]))
        rows.sort()
        out[f"rail_{key}"] = rows
    out["links"] = {}
    for et, e in m["els"].items():
        if e["tag"].startswith("tread"):
            out["links"][e["tag"]] = ops.eleResponse(et, "axialForce")[0]
    out["poles"] = []
    for p in m["pole_info"]:
        rec = dict(x=p["x"])
        for key, pn in p["crossings"].items():
            rec[f"slot_{key}_H"] = ops.nodeReaction(pn)[0] if False else None
        out["poles"].append(rec)
    # slot forces = horizontal constraint forces: from the rail node unbalanced force in X
    for p, rec in zip(m["pole_info"], out["poles"]):
        for key, rn in p["rails"].items():
            rec[f"slot_{key}_H"] = ops.nodeUnbalance(rn)[0] if hasattr(ops, "nodeUnbalance") else None
    # pole moments
    pm = []
    for et, e in m["els"].items():
        if e["tag"] == "pole":
            f = ops.eleResponse(et, "localForce"); pm.append((ops.nodeCoord(e["i"])[0], ops.nodeCoord(e["i"])[1], f[0], f[1], f[2], -f[5]))
    out["pole_forces"] = pm
    out["reactions"] = {"base": ops.nodeReaction(m["nb"])[:2], "top": ops.nodeReaction(m["nt"])[:2]}
    out["disp_max"] = max((abs(ops.nodeDisp(t)[1]), t) for t in ops.getNodeTags())
    br = []
    for et, e in m["els"].items():
        if e["tag"] in ("H04", "K05", "bracket"):
            f = ops.eleResponse(et, "localForce"); br.append((e["tag"], ops.nodeCoord(e["i"])[0], f[0], f[2], -f[5]))
    out["handrail_forces"] = br
    return out
