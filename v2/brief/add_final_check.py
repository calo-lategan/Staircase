"""Brief section "25 Sep model check: what's still needed" (F1-F9), rebuilt from the owner's answers of 26 Sep:
flats joined; hooks cut/bent as part of the rails and locked on the axles; second base removed; jacks on the ground or a
scaffold array; step pins have bushes, washers and a locking cap; the pole and its locking end are one piece with 4
pegs (2 per rail); poles to become solid; handrail padding (note only); top rail measured to 1.1 m from the step.
All numbers from v2/final JSON files (same source as the datasheet). Pictures: render_final_check_refs.py.
Rebuild: copy web/_brief_before_final_check.html over web/index.html, then run this."""
import json, math, os, re
import final_diagrams as D

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.join(HERE, "..", "final")
def J(n): return json.load(open(os.path.join(FIN, n)))
R = J("final_results.json"); BOX = J("tread_box2.json")
HAZ = J("tread_box2_haz.json") if os.path.exists(os.path.join(FIN, "tread_box2_haz.json")) else {}
LAT = J("tread_lattice.json"); BAR = J("barrier_path_check.json"); AX = J("axle_options.json")
GRT = J("tread_grating.json"); UBX = J("tread_ubox.json"); L10 = J("tread_lattice_l10.json") if os.path.exists(os.path.join(FIN, "tread_lattice_l10.json")) else {}
PAGE = os.path.join(HERE, "web", "index.html")
DATASHEET = "https://claude.ai/artifact/GLipbqMzpRje8YZFLYTeL7"
FD = 250 / 1.1

T = {r["check"]: r for r in R["tread"]["checks"]}
def tu(key): return next(r for k, r in T.items() if key in k)
def comp(item, start, base="slides"):
    return next(r for r in R["components"] if r["item"] == item and r["check"].startswith(start) and r["base"] == base)
ENV, ENVH = R["frame_envelopes"]["slides"], R["frame_envelopes"]["held"]
t_front = tu("ULS 4 kN patch front, mid-span"); d_crowd = tu("Crowd 7.5 kN/m2: nosing")
latch = comp("Latch pins O2 (per pole)", "Vertical"); pin_v = comp("Tread pins O10 (with link force)", "Shear"); pin_m = comp("Tread pins O10 (with link force)", "Bending")
hbr = comp("Handrail bracket 15x5 bent flat", "1.25")
poles = {r["ref"]: r["util"] for r in R["components"] if r["item"] == "Pole RHS 25x10x2" and r["base"] == "slides"}
brk25 = hbr["util"] * (5 * 15 ** 2 / 6) / (5 * 25 ** 2 / 6)
MK = json.load(open(os.path.join(HERE, "web", "img", "final", "f_markers.json")))

# ---------------------------------------------------------------- F1 options
def worst(opt):
    c = BOX[opt]["cases"]
    u = max(v["util"] for k, v in c.items() if k.startswith("ULS"))
    h = HAZ.get(opt, {}).get("util", {})
    return dict(u=u, sag4=abs(c["SLS 4 kN front, mid-span"]["uz_min"]), crowd=abs(c["SLS crowd"]["uz_min"]), person=abs(c["SLS person 1 kN at the nosing"]["uz_min"]),
                mass=BOX[opt]["mass_kg"], haz_bent=h.get("bent top U"), haz_all=h.get("welded corners"))
BOXW = {k: worst(k) for k in BOX}
ok = [k for k, v in BOXW.items() if v["u"] <= 0.85 and v["sag4"] <= 12.2 * 0.85 and v["crowd"] <= 4.86 * 0.85 and v["person"] <= 8.5
      and v["haz_bent"] is not None and v["haz_bent"] <= 0.9]
REC = min(ok, key=lambda k: BOXW[k]["mass"]) if ok else "B2 box 4 / 2 / 3, one mid web 3"
def _pass(c):
    return max(v["util"] for k, v in c.items() if k.startswith("ULS")) <= 0.9 and abs(c["SLS 4 kN front, mid-span"]["uz_min"]) <= 12.2 and abs(c["SLS crowd"]["uz_min"]) <= 4.86
