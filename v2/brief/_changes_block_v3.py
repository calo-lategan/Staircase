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
         why=[("R113", "Stairs and platforms must carry 7.5 kN/m² of crowd."), ("R115", "Deflection no more than span/250 (7.3 mm) under the crowd.")],
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
         why=[("R64", "Graspable rail 25–50 mm (a round profile)."), ("R19 R71", "300 mm past both ends, closed ends."),
              ("R72", "Continuous over the whole flight, including across the double-stair joint.")],
         load=("The 300 mm extension sticks out past the last post like a diving board; a 1.25 kN hand load on its tip sets the tube size.",
               "Square bar, too short", "1.25 kN on the tip at 0.94 of capacity"),
         drawing=None),
]
NOTES = [  # decided: not part of the drawing work, with what it means against the sheet
    (5, "Lock pins", "No change: the pin is the bottom of each handrail pole, one piece (see change 4).", "R78 R104 met by the pole-pins; add a latch so a handrail can’t lift out by accident."),
    (6, "Top rail (guardrail)", "No change to the rail. We will add circular padding on top of it; this is noted only, not part of this brief.", "R63 height 1,127 unchanged."),
    (8, "Middle / child rail", "Not fitted (your decision).", "R65/R68 (no gap over 470 mm) and R70 (child rail ~600) are then not met by the unit: the side needs another answer, e.g. mesh infill or the scaffold’s edge protection."),
    (9, "Toe board", "Not fitted (your decision).", "R66 (150 mm toe board) not met by the unit; cover it on site if the edge is open."),
    (11, "Feet", "Not fitted: the scaffold supports the unit.", "R73 footplates move to the scaffold. Where the flat catwalk is used, a scaffold support under its middle keeps the rail sizes in changes 2 and 3 small."),
    (12, "Centre handrail between side-by-side units", "Not needed (your decision).", "R109 only prefers a centre rail on stairs over 28° and 1.8 m wide: accept via the venue risk assessment."),
    (13, "ID and rating plate", "Later, after the design is final.", "R93."),
]
DRAW = {"tread": tread_svg, "rails": rails_svg, "post": post_svg, "round": rails_round_svg, "heights": heights_svg, "hook": hook_svg,
        "poles": lambda: poles_svg(T_FULL, T_PT)}

TABLE = [(1, "Steps", "280 × 50 plank", "285 × 40 hollow + 35 lip", "change"),
         (2, "Right rails", "U 25 × ~20, 5 mm", (f"{R_MID['lower']} / {R_MID['upper']}" if R_MID else "see card"), "change"),
         (3, "Left rails", "U 35 × 25, 5 mm", (f"{L_MID['lower']} / {L_MID['upper']}" if L_MID else "see card"), "change"),
         (4, "Handrail poles", "12 flats 25 × 10", (f"12 flats 25 × {T_FULL:g}" if T_FULL else "thicker"), "change"),
         (10, "Top hooks", "5 mm plate", "10 mm plate, 22 round opening", "change"),
         (7, "Handrail", "25 × 25 solid", "×48.3 × 3, +300 ends, joiner", "consider"),
         (5, "Lock pins", "bottom of the pole", "no change", "no"),
         (6, "Top rail", "25 × 25 hollow", "no change (padding added by us)", "no"),
         (8, "Middle rail", "—", "not fitted", "no"), (9, "Toe board", "—", "not fitted", "no"),
         (11, "Feet", "4 small feet", "scaffold supports the unit", "no"), (12, "Centre handrail", "—", "not needed", "no"),
         (13, "ID plate", "—", "after finalisation", "later")]

COMPLY = [
    ("R3", "Clear width 1,100 (industry anchor)", "1,023 between handrails, unchanged: confirm by crowd-flow calculation", "open"),
    ("R4 R5", "Going ≥ 250 with riser ≤ 175", "Unchanged 250 / 175 on the standard stair (at the limit)", "pass"),
    ("R6", "Closed risers preferred", "Lip part-closes each riser (#1); preferred, not required", "part"),
    ("R7", "Open gap between steps ≤ 120 (100 rec)", "100 mm with the 35 mm lip (#1)", "pass"),
    ("R8", "2 × rise + going 540–660", "600", "pass"),
    ("R9", "Pitch ≤ 35°", "Standard 35°; steep 49.4° is crew-only", "part"),
    ("R12", "Uniform risers", "Walking surface kept at the same height (#1)", "pass"),
    ("R16 R94", "Slip PTV ≥ 36 (40 events)", "Serrated top; pendulum test on the finished step", "test"),
    ("R17", "55 mm contrasting nosings, both edges", "#1", "pass"),
    ("R18 R109", "Centre rail on wide stairs (preferred)", "Not fitted by decision (#12): risk assessment", "part"),
    ("R19 R64 R71 R72", "Handrail: round grip, 300 past ends, closed, continuous", "Change 7 is still to be decided", "open"),
    ("R48", "Deck gap ≤ 25", "20 mm (#1)", "pass"),
    ("R63", "Top rail ≥ 1,100", "1,127, unchanged; circular padding added on top", "pass"),
    ("R65 R68", "No gap in the side over 470", "About 1,000 mm below the handrail without a middle rail (#8)", "open"),
    ("R66", "Toe board 150", "Not fitted (#9)", "open"),
    ("R67", "Handrail clear of objects ≥ 50", "About 95 mm off the poles, unchanged", "pass"),
    ("R70", "Child rail about 600", "Not fitted (#8)", "open"),
    ("R73", "Footplates 150 × 150", "Provided by the scaffold (#11)", "part"),
    ("R78 R104", "Positive locking", "Pins are the pole ends (#5); add a latch against lifting out", "part"),
    ("R93", "ID and rating plate", "After finalisation (#13)", "open"),
    ("R95", "No finger traps in moving joints", "The 20 mm gap between steps closes while folding: procedure, or 298-deep steps", "open"),
    ("R103 R108", "Module joins: gap ≤ 25, level within 4", "Nested join 5 mm, same level; double join 19 mm", "pass"),
    ("R113 R115", "Crowd 7.5 kN/m², span/250, < 10 mm under one person", "With the rail sizes in #2 and #3 and the steps in #1", "pass"),
    ("R114", "4 kN on one step", "0.83 (#1)", "pass"),
    ("R116 R176", "Sideways crowd load and 10 % sway on the whole stair", "Into the hooks and the scaffold: engineer to check", "open"),
    ("R142 R179 R143", "Barrier 3.0 kN/m, post 1.5 kN, rail point 1.25 kN", "Only with the pole thickness in #4, and the pin section where the pole enters the rails", "part"),
    ("R142", "Barrier 5.0 kN/m where people gather to watch", "Not covered", "open"),
    ("R163", "Aluminium EN AW-6082-T6", "All parts", "pass"),
    ("R166 R173", "Type test 1.2×; class C edge protection at 30–45°", "Physical test of the finished unit", "test"),
    ("R170", "Connection loads", "Top hooks 10 mm (#10)", "pass"),
    ("R177", "Natural frequency ≥ 6 Hz", "Well above (stiffer rails)", "pass"),
    ("R181", "Storm overturning (no people)", "Site wind check with the scaffold ties", "open"),
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
