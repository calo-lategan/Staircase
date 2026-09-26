import bpy, sys, types
from mathutils import Vector
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
out = []
for key in ("SINGLE_CATWALK", "SINGLE_STANDARD", "SINGLE_STEEP"):
    m.goto_config(ctx, key)
    dg = ctx.evaluated_depsgraph_get()
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3); lo_s = None
    tread_top = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.get("unit") != "A" or o.hide_render: continue
        e = o.evaluated_get(dg); me = e.to_mesh()
        mw = e.matrix_world
        ws = [mw @ v.co for v in me.vertices]
        e.to_mesh_clear()
        if not ws: continue
        for w in ws:
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        if o.parent_type == 'BONE' or True:
            b = o.parent_bone if o.parent_type == 'BONE' else next((c.subtarget for c in o.constraints if c.type=='CHILD_OF'), "")
            if b.startswith("Tread") and len(ws) > 30:
                tread_top[b] = max(tread_top.get(b, -1e9), max(w.z for w in ws))
        if o.get("role") is None and min(w.z for w in ws) < (lo_s[0] if lo_s else 1e9):
            lo_s = (min(w.z for w in ws), o.name)
    out.append(f"{key}: lo={[round(x,4) for x in lo]} hi={[round(x,4) for x in hi]} lowest_struct={lo_s} tread_tops={ {k: round(v,4) for k,v in sorted(tread_top.items())} }")
for n in ("StaticBar_Stage", "StaticBar_Tube"):
    o = bpy.data.objects[n]; ws = [o.matrix_world @ v.co for v in o.data.vertices]
    out.append(f"{n}: lo={[round(min(w[i] for w in ws),4) for i in range(3)]} hi={[round(max(w[i] for w in ws),4) for i in range(3)]}")
open("_probe6.txt","w").write("\n".join(out))
