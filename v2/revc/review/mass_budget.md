# Whole-unit mass budget and minimum-mass study (Rev C after reviews)

Date: 27 Sep 2026. Scope: everything except the jacks and footplates. That means steps, rails, poles, top rails, handrails, brackets, axles, hooks, pins, locks and caps.

Tags:
- **[C]** means computed, either in `v2/revc/mass_opt/` or in the cited repo script or report.
- **[E]** means estimated from catalogue or geometry judgement, to be confirmed.

R-numbers are sheet line − 1 in `v2/spec/sheet_2026-09-23_events.txt`.

**Owner decisions applied.**
- **No child-safety infill and no child rail.** They are not in the budget and not offered as an option.
  - For the approver: R68 (≤ 100 mm openings for the public, sheet line 69) and R70 (lower rail at about 600, line 71) are **not fitted, by owner decision**.
- **Step envelope is an L:** a 280 × 25 walking zone with a 50 × 50 back support (`review/step_profile_owner.png`).
  - The box A (5.9 kg) and grating C results are void.
  - The step mass is taken from `step_optimisation.md`.
- **Rails are open channels** (owner requirement per `rail_design.md`).
  - Rail mass is taken from `rail_design.md` / `rails/rail_design_box80.json`.

**Scripts written.** No existing repo file was changed.
- `mass_opt/pole_opt.py` → `pole_opt.json`: pole sizing and optimisation.
- `mass_opt/frame_pole_inplane.py` → `frame_pole_inplane.json`: OpenSees side frame (`final/side_frame.py`) with the inside-rail poles.
- `mass_opt/mass_budget.py` → `mass_budget.json`: budget table and relaxations.

---

## 0. Answer

**60 kg is not achievable within the locked constraints and the event loads. It is not close.**

- **The lightest unit I can find inside the locked constraints is ≈ 113–117 kg** (steps 5.7–6.35 kg as built). **Budget 120 kg including margin.**
- The non-step parts alone are **78.5 kg**, before any step is counted.
- **Rev C as it stands after all reviews is ≈ 138 kg.** That is far above the ~88–98 kg quoted so far. The reasons:
  - the inside-rail poles are longer;
  - the top rail is raised by 87 mm;
  - the nested open-channel rails weigh 34 kg, against 14.65 kg in Rev C;
  - the L-envelope step is heavier than the old box.
- `step_optimisation.md` §7 quotes 52.4 / 62.6 kg of non-step parts. Those figures use the old after_changes rails (14.65 kg) and poles (35 kg). **This report supersedes them.**

## 1. Rev C as it now stands, part by part (column RC_R)

| Part | kg | Tag | Basis / source |
|---|---|---|---|
| Barrier poles ×12: solid 25 × 55 √-taper, 6082-T651 plate | **43.5** | C | See the notes below the table. |
| Guide rails ×4: nested open channels with bulbs and lips | **34.1** | C | `rail_design.md` / `rails/rail_design_box80.json`. The plate-55 variant has the same mass. |
| Top rails 2 + handrails 2: U 25 × 25 × 5 × 1,726 | 6.1 | C | `final/final_results.py` mass table. |
| Axles 2: 48.3 × 4 × 1,470 | 4.4 | C | after_changes sizes; length from supports.md. |
| Step pins 24: Ø20 A4, headed, with nut and washer | 4.2 | E | Rev C F2. |
| Hooks 4 (10 mm plate, Ø49 bore) + 8 × M12 | 2.7 | E | hook_b() with r_i 24.5 gives rings of 65 (base) and 46 (top) (supports C1). |
| Handrail brackets 12: waterjet 25 mm S-profile, 2 × M8 | 1.9 | E | poles_barrier A5. |
| Axle collars 8 | 1.2 | E | supports M3. |
| Top-rail pivots + Ø8 pins | 0.9 | E | Repo pivots 0.61 kg plus the pins. |
| Caps, plugs, end returns | 0.7 | E | |
| Pole latch pins 12 | 0.4 | E | poles_barrier C3. |
| Hook keeper pins 4 | 0.3 | E | supports C4/C5. |
| **Non-step total** | **100.2** | | `mass_budget.json` |
| Steps 6 × 6.35 (C8 as built, 6.2–6.5) | 38.1 | C/E | `step_optimisation.md` §7 |
| **Unit** | **≈ 138** | | |

