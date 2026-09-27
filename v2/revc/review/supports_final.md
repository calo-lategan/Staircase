# Supports, final design (Rev C, 27 Sep 2026): base and top

Scope: this report resolves supports review C1–C5 and M1–M7 for the Rev C unit. The unit has:
- the nested open-channel rails from `rail_design.md` (production box pole, lock at both rails);
- the owner-accepted mass of about 117 kg;
- the catwalk and 35° states.

**Scripts and results** (new folder `v2/revc/supports_final/`; no existing file was changed). Run them in this order:
`frame_supports.py` → `supports_checks.py` → `hook_fe.py` → `ring_fe.py` → `supports_checks.py`.

| File | What it does | Output |
|---|---|---|
| `frame_supports.py` | OpenSees side frame. A copy of `rails/frame_rails.py` with the new support positions and the lower-rail ends. Self weight is scaled so the unit weighs 116.6 kg. | `frame_supports.json` |
| `hook_fe.py` | Plane-stress FE of the rail-end hooks. 1 mm quads, each carrying the projected thickness of the channel elements. Gap contact to the tube and to the keeper. | `hook_fe.json` |
| `ring_fe.py` | Local crushing of the tube between the hook and the fork, with and without a solid insert. | `ring_fe.json` |
| `supports_checks.py` | 3D lateral statics, wind, EQU, all component checks, dimensions and masses. | `supports_final.json`, `supports_checks_loads.json` |

Tags used in this report:
- **[C]** computed;
- **[E]** estimate or assumption.

R-numbers are sheet rows (R = sheet line − 1).

## 0. Answer

**One design passes both base conditions**, provided the ties listed in §3 are fitted. The two base conditions are:
- on the ground, with μ anywhere from 0.3 to 0.5;
- clamped to a scaffold.

Three things in the Rev C geometry could not be kept.

1. **The base axle has to move 188 mm up the rail.**
   - The Rev C axle centre (x 9,636.1, z −89.4) is only **35.6 mm above the ground** (z −125, the IFC footplate underside). No real screw jack fits under it.
   - Any hook turned over the axle needs rail metal above the tube. The rail's far face at that point is only 17 mm above the ground.
   - New base axle: **x 9,468.9, z 0.0**. That is 125 mm above the ground, at lower-rail station s = 46 and n = 60 (the B_lo far face) [C].
   - Tread 0's rear pin is 46 mm down the rail from it. The support span along the rail drops from 1,831 to 1,610 mm.
   - The rails benefit: the in-plane envelope is 82.6 MPa against 142.7 MPa, both computed with the same conservative formula [C].
2. **The jack spacing cannot stay 1,373.**
   - The old centres (y −18,404 / −17,031) are 76–87 mm outboard of the pin-leg faces, i.e. **inside the new 108/115 channels**, under the web.
   - A head there leaves the Rev C problem in place: a hook-to-head lever of 70–84 mm (M1).
   - New design: **forks that straddle the hook** (supports review A5).
   - Support centres are 10 mm outboard of the pin-leg faces: **y −18,327.5 / −17,096.5, 1,231 apart** [C].
   - The lever in the axle falls to 7 mm, so axle bending is 0.03.
3. **The unit cannot stand free.**
   - Barrier (R142), wind (R151/R181) and a person on the bottom tread all lift the supports.
   - The keepers are therefore **structural**, not nominal. The task allowed "unless shown otherwise"; this is shown in §3.
   - The top is always bolted or coupled. The base is anchored (ground) or coupled (scaffold).

**Materials.**
- Aluminium everywhere on the unit except the **base axle**. That is steel S355 48.3×4 (EN 10219), because EN 74-1 couplers are rated on steel tube. This is the "clearly better and standard" exception.
- The jacks and landing brackets are site kit in galvanised S355.
  - Jacks: covered by the owner's steel exception.
  - **Landing brackets: steel is my proposal and needs the owner's OK.** An unwelded 6082 bolted version is possible but was not checked.