GOK = [k for k, v in GRT.items() if _pass(v["cases"])]; GRC_K = min(GOK, key=lambda k: GRT[k]["mass_kg"]) if GOK else "G1 grating: bars 3 x 50 at 34 mm along the step"; GRC = GRT[GRC_K]
UOK = [k for k, v in UBX.items() if _pass(v["cases"])]; UBOX_K = min(UOK, key=lambda k: UBX[k]["mass_kg"]) if UOK else list(UBX)[0]; UBOX = UBX[UBOX_K]
rec = BOXW[REC]; rc = BOX[REC]["cfg"]
def lat(name):
    c = LAT[name]["cases"]
    return dict(u=max(v["vm"] for k, v in c.items() if k.startswith("ULS")) / FD, crowd=abs(c["SLS crowd 7.5 kN/m2"]["uz_min"]), sag4=abs(c["SLS 4 kN patch front, mid-span"]["uz_min"]))
L20 = lat("L20 lattice 20 x 20 (13 long bars 3 x 25)"); L40 = lat("L40 lattice 20 x 40 (7 long bars 3 x 25)")
STEP_NOW_KG = (775 * 1200 + 60 * 75 * 270 + 2 * 67.5 * 1177) * 2.7e-6 + 2 * (45 * 47.5 + 230 * 20) * 5 * 2.7e-6
def optname(k):
    cfg = BOX[k]["cfg"]; w = cfg.get("webs", ())
    return f"Closed box: {cfg['t_top']:g} top / {cfg['t_bot']:g} bottom / {cfg['t_wall']:g} walls" + (f", {len(w)} inner web{'s' if len(w) > 1 else ''} {cfg.get('t_web') or cfg['t_wall']:g}" if w else "")
f1_rows = [("Now: J + L + grating, flats joined", f"{t_front['util']:.2f}", f"{abs(R['tread']['cases']['SLS 4 kN patch front, mid-span']['lip']):.0f}", f"{d_crowd['value']:.1f}", "—", f"{STEP_NOW_KG:.1f}", False),
           ("Your idea: one thick sheet with the grating cut out, on the same J + L", "over 1.39", "over 21.9", "over 7.7", "—", "—", False),
           ("Your idea: cross lattice cut from one plate, 20 × 20", f"{L20['u']:.2f}", f"{L20['sag4']:.0f}", f"{L20['crowd']:.1f}", "—", f"{STEP_NOW_KG + LAT['L20 lattice 20 x 20 (13 long bars 3 x 25)']['mass_extra_kg'] - 0.43:.1f}", False),
           ("Your idea: cross lattice cut from one plate, 20 × 40", f"{L40['u']:.2f}", f"{L40['sag4']:.0f}", f"{L40['crowd']:.1f}", "—", f"{STEP_NOW_KG + LAT['L40 lattice 20 x 40 (7 long bars 3 x 25)']['mass_extra_kg'] - 0.43:.1f}", False)]
FDH = 125 / 1.1
def u_weld_box(cases):
    w = 0
    for cn, r in cases.items():
        if not cn.startswith("ULS"): continue
        for part, rec in r["by_part"].items():
            vm, pp, x = rec[0], rec[1], rec[2]
            if (pp in ("top plate", "mid plate") and (x <= 27.5 or x >= 252.5)) or pp in ("rear wall (J)", "front lip (L)"): w = max(w, vm / FDH)
    return w
def gsum(c):
    u = max(v["util"] for k, v in c.items() if k.startswith("ULS"))
    return u, abs(c["SLS 4 kN front, mid-span"]["uz_min"]), abs(c["SLS crowd"]["uz_min"]), abs(c["SLS person 1 kN at the nosing"]["uz_min"])
if L10:
    l = L10["L10 lattice 20 x 10 (24 long bars 3 x 25)"]
    L10_U = f"at least {l['ULS 4 kN patch front, mid-span']['vm'] / FD:.2f} at 4 kN, with {abs(l['SLS 4 kN patch front, mid-span']['uz_min']):.0f} mm of sag (limit 12.2) and {abs(l['SLS crowd 7.5 kN/m2']['uz_min']):.1f} mm under a crowd (limit 4.9)"
    f1_rows.append(("Your idea: finer lattice, bars along the step every 10 mm, 25 deep (coarser mesh, reads up to 8 % low)", f"≥ {l['ULS 4 kN patch front, mid-span']['vm'] / FD:.2f}", f"≥ {abs(l['SLS 4 kN patch front, mid-span']['uz_min']):.0f}", f"≥ {abs(l['SLS crowd 7.5 kN/m2']['uz_min']):.1f}", "—", "—", False))
else:
    L10_U = "over the limit"
