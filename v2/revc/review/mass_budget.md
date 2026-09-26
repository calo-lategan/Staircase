# Whole-unit mass budget and minimum-mass study (Rev C after reviews)

Date: 26 Sep 2026. Scope: everything except the jacks and footplates. That means steps, rails, poles, top rails, handrails, brackets, axles, hooks, pins, locks and caps.
Tags: **[C]** means computed, in a script in `v2/revc/mass_opt/` or an existing repo script as cited. **[E]** means estimated from catalogue or geometry judgement, and should be confirmed.
R-numbers are sheet line − 1 in `v2/spec/sheet_2026-09-23_events.txt`.

**Owner decisions applied:**
- **No child-safety infill and no child rail.** They are not in the budget and not offered as an option. For the approver: R68 (≤ 100 mm openings for the public, sheet line 69) and R70 (lower rail at about 600, line 71) are **not fitted, by owner decision**.
- **Step envelope is an L:** a 280 × 25 walking zone with a 50 × 50 back support (`review/step_profile_owner.png`). The earlier box A (5.9 kg, 0.41) and grating C figures are void. The step mass comes from `step_optimisation.md` (see §3).

Scripts written (no existing repo file was changed):
- `mass_opt/pole_opt.py` → `pole_opt.json`: pole sizing and optimisation.
- `mass_opt/frame_pole_inplane.py` → `frame_pole_inplane.json`: OpenSees side frame (`final/side_frame.py`) with the inside-rail poles.
- `mass_opt/mass_budget.py` → `mass_budget.json`: the budget table and the relaxations.

---

## 0. Answer

**60 kg is not achievable within the locked constraints and the event loads.**

- Without the steps, the minimum-mass non-step parts come to about **70.6 kg [C/E]**. That is already above 60 before one step is counted.
- With six steps at the step optimiser's interim 6.14 kg each (36.8 kg), the achievable minimum is **≈ 107 kg**. If the optimiser gets the step down to about 5 kg, it is ≈ 101 kg. I would budget **≈ 105 kg + 5 % margin ≈ 110 kg**.
- Rev C as it stands after the reviews is about **90 kg of non-step parts**, so **≈ 127 kg** with the interim steps. That is well above the ~88–98 kg quoted so far, for four reasons: the inside-rail poles are longer, the top rail is raised by 87 mm, the rails are wider and deeper, and the L-envelope step is heavier than the old box.

**Inputs from the other agents are INTERIM.** Neither `rail_design.md` nor `step_optimisation.md` had been published when this was written. I used:
- rails: `v2/revc/rails/rail_design.json` → `mass.total_4_rails` = 23.72 kg (for a 55-wide pole);
- steps: `v2/revc/steps_opt/opt_skin.log`, iteration 0 → 6.14 kg per step at util 0.83, with the optimiser still descending.

Re-run `mass_opt/mass_budget.py` (the STEP / RAIL inputs) when the two reports land.

## 1. Rev C as it now stands, part by part (column RC_R)

