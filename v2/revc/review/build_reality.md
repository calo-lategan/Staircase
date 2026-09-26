# Rev C build-reality review (devil's advocate)

Scope: read-only review of `v2/revc/web/{changelist,manufacturing,verdict,datasheet}.html`, `v2/revc/*.json|*.py`, `v2/final/component_checks_final.py`, `v2/spec/*` (events sheet + tabs), and the older part names in `v2/out/parts`. Viewpoint: aluminium fabricator, event-structure site operations, and checking engineer.

Tags used below:
- **[V]** means I verified it in the repo files.
- **[J]** means it is my engineering or trade judgement. Treat it as a question to put to a supplier or checker. It is not a fact.
- **R-numbers** follow the pages' convention: R*n* is line *n*+1 of `spec/sheet_2026-09-23_events.txt`. For example, R113 is line 114, the crowd UDL.

Severity: **Critical** blocks sign-off or public use. **Major** must be resolved before fabrication or release. **Minor** improves quality.

---

## 0. Summary of the most important findings

| # | Sev | One-line |
|---|-----|----------|
| C1 | Critical | Outside-mounted poles (F4) conflict with side-by-side nesting and folding. This geometry has not been checked anywhere. |
| C2 | Critical | Fold lock = the 12 barrier poles, with about 48–60 loose fasteners per unit. One forgotten pin gives a mechanism, and no n-1/robustness check exists. |
| C3 | Critical | Jack utilisation (0.82/0.88) assumes a 30 mm lever, i.e. a fully wound-down jack. Any real extension on uneven ground fails. |
| C4 | Critical | The "complies / every check passes" wording overclaims. Several events-sheet rows are not checked: wind, crowd sway 10 %, horizontal 3 kN/m on flight, EQU, fatigue, pattern load, child-safe side protection, buckling. |
| C5 | Critical | Side protection: 225 mm clear gaps between poles, no mid-rail or toe board, and the handrail at 903 works as a step 209 mm below the top rail. This is not acceptable for a public or child crowd unless infill is added. |
| M1 | Major | A 280×50 multi-void extrusion with 2 mm walls in 6082 is at or beyond practical extrudability. |
| M2 | Major | Stock sections (channel, RHS, grating) are usually 6060/6063, not 6082-T6. The util of 0.76–0.82 becomes about 1.2–1.3 with those alloys. |
| M3 | Major | Acetal bushes and nylon sleeves in bearing joints (about 110 MPa bearing) would crush or creep. |
| M4 | Major | "Bent round the pole" 5 mm 6082-T6 strap and "bent" 25×5 brackets. The page itself says 5 mm 6082-T6 cracks in tight bends. |
| M5 | Major | No local-buckling (class 4) check exists for 2–3 mm step walls or the open 70-deep channel flanges. |
| M6 | Major | Two connections are unchecked: the step end plate to the extrusion (Route 1, "riveted or screwed") and the pin axial retention (R-clips) under barrier push. |
| M7 | Major | At 88–98 kg per unit (about 110 kg with jacks), two people cannot carry it. |
| M8 | Major | Press-locked grating "3×50 at 46 mm" is not a standard catalogue pitch or alloy. Its openings fail the 35 mm-ball rule over occupied space. |
| M9 | Major | The prototype test is described as loading to 7.5 kN/m² and comparing a 0.9 mm sag. That is not a valid proof test, because pin slop dominates. |

---

## 1. Manufacturing claims

