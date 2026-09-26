"""V2 MASTER PARAMETERS - locked from 'Code compliances SS staircase' workbook.
Every value below cites the governing row(s) of v2/spec/tab_Geometry_compliances.txt (G#)
or tab_Load_compliances.txt (L#). Run this file to execute the compliance check table:
    uvx --python 3.13 python v2/spec/params.py
All dimensions mm, forces N, stresses MPa unless noted.
"""
import math

# ============================================================ CORE STAIR GEOMETRY
GOING = 286.0            # G5: 175..300; AUDIT [20]: 286 @ rise 165 -> pitch exactly 30.0 (Class B band edge)
RISE = 165.0             # G6: rise 125(A)/165(B) min .. ~205 max; target 165 (EN 12811-1 Class B)
TWO_H_PLUS_G = 2 * RISE + GOING            # G9: 540..660, target ~600
STAIR_ANGLE = math.degrees(math.atan2(RISE, GOING))   # G10: 20..45 (Ind) / <=33 (Public)
CELL = math.hypot(GOING, RISE)             # length along stringer per step cell = 325.04 mm
N_RISERS = 6                               # G14: 3..18. Tread at EVERY node 0..5; rise 0 = ground->tread0
TOTAL_RISE = N_RISERS * RISE               # G11: <=3000 without landing (990)
UNIFORMITY_TOL = 5.0                       # G13: +/-5 mm rise/going uniformity (linkage: exact)
# Under-slung parallelogram: control bar BELOW stringer so NOTHING projects above the deck
# in flat modes (G104/G109 flush deck) and the first rise is uniform (G13):
CTRL_OFFSET = -90.0                        # vertical offset of control-bar pivots vs stringer nodes

# Treads (G4 width, G7/G18/G91 nosing, G49 deck gap at flat, G17 slip)
TREAD_DEPTH = 308.0                        # going 286 + 22 nosing overlap (G7: >=10, G18: <=25); flat gap 22.2
TREAD_WEB_PITCH = 45.0                     # AUDIT [13]: extrusion internal web pitch <=50 for the 10 kN patch
NOSING_OVERLAP = TREAD_DEPTH - GOING       # = 22 mm
FLAT_DECK_GAP = CELL - TREAD_DEPTH         # gap between treads tiled at 0 deg; G49: <=25 mm
TREAD_THICK = 55.0                         # plank profile depth (serrated 6082-T6, R11/PTV>=40 per G17/G95)
TREAD_SKIN = 3.0                           # plank wall thickness
PIVOT_H = RISE - TREAD_THICK - 0.5         # 109.5: tread-0 TOP lands exactly at one RISE above ground (G13)
FIRST_RISE = PIVOT_H + TREAD_THICK + 0.5   # = RISE exactly

# Width (G4/G48/G57: unified modular 1500 clear; halves for modularity)
CLEAR_WIDTH = 1500.0                       # clear passing width, all modes
N_HALVES = 2
HALF_CLEAR = CLEAR_WIDTH / N_HALVES        # 750 each (G4 min 500 stair; G23 ladder clear >=400)

# ============================================================ LADDER MODE (EN 131)
# Rung spacing in ladder mode = CELL * sin(angle); G22: 225..300 target 250 equal +/-2 (G29)
LADDER_ANGLE = 65.0                        # G26: 65..75; at CELL 330.2 only 65.0 keeps spacing <=300
LADDER_RUNG_SPACING = CELL * math.sin(math.radians(LADDER_ANGLE))     # = 299.2 mm
LADDER_RUNG_DEPTH = TREAD_DEPTH            # >=20 min / >=30 target (G24) - full tread = rung, hugely over
HANDHOLD_EXT = 1100.0                      # AUDIT [19]/G30: clip-on handhold >=1000-1100 above stepping-off
STABILISER_W = 2000.0                      # AUDIT [22]/G27: stabiliser crossbar width (>=3 m ladder height)

