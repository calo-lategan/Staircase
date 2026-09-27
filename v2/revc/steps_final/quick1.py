import sys, json, time
import stepfe_final as s, design as d
D = {**s.DEFAULT, **d.final_cfg(**json.loads(sys.argv[1] if len(sys.argv) > 1 else "{}"))}
cases = sys.argv[2:] or ["ULS 4 kN front, mid-span"]
r = s.run(D, cases)
for k, v in r.items():
    print(k, "mass", round(v["mass_model_kg"], 3), json.dumps(v["mass_parts"]))
    print(json.dumps(sorted(v["by_part"].items(), key=lambda kv: -kv[1][0])[:8]))