### 1.1 Route 1 step: 280 × 50 multi-void extrusion, 2 mm walls, 6082-T6. **Major**
- **Issue:** The circumscribing circle is √(280²+50²) ≈ 284 mm [V, arithmetic]. That needs roughly a 10–12″ billet press, which fewer extruders have. For a 6082 hollow at this CCD, the typical minimum wall is about 3–4 mm [J]. The 2 mm figure is realistic for 6063/6060, and 2.5 mm is marginal for 6005A.
- **Tolerances:** A thin, wide hollow has a width-to-thickness ratio of about 140. That gives poor flatness and convexity, and a wall tolerance of about ±0.2–0.3 mm on 2 mm (±10–15 %) under EN 755-9 [J]. The FE uses nominal walls.
- **Commercial:** A multi-void porthole die of this size is a significant cost, and there is a minimum run quantity (often 0.5–1 t per press run). At 5.9 kg per step and 35 kg per unit, one run is roughly 15–30 units [J].
- **Page wording:** "Drain holes punched … after extruding" cannot be done on closed voids, because there is nothing to back the punch. They must be drilled, milled or laser-cut [J].
- **Recommendation:** Send the section to two or three extruders and ask for a DFM review, a minimum wall, press size, die price and MOQ. Then choose one of these options:
  - (a) 6005A-T6 with 2.5–3 mm walls. EN 1999-1-1 gives f₀ about 215–225 MPa for t ≤ 5; re-run the FE with that value.
  - (b) Split the step into two approximately 140 mm interlocking or bolted extrusions, which suit a smaller press and cheaper die.
  - (c) Buy an existing extruded aluminium scaffold deck or stair-tread plank (320 mm scaffold planks and extruded stair treads with grit inserts are catalogue items) and add the end plates. The util must then be recomputed with the supplier's section and alloy.
  - Also ask the scaffold and event-system suppliers (Layher, PERI UP, HAKI and similar) for their public or event stair treads, which are type-tested. Check the width and rating in their catalogues.

### 1.2 Rails: "6082-T6 extruded channel about 70 deep, 5 mm walls … from stock lengths" (Route 2). **Major**
- **Issue 1, availability:** 70 × 35 × 5 (U) and 70 × 25 × 5 (inverted U, only 15 mm inside) are not common EN 755-9 stock sizes [J]. A channel with a 15 mm inner gap and 70 mm legs is unusual. Most stock channel is 6060-T66 or 6063-T6, with f₀ about 150–170 MPa. Scaling the 0.82 lateral util by 250/160 gives about **1.28 (fail)** [J, proportional estimate]. The repo already shows that a 5083 rail fails at 1.64 (`pole_fixing.json` rails_in_5083) [V].
- **Issue 2, nesting clearance:** The left U is 35 wide with 5 mm walls, which leaves 25 mm inside. The right inverted U is 25 wide outside. That is line-to-line, with no clearance [V, from the section dimensions in the datasheet]. Anodising and stock tolerances make it tighter still.
- **Recommendation:**
  - State "EN AW-6082-T6 (or 6005A-T6 re-checked), EN 755-2, 3.1 certificate per EN 10204" on the drawing.
  - Expect a simple solid-die cost for both channels [J]. This is cheap compared with the step die.
  - Add at least 1–1.5 mm clearance per side to the nest, or change the widths.

### 1.3 5083-H111 "doesn't lose strength when welded / no strength loss". **Minor, wording**
- **Verified part:** In EN 1999-1-1 Table 3.2a, 5083-O/H111 has ρ₀,haz ≈ 1.0. The HAZ equals the base metal because the base is already annealed. `after_changes.py` uses f₀ = 125 [V].
- **Misleading part:** The base is only half as strong as 6082-T6. The welded-5083 util (0.82) is identical to the welded 6082 util [V], so choosing 5083 buys no strength.
- **Other gaps:** Welded details still need a fatigue check (EN 1999-1-3). The internal webs of a closed 50 mm box cannot be fillet-welded from inside [J]. Only slot or plug welds, rivets, or a two-piece design are practical. Thin 2 mm, 1.2 m welded boxes distort.
- **Safer wording:** "5083-H111 has no weld-zone strength reduction because it is already in the annealed condition (f₀ 125 MPa, half of 6082-T6). Welded details still need a fatigue and distortion check. Webs inside the box must be riveted or slot-welded."