for gk, gv in GRT.items():
    u, s4, cr, pe = gsum(gv["cases"]); good = u <= 1 and s4 <= 12.2 and cr <= 4.86 and pe <= 10
    f1_rows.append((("<b>C · " if gk == GRC_K else "") + "Open grating: " + gk.split(": ", 1)[1] + (" (C)</b>" if gk == GRC_K else ""), f"{u:.2f}", f"{s4:.1f}", f"{cr:.1f}", f"crossings {u * 2:.2f}", f"{gv['mass_kg']:.1f}", good))
for uk, uv in UBX.items():
    u, s4, cr, pe = gsum(uv["cases"]); good = u <= 1 and s4 <= 12.2 and cr <= 4.86 and pe <= 10
    f1_rows.append((("<b>B · " if uk == UBOX_K else "") + "Your sketch: " + uk.split(": ", 1)[1] + (" (B)</b>" if uk == UBOX_K else ""), f"{u:.2f}", f"{s4:.1f}", f"{cr:.1f}", f"{u_weld_box(uv['cases']):.2f}", f"{uv['mass_kg']:.1f}", good))
for k, v in BOXW.items():
    good = v["u"] <= 1 and v["sag4"] <= 12.2 and v["crowd"] <= 4.86 and v["person"] <= 10
    f1_rows.append(((f"<b>A · {optname(k)} (A, lightest)</b>" if k == REC else optname(k)), f"{v['u']:.2f}", f"{v['sag4']:.1f}", f"{v['crowd']:.1f}", (f"{v['haz_all']:.2f}" if v["haz_all"] is not None else "—"), f"{v['mass']:.1f}", good))
f1_table = "".join(f'<tr><td>{a}</td><td class="mono">{b}</td><td class="mono">{c}</td><td class="mono">{d}</td><td class="mono">{w}</td><td class="mono">{e}</td><td><span class="st {"pass" if f else "open"}">{"Pass" if f else "Fail"}</span></td></tr>' for a, b, c, d, w, e, f in f1_rows)
haz_note = ""
if REC in HAZ:
    h = HAZ[REC]["util"]
    haz_note = (f"Welds: aluminium is half as strong right next to a weld. Built with the top and both walls bent from one sheet and the bottom plate welded on, "
                f"the worst point is at {h['bent top U']:.2f}; with every corner welded, {h['welded corners']:.2f}.")

# ---------------------------------------------------------------- F4 / F5 numbers
pole55 = BAR["pole"]["solid 25 x 55"]; rails65 = BAR["rails"]; couple = BAR["couple"]["R179 1.5 kN post"]["F_kN"]; pm = BAR["pole_mass_12_kg"]
axrows = {(r[0], r[1]): (r[2], r[3]) for r in AX["axle"]}
gr = AX["friction"]["ground mu 0.5"]

def card(fid, title, meta, now, ask, why, imgs, how=(), drawing="", extra="", crit=True, note=None):
    figs = "".join(f'<figure><img src="img/final/{src}" alt="{alt}" width="1000" height="625" loading="lazy"><figcaption>{alt}</figcaption></figure>' for src, alt in imgs)
    how_html = ('<div class="how"><span>In SketchUp</span><ul>' + "".join(f"<li>{h}</li>" for h in how) + "</ul></div>") if how else ""
    return f"""
    <article class="card" id="{fid}">
      <header><span class="num{' fcrit' if crit else ''}">{fid.upper()}</span><div><h3>{title}</h3><p class="meta">{meta}</p></div></header>
      {f'<p class="yournote"><b>Your note:</b> {note}</p>' if note else ''}
      <div class="nowto">
        <div class="now"><span>In the 25 Sep model</span><p>{now}</p></div>
        <div class="to"><span>What I’m asking</span><p>{ask}</p></div>
      </div>
      <div class="why1"><span>Why, in plain terms</span><p>{why}</p></div>
      {drawing}
      <div class="refs">{figs}</div>
      {how_html}
      {extra}
    </article>"""

