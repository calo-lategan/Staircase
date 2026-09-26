"""All load cases for the FINAL tread on the validated FE (tread_fe2.py, beam bars; governing case re-run with shell
bars). Sheet rows: R113 crowd 7.5 kN/m2 (standard stair: going 250 mm), R114 4.0 kN on 200 x 200, R115 L/250 crowd and
< 10 mm one person (1.0 kN), R153 1.35 G + 1.5 Q."""
import json, time, math, sys
import tread_fe2 as TF
JOINED = "joined" in sys.argv
TF.FLATS_JOINED = JOINED
SUF = "_joined" if JOINED else ""

Q, P4, PERSON, GG, GQ = 7.5e-3, 4000.0, 1000.0, 1.35, 1.5
YMID = 618.0

def scaled(f, k): return lambda yb, x0, x1: k * (f(yb, x0, x1) or 0.0)

CASES = {"SLS crowd 7.5 kN/m2": (TF.udl(Q), 1.0), "ULS crowd": (scaled(TF.udl(Q), GQ), GG),
         "SLS person 1 kN at nosing (100x100)": (TF.patch(PERSON, 225.0, YMID, 100.0, 100.0), 1.0)}
for k, x in (("front", 175.0), ("centre", 140.0), ("back", 105.0)):
    CASES[f"SLS 4 kN patch {k}, mid-span"] = (TF.patch(P4, x, YMID), 1.0)
    CASES[f"ULS 4 kN patch {k}, mid-span"] = (TF.patch(GQ * P4, x, YMID), GG)
CASES["ULS 4 kN patch front, at left end"] = (TF.patch(GQ * P4, 175.0, 125.0), GG)
CASES["ULS 4 kN patch back, at left end"] = (TF.patch(GQ * P4, 105.0, 125.0), GG)
CASES["ULS 4 kN patch front, at right end"] = (TF.patch(GQ * P4, 175.0, 1111.0), GG)

out = {}
for name, (fn, swf) in CASES.items():
    t0 = time.time(); r = TF.solve(fn, sw_factor=swf, label=name); r["s"] = round(time.time() - t0, 1)
    out[name] = r
    vb = r["vm_max_body"]
    print(f"{name:<40} lip {r['uz_mid_lip_top']:7.2f} back {r['uz_mid_rearwall_top']:6.2f} min {r['uz_min']:7.2f} twist {r['twist_mid_deg']:5.2f} | vm {vb[0]:6.1f} {vb[7]} x{vb[8]} y{vb[9]} z{vb[10]} | bar {r['bar_max'][0]:6.1f} | pins "
          + " ".join(f"{k}:{v[2]:.0f}/{v[0]:.0f}" for k, v in r["pins"].items()) + f" | eq dMy {r['equilibrium']['My_support'] - r['equilibrium']['My_load']:.1f}", flush=True)
json.dump(out, open(f"tread2_cases{SUF}.json", "w"), indent=1, default=str)
# governing case with shell bars
g = TF.solve(TF.patch(GQ * P4, 175.0, YMID), sw_factor=GG, label="ULS 4 kN front (shell bars)", bar_shells=True)
print("shell-bar check ULS 4 kN front:", round(g["uz_mid_lip_top"], 2), round(g["vm_max_body"][0], 1), g["vm_max_body"][7])
json.dump(g, open(f"tread2_shellbar_check{SUF}.json", "w"), indent=1, default=str)
