"""LIGHTWEIGHT ALL-ALUMINIUM DESIGN vs the AUG-2026 EVENTS compliance sheet (target < 70 kg / unit).
Sheet: v2/spec/sheet_2026-09-23_events.txt  (R# = row number in that file; Geometry rows 3-109, Load rows 113-181)
Material: EN AW-6082-T6 throughout (R163), f0 260 MPa t<=5 / 250 MPa t>5 (EN 1999-1-1 Tab.3.2b), gM1 1.1, E 70 GPa.
Nothing in the Blender model is changed - this is a sizing + specification study.
Run: uvx --with numpy python v2/loadtest/lightweight_events_2026.py  -> lightweight_events_2026.json
"""
import math, json, os, itertools
import numpy as np
import loadtest_latest as LT

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81
# ------------------------------------------------------------------ Aug-2026 events basis
Q_UDL = 7.5e-3        # R113 stairs 5.0-7.5 kN/m2 (target 7.5); R128 platform 7.5
Q_PT = 4000.0         # R114 tread point 4.0 kN on 200x200 (was 3.0)
PERSON = 1000.0       # R115 perceptibility < 10 mm under a single person (1.0 kN taken)
L_OVER = 250.0        # R115 L/250 under crowd UDL (public SLS)
H_LINE, H_LINE_HI = 3.0, 5.0   # R142 C5 3.0-5.0 kN/m (3.0 recommended value)
P_POST = 1500.0       # R179 post point load 1.5 kN
P_RAIL = 1250.0       # R143/R144/R145 rail / mid rail / toe board point 1.25 kN
V_RAIL = 1.0          # R178 vertical load on top rail 1.0 kN/m
SWAY = 0.10           # R176 crowd sway 10 % of vertical imposed
F1_MIN = 6.0          # R177 f1 vert >= 6 Hz where rhythmic movement credible
GG, GQ = 1.35, 1.5    # R153
E, GMOD, RHO, GM1 = 70000.0, 26000.0, 2.70e-6, 1.1


def f0(t):
    return 260.0 if t <= 5.0 else 250.0


P_FRAME, SPAN, L_TREAD = LT.P_FRAME, LT.SPAN, LT.L_TREAD
LOCKS = LT.LOCKS


# ------------------------------------------------------------------ section helpers
def rects(parts):
    """parts: [(b, h, y_centroid)] -> A, I about centroid, c_max (distance to extreme fibre)"""
    A = sum(b * h for b, h, y in parts)
    yc = sum(b * h * y for b, h, y in parts) / A
    I = sum(b * h ** 3 / 12 + b * h * (y - yc) ** 2 for b, h, y in parts)
    top = max(y + h / 2 for b, h, y in parts); bot = min(y - h / 2 for b, h, y in parts)
    return dict(A=A, I=I, c=max(top - yc, yc - bot), yc=yc)


def rhs(b, h, t):
    """b = width (out of plane / along rail), h = depth in bending direction"""
    if t * 2 >= min(b, h):
        return dict(A=b * h, I=b * h ** 3 / 12, c=h / 2, t=max(b, h))
    A = b * h - (b - 2 * t) * (h - 2 * t)
    I = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12
    J = 2 * t * (b - t) ** 2 * (h - t) ** 2 / (b + h - 2 * t)
    return dict(A=A, I=I, c=h / 2, J=J, t=t)


def chs(D, t):
    I = math.pi * (D ** 4 - (D - 2 * t) ** 4) / 64
    return dict(A=math.pi * (D ** 2 - (D - 2 * t) ** 2) / 4, I=I, c=D / 2, J=2 * I, t=t)


# ------------------------------------------------------------------ TREAD OPTIONS
def tread_plank(width=285.0, depth=30.0, skin=2.0, webs=7, web_t=1.5, down=(50.0, 2.0)):
    """hollow serrated extrusion: top + bottom skin, `webs` webs (incl. the two edge webs),
    plus a turned-down front nosing lip `down` (height, thickness) that closes the open riser."""
    parts = [(width, skin, depth - skin / 2), (width, skin, skin / 2)]
    parts += [(web_t, depth - 2 * skin, depth / 2)] * webs
    if down:
        parts.append((down[1], down[0], -down[0] / 2))
    s = rects(parts); s.update(kind="plank", width=width, depth=depth, skin=skin, webs=webs, web_t=web_t, down=down,
                               pitch=(width - web_t) / (webs - 1), t=max(skin, web_t))
    return s


def tread_grating(width=285.0, bar_h=45.0, bar_t=3.0, pitch=22.0, down=(50.0, 2.0)):
    """press-locked bar grating: bearing bars span between the guide rails, cross bars every 50 mm
    (mass only), two 3 mm edge bands; + the same nosing lip."""
    n = int(round((width - bar_t) / pitch)) + 1
    parts = [(bar_t, bar_h, bar_h / 2)] * n
    if down:
        parts.append((down[1], down[0], -down[0] / 2))
    s = rects(parts)
    cross = width * 3.0 * 8.0 / 50.0            # 3x8 cross bars @ 50 mm, smeared (mass only)
    s["A_mass"] = s["A"] + cross + 2 * 3.0 * bar_h
    s.update(kind="grating", width=width, depth=bar_h, n=n, pitch=pitch, bar_t=bar_t, down=down, t=bar_t)
    return s


