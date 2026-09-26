"""Side frame (2D, OpenSees) of the standard 35 deg stair with the NEW rail sections and positions.
Same model idea, loads and supports as v2/final/side_frame.py (measured geometry, tread-FE pin forces, poles, handrail
frame), with these changes:
  * rail axes = centroid lines of the new sections, offset from the (unchanged) pin lines;
  * pins at the owner's positions (rear 25/12.5, front 225/37.5 in step coords) - same as side_frame.py;
  * poles (rails_lib.POLE: production box 25 x 80 or prototype plate 25 x 55) meet each rail at its mid flange (on the
    pin line). Fold lock at BOTH rails (x and z held at both crossings); lock_upper=False reproduces the poles review's
    lower-only lock, which is a mechanism (reported, not designed for).
"""
import json, math, os, sys
import numpy as np
import openseespy.opensees as ops
import rails_lib as L

G = json.load(open(os.path.join(L.FIN, "frame_geometry_final.json")))
C = json.load(open(os.path.join(L.FIN, "tread2_cases.json")))
TREADS = [dict(i=i, back=9508.8 - 250 * i, z0=175.0 * i) for i in range(6)]
AXLE_BASE = (9636.1, -89.4); AXLE_TOP = (8135.8, 960.6)
TH = math.radians(35.0)
U = np.array([-math.cos(TH), math.sin(TH)]); NU = np.array([math.sin(TH), math.cos(TH)])
REAR0 = np.array([TREADS[0]["back"] + L.REAR[0], L.REAR[1]])
FRONT0 = np.array([TREADS[0]["back"] + L.FRONT[0], L.FRONT[1]])
POLE_SEC = dict(A=L.POLE["A"], I=L.POLE["I_inplane"])
OTHER = {"U25": dict(A=325.0, I=18948.0), "link": dict(A=1e5, I=1e8)}


def rail_props(side):
    p = L.Sec(L.profile()).props()
    return {lev: dict(kind="H", A=p["A"], I=p["Iy"], nc=p["nc"], D=L.D) for lev in ("lo", "up")}


def rail_line(side, lev, rp):
    """rail axis: point + direction; also the web mid-plane offset. Normal offsets are measured with NU (up)."""
    if lev == "lo":
        base = REAR0; n_axis = L.C_PIN - rp["nc"]; n_web = L.C_PIN - L.N_MF
    else:
        base = FRONT0; n_axis = rp["nc"] - L.C_PIN; n_web = L.N_MF - L.C_PIN
    return base, n_axis, n_web


def x_at(base, n_off, x):
    """point on the line base + NU*n_off + U*s with the given x"""
    p0 = base + NU * n_off; s = (x - p0[0]) / U[0]; return p0 + U * s, s


