import sys, os, math, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "loadtest"))
import lightweight_events_2026 as LW
post = LW.rhs(60, 60, 4)
out = {}
# R144 middle rail 1.25 kN point, posts at treads 0,2,5, standard + catwalk; rail alone on the posts (conservative)
for name, sec in (("CHS 30x2", LW.chs(30, 2)), ("CHS 33.7x3", LW.chs(33.7, 3)), ("CHS 40x2", LW.chs(40, 2)), ("CHS 40x2.5", LW.chs(40, 2.5)), ("CHS 42.4x2.5", LW.chs(42.4, 2.5))):
    u = 0
    for lock in ("CATWALK", "STANDARD"):
        r = LW.barrier_fe(lock, [0, 2, 5], post, {"mid": (575.0, sec)}, 0.0, "mid")
        m = max(r["M_rail"].values())
        u = max(u, m / (sec["I"] / sec["c"] * LW.f0(sec["t"]) / LW.GM1))
    out[f"mid rail {name}"] = dict(util_1_25kN=round(u, 2), kg_2x=round(2 * sec["A"] * 1725.8 * LW.RHO, 2))
# same rail with the guardrail + handrail sharing through the posts (full kit)
rails = {"guard": (1127.0, LW.chs(40, 2)), "hand": (1000.0, LW.chs(48.3, 3)), "mid": (575.0, LW.chs(30, 2))}
# centre handrail supported only at the flight ends: 1.25 kN at mid-span, span along the frame ~ 2.1 m incl. ends
h = LW.chs(48.3, 3)
for span in (1.9, 2.1, 2.4):
    M = LW.GQ * 1250 * span * 1000 / 4
    out[f"centre rail 48.3x3 end-supported span {span} m, 1.25 kN"] = round(M / (h["I"] / h["c"] * LW.f0(3) / LW.GM1), 2)
    M2 = LW.GQ * 1.0 * (span * 1000) ** 2 / 8
    out[f"centre rail 48.3x3 end-supported span {span} m, 1.0 kN/m vertical"] = round(M2 / (h["I"] / h["c"] * LW.f0(3) / LW.GM1), 2)
# clear width between handrails (mm): rail outer faces 1,270 apart, 60 posts outboard with gap g, handrail 48.3 with c clear to post
for g in (0, 15):
    for c in (50, 100):
        out[f"clear width, post gap {g}, handrail clearance {c}"] = round(1270 + 2 * g - 2 * (c + 48.3))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sheet_checks.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
