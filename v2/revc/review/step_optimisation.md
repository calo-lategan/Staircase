# Step (tread) optimisation for minimum weight, within the owner's L envelope

Date: 27 Sep 2026. Author: lead-designer study (scripts and results in `v2/revc/steps_opt/`). No existing repo file was changed.

## 0. Answer first

**Is there a compliant, drainable, slip-resistant grating step inside the L envelope?** Yes, but it is not light.
- **Recommended step (C8):** 5.54 kg structural (FE model), about **6.2–6.5 kg as built** (with rib flanges, fasteners, serrations and grit inserts).
- It passes every FE load case with 6005A-T6. The worst utilisation is 0.96 (0.82 if 6082-T6).
- It uses extrusions only. There is no welding.

**The lowest structural mass found:**
- About **5.0 kg** (C1): 6082-T6 only, fabricated with internal diaphragms, no margin.
- About **5.7 kg as built**.

**The 60 kg unit target cannot be met through the steps.**
- The non-step parts of Rev C (rails, poles, axles, top rails and handrails, hooks and pins) weigh 52.4 kg (Route 2) or 62.6 kg (Route 1).
- That leaves 1.3 kg per step (Route 2), or less than zero (Route 1).
- With C8 the unit is ≈ 91 kg (Route 2) or ≈ 101 kg (Route 1).
- A 60 kg unit needs about 25–30 kg taken out of the poles and rails as well, or a change in envelope or load basis.

**Two findings block the L envelope regardless of which step design is chosen** (see §5):
1. **Open riser gap = 175 − 25 = 150 mm.** R7 allows 120 mm maximum (100 mm recommended). The 25 mm-thick front zone does not close the gap. A 30 mm lip (50 mm for the 100 mm sphere) or a rear up-stand is needed. Both are owner options.
2. **Front pin at z 37.5.** A Ø16 pin needs its centre at z ≤ 25.5 (Ø20: z ≤ 20.8) to keep the required ligament above the hole. Today the ligament is 4 mm against 16 mm required. This must go to the rails and pins agent.

Tags used: **[FE]** = computed in this study with OpenSees shells (equilibrium balances to 0.1 N in every case). **[H]** = hand calculation (`handcalcs.py`). **[J]** = engineering or trade judgement, to be confirmed.

---

## 1. Basis

**Envelope (owner correction, `step_profile_owner.png`)**
- Available zones: the walking-surface zone x 0–280, z 25–50, and the back member x 0–50, z 0–50.
- Keep-out zone: x 50–280, z 0–25.
- End plates are full depth at the step ends.
- Pins: rear at (25, 12.5), front at (225, 37.5), bearings at 1,215.75 mm centres.

**Loads (events sheet, R-number = line − 1)**

| Case | Requirement |
|---|---|
| R113 crowd | 7.5 kN/m² over the 250 mm going; ULS 1.35G + 1.5Q |
| R114 point load | 4 kN on 200 × 200, anywhere including the front edge |
| R115 deflection | ≤ L/100 = 12.16 mm under 4 kN; ≤ L/250 = 4.86 mm under crowd; < 10 mm under 1 kN (one person) |

**FE load cases.** Eight cases in total:
- ULS 4 kN front, centre and back at mid-span; ULS 4 kN front at the end; ULS crowd.
- SLS 4 kN front; SLS crowd; SLS person 1 kN on 100 × 100 at the nosing.

**Other sheet rows used**
- R7: open riser gap ≤ 120 mm, 100 mm sphere recommended.
- R16 / R94: PTV ≥ 40 wet.
- R17: 55 mm contrasting nosing on both edges.
- R48: platform deck gaps ≤ 25 mm. This is the only opening rule in the sheet that relates to the walking surface. The sheet has **no** tread-opening or heel rule.

**Opening rule adopted [J]**
- Slots **10 mm wide** and **≤ 48 mm long**. No 20 mm ball passes, which also meets EN ISO 14122-2 over occupied areas.
- Heel-resistant. For stiletto-proof openings, use 8 mm slots: open area falls from 20 % to 16 % and mass is unchanged.

**Material**
- Utilisations use σ_vm / (f0 / 1.1). This is the same elastic criterion as the existing tread scripts.
- Primary alloy: **6005A-T6, hollow, t ≤ 5, f0 = 215** (target ≤ 1.0).
- Also shown: **6082-T6, f0 = 250**.
- E = 70 GPa.

---

## 2. Why the L envelope drives the concept

