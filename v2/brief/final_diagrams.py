"""Section / detail drawings for the brief's 25 Sep model check (F1-F8). Same drawing language as the earlier brief:
grey dashed = now, orange = change. All sizes in mm, drawn to scale inside each panel (scale noted per drawing).
Uses the brief's CSS classes (.sec .old .old2 .new .new2 .newf .void .dim .tag .note .note2 .grd .axle)."""
import math

def _svg(w, h, body, label):
    return f'<div class="draw"><svg class="sec" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">{body}</svg></div>'
def R(x, y, w, h, cls="new"): return f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{max(w, 0.6):.1f}" height="{max(h, 0.6):.1f}"/>'
def T(x, y, s, cls="", anchor="start"): return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}">{s}</text>'
def Ln(x0, y0, x1, y1, cls="dim"): return f'<line class="{cls}" x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}"/>'
def C(x, y, r, cls="new"): return f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>'
def arrow(x0, y0, x1, y1, cls="dim"):
    a = math.atan2(y1 - y0, x1 - x0); h = 7
    p = [(x1, y1), (x1 - h * math.cos(a - 0.4), y1 - h * math.sin(a - 0.4)), (x1 - h * math.cos(a + 0.4), y1 - h * math.sin(a + 0.4))]
    return Ln(x0, y0, x1, y1, cls) + f'<polygon class="{"new" if cls == "newl" else "arrowh"}" points="{" ".join(f"{u:.1f},{v:.1f}" for u, v in p)}"/>'

# ------------------------------------------------------------------ F1 step section
def f1_section(box):
    """box: dict(t_top, t_bot, t_wall, webs, t_web)"""
    s = 1.55; H = 50 * s
    def sec(ox, oy, rects, cls):
        return "".join(R(ox + x0 * s, oy + (50 - z1) * s, (x1 - x0) * s, (z1 - z0) * s, cls) for x0, z0, x1, z1 in rects)
    ox1, oy = 20, 44
    now = [(0, 0, 5, 50), (0, 0, 50, 5), (45, 0, 50, 17.5), (275, 25, 280, 50), (252.5, 25, 280, 30)]
    body = T(ox1, 18, "NOW · open J + L, no top plate", "tag")
    body += R(ox1 + 5 * s, oy, 270 * s, 25 * s, "old2")
    body += sec(ox1, oy, now, "new2")
    for xf in (83.65, 190.8): body += R(ox1 + (xf - 1.35) * s, oy, 2.7 * s, 25 * s, "new2")
    body += T(ox1, oy + H + 22, "J (back) + L (front); grating bars (shaded) run front to back", "") + T(ox1, oy + H + 40, "2 flats 2.7 × 25 along the step", "")
    ox2 = ox1 + 280 * s + 70
    tt, tb, tw = box["t_top"], box["t_bot"], box["t_wall"]
    new = [(0, 50 - tt, 280, 50), (0, 0, 280, tb), (0, 0, tw, 50), (280 - tw, 0, 280, 50)]
    for xw in box.get("webs", ()): new.append((xw - (box.get("t_web") or tw) / 2, 0, xw + (box.get("t_web") or tw) / 2, 50))
    body += T(ox2, 18, "CHANGE TO · closed box, same 280 × 50", "tag") + sec(ox2, oy, new, "new")
    body += T(ox2, oy + H + 22, f"top {tt:g} (serrated) · bottom {tb:g} · walls {tw:g}" + (f" · {len(box.get('webs', ()))} inner web{'s' if len(box.get('webs', ())) > 1 else ''} {box.get('t_web') or tw:g}" if box.get("webs") else ""), "note")
    body += Ln(ox2 - 8, oy, ox2 - 8, oy + H) + T(ox2 - 12, oy + H / 2 + 4, "50", "", "end")
    body += Ln(ox2, oy + H + 34, ox2 + 280 * s, oy + H + 34) + T(ox2 + 140 * s, oy + H + 48, "280", "", "middle")
    w = int(ox2 + 280 * s + 20)
    return _svg(w, int(oy + H + 60), body, "Step section: open J and L with grating now, closed box after")

