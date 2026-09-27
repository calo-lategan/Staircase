"""Pin anchorage in the step end blocks (EB): hand checks [H] + a local plate FE of the end block under the stud pull [FE].
Writes anchorage.json.  Loads from v2/revc/rails/rail_design_box80.json (production, 5.0 kN/m viewing barrier governs):
  front stud (upper rail): cap tension 41.14 kN, pad 15.02 kN, pin pull 27.43 kN (max over both sides)
  rear stud (lower rail):  cap tension 17.98 kN, pad 9.20 kN, pin pull 9.37 kN (R143 inward)
  pin shear (any direction) 8.77 kN (frame, ULS crowd), toward the rail tip 6.75 kN.
Materials: end block 6082-T651 plate 16 mm (EN 1999-1-1 Table 3.2a, 12.5 < t <= 100: f0 240, fu 295; 6 mm web zone f0 255,
fu 300 - 240/295 used throughout); nosing/box extrusions 6005A-T6 hollow t <= 5: f0 215, fu 255; plug 6082-T6 bar f0 250 fu 295;
stud 1.4462 duplex fy 450 fu 650 (as rail_design); screws A4-70 fub 700.  gM1 1.1, gM2 = gMp 1.25."""
import json, math, os
import numpy as np
import openseespy.opensees as ops
import design as dsg

HERE = os.path.dirname(os.path.abspath(__file__))
RJ = json.load(open(os.path.join(HERE, "..", "rails", "rail_design_box80.json")))
G2 = 1.25
EB = dict(f0=240.0, fu=295.0)
EXT = dict(f0=215.0, fu=255.0)
PLUG = dict(f0=250.0, fu=295.0)
DUP = dict(fy=450.0, fu=650.0)
A4 = dict(fub=700.0)
AS = {8: 36.6, 10: 58.0, 12: 84.3, 16: 157.0}

bar = RJ["barrier"]
def worst(lev, key):
    return max(v[lev][key] for v in bar.values()) * 1e3
F = dict(front_cap=worst("up", "cap_tension_max_kN"), front_pad=worst("up", "pad_force_max_kN"), front_pull=worst("up", "pin_pull_max_kN"),
         rear_cap=worst("lo", "cap_tension_max_kN"), rear_pad=max(v["lo"]["pad_force_max_kN"] for k, v in bar.items() if "inward" in k) * 1e3,
         rear_pull=worst("lo", "pin_pull_max_kN"), push_max=max(worst("up", "pin_push_max_kN"), worst("lo", "pin_push_max_kN")),
         V=RJ["frame"]["pin_force_max"]["N"], V_tip=RJ["frame"]["pin_force_toward_tip_max"])
# pad force that goes with the governing front cap tension (same case)
gov = RJ["caps"]["governing_case"]; F["front_pad_with_cap"] = bar[gov]["up"]["pad_force_max_kN"] * 1e3
OUT = {"loads_N": {k: round(v) for k, v in F.items()}, "governing_case": gov}
r = lambda v, n=3: round(float(v), n)
PR, PF = dsg.PIN_REAR, dsg.PIN_FRONT
D0 = 17.0; D = 16.0
TF, TR = dsg.EB_T["front"], dsg.EB_T["rear"]

# ------------------------------------------------------------------ 1. pin bearing and edge distances (EN 1999-1-1 T8.8)
def a_req(Fv, t, f0=EB["f0"]):
    return Fv * G2 / (2 * t * f0) + 2 * D0 / 3
def c_req(Fv, t, f0=EB["f0"]):
    return Fv * G2 / (2 * t * f0) + D0 / 3
def edge_dist(pin, poly, n=720):
    """clear metal from the hole edge to the end-block outline in every direction (ray cast)"""
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n; u = (math.cos(a), math.sin(a)); best = 1e9
        for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
            ex, ez = x2 - x1, z2 - z1; den = u[0] * ez - u[1] * ex
            if abs(den) < 1e-12: continue
            t = ((x1 - pin[0]) * ez - (z1 - pin[1]) * ex) / den; s = ((x1 - pin[0]) * u[1] - (z1 - pin[1]) * u[0]) / den
            if t > 0 and 0 <= s <= 1: best = min(best, t)
        out.append((math.degrees(a), best - D0 / 2))
    return out