**Notes on the pole row (computed in `pole_opt.py`):**
- The pole is **1,344 mm long**: 40 below the lower web for the latch, 167 between the rail crossings, and a 1,137 arm (1,050 plus the 87 mm R63 raise).
- It has a 35 mm tongue, and the top 60 mm is kept 30 deep (poles_barrier C3, A4, A11).
- poles_barrier's figure of 35 kg counted only 88 mm of pole below the upper rail.
- Utilisation is 0.93 at R179 (1.5 kN post) with the 1,137 arm.
- At 5.0 kN/m viewing it is **1.07, a fail**.

## 2. Minimum mass inside the locked constraints (column OPT)

| Part | RC_R → OPT kg | Change and check |
|---|---|---|
| **Poles** | 43.5 → **27.0** [C] | Custom 6082-T6 box extrusion, constant section. See the notes below the table. |
| Rails | 34.1 → 34.1 [C] | Already sized for the box pole (81 mm slots). See the note on closed rails below the table. |
| Top rails / handrails | 6.1 → **4.5** [C] | Ø40 × 2 round tube, in line with the R64 grip target of 40. Utilisation 0.36 under 1.25 kN over the 305 span. |
| Step pins | 4.2 → **2.5** [E] | Ø16 duplex stud with an M16 castle cap nut (`rail_design.md`: bending 0.39, axial 0.56). |
| Hooks | 2.7 → **2.0** [E] | Base hook sits over the axle (supports A1), so the ring works in bearing. |
| Brackets | 1.9 → **1.0** [E] | 12 mm plate S-profile, 18 deep (W 648 mm³, utilisation 0.64). 2 × M6 into rivnuts. |
| Collars, pivots, caps | 2.8 → 1.9 [E] | Single-M8 collars, 20 wide; a saddle plug in the pole top. |
| Pole locks | 0.4 → **0.8** [E] | Lock at **both** rails. See the frame finding below. |
| Axles | 4.4 → 4.4 [C] | 48.3 × 4 is already the lightest tube that passes. |
| **Non-step total** | **100.2 → 78.5** | |
| Steps 6 × 6.35 (or 6 × 5.7 at the no-margin minimum) | 38.1 (34.2) | `step_optimisation.md` |
| **Unit** | **≈ 116.6 (112.7)** | |

**Notes on the box pole.**
- **Section:** 25 along the stair × 80 across, walls 5.5 (ends) / 2.5 (sides). Adopted by the rail agent.
- **Checks:**
  - R179: 0.87.
  - 5.0 kN/m viewing: 0.997.
  - Along-stair post load: 0.40. This assumes the 1.5 kN is shared by 6 poles through the top rail (sharing is [E]).
  - Slot-face bearing: 0.69 [E].
  - All walls are class 1–3.
- **Deflection:** SLS tip deflection from the pole alone is 12 mm, against about 29 mm for the √-taper plate.

**Notes on the rails.** The closed "H" rail (18.1 kg, utilisation 0.86) would save 16 kg. The owner has ruled it out, so it appears only as relaxation E in §3.

**Notes on the axles.**
- 50 × 3 gives 1.11 in the held case, so it fails.
- 50 × 4 is heavier.
- Steel S355 48.3 × 3.2 gives 0.73 but adds 1.4 kg per axle.
- 7020 gives the same mass.

**Pole options compared** (`pole_opt.json`, 12 poles plus a rail-widening penalty, [C]):

| Option | kg | Notes |
|---|---|---|
| Solid √-taper 6082 plate, Rev C | 43.5 | |
| Same, also tapered between the rails | 42.4 | |
| Solid √-taper 7020 plate | 39.4 | |
| Castellated plate | 43–44 | No gain |
| Stock RHS 80 × 40 × 3 | ≈ 32 | Needs a slot 50 mm or more along the rail |
| **Box 6082, 25 × 80** | **29.4** | Chosen |
| I 6082, 25 × 70 | 26.7 | Along-stair utilisation 1.00, open profile |
| Box 7020 | 27.0 | |
| I 7020 | 23.7 | |

- **7020** saves only about 2.4 kg. It brings stress-corrosion and exfoliation risk and costs roughly 1.3–1.6 × [E]. Not recommended for a public barrier.
- **7075** is not listed in EN 1999-1-1 Table 3.2, so it would need design by testing, and it is prone to stress-corrosion cracking in T6. Rejected.
- **Steel** is not competitive for these bending parts (ρ/f₀ 0.022 against 0.012 for aluminium).
- **A tapered hollow pole** (swaged or press-braked) might save about 3–4 kg more [E], but the tooling and the seam HAZ make it doubtful.
- **Prototypes:** make them with waterjet plate. That matches the rail agent's prototype variant, which has the same rails. Use the box die for the series build.

