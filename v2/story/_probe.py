import bpy, sys, types, json, collections
from mathutils import Vector
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context; sc = ctx.scene
out = {}
roles = collections.Counter((o.get("unit"), o.get("hr_variant"), o.get("side"), o.get("role")) for o in bpy.data.objects if o.get("hr_variant"))
out["hr_roles"] = [list(map(str,k))+[v] for k,v in sorted(roles.items(), key=lambda kv: str(kv[0]))]
out["nonhr_roles"] = collections.Counter(str(o.get("role")) for o in bpy.data.objects if o.get("unit") and not o.get("hr_variant")).most_common()
m.goto_config(ctx, "WIDE_STANDARD")
dg = ctx.evaluated_depsgraph_get()
def bb(o):
    e = o.evaluated_get(dg)
    pts = [e.matrix_world @ Vector(c) for c in e.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    return [round(x,3) for x in lo+hi]
vis = [o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and o.get("unit")]
out["n_vis"] = len(vis)
out["poles_A"] = [(o.name, o.get("role"), o.get("side"), bb(o)) for o in vis if o.get("hr_variant") and o.get("unit")=="A"][:40]
names = collections.Counter(o.name.split("_")[0] for o in vis)
out["prefixes"] = names.most_common(20)
allb = [bb(o) for o in vis]
out["scene_bb"] = [min(b[i] for b in allb) for i in range(3)] + [max(b[i+3] for b in allb) for i in range(3)]
for u in "AB":
    a = m.arm(u); out["arm_"+u] = [round(x,3) for x in a.location]
out["bones_A"] = [b.name for b in m.arm("A").data.bones][:80]
json.dump(out, open(r"C:\Users\USER\Desktop\Staircases\idea one\v2\story\_probe.json","w"), indent=1)
