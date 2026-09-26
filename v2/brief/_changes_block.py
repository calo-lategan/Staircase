CHANGES = [
    dict(n=1, name="Steps (treads)", qty="6 per unit", figs="A",
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
    dict(n=2, name="Right-hand guide rails", qty="2 per unit (upper + lower)", figs="A · B · F",
         now="Small 25 mm wide rails about 20 mm deep (open underneath).",
         new="Lower rail: box tube 25 wide × 45 deep, 3 mm wall; keep its top edge where it is and extend it downwards. "
             "Upper rail: box tube 25 × 25, 2.5 mm wall; keep its bottom edge and extend it up 5 mm.",
         how=["Swap each right-hand rail for the box tube, same length and angle.", "Keep every hole centre and the axle position unchanged."],
         why=[("R113", "Stairs and platforms must carry 7.5 kN/m² of crowd."), ("R115", "Deflection no more than span/250 (7.3 mm) under the crowd.")],
         load=("These rails are the side beams: every step hangs its load on them, and they carry it to the axles, hooks and feet. "
               "The weaker right-hand side governs.",
               "Standard stair holds 1.0 kN/m² (7.5× short); catwalk 0.55", "7.5 kN/m² at 0.81 of strength, 0.49 of the deflection limit"),
         drawing=None),
    dict(n=3, name="Left-hand guide rails (channels)", qty="2 per unit (upper + lower)", figs="C",
         now="Open-top channels 35 wide × 25 deep, 5 mm walls, 25 mm slot.",
         new="Keep them as open-top channels with the 25 mm slot, but 4 mm walls: lower 33 × 49 (slot 45 deep), upper 33 × 29 (slot 25 deep). "
             "The new right-hand rail of a second unit must slide into the slot with its bottom on the channel floor.",
         how=["Keep the slot centre-line where it is now.", "Deepen the lower channel downwards and the upper one upwards, matching the right-hand rails.",
              "Do NOT close the channel into a box: the neighbouring unit nests inside it."],
         why=[("R113 R115", "Same crowd load and deflection limit as change 2."),
              ("R103 R105", "Side-by-side joins must stay aligned and flush; that works because the rails nest.")],
         load=("Same side-beam job as change 2 on the other side of the unit.",
               "Holds 2.0 kN/m² on the standard stair", "7.5 kN/m² at 0.83 of strength, 0.37 of the deflection limit"),
         drawing="rails"),
    dict(n=4, name="Handrail posts (outer sides)", qty="was 12, now 6 per unit", figs="A · B",
         now="12 thin flats 25 × 10, one at every step on each side.",
         new="6 square tubes 60 × 60 × 4: three per side, at steps 1, 3 and 6 counted from the bottom. Stand each one 15 mm clear OUTSIDE "
             "the guide rail, on a base socket (bracket detail by the engineer; it must hold 3.4 kNm). Same heights as now; delete the other flats.",
         how=["Delete the flats at steps 2, 4 and 5.", "Replace the flats at steps 1, 3 and 6 with 60 × 60 tubes, inner face 15 mm outside the rail.",
              "Apply to all three handrail sets: catwalk, standard and steep."],
         why=[("R142", "The top rail must hold a crowd pushing 3.0 kN per metre (circulation routes)."), ("R179", "Each post must hold 1.5 kN at the top."),
              ("R3 R67", "Clear width between handrails 1,100 mm with the handrail 50 mm off the posts: moving the posts out gives 1,103 (now 1,023).")],
         load=("Every sideways push on the rails ends up bending the posts at their base. The thin flats bend the weak way.",
               "Rails hold 0.16 kN/m (19× short); a post 0.24 kN (6× short)", "3.0 kN/m at 0.93; 1.5 kN post load passes"),
         drawing="post"),
    dict(n=5, name="Lock pins at the removed posts", qty="6 per unit", figs="B",
         now="The bottom end of each flat post is the lock pin.",
         new="At steps 2, 4 and 5 (no post any more) add a separate Ø12 aluminium pin through both guide rails, on a short lanyard so it "
             "can’t get lost. At steps 1, 3 and 6 the post socket carries the pin.",
         how=["Model a ×12 pin through the same hole the old post pin used, plus a small ring for the lanyard."],
         why=[("R104 R78", "Positive, captive locking of every fold joint.")],
         load=("Without the pins the frame folds under load (it is a mechanism); locked, each side works as a stiff beam. Each pin takes the "
               "locking shear.", "Loose pins can be lost", "8.7 kN locking shear at 0.59 of pin capacity"),
         drawing=None),
    dict(n=6, name="Top rail (guardrail)", qty="2 per unit", figs="A",
         now="25 × 25 square hollow bar.",
         new="Round tube Ø40 × 2 mm. Height unchanged (at least 1,100 above the step line).",
         how=["Replace the profile; keep the rail centre-line and length."],
         why=[("R63", "Top of the barrier at least 1,100 mm (unchanged)."), ("R142 R143 R178", "Crowd push 3.0 kN/m, a 1.25 kN point, and 1.0 kN/m of people leaning down on it.")],
         load=("Now spans up to 915 mm between posts instead of 305, so it bends more; the round tube is sized for that.",
               "Fine on its own, but its posts fail", "0.51 of capacity sideways, 0.31 downwards"),
         drawing="round"),
    dict(n=7, name="Handrail", qty="2 per unit", figs="A",
         now="25 × 25 solid square bar, ending about 80 mm past the end steps.",
         new="Round tube Ø48.3 × 3 mm with closed ends. On the standard (35°) stair set, run it 300 mm past the top and bottom steps. "
             "In the double stair the two units’ handrails must join into one: make the 300 mm ends plug-in pieces and add a short joiner at the unit joint.",
         how=["Replace the profile; keep its height.", "Stair set: add the 300 mm plug-in extensions.", "Model the joiner piece for the double stair."],
         why=[("R64", "Graspable round rail 25–50 mm (48.3 is in range)."), ("R19 R71", "300 mm past both ends, closed ends."),
              ("R72", "Continuous over the whole flight, so across the joint in a double stair.")],
         load=("The 300 mm extension sticks out past the last post like a diving board; a 1.25 kN hand load on its tip sets the tube size.",
               "Square bar, too short", "1.25 kN on the tip at 0.94 of capacity"),
         drawing=None),
    dict(n=8, name="New middle rail", qty="2 per unit (new)", figs="A (dashed)",
         now="Nothing between the step line and the handrail.",
         new="Round tube Ø30 × 2 mm on both sides, 575 mm above the step line, running between the end posts.",
         how=["Add it to all three handrail sets, clamped to the posts."],
         why=[("R65 R68", "No gap in the side bigger than 470 mm (now about 1,000)."), ("R70", "A lower rail near 600 mm for children.")],
         load=("Takes a 1.25 kN push between posts and shares the crowd load with the rails above.", "—", "1.25 kN push at 0.84; crowd share 0.30"),
         drawing="heights"),
    dict(n=9, name="New toe board", qty="2 per unit (new)", figs="A (dashed)",
         now="No toe board.",
         new="Board 150 high along both sides, bottom at the step line: 1.5 mm aluminium with 25 mm folded returns top and bottom.",
         how=["Model it as a long thin C shape fixed to the posts."],
         why=[("R66", "150 mm toe board for events.")],
         load=("Stops feet and objects slipping off the edge; takes a 1.25 kN kick.", "—", "1.25 kN at 0.45"),
         drawing=None),
    dict(n=10, name="Top hooks", qty="2 per unit", figs="E",
         now="5 mm plate with about 12 mm of metal around the hook opening.",
         new="10 mm plate with at least 22 mm of metal around the opening. The opening itself stays the same size (fits the axle).",
         how=["Thicken the hook plate to 10 mm and grow the outline outwards; don’t change the opening."],
         why=[("R113 R170", "The hook carries the whole top end of the stair when it hangs from a bar or the next unit.")],
         load=("Half of the stair’s load goes through the two top hooks.", "1.36 kN capacity vs 4.1 kN needed (3× short)",
               "Sized for the full top reaction, about 0.9 of capacity"),
         drawing="hook"),
    dict(n=11, name="Feet", qty="4 pads + 2 mid-feet per unit", figs="A · F",
         now="Four small corner feet, about 75 × 73.",
         new="Footplates at least 150 × 150 × 10 under the four corners. Add a foot under the middle of each lower guide rail that "
             "only touches the ground in the flat catwalk position.",
         how=["Pads: 150 × 150 plates under the existing feet (they also make room for the deeper lower rails).",
              "Mid-foot: a short leg at the middle of each lower rail, reaching the ground when flat."],
         why=[("R73", "Footplates at least 150 × 150."), ("R113", "The flat catwalk carrying 7.5 kN/m² needs a support mid-span.")],
         load=("The mid-foot halves the catwalk span; without it the catwalk would need far deeper rails.",
               "Catwalk holds 0.55 kN/m² (14× short)", "7.5 kN/m² at 0.53, deflection 0.57"),
         drawing=None),
    dict(n=12, name="Side-by-side lock and centre handrail", qty="per pair of units", figs="C · D",
         now="Each unit brings its own handrail on the inner side.",
         new="Where two units nest, captive ×12 pins at every step go through BOTH nested rails: that locks the pair. For wide stairs add a "
             "centre handrail ×48.3 × 3 held only at the top and bottom of the flight (posts at the flight ends, engineer to size). "
             "Posts can’t go between the steps there: the steps meet 5 mm apart.",
         how=["Model the pins through both nested rails.", "Model the centre handrail as its own set with an end post at the bottom and at the top."],
         why=[("R104", "Positive locking of the joined units."), ("R18 R109", "Centre handrail preferred on stairs over 28° and wider than 1.8 m.")],
         load=("Thin posts at the join can’t take the 1.25 kN hand load a handrail must carry, so the centre rail spans end to end.",
               "Slim posts hold 0.24 kN (5× short)", "1.25 kN at 0.91, 1.0 kN/m downwards at 0.77 (2.1 m span)"),
         drawing=None),
    dict(n=13, name="ID and rating plate", qty="1 per unit", figs="A",
         now="None.",
         new="A small plate (about 100 × 60) on the right-hand guide rail: unit ID, maximum load, standard, date.",
         how=["Model a thin plate with two rivets near the bottom of the right-hand lower rail."],
         why=[("R93", "Permanent ID and rating plate on every unit.")],
         load=("No load; it tells the crew what the unit is rated for.", "—", "—"),
         drawing=None),
]
DRAW = {"tread": tread_svg, "rails": rails_svg, "post": post_svg, "round": rails_round_svg, "heights": heights_svg, "hook": hook_svg}

TABLE = [(1, "Steps", "280 × 50 plank", "285 × 40 hollow + 35 lip", "6"),
         (2, "Right rails", "25 wide, ~20 deep", "box 25×45×3 / 25×25×2.5", "2"),
         (3, "Left rails", "channel 35×25, 5 mm", "channel 33×49 / 33×29, 4 mm", "2"),
         (4, "Posts", "12 flats 25×10", "6 tubes 60×60×4, 15 mm outside", "6"),
         (5, "Lock pins", "post ends", "×12 pins on lanyards", "6"),
         (6, "Top rail", "25×25 square", "×40×2 round", "2"),
         (7, "Handrail", "25×25 solid", "×48.3×3, +300 ends, joiner", "2"),
         (8, "Middle rail", "—", "×30×2 at 575", "2"),
         (9, "Toe board", "—", "150 high, 1.5 mm", "2"),
         (10, "Top hooks", "5 mm plate", "10 mm plate, 22 round opening", "2"),
         (11, "Feet", "4 small feet", "150×150 pads + 2 mid-feet", "6"),
         (12, "Side-by-side", "handrail each side", "pins through both rails + end-held centre rail", "per pair"),
         (13, "ID plate", "—", "100×60 rating plate", "1")]

COMPLY = [  # sheet row, requirement, how the brief meets it, status
    ("R3", "Clear width 1,100 (industry anchor)", "Posts 15 mm outboard, handrail 50 mm off the posts: 1,103 mm (#4)", "pass"),
    ("R4 R5", "Going ≥ 250 with riser ≤ 175", "Unchanged 250 / 175 on the standard stair (at the limit)", "pass"),
    ("R6", "Closed risers preferred", "Lip part-closes each riser (#1); preferred, not required", "part"),
    ("R7", "Open gap between steps ≤ 120 (100 rec)", "100 mm with the 35 mm lip (#1)", "pass"),
    ("R8", "2 × rise + going 540–660", "600", "pass"),
    ("R9", "Pitch ≤ 35°", "Standard 35°; steep 49.4° is crew-only", "part"),
    ("R12", "Uniform risers", "Walking surface kept at the same height (#1)", "pass"),
    ("R16 R94", "Slip PTV ≥ 36 (40 events)", "Serrated top; pendulum test on the finished step", "test"),
    ("R17", "55 mm contrasting nosings, both edges", "Strip on front and back edges (#1)", "pass"),
    ("R18 R109", "Handrails both sides; centre rail on wide stairs", "#4, #7 and the end-held centre rail (#12)", "pass"),
    ("R19 R71", "Handrail 300 past both ends, closed ends", "#7", "pass"),
    ("R48", "Deck gap ≤ 25", "20 mm (#1)", "pass"),
    ("R63", "Top rail ≥ 1,100", "1,127, unchanged", "pass"),
    ("R64", "Grip 25–50 (40 target)", "×48.3 in range; the 300 mm extension needs it", "pass"),
    ("R65 R68", "No gap in the side over 470", "Toe board 150, middle rail 575, handrail 1,000, top rail 1,127: largest gap 425", "pass"),
    ("R66", "Toe board 150", "#9", "pass"),
    ("R67", "Handrail clear of objects ≥ 50 (100 ideal)", "50 mm; 100 would cut the clear width to 1,003", "part"),
    ("R70", "Child rail about 600", "575 (#8)", "pass"),
    ("R72", "Handrail continuous over the flight", "Plug-in ends and a joiner for the double stair (#7)", "pass"),
    ("R73", "Footplates 150 × 150", "#11", "pass"),
    ("R78 R104", "Positive, captive locking", "×12 captive pins (#5, #12)", "pass"),
    ("R93", "ID and rating plate", "#13", "pass"),
    ("R95", "No finger traps in moving joints (gap > 25 or < 8)", "The 20 mm gap between steps closes while folding: see decisions below", "open"),
    ("R103 R108", "Module joins: gap ≤ 25, level within 4", "Nested join 5 mm, same level; double join 19 mm", "pass"),
    ("R106", "Post spacing ≤ 2.5 m", "915 mm maximum", "pass"),
    ("R113", "Crowd 7.5 kN/m²", "Side beams 0.81 (#2, #3), steps 0.83 (#1), catwalk 0.53 with mid-feet (#11)", "pass"),
    ("R114", "4 kN on one step", "0.83 (#1)", "pass"),
    ("R115", "Deflection ≤ span/250 and < 10 mm under one person", "0.49 of the limit; 0.5 mm under a person", "pass"),
    ("R116 R176", "Sideways crowd load on the whole stair (3.0 kN/m, 10 % sway)", "Goes into hooks and feet: engineer to check", "open"),
    ("R142", "Barrier 3.0 kN/m (circulation)", "Posts 0.93, handrail 0.94 (#4, #7)", "pass"),
    ("R142", "Barrier 5.0 kN/m where people gather to watch", "Not covered: a catwalk used as a viewing platform needs more", "open"),
    ("R143 R144 R145", "1.25 kN on top rail, middle rail, toe board", "0.51, 0.84, 0.45", "pass"),
    ("R163", "Aluminium EN AW-6082-T6", "All parts", "pass"),
    ("R166 R173", "Type test 1.2×; class C dynamic edge protection at 30–45°", "Physical test of the finished unit", "test"),
    ("R177", "Natural frequency ≥ 6 Hz", "47 Hz", "pass"),
    ("R178 R179", "Rail 1.0 kN/m downwards; post 1.5 kN", "0.31 and 0.93", "pass"),
    ("R181", "Storm overturning (no people)", "Site wind check; catwalk anchors 3.7 kN or 1.5 t ballast", "open"),
]

cards = []
for c in CHANGES:
    why = "".join(f'<li><span class="ref">{E(r)}</span>{E(t)}</li>' for r, t in c["why"])
    le, before, after = c["load"]
    drawing = DRAW[c["drawing"]]() if c["drawing"] else ""
    cards.append(f"""
    <article class="card" id="c{c['n']}">
      <header><span class="num">{c['n']}</span><div><h3>{E(c['name'])}</h3><p class="meta">{E(c['qty'])} · see Fig {E(c['figs'])}</p></div></header>
      <div class="nowto">
        <div class="now"><span>Now</span><p>{E(c['now'])}</p></div>
        <div class="to"><span>Change to</span><p>{E(c['new'])}</p></div>
      </div>
      <div class="how"><span>In SketchUp</span><ul>{''.join(f'<li>{E(s)}</li>' for s in c['how'])}</ul></div>
      {f'<div class="draw">{drawing}</div>' if drawing else ''}
      <div class="whyload">
        <div class="why"><span>Why (code sheet)</span><ul>{why}</ul></div>
        <div class="load"><span>Load effect</span><p>{E(le)}</p>
          <div class="ba"><div><i>Now</i>{E(before)}</div><div><i>After</i>{E(after)}</div></div></div>
      </div>
    </article>""")
