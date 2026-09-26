"""Collect every final-model calculation into final_results.json (single source for the datasheet, brief and report),
plus a measured mass estimate and the minimum sizes that would pass (sized with the same formulas)."""
import json, math
T = {r["check"]: r for r in json.load(open("tread2_checks.json"))}
TC = json.load(open("tread2_cases.json"))
RC = json.load(open("rail_checks_final.json")); RS = json.load(open("rail_checks_final_slide.json"))
EDGE = json.load(open("lo_r_edge_check.json"))
CC = json.load(open("component_checks_final.json")); PO = json.load(open("pole_options_final.json")); SLS = json.load(open("frame_sls_final.json"))
FD = 250 / 1.1
RHO = 2.7e-6   # kg/mm3

# ---------------- mass (measured sections x lengths)
mass = {
    "treads 6x (frame J+L 775 mm2 x 1200 + end plates + pins)": 6 * (775 * 1200 + 2 * (45 * 47.5 + 230 * 20) * 5 + 4 * 78.5 * 18) * RHO,
    "grating bars 360x (3x25x270)": 360 * 3 * 25 * 270 * RHO,
    "longitudinal flats 12x (2.7x25x1177)": 12 * 2.7 * 25 * 1177 * RHO,
    "rails 4x (375/375/325/275 mm2)": (375 * 1761 + 375 * 1849 + 325 * 1781 + 275 * 1845) * RHO,
    "poles 12x RHS 25x10x2 (1138)": 12 * 124 * 1138 * RHO,
    "lock pins 12x (25x10x245)": 12 * 250 * 245 * RHO,
    "top rails + handrails 4x U25x25x5 (1726)": 4 * 325 * 1726 * RHO,
    "top posts / pivots 16+16": 16 * 76 * 100 * RHO + 16 * 130 * 50 * RHO,
    "handrail brackets 12x": 12 * 88 * 115 * RHO,
    "axles (3 positions, O25x2.5 x 1309; duplicates not counted)": 3 * 176.7 * 1309 * RHO,
    "hooks 10 mm (4) + washers/spacers/nuts": 4 * 4000 * 10 * RHO + 0.25,
}
mass_total = sum(mass.values())

# ---------------- minimum sizes that would pass (same loads, same formulas)
env = CC["envelopes"]["held"]; env_s = CC["envelopes"]["slides"]
def hook_b(R, t=10.0, ri=12.8):
    for b in [x / 2 for x in range(20, 200)]:
        rc = ri + b / 2; k = 1 + (b / 2) / (3 * rc) * 2
        if R / (t * b) + k * R * rc / (t * b * b / 6) <= FD: return b
