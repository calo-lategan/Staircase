import sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "loadtest"))
import lightweight_events_2026 as LW
def uchan(slot, wall, depth_slot):
    """open-top U channel: two walls + base, slot width x slot depth (right-hand rail slides in)"""
    W = slot + 2 * wall; H = depth_slot + wall
    s = LW.rects([(wall, H, H / 2), (wall, H, H / 2), (slot, wall, wall / 2)])
    s.update(t=wall, outer=f"{W:g} x {H:g}"); return s
T = LW.tread_plank(depth=40, skin=1.8, webs=5, down=(35.0, 2.0))
fs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "loadtest", "lightweight_final.json")))
v = fs["recommended (1.8 mm tread skins)"]
hr_kg = v["mass"]["posts 6x SHS 60x60x4"] + v["mass"]["guardrails 2x CHS 40x2"] + v["mass"]["handrails 2x CHS 48.3x3 (+300 ext)"] + v["mass"]["intermediate rails 2x CHS 30x2"]
out = {}
right = (LW.rhs(25.0, 45.0, 3.0), LW.rhs(25.0, 25.0, 2.5))
for wall in (3.0, 4.0, 5.0):
    lo, up = uchan(25.0, wall, 45.0), uchan(25.0, wall, 25.0)
    lo["L"], up["L"] = 1778.7, 1845.1
    c = LW.check_girder(lo, up, T["A"], hr_kg / 2 * 9.81)
    mass = (lo["A"] * 1778.7 + up["A"] * 1845.1) * LW.RHO
    out[f"left U-channels, {wall:g} mm walls"] = dict(lower=lo["outer"], upper=up["outer"], A_lo=round(lo["A"]), A_up=round(up["A"]),
        mass_2bars_kg=round(mass, 2), standard=c["standard"], catwalk_midfoot=c["catwalk_midfoot"], steep_crew=c["steep_crew"], f1=c["f1_standard_Hz"])
lo, up = right; lo["L"], up["L"] = 1778.7, 1845.1
c = LW.check_girder(lo, up, T["A"], hr_kg / 2 * 9.81)
out["right RHS 25x45x3 / 25x25x2.5 (spec)"] = dict(A_lo=round(lo["A"]), A_up=round(up["A"]), mass_2bars_kg=round((lo["A"] * 1778.7 + up["A"] * 1845.1) * LW.RHO, 2),
    standard=c["standard"], catwalk_midfoot=c["catwalk_midfoot"], steep_crew=c["steep_crew"])
out["spec assumed left = right x 35/25 (kg)"] = round((right[0]["A"] * 1778.7 + right[1]["A"] * 1845.1) * 1.4 * LW.RHO, 2)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "left_channel_check.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
