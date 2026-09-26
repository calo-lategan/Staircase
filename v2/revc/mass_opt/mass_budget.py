"""Whole-unit mass budget (26 Sep 2026), everything except the jacks/footplates. Three columns:
  RC_R  = Rev C as it stands after the reviews (poles inside the rails, solid 25 x 55 sqrt-taper plate per
          poles_barrier.md C3, top rail raised +87 mm per supports.md F6, rails widened 82/94 x 70 x 5, 48.3 x 4 axles,
          hooks re-sized for the 48.3 axle, waterjet 25 mm brackets, O20 step pins with nuts, pole latches),
  OPT   = minimum-mass version inside the LOCKED constraints (this study; pole_opt.py),
  and the owner-controlled relaxations (options, NOT decisions).
Tags: C = computed here or in a cited script; E = estimate (catalogue/geometry judgement, to confirm).
Step and rail masses come from the other agents' reports (step_optimisation.md, rail_design.md) - see STEP / RAIL below.
No child-safety infill or child rail: owner decision (not in the budget, not an option).
Output: mass_opt/mass_budget.json"""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
RHO, RHO_ST = 2.7e-6, 7.95e-6
PO = json.load(open(os.path.join(HERE, "pole_opt.json")))

L_LO, L_UP = 1761.0, 1849.0            # rail lengths, v2/final/frame_geometry_final.json (a-b distances)
L_HR = 1726.0                          # top rail / handrail length, v2/final/final_results.py mass table
def u_rail(web, depth=70.0, t=5.0): return web * t + 2 * (depth - t) * t
def rails_kg(web_R, web_L, depth=70.0, t=5.0): return (u_rail(web_R, depth, t) + u_rail(web_L, depth, t)) * (L_LO + L_UP) * RHO
def tube_A(D, t): return math.pi / 4 * (D ** 2 - (D - 2 * t) ** 2)

# ---------------- inputs from the other agents (update when their reports land) ----------------
STEP = dict(kg_each=None, src="step_optimisation.md (pending)", includes_end_plates=True, includes_pins=False)
RAIL = dict(kg_unit=None, src="rail_design.md (pending)")

box = PO["box custom extrusion 6082-T6 extrusion (t<=5)"]["best"]
D_box = box["D"]
parts = {}
def add(name, rc, opt, tag_rc, tag_opt, src):
    parts[name] = dict(RC_R=rc, OPT=opt, tag_RC_R=tag_rc, tag_OPT=tag_opt, src=src)

# rails
add("rails 4 (guide rails)", rails_kg(82, 94), RAIL["kg_unit"] if RAIL["kg_unit"] else rails_kg(D_box + 27, D_box + 39), "C", "C" if RAIL["kg_unit"] else "C (placeholder: RC_R section widened for the box pole)",
    f"RC_R: inv. U 82 / U 94 x 70 x 5 (poles_barrier C3, steps_pins_rails 70 deep) x ({L_LO:.0f}+{L_UP:.0f}) per side; OPT: {RAIL['src']}")
# poles
add("barrier poles 12", PO["solid_RevC_reviewed_25x55_6082plate"]["mass12"], box["mass12"], "C", "C",
    f"pole_opt.py: RC_R solid 25x55 sqrt-taper 6082-T651 plate, 1,344 long (40 latch + 167 rail zone + 1,137 arm), tongue 35, top 60 at 30; "
    f"OPT custom 6082-T6 box 25 along x {D_box:.0f} across x {box['tf']} / {box['tw']} walls, util {box['util']:.2f} (R179 1.5 kN, arm 1,137)")
add("pole fold locks (latch pins, 2 levels x 12)", 12 * 0.03, 12 * 0.07, "E", "E",
    "RC_R: one O10 A4 double-ended spring latch per pole (poles_barrier C3); OPT adds the upper-rail vertical lock that frame_pole_inplane.py shows is needed")
# top rail / handrail
add("top rails 2 + handrails 2", 4 * 325 * L_HR * RHO, 4 * tube_A(40, 2) * L_HR * RHO, "C", "C",
    "RC_R: U 25x25x5 x 1,726 (final_results.py mass table); OPT: O40 x 2 round tube 6082/6060 (R64 grip 25-50, target 40): 1.25 kN over a 305 span -> 0.36")
