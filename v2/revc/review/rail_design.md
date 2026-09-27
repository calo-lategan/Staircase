# Guide rails: final scheme (Rev C, nested open channels)

Scripts: `v2/revc/rails/` (`rails_lib.py`, `frame_rails.py`, `run_rails.py`, `summarize.py`).
Results: `rails/rail_design_box80.json` is production; `rails/rail_design_plate55.json` is the prototype.
Superseded runs are kept for the record:
- `rails/nested_variant.json`: first nested run, with a 55 pole and the lock at the lower rail only.
- `rails/alt_H/`: closed H-shaped rail, rejected by the owner.

Material is 6082-T6 to EN 1999-1-1: f0 = 250 MPa, γM1 = 1.1, γMp = 1.25. There are no welds on the rails.

How values are marked in this report:
- **[C]** computed by script. This covers the OpenSees side frame, the section properties (0.25 mm pixel integration), the continuous-beam lateral model and the code formulae.
- **[E]** engineering estimate. This covers hand and beam-theory local checks and St Venant torsion. None of these has been checked by shell FE.

## 1. Scheme in one paragraph

Each side has two open channels:
- the **lower rail** (a U, web on the far side of the pin line);
- the **upper rail** (an inverted U).

The pin leg of each channel carries the step pins. The web faces away from the steps. The poles run inside the channels and pass through slots in both webs.

The **left rails (profile A)** are wider channels, and the **right rails (profile B)** slide into them:
- B's webs sit under A's webs with 1 mm clearance.
- A has no outer leg, so the neighbouring unit's B rail enters from the side or lengthwise.

Each pin leg has an internal **bulb**, 27 mm high. The bulb gives:
- metal around the pin hole;
- a seat for the washer;
- bearing for the pole;
- torsional stiffness.

At every pin the pin leg has a round **tab**. The opposite rail has a **notch** at the same station, so in the catwalk state the two pin-leg tips touch, with the tabs sitting in the notches.

The **poles lock the fold at BOTH rails**, and each lock carries 9.5 kN. A lock at the lower rail only is a mechanism, as section 6 shows. The poles review's lower-only lock is therefore rejected.

Each pin station is a **Ø16 duplex stud** with an **M16 castle cap nut**, preloaded onto a Ø30 washer. This clamp takes the torque from the eccentric pole push.

The owner's decisions are kept:
- Infill and child rail: **not fitted, by owner decision**. The rails have no provisions for them.
- The rails are open channels only; there is no closed or box section.

## 2. Dimension table for Gerald

Coordinates:
- y is across the rail, measured from the step-side face of the pin leg.
- n is normal to the rail, from the pin-leg tip (n = 0) to the far face of the web.
- s is along the rail, from the frame's lower pin datum.

All four profiles are 6082-T6 extrusions (four dies).

| Item | A_lo (L lower) | A_up (L upper) | B_lo (R lower) | B_up (R upper) |
|---|---|---|---|---|
| Overall width y (web) | 115 | 115 | 108 | 108 |
| Depth n (pin-leg tip to web outer face) | 68 | 62 | 60 | 49 |
| Pin leg thickness | 6 | 6 | 6 | 6 |
| Bulb on pin leg (inside), y × n | 14 × 27 (total 20 at the hole) | 14 × 27 | 8 × 27 (total 14 at the hole) | 8 × 27 |
| Web thickness | 7 | 12 | 7 | 12 |
| Outer leg | none | none | 5 thick, n 29–53 | 5 thick, n 29–37 |
| Edge lip at web free edge (outside the nest) | 6 × 12, standing proud of the web | 6 × 12 | none | none |
| Section area, mm² [C] | 1621 | 2130 | 1410 | 1774 |
| kg/m [C] | 4.38 | 5.75 | 3.81 | 4.79 |
| Length, s from–to [C] | −115.7 to 1615.6 (L) | −114.3 to 1733.4 | −115.7 to 1589.8 (R) | −146.0 to 1698.9 |
| Mass [C] | 7.79 kg | 10.64 kg | 6.78 kg | 8.86 kg |

The four rails weigh **34.07 kg** in total. The bulbs and lips account for 6.5 kg of that.

**Common details**

- **Pin hole.** Ø17.0 +0.1/0, reamed on a jig, at n = 12.5 (the pin line). Pins sit at the owner's rear (25, 12.5) and front (225, 37.5) positions, on a pitch of 305.2 along the rail.
- **Pin.** Ø16 h9, 1.4462 duplex stud fixed in the step end block. It has an M16 threaded end.
- **Cap.** Castle cap nut M16 (duplex or A4-80), 28 OD × 24 long. It sits on a Ø30 × 4 stainless washer on the bulb.
  - Tighten to 40 Nm, then back off to the next castle slot (at most 60°).
  - Lock with a Ø4 split pin. The split pin locks only; it carries no load.