| Part | kg | Tag | Basis / source |
|---|---|---|---|
| Barrier poles ×12, solid 25 × 55 √-taper, 6082-T651 plate | **43.5** | C | `pole_opt.py`. The pole is 1,344 long: 40 below the lower web for the latch, 167 between the crossings, and a 1,137 arm (1,050 + 87 for the R63 raise). It has a 35-wide tongue and the top 60 mm is 30 deep (poles_barrier C3, A4, A11). poles_barrier's "35 kg" counted only 88 mm below the upper rail. Util 0.93 at R179 1.5 kN with the 1,137 arm; **1.07 at 5.0 kN/m viewing**. |
| Guide rails ×4 (rail agent's interim design, 55-wide pole) | 23.7 | C | `rails/rail_design.json` mass.total_4_rails. poles_barrier's plain 82 / 94 × 70 × 5 U would be 21.3, using lengths 1,761 / 1,849 from `final/frame_geometry_final.json`. |
| Top rails 2 + handrails 2, U 25 × 25 × 5 × 1,726 | 6.1 | C | `final/final_results.py` mass table. |
| Axles 2, 48.3 × 4 × 1,470 | 4.4 | C | after_changes sizes; length per supports.md. |
| Step pins 24, Ø20 A4 headed + M20 thin nut + washer | 4.2 | E | Rev C F2; axial nut per steps_pins_rails C4. |
| Hooks 4 (10 mm plate, Ø49 bore) + 8 × M12 | 2.7 | E | hook_b() with r_i 24.5: rings of 65 (base) and 46 (top) mm (supports C1). |
| Handrail brackets 12, waterjet 25 mm S-profile, 2 × M8 | 1.9 | E | poles_barrier A5. |
| Axle collars 8 | 1.2 | E | supports M3. |
| Top-rail pivots + Ø8 pins | 0.9 | E | repo 0.61 + pins. |
| Caps, plugs, end returns | 0.7 | E | |
| Pole latch pins 12 | 0.4 | E | poles_barrier C3. |
| Hook keeper pins 4 | 0.3 | E | supports C4/C5. |
| **Non-step total** | **89.9** | | `mass_budget.json` |

## 2. Minimum-mass version inside the locked constraints (column OPT)

| Part | RC_R → OPT kg | Change and check |
|---|---|---|
| **Poles** | 43.5 → **27.0** [C] | **Custom 6082-T6 box extrusion, 25 along × 80 across, 5.5 end walls / 2.5 side walls, constant section.** Checks: R179 util 0.87 (0.997 at 5.0 kN/m viewing); along-stair post load 0.40 (1.5 kN shared by 6 poles through the top rail, sharing [E]); slot-face bearing 0.69 [E]; all walls class 1–3. SLS tip deflection from the pole alone is 12 mm, against about 29 mm for the √-taper plate. The rails widen by 25 mm (+2.4 kg, charged to the rails). The slot along the rail stays 32 mm, so the Vierendeel ligament result of poles_barrier C2 is unchanged. |
| Rails | 23.7 → **26.2** [C] | The rail agent's interim section with the webs widened by 25 mm for the 80-deep box pole (+2.4 kg). |
| Top rails / handrails | 6.1 → **4.5** [C] | Ø40 × 2 round tube. R64 grip target is 40. Util 0.36 at 1.25 kN over the 305 span. |
| Step pins | 4.2 → **2.5** [E] | Ø16 A4 with the end plate against the rail wall (steps_pins_rails Alt-2: bending 0.65), thin nut kept for axial. |
| Hooks | 2.7 → **2.0** [E] | Base hook over the axle (supports A1), so the ring works in bearing and needs less plate. |
| Brackets | 1.9 → **1.0** [E] | 12 mm plate S-profile, 18 deep (W 648 mm³, 0.64), 2 × M6 in rivnuts on the box pole. |
| Collars, pivots, caps | 2.8 → 1.9 [E] | Single-M8 collars 20 wide; saddle plug in the pole top. |
| Locks | 0.4 → **0.8** [E] | Adds an **upper-rail vertical lock**. See the finding below. |
| Axles | 4.4 → 4.4 [C] | 48.3 × 4 is already the lightest option. 50 × 3 is 1.11 held (fail). 50 × 4 is heavier. Steel S355 48.3 × 3.2 is 0.73 but +1.4 kg per axle. 7020 gives the same mass. |
| **Non-step total** | **89.9 → 70.6** | |

**Pole options compared** (12 poles plus the rail-widening penalty of 0.0975 kg per mm across; `pole_opt.json`) [C]:

| Option | kg |
|---|---|
| Solid plate √-taper 6082, Rev C | 43.5 |
| Solid plate √-taper 6082, also tapered between the rails | 42.4 |
| Solid plate √-taper 7020-T651 (D 52) | 39.4 |
| Castellated plate (NA slots) | 43–44, no gain |
| Stock RHS 80 × 40 × 3 | 29.8 + 2.4 + wider slot (needs 10 mm ligaments and thicker legs) |
| **Box 6082, 25 × 80** | **29.4** |
| I 6082, 25 × 70 (tf 9 / tw 2.5) | 26.7, but along-stair 1.00 and open profile |
| Box 7020, 25 × 75 | 27.0 |
| I 7020, 25 × 65 | 23.7 |

- **7020** saves only about 2.4 kg. It carries a stress-corrosion and exfoliation risk (needs correct ageing and a coating), costs roughly 1.3–1.6 × [E], and has fewer extruders. I don't recommend it for a public barrier.
- **7075** is not in EN 1999-1-1 Table 3.2, so it would need design by testing. It is also SCC-prone in T6. Rejected.
- **Steel** is not competitive on mass for these bending-governed parts (ρ/f₀: steel 0.022 against aluminium 0.012).
- **A swaged or press-braked tapered hollow** might save about 3–4 kg more [E]. Tooling, the 25-wide narrow box, and seam welds (HAZ) make it doubtful. Not recommended.
- **Prototypes:** build the two prototypes with waterjet plate or stock RHS and put the box die into the series build. The die is judged cheap [E].

**Finding (important, not a mass item) [C]:** poles_barrier C3 has "no vertical lock at the upper rail" and says this matches `side_frame.py`. It does not.
- `final/component_checks_final.py` and `frame_sls_final.py` both set `VERTICAL_AT_UPPER = True`. That is where the 5.9 kN latch force comes from.
- With the lock at the lower rail only, `frame_pole_inplane.py` gives 380–490 mm ULS sag and a pole in-plane moment of 1.4 kNm (util 1.1 for the solid pole, about 5 for an I). The frame is almost a mechanism.
- With a vertical lock at **both** rails: sag 0.5–1.0 mm, pole in-plane moment ≤ 32 kNm·mm, axial 6 kN. In-plane action then doesn't govern any pole option.
- **So each pole needs a vertical lock at the upper rail as well**, for example a fixed pin plus a spring latch on the neutral axis. The mass cost is about 0.5 kg per unit.

## 3. Unit total with steps

The step mass is 6.14 kg per step. This is the L envelope, interim from the optimiser log, and treated as including its end plates but not its pins. The step pins are counted in the table above.

| | Non-step | Steps 6 × 6.14 | Unit |
|---|---|---|---|
| Rev C as reviewed | 89.9 | 36.8 | **126.7** |
| Minimum inside the locked constraints | 70.6 | 36.8 | **107.4** |
| same, if the step reaches 5.0 kg | 70.6 | 30.0 | 100.6 |

The **gap to 60 kg is about 40–47 kg.**

## 4. Owner-controlled relaxations (options, not decisions)

Savings are against the OPT column [C, from `mass_budget.py`].

| # | Option (changes a locked item, so owner's call) | Saves |
|---|---|---|
| A | Barrier poles and top rail on the **exposed side only**, where the other side is against a wall or a neighbouring unit. On the unexposed side, 6 short lock posts (330 long, same box) through both rails keep the fold lock. Handrails stay on both sides. That rail pair can also go back to a step-pin-only web width (a further ≈ 2–3 kg [E]). | **≈ 11.6** (+2–3) |
| B | **4 poles per side instead of 6** (457 on the slope). The pole section is about the same (line load 1.55 kN against the 1.5 kN post) and the lock force per pole rises 1.5× (it passes). | **≈ 9.8** (≈ 4.9 if only the exposed side, combined with A) |
| C | Top axle replaced by 2 stub pins in the landing brackets. This is a design change, not a load relaxation: the lateral path goes through the steps and the base axle, which needs a check. | ≈ 1.7 |
| D | **Count 60 kg as the folded carry unit.** The poles, top rails, handrails, brackets, pivots and pole locks are separate carry pieces anyway, because the poles come out before folding. That is ≈ 34 kg, carried as 12 poles of ≈ 2.25 kg plus 4 tubes of ≈ 1.1 kg. The folded core (steps, rails, axles, hooks, pins, collars, caps) is then **≈ 36.7 + 36.8 ≈ 73.5 kg**, or ≈ 67 kg with 5 kg steps. | Handling target, not a mass cut |

A + B (exposed side) + C together save ≈ 18 kg, bringing the whole unit to about 82–89 kg (5.0–6.14 kg steps). That is still well above 60.

Even under D, the folded core reaches 60 kg only if the six steps total ≤ ~23 kg (≤ 3.9 kg each) or the rails lose about 10 kg. Neither is in sight with the current step and rail results. **Honest conclusion:** with the locked geometry, the event loads and aluminium, the realistic whole-unit minimum is ≈ 100–107 kg, and a 60 kg *carry piece* is only reachable if the unit is split further. Examples: each side frame (rails + hooks) carried separately from the steps, or the steps carried loose. Both would change the locked fold mechanism, so they are listed as options only.

Not proposed, because they are fixed limits:
- the R179 post load (it governs the poles);
- the R63 1,100 top-rail height;
- the 1.2 m step width;
- infill (the owner has decided against it).

## 5. Side effects to carry forward
- Unit width grows. The box pole widens the rails by 25 mm per side over the rail agent's 55-wide pole design, so a single unit is ≈ 50 mm wider than theirs.
- The catwalk rail stacking problem (steps_pins_rails C3) is unresolved and is up to the rail agent.
- The √-taper plate pole fails at 5.0 kN/m viewing (1.07) with the raised top rail. The box passes (0.997).
- Barrier deflection (poles_barrier A10) improves with the box: 12 mm from the pole, against 29 mm for the √-taper plate.