poly = dsg.eb_poly()
pc = {}
for name, pin, t in (("front", PF, TF), ("rear", PR, TR)):
    ed = edge_dist(pin, poly); amin = min(e for _, e in ed); ang = min(ed, key=lambda e: e[1])[0]
    up = next(e for a, e in ed if abs(a - 90) < 0.3)
    pc[name] = dict(pin=pin, t=t, V=F["V"], bearing=r(F["V"] / (1.5 * t * D * EB["f0"] / G2)), a_req=r(a_req(F["V"], t), 2), a_min=r(amin, 2),
                    a_min_direction_deg=r(ang, 1), util_a=r(a_req(F["V"], t) / amin), metal_above_hole=r(up, 2),
                    note="full resultant applied in every direction (conservative, as rail_design.md)")
# the old positions for the record
for name, pin in (("front_old_(225,37.5)", (225.0, 37.5)), ("rear_old_(25,12.5)", (25.0, 12.5))):
    old = [(0, 50), (0, 0), (50, 0), (50, 25), (280, 25), (280, 50)]
    ed = edge_dist(pin, [tuple(map(float, p)) for p in old]); amin = min(e for _, e in ed)
    pc[name] = dict(a_min=r(amin, 2), a_req_16mm=r(a_req(F["V"], 16.0), 2), util=r(a_req(F["V"], 16.0) / amin, 2))
OUT["pin_bearing_edges"] = pc

# ------------------------------------------------------------------ 2. stud (1.4462, D16 shank, M16 at both ends)
FtRd = 0.9 * DUP["fu"] * AS[16] / G2; FvRd_thr = 0.5 * DUP["fu"] * AS[16] / G2; FvRd_sh = 0.6 * DUP["fu"] * math.pi * 64 / G2
OUT["stud"] = dict(tension=r(F["front_cap"] / FtRd), shear_shank=r(F["V"] / FvRd_sh),
                   combined_EN1993_1_8=r(F["V"] / FvRd_thr + F["front_cap"] / (1.4 * FtRd)),
                   note="thread M16 only inside the end block and beyond the rail; plain D16 h9 shank through pad + pin leg. Bending: rail_design check 7/7a (0.39/0.53), lever unchanged.")
# thread engagement in the 6082-T651 end block (VDI 2230 style stripping, C1C3 = 0.8)
def strip(d, P, D2, Le, fu):
    A = math.pi * d * (Le / P) * (P / 2 + (d - D2) * math.tan(math.radians(30)))
    return 0.8 * A * fu / math.sqrt(3) / G2, A
for nm, Ft, t in (("front stud in EB", F["front_cap"], TF), ("rear stud in EB", F["rear_cap"], TR)):
    Rd, A = strip(16.0, 2.0, 14.701, t - 1.0, EB["fu"])
    OUT["stud"][f"thread strip {nm} (Le {t - 1:g})"] = dict(A_shear=r(A, 0), FRd_kN=r(Rd / 1e3, 1), util=r(Ft / Rd), status="[H] estimate; prototype pull test to 1.5 x 41 kN = 62 kN")

# ------------------------------------------------------------------ 3. front connection: EB -> nosing end plug -> nosing walls
# plug 6082-T6 flat bar 50 x 20 x 95 (EN 755-9 stock) inside the nosing box (cavity 51 x 21), plug end flush with the EB inner face.
# EB -> plug: 2 x M10 A4-70 (y), at (240, 37.5) and (265, 37.5).  Plug -> nosing: 3 x M8 A4-70 through-bolts in x at z 37.5,
# y = 17 / 50 / 76 from the EB inner face (drawing y 33 / 66 / 92; ribs at y 54.5 / 104.5), countersunk in the front wall.
Npull = F["front_pull"]
M10_FtRd = 0.9 * A4["fub"] * AS[10] / G2; M10_FvRd = 0.5 * A4["fub"] * AS[10] / G2
conn = {}
def bearing_wall(d0, d, t, e1, p1, e2, fu, end):
    k1 = min(2.8 * e2 / d0 - 1.7, 2.5) if e2 is not None else 2.5
    ab = min((e1 / (3 * d0)) if end else (p1 / (3 * d0) - 0.25), A4["fub"] / fu, 1.0)
    return k1 * ab * fu * d * t / G2, k1, ab
