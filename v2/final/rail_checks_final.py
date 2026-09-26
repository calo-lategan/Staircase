"""Final-model rail checks: side-frame forces (latch pins engaged = the only stable configuration) x exact net sections.
Net sections at every tread-pin station (inner-wall O10 hole + outer-wall window / J-notch / J-entry, measured), gross
elsewhere. sigma = N/A + M/W (both fibres), EN 1999-1-1: f_o/gM1 = 250/1.1 (t <= 5). Load cases: ULS crowd (all treads),
pattern (lower 3 / upper 3 treads loaded)."""
import json, math
import numpy as np
import side_frame as SF
import run_side_frame as R

def rects_props(rects):
    A = sum((x1 - x0) * (z1 - z0) for x0, z0, x1, z1 in rects)
    zc = sum((x1 - x0) * (z1 - z0) * (z0 + z1) / 2 for x0, z0, x1, z1 in rects) / A
    I = sum((x1 - x0) * (z1 - z0) ** 3 / 12 + (x1 - x0) * (z1 - z0) * ((z0 + z1) / 2 - zc) ** 2 for x0, z0, x1, z1 in rects)
    zs = [z for r in rects for z in (r[1], r[3])]
    return dict(A=A, I=I, zc=zc, W_top=I / (max(zs) - zc), W_bot=I / (zc - min(zs)))

SECTIONS = {
    "Lo_L": dict(gross=rects_props([(0, 0, 35, 5), (0, 5, 5, 25), (30, 5, 35, 25)]),
                 net=rects_props([(0, 0, 35, 5), (30, 5, 35, 7.5), (30, 17.5, 35, 25)])),
    "Up_L": dict(gross=rects_props([(0, 0, 35, 5), (0, 5, 5, 25), (30, 5, 35, 25)]),
                 net=rects_props([(0, 0, 35, 5), (30, 5, 35, 7.5), (30, 17.5, 35, 25)])),
    "Lo_R": dict(gross=rects_props([(0, 20, 25, 25), (0, 0, 5, 20), (20, 0, 25, 20)]),
                 net=rects_props([(0, 20, 25, 25), (0, 0, 5, 7.5), (0, 17.5, 5, 20), (20, 17.5, 25, 20)])),
    "Up_R": dict(gross=rects_props([(0, 15, 25, 20), (0, 0, 5, 15), (20, 0, 25, 15)]),
                 net=rects_props([(0, 15, 25, 20), (0, 0, 5, 2.5), (0, 12.5, 5, 15), (20, 12.5, 25, 15)])),
}
FD = 250.0 / 1.1
SF.VERTICAL_AT_UPPER = True

def check(side, forces, label, slide=False):
    out = SF.run(side, forces, bracket_rigid=True, label=label, base_slides=slide)
    res = {}
    for key, rn in (("lo", "Lo_" + side), ("up", "Up_" + side)):
        rows = out[f"rail_{key}"]
        r = SF.G[side][f"rail_{key}"]
        a, b = np.array(r["a"]), np.array(r["b"]); u = (b - a) / np.linalg.norm(b - a)
        # pin stations along this rail (rear pins on the lower rail, front pins on the upper rail)
        pins = [((t["back"] + (25 if key == "lo" else 225)), t["z0"] + (12.5 if key == "lo" else 37.5)) for t in SF.TREADS]
        st = [float((np.array(p) - a) @ u) for p in pins]
        worst = (0, None)
        for s, N, M1, M2 in rows:
            near = min(abs(s - x) for x in st) < 13.0          # within the hole / window zone
            sec = SECTIONS[rn]["net" if near else "gross"]
            for M in (M1, M2):
                sig = max(abs(N / sec["A"] + M / sec["W_bot"]), abs(N / sec["A"] - M / sec["W_top"]),
                          abs(N / sec["A"] - M / sec["W_bot"]), abs(N / sec["A"] + M / sec["W_top"]))
                if sig > worst[0]: worst = (sig, dict(s=round(s), N=round(N), M=round(M), section="net (pin station)" if near else "gross"))
        res[rn] = worst
    return res, out

if __name__ == "__main__":
    for slide in (False, True):
        allres = {}
        for side in ("L", "R"):
            for label, only in (("ULS crowd, all treads", None), ("ULS crowd, lower 3 treads", {0, 1, 2}), ("ULS crowd, upper 3 treads", {3, 4, 5})):
                forces = R.pf("ULS crowd", side, only)
                res, out = check(side, forces, label, slide)
                for rn, (sig, info) in res.items():
                    u = sig / FD
                    print(f"{'slides' if slide else 'held  '} {rn:<5} {label:<28} sigma {sig:7.1f} MPa  util {u:5.2f} {'FAIL' if u > 1 else 'PASS'}  at {info}")
                    allres[f"{rn} | {label}" + (" | base slides" if slide else "")] = dict(sigma=sig, util=u, **info)
        if slide: json.dump(allres, open("rail_checks_final_slide.json", "w"), indent=1)
        else: json.dump(dict(sections=SECTIONS, results=allres), open("rail_checks_final.json", "w"), indent=1)
