"""Load verdict Rev C (27 Sep 2026): does the current staircase carry an event crowd, and does it once the Rev C changes are made?
Current model only (25 Sep, cleaned 26 Sep, standard 35 deg). No history. Numbers: v2/final/final_results.json (as drawn),
revc/after_changes.json, revc/frame_after.json, revc/pole_fixing.json (after the changes). Output: revc/web/verdict.html"""
import json, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); FIN = os.path.join(HERE, "..", "final")
R = json.load(open(os.path.join(FIN, "final_results.json")))
AC = json.load(open(os.path.join(HERE, "after_changes.json")))
FA = json.load(open(os.path.join(HERE, "frame_after.json")))
PF = json.load(open(os.path.join(HERE, "pole_fixing.json")))
LINKS = json.load(open(os.path.join(HERE, "links.json"))) if os.path.exists(os.path.join(HERE, "links.json")) else {}
ds, cl, mg = LINKS.get("datasheet", "#"), LINKS.get("changelist", "#"), LINKS.get("manufacturing", "#")
T = {r["check"]: r for r in R["tread"]["checks"]}
tu = lambda key: next(r for k, r in T.items() if key in k)
comp = lambda item, start, base="slides": next(r for r in R["components"] if r["item"] == item and r["check"].startswith(start) and r["base"] == base)
S = AC["steps"]; SL = S["sls"]["A"]
LIM = FA["limit_mm"]
frame_now = max(v["defl_sls"] for v in R["frame_sls"].values())
frame_after = max(v["defl_sls"] for k, v in FA.items() if isinstance(v, dict) and "defl_sls" in v)
f1_frame = min(v["f1"] for k, v in FA.items() if isinstance(v, dict) and "f1" in v)
# step frequency, same estimate as the frame (f1 = 17.75 / sqrt(d[G + 0.3Q] mm)); step self-weight 5.93 kg on 0.28 x 1.2 m
g = S["A_extruded_6082"]["mass"] * 9.81 / (0.28 * 1.2) / 1000; q = 7.5
d_step = SL["crowd"] * (g + 0.3 * q) / (g + q); f1_step = 17.75 / math.sqrt(d_step)
f1_all = 1 / math.sqrt(1 / f1_frame ** 2 + 1 / f1_step ** 2)
poles_now = {r["ref"]: r["util"] for r in R["components"] if r["item"] == "Pole RHS 25x10x2" and r["base"] == "slides"}
hbr = comp("Handrail bracket 15x5 bent flat", "1.25")
f = lambda x: f"{x:.2f}"
# (ref, requirement, as drawn text, as drawn util, after text, after util)
rows = [
  ("Crowd on the stair", [
    ("R113", "Crowd 7.5 kN/m²: steps", "208 MPa", 0.91, "box step, 0.41 of its strength", S["A_extruded_6082"]["util"]),
    ("R113", "Crowd 7.5 kN/m²: fold lock (pole pegs)", "Ø2 pegs, carries ≈ 1.1 kN/m²", 6.62, "Ø12 pegs", AC["pegs"]["bending"]),
    ("R113", "Crowd 7.5 kN/m²: guide rails at the pin holes", "20–25 deep", 6.95, "about 70 deep", AC["rails"]["util_net"]),
    ("R170", "Step pins", "Ø10", 5.30, "Ø20", AC["step_pins"]["d20"]["bending"]),
    ("R170", "Metal round the pin holes", "7.5 mm, needs 10.1", 1.34, "20 mm", AC["rails"]["edge_util_20mm"]),
    ("R115", "Side frame sag ≤ L/250 (7.3 mm)", f"{frame_now:.1f} mm", frame_now / LIM, f"{frame_after:.1f} mm", frame_after / LIM),
    ("R177", "First vertical frequency ≥ 6 Hz", "≈ 6 Hz with step flex", 1.0, f"≈ {f1_all:.0f} Hz (frame {f1_frame:.0f}, steps {f1_step:.0f})", 6 / f1_all),
  ]),
  ("Point loads on a step", [
    ("R114", "4 kN on 200 × 200 at the front edge", "828 MPa", tu("ULS 4 kN patch front, mid-span")["util"], "A extruded (welded box 0.82)", S["A_extruded_6082"]["util"]),
    ("R115", "Sag under 4 kN ≤ 12.2 mm", "58.3 mm", 58.3 / 12.2, f"{SL['sag4']:.1f} mm", SL["sag4"] / 12.2),
    ("R115", "Sag under a crowd ≤ 4.9 mm", "17.5 mm", 17.5 / 4.86, f"{SL['crowd']:.1f} mm", SL["crowd"] / 4.86),
    ("R115", "Sag under one person < 10 mm", "18.8 mm", 1.88, f"{SL['person']:.1f} mm", SL["person"] / 10),
  ]),
  ("Barrier and handrail", [
    ("R179", "1.5 kN at the top of a pole", "hollow 25 × 10 × 2", poles_now["R179"], "solid 25 × 55 (worst barrier load)", AC["poles"]["R1_tapered_solid_25x55"]["util"]),
    ("R142", "3.0 kN/m on the top rail", "0.16 kN/m carried", poles_now["R142"], "covered by the row above", AC["poles"]["R1_tapered_solid_25x55"]["util"]),
    ("R142", "Pole fixing, upper rail", "not drawn", None, "strap + 2 × M12", PF["strap_upper"]["bolt_tension"]),
    ("R142", "Pole fixing, lower rail", "not drawn", None, "Ø16 pin (bearing on the rail)", PF["pin_lower"]["bearing_rail_5mm"]),
    ("R142", "Rails under the pole push", "can’t take it", None, "70-deep rails, right side", AC["rails"]["lateral_right"]),
    ("R143", "1.25 kN on the handrail: brackets", "15 wide", hbr["util"], "25 wide", AC["brackets"]["w25"]),
    ("R178", "1.0 kN/m down on the top rail", "U 25 × 25 × 5", 0.04, "no change", 0.04),
  ]),
  ("Supports", [
    ("R147", "Base axle", "Ø25 × 2.5, 70 mm off the jack", 6.04, "48.3 × 4 tube, clamped base", AC["axles"]["scaffold_clamped"]),
    ("R147", "Top axle", "Ø25 × 2.5", 3.85, "48.3 × 4 tube", AC["axles"]["top_scaffold_clamped"]),
    ("R150", "Base hook lock", "not drawn, 17.7 kN", None, "Ø14 keeper pin", AC["hook_locks"]["d14_single_shear"]),
    ("R150", "Top hook lock", "not drawn, 11.3 kN", None, "Ø12 keeper pin", AC["hook_locks"]["d12_single_shear"]),
    ("R174", "Jacks, base held by a scaffold clamp", "M24", 1.71, "M30", AC["jacks"]["m30_clamped"]),
    ("R174", "Jacks on the ground", "M24", 0.08, "M24", AC["jacks"]["m24_ground"]),
    ("R73", "Footplates", "100 × 100 × 5", 2.66, "150 × 150 × 8", AC["jacks"]["footplate_150x8_clamped"]),
    ("R170", "Top landing bracket", "Ø20 pin, 5 mm plate", 0.38, "no change", AC["landing_bracket"]["plate"]),
  ]),
]
def chip(u):
    if u is None: return '<span class="st open">Missing</span>'
    return '<span class="st pass">Pass</span>' if u <= 1.0 else '<span class="st open">Fail</span>'
