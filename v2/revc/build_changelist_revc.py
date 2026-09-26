"""Change list Rev C (27 Sep 2026) for the SketchUp designer: only the changes still needed on the current model
(25 Sep model as cleaned on 26 Sep). No history. Numbers: v2/final JSON + revc/after_changes.json. Pictures: img/f*.jpg
(render_final_check_refs.py on the cleaned model), diagrams: v2/brief/final_diagrams.py. Output: revc/web/changelist.html"""
import json, os, sys, re, math
HERE = os.path.dirname(os.path.abspath(__file__)); FIN = os.path.join(HERE, "..", "final")
sys.path.insert(0, os.path.join(HERE, "..", "brief"))
import final_diagrams as D
def J(n): return json.load(open(os.path.join(FIN, n)))
R = J("final_results.json"); AC = json.load(open(os.path.join(HERE, "after_changes.json")))
GRT = J("tread_grating.json"); UBX = J("tread_ubox.json"); BOX = J("tread_box2.json")
LINKS = json.load(open(os.path.join(HERE, "links.json"))) if os.path.exists(os.path.join(HERE, "links.json")) else {}
MK = json.load(open(os.path.join(HERE, "web", "img", "f_markers.json")))
T = {r["check"]: r for r in R["tread"]["checks"]}
def tu(key): return next(r for k, r in T.items() if key in k)
comp = lambda item, start, base="slides": next(r for r in R["components"] if r["item"] == item and r["check"].startswith(start) and r["base"] == base)
EF, EH = R["frame_envelopes"]["slides"], R["frame_envelopes"]["held"]
t_front = tu("ULS 4 kN patch front, mid-span"); d_crowd = tu("Crowd 7.5 kN/m2: nosing")
latch = comp("Latch pins O2 (per pole)", "Vertical"); pin_m = comp("Tread pins O10 (with link force)", "Bending"); pin_v = comp("Tread pins O10 (with link force)", "Shear")
poles = {r["ref"]: r["util"] for r in R["components"] if r["item"] == "Pole RHS 25x10x2" and r["base"] == "slides"}
hbr = comp("Handrail bracket 15x5 bent flat", "1.25")
S = AC["steps"]; B4CFG = BOX["B4 box 3 / 2 / 2, two webs 2"]["cfg"]; G5 = GRT["G5 grating: bars 3 x 50 at 46 mm, 8 mm nosing bar"]; U3 = UBX["U3 your box: top 2, mid 2, ribs 2 at 60"]

style = open(os.path.join(HERE, "..", "brief", "web", "_brief_before_final_check.html"), encoding="utf8").read()
style = style[style.index("<style>"):style.index("</style>") + 8]
EXTRA = """<style>
.num.fcrit, .mk.fcrit { background:var(--fail); }
.card .num { font-size:14px; width:40px; }
.mk { width:32px; height:32px; line-height:32px; font-size:12px; }
.card .refs { grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr)); }
.why1 { display:grid; gap:4px; } .why1 > span { font:600 11px/1 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--ink2); } .why1 p { max-width:80ch; }
.sec .arrowh { fill:var(--ink2); }
.decide { display:inline-block; font:600 11px/1 var(--mono); letter-spacing:.06em; text-transform:uppercase; color:var(--warn); background:var(--warnbg); padding:4px 7px; margin-left:6px; vertical-align:middle; }
.lists { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr)); gap:14px; }
.lists > div { background:var(--surface); border:1px solid var(--rule); padding:12px 16px; }
.lists h3 { font-size:18px; margin-bottom:6px; } .lists ul { margin:0; padding-left:18px; display:grid; gap:4px; font-size:14.5px; }
.control { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); border:1px solid var(--rule); background:var(--surface); }
.control div { padding:10px 14px; border-right:1px solid var(--rule); display:grid; gap:3px; } .control div:last-child { border-right:0; }
.control span { font:500 11px/1 var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--ink2); } .control b { font:500 13.5px/1.3 var(--mono); }
</style>"""