ys = [17.0, 50.0, 76.0]
tot = 0.0; rows = []
for i, yb in enumerate(ys):
    end = i == 0; p1 = yb - ys[i - 1] if i else None
    fi, k1i, abi = bearing_wall(9.0, 8.0, 2.0, yb, p1 or 0, 12.5, EXT["fu"], end)      # nosing inner wall (25 high, bolt at mid)
    ff, k1f, abf = bearing_wall(9.0, 8.0, 2.0, yb, p1 or 0, None, EXT["fu"], end)      # front wall continues into the lip (e2 large)
    tot += fi + ff; rows.append(dict(y=yb, inner_wall_N=r(fi, 0), front_wall_N=r(ff, 0), alpha_b=r(abi), k1_inner=r(k1i)))
conn["plug_to_nosing_3xM8_bearing"] = dict(rows=rows, FRd_kN=r(tot / 1e3, 1), F_kN=r(Npull / 1e3, 2), util=r(Npull / tot))
FvRd_M8 = 0.5 * A4["fub"] * AS[8] / G2
conn["M8_through_bolts_double_shear"] = r(Npull / 3 / (2 * FvRd_M8))
# block tearing of each wall: two shear planes along y from the far bolt to the wall end (net), no tension face
Lnet = ys[-1] - 2.5 * 9.0
Veff = 2 * Lnet * 2.0 * EXT["f0"] / math.sqrt(3) / G2 * 2        # 2 planes x 2 walls
conn["block_tearing_walls"] = dict(net_shear_length=r(Lnet, 1), FRd_kN=r(Veff / 1e3, 1), util=r(Npull / Veff))
A_nos = 2 * 55 * 2.0 + 2 * 21 * 2.0 + dsg.LIP * dsg.T_LIP + dsg.LIP_BULB[0] * dsg.LIP_BULB[1] - 2 * 9 * 2.0
conn["nosing_net_tension"] = dict(A_net=r(A_nos, 0), sigma=r(Npull / A_nos, 1), util=r(Npull / A_nos / (EXT["fu"] * 0.9 / G2)))
OUT["front_connection"] = conn

# ------------------------------------------------------------------ 4. local plate FE of the end block under the stud pull
M8_BOX = [(6.5, 6.5), (43.5, 6.5), (6.0, 44.0), (44.0, 44.0)]           # screw ports in the back-box corners: M10 lower, M8 upper
M10_PLUG = [(238.0, 37.5), (264.0, 37.5)]                                # 2 x M12 A4-80 into the nosing end plug
H = 2.5
def contact_zone(x, z):
    """member end faces the end block can bear on (inner face): box walls, box diagonal, skin, nosing walls + plug face, lip, bulb"""
    box = (0 <= x <= 50 and 0 <= z <= 50) and (x <= 2.5 or x >= 46 or z <= 3.5 or z >= 47)
    skin = 50 <= x <= 225 and z >= 48
    nos = 225 <= x <= 280 and 25 <= z <= 50 and (x <= 227 or x >= 278 or z <= 27 or z >= 48)
    plug = 227.5 <= x <= 277.5 and 27.5 <= z <= 47.5
    lip = 277.5 <= x <= 280 and -25 <= z <= 25
    bulb = 267 <= x <= 280 and -25 <= z <= -22
    return box or skin or nos or plug or lip or bulb

