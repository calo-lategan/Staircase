import bpy, sys, types
from mathutils import Vector
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
out = []
for key in ("SINGLE_BAR", "DOUBLE_STANDARD", "WIDE_STANDARD"):
    m.goto_config(ctx, key)
    dg = ctx.evaluated_depsgraph_get()
    def bb(o):
        e = o.evaluated_get(dg)
        pts = [e.matrix_world @ Vector(c) for c in e.bound_box]
        return [round(min(p[i] for p in pts),3) for i in range(3)] + [round(max(p[i] for p in pts),3) for i in range(3)]
    out.append("== " + key)
    for n in ("MainRig_006", "MainRig_010", "UnitB_006", "UnitB_010", "MainRig_037", "UnitB_179"):
        o = bpy.data.objects.get(n)
        out.append(f"{n} {bb(o) if o else None} vis={o and not o.hide_render}")
    for o in bpy.data.objects:
        if o.get("static_bar"):
            out.append(f"BAR {o.name} {o.type} {bb(o)} vis={not o.hide_render} anim={bool(o.animation_data)} parent={o.parent and o.parent.name} loc={tuple(round(v,3) for v in o.location)}")
    hk = [o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and o.get("unit")=="B" and o.name.startswith("UnitB")]
    # parts of B near A's top axle (x 7.86 at catwalk rotated) - list those whose bbox contains A top axle centre
    a = bpy.data.objects["MainRig_010"]; ab = bb(a); c = Vector(((ab[0]+ab[3])/2, ab[4], (ab[2]+ab[5])/2))
    near = [o.name for o in hk if (lambda b: b[0]-0.02 <= c.x <= b[3]+0.02 and b[2]-0.02 <= c.z <= b[5]+0.02 and b[1]-0.05 <= c.y <= b[4]+0.05)(bb(o))]
    out.append("B parts at A top-axle R end: " + ", ".join(near[:20]))
open("_probe3.txt","w").write("\n".join(out))
