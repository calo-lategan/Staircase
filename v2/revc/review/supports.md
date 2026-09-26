# Rev C review: F5 supports and F6 top-rail datum (devil's advocate)

Reviewer scope: F5 (axles, collars, hook rings, keeper pins, jacks and footplates, landing bracket and anchor, base conditions) and F6 (top-rail datum, sheet R63).
This is a read-only review: no repo file was changed. Recomputations were done in a Python shell.
R-numbers are sheet rows (file line = R + 1 in `v2/spec/sheet_2026-09-23_events.txt`).

## 0. What was reproduced

The after-change numbers in `v2/revc/after_changes.py` / `.json` come out the same when recomputed from the envelopes in `final_results.json`:

| Item | Rev C value | Recomputed | Formula |
|---|---|---|---|
| Axle 48.3x4, ground mu 0.5 | 0.60 | 0.597 | R 11,054 x 70 / W 5,701 / 227 |
| Axle 48.3x4, base held | 0.96 | 0.959 | R 17,747 x 70 / W / 227 |
| Top axle 48.3x4, held | 0.61 | 0.612 | R 11,321 x 70 (70 **assumed**, not measured) |
| 30x3 under hook, held, shear | 0.83 | 0.835 | V_pl = 2A/pi x f_o/sqrt3/1.1 |
| Keeper pin D14 / D12, single shear | 0.81 / 0.71 | 0.814 / 0.707 | 0.6 x A x 295/1.25 |
| M24 ground / M30 held | 0.82 / 0.88 | 0.821 / 0.878 | N/A_s + H x 30 / W(d_eq from A_s) |
| Footplate 150x150x8, held | 0.89 (hard-coded) | 0.893 | same formula as `component_checks_final.py` with B 150, t 8, d 30, V 14,031, H 10,866, lever 30 |
| Hook ring 39 / 57.5 | | 39.0 / 57.5 | `hook_b()` in `final_results.py` **with r_i = 12.8 (the D25 axle)** |

The arithmetic holds up. The problems are in the inputs and in checks that are missing.
`v2/final/axle_options.json` (the mu 0.3/0.5 friction cases and the axle table) has **no generator script anywhere in the repo**. The V/H pairs for "ground mu 0.5" (V 9,887, H 4,943, V_top 976) therefore can't be reproduced (**not verified**).

---

## CRITICAL

### C1. Hook ring sizes were computed for the old D25 axle, and the hook bore isn't changed
- Evidence: `final_results.py` `hook_b(R, t=10, ri=12.8)` uses r_i 12.8 (bore 25.6 for the D25x2.5 tube). The changelist's 39 / 57.5 mm are `hook_b(11,054)` / `hook_b(17,747)` with that r_i. With a 48.3 tube (bore about 49, r_i 24.5) the same formula gives:
  - base: ground mu 0.5 → **45.5 mm**; held/clamped → **65 mm**; slides → 31 mm.
  - top: slides 24, ground mu 0.5 26, held/clamped **46 mm**.
- The datasheet says "top as drawn unless clamped (then 40)", but the drawn top hook has a 25.6 bore and can't take a 48.3 tube at all. F5 in the changelist never mentions the hook bore or the top ring.
- Fix (changelist F5 wording): "Re-cut all four hooks for the 48.3 axle: bore D49.0 (+0.5/-0). Plate round the bore at least 46 mm at the base on the ground and 65 mm if the base is clamped or fixed; top at least 46 mm (the top is clamped against the landing in the held case). Re-run `hook_b` with r_i = 24.5 and replace 39/57.5 in after_changes.py." The hand formula is still approximate, and the code note itself asks for a plane-stress FE of the hook before sign-off.

### C2. The jack lever of 30 mm can't survive the new hooks, so M24/M30 fail
- Evidence (parts_final.json, left base): footplate top z -120, axle centre z -89.4 → lever 30.6 mm. The hook plate E8541_L07 reaches down to z -125, i.e. **already level with the underside of the footplate (ground)**.
- A 48.3 tube with a 45.5–65 mm ring under it puts the hook bottom 70–90 mm below the axle centre. So the axle centre must rise by at least 35–55 mm, plus any levelling extension. Nothing in Rev C limits jack extension.
- Recomputed with the Rev C formula:

| Lever (mm) | M24 ground mu 0.5 | M30 held |
|---|---|---|
| 30 | 0.82 | 0.88 (0.97 using the root diameter d3 = 25.7 instead of d_eq 26.7) |
| 65 | 1.63 | 1.77 |
| 90 | 2.22 | 2.41 |
| 150 | 3.61 | 3.95 |

