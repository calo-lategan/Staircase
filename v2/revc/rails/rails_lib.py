"""Rev C guide rails - FINAL family (rail agent, 26 Sep 2026): OPEN channels that nest (owner constraint 3).
  B = right rails: open channel (pin leg + web + outer leg from n = 29 to the web), open toward the other rail.
  A = left rails:  open channel (pin leg + web + edge lip), no outer leg, so a neighbour's B rail slides in sideways
      (across the stair) and sits inside with 1 mm clearance.
All four rails open TOWARD each other (web at the far face): the rails grow away from each other and touch at catwalk
(pin-leg tips with interleaved tabs). Each pin leg carries an inside bulb over the tip zone (n 0..27): pin metal,
washer seat, pole bearing at the pin line (lower rails), torsional stiffness. It sits below the nested rail's outer leg
and the neighbour's caps, so it does not block nesting.
Cross-section coordinates of a rail:
  y = across the stair, from the step-side face of the pin leg (bulb excluded) into the rail;
  n = square to the rail in the side plane, from the touching plane, positive AWAY from the other rail.
Barrier path: the pole bears on the web slots (far face); the offset from the pin line twists the open channel, and
every pin station is a preloaded clamp (castle cap nut M16 on a D30 washer + step-side pad) - see rail_design.md.
Material EN AW-6082-T6 extrusion, EN 1999-1-1: f0 250 (250 used for all t), gM1 1.1, gM2 = gMp 1.25. No welds."""
import math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.join(HERE, "..", "..", "final")
F0, GM1, GMP = 250.0, 1.1, 1.25
FD = F0 / GM1
E_AL = 70000.0

# ------------------------------------------------------------------ step pins (owner's L step, positions unchanged)
REAR, FRONT = (25.0, 12.5), (225.0, 37.5)
LINK = (FRONT[0] - REAR[0], FRONT[1] - REAR[1])
L_LINK = math.hypot(*LINK); PHI = math.degrees(math.atan2(LINK[1], LINK[0]))
PITCH = math.hypot(250.0, 175.0)
STATES = {"catwalk": 0.0, "standard": 35.0, "steep": 49.4}
C_PIN = 12.5
def sep(theta_deg):
    return L_LINK * math.sin(math.radians(theta_deg + PHI))

# ------------------------------------------------------------------ pole variants
POLES = {"box80": dict(W=80.0, along=25.0, A=2 * 80 * 2.5 + 2 * 20 * 5.5, I_inplane=2 * 80 * 2.5 * 11.25 ** 2 + 2 * 5.5 * 20 ** 3 / 12,
                       note="production: custom 6082-T6 box 25 along x 80 across, walls 5.5 (across faces) / 2.5 (mass-budget agent)"),
         "plate55": dict(W=55.0, along=25.0, A=55 * 25.0, I_inplane=55 * 25.0 ** 3 / 12, note="prototype: 25 mm plate, 55 across (poles review)")}
POLE_KEY = os.environ.get("POLE", "box80")
POLE = POLES[POLE_KEY]
RAIL_POLE = POLES[os.environ.get("RAIL_POLE", "box80")]   # rails are always drawn for the production pole; a smaller pole only gets narrower slots
TONGUE_W = 35.0

# ------------------------------------------------------------------ pins and pin-station clamp
PIN_D, HOLE_D = 16.0, 17.0          # 1.4462 duplex, h9 / hole 17.0 +0.1/0 reamed on a jig
WASH_R = 15.0                       # D30 x 4 stainless clamp washer under the cap
CAP_OD, CAP_LEN = 28.0, 24.0        # castle cap nut M16, round 28, 24 incl. crown
N_CAPS = C_PIN + WASH_R             # caps/washers occupy n <= 27.5 at every pin station
PAD = 1.0                           # PTFE-faced stainless shim, step end block to the pin-leg bulb