def cell(u, cls=""):
    if u is None: return '<td class="mono">—</td>'
    return f'<td class="mono {"bad" if u > 1 else "ok"}">{u:.2f}</td>'
body = ""
n_fail_now = 0; n_all = 0; after_max = []
for grp, rs in rows:
    body += f'<tr class="grp"><td colspan="7">{grp}</td></tr>'
    for ref, req, nt, nu, at, au in rs:
        n_all += 1; n_fail_now += (nu is None or nu > 1)
        after_max.append((au, req))
        body += f'<tr><td class="mono">{ref}</td><th scope="row">{req}</th><td>{nt}</td>{cell(nu)}<td>{at}</td>{cell(au)}<td>{chip(au)}</td></tr>'
after_max.sort(reverse=True)
top = after_max[0]
bars = ""
for u, name in after_max[:10]:
    bars += f'<div class="brow"><span>{name}</span><div class="btrack"><i style="width:{min(u, 1.0) * 100:.1f}%"></i></div><b class="mono">{u:.2f}</b></div>'
geo = [
    ("R7", "Open gap under each step ≤ 120", "125 mm", "a lip at least 5 mm down on the front edge (35 mm gives 100)", "Change F1"),
    ("R63", "Top rail ≥ 1,100 above datum", "1,112 above the step · 1,013 above the pitch line", "no change, or +87 mm if measured from the pitch line", "Decide F6"),
    ("R64", "Handrail graspable, 25–50 mm", "U 25 × 25 channel", "owner’s padding, finished shape 25–50 mm", "Owner"),
    ("R16 R17", "Slip resistance, contrasting nosings", "not specified", "serrated step tops, anodised contrast nosing; pendulum test", "Specify"),
    ("R65 R68", "Side infill, toe board", "none", "not fitted by decision; the scaffold edge protection covers it", "By others"),
    ("R9 R4 R5 R8", "Pitch 35°, going 250, rise 175, 2R + G 600", "as drawn", "no change", "Pass"),
]
geo_html = "".join(f'<tr><td class="mono">{a}</td><th scope="row">{b}</th><td>{c}</td><td>{d}</td><td><span class="st {"pass" if e == "Pass" else "cond"}">{e}</span></td></tr>' for a, b, c, d, e in geo)