### 1.4 Press-locked grating "3 × 50 bars every 46 mm". **Major**
- **Issue 1, catalogue fit:** Catalogue press-locked aluminium gratings use standard pitches (typically about 30, 33, 34 or 44 mm) and bars that are often thicker at 50 mm depth. They are usually made in 6063/6060-T6 [J]. 46 mm is non-standard. With a 6063 alloy, util becomes about 0.81 × 250/160 ≈ 1.27 [J, proportional estimate].
- **Issue 2, notching:** Press-locking notches the top (compression) edge of the bearing bars, and the model may not include those notches [J].
- **Issue 3, openings:** Openings of about 43 × 47 mm let a 35 mm ball through. EN ISO 14122-3 practice limits openings to 35 mm, or 20 mm where people are below [J]. They are also heel and stick traps for the public.
- **Recommendation:** Pick a real product from a supplier load table (1.2 m span, 4 kN on 200 × 200, L/100) and re-run the check with its alloy, pitch and notch. Specify the opening limit. If there is space below the stair, prefer the closed step (A).

### 1.5 Waterjet solid tapered poles from 25 mm 6082-T6 plate. **Minor**
- **Tolerance:** Waterjet is acceptable because it leaves no HAZ (unlike plasma or laser). Kerf taper on 25 mm is about 0.1–0.3 mm without a taper-compensating head, and the exit edge is rougher [J]. Pin holes must be drilled and reamed on a jig, not waterjet-cut.
- **Material:** Plate thicker than 12.5 mm is normally supplied as T651. For 12.5 < t ≤ 100 mm, EN 1999-1-1 gives f₀ ≈ 240 MPa, not 250 [J, check the table]. That raises the pole util from about 0.84 to about 0.875.
- **Grain:** Cut the long axis parallel to the rolling direction.

### 1.6 Strap "5 × 40 6082-T6 bent round the pole" and handrail brackets "25 × 5 bent on a jig". **Major**
- **Issue 1, cracking:** The manufacturing page itself says "5 mm 6082-T6 cracks in a tight bend" [V]. Wrapping a 25 mm-wide solid pole needs tight 90° bends. The minimum inner radius for 6082-T6 at t = 5 mm is about 3–5t [J, check EN 485-2 guidance].
- **Issue 2, bracket bending axis:** The bracket util of 0.90 scales with width² (2.51 × (15/25)² = 0.90) [V, arithmetic]. That only holds if the 25 mm dimension is in the plane of bending. A bent-flat bracket is normally formed about its thin axis. If it is loaded about that axis, strength scales linearly: 2.51 × 15/25 ≈ **1.5 (fail)**.
- **Recommendation:**
  - Cut the brackets as a profile from 5 mm plate (waterjet or laser, then machine the edge) instead of bending them.
  - For the strap, use a machined U-clamp from bar or extrusion, bend in T4 or O temper and then age to T6, or use a stainless strap with isolation.
  - Confirm the bracket bending axis on the drawing.

### 1.7 Bushes, sleeves and galvanic isolation. **Major**
- **Acetal bushes:** Route 1 uses acetal bushes on the Ø20 step pins [V]. The pin force is about 11.2 kN on a 5 mm wall, which is about 110 MPa bearing [V/J]. Acetal's usable compressive stress for sustained load is roughly 10–20 MPa [J]. The bushes will crush or creep, the pins will slop, and the holes will elongate.
- **Nylon sleeves:** "Nylon washers and sleeves under every stainless bolt" has two problems [V]:
  - Nylon absorbs water and creeps, so the strap clamp loses preload. The fold lock and barrier depend on that clamp.
  - Sleeves in pin-bearing joints have the same crushing problem as the acetal bushes.
- **Recommendation:**
  - Use steel-backed PTFE (DU-type) bushes. The older design already had `DU_bush_20-16.1x20.step` [V].
  - Alternatively, use stainless pins bearing directly on aluminium with a barrier compound (Duralac or Tef-Gel type).
  - Isolate only under bolt heads and nuts, with hard insulating washers.
  - Put steel thread inserts in aluminium wherever a stainless bolt is re-made each set-up.