CURRENT_TREAD = dict(kind="current extrusion", A=2124.8, I=566862.0, c=37.37, width=280.0, depth=50.0, t=3.0, pitch=45.0, down=None)


def check_tread(s):
    """returns dict of utilisations for the tread (spans L_TREAD between guide rails)"""
    L = L_TREAD
    fyd = f0(s["t"]) / GM1
    A_m = s.get("A_mass", s["A"])
    w_self = A_m * RHO * G
    EI = E * s["I"]
    W = s["I"] / s["c"]
    # effective section under a 200 mm patch: grating -> only bars under the patch; plank -> full (closed box)
    if s["kind"] == "grating":
        frac = min(1.0, (200.0 / s["pitch"] + 1) / s["n"])
    else:
        frac = 1.0
    gp = P_FRAME                                       # catwalk tributary governs (305.2)
    M_udl = (GQ * Q_UDL * gp + GG * w_self) * L * L / 8
    M_pt = GQ * Q_PT * L / 4 + GG * w_self * L * L / 8
    d_udl = 5 * Q_UDL * gp * L ** 4 / (384 * EI)
    d_pt = Q_PT * L ** 3 / (48 * EI * frac)
    d_person = PERSON * L ** 3 / (48 * EI * frac)
    u = dict(bend_udl=M_udl / (W * fyd), bend_point=M_pt / (W * frac * fyd),
             defl_udl=d_udl / (L / L_OVER), defl_point=d_pt / min(L / 100, 25.0), defl_person=d_person / 10.0)
    if s["kind"] == "plank":                           # local top skin between webs under the 4 kN patch
        q = GQ * Q_PT / (200.0 * 200.0)
        m = q * s["pitch"] ** 2 / 12
        u["local_skin"] = (6 * m / s["skin"] ** 2) / fyd
    rise = LOCKS["STANDARD"]["deck"][1] - LOCKS["STANDARD"]["deck"][0]
    lip = s["down"][0] if s.get("down") else 0.0
    gap = rise - s["depth"] - lip
    return dict(util=u, gov=max(u.values()), mass_kg=A_m * s.get("L", 1236.0) * RHO,
                open_riser_gap_mm=round(gap, 1), deck_gap_mm=round(P_FRAME - s["width"], 1))


# ------------------------------------------------------------------ GIRDER FE (flexible)
def girder_fe(lock, lo, up, tread_A, hr_side_N, q, treads="all", mid_support=False, point=None, factor=(1.0, 1.0)):
    """side girder, LOCKED (tread fixed to lower bar at the lock pin, pinned to upper bar).
    q: characteristic UDL (N/mm2); factor=(gG, gQ); treads: 'all' | 'low' | 'high' (pattern);
    point: (tread index, N) extra point load. Returns max stress per bar (MPa) and max vertical deflection."""
    Lk = LOCKS[lock]; th = math.radians(Lk["theta"])
    u = np.array([-math.cos(th), math.sin(th)])
    fr = LT.Frame2D()
    st = Lk["st"]
    xs = sorted(set([0.0, SPAN, SPAN / 2] + st + [SPAN * k / 48 for k in range(49)]))
    nodes = {x: fr.node(*(u * x)) for x in xs}
    for a, c in zip(xs[:-1], xs[1:]):
        fr.beam(nodes[a], nodes[c], E, lo["A"], lo["I"], tag="lower")
        wseg = lo["A"] * RHO * G * (c - a) * factor[0]
        fr.load(nodes[a], fz=-wseg / 2); fr.load(nodes[c], fz=-wseg / 2)
    fr.support(nodes[0.0], {0, 1}); fr.support(nodes[SPAN], {1})
    if mid_support:
        fr.support(nodes[SPAN / 2], {1})
    gp = P_FRAME * math.cos(th)
    link = np.array(LT.LINK)
    ups = []
    for i, s in enumerate(st):
        on = treads == "all" or (treads == "low" and i < 3) or (treads == "high" and i >= 3)
        p = (factor[1] * (q * gp if on else 0.0) + factor[0] * tread_A * RHO * G) * L_TREAD / 2 + factor[0] * hr_side_N / 6
        if point and point[0] == i:
            p += point[1] / 2
        p_lo = u * s; p_up = p_lo + link
        n_up = fr.node(*p_up); n_mid = fr.node(*((p_lo + p_up) / 2))
        ups.append(n_up)
        fr.beam(nodes[s], n_mid, E, 1500.0, 5e6, tag="tread")
        fr.beam(n_mid, n_up, E, 1500.0, 5e6, rel_j=True, tag="tread")
        fr.load(n_mid, fz=-p)
    for a, c in zip(ups[:-1], ups[1:]):
        fr.beam(a, c, E, up["A"], up["I"], tag="upper")
    wup = up["A"] * up.get("L", 1845.0) * RHO * G * factor[0] / len(ups)
    for nd in ups:
        fr.load(nd, fz=-wup)
    r = fr.solve()
    out = {}
    for tag, sec in (("upper", up), ("lower", lo)):
        fs = [f for f in r["forces"] if f["tag"] == tag]
        out[tag] = max(max(abs(f["M1"]), abs(f["M2"])) / (sec["I"] / sec["c"]) + abs(f["N"]) / sec["A"] for f in fs)
    out["defl"] = float(max(abs(r["u"][1::3])))
    return out