def card(fid, title, meta, now, change, why, imgs, how=(), drawing="", extra="", crit=True, decide=False):
    figs = "".join(f'<figure><img src="img/{src}" alt="{alt}" width="1000" height="625" loading="lazy"><figcaption>{alt}</figcaption></figure>' for src, alt in imgs)
    how_html = ('<div class="how"><span>In SketchUp</span><ul>' + "".join(f"<li>{h}</li>" for h in how) + "</ul></div>") if how else ""
    return f"""
    <article class="card" id="{fid}">
      <header><span class="num{' fcrit' if crit else ''}">{fid.upper()}</span><div><h3>{title}{'<span class="decide">decide</span>' if decide else ''}</h3><p class="meta">{meta}</p></div></header>
      <div class="nowto">
        <div class="now"><span>In the model now</span><p>{now}</p></div>
        <div class="to"><span>Change to</span><p>{change}</p></div>
      </div>
      <div class="why1"><span>Why</span><p>{why}</p></div>
      {drawing}
      <div class="refs">{figs}</div>
      {how_html}
      {extra}
    </article>"""

f1_table = f"""<div class="tw"><table><thead><tr><th>Step (280 × 50 outside, with drain holes)</th><th>4 kN at the front edge (≤ 1)</th><th>Sag under 4 kN, mm (≤ 12.2)</th><th>Crowd sag, mm (≤ 4.9)</th><th>kg per step</th></tr></thead><tbody>
<tr><td><b>A · chosen</b> thin closed box: 3 top / 2 bottom / 2 walls, two 2 mm inner webs</td><td class="mono">{S['A_extruded_6082']['util']:.2f} ({S['A_bent_6082_welded']['util']:.2f} if welded)</td><td class="mono">{S['sls']['A']['sag4']:.1f}</td><td class="mono">{S['sls']['A']['crowd']:.1f}</td><td class="mono">{S['A_extruded_6082']['mass']:.1f}</td></tr>
<tr><td><b>C · alternative</b> open grating: 3 × 50 bars every 46 mm along the step, 8 mm front bar</td><td class="mono">{S['C_grating_46_nosing8']['util']:.2f} (press-locked)</td><td class="mono">{S['sls']['C46']['sag4']:.1f}</td><td class="mono">{S['sls']['C46']['crowd']:.1f}</td><td class="mono">{S['C_grating_46_nosing8']['mass']:.1f}</td></tr>
<tr><td>Now: open J + L with grating front to back</td><td class="mono">{t_front['util']:.2f}</td><td class="mono">{abs(R['tread']['cases']['SLS 4 kN patch front, mid-span']['lip']):.0f}</td><td class="mono">{d_crowd['value']:.1f}</td><td class="mono">6.4</td></tr>
</tbody></table></div>"""

