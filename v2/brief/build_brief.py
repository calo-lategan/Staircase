"""SketchUp change brief (plain language) -> web/index.html + web/img/*.jpg
Sizes = verified lightweight all-aluminium spec (v2/loadtest/lightweight_final.json, 1.8 mm treads) with the left
rails kept as open channels so side-by-side units still nest (v2/datasheet/left_channel_check.json).
Run: uvx --with pillow python v2/brief/build_brief.py
"""
import json, os, html
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
CALL = json.load(open(os.path.join(HERE, "img", "callouts.json")))
LC = json.load(open(os.path.join(HERE, "..", "datasheet", "left_channel_check.json")))["left U-channels, 4 mm walls"]
REPORT = "https://claude.ai/artifact/1ZGWmdUZyFepc1gGMdCkok"
DATASHEET = "https://claude.ai/artifact/GLipbqMzpRje8YZFLYTeL7"
os.makedirs(os.path.join(HERE, "web", "img"), exist_ok=True)
for k, v in CALL.items():
    im = Image.open(os.path.join(HERE, "img", v["file"])).convert("RGB")
    im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
    im.save(os.path.join(HERE, "web", "img", v["file"]), quality=84, optimize=True, progressive=True)
    v["w2"], v["h2"] = im.size

# ------------------------------------------------------------------ figures: marker label = change number
FIGS = [
    ("A", "overview", "Standard stair, right-hand side", {1: 1, 2: 2, 3: 2, 4: 4, 6: 7, 9: 10}, set()),
    ("B", "post", "Bottom of a handrail pole: its lower end is the lock pin through the guide rails", {1: 4, 2: 4, 3: 2}, set()),
    ("C", "nested", "Two units side by side: the left channel with the neighbour’s right rail inside", {1: 3, 3: 3}, set()),
    ("D", "pin", "Side by side: one handrail pole\u2019s pin passes through both nested rails", {1: 4}, set()),
    ("E", "hook", "Top hook dropping over the axle of the unit below", {2: 10}, set()),
    ("F", "catwalk", "Flat catwalk seen from the side (the scaffold supports it)", {4: 2}, set()),
]


def figure(fid, key, cap, mapping, new):
    v = CALL[key]
    marks = []
    for c in v["calls"]:
        if c["n"] in mapping and c["ok"]:
            n = mapping[c["n"]]
            cls = "mk new" if c["n"] in new else "mk"
            marks.append(f'<a class="{cls}" href="#c{n}" style="left:{c["x"]}%;top:{c["y"]}%" aria-label="Change {n}">{n}</a>')
    return f"""
    <figure class="fig" id="fig{fid}">
      <div class="shot"><img src="img/{v['file']}" alt="{E(cap)}" width="{v['w2']}" height="{v['h2']}" loading="lazy">{''.join(marks)}</div>
      <figcaption><b>Fig {fid}</b> {E(cap)}</figcaption>
    </figure>"""


# ------------------------------------------------------------------ small to-scale section drawings (mm)
def svg(w, h, body, label):
    return f'<svg class="sec" viewBox="0 0 {w} {h}" role="img" aria-label="{E(label)}">{body}</svg>'


def rect(x, y, w, h, cls="new"):
    return f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}"/>'


def txt(x, y, s, cls="lbl", anchor="start"):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{E(s)}</text>'


def tread_svg():
    s = 1.0
    b = ""
    # before: two solid planks at rise 175 / going 250, 280 x 50
    ox, oy = 10, 40
    b += txt(ox, 16, "NOW", "tag")
    b += rect(ox + 250, oy, 280, 50, "old") + rect(ox, oy + 175, 280, 50, "old")
    b += f'<line class="dim" x1="{ox + 262}" y1="{oy + 50}" x2="{ox + 262}" y2="{oy + 175}"/>' + txt(ox + 268, oy + 118, "gap 125")
    b += txt(ox + 390, oy + 30, "280 × 50", "lbl", "middle")
    # after: hollow 285 x 40 + 35 mm lip at the front (front = left, downhill)
    ox2 = 600
    b += txt(ox2, 16, "CHANGE TO", "tag")
    for (x, y) in ((ox2 + 250, oy), (ox2, oy + 175)):
        b += rect(x, y, 285, 40, "new") + rect(x + 3, y + 3, 279, 34, "void")
        for k in range(1, 4):
            b += f'<line class="rib" x1="{x + 285 * k / 4}" y1="{y + 2}" x2="{x + 285 * k / 4}" y2="{y + 38}"/>'
        b += rect(x, y + 40, 2.5, 35, "new")
    b += f'<line class="dim" x1="{ox2 + 262}" y1="{oy + 75}" x2="{ox2 + 262}" y2="{oy + 175}"/>' + txt(ox2 + 268, oy + 130, "gap 100")
    b += txt(ox2 + 392, oy + 26, "285 × 40", "lbl", "middle") + txt(ox2 + 250 - 6, oy + 70, "lip 35", "lbl", "end")
    return svg(1180, 280, b, "Tread: 280 x 50 plank now, 285 x 40 hollow plank with a 35 mm front lip after")


def rails_svg():
    k = 3.2   # px per mm
    b = ""

    def uchan(x, y, slot, wall, depth, cls):
        W, H = slot + 2 * wall, depth + wall
        return (rect(x, y, wall * k, H * k, cls) + rect(x + (wall + slot) * k, y, wall * k, H * k, cls)
                + rect(x, y + depth * k, W * k, wall * k, cls))

    def box(x, y, w, h, t, cls):
        return rect(x, y, w * k, h * k, cls) + rect(x + t * k, y + t * k, (w - 2 * t) * k, (h - 2 * t) * k, "void")

    # NOW: left U 35 x 25 (5 mm) with the right inverted channel 25 x 20 nested
    x0, y0 = 20, 40
    b += txt(x0, 18, "NOW (upper pair)", "tag")
    b += uchan(x0, y0, 25, 5, 20, "old")
    b += rect(x0 + 5 * k, y0 - 1 * k, 25 * k, 5 * k, "old2") + rect(x0 + 5 * k, y0, 5 * k, 20 * k, "old2") + rect(x0 + 25 * k, y0, 5 * k, 20 * k, "old2")
    b += txt(x0 + 17.5 * k, y0 + 25 * k + 22, "35 wide", "lbl", "middle")
    # AFTER: upper U 33 x 29 with 25 x 25 box; lower U 33 x 49 with 25 x 45 box
    x1 = 250
    b += txt(x1, 18, "CHANGE TO", "tag")
    b += uchan(x1, y0, 25, 4, 25, "new") + box(x1 + 4 * k, y0, 25, 25, 2.5, "new2")
    b += txt(x1 + 16.5 * k, y0 + 29 * k + 22, "upper: 33 × 29", "lbl", "middle")
    x2 = x1 + 160
    b += uchan(x2, y0, 25, 4, 45, "new") + box(x2 + 4 * k, y0, 25, 45, 3, "new2")
    b += txt(x2 + 16.5 * k, y0 + 49 * k + 22, "lower: 33 × 49", "lbl", "middle")
    b += txt(x2 + 130, y0 + 40, "left channel (4 mm walls,", "note") + txt(x2 + 130, y0 + 58, "25 mm slot)", "note")
    b += txt(x2 + 130, y0 + 92, "right rail of the next", "note2") + txt(x2 + 130, y0 + 110, "unit sits inside", "note2")
    b += txt(x2 + 130, y0 + 144, "right rails on their own:", "note2") + txt(x2 + 130, y0 + 162, "25×25×2.5 and 25×45×3", "note2")
    return svg(760, 250, b, "Guide rails: left channels 33 x 29 and 33 x 49 with 4 mm walls; right rails 25 x 25 x 2.5 and 25 x 45 x 3 fit inside")


