import bpy, bmesh, sys, types
from mathutils import Vector
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
m.goto_config(ctx, "SINGLE_CATWALK")
dg = ctx.evaluated_depsgraph_get()
out = []
for n in ("MainRig_026", "MainRig_037", "MainRig_118", "MainRig_179", "MainRig_006", "MainRig_010"):
    o = bpy.data.objects[n]; e = o.evaluated_get(dg)
    bm = bmesh.new(); bm.from_mesh(e.to_mesh()); e.to_mesh_clear()
    bm.transform(e.matrix_world)
    xs = [v.co.x for v in bm.verts]
    out.append(f"== {n} verts={len(bm.verts)} x[{min(xs):.4f},{max(xs):.4f}] y[{min(v.co.y for v in bm.verts):.4f},{max(v.co.y for v in bm.verts):.4f}] z[{min(v.co.z for v in bm.verts):.4f},{max(v.co.z for v in bm.verts):.4f}]")
    for xc in (8.30, 8.80, 9.40):
        b2 = bm.copy()
        r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=(xc, 0, 0), plane_no=(1, 0, 0))
        pts = sorted({(round(g.co.y * 1000, 1), round(g.co.z * 1000, 1)) for g in r["geom_cut"] if isinstance(g, bmesh.types.BMVert)})
        ys = sorted({p[0] for p in pts}); zs = sorted({p[1] for p in pts})
        out.append(f"  x={xc}: y-levels(mm) {ys[:14]}  z-levels(mm) {zs[:14]}")
        b2.free()
    bm.free()
open("_rails.txt", "w").write("\n".join(out))