cards = [
    card("f1", "Steps: redraw as a thin closed box (A)", "6 per unit · needed to pass · open grating (C) is the alternative",
         f"Open J at the back, a small L at the front edge, grating bars running front to back, two thin flats along the step (joined to the end plates). 4 kN on the front edge is {t_front['util']:.1f}× too much; a crowd sags the front edge {d_crowd['value']:.1f} mm (limit 4.9).",
         f"<b>A (draw this)</b> thin closed box, 280 × 50 outside: {B4CFG['t_top']:g} mm top, {B4CFG['t_bot']:g} mm bottom, {B4CFG['t_wall']:g} mm front and back walls, two {B4CFG['t_web']:g} mm inner webs at 95 and 185 mm from the back, drain holes in the top and the bottom. "
         f"<b>C (alternative)</b> open grating in the same 280 × 50: 3 × 50 bearing bars running along the step every 46 mm, a 5 mm back bar, an 8 × 50 front bar, 3 × 25 cross bars on top every 50 mm. Same end plates and pins for both.",
         "The step spans 1.2 m between the rails, so the parts that carry the load must run along that length and be either closed (A) or 50 mm deep (C). Today’s grating bars run the short way, so the J and the small L carry everything and twist. Open shapes only 25 mm deep fail, even as a fine lattice.",
         [("f1_where.jpg", "Where: all 6 steps (orange)"), ("f1_close1.jpg", "The steps as drawn now"), ("f1_close2.jpg", "From below: J, L, bars and flats")],
         ["Draw A. If C is used instead, only the step section changes; the end plates and pins stay the same.",
          "Keep the walking surface height, the end plates and every pin hole exactly where they are.",
          "Add a lip at least 5 mm down along the front edge so the open gap under each step is 120 or less (a 35 mm lip gives the recommended 100).",
          "A: holes up to about a fifth of each plate, at least 20 mm from the walls and webs; holes in the bottom plate too, so water runs through. C: serrated bar tops."],
         D.f1_ac(B4CFG, G5["bars"], (S["A_extruded_6082"]["util"], S["A_extruded_6082"]["mass"]), (S["C_grating_46_nosing8"]["util"], S["C_grating_46_nosing8"]["mass"])), f1_table),
    card("f2", "Step pins 20 mm, rails about 70 deep", "4 pins per step · 4 rails · needed to pass",
         f"Ø10 pins at the step ends. On the right side each pin crosses a 14 mm gap (end plate, washer, 7 mm bush, rail wall). At the top step each pin carries about {pin_v['value'] / 1000:.1f} kN. Rails are 20–25 deep with the pin holes cutting most of the section.",
         f"Ø20 pins and Ø20 holes in the rails and step end plates, with bushes and washers to suit. Rails about 70 deep, same widths, 5 mm walls, with at least 20 mm of metal between every hole and the nearest free edge.",
         f"Each step also props the upper rail off the lower one, so its pins carry that bracing force and bend across the gap. Ø10 is {pin_m['util']:.1f}× too weak; Ø20 is at {AC['step_pins']['d20']['bending']:.2f}. The deeper rails carry the bigger holes ({AC['rails']['edge_util_20mm']:.2f} at the hole edge) and the sideways push from the poles (F4).",
         [("f2_where.jpg", "Where: the 4 guide rails and the step-pin hardware"), ("f2_close1.jpg", "Pins through the rails at the base")],
         ["Keep every hole centre where it is; the rails grow away from their holes.", "Right rails grow downwards; the left channels deepen by the same amount so a neighbour’s right rail still drops fully in.", "Put each split-pin hole just outside its nut."],
         D.f2_pin(70, 20)),
    card("f3", "Pole locking pegs 12 mm, upper pair added", "12 poles, 4 pegs each · needed to pass",
         "Each pole is one piece with its locking end, which drops through both rails. The lower rail has two 2 mm pegs, one each side, reaching 7.5 mm across to holes in the rail walls. The upper rail has only a hole through the pole, no pegs. The left upper rail’s notches are about 9 mm off the poles.",
         "12 mm pegs, 2 at each rail (4 per pole), with the rail-wall notches widened to suit and lined up with the poles, 0.5 mm clearance each side.",
         f"The pegs hold the upper and lower rail at their spacing; that is what stops each side folding flat under a crowd. Each rail’s pair passes about {latch['value'] / 1000:.1f} kN, and each peg bends over its 7.5 mm reach. 12 mm pegs are at {AC['pegs']['bending']:.2f}.",
         [("f3_where.jpg", "Where: all 12 poles, one piece with their locking ends"), ("f3_close1.jpg", "Bottom of a pole through a rail; the dot is a peg end")],
         ["Draw each pole and its locking end as a single part.", "Add the upper-rail pegs."], D.f3_pegs()),
    card("f4", "Poles: solid, deeper across the stair, bolted outside the rails", "12 per unit · needed to pass",
         f"Hollow 25 × 10 × 2 poles, 10 mm across the stair, passing through the rails. Under the barrier loads they are {poles['R142']:.0f}–{poles['R179']:.0f}× too weak.",
         f"Solid 6082-T6, 25 along the stair × 55 across at the rails, tapering to 15 at the top rail. Each pole stands on the outside face of the rails with two fixings into each rail (Ø16 pins or M12 bolts); its locking tab and pegs (F3) stay part of the same piece.",
         f"People push the top rail outward, and each pole bends like a 1 m lever where it meets the rails, so depth across the stair is what counts. 25 × 55 is at {AC['poles']['R1_tapered_solid_25x55']['util']:.2f} under the worst barrier load. A 55 mm pole can’t pass through a 35 mm rail, hence outside mounting. The push reaches the rails as about {AC['pole_fix']['F_kN']:.0f} kN each way, which the deeper rails from F2 carry ({AC['rails']['lateral_left']:.2f} / {AC['rails']['lateral_right']:.2f}).",
         [("f4_where.jpg", "Where: the 12 poles"), ("f4_close1.jpg", "Poles along the left side")],
         ["Keep 25 along the stair; the 55 is across the stair.", "The middle handrail between two units side by side isn’t a barrier (no drop there) and can stay as it is."],
         D.f4_pole(55)),
    card("f5", "Supports: one axle each end, collars, hook locks", "base and top · needed to pass",
         "At the base and the top, the axle tube stops about 34 mm short of the right-hand support. Each hook sits about 70 mm from its jack, so the Ø25 × 2.5 tube bends between them. Nothing stops the rails sliding sideways along the axle. The hook locks aren’t drawn.",
         f"One tube from support to support at each end (about 1,400 long): a 48.3 × 4 aluminium scaffold tube, or move each jack head under its hook and use Ø30 × 3. A collar on the axle each side of every hook. Base hook plates with at least 39 mm of plate round the axle (57.5 if the jacks will be clamped to a scaffold). "
         f"Draw a hook lock: a Ø14 pin through the base hook plate under the axle and Ø12 at the top, or turn the base hook so its plate sits on top of the axle. Draw the landing bracket’s bolts for {AC['landing_bracket']['anchor_kN']:.1f} kN per side.",
         f"The axle is loaded at the hook and held at the jack 70 mm away, so it bends: a scaffold tube is at {AC['axles']['scaffold_ground']:.2f} on the ground and {AC['axles']['scaffold_clamped']:.2f} clamped to a scaffold. The base hook is open on the side the stair pushes, so its lock carries the load (up to {AC['hook_locks']['base_kN']:.1f} kN per hook). Collars stop the stair shifting sideways under the barrier push.",
         [("f5_where.jpg", "Where: axles, hooks, jack heads, landing brackets; missing axle length in yellow"), ("f5_close1.jpg", "Base: the hook sits 70 mm from the jack"), ("f5_close3.jpg", "Right base jack: yellow is the missing length"), ("f5_close2.jpg", "Top: landing bracket and axle")],
         ["Jacks on the ground: M24 jacks and the drawn footplates are fine. Jacks clamped to a scaffold: M30 on 150 × 150 × 8 footplates, with a fixing for 10.9 kN sideways.", "The hooks stay cut or bent as part of the rails."],
         D.f5_base()),
    card("f6", "Top rail height: confirm the measuring line", "decision · no drawing change yet",
         "Top of the top rail: 1,112 mm above the step surface at each pole, 1,013 mm above the pitch line (the line joining the step front edges). Handrail: 903 mm above the pitch line.",
         "If the approver measures from the pitch line, raise the top rail about 90 mm (raise the pole tops or pivot posts). If from the step surface, no change.",
         "The code sheet gives 1,100 mm “above datum (floor / pitch line)”, and it measures the handrail from the pitch line. The handrail passes either way (900–1,000).",
         [("f6_where.jpg", "Where: both top rails"), ("f6_close1.jpg", "Top rail on the pole tops")], [], D.f6_height(), crit=False, decide=True),
    card("f8", "Handrail brackets 25 wide", "12 per unit",
         f"Bent flats 15 wide, about 5 thick, holding the handrail 57 mm off the poles: {hbr['util']:.1f}× too weak under 1.25 kN on the handrail.",
         f"25 wide at the same thickness ({AC['brackets']['w25']:.2f}). Keep the offset and the fixing points.",
         "The bracket is a small cantilever; widening it in the direction it bends adds strength with the square of the width.",
         [("f8_where.jpg", "Where: the 12 brackets"), ("f8_close1.jpg", "Brackets from below")], [], D.f8_bracket(), crit=False),
    card("f9", "Drawing clean-up", "drawing only",
         "18 parts are drawn twice in the same place: 4 right poles with their locking ends and both top pivot parts, and the 2 right hooks. 6 zero-thickness faces. The left rear step pin is drawn Ø10.73 in a Ø10 hole. Split pins sit past the pin ends. Pins, poles and slots are drawn line-to-line.",
         "Delete one of each pair (both copies are red in the pictures) and the empty faces. Draw clearances: about 0.5 mm per side on pins and slots. The pin sizes are set by F2.",
         "Duplicates don’t change the strength checks, but the drawing should match what gets made and counted.",
         [("f9_close1.jpg", "Right poles drawn twice (red)"), ("f9_close2.jpg", "Right base hook drawn twice (red)")], ["Afterwards: 12 poles, 12 locking ends, 4 hooks, 2 axles."], crit=False),
]
pos_ = {}
for k in sorted(MK):
    if k == "f7": continue
    x, y = MK[k]
    for _ in range(6):
        if any(abs(x - a) < 3.5 and abs(y - b) < 4.5 for a, b in pos_.values()): x += 3.0
    pos_[k] = (x, y)