def post_svg():
    k = 2.2
    b = txt(10, 18, "NOW", "tag") + rect(30, 60, 25 * k, 10 * k, "old") + txt(30 + 12.5 * k, 60 + 10 * k + 22, "flat 25 × 10", "lbl", "middle")
    b += txt(230, 18, "CHANGE TO", "tag") + rect(250, 30, 60 * k, 60 * k, "new") + rect(250 + 4 * k, 30 + 4 * k, 52 * k, 52 * k, "void")
    b += txt(250 + 30 * k, 30 + 60 * k + 22, "square tube 60 × 60 × 4", "lbl", "middle")
    return svg(560, 205, b, "Post: flat 25 x 10 now, square tube 60 x 60 x 4 after")


def rails_round_svg():
    k = 2.2
    b = txt(10, 18, "NOW", "tag")
    b += rect(20, 40, 25 * k, 25 * k, "old") + rect(20 + 3.8 * k, 40 + 3.8 * k, 17.4 * k, 17.4 * k, "void") + txt(20 + 12.5 * k, 40 + 25 * k + 20, "top rail 25□", "lbl", "middle")
    b += rect(110, 40, 25 * k, 25 * k, "old") + txt(110 + 12.5 * k, 40 + 25 * k + 20, "handrail 25■", "lbl", "middle")
    b += txt(240, 18, "CHANGE TO", "tag")
    for (cx, D, t, lab) in ((290, 40, 2, "top rail Ø40×2"), (420, 48.3, 3, "handrail Ø48.3×3"), (545, 30, 2, "middle rail Ø30×2 (new)")):
        r = D / 2 * k
        b += f'<circle class="new" cx="{cx}" cy="{40 + r}" r="{r}"/><circle class="void" cx="{cx}" cy="{40 + r}" r="{r - t * k}"/>'
        b += txt(cx, 40 + 2 * r + 20, lab, "lbl", "middle")
    return svg(660, 175, b, "Rails: square bars now; round tubes 40, 48.3 and a new 30 mm middle rail after")


def heights_svg():
    s = 0.2
    base = 260
    b = f'<line class="grd" x1="20" y1="{base}" x2="560" y2="{base}"/>' + txt(24, base + 16, "step line (along the stair)", "note")
    rows = [(150, "toe board top 150 (new)", "new"), (575, "middle rail 575 (new)", "new"), (1000, "handrail ≈ 1,000", "old2"),
            (1127, "top rail ≥ 1,100 (unchanged)", "old2")]
    for h, lab, cls in rows:
        y = base - h * s
        b += f'<line class="{cls}l" x1="60" y1="{y}" x2="400" y2="{y}"/>' + txt(410, y + 4, lab, "lbl")
    b += rect(60, base - 150 * s, 340, 150 * s, "newf")
    for x in (60, 230, 400):
        b += f'<line class="postl" x1="{x}" y1="{base}" x2="{x}" y2="{base - 1127 * s}"/>'
    b += txt(60, base - 1127 * s - 10, "posts at steps 1, 3 and 6 (60 × 60)", "note")
    return svg(640, 300, b, "Side view of rail heights: toe board 150, middle rail 575, handrail about 1000, top rail at least 1100")


def poles_svg(t_full, t_pt):
    k = 3.0
    b = txt(10, 18, "NOW", "tag") + rect(30, 50, 25 * k, 10 * k, "old") + txt(30 + 12.5 * k, 50 + 10 * k + 22, "25 \u00d7 10", "lbl", "middle")
    x = 230
    b += txt(x, 18, "CHANGE TO", "tag")
    for tt, cls, lab in ((t_pt, "new2", "point loads only"), (t_full, "new", "full crowd push")):
        if not tt:
            continue
        b += rect(x, 40, 25 * k, tt * k, cls) + txt(x + 12.5 * k, 40 + tt * k + 20, f"25 \u00d7 {tt:g}", "lbl", "middle")
        b += txt(x + 12.5 * k, 40 + tt * k + 38, lab, "note" if cls == "new" else "note2", "middle")
        x += 200
    b += txt(610, 60, "\u2195 people push this way", "lbl")
    b += txt(610, 80, "(across the stair)", "note2")
    h = 40 + max(t_full or 10, t_pt or 10) * k + 60
    return svg(820, h, b, "Handrail pole section: 25 x 10 now, thicker across the stair after")


def rails_svg_v3():
    k = 3.0
    b = ""

    def uchan(x, y, slot, wall, depth, cls):          # open-top U: two walls + floor
        W, H = slot + 2 * wall, depth + wall
        return (rect(x, y, wall * k, H * k, cls) + rect(x + (wall + slot) * k, y, wall * k, H * k, cls)
                + rect(x, y + depth * k, W * k, wall * k, cls))

    def inv_u(x, y, w, h, t, cls):                   # upside-down U: top web + two legs
        return rect(x, y, w * k, t * k, cls) + rect(x, y, t * k, h * k, cls) + rect(x + (w - t) * k, y, t * k, h * k, cls)

    def pair(x, y, depth, rdepth, cls_l, cls_r):
        return uchan(x, y, 25, 5, depth, cls_l) + inv_u(x + 5 * k, y + (depth - rdepth) * k, 25, rdepth, 5, cls_r)

    b += txt(20, 18, "NOW (lower pair)", "tag")
    b += pair(30, 40, 20, 21, "old", "old2") + txt(30 + 17.5 * k, 40 + 25 * k + 22, "35 × 25 + 25 × 21", "lbl", "middle")
    x1 = 260
    b += txt(x1, 18, "CHANGE TO (lower pair)", "tag")
    b += pair(x1 + 10, 40, 42, 42, "new", "new2") + txt(x1 + 10 + 17.5 * k, 40 + 47 * k + 22, "35 × 47 + 25 × 42", "lbl", "middle")
    b += txt(x1 + 160, 60, "left channel: 5 mm walls, 25 slot, 42 deep", "note")
    b += txt(x1 + 160, 80, "right rail: upside-down U, 5 mm, 42 deep", "note2")
    b += txt(x1 + 160, 110, "upper pair: no change", "lbl")
    b += txt(x1 + 160, 128, "(35 × 25 with 25 × 20)", "lbl")
    b += txt(x1 + 160, 160, "both grow downwards; the right rail", "lbl")
    b += txt(x1 + 160, 178, "still drops fully into the slot", "lbl")
    return svg(760, 40 + 47 * k + 50, b, "Lower guide rail pair: left U channel 35 x 47 with the right upside-down U 25 x 42 nested inside")