sizes = {
    "tread": "closed box 280 x 50 (same outside): 3 top (serrated) / 2 bottom / 2 walls + 2 inner webs 2 at x 95 and 185 (tread_box2 B4, FE with loads on the deck): 4 kN 0.41 (0.82 with every seam welded), sag 3.6 mm, crowd 1.2 mm, about 5.9 kg per step. Top and walls bent from one sheet; bottom welded or riveted. Open shapes (cut-out top sheet, cut lattice) fail.",
    "tread_minimum_I": "I >= 176,000 mm4 for 4 kN / L/100 and >= 157,000 mm4 for crowd L/250 - with a CLOSED section (no twist)",
    "pole_solid_6082": "solid 25 (along) x 55 (across): 0.84 at the worst barrier load; tapered 55 -> 15 at the top saves 15 kg per unit; stands on the outside face of the rails, bolted to both (a 55 mm pole can't pass through a 35 mm rail). The pole couple (~14 kN) needs the 65 mm rails.",
    "tread_pins": "O20 aluminium 6082-T6 (shear 44 kN, M_Rd 235 kNmm) or O16 steel 8.8, for 11.8 kN + 165 kNmm",
    "latch_pins": "pole pegs O12 (each reaches 7.5 mm to the rail wall: bending 0.58, shear 0.18), 2 per rail, 4 per pole; draw the upper pair",
    "axle": "hooks lock, so the base can end up anywhere between free and held: size for held. Base axle O45x5 (0.96), or jacks straight under the hooks with O30x3; "
            "top axle O40x4 (0.94). Free base only: O35x3 / O30x3",
    "hooks": f"10 mm plate ring width >= {hook_b(env['R_base']):.1f} mm at the base, >= {hook_b(env['R_top']):.1f} mm at the top (now about 22)",
    "hook_locks": f"not drawn. As drawn the base hook opens on the side the stair pushes, so the lock carries the base reaction: "
                  f"{env_s['lock_base'] / 1000:.1f} kN (base free) to {env['lock_base'] / 1000:.1f} kN (base held) per side; top lock {env['lock_top'] / 1000:.1f} kN "
                  f"(incl. {env['uplift_top'] / 1000:.1f} kN uplift). E.g. O14 keeper pin in single shear (21.8 kN) at the base, O12 (16.0 kN) at the top; "
                  "better: turn the base hook so the plate sits on top of the axle",
    "jacks": "held base: M30 rods (0.88) and a fixing to the ground/scaffold for 10.9 kN sideways per side (friction needs 0.77, about 0.5 available)",
    "footplate": "150 x 150 x 8 (R73; 0.89 with the held-base rod moment)",
    "rail_hole_lo_r": "Lo_R hole centre >= 15.2 mm above the free edge of the leg (now 12.5) for the top-tread link force",
    "rails": "net section at the pin stations must reach W >= 2,900 mm3 (now 216-595 mm3): about 5 x; or add a mid support and a proper fold lock, then re-run",
}

out = dict(
    model="25.9.2026 final STEP LADDER-standard.ifc (standard 35 deg)", material="EN AW-6082-T6, f_o 250 (t<=5), gM1 1.1, gM2 1.25",
    tread=dict(checks=list(T.values()), cases={k: dict(lip=v["uz_mid_lip_top"], back=v["uz_mid_rearwall_top"], twist=v["twist_mid_deg"],
                                                     vm=v["vm_max_body"][0], bar=v["bar_max"][0], pins=v["pins"]) for k, v in TC.items()}),
    rails=dict(pinned_base=RC["results"], sliding_base=RS, sections=RC["sections"]),
    components=CC["rows"], frame_envelope=env, frame_envelopes=CC["envelopes"], frame_sls=SLS, pole_options=PO,
    mass=dict(parts=mass, total_kg=mass_total), sizes=sizes,
    lo_r_hole_edge=dict(rule="EN 1999-1-1 T8.8: a >= F gMp/(2 t f0) + 2 d0/3, a = hole edge to free edge = 12.5 - 5 = 7.5 mm, t 5, d0 10",
                        worst=EDGE, a_have=7.5, a_req=[round(e_["F_perp"] * 1.25 / (2 * 5 * 250) + 20 / 3, 2) for e_ in EDGE]))
import os
if os.path.exists("tread_box_check.json"): out["tread_box_check_superseded"] = json.load(open("tread_box_check.json"))   # loaded the bottom plate by mistake
for key, fn in (("tread_box2", "tread_box2.json"), ("tread_box2_haz", "tread_box2_haz.json"), ("tread_lattice", "tread_lattice.json"),
                ("barrier_path", "barrier_path_check.json"), ("tread_grating", "tread_grating.json"), ("tread_ubox", "tread_ubox.json"), ("tread_lattice_l10", "tread_lattice_l10.json"), ("axle_options", "axle_options.json"), ("duplicates", "duplicates_final.json")):
    if os.path.exists(fn): out[key] = json.load(open(fn))
json.dump(out, open("final_results.json", "w"), indent=1)
print(f"mass estimate {mass_total:.1f} kg"); [print(f"  {k}: {v:.2f}") for k, v in mass.items()]
print(json.dumps(sizes, indent=1))