mk = "".join(f'<a class="mk{" fcrit" if k in ("f1", "f2", "f3", "f4", "f5") else ""}" href="#{k}" style="left:{x:.2f}%;top:{y:.2f}%" aria-label="Change {k.upper()}">{k.upper()}</a>' for k, (x, y) in sorted(pos_.items()))
summary = [("F1", "Steps", "open J + L, grating front to back", "A thin closed box (C open grating is the alternative)", "R113 R114 R115 R7"),
           ("F2", "Step pins and rails", "Ø10 pins, rails 20–25 deep", "Ø20 pins, rails about 70 deep, 20 mm metal round each hole", "R113 R170"),
           ("F3", "Pole locking pegs", "2 mm, lower rail only", "12 mm, 2 per rail, notches lined up", "R78 R104"),
           ("F4", "Poles", "hollow 25 × 10 × 2 through the rails", "solid 25 × 55 tapering to 15, outside the rails, bolted", "R142 R143 R179"),
           ("F5", "Supports", "Ø25 × 2.5 axle short of the right support; no collars; no hook lock", "one 48.3 × 4 tube each end (or jacks under hooks), collars, hook locks, landing bolts", "R147 R150 R73"),
           ("F6", "Top rail height", "1,013 above the pitch line", "decide the measuring line; +90 mm if the pitch line", "R63"),
           ("F7", "Handrail", "U 25 × 25 channel", "no change (owner’s padding)", "R64"),
           ("F8", "Handrail brackets", "15 wide", "25 wide", "R143"),
           ("F9", "Drawing", "duplicates, empty faces, line-to-line fits", "delete copies, add clearances", "—")]