def poles_svg_v3():
    k = 2.2
    b = txt(10, 18, "NOW", "tag") + rect(30, 50, 25 * k, 10 * k, "old") + txt(30 + 12.5 * k, 50 + 10 * k + 22, "flat 25 × 10", "lbl", "middle")
    x = 200
    b += txt(x, 18, "CHANGE TO (either)", "tag")
    for d, cls, lab in ((50, "new2", "point loads only"), (70, "new", "full crowd push")):
        b += rect(x, 40, 25 * k, d * k, cls) + rect(x + 3 * k, 40 + 3 * k, 19 * k, (d - 6) * k, "void")
        b += txt(x + 12.5 * k, 40 + d * k + 20, f"25 × {d} × 3", "lbl", "middle")
        b += txt(x + 12.5 * k, 40 + d * k + 38, lab, "note" if cls == "new" else "note2", "middle")
        x += 170
    b += txt(560, 60, "↕ people push this way", "lbl")
    b += txt(560, 80, "(across the stair)", "note2")
    return svg(760, 40 + 70 * k + 60, b, "Handrail pole: flat 25 x 10 now; hollow 25 x 50 x 3 or 25 x 70 x 3 after")


def hook_svg():
    k = 2.6
    b = txt(10, 18, "NOW", "tag") + txt(260, 18, "CHANGE TO", "tag")
    for (x0, t, throat, cls) in ((40, 5, 11.9, "old"), (300, 10, 22, "new")):
        r_in = 12.6 * k
        cx, cy = x0 + 60, 110
        r_out = r_in + throat * k
        b += (f'<path class="{cls}" d="M {cx - r_out} {cy} A {r_out} {r_out} 0 0 1 {cx + r_out} {cy} L {cx + r_out} {cy + 25} '
              f'L {cx + r_in} {cy + 25} L {cx + r_in} {cy} A {r_in} {r_in} 0 0 0 {cx - r_in} {cy} L {cx - r_in} {cy - 5} L {cx - r_out} {cy - 5} Z"/>')
        b += f'<circle class="axle" cx="{cx}" cy="{cy}" r="{12.6 * k}"/>'
        b += txt(cx, cy + 60, f"{t:g} mm plate, {throat:g} mm round the hook", "lbl", "middle")
    return svg(560, 200, b, "Top hook: 5 mm plate with 11.9 mm of metal now, 10 mm plate with at least 22 mm after")


KS = json.load(open(os.path.join(HERE, "keep_shapes_check.json")))


def best(q, side, sup):
    e = KS.get(f"{q} | {side} | {sup}") or {}
    opts = e.get("options") or []
    return (opts[0] if opts else None), e.get("now", {})


def rail_txt(o):
    return f"lower {o['lower']}, upper {o['upper']}" if o else "no U size up to 220 mm deep passes"


R_MID, R_NOW_MID = best("7.5", "right", "mid")
R_END, R_NOW_END = best("7.5", "right", "ends")
L_MID, L_NOW_MID = best("7.5", "left", "mid")
L_END, L_NOW_END = best("7.5", "left", "ends")
R5_MID, _ = best("5.0", "right", "mid")
R5_END, _ = best("5.0", "right", "ends")
L5_MID, _ = best("5.0", "left", "mid")
L5_END, _ = best("5.0", "left", "ends")
P = KS.get("poles", {})
P25 = P.get("width along the stair 25 mm", {})
P40 = P.get("width along the stair 40 mm", {})
T_FULL = P25.get("3.0 kN/m crowd push + 1.5 kN post + 1.25 kN rail")
T_PT = P25.get("point loads only: 1.5 kN post + 1.25 kN rail")
T40_FULL = P40.get("3.0 kN/m crowd push + 1.5 kN post + 1.25 kN rail")
PNOW = P.get("now (25 x 10)", {})


def u(o, case):
    return f"{o['util'][case]:.2f}" if o else "—"


def worst_now(now):
    return max(now.values()) if now else float("nan")


