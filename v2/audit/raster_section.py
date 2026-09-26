"""Robust section by ray casting (union of shells, winding by face normals). For each cut plane normal to world axis
`ax` at `pos`, rows are spaced `step` mm along v and rays run along u. Output: filled intervals per row (world mm).
Job JSON: {"config": ..., "unit": "A", "cuts": [{"id", "objects": [...], "ax": "x|y|z", "pos": m, "u": "x|y|z", "v": "x|y|z",
"vmin": m, "vmax": m, "umin": m, "umax": m, "step": mm}]}
blender -b RIGGED3.blend --factory-startup --python raster_section.py -- job.json out.json"""
import bpy, bmesh, sys, types, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
job_p, out_p = sys.argv[sys.argv.index("--") + 1:][:2]
job = json.load(open(job_p))
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline":
                tr.mute = True
m.goto_config(ctx, job["config"])
dg = ctx.evaluated_depsgraph_get()
IX = {"x": 0, "y": 1, "z": 2}
trees = {}
REF = Vector(job.get("ref", (0, 0, 0)))          # meshes are shifted by -REF (float precision near the parts)
from mathutils import Matrix
def tree(n):
    if n not in trees:
        o = bpy.data.objects[n]
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(Matrix.Translation(-REF) @ o.evaluated_get(dg).matrix_world)
        bm.normal_update()
        trees[n] = BVHTree.FromBMesh(bm)
    return trees[n]
out = {}
for c in job["cuts"]:
    a, u, v = IX[c["ax"]], IX[c["u"]], IX[c["v"]]
    step = c["step"] / 1000.0
    rows = []
    vv = c["vmin"] + step / 2
    while vv < c["vmax"]:
        hits = []
        for n in c["objects"]:
            T = tree(n)
            o = Vector((0, 0, 0)); o[a] = c["pos"]; o[v] = vv; o[u] = c["umin"] - 0.01
            o = o - REF
            d = Vector((0, 0, 0)); d[u] = 1.0
            start = o.copy(); guard = 0
            while guard < 400:
                guard += 1
                loc, nrm, idx, dist = T.ray_cast(start, d, (c["umax"] + 0.01 - REF[u]) - start[u])
                if loc is None:
                    break
                hits.append((loc[u] + REF[u], -1 if nrm[u] < 0 else 1, n))     # normal against ray = entering
                start = loc + d * 2e-7
        hits.sort()
        # union winding: per-object winding, inside if any object's winding > 0
        wind = {n: 0 for n in c["objects"]}
        inside, ivs, s0 = False, [], None
        for x, sgn, n in hits:
            wind[n] += 1 if sgn < 0 else -1
            now = any(w > 0 for w in wind.values())
            if now and not inside:
                s0 = x
            elif inside and not now:
                ivs.append((s0 * 1000, x * 1000))
            inside = now
        rows.append((vv * 1000, ivs))
        vv += step
    out[c["id"]] = dict(u=c["u"], v=c["v"], step=c["step"], rows=rows)
json.dump(out, open(out_p, "w"))
print("RASTER", len(out))
