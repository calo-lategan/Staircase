"""STEP 2 LOAD TEST - 'Latest 21-09-2026' STEP LADDER (rigged model, STEP LADDER RIGGED2.blend).

Two independent methods, compared:
  (1) HAND CALCULATIONS  - closed-form statics / Euler-Bernoulli, same style as v2/spec/params.py
  (2) NUMERICAL FE       - numpy direct-stiffness 2D frame (side girders) + out-of-plane grillage (barriers)
(3) Blender rigid-body / cloth physics runs separately (blender_physics.py) and is compared in the report.

Every section below was MEASURED from the CAD mesh in Blender by bisecting each member (see
loadtest_inputs.json). Loads/factors cite v2/spec/tab_Load_compliances.txt by FILE LINE NUMBER (L#),
Event / public column, exactly as params.py does.  Units: N, mm, MPa (N/mm2) unless noted.

Run:  uvx --with numpy python v2/loadtest/loadtest_latest.py
"""
import math, json, os, csv
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81

# ===================================================================== MEASURED GEOMETRY (Blender)
P_FRAME = 305.2            # tread pitch along the frame, every state (rig law, verified vs originals)
SPAN = 1831.0              # base axle 006 -> top axle 010 along the frame (same in every state)
L_TREAD = 1241.0           # tread span: L-bar channel centre -> R-bar channel centre
W_PITCH = 1271.0           # side-by-side pitch (plates flush, axle pins engage)
D_END = 1825.44            # end-to-end pitch (original double catwalk, fit 0.01 mm)
LINK = (199.9, 24.6)       # tread link, lower-bar pin -> upper-bar pin, world (X, Z) mm.
                           # Fitted from bar separation at 0/35 deg, predicts 49.4 deg to 0.0 mm.
RAIL_LEN = 1725.8          # guardrail / cyan rail length per unit
LOCKS = {   # theta, tread stations along frame from base axle, deck heights, rail heights above tread
    "CATWALK":  dict(theta=0.0,  st=[59.0, 364.2, 669.3, 974.5, 1279.7, 1584.8],
                     deck=[150.0] * 6, guard=1111.1, hand=1000.0, d_sep=25.6),
    "STANDARD": dict(theta=35.0, st=[81.4, 386.5, 691.7, 996.9, 1302.0, 1607.2],
                     deck=[175.0, 350.0, 525.1, 700.1, 875.1, 1050.2], guard=1127.0, hand=1011.7, d_sep=135.8),
    "STEEP":    dict(theta=49.4, st=[103.6, 408.7, 713.9, 1019.1, 1324.2, 1629.4],
                     deck=[211.0, 442.6, 674.3, 906.0, 1137.6, 1369.3], guard=1162.0, hand=1018.0, d_sep=168.8),
}

# ===================================================================== MEASURED SECTIONS (mm)
SEC = {
    "tread":  dict(A=2124.8, I=566862.0, c=37.37, L=1236.0, I_in_plane=19882306.0),
    "bar_R_up": dict(A=274.7, I=9878.0,  c=12.05, L=1845.1),
    "bar_R_lo": dict(A=275.0, I=7562.0,  c=12.80, L=1778.7),
    "bar_L_up": dict(A=526.0, I=24959.0, c=14.22, L=1848.6),
    "bar_L_lo": dict(A=314.1, I=16156.0, c=15.21, L=1778.7),
    "post":   dict(A=250.2, I=2089.0, c=5.0, J=6233.0),        # 25x10 flat, weak axis resists barrier load
    "guard":  dict(A=324.6, I=26887.0, c=12.5, J=34800.0),     # 25x25 hollow
    "cyan":   dict(A=624.8, I=32544.0, c=12.5, J=55078.0),     # 25x25 solid
    "axle":   dict(OD=25.24, ID=19.76, L=1305.0),
    "hook":   dict(t=5.0, w=11.9),                             # throat, min width by 72-angle slicing
    "mini":   dict(A=250.2, I=2089.0, c=5.0),                  # 25x10 bottom mini (lock pin)
}
SEC["axle"]["A"] = math.pi / 4 * (SEC["axle"]["OD"] ** 2 - SEC["axle"]["ID"] ** 2)
SEC["axle"]["I"] = math.pi / 64 * (SEC["axle"]["OD"] ** 4 - SEC["axle"]["ID"] ** 4)
HOOK_E = SEC["axle"]["OD"] / 2 + SEC["hook"]["w"] / 2   # load line (bar centre) to throat centroid

# ===================================================================== MATERIAL BASES
BASIS = {
    "A": dict(name="S355 steel structure + EN AW-6082-T6 treads (v2 locked basis, params.py)",
              s=dict(fy=355.0, gM=1.0, E=210000.0, G=81000.0, rho=7.85e-6),
              t=dict(fy=260.0, gM=1.1, E=70000.0, rho=2.70e-6)),
    "B": dict(name="all-aluminium: EN AW-6061-T6 structure + 6082-T6 treads (v1 revision)",
              s=dict(fy=240.0, gM=1.1, E=69000.0, G=26000.0, rho=2.70e-6),
              t=dict(fy=260.0, gM=1.1, E=70000.0, rho=2.70e-6)),
}

# ===================================================================== LOADS (Event column)
Q_UDL = 7.5e-3        # N/mm2  L4  stairs UDL 5.0-7.5 kN/m2 event (target 7.5); L19 platform 7.5
Q_UDL_MIN = 5.0e-3    # N/mm2  L4  lower bound of the event band
Q_PT = 3000.0         # N      L5  3.0 kN on 200x200 (Cat C)
H_LINE = 3.0          # N/mm   L33 guardrail line load 3.0 kN/m (C5 crowd)
H_PT = 1250.0         # N      L34 guardrail point 1.25 kN
BRIDGE_PT = 10000.0   # N      L26 footbridge 10 kN on 0.1x0.1 (informative for catwalk spans)
NOTIONAL = 0.025      # -      L7/L24 2.5 % of vertical
GAMMA_G, GAMMA_Q = 1.35, 1.5          # L44 EN 1990 STR
GAMMA_G_FAV, GAMMA_Q_DST = 0.9, 1.5   # L44 EN 1990 EQU (overturning)
FOS_OT = 1.5          # L40
F_VERT_MIN = 5.0      # Hz     L30 below this a dynamic (crowd) assessment is mandatory
MU = 0.30             # base friction steel foot on concrete/asphalt (conservative)