- **Step pad.** A 1 mm PTFE-faced stainless shim between the step end block and the bulb or tab.
- **Tab.** Round tab on the pin leg at each own pin: R 21.8 about the hole centre, 43.6 wide, projecting 9.3 beyond the tip plane.
- **Notch.** Cut in the pin leg at each pin station of the opposite rail: 11.3 deep × 51.6 wide (4 mm side clearance).
  - Notch centres, upper rails: s = 200.0, 505.2, 810.3, 1115.5, 1420.7, 1725.8.
  - Notch centres, lower rails: s = 105.2, 410.3, 715.5, 1020.7, 1325.8. The station at −200 falls off the rail.
- **Pole slots.**
  - Width: 81 for the production box pole; 56 for the prototype plate.
  - Position across the web, measured from the bulb face: A at y 20–101, B at y 14–95. With the rails nested, A's slot lines up over B's slot.
  - Length along the rail:
    - standard + catwalk, upper web: 37.1;
    - steep, upper web: 48.7;
    - standard + steep, lower web: 48.7;
    - catwalk, lower web: 26.0.
- **Rail ends.** Base ends are cut square at s = −115.7, which is 2 mm clear of the Ø48.3 axle. The hook plate from the supports review bridges from the rail end to the axle.

**Slot centres in s, one row per pole (x = pole station along the stair)**

| Pole x | L up std/cw | L up steep | L lo std/steep | L lo cw | R up std/cw | R up steep | R lo std/steep | R lo cw |
|---|---|---|---|---|---|---|---|---|
| 8396.8 / 8398.8 (top) | 1662.6 | 1770.4* | 1351.6 | 1462.6 | 1651.1 | 1749.0* | 1354.8 | 1451.1 |
| 8646.8 / 8648.8 | 1357.4 | 1465.2 | 1046.4 | 1157.4 | 1345.9 | 1443.8 | 1049.6 | 1145.9 |
| 8896.8 / 8898.8 | 1052.3 | 1160.0 | 741.2 | 852.3 | 1040.7 | 1138.6 | 744.4 | 840.7 |
| 9146.8 / 9148.8 | 747.1 | 854.8 | 436.0 | 547.1 | 735.5 | 833.4 | 439.2 | 535.5 |
| 9396.8 / 9398.8 | 441.9 | 549.6 | 130.8 | 241.9 | 430.3 | 528.2 | 134.0 | 230.3 |
| 9646.8 / 9648.8 (bottom) | 136.7 | 244.4 | −174.4* | −63.3 | 125.1 | 223.1 | −171.2* | −74.9 |

\* This slot falls beyond the rail end. The top pole has no steep slot in the upper rail, and the bottom pole has no standard/steep crossing of the lower rail (see flags F3 and F4).

**Pin-line separation:** 25.0 / 135.2 / 168.1 mm for catwalk / standard / steep.

**Vertical distance between the web mid-planes, L / R:**

| State | L | R |
|---|---|---|
| Catwalk | 120.5 | 99.5 |
| Standard | 281.6 | 256.0 |
| Steep | 405.1 | 372.8 |

## 3. Pass/fail table (production: box pole 25 × 80, lock at both rails, 5.0 kN/m barrier)

Utilisations are the governing values across L and R, both base conditions (held and slides) and all patterns. A negative clearance or gap would fail.