def plate_fe(case):
    """case: dict(stud=(pin, F), pad=(xc, zc, ang, a, b, F), screws=[...], k_screw=[...]). Out-of-plane plate model of the whole
    end block (shells in the xz plane); screws = bilateral springs; member end faces = compression-only springs (iterated)."""
    xs = np.arange(0.0, 280.0 + 1e-9, H); zs = np.arange(-25.0, 50.0 + 1e-9, H)
    zones = dsg.eb_zones()
    quads = []
    for i in range(len(xs) - 1):
        for k in range(len(zs) - 1):
            xm, zm = (xs[i] + xs[i + 1]) / 2, (zs[k] + zs[k + 1]) / 2
            if in_poly(xm, zm, poly):
                quads.append((i, k, xm, zm, next(tz for xa, xb, tz in zones if xa - 1e-9 <= xm <= xb + 1e-9)))
    used = sorted({(i + di, k + dk) for i, k, *_ in quads for di in (0, 1) for dk in (0, 1)})
    nid = {ik: j + 1 for j, ik in enumerate(used)}; coords = {nid[(i, k)]: (xs[i], zs[k]) for (i, k) in used}
    def nearest(p):
        return min(coords, key=lambda v: math.hypot(coords[v][0] - p[0], coords[v][1] - p[1]))
    screws = [nearest(p) for p in case["screws"]]; ks = dict(zip(screws, case["k_screw"]))
    cont = {v for v, (x, z) in coords.items() if contact_zone(x, z) and v not in ks}
    k_c = 70000.0 * H * H / 60.0                      # member wall / plug end stiffness per node (60 mm effective length)
    pin, Fs = case["stud"]
    ring = [v for v, (x, z) in coords.items() if math.hypot(x - pin[0], z - pin[1]) <= 8.0 + 1e-6]
    xc, zc, ang, a, b, Fp = case["pad"]; ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pad = [v for v, (x, z) in coords.items() if abs((x - xc) * ca + (z - zc) * sa) <= a / 2 and abs(-(x - xc) * sa + (z - zc) * ca) <= b / 2]
    if not pad: raise ValueError("pad outside the end block")
    active = set(cont)
    for it in range(20):
        ops.wipe(); ops.model("basic", "-ndm", 3, "-ndf", 6)
        for v, (x, z) in coords.items(): ops.node(v, x, 0.0, z); ops.fix(v, 1, 0, 1, 0, 1, 0)
        secs = {}
        for e, (i, k, xm, zm, t) in enumerate(quads):
            if t not in secs:
                secs[t] = len(secs) + 1; ops.section("ElasticMembranePlateSection", secs[t], 70000.0, 0.3, t, 0.0)
            ops.element("ShellMITC4", e + 1, nid[(i, k)], nid[(i + 1, k)], nid[(i + 1, k + 1)], nid[(i, k + 1)], secs[t])
        spr = {}; j = 10 ** 6
        for v in list(active) + screws:
            j += 1; x, z = coords[v]; ops.node(j, x, 0.0, z); ops.fix(j, 1, 1, 1, 1, 1, 1)
            ops.uniaxialMaterial("Elastic", j, ks.get(v, k_c)); ops.element("zeroLength", j, j, v, "-mat", j, "-dir", 2); spr[v] = ks.get(v, k_c)
        ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
        for v in ring: ops.load(v, 0.0, -Fs / len(ring), 0.0, 0.0, 0.0, 0.0)
        for v in pad: ops.load(v, 0.0, Fp / len(pad), 0.0, 0.0, 0.0, 0.0)
        ops.constraints("Plain"); ops.numberer("RCM"); ops.system("UmfPack"); ops.algorithm("Linear")
        ops.integrator("LoadControl", 1.0); ops.analysis("Static"); ops.analyze(1); ops.reactions()
        lift = [v for v in active if ops.nodeDisp(v)[1] < -1e-9]       # moving outward (-y) = lift-off from the member end
        if not lift: break
        active -= set(lift)
    vm = []
    for e, (i, k, xm, zm, t) in enumerate(quads):
        rr = ops.eleResponse(e + 1, "stresses"); s = 0.0
        for gp in np.array(rr).reshape(-1, 8):
            N11, N22, N12, M11, M22, M12 = gp[:6]
            for sg in (1, -1):
                a_ = N11 / t + sg * 6 * M11 / t ** 2; b_ = N22 / t + sg * 6 * M22 / t ** 2; c_ = N12 / t + sg * 6 * M12 / t ** 2
                s = max(s, math.sqrt(a_ * a_ + b_ * b_ - a_ * b_ + 3 * c_ * c_))
        vm.append((s, xm, zm, t))
    out_zone = [v for v in vm if math.hypot(v[1] - pin[0], v[2] - pin[1]) > 14.0 and not any(math.hypot(v[1] - p[0], v[2] - p[1]) < 9.0 for p in case["screws"])]
    peak = max(out_zone); peak_all = max(vm)
    scr = {str(p): r(-ops.nodeDisp(s)[1] * ks[s], 0) for p, s in zip(case["screws"], screws)}   # + = screw in tension
    comp = sum(ops.nodeDisp(v)[1] * k_c for v in active)
    return dict(vm_peak_outside_thread_and_screw_zones=r(peak[0], 1), at=(r(peak[1], 1), r(peak[2], 1)), t=peak[3],
                util=r(peak[0] / (EB["f0"] / 1.1)), vm_peak_incl_thread_ring=r(peak_all[0], 1), at_all=(r(peak_all[1], 1), r(peak_all[2], 1)),
                screw_tension_N=scr, contact_compression_N=r(comp, 0), contact_nodes=len(active), iterations=it + 1,
                equilibrium_N=r(sum(scr.values()) - comp - (Fs - Fp), 0))


