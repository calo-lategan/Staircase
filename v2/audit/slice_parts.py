"""Cross-section slicer: for each named object, bisect the (world-space, catwalk state) mesh with planes normal to
a chosen axis at chosen stations; export every cut segment. Usage:
blender -b RIGGED3.blend --factory-startup --python slice_parts.py -- <out.json> <config> <name:axis:s1,s2,...> ..."""
import bpy, bmesh, sys, types, json
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
out_path, config, specs = args[0], args[1], args[2:]
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
for o in bpy.data.objects:
    ad = o.animation_data
    if ad:
        for tr in ad.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
m.goto_config(ctx, config)
dg = ctx.evaluated_depsgraph_get()
AX = {"x": Vector((1, 0, 0)), "y": Vector((0, 1, 0)), "z": Vector((0, 0, 1))}
res = {}
for spec in specs:
    name, axis, stations = spec.split(":")
    o = bpy.data.objects[name]; e = o.evaluated_get(dg)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(e.matrix_world)
    lo = min(getattr(v.co, axis) for v in bm.verts); hi = max(getattr(v.co, axis) for v in bm.verts)
    key = f"{name}:{axis}"
    res[key] = {"axis": axis, "range": [lo, hi], "cuts": {}}
    for st in stations.split(","):
        frac = float(st)
        pos = lo + frac * (hi - lo)
        b2 = bm.copy()
        co = Vector((0, 0, 0)); setattr(co, axis, pos)
        r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=co, plane_no=AX[axis])
        segs = [[list(v.co) for v in g.verts] for g in r["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]
        res[key]["cuts"][st] = {"pos": pos, "segs": segs}
        b2.free()
    bm.free()
json.dump(res, open(out_path, "w"))
print("SLICED", len(res))
