"""Material thickness maps by ray casting through each object along a view axis (robust to missing side faces / open
holes): for each grid point (u,v) the ray along `ax` gives the list of material intervals (winding by normals) and the
total thickness. Job: {"config", "ref", "maps": [{"id", "objects", "ax", "u", "v", "umin","umax","vmin","vmax" (m), "du","dv" (mm)}]}
blender -b ... --python thickness_map.py -- job.json out.npz"""
import bpy, bmesh, sys, types, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
job_p, out_p = sys.argv[sys.argv.index("--") + 1:][:2]
job = json.load(open(job_p))
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
m.goto_config(bpy.context, job["config"])
dg = bpy.context.evaluated_depsgraph_get()
REF = Vector(job.get("ref", (0, 0, 0)))
IX = {"x": 0, "y": 1, "z": 2}
trees, bbox = {}, {}
def tree(n):
    if n not in trees:
        o = bpy.data.objects[n]
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(Matrix.Translation(-REF) @ o.evaluated_get(dg).matrix_world)
        bm.normal_update()
        trees[n] = BVHTree.FromBMesh(bm)
        bbox[n] = ([min(v.co[k] for v in bm.verts) for k in range(3)], [max(v.co[k] for v in bm.verts) for k in range(3)])
    return trees[n]
arrays = {}
meta = {}
for mp in job["maps"]:
    a, u, v = IX[mp["ax"]], IX[mp["u"]], IX[mp["v"]]
    du, dv = mp["du"] / 1000, mp["dv"] / 1000
    nu = int(round((mp["umax"] - mp["umin"]) / du)); nv = int(round((mp["vmax"] - mp["vmin"]) / dv))
    TH = np.zeros((nv, nu), dtype=np.float32)       # total thickness, mm
    FIRST = np.full((nv, nu), np.nan, dtype=np.float32)   # first material entry along +ax, mm (world)
    for n in mp["objects"]:
        T = tree(n); lo, hi = bbox[n]
        for j in range(nv):
            vv = mp["vmin"] + (j + 0.5) * dv - REF[v]
            if vv < lo[v] - 1e-4 or vv > hi[v] + 1e-4:
                continue
            for i in range(nu):
                uu = mp["umin"] + (i + 0.5) * du - REF[u]
                if uu < lo[u] - 1e-4 or uu > hi[u] + 1e-4:
                    continue
                o = Vector((0, 0, 0)); o[a] = lo[a] - 0.005; o[u] = uu; o[v] = vv
                d = Vector((0, 0, 0)); d[a] = 1.0
                hits, start, g = [], o, 0
                while g < 200:
                    g += 1
                    loc, nrm, idx, dist = T.ray_cast(start, d, hi[a] + 0.005 - start[a])
                    if loc is None: break
                    hits.append((loc[a], nrm[a] < 0))
                    start = loc + d * 2e-7
                w, s0, tot, first = 0, None, 0.0, None
                for x, entering in hits:
                    nw = w + (1 if entering else -1)
                    if w <= 0 < nw: s0 = x
                    if nw <= 0 < w and s0 is not None:
                        tot += x - s0
                        if first is None: first = s0
                    w = nw
                TH[j, i] += tot * 1000
                if first is not None:
                    fv = (first + REF[a]) * 1000
                    FIRST[j, i] = fv if np.isnan(FIRST[j, i]) else min(FIRST[j, i], fv)
    arrays[mp["id"] + "__TH"] = TH; arrays[mp["id"] + "__FIRST"] = FIRST
    meta[mp["id"]] = dict(u=mp["u"], v=mp["v"], ax=mp["ax"], u0=mp["umin"] * 1000, v0=mp["vmin"] * 1000, du=mp["du"], dv=mp["dv"], objects=mp["objects"])
np.savez_compressed(out_p, **arrays)
json.dump(meta, open(out_p.replace(".npz", ".json"), "w"), indent=1)
print("TMAPS", len(meta))