**Frame finding [C] (`frame_pole_inplane.py`).**
- **With the lock at the lower rail only:**
  - The side frame is close to a mechanism: 380–490 mm ULS sag.
  - Pole in-plane moment is 1.4 kNm: utilisation 1.1 for the solid pole and about 5 for an I-section.
- **With the lock at both rails:** sag is 0.5–1.0 mm and the pole moment is 32 kN·mm or less.
- **Consequences:**
  - The upper-rail lock in poles_barrier C3 is required, not optional.
  - The rail agent reached the same conclusion independently (9.5 kN per lock).
  - The repo's 5.9 kN latch force came from `VERTICAL_AT_UPPER = True`, not from the lower-only model that C3 cites.

## 3. Owner-controlled relaxations (options, not decisions)

Savings are against the OPT unit of ≈ 117 kg.

| # | Option (changes a locked item or owner rule, so the owner's call) | Saves |
|---|---|---|
| A | Barrier poles and top rail on the **exposed side only**. The side against a wall or a neighbouring unit gets 6 short lock posts through both rails, so the fold lock is kept. Handrails stay on both sides. | **≈ 11.6** [C] (+2–3 [E] if that rail pair loses its pole slots) |
| B | **4 poles per side instead of 6**, at 457 mm on the slope. The section stays about the same (1.55 kN line load against the 1.5 kN post). The lock force per pole rises 1.5×. | **≈ 9.8** [C] (≈ 4.9 if applied only to the exposed side with A) |
| C | Top axle replaced by 2 stub pins in the landing brackets. The lateral path then runs through the steps and the base axle, which needs a check. | ≈ 1.7 [C] |
| E | **Allow closed / H rails** (`rail_design.md` alt_H: 18.1 kg, utilisation 0.86) instead of the open channels. | **≈ 16** [C, rail agent] |
| F | **Step envelope.** | ≈ 4 [E] (lip) to ≈ 12 [E] (full-depth plank) |
| G | **Count 60 kg as the folded carry piece.** | A handling target, not a mass cut |

**Option F detail** (`step_optimisation.md` §7):
- Allowing the 30 mm nosing lip (also needed for R7) gives about 4.8–5.0 kg FE per step, roughly −0.7 kg per step as built.
- A full-depth 280 × 50 open plank gives about 4–4.5 kg as built.

**Option G detail.**
- The poles come out before folding anyway. So the poles, top rails, handrails, brackets, pivots and locks (≈ 34 kg) are already carried as small separate pieces: poles of ≈ 2.25 kg and tubes of ≈ 1.1 kg.
- The folded core is then:
  - **≈ 44.6 + 38.1 ≈ 83 kg**;
  - ≈ 67 kg with E;
  - **≈ 53–62 kg with E plus F** (≈ 62 kg with the nosing lip, ≈ 53–56 kg with the full-depth plank at 4–4.5 kg per step as built).

**Combinations.**
- A + B (exposed side only) + C + E together save ≈ 34 kg, so the whole unit is **≈ 79–83 kg**. That is still above 60.
- **60 kg is only in reach as the folded carry piece (G) and only with both E (closed rails) and F (a different step envelope).**
- For the whole unit, nothing short of dropping barrier poles on both sides gets to 60, and that would take away the fold lock (a locked constraint).

**Not proposed, because they are fixed limits:**
- the R179 1.5 kN post load, which governs the poles;
- the R63 1,100 top-rail height;
- the 1.2 m step width;
- aluminium as the main material;
- infill, which the owner has ruled out.

## 4. Side effects to carry forward
- **Unit width** follows the rail agent's box-80 design (81 mm slots).
- **Pole utilisation:**
  - The √-taper plate pole fails at 5.0 kN/m viewing (1.07) with the raised top rail. The box pole passes (0.997).
  - If the prototype uses plate poles, rate it for 3.0 kN/m only.
- **Double-count risk (≈ 2.5 kg):** I count the step pins separately. If the as-built step mass (6.2–6.5 kg, "with fasteners") already includes the pin studs, the unit is about 2.5 kg lighter.
- **Handling:** at 110–140 kg the unit needs wheels or a trolley and rated lifting points (build_reality 2.8, R171).
