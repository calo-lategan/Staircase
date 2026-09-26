"""Datasheet Rev C (27 Sep 2026): the current staircase only (25 Sep model as cleaned by the owner on 26 Sep, standard 35 deg).
Reuses the Rev B builder's calculations (v2/datasheet/build_datasheet_final.py) but publishes one document with no history:
no Rev A tab, no 'what changed' section, no correction notes, no old-model columns. Output: revc/web/datasheet.html"""
import os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "datasheet", "build_datasheet_final.py")
LINKS = json.load(open(os.path.join(HERE, "links.json"))) if os.path.exists(os.path.join(HERE, "links.json")) else {}
AC = json.load(open(os.path.join(HERE, "after_changes.json")))
code = open(SRC, encoding="utf8").read()
code = code[:code.index('out = os.path.join(HERE, "web", "index.html")')]          # build everything, write nothing
ns = {"__file__": SRC}
cwd = os.getcwd(); os.chdir(os.path.dirname(SRC))
exec(compile(code, SRC, "exec"), ns)
os.chdir(cwd)
F = ns["FINAL"]; head = ns["head"]; css = ns["EXTRA_CSS"]

def cut_section(html, sid):
    i = html.index(f'<section id="{sid}">'); j = html.index("</section>", i) + len("</section>")
    return html[:i] + html[j:]
def sub(a, b, html, count=1):
    if a not in html: raise SystemExit("NOT FOUND: " + a[:90])
    return html.replace(a, b, count)

F = sub('<div><span>Document</span><b>DS-FMS-FINAL</b></div>', '<div><span>Document</span><b>DS-FMS</b></div>', F)
F = sub('<div><span>Revision</span><b>B · 25 Sep 2026</b></div>', '<div><span>Revision</span><b>C · 27 Sep 2026</b></div>', F)
F = sub('<div><span>Source model</span><b>IFC 25-09-2026 · standard 35°</b></div>', '<div><span>Source model</span><b>25 Sep model, cleaned 26 Sep · 35°</b></div>', F)
F = sub('<div class="status"><span>Status</span><b>Final model · not rated for events</b></div>', '<div class="status"><span>Status</span><b>Current model · not rated for events</b></div>', F)
F = sub('<div class="eyebrow">Technical datasheet · final model as drawn · part-by-part audit</div>', '<div class="eyebrow">Technical datasheet · current staircase as drawn · Rev C</div>', F)
i = F.index('<p>Rev B covers the final model'); j = F.index("</p>", i) + 4
F = F[:i] + ('<p>This sheet rates the current staircase exactly as drawn: the 25 Sep model (<span class="mono">25.9.2026 final STEP LADDER-standard.ifc</span>) '
             'with the owner’s clean-up of 26 Sep, in the standard 35° state. Every part was measured from the model and checked against the Aug-2026 events sheet, '
             'with the load path traced part to part: shell FE for the steps, 2D frames for the sides with every pin, hook and lock, and EN 1999-1-1 checks for 6082-T6. '
             'The changes that make it pass are in the Rev C change list.</p>') + F[j:]
F = cut_section(F, "f-changes")
# tread section: drop history sentences
F = re.sub(r"<span>No shape that stays open and 25 mm deep passes:.*?</span>", '<span>Open shapes 25 mm deep don’t pass: a cut-out top sheet on the J + L, or a lattice cut from one plate (20 × 20 or finer), all fail the 4 kN point load and the sag limits.</span>', F, flags=re.S)
F = re.sub(r'<p class="dim">Flats joined against flats loose:.*?</p>', '<p class="dim">The flats are checked joined to the end plates, as decided. They make the grating bars pass, but they are themselves over-stressed, and the J and L still carry the span.</p>', F, flags=re.S)
F = re.sub(r" The Rev A model re-run the same way gives [^<]*?\.</p>", "</p>", F)
# compliance: drop the old-model column and its explanation
F = F.replace(" The last column is the Rev A (22 Sep) model re-checked by the same method.", "")
F = sub("<th>Result</th><th>22 Sep model, corrected</th></tr></thead>", "<th>Result</th></tr></thead>", F)
i = F.index('<section id="f-compliance">'); j = F.index("<h3>Geometry and detailing</h3>", i)
block = F[i:j]
def drop_last_cell(m):
    row = m.group(0); k = row.rfind("<td"); return row[:k] + "</tr>"
