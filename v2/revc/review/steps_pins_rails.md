# Rev C review: steps (F1), step pins and rails (F2), frame and fold

Reviewer: devil's-advocate structural and fabrication check. Read-only; no repo file was changed.
Scope: F1 (box A / grating C), F2 (Ø20 pins, rails "about 70 deep", 20 mm edge metal) and how the frame folds.
Re-runs were done on copies in /tmp/rv: `rv70.py` (side frame with 70-deep rails), `rv70b.py` (rail net-section check) and `rvbox.py` (box step FE including the end zone).
Basis: EN 1999-1-1, 6082-T6 f0 250 (t ≤ 5), HAZ 125, γM1 1.1, γM2 = γMp 1.25, as the scripts state.

## Verdict

The F1 and F2 numbers on the Rev C pages are mostly reproducible for the member checks as the scripts define them. The pin formulas, partial factors and the T8.8 edge-distance formula are used correctly.

The detailing Gerald is told to draw does not produce the geometry those numbers assume:
- The pin holes cannot get 20 mm of metal while their centres stay put.
- The "same" end plates cannot take Ø20 pins.
- The 70-deep rails stop the unit folding to catwalk.
- The load paths at the step ends (end plate, pin fixity, pin axial force from the barrier) are not checked anywhere.

F1 and F2 should not go to the drawing stage until C1–C4 below are resolved.

---

## CRITICAL

### C1. "Same end plates" cannot carry Ø20 pins, and the end plate is the unchecked governing part of the step
- **What is wrong.**
  - The current end plate is a 5 mm, 20 mm band at z 30–50, plus the closure of the back J box. Source: datasheet "End plates | 5 mm at y 15–20 … 20 mm band (z 30–50)".
  - The change list says to keep "the end plates and every pin hole exactly where they are".
  - A Ø21 hole at the front pin centre (x 225, z 37.5) spans z 27–48. That is taller than the 20 mm band.
  - The metal left above that hole, up to the 50 mm walking surface, is **2 mm**. Under gravity the plate hangs on the pin, so this is the loaded ligament.
  - The same T8.8 formula the scripts use needs a ≥ F·γMp/(2·t·f0) + 2·d0/3. With F = 11.2 kN and t = 8 that is ≈ 3.5 + 14 = **17.5 mm**. Required ≥ 17.5, provided 2: this fails by about 9×.
  - Rear hole (x 25, z 12.5): 2 mm to the step underside and 14.5 mm to the back face.
- **The end plate stress is never reported.**
  - `tread_box2.py` / `tread_box2_haz.py` only scan elements with 40 < y < 1190. That excludes the end plates (y 17.5 / 1212.5) and the plates next to them.
  - Re-run of box B4 with Ø20 pins (`/tmp/rv/rvbox.py`), 5 mm end plate modelled as continuous with every plate:
    - ULS 4 kN at the end: end plate von Mises **168.7 MPa = 0.74**.
    - ULS 4 kN at mid-span: 161 MPa = 0.71.
    - The deck at mid-span is only 0.41, so the end plate is the governing step element.
  - This figure excludes the frame link force (≈ 9–10 kN between the rear and front pin, carried in the plane of the end plate) and the hole itself (rigid links).
- **The FE joint does not match either build route.**
  - The FE assumes the end plate is fused to the box.
  - Welded in 6082-T6: the HAZ halves the limit, so 0.74 → **≈ 1.48, fail**.
  - Manufacturing guide Route 1 says "End plates riveted or screwed to the webs". That joint (into 2 mm walls and webs) is not modelled or checked. It must carry ≈ 4.1 kN vertical (4 kN case), about 1 kN with the crowd plus about 10 kN of link force, and the barrier axial force (C4).
- **Fix (wording for F1 and F2).**
  - "New end plates for the box step: 8 mm 6082-T6, 280 wide.
    - Either extend them at least 40 mm below the box and lower both pin centres (see Alt-1),
    - or move the front pin down so its centre is at least 28 mm below the walking surface.
  - Every pin hole needs at least 18 mm of metal to any plate edge.
  - Joint to the box: [n] × M6 A4 screws into screw ports in the extrusion (or n × Ø4.8 structural blind rivets), checked for 11.2 kN in shear plus 9.4 kN axial per pin.
  - No welding of 6082 end plates."
- Re-run the step FE with the end plate at its real thickness, the holes and the joint, and report the end-zone utilisation.

