import bpy, sys, types
from mathutils import Vector
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
for o in bpy.data.objects:
    ad = o.animation_data
    if ad:
        for tr in ad.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
m.goto_config(ctx, "DOUBLE_CATWALK")
dg = ctx.evaluated_depsgraph_get()
rows = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.get("unit") and not o.hide_render:
        mw = o.evaluated_get(dg).matrix_world
        xs = [(mw @ v.co).x for v in o.data.vertices]
        rows.append((min(xs), max(xs), o.name, o.get("hr_variant"), o.get("role"), o.get("unit"), o.get("side")))
rows.sort()
for r in rows[:6] + rows[-6:]: print("ROW", [round(r[0],3), round(r[1],3)] + list(r[2:]))
import collections
print("VIS", collections.Counter((r[5], r[3], r[6]) for r in rows))
print("A", tuple(round(v,3) for v in m.arm("A").location), "B", tuple(round(v,3) for v in m.arm("B").location), m.current_angle("A"), m.current_angle("B"))
print("lifts", [(e.name, tuple(round(v,3) for v in e.location)) for e in bpy.data.objects if e.name.startswith("HR_Lift")])