sum_html = "".join(f'<tr><td class="mono"><a href="#{a.lower()}">{a}</a></td><th scope="row">{b}</th><td>{c}</td><td class="strong">{d}</td><td class="mono">{e}</td></tr>' for a, b, c, d, e in summary)
ds, lv, mg = LINKS.get("datasheet", "#"), LINKS.get("verdict", "#"), LINKS.get("manufacturing", "#")
page = f"""<title>Stair Change List Rev C</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{style}
{EXTRA}
<main class="wrap">
  <div class="control" role="group" aria-label="Document control">
    <div><span>Document</span><b>Change list</b></div><div><span>Revision</span><b>C · 27 Sep 2026</b></div>
    <div><span>Model</span><b>25 Sep, cleaned 26 Sep</b></div><div><span>For</span><b>SketchUp redraw</b></div>
  </div>
  <header class="top">
    <div class="eyebrow">SketchUp change list · folding stair unit · Rev C</div>
    <h1>What to change in the model</h1>
    <p>Every change still needed on the current model, and nothing else. Each one says what’s in the model now, what to draw instead, and why. Sizes are final unless marked “decide”. Checked against the Aug-2026 events sheet (R-numbers are its rows).</p>
    <div class="result">
      <div><span>Crowd the unit carries</span><b><s>1.1</s>7.5 kN/m²</b></div>
      <div><span>Push on the top rail</span><b><s>0.16</s>3.0 kN/m</b></div>
      <div><span>4 kN on a step</span><b><s>3.6×</s>0.4–0.8</b></div>
      <div><span>Weight per unit</span><b><s>{AC['mass_unit']['now']:.0f}</s>≈ {AC['mass_unit']['route2']:.0f}–{AC['mass_unit']['route1']:.0f} kg</b></div>
    </div>
  </header>
  <section>
    <h2>Decided and open</h2>
    <div class="lists">
      <div><h3>Already decided</h3><ul><li>Steps: thin closed box (A); open grating (C) is the alternative.</li><li>Hooks cut or bent as part of the rails, and locked onto the axles.</li><li>Each pole is one piece with its locking end (4 pegs).</li><li>Poles solid; they are the crowd barrier.</li><li>Top rail keeps its channel; the owner adds padding.</li><li>No middle rail, toe board or feet; the scaffold supports the unit.</li><li>Jacks stand on the ground or on a scaffold.</li></ul></div>
      <div><h3>Still to decide</h3><ul><li>Top rail height: which line the approver measures from (F6).</li><li>Build route: best strength or lower cost (see the <a href="{mg}">manufacturing guide</a>).</li></ul></div>
    </div>
  </section>
  <section>
    <h2>Where the changes are</h2>
    <div class="key"><span><i style="background:var(--fail)"></i>needed to pass (F1–F5)</span><span><i style="background:var(--accent)"></i>smaller or a decision (F6, F8, F9)</span><span>Click a number to jump to it. In the pictures, <b style="color:#E8590C">orange</b> = change, <b style="color:#D11A1A">red</b> = remove, <b style="color:#B8960C">yellow</b> = missing.</span></div>
    <figure class="fig" id="figG"><div class="shot"><img src="img/f_overview.jpg" alt="Current model, standard stair, with the changes numbered" width="1600" height="1000" loading="lazy">{mk}</div>
      <figcaption><b>Overview</b> current model (25 Sep, cleaned 26 Sep), standard stair</figcaption></figure>
  </section>
  <section>
    <h2>All changes at a glance</h2>
    <div class="tw"><table><thead><tr><th>#</th><th>Part</th><th>Now</th><th>Change to</th><th>Sheet rows</th></tr></thead><tbody>{sum_html}</tbody></table></div>
  </section>
  <section>
    <h2>The changes</h2>
    <div class="cards">{"".join(cards)}</div>
    <p class="cnote"><b>F7 Handrail: no change.</b> The owner adds foam or padding that rounds it off and keeps it cool. For the grip rule (R64) the padded shape should end up 25–50 mm across.</p>
  </section>
  <footer>
    <span>Rev C set: <a href="{ds}">datasheet</a> · <a href="{lv}">load verdict</a> · <a href="{mg}">manufacturing guide</a>.</span>
    <span>Pictures: FINAL_standard.blend (current model). Numbers: v2/final and v2/revc/after_changes.json.</span>
  </footer>
</main>
"""
open(os.path.join(HERE, "web", "changelist.html"), "w", encoding="utf8").write(page)
print("change list Rev C", len(page), "| cards", len(cards))
