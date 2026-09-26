p = "build_brief.py"
s = open(p, encoding="utf-8").read()
blk = open("_changes_block_v3.py", encoding="utf-8").read()
a = s.index("CHANGES = [")
b = s.index('rows = "".join(')
s = s[:a] + blk + "\n" + s[b:]

# pole drawing (to scale, section across the stair)
anchor = "def hook_svg():"
poles = '''def poles_svg(t_full, t_pt):
    k = 3.0
    b = txt(10, 18, "NOW", "tag") + rect(30, 50, 25 * k, 10 * k, "old") + txt(30 + 12.5 * k, 50 + 10 * k + 22, "25 \\u00d7 10", "lbl", "middle")
    x = 230
    b += txt(x, 18, "CHANGE TO", "tag")
    for tt, cls, lab in ((t_pt, "new2", "point loads only"), (t_full, "new", "full crowd push")):
        if not tt:
            continue
        b += rect(x, 40, 25 * k, tt * k, cls) + txt(x + 12.5 * k, 40 + tt * k + 20, f"25 \\u00d7 {tt:g}", "lbl", "middle")
        b += txt(x + 12.5 * k, 40 + tt * k + 38, lab, "note" if cls == "new" else "note2", "middle")
        x += 200
    b += txt(610, 60, "\\u2195 people push this way", "lbl")
    b += txt(610, 80, "(across the stair)", "note2")
    h = 40 + max(t_full or 10, t_pt or 10) * k + 60
    return svg(820, h, b, "Handrail pole section: 25 x 10 now, thicker across the stair after")


'''
s = s.replace(anchor, poles + anchor, 1)

# figures: only markers for parts that still change
s = s.replace('("A", "overview", "Standard stair, right-hand side", {1: 1, 2: 2, 3: 2, 4: 4, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11}, {7, 8}),',
              '("A", "overview", "Standard stair, right-hand side", {1: 1, 2: 2, 3: 2, 4: 4, 6: 7, 9: 10}, set()),')
s = s.replace('("B", "post", "Bottom of a handrail post", {1: 4, 2: 5, 3: 2}, set()),',
              '("B", "post", "Bottom of a handrail pole: its lower end is the lock pin through the guide rails", {1: 4, 2: 4, 3: 2}, set()),')
s = s.replace('("D", "pin", "Centre handrail pin passing through both nested rails", {1: 12}, set()),',
              '("D", "pin", "Side by side: one handrail pole\\u2019s pin passes through both nested rails", {1: 4}, set()),')
s = s.replace('("F", "catwalk", "Flat catwalk seen from the side", {1: 11, 2: 11, 3: 11, 4: 2}, {3}),',
              '("F", "catwalk", "Flat catwalk seen from the side (the scaffold supports it)", {4: 2}, set()),')

# summary table: status column
s = s.replace('''rows = "".join(f'<tr><td class="mono"><a href="#c{n}">{n}</a></td><th scope="row">{E(p)}</th><td>{E(a)}</td><td class="strong">{E(b)}</td><td class="mono">{E(q)}</td></tr>'
               for n, p, a, b, q in TABLE)''',
              '''ST2 = {"change": ("pass", "Change"), "consider": ("part", "To consider"), "no": ("none", "No change"), "later": ("test", "Later")}
rows = "".join(f'<tr><td class="mono"><a href="#c{n}">{n}</a></td><th scope="row">{E(p)}</th><td>{E(a)}</td><td class="strong">{E(b)}</td>'
               f'<td><span class="st {ST2[q][0]}">{ST2[q][1]}</span></td></tr>' for n, p, a, b, q in TABLE)''')
s = s.replace("<thead><tr><th>#</th><th>Part</th><th>Now</th><th>Change to</th><th>Qty / unit</th></tr></thead>",
              "<thead><tr><th>#</th><th>Part</th><th>Now</th><th>Change to</th><th>Status</th></tr></thead>")

