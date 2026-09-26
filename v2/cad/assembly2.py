"""V2 PRECISION ASSEMBLY - compliance-locked folding access unit (stair/ladder/ramp/platform/bridge).
AUDITED DESIGN (32-finding compliance audit integrated):
 - UNDER-SLUNG parallelogram (ctl bar 90 below stringer) -> perfectly flush deck in flat modes.
 - Tread at every node (0..5): first rise ground->tread0 exactly 165 (G13 uniform).
 - LOCK: Ø16 follower pin in TWIN-CHEEK U-guide; radial J-branch slots at 0/4.76/20/29.98/65 deg
   (square shoulder, 2.5deg undercut, 10 mm vertical float on the base pivot seats the pin);
   SECONDARY independent Ø12 ball-lock pin; Ø12 plunger = indexing only; 3 mm cover strip (G96);
   welded end stop at 69 deg (NO 90-deg pocket).
 - Sections per audited sizing: stringer SHS60x5, post SHS50x5, ctl SHS40x4.
 - Added: mesh infill, end guard panels, self-closing gate, stabiliser, handhold extensions,
   sole boards, rubber pads, lifting lugs, ballast lugs, diagonal braces, ramp overlay thresholds,
   bridge bearing pads, rail returns, rating + pictogram plates, spigot couplers, modeled bolts.
Every part REGISTERED -> model + cutting list + per-part exports from one source of truth.
Run: uvx --python 3.13 --with "build123d==0.10.0" --with "cadquery-ocp==7.8.1.1.post1" python v2/cad/assembly2.py
"""
import sys, math, csv, pathlib
ROOT = pathlib.Path(r"C:/Users/USER/Desktop/Staircases/idea one")
sys.path.insert(0, str(ROOT / "v2" / "spec"))
import params as P
from build123d import *

OUT = ROOT / "v2" / "out"; (OUT / "parts").mkdir(parents=True, exist_ok=True); (OUT / "groups").mkdir(parents=True, exist_ok=True)

TH = P.STAIR_ANGLE
C, S = math.cos(math.radians(TH)), math.sin(math.radians(TH))
CELL = P.CELL
D = P.CTRL_OFFSET                       # -90 under-slung
PIVOT_H = P.PIVOT_H                     # 109.5
N_NODES = 6

SW = P.SEC_STRINGER[0]                  # 60
HALF_CLEAR = P.HALF_CLEAR
SEAM_GAP = 20.0
Y_A = [-SW / 2, HALF_CLEAR + SW / 2]
HALF_OUT = HALF_CLEAR + 2 * SW
Y_B = [y + HALF_OUT + SEAM_GAP for y in Y_A]
STRINGERS = [("A", 0, Y_A[0], True, -1), ("A", 1, Y_A[1], False, +1),
             ("B", 0, Y_B[0], False, -1), ("B", 1, Y_B[1], True, +1)]  # (half, idx, y, outer?, rail side sgn)
STRINGER_LEN = 5 * CELL + 260.0
CTRL_LEN = 5 * CELL + 120.0

REG = []
def reg(pid, name, qty, material, stock, L, W, T, ops, en, group, color, shape):
    if type(shape).__name__ == "ShapeList":
        shape = Part() + list(shape)
    shape.label = pid
    shape.color = Color(*color)
    REG.append(dict(pid=pid, name=name, qty=qty, material=material, stock=stock,
                    L=L, W=W, T=T, ops=ops, en=en, group=group, shape=shape))
    return shape

COL = dict(steel=(0.16, 0.17, 0.19), galv=(0.55, 0.57, 0.60), alu=(0.72, 0.74, 0.76),
           ss=(0.80, 0.82, 0.85), guide=(0.75, 0.35, 0.10), bush=(0.85, 0.75, 0.45),
           rail=(0.10, 0.10, 0.11), plate=(0.30, 0.32, 0.35), rubber=(0.06, 0.06, 0.06),
           mesh=(0.40, 0.42, 0.45), timber=(0.55, 0.42, 0.25), overlay=(0.60, 0.62, 0.64))


def shs(b, t, L):
    return extrude(Rectangle(b, b) - Rectangle(b - 2 * t, b - 2 * t), L)

def chs(d, t, L):
    return extrude(Circle(d / 2) - Circle(d / 2 - t), L)

def on_incline(y, s0):
    return Pos(0, y, PIVOT_H) * Rot(0, 90 - TH, 0) * Pos(0, 0, s0)

def P_M(i, y):  return (i * CELL * C, y, PIVOT_H + i * CELL * S)
def P_C(i, y):  return (i * CELL * C, y, PIVOT_H + i * CELL * S + D)
def ybore(r, ln=200): return Rot(-90, 0, 0) * Cylinder(r, ln)
def follower_pos(y):  return (P.GUIDE_R * C, y, PIVOT_H + P.GUIDE_R * S)


def hexbolt(dia, L, af, hh):
    """ISO 4014-style hex bolt, exact envelope (cosmetic thread; spec in ops)."""
    head = extrude(RegularPolygon(af / math.sqrt(3), 6), hh)
    return head + Pos(0, 0, -L) * Cylinder(dia / 2, L, align=(Align.CENTER, Align.CENTER, Align.MIN))

def hexnut(dia, af, h):
    return extrude(RegularPolygon(af / math.sqrt(3), 6) - Circle(dia / 2), h)


