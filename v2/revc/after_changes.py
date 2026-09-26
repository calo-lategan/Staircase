"""Rev C (27 Sep 2026): utilisation of every part AFTER the Rev C changes, with the same forces and formulas as the checks
of the current model (v2/final). One file for the datasheet, load verdict, change list and manufacturing guide.
Two build routes: R1 best strength, R2 lower cost. EN 1999-1-1: 6082-T6 f_o 250 (t <= 5 extrusion walls; bar 250),
5083-H111 f_o 125 (no weld weakening), gM1 1.1, gM2 = gMp 1.25. Welded 6082-T6: f_o,haz 125."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__)); FIN = os.path.join(HERE, "..", "final")
def J(n): return json.load(open(os.path.join(FIN, n)))
R = J("final_results.json"); BOX = J("tread_box2.json"); HAZ = J("tread_box2_haz.json"); GRT = J("tread_grating.json"); UBX = J("tread_ubox.json")
BAR = J("barrier_path_check.json"); AX = J("axle_options.json"); EDGE = J("lo_r_edge_check.json")
FD, FDH, FD5083 = 250 / 1.1, 125 / 1.1, 125 / 1.1
EF, EH = R["frame_envelopes"]["slides"], R["frame_envelopes"]["held"]
comp = lambda item, start, base: next(r for r in R["components"] if r["item"] == item and r["check"].startswith(start) and r["base"] == base)
pin_v = comp("Tread pins O10 (with link force)", "Shear", "slides"); pin_m = comp("Tread pins O10 (with link force)", "Bending", "slides")
latch = comp("Latch pins O2 (per pole)", "Vertical", "slides")
out = {}
# ---- steps
b4 = BOX["B4 box 3 / 2 / 2, two webs 2"]; b4u = max(v["util"] for k, v in b4["cases"].items() if k.startswith("ULS"))
b4vm = b4u * FD
out["steps"] = {
    "A_extruded_6082": dict(util=b4u, mass=b4["mass_kg"], note="one extrusion, no welds"),
    "A_bent_6082_welded": dict(util=HAZ["B4 box 3 / 2 / 2, two webs 2"]["util"]["welded corners"], mass=b4["mass_kg"], note="bent 6082-T6 sheet, bottom and webs welded"),
    "A_bent_5083_welded": dict(util=b4vm / FD5083, mass=b4["mass_kg"], note="bent 5083-H111 sheet, welded anywhere (no weld weakening)"),
    "B_owner_2mm_riveted": dict(util=max(v["util"] for k, v in UBX["U3 your box: top 2, mid 2, ribs 2 at 60"]["cases"].items() if k.startswith("ULS")), mass=UBX["U3 your box: top 2, mid 2, ribs 2 at 60"]["mass_kg"]),
    "B_owner_3mm_welded": dict(util=0.93, mass=UBX["U2 your box: top 3, mid 2, ribs 2 at 60"]["mass_kg"], note="weld-zone value from each plate's peak next to the J and L"),
    "C_grating_46_nosing8": dict(util=max(v["util"] for k, v in GRT["G5 grating: bars 3 x 50 at 46 mm, 8 mm nosing bar"]["cases"].items() if k.startswith("ULS")), mass=GRT["G5 grating: bars 3 x 50 at 46 mm, 8 mm nosing bar"]["mass_kg"]),
    "C_grating_34_nosing8": dict(util=max(v["util"] for k, v in GRT["G4 grating: bars 3 x 50 at 34 mm, 8 mm nosing bar"]["cases"].items() if k.startswith("ULS")), mass=GRT["G4 grating: bars 3 x 50 at 34 mm, 8 mm nosing bar"]["mass_kg"]),
}
for k, g in (("A", b4), ("C46", GRT["G5 grating: bars 3 x 50 at 46 mm, 8 mm nosing bar"]), ("C34", GRT["G4 grating: bars 3 x 50 at 34 mm, 8 mm nosing bar"]), ("B2", UBX["U3 your box: top 2, mid 2, ribs 2 at 60"])):
    c = g["cases"]; out["steps"].setdefault("sls", {})[k] = dict(sag4=abs(c["SLS 4 kN front, mid-span"]["uz_min"]), crowd=abs(c["SLS crowd"]["uz_min"]), person=abs(c["SLS person 1 kN at the nosing"]["uz_min"]))
# ---- step pins (same force, Ø20 6082-T6 bar; lever 14 right / 6.75 left)
V, M = pin_v["value"], pin_m["value"]
def pin(d, lever_ratio=1.0):
    W = math.pi * d ** 3 / 32; MRd = 1.5 * W * 250 / 1.25; Fv = 0.6 * math.pi * d * d / 4 * 295 / 1.25
    return dict(bending=M * lever_ratio / MRd, shear=V / Fv)
out["step_pins"] = {"d20": pin(20), "d16_gap7": pin(16, 7 / 14)}
# ---- pole pegs Ø12 (cantilever 7.5 mm + half wall), 2 per rail
Fp = latch["value"] / 2
for d in (12,):
    W = math.pi * d ** 3 / 32; MRd = 1.5 * W * 250 / 1.25; Fv = 0.6 * math.pi * d * d / 4 * 295 / 1.25
    out["pegs"] = dict(d=12, bending=Fp * 10 / MRd, shear=Fp / Fv, bearing=Fp / (1.5 * 5 * d * 250 / 1.25))
# ---- poles
Wreq = max(25 * v ** 2 / 6 for v in R["pole_options"]["required_solid_depth_across_mm"].values())
def rhsW(b, h, t): return (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12 / (h / 2)
m12 = lambda A: 12 * A * 1138 * 2.7e-6
out["poles"] = {
    "R1_tapered_solid_25x55": dict(util=Wreq / (25 * 55 ** 2 / 6), mass12=BAR["pole_mass_12_kg"]["tapered_25x55_to_15"]),
    "R2_flat_bar_60x25": dict(util=Wreq / (25 * 60 ** 2 / 6), mass12=m12(25 * 60)),
    "R2_rhs_80x40x3": dict(util=Wreq / rhsW(40, 80, 3), mass12=m12(40 * 80 - 34 * 74)),
}
# pole-to-rail bolts: couple ~14 kN at each rail crossing
F_cpl = BAR["couple"]["R142 5.0 kN/m viewing"]["F_kN"] * 1000
out["pole_fix"] = dict(F_kN=F_cpl / 1000, pin16_6082_shear=F_cpl / (0.6 * math.pi * 64 * 295 / 1.25), bearing_5mm_wall_d16=F_cpl / (1.5 * 5 * 16 * 250 / 1.25))
# ---- rails 65 deep (net W at Ø21 holes from final/ sizing; lateral from barrier_path_check)
out["rails"] = dict(net_W_left=7494, net_W_right=7193, W_needed=2900, util_net=2900 / 7193,
                    lateral_left=max(BAR["rails"]["left rails U 35 x 65 x 5 (F2)"].values()), lateral_right=max(BAR["rails"]["right rails inv. U 25 x 65 x 5 (F2)"].values()))
Fe = max(e["F_perp"] for e in EDGE)
for a in (18.0, 20.0):
    out["rails"][f"edge_util_{int(a)}mm"] = (Fe * 1.25 / (2 * 5 * 250) + 2 * 21 / 3) / a
# ---- axles
ax = {(r[0], r[1]): r[2] for r in AX["axle"]}; axv = {(r[0], r[1]): r[3] for r in AX["axle"]}
def tubeW(D, t): return math.pi / 64 * (D ** 4 - (D - 2 * t) ** 4) / (D / 2)
out["axles"] = dict(scaffold_ground=ax[("scaffold tube 48.3 x 4.0 (6082-T6)", "ground mu 0.5")], scaffold_clamped=ax[("scaffold tube 48.3 x 4.0 (6082-T6)", "base held (scaffold clamp)")],
                    jack_under_hook_d30_clamped_shear=axv[("30 x 3 (jack under the hook)", "base held (scaffold clamp)")],
                    top_scaffold_clamped=EH["R_top"] * 70 / tubeW(48.3, 4.0) / FD, top_scaffold_ground=math.hypot(AX["friction"]["ground mu 0.5"]["H"], AX["friction"]["ground mu 0.5"]["V_top"]) * 70 / tubeW(48.3, 4.0) / FD)
# ---- hooks, locks, jacks, footplates, brackets
out["hook_locks"] = dict(base_kN=EH["lock_base"] / 1000, top_kN=EH["lock_top"] / 1000, d14_single_shear=EH["lock_base"] / (0.6 * math.pi * 49 * 295 / 1.25), d12_single_shear=EH["lock_top"] / (0.6 * math.pi * 36 * 295 / 1.25))
out["jacks"] = dict(m24_ground=((AX["friction"]["ground mu 0.5"]["V"] / 353 + AX["friction"]["ground mu 0.5"]["H"] * 30 / (math.pi * 21.2 ** 3 / 32)) / FD),
                    m30_clamped=((EH["V_base"] / 561 + EH["H_base"] * 30 / (math.pi * 26.7 ** 3 / 32)) / FD), footplate_150x8_clamped=0.89)
hbr = comp("Handrail bracket 15x5 bent flat", "1.25", "slides")
out["brackets"] = dict(w25=hbr["util"] * (5 * 15 ** 2 / 6) / (5 * 25 ** 2 / 6))
out["landing_bracket"] = dict(pin=comp("Top bracket pin O20", "Pin", "held")["util"], plate=comp("Top bracket plate 5 mm", "Pin", "held")["util"], anchor_kN=EH["R_top"] / 1000)
# ---- mass per unit (route estimates)
rails_kg = (2 * (35 * 5 + 2 * 60 * 5) * 1805 + 2 * (25 * 5 + 2 * 60 * 5) * 1813) * 2.7e-6
axles_kg = 2 * (math.pi / 4 * (48.3 ** 2 - 40.3 ** 2)) * 1400 * 2.7e-6
fixed = 6.06 + 0.61 + 12 * 5 * 25 * 115 * 2.7e-6 + 1.2          # top rails + handrails, pivots, brackets 25 wide, pins/hooks/fixings
out["mass_unit"] = dict(route1=6 * b4["mass_kg"] + rails_kg + out["poles"]["R1_tapered_solid_25x55"]["mass12"] + axles_kg + fixed,
                        route2=6 * b4["mass_kg"] + rails_kg + out["poles"]["R2_rhs_80x40x3"]["mass12"] + axles_kg + fixed,
                        now=R["mass"]["total_kg"], rails=rails_kg, axles=axles_kg)
json.dump(out, open(os.path.join(HERE, "after_changes.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