| # | Check | Result | Limit | Util | Status | Source |
|---|---|---|---|---|---|---|
| 1 | In-plane bending + axial at the net section (hole, notch, slot, notch + slot) | B_lo hole, crowd, σ 114.7 | 227 MPa | 0.51 | PASS [C] | frame_rails.py, run_rails.py §B; EN 1999-1-1 6.2 |
| 2 | Combined in-plane + lateral + torsion, von Mises | L_lo 0.76 / L_up 0.89 / R_lo 0.90 / R_up **0.91** | 1.0 | 0.91 | PASS [C]+[E] | run_rails.py §E |
|  | – of which τ from torsion | A_up 97 MPa, B_lo 92 MPa, B_up 81 MPa | | | [E] St Venant | rails_lib.torsion_J |
| 3 | Local buckling class, all elements | all Class 1–3, ρc = 1.0; A_lo pin leg β 5.67 (class 3, the worst) | Class 4 limit 6 / 22 | – | PASS [C] | EN 1999-1-1 6.1.4, Table 6.2 |
| 4 | Upper web outer chord beside the slot (local bending) | B_up 0.55, A_up 0.42 | 1.0 | 0.55 | PASS [E] | run_rails.py §F |
| 5 | Lower web under the pole shoulder | A_lo 0.72, B_lo 0.60 | 1.0 | 0.72 | PASS [E] | §F |
| 6 | Pole / tongue bearing on the slot edge; upper latch | 0.14 / 0.20 / 0.17 | 1.0 | 0.20 | PASS [E] | §F |
| 7 | Pin Ø16 1.4462, stud fixed in the step end block (lever 11) | bending 0.39, shear 0.14 | 1.0 | 0.39 | PASS [C] | §D |
| 7a | Same pin, simply bearing in an 8 mm end plate (lever 15) | bending 0.53 | 1.0 | 0.53 | PASS [C] | §D |
| 7b | Alternative: 6082-T6 Ø16 / Ø20 pin | 0.80 / 0.41 | 1.0 | – | info [C] | §D |
| 8 | Pin bearing on the pin leg + bulb (14 mm) | V = 8.8 kN | Table 8.8 | 0.13 | PASS [C] | EN 1999-1-1 8.5.14 |
| 9 | Edge distance at the tab, a = 13.3 vs a_req 12.9 | Table 8.8 | | 0.97 | PASS (tight) [C] | Table 8.8 |
| 10 | Pin axial retention: castle cap nut M16, pull 41.1 kN | thread tension | | 0.56 | PASS [C] | §D; EN 1993-1-8 |
| 10a | Owner's plain cap + Ø8 cross-pin (double shear) | cross-pin 1.31, pin net section at the cross-hole 1.26 | | **1.31** | **FAIL** [C] | §D |
| 10b | Owner's plain cap + Ø6 cross-pin | cross-pin 2.33 | | **2.33** | **FAIL** [C] | §D |
| 11 | Washer Ø30 bearing on the bulb; pull-through | 0.29 / 0.27 | | 0.29 | PASS [E] | §D |
| 12 | Step pad on the bulb or tab (30 × 10), 17.6 kN | | | 0.20 | PASS [E] | §D |
| 13 | Fold lock force per pole per rail | 9.5 kN (both rails) | | – | [C] | frame_rails.py |
| 14 | Lock at the lower rail only (poles review) | 1126–1532 mm displacement | stable | – | **FAIL: mechanism** [C] | frame_rails.py |
| 15 | SLS sag / f1 | 0.66 mm / 36.9–54.4 Hz | 7.32 mm / – | 0.09 | PASS [C] | §B |
| 16 | Fold-out: tabs leave the notches | clear at 3.4°, 1.8 mm drift; 4 mm side clearance | > drift | – | PASS [C] | rails_lib kinematics |
| 17 | Cap to pole clearance (all states) | ≥ 34.7 mm | > 0 | – | PASS [C] | §A |
| 18 | Ground clearance at the base end (far corner above the footplate top) | L 20.5 / R 27.1 mm | > 0 | – | PASS [C] | §A |
| 19 | Nest: B inside A | 1.0 clearance at web and pin leg; A cap zone (n ≤ 27.5) vs B outer leg (n ≥ 29): 1.5 clearance | > 0 | – | PASS, tight [C] | §G |
| 20 | Step end plates / studs inside the owner's L-step envelope | front stud pull 41 kN in a 25 mm band; 8 mm plate c_req 8.4 vs 4 available | | – | **FAIL: envelope change needed** [E] | see F1 |
| 21 | Catwalk stacked-rail strength | not verified | – | – | **OPEN** | see F5 |

Barrier loads, ULS, 5.0 kN/m governing:

| Quantity | L | R |
|---|---|---|
| Force per pole at the upper rail, F_up | 14.3 kN | 15.4 kN |
| Force per pole at the lower rail, F_lo | 11.7 kN | 12.9 kN |
| Lever between the rails | 219 mm | 203 mm |

The pin pull at the upper rail reaches 27.4 kN, and the cap tension 41.1 kN. The cap tension is the combination of the direct pull and the clamp couple that resists the eccentric pole torque, P = max(R, (T + R(12.5 − n_s))/(n_c − n_s)).

The reviewer's estimate of 7.9–9.4 kN for the pin axial force left out the torsion clamp. That is why the owner's cross-pinned cap fails.

## 4. Prototype: 25 × 55 plate pole in the same extrusions

