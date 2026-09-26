"""All tread load cases on the validated shell FE (tread_fe.py, MITC4, h=2.5 x 5 mm, exact equilibrium).
Loads per the sheet: R113/R128 crowd 7.5 kN/m2 (catwalk tributary 305.2 mm governs), R114 4.0 kN on 200x200,
R115 L/250 under crowd and < 10 mm under one person (1.0 kN), factors R153 1.35 G + 1.5 Q.
Writes tread_cases.json (per case: deflections, twist, pin forces, peak stresses by part, deck plate stresses)."""
import json, math, time
import numpy as np
import tread_fe as TF

Q, P4, PERSON = 7.5e-3, 4000.0, 1000.0
GG, GQ = 1.35, 1.5
YMID = 618.5                    # mid-span between the pin bearings (10.49 .. 1226.5)
X = dict(front=180.0, centre=140.0, back=100.0)     # 200 mm patch centres: nosing (80-280), middle, back (0-200)


def comb(*fns):
    return lambda e: sum((f(e) or 0.0) for f in fns)


def scaled(f, k):
    return lambda e: k * (f(e) or 0.0)


CASES = {
    "SLS crowd 7.5 kN/m2": (TF.udl_fn(Q), 1.0),
    "ULS crowd": (scaled(TF.udl_fn(Q), GQ), GG),
    "SLS person 1 kN at nosing, mid-span (100x100)": (TF.patch_fn(PERSON, 230.0, YMID, 100.0, 100.0), 1.0),
}
for k, x in X.items():
    CASES[f"SLS 4 kN patch {k}, mid-span"] = (TF.patch_fn(P4, x, YMID), 1.0)
    CASES[f"ULS 4 kN patch {k}, mid-span"] = (TF.patch_fn(GQ * P4, x, YMID), GG)
CASES["ULS 4 kN patch front, at left end (pin)"] = (TF.patch_fn(GQ * P4, 180.0, 120.0), GG)
CASES["ULS 4 kN patch back, at left end (pin)"] = (TF.patch_fn(GQ * P4, 100.0, 120.0), GG)

out = {}
for name, (fn, swf) in CASES.items():
    t0 = time.time()
    r = TF.solve(fn, h=2.5, hy=5.0, sw_factor=swf, label=name)
    rows = r.pop("_rows")
    # deck plate (transverse) bending at mid-span and the max over the deck
    deck = [w for w in rows if w[9] == "prof" and w[10] == 3]
    r["deck_transverse_max"] = max(deck, key=lambda w: abs(w[2]))[:14]
    r["deck_long_min"] = min(deck, key=lambda w: w[1])[:14]
    r["deck_membrane_min"] = min(deck, key=lambda w: w[4])[:14]          # mid-plane longitudinal (for local buckling)
    r["deck_vm_max"] = max(deck, key=lambda w: w[0])[:14]
    r["deck_transverse_bending_max"] = max(deck, key=lambda w: abs(w[7]))[:14]
    lipret = [w for w in rows if w[9] == "prof" and w[10] in (4, 5)]
    r["lip_return_membrane_max"] = max(lipret, key=lambda w: w[4])[:14]
    r["seconds"] = round(time.time() - t0, 1)
    out[name] = r
    print(f"{name:<48} front {r['uz_mid_front_lip']:7.2f} back {r['uz_mid_back']:6.2f} min {r['uz_min']:7.2f} twist {r['twist_mid_deg']:5.2f} deg | "
          f"vm body {r['vm_max_body'][0]:6.1f} ({TF.SEG_NAMES[r['vm_max_body'][10]]} x{r['vm_max_body'][11]} y{r['vm_max_body'][12]}) | pins "
          + " ".join(f"{k}:{v[2]:.0f}/{v[0]:.0f}" for k, v in r["pins"].items()), flush=True)
json.dump(out, open("tread_cases.json", "w"), indent=1, default=str)
