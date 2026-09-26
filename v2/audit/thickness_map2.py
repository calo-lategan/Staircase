"""Thickness maps in a part-aligned frame. For each map: frame 'auto' = PCA of the object's vertices (u = long axis,
w = across (closest to world Y), v = u x w (up)); view 'side' rays along w, grid (u,v); view 'plan' rays along v,
grid (u,w); view 'end' rays along u, grid (w,v). Grid ranges in mm relative to the object's bbox in that frame.
Job: {"config", "maps": [{"id", "object", "view", "du", "dv"}]}.  Writes npz + json meta (frame, origin, extents)."""
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
arrays, meta = {}, {}
cache = {}
for mp in job["maps"]:
    n = mp["object"]
    if n not in cache:
        o = bpy.data.objects[n]
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.evaluated_get(dg).matrix_world)
        P = np.array([v.co[:] for v in bm.verts]); c = P.mean(axis=0)
        w_, V_ = np.linalg.eigh(np.cov((P - c).T))
        U = V_[:, np.argmax(w_)]
        if U[0] < 0 and abs(U[0]) > 0.5: U = -U
        if abs(U[2]) > 0.9 and U[2] < 0: U = -U
        ref = np.array([0, 1.0, 0]) if abs(U[1]) < 0.9 else np.array([1.0, 0, 0])
        W = ref - ref.dot(U) * U; W /= np.linalg.norm(W)
        Vv = np.cross(U, W)
        if Vv[2] < 0 and abs(Vv[2]) > 0.3: W = -W; Vv = -Vv
        if mp.get("frame"):                          # explicit frame override (u, w) in world
            U = np.array(mp["frame"]["u"], float); U /= np.linalg.norm(U)
            W = np.array(mp["frame"]["w"], float); W -= W.dot(U) * U; W /= np.linalg.norm(W); Vv = np.cross(U, W)
        R = np.array([U, W, Vv])                    # rows: local axes
        L = (P - c) @ R.T                           # local coords (m)
        lo, hi = L.min(axis=0), L.max(axis=0)
        M = Matrix([list(R[0]) + [-(R[0] @ c)], list(R[1]) + [-(R[1] @ c)], list(R[2]) + [-(R[2] @ c)], [0, 0, 0, 1]])
        bm2 = bmesh.new(); bm2.from_mesh(o.data); bm2.transform(M @ o.evaluated_get(dg).matrix_world); bm2.normal_update()
        cache[n] = (BVHTree.FromBMesh(bm2), lo, hi, c, R)
    T, lo, hi, c, R = cache[n]
    view = mp["view"]
    ax, u, v = {"side": (1, 0, 2), "plan": (2, 0, 1), "end": (0, 1, 2)}[view]
    du, dv = mp["du"] / 1000, mp["dv"] / 1000
    u0, u1, v0, v1 = lo[u] - 0.001, hi[u] + 0.001, lo[v] - 0.001, hi[v] + 0.001
    if "urange" in mp: u0, u1 = lo[u] + mp["urange"][0] / 1000, lo[u] + mp["urange"][1] / 1000
    nu, nv = int(round((u1 - u0) / du)), int(round((v1 - v0) / dv))
    TH = np.zeros((nv, nu), np.float32); FIRST = np.full((nv, nu), np.nan, np.float32)
    for j in range(nv):
        vv = v0 + (j + 0.5) * dv
        for i in range(nu):
            uu = u0 + (i + 0.5) * du
            s = Vector((0, 0, 0)); s[ax] = lo[ax] - 0.005; s[u] = uu; s[v] = vv
            d = Vector((0, 0, 0)); d[ax] = 1.0
            hits, g = [], 0
            while g < 200:
                g += 1
                loc, nrm, idx, dist = T.ray_cast(s, d, hi[ax] + 0.005 - s[ax])
                if loc is None: break
                hits.append((loc[ax], nrm[ax] < 0)); s = loc + d * 2e-7
            wnd, s0, tot, first = 0, None, 0.0, None
            for x, ent in hits:
                nw = wnd + (1 if ent else -1)
                if wnd <= 0 < nw: s0 = x
                if nw <= 0 < wnd and s0 is not None:
                    tot += x - s0
                    if first is None: first = s0
                wnd = nw
            TH[j, i] = tot * 1000
            if first is not None: FIRST[j, i] = (first - lo[ax]) * 1000
    key = mp["id"]
    arrays[key + "__TH"] = TH; arrays[key + "__FIRST"] = FIRST
    meta[key] = dict(object=n, view=view, du=mp["du"], dv=mp["dv"], u0=(u0 - lo[u]) * 1000, v0=(v0 - lo[v]) * 1000,
                     axes="uwv"[u] + "uwv"[v], ray="uwv"[ax], dims_mm=[(hi[k] - lo[k]) * 1000 for k in range(3)],
                     centre=list(c), R=R.tolist(), lo_local_mm=[x * 1000 for x in lo])
np.savez_compressed(out_p, **arrays)
json.dump(meta, open(out_p.replace(".npz", ".json"), "w"), indent=1)
print("TMAPS2", len(meta))