### 1.8 Anodising and finish. **Minor**
- **Nosing contrast:** An anodised "contrast strip" on the nosing has three weaknesses [J]. The contrast is low (clear against black). It wears through at the nosing, and dyed colours fade under UV. R18 (sheet line 18) asks for **55 mm contrasting nosings on both edges** [V].
- **Route 2 surface:** Bent 5083 sheet cannot have serrations or an anodised strip, so its slip resistance and contrast are undefined [J].
- **Anodising closed shapes:** Closed boxes trap anodising acid unless each void has drain and vent holes at both ends. Welded 5083 anodises dark at the welds.
- **Recommendation:** Use replaceable screw-fixed nosing inserts with a grit (carborundum) contrast strip, 55 mm wide. Specify PTV ≥ 40 wet (R16/R94) and test the actual surface.

### 1.9 Route 2 "standard M24 scaffold base jacks" and "scaffold clamps as collars". **Minor to Major**
- **Jacks:** Standard scaffold base jacks are Ø38 spindles, not M24 [J]. Use a system-approved Ø38 jack with its published extension limits.
- **Collars:** EN 74-1 couplers are rated on steel tube. On aluminium tube they slip at lower loads and can crush the tube at full torque [J]. Get a rating for aluminium tube, or use bolted split collars.
- **Tube size:** Aluminium scaffold tube is 48.3 × 4.0 (EU) or 48.3 × 4.47 (UK). State which is meant.

### 1.10 Thread and tap. **Minor**
- M12 A4-70 "into the rail" with a 5 mm wall gives only about 5 mm of thread engagement [J]. A nut cannot fit inside the right rail, which is 15 mm wide inside and an M12 nut is 19 AF [V/J].
- Stainless in tapped aluminium galls with repeated set-ups.
- **Recommendation:** Use steel inserts (keenserts or rivnuts rated for the load) or through-bolts. Confirm the bolt axis does not clash with the step end plates.

---

## 2. Real-world conditions not covered

### C1 Nesting side-by-side and folding with outside poles. **Critical [V absence, J geometry]**
- **Nesting:** The change list says a neighbour's right rail "drops fully in" to the left channel [V]. F4 then puts 55-deep solid poles (or 80-deep RHS) plus straps and bolt heads on the **outside face** of both rails. On a shared edge, those parts sit exactly where the neighbour's rail must go. No Rev C page checks this, and "nest" does not appear in any Rev C check [V].
- **Folding:** The poles are now clamped to both rails, so every fold needs 12 straps (24 bolts), 12 cross-pins and 12 lower pins removed and refitted. That defeats a "folding" unit.
- **Other states:** The catwalk and steep states are "not re-checked" [V]. The 70-deep rails may also clash in the folded stack.
- **Recommendation:** Before any redraw is released, model the nested pair and all three fold states in SketchUp. Consider separating functions:
  - a dedicated fold lock, such as the earlier `Index_plunger_Ø12`, `Latch_arm_+_plunger` or `Diagonal_brace` parts [V, part names];
  - barrier posts that plug in (spigot or socket) only on exposed edges.

### C2 Forgotten, loose or lost pins; robustness. **Critical**
- **Dependency:** "Without them [poles] each side folds flat" [V, verdict]. Each unit carries about 12 × 4 + 24 + 4 safety-critical fasteners. On a dark, wet get-in, one omission is likely [J]. There is no n-1 check (one pole or pin missing) per EN 1991-1-7 / EN 1990 robustness (R175).
- **Recommendation:**
  - Make the fold lock fail-safe: gravity or spring engaged, captive, with a visual indicator (a flag visible when not engaged).
  - Run a missing-component check.
  - Colour-code the critical pins, use captive lanyards, and add a pre-use checklist to the rating plate.

