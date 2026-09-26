import bpy, bmesh, sys, types, json
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
m.goto_config(ctx, "SINGLE_CATWALK")
dg = ctx.evaluated_depsgraph_get()
res = {}
for n in ("MainRig_026", "MainRig_037", "MainRig_118", "MainRig_179"):
    o = bpy.data.objects[n]; e = o.evaluated_get(dg)
    bm = bmesh.new(); bm.from_mesh(e.to_mesh()); e.to_mesh_clear(); bm.transform(e.matrix_world)
    res[n] = {}
    for xc in (8.52, 8.80, 9.10):
        b2 = bm.copy()
        r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=(xc, 0, 0), plane_no=(1, 0, 0))
        segs = [[(v.co.y, v.co.z) for v in g.verts] for g in r["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]
        res[n][str(xc)] = segs
        b2.free()
    bm.free()
json.dump(res, open("_rails2.json", "w"))