### C2. The rail holes cannot get "20 mm of metal" if the hole centres stay and the rails "grow away from their holes"
- **Where the holes sit today** (`rail_checks_final.py` SECTIONS):
  - Every step-pin hole centre is **12.5 mm from the web's outer face**.
  - Lo_L / Up_L: 12.5 above the web underside.
  - Lo_R: 12.5 below the web top.
  - Up_R: 12.5 below the web top, 7.5 above the leg tips.
- **What the instruction produces.** Change list: "Right rails grow downwards; the left channels deepen by the same amount".
  - A Ø21 hole at 12.5 from the web face runs 3 mm into the 5 mm web.
  - It leaves a **2 mm ligament** to the outer face and breaks through the web-to-leg corner.
- **Left channels:** "deepen" has no direction.
  - If they deepen downward so a neighbour's longer right rail still drops in (the stated purpose), the hole ends up 12.5 mm from the **free leg tips**.
  - That leaves a = 2 mm against 17.4 mm required: the edge check goes from 0.87 to about **8.7**.
  - If they deepen upward, the web-side problem above applies instead.
- **What the 0.87 assumes.** `after_changes.py` takes a = 20 mm on a free edge, which the drawn instruction cannot produce.
  - It also uses only the component of the force pointing at the edge, F_perp = 6.79 kN from the Ø10 frame.
- **Fix.**
  - "Rails 70.0 deep. Every step-pin hole centre at mid-depth: 35 mm from the web's outer face and 35 mm from the leg tips. The rails grow 22.5 mm on both sides of the current hole line."
  - Then a = 35 − 10.5 = 24.5 mm. Using the full resultant (≈ 11.2 kN, any direction): a_req = 5.6 + 14 = 19.6, **0.80**.
  - The web is also clear of a Ø20 pin and its nut (see M4). Today, a nut of about 30 mm across flats at 12.5 mm from the web face clashes with the web.

### C3. 70-deep rails remove the catwalk state and restrict the fold (not stated anywhere)
- **Geometry.** The side frame is a parallelogram. The step link runs from the rear pin (25, 12.5) to the front pin (225, 37.5): length 201.6 mm at +7.1°.
  - Perpendicular gap between the lower- and upper-rail pin lines = 201.6·sin(θ + 7.1°):
    - **catwalk 0°: 25 mm**
    - standard 35°: 135 mm
    - steep 49.4°: 168 mm
  - Both rails on a side sit in the same Y band (parts_final bboxes: left −18352…−18317, right −17106…−17081).
  - Today the 25-deep rails, centred 12.5 on the pin lines, stack exactly in catwalk.
- **With Rev C.**
  - As written (grow away from the holes): the rails need ≥ 65–70 mm between pin lines.
  - With the C2 fix (mid-depth holes): 70 mm.
  - Either way, **catwalk (DOUBLE/WIDE catwalk too) is geometrically impossible**, and the fold stops at θ ≈ asin(70/201.6) − 7.1 ≈ **13°**.
  - The transport fold pack gets thicker by the same amount.
- **Status.** The verdict says "catwalk and steep states were not re-checked in Rev C". The change list does not warn Gerald.
- **Fix.** This needs an owner decision on the change list:
  - either (a) Rev C units are stair-only (catwalk dropped; state the minimum fold angle),
  - or (b) the upper and lower rails move to different Y planes (for example the upper rail outboard of the lower), so they can overlap in depth. That is a new layout and needs re-checks.

### C4. The barrier load path through the steps (pin axial force) is assumed but never checked
- **The assumption.** `barrier_path_check.py` treats the step pins as the lateral supports of the rails: the pole couple F = 14.4 kN sits between pins at a/b = 138/167 (lower) and 106/199 (upper).
- **Reaction per pin, along the pin's axis:**
  - up to **7.9 kN** at the lower rail (F·b/(a+b))
  - up to **9.4 kN** at the upper rail (F·a/(a+b))
- **What carries it.** An outward push pulls the rail away from the step, so the pin is in tension. That force goes through the retainer (castle nut in Route 1, R-clip in Route 2), the pin head, the end plate and the end-plate-to-box joint.
  - None of these is checked. An R-clip cannot carry 9 kN.
- **Fix.**
  - "Step pins are headed on the step side, with a full nut (M20, 8.8 zinc-flake steel or A4-70) inside the rail wall, and are checked for 9.4 kN axial tension combined with 11.2 kN shear."
  - Also check nut pull-through on the 5 mm wall (Ø30 washer) and the end-plate joint for the same axial force.
  - Route 2 R-clips are only acceptable if a separate element takes the lateral force.

---

## MAJOR

