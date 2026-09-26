"""Builds the technical datasheet page (HTML) from computed data.
AS-IS  : uvx python v2/datasheet/build_datasheet.py            -> web/index.html  (DS-FMS-ASIS)
The same template is reused for the final design once it has been load-tested (DS-FMS-FINAL).
Inputs: asis_ratings.json (asis_ratings.py), state_dims.json (Blender), geometry_vs_sheet.json (Aug-2026 sheet)
"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "asis_ratings.json")))
GEO = json.load(open(os.path.join(HERE, "geometry_vs_sheet.json")))
E = html.escape
REPORT = "https://claude.ai/artifact/1ZGWmdUZyFepc1gGMdCkok"

LOCKS = ("CATWALK", "STANDARD", "STEEP")
LOCK_LBL = {"CATWALK": "Catwalk 0°", "STANDARD": "Standard 35°", "STEEP": "Steep 49.4°"}
TOP = {  # measured heights above ground (mm), rig law + Blender
    "SINGLE_CATWALK": "Deck +150", "SINGLE_STANDARD": "Top tread +1,050 · landing +1,225",
    "SINGLE_STEEP": "Top tread +1,369", "SINGLE_BAR": "Hooks on bar +1,072 · cabin sill +1,225",
    "DOUBLE_CATWALK": "Deck +150", "DOUBLE_STANDARD": "Top tread +2,097", "DOUBLE_STEEP": "Top tread +2,755",
    "WIDE_CATWALK_FULL": "Deck +150", "WIDE_CATWALK_MINI": "Deck +150",
    "WIDE_STANDARD": "Top tread +1,050 · landing +1,225", "WIDE_STEEP": "Top tread +1,369",
}
NAME = {
    "SINGLE_CATWALK": "Catwalk", "SINGLE_STANDARD": "Standard stair", "SINGLE_STEEP": "Steep steps",
    "SINGLE_BAR": "Stair hooked to cabin bar", "DOUBLE_CATWALK": "Double catwalk", "DOUBLE_STANDARD": "Double stair",
    "DOUBLE_STEEP": "Double steep", "WIDE_CATWALK_FULL": "Wide catwalk · full handrail",
    "WIDE_CATWALK_MINI": "Wide catwalk · mini handrail", "WIDE_STANDARD": "Wide stair", "WIDE_STEEP": "Wide steep",
}
GROUP = {"Single": "1 unit", "Double (end-to-end)": "2 units end-to-end", "Wide (side-by-side)": "2 units side-by-side, rails nested"}
ORDER = ["SINGLE_CATWALK", "SINGLE_STANDARD", "SINGLE_STEEP", "SINGLE_BAR", "DOUBLE_CATWALK", "DOUBLE_STANDARD",
         "DOUBLE_STEEP", "WIDE_CATWALK_FULL", "WIDE_CATWALK_MINI", "WIDE_STANDARD", "WIDE_STEEP"]
ST = {s["key"]: s for s in R["states"]}


def n(x, d=0):
    return f"{x:,.{d}f}"


def chip(kind, text):
    return f'<span class="chip {kind}">{E(text)}</span>'


def verdict(text):
    t = text.upper()
    if "FAIL" in t and "PASS" in t:
        return "warn", "Partial"
    if "FAIL" in t or "BELOW" in t:
        return "fail", "Fail"
    if "PASS" in t:
        return "pass", "Pass"
    return "warn", "Specify"


# ----------------------------------------------------------------- configuration cards + rating table
cards, rate_rows = [], []
for k in ORDER:
    s = ST[k]
    c = s["candidates"]
    strength = min(v for kk, v in c.items() if "SLS" not in kk)
    sls = c["side girder SLS L/250"]
    gov = min(c, key=c.get)
    cards.append(f"""
      <figure class="cfg">
        <img src="img/{k}.jpg" alt="{E(NAME[k])} configuration" loading="lazy" width="1200" height="750">
        <figcaption>
          <div class="cfg-top"><b>{E(NAME[k])}</b><span class="mono dim">{E(GROUP[s['group']])}</span></div>
          <dl class="kv">
            <div><dt>L × W × H</dt><dd class="mono">{n(s['L_mm'])} × {n(s['W_mm'])} × {n(s['H_mm'])}</dd></div>
            <div><dt>Pitch</dt><dd class="mono">{s['deg']:g}°</dd></div>
            <div><dt>Height</dt><dd class="mono">{E(TOP[k])}</dd></div>
            <div><dt>Mass</dt><dd class="mono">{n(s['mass_kg'], 1)} kg</dd></div>
          </dl>
        </figcaption>
      </figure>""")
    rate_rows.append(f"""
        <tr><th scope="row">{E(NAME[k])}</th>
          <td class="num">{n(strength, 2)}</td><td class="num">{n(sls, 2)}</td>
          <td class="num strong">{n(min(strength, sls), 2)}</td>
          <td>{E(gov)}</td><td class="num">{chip('fail', f'{7.5 / min(strength, sls):.1f}× short') if min(strength, sls) > 0 else ''}</td></tr>""")

# ----------------------------------------------------------------- performance table per lock
g = R["girder"]; t = R["tread"]; b = R["barrier"]; h = R["hooks"]
GR = "R (25 wide, governs)"


def row(label, vals, unit, req=None, better="high", note=""):
    tds = []
    for v in vals:
        if v is None:
            tds.append('<td class="num dim">—</td>')
            continue
        ok = None if req is None else (v >= req if better == "high" else v <= req)
        cls = "" if ok is None else (" ok" if ok else " bad")
        tds.append(f'<td class="num{cls}">{v if isinstance(v, str) else n(v, 2 if v < 100 else 0)}</td>')
    rq = "" if req is None else (f"≥ {req:g}" if better == "high" else f"≤ {req:g}")
    return f'<tr><th scope="row">{E(label)}<span class="note">{E(note)}</span></th>{"".join(tds)}<td class="unit">{E(unit)}</td><td class="num req">{rq}</td></tr>'


perf = "".join([
    row("Side girder strength rating (ULS)", [g[L][GR]["uls_rating_kN_m2"] for L in LOCKS], "kN/m²", 7.5,
        note="locked Vierendeel FE, 1.35G + 1.5Q, load patterns"),
    row("Side girder deflection rating (L/250)", [g[L][GR]["sls_rating_kN_m2"] for L in LOCKS], "kN/m²", 7.5,
        note="7.3 mm on the 1,831 mm span"),
    row("Girder deflection, one person 1 kN", [g[L]["person_1kN_defl_mm"] for L in LOCKS], "mm", 10, "low"),
    row("Tread UDL rating", [t["udl_rating"][L]["rating_kN_m2"] for L in LOCKS], "kN/m²", 7.5,
        note="280 × 50 plank on 1,241 mm span"),
    row("Tread point rating (200 × 200 patch)", [t["point_rating_kN"]] * 3, "kN", 4.0),
    row("Top hook capacity", [None, h["STANDARD"]["capacity_kN"], h["STEEP"]["capacity_kN"]], "kN",
        note="5 mm plate, 11.9 mm throat"),
    row("Top hook demand at 7.5 kN/m²", [None, h["STANDARD"]["demand_at_7_5_kN"], h["STEEP"]["demand_at_7_5_kN"]], "kN"),
    row("Barrier line-load rating (top rail)", [b[L]["line_rating_kN_m"] for L in LOCKS], "kN/m", 3.0,
        note="12 posts 25 × 10 flat, weak axis"),
    row("Post point-load rating (top)", [b[L]["post_point_rating_kN"] for L in LOCKS], "kN", 1.5),
    row("Vertical natural frequency", [R["frequency"]["catwalk_Hz"], R["frequency"]["standard_Hz"], None], "Hz", 6.0,
        note="self weight, locked"),
])

# ----------------------------------------------------------------- compliance (loads) vs Aug-2026 sheet
cat = R["catwalk_overturning"]
loads = [
    ("R113", "Crowd UDL 7.5 kN/m² on stairs and platforms",
     f"{g['CATWALK'][GR]['uls_rating_kN_m2']:.2f} / {g['STANDARD'][GR]['uls_rating_kN_m2']:.2f} / {g['STEEP'][GR]['uls_rating_kN_m2']:.2f} kN/m²", "fail", "Fail"),
    ("R114", "Tread point load 4.0 kN on 200 × 200", f"{t['point_rating_kN']:.2f} kN", "pass", "Pass"),
    ("R115", "Deflection ≤ L/250 under crowd", "catwalk 0.14, stair 2.36 kN/m² before L/250", "fail", "Fail"),
    ("R115", "< 10 mm under a single person", f"catwalk {g['CATWALK']['person_1kN_defl_mm']:.1f} mm, stair {g['STANDARD']['person_1kN_defl_mm']:.1f} mm", "warn", "Partial"),
    ("R142", "Barrier line load 3.0 kN/m", f"{b['STANDARD']['line_rating_kN_m']:.2f} kN/m", "fail", "Fail"),
    ("R179", "Post point load 1.5 kN", f"{b['STANDARD']['post_point_rating_kN']:.2f} kN", "fail", "Fail"),
    ("R178", "Top rail vertical 1.0 kN/m", "25 × 25 rail over 305 mm post spacing", "pass", "Pass"),
    ("R177", "Vertical f₁ ≥ 6 Hz", f"{R['frequency']['catwalk_Hz']:.1f} Hz catwalk, {R['frequency']['standard_Hz']:.1f} Hz stair", "pass", "Pass"),
    ("R40", "Overturning FoS ≥ 1.5 (free-standing catwalk)", f"FoS {cat['FoS']:.2f} → {cat['ballast_or_anchor_kg']:,} kg ballast or anchors", "fail", "Fail"),
    ("R61", "Top hook, stair on bar or double joint", f"{h['STANDARD']['capacity_kN']:.2f} kN vs {h['STANDARD']['demand_at_7_5_kN']:.2f} kN", "fail", "Fail"),
    ("R51", "End-to-end joint", "hooks cannot carry the joint moment", "fail", "Trestle"),
    ("—", "Unlocked frame (handrails out)", "parallelogram mechanism", "warn", "Lock first"),
]
load_rows = "".join(f'<tr><td class="mono ref">{E(r)}</td><td>{E(req)}</td><td class="mono">{E(val)}</td><td>{chip(k, lab)}</td></tr>'
                    for r, req, val, k, lab in loads)
geo_rows = []
for ref, req, drawn, txt in GEO:
    k, lab = verdict(txt)
    geo_rows.append(f'<tr><td class="mono ref">{E(ref)}</td><td>{E(req)}</td><td class="mono">{E(drawn)}</td>'
                    f'<td>{chip(k, lab)}<span class="note">{E(txt)}</span></td></tr>')
n_fail = sum(1 for x in loads if x[3] == "fail") + sum(1 for x in GEO if verdict(x[3])[0] == "fail")
n_pass = sum(1 for x in loads if x[3] == "pass") + sum(1 for x in GEO if verdict(x[3])[0] == "pass")
n_part = len(loads) + len(GEO) - n_fail - n_pass

# ----------------------------------------------------------------- mass bars
mb = R["mass_breakdown"]
tot = mb["TOTAL"]
MB_LBL = {"treads 6x": "Treads 6×", "guide bars 4x": "Guide bars 4×", "axles 2x": "Axles 2×",
          "posts 12x1000": "Handrail posts 12×", "top posts 12x100": "Top posts 12×",
          "bottom minis 12x~165": "Lock pins (minis) 12×", "guardrails 2x": "Guardrails 2×",
          "cyan handrails 2x": "Handrails 2×", "rail brackets 12x": "Rail brackets 12×",
          "hooks/connectors/brackets (lump)": "Hooks, connectors"}
mass_rows = "".join(
    f'<div class="mrow"><span>{E(MB_LBL.get(k, k))}</span><span class="bar"><i style="width:{v / mb["treads 6x"] * 100:.1f}%"></i></span>'
    f'<span class="mono">{v:.2f}</span></div>'
    for k, v in sorted(mb.items(), key=lambda kv: -kv[1]) if k != "TOTAL")

DETAILS = [
    ("detail_pole_insert", "Locking",
     "The guide bars and treads form a parallelogram that folds freely. Dropping the handrail in pushes its bottom minis "
     "through both guide bars; from then on each side acts as a locked Vierendeel girder. Unlocked, it is a mechanism: "
     "handrails go in before anyone steps on."),
    ("detail_side_join", "Side-by-side join: nested rails",
     "The left guide rails are 35 mm U-channels (5 mm walls, 25 mm slot, open at the top and both ends); the right rails are "
     "25 mm inverted channels. Unit B slides lengthwise until its right rails sit inside unit A's left channels, a zero-clearance "
     "fit. One handrail then drops its lock pins through both nested rails and locks the two units together. Pitch 1,241 mm; "
     "tread ends 5 mm apart over the join. As modelled, both units' axle tubes run into the join and overlap by 64 mm: "
     "one must stop short, or act as a pin in the other's bore (to confirm on the drawings)."),
    ("detail_end_hook", "End-to-end join",
     "The lower guide plates of the upper unit hook over the top axle of the lower unit. Pitch 1,825 mm along the slope. "
     "The hooks cannot carry the joint moment: a trestle under every joint is required."),
    ("detail_bar_cabin", "Hooked to a cabin",
     "In the bar configuration the top axle position hooks onto a fixed bar below the door sill. Landing = sill = +1,225 mm, "
     "one riser above the top tread. Shown on the toilet cabin from the IFC, packed 218 mm."),
    ("detail_fold_rails", "Folding",
     "Changing state slides the guide bars along the tread pins (123 mm at catwalk → 177 mm at steep); tread pitch "
     "along the frame stays 305.2 mm in every state."),
    ("detail_lift_out", "Handrail removal",
     "Lifting the handrail pulls the minis out of the guide bars (first 150 mm), which frees the steps to fold. Top posts pivot "
     "on the guardrail so the poles stay plumb in every state."),
]
detail_html = "".join(f"""
      <figure class="det">
        <img src="img/{f}.jpg" alt="{E(ttl)} detail" loading="lazy" width="1200" height="675">
        <figcaption><b>{E(ttl)}</b><p>{E(txt)}</p></figcaption>
      </figure>""" for f, ttl, txt in DETAILS)

page = f"""<title>Folding Stair Datasheet</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root {{
  --paper:#EFF2F2; --surface:#FFFFFF; --ink:#15202A; --ink2:#4B5966; --rule:#D3DADE; --soft:#E6EBED;
  --accent:#1E5A86; --accentbg:#E1ECF4;
  --pass:#2F7A4F; --passbg:#E2F1E7; --fail:#B42318; --failbg:#FBE3E0; --warn:#9A620E; --warnbg:#FBEFD8;
  --display:"Barlow Semi Condensed","Arial Narrow",system-ui,sans-serif;
  --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"Cascadia Mono",Consolas,monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --paper:#0E151B; --surface:#152029; --ink:#E3E9ED; --ink2:#9DACB8; --rule:#27353F; --soft:#1B2833;
    --accent:#7DB7E3; --accentbg:#16283A;
    --pass:#6CC790; --passbg:#17301F; --fail:#FF8C80; --failbg:#3A1B18; --warn:#E6B45A; --warnbg:#382B12; color-scheme:dark;
  }}
}}
:root[data-theme="dark"] {{
  --paper:#0E151B; --surface:#152029; --ink:#E3E9ED; --ink2:#9DACB8; --rule:#27353F; --soft:#1B2833;
  --accent:#7DB7E3; --accentbg:#16283A;
  --pass:#6CC790; --passbg:#17301F; --fail:#FF8C80; --failbg:#3A1B18; --warn:#E6B45A; --warnbg:#382B12; color-scheme:dark;
}}
* {{ box-sizing:border-box; }}
body {{ background:var(--paper); color:var(--ink); font:15px/1.55 var(--body); margin:0; padding-inline:16px; padding-block:28px 64px; }}
.sheet {{ max-width:1180px; margin:0 auto; display:grid; gap:34px; }}
h1,h2,h3 {{ font-family:var(--display); letter-spacing:.01em; text-wrap:balance; margin:0; }}
h1 {{ font-size:clamp(34px,5vw,54px); font-weight:700; line-height:1.02; }}
h2 {{ font-size:26px; font-weight:600; }}
p {{ margin:0; max-width:70ch; }}
a {{ color:var(--accent); }}
a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.mono {{ font-family:var(--mono); font-variant-numeric:tabular-nums; }}
.dim {{ color:var(--ink2); }}
.eyebrow {{ font:600 12px/1 var(--mono); letter-spacing:.12em; text-transform:uppercase; color:var(--accent); }}
/* document control strip */
.control {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); border:1px solid var(--rule); background:var(--surface); }}
.control div {{ padding:10px 14px; border-right:1px solid var(--rule); display:grid; gap:3px; }}
.control div:last-child {{ border-right:0; }}
.control span {{ font:500 11px/1 var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--ink2); }}
.control b {{ font:500 13.5px/1.3 var(--mono); }}
.control .status b {{ color:var(--fail); }}
header.title {{ display:grid; gap:14px; }}
header.title p {{ color:var(--ink2); font-size:16.5px; }}
/* section frame: label column + content */
section {{ display:grid; grid-template-columns:210px 1fr; gap:10px 34px; border-top:2px solid var(--ink); padding-top:14px; }}
section > .lab {{ display:grid; align-content:start; gap:6px; }}
section > .lab p {{ color:var(--ink2); font-size:13.5px; }}
section > .body {{ display:grid; gap:18px; min-width:0; }}
@media (max-width: 860px) {{ section {{ grid-template-columns:1fr; }} }}
/* overview */
.hero {{ display:grid; grid-template-columns:minmax(0,1.55fr) minmax(0,1fr); gap:18px; align-items:start; }}
.hero img {{ width:100%; height:auto; display:block; border:1px solid var(--rule); }}
.figs {{ display:grid; grid-template-columns:1fr 1fr; border:1px solid var(--rule); background:var(--surface); }}
.figs div {{ padding:12px 14px; border-bottom:1px solid var(--rule); display:grid; gap:2px; min-width:0; overflow-wrap:anywhere; }}
.figs div:nth-child(odd) {{ border-right:1px solid var(--rule); }}
.figs div:nth-last-child(-n+2) {{ border-bottom:0; }}
.figs span {{ font-size:12.5px; color:var(--ink2); }}
.figs b {{ font:600 25px/1.1 var(--display); font-variant-numeric:tabular-nums; }}
.figs b small {{ font:500 13px var(--mono); color:var(--ink2); margin-left:3px; }}
.figs .bad b {{ color:var(--fail); }}
@media (max-width: 860px) {{ .hero {{ grid-template-columns:1fr; }} }}
/* configuration gallery */
.gallery {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:14px; }}
.cfg {{ margin:0; background:var(--surface); border:1px solid var(--rule); display:grid; grid-template-rows:auto 1fr; }}
.cfg img {{ width:100%; height:auto; aspect-ratio:16/10; object-fit:cover; display:block; border-bottom:1px solid var(--rule); }}
.cfg figcaption {{ padding:10px 12px 12px; display:grid; gap:8px; }}
.cfg-top {{ display:grid; gap:1px; }}
.cfg-top b {{ font:600 17px/1.2 var(--display); }}
.cfg-top span {{ font-size:12px; }}
.kv {{ margin:0; display:grid; gap:3px; font-size:12.5px; }}
.kv div {{ display:grid; grid-template-columns:78px 1fr; gap:8px; }}
.kv dt {{ color:var(--ink2); }}
.kv dd {{ margin:0; }}
/* tables */
.tw {{ overflow-x:auto; border:1px solid var(--rule); background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
th, td {{ padding:8px 12px; border-bottom:1px solid var(--rule); text-align:left; vertical-align:top; }}
thead th {{ font:600 11.5px/1.2 var(--mono); letter-spacing:.06em; text-transform:uppercase; color:var(--ink2); background:var(--soft); white-space:nowrap; }}
tbody tr:last-child th, tbody tr:last-child td {{ border-bottom:0; }}
tbody th {{ font-weight:500; }}
td.num, th.num {{ text-align:right; font-family:var(--mono); font-variant-numeric:tabular-nums; white-space:nowrap; }}
td.ok {{ color:var(--pass); }} td.bad {{ color:var(--fail); font-weight:500; }}
td.strong {{ font-weight:600; }}
td.unit {{ color:var(--ink2); font-family:var(--mono); font-size:12.5px; white-space:nowrap; }}
td.req {{ color:var(--ink2); }}
td.ref {{ color:var(--ink2); white-space:nowrap; }}
.note {{ display:block; color:var(--ink2); font-size:12px; font-weight:400; margin-top:2px; }}
.chip {{ display:inline-block; font:600 11px/1 var(--mono); letter-spacing:.05em; text-transform:uppercase; padding:4px 7px; border-radius:3px; white-space:nowrap; }}
.chip.pass {{ color:var(--pass); background:var(--passbg); }}
.chip.fail {{ color:var(--fail); background:var(--failbg); }}
.chip.warn {{ color:var(--warn); background:var(--warnbg); }}
.tally {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; font-size:13.5px; color:var(--ink2); }}
/* mass */
.split {{ display:grid; grid-template-columns:1.2fr 1fr; gap:18px; align-items:start; }}
@media (max-width: 860px) {{ .split {{ grid-template-columns:1fr; }} }}
.mass {{ background:var(--surface); border:1px solid var(--rule); padding:12px 14px; display:grid; gap:7px; font-size:13px; }}
.mrow {{ display:grid; grid-template-columns:150px 1fr 48px; gap:10px; align-items:center; }}
.mrow .bar {{ height:9px; background:var(--soft); }}
.mrow .bar i {{ display:block; height:100%; background:var(--accent); }}
.mrow .mono {{ text-align:right; }}
.mtot {{ border-top:1px solid var(--rule); padding-top:7px; display:flex; justify-content:space-between; font-weight:600; }}
.matl {{ background:var(--accentbg); border:1px solid var(--rule); padding:12px 14px; display:grid; gap:6px; font-size:13.5px; }}
.matl b {{ font:600 17px var(--display); }}
/* details */
.details {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:14px; }}
.det {{ margin:0; background:var(--surface); border:1px solid var(--rule); }}
.det img {{ width:100%; height:auto; display:block; border-bottom:1px solid var(--rule); }}
.det figcaption {{ padding:10px 12px 12px; display:grid; gap:4px; font-size:13.5px; }}
.det b {{ font:600 17px var(--display); }}
.det p {{ color:var(--ink2); }}
/* conditions */
.cond {{ margin:0; padding:0; list-style:none; display:grid; gap:8px; }}
.cond li {{ padding:10px 14px; background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--fail); }}
.cond li.info {{ border-left-color:var(--accent); }}
.next {{ background:var(--surface); border:1px dashed var(--ink2); padding:14px 16px; display:grid; gap:6px; }}
.next b {{ font:600 19px var(--display); }}
footer {{ color:var(--ink2); font-size:12.5px; border-top:1px solid var(--rule); padding-top:12px; display:grid; gap:4px; }}
</style>