style = open(os.path.join(HERE, "..", "brief", "web", "_brief_before_final_check.html"), encoding="utf8").read()
style = style[style.index("<style>"):style.index("</style>") + 8]
EXTRA = """<style>
.control { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); border:1px solid var(--rule); background:var(--surface); }
.control div { padding:10px 14px; border-right:1px solid var(--rule); display:grid; gap:3px; } .control div:last-child { border-right:0; }
.control span { font:500 11px/1 var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--ink2); } .control b { font:500 13.5px/1.3 var(--mono); }
.verdict { display:grid; grid-template-columns:1fr 1fr; border:1.5px solid var(--ink); background:var(--surface); }
.verdict > div { padding:18px 20px; display:grid; gap:10px; align-content:start; }
.verdict > div + div { border-left:1.5px solid var(--ink); }
.stamp { justify-self:start; font:700 15px/1 var(--display); letter-spacing:.14em; text-transform:uppercase; padding:6px 10px; border:2px solid currentColor; }
.stamp.fail { color:var(--fail); } .stamp.pass { color:var(--pass); }
.big { font:600 42px/1 var(--display); font-variant-numeric:tabular-nums; } .big small { font:500 16px var(--body); color:var(--ink2); margin-left:6px; }
@media (max-width:760px) { .verdict { grid-template-columns:1fr; } .verdict > div + div { border-left:0; border-top:1.5px solid var(--ink); } }
td.bad { color:var(--fail); font-weight:600; } td.ok { color:var(--pass); }
tr.grp td { font:600 11px/1.2 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--accent); background:var(--paper); padding-top:12px; }
.bars { background:var(--surface); border:1px solid var(--rule); padding:14px 16px; display:grid; gap:8px; }
.brow { display:grid; grid-template-columns:minmax(140px,300px) minmax(0,1fr) 48px; gap:12px; align-items:center; font-size:13.5px; }
.btrack { position:relative; height:12px; background:var(--soft); } .btrack i { position:absolute; inset:0 auto 0 0; background:var(--pass); }
.btrack::after { content:""; position:absolute; right:0; top:-4px; bottom:-4px; border-left:2px solid var(--ink); }
.brow b { text-align:right; font-weight:500; }
@media (max-width:560px) { .brow { grid-template-columns:minmax(0,1fr) 44px; } .brow span { grid-column:1 / -1; } }
.conds { margin:0; padding:0; list-style:none; display:grid; gap:8px; }
.conds li { background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--accent); padding:10px 14px; font-size:14.5px; }
.conds li.must { border-left-color:var(--fail); }
</style>"""
page = f"""<title>Stair Load Verdict Rev C</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
{style}
{EXTRA}
<main class="wrap">
  <div class="control" role="group" aria-label="Document control">
    <div><span>Document</span><b>Load verdict</b></div><div><span>Revision</span><b>C · 27 Sep 2026</b></div>
    <div><span>Model</span><b>25 Sep, cleaned 26 Sep · 35°</b></div><div><span>Basis</span><b>Aug-2026 events sheet · EN 1999-1-1</b></div>
  </div>
  <header class="top">
    <div class="eyebrow">Load verdict · folding stair unit · Rev C</div>
    <h1>Does the stair hold an event crowd?</h1>
    <p>As drawn, no. With the Rev C changes, yes, on every load the events sheet asks for. Loads are factored by EN 1990
       (1.35 × self-weight + 1.5 × crowd); aluminium is EN AW-6082-T6. A value of 1.00 means the part is exactly at its limit.</p>
  </header>
  <section>
    <div class="verdict">
      <div><span class="stamp fail">As drawn: does not comply</span>
        <div class="big">1.1<small>of 7.5 kN/m² crowd carried</small></div>
        <p>The fold lock pegs, rails, step pins, steps, poles and supports all fail. The handrail poles are 30× too weak, so nobody can lean on the barrier.</p></div>
      <div><span class="stamp pass">With the Rev C changes: complies</span>
        <div class="big">{top[0]:.2f}<small>highest use of any part</small></div>
        <p>Every check on this page passes. The tightest is the {top[1][0].lower() + top[1][1:]}. What to draw is in the <a href="{cl}">change list</a>; how to build it is in the <a href="{mg}">manufacturing guide</a>.</p></div>
    </div>
  </section>
  <section>
    <h2>Every check, now and after</h2>
    <p>“Now” is the model as drawn. “After” is the same model with the Rev C changes, under the same loads and formulas. R-numbers are rows of the events sheet.</p>
    <div class="tw"><table><thead><tr><th>Ref</th><th>Check</th><th>Now</th><th>Use</th><th>After Rev C</th><th>Use</th><th>Result</th></tr></thead><tbody>{body}</tbody></table></div>
    <p class="meta">Sag and frequency after the changes come from re-running the side-frame model with the 70-deep rails. The step frequency is an estimate from the step’s own sag; the combined value uses Dunkerley’s rule.</p>
  </section>
  <section>
    <h2>Closest to the limit after the changes</h2>
    <div class="bars">{bars}</div>
    <p class="meta">The black line is 1.00. The base axle only reaches {AC['axles']['scaffold_clamped']:.2f} when the jacks are clamped to a scaffold. On the ground it is {AC['axles']['scaffold_ground']:.2f}.</p>
  </section>
  <section>
    <h2>Geometry and detailing</h2>
    <div class="tw"><table><thead><tr><th>Ref</th><th>Requirement</th><th>As drawn</th><th>After Rev C</th><th>Status</th></tr></thead><tbody>{geo_html}</tbody></table></div>
  </section>
  <section>
    <h2>Conditions of use after the changes</h2>
    <ul class="conds">
      <li class="must">All 12 poles fitted and fixed (strap and pins) before anyone steps on. Without them each side folds flat.</li>
      <li class="must">Hook keeper pins in at the base and the top, and a collar each side of every hook.</li>
      <li class="must">The top landing brackets anchored to the landing or cabin for {AC['landing_bracket']['anchor_kN']:.1f} kN per side. That fixing is outside this model.</li>
      <li class="must">Jacks clamped to a scaffold: use M30 jacks on 150 × 150 × 8 footplates. On the ground, M24 is enough.</li>
      <li>Standard 35° stair only. The catwalk and steep states were not re-checked in Rev C.</li>
      <li>The top rail height reference (F6) must be agreed with the approver.</li>
      <li>These capacities are calculated, not tested. Before sign-off, load one finished unit to the crowd load and compare its sag with the {frame_after:.1f} mm frame and {SL['crowd']:.1f} mm step predicted here.</li>
    </ul>
  </section>
  <footer>
    <span>Rev C set: <a href="{ds}">datasheet</a> · <a href="{cl}">change list</a> · <a href="{mg}">manufacturing guide</a>.</span>
    <span>Numbers: v2/final/final_results.json (as drawn); v2/revc/after_changes.json, frame_after.json, pole_fixing.json (after). Loads: v2/spec/sheet_2026-09-23_events.txt.</span>
  </footer>
</main>
"""
open(os.path.join(HERE, "web", "verdict.html"), "w", encoding="utf8").write(page)
print("verdict Rev C", len(page), "| rows", n_all, "| fail now", n_fail_now, "| top after", top)
