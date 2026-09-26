"""Section properties from raster rows (strips). props(rows, step, u0, v0) -> dict. Also wall/void map helpers."""
import json, math


def props(cut, u0=0.0, v0=0.0, vrange=None, urange=None):
    step = cut["step"]; A = Su = Sv = Iuu = Ivv = 0.0
    umin = vmin = 1e18; umax = vmax = -1e18
    for v, ivs in cut["rows"]:
        v = v - v0
        if vrange and not (vrange[0] <= v <= vrange[1]):
            continue
        for a, b in ivs:
            a -= u0; b -= u0
            if urange:
                a, b = max(a, urange[0]), min(b, urange[1])
                if b <= a:
                    continue
            L = b - a; dA = L * step
            A += dA; Su += dA * (a + b) / 2; Sv += dA * v
            Iuu += step * (b ** 3 - a ** 3) / 3          # int u^2 dA
            Ivv += dA * v * v + L * step ** 3 / 12      # int v^2 dA
            umin, umax, vmin, vmax = min(umin, a), max(umax, b), min(vmin, v - step / 2), max(vmax, v + step / 2)
    if A == 0:
        return None
    cu, cv = Su / A, Sv / A
    return dict(A=A, cu=cu, cv=cv, I_about_u_axis=Ivv - A * cv * cv, I_about_v_axis=Iuu - A * cu * cu,
                umin=umin, umax=umax, vmin=vmin, vmax=vmax, c_vtop=vmax - cv, c_vbot=cv - vmin)


def ascii_map(cut, u0, v0, ures=1.0, vskip=1, urange=None, vrange=None):
    """coarse picture: one char per ures mm along u, rows every vskip rows"""
    lines = []
    rows = cut["rows"]
    for k in range(len(rows) - 1, -1, -vskip):
        v, ivs = rows[k]
        if vrange and not (vrange[0] <= v - v0 <= vrange[1]):
            continue
        n = int((urange[1] - urange[0]) / ures)
        s = ["."] * n
        for a, b in ivs:
            for i in range(n):
                uc = urange[0] + (i + 0.5) * ures + u0
                if a <= uc <= b:
                    s[i] = "#"
        lines.append(f"{v - v0:7.2f} " + "".join(s))
    return "\n".join(lines)
