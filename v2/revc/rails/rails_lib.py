"""Rev C guide-rail design: shared parameters, section builder and fold kinematics (rail agent, 26 Sep 2026).
All four rails are channels OPENING TOWARD EACH OTHER: web at the far face, pin (inner) leg running to the touching
plane, where the pin legs carry interleaved tabs (see rail_design.md). Coordinates of a rail cross-section:
  y = across the stair, measured from the OUTER face of the pin leg (the face against the step end) into the rail;
  n = square to the rail in the side plane, measured from the touching plane (catwalk contact face), positive AWAY
      from the other rail (down for the lower rail, up for the upper rail). Pin line at n = C_PIN = 12.5.
Material EN AW-6082-T6 extrusion, EN 1999-1-1: f0 250 (t <= 5; 260 for 5 < t <= 15 - 250 used throughout), gM1 1.1,
gM2 = gMp 1.25. No welds anywhere, so no HAZ."""
import math, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.join(HERE, "..", "..", "final")
F0, GM1, GMP = 250.0, 1.1, 1.25
FD = F0 / GM1
E_AL = 70000.0

# ------------------------------------------------------------------ step pins (owner's L-step envelope, unchanged)
REAR, FRONT = (25.0, 12.5), (225.0, 37.5)          # step coords: x from the step back, z from the step underside
LINK = (FRONT[0] - REAR[0], FRONT[1] - REAR[1])      # (200, 25)
L_LINK = math.hypot(*LINK); PHI = math.degrees(math.atan2(LINK[1], LINK[0]))
PITCH = math.hypot(250.0, 175.0)                     # pin pitch along each rail, 305.16
STATES = {"catwalk": 0.0, "standard": 35.0, "steep": 49.4}
C_PIN = 12.5                                         # pin line to touching plane (both rails): 2 x 12.5 = 25 = catwalk pin-line gap

def sep(theta_deg):
    """perpendicular distance between the lower and upper pin lines"""
    return L_LINK * math.sin(math.radians(theta_deg + PHI))

# ------------------------------------------------------------------ pins, caps
PIN_D, HOLE_D = 16.0, 17.0          # 1.4462 duplex pin, h9; hole drilled + reamed 17.0 +0.1/0
CAP_OD = 28.0                       # locking cap (castle-type cap nut M16, AF 24 / 28 round), sits on a 2 mm washer on the bulb face
PAD = 1.0                           # PTFE-faced stainless thrust washer between step end block and rail pin leg

# ------------------------------------------------------------------ profile family (all mm)
T_LEG = 6.0         # pin (inner) leg
T_OUT = 5.0         # outer leg (lower rails only)
T_WEB = 6.0         # web (far face), all rails
H_BULB = 27.0       # bulb on the pin leg: n = 0 .. 27 (tip zone: pin bearing, pole bearing, tabs)
BULB_A, BULB_B = 13.5, 8.0          # bulb protrusion into the rail (left A / right B)
INT_B = 72.0                        # right rail inside width (pole 55 + 2 x 8.5)
CLR_NEST = 1.0                      # nesting clearance, each side / under the web
W_B = T_LEG + INT_B + T_OUT         # 83 right rail outside width
Y_B_IN_A = T_LEG + CLR_NEST         # B (nested) outer leg starts at y_A = 7
W_A_WEB_UP = T_LEG + CLR_NEST + W_B  # 90: upper-left web ends flush with the nested right rail's pin-leg face
W_A = W_A_WEB_UP + CLR_NEST + T_OUT  # 96: lower-left outside width (outer leg outboard of the nested rail + end-plate zone)
LIP_H = 18.0                        # upper rails: edge lip on the web's free edge, standing up beyond the far face
D_LO_A = 70.0                       # lower-left depth (touching plane to far face)
D_LO_B = D_LO_A - T_WEB - CLR_NEST  # 63: nested inside A with 1 mm under the web
N_OUT_LO_A = 42.0                   # lower-left outer leg starts at n = 42 (clears the neighbour's step end, see kinematics)
N_OUT_LO_B = 28.0                   # lower-right outer leg starts at n = 28 (clears the neighbour's caps, 12.5 + 14 + 1.5)
N_WEB_UP_B = C_PIN + CAP_OD / 2 + 1.5   # 28: upper-right web inner face just above the caps
D_UP_B = N_WEB_UP_B + T_WEB             # 34
D_UP_A = D_UP_B + CLR_NEST + T_WEB      # 41
SLOT_UP = (56.0, 36.0)      # upper-web pole slot: across x along (normal cut; 25/cos35 + t tan35 + 1)
SLOT_LO = (36.0, 36.0)      # lower-web tongue slot (tongue 35 across)
# pole y-position (from the pin-leg face): right rail: bulb face + 0.5; left rail: aligned with the nested right rail
POLE_W = 55.0
POLE_Y_B = (T_LEG + BULB_B + 0.5, T_LEG + BULB_B + 0.5 + POLE_W)            # 14.5 .. 69.5
POLE_Y_A = (W_A_WEB_UP - POLE_Y_B[1], W_A_WEB_UP - POLE_Y_B[0])            # 20.5 .. 75.5
SLOT_Y_B = (POLE_Y_B[0] - 0.5, POLE_Y_B[1] + 0.5)
SLOT_Y_A = (POLE_Y_A[0] - 0.5, POLE_Y_A[1] + 0.5)