### C3 Jacks extended or uneven ground. **Critical [V]**
- **Assumption:** `component_checks_final.py` line 85 and `after_changes.py` line 67 use a lever of `30.0` mm, with the comment "axle centre about 30 mm above the footplate" [V]. At 10.9 kN sideways, 100 mm of extension gives about 3.3× the bending. The util of 0.82–0.88 becomes roughly 2–3 [J, proportional]. R74 (line 75) allows up to 600 mm extension.
- **Ground:** A footplate carrying about 12 kN SLS on grass is about 0.5 MPa, and it will sink. R76/R77 call for sole boards and a 1:100 level tolerance [V].
- **Support pattern:** Two jacks plus two top hooks is a four-point support, so a 10 mm level error twists the unit. That case is unchecked.
- **Recommendation:**
  - Recheck the jacks at the maximum permitted extension and state a limit (e.g., ≤ 100 mm) on the plate.
  - Require sole boards.
  - Capture the axle in U-heads so a sliding base cannot roll it off.
  - Provide positive base restraint (stake, tie or scaffold) instead of relying on friction. Wet or icy friction can be about 0.1.

### 2.1 Wet or icy steps, slip, drainage. **Major**
- **Surface:** Serrations fill with ice and mud [J]. Grit inserts perform better.
- **Holes:** "Holes up to about a fifth of each plate" in the walking surface [V] create heel traps. Use slots of 10 mm or less in the walking direction, or small perforations [J].
- **Frost:** Closed voids that hold water can burst on freezing. Each void needs a low drain at both ends.
- **Testing:** Specify a pendulum test (EN 16165) on the production surface, wet and dry, in both walking directions.

### 2.2 Wind and barrier. **Major (unchecked) [V]**
- **Rows not addressed:** R148, R150–R151 and R181 (wind, uplift, storm EQU: 0.9 Gk + 1.5 W) are not addressed in the verdict. The bare poles have little wind area.
- **Banners:** Banners or scrim fixed to event barriers are common and multiply the wind load [J].
- **Recommendation:** Add "no sheeting or banners unless checked" to the conditions, and run an EQU check with the landing hook uplift.

### 2.3 Dynamic crowd, sway, impact, pattern loads. **Major (unchecked) [V]**
- **Not checked:** R116 (horizontal 3.0 kN/m on the flight), R176 (crowd sway at 10 % of vertical), R177 (lateral f ≥ 1.5 Hz; only vertical is checked) and R180 (asymmetric or pattern loading).
- **Checked:** Vertical f₁ ≈ 22 Hz is fine for R177 (vertical).
- **Consequence:** Lateral stability of two side frames joined only by pinned steps, with 0.5 mm clearance per side, is unproven. Surge on descent is the realistic dynamic case.
- **Recommendation:** Build a 3D frame model with pin slop, or run a physical sway test.

### 2.4 Fatigue, pin and bush wear. **Major**
- **Wear:** 6082 pins in 6082 holes (Route 1) gall and fret [J]. The 0.5 mm per side clearance means rattle and impact under walking.
- **Fatigue:** Welded Route 2 steps under footfall need an EN 1999-1-3 check. R141 is listed in the sheet only as a bridge row, but it applies [J].
- **Recommendation:** Use stainless or hard-anodised pins in DU bushes, set a hole-elongation reject limit (e.g., +0.5 mm), and run a cyclic test on the fold joints.

### 2.5 Pin axial retention under barrier push. **Major [J]**
- **Load path:** An outward barrier load pushes the upper rail outward by about 14 kN per pole [V, `pole_fixing.json`]. The rail can only stay on the steps if the pin ends (nut or R-clip) hold it axially. Route 2 uses **R-clips**, which have almost no axial capacity [J].
- **Gap:** No check of pin axial retention was found [V, absence].
- **Recommendation:** Use headed pins with a castle nut or a collar on both routes, and check the axial load path from the rail through the end plate into the step.

