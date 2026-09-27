"""Rev C FINAL supports (27 Sep 2026): side frame (2D OpenSees) of the standard 35 deg stair with the Rev C nested
open-channel rails (v2/revc/rails, production box pole) and the FINAL support geometry of this folder:

  * hooks are cut in the LOWER rail itself (owner decision) and sit OVER the axle: saddle = semicircle R 24.5
    (bore D49.0 for the D48.3 tube) whose centre lies on the B_lo far-face line n = 60 (see supports_final.md);
  * base axle moved UP the rail to s = +46 (x 9,468.9, z 0.0): axle centre 125 above the ground (z -125), so a
    real screw jack fits under it (the Rev C axle at z -89.4 was only 35.6 above the ground);
  * top axle on the same n = 60 line at s = 1,656 (x 8,150.0, z 923.5): tube 38 mm clear of the 12 mm landing-bracket
    back plate (landing face x 8,100, IFC);
  * lower rails re-cut: base end s = -30 (was -115.7), top end s = 1,728.5 at the top edge (vertical cut 22 mm uphill
    of the top axle centre; was 1,589.8 R / 1,615.6 L).

Everything else (loads, tread-FE pin forces, poles locked at both rails, handrails) is frame_rails.py unchanged.
Self weight of the frame members is scaled so the unit weighs the owner-accepted 116.6 kg (mass_budget.md OPT).
Writes frame_supports.json. Run: python3 v2/revc/supports_final/frame_supports.py
"""
import json, math, os, sys
sys.dont_write_bytecode = True           # do not leave __pycache__ in v2/revc/rails
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
RAILS = os.path.join(HERE, "..", "rails")
sys.path.insert(0, RAILS)
import openseespy.opensees as ops
import rails_lib as L
import frame_rails as F

TH = math.radians(35.0)
U, NU, REAR0 = F.U, F.NU, F.REAR0
N_SADDLE = 60.0                 # saddle centre on the B_lo far face line (both rails: pin lines coincide)
S_BASE, S_TOP = 46.0, 1656.0    # saddle centres along the lower rail (s from the tread-0 rear pin)
S_END_BASE, S_END_TOP = -30.0, 1728.5


def lo_point(s, n):
    """global (x, z) of lower-rail coordinates (s up the rail, n away from the upper rail)"""
    return REAR0 + U * s - NU * (n - L.C_PIN)


AXLE_BASE = tuple(lo_point(S_BASE, N_SADDLE)); AXLE_TOP = tuple(lo_point(S_TOP, N_SADDLE))
GROUND_Z = -125.0

# ---------------------------------------------------------------- mass target (mass_budget.md, OPT column)
UNIT_KG = 116.6; AXLES_KG = 4.4; STEPS_KG = 6 * 6.35
TREAD_G_N = (3460.5 - 1.5 * 2250.0) / 1.35       # self weight in the tread-FE pin forces (N per tread) -> 6.45 kg