Masses:
- Support parts carried on the unit: **9.8 kg**, against 7.7 kg in the mass budget. The unit is therefore **about 118.7 kg**.
- Switching the base axle to aluminium saves 3.85 kg, but only if the coupler supplier declares class B values on 48.3×4 aluminium tube.

## 1. Loads [C] (`frame_supports.json`, `supports_final.json`)

The frame run uses the new rails, pins and locks, with loads as in `rails/frame_rails.py`. Sway R176 is added along the flight: 10 % of the imposed load, 169 N per tread per side at ULS.

| Per side, ULS | Base held (scaffold) | Base slides (ground, μ → 0) | Ground μ 0.3 | Ground μ 0.5 |
|---|---|---|---|---|
| Base reaction R (angle) | **11.64 kN** (62–132°) | 7.60 kN (90°) | 10.04 kN | 11.64 kN (= held) |
| Base H / V | 4.90 / 10.69 kN | 0 / 7.60 kN | 2.88 / 9.61 kN | 4.58 / 10.69 kN |
| Top reaction R | 5.60 kN (−25…+157°) | 4.48 kN (−90…139°) | 4.12 kN | 5.60 kN |
| Top uplift (person on tread 0, EQU) | 0.99 kN | 0.72 kN | | |

- The held case now needs H/V = 0.46, so μ 0.5 friction reaches it. The Rev C value was 0.77.
- There was no base uplift in any frame case.

**Lateral and overturning (3D statics, per unit).**
- Loads:
  - barrier on 1.83 m of rail: 13.73 kN ULS at 5.0 kN/m, 8.24 kN at 3.0 kN/m;
  - acting at the top rail: 1,100 mm above the pitch line (R63), which is **1,374 mm above the support line**;
  - sway along the axle, R176: 2.03 kN at deck level.
- Two ways of sharing the overturning couple:
  - r1: half at the base, half at the top (base anchored or clamped);
  - r0: all at the top (base not anchored; the torsion path through the unit is **not verified**).

**Wind [E].** The site value is not in the repo, so these are assumptions:
- storm q_p = 0.85 kPa; operational (OWS) 0.20 kPa;
- c_f 2.0; leeward side at 0.8;
- 0.618 m² per side, centroid 575 mm above the support line;
- F_w,k = 1.89 kN lateral, plus 0.86 kN uplift on the treads.

## 2. Final design: what Gerald draws

### 2.1 Dimension table (all [C] unless marked)