### 2.6 Step end-plate connection (Route 1). **Major [V absence]**
- **Gap:** "End plates riveted or screwed to the webs" must carry about 11 kN of pin force from each end into 2 mm walls. No check exists for it.
- **Recommendation:** Design screw ports in the extrusion, or a thick end block with through-bolts, and check bearing in the 2 mm walls.

### 2.7 Local buckling (class 4). **Major [V absence, J magnitude]**
- **Gap:** No script contains a buckling or effective-thickness check [V, grep].
- **Step top:** The 3 mm top plate between webs 90 mm apart has β ≈ 30, which is probably class 4 in compression under EN 1999-1-1 Table 6.2 [J].
- **Rail flanges:** The open 70-deep channel legs are outstands with free edges in compression, β ≈ 13, which is well into class 4 for outstands [J].
- **Recommendation:** Apply EN 1999-1-1 §6.1.4–6.1.5 effective thickness, or run a nonlinear FE. This could remove much of the rail margin (0.40 net) and the step margin.

### 2.8 Transport and handling weight. **Major**
- **Weight:** 98.2 / 88.0 kg per unit for the structure alone [V, `after_changes.json`], plus jacks, so about 105–115 kg in total.
- **Handling limits:** HSE team-handling guidance (and EN 1005-2 / ISO 11228-1) gives a two-person capacity of about two-thirds of the sum of individual limits. That is roughly 33–50 kg for two people [J]. Even four people would be over the limit.
- **Recommendation:**
  - Design in wheels, a trolley or cradle, and rated lifting points (R171; there is an older `Lifting_lug.step` [V]).
  - Mark the unit weight.
  - Alternatively, make the unit demountable into pieces of 25 kg or less (steps about 6 kg each, poles about 3 kg, side frames).

### 2.9 Assembly sequence and finger traps. **Major**
- **Hazard:** During erection the unit is a folding parallelogram until all poles are fixed, which creates shear and crush points (R95: guard, or keep gaps above 25 mm or below 8 mm).
- **Recommendation:** Write the erection method statement required by R96 (EN 1298 style):
  1. unfold;
  2. engage the independent fold lock;
  3. set the jacks and sole boards;
  4. hook the top and fit the keeper pins;
  5. fit the poles;
  6. pre-use check.

  Include a stated time and crew size.

### C5 Children, gaps, climbability. **Critical for public use**
- **Gaps and rails:** The poles have about 225 mm clear gaps. There is no mid-rail and no toe board, and the side infill is "by others" [V]. R68 (line 69) and R70 (line 71) ask for 100 mm mesh or less for the public and a child rail at about 600 mm [V].
- **Climbing:** The handrail at 903 mm, on brackets 57 mm off the poles, is a foothold only 209 mm below the 1,112 mm top rail [V, arithmetic]. The rails also act as a toe step.
- **Height:** Units on a scaffold increase the fall height.
- **Recommendation:** Add mesh infill panels (the older `Mesh_infill_panel.step` exists [V]) or balusters at 100 mm or less. Assess climbability. Do not treat "scaffold edge protection" as covering the stair sides unless it physically does.

### 2.10 Barrier rating and height interaction. **Major**
- **Line-load range:** R142 allows 3.0–5.0 kN/m. At 5.0 kN/m, pole util becomes about 1.4 [J, proportional].
- **Height:** If F6 is resolved as pitch-line (+87 mm), the lever grows about 8 % and the pole util rises to about 0.91 [J].
- **Recommendation:** Rate the stair at 3.0 kN/m only, state that on the plate, and re-check once F6 is decided. My judgement is that an approver will most likely measure from the pitch line.

### 2.11 Inspection, maintenance, marking. **Major**
- **Missing:** R93 (rating plate) and R96 (manual) have no page content. The older `Rating_plate.step` and `EN_131-3_pictogram_plate.step` exist [V].
- **Plate content:** manufacturer, model or serial, year, permitted state(s), crowd 7.5 kN/m², barrier 3.0 kN/m, maximum jack extension, "all poles and pins fitted", inspection due date.
- **Inspection regime:** a pre-use visual check; a thorough examination after each hire or at least every 12 months; reject criteria (cracks at holes, hole elongation, bent pins, dented steps, missing captive pins).