# ------------------------------------------------------------------ profiles
T_LEG = 6.0; T_OUT = 5.0
T_WEB_LO = float(os.environ.get("T_WEB_LO", 7.0)); T_WEB_UP = float(os.environ.get("T_WEB_UP", 12.0))
T_WEB = T_WEB_LO
H_BULB = 27.0                        # inside bulb on every pin leg, n = 0..27 (tip zone): pin metal, washer seat, pole bearing, torsion
BULB = {"A": 14.0, "B": 8.0}         # bulb thickness into the rail: A reaches the pole across the nested B's outer zone
LIP = (6.0, 12.0)                    # A: edge lip at the web's free edge, standing away from the rail (outside the nest)
CLR = 1.0                            # nesting clearance
LIG_IN = 8.0                         # web ligament pin side (B)
LIG_OUT = {"lo": 8.0, "up": 8.0}     # web ligament outer side (B), backed by B's outer leg
SLOT_W = POLE["W"] + 1.0
SLOT_W_RAIL = RAIL_POLE["W"] + 1.0
N_OUT_B = N_CAPS + 1.5               # B outer leg starts above the neighbour's caps and bulb: n = 29
OUT_UP_LEN = float(os.environ.get("OUT_UP_LEN", 8.0))    # B upper outer leg length (n 29 .. 37), web above it
W_B = {lv: T_LEG + LIG_IN + SLOT_W_RAIL + LIG_OUT[lv] + T_OUT for lv in ("lo", "up")}
W_A = {lv: T_LEG + CLR + W_B[lv] for lv in ("lo", "up")}   # A web ends flush with the nested B's pin-leg face
D_LO_B = float(os.environ.get("D_LO_B", 60.0)); D_LO_A = D_LO_B + CLR + T_WEB_LO
D_UP_B = N_OUT_B + OUT_UP_LEN + T_WEB_UP; D_UP_A = D_UP_B + CLR + T_WEB_UP
DEPTH = {"A_lo": D_LO_A, "B_lo": D_LO_B, "A_up": D_UP_A, "B_up": D_UP_B}
RAIL_OF = {("L", "lo"): "A_lo", ("L", "up"): "A_up", ("R", "lo"): "B_lo", ("R", "up"): "B_up"}
WIDTH = {"A_lo": W_A["lo"], "A_up": W_A["up"], "B_lo": W_B["lo"], "B_up": W_B["up"]}
def slot_y(kind):
    """pole slot across the web (y from the pin leg's step-side face), starting at the bulb face so the pole bears on the
    bulb (lower rails). For the production pole A's slot then lines up with the nested B's slot (20..101 = 115 - (95..14))."""
    b0 = T_LEG + BULB[kind[0]]
    return (b0, b0 + SLOT_W)
F_PIN_DESIGN = 8200.0

def t88_a(F, t, d0):
    return F * GMP / (2 * t * F0) + 2 * d0 / 3
T_PINLEG = T_LEG + min(BULB.values())                    # 14 mm of metal at the hole (B governs)
TAB_R = HOLE_D / 2 + t88_a(F_PIN_DESIGN, T_PINLEG, HOLE_D) + 0.5
TAB_W = 2 * TAB_R; TAB_H = TAB_R - C_PIN
NOTCH_DEPTH = TAB_H + 2.0; NOTCH_CLR = 4.0; NOTCH_W = TAB_W + 2 * NOTCH_CLR
SLOT_LEN = {"standard": 25.0 / math.cos(math.radians(35)) + 8.0 * math.tan(math.radians(35)) + 1.0,
            "catwalk": 25.0 + 1.0,
            "steep": 25.0 / math.cos(math.radians(49.4)) + 8.0 * math.tan(math.radians(49.4)) + 1.0}
UP_SLOTS = {"standard+catwalk": SLOT_LEN["standard"], "steep": SLOT_LEN["steep"]}
LO_SLOTS = {"standard+steep": SLOT_LEN["steep"], "catwalk": SLOT_LEN["catwalk"]}


def t_web(kind):
    return T_WEB_LO if kind.endswith("lo") else T_WEB_UP

def n_web(kind):
    return DEPTH[kind] - t_web(kind) / 2