def profile(kind):
    """list of (y0, n0, y1, n1, element) rectangles; element names used for classification"""
    if kind == "A_lo":
        D = D_LO_A
        return [(0, 0, T_LEG, D - T_WEB, "pin leg"), (T_LEG, 0, T_LEG + BULB_A, H_BULB, "bulb"),
                (0, D - T_WEB, W_A, D, "web"), (W_A - T_OUT, N_OUT_LO_A, W_A, D - T_WEB, "outer leg")]
    if kind == "B_lo":
        D = D_LO_B
        return [(0, 0, T_LEG, D - T_WEB, "pin leg"), (T_LEG, 0, T_LEG + BULB_B, H_BULB, "bulb"),
                (0, D - T_WEB, W_B, D, "web"), (W_B - T_OUT, N_OUT_LO_B, W_B, D - T_WEB, "outer leg")]
    if kind == "A_up":
        D = D_UP_A
        return [(0, 0, T_LEG, D - T_WEB, "pin leg"), (T_LEG, 0, T_LEG + BULB_A, H_BULB, "bulb"),
                (0, D - T_WEB, W_A_WEB_UP, D, "web"), (W_A_WEB_UP - T_WEB, D, W_A_WEB_UP, D + LIP_H, "lip")]
    if kind == "B_up":
        D = D_UP_B
        return [(0, 0, T_LEG, D - T_WEB, "pin leg"), (T_LEG, 0, T_LEG + BULB_B, H_BULB, "bulb"),
                (0, D - T_WEB, W_B, D, "web"), (W_B - T_WEB, D, W_B, D + LIP_H, "lip")]
    raise KeyError(kind)

DEPTH = {"A_lo": D_LO_A, "B_lo": D_LO_B, "A_up": D_UP_A, "B_up": D_UP_B}
RAIL_OF = {("L", "lo"): "A_lo", ("L", "up"): "A_up", ("R", "lo"): "B_lo", ("R", "up"): "B_up"}
SLOT_Y = {"A": SLOT_Y_A, "B": SLOT_Y_B}


