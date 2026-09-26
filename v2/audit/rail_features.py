"""Rail features from straightened thickness maps: per-wall presence maps, voids (holes, J-slots, notches, web slots),
dimensioned in the rail's own frame (u along rail from its start, v up from its bottom, w across from its -w face)."""
import json, math, sys
import numpy as np
from scipy import ndimage
Z = np.load("tmap2_rails.npz"); M = json.load(open("tmap2_rails.json"))


def comps(mask, du, dv, u0, v0, min_area=3.0):
    lab, n = ndimage.label(mask)
    out = []
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        mm = lab[sl] == k
        area = mm.sum() * du * dv
        if area < min_area:
            continue
        rr, cc = np.nonzero(mm); rr += sl[0].start; cc += sl[1].start
        umin, umax = u0 + cc.min() * du, u0 + (cc.max() + 1) * du
        vmin, vmax = v0 + rr.min() * dv, v0 + (rr.max() + 1) * dv
        d = dict(u=(round(umin, 2), round(umax, 2)), v=(round(vmin, 2), round(vmax, 2)), area=round(area, 1),
                 cu=round(u0 + (cc.mean() + 0.5) * du, 2), cv=round(v0 + (rr.mean() + 0.5) * dv, 2))
        # circle fit to the lowest 40 % of the void's boundary (seat) if the void reaches an edge
        w, h = umax - umin, vmax - vmin
        d["w"], d["h"] = round(w, 2), round(h, 2)
        d["round"] = abs(area / (math.pi / 4 * w * h) - 1) < 0.05 and abs(w - h) < 0.6
        # seat circle: pixels of the void in its bottom 12 mm, fit circle to boundary
        sub = (lab == k)
        er = sub & ~ndimage.binary_erosion(sub)
        br, bc = np.nonzero(er)
        pu = u0 + (bc + 0.5) * du; pv = v0 + (br + 0.5) * dv
        sel = pv < vmin + min(12.0, h)
        if sel.sum() > 8:
            A = np.c_[2 * pu[sel], 2 * pv[sel], np.ones(sel.sum())]; b = pu[sel] ** 2 + pv[sel] ** 2
            x, *_ = np.linalg.lstsq(A, b, rcond=None)
            r = math.sqrt(max(x[2] + x[0] ** 2 + x[1] ** 2, 0))
            d["seat_circle"] = (round(x[0], 2), round(x[1], 2), round(2 * r, 2))
        out.append(d)
    return sorted(out, key=lambda d: d["u"][0])


res = {}
for rail in ["MainRig_037", "MainRig_026", "MainRig_118", "MainRig_179"]:
    ms, mp = M[rail + ":side"], M[rail + ":plan"]
    TH, FI = Z[rail + ":side__TH"], Z[rail + ":side__FIRST"]
    dims = ms["dims_mm"]; L, W, H = dims
    du, dv, u0, v0 = ms["du"], ms["dv"], ms["u0"], ms["v0"]
    print(f"\n######## {rail}  length {L:.2f}  width {W:.2f}  height {H:.2f}  (frame u along, w across, v up)")
    # which rows are web rows? plan map: thickness in the middle columns
    THp = Z[rail + ":plan__TH"]
    wmid = int((W / 2 - mp["v0"]) / mp["dv"])
    web_t = np.median(THp[wmid, :][THp[wmid, :] > 0]) if (THp[wmid, :] > 0).any() else 0
    wallA = np.median(THp[int((2.5 - mp["v0"]) / mp["dv"]), :]); wallB = np.median(THp[int((W - 2.5 - mp["v0"]) / mp["dv"]), :])
    print(f"   plan: web thickness (median at w={W/2:.1f}) {web_t:.2f}; wall heights: -w wall {wallA:.2f}, +w wall {wallB:.2f}")
    # web position: rows of side map where TH ~ W
    rowmed = np.median(TH, axis=1)
    web_rows = np.where(rowmed > W - 1.5)[0]
    wall_rows = np.where((rowmed > 8) & (rowmed < 11))[0]
    if len(wall_rows) == 0:
        print("   no wall rows; row medians:", np.round(rowmed[::8], 1)); continue
    if len(web_rows):
        print(f"   side: web rows v {v0 + web_rows.min()*dv:.2f}..{v0 + (web_rows.max()+1)*dv:.2f}; wall-only rows v {v0 + wall_rows.min()*dv:.2f}..{v0 + (wall_rows.max()+1)*dv:.2f}")
    A_pres = (FI < 2.5) & (TH > 3.5)                    # -w wall present at this (u, v)
    B_pres = ((TH - np.where(A_pres, 5.0, 0.0)) > 3.5) | ((FI > W - 7.5) & (TH > 3.5))
    rows = wall_rows
    r0, r1 = rows.min(), rows.max() + 1
    cols = np.where(TH.max(axis=0) > 0)[0]; c0, c1 = cols.min(), cols.max() + 1
    out = {}
    for nm, pres in (("wall(-w)", A_pres), ("wall(+w)", B_pres)):
        env = np.zeros_like(pres); env[r0:r1, c0 + 4:c1 - 4] = True     # skip the last 2 mm at the ends
        voids = comps(env & ~pres, du, dv, u0, v0)
        out[nm] = voids
        print(f"   {nm}: {len(voids)} voids")
        for d in voids:
            print(f"      u {d['u'][0]:8.2f}-{d['u'][1]:8.2f} v {d['v'][0]:6.2f}-{d['v'][1]:6.2f}  w={d['w']:6.2f} h={d['h']:5.2f} A={d['area']:6.1f} "
                  f"{'ROUND d=%.2f' % ((d['w']+d['h'])/2) if d['round'] else ''} seat={d.get('seat_circle')}")
    # web slots from the plan map: middle columns thickness 0 within web span
    band = THp[int((7.5 - mp["v0"]) / mp["dv"]):int((W - 7.5 - mp["v0"]) / mp["dv"]), :]
    envp = np.zeros_like(THp, bool); envp[int((5.0 - mp["v0"]) / mp["dv"]):int((W - 5.0 - mp["v0"]) / mp["dv"]), c0 + 4:c1 - 4] = True
    sl = comps(envp & (THp < 0.5), mp["du"], mp["dv"], mp["u0"], mp["v0"])
    out["web_slots"] = sl
    print(f"   web slots/openings: {len(sl)}")
    for d in sl:
        print(f"      u {d['u'][0]:8.2f}-{d['u'][1]:8.2f} w {d['v'][0]:6.2f}-{d['v'][1]:6.2f}  len={d['w']:6.2f} width={d['h']:5.2f} A={d['area']:7.1f}")
    res[rail] = dict(dims=dims, web_t=float(web_t), features=out, frame=dict(centre=ms["centre"], R=ms["R"], lo=ms["lo_local_mm"]))
json.dump(res, open("rail_features.json", "w"), indent=1)
