"""Full FE of the FINAL step: all 8 load cases of step_optimisation.md + barrier stud-pull cases. Writes final_fe.json.
python3 run_final.py  (runs cases in parallel, 4 workers)"""
import json, math, sys, time
from multiprocessing import Pool
import stepfe_final as s, design as dsg, evalfe as ev

FINAL = json.load(open("final_cfg.json"))
A = json.load(open("anchorage.json"))["loads_N"]
PF, PR = dsg.PIN_FRONT, dsg.PIN_REAR
def pad(pin, lev, th, n_pad=-7.0, c=12.5):
    t = math.radians(th); nu = (math.sin(t), math.cos(t)); d = c - n_pad; sg = -1 if lev == "up" else 1
    return (pin[0] + sg * d * nu[0], pin[1] + sg * d * nu[1], -th, 30.0, 10.0)
UDL07 = 0.7 * 1.5 * 7.5e-3
s.CASES["ULS barrier 5.0 kN/m: front stud 41.1 kN + tab pad 15.0 kN (35 deg) + 0.7 crowd"] = (
    ("pull", dict(stud=("L_front", A["front_cap"]), pads=[pad(PF, "up", 35.0) + (A["front_pad_with_cap"],)], udl=UDL07)), 1.35)
s.CASES["ULS barrier 5.0 kN/m: front stud 41.1 kN + tab pad 15.0 kN (catwalk)"] = (
    ("pull", dict(stud=("L_front", A["front_cap"]), pads=[pad(PF, "up", 0.0) + (A["front_pad_with_cap"],)], udl=0.0)), 1.35)
s.CASES["ULS handrail inward: rear stud 18.0 kN + pad 9.2 kN, front pad push 17.6 kN (35 deg)"] = (
    ("pull", dict(stud=("L_rear", A["rear_cap"]), pads=[pad(PR, "lo", 35.0) + (A["rear_pad"],), pad(PF, "up", 35.0) + (A["push_max"],)], udl=0.0)), 1.35)

def one(cn):
    D = {**s.DEFAULT, **dsg.final_cfg(**FINAL)}
    t0 = time.time(); r = s.run(D, [cn], verbose=False); r[cn]["sec"] = round(time.time() - t0); return cn, r[cn]

if __name__ == "__main__":
    with Pool(4) as p: res = dict(p.map(one, list(s.CASES)))
    summ = ev.summarise(res)
    out = dict(cfg=FINAL, summary=summ, cases=res)
    json.dump(out, open("final_fe.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in summ.items() if k != "parts"}, indent=1))
    for cn, v in res.items():
        top = sorted(((val[0], part) for part, val in v["by_part"].items() if "rigid-link" not in part), reverse=True)[:3]
        print(f"{cn[:70]:<70} eq {v['eq']} eqy {v.get('eq_y')} uz {v['uz_min']:.2f} top {top}")
        if "eb_to_members_y_N" in v: print("    EB->members", v["eb_to_members_y_N"])
