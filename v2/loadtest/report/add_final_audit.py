"""Adds the 25 Sep 2026 final-model audit to the load verdict report (step_ladder_load_verdict.html), between
FINAL-AUDIT markers (re-runnable). Numbers from final/final_results.json, the same source as DS-FMS-FINAL."""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "..", "..", "final", "final_results.json")))
AUD = {r["check"]: r for r in json.load(open(os.path.join(HERE, "..", "..", "audit", "tread_checks.json")))["rows"]}
PAGE = os.path.join(HERE, "step_ladder_load_verdict.html")
DATASHEET = "https://claude.ai/artifact/GLipbqMzpRje8YZFLYTeL7"
BRIEF = "https://claude.ai/artifact/Biz2ptYvZVvXxDctWsHCE5"
FD = 250 / 1.1

T = {r["check"]: r for r in R["tread"]["checks"]}
def tu(key): return next(r for k, r in T.items() if key in k)
def comp(item, start, base="slides"):
    return next(r for r in R["components"] if r["item"] == item and r["check"].startswith(start) and r["base"] == base)
t_front = tu("ULS 4 kN patch front, mid-span"); d_crowd = tu("Crowd 7.5 kN/m2: nosing"); d4f = tu("4 kN patch (front)")
latch = comp("Latch pins O2 (per pole)", "Vertical"); pin_m = comp("Tread pins O10 (with link force)", "Bending")
ax_b = comp("Base axle O25x2.5", "Bending", "held"); ax_bh = ax_b; hk_b = comp("Hook plate 10 mm (base)", "Throat", "held")
ENV = R["frame_envelopes"]["slides"]
poles = {r["ref"]: r["util"] for r in R["components"] if r["item"] == "Pole RHS 25x10x2" and r["base"] == "slides"}
rails_s = max(v["util"] for v in R["rails"]["sliding_base"].values())
ENVH = R["frame_envelopes"]["held"]; BOX = R.get("tread_box_check") or R["tread_box_check_superseded"]
aud_front = next(r for k, r in AUD.items() if "4 kN patch front, mid-span" in k and "Profile stress" in k)
aud_crowd = next(r for k, r in AUD.items() if "Crowd 7.5" in k)

def u(x): return f'<span class="u {"good" if x <= 1 else "bad"}">{x:.2f}</span>'
rows = [
    ("Handrail poles", "RHS 25 × 10 × 2", "1.5 kN post load (R179)", poles["R179"], "Solid 6082-T6 25 × 55 (tapered to 15 at the top), on the outside face of the rails, bolted to both"),
    ("Guide rails", "U 35 × 25 × 5 / inverted U 25 × 25 and 25 × 20", "Net section at the pin holes (R113)", rails_s, "About 65 deep with Ø20 pins (net W ≥ 2,900 mm³, 18 mm to every edge)"),
    ("Pole locking pegs", "Ø2 pegs on each pole (one piece with it), 2 per rail", "Rail-to-rail transfer (R78/R104)", latch["util"], "Ø12 pegs (they bend over 7.5 mm to the rail wall); add the upper pair; notches lined up"),
    ("Step pins", "Ø10, 6.75–14 mm lever", "Bending with the frame link force (R170)", pin_m["util"], "Ø20 6082-T6"),
    ("Steps", "Open J + L, grating front to back, no deck", "4 kN at the nosing (R114); sag L/250 (R115)", max(t_front["util"], d_crowd["util"]), "Closed box 280 × 50: 5 mm top, 3 mm bottom, 5 mm walls (FE 0.68)"),
    ("Base axle", "Ø25 × 2.5, hook 70 mm from the jack, drawn as two tubes", "Bending, base held (R147)", ax_b["util"], "One tube jack to jack (the kept tube stops 34 mm short): 48.3 × 4 scaffold tube, or jacks under the hooks with Ø30 × 3"),
    ("Hooks", "10 mm plate, ring ≈ 22 mm, lock not drawn", "Throat (R150); lock carries the base reaction", hk_b["util"], "Ring ≥ 39 mm on the ground (57.5 clamped); lock for up to 17.7 kN per hook"),
]
table = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td class=\"num\">{u(x)}</td><td>{e}</td></tr>" for a, b, c, x, e in rows)