def build(side, base_slides=False, top_free_x=False):
    """copy of frame_rails.build with the lower-rail extent and the hook links moved to the saddle stations"""
    rp = F.rail_props(side); g = F.G[side]
    ops.wipe(); ops.model("basic", "-ndm", 2, "-ndf", 3); ops.geomTransf("Linear", 1)
    nt = [0]; et = [0]; els = {}; SEC = {}
    def node(x, z):
        nt[0] += 1; ops.node(nt[0], float(x), float(z)); return nt[0]
    def beam(i, j, sec, tag):
        et[0] += 1; s = SEC[sec]; ops.element("elasticBeamColumn", et[0], i, j, s["A"], L.E_AL, s["I"], 1); els[et[0]] = dict(tag=tag, sec=sec, i=i, j=j)
    def truss(i, j, A, tag):
        et[0] += 1; ops.uniaxialMaterial("Elastic", 100000 + et[0], L.E_AL); ops.element("Truss", et[0], i, j, A, 100000 + et[0]); els[et[0]] = dict(tag=tag, sec="truss", i=i, j=j)
    SEC.update(F.OTHER); SEC["pole"] = F.POLE_SEC
    rails = {}
    for lev, old in (("lo", g["rail_lo"]), ("up", g["rail_up"])):
        SEC[lev] = dict(A=rp[lev]["A"], I=rp[lev]["I"])
        base, n_axis, n_web = F.rail_line(side, lev, rp[lev])
        if lev == "lo":
            sa, sb = S_END_BASE, S_END_TOP
        else:
            _, sa = F.x_at(base, n_axis, old["a"][0]); _, sb = F.x_at(base, n_axis, old["b"][0])
        rails[lev] = dict(base=base, n_axis=n_axis, n_web=n_web, s0=sa, s1=sb, stations={})
    pins = {"lo": [], "up": []}
    for t in F.TREADS:
        pins["lo"].append(np.array([t["back"] + L.REAR[0], t["z0"] + L.REAR[1]])); pins["up"].append(np.array([t["back"] + L.FRONT[0], t["z0"] + L.FRONT[1]]))
    def s_of(lev, p):
        r = rails[lev]; return float((np.asarray(p) - (r["base"] + NU * r["n_axis"])) @ U)
    pole_cross = []
    for p in g["poles"]:
        rec = dict(x=p["x"], zlo=p["zlo"], zhi=p["zhi"])
        for lev in ("lo", "up"):
            r = rails[lev]; pw, sw = F.x_at(r["base"], r["n_web"], p["x"])
            s_ax = float((pw - (r["base"] + NU * r["n_axis"])) @ U)
            if min(r["s0"], r["s1"]) <= s_ax <= max(r["s0"], r["s1"]): rec[lev] = dict(pw=pw, s=s_ax)
        pole_cross.append(rec)
    s_sad = {"base": s_of("lo", AXLE_BASE), "top": s_of("lo", AXLE_TOP)}
    for lev in ("lo", "up"):
        r = rails[lev]; ss = {round(r["s0"], 3), round(r["s1"], 3)}
        for p in pins[lev]: ss.add(round(s_of(lev, p), 3))
        for pc in pole_cross:
            if lev in pc: ss.add(round(pc[lev]["s"], 3))
        if lev == "lo": ss |= {round(v, 3) for v in s_sad.values()}
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
    beam(at("lo", s_sad["base"]), nb, "link", "hook_base"); beam(at("lo", s_sad["top"]), ntop, "link", "hook_top")
    ops.fix(nb, 0 if base_slides else 1, 1, 0); ops.fix(ntop, 0 if top_free_x else 1, 1, 0)
    link_tags = []
    for t, pr, pf in zip(F.TREADS, pins["lo"], pins["up"]):
        nr, nf = node(*pr), node(*pf)
        beam(at("lo", s_of("lo", pr)), nr, "link", "offset"); beam(at("up", s_of("up", pf)), nf, "link", "offset")
        nr2, nf2 = node(*pr), node(*pf); ops.equalDOF(nr, nr2, 1, 2); ops.equalDOF(nf, nf2, 1, 2)
        truss(nr2, nf2, 1e4, f"tread{t['i']}"); link_tags.append((t["i"], nr, nf)); ops.fix(nr2, 0, 0, 1); ops.fix(nf2, 0, 0, 1)
    hr = {h["mat"][:3]: h for h in g["hand_rails"]}
    def line_z(h, x):
        (x0, z0), (x1, z1) = h["a"], h["b"]; return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    hr_nodes = {"H04": [], "K05": []}
    for pc in pole_cross:
        x = pc["x"]; zH, zK = line_z(hr["H04"], x), line_z(hr["K05"], x)
        cz = {lev: pc[lev]["pw"][1] for lev in ("lo", "up") if lev in pc}
        # the bottom pole has no lower-rail crossing: stop it 40 mm below the upper web (the IFC zlo -414 is below ground)
        zb = cz["lo"] - 40.0 if "lo" in cz else cz["up"] - 40.0
        levels = sorted(set([round(zb, 3), round(pc["zhi"], 3), round(zH, 3), round(zK, 3)] + [round(v, 3) for v in cz.values()]))
        ptags = [(z, node(x, z)) for z in levels]
        for (z0, t0), (z1, t1) in zip(ptags[:-1], ptags[1:]): beam(t0, t1, "pole", "pole")
        def pnode(z): return min(ptags, key=lambda zt: abs(zt[0] - z))[1]
        for lev, zc in cz.items():
            r = rails[lev]; pw = pc[lev]["pw"]
            ra = at(lev, pc[lev]["s"]); off = node(*pw); beam(ra, off, "link", "pole_off_" + lev)
            ops.equalDOF(off, pnode(zc), 1, 2)
        hH = node(x, zH); hK = node(x, zK)
        ops.equalDOF(pnode(zH), hH, 1, 2, 3); ops.equalDOF(pnode(zK), hK, 1, 2)
        hr_nodes["H04"].append((x, hH)); hr_nodes["K05"].append((x, hK))
    for key in ("H04", "K05"):
        ns = sorted(hr_nodes[key])
        for (x0, t0), (x1, t1) in zip(ns[:-1], ns[1:]): beam(t0, t1, "U25", key)
    return dict(rails=rails, link_tags=link_tags, nb=nb, nt=ntop, els=els, SEC=SEC, pins=pins, s_sad=s_sad)


