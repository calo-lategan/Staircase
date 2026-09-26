# Rev C review: poles, barrier, pole fixings, handrail brackets

Reviewer role: devil's advocate, structural and fabrication. This is a read-only review. No repo file was changed.
Date: 26 Sep 2026. Model: IFC 25 Sep 2026, cleaned 26 Sep. Standard 35° stair, EN AW-6082-T6.

**Basis.** I read and cross-checked these files:
- `v2/revc/web/changelist.html` (F3, F4, F8), `manufacturing.html`, `verdict.html` and `datasheet.html`.
- `v2/revc/pole_fixing.py/.json`, `after_changes.py/.json` and `frame_after.py`.
- `v2/final/barrier_path_check.py/.json`, `component_checks_final.py`, `side_frame.py`, `frame_geometry_final.json`, `parts_final.json` and `final_meshes.npz`. I sliced the IFC meshes at the pole stations.
- `v2/spec/sheet_2026-09-23_events.txt`. R-number = sheet line − 1. For example, R142 is the 3.0–5.0 kN/m line, R179 is the 1.5 kN post and R104 is the lock row.

My own calculations are in the scratchpad (`pole.py`, `inside.py`, `inside2.py`). They are not repo files.

The document has three parts:
- **Part A** reviews Rev C as issued, with the poles outside the rails and strap / cross-pin / Ø16 pin fixings.
- **Part B**, "Spring-pin snap connection", answers the coordinator's first request. It covers the outside-socket idea, which the owner has since superseded.
- **Part C**, "Poles inside the rails (owner constraint)", is the current direction and my recommended scheme.

**Assumed rail width, to reconcile with `rail_design.md`.** The recommended pole is solid 25 along × 55 across. It needs:
- right inverted U: at least 72 mm inside (82 outside at 5 mm walls);
- left U: at least 84 mm inside (94 outside).

This gives about 8 mm of web beside each 56 mm pole slot. With legs only (57 inside), the hand estimate is 0.81–0.91, which is marginal.

If the pole is the RHS 60 × 40 × 4 with a 61 mm slot and 61 mm inside, the web is cut right across over 50 mm of rail. By my estimate that fails at 1.27–1.44. It needs 8–10 mm ligaments (77–81 inside) or deeper/thicker legs. See C3.

---

## Summary of findings (Part A, Rev C as issued)

| # | Sev. | Finding |
|---|---|---|
| A1 | Critical | F3 and F4 contradict each other. A pole on the outside face cannot also have a "locking tab with pegs" inside both rails. |
| A2 | Critical | Outside poles make side-by-side nesting (WIDE layout) impossible. The junction fold lock is left "as it is", which means Ø2 pegs failing 6.6×. |
| A3 | Critical | The 14.4 kN couple enters the rails through the free 5 mm legs, bent out of plane. This is about 1.5–3.5× over and was checked nowhere. |
| A4 | Critical | Taper profile not specified. A straight taper 55→15 fails at 1.31–1.33 at mid-height. Only the √-profile passes (0.84). |
| A5 | Critical | Handrail brackets (F8) were checked about the wrong axis. A 25 × 5 bent flat is about 2.8–4.0×, not 0.90. |
| A6 | Major | The Ø16 "pin across" at the lower rail is loaded along its own axis, not in shear. The pole_fixing vector sum is wrong. Inward loads pull it out, and an R-clip can't hold that. |
| A7 | Major | The strap is not detailed and not checked: flange (T-stub) bending, the bight, the bend radius in 6082-T6, and the bolt positions on a 35° rail. |
| A8 | Major | The bottom pole (x ≈ 9,647) does not cross the lower rail at all. The "Ø16 pin at the lower rail" does not exist there. |
| A9 | Major | Margin on the 25 × 55 pole: 0.84 × continuity 1.13 × F6 lever 1.083 ≈ 1.03 (plate f₀ 240 → 1.07). |
| A10 | Major | Barrier top deflection (SLS) is about 29 mm from the taper alone, plus about 8 mm from the rails, plus about 13 mm of pin/slot play. No limit is set. |
| A11 | Major | The pole top (15–17 mm) cannot take the existing top-rail post spigot (14 × 21 pocket). There is no pivot detail. |
| A12 | Major | Folding and removal: M12 nuts inside the channels have no access, and the pins aren't captive (R104). |
| A13 | Minor | `barrier_path_check.py` no longer runs (`np.trapz` was removed in numpy 2.4.6). The results can't be reproduced as-is. |
| A14 | Minor | The along-stair post load, the along-stair shear through the fixings, and the pin/bolt combined checks are all unchecked. |

