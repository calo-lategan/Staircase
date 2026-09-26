"""Exact rail cross-sections (polygons with the real features), measured in the model (see rail_features.json,
jslot_geom / renders): gross, at a tread-pin station (inner-wall O10 hole + outer-wall window/notch), at a pole web
slot. Local frame per rail: w across (0 at the outer face of the -w wall), z up (0 at the rail bottom). Units mm."""
import json, math
from section_tools import section


def rect(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def union_rects(rects):
    """properties of a set of non-overlapping rectangles (exact)"""
    A = Sx = Sz = Ixx = Izz = Ixz = 0.0
    for x0, z0, x1, z1 in rects:
        b, h = x1 - x0, z1 - z0
        if b <= 0 or h <= 0:
            continue
        a = b * h; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        A += a; Sx += a * cx; Sz += a * cz
        Ixx += b * h ** 3 / 12 + a * cz * cz; Izz += h * b ** 3 / 12 + a * cx * cx; Ixz += a * cx * cz
    xc, zc = Sx / A, Sz / A
    zs = [z for r in rects for z in (r[1], r[3])]; xs_ = [x for r in rects for x in (r[0], r[2])]
    Iv = Ixx - A * zc * zc; Il = Izz - A * xc * xc; Ic = Ixz - A * xc * zc
    return dict(A=A, w_c=xc, z_c=zc, I_vert=Iv, I_lat=Il, I_prod=Ic, c_top=max(zs) - zc, c_bot=zc - min(zs),
                W_top=Iv / (max(zs) - zc), W_bot=Iv / (zc - min(zs)))


RAILS = {
    # left rails: U 35 x 25, t 5, web at the bottom (z 0-5); outer wall = w 0-5, inner wall = w 30-35
    "Lo_L 037 (U 35x25x5, open top)": dict(
        gross=[(0, 0, 35, 5), (0, 5, 5, 25), (30, 5, 35, 25)],
        pin_station=[(0, 0, 35, 5), (30, 5, 35, 7.5), (30, 17.5, 35, 25)],           # outer wall window to the web; inner O10 hole at z 12.5
        pole_slot=[(0, 0, 12.5, 5), (22.5, 0, 35, 5), (0, 5, 5, 25), (30, 5, 35, 25)],   # 10 mm web slot w 12.5-22.5
    ),
    "Up_L 026 (U 35x25x5, open top)": dict(
        gross=[(0, 0, 35, 5), (0, 5, 5, 25), (30, 5, 35, 25)],
        pin_station=[(0, 0, 35, 5), (30, 5, 35, 7.5), (30, 17.5, 35, 25)],           # J-slot (O15 seat) removes the outer wall above the web
        pole_slot=[(0, 0, 12.5, 5), (22.5, 0, 35, 5), (0, 5, 5, 25), (30, 5, 35, 25)],
    ),
    # right rails: inverted U 25 x 20, t 5, web at the top (z 15-20); inner wall = w 0-5, outer wall = w 20-25
    "Up_R 118 (inv. U 25x20x5, open bottom)": dict(
        gross=[(0, 15, 25, 20), (0, 0, 5, 15), (20, 0, 25, 15)],
        pin_station=[(0, 15, 25, 20), (0, 0, 5, 2.5), (0, 12.5, 5, 15), (20, 12.5, 25, 15)],   # inner O10 hole z 2.5-12.5; outer J-notch from the free edge to z 12.5
        pole_slot=[(0, 15, 7.5, 20), (17.5, 15, 25, 20), (0, 0, 5, 15), (20, 0, 25, 15)],       # 10 mm web slot w 7.5-17.5
    ),
    "Lo_R 179 (inv. U 25x20x5, open bottom)": dict(
        gross=[(0, 15, 25, 20), (0, 0, 5, 15), (20, 0, 25, 15)],
        pin_station=[(0, 15, 25, 20), (0, 0, 5, 2.5), (0, 12.5, 5, 15)],                       # inner O10 hole; outer O15 window takes the whole wall
        pole_slot=[(0, 15, 7.5, 20), (17.5, 15, 25, 20), (0, 0, 5, 15), (20, 0, 25, 15)],
    ),
}

if __name__ == "__main__":
    out = {}
    for name, S in RAILS.items():
        out[name] = {k: union_rects(v) for k, v in S.items()}
        g = out[name]["gross"]
        print(f"\n{name}")
        for k, p in out[name].items():
            print(f"   {k:<12} A={p['A']:6.1f} ({p['A']/g['A']*100:5.1f}%)  z_c={p['z_c']:5.2f}  I_vert={p['I_vert']:8.0f} ({p['I_vert']/g['I_vert']*100:5.1f}%)  "
                  f"W_top={p['W_top']:6.0f} W_bot={p['W_bot']:6.0f}  I_lat={p['I_lat']:7.0f}  I_prod={p['I_prod']:7.0f}")
    json.dump(out, open("rail_sections.json", "w"), indent=1)
    # the previous load test used these (loadtest_latest.SEC):
    print("\nprevious SEC: bar_L_lo A=314.1 I=16156 c=15.21 | bar_L_up A=526.0 I=24959 c=14.22 | bar_R_up A=274.7 I=9878 c=12.05 | bar_R_lo A=275.0 I=7562 c=12.80")
