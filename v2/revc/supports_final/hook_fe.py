"""Plane-stress FE (OpenSees quads, 1 mm pixels) of the rail-end hooks cut in the LOWER rail (owner: hooks are part of
the rails), turned OVER the axle. Rail coordinates (s up the rail, n away from the upper rail), see frame_supports.py.

Each pixel carries the summed thickness of the channel elements that exist there (projected-thickness model):
  pin leg 6 (n 0 .. D - t_web), bulb (A 14 / B 8, n 0..27), web (t_web, full width W), B outer leg 5 (n 29..53), A lip 6 (n D..D+12).
Local cuts at each hook:
  * saddle: semicircle R 24.5 (bore D49.0 +0.3/0 for the D48.3 tube) centred on n = 60, cut through the pin leg + bulb
    (A pin leg trimmed to n 60 over the window); only the pin leg bears on the tube;
  * web window (web removed from y 6, keeping the pin-leg corner): y 6..70 over s_c -45 .. s_c +45 (axle, collar,
    fork jaws) and y 6..32 over the jaw zone beyond (to the keeper side, 58 mm from s_c); the outer web strip with the
    B outer leg / A lip stays and bridges the window; the pole-2 lower web slot (s 106.5-155 L / 109.7-158.4 R) is included;
  * keeper hole D12.5 in the pin leg (pin D12, 0.25 radial clearance, structural: uplift / pull-out) at n 36,
    36 mm UPHILL of the saddle at the base (s 82) and 36 mm DOWNHILL at the top (s 1,620);
  * top end: vertical cut 22 mm uphill of the top axle centre; base: rail stub continues to s = -30 (tread-0 rear pin hole D17 at s 0).
Contact: rigid tube (or keeper pin) with compression-only gap trusses to the bore / hole boundary nodes (radial clearance
0.35 mm on the tube, 0.5 / 2.0 mm on the keeper). The uphill cut face of the model is fixed: the free body then carries
exactly the frame forces (axle reaction and, at the base, the tread-0 rear pin force), so the fixed face carries the
true rail section forces.
Material 6082-T6: E 70,000, nu 0.3, f_o 250, gamma_M1 1.1 -> 227 MPa (elastic von Mises check).
"""
import json, math, os, sys
sys.dont_write_bytecode = True           # do not leave __pycache__ in v2/revc/rails
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import openseespy.opensees as ops
import frame_supports as FS

S_BASE, S_TOP, NC = FS.S_BASE, FS.S_TOP, FS.N_SADDLE
R_BORE = 24.5; R_TUBE = 24.15
KEEPER = {"base": dict(ds=36.0, n=36.0, d=12.5), "top": dict(ds=-36.0, n=36.0, d=12.5)}
PIN_D = 12.0
FD = 250.0 / 1.1
KIND = {"L": dict(D=68.0, tw=7.0, W=115.0, bulb=14.0, outer=None, lip=(6.0, 12.0), slot=(106.45, 155.15)),
        "R": dict(D=60.0, tw=7.0, W=108.0, bulb=8.0, outer=5.0, lip=None, slot=(109.65, 158.35))}
WIN_HALF = 45.0; JAW_REACH = 58.0


def web_removed(side, end, s):
    """width (y) of web removed at station s (window + jaw strip + pole-2 slot at the base)"""
    sc = S_BASE if end == "base" else S_TOP; k = KIND[side]; rem = 0.0
    if abs(s - sc) <= WIN_HALF: rem = 70.0 - 6.0
    elif (end == "base" and sc < s <= sc + JAW_REACH) or (end == "top" and sc - JAW_REACH <= s < sc): rem = 32.0 - 6.0
    if end == "base" and k["slot"][0] <= s <= k["slot"][1]: rem = max(rem, 81.0) if rem < 81 else rem + 26.0 if rem else 81.0
    return rem


