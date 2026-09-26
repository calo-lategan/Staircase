"""Section analysis from mesh slices: join cut segments into closed loops, classify outer / hole by containment,
compute area, centroid, second moments (about centroidal axes of the section plane), extreme fibres, and plot."""
import json, math, sys
from collections import defaultdict


def loops_from_segments(segs, tol=1e-6):
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))
    adj = defaultdict(list)
    pts = {}
    for a, b in segs:
        ka, kb = key(a), key(b)
        if ka == kb:
            continue
        pts[ka], pts[kb] = a, b
        adj[ka].append(kb); adj[kb].append(ka)
    seen, loops = set(), []
    for start in list(adj):
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [n for n in adj[cur] if n != prev and (n not in seen or (n == start and len(loop) > 2))]
            if not nxt:
                break
            n = nxt[0]
            if n == start:
                break
            loop.append(n); seen.add(n); prev, cur = cur, n
        if len(loop) >= 3:
            loops.append([pts[k] for k in loop])
    return loops


def poly_props(P):
    A = Cx = Cy = Ixx = Iyy = Ixy = 0.0
    n = len(P)
    for i in range(n):
        x0, y0 = P[i]; x1, y1 = P[(i + 1) % n]
        c = x0 * y1 - x1 * y0
        A += c; Cx += (x0 + x1) * c; Cy += (y0 + y1) * c
        Ixx += (y0 * y0 + y0 * y1 + y1 * y1) * c       # about the x axis (bending depth along y)
        Iyy += (x0 * x0 + x0 * x1 + x1 * x1) * c
        Ixy += (x0 * y1 + 2 * x0 * y0 + 2 * x1 * y1 + x1 * y0) * c
    A /= 2.0
    return A, Cx / 6.0, Cy / 6.0, Ixx / 12.0, Iyy / 12.0, Ixy / 24.0   # area, int x dA, int y dA, int y2 dA, int x2 dA, int xy dA


def point_in(poly, p):
    x, y = p; inside = False
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-18) + x0:
            inside = not inside
    return inside


def section(loops):
    """outer loops add, holes (inside an odd number of other loops) subtract. Works in local coordinates
    (shifted to the bbox corner) so world-scale offsets do not destroy precision."""
    allp = [p for L in loops for p in L]
    x0, y0 = min(p[0] for p in allp), min(p[1] for p in allp)
    loc = [[(p[0] - x0, p[1] - y0) for p in L] for L in loops]
    A = Sx = Sy = Ixx = Iyy = Ixy = 0.0
    info = []
    for i, L in enumerate(loc):
        depth = sum(1 for j, M in enumerate(loc) if j != i and point_in(M, L[0]))
        a, sy_, sx_, ixx, iyy, ixy = poly_props(L)
        if a < 0:                       # make every loop positive (counter-clockwise)
            L = L[::-1]
            a, sy_, sx_, ixx, iyy, ixy = poly_props(L)
        sgn = 1 if depth % 2 == 0 else -1
        A += sgn * a; Sx += sgn * sx_; Sy += sgn * sy_
        Ixx += sgn * ixx; Iyy += sgn * iyy; Ixy += sgn * ixy
        info.append(dict(n=len(L), area=a, hole=sgn < 0))
    cx, cy = Sy / A, Sx / A
    Ix = Ixx - A * cy * cy
    Iy = Iyy - A * cx * cx
    Ixyc = Ixy - A * cx * cy
    W = max(p[0] for L in loc for p in L); H = max(p[1] for L in loc for p in L)
    return dict(A=A, cx=cx + x0, cy=cy + y0, Ix=Ix, Iy=Iy, Ixy=Ixyc, c_top=H - cy, c_bot=cy, c_right=W - cx, c_left=cx,
                w=W, h=H, loops=info)