def check_girder(lo, up, tread_A, hr_side_N):
    """public event checks on the standard stair + catwalk with a mid-span foot; steep = crew use (EN 131)."""
    res = {}
    fyd_lo = f0(lo["t"]) / GM1; fyd_up = f0(up["t"]) / GM1
    for name, lock, mid in (("standard", "STANDARD", False), ("catwalk_midfoot", "CATWALK", True)):
        worst_s, worst_d = 0.0, 0.0
        for pat in ("all", "low", "high"):
            uls = girder_fe(lock, lo, up, tread_A, hr_side_N, Q_UDL, pat, mid, factor=(GG, GQ))
            worst_s = max(worst_s, uls["lower"] / fyd_lo, uls["upper"] / fyd_up)
        sls = girder_fe(lock, lo, up, tread_A, hr_side_N, Q_UDL, "all", mid)
        worst_d = sls["defl"] / (SPAN / (2 if mid else 1) / L_OVER)
        person = max(girder_fe(lock, lo, up, 0.0, 0.0, 0.0, "all", mid, point=(i, PERSON))["defl"] for i in range(6))
        res[name] = dict(stress=round(worst_s, 3), defl_L250=round(worst_d, 3), person_10mm=round(person / 10.0, 3))
    # steep 49.4 deg: not a public stair (pitch > 35 deg, R9) -> crew step-ladder, EN 131 2.7 kN strength load (R118)
    s = girder_fe("STEEP", lo, up, tread_A, hr_side_N, 0.0, "all", False, point=(2, 2 * 2700.0), factor=(GG, GQ))
    res["steep_crew"] = dict(stress=round(max(s["lower"] / fyd_lo, s["upper"] / fyd_up), 3))
    # f1 of the standard stair, self weight only (R177): Rayleigh f = 17.75 / sqrt(delta_mm)
    sw = girder_fe("STANDARD", lo, up, tread_A, hr_side_N, 0.0, "all", False)
    res["f1_standard_Hz"] = round(17.75 / math.sqrt(max(sw["defl"], 1e-6)), 2)
    return res