---

## Part A: findings on Rev C as issued

### A1 Critical: F3 and F4 are not coherent
**What is wrong.**
- F3 says each pole's locking end "drops through both rails", with Ø12 pegs reaching 7.5 mm into the rail walls.
- F4 puts a 55 mm deep solid pole on the outside face of the rails and says "its locking tab and pegs (F3) stay part of the same piece".

**Evidence (IFC slice at x = 8,896.8, left side).**
- Lower rail: y −18,352…−18,317, z 443–473.
- Upper rail: same y, z 609–640.
- Locking end E7169: y −18,359.5…−18,309.5, z 330–575.

So the drawn locking end crosses the lower rail only. It stops 34 mm below the upper rail. The "upper pair" has nothing to sit in.

**Why it can't work.**
- A pole outside the outer wall can only reach inside the channel by wrapping round the wall's free edge.
- The outer peg would then sit where the pole body is.
- The F4 fixings already give vertical and along-stair restraint at both rails: the cross-pin and Ø16 pin carry vertical load, and the strap legs and Ø16 pin carry along-stair load. The pegs would add a third, statically indeterminate lock that can't be assembled within ±0.5 mm.

**Fix.**
- Delete the F3 pegs from F4 Route 1, as Route 2 already does. The lock is then the strap + cross-pin + Ø16 pin.
- Or abandon outside mounting (see Part C).
- Suggested F3 wording: "Pegs are not used with outside-mounted poles. The fold lock is the upper cross-pin and the lower pin; both must be captive."

### A2 Critical: nesting side by side (WIDE) is broken
**Evidence.**
- `story/_patch_nest.py:23`: B's right rails run inside A's left channels. The only way in or out is lengthwise.
- `datasheet/state_dims.json`: WIDE W = 2,546 vs a single unit at 1,305.
- `asis_ratings.py:188`: nested, one handrail set is spare, so one pole line passes through both nested rails.
- Left channel inside width 25, right rail outside 25. That is line-to-line.

With F4:
1. A's left poles, straps and bolts sit at y −18,352…−18,412. That is inside B's stair width, where B's step ends and end plates are (y ≈ −18,335…−18,368 after the −1,241 mm shift) and B's steps (z 525–575 at x 8,759–9,039). They clash.
2. B's right poles and straps would have to sit inside A's channel, which has 0 mm clearance. Even an M12 head can't pass. Strap nuts inside A's left channel block B's rail.
3. F4 says the middle handrail "can stay as it is". At the junction that means the hollow 25 × 10 pole with Ø2 pegs. That pole is the fold lock for both inner side frames, and it is 6.6× over (`final_results.json`, latch 5,892 N vs 890 N).

**Fix.**
- Give the WIDE junction its own lock part: a through-rail lock post with the same lock checks.
- Make everything on the outside face removable and flush.
- Or keep poles inside the rails (Part C, which the owner has now chosen).

### A3 Critical: the rail legs can't take the couple out of plane
**What is wrong.**
- Upper rail: the strap bolts pull 2 × 7.2 kN (ULS) out of the rail's outer leg.
- Lower rail: the pole bears 14.4 kN on the outer leg.

The legs are 5 mm plates attached to the web along one edge only:
- left U: the web is at the bottom and the top edge is free;
- right inverted U: the web is at the top and the bottom edge is free.

`barrier_path_check.py` checks only the whole rail in lateral bending (0.51 / 0.82). `pole_fixing.py` checks bolt tension and pull-through only.

**Evidence (yield-line estimate).** m_p = 5²/4 × 227 = 1,420 N·mm/mm. P ≈ m_p (a/e + 2…4).
- Bolt pair (a ≈ 70, e = 20–40 from the web): 5.3–10.7 kN vs 14.4 → 1.35–2.7×.
- Pole bearing (a = 25): 3.7–6.9 kN vs 14.4 → 2.1–3.9×.

Not FE-verified.

**Fix.** The couple has to go into the web in its own plane, or into both legs:
- a through-bolt with a spacer tube across the channel; this conflicts with nesting in the left channel;
- or a saddle round the whole rail;
- or poles through web slots (Part C).

