"""ALTERNATIVE (rejected by owner 26 Sep: rails must be open, nesting channels). Rev C guide rails - H family (rail agent, 26 Sep 2026): "H" rails with the cross web ("mid flange") on the pin line.
One extrusion profile per depth; the left rails are the right rails turned over (mirror), so one die serves all four
(lower and upper differ only if the depths differ - here one die, one depth).
Cross-section coordinates:
  y = across the stair, from the OUTER face of the pin wall (the face against the step end) into the rail;
  n = square to the rail in the side plane, from the touching plane (catwalk contact face), positive AWAY from the
      other rail (down for the lower rail, up for the upper rail). Pin line at n = C_PIN = 12.5.
Why an H: the pole's barrier push must reach the pins at the pin line, or the open rail twists (see rail_design.md,
nested variant: 53-61 kN cap pull). The mid flange carries the pole push at n = N_MF (4 mm off the pin line) straight
into the pin wall. A mid flange across the rail makes nesting (one rail inside another) impossible - owner
constraint 3 is replaced by rail-to-rail side-by-side joining.
Material EN AW-6082-T6 extrusion, EN 1999-1-1: f0 250 (t <= 5; 260 for 5 < t <= 15 - 250 used), gM1 1.1, gM2 = gMp 1.25."""
import math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.join(HERE, "..", "..", "..", "final")
F0, GM1, GMP = 250.0, 1.1, 1.25
FD = F0 / GM1
E_AL = 70000.0

# ------------------------------------------------------------------ step pins (owner's L-step, pin positions unchanged)
REAR, FRONT = (25.0, 12.5), (225.0, 37.5)
LINK = (FRONT[0] - REAR[0], FRONT[1] - REAR[1])
L_LINK = math.hypot(*LINK); PHI = math.degrees(math.atan2(LINK[1], LINK[0]))
PITCH = math.hypot(250.0, 175.0)
STATES = {"catwalk": 0.0, "standard": 35.0, "steep": 49.4}
C_PIN = 12.5
def sep(theta_deg):
    return L_LINK * math.sin(math.radians(theta_deg + PHI))

# ------------------------------------------------------------------ pole variants (across x along)
POLES = {"box80": dict(W=80.0, along=25.0, A=2 * 80 * 2.5 + 2 * 20 * 5.5, I_inplane=2 * 80 * 2.5 * 11.25 ** 2 + 2 * 5.5 * 20 ** 3 / 12,
                       note="production: custom 6082-T6 box 25 along x 80 across, walls 5.5 (across faces) / 2.5"),
         "plate55": dict(W=55.0, along=25.0, A=55 * 25.0, I_inplane=55 * 25.0 ** 3 / 12, note="prototype: 25 mm plate, 55 across")}
POLE_KEY = os.environ.get("POLE", "box80")
POLE = POLES[POLE_KEY]
TONGUE_W = 35.0                     # pole tongue at the lower rail (both variants: end plug on the box pole)

# ------------------------------------------------------------------ pins and retention
PIN_D, HOLE_D = 16.0, 17.0          # 1.4462 duplex pin, h9; hole 17.0 +0.1/0 drilled + reamed through both walls on a jig
CAP_OD, CAP_LEN = 28.0, 24.0        # locking cap = castle cap nut M16 (28 round, 24 long incl. D30 x 3 washer)
PAD = 1.0                           # PTFE-faced stainless thrust washer, step end block to pin wall

# ------------------------------------------------------------------ profile (one die)
T_P = 6.0            # pin wall
T_O = 3.5            # outer wall
T_MF = 4.5           # mid flange (cross web)
LIG_IN = 8.0         # mid-flange ligament between the pin wall and the pole slot
LIG_OUT = 20.0       # ligament between the pole slot and the outer wall: the chord that takes the outward pole push
LIG = LIG_IN
W_INT = POLE["W"] + 1.0 + LIG_IN + LIG_OUT   # clear width between walls
W = T_P + W_INT + T_O                    # outside width
D = float(os.environ.get("RAIL_D", 45.0))   # touching plane to far edge (lower = upper, one die)
F_PIN_DESIGN = 9300.0                    # max pin resultant from the frame (run_rails.py verifies: 9.2 kN)

def t88_a(F, t, d0):
    return F * GMP / (2 * t * F0) + 2 * d0 / 3
def t88_c(F, t, d0):
    return F * GMP / (2 * t * F0) + d0 / 3