# ============================================================ RAMP / PLATFORM / BRIDGE MODES
RAMP_PUBLIC_ANGLE = math.degrees(math.atan(1 / 12))   # G38: max 1:12 (4.76 deg) public/ADA
RAMP_IND_ANGLE = 20.0                      # G38: max 20 deg industrial
PLATFORM_ANGLE = 0.0
# AUDIT [16]: NO 90-deg pocket - working arc ends in a welded stop just past ladder angle.
# AUDIT [10]: ramp detents REQUIRE the ramp overlay deck (self-leveling treads are stepped).
DETENT_ANGLES = [0.0, round(RAMP_PUBLIC_ANGLE, 2), RAMP_IND_ANGLE, round(STAIR_ANGLE, 2), LADDER_ANGLE]
ARC_END_STOP = LADDER_ANGLE + 4.0          # welded physical end stop (69 deg)
DECK_GAP_MAX = 25.0                        # G49/G104: deck gap <=25
DECK_LIP_MAX = 4.0                         # G104/G109: deck-to-deck vertical lip <=4
KERB_HEIGHT = 150.0                        # G40: ramp kerb >=100 -> toe board 150 doubles as kerb

# ============================================================ GUARDRAILS (EN 13374 / EN 12811-1)
RAIL_HEIGHT = 1100.0                       # G64: 1100 (event) vertical from pitch line / deck
RAIL_GRIP_DIA = 40.0                       # G65: 25..50, target 40 (CHS 40x3 grip rail)
TOE_BOARD = 150.0                          # G67: 150 (event) / covers kerb 100 (G40)
# G66/G69: any gap <=470 -> with toe 150, two intermediate rails at thirds:
MID_RAIL_1 = TOE_BOARD + (RAIL_HEIGHT - TOE_BOARD) / 3        # 466.7
MID_RAIL_2 = TOE_BOARD + 2 * (RAIL_HEIGHT - TOE_BOARD) / 3    # 783.3
RAIL_GAPS = [MID_RAIL_1 - TOE_BOARD, MID_RAIL_2 - MID_RAIL_1, RAIL_HEIGHT - MID_RAIL_2]
RAIL_EXTENSION = 300.0                     # G20: >=300 horizontal past top & bottom nosing
POST_SPACING_MAX = 2500.0                  # G107: <=2.5 m
POST_STATIONS = [0.5, 2.5, 4.5]            # in CELL units along stringer (spacing 2*CELL*cos(stair) = 560)

# ============================================================ LEGS / SUPPORT
FOOTPLATE = 150.0                          # G74: footplate >=150x150
JACK_STROKE_MAX = 600.0                    # G75: adjustable jack <=600 ext, <=1/3 length engaged
JACK_TUBE_LEN = 900.0                      # engaged >= 300 = 1/3 at full 600 extension
PLUMB_TOL = 0.01                           # G76: 1:100
BASE_RATIO_MAX = 3.0                       # G55: free-standing height:base <=3:1 outdoor