| Part | Dimension |
|---|---|
| **Lower-rail hooks** (cut in A_lo / B_lo, no separate plate) | **Saddle:** semicircle R 24.5 (bore Ø49.0 +0.3/0), centre on the far-face line n = 60. It sits at s = **46** (base) and s = **1,656** (top), and is cut through the pin leg and bulb. It covers −35° to 145°. |
| | **Ring (metal above the bore):** 35.5 mm normal to the rail, of which the bulb zone is n 0–27. |
| | **A_lo only:** pin leg trimmed from n 61 to n 60 over the window. |
| | **Web window:** web removed from y 6 to 70 over s_c ± 45; from y 6 to 32 over the fork jaw (to s_c + 58 at the base, to s_c − 58 at the top). The outer web strip with the lip / outer leg stays. |
| | **Keeper hole:** Ø12.5 H11 at n 36; s 82 at the base (uphill of the saddle), s 1,620 at the top (downhill). |
| | **Rail ends:** base end cut square at s −30 (was −115.7). Top end cut vertical at x 8,128, i.e. 22 mm uphill of the top axle (s 1,724.6 at n 0; the lower rails get about 113 mm (L) / 139 mm (R) longer). |
| Axle positions | Base (x 9,468.9, z 0.0), 125 above the ground. Top (x 8,150.0, z 923.4), 38 mm clear of the bracket plate. Rev C positions were (9,636.1, −89.4) and (8,135.8, 960.6). |
| **Base axle** | 48.3 × 4.0 S355J2H (EN 10219), hot-dip galvanised, **L = 1,343** (±671.5 from the stair centre line y −17,712). |
| **Top axle** | 48.3 × 4.0 EN AW-6082-T6, L = 1,343. |
| **Inserts (all 4 supports)** | Solid 6082-T6 Ø40 h11 × 90, centred on each fork. Fixed by a Ø8 × 55 roll pin through tube and insert at the fork centre (axle moment there is about 0.08 kNm). |
| **Collars** (4) | Split clamp collar 6082-T6, bore 48.3, OD 70, width 25, 2 × M10 8.8 at 40 Nm. Positioned **636.5–661.5 from the centre line**: just outboard of each fork's outer jaw, 10 mm from the axle end. |
| **Fork** (jack head and landing bracket alike) | Two 8 mm S355 jaws parallel to the rail, **inner gap 24**, inner faces at −2 / +22 from the pin-leg face. U-seat R 24.5 with 2 mm to the fork base. Keeper hole Ø12.5 on R 43.3 from the axle centre; add a **second hole rotated 35° for catwalk**. |
| **Keeper pin** (4) | Ø12 × 60 A4-80 headed clevis pin. R-clip on a lanyard (captive). Ø16/12.5 × 15 A4 spacer bush on the outboard side. Double shear. |
| **Jack** (site kit, 2 per unit) | **Base plate:** S355 **250 × 250 × 12**, 4 × Ø22 holes on a 200 × 200 pitch (for stakes, anchors or bolts). M36 nut (ISO 4032) welded **under** the plate, a5 all round, over a Ø38 hole. |
| | **Spindle:** M36 8.8 rod, 150 long, with an M36 thin lock nut on the plate. |
| | **Fork base:** 12 × 80 × 60, tapped M36 and fillet a6 all round to the rod. |
| | **Range:** plate underside to axle centre 68 min – **150 max**, i.e. **maximum exposed thread 82 mm**. Nominal on 38 mm boards: 87. |
| Sole boards (R76) | 2 scaffold boards, 225 × 38 × 600, side by side (450 × 600). Jack plate bolted through them. |
| **Landing bracket** (2) | S355 galvanised. **Back plate:** 12 × 160 (y) × 200 (z). **Bolts:** **4 × M12 8.8 through-bolts** on a 110 × 150 pitch with 40 mm washers. **Jaws:** fork as above, 110 × 110, welded a5 both sides. |
| | Scaffold landing: replace the back plate with a 48.3 × 4 S355 stub, 300 long, fixed by 2 × EN 74-1 class B right-angle couplers. **No wing clamps.** |
| Scaffold-clamped base | 2 × EN 74-1 class B right-angle couplers per jack, on the steel axle, within 100 mm inboard of the fork. They connect to a standard or ledger at axle level. |

### 2.2 Load paths
- **Vertical:** rail pin leg (saddle) → tube with insert → fork seat → spindle or bracket.
  - The keeper carries nothing in any crowd case. The reaction angles are 62–132° (base) and up to 139° (top), all inside the saddle.
  - Uplift / pull-out goes rail → keeper → jaws. The cases are:
    - person on tread 0: 0.99 kN at the top;
    - top pull at 157°: 2.9 kN;
    - barrier / wind EQU: 7.2 kN base, 7.7 kN top.
- **Along the axle (barrier R142, sway R176):** pin leg → fork jaw (direct bearing, no collar slip) → head.
  - **Ground case:** all lateral load goes to the top brackets: 6.9 kN each, plus a ±9.7 kN x-couple from torsion. The jacks see only friction, which is checked at H = 0.5 V in any direction.
  - **Scaffold case:** lever rule, base share 4.5 kN per jack. It goes jaw → collar (9.1 kN if one collar takes both sides) → steel axle → couplers.