def defl_lim(L):
    return min(L / 100.0, 25.0)       # L6/L23 EN 12811-1


STATES = [  # key, label, lock, layout
    ("SINGLE_CATWALK", "Catwalk (flat)", "CATWALK", "SINGLE"),
    ("SINGLE_STANDARD", "Standard stair 35 deg", "STANDARD", "SINGLE"),
    ("SINGLE_STEEP", "Steep steps 49.4 deg", "STEEP", "SINGLE"),
    ("SINGLE_BAR", "Standard on static hook bar", "STANDARD", "BAR"),
    ("DOUBLE_CATWALK", "Double catwalk (end-to-end)", "CATWALK", "DOUBLE"),
    ("DOUBLE_STANDARD", "Double staircase", "STANDARD", "DOUBLE"),
    ("DOUBLE_STEEP", "Double steep", "STEEP", "DOUBLE"),
    ("WIDE_CATWALK_FULL", "Wide catwalk, handrails between", "CATWALK", "WIDE"),
    ("WIDE_CATWALK_MINI", "Wide catwalk, mini handrail between", "CATWALK", "WIDE_MINI"),
    ("WIDE_STANDARD", "Wide staircase", "STANDARD", "WIDE"),
    ("WIDE_STEEP", "Wide steep staircase", "STEEP", "WIDE"),
]


# ===================================================================== SELF WEIGHT
def self_weight(b):
    rs, rt = BASIS[b]["s"]["rho"], BASIS[b]["t"]["rho"]
    kg = {
        "treads 6x": 6 * SEC["tread"]["A"] * SEC["tread"]["L"] * rt,
        "guide bars 4x": sum(SEC[k]["A"] * SEC[k]["L"] for k in ("bar_R_up", "bar_R_lo", "bar_L_up", "bar_L_lo")) * rs,
        "axles 2x": 2 * SEC["axle"]["A"] * SEC["axle"]["L"] * rs,
        "posts 12x1000": 12 * SEC["post"]["A"] * 1000.0 * rs,
        "top posts 12x100": 12 * SEC["post"]["A"] * 100.0 * rs,
        "bottom minis 12x~165": 12 * SEC["mini"]["A"] * 165.0 * rs,
        "guardrails 2x": 2 * SEC["guard"]["A"] * RAIL_LEN * rs,
        "cyan handrails 2x": 2 * SEC["cyan"]["A"] * RAIL_LEN * rs,
        "rail brackets 12x": 12 * 250.0 * 134.0 * rs,
        "hooks/connectors/brackets (lump)": 2.0 * rs / 7.85e-6,
    }
    kg["TOTAL"] = sum(kg.values())
    hr_keys = ("posts 12x1000", "top posts 12x100", "bottom minis 12x~165", "guardrails 2x",
               "cyan handrails 2x", "rail brackets 12x")
    kg["_handrail_per_side"] = sum(kg[k] for k in hr_keys) / 2
    return kg


# ===================================================================== CLOSED-FORM BEAM TOOLS
def ss_point_loads(L, loads, EI, n=600):
    """Simply supported span L with transverse point loads [(a,P)]. Returns (Mmax, dmax, RA, RB)."""
    RB = sum(P * a for a, P in loads) / L
    RA = sum(P for _, P in loads) - RB
    Mmax, dmax = 0.0, 0.0
    for i in range(n + 1):
        x = L * i / n
        M = RA * x - sum(P * (x - a) for a, P in loads if a < x)
        d = 0.0
        for a, P in loads:                    # Roark: point load on SS beam
            bb = L - a
            if x <= a:
                d += P * bb * x * (L * L - bb * bb - x * x) / (6 * EI * L)
            else:
                d += P * a * (L - x) * (2 * L * x - x * x - a * a) / (6 * EI * L)
        Mmax, dmax = max(Mmax, abs(M)), max(dmax, abs(d))
    return Mmax, dmax, RA, RB