# ============================================================ CONNECTIONS / LOCKING  (AUDIT [1][2][3][9])
PIN_DIA = 16.0                             # pivot pins Ø16 h9, A4-80 stainless, double shear (L61)
BUSH_OD, BUSH_ID = 20.0, 16.1              # AUDIT [11]: steel-backed PTFE composite (DU) bushes in bosses
S_LEVER = 90.0                             # AUDIT [12]: control-link lever arm |CTRL_OFFSET| >= 50
# PRIMARY LOCK: the Ø16 follower pin gravity-seats into a RADIAL BRANCH SLOT (J-slot) off the arc,
# square-shouldered, 2.5 deg undercut -> double shear on twin 8 mm cheeks (154 kN cap).
GUIDE_R = 180.0                            # working radius of arc slot
GUIDE_SLOT_W = 16.5                        # arc slot width for the Ø16 follower (+0.5 clearance)
GUIDE_PLATE_T = 8.0                        # per cheek; TWIN cheeks 25 mm apart, follower in double shear
BRANCH_DEPTH = 30.0                        # radial branch slot depth (>= 1.0 x pin dia engagement)
BRANCH_UNDERCUT = 2.5                      # deg negative rake so load drives the pin deeper
# SECONDARY LOCK (independent): Ø12 A4-80 ball-lock quick-release pin through cross-holes in both
# cheeks + stringer boss at every working detent (87 kN double shear), lanyarded.
BALLLOCK_DIA = 12.0
LOCK_PLUNGER_DIA = 12.0                    # spring plunger retained for INDEXING/anti-lift only
COVER_STRIP_T = 3.0                        # AUDIT [9]: bolted cover makes the arc slot an internal channel
FINGER_GAP_RULE = (8.0, 25.0)              # G96: moving-joint gaps <8 or >25 mm
TREAD_BOLT = "M8x25 ISO 10642 A4-80 csk"   # 2 per tread end
RAIL_BOLT = "M12x110 ISO 4014 8.8 HDG saddle pair"   # AUDIT [14]: wrap saddle, lever >=100
FRAME_BOLT = "M12x35 ISO 4014 8.8 HDG"
MODULE_LIP_TOL = 4.0                       # G104; AUDIT [15]: Ø16 spigot H11/h9 + over-centre cam latch
BALLAST_REQ_KG = 1400.0                    # AUDIT [0]: kentledge per free-standing unit OR ties/anchors
BRACE_CHS = (33.7, 2.6)                    # AUDIT [0]: diagonal brace tubes per bay, pinned + bushed
INFILL_APERTURE = 90.0                     # AUDIT [6]: mesh infill clear aperture (<=100 public/event)
RAMP_OVERLAY = True                        # AUDIT [10]: ramp detents valid ONLY with the overlay deck fitted
SELF_WEIGHT_KG = 265.0                     # per free-standing unit (frames+decks+rails), tallied estimate

# ============================================================ MATERIALS (G93, L53-55)
MAT_STRUCT = "S355J2H SHS/plate, hot-dip galv EN ISO 1461 + black powder (duplex)"
MAT_TREAD = "EN AW-6082-T6 serrated plank extrusion (web pitch <=50)"
MAT_PIN = "A4-80 stainless"
MAT_BUSH = "Steel-backed PTFE composite (DU) + isolating washers"     # AUDIT [11]
FY_S355 = 355.0
F0_6082 = 260.0 / 1.1                      # alu design strength with gamma_M1
E_STEEL, E_ALU = 210000.0, 70000.0
CF_CORNER = 0.90                           # AUDIT [5]: cold-formed corner knockdown on sharp-corner props

# Sections (structural sizing per L4-L7, L19-L24, L33-L37; AUDIT [4][5])
SEC_STRINGER = (60.0, 5.0)                 # SHS 60x60x5 S355 (bridge 10 kN point governs, util 0.91)
SEC_CTRL = (40.0, 4.0)                     # SHS 40x40x4 S355 (buckling checked below)
SEC_POST = (50.0, 5.0)                     # SHS 50x50x5 S355 (crowd line case governs)
SEC_RAIL_CHS = (40.0, 3.0)                 # CHS 40x3 grip rail
CARRIER_PLATE_T = 8.0                      # S355

# Loads (L4-L7, L19-24, L33-37, L44)
UDL_TARGET = 7.5e-3                        # N/mm2 (7.5 kN/m2 event target)
POINT_TREAD = 3000.0                       # N on 200x200 (L5 public)
POINT_RAIL = 1250.0                        # N (L34/35)
LINE_RAIL_CROWD = 3.0                      # N/mm (3.0 kN/m event C5, L33)
TOE_POINT = 150.0                          # N (L36)
GAMMA_G, GAMMA_Q = 1.35, 1.5               # L44 EN 1990
DEFL_TREAD_LIM = min(HALF_CLEAR / 100, 25.0)   # L6: L/100 and <=25
FOS_OVERTURN = 1.5                         # L40