- **Along the flight (thrust, R176 sway):**
  - held case: into the couplers (scaffold) or friction (ground, ≤ 0.5 V);
  - slides case: all to the top brackets, 1.0 kN sway.
- **The unit cannot walk downhill (M6):** the top is bolted and the top keeper is fitted.

## 3. Pass/fail (`supports_final.json` → `checks`)

The governing rows are listed below. The full 52 rows are in the JSON.

| # | Check (review item) | Ed / Rd | Util | Status | Tag |
|---|---|---|---|---|---|
| 1 | Base reaction inside the saddle, 5° margin (C4) | 132.4° / 140° | 0.95 | PASS | C |
| 2 | Top crowd reaction inside the saddle (keeper backs it up) | 139.0° / 140° | 0.99 | PASS (tight) | C |
| 3 | Hook FE, base A_lo, von Mises ≥ 2 mm from contact (C1) | 94.6 / 227 MPa | 0.42 | PASS | C |
| 4 | Hook FE, keeper region, top A_lo, 7.65 kN | 174.6 / 227 MPa | 0.77 | PASS | C |
| 5 | Saddle bearing, 6 mm leg on Ø48.3 | 11.6 / 86.9 kN | 0.13 | PASS | C |
| 6 | Base axle, bending in the fork (M1) | 0.08 / 2.79 kNm | 0.03 | PASS | C |
| 7 | Base axle, scaffold coupler lever 60 mm | 0.39 / 2.79 kNm | 0.14 | PASS | C |
| 8 | Tube crushing **without** insert, base / top (M2) | 1.40 / 1.41 | 1.41 | **FAIL → insert required** | C |
| 9 | Tube crushing **with** Ø40 insert, base / top (L_eff 30; at L_eff 20: 0.21 / 0.34) | 0.18 / 0.25 | 0.25 | PASS | C |
| 10 | Collar slip, scaffold case (M3) | 9.08 / 12.8 kN | 0.71 | PASS | **E, test** |
| 11 | Keeper pin Ø12 bending, EN 1993-1-8 Tab 3.10 (C5) | 24.9 / 152.7 kNmm | 0.16 | PASS | C |
| 12 | Keeper hole bearing in the 6 mm leg / edge distance | 7.65 / 21.6 kN; 11.5 / 17.75 mm | 0.35 / 0.65 | PASS | C |
| 13 | Jack spindle M36, 82 mm extension, H = 0.5 V (C2) | 194 / 640 MPa | 0.30 | PASS | C |
| 14 | Spindle buckling, K = 2, plus bending (m6) | – | 0.32 | PASS | C |
| 15 | Jack tipping on its own 250 plate | e 75 / 83 mm | 0.90 | PASS | C |
| 16 | Base plate bending (C3, R73) | 148 / 355 MPa | 0.42 | PASS | C |
| 17 | Timber bearing under the plate (R76) | 0.78 / 2.6 MPa | 0.30 | PASS | C |
| 18 | Ground, SLS peak (R174); needs allowable ≥ 90 kPa on site | 84 / 150 kPa | 0.56 | PASS | C/E |
| 19 | Base hold-down per jack, ground (barrier 5.0 EQU) | **7.2 kN required** (4.1 at 3.0 kN/m) | – | REQ | C |
| 20 | Scaffold couplers, slip, 2 × class B (M5) | 6.56 / 20 kN | 0.33 | PASS | C |
| 21 | Scaffold couplers, pull-apart | 7.2 / 20 kN | 0.36 | PASS | E (supplier) |
| 22 | Landing bolts 4 × M12 8.8, tension + shear (M4) | 5.4 / 48.6; 3.5 / 32.4 kN | 0.19 | PASS | C |
| 23 | Landing jaw, weld, back plate | – | ≤ 0.16 | PASS | C |
| 24 | Wing clamps (IFC) | – | – | REPLACED | – |
| 25 | Free-standing, no ties: barrier 5.0 / 3.0, storm wind (FoS ≥ 1.5, R149) | FoS 0.06 / 0.09 / 0.44 | – | **FAIL → ties** | C |
| 26 | Free-standing, storm sliding at μ 0.3 | FoS 0.05 | – | **FAIL → ties** | C |
| 27 | Tied unit, EQU 0.9G + 1.5W (R181) | 0.97 / 194 kN | 0.01 | PASS | C |
| 28 | Rails in plane with the moved supports | 82.6 / 227 MPa | 0.36 | PASS | C |