def build(side, base_slides=False, lock_upper=True):
    rp = rail_props(side); g = G[side]
    ops.wipe(); ops.model("basic", "-ndm", 2, "-ndf", 3); ops.geomTransf("Linear", 1)
    nt = [0]; et = [0]; els = {}; SEC = {}
    def node(x, z):
        nt[0] += 1; ops.node(nt[0], float(x), float(z)); return nt[0]
    def beam(i, j, sec, tag):
        et[0] += 1; s = SEC[sec]; ops.element("elasticBeamColumn", et[0], i, j, s["A"], L.E_AL, s["I"], 1); els[et[0]] = dict(tag=tag, sec=sec, i=i, j=j)
    def truss(i, j, A, tag):
        et[0] += 1; ops.uniaxialMaterial("Elastic", 100000 + et[0], L.E_AL); ops.element("Truss", et[0], i, j, A, 100000 + et[0]); els[et[0]] = dict(tag=tag, sec="truss", i=i, j=j)
    SEC.update(OTHER); SEC["pole"] = POLE_SEC
    rails = {}
    for lev, old in (("lo", g["rail_lo"]), ("up", g["rail_up"])):
        SEC[lev] = dict(A=rp[lev]["A"], I=rp[lev]["I"])
        base, n_axis, n_web = rail_line(side, lev, rp[lev])
        pa, sa = x_at(base, n_axis, old["a"][0]); pb, sb = x_at(base, n_axis, old["b"][0])
        rails[lev] = dict(base=base, n_axis=n_axis, n_web=n_web, s0=sa, s1=sb, stations={})
    # stations: pin projections, pole web crossings, ends, 25 mm fill
    pins = {"lo": [], "up": []}
    for t in TREADS:
        rear = np.array([t["back"] + L.REAR[0], t["z0"] + L.REAR[1]]); front = np.array([t["back"] + L.FRONT[0], t["z0"] + L.FRONT[1]])
        pins["lo"].append(rear); pins["up"].append(front)
    def s_of(lev, p):
        r = rails[lev]; return float((np.asarray(p) - (r["base"] + NU * r["n_axis"])) @ U)
    pole_cross = []
    for p in g["poles"]:
        rec = dict(x=p["x"], zlo=p["zlo"], zhi=p["zhi"])
        for lev in ("lo", "up"):
            r = rails[lev]; pw, sw = x_at(r["base"], r["n_web"], p["x"])
            s_ax = float((pw - (r["base"] + NU * r["n_axis"])) @ U)
            if min(r["s0"], r["s1"]) <= s_ax <= max(r["s0"], r["s1"]): rec[lev] = dict(pw=pw, s=s_ax)
        pole_cross.append(rec)
    for lev in ("lo", "up"):
        r = rails[lev]; ss = {round(r["s0"], 3), round(r["s1"], 3)}
        for p in pins[lev]: ss.add(round(s_of(lev, p), 3))
        for pc in pole_cross:
            if lev in pc: ss.add(round(pc[lev]["s"], 3))
        ss = sorted(ss); full = []
        for a, b in zip(ss[:-1], ss[1:]):
            n = max(1, int(math.ceil((b - a) / 25.0))); full += [a + (b - a) * k / n for k in range(n)]
        full.append(ss[-1]); tags = []
        for s in full:
            xy = r["base"] + NU * r["n_axis"] + U * s; tags.append((s, node(*xy)))
        for (s0, t0), (s1, t1) in zip(tags[:-1], tags[1:]): beam(t0, t1, lev, "rail_" + lev)
        r["tags"] = tags
    def at(lev, s): return min(rails[lev]["tags"], key=lambda st: abs(st[0] - s))[1]
    nb = node(*AXLE_BASE); ntop = node(*AXLE_TOP)
    lo = rails["lo"]
    s_base, s_top = (lo["s0"], lo["s1"]) if lo["s0"] < lo["s1"] else (lo["s1"], lo["s0"])
    beam(at("lo", s_base), nb, "link", "hook_base"); beam(at("lo", s_top), ntop, "link", "hook_top")
    ops.fix(nb, 0 if base_slides else 1, 1, 0); ops.fix(ntop, 1, 1, 0)
    link_tags = []
    for t, pr, pf in zip(TREADS, pins["lo"], pins["up"]):
        nr, nf = node(*pr), node(*pf)
        beam(at("lo", s_of("lo", pr)), nr, "link", "offset"); beam(at("up", s_of("up", pf)), nf, "link", "offset")
        nr2, nf2 = node(*pr), node(*pf); ops.equalDOF(nr, nr2, 1, 2); ops.equalDOF(nf, nf2, 1, 2)
        truss(nr2, nf2, 1e4, f"tread{t['i']}"); link_tags.append((t["i"], nr, nf)); ops.fix(nr2, 0, 0, 1); ops.fix(nf2, 0, 0, 1)
    hr = {h["mat"][:3]: h for h in g["hand_rails"]}
    def line_z(h, x):
        (x0, z0), (x1, z1) = h["a"], h["b"]; return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    hr_nodes = {"H04": [], "K05": []}; pole_info = []
    for pc in pole_cross:
        x = pc["x"]; zH, zK = line_z(hr["H04"], x), line_z(hr["K05"], x)
        cz = {lev: pc[lev]["pw"][1] for lev in ("lo", "up") if lev in pc}
        zb = cz["lo"] - 40.0 if "lo" in cz else pc["zlo"]
        levels = sorted(set([round(zb, 3), round(pc["zhi"], 3), round(zH, 3), round(zK, 3)] + [round(v, 3) for v in cz.values()]))
        ptags = [(z, node(x, z)) for z in levels]
        for (z0, t0), (z1, t1) in zip(ptags[:-1], ptags[1:]): beam(t0, t1, "pole", "pole")
        def pnode(z): return min(ptags, key=lambda zt: abs(zt[0] - z))[1]
        info = dict(x=x, rail_nodes={})
        for lev, zc in cz.items():
            r = rails[lev]; pw = pc[lev]["pw"]
            ra = at(lev, pc[lev]["s"]); off = node(*pw); beam(ra, off, "link", "pole_off_" + lev)      # rigid offset axis -> web crossing
            if lev == "lo" or lock_upper: ops.equalDOF(off, pnode(zc), 1, 2)
            else: ops.equalDOF(off, pnode(zc), 1)
            info["rail_nodes"][lev] = off
        hH = node(x, zH); hK = node(x, zK)
        ops.equalDOF(pnode(zH), hH, 1, 2, 3); ops.equalDOF(pnode(zK), hK, 1, 2)
        hr_nodes["H04"].append((x, hH)); hr_nodes["K05"].append((x, hK)); pole_info.append(info)
    for key in ("H04", "K05"):
        ns = sorted(hr_nodes[key])
        for (x0, t0), (x1, t1) in zip(ns[:-1], ns[1:]): beam(t0, t1, "U25", key)
    return dict(rails=rails, link_tags=link_tags, pole_info=pole_info, nb=nb, nt=ntop, els=els, SEC=SEC, pins=pins, rp=rp, s_of=s_of)