add("top-rail pivots / saddles 12 + O8 pins", 0.61 + 12 * 0.02, 12 * 0.045, "E", "E", "RC_R: repo pivots 0.61 kg (final_results.py) + O8 pins; OPT: pressed-in end plug saddle in the box pole top")
add("handrail brackets 12 + screws", 12 * (0.135 + 2 * 0.012), 12 * (0.073 + 2 * 0.006), "E", "E",
    "RC_R: waterjet 25 mm plate S-profile 16 deep (poles_barrier A5), 2 x M8; OPT: 12 mm plate S-profile 18 deep (W 648 mm3 -> 0.64), 2 x M6 in rivnuts")
# supports
ax = 2 * tube_A(48.3, 4.0) * 1470 * RHO
add("axles 2 (48.3 x 4 x 1,470)", ax, ax, "C", "C", "after_changes.py sizes, length 1,470 per supports.md 'missing for Gerald' 1; 48.3x4 is already the lightest tube that passes held (0.96)")
add("axle collars 8 (split, 2 x M8)", 8 * 0.15, 8 * 0.10, "E", "E", "supports.md M3; OPT: 20 wide collar, one M8")
add("hooks 4 (10 mm plate, bore 49) + 8 x M12 bolts", 2 * 0.65 + 2 * 0.41 + 8 * 0.07, 2 * 0.40 + 2 * 0.30 + 8 * 0.07, "E", "E",
    "hook_b() of final_results.py with r_i 24.5: base held 65 mm, top 46 mm (supports C1); OPT: base hook over the axle (supports A1) -> ring in bearing")
add("hook keeper pins 4 (+ R-clip, lanyard)", 4 * 0.08, 4 * 0.08, "E", "E", "supports.md C4/C5, double-cheek O14 / O12")
# step pins
add("step pins 24 (A4, headed, nut, washer)", 24 * 0.176, 24 * 0.104, "E", "E",
    "RC_R: O20 x ~30 shank + M20 thin nut (Rev C F2, steps_pins_rails C4); OPT: O16 with the end plate against the rail wall (steps_pins_rails Alt-2: 0.65)")
add("caps, end plugs, returns", 0.68, 0.60, "E", "E", "8 rail end caps, 12 pole caps, 8 rail/handrail end returns (R71)")

def total(col, extra=0.0):
    return sum(p[col] for p in parts.values()) + extra
steps_kg = 6 * STEP["kg_each"] if STEP["kg_each"] else None
res = dict(parts=parts, step=STEP, rail=RAIL, non_step=dict(RC_R=total("RC_R"), OPT=total("OPT")))
if steps_kg:
    res["unit"] = dict(RC_R=total("RC_R") + steps_kg, OPT=total("OPT") + steps_kg, steps=steps_kg)

# ---------------- owner-controlled relaxations (options, not decisions) ----------------
pole_each = box["mass12"] / 12
rel = {}
rel["A. barrier poles + top rail on ONE exposed side only; other side: 6 short lock posts through both rails (fold lock kept)"] = \
    -(6 * pole_each - 6 * (box["A"] * 330 * RHO)) - tube_A(40, 2) * L_HR * RHO - 6 * 0.045
rel["B. 4 poles per side instead of 6 (8 total, 457 mm spacing on the slope)"] = -4 * pole_each - 4 * (0.07 + 0.085 + 0.045)
rel["C. top axle replaced by 2 stub pins in the landing brackets (the steps and base axle keep the sides together)"] = -(tube_A(48.3, 4) * 1470 * RHO - 2 * 0.25)
rel["D. rails narrower on a pole-free side (with A): web back to the step-pin-only width"] = None
res["relaxations_kg"] = rel
json.dump(res, open(os.path.join(HERE, "mass_budget.json"), "w"), indent=1)
w = max(len(k) for k in parts)
print(f"{'part':<{w}}  RC_R    OPT")
for k, p in parts.items(): print(f"{k:<{w}}  {p['RC_R']:5.2f} {p['tag_RC_R'][0]}  {p['OPT']:5.2f} {p['tag_OPT'][0]}")
print(f"{'non-step total':<{w}}  {total('RC_R'):5.1f}    {total('OPT'):5.1f}")
if steps_kg: print(f"unit incl. steps {steps_kg:.1f}: RC_R {res['unit']['RC_R']:.1f}  OPT {res['unit']['OPT']:.1f}")
for k, v in rel.items(): print(k, None if v is None else round(v, 1))