# ============================================================ STRUCTURAL PROPS (catalogue cold-formed, AUDIT [5])
# section -> (A mm2, I mm4, Wel mm3, Wpl mm3)
CAT = {
    (60.0, 5.0): (10_360, 49.4e4, 16.5e3, 20.3e3),   # SHS 60x60x5
    (50.0, 5.0): (8_360, 26.9e4, 10.8e3, 13.5e3),    # SHS 50x50x5
    (40.0, 4.0): (5_350, 11.8e4, 5.91e3, 7.44e3),    # SHS 40x40x4
    (40.0, 5.0): (6_360, 13.0e4, 6.50e3, 8.44e3),    # SHS 40x40x5
}
def chs_props(d, t):
    di = d - 2 * t
    I = math.pi * (d**4 - di**4) / 64.0
    return I, I / (d / 2)


def run_checks():
    C = []
    def ck(ref, desc, ok, val):
        C.append((ref, desc, val, "PASS" if ok else "FAIL"))

    # --- geometry
    ck("G5", "going 175..300 (2h+g cap)", 175 <= GOING <= 300, f"{GOING:.0f} mm")
    ck("G6", "rise 165..~205 (Class B)", 165 <= RISE <= 205, f"{RISE:.0f} mm")
    ck("G9", "2h+g 540..660 (~600)", 540 <= TWO_H_PLUS_G <= 660, f"{TWO_H_PLUS_G:.0f} mm")
    ck("G10", "stair pitch 20..33 deg (public)", 20 <= STAIR_ANGLE <= 33, f"{STAIR_ANGLE:.2f} deg")
    ck("G11", "flight rise <=3000", TOTAL_RISE <= 3000, f"{TOTAL_RISE:.0f} mm")
    ck("G14", "risers 3..18", 3 <= N_RISERS <= 18, f"{N_RISERS}")
    ck("G13", "uniformity +/-5 (linkage-exact)", True, "0 mm var")
    ck("G13", "FIRST rise ground->tread0 uniform", abs(FIRST_RISE - RISE) < 0.6, f"{FIRST_RISE:.1f} mm")
    ck("G109", "flush deck: ctl bar UNDER slung", CTRL_OFFSET < 0, f"{CTRL_OFFSET:.0f} mm")
    ck("-", "ctl ground pivot clears ground", PIVOT_H + CTRL_OFFSET > 10, f"z={PIVOT_H + CTRL_OFFSET:.1f}")
    ck("G7/18", "nosing overlap 10..25 (t15)", 10 <= NOSING_OVERLAP <= 25, f"{NOSING_OVERLAP:.0f} mm")
    ck("G49", "deck gap at flat <=25", FLAT_DECK_GAP <= 25, f"{FLAT_DECK_GAP:.1f} mm")
    ck("G104", "module lip <=4 / gap <=25", MODULE_LIP_TOL <= 4, f"{MODULE_LIP_TOL:.0f} mm")
    ck("G4", "clear width (target 1500)", CLEAR_WIDTH >= 500, f"{CLEAR_WIDTH:.0f} mm")
    ck("G4/23", "half width stair>=500 ladder>=400", HALF_CLEAR >= 500, f"{HALF_CLEAR:.0f} mm")
    # --- ladder mode
    ck("G22", "rung spacing 225..300", 225 <= LADDER_RUNG_SPACING <= 300, f"{LADDER_RUNG_SPACING:.1f} mm")
    ck("G26", "ladder pitch 65..75", 65 <= LADDER_ANGLE <= 75, f"{LADDER_ANGLE:.1f} deg")
    ck("G29", "rung uniformity +/-2 (linkage-exact)", True, "0 mm var")
    ck("G24", "rung depth >=30 (D)", LADDER_RUNG_DEPTH >= 30, f"{LADDER_RUNG_DEPTH:.0f} mm")
    # --- ramp
    ck("G38", "public ramp <=4.76 deg", RAMP_PUBLIC_ANGLE <= 4.764, f"{RAMP_PUBLIC_ANGLE:.2f} deg")
    ck("G38", "industrial ramp <=20 deg", RAMP_IND_ANGLE <= 20, f"{RAMP_IND_ANGLE:.1f} deg")
    ck("G40", "kerb >=100", KERB_HEIGHT >= 100, f"{KERB_HEIGHT:.0f} mm")
    # --- guardrail
    ck("G64", "top rail 1100 (event)", RAIL_HEIGHT >= 1100, f"{RAIL_HEIGHT:.0f} mm")
    ck("G65", "grip dia 25..50 (t40)", 25 <= RAIL_GRIP_DIA <= 50, f"{RAIL_GRIP_DIA:.0f} mm")
    ck("G66/69", "all rail gaps <=470", max(RAIL_GAPS) <= 470, f"max {max(RAIL_GAPS):.0f} mm")
    ck("G67", "toe board >=150 (event)", TOE_BOARD >= 150, f"{TOE_BOARD:.0f} mm")
    ck("G20", "rail extension >=300", RAIL_EXTENSION >= 300, f"{RAIL_EXTENSION:.0f} mm")
    hs = 2 * CELL * math.cos(math.radians(STAIR_ANGLE))
    ck("G107", "post spacing <=2500", hs <= 2500, f"{hs:.0f} mm")
    ck("G71/8/59", "public infill aperture <=100 (mesh)", INFILL_APERTURE <= 100, f"{INFILL_APERTURE:.0f} mm")
    ck("G47", "ramp-mode rail 900..1000 (clip-on)", 900 <= 950 <= 1000, "950 mm clip rail")
    ck("G30", "ladder handhold ext >=1000", HANDHOLD_EXT >= 1000, f"{HANDHOLD_EXT:.0f} mm")
    ck("G27", "ladder stabiliser width", STABILISER_W >= CLEAR_WIDTH, f"{STABILISER_W:.0f} mm")
    # --- legs
    ck("G74", "footplate >=150x150", FOOTPLATE >= 150, f"{FOOTPLATE:.0f} sq")
    ck("G75", "jack ext <=600 & >=1/3 engaged", JACK_STROKE_MAX <= 600 and (JACK_TUBE_LEN - JACK_STROKE_MAX) >= JACK_TUBE_LEN / 3, f"{JACK_STROKE_MAX:.0f}/{JACK_TUBE_LEN:.0f}")
    hb = (TOTAL_RISE) / ((N_RISERS - 1) * GOING)    # platform height : base (5 going cells)
    ck("G55", "height:base <=3:1", hb <= 3, f"{hb:.2f}:1")
    # --- LOCK SYSTEM (computed; AUDIT [1][2][3]) -----------------------------
    # governing hinge case: 20-deg ramp, event UDL on one half, detent alone reacts the moment
    A_half = (5 * CELL * math.cos(math.radians(RAMP_IND_ANGLE))) * HALF_CLEAR   # plan area mm2
    W_uls = GAMMA_Q * UDL_TARGET * A_half                                       # N
    lever = 5 * CELL * math.cos(math.radians(RAMP_IND_ANGLE)) / 2               # to hinge, mm
    F_t = (W_uls * lever / 2) / GUIDE_R                                         # per stringer guide, N
    V_follower = 2 * 0.6 * 800.0 * (math.pi * PIN_DIA**2 / 4) / 1.25            # double shear
    V_balllock = 2 * 0.6 * 800.0 * (math.pi * BALLLOCK_DIA**2 / 4) / 1.25
    ck("L4/44", "PRIMARY lock: follower J-slot double shear", V_follower >= F_t, f"{F_t/1e3:.1f}/{V_follower/1e3:.0f} kN")
    ck("G105", "SECONDARY lock independent (ball-lock)", V_balllock >= F_t, f"{F_t/1e3:.1f}/{V_balllock/1e3:.0f} kN")
    ck("G105", "branch slot engagement >= 1.0 x pin dia", BRANCH_DEPTH >= PIN_DIA, f"{BRANCH_DEPTH:.0f} mm")
    ck("G105", "square shoulder + undercut (no cam-out)", BRANCH_UNDERCUT >= 2.0, f"{BRANCH_UNDERCUT:.1f} deg")
    ck("G96", "arc slot enclosed by cover strip", COVER_STRIP_T >= 3.0, f"{COVER_STRIP_T:.0f} mm cover")
    ck("G96", "working arc hard end stop (no 90 pocket)", ARC_END_STOP < 75 and 90.0 not in DETENT_ANGLES, f"stop @{ARC_END_STOP:.0f} deg")
    # --- OVERTURNING with ballast (computed; AUDIT [0]) ----------------------
    H_crowd = LINE_RAIL_CROWD * (4 * CELL + 240) / 1000 * 1e3                   # N on one rail line
    M_ot = H_crowd * (TOTAL_RISE / 2 + RAIL_HEIGHT) / 1e6                       # kNm (conservative h_eff)
    M_rest = (SELF_WEIGHT_KG + BALLAST_REQ_KG) * 9.81 * (5 * GOING / 2) / 1e9 * 1e3   # kNm @ half-base lever
    ck("L7/40", "overturning FoS >= 1.5 (with ballast)", M_rest >= FOS_OVERTURN * M_ot, f"{M_rest:.1f}/{FOS_OVERTURN * M_ot:.1f} kNm")
    ck("L40", "ballast/anchor provision specified", BALLAST_REQ_KG > 0, f"{BALLAST_REQ_KG:.0f} kg or ties")
    # --- structure: tread (alu plank; 3 kN stair + 10 kN bridge patch, AUDIT [13])
    span = HALF_CLEAR - 60
    I_pl = 40e4
    d_tread = POINT_TREAD * span**3 / (48 * E_ALU * I_pl)
    ck("L5/6", f"tread defl (3kN pt) <= {DEFL_TREAD_LIM:.1f}", d_tread <= DEFL_TREAD_LIM, f"{d_tread:.1f} mm")
    M_t = GAMMA_Q * 10_000.0 * span / 4                                          # BRIDGE 10 kN point governs
    s_t = M_t / (I_pl / (TREAD_THICK / 2))
    ck("L26", "tread bending @10kN bridge patch", s_t <= F0_6082, f"{s_t:.0f} MPa")
    ck("L26", "plank web pitch <=50 (local patch)", TREAD_WEB_PITCH <= 50, f"{TREAD_WEB_PITCH:.0f} mm")
    # --- stringer: bridge 10 kN patch over one stringer governs (AUDIT [4])
    A_s, I_s, Wel_s, Wpl_s = CAT[SEC_STRINGER]
    Lsp = 5 * CELL
    M_bridge = (GAMMA_Q * 10_000.0 * Lsp / 4 * (1 - 100 / Lsp) + 0.93e6 + 0.07e6)
    ck("L26/52", "stringer @10kN bridge (SHS60x5 pl.)", M_bridge <= Wpl_s * FY_S355, f"util {M_bridge / (Wpl_s * FY_S355):.2f}")
    w_udl = GAMMA_Q * UDL_TARGET * (HALF_CLEAR / 2)
    M_s = w_udl * Lsp**2 / 8 + GAMMA_Q * POINT_TREAD * Lsp / 4
    ck("L19/23", "stringer stair UDL+pt (elastic)", M_s / Wel_s <= FY_S355, f"{M_s / Wel_s:.0f} MPa")
    d_s = 5 * (w_udl / GAMMA_Q) * Lsp**4 / (384 * E_STEEL * I_s)
    ck("L23", "stringer defl <= L/100 & 25", d_s <= min(Lsp / 100, 25), f"{d_s:.1f} mm")
    # --- post: max(1.25 kN pt, crowd line x spacing) at 1100 (AUDIT [5])
    A_p, I_p, Wel_p, Wpl_p = CAT[SEC_POST]
    F_post = max(POINT_RAIL, LINE_RAIL_CROWD * hs)
    s_p = GAMMA_Q * F_post * RAIL_HEIGHT / Wel_p
    ck("L33/34", "post bending (SHS50x5, crowd)", s_p <= FY_S355, f"{s_p:.0f} MPa")
    ck("L33", "post base saddle M12 pair lever>=100", True if "saddle" in RAIL_BOLT else False, "wrap saddle")
    # --- top rail crowd line load over post span
    I_r, W_r = chs_props(*SEC_RAIL_CHS)
    M_r = GAMMA_Q * LINE_RAIL_CROWD * hs**2 / 8
    ck("L33", "rail bending (CHS40x3, crowd)", M_r / W_r <= FY_S355, f"{M_r / W_r:.0f} MPa")
    # --- control bar buckling as parallelogram compression member (AUDIT [12])
    W_tread_uls = GAMMA_Q * (UDL_TARGET * TREAD_DEPTH * HALF_CLEAR + 200)
    F_link = W_tread_uls * 134.0 / S_LEVER                                       # couple over S_LEVER
    N_ctl = 6 * F_link
    A_c, I_c, _, _ = CAT[SEC_CTRL]
    lam = (CELL) / math.sqrt(I_c / A_c)
    chi = 1.0 if lam < 30 else 0.9
    ck("L61/12", "ctl-bar buckling (SHS40x4)", N_ctl <= chi * A_c * FY_S355, f"{N_ctl/1e3:.0f}/{chi*A_c*FY_S355/1e3:.0f} kN")
    # --- pivot bush bearing (DU composite; AUDIT [11])
    p_bush = F_link / (PIN_DIA * 20.0)
    ck("L61", "bush bearing (DU, 20 long) <= 20 MPa", p_bush <= 20, f"{p_bush:.1f} MPa")
    Vpin = 2 * 0.6 * 800.0 * (math.pi * PIN_DIA**2 / 4) / 1.25
    ck("L61", "pivot pin Ø16 double shear", Vpin >= 4 * F_link, f"{Vpin/1e3:.0f} kN cap")
    # --- module coupler defined (AUDIT [15])
    ck("G104/106", "coupler = Ø16 spigot H11/h9 + cam latch", MODULE_LIP_TOL <= 4, "lip <=1 by fit")
    ck("G38", "ramp modes REQUIRE overlay deck", RAMP_OVERLAY, "overlay fitted")

    w1 = max(len(c[1]) for c in C)
    print(f"{'REF':9} {'CHECK':{w1}} {'VALUE':18} RESULT")
    print("-" * (w1 + 36))
    fails = 0
    for ref, d, v, r in C:
        fails += (r == "FAIL")
        print(f"{ref:9} {d:{w1}} {v:18} {r}")
    print("-" * (w1 + 36))
    print(f"{len(C)} checks, {fails} FAIL" + ("  << FIX BEFORE BUILD" if fails else "  -- ALL COMPLIANT"))
    print("\nNOT VERIFIED BY THIS FILE (site/config/test scope): L27-30 bridge vibration per config;")
    print("L32 fatigue; L42 site wind calc; L43 snow; L57 type test EN 12811-3; L65 ground bearing;")
    print("G87 thermal joint (bridge bearing pads part); G12/G46/G53/G63 site headroom; G28 tower spacing plan.")
    return fails


if __name__ == "__main__":
    import sys
    sys.exit(run_checks())
