import bpy, sys, types, json, collections
from mathutils import Vector
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
m.goto_config(ctx, "SINGLE_CATWALK")
dg = ctx.evaluated_depsgraph_get()
def bb(o):
    e = o.evaluated_get(dg)
    pts = [e.matrix_world @ Vector(c) for c in e.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi
def bone(o):
    if o.parent_type == 'BONE': return o.parent_bone
    for c in o.constraints:
        if c.type == 'CHILD_OF' and getattr(c, "subtarget", ""): return c.subtarget
    return o.parent.name if o.parent else ""
rows = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.get("unit") != "A" or o.hide_render: continue
    lo, hi = bb(o)
    d = [round((hi[i]-lo[i])*1000) for i in range(3)]
    c = [round((hi[i]+lo[i])/2, 3) for i in range(3)]
    rows.append((bone(o), o.get("role") or "-", o.name, d, c, round(lo[1],3), round(hi[1],3), round(lo[2],3)))
rows.sort()
with open("_probe2.txt","w") as f:
    for r in rows: f.write("%-16s %-9s %-13s dims=%-18s c=%-24s y[%s..%s] zmin=%s\n" % tuple(map(str, r)))