Add the check to `pole_fixing.py`.

### A4 Critical: taper profile
**What is wrong.**
- `barrier_path_check.py` sizes the taper as D = 55·√(1 − h/1,050), with h measured from the upper-rail centre (full 55 below that). This keeps utilisation constant at 0.84.
- The change list says only "tapering to 15 at the top rail". A drafter will draw a straight line.

**Evidence (`pole.py`, ULS).**

| Load | √-profile | Linear 55→15 at pole top (h ≈ 950) | Linear 55→15 at h = 1,050 |
|---|---|---|---|
| R179 post 1.5 kN | 0.82 | 1.31 at h ≈ 794 (D 21.6) | 1.04 |
| R142 5.0 kN/m | 0.84 | 1.33 | 1.06 |
| R142 3.0 kN/m | 0.50 | 0.80 | 0.63 |

**Fix.** Give Gerald a table of depth D (mm) against height above the upper-rail centreline:

| h | 0 | 200 | 400 | 600 | 800 | 900 | 950 (top) |
|---|---|---|---|---|---|---|---|
| D | 55 | 49.5 | 43.3 | 36.0 | 26.8 | 20.8 | 17.0 |

- Keep full 55 from the pole foot to the top of the upper fixing, with the taper starting above it.
- Keep the inner edge straight; taper the outer edge only.
- Minimum depth 17 at the top, not 15.

### A5 Critical: handrail brackets (F8) checked about the wrong axis
**Evidence.**
- Bracket E11145 slice: an S-shaped profile in the y–z plane. The lower leg sits on the pole, then a horizontal arm at z 1,522.5–1,527.5 (5 thick) runs 50 mm inboard, then an upper leg rises 35 mm into the handrail.
- The 15 mm width is along the stair (x). So every handrail load across the stair or vertical bends the flat through its 5 mm thickness.
- `component_checks_final.py:128` uses W = 5 × 15²/6 (strong axis). Rev C scales it by (15/25)² to get 0.90.

**Correct values.** W = b·t²/6 = 25 × 25/6 = 104 mm³.
- Vertical 1.25 kN: M = 1.5 × 1,250 × 50 = 94 kN·mm → 900 MPa → **3.96**.
- Horizontal: M = 1.5 × 1,250 × 35 = 66 kN·mm → **2.77**.
- As drawn today (15 × 5): about 6.6 / 4.6. At the measured 4.2 mm thickness it is worse still.

**Fix.** Profile-cut the brackets from 25 mm plate (waterjet, the same stock as the poles):
- 25 along the stair, with the S-profile at least 16 deep in its own plane. W = 25 × 16²/6 = 1,067 → about 0.39 vertical and 0.27 horizontal.
- Fix with 2 × M8 into the pole.
- Suggested F8 wording: "Brackets waterjet-cut from 25 mm 6082-T6 plate, S-profile 16 mm deep in the plane of the S, not bent flat."

### A6 Major: the lower Ø16 pin is loaded along its axis
**What is wrong.** The pin runs across the stair (y). The couple force at the lower rail is also along y.
- Outward push: the pole bears on the rail by contact, and the pin is idle.
- Inward load (R143/R179 can act either way): the pole pulls away from the rail, and the pin is in tension. That is 1.5 × 1.5 × 1,050 / 167 ≈ 14 kN. An R-clip or split pin gives about 0 kN.

`pole_fixing.py` wrongly uses V = √(F² + FL²) in shear (0.55/0.65). In shear the pin only sees FL (5.9 kN vertical) plus the along-stair frame force, which is not reported anywhere.

**Fix.**
- Make it a headed M16 bolt or pin with a nut and washer, sized for 14 kN in tension, with pull-out through the rail wall checked. The leg bending from A3 applies again.
- Or add an inward stop.
- Correct the formula.

### A7 Major: the strap is neither detailed nor fully checked
**Bight bending.** The bight across the 25 face, with 14.4 kN spread over about 30 mm: M ≈ F·L/8 = 54 kN·mm vs M_pl = 40 × 5²/4 × 227 = 57 kN·mm → about 0.95. This is not in `pole_fixing.json`.

**Flange T-stub (mode 1).** 4·M_pl/m per flange. For m = 20–30: 11.4–7.6 kN per flange vs 7.2 → 0.63–0.95. Prying is ignored, so the bolt figure of 0.17 is optimistic.