# ============================================================ PART BUILDERS
def stringer(y):
    b = on_incline(y, -130) * shs(*P.SEC_STRINGER, STRINGER_LEN)
    for i in range(0, N_NODES):
        b = b - Pos(*P_M(i, y)) * ybore(P.BUSH_OD / 2)
    for k in (0.5, 2.5, 4.5):                                               # Ø16.05 coupler-spigot bores (mid-cell)
        b = b - Pos(k * CELL * C, y, PIVOT_H + k * CELL * S - 40) * ybore(8.025)
    return b

def ctrlbar(y):
    b = Pos(0, 0, D) * (on_incline(y, -60) * shs(*P.SEC_CTRL, CTRL_LEN))
    for i in range(0, N_NODES):
        b = b - Pos(*P_C(i, y)) * ybore(P.BUSH_OD / 2)
    return b

def carrier(i, y, master, seam=0):
    """Under-slung carrier: twin 8 mm cheeks astride the stringer, seat on top, lower pivot at D.
    seam=+1/-1 clips the seam-side cheek (to +/-35) and seat (to 38) so the two halves clear."""
    if seam == 0:
        offs, inb = (-38.0, 38.0), (+1 if y < 400 else -1)                  # outer: A0 spans +y, B1 spans -y
    elif seam > 0:
        offs, inb = (-38.0, 35.0), -1                                       # A1: seam at +y, clear span at -y
    else:
        offs, inb = (-35.0, 38.0), +1                                       # B0: clear span at +y
    if i == 0:                                                              # node0 shares the bracket pin:
        offs = (-46.0, 46.0) if seam == 0 else (46.0 * (-1 if seam > 0 else 1),)   # cheeks OUTSIDE the ears
    c = None
    for sy in offs:
        ch = Pos(0, sy, -42.5) * Box(70, 8, 155)
        c = ch if c is None else c + ch
    # seat INBOARD of the stringer (treads span BETWEEN the webs, never over them)
    c = c + Pos(P.TREAD_DEPTH / 2 - 20, inb * 68.0, -1.5) * Box(P.TREAD_DEPTH - 30, 68, 4)
    c = c - ybore(P.BUSH_OD / 2)
    low = ybore(P.BUSH_OD / 2) if master else (Pos(0, 0, 0.8) * ybore(P.BUSH_OD / 2) + Pos(0, 0, -0.8) * ybore(P.BUSH_OD / 2))
    c = c - Pos(0, 0, D) * low
    for hx in (P.TREAD_DEPTH * 0.25, P.TREAD_DEPTH * 0.62):
        c = c - Pos(hx, inb * 68.0, -4) * Cylinder(4.5, 30)
    return Pos(*P_M(i, y)) * c

def tread(i, y_left_web):
    """Plank spans BETWEEN the stringer webs (never over them); tread 0 additionally clears the
    base-bracket ears (inset 16). Ø9 csk holes on the carrier-seat lines at web+38."""
    yin = 16.0 if i == 0 else 2.0
    Lp = HALF_CLEAR - 2 * yin
    x, z = i * CELL * C, PIVOT_H + i * CELL * S
    yc = y_left_web + HALF_CLEAR / 2
    xc = x + P.TREAD_DEPTH / 2 - 20 - P.NOSING_OVERLAP
    body = Pos(xc, yc, z + P.TREAD_THICK / 2 + 0.5) * Box(P.TREAD_DEPTH, Lp, P.TREAD_THICK)
    t = body - Pos(xc, yc, z + P.TREAD_THICK / 2 + 0.5) * Box(P.TREAD_DEPTH - 2 * P.TREAD_SKIN, Lp + 2, P.TREAD_THICK - 2 * P.TREAD_SKIN)
    for k in range(-3, 4):
        t = t - Pos(xc + k * 40, yc, z + P.TREAD_THICK + 0.5) * Box(6, Lp + 2, 3)
    for byy in (y_left_web + 38, y_left_web + HALF_CLEAR - 38):
        for hx in (P.TREAD_DEPTH * 0.25, P.TREAD_DEPTH * 0.62):
            t = t - Pos(x + hx, byy, z + P.TREAD_THICK / 2) * Cylinder(4.5, P.TREAD_THICK + 6)
            t = t - Pos(x + hx, byy, z + P.TREAD_THICK - 1.2) * Cone(9.2, 4.5, 9)
    return t

def nosing_strip(i, y_left_web):
    yin = 16.0 if i == 0 else 2.0
    x, z = i * CELL * C, PIVOT_H + i * CELL * S
    yc = y_left_web + HALF_CLEAR / 2
    return Pos(x - 20 - P.NOSING_OVERLAP + 12, yc, z + P.TREAD_THICK + 0.5) * Box(24, HALF_CLEAR - 2 * yin, 2)

def base_bracket(y):
    """Twin-ear base bracket: PLAIN reamed bores for both ground pivots (lock lives at the
    rear leg-top pivot, node 5 - user directive)."""
    ear_h = abs(D) + 220.0
    zc = PIVOT_H + D / 2
    b = Pos(0, y - 35, zc) * Box(130, 8, ear_h) + Pos(0, y + 35, zc) * Box(130, 8, ear_h)   # ears at 31..39
    b = b + Pos(0, y - 40, zc - ear_h / 2 + 6) * Box(180, 36, 12) \
        + Pos(0, y + 40, zc - ear_h / 2 + 6) * Box(180, 36, 12)             # twin pads (clear of ctl bar)
    b = b - Pos(0, y, PIVOT_H) * ybore(P.BUSH_OD / 2)
    b = b - Pos(0, y, PIVOT_H + D) * ybore(P.BUSH_OD / 2)
    return b