def frame_mass_side(side):
    """kg of the members that carry self weight in the model (rails, poles, top rail, handrail), one side"""
    m = build(side); kg = 0.0
    for e in m["els"].values():
        if e["sec"] in ("link", "truss"): continue
        (xi, zi), (xj, zj) = ops.nodeCoord(e["i"]), ops.nodeCoord(e["j"])
        kg += 2.70e-6 * m["SEC"][e["sec"]]["A"] * math.hypot(xj - xi, zj - zi)
    return kg


def run(side, forces, sw_factor, base_slides=False, top_free_x=False, hx=None):
    """forces: tread pin forces {i: {rear:(Fx,Fz), front:(Fx,Fz)}} on the rails (N, one side);
    sw_factor: multiplier on member self weight (gamma x mass calibration); hx: extra horizontal load per tread (N, +x = downhill)"""
    m = build(side, base_slides, top_free_x)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    for (i, nr, nf) in m["link_tags"]:
        f = forces[i]; h = 0.0 if hx is None else hx / 2
        ops.load(nr, f["rear"][0] + h, f["rear"][1], 0.0); ops.load(nf, f["front"][0] + h, f["front"][1], 0.0)
    rho_g = 2.70e-9 * 9810.0 * sw_factor
    for e in m["els"].values():
        if e["sec"] in ("link", "truss"): continue
        (xi, zi), (xj, zj) = ops.nodeCoord(e["i"]), ops.nodeCoord(e["j"])
        w = rho_g * m["SEC"][e["sec"]]["A"] * math.hypot(xj - xi, zj - zi) / 2
        ops.load(e["i"], 0.0, -w, 0.0); ops.load(e["j"], 0.0, -w, 0.0)
    ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.algorithm("Linear"); ops.integrator("LoadControl", 1.0); ops.analysis("Static")
    ok = ops.analyze(1); ops.reactions()
    out = dict(ok=ok, base=list(ops.nodeReaction(m["nb"])[:2]), top=list(ops.nodeReaction(m["nt"])[:2]))
    # rail internal forces near the saddles (for the hook FE boundary)
    for lev in ("lo", "up"):
        rows = []
        for et, e in m["els"].items():
            if e["tag"] != "rail_" + lev: continue
            f = ops.eleResponse(et, "localForce"); r = m["rails"][lev]
            for nd, N, V, M in ((e["i"], -f[0], f[1], -f[2]), (e["j"], f[3], -f[4], f[5])):
                c = np.array(ops.nodeCoord(nd)); s = float((c - (r["base"] + NU * r["n_axis"])) @ U); rows.append((s, N, V, M))
        out["rail_" + lev] = sorted(rows)
    out["disp_max"] = max(abs(ops.nodeDisp(t)[1]) for t in ops.getNodeTags())
    links = {}
    for et, e in m["els"].items():
        if e["tag"].startswith("tread"): links[int(e["tag"][5:])] = ops.eleResponse(et, "axialForce")[0]
    e_ = np.array(L.LINK) / L.L_LINK
    out["pin0_on_lo"] = list(np.array(forces[0]["rear"]) + (0 if hx is None else np.array([hx / 2, 0.0])) + links[0] * e_)   # tread-0 rear pin -> lower rail (x, z)
    return out


