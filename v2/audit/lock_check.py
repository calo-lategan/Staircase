"""Fold-lock check: in each state, slice every rail at its web mid-plane (rail-aligned frame) together with every
visible handrail pole / mini; output the loops in the rail frame (u along rail from its low-x end, w across) so
slot-to-pin clearances can be measured. blender ... -- out.json CONFIG [CONFIG ...]"""
import bpy, bmesh, sys, types, json
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
out_p, cfgs = a[0], a[1:]
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
RAILS = {"MainRig_037": "bottom", "MainRig_026": "bottom", "MainRig_179": "top", "MainRig_118": "top"}
res = {}
for cfg in cfgs:
    m.goto_config(bpy.context, cfg)
    dg = bpy.context.evaluated_depsgraph_get()
    def wbm(o):
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.evaluated_get(dg).matrix_world); return bm
    pins = [o for o in bpy.data.objects if o.type == 'MESH' and o.get("unit") == "A" and not o.hide_render and o.get("role") in ("mini", "pole", "fitting")]
    res[cfg] = {}
    for rn, webpos in RAILS.items():
        ro = bpy.data.objects[rn]; bm = wbm(ro)
        P = np.array([v.co[:] for v in bm.verts]); c = P.mean(0)
        w_, V_ = np.linalg.eigh(np.cov((P - c).T)); U = V_[:, np.argmax(w_)]
        if U[0] > 0: U = -U                       # u runs from the high-x (axle 006) end? keep: u points to -x
        U = -U                                    # u points to +x (low end -> high end in catwalk)
        W = np.array([0, 1.0, 0]) - U[1] * U; W /= np.linalg.norm(W); V = np.cross(U, W)
        if V[2] < 0: V = -V; W = -W
        L = (P - c) @ np.array([U, W, V]).T
        lo, hi = L.min(0), L.max(0)
        vpos = lo[2] + 0.0025 if webpos == "bottom" else hi[2] - 0.0025
        co = Vector(c + V * vpos); no = Vector(V)
        def cut(bmx):
            b2 = bmx.copy()
            r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=co, plane_no=no)
            segs = []
            for g in r["geom_cut"]:
                if isinstance(g, bmesh.types.BMEdge):
                    pts = []
                    for v in g.verts:
                        d = np.array(v.co[:]) - c
                        pts.append([float((d @ U - lo[0]) * 1000), float((d @ W - lo[1]) * 1000)])
                    segs.append(pts)
            b2.free(); return segs
        entry = dict(rail=cut(bm), frame=dict(U=U.tolist(), W=W.tolist(), V=V.tolist(), c=c.tolist(), lo=lo.tolist(), hi=hi.tolist()), pins={})
        for po in pins:
            pb = wbm(po)
            d = [(Vector(v.co) - co).dot(no) for v in pb.verts]
            if min(d) < 0 < max(d):
                s = cut(pb)
                if s: entry["pins"][po.name] = dict(segs=s, role=po.get("role"), variant=po.get("hr_variant"), side=po.get("side"))
            pb.free()
        res[cfg][rn] = entry
        bm.free()
json.dump(res, open(out_p, "w"))
print("LOCK", {k: {r: len(v["pins"]) for r, v in d.items()} for k, d in res.items()})