### M1. The 70-deep U legs are class 4 slender outstands; no script applies local buckling
- **Classification.**
  - Leg flat 65 mm, t = 5, so β = 13.
  - EN 1999-1-1 Table 6.2 limit for a class A outstand is β3/ε = 6 (ε = 1). So the legs are **class 4**.
  - Today's rails (β ≈ 4) are not.
- **Effect on the lateral check.** Pole push bends the rail about its vertical axis, so one leg is in uniform compression.
  - ρc = 10/13 − 24/13² = 0.63.
  - My estimate of W_eff / W_gross: right rail ≈ 1/1.69, left ≈ 1/1.61.
  - Right lateral: 0.82 (at 65 deep) → 0.77 (gross at 70) → **≈ 1.3, fail**.
  - Left: ≈ 0.77.
- **Effect in-plane.** Hogging puts the leg tips in compression, so the in-plane values in M3 also drop.
- **Status:** estimate only; not verified with a full effective-section calculation.
- **Fix.** Run the EN 1999-1-1 §6.1.5 effective-thickness check. If it fails:
  - right rails with 6–8 mm legs,
  - or a lipped or closed right-rail section (mind the nesting and nut access),
  - or 35 wide like the left.

### M2. In-plane and lateral rail bending are never combined
- The crowd case (in-plane 0.33–0.63, see M3) and the barrier case (lateral 0.82) are checked separately. A viewing crowd on the stair leaning on the barrier is one situation.
- At the right rails even ψ0 = 0.7 on one action gives about 1.0–1.3 (not verified).
- **Fix:** add σ_N + σ_My + σ_Mz ≤ f0/γM1 on the effective section for "crowd + barrier" (EN 1990 6.10 with ψ0).

