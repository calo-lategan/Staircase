"""Manufacturing guide Rev C (27 Sep 2026): how to make the Rev C stair. Route 1 best strength, Route 2 lower cost.
Every utilisation is from revc/after_changes.json and revc/pole_fixing.json (same loads and formulas as the load verdict).
No prices: cost is described by what drives it (tooling, machining time, welding). Output: revc/web/manufacturing.html"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
AC = json.load(open(os.path.join(HERE, "after_changes.json")))
PF = json.load(open(os.path.join(HERE, "pole_fixing.json")))
LINKS = json.load(open(os.path.join(HERE, "links.json"))) if os.path.exists(os.path.join(HERE, "links.json")) else {}
ds, lv, cl = LINKS.get("datasheet", "#"), LINKS.get("verdict", "#"), LINKS.get("changelist", "#")
S = AC["steps"]; P = AC["poles"]; M = AC["mass_unit"]
u = lambda x: f'<span class="u{" bad" if x > 1 else ""}">{x:.2f}</span>'

# part, qty, route 1 (how, util), route 2 (how, util)
parts = [
  ("Steps (F1)", "6",
   f"One 6082-T6 extrusion, 280 × 50 box with two inner webs (3 top, 2 bottom and walls, 2 webs). No welds. Drain holes punched or CNC-cut after extruding. End plates riveted or screwed to the webs.", S["A_extruded_6082"]["util"],
   f"Same outside shape, bent from 5083-H111 sheet on a press brake: top and both walls in one piece, bottom and webs welded or riveted in. 5083 doesn’t lose strength when welded. Or buy a press-locked grating panel, 3 × 50 bars every 46 mm with an 8 mm front bar ({S['C_grating_46_nosing8']['util']:.2f}, {S['C_grating_46_nosing8']['mass']:.1f} kg).", S["A_bent_5083_welded"]["util"]),
  ("Guide rails (F2)", "4",
   "6082-T6 extruded channel, about 70 deep, 5 mm walls (left U 35 wide, right inverted U 25 wide). Holes CNC-drilled and reamed to Ø20 H9. Hooks cut from the same channel or bolted on as 10 mm plate.", AC["rails"]["lateral_right"],
   "Same 6082-T6 extruded channel from stock lengths, holes drilled on a jig. Don’t bend the rails from sheet: 5 mm 6082-T6 cracks in a tight bend, and 5083 is too weak here.", AC["rails"]["lateral_right"]),
  ("Poles (F4)", "12",
   f"Waterjet or CNC-cut from 25 mm 6082-T6 plate: 55 across at the rails, tapering to 15 at the top, with the locking tab in the same piece. Solid, so it won’t dent or hold water.", P["R1_tapered_solid_25x55"]["util"],
   f"6082-T6 rectangular tube 80 × 40 × 3 from stock, cut to length, 80 across the stair. The locking tab and pegs aren’t needed: the strap, cross-pin and lower pin do the locking.", P["R2_rhs_80x40x3"]["util"]),
  ("Pole fixing, upper rail", "12",
   "5 × 40 6082-T6 strap bent round the pole, 2 × M12 A4-70 into the rail, plus a Ø12 cross-pin along the stair through the middle of the pole.", max(PF["strap_upper"]["bolt_tension"], PF["crosspin_upper"]["double_shear"]),
   "Same strap and cross-pin; the pin bears on the tube’s two 3 mm walls.", max(PF["strap_upper"]["bolt_tension"], PF["crosspin_upper"]["bearing_rhs_2x3mm"])),
  ("Pole fixing, lower rail", "12",
   "One Ø16 6082-T6 pin across the stair through the pole and the rail.", PF["pin_lower"]["bearing_rail_5mm"],
   "Same pin.", PF["pin_lower"]["bearing_rail_5mm"]),
  ("Pole locking pegs (F3)", "48",
   "Ø12 6082-T6 or stainless pins pressed through the locking tab, 2 per rail.", AC["pegs"]["bending"],
   "Not used.", None),
  ("Step pins (F2)", "24",
   "Ø20 6082-T6 bar, turned, with castle nut and split pin; acetal bushes and washers.", AC["step_pins"]["d20"]["bending"],
   "Ø20 stainless bar cut to length, drilled for R-clips instead of turned threads.", AC["step_pins"]["d20"]["bending"]),
  ("Axles and collars (F5)", "2",
   "48.3 × 4 6082-T6 tube, one piece support to support, with bolted split collars each side of every hook.", AC["axles"]["scaffold_clamped"],
   "Standard 48.3 × 4 aluminium scaffold tube; scaffold clamps used as the collars.", AC["axles"]["scaffold_clamped"]),
  ("Hook locks (F5)", "4",
   "Ø14 keeper pin at the base, Ø12 at the top, captive on a lanyard with a spring detent.", AC["hook_locks"]["d14_single_shear"],
   "Same pins with R-clips.", AC["hook_locks"]["d14_single_shear"]),
  ("Base jacks", "2",
   "M30 jacks on 150 × 150 × 8 footplates, so the unit can stand on the ground or be clamped to a scaffold.", AC["jacks"]["m30_clamped"],
   "Standard M24 scaffold base jacks, on the ground only. Use M30 if the base is clamped to a scaffold.", AC["jacks"]["m24_ground"]),
  ("Handrail brackets (F8)", "12",
   "25 × 5 6082-T6 flat, bent on a jig.", AC["brackets"]["w25"],
   "Same.", AC["brackets"]["w25"]),
]
rows = ""
for name, q, h1, u1, h2, u2 in parts:
    rows += f'<tr><th scope="row">{name}</th><td class="mono">{q}</td><td>{h1}</td><td class="mono">{u(u1)}</td><td>{h2}</td><td class="mono">{u(u2) if u2 is not None else "—"}</td></tr>'
worst1 = max(p[3] for p in parts); worst2 = max(p[5] for p in parts if p[5] is not None)

style = open(os.path.join(HERE, "..", "brief", "web", "_brief_before_final_check.html"), encoding="utf8").read()
style = style[style.index("<style>"):style.index("</style>") + 8]
EXTRA = """<style>
.control { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); border:1px solid var(--rule); background:var(--surface); }
.control div { padding:10px 14px; border-right:1px solid var(--rule); display:grid; gap:3px; } .control div:last-child { border-right:0; }
.control span { font:500 11px/1 var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--ink2); } .control b { font:500 13.5px/1.3 var(--mono); }
.routes { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.route { background:var(--surface); border:1px solid var(--rule); border-top:4px solid var(--accent); padding:16px 18px; display:grid; gap:10px; align-content:start; }
.route.r2 { border-top-color:var(--new); }
.route .tag { font:600 11px/1 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--ink2); }
.route dl { margin:0; display:grid; gap:6px; font-size:14px; }
.route dl div { display:grid; grid-template-columns:130px 1fr; gap:10px; }
.route dt { color:var(--ink2); } .route dd { margin:0; font-weight:500; }
@media (max-width:760px) { .routes { grid-template-columns:1fr; } }
.u { font-family:var(--mono); color:var(--pass); } .u.bad { color:var(--fail); }
.rules { counter-reset:none; }
table.mf td { min-width:120px; } table.mf th[scope=row] { min-width:130px; }
</style>"""
page = f"""<title>Stair Manufacturing Guide Rev C</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{style}
{EXTRA}
<main class="wrap">
  <div class="control" role="group" aria-label="Document control">
    <div><span>Document</span><b>Manufacturing guide</b></div><div><span>Revision</span><b>C · 27 Sep 2026</b></div>
    <div><span>Builds</span><b>Rev C change list</b></div><div><span>Material</span><b>6082-T6 · 5083-H111</b></div>
  </div>
  <header class="top">
    <div class="eyebrow">Manufacturing guide · folding stair unit · Rev C</div>
    <h1>How to build it</h1>
    <p>Two ways to make the Rev C stair. Both pass every check in the <a href="{lv}">load verdict</a>. Route 1 is the one drawn in the
       <a href="{cl}">change list</a> and has the most margin on the steps. Route 2 uses stock sections and simpler processes to cut tooling and machining.
       The outside shape of the steps, the rails, the pins and the supports are the same in both.</p>
  </header>
  <section>
    <h2>The two routes</h2>
    <div class="routes">
      <div class="route"><span class="tag">Route 1 · best strength</span><h3>Extruded steps, solid cut poles</h3>
        <dl><div><dt>Weight per unit</dt><dd class="mono">≈ {M['route1']:.0f} kg</dd></div>
        <div><dt>Highest use</dt><dd class="mono">{worst1:.2f}</dd></div>
        <div><dt>Steps at 4 kN</dt><dd class="mono">{S['A_extruded_6082']['util']:.2f}</dd></div>
        <div><dt>Structural welds</dt><dd>none</dd></div>
        <div><dt>Cost drivers</dt><dd>an extrusion die for the step; CNC or waterjet time on 12 poles</dd></div>
        <div><dt>Best for</dt><dd>a production run, where the die cost is spread over many units</dd></div></dl></div>
      <div class="route r2"><span class="tag">Route 2 · lower cost</span><h3>Bent-sheet steps, tube poles</h3>
        <dl><div><dt>Weight per unit</dt><dd class="mono">≈ {M['route2']:.0f} kg</dd></div>
        <div><dt>Highest use</dt><dd class="mono">{worst2:.2f}</dd></div>
        <div><dt>Steps at 4 kN</dt><dd class="mono">{S['A_bent_5083_welded']['util']:.2f}</dd></div>
        <div><dt>Structural welds</dt><dd>step bottoms and webs only (5083, no strength loss)</dd></div>
        <div><dt>Cost drivers</dt><dd>press-brake bending and welding labour per step</dd></div>
        <div><dt>Best for</dt><dd>a first batch or prototype; no special tooling</dd></div></dl></div>
    </div>
    <p class="meta">Route 2 is lighter because a hollow tube carries the barrier load with less metal than a solid bar. Weights are for the aluminium structure; jacks are extra. No prices are quoted: get quotes on the parts that differ (steps and poles).</p>
  </section>
  <section>
    <h2>Rules for both routes</h2>
    <ol class="rules">
      <li><b>6082-T6 for everything structural</b>Rails, poles, pins, axles, hooks and brackets. The only exception is the Route 2 step (5083-H111). Pure aluminium (1000 series) is too weak.</li>
      <li><b>No welds on rails, poles, pins or axles</b>A weld halves the strength of 6082-T6 next to it. Join these parts with pins, bolts or rivets.</li>
      <li><b>No hole across the pole at the upper rail</b>The pole bends most there; a Ø16 hole would take it from {P['R1_solid_25x55']['util'] if 'R1_solid_25x55' in P else PF['R1_solid_25x55']['gross']:.2f} to {PF['R1_solid_25x55']['hole_at_upper_rail']:.1f}. Use the strap and the centre-line cross-pin.</li>
      <li><b>Holes: 20 mm of metal to any edge</b>Drill and ream on a jig; hole centres within ± 0.5 mm so steps and poles fit every unit. About 0.5 mm clearance per side on pins.</li>
      <li><b>Isolate stainless from aluminium</b>Nylon washers and sleeves under every stainless bolt, stops the aluminium corroding at the joint.</li>
      <li><b>Captive locking pins</b>Hook keepers and step pins on lanyards or with R-clips, so they can’t be lost on site.</li>
      <li><b>Finish</b>Deburr every cut. Serrated step tops for grip, anodised contrast strip on each front edge. Anodise or leave mill finish; don’t paint over the bearing faces.</li>
      <li><b>Prove the first unit</b>Load one finished unit to the crowd load (7.5 kN/m²) and measure the sag against the load verdict before building the rest.</li>
    </ol>
  </section>
  <section>
    <h2>Part by part</h2>
    <p>“Use” is the share of the part’s strength taken by the worst event load (1.00 = at the limit).</p>
    <div class="tw"><table class="mf"><thead><tr><th>Part</th><th>Qty</th><th>Route 1 · best strength</th><th>Use</th><th>Route 2 · lower cost</th><th>Use</th></tr></thead><tbody>{rows}</tbody></table></div>
    <p class="meta">Top landing brackets, top rails and handrails are unchanged in both routes. The landing fixing ({AC['landing_bracket']['anchor_kN']:.1f} kN per side) is by others.</p>
  </section>
  <section>
    <h2>Which to choose</h2>
    <p>For a first batch, Route 2: stock tube and bent sheet, no die, and every part still passes. For a production run, Route 1: the extruded step has twice the margin, there are no welds anywhere, and the solid poles take knocks on site without denting. If Route 2 is chosen, tell Gerald: only cards F1, F3 and F4 in the change list change.</p>
  </section>
  <footer>
    <span>Rev C set: <a href="{ds}">datasheet</a> · <a href="{lv}">load verdict</a> · <a href="{cl}">change list</a>.</span>
    <span>Numbers: v2/revc/after_changes.json and pole_fixing.json. EN 1999-1-1: 6082-T6 f₀ 250 MPa (125 next to a weld), 5083-H111 f₀ 125 MPa.</span>
  </footer>
</main>
"""
open(os.path.join(HERE, "web", "manufacturing.html"), "w", encoding="utf8").write(page)
print("manufacturing Rev C", len(page), "| worst R1", round(worst1, 2), "R2", round(worst2, 2))