### 2.12 What a checking engineer or approver will ask for. **Critical to plan**
1. A full Rev C calculation package on the **redrawn** model, not delta sizing. It should cover all states, all R-rows, connections, buckling, robustness, jack extension, landing interface loads and fatigue.
2. An execution specification to **EN 1090-3** (aluminium) at **EXC2**. The sheet cites EN 1090-2, which is the steel standard; fix that.
3. For Route 2 welding: WPQR to ISO 15614-2, welders qualified to ISO 9606-2, and a VT/PT plan. Material certificates to EN 10204 3.1.
4. An independent design check. EN 17879 CC2/RC2 is cited at R165.
5. A prototype test (R166): a documented protocol and witnessed report.
6. An erection and user manual, a risk assessment, and the landing-anchor design (11.3 kN per side) by others.
7. A jurisdiction check on approval routes: for example, Germany's "Fliegende Bauten" (Ausführungsgenehmigung and Prüfbuch), UK IStructE TDS guidance, and local building-control rules [J].

On CE marking under EN 1090-1: my judgement is that a demountable event stair is usually not placed on the market as a CPR construction product. Get this confirmed and do not claim CE marking.

### M9 Prototype test. **Major**
- **Issue:** "Load … to 7.5 kN/m² and compare with 0.9 mm" [V]. With 0.5 mm clearance per side at dozens of pins, bedding-in slop will exceed 0.9 mm, so the comparison is meaningless.
- **Recommended protocol:**
  1. Bedding-in load, then unload.
  2. Serviceability load; measure deflection and set.
  3. Proof load at the design (factored) level or 1.25–1.5 × characteristic as agreed with the checker; no permanent set above the agreed limit.
  4. Separate tests for the 4 kN nosing load, 3.0 kN/m on the top rail, 1.5 kN on a post, and the 1.25 kN handrail load.
  5. Repeat after about 50 fold/unfold cycles.
  6. Test with worst-tolerance parts.

---

## 3. Misinformation, overclaims and untested statements (proposed wording)