### M3. The rail "net W 7,193 / 7,494 mm³, W needed 2,900, 0.40" figures are hard-coded and not traceable
- **Hard-coded values.** `after_changes.py` line 54 types in 7494, 7193 and 2900. No script computes them, and axial force is ignored.
- **My re-run with 70-deep sections** (`rv70.py`, `rv70b.py`, same loads, both base conditions, pattern loading):
  - Rail M_max is 657–661 kNmm at the top-tread station. That confirms 2,900 = M/fd.
  - The link force falls to 9.04–9.09 kN (from 9.87).
  - Utilisation (σ = N/A + M/W):

    | Net section assumed | Utilisation |
    |---|---|
    | Hole at mid-depth, outer leg intact | **0.33 / 0.36** (Lo_L / Lo_R) |
    | Hole at mid-depth, outer leg fully windowed (as in today's net section) | **0.60 / 0.63** |
    | Hole 12.5 from the web face | 0.40 |

- These pass before M1/M2.
- **Fix:** compute the section in the script and state on the drawing whether the outer-leg window or J-notch still exists with box steps. Quote 0.33–0.63, not 0.40.

### M4. Pin retention does not fit, and the thread must not sit where the pin bends
- **Right side.**
  - The pin ends in the right rail's inner wall. The rail interior is 25 − 2×5 = **15 mm** wide.
  - An M20 castle nut is 24 mm thick (DIN 935), or 16 mm for the low type (DIN 937), plus the split pin. It does not fit.
- **Left side.**
  - The retainer sits inside the left channel. That is where a neighbour's right rail nests, and it is line-to-line (25 / 25), so they clash in the side-by-side layout.
- **Threads.**
  - If the M20 thread (minor diameter 16.9) reaches the section where the pin bends or shears, W falls to 0.60×.
  - Pin bending then goes from 0.66 to **1.10**.
- **Fix:**
  - "Plain shank from the end plate through the full rail wall; thread only beyond the wall face."
  - Draw the pin in 3D with its nut and split pin, and show the nested pair (WIDE layouts).
  - Give every pin length: left ≈ end plate + 1 + 5 + nut; right ditto.
  - Drop the castle nut in favour of a thin nut with a drilled pin, or a headed pin with a retaining collar.

### M5. The step pin is assumed moment-fixed in a 5 mm end plate across a 14 mm gap
- **The assumption.** M = V·14 = 156 kNmm is a cantilever from the end plate. In the FE, the pin is tied rigidly to the end-plate nodes.
- **Why it fails.** A pin with 0.5 mm clearance cannot be clamped against that moment by a 5 mm plate: the edge-bearing couple would be ≈ 156,000/5 ≈ 31 kN.
  - In reality the pin rotates and bears unevenly on both plates. That needs a proper single-shear-with-packing check, or a boss.
- **Fix (simpler and lighter, see Alt-2):**
  - Put the end plate against the rail wall with a 1 mm acetal washer only. Lever ≈ 4 + 1 + 2.5 = 7.5 mm.
  - Then **Ø16** passes: M = 10.4 kN × 7.5 = 78 kNmm against MRd = 1.5·402·250/1.25 = 121 kNmm, **0.65**. Shear 0.37; bearing on 5 mm 0.43.
  - `after_changes.json` "d16_gap7" already shows 0.65.
  - A Ø17 hole needs a ≥ 14.7 mm instead of 17.4.

### M6. The pin hole size is stated three ways
| Source | Hole |
|---|---|
| Change list | "Ø20 holes" |
| Manufacturing | "reamed Ø20 H9" and "about 0.5 mm clearance per side" |
| after_changes | d0 = 21 |

- A Ø20 pin in a Ø20 H9 hole has no clearance and cannot be assembled on site with 24 pins.
- **Fix:** "Pin Ø20 h9 (Ø16 h9 if Alt-2). Hole Ø21.0 +0.1/0 (Ø17), drilled and reamed on a jig through both rails together."

### M7. Bush and spacer material
- "Acetal bushes" (manufacturing guide) under a radial pin load: 11.2 kN / (20×5) = **112 MPa**. Acetal's allowable bearing is about 20–30 MPa.
- **Fix:** "The 7 mm part is an axial spacer only; the pin bears directly on the aluminium (or on a pressed-in stainless or bronze bush, checked)." Give the spacer OD, ID and length.

### M8. Route 2 stainless pins are weaker than the 6082 checks assume
- Annealed 1.4401/1.4404 bar has Rp0.2 ≈ 200–220 MPa, which is below the 250 used.
- Bending then goes 0.66 → 0.75–0.83. EN 1999 pin formulas do not apply to stainless steel.
- **Fix:** specify cold-drawn 1.4404 with Rp0.2 ≥ 350, or 1.4462, check it to EN 1993-1-4, and isolate it from the aluminium (manufacturing rule).
- Also consider stainless pins in Route 1: an aluminium pin in an aluminium hole galls and wears with repeated site assembly.

### M9. "With drain holes, FE-verified" is not true for box A
- `tread_box2.py` has no holes. The datasheet says "both with drain holes, FE-verified".
- "Holes up to about a fifth of each plate" is not a dimension (a fifth of the area? of the 90 mm cell width?).
- The governing stress is local plate bending of the 3 mm deck at the web at x ≈ 186 (93.5 MPa ULS). Holes in the deck cells raise it.
- **Fix:** specify, for example, "Ø10 holes, 1 row on the centre line of each of the 3 cells, 50 mm pitch, top and bottom, first hole 40 mm from the end plates". Then re-run the FE with the holes.

### M10. Can the step actually be extruded, and what does the serration do?
- **Die size.** A 280 × 50 four-cell hollow with 2 mm walls has a circumscribing circle ≈ 285 mm. That is a large press.
  - 2 mm walls in 6082 at that size are generally below what extruders offer.
  - Not verified: obtain the minimum wall from the extruder.
- **Alternative alloy.** 6005A-T6 (f0 225 for t ≤ 5) gives 0.41 × 250/225 = **0.46**. This is the likely production alloy.
- **Serration.** "Serrated step tops" must be added on top of the 3 mm deck; the FE uses a plain 3 mm plate. State it as "3.0 mm minimum under the serration".

### M11. How the Route 2 bent box gets built is undefined
- The internal webs of a closed box cannot be fillet-welded or riveted normally after closing.
- The FE assumes the webs are continuously joined to the deck and bottom.
- **Fix:** specify slot or plug welds through the bottom (5083), or blind structural rivets at a stated pitch (≤ 50 mm), checked for the shear flow. Estimate ≈ 60 N/mm at 3 kN shear; not verified.
- Say explicitly that a bent 6082-T6 box is not permitted (3 mm T6 cracks in tight bends), because `after_changes` still lists "A_bent_6082_welded".

### M12. Base clearance for the right lower rail
- If Lo_R grows 45 mm downward (as written), its bottom edge drops by 45/cos35° = 55 mm, from z −64.8 to **≈ −120** at the base end.
- Footplate top is −119.9 and the ground is −124.9 (E5190_E08). The rail meets the jack footplate.
- With the C2 mid-depth fix it drops only 27 mm, to ≈ −92. Not verified in 3D.
- **Fix:** check with the rail end outline and trim or chamfer the rail end; state the minimum jack extension.

### M13. Option C grating openings are too large for a public walkway
- Bars at 46 mm pitch and cross bars at 50 mm leave clear openings of about **43 × 47 mm**.
- That is over the usual walkway limit (a 35 mm ball; 20 mm where people pass underneath, EN ISO 14122-2) and a heel trap.
- The FE also models "press-locked" crossings as fused (shared nodes). The end bars would be welded to the end plates, which is the HAZ case at 0.54–0.63.
- **Fix:** if C is kept, use cross bars at ≤ 25 mm pitch and bars at 34 mm (G4, 0.72, 7.1 kg), and re-run the FE with realistic crossing stiffness. Otherwise drop C.

### M14. The R7 lip is under-specified and has no tolerance
- The gap is 175 − 50 = 125 mm, so "at least 5 mm" gives exactly 120 with zero tolerance.
- **Fix:** "Front lip 15 mm down × 3 mm, part of the extrusion (open gap 110 mm)", and check it against the fold clearance with the step below.
- The recommended 35 mm lip needs a fold-clash check (not verified).

---

## MINOR

- **70 vs 65.**
  - after_changes comment: "rails 65 deep".
  - `barrier_path_check.py` sections: 65 deep.
  - `rails_kg`: 60 mm legs, i.e. 65 deep, about 1 kg per unit light.
  - `frame_after.py`: 70.
  - Change list: "about 70", then "now 70 deep".
  - Fix: "70.0 deep" everywhere, and re-run barrier_path at 70 (right lateral 0.82 → 0.77 gross, before M1).
- **Web positions.** "95 and 185 from the back" should say "web centrelines 95.0 and 185.0 from the outside back face, ±0.5". The FE uses a 2.5 mm mid-surface offset for the 2 mm walls; that is negligible.
- **Pin forces.** Pin forces in after_changes come from the 25-deep frame. With 70-deep rails the link force is 9.09 kN, so pin bending is 0.62 (Ø20, lever 14). The published value is conservative.
- **Missing but passing.** Pin bearing on the 5 mm rail wall is not reported: 11.2/30.0 = 0.37.
- **Deck buckling.** The deck cells are class 4 (b/t ≈ 30). Global compression is ≈ 44 MPa ULS against ρ·fd ≈ 186, so it is fine, but it is not in the FE.
- **Not assessed:** fatigue of repeatedly assembled pinned joints and riveted end plates; torsion of the open U from the pole strap on the outside face.
- **Dates.** Rev C is dated 27 Sep 2026 in after_changes and on the pages; this review is dated 26 Sep.

## Dimensions Gerald still needs (missing or ambiguous)
1. **Rail section:** exact depth (70.0), hole centre measured from the web face (35.0), inner corner radii, which way the left channel deepens, and the outer-leg window or J-notch (kept or removed).
2. **Pin holes:** diameter and tolerance (M6), and position tolerance relative to the rail ends and axle hooks.
3. **Pins:** diameter, total length per side, plain-shank length, thread size and length, head type, retainer (Route 1 vs 2 differ, M4), material grade (M8).
4. **Spacer/bush and washers:** OD, ID, thickness, material (M7). With Alt-2, one 1 mm washer.
5. **End plates:** thickness, outline (height, and whether it drops below the box), hole positions if moved, joint to the box (number, size and pitch of fasteners) (C1).
6. **Box:** outside 280 × 50 tolerance, box length between end plates, web centrelines, corner radii, top thickness under the serration, serration profile.
7. **Drain holes:** diameter, pitch, rows, edge distances, top and bottom (M9).
8. **Lip:** depth, thickness, integral or fixed on (M14).
9. **Contrast nosing strip:** width and position.
10. **Pin-retainer clearance** in the nested (WIDE) layout, and minimum fold angle / catwalk status (C3).

## Better or simpler alternatives (quick checks; confirm with FE)
- **Alt-1: drop-lug end plates, both pins lowered 25 mm.**
  - New pin centres: rear (25, −12.5), front (225, 12.5). The link vector (200, 25) is unchanged, so the frame kinematics and forces do not change.
  - Front hole ligament to the walking surface: 50 − 12.5 − 10.5 = 27 mm, above the 17.5 needed.
  - With mid-depth rail holes, the upper rail's top ends at z 47.5, below the walking surface, so nothing sticks up beside the nosing.
  - Cost: the steps sit 25 mm higher relative to the axles, so re-set the hook or landing heights.
- **Alt-2: close the pin gap and use Ø16 pins.**
  - Lever 7.5 mm: bending 0.65, shear 0.37, bearing 0.43.
  - The hole is Ø17 instead of Ø21, the edge requirement drops to 14.7 mm, and it is lighter.
  - The rails still need about 70 deep for the lateral barrier load, not for the pins.
- **Right rail lateral (M1/M2):** 6 mm legs, or a 30–35 wide right rail. This changes the nesting; decide together with C3.
