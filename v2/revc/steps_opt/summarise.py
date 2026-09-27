"""Collect cand_*.json into candidates_summary.json (utilisations vs 6005A-T6 hollow f0 215 and 6082-T6 f0 250, gM1 1.1)."""
import json, glob
rows = []
for f in sorted(glob.glob("cand_C*.json")):
    d = json.load(open(f)); c = d["cases"]; k0 = list(c)[0]
    w = max(((v[0], p, cn) for cn, r in c.items() if cn.startswith("ULS") for p, v in r["by_part"].items() if "rigid" not in p))
    rows.append(dict(name=d["name"], mass_fe=round(c[k0]["mass_model_kg"], 2), open_area=round(c[k0]["open_area"], 3),
                     vm_uls=w[0], where=f"{w[1]} ({w[2]})", u_6005A=round(w[0] / (215 / 1.1), 2), u_6082=round(w[0] / (250 / 1.1), 2),
                     sls4=round(-c["SLS 4 kN front, mid-span"]["uz_min"], 2), sls4_util=round(-c["SLS 4 kN front, mid-span"]["uz_min"] / 12.16, 2),
                     crowd=round(-c["SLS crowd"]["uz_min"], 2), crowd_util=round(-c["SLS crowd"]["uz_min"] / 4.86, 2),
                     person=round(-c["SLS person 1 kN at the nosing"]["uz_min"], 2),
                     eq_ok=all(abs(r["eq"][0] - r["eq"][1]) < 1 for r in c.values())))
json.dump(rows, open("candidates_summary.json", "w"), indent=1)
for r in rows: print(json.dumps(r))
