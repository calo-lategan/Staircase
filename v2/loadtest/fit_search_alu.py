"""Find upper/lower guide-bar depths (solid 6061-T6, existing widths) that pass the locked-girder ULS stress
and SLS deflection in every lock AND fit the catwalk stack envelope (bars nearly stacked at 0 deg).
Envelope (measured at catwalk, vertical): ground -> lower-bar bottom 34.7 | lower 20.45 | gap 5.4 |
upper 20.0 | gap to tread end 19.5 mm.  Lower bar grows DOWN, upper bar grows UP (slot edges stay put)."""
import copy, json, math
import loadtest_latest as L
b = "B"; KEEP = copy.deepcopy(L.SEC)
fy = L.BASIS[b]["s"]["fy"] / L.BASIS[b]["s"]["gM"]
bo, t = 50.0, 4.0
I = (bo**4 - (bo - 2*t)**4) / 12
L.SEC["post"].update(A=bo*bo - (bo-2*t)**2, I=I, c=bo/2)
wst = L.SEC["tread"]["A"] * L.BASIS[b]["t"]["rho"] * L.G
hr = L.self_weight(b)["_handrail_per_side"] * L.G
CLR_GROUND, CLR_TREAD = 34.7, 19.5
res = []
for h_up in (20, 25, 30, 35):
    for h_lo in range(30, 66, 5):
        up = dict(A=25.0*h_up, I=25.0*h_up**3/12, c=h_up/2, L=KEEP["bar_R_up"]["L"])
        lo = dict(A=25.0*h_lo, I=25.0*h_lo**3/12, c=h_lo/2, L=KEEP["bar_R_lo"]["L"])
        us, ds = [], []
        for lock in L.LOCKS:
            us.append(L.girder_utils(lock, b, L.Q_UDL, lo=lo, up=up)["locked_fe"])
            r, _ = L.side_frame_fe(lock, b, L.Q_UDL, wst, hr, up, lo, "locked")
            ds.append(max(abs(r["u"][1::3])) / L.defl_lim(L.SPAN))
        g_clear = CLR_GROUND - (h_lo - 20.45)
        t_clear = CLR_TREAD - (h_up - 20.0)
        res.append(dict(h_up=h_up, h_lo=h_lo, util=round(max(us), 3), defl=round(max(ds), 3),
                        ground_clear=round(g_clear, 1), tread_clear=round(t_clear, 1),
                        passes=bool(max(us) <= 1 and max(ds) <= 1), fits=bool(g_clear >= 10 and t_clear >= 3)))
ok = [r for r in res if r["passes"]]
[print(r["h_up"], r["h_lo"], r["util"], r["defl"], r["ground_clear"], r["tread_clear"]) for r in ok]
fit = [r for r in ok if r["fits"]]
print("FITS:", json.dumps(fit[:6]))
