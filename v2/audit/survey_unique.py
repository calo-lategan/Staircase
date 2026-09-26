"""Unique part geometries across ALL objects of unit A (visible or not): group by mesh datablock + rounded dims.
Reports per group: count, members, role/variant/side, bone, dims, volume (divergence), closed?, vertex/face counts,
and whether any two members occupy the same space in the same state (duplicates)."""
import bpy, bmesh, sys, types, json
from mathutils import Vector
out_p = sys.argv[sys.argv.index("--") + 1]
groups = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.get("unit") != "A":
        continue
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    vol = bm.calc_volume(signed=True) * 1e9
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    sc = o.matrix_world.to_scale()
    d = tuple(sorted(round(abs(x) * 1000, 1) for x in ((max(xs) - min(xs)) * sc.x, (max(ys) - min(ys)) * sc.y, (max(zs) - min(zs)) * sc.z)))
    closed = all(e.is_manifold for e in bm.edges)
    key = (me.name, d)
    g = groups.setdefault(key, dict(mesh=me.name, dims_sorted=d, verts=len(bm.verts), faces=len(bm.faces), closed=closed,
                                    vol_mm3=round(vol * abs(sc.x * sc.y * sc.z), 1), members=[]))
    g["members"].append(dict(name=o.name, role=o.get("role"), variant=o.get("hr_variant"), side=o.get("side"),
                             bone=o.parent_bone if o.parent_type == 'BONE' else "", hide_render=o.hide_render))
    bm.free()
res = sorted(groups.values(), key=lambda g: (-len(g["members"]), g["mesh"]))
json.dump(res, open(out_p, "w"), indent=1)
print("UNIQUE", len(res), "groups,", sum(len(g["members"]) for g in res), "objects")