TAB_R = HOLE_D / 2 + t88_a(F_PIN_DESIGN, T_P, HOLE_D) + 0.5
TAB_W = 2 * TAB_R
TAB_H = TAB_R - C_PIN
NOTCH_DEPTH = TAB_H + 2.0
NOTCH_CLR = 4.0
NOTCH_W = TAB_W + 2 * NOTCH_CLR
N_MF0 = NOTCH_DEPTH + 0.5                # mid flange starts just beyond the notches, so notches never cut it
N_MF = N_MF0 + T_MF / 2                  # mid-flange mid-plane = pole bearing level
E_TORQUE = N_MF - C_PIN                  # lever of the pole push about the pin line
LIP = (5.0, 3.0)                         # small lips at the far edges of both walls (edge stiffeners), across x thick
SLOT_LEN = {"standard": 25.0 / math.cos(math.radians(35)) + T_MF * math.tan(math.radians(35)) + 1.0,
            "catwalk": 25.0 + 1.0,
            "steep": 25.0 / math.cos(math.radians(49.4)) + T_MF * math.tan(math.radians(49.4)) + 1.0}
SLOT_UP_W = POLE["W"] + 1.0
# slot sets: upper flange - one slot shared by standard + catwalk (standard length), one steep slot;
#            lower flange - one slot shared by standard + steep (steep length), one catwalk slot
UP_SLOTS = {"standard+catwalk": SLOT_LEN["standard"], "steep": SLOT_LEN["steep"]}
LO_SLOTS = {"standard+steep": SLOT_LEN["steep"], "catwalk": SLOT_LEN["catwalk"]}
SLOT_LO_W = TONGUE_W + 1.0
SLOT_Y0 = T_P + LIG_IN                   # slot starts 8 mm from the pin wall's inside face
CAP_CUT = (CAP_OD + 8.0, CAP_LEN + 4.0)  # cut-out in the mid flange at every pin: along x across (from the pin wall)


def profile():
    r = [(0, 0, T_P, D, "pin wall"), (W - T_O, 0, W, D, "outer wall"),
         (T_P, N_MF0, W - T_O, N_MF0 + T_MF, "mid flange")]
    if LIP[0] > 0:
        r += [(T_P, D - LIP[1], T_P + LIP[0], D, "lip"), (W - T_O - LIP[0], D - LIP[1], W - T_O, D, "lip")]
    return r


# ------------------------------------------------------------------ pixel section tools (0.25 mm grid)
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

def classify():
    """EN 1999-1-1 6.1.4: beta = b/t, eta = 1 (uniform compression, conservative). Walls: outstand from the mid flange
    to the far edge (lipped: internal-like, taken as outstand of the lip-to-flange length for safety) and to the tip."""
    rows = {"pin wall, far part": dict(b=D - (N_MF0 + T_MF), t=T_P, internal=False),
            "pin wall, tip part": dict(b=N_MF0, t=T_P, internal=False),
            "outer wall, far part": dict(b=D - (N_MF0 + T_MF), t=T_O, internal=False),
            "outer wall, tip part": dict(b=N_MF0, t=T_O, internal=False),
            "mid flange": dict(b=W_INT, t=T_MF, internal=True),
            "mid flange, outer ligament at slot": dict(b=LIG_OUT, t=T_MF, internal=False)}
    if LIP[0] > 0:
        for k in ("pin wall, far part", "outer wall, far part"):
            rows[k]["internal"] = True                       # lipped far edge: edge-stiffened (checked below as internal)
        rows["lip"] = dict(b=LIP[0], t=LIP[1], internal=False)
    for r in rows.values():
        r["beta"] = r["b"] / r["t"]; r["rho"] = rho_c(r["beta"], r["internal"])
        lim = (11, 16, 22) if r["internal"] else (3, 4.5, 6)
        r["class"] = 1 if r["beta"] <= lim[0] else 2 if r["beta"] <= lim[1] else 3 if r["beta"] <= lim[2] else 4
    return rows


def sections():
    """gross; net at a pin (hole in the pin wall + cap cut-out in the mid flange); net at a notch (pin wall cut to the
    notch depth); net at the upper pole slot; net at the lower tongue slot"""
    g = Sec(profile())
    rmf = classify()["mid flange"]["rho"]                     # class-4 mid flange: effective thickness everywhere (conservative)
    g.rho[g.el == "mid flange"] *= rmf
    pin = g.cut(-1, C_PIN - HOLE_D / 2, T_P + 0.01, C_PIN + HOLE_D / 2).cut(T_P - 0.01, N_MF0 - 0.01, T_P + CAP_CUT[1], N_MF0 + T_MF + 0.01)
    notch = g.cut(-1, -1, T_P + 0.01, NOTCH_DEPTH)
    slot_up = g.cut(SLOT_Y0, N_MF0 - 0.01, SLOT_Y0 + SLOT_UP_W, N_MF0 + T_MF + 0.01)
    yc = SLOT_Y0 + SLOT_UP_W / 2
    slot_lo = g.cut(yc - SLOT_LO_W / 2, N_MF0 - 0.01, yc + SLOT_LO_W / 2, N_MF0 + T_MF + 0.01)
    return dict(gross=g, hole=pin, notch=notch, slot_up=slot_up, slot_lo=slot_lo)


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
