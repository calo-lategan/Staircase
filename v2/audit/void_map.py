"""Find holes / slots / notches in a longitudinal wall or web raster. Grid at `res` mm; voids = empty cells inside the
part's envelope rows; connected components labelled; each reported with bbox, area, centroid, opening edge."""
import json, sys, math
import numpy as np
from scipy import ndimage


def grid(cut, res=0.1):
    rows = cut["rows"]
    us = [x for _, ivs in rows for iv in ivs for x in iv]
    if not us:
        return None
    u0, u1 = min(us), max(us)
    nu = int(math.ceil((u1 - u0) / res))
    G = np.zeros((len(rows), nu), dtype=bool)
    vs = []
    for i, (v, ivs) in enumerate(rows):
        vs.append(v)
        for a, b in ivs:
            ia, ib = int(round((a - u0) / res)), int(round((b - u0) / res))
            G[i, max(ia, 0):min(ib, nu)] = True
    return G, u0, np.array(vs), res


def voids(cut, res=0.1, min_area=2.0):
    g = grid(cut, res)
    if g is None:
        return None
    G, u0, vs, res = g
    filled_rows = np.where(G.any(axis=1))[0]
    r0, r1 = filled_rows.min(), filled_rows.max()
    cols = np.where(G.any(axis=0))[0]; c0, c1 = cols.min(), cols.max()
    env = np.zeros_like(G); env[r0:r1 + 1, c0:c1 + 1] = True
    V = env & ~G
    lab, n = ndimage.label(V)
    out = []
    dv = (vs[1] - vs[0]) if len(vs) > 1 else res
    for k, sl in enumerate(ndimage.find_objects(lab), start=1):
        m = lab[sl] == k
        area = m.sum() * res * dv
        if area < min_area:
            continue
        rr, cc = np.nonzero(m)
        rr = rr + sl[0].start; cc = cc + sl[1].start
        umin, umax = u0 + cc.min() * res, u0 + (cc.max() + 1) * res
        vmin, vmax = vs[rr.min()] - dv / 2, vs[rr.max()] + dv / 2
        opens = [e for e, cond in (("top", rr.max() == r1), ("bottom", rr.min() == r0), ("start", cc.min() == c0), ("end", cc.max() == c1)) if cond]
        w, h = umax - umin, vmax - vmin
        roundness = area / (math.pi / 4 * w * h) if w * h > 0 else 0
        out.append(dict(u_min=round(umin, 2), u_max=round(umax, 2), v_min=round(vmin, 2), v_max=round(vmax, 2), w=round(w, 2), h=round(h, 2),
                        area=round(area, 1), cu=round(u0 + (cc.mean() + 0.5) * res, 2), cv=round(float(vs[rr].mean()), 2), opens=opens,
                        kind=("round hole d=%.2f" % ((w + h) / 2) if not opens and abs(roundness - 1) < 0.04 and abs(w - h) < 0.4 else
                              "closed slot" if not opens else "open " + "/".join(opens))))
    env_box = dict(u=(round(u0 + c0 * res, 2), round(u0 + (c1 + 1) * res, 2)), v=(round(vs[r0] - dv / 2, 2), round(vs[r1] + dv / 2, 2)))
    return env_box, sorted(out, key=lambda d: d["u_min"])


if __name__ == "__main__":
    R = json.load(open(sys.argv[1]))
    res = {}
    for k, cut in R.items():
        r = voids(cut)
        if r is None:
            print(k, "EMPTY"); continue
        env, vo = r
        res[k] = dict(envelope=env, voids=vo)
        print(f"\n=== {k}  envelope u {env['u']} v {env['v']}  ({len(vo)} voids)")
        for d in vo:
            print(f"   u[{d['u_min']:9.2f},{d['u_max']:9.2f}] v[{d['v_min']:8.2f},{d['v_max']:8.2f}] w={d['w']:6.2f} h={d['h']:5.2f} A={d['area']:7.1f} c=({d['cu']:.2f},{d['cv']:.2f}) {d['kind']}")
    json.dump(res, open(sys.argv[2], "w"), indent=1)