def in_poly(x, z, p):
    c = False
    for (x1, z1), (x2, z2) in zip(p, p[1:] + p[:1]):
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1): c = not c
    return c

def pad_at(pin, lev, theta, n_pad=-7.0, c_pin=12.5):
    """pad centre in step coordinates. lev 'up': the rail lies on +nu side of its pin line; the tab (n -7) is toward -nu."""
    th = math.radians(theta); nu = (math.sin(th), math.cos(th)); d = c_pin - n_pad
    sgn = -1 if lev == "up" else 1
    return (pin[0] + sgn * d * nu[0], pin[1] + sgn * d * nu[1], -theta)

k_M10 = 200e3; k_M8 = 120e3
fe = {}
for st, th in (("standard 35", 35.0), ("catwalk 0", 0.0)):
    xc, zc, ang = pad_at(PF, "up", th)
    case = dict(stud=(PF, F["front_cap"]), pad=(xc, zc, ang, 30.0, 10.0, F["front_pad_with_cap"]), screws=M8_BOX + M10_PLUG, k_screw=[k_M8] * 4 + [k_M10] * 2)
    fe[f"front stud {F['front_cap'] / 1e3:.1f} kN + tab pad {F['front_pad_with_cap'] / 1e3:.1f} kN, {st}"] = dict(pad_centre=(r(xc, 1), r(zc, 1)), **plate_fe(case))
    xc, zc, ang = pad_at(PR, "lo", th)
    case = dict(stud=(PR, F["rear_cap"]), pad=(xc, zc, ang, 30.0, 10.0, F["rear_pad"]), screws=M8_BOX + M10_PLUG, k_screw=[k_M8] * 4 + [k_M10] * 2)
    fe[f"rear stud {F['rear_cap'] / 1e3:.1f} kN + tab pad {F['rear_pad'] / 1e3:.1f} kN, {st}"] = dict(pad_centre=(r(xc, 1), r(zc, 1)), **plate_fe(case))
OUT["end_block_plate_fe"] = fe
# screw checks from the plate FE (tension incl. prying) + shear share of V
M8_FtRd = 0.9 * A4["fub"] * AS[8] / G2
M12_FtRd = 0.9 * 800.0 * AS[12] / G2; M12_FvRd = 0.5 * 800.0 * AS[12] / G2
M10p_FtRd = 0.9 * A4["fub"] * AS[10] / G2
T10 = max(max(v for k, v in c["screw_tension_N"].items() if k in (str(M10_PLUG[0]), str(M10_PLUG[1]))) for c in fe.values())
T8 = max(max(v for k, v in c["screw_tension_N"].items() if k in map(str, M8_BOX)) for c in fe.values())
OUT["screws_from_plate_fe"] = dict(
    M12_A4_80_plug_tension_max_N=r(T10, 0), M12_util_tension=r(T10 / M12_FtRd),
    M12_combined_EN1993_1_8=r(F["V"] / 2 / M12_FvRd + T10 / (1.4 * M12_FtRd)),
    M12_in_plug_thread_strip_Le24=r(T10 / strip(12.0, 1.75, 10.863, 24.0, PLUG["fu"])[0]),
    box_lower_port_M10_A4_70_tension_max_N=r(T8, 0), M10_bolt_util=r(T8 / M10p_FtRd),
    box_port_pullout="[J] screw-port pull-out, 6005A-T6, M10 at 20 mm engagement taken as 12 kN design -> util %.2f; prototype pull-out test required (>= 1.5 x %.1f kN)" % (T8 / 12000.0, T8 / 1e3))
json.dump(OUT, open(os.path.join(HERE, "anchorage.json"), "w"), indent=1, default=float)
print(json.dumps(OUT, indent=1, default=float))