- M24 aluminium threaded rods can't carry the sideways base force at any realistic extension. Also, the bending was checked on d_eq from the stress area; EN practice uses the minor diameter d3, which is 10–12 % weaker.
- Fix: replace the aluminium M24/M30 jacks with **standard steel scaffold base jacks with a U-head (fork head) for 48.3 tube** (hollow D38 spindle, 150x150 base plate, rated load tables with max extension). Or, if aluminium stays, state "max extension X mm" and check it. Either way add to F5: "axle centre >= 100 mm above the footplate; max spindle extension 200 mm (check with the supplier table incl. 10.9 kN sideways)". Alternatively turn the base hook over the axle (see A1), which removes the ring from under the axle.

### C3. The ground case says "drawn footplates are fine", but they fail and break R73
- Evidence: the drawn footplate is 100x100x5 (E6956_E08). R73: "Legs / Support || Base || Footplate dimension || 150 x 150 mm || ... 150 x 150 mm minimum".
- With the ground mu 0.5 forces (V 9,887, H 4,943, lever 30) and the repo's footplate formula: **1.43** (peak pressure 1.88 MPa). Uniform-only: 0.75.
- The same forces on 150x150x8 give 0.58.
- Fix: F5 bullet 1 → "Jacks on the ground: 150 x 150 x 8 footplates always (R73), on sole boards." Ground bearing (R174) and sole boards (R76) are unchecked: about 10 kN on 0.0225 m² is 0.44 MPa, far above turf or soil. State "sole board >= 0.1 m² per jack (e.g. 225 x 450 x 38 timber) unless a ground survey says otherwise".

### C4. A forgotten base keeper pin means collapse, even with the base free
- Evidence: `hook_direction_check.json` gives L_free_base on_plate **false**; `frame_envelopes.slides.lock_base` = 6,427 N, which is the full base reaction. As drawn, the base hook plate doesn't carry even the plain vertical load; the pin does.
- R78: "Coupler engagement / pin locking || Locked / pinned || Positive lock".
- Fix: make "turn the base hook so the plate sits on top of the axle" the **primary** instruction, not an "or". The keeper then only stops the stair lifting off. Keep a captive pin with a positive lock (R-clip or linch pin on a lanyard, not a spring-detent pin alone) and a "pin fitted" visual check in the assembly sequence. The top keeper stays structural in the held case (11.3 kN at 344–349°), so the same rule applies there.

### C5. The keeper pin check covers shear only, but the pin as described works in bending
- "A D14 pin through the base hook plate under the axle": if the pin runs parallel to the axle through a single 10 mm plate, the axle bears on the projecting ends and the pin is a cantilever.
- With F/2 per projection at a 10–20 mm lever: M_Rd (D14, 1.5 W f_o/1.25) = 80.8 kNmm → **1.10–2.20**. The single-shear 0.81 does not cover this case.
- Also not stated: hole edge distance in the hook plate (e1 >= 1.2 d0, EN 1999 T8.8), and bearing on a 4 mm tube wall if the pin touches the axle.
- Fix: draw the keeper as a pin through **two cheeks** (double shear), or across the hook mouth with both ends supported in plate. Give the pin axis, hole diameter (15 H11), edge distances and pin length. Otherwise size it for bending, which needs about D20 at a 15 mm lever.

## MAJOR

### M1. Axle margin: 0.96 held with the offset fixed at exactly 70 mm; collar holes and welds would take it over 1.0
- Between the two hooks the moment is constant at R·a, so any cross-hole there sits at full moment.
- Offset a = 80 → 1.10, a = 90 → 1.23. Collars (about 20–25 mm) plus the U-head half-width must fit inside the 70 mm.
- A D10.5 cross-hole for a collar pin cuts W to about 0.70 of the gross → **1.37 held**. A welded collar brings HAZ f_o 125 → **1.92 held**.
- Fix: specify "hook plate centre to jack-head bearing centre <= 70 mm; collars clamp-type (split, 2 x M8), no holes and no welds in the axle between the jack heads". Or use steel 48.3x4 S355 (EN 39), which gives 0.61 held (see A2).