**Bending the strap.**
- "Bent round the pole" in 5 mm 6082-T6. The manufacturing page itself says 5 mm 6082-T6 cracks in tight bends.
- A waterjet pole has sharp corners.

**Geometry on a 35° rail.**
- The bolts sit about ±40 mm along x from the pole centre, so they are ±28 mm apart vertically on the sloping rail band.
- The rail band is 79 mm tall at 65 deep. A 40-wide strap fixed on one level puts one bolt within about 9 mm (measured square to the rail) of the band edge. EN 1999-1-8 wants at least 1.2d₀ = 15.6 mm, and the Rev C rule says 20 mm.
- The flanges must be cut parallel to the rail, with both bolts on the rail centreline.

**Fix.**
- A machined U-clamp (from bar or extrusion) with sloped flanges.
- Or form in T4 and age.
- Or use a stainless 316 strap with isolation.
- Add bight and T-stub checks.

### A8 Major: the bottom poles have no lower-rail crossing
**Evidence.** Slice at x = 9,640–9,655: the lower rails E8505 and E11379 are absent (they end at x ≈ 9,628). The bottom pole E7449 (z 29–1,050) crosses only the upper rail. Its locking end E7573 is a sloping 170 mm part down to the hook area.

**What this means.**
- F4's "one Ø16 pin at the lower rail" does not exist for 2 of the 12 poles.
- The couple needs a second point, at the hook plate or axle. The lever is different, and it must be checked.
- The base jack head and axle parts at y −18,454…−18,354 (E6956, E6985 and others) sit right where an outside pole would go.

**Fix.** Draw a special detail for the bottom poles and check it.

### A9 Major: little margin left on the 25 × 55 pole
- The governing case is 5.0 kN/m viewing: 0.84.
- The top rail is continuous over 6 poles. The second pole takes about 1.13 wL → 0.95.
- If F6 goes to the pitch line, the arm becomes 1,137 → ×1.083 → **1.03**.
- 25 mm plate is T651 with f₀ ≈ 240 → about 1.07. (The build_reality review says "5.0 kN/m → 1.4". That is wrong, because 5.0 kN/m is already the governing case.)

**Fix.** Either:
- 25 × 60 at the rails (0.70 → about 0.86 with both factors); or
- state that 3.0 kN/m applies (a circulation stair). The R179 post load then governs at 0.82 → ×1.083 = 0.89.

### A10 Major: barrier deflection not checked
There is no barrier deflection limit in the sheet. SLS, per pole, 3.0 kN/m (0.92 kN):
- √-taper pole: 28.8 mm;
- rail lateral flexibility: +7.6 mm;
- hole clearances of 0.5 mm per side at 167 mm spacing: up to about 12.6 mm of rattle at the top.

That is about 40–50 mm in total. At 5.0 kN/m it is 48 + 12.6 + slack ≈ 65 mm. Comparison: a uniform 25 × 55 pole gives 14.6 mm, and RHS 80 × 40 × 3 gives 9.0 mm.

**Fix.**
- Ask the approver for a limit. BS 6180 uses 25 mm.
- Specify 0.2 mm reamed fits, or wedges.

### A11 Major: pole top and top-rail pivot
**Evidence.**
- The top-rail post E7177 is 25 × 20 × 100.
- Its spigot E7182 (14 × 21 × 50) plugs into the hollow pole top at z 1,550–1,600.
- A solid pole 17 mm deep can't take that pocket (walls of about 1.5 mm).

**Fix.** Keep the pole at least 30 deep for its top 60 mm (easy on a waterjet profile), with a Ø8 pivot hole or a clevis. Draw it. Moment at the pivot is about P × 100 mm ≈ 225 kN·mm ULS. A net section of 25 × 30 with a Ø9 hole works out at about 0.41 by my calculation.

### A12 Major: removal for folding, and captive pins (R104)
**What is wrong.**
- M12 nuts would be inside a 25 mm (left) or 15 mm (right) channel. There is no spanner access, and they block nesting.
- The cross-pin and Ø16 pin are not specified as captive (lanyard, R-clip or detent). R104 asks for a positive, captive lock with no unintended release.