# ------------------------------------------------------------------ F2 step pin + rail depth
def f2_pin(depth=70, metal=20):
    s = 4.0; oy = 175; body = ""
    def stack(ox, d, now, title, note):
        b = T(ox - 30, 18, title, "tag")
        parts = [("end plate", 5), ("washer", 2), ("bush", 7), ("rail wall", 5)]
        x = ox; xs = []
        for nm, t in parts:
            b += R(x, oy - 20 * s, t * s, 40 * s, "old2"); xs.append((nm, x, t)); x += t * s
        pin = R(ox - 30, oy - d * s / 2, 19 * s + 60, d * s, "old" if now else "new")
        b += pin
        b += T(ox + 5 * s, oy + 20 * s + 16, "end plate", "", "end") + T(ox + 14 * s, oy + 20 * s + 16, "rail wall", "", "start")
        b += Ln(ox + 6 * s, oy + 20 * s, ox + 6 * s, oy + 20 * s + 26) + T(ox + 6 * s, oy + 20 * s + 38, "washer", "", "middle")
        b += Ln(ox + 10.5 * s, oy + 20 * s, ox + 10.5 * s, oy + 20 * s + 44) + T(ox + 10.5 * s, oy + 20 * s + 56, "bush", "", "middle")
        b += arrow(ox + 2.5 * s, oy - 20 * s - 34, ox + 2.5 * s, oy - 20 * s - 4, "newl" if not now else "dim") + T(ox + 2.5 * s + 8, oy - 20 * s - 22, "step load", "")
        b += Ln(ox + 2.5 * s, oy - 20 * s - 44, ox + 16.5 * s, oy - 20 * s - 44) + T(ox + 9.5 * s, oy - 20 * s - 50, "lever 14 mm", "", "middle")
        b += T(ox - 30, oy + 20 * s + 80, note, "note" if not now else "")
        return b
    body += stack(90, 10, True, "NOW · Ø10 pin (right-hand side)", "bends 5.3× too much at the top step")
    body += stack(390, 20, False, "CHANGE TO · Ø20 pin, Ø20 holes", "0.66 bending, 0.25 shear")
    rs = 2.0; rx = 660; ry = 40
    body += T(rx, 18, f"RAIL · 25 deep → about {depth} deep", "tag")
    body += R(rx, ry, 25 * rs, 25 * rs, "old") + T(rx + 12.5 * rs, ry + 25 * rs + 16, "now", "", "middle")
    body += R(rx + 90, ry, 25 * rs, depth * rs, "new") + R(rx + 90 + 5 * rs, ry + 5 * rs, 15 * rs, (depth - 5) * rs, "void")
    body += C(rx + 90 + 12.5 * rs, ry + 22 * rs, 10 * rs, "void")
    body += T(rx, ry + depth * rs + 22, f"{depth} deep; {metal} mm of metal", "note") + T(rx, ry + depth * rs + 40, "round each Ø20 hole", "note")
    return _svg(900, 390, body, "Step pin: 10 mm now, 20 mm after; rail deepened to about 65 mm")

# ------------------------------------------------------------------ F3 pole locking end in the lower rail
def f3_pegs():
    s = 5.0; body = ""; oy = 70
    def panel(ox, d, now, title, note):
        b = T(ox, 18, title, "tag")
        b += R(ox, oy, 5 * s, 25 * s, "old2") + R(ox + 30 * s, oy, 5 * s, 25 * s, "old2") + R(ox, oy + 20 * s, 35 * s, 5 * s, "old2")   # U channel
        b += R(ox + 12.5 * s, oy - 8, 10 * s, 25 * s + 24, "new2")                                                                         # pole end
        zc = oy + 10 * s
        cls = "old" if now else "new"
        b += R(ox + 2.5 * s, zc - d * s / 2, 10 * s, d * s, cls) + R(ox + 22.5 * s, zc - d * s / 2, 10 * s, d * s, cls)                   # the two pegs
        b += T(ox, oy + 25 * s + 36, note, "" if now else "note")
        return b
    body += panel(40, 2, True, "NOW · 2 mm pegs", "2 per rail, 4 per pole: far too weak")
    body += panel(330, 12, False, "CHANGE TO · 12 mm pegs", "0.58 (each reaches 7.5 mm to the wall)")
    body += T(620, 70, "pole and locking end: one piece", "note2") + T(620, 92, "the pegs sit in holes in the rail walls", "")
    body += T(620, 110, "and hold the upper and lower rail", "") + T(620, 128, "at their spacing (the fold lock)", "") + T(620, 162, "add the upper-rail pair to the drawing", "note")
    return _svg(900, 262, body, "Pole locking end in the rail: 2 mm pegs now, 12 mm after")

