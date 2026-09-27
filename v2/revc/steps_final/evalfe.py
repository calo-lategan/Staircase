"""Evaluate a step variant with the final FE (stepfe_final.py). Utilisation: extrusions 6005A-T6 hollow f0 215 (t<=5),
fd = 215/1.1 = 195.5; end blocks 6082-T651 plate (12.5<t<=100) f0 240, fd 218.2. Rigid-link pin zones excluded (hand checks)."""
import json, time, sys
from multiprocessing import Pool
import stepfe_final as s, design as dsg

FD_EXT, FD_EXT_6082, FD_EB = 215 / 1.1, 250 / 1.1, 240 / 1.1
SCREEN = ["ULS 4 kN front, mid-span", "ULS 4 kN back, mid-span", "ULS 4 kN front, at the end", "SLS 4 kN front, mid-span"]


def summarise(r):
    ext, eb = (0.0, ""), (0.0, "")
    for cn, v in r.items():
        if not cn.startswith("ULS"): continue
        for part, val in v["by_part"].items():
            if "rigid-link" in part: continue
            if part.startswith("end plate"):
                if val[0] > eb[0]: eb = (val[0], f"{part} | {cn} | {val[1:]}")
            elif val[0] > ext[0]: ext = (val[0], f"{part} | {cn} | {val[1:]}")
    out = dict(vm_ext=ext[0], where_ext=ext[1], u_6005A=round(ext[0] / FD_EXT, 3), u_6082=round(ext[0] / FD_EXT_6082, 3),
               vm_eb=eb[0], where_eb=eb[1], u_eb=round(eb[0] / FD_EB, 3))
    for cn, key, lim in (("SLS 4 kN front, mid-span", "sls4", s.LIM["sls4"]), ("SLS crowd", "crowd", s.LIM["crowd"]),
                         ("SLS person 1 kN at the nosing", "person", s.LIM["person"])):
        if cn in r: out[key] = round(-r[cn]["uz_min"], 2); out["u_" + key] = round(-r[cn]["uz_min"] / lim, 3)
    v0 = next(iter(r.values()))
    out["mass"] = round(v0["mass_model_kg"], 3); out["open"] = round(v0["open_area"], 4); out["parts"] = v0["mass_parts"]
    out["u"] = max([out["u_6005A"], out["u_eb"]] + [out[k] for k in ("u_sls4", "u_crowd", "u_person") if k in out])
    return out


def evaluate(args):
    name, over, cases = args
    t0 = time.time()
    D = {**s.DEFAULT, **dsg.final_cfg(**over)}
    r = s.run(D, cases, verbose=False)
    out = dict(name=name, over=over, **summarise(r), sec=round(time.time() - t0))
    return out, r


if __name__ == "__main__":
    variants = json.load(open(sys.argv[1])); tag = sys.argv[2]
    cases = SCREEN
    with Pool(min(4, len(variants))) as p:
        res = p.map(evaluate, [(k, v, cases) for k, v in variants.items()])
    out = {o["name"]: o for o, r in res}
    json.dump(out, open(f"screen_{tag}.json", "w"), indent=1)
    for o, r in res:
        print(json.dumps({k: o[k] for k in ("name", "mass", "u", "u_6005A", "u_eb", "sls4", "where_ext", "where_eb")}), flush=True)