# ===================================================================== FE: 2D FRAME
class Frame2D:
    """Direct stiffness, 3 DOF/node (ux, uz, ry), beam elements with optional end releases."""

    def __init__(self):
        self.X, self.els, self.fix, self.F = [], [], {}, {}

    def node(self, x, z):
        self.X.append((float(x), float(z)))
        return len(self.X) - 1

    def beam(self, i, j, E, A, I, rel_i=False, rel_j=False, tag=""):
        self.els.append(dict(i=i, j=j, E=E, A=A, I=I, ri=rel_i, rj=rel_j, tag=tag))

    def support(self, n, dofs):
        self.fix.setdefault(n, set()).update(dofs)

    def load(self, n, fx=0.0, fz=0.0, m=0.0):
        f = self.F.setdefault(n, [0.0, 0.0, 0.0])
        f[0] += fx; f[1] += fz; f[2] += m

    def _kloc(self, e, L):
        E, A, I = e["E"], e["A"], e["I"]
        k = np.zeros((6, 6))
        a = E * A / L
        k[0, 0] = k[3, 3] = a; k[0, 3] = k[3, 0] = -a
        b = E * I / L ** 3
        kb = b * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                           [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        idx = [1, 2, 4, 5]
        for p in range(4):
            for q in range(4):
                k[idx[p], idx[q]] = kb[p, q]
        rel = [d for d, r in ((2, e["ri"]), (5, e["rj"])) if r]
        for d in rel:                       # static condensation of released rotations
            if k[d, d] > 0:
                k = k - np.outer(k[:, d], k[d, :]) / k[d, d]
                k[d, :] = 0; k[:, d] = 0
        return k

    def _T(self, c, s):
        T = np.zeros((6, 6))
        for o in (0, 3):
            T[o, o] = c; T[o, o + 1] = s; T[o + 1, o] = -s; T[o + 1, o + 1] = c; T[o + 2, o + 2] = 1
        return T

    def solve(self):
        n = len(self.X); N = 3 * n
        K = np.zeros((N, N)); F = np.zeros(N)
        cache = []
        for e in self.els:
            (x1, z1), (x2, z2) = self.X[e["i"]], self.X[e["j"]]
            L = math.hypot(x2 - x1, z2 - z1); c, s = (x2 - x1) / L, (z2 - z1) / L
            kl = self._kloc(e, L); T = self._T(c, s); kg = T.T @ kl @ T
            dof = [3 * e["i"], 3 * e["i"] + 1, 3 * e["i"] + 2, 3 * e["j"], 3 * e["j"] + 1, 3 * e["j"] + 2]
            K[np.ix_(dof, dof)] += kg
            cache.append((dof, kl, T, L))
        for nd, f in self.F.items():
            F[3 * nd:3 * nd + 3] += f
        # tiny rotational spring on nodes whose rotation is not stiffened by any beam (pure pinned nodes)
        for d in range(2, N, 3):
            if abs(K[d, d]) < 1e-9:
                K[d, d] = 1e-6
        fixed = sorted(3 * nd + d for nd, ds in self.fix.items() for d in ds)
        free = [d for d in range(N) if d not in fixed]
        Kff = K[np.ix_(free, free)]
        cond = np.linalg.cond(Kff)
        u = np.zeros(N)
        try:
            u[free] = np.linalg.solve(Kff, F[free])
        except np.linalg.LinAlgError:          # exactly singular -> mechanism
            return dict(u=np.full(N, np.inf), R=np.zeros(N), forces=[], cond=float("inf"))
        R = K @ u - F
        forces = []
        for (dof, kl, T, L), e in zip(cache, self.els):
            fl = kl @ (T @ u[dof])          # local end forces [N1,V1,M1,N2,V2,M2]
            forces.append(dict(tag=e["tag"], N=-fl[0], M1=fl[2], M2=-fl[5], V=fl[1], L=L))
        return dict(u=u, R=R, forces=forces, cond=cond)


def side_frame_fe(lock, b, q, w_self_tread, hr_side_N, bar_up, bar_lo, model, n_sub=8):
    """One side girder of one unit, world XZ. model: 'lower_only' | 'locked' | 'unlocked' | 'braced'.
    Tread link: rear pin on the lower bar -> nosing pin on the upper bar (vector LINK).
    'locked'  : bottom mini pins the tread to the lower bar -> link rigid to lower bar, pinned to upper.
    'unlocked': link pinned both ends (parallelogram) -> mechanism expected.
    'braced'  : 'locked' + a diagonal S355 25x10 flat per panel (proposed upgrade)."""
    Lk = LOCKS[lock]; th = math.radians(Lk["theta"])
    u = np.array([-math.cos(th), math.sin(th)])        # frame direction (up-run), world XZ
    E = BASIS[b]["s"]["E"]; Et = BASIS[b]["t"]["E"]; rho = BASIS[b]["s"]["rho"]
    fr = Frame2D()
    st = Lk["st"]
    # lower bar nodes: supports + stations + subdivisions
    xs = sorted(set([0.0, SPAN] + st + [SPAN * k / (n_sub * 6) for k in range(n_sub * 6 + 1)]))
    lo = {x: fr.node(*(u * x)) for x in xs}
    for a, c in zip(xs[:-1], xs[1:]):
        fr.beam(lo[a], lo[c], E, bar_lo["A"], bar_lo["I"], tag="lower")
        wseg = bar_lo["A"] * rho * G * (c - a)
        fr.load(lo[a], fz=-wseg / 2); fr.load(lo[c], fz=-wseg / 2)
    fr.support(lo[0.0], {0, 1}); fr.support(lo[SPAN], {1})
    Rk = Q_UDL_live = None
    per_tread = (q * P_FRAME * math.cos(th) + w_self_tread) * L_TREAD / 2 + hr_side_N / 6
    if model == "lower_only":
        for s in st:
            fr.load(lo[s], fz=-per_tread)
        return fr.solve(), per_tread
    link = np.array(LINK)
    up_nodes = []
    for s in st:
        p_lo = u * s; p_up = p_lo + link
        n_up = fr.node(*p_up); up_nodes.append((s, n_up))
        n_mid = fr.node(*((p_lo + p_up) / 2))
        rel = model == "unlocked"
        fr.beam(lo[s], n_mid, Et, SEC["tread"]["A"], SEC["tread"]["I_in_plane"], rel_i=rel, tag="tread")
        fr.beam(n_mid, n_up, Et, SEC["tread"]["A"], SEC["tread"]["I_in_plane"], rel_j=True, tag="tread")
        fr.load(n_mid, fz=-per_tread)
    # upper bar through the nosing pins (+ its self weight lumped to those pins)
    for (s0, a), (s1, c) in zip(up_nodes[:-1], up_nodes[1:]):
        fr.beam(a, c, E, bar_up["A"], bar_up["I"], tag="upper")
    wup = bar_up["A"] * bar_up["L"] * rho * G / len(up_nodes)
    for _, nd in up_nodes:
        fr.load(nd, fz=-wup)
    if model == "braced":
        for (s0, a), s1 in zip(up_nodes[:-1], st[1:]):
            fr.beam(a, lo[s1], E, 250.0, 0.0, rel_i=True, rel_j=True, tag="diag")
    return fr.solve(), per_tread


def envelope(res, tag):
    fs = [f for f in res["forces"] if f["tag"] == tag]
    if not fs:
        return 0.0, 0.0
    M = max(max(abs(f["M1"]), abs(f["M2"])) for f in fs)
    N = max(abs(f["N"]) for f in fs)
    return M, N


# ===================================================================== FE: BARRIER GRILLAGE (out of plane)
def barrier_grillage(lock, b, load_case):
    """Posts (vertical, fixed in the rail socket at tread level) + continuous guardrail + cyan rail.
    Out-of-plane DOFs per node: w (Y), ra (rot about run axis), rz (rot about vertical).
    load_case: 'point_top_mid' | 'point_top_post' | 'line_guard'  (ULS factored inside)."""
    Lk = LOCKS[lock]; th = math.radians(Lk["theta"])
    E = BASIS[b]["s"]["E"]; Gm = BASIS[b]["s"]["G"]
    g_h = P_FRAME * math.cos(th)
    n_post = 6
    X, els, F = [], [], {}

    def node(a, z):
        X.append((a, z)); return len(X) - 1
    base, cy, gr = [], [], []
    for i in range(n_post):
        a = i * g_h; z0 = Lk["deck"][i] - Lk["deck"][0]
        base.append(node(a, z0)); cy.append(node(a, z0 + Lk["hand"])); gr.append(node(a, z0 + Lk["guard"]))
        els.append((base[i], cy[i], SEC["post"]["I"], SEC["post"]["J"], "post_lo"))
        els.append((cy[i], gr[i], SEC["post"]["I"], SEC["post"]["J"], "post_up"))
    for i in range(n_post - 1):
        els.append((gr[i], gr[i + 1], SEC["guard"]["I"], SEC["guard"]["J"], "guard"))
        els.append((cy[i], cy[i + 1], SEC["cyan"]["I"], SEC["cyan"]["J"], "cyan"))
    # mid-span node on the guardrail between posts 2 and 3 for the mid point load
    if load_case == "point_top_mid":
        i = 2
        els = [e for e in els if not (e[0] == gr[i] and e[1] == gr[i + 1])]
        (a0, z0), (a1, z1) = X[gr[i]], X[gr[i + 1]]
        mid = node((a0 + a1) / 2, (z0 + z1) / 2)
        els += [(gr[i], mid, SEC["guard"]["I"], SEC["guard"]["J"], "guard"),
                (mid, gr[i + 1], SEC["guard"]["I"], SEC["guard"]["J"], "guard")]
        F[mid] = GAMMA_Q * H_PT
    elif load_case == "point_top_post":
        F[gr[2]] = GAMMA_Q * H_PT
    else:
        for i in range(n_post - 1):
            (a0, z0), (a1, z1) = X[gr[i]], X[gr[i + 1]]
            Ls = math.hypot(a1 - a0, z1 - z0)
            for nd in (gr[i], gr[i + 1]):
                F[nd] = F.get(nd, 0.0) + GAMMA_Q * H_LINE * Ls / 2
        # rail overhang beyond end posts (RAIL_LEN vs post run) lumped on end posts
        run = (n_post - 1) * P_FRAME
        over = max(0.0, RAIL_LEN - run) / 2
        F[gr[0]] = F.get(gr[0], 0.0) + GAMMA_Q * H_LINE * over
        F[gr[-1]] = F.get(gr[-1], 0.0) + GAMMA_Q * H_LINE * over
    n = len(X); N = 3 * n
    K = np.zeros((N, N)); Fv = np.zeros(N)
    cache = []
    for (i, j, I, J, tag) in els:
        (a1, z1), (a2, z2) = X[i], X[j]
        L = math.hypot(a2 - a1, z2 - z1); c, s = (a2 - a1) / L, (z2 - z1) / L
        EI, GJ = E * I, Gm * J
        kl = np.zeros((6, 6))   # local [w1, t1, b1, w2, t2, b2]
        kb = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                     [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        ib = [0, 2, 3, 5]
        for p in range(4):
            for qq in range(4):
                kl[ib[p], ib[qq]] = kb[p, qq]
        kt = GJ / L
        kl[1, 1] = kl[4, 4] = kt; kl[1, 4] = kl[4, 1] = -kt
        T = np.zeros((6, 6))
        for o in (0, 3):
            T[o, o] = 1.0
            T[o + 1, o + 1] = c; T[o + 1, o + 2] = s      # torsion rot  = c*ra + s*rz
            T[o + 2, o + 1] = -s; T[o + 2, o + 2] = c     # bending rot  = -s*ra + c*rz
        dof = [3 * i, 3 * i + 1, 3 * i + 2, 3 * j, 3 * j + 1, 3 * j + 2]
        K[np.ix_(dof, dof)] += T.T @ kl @ T
        cache.append((dof, kl, T, tag, L))
    for nd, f in F.items():
        Fv[3 * nd] += f
    fixed = [3 * nd + d for nd in base for d in (0, 1, 2)]
    free = [d for d in range(N) if d not in fixed]
    uu = np.zeros(N)
    uu[free] = np.linalg.solve(K[np.ix_(free, free)], Fv[free])
    Mpost, Mrail = 0.0, 0.0
    for dof, kl, T, tag, L in cache:
        fl = kl @ (T @ uu[dof])
        m = max(abs(fl[2]), abs(fl[5]))
        if tag.startswith("post"):
            Mpost = max(Mpost, m)
        else:
            Mrail = max(Mrail, m)
    wmax = max(abs(uu[3 * nd]) for nd in gr)
    return dict(M_post=Mpost, M_rail=Mrail, w_top=wmax, F_total=sum(F.values()))


# ===================================================================== CHECKS
INFO_PREFIXES = ("Girder bending, UNBRACED", "Girder deflection, UNBRACED", "Girder chord stress, LOCKED truss",
                 "Girder deflection, LOCKED truss", "FE: lower bar alone", "FE: UPGRADE braced",
                 "Joint WITH mid support", "Footbridge")
UPGRADED = False       # set by run_upgraded(): anchors on free-standing catwalks, trestle under double joints


def run(b="A", verbose=True):
    B = BASIS[b]; fy_s = B["s"]["fy"] / B["s"]["gM"]; fy_t = B["t"]["fy"] / B["t"]["gM"]
    sw = self_weight(b)
    W_unit = sw["TOTAL"] * G
    hr_side_N = sw["_handrail_per_side"] * G
    w_self_tread = SEC["tread"]["A"] * B["t"]["rho"] * G            # N/mm along tread
    rows = []

    def ck(state, ref, check, demand, capacity, unit, util=None, note="", method="hand"):
        if util is None:
            util = demand / capacity if capacity else float("inf")
        res = "PASS" if util <= 1.0 else "FAIL"
        if check.startswith(INFO_PREFIXES):
            res = "INFO"                       # model bound / validation row, not a code check
        elif check.startswith("FE: UNLOCKED"):
            res = "CONDITION"                  # operating rule: lock before loading
        rows.append(dict(basis=b, state=state, ref=ref, check=check, method=method,
                         demand=round(demand, 3), capacity=round(capacity, 3), unit=unit,
                         util=round(util, 3), result=res, note=note))
        return util

    fe_cache = {}
    for key, label, lock, layout in STATES:
        Lk = LOCKS[lock]; th = math.radians(Lk["theta"]); c = math.cos(th)
        catwalk = Lk["theta"] == 0.0
        # ---------------- TREAD (identical per unit in every layout)
        gp = P_FRAME * c
        wk = Q_UDL * gp
        L = L_TREAD; EIt = B["t"]["E"] * SEC["tread"]["I"]; Wt = SEC["tread"]["I"] / SEC["tread"]["c"]
        M = (GAMMA_Q * wk + GAMMA_G * w_self_tread) * L * L / 8
        ck(key, "L4", "Tread bending, 7.5 kN/m2 UDL", M / 1e6, Wt * fy_t / 1e6, "kNm")
        M = GAMMA_Q * Q_PT * L / 4 + GAMMA_G * w_self_tread * L * L / 8
        ck(key, "L5", "Tread bending, 3 kN point", M / 1e6, Wt * fy_t / 1e6, "kNm")
        d = max(5 * wk * L ** 4 / (384 * EIt), Q_PT * L ** 3 / (48 * EIt))
        ck(key, "L6", "Tread deflection (SLS) <= L/100 & 25", d, defl_lim(L), "mm")
        # ---------------- SIDE GIRDER (per unit, weakest side = R)
        per_tread_k = (Q_UDL * gp + w_self_tread) * L_TREAD / 2 + hr_side_N / 6
        per_tread_d = (GAMMA_Q * Q_UDL * gp + GAMMA_G * w_self_tread) * L_TREAD / 2 + GAMMA_G * hr_side_N / 6
        up, lo = SEC["bar_R_up"], SEC["bar_R_lo"]
        EI_s = B["s"]["E"]
        bar_w = lambda s_: s_["A"] * B["s"]["rho"] * G
        loads_d = [(s, per_tread_d * c) for s in Lk["st"]]
        # distributed bar self weight -> 12 lumped points
        for k in range(12):
            loads_d.append((SPAN * (k + 0.5) / 12, GAMMA_G * (bar_w(lo) + bar_w(up)) * SPAN / 12 * c))
        Md, _, RAd, RBd = ss_point_loads(SPAN, loads_d, 1.0)
        loads_k = [(s, per_tread_k * c) for s in Lk["st"]]
        _, dk_lo, _, _ = ss_point_loads(SPAN, loads_k, EI_s * lo["I"])
        _, dk_sh, _, _ = ss_point_loads(SPAN, loads_k, EI_s * (lo["I"] + up["I"]))
        # (a) as drawn: independent bars sharing (upper bound on unbraced capacity)
        Mrd_sh = (up["I"] / up["c"] + lo["I"] / lo["c"]) * fy_s
        ck(key, "L4/L60", "Girder bending, UNBRACED bars (upper+lower share)", Md / 1e6, Mrd_sh / 1e6, "kNm",
           note="optimistic bound: both bars at yield together")
        ck(key, "L6", "Girder deflection, UNBRACED (SLS)", dk_sh, defl_lim(SPAN), "mm")
        # (b) locked truss/Vierendeel bound: chords = bars, lever = bar separation
        dsep = Lk["d_sep"]
        Nch = Md / dsep
        sig = Nch / min(up["A"], lo["A"])
        ck(key, "L4/L60", f"Girder chord stress, LOCKED truss bound (d={dsep:.0f} mm)", sig, fy_s, "MPa",
           note="ideal triangulated upper bound")
        I_tr = up["A"] * lo["A"] / (up["A"] + lo["A"]) * dsep ** 2 + up["I"] + lo["I"]
        _, dk_tr, _, _ = ss_point_loads(SPAN, loads_k, EI_s * I_tr)
        ck(key, "L6", "Girder deflection, LOCKED truss bound (SLS)", dk_tr, defl_lim(SPAN), "mm")
        # FE: locked Vierendeel (actual lock), and unlocked parallelogram (mechanism check)
        fe_key = (lock, b)
        if fe_key not in fe_cache:
            r_lo, _ = side_frame_fe(lock, b, Q_UDL * GAMMA_Q, w_self_tread * GAMMA_G, hr_side_N * GAMMA_G, up, lo, "lower_only")
            r_lk, _ = side_frame_fe(lock, b, Q_UDL * GAMMA_Q, w_self_tread * GAMMA_G, hr_side_N * GAMMA_G, up, lo, "locked")
            r_ul, _ = side_frame_fe(lock, b, Q_UDL * GAMMA_Q, w_self_tread * GAMMA_G, hr_side_N * GAMMA_G, up, lo, "unlocked")
            r_br, _ = side_frame_fe(lock, b, Q_UDL * GAMMA_Q, w_self_tread * GAMMA_G, hr_side_N * GAMMA_G, up, lo, "braced")
            s_lo, _ = side_frame_fe(lock, b, Q_UDL, w_self_tread, hr_side_N, up, lo, "locked")
            s_br, _ = side_frame_fe(lock, b, Q_UDL, w_self_tread, hr_side_N, up, lo, "braced")
            fe_cache[fe_key] = (r_lo, r_lk, r_ul, r_br, s_lo, s_br)
        r_lo, r_lk, r_ul, r_br, s_lk, s_br = fe_cache[fe_key]
        M_lo_only, _ = envelope(r_lo, "lower")
        ck(key, "L4/L60", "FE: lower bar alone (validates hand statics)", M_lo_only / 1e6, lo["I"] / lo["c"] * fy_s / 1e6,
           "kNm", method="FE", note=f"hand SS moment {Md/1e6:.3f} kNm")
        Mu, Nu = envelope(r_lk, "upper"); Ml, Nl = envelope(r_lk, "lower")
        s_up = Mu / (up["I"] / up["c"]) + Nu / up["A"]; s_lo = Ml / (lo["I"] / lo["c"]) + Nl / lo["A"]
        ck(key, "L4/L60", "FE: girder stress, LOCKED Vierendeel (actual lock)", max(s_up, s_lo), fy_s, "MPa", method="FE",
           note=f"upper {s_up:.0f} / lower {s_lo:.0f} MPa")
        dl = max(abs(s_lk["u"][1::3]))
        ck(key, "L6", "FE: girder deflection, LOCKED Vierendeel (SLS)", dl, defl_lim(SPAN), "mm", method="FE")
        mech = r_ul["cond"] > 1e12 or max(abs(r_ul["u"][1::3])) > 1e4
        ck(key, "-", "FE: UNLOCKED parallelogram is a mechanism", 1.0 if mech else 0.0, 0.5, "flag",
           util=2.0 if mech else 0.0, method="FE",
           note="handrails/minis MUST be inserted before loading" if mech else "stable without lock")
        Mu, Nu = envelope(r_br, "upper"); Ml, Nl = envelope(r_br, "lower"); _, Nd = envelope(r_br, "diag")
        s_up = Mu / (up["I"] / up["c"]) + Nu / up["A"]; s_lo = Ml / (lo["I"] / lo["c"]) + Nl / lo["A"]
        ck(key, "L4/L60", "FE: UPGRADE braced (25x10 diagonal per panel)", max(s_up, s_lo, Nd / 250.0), fy_s, "MPa",
           method="FE", note=f"diag force {Nd/1e3:.1f} kN")
        # ---------------- SUPPORTS / CONNECTIONS (per side)
        V = max(RAd, RBd)
        A_ax = SEC["axle"]["A"]
        ck(key, "L61", "Axle tube shear (per side)", 2 * V / A_ax, fy_s / math.sqrt(3), "MPa")
        top_hook = layout in ("BAR", "DOUBLE") or not catwalk
        if top_hook:
            t, w = SEC["hook"]["t"], SEC["hook"]["w"]
            e_h = SEC["axle"]["OD"] / 2 + w / 2
            sig = RBd / (t * w) + RBd * e_h / (t * w * w / 6)
            ck(key, "L61", f"Top hook ({t:.0f}x{w:.1f} throat) tension+bending", sig, fy_s, "MPa",
               note=f"hook load {RBd/1e3:.2f} kN, e={e_h:.1f} mm")
        sig_b = per_tread_d / (2 * 5.0 * 20.0)
        ck(key, "L61", "Nosing pin bearing on 2x5 mm skins (d=20 assumed)", sig_b, 1.5 * fy_s, "MPa")
        # ---------------- BARRIERS
        if layout != "WIDE_MINI" or True:
            Wp = SEC["post"]["I"] / SEC["post"]["c"]
            h = Lk["guard"]
            ck(key, "L34", "Post bending, 1.25 kN point at top (single post)", GAMMA_Q * H_PT * h / 1e6, Wp * fy_s / 1e6, "kNm")
            ck(key, "L33", "Post bending, 3.0 kN/m line (tributary)", GAMMA_Q * H_LINE * P_FRAME * h / 1e6, Wp * fy_s / 1e6, "kNm")
            gk = ("bar", lock, b)
            if gk not in fe_cache:
                fe_cache[gk] = {lc: barrier_grillage(lock, b, lc) for lc in ("point_top_mid", "point_top_post", "line_guard")}
            gg = fe_cache[gk]
            Mfe = max(gg["point_top_mid"]["M_post"], gg["point_top_post"]["M_post"])
            ck(key, "L34", "FE grillage: post moment, 1.25 kN point (rails share)", Mfe / 1e6, Wp * fy_s / 1e6, "kNm", method="FE",
               note=f"top defl {max(gg['point_top_mid']['w_top'], gg['point_top_post']['w_top']):.0f} mm (ULS)")
            ck(key, "L33", "FE grillage: post moment, 3.0 kN/m line", gg["line_guard"]["M_post"] / 1e6, Wp * fy_s / 1e6, "kNm",
               method="FE", note=f"top defl {gg['line_guard']['w_top']:.0f} mm (ULS)")
            Wr = SEC["guard"]["I"] / SEC["guard"]["c"]
            Mr = max(GAMMA_Q * H_LINE * P_FRAME ** 2 / 8, GAMMA_Q * H_PT * P_FRAME / 4)
            ck(key, "L33/34", "Guardrail bending between posts", Mr / 1e6, Wr * fy_s / 1e6, "kNm")
            ck(key, "G64", "Guardrail height >= 1100 above pitch line", 1100.0, Lk["guard"], "mm", util=1100.0 / Lk["guard"])
        # ---------------- GLOBAL STABILITY
        n_units = 2 if layout in ("DOUBLE", "WIDE", "WIDE_MINI") else 1
        width = W_PITCH * (2 if layout in ("WIDE", "WIDE_MINI") else 1)
        free_standing = catwalk and layout not in ("BAR",)
        if free_standing:
            L_rail = RAIL_LEN * (2 if layout == "DOUBLE" else 1)
            H_arm = Lk["deck"][0] + Lk["guard"]
            M_ot = H_LINE * L_rail * H_arm
            lever = width / 2
            M_st = W_unit * n_units * lever
            Hs = H_LINE * L_rail
            if UPGRADED:
                T_anchor = max(0.0, GAMMA_Q_DST * M_ot - GAMMA_G_FAV * M_st) / width / 2
                V_anchor = max(0.0, GAMMA_Q * Hs - MU * GAMMA_G_FAV * W_unit * n_units) / 4
                ck(key, "L40/L41", "Overturning: 4 ground anchors (design tension per anchor)", T_anchor / 1e3,
                   T_anchor / 1e3 if T_anchor else 1.0, "kN", util=1.0 if T_anchor else 0.0,
                   note=f"specify anchors >= {T_anchor/1e3:.1f} kN tension + {V_anchor/1e3:.1f} kN shear each "
                        f"(or {max(0.0, (FOS_OT * M_ot - M_st) / (G * lever)):.0f} kg ballast)")
            else:
                ck(key, "L40", "Overturning (EQU) crowd on outer rail, self-weight only",
                   GAMMA_Q_DST * M_ot / 1e6, GAMMA_G_FAV * M_st / 1e6, "kNm",
                   note=f"FoS={M_st / M_ot:.2f} (need {FOS_OT}); ballast/anchor "
                        f"{max(0.0, (FOS_OT * M_ot - M_st) / (G * lever)):.0f} kg")
                ck(key, "L7/L24", "Sliding under crowd line load (mu=0.30, no crowd weight)", GAMMA_Q * Hs / 1e3,
                   MU * GAMMA_G_FAV * W_unit * n_units / 1e3, "kN")
            # frequency (bridge-like span); unit mass on its support span
            EIsum = B["s"]["E"] * sum(SEC[k]["I"] for k in ("bar_R_up", "bar_R_lo", "bar_L_up", "bar_L_lo"))
            m_l = sw["TOTAL"] / SPAN
            f1 = math.pi / (2 * SPAN ** 2) * math.sqrt(EIsum * 1e-3 / (m_l * 1e-3)) * math.sqrt(1e3)
            ck(key, "L30", "Vertical natural frequency >= 5 Hz (else dynamic check)", F_VERT_MIN, f1, "Hz",
               util=F_VERT_MIN / f1, note="unbraced bars, self weight only")
            Mb = GAMMA_Q * BRIDGE_PT * SPAN / 4 / 2
            if not UPGRADED:
                ck(key, "L26", "Footbridge 10 kN point (informative): girder", Mb / 1e6, Mrd_sh / 1e6, "kNm",
                   note="only if the catwalk is classed as a footbridge (service-vehicle access)")
        else:
            ck(key, "L40", "Overturning", 0.0, 1.0, "-", util=0.0,
               note="restrained: top hooked to landing/bar (bar must be anchored)")
        # ---------------- END-TO-END JOINT
        if layout == "DOUBLE":
            w_d = sum(P for _, P in loads_d) / SPAN
            M_joint = w_d * (2 * SPAN) ** 2 / 8
            t, w = SEC["hook"]["t"], SEC["hook"]["w"]
            F_hook = fy_s / (1 / (t * w) + (SEC["axle"]["OD"] / 2 + w / 2) / (t * w * w / 6))
            M_cap = F_hook * 157.0
            if not UPGRADED:
                ck(key, "L61", "Joint WITHOUT mid support: moment vs hook+connector couple",
                   M_joint / 1e6, M_cap / 1e6, "kNm", note="=> a support/trestle under the joint is REQUIRED")
            ck(key, "L51", "Joint WITH mid support: support reaction (per side)", 2 * RBd / 1e3, 1e9, "kN",
               util=0.0, note=f"design trestle for {2 * 2 * RBd / 1e3:.1f} kN ULS total")
    return rows, sw


def girder_utils(lock, b, q, lo=None, up=None):
    """Utilisations of the side girder at characteristic UDL q (N/mm2) for the three girder models."""
    B = BASIS[b]; fy_s = B["s"]["fy"] / B["s"]["gM"]
    sw = self_weight(b); hr = sw["_handrail_per_side"] * G
    wst = SEC["tread"]["A"] * B["t"]["rho"] * G
    up = up or SEC["bar_R_up"]; lo = lo or SEC["bar_R_lo"]
    Lk = LOCKS[lock]; c = math.cos(math.radians(Lk["theta"])); gp = P_FRAME * c
    pd = (GAMMA_Q * q * gp + GAMMA_G * wst) * L_TREAD / 2 + GAMMA_G * hr / 6
    loads = [(s, pd * c) for s in Lk["st"]]
    for k in range(12):
        loads.append((SPAN * (k + 0.5) / 12, GAMMA_G * (up["A"] + lo["A"]) * B["s"]["rho"] * G * SPAN / 12 * c))
    Md, _, _, _ = ss_point_loads(SPAN, loads, 1.0, n=200)
    u_unbr = Md / ((up["I"] / up["c"] + lo["I"] / lo["c"]) * fy_s)
    u_truss = Md / Lk["d_sep"] / min(up["A"], lo["A"]) / fy_s
    r, _ = side_frame_fe(lock, b, q * GAMMA_Q, wst * GAMMA_G, hr * GAMMA_G, up, lo, "locked")
    Mu, Nu = envelope(r, "upper"); Ml, Nl = envelope(r, "lower")
    s = max(Mu / (up["I"] / up["c"]) + Nu / up["A"], Ml / (lo["I"] / lo["c"]) + Nl / lo["A"])
    return dict(unbraced=u_unbr, truss=u_truss, locked_fe=s / fy_s)


def rating(b="A"):
    """Max characteristic UDL (kN/m2) each lock's side girder can carry, per girder model."""
    out = {}
    for lock in LOCKS:
        res = {}
        for model in ("unbraced", "truss", "locked_fe"):
            lo_q, hi_q = 0.0, 30e-3
            for _ in range(30):
                q = (lo_q + hi_q) / 2
                if girder_utils(lock, b, q)[model] <= 1.0:
                    lo_q = q
                else:
                    hi_q = q
            res[model] = round(lo_q * 1e3, 2)
        out[lock] = res
    return out


def required_lower_bar(b="A"):
    """Minimum depth h of a 25-wide solid lower bar (fits the channel) so the LOCKED girder passes
    at 7.5 kN/m2 (FE), per lock. Upper bar kept as drawn."""
    out = {}
    for lock in LOCKS:
        lo_h, hi_h = 20.0, 200.0
        for _ in range(30):
            h = (lo_h + hi_h) / 2
            sec = dict(A=25.0 * h, I=25.0 * h ** 3 / 12, c=h / 2, L=SEC["bar_R_lo"]["L"])
            if girder_utils(lock, b, Q_UDL, lo=sec)["locked_fe"] <= 1.0:
                hi_h = h
            else:
                lo_h = h
        out[lock] = math.ceil(hi_h)
    return out


def required_hook(b="A", V=None):
    """Throat width w needed for t=5 and t=10 hooks for the governing top-hook load V (N)."""
    fy = BASIS[b]["s"]["fy"] / BASIS[b]["s"]["gM"]
    res = {}
    for t in (5.0, 8.0, 10.0):
        w = 5.0
        while w < 80:
            e = SEC["axle"]["OD"] / 2 + w / 2
            if V / (t * w) + V * e / (t * w * w / 6) <= fy:
                break
            w += 0.5
        res[f"t={t:.0f}"] = w
    return res


def required_sections(b="A"):
    B = BASIS[b]; fy = B["s"]["fy"] / B["s"]["gM"]; E = B["s"]["E"]
    out = {}
    # stringer as a single deep flat (25 wide channel) carrying one side alone, standard 35 deg (governing SS moment)
    sw = self_weight(b)
    for lock in LOCKS:
        Lk = LOCKS[lock]; c = math.cos(math.radians(Lk["theta"]))
        gp = P_FRAME * c
        wt = SEC["tread"]["A"] * B["t"]["rho"] * G
        pd = (GAMMA_Q * Q_UDL * gp + GAMMA_G * wt) * L_TREAD / 2 + GAMMA_G * sw["_handrail_per_side"] * G / 6
        pk = (Q_UDL * gp + wt) * L_TREAD / 2 + sw["_handrail_per_side"] * G / 6
        Md, _, _, _ = ss_point_loads(SPAN, [(s, pd * c) for s in Lk["st"]], 1.0)
        W_req = Md / fy
        _, d1, _, _ = ss_point_loads(SPAN, [(s, pk * c) for s in Lk["st"]], E * 1.0)
        I_req = d1 / defl_lim(SPAN)
        h_W = math.sqrt(6 * W_req / 25.0); h_I = (12 * I_req / 25.0) ** (1 / 3)
        out[f"stringer_{lock}"] = dict(M_Ed_kNm=round(Md / 1e6, 3), W_req_mm3=round(W_req), I_req_mm4=round(I_req),
                                       flat_25_wide_depth_mm=math.ceil(max(h_W, h_I)))
    # posts: 1.25 kN at guard height (steep = tallest)
    h = max(L["guard"] for L in LOCKS.values())
    Wreq = GAMMA_Q * H_PT * h / fy
    cands = []
    for bo, t in ((30, 3), (40, 3), (40, 4), (50, 3), (50, 4), (50, 5), (60, 4)):
        I = (bo ** 4 - (bo - 2 * t) ** 4) / 12
        cands.append((f"SHS {bo}x{bo}x{t}", round(I / (bo / 2))))
    ok = [n for n, W in cands if W >= Wreq]
    out["post"] = dict(W_req_mm3=round(Wreq), lightest_SHS=ok[0] if ok else None, table=cands)
    # hook throat for the governing top reaction (standard stair) at t=10
    return out


def run_upgraded(b="A"):
    """Re-run every state with the recommended upgrades; lower-bar depth searched for ULS stress AND SLS
    deflection (locked FE) in every lock."""
    global UPGRADED
    import copy
    keep = copy.deepcopy(SEC)
    fy = BASIS[b]["s"]["fy"] / BASIS[b]["s"]["gM"]
    wst = SEC["tread"]["A"] * BASIS[b]["t"]["rho"] * G
    hr = self_weight(b)["_handrail_per_side"] * G
    h = 20.0
    while h < 200:
        sec = dict(A=25.0 * h, I=25.0 * h ** 3 / 12, c=h / 2, L=SEC["bar_R_lo"]["L"])
        ok = True
        for lock in LOCKS:
            if girder_utils(lock, b, Q_UDL, lo=sec)["locked_fe"] > 1.0:
                ok = False; break
            r, _ = side_frame_fe(lock, b, Q_UDL, wst, hr, SEC["bar_R_up"], sec, "locked")
            if max(abs(r["u"][1::3])) > defl_lim(SPAN):
                ok = False; break
        if ok:
            break
        h += 1.0
    h = math.ceil(h / 5.0) * 5.0                       # round up to a stock flat size
    for k in ("bar_R_lo", "bar_L_lo"):
        SEC[k].update(A=25.0 * h, I=25.0 * h ** 3 / 12, c=h / 2)
    bo, t = 40.0, 4.0
    SEC["post"].update(A=bo * bo - (bo - 2 * t) ** 2, I=(bo ** 4 - (bo - 2 * t) ** 4) / 12, c=bo / 2,
                       J=4 * ((bo - t) ** 2) ** 2 * t / (4 * (bo - t)))
    SEC["hook"].update(t=10.0, w=16.0)
    UPGRADED = True
    try:
        rows, sw = run(b)
    finally:
        UPGRADED = False
        SEC.clear(); SEC.update(keep)
    spec = dict(lower_guide_bar=f"25 x {h:.0f} solid flat S355 (both sides)", posts="SHS 40x40x4 S355",
                hooks="10 mm plate, 16 mm throat, S355", catwalk_free_standing="4 ground anchors or ballast (see rows)",
                double_joint="support trestle under every end-to-end joint",
                lock="handrails/bottom minis inserted before any load (unlocked = mechanism)")
    return rows, spec


def print_table(rows):
    w = max(len(r["check"]) for r in rows)
    cur = None
    for r in rows:
        if r["state"] != cur:
            cur = r["state"]
            print(f"\n=== {cur}  [{r['basis']}]")
        print(f"  {r['ref']:7} {r['method']:4} {r['check']:{w}}  {r['demand']:>10} / {r['capacity']:<10} {r['unit']:4}"
              f" util {r['util']:>7}  {r['result']}  {r['note']}")


if __name__ == "__main__":
    allrows, summary = [], {}
    for b in ("A", "B"):
        rows, sw = run(b)
        allrows += rows
        rt = rating(b)
        rq = required_sections(b)
        rlb = required_lower_bar(b)
        vhook = max(float(r["note"].split("hook load ")[1].split(" kN")[0]) * 1e3
                    for r in rows if r["check"].startswith("Top hook"))
        rh = required_hook(b, vhook)
        summary[b] = dict(basis=BASIS[b]["name"], self_weight_kg={k: round(v, 2) for k, v in sw.items()},
                          rating_qk_max_kN_m2=rt, required_sections=rq,
                          required_lower_bar_depth_mm=rlb, governing_hook_load_N=round(vhook),
                          required_hook_throat_mm=rh)
        print_table(rows)
        print(f"\nBASIS {b}: self weight per unit {sw['TOTAL']:.1f} kg")
        print("Max characteristic UDL (kN/m2) per lock:", json.dumps(rt))
        print("Lower bar depth needed (25 wide, locked FE, 7.5 kN/m2):", json.dumps(rlb))
        print(f"Hook throat needed for {vhook/1e3:.2f} kN:", json.dumps(rh))
        print("Post:", rq["post"]["W_req_mm3"], "mm3 ->", rq["post"]["lightest_SHS"])
    up_rows, up_spec = run_upgraded("A")
    print_table(up_rows)
    print("UPGRADE SPEC:", json.dumps(up_spec))
    print(f"UPGRADED BASIS A: {sum(1 for r in up_rows if r['result'] in ('PASS','FAIL'))} code checks, "
          f"{sum(1 for r in up_rows if r['result'] == 'FAIL')} FAIL")
    with open(os.path.join(HERE, "results_handcalc_fe.json"), "w") as f:
        json.dump(dict(rows=allrows, summary=summary, upgraded=dict(spec=up_spec, rows=up_rows)), f, indent=1)
    with open(os.path.join(HERE, "results_handcalc_fe.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(allrows[0].keys()))
        wr.writeheader(); wr.writerows(allrows)
    n_fail = sum(1 for r in allrows if r["result"] == "FAIL" and r["basis"] == "A")
    print(f"\nBASIS A: {sum(1 for r in allrows if r['basis']=='A')} checks, {n_fail} FAIL")
