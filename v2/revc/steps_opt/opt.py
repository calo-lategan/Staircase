"""Greedy discrete mass descent for the L-envelope step (family 'skin + ribs' or 'grating').
Each candidate is checked with the screening cases; accept the lightest feasible single-step change; repeat."""
import sys, json, time, os
from multiprocessing import Pool
import stepfe as s

SIG_MAX = 215.0 / 1.1          # 6005A-T6 hollow extrusion f0 215 (t<=5): also covers 6082-T6 (250) with margin
CASES = ["ULS 4 kN front, mid-span", "ULS 4 kN front, at the end", "SLS 4 kN front, mid-span", "SLS crowd"]


def evaluate(D):
    t0 = time.time()
    try:
        r = s.run({**s.DEFAULT, **D}, CASES, verbose=False)
    except Exception as ex:
        return dict(D=D, ok=False, err=str(ex))
    vm, where = 0.0, ""
    for cn, v in r.items():
        if not cn.startswith("ULS"): continue
        for part, val in v["by_part"].items():
            if "rigid-link" in part: continue
            if val[0] > vm: vm, where = val[0], f"{part} | {cn} | {val[1:]}"
    sls4 = -r["SLS 4 kN front, mid-span"]["uz_min"]; crowd = -r["SLS crowd"]["uz_min"]
    m = r[CASES[0]]["mass_model_kg"]
    u = max(vm / SIG_MAX, sls4 / s.LIM["sls4"], crowd / s.LIM["crowd"])
    return dict(D=D, mass=round(m, 3), vm=vm, u_str=round(vm / SIG_MAX, 3), sls4=round(sls4, 2), crowd=round(crowd, 2), u=round(u, 3),
                ok=u <= 1.0, where=where, open=round(r[CASES[0]]["open_area"], 3), parts=r[CASES[0]]["mass_parts"], sec=round(time.time() - t0))


def descend(start, space, log, workers=4, max_iter=30):
    cur = evaluate(start); print(json.dumps(cur), flush=True); log.append(cur)
    if not cur["ok"]:
        print("start infeasible", flush=True)
    for it in range(max_iter):
        cands = []
        for k, lst in space.items():
            v = cur["D"].get(k, s.DEFAULT.get(k))
            if v in lst:
                i = lst.index(v)
                if i + 1 < len(lst): cands.append({**cur["D"], k: lst[i + 1]})
        if not cands: break
        with Pool(workers) as p: res = p.map(evaluate, cands)
        for r in res: log.append(r); print("   ", json.dumps({k: r.get(k) for k in ("mass", "u", "u_str", "sls4", "crowd", "where")}), {k: v for k, v in r["D"].items() if cur["D"].get(k) != v}, flush=True)
        feas = [r for r in res if r.get("ok")]
        if not feas: break
        # combine all feasible single moves (best mass-saving per utilisation rise first); drop the worst until feasible
        def ratio(r): return (cur["mass"] - r["mass"]) / max(1e-3, r["u"] - cur["u"] + 0.01)
        feas.sort(key=ratio, reverse=True)
        best = min(feas, key=lambda r: r["mass"])
        moves = [{k: v for k, v in r["D"].items() if cur["D"].get(k) != v} for r in feas]
        while len(moves) > 1:
            comb = dict(cur["D"])
            for mv in moves: comb.update(mv)
            rc = evaluate(comb); log.append(rc)
            print("   combined", len(moves), json.dumps({k: rc.get(k) for k in ("mass", "u", "where")}), flush=True)
            if rc.get("ok") and rc["mass"] < best["mass"]:
                best = rc; break
            moves = moves[:-1] if len(moves) > 2 else moves[:1]
            if len(moves) == 1: break
        cur = best; print(f"iter {it}: accept {json.dumps({k: v for k, v in cur['D'].items() if k in space})} mass {cur['mass']} u {cur['u']}", flush=True)
    return cur


if __name__ == "__main__":
    tag = sys.argv[1]
    cfg = json.load(open(sys.argv[2]))
    log = []
    best = descend(cfg["start"], cfg["space"], log)
    json.dump(dict(best=best, log=log), open(f"opt_{tag}.json", "w"), indent=1, default=str)
    print("BEST", json.dumps(best, default=str))