### M2. The tube's local crushing and ring bending at the hook and jack head is not checked
- The 10 mm hook bears on a 4 mm wall. If contact is along a line (bore clearance), a rough ring estimate (M ≈ 0.24 P r) needs about 100 mm of effective length at 17.7 kN, and only 30–40 mm is available. Not verified.
- The old "Bearing of the axle on the hook" row (limit 75 kN) uses D25 and pin-in-hole bearing, which doesn't address the tube wall.
- Fix: close-fit bore (D49.0 on 48.3, contact over >= 90°). Check it with plane-stress FE or a test, or fit an internal sleeve or solid spigot at each hook and jack head.

### M3. Across-stair (axial) load path is missing: collars, jack heads, friction
- The collars are specified with no load, type or position. The barrier line load R142 of 3.0/5.0 kN/m over about 1.76 m of flight gives **7.9–13.2 kN ULS per unit** sideways (my estimate), about 4–6.6 kN per end.
- In an open U-head the axle can slide along its own axis, so only friction resists it: 0.3 x 2 x 6.4 kN ≈ 3.9 kN at the base in the slides case.
- Sideways load also bends the jacks about the other axis, adding vectorially to H.
- Crowd sway R176 (10 % of vertical imposed, about 1.35 kN ULS along the flight) and R116 are not in any check. In the slides case all of it goes to the top hook and keeper.
- Fix: add a lateral load case (R142 x flight length, plus R176) with a path collar → axle → jack head stop (bolt through the U-head or end stop) → base fixing or friction check, and the top bracket. Specify the collar: "split aluminium collar, width 25, bore 48.3, 2 x M8 8.8, one each side of each hook, 1–2 mm total play, slip capacity >= X kN (test)".

### M4. Landing bracket and anchor are under-specified, and the 11.3 kN is not the whole load
- The bracket pin (0.25) and plate (0.38) are for the **old D20 pin** detail (`component_checks_final.py`). With a 48.3 top axle, the bracket interface changes and those rows no longer apply.
- The fixing is "wing clamps" (not checked).
- In the held case the top reaction is 10.9 kN horizontal into the landing plus 3.2 kN uplift per side, i.e. **about 22 kN horizontal into the landing structure per unit**. The landing, stage deck or scaffold must resist that, and nobody has been told.
- The lateral (M3) and sway loads come on top.
- Fix: F5 → "Landing bracket: design load per side 11.3 kN at 344° (10.9 kN into the landing, 3.2 kN uplift) + lateral share Y kN. Draw 2 x M12 8.8 through-bolts per bracket (or 2 EN 74-1 class B couplers onto a 48.3 ledger), edge distances >= 1.2 d0. No wing clamps. Landing supplier to confirm 22 kN horizontal per unit."

### M5. Scaffold clamping (EN 74) is not designed
- The "fixing for 10.9 kN sideways" has no detail. EN 74-1 couplers are rated on steel tube; class B right-angle couplers have a characteristic slip of about 15 kN, design about 10 kN (γM 1.5). Not verified; the supplier's aluminium-tube values are lower.
- R170 lists "EN 74-1 … + crowd uplift".
- Fix: "2 x EN 74-1 class B couplers per jack/axle end, supplier-rated for 48.3 x 4 aluminium tube". Better still, couple the 48.3 axle straight to the scaffold ledger and drop the jack (A3).

### M6. The two base conditions are left to chance
- "Hooks lock, so anywhere between free and held" is a sound envelope, but the free case lets the unit **walk downhill** under cyclic crowd load: there's no horizontal restraint at the base, and the top hook is open.
- With mu 0.3 on steel decks or wet timber, the ground case is the mu 0.3 row. That one isn't checked for the axle or jacks (H 2,440 N, lower).
- The held case needs friction of 0.77 (component row "Base held by friction alone" 1.55).
- Fix: state one intended condition in the method statement. Either "base tied to the landing / pegged" (design for held) or a slotted base with a stop.

### M7. Wind, uplift and overturning (R150, R151, R181) are unchecked
- There's no wind or EQU (0.9 G + 1.5 W, out of service) check anywhere in `final/` or `revc/`.
- An 88–98 kg unit sitting on hooks is light, and the barrier infill catches wind.
- Fix: add an out-of-service wind check and a tie-down instruction.

## MINOR

