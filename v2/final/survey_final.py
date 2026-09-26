"""Survey of every part of the final IFC model (read-only on FINAL_standard.blend): PCA frame (u long, w, v), dims in
that frame, sections normal to u at 13 stations (segments in the part frame, mm), closedness, volume, colour, and
contacts (touching <= 0.5 mm or interpenetrating). blender -b FINAL_standard.blend --python survey_final.py -- out_dir"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
out_dir = sys.argv[sys.argv.index("--") + 1]
STATIONS = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
parts, bms, frames = {}, {}, {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-7)
    bms[o.name] = bm
    P = np.array([v.co[:] for v in bm.verts]); c = P.mean(0)
    w_, V_ = np.linalg.eigh(np.cov((P - c).T)) if len(P) > 3 else (np.ones(3), np.eye(3))
    order = np.argsort(w_)[::-1]; U, W2, V3 = V_[:, order[0]], V_[:, order[1]], V_[:, order[2]]
    L = (P - c) @ np.array([U, W2, V3]).T; lo, hi = L.min(0), L.max(0)
    d = (hi - lo) * 1000
    cuts = {}
    for st in STATIONS:
        b2 = bm.copy()
        co = Vector(c + U * (lo[0] + st * (hi[0] - lo[0]))); no = Vector(U)
        r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=co, plane_no=no)
        segs = []
        for g in r["geom_cut"]:
            if isinstance(g, bmesh.types.BMEdge):
                segs.append([[float((np.array(v.co[:]) - c) @ W2 * 1000), float((np.array(v.co[:]) - c) @ V3 * 1000)] for v in g.verts])
        cuts[str(st)] = segs; b2.free()
    closed = all(e.is_manifold for e in bm.edges)
    parts[o.name] = dict(material=o.get("material", ""), dims_frame_mm=[round(x, 2) for x in d], centre=(c * 1000).tolist(),
                         U=U.tolist(), W=W2.tolist(), V=V3.tolist(), lo_w=float(lo[1] * 1000), lo_v=float(lo[2] * 1000),
                         bb_lo=(P.min(0) * 1000).tolist(), bb_hi=(P.max(0) * 1000).tolist(), closed=closed,
                         volume_mm3=round(bm.calc_volume(signed=True) * 1e9, 1), nv=len(bm.verts), nf=len(bm.faces), cuts=cuts)
names = list(bms); trees = {n: BVHTree.FromBMesh(bms[n]) for n in names}
contacts = []
for i, a in enumerate(names):
    A = parts[a]
    for b in names[i + 1:]:
        B = parts[b]
        if any(A["bb_hi"][k] < B["bb_lo"][k] - 1.0 or B["bb_hi"][k] < A["bb_lo"][k] - 1.0 for k in range(3)): continue
        ov = trees[a].overlap(trees[b]); near = 0.0
        if not ov:
            dmin = 1e9
            vs = list(bms[a].verts)
            for v in vs[::max(1, len(vs) // 600)]:
                loc, nrm, idx, dd = trees[b].find_nearest(v.co)
                if dd is not None and dd < dmin: dmin = dd
            vs = list(bms[b].verts)
            for v in vs[::max(1, len(vs) // 600)]:
                loc, nrm, idx, dd = trees[a].find_nearest(v.co)
                if dd is not None and dd < dmin: dmin = dd
            near = dmin
            if dmin > 0.0005: continue
        contacts.append(dict(a=a, b=b, intersect=bool(ov), n_overlap=len(ov), gap_mm=round(near * 1000, 3),
                             zone_lo=[max(A["bb_lo"][k], B["bb_lo"][k]) for k in range(3)], zone_hi=[min(A["bb_hi"][k], B["bb_hi"][k]) for k in range(3)]))
json.dump(parts, open(os.path.join(out_dir, "parts_final.json"), "w"))
json.dump(contacts, open(os.path.join(out_dir, "contacts_final.json"), "w"), indent=1)
print("SURVEY", len(parts), "parts", len(contacts), "contacts")