rec_txt = f"{rc['t_top']:g} mm top, {rc['t_bot']:g} mm bottom, {rc['t_wall']:g} mm front and back walls" + (f", {len(rc.get('webs', []))} inner web{'s' if len(rc.get('webs', [])) > 1 else ''} {rc.get('t_web') or rc['t_wall']:g} mm" if rc.get("webs") else "")
sc_ground = axrows[("scaffold tube 48.3 x 4.0 (6082-T6)", "ground mu 0.5")][0]; sc_held = axrows[("scaffold tube 48.3 x 4.0 (6082-T6)", "base held (scaffold clamp)")][0]
cards = [
    card("f1", "Steps: three ways that pass, all with drain holes", "6 per unit · critical",
         f"Open J at the back, a small L at the front edge, 60 grating bars running front to back, and two thin flats along the step (to be joined). 4 kN on the front edge is {t_front['util']:.1f}× too much, and a crowd sags the front edge {d_crowd['value']:.1f} mm where 4.9 is allowed.",
         f"Pick one; all keep the 280 × 50 outside and all have holes. "
         f"<b>A, lightest:</b> a thin closed box ({rec_txt}) with drain holes punched in the top and bottom, about {rec['mass']:.1f} kg. "
         f"<b>B, your sketch:</b> keep the J and the L, add a {UBOX['cfg']['t_top']:g} mm top plate and a {UBOX['cfg']['t_mid']:g} mm plate at mid-depth with ribs between, holes in both, about {UBOX['mass_kg']:.1f} kg. Rivet or screw those plates to the J and L ({u_weld_box(UBOX['cases']):.2f} if welded); with a 3 mm top plate (about {UBX['U2 your box: top 3, mid 2, ribs 2 at 60']['mass_kg']:.1f} kg) welding is fine too ({u_weld_box(UBX['U2 your box: top 3, mid 2, ribs 2 at 60']['cases']):.2f}). "
         f"<b>C, most open:</b> a real grating turned the right way: {GRC_K.split(': ', 1)[1].replace(' along the step', '')}, the bars running along the step, small cross bars on top; about {GRC['mass_kg']:.1f} kg. Interlock the bars and press-lock or swage the crossings; don’t weld them (welded, it would reach about {max(r['util'] for cn, r in GRC['cases'].items() if cn.startswith('ULS')) * 2:.1f}).",
         "The step spans 1.2 m between the rails, so whatever carries the load has to run along those 1.2 m. It also has to either be closed, so it can’t twist (A and B), or be deep enough on its own (C, with 50 mm bars). "
         "Today the grating bars run front to back, across the short 280 mm, so they only pass the load to the J and the small L, which then twist. "
         f"A 25 mm grating is too shallow on its own: your finer lattice (bars along the step every 10 mm, 25 deep) still comes out at {L10_U}. Closing the top 25 mm with a plate on each face, as you sketched, fixes it.",
         [("f1_where.jpg", "Where: all 6 steps (orange)"), ("f1_close1.jpg", "The steps as drawn: open, with grating"), ("f1_close2.jpg", "From below: J, L, bars and flats")],
         ["Keep the walking surface height and every pin hole exactly where they are.", "A and B: holes up to about a fifth of each plate, at least 20 mm from walls, webs and bends, and holes in the lower plate too so water runs straight through.",
          "C: serrated bar tops for grip; the cross bars sit in slots cut in the bearing bars (or the whole grid is cut from one plate)."],
         D.f1_options(rc, GRC["bars"], UBOX["cfg"]),
         f"""<div class="tw"><table><thead><tr><th>Option (same 280 × 50 outside)</th><th>4 kN stress (pass ≤ 1)</th><th>4 kN sag, mm (≤ 12.2)</th><th>Crowd sag, mm (≤ 4.9)</th><th>If welded (≤ 1)</th><th>kg per step</th><th>Result</th></tr></thead><tbody>{f1_table}</tbody></table></div>
         <p class="cnote">{haz_note} Correction: my earlier box check loaded the bottom plate by mistake. Re-run correctly, the box passes by more than I said (5 / 3 / 5 at {BOXW['B1 box 5 top / 3 bottom / 5 walls']['u']:.2f}, not 0.68).</p>""",
         note="you want holes for drainage and grip, the lightest design, and options, and you sketched a 25 mm box on top of the J and L. You’d also pictured one thick sheet with the grating cut out, or a finer lattice cut from one piece."),
    card("f2", "Step pins: 20 mm instead of 10 mm", "4 per step (2 at each end) · critical",
         f"Ø10 pins. On the right side the pin crosses a 14 mm gap (end plate, washer, 7 mm bush, rail wall); on the left, 6.75 mm. With a crowd on, the top step’s pins carry about {pin_v['value'] / 1000:.1f} kN each.",
         "Ø20 pins with Ø20 holes in the rails and step end plates (bushes and washers to suit). Deepen each rail to about 65 mm, so there’s at least 18 mm of metal round every hole.",
         f"These are the pins on the ends of the steps that go into the guide rails, not the pegs on the handrail poles (those are F3). Besides holding the step up, each step props the upper rail off the lower one, so its pins also carry that bracing force. "
         f"The pin bends across the gap like a short cantilever: at 14 mm it’s {pin_m['util']:.1f}× too weak. Doubling the diameter makes it 8× stronger in bending (0.66). Your bushes stop the wiggle, but they don’t take the bending unless a bush is pressed into the end plate and carries on into the rail hole. With a gap of 7 mm or less, Ø16 would do (0.62).",
         [("f2_where.jpg", "Where: the 4 guide rails and the step-pin hardware"), ("f2_close1.jpg", "Pins through the rails at the base")],
         ["Keep every hole centre where it is; the rails grow away from their holes.", "Right rails grow downwards; the left channels deepen by the same amount so a neighbour’s right rail still drops in.", "Put the split-pin hole just outside the nut (it now sits past the pin end)."],
         D.f2_pin(), note="there are bushes and a washer between, and a locking cap over the end."),
    card("f3", "Pole pegs: 12 mm instead of 2 mm", "12 poles, 4 pegs each · critical",
         "Each pole’s locking end (one piece with the pole) drops through both rails. At the lower rail it has two 2 mm pegs, one each side, reaching 7.5 mm across to holes in the rail walls. At the upper rail the model has only a hole through the pole, no pegs.",
         "Make the pegs 12 mm and widen the notches to match. Add the upper pair to the drawing. Line the left upper rail’s notches up with the poles (about 9 mm out now).",
         f"Yes, in short: bigger pegs. They don’t make the handrail stronger against people pushing (that’s F4). They hold the upper and lower rail at their spacing, which is what stops each side of the stair folding flat under a crowd. Each rail’s pair passes about {latch['value'] / 1000:.1f} kN. Because each peg reaches 7.5 mm to the rail wall, it bends; at 2 mm that’s far too weak, at 12 mm it’s 0.58.",
         [("f3_where.jpg", "Where: all 12 poles, one piece with their locking ends"), ("f3_close1.jpg", "Bottom of a pole through a rail; the dot is a peg end")],
         ["Draw each pole and its locking end as a single part.", "Add the upper-rail pegs."],
         D.f3_pegs(), note="the locking end is part of the pole, with 4 pegs per pole across both guide rails."),
    card("f4", "Poles: solid, deeper across the stair, on the outside of the rails", "12 per unit · critical",
         f"Hollow 25 × 10 × 2 poles, only 10 mm across the stair. Under the code’s barrier loads they are {poles['R142']:.0f}–{poles['R179']:.0f}× too weak.",
         f"Solid 25 (along the stair) × 55 (across, the way people push). Worst load at {max(pole55.values()):.2f}, so about {100 - 100 * max(pole55.values()):.0f} % spare. Cut as a taper, 55 at the rails down to 15 at the top, the 12 poles weigh {pm['tapered_25x55_to_15']:.0f} kg instead of {pm['uniform_25x55']:.0f} kg (they’re {pm['now_rhs']:.1f} kg now). "
         "A 55 mm pole can’t pass through a 35 mm rail, so it stands on the outside face of the rails, bolted to both. Its locking tab (F3) can still be part of the same cut piece.",
         f"Yes, you have it right. Each pole is a lever about 1 m long, fixed at the rails; people pushing outward on the top rail bend it where it meets the rails. Depth across the stair is what counts (strength grows with the depth squared), and solid beats hollow. "
         f"The push then reaches the two rails as a pair of sideways forces of about {couple:.0f} kN. Today’s rails can’t take that; the 65 mm rails from F2 can ({max(rails65['left rails U 35 x 65 x 5 (F2)'].values()):.2f} left, {max(rails65['right rails inv. U 25 x 65 x 5 (F2)'].values()):.2f} right). "
         "Between two units side by side there’s no drop, so the middle handrail doesn’t need to be a barrier and can stay as it is.",
         [("f4_where.jpg", "Where: the 12 poles (the full size runs down to the rails)"), ("f4_close1.jpg", "Poles along the left side")],
         ["Grow each pole across the stair; keep 25 along the stair.", "Solid 6082-T6 (or 6061-T6) aluminium bar.", "Two bolts into each rail per pole, one upper, one lower."],
         D.f4_pole(55), note="this is the crowd barrier; the poles can be wider and solid."),
    card("f5", "Supports: one axle, jack under the hook, hook locks", "base and top · critical",
         "The axle tube you kept stops about 34 mm short of the right-hand jack (the top one likewise, short of the right bracket rod). Each hook sits about 70 mm from its jack, so the Ø25 × 2.5 tube bends between them. The hooks are part of the rails and lock onto the axle, but nothing stops the rails sliding sideways along it.",
         "One axle tube from jack head to jack head, about 1,400 long. Either a 48.3 × 4 aluminium scaffold tube, or move each jack head under its hook and use Ø30 × 3. A collar on the axle each side of every hook. Base hook plates with at least 39 mm of plate round the axle (57.5 if the jacks will be clamped to a scaffold). The top hooks are fine as they are unless the base is clamped (then 40).",
         f"The axle works like a shelf bracket: the load comes in at the hook and goes out at the jack 70 mm away, so it bends. A scaffold tube is about 6× stronger than today’s tube (not 300×, but plenty): {sc_ground:.2f} on normal ground, {sc_held:.2f} clamped to a scaffold. With the jack right under the hook there’s no bending at all. "
         f"Each hook carries its own side’s share at the base: about {ENV['R_base'] / 1000:.1f} kN if the feet slide, {gr['R_base'] / 1000:.1f} kN on normal ground, {ENVH['R_base'] / 1000:.1f} kN if clamped to a scaffold. As drawn the base hook is open on the side the stair pushes, so its lock carries that. "
         f"The top hooks only lift (about {ENVH['uplift_top'] / 1000:.1f} kN) if the base is clamped. Your lock-nut jacks hold the height well; the only extra load is the sideways push when the feet are clamped.",
         [("f5_where.jpg", "Where: axles, hooks, jack heads, landing brackets; missing axle length in yellow"), ("f5_close1.jpg", "Base: the hook sits 70 mm from the jack"), ("f5_close3.jpg", "Right base jack: yellow is the missing length"), ("f5_close2.jpg", "Top: landing bracket and axle")],
         ["Make the axle one tube reaching into both jack heads.", "Add a collar each side of every hook on the axle.", "Draw the hook lock, for example a pin through the hook plate under the axle."],
         D.f5_base(), note="the second base was only an example and is removed; the hooks are cut or bent as part of the rails; the jacks go on the ground or on a scaffold array; their lock nuts hold the height."),
    card("f6", "Top rail height: which line to measure from", "a decision, not a drawing change yet",
         "Top of the top rail: 1,112 mm above the step surface at each pole (your 1.1 m), and 1,013 mm above the pitch line (the line joining the front edges of the steps).",
         "Check with whoever approves the stair how they measure. If from the pitch line, raise the top rail about 90 mm. If from the step surface, no change.",
         "Both numbers are right; they start from different lines. On a stair the usual reference is the pitch line (the code sheet’s row says “height from floor / pitch line”), and the sheet measures the handrail the same way. Your handrail is 903 mm above the pitch line, which passes (900–1,000).",
         [("f6_where.jpg", "Where: both top rails"), ("f6_close1.jpg", "Top rail on the pole tops")], [], D.f6_height(), crit=False, note="it’s 1.1 m to the top of the handrail."),
    card("f8", "Handrail brackets: 25 wide instead of 15", "12 per unit",
         f"Bent flats 15 wide, about 5 thick, holding the handrail 57 mm off the poles. Someone grabbing the handrail (1.25 kN) bends them {hbr['util']:.1f}× too much.",
         f"Make them 25 wide at the same thickness ({brk25:.2f}).", "The bracket is a small cantilever. Making it wider in the direction it bends adds strength with the square of the width.",
         [("f8_where.jpg", "Where: the 12 brackets"), ("f8_close1.jpg", "Brackets from below")], ["Widen each bracket to 25; keep the offset and the fixing points."], D.f8_bracket(), crit=False, note="these can be wider."),
    card("f9", "Clean-up still in the drawing", "drawing only",
         "Done: the second base, one of each pair of axle tubes, and 8 extra blocks on the right poles. Still there: 18 parts drawn twice in the same place (4 right poles with their locking ends and both top pivot parts, and the 2 right hooks), and 6 zero-thickness faces.",
         "Delete one of each pair (both copies are red in the pictures) and the empty faces. The axle length is covered in F5, the upper pegs in F3.",
         "Duplicates don’t change the checks (each part is counted once), but the drawing should match what gets made.",
         [("f9_close1.jpg", "Right poles drawn twice (red)"), ("f9_close2.jpg", "Right base hook drawn twice (red)")], ["Afterwards: 12 poles, 12 locking ends, 4 hooks."], crit=False, note="you cleaned up what you could and saved it."),
]
F7 = """<p class="cnote"><b>F7 Handrail grip: no change.</b> You’ll add foam or padding that rounds it off and keeps it cool in the sun. Noted only. For the grip rule (R64), the padded shape should end up 25–50 mm across and easy to wrap a hand round.</p>"""

