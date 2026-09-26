"""Full part survey (read-only on RIGGED3.blend): for every visible part of unit A in a given state,
slice along its longest axis at 11 stations and across its two other axes at mid-length, export the cut
segments; also find every pair of parts that touch or interpenetrate (connections).
blender -b RIGGED3.blend --factory-startup --python survey_sections.py -- <out_dir> <CONFIG>"""
import bpy, bmesh, sys, types, json, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
args = sys.argv[sys.argv.index("--") + 1:]
out_dir, config = args[0], args[1]
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
for o in bpy.data.objects:
    ad = o.animation_data
    if ad:
        for tr in ad.nla_tracks:
            if tr.name == "Storyline":
                tr.mute = True
m.goto_config(ctx, config)
dg = ctx.evaluated_depsgraph_get()
AX = {"x": Vector((1, 0, 0)), "y": Vector((0, 1, 0)), "z": Vector((0, 0, 1))}
STATIONS = [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]


def bone_of(o):
    if o.parent_type == 'BONE':
        return o.parent_bone
    for c in o.constraints:
        if c.type == 'CHILD_OF' and getattr(c, "subtarget", ""):
            return c.subtarget
    return ""


parts, bms = {}, {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.get("unit") != "A" or o.hide_render:
        continue
    e = o.evaluated_get(dg)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(e.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bms[o.name] = bm
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    lo, hi = Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))
    dims = hi - lo
    long_ax = "xyz"[max(range(3), key=lambda i: dims[i])]
    cuts = {}
    for axis in "xyz":
        a_lo, a_hi = getattr(lo, axis), getattr(hi, axis)
        sts = STATIONS if axis == long_ax else [0.5]
        cuts[axis] = {}
        for st in sts:
            b2 = bm.copy()
            co = Vector((0, 0, 0)); setattr(co, axis, a_lo + st * (a_hi - a_lo))
            r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=co, plane_no=AX[axis])
            cuts[axis][str(st)] = {"pos": getattr(co, axis),
                                   "segs": [[list(v.co) for v in g.verts] for g in r["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]}
            b2.free()
    closed = all(ed.is_manifold for ed in bm.edges)
    parts[o.name] = dict(bone=bone_of(o), role=o.get("role"), variant=o.get("hr_variant"), side=o.get("side"),
                         lo=list(lo), hi=list(hi), dims_mm=[round(d * 1000, 2) for d in dims], long_axis=long_ax,
                         closed=closed, volume_mm3=round(bm.calc_volume() * 1e9, 1) if closed else None, cuts=cuts)

# contacts: parts whose surfaces come within 0.5 mm, or interpenetrate
names = list(bms)
trees = {n: BVHTree.FromBMesh(bms[n]) for n in names}
contacts = []
for i, a in enumerate(names):
    A = parts[a]
    for b in names[i + 1:]:
        B = parts[b]
        if any(A["hi"][k] < B["lo"][k] - 0.001 or B["hi"][k] < A["lo"][k] - 0.001 for k in range(3)):
            continue
        ov = trees[a].overlap(trees[b])
        near = None
        if not ov:              # closest distance between vertex sets (sampled) -> touching within 0.5 mm?
            dmin = 1e9
            for v in list(bms[a].verts)[::max(1, len(bms[a].verts) // 400)]:
                loc, nrm, idx, d = trees[b].find_nearest(v.co)
                if d is not None and d < dmin:
                    dmin = d
            near = dmin
            if dmin > 0.0005:
                continue
        lo = [max(A["lo"][k], B["lo"][k]) for k in range(3)]
        hi = [min(A["hi"][k], B["hi"][k]) for k in range(3)]
        contacts.append(dict(a=a, b=b, intersect=bool(ov), faces_overlapping=len(ov), gap_mm=round(near * 1000, 3) if near is not None else 0.0,
                             zone_lo=lo, zone_hi=hi))
json.dump(parts, open(os.path.join(out_dir, f"sections_{config}.json"), "w"))
json.dump(contacts, open(os.path.join(out_dir, f"contacts_{config}.json"), "w"), indent=1)
print("SURVEY", config, len(parts), "parts", len(contacts), "contacts")