CHANGES = [
    dict(n=1, kind="change", name="Steps (treads)", qty="6 per unit", figs="A",
         now="Flat plank 280 deep × 50 thick.",
         new="Hollow plank 285 deep × 40 thick: 1.8 mm walls, 5 ribs inside, serrated top. Add a lip turned down 35 mm along the front edge, "
             "2 mm thick, stopping 30 mm short of each end so it clears the guide rails. Length stays 1,236. A 55 mm contrasting strip on the "
             "front and back edges (colour only).",
         how=["Keep the walking surface at exactly the same height as now: the plank gets thinner from underneath, so every riser stays 175.",
              "Keep the pin holes exactly where they are.",
              "You may model it solid and label it “hollow, 1.8 mm walls, 5 ribs”."],
         why=[("R7", "Open gap between steps ≤ 120 mm (100 recommended), so a child cannot slip through. Now 125 mm; the thinner step alone "
                     "would make it 135. The lip brings it to 100."),
              ("R48", "Gap between planks on the flat catwalk ≤ 25 mm. Now 25.2; the deeper 285 plank makes it 20."),
              ("R12", "Uniform risers: why the walking surface must not move."),
              ("R17", "55 mm contrasting nosings on both edges of each step.")],
         load=("Carries the crowd (7.5 kN/m²) and one foot (4 kN on a 200 mm square) across the 1.24 m span. The lip is part of the "
               "section and stiffens the front edge.",
               "Strong but heavy: 7.67 kN point capacity, 7.09 kg each", "4 kN point at 0.83 of capacity, 4.57 kg each (−15 kg per unit)"),
         drawing="tread"),
    dict(n=2, kind="change", name="Right-hand guide rails (keep the U shape)", qty="2 per unit (upper + lower)", figs="A · B · F",
         now="Upside-down U, 25 wide × about 20 deep, 5 mm walls, open underneath.",
         new=f"Keep the upside-down U and its 25 mm width (it must still nest in the next unit). Make it deeper and thicker: "
             f"with the scaffold supporting the flat catwalk in the middle: {rail_txt(R_MID)}. "
             f"If the scaffold only supports the two ends: {rail_txt(R_END)}. The lower rail grows downwards, the upper rail upwards.",
         how=["Keep the 25 mm outside width, the hole centres and the axle position.",
              "Thicken the walls inwards (the open slot underneath gets narrower) and extend the depth as listed."],
         why=[("R113 R128", "Stairs and platforms (the catwalk) must carry 7.5 kN/m\u00b2 of crowd."), ("R115", "Deflection no more than span/250 (7.3 mm) under the crowd, under 10 mm for one person."), ("R180", "Uneven crowds: one part loaded, the rest empty.")],
         load=("These rails are the side beams: every step hangs its load on them. The right-hand side is the weaker one and governs.",
               f"At 7.5 kN/m² the rails are loaded {worst_now(R_NOW_MID):.1f}× their capacity",
               f"Stair {u(R_MID, 'standard')}, catwalk {u(R_MID, 'catwalk_mid')} (mid-supported) · catwalk on ends only {u(R_END, 'catwalk_ends')}"),
         drawing=None),
    dict(n=3, kind="change", name="Left-hand guide rails (keep the U channel)", qty="2 per unit (upper + lower)", figs="C",
         now="Open-top U channel 35 wide × 25 deep, 5 mm walls, 25 mm slot.",
         new=f"Keep the open-top U and its 25 mm slot (the next unit’s right rail drops into it). Extra thickness and depth needed: "
             f"with the scaffold supporting the flat catwalk in the middle: {rail_txt(L_MID)}. "
             f"If the scaffold only supports the two ends: {rail_txt(L_END)}. Walls thicken outwards, so the slot stays 25.",
         how=["Keep the slot centre-line and width (25 mm).", "Thicken the walls outwards and the floor downwards; deepen the slot to match the right rail."],
         why=[("R113 R115", "Same crowd load and deflection limit as change 2."),
              ("R103 R105", "Side-by-side joins must stay aligned and flush; that works because the rails nest.")],
         load=("Same side-beam job as change 2 on the other side of the unit.",
               f"At 7.5 kN/m² loaded {worst_now(L_NOW_MID):.1f}× capacity",
               f"Stair {u(L_MID, 'standard')}, catwalk {u(L_MID, 'catwalk_mid')} (mid-supported) · ends only {u(L_END, 'catwalk_ends')}"),
         drawing="rails"),
    dict(n=4, kind="change", name="Handrail poles: thicker, same layout", qty="12 per unit (unchanged)", figs="A · B",
         now="12 flat poles 25 × 10, one at every step on each side; the bottom of each pole is its lock pin.",
         new=(f"Keep all 12 poles and their positions; the pin stays part of the pole. For the full crowd push (3.0 kN/m) each pole needs to be "
              f"25 × {T_FULL:g} (thickness across the stair)" if T_FULL else "Thicker poles") +
             (f", or 40 × {T40_FULL:g}" if T40_FULL else "") +
             (f". For the point loads only (1.5 kN on a post, 1.25 kN on the rail): 25 × {T_PT:g}." if T_PT else ".") +
             " Thicken outwards, away from the steps.",
         how=["Thicken each pole across the stair (the direction people push); keep 25 along the stair unless noted.",
              "The pin at the bottom of the pole passes through both guide rails: its thickness sets the hole size in the rails (see the note below)."],
         why=[("R142", "The top rail must hold a crowd pushing 3.0 kN per metre (circulation routes)."), ("R179", "Each post must hold 1.5 kN at the top."),
              ("R143", "1.25 kN on the top rail between posts.")],
         load=("Every sideways push on the rails ends up bending the poles where they enter the guide rails. A 10 mm flat bends the weak way.",
               f"Crowd push {PNOW.get('line', float('nan')):.0f}× over, post load {PNOW.get('post', float('nan')):.1f}× over",
               "All three loads pass at the thickness above"),
         note="The pin part of the pole goes through the right-hand rail, which is only 25 mm wide. Anything much over 15 mm thick leaves no rail "
              "material either side of the hole, so the pin section (where the pole enters the rails) is the limit. If that section has to stay "
              "thin, the full crowd push cannot be carried by the poles alone: plan on crowd barriers from the scaffold side, or check with the engineer.",
         drawing="poles"),
    dict(n=10, kind="change", name="Top hooks", qty="2 per unit", figs="E",
         now="5 mm plate with about 12 mm of metal around the hook opening.",
         new="10 mm plate with at least 22 mm of metal around the opening. The opening itself stays the same size (fits the axle).",
         how=["Thicken the hook plate to 10 mm and grow the outline outwards; don’t change the opening."],
         why=[("R113 R170", "The hook carries the whole top end of the stair when it hangs from a bar or the next unit.")],
         load=("Half of the stair’s load goes through the two top hooks.", "1.36 kN capacity vs 4.1 kN needed (3× short)",
               "Sized for the full top reaction, about 0.9 of capacity"),
         drawing="hook"),
    dict(n=7, kind="consider", name="Handrail (to consider)", qty="2 per unit", figs="A",
         now="25 × 25 solid square bar, ending about 80 mm past the end steps.",
         new="Round tube Ø48.3 × 3 mm with closed ends; on the standard (35°) stair set run it 300 mm past the top and bottom steps. "
             "In the double stair the two units’ handrails join into one: plug-in 300 mm ends and a joiner at the unit joint.",
         how=["Only if you decide to adopt it: replace the profile, keep its height, add the extensions."],
         why=[("R64", "Grip size 25\u201350 mm (40 target)."), ("R19 R71", "300 mm past both ends, closed ends."),
              ("R72", "Continuous over the whole flight, including across the double-stair joint.")],
         load=("The 300 mm extension sticks out past the last post like a diving board; a 1.25 kN hand load on its tip sets the tube size.",
               "Square bar, too short", "1.25 kN on the tip at 0.94 of capacity"),
         drawing=None),
]

BN = json.load(open(os.path.join(HERE, "brief_numbers.json")))
_L = BN["left U35x47 (slot 42) / U35x25"]
_R = BN["right 25x42 / 25x20"]
CH = {c["n"]: c for c in CHANGES}
CH[2].update(
    new="Keep the upside-down U, 25 wide, 5 mm walls. Lower rail: 42 deep (now about 21); the extra depth goes downwards. "
        "Upper rail: no change (25 × 20). With 6 mm walls the lower rail can be 39 deep instead. These sizes assume the scaffold supports "
        "the flat catwalk under its middle; with support at the two ends only, the lower rail would need to be 109 deep.",
    load=("These rails are the side beams: every step hangs its load on them. The right-hand side is the weaker one and governs.",
          "At 7.5 kN/m² loaded 3.7× over capacity on the stair",
          f"Stair {_R['standard']:.2f}, flat catwalk {_R['catwalk_mid']:.2f}; deflection {_R['standard_parts']['defl_L250']:.2f} of the limit"))
CH[3].update(
    new="Keep the open-top U, 35 wide, 5 mm walls, 25 mm slot. Lower channel: 47 deep overall with a 42 deep slot, so the new 42 deep right rail "
        "of the next unit still drops fully in (the load alone needs 40). Upper channel: no change (35 × 25). With support at the two "
        "ends only it would need to be 114 deep.",
    load=("Same side-beam job as change 2 on the other side of the unit.", "At 7.5 kN/m² loaded 2.5× over capacity",
          f"Stair {_L['standard']:.2f}, flat catwalk {_L['catwalk_mid']:.2f}"))
CH[4].update(
    new="Keep all 12 poles and their positions; the pin stays part of the pole. To carry the sheet’s barrier loads each pole must be much stiffer "
        "across the stair: hollow 25 × 70 × 3 mm for the full crowd push (3.0 kN/m), or 25 × 50 × 3 mm for the point loads only "
        "(1.5 kN on a post, 1.25 kN on the rail). Solid alternatives: 25 × 46 and 25 × 32, about twice the weight.",
    load=("Every sideways push on the rails ends up bending the poles, most of all where they enter the guide rails.",
          "Crowd push 20× over, post load 6.6× over",
          f"25×70×3: full crowd push at {BN['pole RHS 25x70x3']['full']:.2f} · 25×50×3: point loads at {BN['pole RHS 25x50x3']['points']:.2f}"),
    note="The catch: the bending is largest exactly where the pole enters the guide rails, and that part is the pin, which has to fit through "
         "the 25 mm-wide rails. A 25 × 10 pin carries only 0.095 kNm, about 1/16 of what the crowd push needs and 1/10 of the point loads. "
         "A pole is only as strong as its pin, so thickening the pole above the rails alone won’t pass. Either the rails get a socket that grips "
         "a full-size pole, or the handrail is treated as a handrail only and the crowd barrier comes from the scaffold side.")