def profile(kind):
    D = DEPTH[kind]; W = WIDTH[kind]; tw = t_web(kind); bu = BULB[kind[0]]
    r = [(0, 0, T_LEG, D - tw, "pin leg"), (T_LEG, 0, T_LEG + bu, H_BULB, "bulb"), (0, D - tw, W, D, "web")]
    if kind[0] == "B":
        r += [(W - T_OUT, N_OUT_B, W, D - tw, "outer leg")]
    if kind[0] == "A":
        r += [(W - LIP[0], D, W, D + LIP[1], "lip")]
    return r


_BT = [(1.0, 0.141, 0.208), (1.5, 0.196, 0.231), (2.0, 0.229, 0.246), (3.0, 0.263, 0.267), (4.0, 0.281, 0.282),
       (6.0, 0.299, 0.299), (10.0, 0.312, 0.312), (1e9, 1 / 3, 1 / 3)]
def _ba(r):
    """Saint-Venant rectangle factors beta (J = beta b t^3) and alpha (tau = T/(alpha b t^2)) for b/t = r"""
    r = max(r, 1.0)
    for (r0, b0, a0), (r1, b1, a1) in zip(_BT[:-1], _BT[1:]):
        if r <= r1:
            f = (r - r0) / (r1 - r0) if r1 < 1e8 else 1 - 10.0 / r
            return b0 + f * (b1 - b0), a0 + f * (a1 - a0)
    return 1 / 3, 1 / 3

def torsion_parts(kind):
    """open section as rectangles (b, t): bulb zone (pin leg + bulb), pin leg above the bulb, web, outer leg, lip"""
    D = DEPTH[kind]; W = WIDTH[kind]; tw = t_web(kind); tb = T_LEG + BULB[kind[0]]
    parts = [("bulb zone", H_BULB, tb), ("pin leg", max(0.0, D - tw - H_BULB), T_LEG), ("web", W, tw)]
    if kind[0] == "B": parts.append(("outer leg", D - tw - N_OUT_B, T_OUT))
    if kind[0] == "A": parts.append(("lip", LIP[1], LIP[0]))
    return [(n, max(b, t), min(b, t)) for n, b, t in parts if b > 0]

def torsion_J(kind):
    """St Venant J = sum beta b t^3 (rectangle factors) and the peak shear per unit torque (tau = T * k)"""
    parts = torsion_parts(kind); J = 0.0; rows = []
    for n, b, t in parts:
        be, al = _ba(b / t); Ji = be * b * t ** 3; J += Ji; rows.append((n, b, t, Ji, al))
    k = max(Ji / J / (al * b * t * t) for n, b, t, Ji, al in rows)     # tau_max per unit torque
    return J, k


# ------------------------------------------------------------------ pixel section tools
G = 0.25
class Sec:
    def __init__(self, rects):
        ys = [v for r in rects for v in (r[0], r[2])]; ns = [v for r in rects for v in (r[1], r[3])]
        self.y0, self.n0 = min(ys), min(ns)
        ny, nn = int(round((max(ys) - self.y0) / G)), int(round((max(ns) - self.n0) / G))
        self.Y = self.y0 + (np.arange(ny) + 0.5) * G; self.N = self.n0 + (np.arange(nn) + 0.5) * G
        self.el = np.full((ny, nn), "", dtype=object); self.rho = np.zeros((ny, nn))
        for y0, n0, y1, n1, name in rects:
            m = np.outer((self.Y > y0) & (self.Y < y1), (self.N > n0) & (self.N < n1)); self.el[m] = name; self.rho[m] = 1.0
    def copy(self):
        s = Sec.__new__(Sec); s.__dict__.update(self.__dict__); s.rho = self.rho.copy(); s.el = self.el.copy(); return s
    def cut(self, y0, n0, y1, n1):
        s = self.copy(); m = np.outer((s.Y > y0) & (s.Y < y1), (s.N > n0) & (s.N < n1)); s.rho[m] = 0.0; s.el[m] = ""; return s
    def props(self):
        dA = self.rho * G * G; A = dA.sum()
        Yg, Ng = np.meshgrid(self.Y, self.N, indexing="ij")
        yc, nc = (dA * Yg).sum() / A, (dA * Ng).sum() / A
        Iy = (dA * (Ng - nc) ** 2).sum(); In = (dA * (Yg - yc) ** 2).sum()
        occ = dA > 0
        nmin, nmax = Ng[occ].min() - G / 2, Ng[occ].max() + G / 2; ymin, ymax = Yg[occ].min() - G / 2, Yg[occ].max() + G / 2
        return dict(A=A, yc=yc, nc=nc, Iy=Iy, In=In, W_tip=Iy / (nc - nmin), W_far=Iy / (nmax - nc),
                    Wlat_in=In / (yc - ymin), Wlat_out=In / (ymax - yc), nmin=nmin, nmax=nmax, ymin=ymin, ymax=ymax)