SECTION = f"""<!-- FINAL-AUDIT -->
<section id="final-audit">
  <div class="eyebrow">Precise audit · 25 Sep 2026 final model</div>
  <h2>The final model, part by part</h2>
  <p>The 25 Sep model (<code>25.9.2026 final STEP LADDER-standard.ifc</code>, standard 35°) was measured part by part: 791 elements and 1,673 contacts. The steps were run as a shell FE that balances exactly, cross-checked by an independent thin-walled calculation within 12 %. Each side was run as a frame with every pin, hook and lock modelled. Results below take the worse of a sliding and a held base, since the hooks lock onto the axles.</p>
  <div class="keyfigs">
    <div><b class="num">≈ {7.5 / latch['util']:.1f} kN/m²</b><span>crowd the unit carries (7.5 needed); the Ø2 latch pins govern</span></div>
    <div><b class="num">{t_front['util']:.2f}×</b><span>4 kN at the front of a step ({t_front['value']:.0f} MPa)</span></div>
    <div><b class="num">{3.0 / poles['R142']:.2f} kN/m</b><span>barrier line load carried (3.0 needed)</span></div>
    <div><b class="num">{R['mass']['total_kg']:.1f} kg</b><span>per unit, measured sections</span></div>
  </div>
  <div class="tbl"><table class="changes">
    <thead><tr><th>Part</th><th>25 Sep model</th><th>Governing check</th><th>Util</th><th>Smallest that passes</th></tr></thead>
    <tbody>{table}</tbody>
  </table></div>
  <p class="callout"><b>Correction to this report.</b> The verdict above calls the treads “fine”. That treated the tread as a solid 280 × 50 plank. Measured part by part, the 22 Sep tread is an open J + L with a 5 mm deck. It fails 4 kN at the nosing ({aud_front['value']:.0f} MPa, {aud_front['util']:.2f}×) and L/250 under the crowd ({aud_crowd['value']:.1f} mm against 4.86). The 25 Sep model removed the deck, which made it worse: {t_front['value']:.0f} MPa and {d_crowd['value']:.1f} mm. Only closed sections pass. Re-run on 26 Sep with the load on the top plate (an earlier box check loaded the bottom plate by mistake): a 280 × 50 box with a 3 mm top, 2 mm bottom and walls and two 2 mm inner webs passes at 0.41 (0.82 with every seam welded), about 5.9 kg per step. Three step designs with drain holes pass (all 280 × 50): A, that thin box with holes punched top and bottom (lightest); B, the owner’s sketch, a 25 mm box added on top of the J + L; C, an open grating with 50 mm bars running along the step. Open 25 mm lattices fail, even with bars every 10 mm.</p>
  <p class="callout"><b>Base condition.</b> The hooks lock onto the axles, so the unit works anywhere between a base that slides (worst for the rails) and one the ground holds (worst for the supports). Held, each jack takes {ENVH['H_base'] / 1000:.1f} kN sideways, the top hook locks {ENVH['uplift_top'] / 1000:.1f} kN uplift, and the base axle reaches {ax_bh['util']:.1f}×. Both limits are checked; each part takes the worse. The steps are checked with their flats joined to the end plates, as confirmed.</p>
  <p>Full results: <a href="{DATASHEET}">datasheet DS-FMS-FINAL, Rev B</a>. What to draw: <a href="{BRIEF}#final-check">change brief, 25 Sep model check</a>. Source: <code>v2/final/final_results.json</code>.</p>
</section>
<!-- /FINAL-AUDIT -->
"""
BANNER = f"""<!-- FINAL-AUDIT-BANNER -->
<a class="banner" href="#final-audit">
  <b>Update 25 Sep 2026.</b> The final model has been audited part by part. It carries about <b class="num">{7.5 / latch['util']:.1f} kN/m²</b> of the 7.5 needed; the steps, fold lock, rails, pins and poles fail. This report's tread verdict is corrected below &darr;
</a>
<!-- /FINAL-AUDIT-BANNER -->
"""
s = open(PAGE, encoding="utf8").read()
s = re.sub(r"<!-- FINAL-AUDIT(-BANNER)? -->.*?<!-- /FINAL-AUDIT(-BANNER)? -->\n?", "", s, flags=re.S)
i = s.index('<a class="banner" href="#lightweight">')
s = s[:i] + BANNER + "\n" + s[i:]
j = s.index("<section>", s.index('<a class="banner" href="#lightweight">'))
s = s[:j] + SECTION + "\n" + s[j:]
open(PAGE, "w", encoding="utf8").write(s)
print("report updated", len(s))
