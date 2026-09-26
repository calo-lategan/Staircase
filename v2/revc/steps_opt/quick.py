"""Quick variant runner: python3 quick.py '<json dict of overrides>' [cases...] -> one line summary + JSON line."""
import sys, json
import stepfe as s

FD = {"6082-T6": 250 / 1.1, "6005A-T6": 225 / 1.1}


def summary(name, D, cases):
    r = s.run({**s.DEFAULT, **D}, cases, verbose=False)
    uls = [v for k, v in r.items() if k.startswith("ULS")]
    worst = (0, "")
    for v in uls:
        for part, val in v["by_part"].items():
            if "rigid-link" in part: continue
            if val[0] > worst[0]: worst = (val[0], f"{part} @ {v['label']} {val[1:]}")
    sls4 = r.get("SLS 4 kN front, mid-span", {}).get("uz_min")
    crowd = r.get("SLS crowd", {}).get("uz_min")
    person = r.get("SLS person 1 kN at the nosing", {}).get("uz_min")
    m = next(iter(r.values()))["mass_model_kg"]; oa = next(iter(r.values()))["open_area"]
    line = dict(name=name, mass=round(m, 3), open=round(oa, 3), vm=worst[0], u6082=round(worst[0] / FD["6082-T6"], 3),
                u6005A=round(worst[0] / FD["6005A-T6"], 3), where=worst[1], sls4=sls4, crowd=crowd, person=person, D=D)
    return line, r


if __name__ == "__main__":
    D = json.loads(sys.argv[1]); cases = sys.argv[2:] or ["ULS 4 kN front, mid-span", "SLS 4 kN front, mid-span"]
    line, r = summary(D.pop("name", "x"), D, cases)
    print(json.dumps(line, default=str))