**Fix.**
- Clinch or rivet nuts in the rail, or bolts from inside with captive heads.
- Captive pins on lanyards.
- A defined removal sequence.

### A13 Minor: reproducibility
`final/barrier_path_check.py` calls `np.trapz`, which fails on numpy 2.4.6. It also writes to the current directory. Change it to `np.trapezoid`.

### A14 Minor: loads not traced
- **Along-stair loads.** The post load along the stair, on the 25 mm axis (W = 5,729), is 1.81 if one pole took it alone. The top rail's pivots share it between 6 poles, which gives about 0.3, but this is not verified.
- **Frame loads.** The side frame gives the poles along-stair slot forces (`side_frame.py` "slot_*_H"). These are never reported or checked for the strap legs or bolts in shear.
- **Combined checks.** Bolt shear + tension interaction is not checked.

---

## Part B: Spring-pin snap connection

The coordinator's proposal was a socket bolted to the outside face of each rail, with the pole dropped in and a spring plunger along x at mid-depth. The owner decision in Part C supersedes this. My findings are kept for the record.

1. **Chamfered-nose snap plungers are not a positive lock in the direction they chamfer.**
   - The nose chamfer that lets the pole push the plunger back on the way down also lets a downward pole load push it back.
   - Only a nose with a flat bearing face on the loaded side, and a lead chamfer only on the insertion side, is positive. That means an anti-rotation flat plus the cam placed on the pole end.
   - Pull-knob index plungers (for example the GN 617 or Kipp K0338 type) are positive and captive. But any member of the public can release them without tools. EN 13200-6 cl. 5.1 behind R104 wants elements that are "lockable / not removable" without tools.
   - Use a tool-release design (squeeze tool or key), or add a secondary R-clip or padlock hole.
   - Catalogue shear ratings for index plungers are generally not published (not verified). Treat them as retainers, or size them yourself.
2. **Capacity.** The fold lock is 5.9 kN per pole (ULS, `final_results.json`).
   - Ø10 stainless pin, single shear: 0.6 × 500 × 78.5 / 1.25 = 18.8 kN → 0.31.
   - Bending over a 3–6 mm lever with Ø10 is about 0.7–1.1, which is marginal. Ø12 gives about 0.4–0.65.
   - Bearing on the aluminium is fine.
   - A threaded M16–M20 body in a 5–8 mm aluminium wall is too short. It needs a boss of at least 15 mm or a steel nut plate.
3. **The sockets have the A3 problem.** A socket bolted to one leg with 2 × M12 loads that leg out of plane, just like the strap (1.5–2.7× by estimate). Its bearing at the lower rail does the same (2–4×).
4. **Nesting.** Sockets on the outside face block nesting, as in A2. Folding with the poles removed is fine only if every socket stays within its own rail's vertical band. Because the rail slopes at 35°, that means a socket at most about 50 mm tall with a skewed back plate.
5. **Better approach.** Carry the load in bearing (slot or shoulder) and use the spring pin only as the latch against the reverse direction. Part C does this.

---

## Part C: Poles inside the rails (owner constraint)

### C1 Required section. Your numbers are verified.
W_req = 10,584 mm³ at the upper rail (5.0 kN/m, arm 1,050, f₀/γ = 227). The post load gives 10,395. Moving the rails apart does **not** reduce W_req, because M = P × arm at the upper rail. It only reduces the couple force F.

| Pole (6082-T6) | W mm³ | Util | Util × 1.13 continuity | 12 poles kg | Slot (across × along rail) |
|---|---|---|---|---|---|
| Solid 25 along × 55 across, √-tapered | 12,604 | 0.84 | 0.95 | 35.4 | 56 × 32 |
| Solid 25 × 51 | 10,838 | 0.98 (0.96 post) ✔ your 0.96 | 1.10 | ≈33 tapered | 52 × 32 |
| RHS 60 across × 40 along × 4 | 11,502 | 0.92 ✔ | 1.04 | 27.1 ✔ | 61 × 50 |
| RHS 50 × 50 × 5 | 12,300 | 0.86 ✔ | 0.97 | 33.2 ✔ | 51 × 62 |
| RHS 40 across × 80 along × 5 | 13,458 | 0.79 | 0.89 | 40.6 | 41 × 99 |

The ✔ marks confirm the coordinator's figures.