ids = sorted(MK); pos_ = {}
for k in ids:
    if k == "f7": continue
    x, y = MK[k]
    for _ in range(6):
        if any(abs(x - a) < 3.5 and abs(y - b) < 4.5 for a, b in pos_.values()): x += 3.0
    pos_[k] = (x, y)
mk = "".join(f'<a class="mk{" fcrit" if k in ("f1", "f2", "f3", "f4", "f5") else ""}" href="#{k}" style="left:{x:.2f}%;top:{y:.2f}%" aria-label="Change {k.upper()}">{k.upper()}</a>' for k, (x, y) in sorted(pos_.items()))

SECTION = f"""<!-- FINAL-CHECK -->
  <section id="final-check">
    <h2>25 Sep model check: what’s still needed</h2>
    <p>Updated with your answers of 26 Sep and your clean-up of the model. Each change says what I’m asking and why, in plain terms, so you can tell me where it doesn’t match how the part is really made. F1–F5 are needed to pass the sheet; F6 is a measuring question; F8 and F9 are small. Full results: <a href="{DATASHEET}">datasheet, Rev B</a>.</p>
    <div class="key"><span><i style="background:var(--fail)"></i>needed to pass (F1–F5)</span><span><i style="background:var(--accent)"></i>smaller, or a decision (F6, F8, F9)</span><span>Click a number to jump to its change. In the pictures, <b style="color:#E8590C">orange</b> = change, <b style="color:#D11A1A">red</b> = remove.</span></div>
    <figure class="fig" id="figG">
      <div class="shot"><img src="img/final/f_overview.jpg" alt="25 Sep model, standard stair, with the changes numbered" width="1600" height="1000" loading="lazy">{mk}</div>
      <figcaption><b>Fig G</b> 25 Sep model, cleaned: what’s still needed</figcaption>
    </figure>
    <div class="cards">{"".join(cards)}
    </div>
    {F7}
  </section>
<!-- /FINAL-CHECK -->
"""
CSS = """<!-- FINAL-CHECK-CSS -->
<style>
.num.fcrit, .mk.fcrit { background:var(--fail); }
.card .num { font-size:14px; }
.mk { width:32px; height:32px; line-height:32px; font-size:12px; }
#final-check .refs { grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr)); }
.yournote { background:var(--accentbg); padding:8px 12px; font-size:14px; max-width:none; }
.why1 { display:grid; gap:4px; }
.why1 > span { font:600 11px/1 var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--ink2); }
.why1 p { max-width:80ch; }
.sec .arrowh { fill:var(--ink2); }
</style>
<!-- /FINAL-CHECK-CSS -->
"""
s = open(PAGE, encoding="utf8").read()
s = re.sub(r"<!-- FINAL-CHECK -->.*?<!-- /FINAL-CHECK -->\n?", "", s, flags=re.S)
s = re.sub(r"<!-- FINAL-CHECK-CSS -->.*?<!-- /FINAL-CHECK-CSS -->\n?", "", s, flags=re.S)
i = s.index("</header>") + len("</header>")
s = s[:i] + "\n\n  " + SECTION + s[i:]
s = s.replace("</style>\n\n<main", "</style>\n" + CSS + "\n<main", 1)
s = s.replace('Current design and ratings: <a href="https://claude.ai/artifact/GLipbqMzpRje8YZFLYTeL7">as-is datasheet</a>.',
              'Current design and ratings: <a href="https://claude.ai/artifact/GLipbqMzpRje8YZFLYTeL7">datasheet (Rev B, 25 Sep model; Rev A in the second tab)</a>.')
open(PAGE, "w", encoding="utf8").write(s)
print("brief updated", len(s), "| recommended step:", REC, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in rec.items()})