- The extrusions are the same; only the slots change, to 56 wide, from the bulb face.
- Combined utilisation: 0.77 / 0.88 / 0.90 / **0.92**.
- In-plane, maximum 0.52.
- Lock force: 10.0 kN per rail.
- Pin shear: 9.0 kN, pin bending 0.40, edge distance 0.97.
- Outer chords are 0.06 because the narrow slot leaves a wide chord. Shoulder 0.50.
- The lower-only lock is again a mechanism (930–1272 mm).

**All checks pass.** Do not cut the 56 slots into rails meant for production. The box pole needs 81-wide slots.

## 5. Reconciliation with poles_barrier.md (Part C)

| Poles review | This scheme | Reason |
|---|---|---|
| 25 × 55 plate pole, 56 × 32 slot | Production 25 × 80 box, slot 81 wide. Slot lengths 26 / 37.1 / 48.7 along the rail: the pole is inclined through the web in the 35° and 49.4° states. Plate 55 kept as the prototype (section 4). | Mass-budget decision; the slot length follows from the kinematics |
| U-channel widths 82 / 94 | 108 (B) / 115 (A) | 81 slot + 8 + 8 web ligaments + pin leg + outer leg; A = B + 6 leg + 1 clearance for nesting |
| Lock at the lower rail only | Lock at **both** rails | Lower-only is a mechanism (check 14) |
| Cap with cross-pin carrying the pull | Castle cap nut, preloaded | The cross-pin fails at 41 kN (checks 10a and 10b). A plain cap cannot be preloaded, so it cannot clamp the rail against torsion. |
| (A8) Bottom pole | Still has no crossing of the lower rail in standard/steep | See F4 |

## 6. Superseded options (numbers for the record)

| Option | Rails mass | Worst util | Cap pull | Status |
|---|---|---|---|---|
| Rev C after_changes rails | 14.65 kg | – (no pole slots, no nesting) | – | baseline |
| First nested open run (55 pole, lower-only lock) | 23.7 kg | R_up **1.02** | 61.2 kN | FAIL |
| H / closed rail (alt_H, box80) | 18.1 kg | 0.86 | 30.0 kN | passes but **rejected: owner requires open channels** |
| **Final nested open channels (box80)** | **34.07 kg** | **0.91** | 41.1 kN | **ADOPTED** |

## 7. Flags and compromises for the owner

- **F1 – Step envelope (envelope change required).**
  - The front stud's 41 kN pull cannot be anchored inside the L-step envelope. The 25 mm band leaves 4 mm ligaments.
  - An 8 mm end plate fails the Table 8.8 edge distance at both pins (8.4 required vs 4 available).
  - Smallest compromise: add **local lugs on the end block** at the front pin, extending below the front zone. This is an **envelope change** and needs owner approval.
  - Steps become 1,209 mm over their end blocks. The IFC value of 1,236 overlaps the rails.
- **F2 – Mass.** The rails are 34.07 kg against 14.65 kg in Rev C, **+19.4 kg per unit**. This moves the unit further from the 60 kg target.
  - The open section pays for torsion from the eccentric pole push with the 12 mm upper webs and the bulbs.
  - The H option would have saved 16 kg but is not allowed.
  - The remaining mass levers are:
    - a smaller pole width, which narrows the slot and web;
    - moving the pole bearing onto the pin line, which removes the torsion.
  - Neither lever is taken here.
- **F3 – Top pole.** The steep slot falls beyond the upper rail end. The top pole cannot lock the steep state unless the upper rails are extended by about 76 mm (L) and 90 mm (R). That figure is the slot end plus 15 mm of end metal [E]. The alternative is to leave that pole unlocked at the upper rail in steep.
- **F4 – Bottom pole.** It does not cross the lower rail in standard/steep (poles review A8). Only the upper rail locks it in those states.
- **F5 – Catwalk.** The strength of the stacked rails in catwalk is not verified. It depends on composite action through the tabs and on the unknown mid-foot support. It needs a dedicated check before catwalk use.
- **F6 – Estimates.** Torsion, the slot regions, the shoulder and chord checks are hand or beam theory only [E]. Combined utilisations of 0.89–0.92 leave little margin. **A shell-FE check of the upper rail around the top pole slot is recommended before the dies are cut.**
- **F7 – Tight items.**
  - The tab edge distance is 0.97.
  - The nest clearances are 1.0 / 1.5 mm, which needs extrusion tolerance of ±0.3 or better, or a 1.5 mm nominal clearance.
- **F8 – Tooling and layout.**
  - Four custom dies are needed.
  - The WIDE pitch is 1,326 mm.
- **Infill / child rail:** not fitted, by owner decision.