# ------------------------------------------------------------------ F4 pole section + outside mounting
def f4_pole(depth=55):
    s = 3.2; body = ""; oy = 40
    body += T(30, 18, "NOW · hollow 25 × 10 × 2", "tag") + R(40, oy, 25 * s, 10 * s, "old") + R(40 + 2 * s, oy + 2 * s, 21 * s, 6 * s, "void")
    body += T(250, 18, f"CHANGE TO · solid 25 × {depth}", "tag") + R(260, oy, 25 * s, depth * s, "new")
    body += arrow(260 + 12.5 * s, oy + depth * s + 40, 260 + 12.5 * s, oy + depth * s + 8, "newl") + T(40, oy + depth * s + 62, "people push this way (across the stair) ↑", "note")
    body += T(40, oy + 10 * s + 20, "25 along the stair", "") + T(40, oy + 10 * s + 38, "10 across", "")
    # elevation: pole outside the rails, bolted to both
    ex, ey = 560, 30; es = 0.42
    body += T(ex, 18, "IT CAN’T PASS THROUGH A 35 WIDE RAIL", "tag")
    body += R(ex, ey + 40, 60, 16, "old2") + T(ex + 66, ey + 52, "upper rail", "") + R(ex, ey + 40 + 167 * es, 60, 16, "old2") + T(ex + 66, ey + 52 + 167 * es, "lower rail", "")
    body += R(ex - 26, ey, 22, 260 * es + 110, "new") + C(ex - 15, ey + 48, 4, "void") + C(ex - 15, ey + 48 + 167 * es, 4, "void")
    body += T(ex - 40, ey + 260 * es + 130, "pole on the outside face, 2 bolts into each rail", "note")
    return _svg(900, int(max(oy + depth * s + 60, 250)), body, f"Pole: hollow 25 x 10 now, solid 25 x {depth} after, mounted outside the rails")

# ------------------------------------------------------------------ F5 base: axle, hook, jack (plan, right-hand end)
def f5_base():
    s = 2.0; oy = 120; body = ""
    # NOW: jack centre at y 0, hook 70 mm inboard, tube ends 52 mm inboard (34 mm short of the jack head)
    jx = 360
    body += T(30, 18, "NOW · plan of the right-hand base end", "tag")
    body += R(40, oy - 12.5 * s, (jx - 52 * s) - 40, 25 * s, "old") + T(50, oy - 12.5 * s - 8, "axle Ø25 × 2.5", "")
    body += R(jx - 70 * s - 5 * s, oy - 30 * s, 10 * s, 60 * s, "new2") + T(jx - 70 * s, oy + 30 * s + 16, "hook (part of the rail)", "", "middle")
    body += C(jx, oy, 18 * s, "old2") + T(jx, oy + 18 * s + 16, "jack head", "", "middle")
    body += R(jx - 52 * s, oy - 12.5 * s, 52 * s, 25 * s, "newf") + T(jx - 26 * s, oy - 12.5 * s - 8, "missing", "note", "middle")
    body += Ln(jx - 70 * s, oy + 30 * s + 30, jx, oy + 30 * s + 30) + T(jx - 35 * s, oy + 30 * s + 46, "70 mm: the tube bends here", "", "middle")
    # CHANGE TO: jack head under the hook, one tube, collars
    ox = 500; hx = ox + 250
    body += T(ox, 18, "CHANGE TO · jack under the hook, collars", "tag")
    body += R(ox, oy - 15 * s, 300, 30 * s, "new") + T(ox + 10, oy - 15 * s - 8, "one tube, jack head to jack head", "note")
    body += C(hx, oy, 18 * s, "old") + R(hx - 5 * s, oy - 30 * s, 10 * s, 60 * s, "new2")
    body += R(hx - 5 * s - 10, oy - 18 * s, 8, 36 * s, "new") + R(hx + 5 * s + 2, oy - 18 * s, 8, 36 * s, "new")
    body += T(hx, oy + 30 * s + 16, "hook over the jack head, collar each side", "", "middle")
    body += T(ox, oy + 30 * s + 46, "Ø30 × 3 · or keep the offset with a 48.3 × 4 scaffold tube", "note")
    return _svg(900, 250, body, "Base plan: hook 70 mm from the jack and the tube short of it now; jack under the hook with collars after")

