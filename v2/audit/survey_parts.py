"""Part survey of unit A at the flat catwalk state (every tread level, rails horizontal):
for every mesh: bone, role, vertex/face count, world bbox, closed/manifold, mesh volume (if closed).
Writes parts_catwalk.json. Run headless on RIGGED3.blend (read only)."""
import bpy, bmesh, sys, types, json, os
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
for o in bpy.data.objects:
    ad = o.animation_data
    if ad:
        for tr in ad.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
m.goto_config(ctx, "SINGLE_CATWALK")
dg = ctx.evaluated_depsgraph_get()
def bone_of(o):
    if o.parent_type == 'BONE': return o.parent_bone
    for c in o.constraints:
        if c.type == 'CHILD_OF' and getattr(c, "subtarget", ""): return c.subtarget
    return ""
rows = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.get("unit") != "A": continue
    e = o.evaluated_get(dg)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(e.matrix_world)
    closed = all(ed.is_manifold for ed in bm.edges) and len(bm.edges) > 0
    vol = bm.calc_volume(signed=False) if closed else None
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    rows.append(dict(name=o.name, bone=bone_of(o), role=o.get("role"), variant=o.get("hr_variant"), side=o.get("side"),
                     visible=not o.hide_render, verts=len(bm.verts), faces=len(bm.faces), closed=closed,
                     volume_cm3=round(vol * 1e6, 2) if vol else None,
                     lo=[round(min(xs), 5), round(min(ys), 5), round(min(zs), 5)], hi=[round(max(xs), 5), round(max(ys), 5), round(max(zs), 5)],
                     dims_mm=[round((max(xs) - min(xs)) * 1000, 1), round((max(ys) - min(ys)) * 1000, 1), round((max(zs) - min(zs)) * 1000, 1)],
                     mesh=o.data.name, users=o.data.users))
    bm.free()
json.dump(rows, open(os.path.join(OUT, "parts_catwalk.json"), "w"), indent=1)
print("PARTS", len(rows))