1. **A 25 mm-deep zone cannot span 1.2 m.**
   - Bars or a deck spanning along the step need I ≈ 1.7 × 10⁵ mm⁴.
   - A 25 mm-deep section would need about 660 mm² in each flange, so > 5 kg for the deck alone. The earlier `tread_lattice*.json` results also fail.
   - Only the 50 × 50 back member can carry the 1.2 m bending. The owner's measured design does this too, but with an open J, which has no torsional stiffness. That is why it fails at 3.6× under 4 kN.
2. **Load path.** The 25 mm deck must **cantilever about 230 mm front-to-back from a closed torsion box**, with a stiff nosing that spreads a front point load along the step. Under the ULS front load the torque on the box is about 930 kNmm [H/FE].
3. **Transverse ribs are unavoidable.**
   - A 2–2.5 mm skin cannot cantilever. Ribs (or bearing bars) must run **front-to-back**.
   - Each rib's root moment has to be carried into the box without distorting the box section. The FE showed this is the governing detail:
     - rib butting a plain box wall: 397 MPa (1.94) [FE];
     - with a diaphragm inside the box at each rib, or an extruded diagonal web in the box: 184–190 MPa [FE].
4. **Slot orientation.** In the deck the stress runs front-to-back (the ribs' top flange is the skin). Slots **long in x**, parallel to the ribs, keep the skin working.
   - Slots long in y cut the flange: the skin then fails at 0.84 → > 1 in the tests.
   - So the slots run in the direction of travel but are only 10 mm wide.

---

## 3. Design-space search

**Tools and method**
- Parametric shell FE: `stepfe.py`. It covers the back box, slotted skin with explicit holes, ribs with a bottom flange, the nosing box, the 6 mm end plates, and pins as in `tread_grating.py`.
- Greedy discrete optimiser: `opt.py`, over 12 variables:
  - box walls, box bottom and top thickness;
  - skin thickness;
  - nosing walls, bottom and top, and nosing type (closed / C / L);
  - rib pitch 50–100, rib web thickness, rib bulb size;
  - end-plate thickness.
- Screening cases, then full 8-case runs on the candidates (`cands.py`, `candidates_summary.json`).

**Results of the variable sweep [FE]**
- **Nosing:** an open C or L nosing fails (1.66). The closed 55 × 25 nosing is needed.
- **Rib pitch:** 60 fails at the nosing inner wall (1.08). **50 mm is the optimum.**
- **Rib section:**
  - Flat 3 mm ribs with no bulb fail (1.20; 1.03 in 6082).
  - A 10–12 × 3 bottom bulb is needed.
- **End plates:** 6 mm is enough for the step stresses. Pin bearing and ligament are a separate check (§5).
- **Skin:** 2.0 mm structurally. Use 2.5 mm if the extruder cannot hold 2.0 mm over a 175 mm span (C9, +0.18 kg).

**Candidates (full FE, all 8 cases, equilibrium exact) [FE]**

| # | Concept | FE mass kg | Worst ULS MPa (where) | u 6005A / 6082 | Sag 4 kN, mm (/12.16) | Crowd, mm (/4.86) | Person, mm | Open area |
|---|---|---|---|---|---|---|---|---|
| C1 | Greedy optimum; box 3/3/2.5, diaphragms, skin 2, ribs 2 + 8×3 @ 50 | **5.02** | 203.5 skin (4 kN back) | 1.04 / **0.90** | 11.58 (0.95) | 3.71 | 3.3 | 20 % |
| C2 | As C1 with box bottom 3.5, top 3, bulb 10×3 (fabricated route) | 5.24 | 184.4 skin | **0.94** / 0.81 | 10.79 (0.89) | 3.44 | 3.1 | 20 % |
| C3 | C2 with flat 3 mm ribs, no bulb | 5.29 | 234.9 rib root | 1.20 / 1.03 ✗ | 10.92 | 3.47 | 3.2 | 20 % |
| C4 | T-bar grating (bars in x @ 20, top 10×2, Ø5 rods, bars through box) | 6.45 | 173.1 | 0.89 / 0.76 | 11.51 | 3.72 | 3.3 | 28 % |
| C6 | Extruded closed box + 2.5 diagonal web (no diaphragms), bulb 10×3 | 5.47 | 206.5 rib flange | 1.06 / 0.91 | 10.09 | 3.18 | 2.9 | 20 % |
| **C8** | **C6 with bulb 12×3 (RECOMMENDED, production)** | **5.54** | **187.2 rib flange at root** | **0.96 / 0.82** | **10.05 (0.83)** | **3.18 (0.65)** | **2.9** | **20 %** |
| C9 | C8 with 2.5 mm skin (extruder-safe) | 5.72 | 189.4 | 0.97 / 0.83 | 10.03 | 3.17 | 2.9 | 20 % |
| C5/C7 | Owner option: 30 mm nosing lip | 5.00 / 5.24 | 250–288 at the lip tip | ✗ as modelled | 9.4 / **8.5** | 3.0 / 2.8 | 2.4–2.7 | 20 % |

**Notes on the table**
- The pin-hole rigid-link peak (≈ 114 MPa) is an idealisation and is excluded. The end plate away from the pins is ≤ 125 MPa.
- **Bar grating (C4) is 1.2–1.4 kg heavier than the slotted skin.** The reason: every bar needs its own root moment connection into the box. A slotted skin with ribs at 50 mm needs a root connection only once per 50 mm.
- **The lip options are not converged.**
  - With a lip, the nosing becomes a 55 mm-deep beam and all deflections fall about 20 %.
  - The plain 2–3 mm lip tip is over-stressed as modelled. It needs a bulb of about 10 × 3 mm, which was not run.
  - Estimate once the lip has its bulb: about 4.8–5.0 kg FE for a compliant step [J].

**GRP / FRP check [H]**
- Same geometry in pultruded FRP (E ≈ 25 GPa): sag 28 mm against 12.16 mm. Fails.
- For equal stiffness it needs about 2.8× the thickness, so ≈ 8–9 kg. Composite design factors are also larger.
- Custom L pultrusions cost more than aluminium extrusions [J].
- **Not recommended.**

---

## 4. Recommended step C8: dimensions for the drawing

Tread-local axes: x 0 = back face → 280 = front face; z 0 = underside of the back member → 50 = walking surface; y along the span. End-plate mid-planes are at y 17.5 and 1,212.5, so the members are 1,195 mm long. The dimensions below are mid-surface positions converted to outside faces.

| Part | Specification |
|---|---|
| **Back box** (6005A-T6 extrusion, closed) | 50 × 50 outside.<br>Rear wall 2.5; **front wall 4.0**; bottom 3.5; top 3.0 (the top is the rear 50 mm of the walking surface: serrated, with one grit strip).<br>**Internal diagonal web 2.5**, from the front wall at z 26.5 (the rib-foot node) to the rear-top corner.<br>External ledge on the front face at z 25–28 for the rib feet, with a screw groove.<br>Screw ports for M8 in the 4 corners.<br>Drain/vent holes Ø6 in the bottom at both ends of each cell. |
| **Deck skin** | **2.0 mm** under the serration, x 50 → 225, continuous along y. Integral with the box top (one "deck-box" extrusion, CCD ≈ 232 mm), or C9 at 2.5 mm if the extruder asks for it.<br>**Slots 10.0 wide (y) × 47.7 long (x)**, 3 per column at x 56–103.7 / 113.7–161.3 / 171.3–219, with 10 mm bridges.<br>2 columns per 50 mm rib bay: 12 mm solid over each rib, then 5 / slot 10 / 8 / slot 10 / 5.<br>46 columns in total; the first and last bay have one column, ≥ 20 mm from the end plates.<br>**Open area 19.7 %** of the 280 × 1,195 plan. |
| **Ribs** (6005A-T6 x-direction extrusion, cut to 175) | 23 ribs at **50 mm pitch**, centred on the span (y 65 … 1,165).<br>Section: web 2.0 × 22 (z 28 → skin); bottom bulb **12 × 3** (z 25–28); top rivet/bond flange 12 × 2 (not in the FE, conservative).<br>Rib runs x 50 (foot on the box ledge) → 225 (into the nosing inner wall). |
| **Nosing** (6005A-T6, closed) | 55 × 25 outside (x 225–280, z 25–50), walls **2.0**. Specify the **top at 2.5** or with a centre grit-groove stiffener: a plain 55 / 2.0 top is class 4, ρ ≈ 0.92 [H].<br>Top: 50 mm **contrasting grit insert** in an extruded dovetail recess. Front face: contrasting 20 mm band (R17, both edges).<br>Drain holes Ø6 in the bottom at 200 mm pitch. |
| **End plates** | 6 mm 6082-T6, 280 × 50 (full depth at the ends), no welding.<br>4 × M8 A4-70 into the box screw ports and 2 × M6 into the nosing.<br>Pin holes per the rails agent: see §5 for the front-pin position. |
| **Joints** | Ribs to skin: structural epoxy on the 12 mm flange plus 3 self-piercing or blind rivets.<br>Rib foot: 1 × M5 into the ledge groove, or 2 rivets. Rib front: 1 rivet.<br>Nosing to deck: interlocking hook plus a rivet every 100 mm. |

**Mass**
- FE model: 5.54 kg.
- Add-ons: rib top flanges 0.26, serration ridges ≈ 0.36, fasteners 0.20, inserts 0.10.
- **As built: ≈ 6.2–6.5 kg per step, ≈ 37–39 kg for six [H].**

**Utilisations (ULS, 6005A-T6 f0 215 / 6082-T6 f0 250) [FE]**

| Location and case | MPa | Utilisation 6005A / 6082 |
|---|---|---|
| Rib bottom flange at the root, 4 kN front | 187 | **0.96** / 0.82 |
| Nosing inner wall | 175 | 0.90 |
| Box front wall at the rib foot | 172 | 0.88 |
| Skin, 4 kN centre / back | 165 / 160 | 0.84 / 0.82 |
| Box bottom | 151 | 0.77 |
| 4 kN at the end | 127 | 0.65 |
| Crowd ULS | 48 | 0.25 |

**Deflections and frequency**
- Sag under 4 kN at the front: **10.05 mm** against 12.16 (**0.83**).
- Crowd: **3.18 mm** against 4.86 (**0.65**).
- Person at the nosing: **2.9 mm** against 10.
- Twist under 4 kN: 0.8°.
- First vertical frequency of the step: ≈ 65 Hz empty; ≈ 13–18 Hz with 0.3–0.6 of the crowd mass [H, beam formula from the FE sag].

**Joints [H]**
- End screws: 4.1 kN per M8 against 10.2 kN (0.40). End-plate bearing 0.25.
- Barrier axial force of 9.4 kN per end → 1.6 kN per screw in tension. Screw-port pull-out to be confirmed by test [J].
- Rib-to-skin shear flow 52 N/mm:
  - 4.3 MPa on the adhesive;
  - or 1.3 kN per Ø4.8 rivet at 25 mm pitch against about 2.1 kN (0.62).
- Rib foot bearing force: 6.7 kN into the ledge.

**Slip strategy (R16/R94, PTV ≥ 40 wet)**
- Extruded ridges about 0.8 mm high at 3–4 mm pitch, running along y, i.e. across the direction of travel, on the skin, box top and nosing.
- Slot bridges give further edges.
- Two grit inserts: the 55 mm nosing strip and one strip on the box top.
- Anodised or bare finish, no paint on the top.
- **Must be proven** by an EN 16165 pendulum test on prototype 1, in both directions, slider 96 wet. Fallback: a thin epoxy-aggregate coating on the whole top (+0.15 kg).

**Drainage**
- 10 mm slots over the whole deck; the underside is open, so water falls straight through.
- The box and nosing tops are narrow (50 / 55 mm) and shed water.
- Closed cells have low drain and vent holes at both ends. This also covers anodising and freeze risk.

---

## 5. Blocking and open items (not solvable inside the step)

1. **Riser gap, R7 [H].**
   - Gap = rise 175 − front-zone thickness 25 = **150 mm** over the 30 mm overlap. It fails the 120 mm maximum and the 100 mm recommendation.
   - The earlier "175 − 50 = 125" figure (review M14) assumed a 50 mm-thick step everywhere.
   - Owner options:
     - (a) nosing lip **30 mm** below z 25 (50 mm for the 100 mm sphere). It lies in the keep-out zone, so fold/stack clearance must be checked. Structurally it helps: C7 sag falls 16 %. It needs a 10 × 3 bulb.
     - (b) a 30–35 mm up-stand at the rear of each step, under the nosing above. Check it against folding.
2. **Front pin ligament [H].**
   - With the front pin at z 37.5, a Ø17 hole leaves **4 mm** to the walking surface; about 16 mm is required.
   - The front pin centre must be ≤ z 25.5 (Ø16) or ≤ z 20.8 (Ø20).
   - Alternative: Alt-1 drop-lug end plates with both pins lowered 25 mm, which keeps the link vector.
   - The FE result for the step is insensitive to where the pin sits in the rigid end plate.
3. **Not modelled.**
   - Joints are modelled as rigid (fused). The epoxy and rivets must be proven in the prototype test.
   - No explicit local-buckling or nonlinear run. The classes were checked by hand: skin strips b/t ≤ 5, box walls ≤ 20 (class 3), nosing top as above.
   - No fatigue check (EN 1999-1-3).
   - Barrier axial force through the end plate: checked by hand only.
4. **Tolerance on the numbers.**
   - C8 has 4 % stress margin at 6005A.
   - If the extruder cannot supply 6005A with f0 215 in the rib bulb, use a 14 × 3 bulb (+0.03 kg) or 6082-T6 ribs.

---

## 6. Prototype (×2) and production

### Prototype (stock material, waterjet, no dies)
- **Box:** 6082-T6 50 × 50 × 3 channel (U) with a 3 mm top plate. The diagonal web is replaced by **internal diaphragm plates at each rib** (C2 route, u 0.94 / 0.81, sag 10.8). Diaphragms and ribs are **one waterjet L-plate** each (3 mm 6082-T6: 50 deep over the box, 25 deep in front).
- **Rib bulb:** a riveted 12 × 3 6082-T6 flat bar.
- **Skin:** waterjet-slotted 2.5 mm 6082-T6 sheet, with grit tape or an epoxy-aggregate top in place of extruded ridges.
- **Nosing:** 6082-T6 rectangular tube 60 × 25 × 2 machined to 55, or a bent 5754 channel plus a riveted strip.
- **Joints:** bonded (2-part structural epoxy) plus Ø4.8 structural blind rivets. No welding.
- **Mass:** about 6.5–7 kg.
- **Tests:**
  - Proof load 6 kN on 200 × 200 at the front, mid-span, and at the end.
  - Sag under 4 kN (≤ 12.16) and under 1 kN.
  - Crowd sandbag test.
  - Pendulum PTV wet.
  - 20 mm ball / heel check.
  - Fold-clearance check in the frame.

### Production (100s–1000s)
- **Extrusion 1 "deck-box":** box with the diagonal web and ledge, plus serrated skin to x 225. 6005A-T6, CCD ≈ 232 mm.
  - Or split into box + skin with an interlocking seam if the extruder prefers; then re-check the seam, since the skin peaks at x 54.
- **Extrusion 2:** nosing with the grit groove and a hook to the skin.
- **Extrusion 3:** rib T-bulb profile, cut to 175 mm.
- **Punching:** slots punched in one hit per column; the skin is open underneath, so a die can back it.
- **Assembly:** a jig with robot adhesive dispense plus about 70–100 self-piercing rivets per step.
- **End plates:** laser-cut or punched; screws into the extruded screw ports.
- **Finish:** anodise, then the grit inserts.
- **Die cost:** small for extrusions 2 and 3; medium for extrusion 1 [J]. Ask 2–3 extruders for a DFM review of 2.0 mm walls at a 232 mm CCD.

**Rejected for production**
- Welding: HAZ ρ 0.5 exactly at the rib roots, where the moment peaks.
- Press-locked bar grating: C4, +1.2 kg, and each bar needs a moment root.
- GRP.
- Castings: size and ductility.

---

## 7. What this means for the 60 kg unit

| | Route 2 (RHS poles) | Route 1 (solid poles) |
|---|---|---|
| Non-step parts | 52.4 kg | 62.6 kg |
| + 6 × C8 as built (≈ 6.2–6.5 kg) | **≈ 90 kg** | **≈ 100 kg** |
| Step budget for 60 kg | 1.3 kg per step (not achievable) | < 0 |

- **Lowest achievable step, structural:** ≈ 5.0 kg (C1, 6082-T6, fabricated, no margin), about 5.7 kg as built.
- **Recommended:** 5.5 kg FE, ≈ 6.2–6.5 kg as built.
- **The L envelope costs about 1 kg per step** compared with a full-depth open-bottom slotted plank. That plank would use the whole 280 × 50 section for bending (estimated about 4–4.5 kg as built [J]), but the owner's envelope rules it out.
- **Smallest envelope change that pays:** allow the 30 mm nosing lip. It is needed anyway for R7, and the resulting 55 mm-deep nosing beam should bring the step to about 4.8–5.0 kg FE [J, to be run with the lip bulb].
- **The rest of the 60 kg target must come from the poles and rails** (≈ 40 kg together today).

## Files (`v2/revc/steps_opt/`)
- `stepfe.py`: parametric shell FE (L envelope).
- `quick.py`: one-line variant runner.
- `opt.py`, `cfg_skin*.json`, `opt_skin2.json` / `.log`: greedy optimiser and its log.
- `cands.py`, `cand_C*.json`: full-case FE of the candidates.
- `candidates_summary.json`: the candidate table.
- `handcalcs.py`, `handcalcs.json`: mass, unit budget, riser gap, pin ligament, joints, frequency, GRP.
- Copies of the repo FE used as the base: `tread_grating.py`, `tread_fe2.py`, `tread_box2.py`.