# ------------------------------------------------------------------ F6 top rail height: step surface vs pitch line (side view)
def f6_height():
    s = 0.24; ox, oy = 60, 440; body = ""
    def P(x, z): return ox + x * s, oy - z * s
    for i in range(3):                                   # steps rising to the right; front edge on the left of each
        x0, y0 = P(250 * i, 175 * i + 50); body += R(x0, y0, 280 * s, 50 * s, "old2")
    body += Ln(*P(-150, 50 - 105), *P(760, 50 + 532), "grd")
    body += T(P(600, 0)[0] + 8, P(0, 50 + 420)[1] + 4, "pitch line (joins the step fronts)", "note2")
    xp = 250 + 142; zt = 175 + 50; zpl = 50 + 0.7 * xp
    body += R(P(xp, 0)[0] - 2, P(0, zt + 1112)[1], 4, 1112 * s, "old2")
    body += Ln(*P(xp - 300, zt + 1112 - 210), *P(xp + 300, zt + 1112 + 210), "newl")
    body += T(P(xp + 300, 0)[0] + 6, P(0, zt + 1112 + 210)[1] + 4, "top rail", "")
    x1 = P(xp, 0)[0] + 16; x2 = P(xp, 0)[0] + 150
    body += Ln(x1, P(0, zt)[1], x1, P(0, zt + 1112)[1]) + Ln(P(xp, 0)[0], P(0, zt)[1], x1 + 4, P(0, zt)[1])
    body += T(x1 + 6, P(0, zt + 380)[1], "1,112 from the step surface", "")
    body += Ln(x2, P(0, zpl)[1], x2, P(0, zt + 1112)[1], "dim") + Ln(P(xp, 0)[0], P(0, zpl)[1], x2 + 4, P(0, zpl)[1], "dim")
    body += T(x2 + 6, P(0, zpl + 700)[1], "1,013 from the pitch line", "note")
    body += T(600, 60, "Same rail, two starting lines.", "") + T(600, 82, "The sheet measures stair handrails", "") + T(600, 100, "from the pitch line; your handrail", "") + T(600, 118, "is 903 that way, which passes.", "")
    return _svg(900, 470, body, "Top rail height measured from the step surface and from the pitch line")

# ------------------------------------------------------------------ F8 handrail bracket
def f8_bracket():
    s = 6.0; body = ""; oy = 50
    body += T(40, 18, "NOW · bent flat 15 wide", "tag") + R(60, oy, 15 * s, 5 * s, "old") + T(60 + 7.5 * s, oy + 5 * s + 18, "15 × ≈ 5", "", "middle")
    body += T(300, 18, "CHANGE TO · 25 wide, same thickness", "tag") + R(320, oy, 25 * s, 5 * s, "new") + T(320 + 12.5 * s, oy + 5 * s + 18, "25 × ≈ 5 · 0.90", "note", "middle")
    ex = 600; body += T(ex, 18, "SIDE VIEW", "tag") + R(ex, 30, 14, 150, "old2") + T(ex + 7, 196, "pole", "", "middle")
    body += Ln(ex + 14, 80, ex + 14 + 57 * 2.2, 80, "newl") + R(ex + 14 + 57 * 2.2, 66, 28, 28, "old2") + T(ex + 14 + 57 * 2.2 + 14, 112, "handrail", "", "middle")
    body += Ln(ex + 14, 60, ex + 14 + 57 * 2.2, 60) + T(ex + 14 + 57 * 1.1, 52, "57 offset", "", "middle")
    return _svg(900, 210, body, "Handrail bracket: 15 wide now, 25 wide after")