def pins(case, side, only=None, scale=1.0):
    p = F.C[case]["pins"]; r, f = p[f"{side}_rear"], p[f"{side}_front"]
    return {i: ({"rear": (-r[0] * scale, -r[2] * scale), "front": (-f[0] * scale, -f[2] * scale)} if (only is None or i in only)
                else {"rear": (0.0, 0.0), "front": (0.0, 0.0)}) for i in range(6)}


def add(a, b):
    return {i: {k: (a[i][k][0] + b[i][k][0], a[i][k][1] + b[i][k][1]) for k in ("rear", "front")} for i in range(6)}


if __name__ == "__main__":
    OUT = dict(geometry=dict(axle_base=[round(v, 1) for v in AXLE_BASE], axle_top=[round(v, 1) for v in AXLE_TOP],
                             base_axle_height_above_ground=round(AXLE_BASE[1] - GROUND_Z, 1), s_base=S_BASE, s_top=S_TOP,
                             n_saddle=N_SADDLE, lower_rail_ends_s=[S_END_BASE, S_END_TOP],
                             rev_c_axles=dict(base=[9636.1, -89.4], top=[8135.8, 960.6])))
    # ---- mass calibration
    kg = {s: frame_mass_side(s) for s in ("L", "R")}
    target_side = (UNIT_KG - AXLES_KG - STEPS_KG) / 2
    k_mass = target_side / (sum(kg.values()) / 2)
    OUT["mass"] = dict(model_members_kg=dict((s, round(v, 2)) for s, v in kg.items()), target_members_per_side_kg=round(target_side, 2),
                       k_mass=round(k_mass, 3), tread_kg_in_pin_forces=round(TREAD_G_N / 9.81, 2),
                       note="member self weight scaled by k_mass so rails+poles+rails+hardware = 116.6 - 4.4 axles - 38.1 steps")
    # ---- tread pin-force building blocks (one side)
    Gp = {s: pins("ULS crowd", s, scale=TREAD_G_N / 3460.5) for s in ("L", "R")}         # tread self weight, unfactored
    Qsway = 0.10 * 2250.0 / 2 * 1.5                                                       # R176: 10 % of vertical imposed, ULS, per tread per side
    cases = {}; cases_rail = {}
    for side in ("L", "R"):
        for cond, slide in (("held", False), ("slides", True)):
            for only, lab in ((None, "crowd all"), ({0, 1, 2}, "crowd lower 3"), ({3, 4, 5}, "crowd upper 3")):
                base_f = pins("ULS crowd", side, only)
                if only is not None:          # unloaded treads keep 1.35 x self weight
                    base_f = add(base_f, {i: (Gp[side][i] if i not in only else {"rear": (0, 0), "front": (0, 0)}) for i in range(6)})
                    base_f = {i: ({k: (v[0] * (1.35 if i not in only else 1.0), v[1] * (1.35 if i not in only else 1.0)) for k, v in base_f[i].items()}) for i in range(6)}
                for sw_lab, hx in (("", None), (" + sway downhill", Qsway), (" + sway uphill", -Qsway)):
                    o = run(side, base_f, 1.35 * k_mass, base_slides=slide, hx=hx)
                    cases[f"{side} | ULS {lab}{sw_lab} | base {cond}"] = o
                    if hx is None: cases_rail[(side, cond, lab)] = o
            # person 4 kN (ULS 6 kN) at the front of each tread + 1.0 G elsewhere (reversal / top uplift, R180)
            for i in range(6):
                for pc in ("ULS 4 kN patch front, mid-span", "ULS 4 kN patch front, at left end" if side == "L" else "ULS 4 kN patch front, at right end"):
                    f = pins(pc, side, {i}); g1 = {j: (Gp[side][j] if j != i else {"rear": (0, 0), "front": (0, 0)}) for j in range(6)}
                    o = run(side, add(f, g1), 1.0 * k_mass, base_slides=slide)
                    cases[f"{side} | {pc} on tread {i}, 1.0 G | base {cond}"] = o
                    f09 = {j: ({k: (v[0] * 0.9, v[1] * 0.9) for k, v in g1[j].items()}) for j in range(6)}
                    o = run(side, add(f, f09), 0.9 * k_mass, base_slides=slide)
                    cases[f"{side} | {pc} on tread {i}, 0.9 G (EQU) | base {cond}"] = o
            # SLS crowd (ground bearing) and G only
            cases[f"{side} | SLS crowd | base {cond}"] = run(side, pins("SLS crowd 7.5 kN/m2", side), 1.0 * k_mass, base_slides=slide)
            cases[f"{side} | G only | base {cond}"] = run(side, Gp[side], 1.0 * k_mass, base_slides=slide)
    res = {}
    for k, o in cases.items():
        b, t = o["base"], o["top"]
        res[k] = dict(base_H=round(b[0], 1), base_V=round(b[1], 1), top_H=round(t[0], 1), top_V=round(t[1], 1),
                      R_base=round(math.hypot(*b), 1), R_top=round(math.hypot(*t), 1),
                      ang_base=round(math.degrees(math.atan2(b[1], b[0])) % 360, 1), ang_top=round(math.degrees(math.atan2(t[1], t[0])) % 360, 1),
                      disp_max=round(o["disp_max"], 2), ok=o["ok"], pin0=[round(v, 1) for v in o["pin0_on_lo"]])
    OUT["reactions"] = res
    def env(cond, filt=lambda k: "ULS crowd" in k or "ULS" in k and "EQU" not in k):
        rows = {k: v for k, v in res.items() if k.endswith("base " + cond) and filt(k)}
        return dict(R_base=max(v["R_base"] for v in rows.values()), R_top=max(v["R_top"] for v in rows.values()),
                    V_base=max(v["base_V"] for v in rows.values()), H_base=max(abs(v["base_H"]) for v in rows.values()),
                    H_top=max(abs(v["top_H"]) for v in rows.values()), top_uplift=max(0.0, -min(v["top_V"] for v in rows.values())),
                    base_uplift=max(0.0, -min(v["base_V"] for v in rows.values())),
                    ang_base=[min(v["ang_base"] for v in rows.values()), max(v["ang_base"] for v in rows.values())],
                    ang_top=[min((v["ang_top"] + 90) % 360 - 90 for v in rows.values()), max((v["ang_top"] + 90) % 360 - 90 for v in rows.values())])
    OUT["envelope_ULS"] = {c: env(c, lambda k: "ULS" in k and "EQU" not in k) for c in ("held", "slides")}
    OUT["envelope_EQU"] = {c: env(c, lambda k: "EQU" in k) for c in ("held", "slides")}
    # friction cases: base force = slides + a x (held - slides) with H = mu V (per side, crowd all + sway both ways)
    fr = {}
    for mu in (0.3, 0.5):
        best = None
        for k, v in res.items():
            if not (k.endswith("base held") and "ULS crowd" in k): continue
            s = res[k.replace("base held", "base slides")]
            Hh, Vh, Hs, Vs = v["base_H"], v["base_V"], s["base_H"], s["base_V"]
            # find a in [0,1] with |H(a)| = mu V(a)
            a_lo, a_hi = 0.0, 1.0
            f = lambda a: abs(Hs + a * (Hh - Hs)) - mu * (Vs + a * (Vh - Vs))
            if f(1.0) <= 0: a = 1.0
            else:
                for _ in range(60):
                    am = 0.5 * (a_lo + a_hi)
                    if f(am) > 0: a_hi = am
                    else: a_lo = am
                a = a_lo
            H = Hs + a * (Hh - Hs); V = Vs + a * (Vh - Vs)
            Ht = s["top_H"] + a * (v["top_H"] - s["top_H"]); Vt = s["top_V"] + a * (v["top_V"] - s["top_V"])
            rec = dict(case=k.replace(" | base held", ""), a=round(a, 3), H=round(H, 1), V=round(V, 1), R=round(math.hypot(H, V), 1),
                       top_H=round(Ht, 1), top_V=round(Vt, 1), R_top=round(math.hypot(Ht, Vt), 1))
            if best is None or rec["R"] > best["R"]: best = rec
        fr[f"ground mu {mu}"] = best
    OUT["friction"] = fr
    # rail forces at the saddles (crowd all, held, L and R) for the hook FE
    OUT["rail_at_saddle"] = {}
    for key in ("L | ULS crowd all | base held", "R | ULS crowd all | base held", "L | ULS crowd all | base slides", "R | ULS crowd all | base slides"):
        rows = cases[key]["rail_lo"]
        OUT["rail_at_saddle"][key] = {nm: min(rows, key=lambda r: abs(r[0] - s0)) for nm, s0 in (("base", S_BASE + 60), ("top", S_TOP - 60))}
    # ---- rail in-plane stress envelope (crowd cases), conservative: every station checked with the weakest net
    # section of that rail (hole / notch / slot / notch+slot) - same formula as run_rails.inplane_check
    def rail_env(o, side):
        res = {}
        for lev in ("lo", "up"):
            kind = L.RAIL_OF[(side, lev)]; secs = {t: v.props() for t, v in L.sections(kind).items()}
            A = min(p["A"] for p in secs.values()); W = min(min(p["W_tip"], p["W_far"]) for p in secs.values())
            rows = [(r[0], r[1], 0.0, r[-1]) for r in o["rail_" + lev]]
            res[lev] = max(abs(N) / A + abs(M) / W for s_, N, V, M in rows)
        return res
    cmp_ = {}
    for side in ("L", "R"):
        for cond, slide in (("held", False), ("slides", True)):
            for only, lab in ((None, "crowd all"), ({0, 1, 2}, "crowd lower 3"), ({3, 4, 5}, "crowd upper 3")):
                new_ = rail_env(cases_rail[(side, cond, lab)], side)
                old_o = F.run(side, F.pin_forces("ULS crowd", side, only), base_slides=slide)
                old_ = rail_env(old_o, side)
                cmp_[f"{side} | {lab} | base {cond}"] = {lev: dict(new_supports=round(new_[lev], 1), rev_c_rail_run=round(old_[lev], 1)) for lev in ("lo", "up")}
    OUT["rail_inplane_envelope_MPa"] = cmp_
    OUT["rail_inplane_max"] = dict(new=round(max(v[l]["new_supports"] for v in cmp_.values() for l in v), 1),
                                   rev_c=round(max(v[l]["rev_c_rail_run"] for v in cmp_.values() for l in v), 1), fd=round(L.FD, 1))
    json.dump(OUT, open(os.path.join(HERE, "frame_supports.json"), "w"), indent=1)
    print(json.dumps(dict(geometry=OUT["geometry"], mass=OUT["mass"], env=OUT["envelope_ULS"], equ=OUT["envelope_EQU"], friction=fr), indent=1))
