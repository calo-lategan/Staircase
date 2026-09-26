"""Robust outline of the tread end plate: ray thickness through the tread frame along y (end region only)."""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
o = bpy.data.objects["E8649_D03"]
bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bm.normal_update()
REF = Vector((9.5088, -18.330, 0.0))
for v in bm.verts: v.co -= REF
T = BVHTree.FromBMesh(bm)
res = {}
for tag, y0, y1 in (("left_end", -0.001, 0.030), ("right_end", 1.206, 1.237)):
    G = np.zeros((int(0.052 / 0.00125), int(0.282 / 0.00125)))
    for j in range(G.shape[0]):
        z = -0.001 + (j + 0.5) * 0.00125
        for i in range(G.shape[1]):
            x = -0.001 + (i + 0.5) * 0.00125
            s = Vector((x, y0, z)); d = Vector((0, 1, 0)); hits = []
            for _ in range(60):
                loc, nrm, idx, dist = T.ray_cast(s, d, y1 - s.y)
                if loc is None: break
                hits.append((loc.y, nrm.y < 0)); s = loc + d * 2e-7
            tot, w, s0 = 0.0, 0, None
            for yy, ent in hits:
                nw = w + (1 if ent else -1)
                if w <= 0 < nw: s0 = yy
                if nw <= 0 < w and s0 is not None: tot += yy - s0
                w = nw
            G[j, i] = tot * 1000
    res[tag] = G.tolist()
json.dump(res, open("endcap_map.json", "w")); print("ENDCAP ok")
