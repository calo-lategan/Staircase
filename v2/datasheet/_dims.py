import bpy, sys, types, json
from mathutils import Vector
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
out = {}
for key, lab, grp, deg, lay in m.CONFIGS:
    m.goto_config(ctx, key)
    dg = ctx.evaluated_depsgraph_get()
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
    n = 0
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.get("unit") or o.hide_render: continue
        e = o.evaluated_get(dg); mw = e.matrix_world
        for v in o.data.vertices:
            w = mw @ v.co
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        n += 1
    out[key] = dict(label=lab, group=grp, deg=deg, layout=lay, parts=n,
                    L=round((hi.x-lo.x)*1000), W=round((hi.y-lo.y)*1000), zmin=round(lo.z,4), zmax=round(hi.z,4))
json.dump(out, open(r"C:\Users\USER\Desktop\Staircases\idea one\v2\datasheet\state_dims.json","w"), indent=1)