**Anchor forces the landing must take**, ULS, per bracket. Forces are on the landing.

| Force | Value |
|---|---|
| Push into the face, base held | up to 5.6 kN in plane, i.e. **11.2 kN per unit** (crowd + sway) |
| Push into the face, ground case, 5.0 kN/m barrier | up to 14.5 kN |
| Pull-out | 9.7 kN |
| Lateral | 6.9 kN (**13.7 kN per unit** if the base is not laterally held) |
| Down | 12.2 kN |
| **Uplift** | **7.7 kN** (base anchored) / **8.5 kN** (base not anchored) |

The landing designer must confirm these values. They replace the old "11.3 kN per side".

## 4. Review items, closed

| Item | How it is closed |
|---|---|
| C1 | The hook is part of the rail. Bore Ø49.0, ring 35.5 mm, checked by FE. |
| C2 | Real jack; maximum extension 82 mm is stated and checked. |
| C3 | 250 × 12 plate and sole boards. |
| C4 | The hook sits over the axle. A forgotten keeper does not collapse the unit under crowd load, but it loses the hold-down. Pin captive on a lanyard, with a "pin fitted" check. |
| C5 | Double-shear clevis with a spacer bush. |
| M1 | Fork lever 7 mm. |
| M2 | Inserts. |
| M3 | Jaw bearing, plus the collars and couplers in the scaffold case. |
| M4 / M5 | Bolts or couplers; values in §3. |
| M6 | Top fixed; base anchored or clamped. |
| M7 | Wind and EQU checked; ties required. |
| m4 | The spare second base axle (x 9,936) is deleted. |

## 5. Masses

| Part | kg | Tag |
|---|---|---|
| Base axle, steel | 5.87 | C |
| Top axle, 6082 | 2.02 | C |
| 4 inserts | 1.22 | C |
| 4 collars | 0.54 | C |
| Keepers | 0.27 | E |
| Rail change | −0.14 | C |
| **Carried on the unit** | **9.79** (budget 7.7) | |
| Jack, each (site kit) | 9.6 | C |
| Landing bracket, each (site kit) | 4.5 | C |

## 6. Open items and limits

1. **Tests.**
   - Collar slip: target 1.5 × 9.1 kN.
   - Stake pull-out on site.
   - Coupler pull-apart values from the supplier.
2. **CAD clash checks.** Computed clearances [C]:
   - base fork to tread 0: 7.4 mm;
   - jaw to pole 2: about 22 mm;
   - window end to the pole-2 web slot: about 2.5 mm (the window effectively merges with the slot);
   - castle caps at s 0: to be checked.
3. **Hook FE limits.**
   - It is 2D with projected thickness and a rigid tube with 0.35 mm clearance.
   - A 3D or shell check of the saddle and window is recommended before the dies and CNC programs are released.
   - The top saddle margin is tight: 139° against 145°.
4. **Wind pressure** is assumed. A site q_p and a wind management plan (OWS, R150/R151) are needed.
5. **Ground case without anchors (r0).** The unit's torsional path to the top (8.5 kN uplift per bracket) is not verified. Recommendation: always anchor the base.
6. **Catwalk.**
   - The saddle is symmetric and the jaws need a second keeper hole.
   - Catwalk support heights and rail strength remain open (rail F5). The span is now shorter, which helps.
7. **Owner decisions needed.**
   - Steel landing brackets.
   - Barrier design value: 5.0 governs here, as in the rails report.
   - Unit mass: about 118.7 kg.