- A flat bar 25 across needs 102 along (✔).
- A 15 mm slot needs 282 along in 6082, or 180 in S355 steel (✔, impossible).
- If the approver accepts 3.0 kN/m and not R179, W_req drops to about 8,700 (R143 1.25 kN governs).

### C2 Why the slot width is not just "pole + 1"
With the web cut across the whole channel over the slot length, the rail at the pole station is two free legs.

**The Vierendeel problem.** The lateral shear V ≈ F·b/L = 14.4 × 199/305 = 9.4 kN (10.6 with continuity) must cross the opening in the legs' weak-axis bending. Per chord: M = V·L_slot/4. Results from my `inside2` estimate, with 65 × 5 legs:

| Pole / slot along the rail | Legs only (inside = slot) | 6.5 mm web ligaments | 8 mm ligaments | 10 mm ligaments |
|---|---|---|---|---|
| Solid 25 along (L = 32) | 0.81 / 0.91, marginal | 0.56 / 0.63 | 0.50 / 0.56 | 0.42 / 0.48 |
| RHS 60 × 40 (L = 50) | **1.27 / 1.44, fails** | 0.88 / 0.99 | 0.78 / 0.89 | 0.67 / 0.76 |

Pairs are without / with the 1.13 continuity factor.

**Lateral bending of the rail** at the slot section is low with wide rails: 0.17–0.27.

Deeper or thicker legs help in proportion to depth × t²: a 100-deep leg gives about 0.82 / 0.93 for the RHS with legs only. These are hand estimates; confirm by FE or a prototype push test.

**Conclusion.** The solid 25 × 55 pole needs a shorter slot, so it allows a narrower rail than the RHS 60 × 40.

### C3 Recommended scheme (dimensions for Gerald; the rail agent to reconcile)
**Pole.**
- Waterjet from 25 mm 6082-T6 plate. 25 along the stair.
- Profile in the across-stair / vertical plane:
  - full 55 across from 35 mm above the lower-rail web up through the upper rail;
  - √-taper above the upper rail (A4 table, min 17);
  - inner edge straight and vertical;
  - top 60 mm kept 30 deep for the top-rail pivot (A11).
- At the lower rail, a **tongue 35 across × 25 along**, stepping from 55 to 35 at a **shoulder** that seats on the lower rail web. This is the bottom seating: downward load goes in bearing on 2 × 10 × 25 mm.
- Mass: 35 kg per 12 (2.95 kg each). The RHS alternative is lighter (27 kg) but needs the wider rail from C2.

**Slots.**
- Upper rail web: 56 × (26 / cos 35° = 32) along the rail.
- Lower rail web: 36 × 32.
- Clearance 0.5 per side; ream to 0.2 if deflection matters (A10).
- The pole's across and along faces bear on the slot edges, so the couple goes into the webs in their own plane. This removes the A3 problem.