<main class="sheet">
  <div class="control" role="group" aria-label="Document control">
    <div><span>Document</span><b>DS-FMS-ASIS</b></div>
    <div><span>Revision</span><b>A · 23 Sep 2026</b></div>
    <div><span>Source model</span><b>IFC 22-09-2026</b></div>
    <div><span>Material</span><b>EN AW-6082-T6</b></div>
    <div class="status"><span>Status</span><b>As-is · not rated for events</b></div>
  </div>

  <header class="title">
    <div class="eyebrow">Technical datasheet · current design as modelled</div>
    <h1>Folding modular stair unit</h1>
    <p>One aluminium unit that folds from a flat catwalk to a 35° stair or a 49.4° step by sliding its guide bars on the tread pins,
       and locks when the handrails drop in. Two units join end-to-end, or side-by-side with the right rails nested inside the neighbour’s left channels, for eleven configurations.
       All values below are for the design exactly as modelled, rated against the Aug-2026 events compliance sheet.</p>
  </header>

  <section id="overview">
    <div class="lab"><h2>Overview</h2><p>Per unit unless stated.</p></div>
    <div class="body">
      <div class="hero">
        <img src="img/SINGLE_BAR.jpg" alt="Standard stair hooked to the cabin door" width="1200" height="750">
        <div class="figs">
          <div><span>Mass per unit</span><b>{tot:.1f}<small>kg</small></b></div>
          <div><span>Configurations</span><b>11<small>from 1 or 2 units</small></b></div>
          <div><span>Unit width</span><b>1,305<small>mm outside</small></b></div>
          <div><span>Clear width</span><b>1,023<small>mm between handrails</small></b></div>
          <div><span>Treads</span><b>6<small>× 280 × 1,236</small></b></div>
          <div><span>Stair pitch</span><b>35°<small>/ 49.4° steep</small></b></div>
          <div class="bad"><span>Rated crowd load, standard stair</span><b>{g['STANDARD'][GR]['uls_rating_kN_m2']:.2f}<small>kN/m² (7.5 required)</small></b></div>
          <div class="bad"><span>Rated barrier line load</span><b>{b['STANDARD']['line_rating_kN_m']:.2f}<small>kN/m (3.0 required)</small></b></div>
        </div>
      </div>
    </div>
  </section>

  <section id="configurations">
    <div class="lab"><h2>Configurations</h2><p>Overall dimensions in mm, measured on the rig with handrails inserted. Height is ground to the top of the handrail.</p></div>
    <div class="body">
      <div class="gallery">{''.join(cards)}</div>
    </div>
  </section>

  <section id="ratings">
    <div class="lab"><h2>Load rating by configuration</h2><p>Largest characteristic uniformly distributed load (kN/m²) that keeps every member check ≤ 1.0. Double configurations assume a trestle under the joint.</p></div>
    <div class="body">
      <div class="tw"><table>
        <thead><tr><th>Configuration</th><th class="num">Strength</th><th class="num">Deflection L/250</th><th class="num">Rated UDL</th><th>Governs</th><th class="num">vs 7.5 kN/m²</th></tr></thead>
        <tbody>{''.join(rate_rows)}</tbody>
      </table></div>
    </div>
  </section>

  <section id="geometry">
    <div class="lab"><h2>Step geometry</h2><p>Rig law: tread pitch 305.2 mm along the frame in every state; frame span 1,831 mm axle to axle.</p></div>
    <div class="body">
      <div class="tw"><table>
        <thead><tr><th></th><th class="num">Catwalk 0°</th><th class="num">Standard 35°</th><th class="num">Steep 49.4°</th><th>Unit</th></tr></thead>
        <tbody>
          <tr><th scope="row">Rise per step</th><td class="num">—</td><td class="num">175</td><td class="num">232 (first 211)</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Going</th><td class="num">305 (tread pitch)</td><td class="num">250</td><td class="num">199</td><td class="unit">mm</td></tr>
          <tr><th scope="row">2 × rise + going</th><td class="num">—</td><td class="num">600</td><td class="num">663</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Deck / top tread above ground</th><td class="num">150</td><td class="num">1,050</td><td class="num">1,369</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Landing level (one riser above top tread)</th><td class="num">—</td><td class="num">1,225</td><td class="num">1,601</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Top rail above pitch line / deck</th><td class="num">1,111</td><td class="num">1,127</td><td class="num">1,162</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Handrail above pitch line / deck</th><td class="num">1,000</td><td class="num">1,012</td><td class="num">1,018</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Open riser gap</th><td class="num">—</td><td class="num">125</td><td class="num">182</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Gap between treads</th><td class="num">25.2</td><td class="num">—</td><td class="num">—</td><td class="unit">mm</td></tr>
          <tr><th scope="row">Unit pitch: side-by-side / end-to-end</th><td class="num" colspan="3">1,241 nested / 1,825 along the slope</td><td class="unit">mm</td></tr>
        </tbody>
      </table></div>
    </div>
  </section>

  <section id="components">
    <div class="lab"><h2>Components &amp; material</h2><p>Sections measured from the CAD mesh; masses at 2,700 kg/m³.</p></div>
    <div class="body">
      <div class="tw"><table>
        <thead><tr><th>Component</th><th>Qty</th><th>Section as modelled</th><th class="num">A mm²</th><th class="num">I mm⁴</th></tr></thead>
        <tbody>
          <tr><th scope="row">Tread</th><td class="mono">6</td><td>Extruded plank 280 × 50, 1,236 long</td><td class="num">2,125</td><td class="num">566,862</td></tr>
          <tr><th scope="row">Guide bar, right upper / lower</th><td class="mono">1 + 1</td><td>25 wide (female plate side)</td><td class="num">275 / 275</td><td class="num">9,878 / 7,562</td></tr>
          <tr><th scope="row">Guide bar, left upper / lower</th><td class="mono">1 + 1</td><td>35 wide (male sandwich side)</td><td class="num">526 / 314</td><td class="num">24,959 / 16,156</td></tr>
          <tr><th scope="row">Axle</th><td class="mono">2</td><td>Tube Ø25.2 × 2.74, 1,305 long, 26 mm pin each side</td><td class="num">194</td><td class="num">12,438</td></tr>
          <tr><th scope="row">Handrail post</th><td class="mono">12</td><td>Flat 25 × 10, 1,000 long (weak axis carries barrier load)</td><td class="num">250</td><td class="num">2,089</td></tr>
          <tr><th scope="row">Top post / lock pin (mini)</th><td class="mono">12 + 12</td><td>Flat 25 × 10, 100 / ~165 long</td><td class="num">250</td><td class="num">2,089</td></tr>
          <tr><th scope="row">Guardrail</th><td class="mono">2</td><td>25 × 25 hollow, 1,726 long</td><td class="num">325</td><td class="num">26,887</td></tr>
          <tr><th scope="row">Handrail</th><td class="mono">2</td><td>25 × 25 solid, 1,726 long</td><td class="num">625</td><td class="num">32,544</td></tr>
          <tr><th scope="row">Top hook</th><td class="mono">1 per side</td><td>5 mm plate, 11.9 mm minimum throat</td><td class="num">—</td><td class="num">—</td></tr>
        </tbody>
      </table></div>
      <div class="split">
        <div class="mass">{mass_rows}<div class="mtot"><span>Total per unit</span><span class="mono">{tot:.1f} kg</span></div></div>
        <div class="matl">
          <span class="eyebrow">Material, all parts</span>
          <b>Aluminium EN AW-6082-T6</b>
          <span class="mono">f0 260 MPa (t ≤ 5) · 250 MPa (t &gt; 5)<br>fu 310 / 290 MPa · E 70 GPa · G 27 GPa<br>ρ 2,700 kg/m³ · γM1 1.10 · α 23×10⁻⁶ /K</span>
          <span>Assigned to all 648 staircase elements in <span class="mono">final STEP LADDER 22-9-2026 - ALUMINIUM.ifc</span>, with property sets and a metal surface style.</span>
        </div>
      </div>
    </div>
  </section>

  <section id="performance">
    <div class="lab"><h2>Structural performance</h2><p>EN AW-6082-T6, EN 1990 factors 1.35G + 1.5Q, EN 1999-1-1. Values below the requirement are shown in red.</p></div>
    <div class="body">
      <div class="tw"><table>
        <thead><tr><th>Check</th><th class="num">Catwalk</th><th class="num">Standard</th><th class="num">Steep</th><th>Unit</th><th class="num">Required</th></tr></thead>
        <tbody>{perf}</tbody>
      </table></div>
      <p class="dim">Free-standing catwalk: overturning factor of safety {cat['FoS']:.2f} against 1.5, so it needs {cat['ballast_or_anchor_kg']:,} kg of ballast or ground anchors. Axle shear capacity {R['axle_shear_capacity_per_side_kN']:.1f} kN per side; lock-pin shear capacity {R['lock_pin_shear_capacity_kN']:.1f} kN.
      Hand calculation, FE and Blender rigid-body runs agree within 0.7 %.</p>
    </div>
  </section>

  <section id="compliance">
    <div class="lab"><h2>Compliance, Aug-2026 events sheet</h2><p>R-numbers are rows of the sheet.</p></div>
    <div class="body">
      <div class="tally">{chip('fail', f'{n_fail} fail')} {chip('warn', f'{n_part} partial or to specify')} {chip('pass', f'{n_pass} pass')}</div>
      <h3>Loads</h3>
      <div class="tw"><table>
        <thead><tr><th>Ref</th><th>Requirement</th><th>As-is</th><th>Result</th></tr></thead>
        <tbody>{load_rows}</tbody>
      </table></div>
      <h3>Geometry and detailing</h3>
      <div class="tw"><table>
        <thead><tr><th>Ref</th><th>Requirement</th><th>As drawn</th><th>Result</th></tr></thead>
        <tbody>{''.join(geo_rows)}</tbody>
      </table></div>
    </div>
  </section>

  <section id="connections">
    <div class="lab"><h2>Connections &amp; locking</h2><p>Close-ups from the storyline animation.</p></div>
    <div class="body"><div class="details">{detail_html}</div></div>
  </section>

  <section id="use">
    <div class="lab"><h2>Conditions of use</h2></div>
    <div class="body">
      <ul class="cond">
        <li>Not rated for public event use in any configuration. Its capacities are calculated, not type-tested, and fall well short of the Aug-2026 sheet.</li>
        <li>Insert the handrails, with every lock pin seated, before any load. With the handrails out the frame is a mechanism.</li>
        <li>Nobody may lean on or load the barriers: the top rail is rated at {b['STANDARD']['line_rating_kN_m']:.2f} kN/m against 3.0 required.</li>
        <li>Free-standing catwalks must be ballasted or anchored; double configurations need a trestle under the joint.</li>
        <li>Steep (49.4°) is a crew step-ladder only: pitch, going and riser are outside public stair limits.</li>
        <li class="info">A verified lightweight all-aluminium upgrade (69.4 kg, passes every Aug-2026 check) is set out part by part in the <a href="{REPORT}">load verdict report</a>.</li>
      </ul>
      <div class="next">
        <span class="eyebrow">Next issue</span>
        <b>DS-FMS-FINAL · final design</b>
        <p>Issued after the final design has been load-tested, in this same layout so the two sheets compare line by line.</p>
      </div>
    </div>
  </section>

  <footer>
    <span>Basis: v2/datasheet/asis_ratings.py (FE + hand calculation, same functions as the load test), measured sections from the rig, Aug-2026 events sheet (v2/spec/sheet_2026-09-23_events.txt).</span>
    <span>Model: STEP LADDER RIGGED3.blend · IFC: final STEP LADDER 22-9-2026 - ALUMINIUM.ifc · Load test: <a href="{REPORT}">Step Ladder Load Verdict</a>.</span>
  </footer>
</main>
"""
os.makedirs(os.path.join(HERE, "web"), exist_ok=True)
open(os.path.join(HERE, "web", "index.html"), "w", encoding="utf-8").write(page)
print("written", len(page), "chars", n_fail, n_part, n_pass)