def thickness(side, end, s, n):
    k = KIND[side]; D, tw, W = k["D"], k["tw"], k["W"]
    sc = S_BASE if end == "base" else S_TOP
    inwin = abs(s - sc) <= WIN_HALF
    t = 0.0
    leg_bot = NC if inwin else D - tw
    in_saddle = math.hypot(s - sc, n - NC) < R_BORE
    kp = KEEPER[end]; in_keeper = math.hypot(s - (sc + kp["ds"]), n - kp["n"]) < kp["d"] / 2
    if 0 <= n <= leg_bot and not in_saddle and not in_keeper:
        t += 6.0
        if n <= 27.0: t += k["bulb"]
    if D - tw <= n <= D:
        t += W - 6.0 - web_removed(side, end, s)        # the pin-leg corner (6) is counted with the pin leg above
        if not inwin: t += 6.0 if not in_saddle else 0.0
    if k["outer"] and 29.0 <= n <= D - tw: t += k["outer"]
    if k["lip"] and D <= n <= D + k["lip"][1]: t += k["lip"][0]
    if end == "top":
        x = FS.lo_point(s, n)[0]
        if x < FS.AXLE_TOP[0] - 22.0: t = 0.0
    if end == "base" and math.hypot(s - 0.0, n - 12.5) < 8.5: t = 0.0
    return max(t, 0.0)