# ------------------------------------------------------------------ F1 options side by side (same scale)
def f1_options(box, grating_bars, ubox):
    """box: tread_box2 cfg (A); grating_bars: list of (x, t, z0) (C); ubox: tread_ubox cfg (B)"""
    s = 1.25; H = 50 * s; W = 280 * s
    def sec(ox, oy, rects, cls):
        return "".join(R(ox + x0 * s, oy + (50 - z1) * s, (x1 - x0) * s, (z1 - z0) * s, cls) for x0, z0, x1, z1 in rects)
    def holes(ox, oy, z, t, x0=20, x1=260, pitch=40):
        return "".join(R(ox + x * s, oy + (50 - z - t / 2) * s - 1, 12 * s, t * s + 2, "void") for x in range(x0, x1, pitch))
    body = ""
    P = [(20, 30), (40 + W + 30, 30), (20, 30 + H + 90), (40 + W + 30, 30 + H + 90)]
    # now
    ox, oy = P[0]
    body += T(ox, oy - 12, "NOW · open J + L, grating front to back", "tag") + R(ox + 5 * s, oy, 270 * s, 25 * s, "old2")
    body += sec(ox, oy, [(0, 0, 5, 50), (0, 0, 50, 5), (45, 0, 50, 17.5), (275, 25, 280, 50), (252.5, 25, 280, 30)], "new2")
    body += T(ox, oy + H + 18, "fails: twists; 3.6× at 4 kN", "")
    # A thin closed box with holes
    ox, oy = P[1]; tt, tb, tw = box["t_top"], box["t_bot"], box["t_wall"]
    rects = [(0, 50 - tt, 280, 50), (0, 0, 280, tb), (0, 0, tw, 50), (280 - tw, 0, 280, 50)] + [(x - (box.get("t_web") or tw) / 2, 0, x + (box.get("t_web") or tw) / 2, 50) for x in box.get("webs", ())]
    body += T(ox, oy - 12, "A · thin closed box, holes top and bottom", "tag") + sec(ox, oy, rects, "new") + holes(ox, oy, 50 - tt / 2, tt, 15, 265, 45) + holes(ox, oy, tb / 2, tb, 35, 265, 45)
    body += T(ox, oy + H + 18, f"{tt:g} top / {tb:g} bottom / {tw:g} walls + {len(box.get('webs', ()))} webs · lightest", "note")
    # B owner's sketch
    ox, oy = P[2]
    rects = [(0, 50 - ubox["t_top"], 280, 50), (0, 25 - ubox["t_mid"] / 2, 280, 25 + ubox["t_mid"] / 2), (0, 0, 5, 50), (0, 0, 50, 5), (45, 0, 50, 17.5), (275, 25, 280, 50)]
    body += T(ox, oy - 12, "B · your sketch: 25 mm box on the J + L", "tag") + sec(ox, oy, rects, "new")
    body += holes(ox, oy, 50 - ubox["t_top"] / 2, ubox["t_top"], 60, 265, 45) + holes(ox, oy, 25, ubox["t_mid"], 60, 265, 45)
    body += T(ox, oy + H + 18, f"top {ubox['t_top']:g}, mid {ubox['t_mid']:g}, ribs inside · keeps the J and L", "note")
    # C open grating, bars along the step
    ox, oy = P[3]
    rects = [(x - t / 2, z0, x + t / 2, 50) for x, t, z0 in grating_bars] + [(grating_bars[0][0], 25, grating_bars[-1][0], 26.5)]
    body += T(ox, oy - 12, "C · open grating, bars along the step", "tag") + sec(ox, oy, [r for r in rects[:-1]], "new")
    body += R(ox + grating_bars[0][0] * s, oy + (50 - 50) * s, (grating_bars[-1][0] - grating_bars[0][0]) * s, 1.5, "newf")
    pitch = (grating_bars[-1][0] - grating_bars[0][0]) / (len(grating_bars) - 1)
    body += T(ox, oy + H + 18, f"3 × 50 bars every {pitch:.0f} mm, {grating_bars[-1][1]:g} mm front bar · most open", "note")
    return _svg(int(2 * W + 110), int(2 * (H + 90) + 30), body, "Step options: now, thin closed box, owner's 25 mm box, open grating with bars along the step")

