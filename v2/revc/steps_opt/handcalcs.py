"""Hand checks that sit outside the shell FE (recommended step C8).  Writes handcalcs.json.
Sources: v2/revc/after_changes.json (non-step unit masses), cand_C8.json (FE), EN 1999-1-1 / EN 1993-1-8 style formulas
as used in the repo scripts (T8.8 edge distance a >= F*gM2/(2 t f0) + 2 d0/3)."""
import json, math

ac = json.load(open("../after_changes.json"))
c8 = json.load(open("cand_C8.json"))
cs = c8["cases"]; m_fe = cs["ULS 4 kN front, mid-span"]["mass_model_kg"]
out = {}

# ---- production mass per step (FE mass + items not in the FE)
extras = {"rib top rivet/bond flange 12 x 2 (23 ribs x 175)": 23 * 12 * 2 * 175 * 2.7e-6,
          "serration ridges on skin/box/nosing top (~0.4 mm equivalent over 280 x 1195)": 0.4 * 280 * 1195 * 2.7e-6,
          "rivets (~100 SPR/blind) + 8 screws M8/M6 A4": 0.20,
          "grit/contrast inserts (55 mm nosing + 1 strip)": 0.10}
m_prod = m_fe + sum(extras.values())
out["mass"] = dict(fe_model=round(m_fe, 2), extras={k: round(v, 2) for k, v in extras.items()}, production_per_step=round(m_prod, 2),
                   six_steps=round(6 * m_prod, 1))

# ---- unit budget (after_changes.py composition, steps replaced)
rails, axles = ac["mass_unit"]["rails"], ac["mass_unit"]["axles"]
fixed = 6.06 + 0.61 + 12 * 5 * 25 * 115 * 2.7e-6 + 1.2
for route, pole in (("route1_solid_poles", ac["poles"]["R1_tapered_solid_25x55"]["mass12"]), ("route2_rhs_poles", ac["poles"]["R2_rhs_80x40x3"]["mass12"])):
    non_step = rails + axles + fixed + pole
    out.setdefault("unit", {})[route] = dict(non_step=round(non_step, 1), unit_with_C8=round(non_step + 6 * m_prod, 1),
                                              step_budget_for_60kg_each=round((60 - non_step) / 6, 2))

# ---- open riser gap with the L profile (rise 175, front zone 25 thick)
out["riser_gap"] = dict(gap=175 - 25, limit_max=120, rec_sphere=100,
                        lip_needed_for_120=175 - 25 - 120, lip_needed_for_100=175 - 25 - 100)

# ---- front pin ligament in the end plate (pin at z 37.5, walking surface z 50)
F = 11200.0; t = 6.0; f0 = 250.0
for d in (16.0, 20.0):
    d0 = d + 1
    a_req = F * 1.25 / (2 * t * f0) + 2 * d0 / 3
    out.setdefault("front_pin_ligament", {})[f"d{d:.0f}"] = dict(ligament=50 - 37.5 - d0 / 2, a_req=round(a_req, 1),
                                                                   max_centre_z=round(50 - d0 / 2 - a_req, 1))

# ---- box-to-end-plate joint: 4 x M8 A4-70 at the box corners (screw ports), 2 x M6 into the nosing
T_half = 6000 * (180 - 25) / 2           # Nmm, ULS 4 kN front mid-span, half to each end (box shear centre ~x 25)
V_end = max(abs(v[2]) for v in cs["ULS 4 kN front, at the end"]["pins"].values()) + 1000   # conservative end shear
r = math.hypot(21, 21)
Fs = math.hypot(T_half / (4 * r), V_end / 4)
Fv_Rd = 0.5 * 700 * 36.6 / 1.25
Fb_Rd = 2.5 * 0.6 * 290 * 8 * 6 / 1.25                   # bearing in the 6 mm end plate (6082-T6 fu 290)
out["end_joint"] = dict(T_half_Nmm=T_half, V_end_N=round(V_end), F_screw_N=round(Fs), M8_A4_70_shear_Rd=round(Fv_Rd), util_shear=round(Fs / Fv_Rd, 2),
                        util_bearing_endplate=round(Fs / Fb_Rd, 2), barrier_axial_per_end_N=9400,
                        axial_per_screw_6_screws_N=round(9400 / 6), note="screw-port pull-out in 6005A to be confirmed by test (~8-10 kN per M8 at 16 mm engagement, judgement)")

# ---- rib root joint (rib top flange to skin; rib foot into box ledge)
sig_fl = 187.2; A_fl = 12 * 3
Nfl = sig_fl * A_fl                               # ULS flange force at the root, N (conservative: peak stress x area)
q = Nfl / 130.0                                   # shed over ~130 mm of rib (patch centroid to root)
out["rib_joint"] = dict(flange_force_N=round(Nfl), shear_flow_N_per_mm=round(q, 1),
                        adhesive_shear_MPa_on_12mm=round(q / 12, 2), rivets_4p8_at_25_each_N=round(q * 25),
                        blind_rivet_design_N=2100, foot_bearing_on_ledge_N=round(Nfl))

# ---- first vertical frequency of the step (from FE crowd deflection, UDL beam formula f = 17.75/sqrt(delta_mm))
w_crowd = 7.5e-3 * 250; w_sw = m_fe * 9.81 / 1195
d_per_w = -cs["SLS crowd"]["uz_min"] / (w_crowd + w_sw)
for share in (0.0, 0.3, 0.6):
    out.setdefault("frequency_Hz", {})[f"self + {share} crowd"] = round(17.75 / math.sqrt(d_per_w * (w_sw + share * w_crowd)), 1)

# ---- GRP comparison (same geometry; pultruded FRP E ~ 25 GPa, rho 1.9)
out["grp_same_geometry"] = dict(sls4_mm=round(-cs["SLS 4 kN front, mid-span"]["uz_min"] * 70 / 25, 1), limit=12.16,
                                mass_kg=round(m_fe * 1.9 / 2.7, 2),
                                thickness_scale_for_same_stiffness=round(70 / 25, 2),
                                mass_for_same_stiffness_kg=round(m_fe * 1.9 / 2.7 * 70 / 25 * 0.8, 1))
json.dump(out, open("handcalcs.json", "w"), indent=1)
print(json.dumps(out, indent=1))
