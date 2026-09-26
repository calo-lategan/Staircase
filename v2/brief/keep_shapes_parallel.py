"""Parallel driver for keep_shapes_check.py (same functions, one process per scenario)."""
import sys, os, json, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__))


def job(key):
    sys.path.insert(0, HERE)
    import importlib.util
    spec = importlib.util.spec_from_file_location("ks", os.path.join(HERE, "keep_shapes_lib.py"))
    ks = importlib.util.module_from_spec(spec); spec.loader.exec_module(ks)
    return key, ks.run_job(key)


if __name__ == "__main__":
    keys = [(q, side, sup) for q in ("7.5", "5.0") for side in ("right", "left") for sup in ("mid", "ends")] + [("poles",)]
    with mp.Pool(9) as pool:
        res = dict(pool.map(job, keys))
    out = {}
    for k, v in res.items():
        out[" | ".join(k)] = v
    json.dump(out, open(os.path.join(HERE, "keep_shapes_check.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