# ------------------------------------------------------------------ BARRIER FE (flexible layout)
def barrier_fe(lock, post_idx, post, rails, ext_hand=0.0, case="line", load=H_LINE, at=None):
    """out-of-plane grillage. rails: {name: (height above tread top, section)}; posts fixed at their base
    (moment socket on the guide rail). ext_hand: horizontal cantilever of the HANDRAIL beyond the end posts.
    case: 'line' (guardrail line load) | 'post' (P_POST at a post top) | 'mid' (P_RAIL mid-span top rail)
          | 'tip' (P_RAIL at handrail extension tip). Returns max post moment (Nmm), max rail moment, top defl."""
    Lk = LOCKS[lock]; th = math.radians(Lk["theta"])
    g_h = P_FRAME * math.cos(th)
    X, els, F = [], [], {}

    def node(a, z):
        X.append((a, z)); return len(X) - 1
    rail_nodes = {k: [] for k in rails}
    for i in post_idx:
        a = i * g_h; z0 = Lk["deck"][i] - Lk["deck"][0]
        prev = node(a, z0); base = prev
        for k, (h, sec) in sorted(rails.items(), key=lambda kv: kv[1][0]):
            nd = node(a, z0 + h)
            els.append((prev, nd, post, "post"))
            rail_nodes[k].append(nd); prev = nd
        X[base] = X[base]
        F.setdefault("_bases", []).append(base)
    bases = F.pop("_bases")
    for k, (h, sec) in rails.items():
        ns = rail_nodes[k]
        for a, b in zip(ns[:-1], ns[1:]):
            els.append((a, b, sec, "rail:" + k))
    tip = None
    if ext_hand > 0 and "hand" in rails:
        ns = rail_nodes["hand"]
        for end, sgn in ((ns[0], -1), (ns[-1], 1)):
            a0, z0 = X[end]
            t = node(a0 + sgn * ext_hand, z0 + sgn * ext_hand * math.tan(th))
            els.append((end, t, rails["hand"][1], "rail:hand"))
            tip = tip if tip is not None else t
    top = max(rails, key=lambda k: rails[k][0])
    tn = rail_nodes[top]
    if case == "line":
        for a, b in zip(tn[:-1], tn[1:]):
            Ls = math.dist(X[a], X[b])
            F[a] = F.get(a, 0.0) + GQ * load * Ls / 2; F[b] = F.get(b, 0.0) + GQ * load * Ls / 2
        over = max(0.0, LT.RAIL_LEN - math.dist(X[tn[0]], X[tn[-1]])) / 2      # guardrail beyond end posts
        F[tn[0]] = F.get(tn[0], 0.0) + GQ * load * over; F[tn[-1]] = F.get(tn[-1], 0.0) + GQ * load * over
    elif case == "post":
        F[tn[len(tn) // 2]] = GQ * P_POST
    elif case == "mid":
        # widest span of the top rail
        spans = [(math.dist(X[a], X[b]), a, b) for a, b in zip(tn[:-1], tn[1:])]
        Ls, a, b = max(spans)
        els = [e for e in els if not (e[0] == a and e[1] == b and e[3] == "rail:" + top)]
        m = node((X[a][0] + X[b][0]) / 2, (X[a][1] + X[b][1]) / 2)
        els += [(a, m, rails[top][1], "rail:" + top), (m, b, rails[top][1], "rail:" + top)]
        F[m] = GQ * P_RAIL
    elif case == "tip" and tip is not None:
        F[tip] = GQ * P_RAIL
    n = len(X); N = 3 * n
    K = np.zeros((N, N)); Fv = np.zeros(N)
    cache = []
    for (i, j, sec, tag) in els:
        (a1, z1), (a2, z2) = X[i], X[j]
        L = math.hypot(a2 - a1, z2 - z1); c, s = (a2 - a1) / L, (z2 - z1) / L
        EI, GJ = E * sec["I"], GMOD * sec.get("J", 2 * sec["I"])
        kl = np.zeros((6, 6))
        kb = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                     [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        ib = [0, 2, 3, 5]
        for p in range(4):
            for q in range(4):
                kl[ib[p], ib[q]] = kb[p, q]
        kl[1, 1] = kl[4, 4] = GJ / L; kl[1, 4] = kl[4, 1] = -GJ / L
        T = np.zeros((6, 6))
        for o in (0, 3):
            T[o, o] = 1.0; T[o + 1, o + 1] = c; T[o + 1, o + 2] = s; T[o + 2, o + 1] = -s; T[o + 2, o + 2] = c
        dof = [3 * i, 3 * i + 1, 3 * i + 2, 3 * j, 3 * j + 1, 3 * j + 2]
        K[np.ix_(dof, dof)] += T.T @ kl @ T
        cache.append((dof, kl, T, tag, sec))
    for nd, f in F.items():
        Fv[3 * nd] += f
    fixed = [3 * b + d for b in bases for d in (0, 1, 2)]
    free = [d for d in range(N) if d not in fixed]
    uu = np.zeros(N)
    uu[free] = np.linalg.solve(K[np.ix_(free, free)], Fv[free])
    Mp, Mr = 0.0, {}
    for dof, kl, T, tag, sec in cache:
        fl = kl @ (T @ uu[dof]); m = max(abs(fl[2]), abs(fl[5]))
        if tag == "post":
            Mp = max(Mp, m)
        else:
            Mr[tag] = max(Mr.get(tag, 0.0), m)
    wtop = max(abs(uu[3 * nd]) for nd in tn)
    return dict(M_post=Mp, M_rail=Mr, w_top=wtop)


def check_barrier(post_idx, post, rails, stair_ext):
    """public barrier checks at catwalk + standard (steep shares the kit; flagged crew-only)."""
    fyd_p = f0(post["t"]) / GM1
    worst = dict(post=0.0, rails={}, defl=0.0, Mbase=0.0)
    for lock in ("CATWALK", "STANDARD"):
        ext = stair_ext if lock == "STANDARD" else 0.0
        for case in ("line", "post", "mid", "tip"):
            r = barrier_fe(lock, post_idx, post, rails, ext, case)
            worst["post"] = max(worst["post"], r["M_post"] / (post["I"] / post["c"] * fyd_p))
            worst["Mbase"] = max(worst["Mbase"], r["M_post"])
            for tag, m in r["M_rail"].items():
                k = tag.split(":")[1]; sec = rails[k][1]
                worst["rails"][k] = max(worst["rails"].get(k, 0.0), m / (sec["I"] / sec["c"] * f0(sec["t"]) / GM1))
            if case == "line":
                worst["defl"] = max(worst["defl"], r["w_top"] / GQ)       # SLS approx
    # vertical 1.0 kN/m on the top rail between posts (in-plane, hand)
    g_max = max(b - a for a, b in zip(post_idx[:-1], post_idx[1:])) * P_FRAME
    top_sec = rails[max(rails, key=lambda k: rails[k][0])][1]
    Mv = GQ * V_RAIL * g_max ** 2 / 8
    worst["rails"]["guard_vertical"] = Mv / (top_sec["I"] / top_sec["c"] * f0(top_sec["t"]) / GM1)
    # toe board 1.25 kN point between posts (hand, simply supported, weak axis of a 150 x t plate with lip)
    return worst


# ------------------------------------------------------------------ GEOMETRY CHECK vs the sheet (as drawn)
def geometry_check():
    stdd = LOCKS["STANDARD"]; stp = LOCKS["STEEP"]
    r_std = stdd["deck"][1] - stdd["deck"][0]; g_std = P_FRAME * math.cos(math.radians(35.0))
    r_stp = stp["deck"][1] - stp["deck"][0]; g_stp = P_FRAME * math.cos(math.radians(49.4))
    rows = [
        ("R9", "Stair pitch <= 35 deg", "35.0 / 49.4 deg", "standard PASS (at limit) / steep FAIL - crew step-ladder only"),
        ("R4", "Going >= 250 (riser <= 175)", f"{g_std:.0f} / {g_stp:.0f} mm", "standard PASS (at limit) / steep FAIL"),
        ("R5", "Riser 100-200 (rec 170); riser <= going x tan35", f"{r_std:.0f} / {r_stp:.0f} mm", "standard PASS (5 mm over the 170 rec) / steep FAIL"),
        ("R8", "2h + g 540-660 (design aid)", f"{2*r_std+g_std:.0f} / {2*r_stp+g_stp:.0f} mm", "standard PASS / steep FAIL (663)"),
        ("R12", "Uniform risers", "standard 175 all / steep first 211 vs 232", "standard PASS / steep FAIL"),
        ("R7", "Open riser gap <= 120 max / 100 rec", f"{r_std-50:.0f} mm (175 rise - 50 tread)", "FAIL - close with a 50 mm nosing lip or riser plate"),
        ("R48", "Deck gap <= 25 (catwalk)", f"{P_FRAME-280:.1f} mm", "FAIL by 0.2 mm - tread depth 285"),
        ("R3", "Clear width >= 1100 (industry anchor, flow calc)", "1023 between handrails / 1211 between rails", "BELOW anchor for a single unit; wide config PASS - confirm by flow calc"),
        ("R63", "Top rail >= 1100 above pitch line", "1111 / 1127 / 1162", "PASS"),
        ("R64", "Grip 25-50 (40 target)", "25x25 square bars", "PASS range, not round - specify CHS 40"),
        ("R65/R68", "No gap > 470 in side protection", "about 1000 mm tread-to-handrail", "FAIL - add intermediate rail"),
        ("R66", "Toe board 150 (event)", "none", "FAIL - add 150 mm toe board"),
        ("R70", "Lower child rail ~600 (event)", "none", "FAIL - intermediate rail at ~575 mm serves both"),
        ("R19", "Handrail extension >= 300 past top/bottom nosing", "~80 mm", "FAIL - extend handrail (stair variant only)"),
        ("R18/R109", "Centre handrail if > 28 deg and > 1800 wide", "wide stair 2.54 m at 35 deg", "PASS only with the inner handrail FULL (not mini) on wide stairs"),
        ("R103", "Module join gap <= 25 / lip <= 4", "wide join 5 mm (right rails nest in left channels); double join 19 mm", "PASS - wide and double"),
        ("R104", "Positive captive locking", "lock pins (bottom minis) loose", "specify captive (lanyard / spring detent)"),
        ("R16/R94", "Slip PTV >= 36 wet (40 event)", "not specified", "specify serrated top, PTV >= 40 test"),
        ("R17", "55 mm contrasting nosings", "none", "specify contrasting nosing insert"),
        ("R106", "Post spacing <= 2.5 m", "305 mm", "PASS"),
        ("R54", "Free-standing height:base <= 3:1", "0.7:1 standard", "PASS"),
    ]
    return rows


# ------------------------------------------------------------------ MASS ROLL-UP
def mass_unit(tread, bars, posts_n, post, rails_len, rails, extras):
    kg = {}
    kg["treads 6x"] = 6 * tread.get("A_mass", tread["A"]) * 1236.0 * RHO
    kg["guide bars 4x"] = sum(sec["A"] * L for sec, L in bars) * RHO
    kg["axles 2x"] = 2 * LT.SEC["axle"]["A"] * 1305.0 * RHO
    kg[f"posts {posts_n}x1000"] = posts_n * post["A"] * 1000.0 * RHO
    kg[f"pivot heads {posts_n}x"] = posts_n * 250.0 * 100.0 * RHO
    kg["lock pins 12x (all treads)"] = 12 * 250.0 * 165.0 * RHO
    for k, (h, sec) in rails.items():
        kg[f"rail {k} 2x"] = 2 * sec["A"] * rails_len[k] * RHO
    kg.update(extras)
    kg["TOTAL"] = sum(kg.values())
    return kg


if __name__ == "__main__":
    out = {}
    out["geometry_vs_sheet"] = geometry_check()
    # ---- treads
    tr = {}
    tr["current extrusion 280x50"] = check_tread(CURRENT_TREAD)
    rise_std = LOCKS["STANDARD"]["deck"][1] - LOCKS["STANDARD"]["deck"][0]
    best = None
    for d, sk, nw, lt in itertools.product((30, 35, 40, 45, 50), (1.5, 2.0, 2.5), (5, 7, 9), (2.0, 3.0)):
        lip = max(0.0, rise_std - d - 100.0)                     # smallest lip that closes the riser to 100
        s = tread_plank(depth=d, skin=sk, webs=nw, down=(lip, lt) if lip > 0 else None)
        c = check_tread(s)
        key = f"hollow plank 285x{d}, {sk} skins, {nw} webs, lip {lip:.0f}x{lt:.0f}"
        if c["gov"] <= 1.0 and c["open_riser_gap_mm"] <= 100.0:
            if best is None or c["mass_kg"] < best[0]:
                best = (c["mass_kg"], key, s, c)
        if (d, sk, nw, lt) in ((40, 2.0, 7, 2.0), (35, 2.0, 7, 3.0), (30, 2.0, 7, 2.0)):
            tr[key] = dict(c, A=round(s["A"]), I=round(s["I"]))
    tr[best[1]] = dict(best[3], A=round(best[2]["A"]), I=round(best[2]["I"]))
    for bh, bt, p in ((40, 3.0, 22), (45, 3.0, 22), (50, 3.0, 25), (50, 4.0, 22)):
        s = tread_grating(bar_h=bh, bar_t=bt, pitch=p, down=(max(0.0, rise_std - bh - 100.0), 2.0) if rise_std - bh > 100 else None)
        tr[f"bar grating {bh}x{bt} @ {p}"] = dict(check_tread(s), A=round(s["A_mass"]), I=round(s["I"]))
    out["treads"] = tr
    t_mass, t_name, TREAD, _ = best
    out["tread_choice"] = t_name
    # ---- guide bars: hollow + solid options within the catwalk stack envelope (lower <= 55 w/ pads, upper <= 50 w/ thinner tread)
    hr_side_N = 14.0 * G                     # provisional handrail per side (kg), refined after barrier sizing
    bars = []
    for (hl, tl), (hu, tu) in itertools.product(((40, 3), (45, 3), (50, 3), (50, 4), (55, 3), (40, 5), (50, 6)),
                                                 ((25, 2.5), (30, 3), (35, 3), (40, 3), (35, 4), (45, 3))):
        lo = rhs(25.0, hl, tl); lo["L"] = 1778.7
        up = rhs(25.0, hu, tu); up["L"] = 1845.1
        c = check_girder(lo, up, TREAD["A"], hr_side_N)
        ok = all(v <= 1.0 for k in ("standard", "catwalk_midfoot") for v in c[k].values()) \
            and c["steep_crew"]["stress"] <= 1.0 and c["f1_standard_Hz"] >= F1_MIN
        # mass of 4 bars (L side 35 wide scaled by width ratio)
        m = (lo["A"] * 1778.7 * (1 + 35 / 25) + up["A"] * 1845.1 * (1 + 35 / 25)) * RHO
        bars.append(dict(lower=f"RHS 25x{hl}x{tl}", upper=f"RHS 25x{hu}x{tu}", ok=bool(ok), mass_kg=round(m, 2), **c))
    okb = sorted([b for b in bars if b["ok"]], key=lambda b: b["mass_kg"])
    out["bars_best5"] = okb[:5]
    out["bars_n_ok"] = len(okb)
    # ---- barrier: layouts x post sections, rails CHS
    g_std = P_FRAME * math.cos(math.radians(35.0))
    ext_h = 142.5 + 300.0                   # handrail beyond end-post centre to 300 past nosing (horizontal)
    rail_opts = {"guard": (LOCKS["STANDARD"]["guard"], chs(40.0, 2.0)), "hand": (1000.0, chs(40.0, 2.0)),
                 "mid": (575.0, chs(30.0, 2.0))}
    layouts = {"6 per side (every tread)": [0, 1, 2, 3, 4, 5], "4 per side (0,2,3,5)": [0, 2, 3, 5], "3 per side (0,2,5)": [0, 2, 5]}
    posts = {"SHS 40x40x3": rhs(40, 40, 3), "SHS 40x40x4": rhs(40, 40, 4), "SHS 50x50x3": rhs(50, 50, 3),
             "SHS 50x50x4": rhs(50, 50, 4), "RHS 60x40x3 (60 deep)": rhs(40, 60, 3), "SHS 60x60x3": rhs(60, 60, 3),
             "RHS 80x40x3 (80 deep)": rhs(40, 80, 3), "SHS 60x60x4": rhs(60, 60, 4)}
    rails_try = {"CHS 40x2": chs(40, 2), "CHS 40x3": chs(40, 3), "CHS 48.3x3": chs(48.3, 3)}
    bar_res = []
    for (lname, idx), (pname, psec) in itertools.product(layouts.items(), posts.items()):
        for gname, gsec in rails_try.items():
            for hname, hsec in rails_try.items():
                rails = {"guard": (LOCKS["STANDARD"]["guard"], gsec), "hand": (1000.0, hsec), "mid": (575.0, chs(30.0, 2.0))}
                w = check_barrier(idx, psec, rails, ext_h)
                ok = w["post"] <= 1.0 and all(v <= 1.0 for v in w["rails"].values())
                m = 2 * len(idx) * psec["A"] * 1000 * RHO + 2 * (gsec["A"] * LT.RAIL_LEN + hsec["A"] * (LT.RAIL_LEN + 2 * ext_h / math.cos(math.radians(35)) - 200)) * RHO
                bar_res.append(dict(layout=lname, post=pname, guard=gname, hand=hname, ok=bool(ok), mass_kg=round(m, 2),
                                    post_util=round(w["post"], 3), rails={k: round(v, 3) for k, v in w["rails"].items()},
                                    M_base_kNm=round(w["Mbase"] / 1e6, 2), top_defl_mm=round(w["defl"], 1)))
    okr = sorted([b for b in bar_res if b["ok"]], key=lambda b: b["mass_kg"])
    out["barrier_best5"] = okr[:5]
    out["barrier_6post_best"] = next((b for b in okr if b["layout"].startswith("6")), None)
    # ---- mass roll-up (standard-stair installed kit)
    B = okb[0]; R = okr[0]
    lo_s = rhs(25.0, *map(float, B["lower"].split("x")[1:])) if False else None
    extras = {"rail brackets / clamps": 2 * len(layouts[R["layout"]]) * 3 * 0.06,
              "post base sockets (moment)": 2 * len(layouts[R["layout"]]) * 0.30,
              "toe boards 2x 150x2 + 10 lip": 2 * (150 * 2 + 10 * 2) * LT.RAIL_LEN * RHO,
              "hooks 4x 10 mm + male connectors 2x": 4 * 0.08 + 2 * 0.10,
              "rail-end brackets, spacers, bolts (lump)": 1.2,
              "foot pads 4x + catwalk mid-feet 2x": 4 * 0.06 + 2 * 0.15}
    tread_mass_each = TREAD["A"] * 1236 * RHO
    total = 6 * tread_mass_each + B["mass_kg"] + 2 * LT.SEC["axle"]["A"] * 1305 * RHO + R["mass_kg"] \
        + 2 * chs(30, 2)["A"] * LT.RAIL_LEN * RHO + 2 * len(layouts[R["layout"]]) * 250 * 100 * RHO \
        + 12 * 250 * 165 * RHO + sum(extras.values())
    out["mass_rollup"] = {"treads 6x": round(6 * tread_mass_each, 2), "guide bars 4x": B["mass_kg"],
                          "axles 2x": round(2 * LT.SEC["axle"]["A"] * 1305 * RHO, 2),
                          "posts + guardrail + handrail": R["mass_kg"],
                          "intermediate rails 2x CHS 30x2": round(2 * chs(30, 2)["A"] * LT.RAIL_LEN * RHO, 2),
                          "pivot heads": round(2 * len(layouts[R["layout"]]) * 250 * 100 * RHO, 2),
                          "lock pins 12x": round(12 * 250 * 165 * RHO, 2),
                          **{k: round(v, 2) for k, v in extras.items()}, "TOTAL": round(total, 1)}
    with open(os.path.join(HERE, "lightweight_events_2026.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ("tread_choice", "bars_n_ok", "mass_rollup")}, indent=1))
    print("TREADS", json.dumps({k: (round(v["gov"], 3), round(v["mass_kg"], 2), v["open_riser_gap_mm"]) for k, v in tr.items()}, indent=0))
    print("BARS", json.dumps(okb[:3], indent=0))
    print("BARRIER", json.dumps(okr[:4], indent=0))
    print("BARRIER 6-post best", json.dumps(out["barrier_6post_best"]))


# ================================================================== FINAL SPEC (robust + thin-skin variants)
def final_spec():
    th35 = math.radians(35.0)
    ext_h = 142.5 + 300.0
    rails = {"guard": (LOCKS["STANDARD"]["guard"], chs(40.0, 2.0)), "hand": (1000.0, chs(48.3, 3.0)),
             "mid": (575.0, chs(30.0, 2.0))}
    post_idx, post = [0, 2, 5], rhs(60, 60, 4)
    lo, up = rhs(25.0, 45.0, 3.0), rhs(25.0, 25.0, 2.5)
    lo["L"], up["L"] = 1778.7, 1845.1
    toe = rects([(1.5, 150.0, 75.0), (25.0, 1.5, 150.0), (25.0, 1.5, 0.75)])       # 150 toe board, 25 returns
    toe_I_out = 2 * (1.5 * 25.0 ** 3 / 12 + 25 * 1.5 * 12.5 ** 2) + 150 * 1.5 ** 3 / 12 + 150 * 1.5 * 12.5 ** 2
    variants = {}
    for vname, skin in (("recommended (1.8 mm tread skins)", 1.8), ("robust (2.0 mm tread skins)", 2.0), ("thin-skin (1.5 mm tread skins, extruder to confirm)", 1.5)):
        T = tread_plank(depth=40, skin=skin, webs=5, down=(35.0, 2.0))
        tc = check_tread(T)
        hr_kg = (2 * len(post_idx) * post["A"] * 1000 + 2 * rails["guard"][1]["A"] * LT.RAIL_LEN
                 + 2 * rails["hand"][1]["A"] * (LT.RAIL_LEN + 2 * ext_h / math.cos(th35) - 200)
                 + 2 * rails["mid"][1]["A"] * LT.RAIL_LEN) * RHO
        gc = check_girder(lo, up, T["A"], hr_kg / 2 * G)
        bc = check_barrier(post_idx, post, rails, ext_h)
        # toe board: 1.25 kN horizontal point mid-span between posts (widest span 3 treads = 916 mm along slope)
        span_toe = 3 * P_FRAME
        toe_u = (GQ * P_RAIL * span_toe / 4) / (toe_I_out / 12.5) / (f0(1.5) / GM1)
        # standalone captive lock pins at the 3 treads per side without posts: dia 12 6082, single shear 8.7 kN
        pin_u = 8.7e3 / (math.pi * 36 * (f0(12) / GM1) / math.sqrt(3))
        kg = {
            "treads 6x (285x40 hollow plank)": 6 * T["A"] * 1236 * RHO,
            "guide bars 4x (RHS)": (lo["A"] * 1778.7 + up["A"] * 1845.1) * (1 + 35 / 25) * RHO,
            "axles 2x (tube 25.2x2.7)": 2 * LT.SEC["axle"]["A"] * 1305 * RHO,
            "posts 6x SHS 60x60x4": 2 * len(post_idx) * post["A"] * 1000 * RHO,
            "guardrails 2x CHS 40x2": 2 * rails["guard"][1]["A"] * LT.RAIL_LEN * RHO,
            "handrails 2x CHS 48.3x3 (+300 ext)": 2 * rails["hand"][1]["A"] * (LT.RAIL_LEN + 2 * ext_h / math.cos(th35) - 200) * RHO,
            "intermediate rails 2x CHS 30x2": 2 * rails["mid"][1]["A"] * LT.RAIL_LEN * RHO,
            "toe boards 2x 150x25x1.5": 2 * toe["A"] * LT.RAIL_LEN * RHO,
            "pivot heads 6x": 6 * 250 * 100 * RHO,
            "lock pins: 6 post minis + 6 dia-12 captive": 6 * 250 * 165 * RHO + 6 * math.pi * 36 * 70 * RHO,
            "post base moment sockets 6x": 6 * 0.30,
            "rail clamps 18x": 18 * 0.06,
            "hooks 4x 10 mm + male connectors 2x": 4 * 0.08 + 2 * 0.10,
            "rail brackets, spacers, bolts (lump)": 1.2,
            "foot pads 4x + catwalk mid-feet 2x": 4 * 0.06 + 2 * 0.12,
        }
        kg = {k: round(v, 2) for k, v in kg.items()}
        kg["TOTAL"] = round(sum(kg.values()), 1)
        W_unit = kg["TOTAL"] * G
        # catwalk anchors (free-standing): 3.0 kN/m on guardrail at 1.261 m, self weight only, 4 anchors
        M_ot = H_LINE * LT.RAIL_LEN * (150 + LOCKS["CATWALK"]["guard"])
        T_anchor = max(0.0, GQ * M_ot - 0.9 * W_unit * 635.5) / 1271.0 / 2
        V_anchor = max(0.0, GQ * H_LINE * LT.RAIL_LEN - 0.3 * 0.9 * W_unit) / 4
        # crowd sway 10 % of vertical imposed (stair, standard) -> base + hooks
        sway = SWAY * Q_UDL * L_TREAD * SPAN * math.cos(th35)
        variants[vname] = dict(
            tread=dict(A=round(T["A"]), I=round(T["I"]), util=round(tc["gov"], 3), mass_each=round(tc["mass_kg"], 2),
                       open_riser_gap=tc["open_riser_gap_mm"], deck_gap=tc["deck_gap_mm"], checks={k: round(v, 3) for k, v in tc["util"].items()}),
            girder=gc, barrier=dict(post=round(bc["post"], 3), rails={k: round(v, 3) for k, v in bc["rails"].items()},
                                    M_base_kNm=round(bc["Mbase"] / 1e6, 2), defl_mm=round(bc["defl"], 1)),
            toe_board_util=round(toe_u, 3), lock_pin_util=round(pin_u, 3),
            anchors=dict(T_kN=round(T_anchor / 1e3, 2), V_kN=round(V_anchor / 1e3, 2),
                         ballast_kg=round(max(0.0, (1.5 * M_ot - W_unit * 635.5) / (G * 635.5)))),
            sway_kN=round(sway / 1e3, 2), mass=kg)
    return variants


if __name__ == "__main__":
    fs = final_spec()
    with open(os.path.join(HERE, "lightweight_final.json"), "w") as f:
        json.dump(fs, f, indent=1)
    for k, v in fs.items():
        print("\n==", k)
        print(json.dumps({kk: v[kk] for kk in ("tread", "girder", "barrier", "toe_board_util", "lock_pin_util", "anchors", "sway_kN")}))
        print(json.dumps(v["mass"], indent=0))
