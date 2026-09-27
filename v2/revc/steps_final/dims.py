"""Drawing dimensions and masses of the FINAL step (as drawn, not the FE mesh). Writes dims.json.
Datum (step-local, for SketchUp): x 0 = back face of the back box -> 280 = nosing front face (direction of travel down
the stair is +x); z 0 = underside of the back box -> 50 = walking surface (serration tips +0.8); y 0 = LEFT end-block outer
face (left = walking up the stair) -> 1209 = RIGHT end-block outer face.  End blocks 16 thick: inner faces y 16 / 1193, so
every extrusion is 1177 long (y 16 -> 1193).  Tags: [FE] from final_fe.json, [H] hand calc, [J] judgement / estimate."""
import json, math
import design as dsg

C = json.load(open("final_cfg.json"))
RHO = 2.70e-6; RHO_ST = 7.8e-6
L_EXT = 1177.0; Y_IN_L, Y_IN_R = 16.0, 1193.0; Y_OUT_R = 1209.0
tb, tbf, tbb, tbt = C["tb"], C["tb_front"], C["tb_bot"], C["tb_top"]
ts, tn, tnt, tlip = 2.0, 2.0, C["tn_top"], C["t_lip"]
bulb_rib, bulb_lip, ws = C["bulb"], C["lip_bulb"], C["ws"]
tr = 2.0

# ---------------------------------------------------------------- section areas (mm2)
deck_box = {"rear wall 50 x %.1f" % tb: 50 * tb, "front wall 50 x %.1f" % tbf: 50 * tbf,
            "bottom": (50 - tb - tbf) * tbb, "top (under serration)": (50 - tb - tbf) * tbt,
            "skin x 50-225": 175 * ts, "rib ledge on front face z 25-28 (3 x 8) [J]": 24.0,
            "4 screw ports (2 x M10 lower, 2 x M8 upper) [J]": 2 * 45.0 + 2 * 35.0,
            "serration ridges 0.8 high, 50 % solid (0.4 mm equiv over x 0-225)": 0.4 * 225}
nosing = {"top 55 x %.1f" % tnt: 55 * tnt, "bottom": (55 - 2 * tn) * tn, "front wall z 25-50": 25 * tn, "inner wall": (25 - tn - tnt) * tn,
          "lip z -25..25 x %.1f" % tlip: 50 * tlip, "tip flange %g x %g" % tuple(bulb_lip): bulb_lip[0] * bulb_lip[1],
          "hook to skin + grit dovetail recess [J]": 30.0, "serration 0.4 equiv": 0.4 * 55}
rib = {"web 20 x %.1f (z 28-48)" % tr: 20 * tr, "bottom bulb %g x %g (z 25-28)" % tuple(bulb_rib): bulb_rib[0] * bulb_rib[1],
       "top bond/rivet flange 12 x 2 (not in FE)": 24.0}