| Where | Current text [V] | Problem | Proposed text |
|---|---|---|---|
| verdict.html headline | "With the Rev C changes: complies … Every check on this page passes." | Many sheet rows are unchecked: wind, sway, EQU, fatigue, buckling, child protection, other states, jack extension, nesting. The results are calculated, not tested. | "With the Rev C changes, the checks listed on this page pass by calculation (standard 35° state, jacks at minimum extension). Not yet checked: wind/EQU, crowd sway, lateral frequency, fatigue, local buckling, robustness, catwalk/steep states, nesting geometry, side infill. Not approved until independently checked and load-tested." |
| verdict.html | "As drawn: does not comply" / "With … complies" | "complies" implies approval | Use "passes the listed calculations" and "fails the listed calculations". |
| manufacturing.html intro | "Both pass every check in the load verdict." | Stock alloys, the grating product and buckling are unverified | "Both routes are sized to pass the load-verdict checks, provided the materials are the stated alloy and temper (3.1 certificates) and subject to the open checks listed in the verdict." |
| manufacturing.html Route 2 | "5083, no strength loss" / "5083 doesn't lose strength when welded." | True but misleading | See §1.3. |
| manufacturing.html Route 1 | "280 × 50 box … 2 mm walls" | Extrudability not confirmed | Add: "Subject to extruder DFM; 2.5–3 mm walls or 6005A may be needed. Re-check if changed." |
| manufacturing.html Route 2 rails | "extruded channel from stock lengths" | Likely not stock, and stock is often 6060 | "Custom or stock channel in 6082-T6 only (6060/6063 fails). Confirm availability; a simple die may be needed." |
| manufacturing.html grating | "press-locked grating panel, 3 × 50 bars every 46 mm" | Not a standard catalogue item or alloy | "Grating option only with a supplier product whose load table and alloy are re-checked; openings ≤ 35 mm (≤ 20 mm over occupied areas)." |
| manufacturing.html | "Isolate … Nylon washers and sleeves under every stainless bolt" | Creep, preload loss, bearing crush | "Use barrier compound on stainless/aluminium contact; hard insulating washers under heads only; no polymer in bearing or preloaded joints." |
| manufacturing.html | "acetal bushes" | About 110 MPa bearing | "Steel-backed PTFE (DU-type) bushes, or none." |
| manufacturing.html | "Strap bent round the pole" / "brackets bent on a jig" | Cracking in 6082-T6; bending axis | "Machined or profile-cut, or formed in T4 and aged to T6; confirm the bending axis." |
| manufacturing.html | "Prove the first unit: load … to 7.5 kN/m² and measure the sag" | Not a proof test | See M9. |
| manufacturing.html / verdict | "Jacks on the ground M24 … 0.82" | 30 mm lever only | "…at ≤ 30 mm jack extension; re-check and state the maximum extension." |
| changelist.html | "Sizes are final unless marked 'decide'." | Hand-sized, not re-analysed as a set | "Sizes are proposed Rev C sizes, pending a full re-analysis of the redrawn model and an independent check." |
| verdict.html / datasheet | "R9 Pitch 35° … Pass" | At the limit; R109 (line 110) triggers assist elements above 28° | "Pass at the 35° limit; gradient > 28° triggers assist-element / handrail provisions (R109)." |
| datasheet.html | "Capacities are calculated, not type-tested." | Good; keep it | Also add it to manufacturing.html. |
| manufacturing.html | "the solid poles take knocks on site without denting" | Judgement presented as fact | "Solid poles are less prone to denting than thin tube (not tested)." |
| manufacturing.html | "If Route 2 is chosen … only cards F1, F3 and F4 change" | Rails, pins, jacks, collars and slip surface also differ | "F1, F3 and F4 change on the drawing; materials, jacks, collars, pin retention and step surface also differ (see the part table)." |
| Spec tab / sheet rows R82/R108 | "EN 1090-2 EXC2" | EN 1090-2 is steel | "EN 1090-3 (aluminium), EXC2." |

---

## 4. Cheaper or more realistic alternatives to evaluate

All items in this section are [J] and need checking with suppliers.
- **Steps:** Use a catalogue extruded scaffold or stair-tread plank, preferably with grit inserts, in 6005A or 6063. Cut it to length and bolt it to machined end blocks. Re-check with the real section and alloy. This avoids both a die and welding.
- **Whole system:** Adapt a type-tested event stair from a system (Layher, PERI UP, HAKI and similar public stairs are rated 5.0–7.5 kN/m²). Use it as the base, or at least as the benchmark for tread and stringer sizing. Treads and guardrails are then covered by type tests, which removes most of the calculation and approval burden.
- **Poles:** Use stock 6082-T6 RHS 80 × 40 × 3 from a certified stockist (Route 2) in plug-in sockets on exposed edges only, with a dedicated fold lock. This is lighter than solid poles, needs no waterjet, and keeps nesting possible.
- **Jacks:** Use a system Ø38 base jack with published extension/load tables, and sole boards.
- **Collars, keepers, locks:** Use shaft collars, ball-lock or spring index pins (the older parts exist), and gravity latches with indicators.
- **Infill:** Use clip-in mesh panels (≤ 100 mm) that double as child protection and banner substrate (then check wind).

---
Files reviewed: the four Rev C pages; `v2/revc/after_changes.json|py`, `frame_after.json`, `pole_fixing.json`; `v2/final/component_checks_final.py`; `v2/spec/sheet_2026-09-23_events.txt`, `tab_Parts_Checklist.txt`, `tab_Geometry_compliances.txt`; part names in `v2/out/parts`.