# ------------------------------------------------------------------ pixel section tools (0.25 mm grid)
G = 0.25
class Sec:
    def __init__(self, rects):
        self.rects = rects
        ys = [v for r in rects for v in (r[0], r[2])]; ns = [v for r in rects for v in (r[1], r[3])]
        self.y0, self.n0 = min(ys), min(ns)
        ny, nn = int(round((max(ys) - self.y0) / G)), int(round((max(ns) - self.n0) / G))
        self.Y = self.y0 + (np.arange(ny) + 0.5) * G; self.N = self.n0 + (np.arange(nn) + 0.5) * G
        self.el = np.full((ny, nn), "", dtype=object); self.rho = np.zeros((ny, nn))
        for y0, n0, y1, n1, name in rects:
            m = np.outer((self.Y > y0) & (self.Y < y1), (self.N > n0) & (self.N < n1))
            self.el[m] = name; self.rho[m] = 1.0
    def copy(self):
        s = Sec.__new__(Sec); s.__dict__.update(self.__dict__); s.rho = self.rho.copy(); s.el = self.el.copy(); return s
    def cut(self, y0, n0, y1, n1):
        s = self.copy(); m = np.outer((s.Y > y0) & (s.Y < y1), (s.N > n0) & (s.N < n1)); s.rho[m] = 0.0; s.el[m] = ""; return s
    def props(self):
        dA = self.rho * G * G; A = dA.sum()
        Yg, Ng = np.meshgrid(self.Y, self.N, indexing="ij")
        yc, nc = (dA * Yg).sum() / A, (dA * Ng).sum() / A
        Iy = (dA * (Ng - nc) ** 2).sum()          # in-plane bending (about the across-stair axis)
        In = (dA * (Yg - yc) ** 2).sum()          # lateral bending (about the rail's depth axis)
        occ = dA > 0
        nmin, nmax = Ng[occ].min() - G / 2, Ng[occ].max() + G / 2; ymin, ymax = Yg[occ].min() - G / 2, Yg[occ].max() + G / 2
        return dict(A=A, yc=yc, nc=nc, Iy=Iy, In=In, W_tip=Iy / (nc - nmin), W_far=Iy / (nmax - nc),
                    Wlat_in=In / (yc - ymin), Wlat_out=In / (ymax - yc), nmin=nmin, nmax=nmax, ymin=ymin, ymax=ymax)
    def stress(self, N, My, Mn):
        """elastic stress at every cell: N/A + My*(n - nc)/Iy + Mn*(y - yc)/In (tension +).
        My > 0 puts the FAR face in tension; Mn > 0 puts the OUTER side (large y) in tension."""
        p = self.props(); Yg, Ng = np.meshgrid(self.Y, self.N, indexing="ij")
        return N / p["A"] + My * (Ng - p["nc"]) / p["Iy"] + Mn * (Yg - p["yc"]) / p["In"]


def rho_c(beta, internal):
    """EN 1999-1-1 6.1.5 (6.12), class A (6082-T6), unwelded: C1/C2 = 32/220 internal, 10/24 outstand; eps = 1"""
    C1, C2 = (32.0, 220.0) if internal else (10.0, 24.0)
    b3 = 22.0 if internal else 6.0
    return 1.0 if beta <= b3 else min(1.0, C1 / beta - C2 / beta ** 2)

def classify(kind):
    """element slenderness beta = b/t (eta = 1, uniform compression: conservative) and rho_c"""
    rows = {}
    D = DEPTH[kind]; a = kind[0] == "A"; up = kind.endswith("up")
    bulb = BULB_A if a else BULB_B
    width = (W_A_WEB_UP if up else W_A) if a else W_B
    # pin leg between the bulb (edge stiffener, 13.5/8 x 27 solid) and the web: internal element
    b = D - T_WEB - H_BULB; rows["pin leg"] = dict(b=b, t=T_LEG, internal=True)
    rows["bulb"] = dict(b=H_BULB, t=T_LEG + bulb, internal=False)
    # web: between pin leg and outer leg (lower) / pin leg and lip (upper): internal, clear width
    rows["web"] = dict(b=width - T_LEG - (T_OUT if not up else T_WEB), t=T_WEB, internal=True)
    if up: rows["lip"] = dict(b=LIP_H, t=T_WEB, internal=False)
    else: rows["outer leg"] = dict(b=D - T_WEB - (N_OUT_LO_A if a else N_OUT_LO_B), t=T_OUT, internal=False)
    for k, r in rows.items():
        r["beta"] = r["b"] / r["t"]; r["rho"] = rho_c(r["beta"], r["internal"])
        lim = (11, 16, 22) if r["internal"] else (3, 4.5, 6)
        r["class"] = 1 if r["beta"] <= lim[0] else 2 if r["beta"] <= lim[1] else 3 if r["beta"] <= lim[2] else 4
    return rows