def rho_c(beta, internal):
    C1, C2 = (32.0, 220.0) if internal else (10.0, 24.0)
    b3 = 22.0 if internal else 6.0
    return 1.0 if beta <= b3 else min(1.0, C1 / beta - C2 / beta ** 2)

def classify(kind):
    """EN 1999-1-1 6.1.4, eta = 1 (uniform compression, conservative). Pin leg: outstand from the web to the bulb (edge
    stiffener). Web: internal between pin leg and outer leg (B_lo) / lip (A); B_up web ends free: outstand."""
    D = DEPTH[kind]; W = WIDTH[kind]; tw = t_web(kind)
    rows = {"pin leg (web to bulb)": dict(b=max(0.0, D - tw - H_BULB), t=T_LEG, internal=False),
            "bulb": dict(b=H_BULB, t=T_LEG + BULB[kind[0]], internal=False)}
    rows["web"] = dict(b=W - T_LEG - (T_OUT if kind[0] == "B" else LIP[0]), t=tw, internal=True)
    if kind[0] == "B":
        rows["outer leg"] = dict(b=D - tw - N_OUT_B, t=T_OUT, internal=False)
    if kind[0] == "A":
        rows["lip"] = dict(b=LIP[1], t=LIP[0], internal=False)
    for r in rows.values():
        r["beta"] = r["b"] / r["t"]; r["rho"] = rho_c(r["beta"], r["internal"])
        lim = (11, 16, 22) if r["internal"] else (3, 4.5, 6)
        r["class"] = 1 if r["beta"] <= lim[0] else 2 if r["beta"] <= lim[1] else 3 if r["beta"] <= lim[2] else 4
    return rows


def sections(kind):
    g = Sec(profile(kind)); cl = classify(kind)
    for name, r in cl.items():                     # class-4 elements: effective thickness everywhere (conservative)
        if r["class"] == 4:
            g.rho[g.el == name.split(" (")[0]] *= r["rho"]
    D = DEPTH[kind]; W = WIDTH[kind]; tw = t_web(kind); bu = BULB[kind[0]]
    hole = g.cut(-1, C_PIN - HOLE_D / 2, T_LEG + bu + 0.01, C_PIN + HOLE_D / 2)
    notch = g.cut(-1, -1, T_LEG + bu + 0.01, NOTCH_DEPTH)
    sy = slot_y(kind)
    if kind.endswith("up"):
        slot = g.cut(sy[0], D - tw - 0.01, sy[1], D + 0.01)
    else:
        yc = 0.5 * (sy[0] + sy[1]); slot = g.cut(yc - (TONGUE_W + 1) / 2, D - tw - 0.01, yc + (TONGUE_W + 1) / 2, D + 0.01)
    return dict(gross=g, hole=hole, notch=notch, slot=slot, **{"notch+slot": slot.cut(-1, -1, T_LEG + bu + 0.01, NOTCH_DEPTH)})


# ------------------------------------------------------------------ fold kinematics
def frame_state(theta):
    th = math.radians(theta)
    return np.array([-math.cos(th), math.sin(th)]), np.array([math.sin(th), math.cos(th)])

def to_rail(p, theta, which):
    u, nu = frame_state(theta); p = np.asarray(p, float)
    if which == "lo":
        return float(p @ u), float(-(p @ nu)) + C_PIN
    q = p - np.array(LINK); return float(q @ u), float(q @ nu) + C_PIN

def from_rail(s, n_away, theta, which):
    u, nu = frame_state(theta)
    if which == "lo":
        return u * s - nu * (n_away - C_PIN)
    return np.array(LINK) + u * s + nu * (n_away - C_PIN)