def solve(side, end, R_on_rail, pin0=None, keeper_load=None, h=1.0, tag=""):
    """R_on_rail: force on the rail from the axle (global x, z, N). keeper_load: force on the rail from the keeper pin
    (global, N) - used alone for uplift / pull-out cases. Returns stresses and contact data."""
    k = KIND[side]; sc = S_BASE if end == "base" else S_TOP
    if end == "base": s0, s1 = -30.0, sc + 90.0
    else: s0, s1 = sc - 90.0, sc + 60.0
    n0, n1 = 0.0, (k["D"] + (k["lip"][1] if k["lip"] else 0.0))
    ns_, nn_ = int(round((s1 - s0) / h)), int(round((n1 - n0) / h))
    T = np.zeros((ns_, nn_))
    for i in range(ns_):
        for j in range(nn_):
            T[i, j] = thickness(side, end, s0 + (i + 0.5) * h, n0 + (j + 0.5) * h)
    U, NU = FS.U, FS.NU
    def glob(s, n): return FS.lo_point(s, n)
    ops.wipe(); ops.model("basic", "-ndm", 2, "-ndf", 2)
    ops.nDMaterial("ElasticIsotropic", 1, 70000.0, 0.3)
    nid = {}
    def node(i, j):
        if (i, j) not in nid:
            tg = len(nid) + 1; x, z = glob(s0 + i * h, n0 + j * h); ops.node(tg, float(x), float(z)); nid[(i, j)] = tg
        return nid[(i, j)]
    eles = {}
    for i in range(ns_):
        for j in range(nn_):
            t = T[i, j]
            if t <= 0: continue
            a, b, c, d = node(i, j), node(i + 1, j), node(i + 1, j + 1), node(i, j + 1)
            # (s, n) -> global keeps orientation (det [U, -NU] = +1): a-b-c-d is counter-clockwise
            et = len(eles) + 1
            ops.element("quad", et, a, b, c, d, float(t), "PlaneStress", 1)
            eles[et] = (i, j, t)
    # fixed face: uphill (base) / downhill (top) end of the model
    fix_i = ns_ if end == "base" else 0
    for (i, j), tg in nid.items():
        if i == fix_i: ops.fix(tg, 1, 1)
    # boundary nodes of a circular cut in the pin leg (nodes of kept pin-leg pixels on the circle)
    def ring_nodes(scc, ncc, r, only_leg=True):
        out = []
        for (i, j), tg in nid.items():
            s, n = s0 + i * h, n0 + j * h; rr = math.hypot(s - scc, n - ncc)
            if abs(rr - r) <= 0.75 * h:
                # node must touch a pixel that has pin-leg metal (n <= leg bottom)
                if n <= NC + 1e-6: out.append((tg, s, n))
        return out
    mt = [100]
    def gap_truss(center_tag, nodes, gap, kstiff=2.0e4):
        els = []
        for (tg, s, n) in nodes:
            cx, cz = ops.nodeCoord(center_tag); x, z = ops.nodeCoord(tg); L = math.hypot(x - cx, z - cz)
            mt[0] += 1; ops.uniaxialMaterial("ElasticPPGap", mt[0], kstiff * L, -1e9, -gap / L, 0.0)
            et = 100000 + mt[0]; ops.element("Truss", et, center_tag, tg, 1.0, mt[0]); els.append((et, s, n))
        return els
    def soft_anchor(tg):
        for dx, dz in ((1, 0), (0, 1)):
            x, z = ops.nodeCoord(tg); a = 900000 + mt[0] + dx; mt[0] += 2
            ops.node(a, x + 100 * dx, z + 100 * dz); ops.fix(a, 1, 1); mm = 700000 + mt[0]
            ops.uniaxialMaterial("Elastic", mm, 1.0 * 100); ops.element("Truss", mm, tg, a, 1.0, mm)
    ax = glob(sc, NC); AX = 500001; ops.node(AX, float(ax[0]), float(ax[1])); soft_anchor(AX)
    tube_els = gap_truss(AX, ring_nodes(sc, NC, R_BORE), R_BORE - R_TUBE)
    kp = KEEPER[end]; kc = glob(sc + kp["ds"], kp["n"]); KP = 500002; ops.node(KP, float(kc[0]), float(kc[1])); soft_anchor(KP)
    keep_els = gap_truss(KP, ring_nodes(sc + kp["ds"], kp["n"], kp["d"] / 2), (kp["d"] - PIN_D) / 2)
    ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
    if R_on_rail is not None: ops.load(AX, float(R_on_rail[0]), float(R_on_rail[1]))
    if keeper_load is not None: ops.load(KP, float(keeper_load[0]), float(keeper_load[1]))
    if pin0 is not None and end == "base":
        # tread-0 rear pin force on the lower rail: spread over the half of the D17 hole boundary facing the force
        hn = []
        for (i, j), tg in nid.items():
            s, n = s0 + i * h, n0 + j * h
            if abs(math.hypot(s, n - 12.5) - 8.5) <= 0.75 * h:
                x, z = ops.nodeCoord(tg); c = FS.lo_point(0.0, 12.5); d = np.array([x - c[0], z - c[1]])
                if d @ np.array(pin0) > 0: hn.append(tg)
        for tg in hn: ops.load(tg, pin0[0] / len(hn), pin0[1] / len(hn))
    ops.constraints("Plain"); ops.numberer("RCM"); ops.system("UmfPack")
    ops.test("NormDispIncr", 1e-8, 60); ops.algorithm("Newton"); ops.integrator("LoadControl", 0.1); ops.analysis("Static")
    ok = ops.analyze(10)
    # element stresses (von Mises), skip pixels within 2 mm of a contact circle for the "net" value
    vm = []
    for et, (i, j, t) in eles.items():
        sx, sy, txy = ops.eleResponse(et, "stresses")[:3] if False else _avg_stress(et)
        v = math.sqrt(sx * sx - sx * sy + sy * sy + 3 * txy * txy)
        s, n = s0 + (i + 0.5) * h, n0 + (j + 0.5) * h
        dc = min(math.hypot(s - sc, n - NC) - R_BORE, math.hypot(s - sc - kp["ds"], n - kp["n"]) - kp["d"] / 2)
        vm.append((v, s, n, t, dc))
    peak = max(vm); net = max(r for r in vm if r[4] >= 2.0)
    # contact force distribution on the tube (for ring_fe.py): angle (global, from the tube centre) and force
    cont = []
    for et, s, n in tube_els:
        f = ops.eleResponse(et, "axialForce")[0]
        if f < -1e-6:
            p = glob(s, n); cont.append((round(math.degrees(math.atan2(p[1] - ax[1], p[0] - ax[0])) % 360, 1), round(-f, 1)))
    kf = sum(-ops.eleResponse(et, "axialForce")[0] for et, s, n in keep_els if ops.eleResponse(et, "axialForce")[0] < 0)
    arc = [a for a, f in cont]
    return dict(tag=tag, side=side, end=end, ok=ok, R=[round(v, 1) for v in (R_on_rail if R_on_rail is not None else (0, 0))],
                keeper_load=keeper_load, vm_peak=round(peak[0], 1), vm_peak_at=[round(peak[1], 1), round(peak[2], 1)],
                vm_net=round(net[0], 1), vm_net_at=[round(net[1], 1), round(net[2], 1)], util_net=round(net[0] / FD, 3),
                contact_n=len(cont), contact_arc_deg=[min(arc), max(arc)] if arc else None, contact=cont,
                keeper_force=round(kf, 1), elements=len(eles))