NOTES = [  # decided: not part of the drawing work, with what it means against the sheet
    (5, "Lock pins", "No change: the pin is the bottom of each handrail pole, one piece (see change 4).", "R78 R104: the pole-pins lock the steps; a latch so a handrail can\u2019t lift out by accident is still to design."),
    (6, "Top rail (guardrail)", "No change to the rail. We will add circular padding on top of it; this is noted only, not part of this brief.", "R63 height 1,127 unchanged."),
    (8, "Middle / child rail", "Not fitted (your decision).", "R65/R68 (no gap over 470 mm; mesh \u2264 100 mm for the public) and R70 (child rail ~600) are then not met by the unit: the scaffold\u2019s edge protection or \u2264 100 mm mesh must cover the side."),
    (9, "Toe board", "Not fitted (your decision).", "R66 (150 mm toe board) not met by the unit; cover it on site if the edge is open."),
    (11, "Feet", "Not fitted: the scaffold supports the unit.", "R73 footplates move to the scaffold. Where the flat catwalk is used, a scaffold support under its middle keeps the rail sizes in changes 2 and 3 small."),
    (12, "Centre handrail between side-by-side units", "Not needed (your decision).", "R109 prefers a centre rail (and assist elements) on stairs over 28\u00b0 and 1.8 m wide, which a side-by-side pair is: accept through the venue risk assessment."),
    (13, "ID and rating plate", "Later, after the design is final.", "R93."),
]
DRAW = {"tread": tread_svg, "rails": rails_svg_v3, "post": post_svg, "round": rails_round_svg, "heights": heights_svg, "hook": hook_svg,
        "poles": poles_svg_v3}

TABLE = [(1, "Steps", "280 × 50 plank", "285 × 40 hollow + 35 lip", "change"),
         (2, "Right rails", "U 25 × ~21 / 25 × 20, 5 mm", "lower U 25 × 42; upper no change", "change"),
         (3, "Left rails", "U 35 × 25 / 35 × 25, 5 mm", "lower U 35 × 47 (slot 42); upper no change", "change"),
         (4, "Handrail poles", "12 flats 25 × 10", "12 hollow 25 × 70 × 3 (see pin note)", "change"),
         (10, "Top hooks", "5 mm plate", "10 mm plate, 22 round opening", "change"),
         (7, "Handrail", "25 × 25 solid", "×48.3 × 3, +300 ends, joiner", "consider"),
         (5, "Lock pins", "bottom of the pole", "no change", "no"),
         (6, "Top rail", "25 × 25 hollow", "no change (padding added by us)", "no"),
         (8, "Middle rail", "—", "not fitted", "no"), (9, "Toe board", "—", "not fitted", "no"),
         (11, "Feet", "4 small feet", "scaffold supports the unit", "no"), (12, "Centre handrail", "—", "not needed", "no"),
         (13, "ID plate", "—", "after finalisation", "later")]

COMPLY = [
    ("R3", "Clear width 1,100 (industry anchor)", "1,023 between handrails, unchanged: confirm by crowd-flow calculation", "open"),
    ("R4 R5", "Going \u2265 250 with riser \u2264 175", "Unchanged 250 / 175 on the standard stair (at the limit)", "pass"),
    ("R6", "Closed risers preferred", "Lip part-closes each riser (#1); preferred, not required", "part"),
    ("R7", "Open gap between steps \u2264 120 (100 rec)", "100 mm with the 35 mm lip (#1)", "pass"),
    ("R8", "2 \u00d7 rise + going 540\u2013660 (guidance only)", "600", "pass"),
    ("R9", "Pitch \u2264 35\u00b0", "Standard 35\u00b0; steep 49.4\u00b0 is crew-only", "part"),
    ("R10 R13 R14 R15", "Landings sized by the flow calculation, \u2265 gangway width", "Where flights join or the catwalk is used as a landing: set on the site layout", "site"),
    ("R11", "Headroom \u2265 2,100", "Site layout", "site"),
    ("R12", "Uniform risers, also with connecting stairs", "Walking surface kept at the same height (#1); check the step at the end-to-end joint", "part"),
    ("R16 R94", "Slip PTV \u2265 36 (40 events)", "Serrated top; pendulum test on the finished step", "test"),
    ("R17", "55 mm contrasting nosings, both edges", "#1", "pass"),
    ("R18 R109", "Centre rail preferred over 28\u00b0 and 1,800 wide", "Not fitted by decision (#12): accept through the venue risk assessment", "part"),
    ("R19 R64 R71 R72", "Handrail: grip 25\u201350, 300 past ends, closed, continuous", "Change 7 is still to be decided", "open"),
    ("R48", "Deck gap \u2264 25", "20 mm (#1)", "pass"),
    ("R63 R69", "Top rail \u2265 1,100, both sides, full length", "1,127 both sides, unchanged; circular padding added on top", "pass"),
    ("R65 R68", "No gap in the side over 470 (\u2264 100 mesh for the public)", "About 1,000 mm below the handrail without a middle rail (#8); the scaffold edge protection or \u2264 100 mm mesh must cover it", "site"),
    ("R66", "Toe board 150", "Not fitted (#9): cover on site where the edge is open", "site"),
    ("R67", "Handrail clear of objects \u2265 50", "About 95 mm off the poles, unchanged", "pass"),
    ("R70", "Child rail about 600", "Not fitted (#8): site / scaffold", "site"),
    ("R73 R74\u2013R77", "Footplates, base jacks, plumb 1:100, bracing, bearing", "Scaffold scope (#11); the engineer gives the unit\u2019s support reactions", "site"),
    ("R78 R104", "Positive, captive locking, no unintended release", "Pins are the pole ends (#5); a latch so a handrail can\u2019t lift out is still to design", "open"),
    ("R90", "Effective going: going + 15 mm nosing", "285 step on a 250 going: 35 mm overlap", "pass"),
    ("R93", "ID and rating plate", "After finalisation (#13)", "open"),
    ("R95", "No finger traps in moving joints", "The 20 mm gap between steps closes while folding: procedure, or 298-deep steps", "open"),
    ("R96", "Instruction manual and method statement", "To write with the final design", "open"),
    ("R103 R108", "Module joins: gap \u2264 25, level within 4", "Nested join 5 mm, same level; double join 19 mm", "pass"),
    ("R106", "Post spacing (1.2 m for class C)", "305 mm: a pole at every step", "pass"),
    ("R113 R128 R115 R180", "Crowd 7.5 kN/m\u00b2 (stairs and platforms), span/250, < 10 mm under one person, pattern loads", "Checked for #1\u2013#3 with load patterns; holds if those changes are adopted and the flat catwalk has a middle support", "cond"),
    ("R114", "4 kN on one step", "0.83 (#1)", "pass"),
    ("R116 R176", "Sideways crowd load and 10 % sway on the whole stair", "Into the hooks and the scaffold: engineer to check", "open"),
    ("R142 R179 R143", "Barrier 3.0 kN/m, post 1.5 kN, rail point 1.25 kN", "Only with the pole thickness in #4 and a pin section that carries it", "part"),
    ("R142", "Barrier 5.0 kN/m where people gather to watch", "Not covered", "open"),
    ("R150 R170", "Connections: crowd uplift and tie-down", "Top hooks 10 mm (#10); hooks resting on the axle need a keeper against lifting; pole-pin holes in the 25 mm rail to check", "part"),
    ("R153 R169", "Partial factors 1.35 G + 1.5 Q", "All utilisations in this brief are factored this way", "pass"),
    ("R163", "Aluminium EN AW-6082-T6", "All parts", "pass"),
    ("R165 R166", "Independent design check; load test 1.2\u00d7", "For the final design", "test"),
    ("R173 R98", "Edge protection class", "Class C for the 35\u00b0 stair, class A for the flat catwalk; the 49.4\u00b0 steep setting is outside EN 13374 (crew only)", "test"),
    ("R177", "f\u2081 \u2265 6 Hz vertical, \u2265 1.5 Hz sway", "Stiffer rails raise f\u2081; confirm both on the scaffold", "open"),
    ("R178", "1.0 kN/m downwards on the top rail", "Top rail unchanged, 305 mm between poles: passes easily; matters more because the padding invites sitting", "pass"),
    ("R181", "Storm overturning (no people)", "Site wind check with the scaffold ties", "site"),
]

