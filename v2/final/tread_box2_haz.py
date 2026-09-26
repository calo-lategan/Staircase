"""Weld-zone (HAZ) check of the closed-box step options for different ways of building them. 6082-T6 next to a weld:
f_o,haz 125 MPa (EN 1999-1-1 Table 3.2b, rho_o,haz 0.50), HAZ width 25 mm each side of the weld (b_haz 20 mm for
t <= 6 mm MIG, plus margin). Layouts:
  'welded corners'   : deck, walls and bottom as separate plates, welded at all four corners (and inner webs welded)
  'bent top U'       : deck + front + back wall bent from one sheet (top corners are bends, no HAZ); bottom plate welded
                       at the two bottom corners; inner webs (if any) welded to deck and bottom
  'bent top U, riveted webs' : as above, inner webs riveted/bolted (no HAZ at the webs)
  'extruded'         : one extrusion, no welds
Governing ULS cases only (4 kN front and centre at mid-span)."""
import json, math, sys
import numpy as np
import openseespy.opensees as ops
import tread_box2 as B

HAZ_W = 25.0
def zones(layout, webs):
    """return a function (element) -> True if the element lies in a weld zone"""
    def f(e):
        x, z, part = e["xm"], e["zm"], e["part"]
        if layout == "extruded": return False
        near_web = any(abs(x - w) <= HAZ_W for w in webs) and part in ("deck", "bottom")
        web_ends = part.startswith("web") and (z <= 2.5 + HAZ_W or z >= 47.5 - HAZ_W)
        if layout == "welded corners":
            if part in ("deck", "bottom") and (x <= 2.5 + HAZ_W or x >= 277.5 - HAZ_W): return True
            if part in ("rear wall", "front web") and (z <= 2.5 + HAZ_W or z >= 47.5 - HAZ_W): return True
            return near_web or web_ends
        if layout.startswith("bent top U"):
            if part == "bottom" and (x <= 2.5 + HAZ_W or x >= 277.5 - HAZ_W): return True
            if part in ("rear wall", "front web") and z <= 2.5 + HAZ_W: return True
            if "riveted" in layout: return False
            return near_web or web_ends
        return False
    return f

LAYOUTS = ["welded corners", "bent top U", "bent top U, riveted webs", "extruded"]
if __name__ == "__main__":
    names = sys.argv[1:] or list(B.OPTIONS)
    out = {}
    for name in names:
        cfg = B.OPTIONS[name]; webs = cfg.get("webs", ())
        res = {L: 0.0 for L in LAYOUTS}; where = {}
        for cn in ("ULS 4 kN front, mid-span", "ULS 4 kN centre, mid-span", "ULS 4 kN front, at the end"):
            fn, swf = B.CASES[cn]
            nodes, elems, pins, ys, seams = B.build(**cfg)
            for pn, (c, b) in pins.items(): ops.fix(b, 1, 1 if pn == "L_rear" else 0, 1, 0, 0, 0)
            ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
            F = {}
            for et, e in elems.items():
                f = B.RHO_W * e["t"] * e["area"] * swf + ((fn(e) or 0.0) * e["area"] if e["part"] == "deck" else 0.0)
                for n in ops.eleNodes(et): F[n] = F.get(n, 0.0) + f / 4
            for n, fz in F.items(): ops.load(n, 0.0, 0.0, -fz, 0.0, 0.0, 0.0)
            ops.constraints("Transformation"); ops.numberer("RCM"); ops.system("UmfPack"); ops.algorithm("Linear")
            ops.integrator("LoadControl", 1.0); ops.analysis("Static"); ops.analyze(1); ops.reactions()   # reactions() updates element stresses
            zf = {L: zones(L, webs) for L in LAYOUTS}
            for et, e in elems.items():
                if e["kind"] != "plate" or not (40 < e["ym"] < 1190): continue
                r = ops.eleResponse(et, "stresses"); t = e["t"]
                if not r: continue
                vm = 0.0
                for gp in np.array(r).reshape(-1, 8):
                    N11, N22, N12, M11, M22, M12 = gp[:6]
                    for s in (1, -1):
                        a = N11 / t + s * 6 * M11 / t ** 2; b = N22 / t + s * 6 * M22 / t ** 2; c = N12 / t + s * 6 * M12 / t ** 2
                        vm = max(vm, math.sqrt(a * a + b * b - a * b + 3 * c * c))
                for L in LAYOUTS:
                    lim = B.FD_HAZ if zf[L](e) else B.FD
                    u = vm / lim
                    if u > res[L]: res[L] = u; where[L] = (cn, e["part"], round(e["xm"], 1), round(e["zm"], 1), round(vm, 1), "HAZ" if zf[L](e) else "parent")
        out[name] = dict(util=res, where=where)
        print(name, {L: round(u, 2) for L, u in res.items()}, flush=True)
        for L in LAYOUTS: print("    ", L, where[L])
    old = {}
    try: old = json.load(open("tread_box2_haz.json"))
    except Exception: pass
    old.update(out); json.dump(old, open("tread_box2_haz.json", "w"), indent=1)