- m1: `after_changes.py` "top_scaffold_ground" uses hypot(H_base, V_top). That's valid only if no other horizontal load exists, which is true of the crowd case but not with sway or wind.
- m2: R-references are wrong. The hook throat and keeper rows cite **R150** ("Uplift / anchorage"); the hook throat should cite R147/R170 and the keepers R78/R170. The changelist lists "R147 R150 R73" for F5 and should add R76, R78, R170, R174 and R176.
- m3: The top axle offset of 70 mm is **assumed**, not measured ("bracket span assumed like the base"). Measure it or specify it.
- m4: The second base axle at x 9,936 carries no load (datasheet). F5 should say "delete it" or "keep as spare"; F9 lists 2 axles afterwards, so make that explicit.
- m5: The footplate formula uses the rod diameter as the cantilever root. If the rod-to-plate joint is a 6082 weld, f_o,haz 125 gives **1.79** for 150x150x8 held. Specify a bolted or threaded boss, or a steel jack.
- m6: Jack buckling at extension isn't checked (a free-standing spindle, K about 2). With a steel jack from the supplier's table this goes away.

## Missing or ambiguous for Gerald (F5)

1. Axle length: "about 1,400" vs jack centres 1,373 (y -18,404 / -17,031). Give an exact length (e.g. 1,470 = 1,373 + 2 x 48.5 overhang past the head) and end caps.
2. Hook bore and ring at the base and top for 48.3 (C1); hook outer profile; how it joins the 65 mm rail.
3. Axle centre height above the footplate; ground clearance under the hook (C2).
4. Collar type, width, bore, fastener and position (gap to the hook plate) (M3).
5. Keeper pin axis, hole, edge distances, length, retention device, and single or double cheek (C5).
6. Jack: material, spindle size, max extension, U-head inside width for 48.3, and a positive tube retainer in the head (the axle can lift out of an open U when the top reaction reverses).
7. Footplate 150x150x8 in **both** cases, the rod-to-plate joint, and nail holes for sole boards.
8. Scaffold case: coupler class, count, and position.
9. Landing bracket: bolts (size, grade, count, edge distance), what it bolts into, and removal of the wing clamps.
10. The 30x3 "jack under hook" option needs a fork head straddling the hook. The hook and jack head can't occupy the same axial position otherwise, and the offset must be <= 20 mm (30x3 held: bending 1.0 at 20 mm). Only shear (0.83) was checked.
11. Assembly order: jacks set and levelled → axle in heads → collars loose → hooks down → collars set → keepers in → top. Also transport: the axle is a loose 1.47 m part, and collars and pins need to be captive.

## F6: top-rail datum (R63)

Sheet wording (R63, file line 64): *"Handrail / Guardrail || Top Rail || **Height from floor / pitch line** || 1100 mm above datum (EN 13200-3:2018 cl.4.4 pp.8-9) / 1000 mm (EN 12811-1 Ind) || … || 1100 mm; 800 mm only per seating exception"*.
R46 (handrails) likewise says *"height to pitch line"*.
The sheet's datum on a stair is the **pitch line**, and the floor on landings. No row mentions a "step surface at each pole". That measurement is taken from the lowest point of each tread and flatters the height by about 99 mm.

F6's "if from the step surface, no change" is therefore **not supported by the sheet**.
Fix: turn F6 from a "decision" into a required change: "Raise the top rail to >= 1,100 above the pitch line (+87 mm; draw +95 for tolerance)". Then re-run the pole, strap and handrail-bracket checks: the barrier lever grows from about 1,050 to 1,137, so the pole 0.84 becomes about 0.91 by proportion (estimate).
I did not verify the 1,112 / 1,013 measurements themselves.

## Better or cheaper alternatives (quick checks)

- **A1. Base hook over the axle** (ledger-hook style), covering about 60–160° at the axle centre. The plate then carries the 90–128° reactions, the keeper becomes nominal (removing C4 and C5), and the ring moves above the axle, so the axle can sit low and the jack lever stays short.
- **A2. Steel 48.3x4 S355 (EN 39) axle**: held 17,747 x 70 / (5,701 x 355) = **0.61** (S235: 0.93). It's cheap, stock, and EN 74 couplers are rated for it. It adds about 3 kg/m (+about 9 kg per unit for two axles). Isolate it from the aluminium with nylon washers.
- **A3. On a scaffold, no jacks**: couple the 48.3 axle straight to the scaffold ledgers with 2 class B couplers per end, placed next to the hooks. This removes the jack bending and the footplate.
- **A4. Standard steel U-head base jacks** (D38 spindle, 150x150 plate) instead of aluminium M24/M30. They're off the shelf, rated with extension, and meet R73.
- **A5. Fork-head jack straddling the hook**: axle bending about R x 15 mm, so a 48.3 tube is at about 0.2 held. The axle can then be two short stubs, but the lateral path (M3) still needs a spreader tube.