block = re.sub(r"<tr><td class=\"mono ref\">.*?</tr>", drop_last_cell, block, flags=re.S)
F = F[:i] + block + F[j:]
F = re.sub(r"<span>EN 1999-1-1 Table 3\.2b\. Rev A listed[^<]*</span>", "<span>EN 1999-1-1 Table 3.2b (thickness band t ≤ 5 mm for the extrusion walls).</span>", F)
# sizes table: rows that Rev C settles differently
F = re.sub(r'<td class="strong">net W ≥ 2,900 mm³ at the pin holes, or a mid support plus a proper lock</td><td>ULS crowd</td>',
           f'<td class="strong">About 70 deep, same widths and 5 mm walls: at least 20 mm of metal round every Ø20 hole (edge {AC["rails"]["edge_util_20mm"]:.2f}); net W about 7,200 mm³ against 2,900 needed ({AC["rails"]["util_net"]:.2f})</td><td>ULS crowd, pole push</td>', F)
F = re.sub(r'<tr><th scope="row">Right lower rail hole</th>.*?</tr>', '', F, flags=re.S)
F = F.replace("The rails then take ≈ 14 kN each way: fine with the 65 mm rails", f"The rails then take ≈ {AC['pole_fix']['F_kN']:.0f} kN each way: fine with the deeper rails ({AC['rails']['lateral_left']:.2f} left, {AC['rails']['lateral_right']:.2f} right)")
F = F.replace("on the outside face of the rails, bolted to both", "on the outside face of the rails: a strap and Ø12 cross-pin at the upper rail (no hole across the pole there), a Ø16 pin at the lower rail")
F = F.replace(">change brief</a>", ">change list</a>")
F = F.replace("+87 mm if the pitch line", "+87 mm if the pitch line")
F = F.replace("<td class=\"strong\">≤ 120</td><td>R7</td>", "<td class=\"strong\">≤ 120: a lip at least 5 mm down on the step’s front edge (35 mm gives the recommended 100)</td><td>R7</td>")
F = F.replace("Cleaned by the owner on 26 Sep: the second base (axle and jacks), one of each pair of axle tubes and 8 extra blocks on the right poles. Still drawn twice:",
              "Still drawn twice:")
# step design decided 27 Sep: A chosen, C the alternative (B not taken forward)
F = sub('<span class="eyebrow">Steps that pass, all with drain holes · FE-verified (27 Sep)</span>', '<span class="eyebrow">Step design · A chosen, C the alternative · both with drain holes, FE-verified</span>', F)
F = sub('<b>A · thin closed box:', '<b>A · chosen · thin closed box:', F)
F, n1 = re.subn(r'<b>B · owner’s sketch:.*?</span>', '', F, flags=re.S)
F, n2 = re.subn(r'<b>C · open grating turned the right way:[^<]*</b>', '<b>C · alternative · open grating: 3 × 50 bars along the step every 46 mm, 8 mm front bar, cross bars on top</b>', F)
_S = AC["steps"]
F, n3 = re.subn(r'Any of three, all 280 × 50 with drain holes:[^<]*', f'A thin closed box, 280 × 50 with drain holes: 3 top / 2 bottom / 2 walls + two 2 mm webs ({_S["A_extruded_6082"]["util"]:.2f}, {_S["A_extruded_6082"]["mass"]:.1f} kg). Alternative C: open grating, 3 × 50 bars along the step every 46 mm + 8 mm front bar, press-locked ({_S["C_grating_46_nosing8"]["util"]:.2f}, {_S["C_grating_46_nosing8"]["mass"]:.1f} kg)', F)
if (n1, n2, n3) != (1, 1, 1): raise SystemExit(f"step option patch counts {n1} {n2} {n3}")
# links to the Rev C set
cl = LINKS.get("changelist", "#"); lv = LINKS.get("verdict", "#"); mg = LINKS.get("manufacturing", "#")
F = F.replace('https://claude.ai/artifact/Biz2ptYvZVvXxDctWsHCE5', cl)
F = re.sub(r'Earlier load test: <a href="[^"]+">Step Ladder Load Verdict</a>\.', f'Rev C set: <a href="{lv}">load verdict</a> · <a href="{cl}">change list</a> · <a href="{mg}">manufacturing guide</a>.', F)
for bad in ("Rev A", "Rev B", "22 Sep model"):
    if bad in F: print("WARNING still contains", bad, "at", F.index(bad), F[F.index(bad) - 80:F.index(bad) + 60].replace("\n", " "))
page = head.replace("<title>Folding Stair Datasheet</title>", "<title>Stair Datasheet Rev C</title>") + css + "</style>\n" + F
os.makedirs(os.path.join(HERE, "web"), exist_ok=True)
open(os.path.join(HERE, "web", "datasheet.html"), "w", encoding="utf8").write(page)
print("datasheet Rev C", len(page))