def pin_forces(case, side, only=None):
    p = C[case]["pins"]; r, f = p[f"{side}_rear"], p[f"{side}_front"]
    return {i: ({"rear": (-r[0], -r[2]), "front": (-f[0], -f[2])} if (only is None or i in only) else {"rear": (0, 0), "front": (0, 0)}) for i in range(6)}


def run(side, forces, factor_sw=1.35, base_slides=False, lock_upper=True):
    m = build(side, base_slides, lock_upper)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    for (i, nr, nf) in m["link_tags"]:
        f = forces[i]; ops.load(nr, f["rear"][0], f["rear"][1], 0.0); ops.load(nf, f["front"][0], f["front"][1], 0.0)
    rho_g = 2.70e-9 * 9810.0 * factor_sw
    for e in m["els"].values():
        if e["sec"] in ("link", "truss"): continue
        (xi, zi), (xj, zj) = ops.nodeCoord(e["i"]), ops.nodeCoord(e["j"])
        w = rho_g * m["SEC"][e["sec"]]["A"] * math.hypot(xj - xi, zj - zi) / 2
        ops.load(e["i"], 0.0, -w, 0.0); ops.load(e["j"], 0.0, -w, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.algorithm("Linear"); ops.integrator("LoadControl", 1.0); ops.analysis("Static")
    ok = ops.analyze(1); ops.reactions()
    out = dict(ok=ok)
    for lev in ("lo", "up"):
        rows = []
        for et, e in m["els"].items():
            if e["tag"] != "rail_" + lev: continue
            f = ops.eleResponse(et, "localForce")
            ci, cj = ops.nodeCoord(e["i"]), ops.nodeCoord(e["j"])
            r = m["rails"][lev]; p0 = r["base"] + NU * r["n_axis"]
            si, sj = float((np.array(ci) - p0) @ U), float((np.array(cj) - p0) @ U)
            rows.append((si, -f[0], -f[2])); rows.append((sj, f[3], f[5]))   # internal N (tension +), M
        out["rail_" + lev] = rows
    out["links"] = {}
    for et, e in m["els"].items():
        if e["tag"].startswith("tread"): out["links"][int(e["tag"][5:])] = ops.eleResponse(et, "axialForce")[0]
    # pole-to-rail forces (fold lock) = force carried by the rigid offset from the rail axis to the web crossing
    out["pole_rail"] = []
    for et, e in m["els"].items():
        if e["tag"].startswith("pole_off_"):
            gf = ops.eleResponse(et, "globalForce")          # [Fx_i, Fz_i, M_i, Fx_j, Fz_j, M_j] on the element
            out["pole_rail"].append(dict(lev=e["tag"][-2:], x=ops.nodeCoord(e["j"])[0], Fx=gf[3], Fz=gf[4]))
    out["reactions"] = {"base": ops.nodeReaction(m["nb"])[:2], "top": ops.nodeReaction(m["nt"])[:2]}
    out["disp_max"] = max(abs(ops.nodeDisp(t)[1]) for t in ops.getNodeTags())
    out["model"] = m
    return out


def pin_resultants(out, forces):
    """force FROM the tread end ON each rail at every pin, in rail axes (s up the rail, n_up toward the upper rail)"""
    e = np.array(L.LINK) / L.L_LINK; res = []
    for i in range(6):
        N = out["links"][i]                       # tension +
        f = forces[i]
        F_lo = np.array(f["rear"]) + N * e        # tension pulls the rear pin toward the front pin
        F_up = np.array(f["front"]) - N * e
        res.append(dict(i=i, link=N, lo=(float(F_lo @ U), float(F_lo @ NU)), up=(float(F_up @ U), float(F_up @ NU)),
                        lo_abs=float(np.linalg.norm(F_lo)), up_abs=float(np.linalg.norm(F_up))))
    return res