# ---- U-GUIDE AT THE REAR LEG-TOP PIVOT (node 5) - user directive ----------------------------
# The guide fan is WELDED TO THE STRINGER, centred on the node-5 pivot; the Ø16 follower pin is
# on the VERTICAL LEG at R180 below the pivot. In the build pose (theta=29.98) a detent theta_d
# sits at world angle A_d = 270 + (TH - theta_d) measured from node 5.
def det_world(a_d):  return 270.0 + (TH - a_d)

N5 = lambda y: P_M(5, y)

def _sector(a0, a1, ri, ro):
    """Annular sector between world angles a0..a1 (deg) as a 2D face (XZ plane wedge cut)."""
    ann = Circle(ro) - Circle(ri)
    n = 24
    pts = [(0.0, 0.0)] + [(1.3 * ro * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                           1.3 * ro * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    return ann & Polygon(*pts, align=None)

def guide_cheek(y, off, sgn):
    """One 8 mm cheek of the TWIN U-guide fan at node 5 (OUTBOARD side, sgn=+/-1): arc slot R180
    + J-branch dips (square shoulder, 30 radially OUTWARD, 2.5deg undercut) + Ø12.2 ball-lock holes."""
    RO, RI = 218.0, 148.0
    a_lo, a_hi = det_world(P.LADDER_ANGLE) - 8, det_world(0.0) + 8
    pl = extrude(Plane.XZ * _sector(a_lo, a_hi, RI, RO), 8)
    pl = pl - extrude(Plane.XZ * _sector(det_world(P.LADDER_ANGLE) - 2, det_world(0.0) + 2,
                                         P.GUIDE_R - P.GUIDE_SLOT_W / 2, P.GUIDE_R + P.GUIDE_SLOT_W / 2), 10)
    for a_d in P.DETENT_ANGLES:
        a = det_world(a_d); r = math.radians(a)
        cx, cz = P.GUIDE_R * math.cos(r), P.GUIDE_R * math.sin(r)
        br = Pos(cx, 4, cz) * Rot(0, -a, 0) * Pos(P.BRANCH_DEPTH / 2, 0, 0) * Box(P.BRANCH_DEPTH + P.GUIDE_SLOT_W / 2, 12, P.GUIDE_SLOT_W)
        pl = pl - br
        ir = RI + 17
        pl = pl - Pos(ir * math.cos(r), 4, ir * math.sin(r)) * ybore(6.1, 40)
    p5 = N5(y)
    return Pos(p5[0], y + sgn * off + (4 if sgn < 0 else 0) * 0 - (8 if sgn < 0 else 0) * 0, p5[2]) * (pl if sgn > 0 else mirror(pl, Plane.XZ.offset(0)))

def cover_strip(y, sgn):
    a_lo, a_hi = det_world(P.LADDER_ANGLE) - 4, det_world(0.0) + 4
    p5 = N5(y)
    st = extrude(Plane.XZ * _sector(a_lo, a_hi, 155.0, 212.0), 3)
    return Pos(p5[0], y + sgn * 96, p5[2]) * (st if sgn > 0 else mirror(st, Plane.XZ.offset(0)))

def follower_pin(y, sgn):
    p5 = N5(y)
    fw = (p5[0], y, p5[2] - P.GUIDE_R)
    rx = -90 * sgn
    return Pos(fw[0], y - sgn * 24, fw[2]) * (Rot(rx, 0, 0) * Cylinder(P.PIN_DIA / 2, 124)) \
        + Pos(fw[0], y + sgn * 106, fw[2]) * (Rot(rx, 0, 0) * Cylinder(12, 6))

def balllock_pin(y, a_d, sgn):
    a = det_world(a_d); r = math.radians(a); ir = 148.0 + 17
    p5 = N5(y)
    px, pz = p5[0] + ir * math.cos(r), p5[2] + ir * math.sin(r)
    rx = -90 * sgn
    body = Pos(px, y + sgn * 50, pz) * (Rot(rx, 0, 0) * Cylinder(P.BALLLOCK_DIA / 2, 60))
    ring = Pos(px, y + sgn * 114, pz) * (Rot(rx, 0, 0) * (Cylinder(14, 4) - Cylinder(9, 6)))
    return body + ring

def plunger(y, sgn):
    p5 = N5(y)
    fw = (p5[0] - 34, y, p5[2] - P.GUIDE_R + 10)
    rx = -90 * sgn
    return Pos(fw[0], y + sgn * 52, fw[2]) * (Rot(rx, 0, 0) * Cylinder(P.LOCK_PLUNGER_DIA / 2, 44)) \
        + Pos(fw[0], y + sgn * 100, fw[2]) * (Rot(rx, 0, 0) * Cylinder(11, 12))

def pin(pt, ln):
    return Pos(pt[0], pt[1] - ln / 2, pt[2]) * (Rot(-90, 0, 0) * Cylinder(P.PIN_DIA / 2, ln)) \
        + Pos(pt[0], pt[1] + ln / 2 + 3, pt[2]) * (Rot(-90, 0, 0) * Cylinder(12, 6))

def bush(pt):
    return Pos(pt[0], pt[1] - 12, pt[2]) * (Rot(-90, 0, 0) * (Cylinder(P.BUSH_OD / 2, 24) - Cylinder(P.BUSH_ID / 2, 26)))

def leg(y, seam=0):
    """PIVOTING rear leg (user directive): head plates at node 5 with Ø20 bore + VERTICAL FLOAT
    SLOT (+10, seats the follower into the J-dip), socket tube with Ø16.1 follower bore at R180,
    jack slider + footplate. Leg hangs gravity-vertical in every mode.
    seam=0: twin heads (outer stringers). seam=+/-1: SINGLE outboard head plate (inner stringers,
    the 20 mm seam cannot host twin plates); footplate offset 40 inboard so the halves clear."""
    p5 = P_M(5, y)
    XO = 55.0                                                               # leg column offset BEHIND the pivot
    slot = ybore(P.BUSH_OD / 2) + Pos(0, 0, 10) * ybore(P.BUSH_OD / 2) + Pos(0, 0, 5) * (Rot(-90, 0, 0) * extrude(Rectangle(P.BUSH_OD, 10), 200, both=True))
    hp = Pos(p5[0] + 30, 0, p5[2] - 75) * Box(120, 8, 270)                  # covers pivot + follower + tube weld
    if seam == 0:
        head = Pos(0, y - 52, 0) * hp + Pos(0, y + 52, 0) * hp
    else:
        head = Pos(0, y - seam * 52, 0) * hp                                # single plate, outboard of the half
    head = head - Pos(p5[0], y, p5[2]) * slot                               # float slot at the pivot
    head = head - Pos(p5[0], y, p5[2] - P.GUIDE_R) * ybore(P.PIN_DIA / 2 + 0.05)   # follower bore (in plates)
    sock = Pos(p5[0] + XO, y, p5[2] - 480) * shs(50, 4, 440)                # column clear of ctl-bar pivot zone
    for k in range(5):
        sock = sock - Pos(p5[0] + XO, y, p5[2] - 240 - k * 45) * ybore(6.5)
    fdy = -seam * 40.0
    slide = Pos(p5[0] + XO, y, 8) * shs(40, 4, P.JACK_TUBE_LEN)
    foot = Pos(p5[0] + XO, y + fdy, 4) * Box(P.FOOTPLATE, P.FOOTPLATE, 8)
    return head + sock, slide + foot, fdy

def rubber_pad(y, fdy=0.0):
    p5 = P_M(5, y)
    return Pos(p5[0] + 55, y + fdy, -5) * Box(P.FOOTPLATE, P.FOOTPLATE, 10)

def sole_board(y):
    p5 = P_M(5, y)
    return Pos(p5[0] + 55, y, -29) * Box(500, 225, 38)

def rail_post(st, y):
    b = (st * CELL * C, y, PIVOT_H + st * CELL * S)
    post = Pos(b[0], y, b[2] + 28) * shs(*P.SEC_POST, P.RAIL_HEIGHT - 28)
    # saddle = 2 side plates + bottom strap BELOW the inclined stringer sweep (dz = 60*tan30 = 35)
    saddle = Pos(b[0], y - 34.25, b[2] - 25) * Box(120, 8, 110) + Pos(b[0], y + 34.25, b[2] - 25) * Box(120, 8, 110)
    saddle = saddle + Pos(b[0], y, b[2] - 70) * Box(120, 76.5, 10)
    for bz in (-34, 34):
        saddle = saddle - Pos(b[0] + bz, y, b[2] - 55) * ybore(6.5, 120)    # Ø13 M12 pairs under the sweep
    return post + saddle

def rails(y):
    s0 = 0.5 * CELL - 120
    ln = 4.0 * CELL + 360
    parts = []
    for h, dia, t in ((P.RAIL_HEIGHT, *P.SEC_RAIL_CHS), (950.0, 26.9, 2.6),
                      (P.MID_RAIL_2, 26.9, 2.6), (P.MID_RAIL_1, 26.9, 2.6)):
        parts.append(Pos(0, 0, h) * (on_incline(y, s0) * chs(dia, t, ln)))
    toe = on_incline(y, s0) * extrude(Plane.XY * Rectangle(P.TOE_BOARD, 3, align=(Align.MAX, Align.CENTER)), ln)
    parts.append(toe)
    return parts, ln

def rail_return(y, end_s, h):
    pt = (end_s * C, y, PIVOT_H + end_s * S + h)
    return Pos(pt[0], y, pt[2] - 60) * Cylinder(20, 120) + Pos(pt[0], y, pt[2] - 122) * Cylinder(22, 6)

def mesh_panel(y, sgn):
    """VERTICAL parallelogram infill panel in the rail plane (follows the pitch line)."""
    s0, s1 = 0.75 * CELL, 4.25 * CELL
    x0, z0 = s0 * C, PIVOT_H + s0 * S + 180
    x1, z1 = s1 * C, PIVOT_H + s1 * S + 180
    prof = Polygon((x0, z0), (x1, z1), (x1, z1 + 640), (x0, z0 + 640), align=None)
    return Pos(0, y + sgn * 1.5, 0) * extrude(Plane.XZ * prof, 3)

def end_guard(x, y0, y1, z):
    w = (y1 - y0)
    f = Pos(x, (y0 + y1) / 2, z + 550) * (Box(46, w, 1100) - Box(50, w - 92, 1008))
    f = f + Pos(x, (y0 + y1) / 2, z + P.MID_RAIL_1) * Box(40, w - 80, 26)
    f = f + Pos(x, (y0 + y1) / 2, z + P.MID_RAIL_2) * Box(40, w - 80, 26)
    return f

def gate(y0):
    w = 700.0
    f = Pos(-150, y0 + w / 2, PIVOT_H + 620) * (Box(42, w, 980) - Box(46, w - 84, 896))
    f = f + Pos(-150, y0 + w / 2, PIVOT_H + 620) * Box(36, w - 80, 24)
    return f

def stabiliser():
    yc = (Y_A[0] + Y_B[1]) / 2
    bar = Pos(-240, yc - P.STABILISER_W / 2, 40) * (Rot(-90, 0, 0) * shs(40, 4, P.STABILISER_W))
    feet = Pos(-240, yc - P.STABILISER_W / 2 + 20, 18) * Box(80, 40, 36) + Pos(-240, yc + P.STABILISER_W / 2 - 20, 18) * Box(80, 40, 36)
    return bar + feet

def handhold_ext(y):
    """Clip-mounts on the TOP END GUARD panel posts (deployed in ladder mode)."""
    p5 = P_M(5, y)
    return Pos(1820, y, p5[2] + 780) * (Cylinder(20, P.HANDHOLD_EXT) - Cylinder(17, P.HANDHOLD_EXT + 2))

def lifting_lug(sx, y):
    pt = (sx * CELL * C, y, PIVOT_H + sx * CELL * S)
    return Pos(pt[0], y, pt[2] - 14) * (Box(80, 8, 70) - Pos(0, 0, 15) * ybore(9.05, 20))   # below deck line

def ballast_lug(y):
    return Pos(-60, y, 26) * (Box(8, 90, 52) - Pos(0, 0, 6) * Rot(0, 90, 0) * Cylinder(9.05, 20))

def brace(y_from, y_to):
    p0 = (5 * CELL * C - 60, y_from, 60.0)
    p1 = (2.5 * CELL * C, y_to, PIVOT_H + 2.5 * CELL * S - 60)
    v = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    Lb = math.sqrt(sum(c * c for c in v))
    zr = math.degrees(math.atan2(v[1], v[0]))
    yr = math.degrees(math.acos(v[2] / Lb))
    return Pos(*p0) * Rot(0, 0, zr) * Rot(0, yr, 0) * chs(*P.BRACE_CHS, Lb)

def ramp_threshold(y0, y1, at_top):
    x = 1660.0 if at_top else (-560.0)                                      # stored clear of feet/brackets
    return Pos(x, (y0 + y1) / 2, 18) * Box(220, (y1 - y0), 36) - Pos(x + (120 if at_top else -120), (y0 + y1) / 2, 40) * Rot(0, 15, 0) * Box(300, (y1 - y0) + 4, 60)

def bearing_pad(y, at_top):
    x = 1940.0 if at_top else (-480.0)                                      # stored on ground, clear of frame
    return Pos(x, y, 10) * Box(200, 150, 20)

def coupler(k):
    """Seam coupler at MID-CELL k (clear of carriers/legs): 19 mm filler block in the 20 mm seam
    + Ø15.96 spigot pin h9 through the Ø16.05 stringer bores (both inner webs). Lip <=1 by fit."""
    x, z = k * CELL * C, PIVOT_H + k * CELL * S - 40
    ymid = Y_A[1] + SW / 2 + SEAM_GAP / 2
    blk = Pos(x, ymid, z) * (Box(60, 19.0, 44) - ybore(8.05, 60))
    spig = Pos(x, ymid - 65, z) * (Rot(-90, 0, 0) * Cylinder(7.98, 130)) \
        + Pos(x, ymid - 71, z) * (Rot(-90, 0, 0) * Cylinder(12, 6))
    return blk + spig

def marking_plate(y):
    p1 = P_M(1, y)
    return Pos(p1[0] - 140, y + 32, p1[2] + 30) * Box(100, 1.5, 75)

def picto_plate(y):
    return Pos(-90, y + 32, PIVOT_H + 130) * Box(60, 1.5, 60)


# ============================================================ BUILD
def build():
    shapes = []
    add = shapes.append
    AF = dict(M8=(13.0, 5.3), M12=(18.0, 7.5), M6=(10.0, 4.0))

    for half, idx, y, outer, sgn in STRINGERS:
        tag = f"{half}{idx}"
        add(reg(f"PRT-01-{tag}", "Stringer", 1, P.MAT_STRUCT, "SHS 60x60x5", STRINGER_LEN, 60, 60,
                f"6x Ø{P.BUSH_OD:.0f} H7 line-reamed; 1x Ø16.1; ends mitre {TH:.1f}deg; EXC2", "EN 12811-1/1993 L26", f"str_{tag}", COL['steel'], stringer(y)))
        add(reg(f"PRT-02-{tag}", "Control bar", 1, P.MAT_STRUCT, "SHS 40x40x4", CTRL_LEN, 40, 40,
                f"6x Ø{P.BUSH_OD:.0f} H7 line-reamed", "EN 12811-1 [12]", f"ctl_{tag}", COL['steel'], ctrlbar(y)))
        seam = 0 if outer else (+1 if half == "A" else -1)                   # inner stringers face the seam
        add(reg(f"PRT-05-{tag}", "Base pivot bracket", 1, P.MAT_STRUCT, "PL 8 + PL 12", 330, 130, 8,
                "2x Ø20 H7 reamed ground pivots; ears astride SHS60; EXC2", "EN 12811-1/1090-2", f"base_{tag}", COL['plate'], base_bracket(y)))
        if outer:                                                           # U-guide fan on OUTER stringers only
            add(reg(f"PRT-06-{tag}-i", "U-guide cheek (inner)", 1, P.MAT_STRUCT, "PL 8 laser", 460, 300, 8,
                    f"REAR LEG-TOP fan @node5; arc slot R{P.GUIDE_R:.0f}x{P.GUIDE_SLOT_W:.1f}; 5x J-dip {P.GUIDE_SLOT_W:.1f}w x {P.BRANCH_DEPTH:.0f} SQUARE +2.5deg undercut; end stops; 5x Ø12.2; welds to stringer", "G105/G96 [1][2]", f"str_{tag}", COL['guide'], guide_cheek(y, 62, sgn)))
            add(reg(f"PRT-06-{tag}-o", "U-guide cheek (outer)", 1, P.MAT_STRUCT, "PL 8 laser", 460, 300, 8,
                    "identical to inner cheek; spacer bosses 18", "G105/G96", f"str_{tag}", COL['guide'], guide_cheek(y, 88, sgn)))
            add(reg(f"PRT-08-{tag}", "Guide cover strip", 1, P.MAT_STRUCT, "PL 3 laser", 420, 60, 3,
                    "M6x12 @100 crs into outer cheek (finger-guard, G96)", "G96 [9]", f"str_{tag}", COL['plate'], cover_strip(y, sgn)))
            add(reg(f"PIN-16F-{tag}", "Follower pin Ø16", 1, P.MAT_PIN, "Ø16 h9 bar", 124, 16, 16,
                    "through LEG socket + both cheeks; circlips + R-clip; DOUBLE SHEAR primary lock", "L61 [1]", f"leg_{tag}", COL['ss'], follower_pin(y, sgn)))
            add(reg(f"BLP-12-{tag}", "Ball-lock pin Ø12 (secondary)", 1, P.MAT_PIN, "Ø12 A4-80 QR pin", 60, 12, 12,
                    "through both cheeks + leg boss at detent; SS lanyard; independent lock", "G105 [3]", f"str_{tag}", COL['ss'], balllock_pin(y, TH, sgn)))
            add(reg(f"PLG-12-{tag}", "Index plunger Ø12", 1, P.MAT_PIN, "GN 617 type", 44, 12, 12,
                    "INDEXING ONLY (not load path); lanyard tab", "G105", f"leg_{tag}", COL['ss'], plunger(y, sgn)))
        for i in range(0, N_NODES):
            add(reg(f"PRT-03-{tag}-{i}", "Carrier (twin cheek)" if seam == 0 else "Carrier (seam-clipped)", 1, P.MAT_STRUCT, "PL 8 x2 + PL 4",
                    155, 70, 8, "2x Ø20 H7 (lower slotted ±0.8 exc. node-3 master); 2x Ø9 csk; cheeks astride stringer" + ("" if seam == 0 else "; seam side clipped to 35/38"), "EN 12811-1", f"car_{tag}_{i}", COL['galv'], carrier(i, y, master=(i == 3), seam=seam)))
            pts = [(P_M(i, y), 100), (P_C(i, y), 100)] if i > 0 else []
            for pt, ln in pts:
                zkey = round(pt[2])
                add(reg(f"PIN-16-{tag}-{i}-{zkey}", "Pivot pin Ø16", 1, P.MAT_PIN, "Ø16 h9 bar", ln, 16, 16,
                        "circlip grooves DIN 471 + R-clip retainer", "L61", f"str_{tag}" if pt[2] > P_C(i, y)[2] else f"ctl_{tag}", COL['ss'], pin(pt, ln)))
                add(reg(f"BSH-{tag}-{i}-{zkey}", "DU bush 20/16.1x20", 1, P.MAT_BUSH, "Ø20 DU bush", 20, 20, 20,
                        "press in welded boss; isolating washers", "L61 [11]", f"car_{tag}_{i}", COL['bush'], bush(pt)))
        add(reg(f"PIN-16-{tag}-b0", "Pivot pin Ø16 (base main)", 1, P.MAT_PIN, "Ø16 h9 bar", 100, 16, 16, "in vertical float slot; circlips+R-clip", "L61", f"base_{tag}", COL['ss'], pin((0, y, PIVOT_H), 100)))
        add(reg(f"PIN-16-{tag}-b1", "Pivot pin Ø16 (base ctl)", 1, P.MAT_PIN, "Ø16 h9 bar", 100, 16, 16, "circlips+R-clip", "L61", f"base_{tag}", COL['ss'], pin((0, y, PIVOT_H + D), 100)))
        sock, slider, fdy = leg(y, seam)
        add(reg(f"PRT-10-{tag}", "Leg upper (twin head)" if seam == 0 else "Leg upper (single head)", 1, P.MAT_STRUCT, "SHS 50x50x4 + PL8 head", 440, 90, 50,
                "PIVOTS at node5: Ø20 bore + VERTICAL FLOAT SLOT +10 (J-lock seat); Ø16.1 follower bore @R180; 5x Ø13 @45" + ("" if seam == 0 else "; single outboard head"), "G75 [1]", f"leg_{tag}", COL['steel'], sock))
        add(reg(f"PRT-11-{tag}", "Leg slider + footplate", 1, P.MAT_STRUCT, "SHS 40x40x4 + PL8", P.JACK_TUBE_LEN, 150, 150,
                "engagement >=300 at full ext; datum groove for 165 bottom-rise gauge [18]" + ("" if seam == 0 else "; foot offset 40 inboard"), "G74/75", f"leg_{tag}", COL['galv'], slider))
        add(reg(f"PAD-{tag}", "Rubber foot pad", 1, "NBR 70ShA", "PL 10 rubber", 150, 150, 10, "bonded + 4x M5 csk retained", "G34/L14 [23]", f"leg_{tag}", COL['rubber'], rubber_pad(y, fdy)))
        if outer:
            add(reg(f"SOL-{tag}", "Sole board", 1, "C24 timber", "500x225x38", 500, 225, 38, "locating studs for footplate", "G77 [24]", f"leg_{tag}", COL['timber'], sole_board(y)))
            for st in P.POST_STATIONS:
                add(reg(f"PRT-12-{tag}-{st}", "Guardrail post + saddle", 1, P.MAT_STRUCT, "SHS 50x50x5 + PL6 saddle", P.RAIL_HEIGHT - 28, 50, 50,
                        "wrap saddle both webs; 2x M12 8.8 pairs lever>=100 [14]", "L33/34", f"hr_{tag}", COL['rail'], rail_post(st, y)))
                for bz in (-34, 34):
                    add(reg(f"BLT-M12-{tag}-{st}-{bz}", "Bolt M12x110 8.8 HDG + nut", 1, "8.8 HDG", "ISO 4014/4032", 110, 18, 12,
                            "saddle through-pair", "L33 [14]", f"hr_{tag}", COL['ss'],
                            Pos(st * CELL * C + bz, y - 44, PIVOT_H + st * CELL * S - 55) * Rot(-90, 0, 0) * hexbolt(12, 110, 18, 7.5)))
            rl, rln = rails(y)
            for rp, nm, stock in zip(rl, ("Top grip rail CHS40x3", "Ramp rail 950 CHS26.9 (clip-on)", "Mid rail 2 CHS26.9", "Mid rail 1 CHS26.9", "Toe board FB150x3"),
                                     ("CHS 40x3", "CHS 26.9x2.6", "CHS 26.9x2.6", "CHS 26.9x2.6", "FB 150x3 alu")):
                add(reg(f"PRT-13-{tag}-{nm.split()[0]}{nm.split()[1]}", nm, 1, P.MAT_STRUCT if 'CHS' in stock else P.MAT_TREAD, stock,
                        round(rln), 40, 3, "returned ends [26]; ext>=300 (G20); 950 rail = ramp config", "G64-69/G47", f"hr_{tag}", COL['rail'], rp))
            for es, nm in ((0.5 * CELL - 120, "bottom"), (4.5 * CELL + 240, "top")):
                add(reg(f"RET-{tag}-{nm}", "Rail return + end cap", 1, P.MAT_STRUCT, "CHS 40x3 bend", 120, 40, 3,
                        "90deg return into post + domed cap, no snag (G72)", "G72 [26]", f"hr_{tag}", COL['rail'], rail_return(y, es, P.RAIL_HEIGHT)))
            add(reg(f"MSH-{tag}", "Mesh infill panel", 1, P.MAT_STRUCT, "welded mesh 3mm/90ap + PL3 frame", round(3 * CELL), 700, 3,
                    "clip-in; aperture <=100 (public/event)", "G8/59/71 [6]", f"hr_{tag}", COL['mesh'], mesh_panel(y, sgn)))
            add(reg(f"HND-{tag}", "Handhold extension (ladder)", 1, P.MAT_STRUCT, "CHS 40x3", P.HANDHOLD_EXT, 40, 3,
                    "clip sockets on top post; >=1000 above step-off", "G30 [19]", f"str_{tag}", COL['rail'], handhold_ext(y)))
            for sx in (1.0, 4.0):
                add(reg(f"LUG-{tag}-{sx}", "Lifting lug", 1, P.MAT_STRUCT, "PL 8", 80, 70, 8,
                        "Ø18 shackle hole; below deck line; rated w/ dyn factor", "L62 [25]", f"str_{tag}", COL['plate'], lifting_lug(sx + 0.5, y)))
        add(reg(f"BAL-{tag}", "Ballast/anchor lug", 1, P.MAT_STRUCT, "PL 8", 90, 52, 8,
                f"Ø18 slot; kentledge {P.BALLAST_REQ_KG:.0f} kg OR ground anchors", "L40 [0]", f"base_{tag}", COL['plate'], ballast_lug(y)))
        add(reg(f"PRT-17-{tag}", "Rating plate", 1, "SS 1.4301", "PL 1.5 etched", 100, 75, 1.5,
                "class 6 / 7.5 kN/m2 / modes+detents / ballast rule / EN refs / ID / date; 4x Ø3.2 rivets", "G94", f"str_{tag}", COL['ss'], marking_plate(y)))

    for half, y0w in (("A", Y_A[0] + SW / 2), ("B", Y_B[0] + SW / 2)):
        t0 = f"{half}0"
        for i in range(0, N_NODES):
            add(reg(f"PRT-04-{half}-{i}", "Tread plank", 1, P.MAT_TREAD, f"plank {P.TREAD_DEPTH:.0f}x{P.TREAD_THICK:.0f}x{P.TREAD_SKIN:.0f} (web pitch 45)",
                    HALF_CLEAR + 110, P.TREAD_DEPTH, P.TREAD_THICK, "4x Ø9 csk; serrated (R11); web pitch<=50 [13]", "G4-7/L26", f"car_{t0}_{i}", COL['alu'], tread(i, y0w)))
            add(reg(f"NOS-{half}-{i}", "Contrast nosing strip", 1, "PA/alu hi-vis", "snap strip 24x2", HALF_CLEAR + 110, 24, 2,
                    "snap-in front edge, rounded", "G18 [30]", f"car_{t0}_{i}", COL['guide'], nosing_strip(i, y0w)))
            for byy in (y0w - 30, y0w + HALF_CLEAR + 30):
                for bx in (0.25, 0.62):
                    add(reg(f"BLT-M8-{half}-{i}-{round(byy)}-{bx}", "Bolt M8x25 csk A4", 1, "A4-80", "ISO 10642", 25, 13, 8,
                            "tread to carrier seat (through Ø9 csk)", "L5", f"car_{t0}_{i}", COL['ss'],
                            Pos(i * CELL * C + P.TREAD_DEPTH * bx, byy, PIVOT_H + i * CELL * S + P.TREAD_THICK + 0.5) * hexbolt(8, 25, 13, 5.3)))
    for k in (0.5, 2.5, 4.5):
        add(reg(f"PRT-16-{k}", "Module coupler (spigot+cam)", 1, P.MAT_STRUCT, "machined + Ø16 spigot h9", 60, 19, 44,
                "MID-CELL seam filler + Ø15.96 spigot through Ø16.05 web bores; lip<=1 by fit; over-centre cam; 15deg nosing chamfers (G96)", "G104/106 [15]", "couplers", COL['guide'], coupler(k)))
    add(reg("STB-1", "Stabiliser crossbar", 1, P.MAT_STRUCT, "SHS 40x40x4", P.STABILISER_W, 40, 40,
            "pins to base brackets Ø16; rubber swivel feet; REQUIRED ladder mode >=3m", "G27 [22]", "base_A0", COL['steel'], stabiliser()))
    add(reg("GTE-1", "Self-closing gate", 1, P.MAT_STRUCT, "SHS 40x4 frame", 980, 700, 40,
            "double torsion-spring hinges; inward opening; hooks std posts", "G21 [8]", "hr_A0", COL['rail'], gate(Y_A[0] + 40)))
    for x, z, nm in ((1820.0, PIVOT_H + 5 * CELL * S, "top"), (-360.0, PIVOT_H, "bottom")):
        add(reg(f"EGP-{nm}", "End guardrail panel", 1, P.MAT_STRUCT, "SHS 40x4 + CHS26.9", 1100, round(Y_B[1] - Y_A[0]), 40,
                "demountable drop-in; rails at 467/783/1100 + toe; sockets on stringer ends", "G56/70 [7]", "couplers", COL['rail'], end_guard(x, Y_A[0], Y_B[1], z)))
    for at_top in (False, True):
        add(reg(f"RTH-{'t' if at_top else 'b'}", "Ramp overlay threshold", 1, P.MAT_TREAD, "PL 6 folded chamfer", 220, round(Y_B[1] - Y_A[0]), 36,
                "hooks tread nosing; <=15mm chamfered lip (G84); REQUIRED for ramp detents", "G38/84 [10]", "couplers", COL['overlay'], ramp_threshold(Y_A[0], Y_B[1], at_top)))
        for y in (Y_A[0], Y_B[1]):
            add(reg(f"BRG-{'t' if at_top else 'b'}-{round(y)}", "Bridge bearing pad", 1, "EPDM 60ShA", "200x150x20", 200, 150, 20,
                    "slotted (sliding) fixing one end = thermal joint", "G87 [29]", "couplers", COL['rubber'], bearing_pad(y, at_top)))
    add(reg("BRC-A", "Diagonal brace CHS33.7", 1, P.MAT_STRUCT, "CHS 33.7x2.6", 1450, 34, 2.6,
            "flattened ends Ø16 pin holes + bushes; per bay free-standing", "G78 [0]", "str_A0", COL['steel'], brace(Y_A[0], Y_A[1])))
    add(reg("BRC-B", "Diagonal brace CHS33.7", 1, P.MAT_STRUCT, "CHS 33.7x2.6", 1450, 34, 2.6,
            "flattened ends Ø16 pin holes + bushes", "G78 [0]", "str_B1", COL['steel'], brace(Y_B[1], Y_B[0])))
    add(reg("PIC-1", "EN 131-3 pictogram plate", 1, "alu 1.5 printed", "60x60", 60, 60, 1.5,
            "ladder-mode base end", "G98 [27]", "base_A0", COL['ss'], picto_plate(Y_A[0])))
    return shapes


def export_all(shapes):
    comp = Compound(children=[s for s in shapes])
    bb = comp.bounding_box()
    print("PARTS", len(shapes), " BBOX", [round(v, 1) for v in (bb.size.X, bb.size.Y, bb.size.Z)],
          " VALID", all(s.is_valid for s in shapes))
    export_step(comp, str(OUT / "full_v2.step"))
    export_gltf(comp, str(OUT / "full_v2.glb"), binary=True)
    from collections import defaultdict
    gd = defaultdict(list)
    for r in REG:
        gd[r["group"]].append(r["shape"])
    for g in (OUT / "groups").glob("*.glb"):
        g.unlink()
    for g, shp in gd.items():
        export_gltf(Compound(children=shp), str(OUT / "groups" / f"{g}.glb"), binary=True)
    seen = set()
    grid = []
    gx = gy = 0
    for r in REG:
        if r["name"] in seen: continue
        seen.add(r["name"])
        export_step(r["shape"], str(OUT / "parts" / (r["name"].replace(' ', '_').replace('/', '-') + ".step")))
        bb2 = r["shape"].bounding_box()
        gsh = Pos(gx * 2300 - bb2.min.X, gy * 1100 - bb2.min.Y, -bb2.min.Z) * r["shape"]
        gsh.label = r["name"]; gsh.color = r["shape"].color
        grid.append(gsh)
        gx += 1
        if gx >= 7: gx = 0; gy += 1
    export_gltf(Compound(children=grid), str(OUT / "parts_grid.glb"), binary=True)
    agg = {}
    for r in REG:
        key = (r["name"], r["material"], r["stock"], round(r["L"], 1), r["W"], r["T"], r["ops"], r["en"])
        agg[key] = agg.get(key, 0) + r["qty"]
    with open(OUT / "cutlist.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Item", "Qty", "Material", "Stock / section", "Cut length (mm)", "Width (mm)", "Thk (mm)", "Machining / ops", "EN ref / audit"])
        for (nm, mat, stock, L, W, T, ops, en), q in sorted(agg.items()):
            w.writerow([nm, q, mat, stock, L, W, T, ops, en])
    print("cutlist rows:", len(agg), " groups:", len(gd), " unique STEPs:", len(seen))


if __name__ == "__main__":
    export_all(build())