cards = []
for c in CHANGES:
    why = "".join(f'<li><span class="ref">{E(r)}</span>{E(t)}</li>' for r, t in c["why"])
    le, before, after = c["load"]
    drawing = DRAW[c["drawing"]]() if c["drawing"] else ""
    tag = '<span class="tagc">to consider</span>' if c["kind"] == "consider" else ""
    note = f'<p class="cnote">{E(c["note"])}</p>' if c.get("note") else ""
    cards.append(f"""
    <article class="card{' consider' if c['kind'] == 'consider' else ''}" id="c{c['n']}">
      <header><span class="num">{c['n']}</span><div><h3>{E(c['name'])} {tag}</h3><p class="meta">{E(c['qty'])} · see Fig {E(c['figs'])}</p></div></header>
      <div class="nowto">
        <div class="now"><span>Now</span><p>{E(c['now'])}</p></div>
        <div class="to"><span>Change to</span><p>{E(c['new'])}</p></div>
      </div>
      <div class="refs">
        <figure><img src="img/chg/c{c['n']}_where.jpg" alt="{E(c['name'])}: where on the unit" width="1000" height="625" loading="lazy"><figcaption>Where on the unit</figcaption></figure>
        <figure><img src="img/chg/c{c['n']}_close.jpg" alt="{E(c['name'])}: close-up" width="1000" height="625" loading="lazy"><figcaption>Close-up</figcaption></figure>
      </div>
      <div class="how"><span>In SketchUp</span><ul>{''.join(f'<li>{E(s)}</li>' for s in c['how'])}</ul></div>
      {note}
      {f'<div class="draw">{drawing}</div>' if drawing else ''}
      <div class="whyload">
        <div class="why"><span>Why (code sheet)</span><ul>{why}</ul></div>
        <div class="load"><span>Load effect</span><p>{E(le)}</p>
          <div class="ba"><div><i>Now</i>{E(before)}</div><div><i>After</i>{E(after)}</div></div></div>
      </div>
    </article>""")
notes_html = "".join(f'<tr><td class="mono"><span id="c{n}">{n}</span></td><th scope="row">{E(p)}</th><td>{E(d)}</td><td>{E(cm)}</td></tr>'
                     for n, p, d, cm in NOTES)

ST2 = {"change": ("pass", "Change"), "consider": ("part", "To consider"), "no": ("none", "No change"), "later": ("test", "Later")}
rows = "".join(f'<tr><td class="mono"><a href="#c{n}">{n}</a></td><th scope="row">{E(p)}</th><td>{E(a)}</td><td class="strong">{E(b)}</td>'
               f'<td><span class="st {ST2[q][0]}">{ST2[q][1]}</span></td></tr>' for n, p, a, b, q in TABLE)
figs_html = "".join(figure(*f) for f in FIGS)
W_NEW = 71.6 - 15.1 + 1.65 + 9.2 + 0.3        # treads, rails (#2 #3), hollow poles 25x70x3 (#4), hooks
ST_LBL = {"pass": "Pass", "part": "Partly", "test": "Test", "open": "Open", "site": "Site / scaffold", "cond": "If adopted"}
comply_rows = "".join(f'<tr><td class="mono">{E(r)}</td><td>{E(q)}</td><td>{E(h)}</td><td><span class="st {k}">{ST_LBL[k]}</span></td></tr>' for r, q, h, k in COMPLY)