A = {k: sum(v.values()) for k, v in (("deck_box", deck_box), ("nosing_lip", nosing), ("rib", rib))}
n_rib = 23; L_rib = 175.0
# skin slots removed: 3 slots of 47.7 per column, columns: 2 per 50 bay (ws wide) -> count from the FE geometry
import stepfe_final as s
g = s.geometry({**s.DEFAULT, **dsg.final_cfg(**C)})
n_col = len(g["slot_ys"]); slot_len = sum(b - a for a, b in g["slot_rows"])
V_slots = n_col * ws * slot_len * ts
M = {}
M["deck-box extrusion (6005A-T6), 1177 long, less slots"] = (A["deck_box"] * L_EXT - V_slots) * RHO
M["nosing-lip extrusion (6005A-T6), 1177 long"] = A["nosing_lip"] * L_EXT * RHO
M["ribs 23 x 175 (6005A-T6 T-bulb extrusion)"] = A["rib"] * L_rib * n_rib * RHO
holes_eb = [(16.0, 16.0), (13.0, 16.0), (13.0, 16.0), (11.0, 16.0), (11.0, 16.0), (9.0, 16.0), (9.0, 16.0)]
M["end blocks 2 x (6082-T651, 16 mm plate, web pocketed to 6)"] = 2 * dsg.eb_mass_kg(holes=holes_eb)
M["nosing end plugs 2 x (6082-T6 flat bar 50 x 20 x 86)"] = 2 * 50 * 20 * 86 * RHO
struct_al = sum(M.values())
Mst = {"studs 4 x 1.4462 D16 (2 x 62 left, 2 x 56 right)": (2 * 62 + 2 * 56) * math.pi * 64 * RHO_ST,
       "screws/bolts A4: 4 x M12x30 csk, 4 x M10x25 csk, 4 x M8x25 csk, 6 x M8x60 + nuts": 0.20,
       "rivets (~70 SPR/blind) + structural adhesive": 0.12,
       "pads 4 x 1 mm PTFE-faced stainless R25 discs": 4 * math.pi * 25 ** 2 * 1.0 * RHO_ST * 0.6,
       "grit/contrast inserts (55 nosing top + 1 strip on box top) + contrast band on lip face": 0.15}
fe = json.load(open("final_fe.json")) if __import__("os").path.exists("final_fe.json") else None
OUT = dict(datum=__doc__.split("Datum")[1].split("Tags")[0].strip(), section_areas={"deck_box": deck_box, "nosing_lip": nosing, "rib": rib, "totals": A},
           slots=dict(width=ws, length=round(g["slot_rows"][0][1] - g["slot_rows"][0][0], 1), rows_x=[(round(a, 1), round(b, 1)) for a, b in g["slot_rows"]],
                      columns=n_col, open_area_plan=round(s.open_area({**s.DEFAULT, **dsg.final_cfg(**C)}, g), 4)),
           mass_structural_al={k: round(v, 3) for k, v in M.items()}, structural_al_total=round(struct_al, 2),
           mass_other={k: round(v, 3) for k, v in Mst.items()}, as_built_total=round(struct_al + sum(Mst.values()), 2),
           fe_model_mass=(round(fe["summary"]["mass"], 3) if fe else None), eb_poly=dsg.eb_poly(),
           eb_area_mm2=round(dsg.poly_area(dsg.eb_poly()), 0))
# rib and bolt stations in drawing y
mid = Y_OUT_R / 2
OUT["rib_y"] = [round(mid + 50 * (k - 11), 1) for k in range(23)]
OUT["plug_bolt_y_left"] = [Y_IN_L + e for e in (17.0, 50.0, 76.0)]
OUT["plug_bolt_y_right"] = [round(Y_IN_R - e, 1) for e in (17.0, 50.0, 76.0)]
# slot columns in drawing y: 2 per rib bay, symmetric in each bay: 12 solid over each rib web (6 either side), slots ws, bridge 8
cols = []
bays = [(Y_IN_L, OUT["rib_y"][0])] + list(zip(OUT["rib_y"][:-1], OUT["rib_y"][1:])) + [(OUT["rib_y"][-1], Y_IN_R)]
for a, b in bays:
    lo = a + (6.0 if a != Y_IN_L else 20.0); hi = b - (6.0 if b != Y_IN_R else 20.0); avail = hi - lo
    nc = int((avail + 8.0) // (ws + 8.0))
    if nc <= 0: continue
    nc = min(nc, 2); used = nc * ws + (nc - 1) * 8.0; y = lo + (avail - used) / 2
    for k in range(nc): cols.append((round(y, 1), round(y + ws, 1))); y += ws + 8.0
OUT["slot_columns_y"] = cols
OUT["open_area_drawing"] = round(len(cols) * ws * slot_len / (280 * Y_OUT_R), 4)
json.dump(OUT, open("dims.json", "w"), indent=1)
print(json.dumps({k: v for k, v in OUT.items() if k not in ("eb_poly", "slot_columns_y")}, indent=1)); print(len(cols), "slot columns", cols[:5], cols[-3:])