# intro + result box
s = s.replace('''<p>Thirteen shape and size changes that turn the current model into the lighter, event-rated version. Nothing folds or moves differently:
       the unit keeps its length, width, fold positions and every pin and axle hole. Everything stays aluminium. The sizes have already been
       checked by the load test, so they just need drawing as written. The numbers on the pictures match the numbered changes.</p>''',
              '''<p>The geometry changes that make the current model meet the event load sheet, updated with your decisions: five changes to draw
       (1, 2, 3, 4, 10), one to consider (7), and the rest decided as no change. Nothing folds or moves differently: the unit keeps its length,
       width, fold positions, rail shapes and every pin and axle hole. Everything stays aluminium. Sizes come from the load test; the numbers
       on the pictures match the numbered changes.</p>''')
s = s.replace('''      <div><span>Weight per unit</span><b><s>71.6</s>\\u2248 69 kg</b></div>''',
              '''      <div><span>Weight per unit</span><b><s>71.6</s>\\u2248 {W_NEW:.0f} kg</b></div>''')
s = s.replace("<div><span>Weight per unit</span><b><s>71.6</s>≈ 69 kg</b></div>",
              "<div><span>Weight per unit</span><b><s>71.6</s>≈ {W_NEW:.0f} kg</b></div>")
# notes section after the cards
s = s.replace('''  <section id="compliance">''', '''  <section id="decided">
    <h2>Decided: no drawing work</h2>
    <p>Your decisions on the other items, and what each one means against the sheet.</p>
    <div class="tw"><table>
      <thead><tr><th>#</th><th>Item</th><th>Decision</th><th>Against the sheet</th></tr></thead>
      <tbody>{notes_html}</tbody>
    </table></div>
  </section>

  <section id="compliance">''')
# decisions list refresh
a = s.index('<ul class="notmodel">')
b = s.index('</ul>', a) + len('</ul>')
s = s[:a] + '''<ul class="notmodel">
      <li><b>Finger trap while folding (R95).</b> The 20 mm gap between steps closes as the unit folds. Either fold only when nobody is on it, by trained crew (a written procedure), or make the steps 298 deep so the gap is 7 mm (+1.3 kg per unit).</li>
      <li><b>Scaffold support.</b> If the scaffold can support the flat catwalk under its middle, the rails in changes 2 and 3 stay much smaller than if it supports the ends only.</li>
      <li><b>Pole pins.</b> The pin section where each pole enters the rails is the weak point for the crowd push (see change 4); confirm the detail with the engineer, or give the edge its crowd barrier from the scaffold side.</li>
      <li><b>Viewing platforms (R142).</b> The barrier sizes are for 3.0 kN/m (people walking through). A catwalk where people stand and watch against the rail needs 5.0 kN/m.</li>
      <li><b>Engineer to check:</b> sideways crowd load and 10 % sway into the hooks and the scaffold (R116, R176); storm overturning with the scaffold ties (R181).</li>
      <li><b>Tests:</b> slip resistance of the step surface (R16), and a physical load test at 1.2\\u00d7 including class C edge protection at 35\\u00b0 (R166, R173).</li>
      <li><b>Steep 49.4\\u00b0</b> is for crew only (step-ladder use), not the public (R9).</li>
    </ul>''' + s[b:]
# css
s = s.replace(".whyload {{ display:grid;", ".tagc {{ font:600 11px/1 var(--mono); letter-spacing:.06em; text-transform:uppercase; color:var(--warn); background:var(--warnbg); padding:4px 7px; vertical-align:middle; margin-left:6px; }}\n"
              ".card.consider {{ border-style:dashed; }}\n.cnote {{ background:var(--warnbg); padding:10px 12px; font-size:14px; max-width:none; }}\n"
              ".st.none {{ color:var(--ink2); background:var(--soft); }}\n.whyload {{ display:grid;", 1)
# weight estimate
s = s.replace('figs_html = "".join(figure(*f) for f in FIGS)',
              'figs_html = "".join(figure(*f) for f in FIGS)\n'
              'W_NEW = 71.6 - 15.1 - 6.82 + ((R_MID or {}).get("mass_2bars_kg", 3.41) + (L_MID or {}).get("mass_2bars_kg", 3.41)) '
              '+ 12 * 25 * ((T_FULL or 10) - 10) * 1000 * 2.7e-6 + 0.3')
open(p, "w", encoding="utf-8").write(s)
print("brief v3 patched")