page = f"""<title>Stair Unit Change Brief</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root {{
  --paper:#EFF2F2; --surface:#FFFFFF; --ink:#15202A; --ink2:#4B5966; --rule:#D3DADE; --soft:#E6EBED;
  --accent:#1E5A86; --accentbg:#E1ECF4; --new:#C2410C; --newbg:#FDEBDD; --old:#8A96A0;
  --pass:#2F7A4F; --passbg:#E2F1E7; --warn:#9A620E; --warnbg:#FBEFD8; --fail:#B42318; --failbg:#FBE3E0;
  --display:"Barlow Semi Condensed","Arial Narrow",system-ui,sans-serif;
  --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"Cascadia Mono",Consolas,monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --paper:#0E151B; --surface:#152029; --ink:#E3E9ED; --ink2:#9DACB8; --rule:#27353F; --soft:#1B2833;
    --accent:#7DB7E3; --accentbg:#16283A; --new:#FB923C; --newbg:#3A2112; --old:#6B7985;
    --pass:#6CC790; --passbg:#17301F; --warn:#E6B45A; --warnbg:#382B12; --fail:#FF8C80; --failbg:#3A1B18; color-scheme:dark;
  }}
}}
:root[data-theme="dark"] {{
  --paper:#0E151B; --surface:#152029; --ink:#E3E9ED; --ink2:#9DACB8; --rule:#27353F; --soft:#1B2833;
  --accent:#7DB7E3; --accentbg:#16283A; --new:#FB923C; --newbg:#3A2112; --old:#6B7985;
    --pass:#6CC790; --passbg:#17301F; --warn:#E6B45A; --warnbg:#382B12; --fail:#FF8C80; --failbg:#3A1B18; color-scheme:dark;
}}
* {{ box-sizing:border-box; }}
body {{ background:var(--paper); color:var(--ink); font:15.5px/1.6 var(--body); margin:0; padding-inline:16px; padding-block:28px 64px; }}
.wrap {{ max-width:1120px; margin:0 auto; display:grid; gap:34px; }}
h1,h2,h3 {{ font-family:var(--display); text-wrap:balance; margin:0; letter-spacing:.01em; }}
h1 {{ font-size:clamp(34px,5vw,52px); line-height:1.02; }}
h2 {{ font-size:27px; font-weight:600; }}
h3 {{ font-size:21px; font-weight:600; line-height:1.15; }}
p {{ margin:0; max-width:72ch; }}
a {{ color:var(--accent); }}
a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.mono {{ font-family:var(--mono); font-variant-numeric:tabular-nums; }}
.eyebrow {{ font:600 12px/1 var(--mono); letter-spacing:.12em; text-transform:uppercase; color:var(--accent); }}
header.top {{ display:grid; gap:12px; }}
header.top p {{ color:var(--ink2); font-size:16.5px; }}
.result {{ display:flex; flex-wrap:wrap; gap:0; border:1px solid var(--rule); background:var(--surface); }}
.result div {{ flex:1 1 180px; padding:12px 16px; border-right:1px solid var(--rule); display:grid; gap:2px; }}
.result div:last-child {{ border-right:0; }}
.result span {{ font-size:12.5px; color:var(--ink2); }}
.result b {{ font:600 23px/1.15 var(--display); font-variant-numeric:tabular-nums; }}
.result b s {{ color:var(--ink2); font-weight:500; font-size:18px; margin-right:6px; }}
section {{ display:grid; gap:16px; }}
section > h2 {{ border-top:2px solid var(--ink); padding-top:12px; }}
.rules {{ margin:0; padding:0; list-style:none; display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:10px; counter-reset:r; }}
.rules li {{ background:var(--surface); border:1px solid var(--rule); padding:12px 14px; font-size:14.5px; }}
.rules li b {{ display:block; font-family:var(--display); font-size:17px; font-weight:600; }}
/* figures */
.figs {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,460px),1fr)); gap:16px; }}
.fig {{ margin:0; background:var(--surface); border:1px solid var(--rule); }}
.fig:first-child {{ grid-column:1 / -1; }}
.shot {{ position:relative; }}
.shot img {{ width:100%; height:auto; display:block; }}
.mk {{ position:absolute; transform:translate(-50%,-50%); width:28px; height:28px; border-radius:50%; background:var(--accent); color:#fff;
      font:600 13px/28px var(--mono); text-align:center; text-decoration:none; box-shadow:0 0 0 3px rgba(255,255,255,.85); }}
.mk.new {{ background:var(--new); }}
.mk:hover, .mk:focus-visible {{ transform:translate(-50%,-50%) scale(1.15); outline:none; }}
.fig figcaption {{ padding:9px 12px; font-size:13.5px; color:var(--ink2); border-top:1px solid var(--rule); }}
.fig figcaption b {{ color:var(--ink); font-family:var(--mono); font-weight:500; margin-right:6px; }}
.key {{ display:flex; flex-wrap:wrap; gap:14px; font-size:13px; color:var(--ink2); align-items:center; }}
.key i {{ display:inline-block; width:14px; height:14px; border-radius:50%; vertical-align:-2px; margin-right:6px; }}
/* summary table */
.tw {{ overflow-x:auto; border:1px solid var(--rule); background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
th, td {{ padding:8px 12px; border-bottom:1px solid var(--rule); text-align:left; vertical-align:top; }}
thead th {{ font:600 11.5px/1.2 var(--mono); letter-spacing:.06em; text-transform:uppercase; color:var(--ink2); background:var(--soft); }}
tbody tr:last-child > * {{ border-bottom:0; }}
tbody th {{ font-weight:500; }}
td.strong {{ font-weight:600; }}
/* change cards */
.cards {{ display:grid; gap:14px; }}
.card {{ background:var(--surface); border:1px solid var(--rule); padding:16px 18px; display:grid; gap:12px; scroll-margin-top:16px; }}
.card:target {{ box-shadow:0 0 0 2px var(--accent); }}
.card header {{ display:flex; gap:12px; align-items:center; }}
.num {{ flex:none; width:36px; height:36px; border-radius:50%; background:var(--accent); color:#fff; font:600 16px/36px var(--mono); text-align:center; }}
.meta {{ color:var(--ink2); font-size:13px; }}
.nowto {{ display:grid; grid-template-columns:1fr 1.5fr; gap:10px; }}
.nowto > div {{ padding:10px 12px; display:grid; gap:4px; min-width:0; }}
.now {{ background:var(--soft); }}
.to {{ background:var(--newbg); }}
.nowto span, .how > span {{ font:600 11px/1 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--ink2); }}
.to span {{ color:var(--new); }}
.how ul {{ margin:6px 0 0; padding-left:20px; display:grid; gap:3px; }}
.refs {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; }}
.refs figure {{ margin:0; border:1px solid var(--rule); background:var(--paper); }}
.refs img {{ width:100%; height:auto; display:block; }}
.refs figcaption {{ font:500 12px/1 var(--mono); color:var(--ink2); padding:7px 9px; letter-spacing:.04em; }}
@media (max-width: 640px) {{ .refs {{ grid-template-columns:1fr; }} }}
.tagc {{ font:600 11px/1 var(--mono); letter-spacing:.06em; text-transform:uppercase; color:var(--warn); background:var(--warnbg); padding:4px 7px; vertical-align:middle; margin-left:6px; }}
.card.consider {{ border-style:dashed; }}
.cnote {{ background:var(--warnbg); padding:10px 12px; font-size:14px; max-width:none; }}
.st.none, .st.site {{ color:var(--ink2); background:var(--soft); }}
.st.cond {{ color:var(--accent); background:var(--accentbg); }}
.whyload {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.whyload > div {{ border:1px solid var(--rule); padding:10px 12px; display:grid; gap:6px; align-content:start; min-width:0; }}
.whyload > div > span {{ font:600 11px/1 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--ink2); }}
.why ul {{ margin:0; padding:0; list-style:none; display:grid; gap:6px; font-size:14px; }}
.ref {{ display:inline-block; font:600 11.5px/1.4 var(--mono); color:var(--accent); background:var(--accentbg); padding:0 5px; margin-right:6px; }}
.load p {{ font-size:14px; }}
.ba {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:13px; }}
.ba div {{ padding:6px 8px; background:var(--soft); }}
.ba div:last-child {{ background:var(--passbg); }}
.ba i {{ display:block; font:600 10.5px/1.3 var(--mono); letter-spacing:.08em; text-transform:uppercase; font-style:normal; color:var(--ink2); }}
.st {{ display:inline-block; font:600 11px/1 var(--mono); letter-spacing:.05em; text-transform:uppercase; padding:4px 7px; white-space:nowrap; }}
.st.pass {{ color:var(--pass); background:var(--passbg); }} .st.part, .st.test {{ color:var(--warn); background:var(--warnbg); }} .st.open {{ color:var(--fail); background:var(--failbg); }}
@media (max-width: 760px) {{ .whyload {{ grid-template-columns:1fr; }} }}
.draw {{ overflow-x:auto; border:1px solid var(--rule); background:var(--paper); padding:8px; }}
.sec {{ display:block; width:100%; min-width:520px; height:auto; max-height:320px; }}
.sec .old {{ fill:none; stroke:var(--old); stroke-width:2; stroke-dasharray:5 4; }}
.sec .old2 {{ fill:var(--soft); stroke:var(--old); stroke-width:1.5; }}
.sec .new {{ fill:var(--new); stroke:var(--new); stroke-width:1; }}
.sec .new2 {{ fill:var(--accent); stroke:var(--accent); stroke-width:1; }}
.sec .newf {{ fill:var(--newbg); stroke:var(--new); stroke-width:1.5; }}
.sec .void {{ fill:var(--paper); stroke:none; }}
.sec .rib {{ stroke:var(--new); stroke-width:1.5; }}
.sec .dim {{ stroke:var(--ink2); stroke-width:1.2; }}
.sec .axle {{ fill:none; stroke:var(--ink2); stroke-width:1.5; stroke-dasharray:3 3; }}
.sec .grd {{ stroke:var(--ink); stroke-width:2; }}
.sec .newl {{ stroke:var(--new); stroke-width:4; }}
.sec .old2l {{ stroke:var(--old); stroke-width:4; }}
.sec .postl {{ stroke:var(--ink2); stroke-width:6; }}
.sec text {{ fill:var(--ink); font-family:var(--mono); font-size:13px; }}
.sec .tag {{ fill:var(--ink2); font-size:12px; letter-spacing:.08em; }}
.sec .note {{ fill:var(--new); font-size:12.5px; }}
.sec .note2 {{ fill:var(--accent); font-size:12.5px; }}
.notmodel {{ margin:0; padding-left:20px; display:grid; gap:8px; color:var(--ink2); max-width:80ch; }}
.notmodel b {{ color:var(--ink); }}
footer {{ color:var(--ink2); font-size:12.5px; border-top:1px solid var(--rule); padding-top:12px; display:grid; gap:4px; }}
@media (max-width: 700px) {{ .nowto {{ grid-template-columns:1fr; }} }}
@media (prefers-reduced-motion: reduce) {{ .mk:hover {{ transform:translate(-50%,-50%); }} }}
</style>

<main class="wrap">
  <header class="top">
    <div class="eyebrow">SketchUp change brief · folding stair unit</div>
    <h1>Stair unit change brief</h1>
    <p>The geometry changes that make the current model meet the event load sheet, updated with your decisions: five changes to draw
       (1, 2, 3, 4, 10), one to consider (7), and the rest decided as no change. Nothing folds or moves differently: the unit keeps its length,
       width, fold positions, rail shapes and every pin and axle hole. Everything stays aluminium. Sizes come from the load test; the numbers
       on the pictures match the numbered changes.</p>
    <div class="result">
      <div><span>Weight per unit</span><b><s>71.6</s>≈ {W_NEW:.0f} kg</b></div>
      <div><span>Crowd load on the stair</span><b><s>1.0</s>7.5 kN/m²</b></div>
      <div><span>Push on the top rail</span><b><s>0.16</s>3.0 kN/m</b></div>
      <div><span>Gap under each step</span><b><s>125</s>100 mm</b></div>
    </div>
  </header>

  <section>
    <h2>Before you start</h2>
    <ul class="rules">
      <li><b>Holes stay put</b>Don’t move any pin hole, axle centre or hook opening. The folding depends on them.</li>
      <li><b>Same overall unit</b>Length, width, fold angles (flat, 35°, 49.4°) and the gap between units stay as they are.</li>
      <li><b>Left rails stay open</b>The left-hand rails must remain open-top channels: a second unit’s right-hand rails slide into them.</li>
      <li><b>Three handrail sets</b>Apply changes 4–9 to the catwalk, standard and steep handrail sets. The 300 mm handrail extension is only for the standard stair.</li>
    </ul>
  </section>

  <section>
    <h2>Where the changes are</h2>
    <div class="key"><span><i style="background:var(--accent)"></i>change to an existing part</span><span><i style="background:var(--new)"></i>new part: shows where it goes</span><span>Click a number to jump to its change. In each change’s own pictures, <b style="color:#E8590C">orange</b> = change or new part, <b style="color:#D11A1A">red</b> = remove.</span></div>
    <div class="figs">{figs_html}</div>
  </section>

  <section>
    <h2>All changes at a glance</h2>
    <div class="tw"><table>
      <thead><tr><th>#</th><th>Part</th><th>Now</th><th>Change to</th><th>Status</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </section>

  <section>
    <h2>The changes</h2>
    <div class="cards">{''.join(cards)}</div>
  </section>

  <section id="decided">
    <h2>Decided: no drawing work</h2>
    <p>Your decisions on the other items, and what each one means against the sheet.</p>
    <div class="tw"><table>
      <thead><tr><th>#</th><th>Item</th><th>Decision</th><th>Against the sheet</th></tr></thead>
      <tbody>{notes_html}</tbody>
    </table></div>
  </section>

  <section id="compliance">
    <h2>Checked against the code compliance sheet</h2>
    <p>Every row of the Aug-2026 events sheet that applies to this unit, and how the changes above meet it. Row numbers match the sheet.</p>
    <div class="tw"><table>
      <thead><tr><th>Row</th><th>Requirement</th><th>How it is met</th><th>Status</th></tr></thead>
      <tbody>{comply_rows}</tbody>
    </table></div>
  </section>

  <section>
    <h2>Decisions and checks outside the model</h2>
    <ul class="notmodel">
      <li><b>Finger trap while folding (R95).</b> The 20 mm gap between steps closes as the unit folds. Either fold only when nobody is on it, by trained crew (a written procedure), or make the steps 298 deep so the gap is 7 mm (+1.3 kg per unit).</li>
      <li><b>Scaffold support.</b> If the scaffold can support the flat catwalk under its middle, the rails in changes 2 and 3 stay much smaller than if it supports the ends only.</li>
      <li><b>Pole pins.</b> The pin section where each pole enters the rails is the weak point for the crowd push (see change 4); confirm the detail with the engineer, or give the edge its crowd barrier from the scaffold side.</li>
      <li><b>Viewing platforms (R142).</b> The barrier sizes are for 3.0 kN/m (people walking through). A catwalk where people stand and watch against the rail needs 5.0 kN/m.</li>
      <li><b>Engineer to check:</b> sideways crowd load and 10 % sway into the hooks and the scaffold (R116, R176); storm overturning with the scaffold ties (R181).</li>
      <li><b>Tests:</b> slip resistance of the step surface (R16), and a physical load test at 1.2\u00d7 including class C edge protection at 35\u00b0 (R166, R173).</li>
      <li><b>Steep 49.4\u00b0</b> is for crew only (step-ladder use), not the public (R9).</li>
    </ul>
  </section>

  <footer>
    <span>Sizes: the verified lightweight all-aluminium specification in the <a href="{REPORT}">load verdict report</a>, with the left rails kept as open 4 mm channels so side-by-side units still nest (checked: {LC['standard']['stress']:.2f} of capacity).</span>
    <span>Current design and ratings: <a href="{DATASHEET}">as-is datasheet</a>. Pictures: RIGGED3.blend, current geometry.</span>
  </footer>
</main>
"""
open(os.path.join(HERE, "web", "index.html"), "w", encoding="utf-8").write(page)
print("brief written", len(page))