**Rails** (same web for all four; the rail agent's depth is fine):

| Option | Right inverted U | Left U | Web beside the 56 slot | Mass per unit |
|---|---|---|---|---|
| Recommended | 82 outside / 72 inside | 94 / 84 (1 mm nesting gap per side) | at least 8 mm | about +5.6 kg |
| Minimum | 67 / 57 | 79 / 69 | legs only, 0.81–0.91, marginal | — |

**Where the rails grow.** Widen outward only, keeping today's inner faces:
- left inner face at y −18,317, right at y −17,106 (IFC);
- steps (1,236 long), handrails and clear width R3 (1,101 between handrails) stay unchanged;
- the handrail stays where it is (brackets redrawn per A5).

Unit width grows about 116 mm to about 1,421 single, and WIDE to about 2,700. Step pins grow by the added rail width.

**Lock (F3 replacement): snap latch at the lower rail.**
- One double-ended spring latch pin through the tongue along the stair (x), at its across-stair centre (on the neutral axis).
- Ø10 stainless 1.4404, D-shaped with a flat top, anti-rotation flat, 45° lead chamfer on the underside only.
- Each end stands 6 mm proud of the tongue face. The pin top sits 0.5 mm below the underside of the web.
- On insertion the slot ends press the pins in, and they snap out under the web.
- Load path:
  - uplift or reverse fold load: the pin flats against the web underside (2 × Ø10 single shear 37.7 kN → 0.16; bending 0.28);
  - downward load: the shoulder.

  Positive in both directions and captive, meeting R104 and R78.
- Release: with a squeeze tool from below. This is possible because the lower-rail pin ends sit under the web: below the rail on the left U, and inside the open bottom on the right inverted U. No pull knob, so no casual release.
- Add a visible red band on the pin ends so you can see at a glance that the pole is locked.
- No vertical lock at the upper rail. The slot gives along-stair and across-stair restraint there. This matches the frame model in `final/side_frame.py:29` (VERTICAL_AT_LOWER = True, VERTICAL_AT_UPPER = False), which carries the 5.9 kN latch force.
  - Rev C's `frame_after.py` switched the upper vertical lock on. Re-run it with the upper lock off for the new rails. **Not re-run by me.**
- Pole-to-rail sequence: lower pins are offset along x from any upper-rail feature, so they cannot snap into the upper rail first. The upper rail has no pin holes at all.

**Nesting (WIDE).**
- Right inverted U 82 outside inside the left U 84 inside. One pole line passes through both nested rails: B's right web slot on top, A's left web slot at the bottom.
- That pole needs a tongue about 70 mm longer, with **two latch pairs**:
  - the upper pair snaps under B's web and locks unit B;
  - the lower pair snaps under A's web and locks unit A.
- With two different latch heights, the same "right/junction" pole works on a single right edge too. There the lower pair just hangs below the rail.
- Left-edge poles seat on a web that is 60 mm lower in the section (U open upward), so they need a separate "L" variant with the shoulder 60 mm lower.
- The junction line carries no barrier load. It can take the centre handrail that R19 asks for on wide gangways.

**Catwalk (rails touching).** The slots in the upper and lower rails must line up in the touching position as well as the stair position. That is the rail agent's job (second slot set or longer slots). The shoulder-and-latch detail is unchanged, because the pole seats on the lower rail in both states.

**Child infill (owner option).**
- Clip-in panels in each bay between poles (about 225 clear): a 6082 frame 20 × 20 × 2 with perforated sheet or mesh, openings ≤ 100 mm (R69), and a horizontal child rail at about 600 (R71).
- Loads: 1.0 kN/m² on the infill and 0.3 kN on 0.3 m square (tab_Load rows 37/50). That gives about 0.17 kN·m per pole, well below the line-load case if not combined. The clips carry about 0.3 kN.
- Clips must also be tool-release (R104).
- Watch climbability. The child rail at 600, the handrail at 903 and the rails form a ladder. Use vertical-bar or small-mesh infill (≤ 50 mm) so there are no footholds.
- The mesh adds wind area, and R148 wind is unchecked (not verified).
- Panels come off before the poles are pulled for folding.

### C4 Still to verify for the inside scheme
- FE or a test of the slot region (Vierendeel and leg bearing).
- The re-run of `frame_after.py` with the lock at the lower rail only.
- Slot positions for the catwalk state.
- The bottom-pole detail (A8 still applies).
- The top-pivot redesign (A11).
- Deflection (A10).

---

## Dimensions Gerald still needs (whichever scheme)
- **Pole.**
  - Profile table (A4).
  - Shoulder and tongue: height, width 35, length below the web.
  - Latch bore position.
  - Top 60 mm detail and pivot hole.
  - L/R variants.
  - Bottom-pole special.
- **Slots and holes.**
  - Slot sizes and positions along each rail: pole-station x, 32 mm along the rail, for both the stair and catwalk states.
  - Clearances.
  - Distance to step-pin holes (at least 20 mm of metal, R170).
- **Latch.** Pin Ø, length, chamfer side, spring, retaining roll-pin, release tool.
- **Brackets.** Profile, 25 mm plate, S depth 16, 2 × M8 hole positions on the pole, handrail seat.
- **Top rail.** Post, clevis and pin Ø on the solid pole top.
- **Infill.** Panel frame, clip positions and child rail height.
- **If outside mounting is kept anyway.**
  - Strap or clamp drawing: flanges parallel to the rail, both bolts on the rail centreline, edge distances, cross-pin hole position, lengths of all pins and bolts, nut access.
  - Headed lower bolt.

## Files
- Written: `/home/user/staircase/v2/revc/review/poles_barrier.md`.
- My scratch calculations: `/tmp/claude-0/-home-user/d308df96-ddeb-5b2b-bf5c-85277917a92e/scratchpad/{pole.py, inside.py, inside2.py, slice.py}`.