# ------------------------------------------------------------------ F1 Rev C: A chosen, C alternative, now for reference (one column)
def f1_ac(box, grating_bars, a=(None, None), c=(None, None)):
    """box: tread_box2 cfg (A); grating_bars: list of (x, t, z0) (C); a, c: (4 kN util, kg per step)"""
    s = 1.25; H = 50 * s; W = 280 * s; ox = 20; tx = ox + W + 30; gap = H + 44
    def sec(ox, oy, rects, cls):
        return "".join(R(ox + x0 * s, oy + (50 - z1) * s, (x1 - x0) * s, (z1 - z0) * s, cls) for x0, z0, x1, z1 in rects)
    def holes(ox, oy, z, t, x0, x1, pitch):
        return "".join(R(ox + x * s, oy + (50 - z - t / 2) * s - 1, 12 * s, t * s + 2, "void") for x in range(x0, x1, pitch))
    def notes(oy, lines):
        return "".join(T(tx, oy + 10 + 16 * i, ln, "note" if i < len(lines) - 1 else "") for i, ln in enumerate(lines))
    body = ""; oy = 30
    tt, tb, tw, tweb = box["t_top"], box["t_bot"], box["t_wall"], box.get("t_web") or box["t_wall"]
    rects = [(0, 50 - tt, 280, 50), (0, 0, 280, tb), (0, 0, tw, 50), (280 - tw, 0, 280, 50)] + [(x - tweb / 2, 0, x + tweb / 2, 50) for x in box.get("webs", ())]
    body += T(ox, oy - 12, "A · CHOSEN · thin closed box", "tag") + sec(ox, oy, rects, "new") + holes(ox, oy, 50 - tt / 2, tt, 15, 265, 45) + holes(ox, oy, tb / 2, tb, 35, 265, 45)
    body += notes(oy, [f"{tt:g} top · {tb:g} bottom · {tw:g} front and back walls",
                       f"{len(box.get('webs', ()))} inner webs {tweb:g} at " + " and ".join(f"{x:g}" for x in box.get("webs", ())) + " from the back",
                       "drain holes in the top and the bottom",
                       f"4 kN at the front edge {a[0]:.2f} · {a[1]:.1f} kg per step" if a[0] else ""])
    oy += gap
    xs = [b[0] for b in grating_bars]
    body += T(ox, oy - 12, "C · ALTERNATIVE · open grating, bars along the step", "tag")
    body += R(ox + (xs[0] - grating_bars[0][1] / 2) * s, oy, (xs[-1] + grating_bars[-1][1] / 2 - xs[0] + grating_bars[0][1] / 2) * s, 25 * s, "newf")
    body += sec(ox, oy, [(x - t / 2, z0, x + t / 2, 50) for x, t, z0 in grating_bars], "new")
    inner = [b for b in grating_bars[1:-1]]
    pitch = (inner[-1][0] - inner[0][0]) / (len(inner) - 1) if len(inner) > 1 else 0
    body += notes(oy, [f"3 × 50 bars every {pitch:.0f} mm, {grating_bars[0][1]:g} mm back bar",
                       f"{grating_bars[-1][1]:g} × 50 front bar",
                       "3 × 25 cross bars on top every 50 mm (light)",
                       f"4 kN at the front edge {c[0]:.2f} · {c[1]:.1f} kg per step" if c[0] else ""])
    oy += gap
    body += T(ox, oy - 12, "NOW · open J + L, grating front to back", "tag") + R(ox + 5 * s, oy, 270 * s, 25 * s, "old")
    body += sec(ox, oy, [(0, 0, 5, 50), (0, 0, 50, 5), (45, 0, 50, 17.5), (275, 25, 280, 50), (252.5, 25, 280, 30)], "old2")
    body += T(tx, oy + 10, "J at the back, L at the front,") + T(tx, oy + 26, "grating bars (dashed) run front to back") + T(tx, oy + 42, "3.6× too much at 4 kN")
    body += Ln(ox, oy + H + 12, ox + W, oy + H + 12) + T(ox + W / 2, oy + H + 26, "280 deep, 50 high, same for all", "", "middle")
    return _svg(int(tx + 330), int(oy + H + 34), body, "Step sections: A thin closed box (chosen), C open grating with bars along the step (alternative), and the step as drawn now")