def eff_section(sec, kind, N, My, Mn):
    """one-pass effective section: every class-4 element with any compressed cell gets t_eff = rho t"""
    s = sec.copy(); sig = sec.stress(N, My, Mn); cl = classify(kind)
    for name, r in cl.items():
        if r["class"] < 4: continue
        m = (s.el == name)
        if (sig[m] < 0).any(): s.rho[m] *= r["rho"]
    return s


def sections(kind):
    """gross, net at a pin hole, net at a catwalk notch, net at a pole slot (upper slot or tongue slot)"""
    g = Sec(profile(kind)); a = kind[0]
    D = DEPTH[kind]; bulb = BULB_A if a == "A" else BULB_B
    hole = g.cut(-1, C_PIN - HOLE_D / 2, T_LEG + bulb + 0.01, C_PIN + HOLE_D / 2)
    notch = g.cut(-1, -1, T_LEG + bulb + 0.01, NOTCH_DEPTH)
    sy = SLOT_Y[a]; sw = SLOT_UP[0] if kind.endswith("up") else SLOT_LO[0]
    yc = 0.5 * (sy[0] + sy[1]); slot = g.cut(yc - sw / 2, D - T_WEB - 0.01, yc + sw / 2, D + 0.01)
    return dict(gross=g, hole=hole, notch=notch, slot=slot)


# ------------------------------------------------------------------ tabs / notches (catwalk interleave)
def t88_a(F, t, d0):
    """EN 1999-1-1 Table 8.8 pin plate, given t: a >= F gMp/(2 t f0) + 2 d0/3 (hole edge to plate edge, in the force direction)"""
    return F * GMP / (2 * t * F0) + 2 * d0 / 3
def t88_c(F, t, d0):
    return F * GMP / (2 * t * F0) + d0 / 3
F_PIN_DESIGN = 11200.0                          # N, resultant pin force used for tab sizing (verified in run_rails.py)
TAB_R = HOLE_D / 2 + t88_a(F_PIN_DESIGN, T_LEG + BULB_B, HOLE_D) + 0.5   # metal round the hole, any direction (B leg 14 thick governs)
TAB_W = 2 * TAB_R                               # tab width along the rail
TAB_H = TAB_R - C_PIN                           # tab reach beyond the touching plane
NOTCH_DEPTH = TAB_H + 2.0
NOTCH_CLR = 4.0                                 # along the rail, each side of the tab (fold-out drift + tolerance)
NOTCH_W = TAB_W + 2 * NOTCH_CLR


# ------------------------------------------------------------------ fold kinematics
def frame_state(theta):
    """rail direction u (up the rail), upward normal nu, lower pin line through origin; upper pin line offset by LINK.
    Positions along a rail are s (from the tread-0 pin of that rail), normal offset from the lower pin line = n_up."""
    th = math.radians(theta)
    u = np.array([-math.cos(th), math.sin(th)]); nu = np.array([math.sin(th), math.cos(th)])
    return u, nu

def to_rail(p, theta, which):
    """global (x, z) relative to tread-0 rear pin -> (s, n_away) in the lower or upper rail's own frame"""
    u, nu = frame_state(theta); p = np.asarray(p, float)
    if which == "lo":
        return float(p @ u), float(-(p @ nu)) + C_PIN            # n_away from the touching plane (touching plane is C_PIN above the pin line)
    q = p - np.array(LINK)
    return float(q @ u), float(q @ nu) + C_PIN

def from_rail(s, n_away, theta, which):
    u, nu = frame_state(theta)
    if which == "lo":
        return u * s - nu * (n_away - C_PIN)
    return np.array(LINK) + u * s + nu * (n_away - C_PIN)