def _avg_stress(et):
    r = ops.eleResponse(et, "stresses")          # 4 Gauss points x (sxx, syy, sxy)
    a = np.array(r[:12]).reshape(4, 3).mean(axis=0)
    return a[0], a[1], a[2]


if __name__ == "__main__":
    FR = json.load(open(os.path.join(HERE, "frame_supports.json")))
    R = FR["reactions"]
    CASES = []
    # governing base / top reactions per side (largest R and the extreme angles)
    for side in ("L", "R"):
        rows = {k: v for k, v in R.items() if k.startswith(side + " |") and "ULS" in k}
        kb = max(rows, key=lambda k: rows[k]["R_base"]); kt = max(rows, key=lambda k: rows[k]["R_top"])
        ka = max(rows, key=lambda k: rows[k]["ang_base"]); ka2 = min(rows, key=lambda k: rows[k]["ang_base"])
        for key in dict.fromkeys([kb, ka, ka2]):
            v = rows[key]; CASES.append((side, "base", (v["base_H"], v["base_V"]), v["pin0"], None, key))
        kt2 = max(rows, key=lambda k: (rows[k]["ang_top"] + 90) % 360 - 90)
        for key in dict.fromkeys([kt, kt2]):
            v = rows[key]
            if -30.0 <= ((v["ang_top"] + 90) % 360 - 90) <= 140.0:          # inside the saddle; outside it the keeper carries it
                CASES.append((side, "top", (v["top_H"], v["top_V"]), None, None, key))
    LAT = json.load(open(os.path.join(HERE, "supports_checks_loads.json"))) if os.path.exists(os.path.join(HERE, "supports_checks_loads.json")) else None
    res = []
    for side, end, Rv, p0, kl, key in CASES:
        r = solve(side, end, Rv, pin0=p0, keeper_load=kl, tag=key); res.append(r)
        print(f"{side} {end:4s} R=({Rv[0]:8.0f},{Rv[1]:8.0f}) vm_net {r['vm_net']:6.1f} (util {r['util_net']:.2f}) peak {r['vm_peak']:6.1f} contact {r['contact_arc_deg']}  ok={r['ok']}  | {key}")
    # keeper cases (uplift / pull-out) from the hold-down design values written by supports_checks.py
    if LAT:
        for side in ("L", "R"):
            for end in ("base", "top"):
                F = LAT["keeper_design"][end]
                r = solve(side, end, None, keeper_load=F, tag=f"keeper {end}: {F}"); res.append(r)
                print(f"{side} {end:4s} keeper F=({F[0]:8.0f},{F[1]:8.0f}) vm_net {r['vm_net']:6.1f} (util {r['util_net']:.2f}) peak {r['vm_peak']:6.1f} keeper {r['keeper_force']:.0f} ok={r['ok']}")
    json.dump(res, open(os.path.join(HERE, "hook_fe.json"), "w"), indent=1)
