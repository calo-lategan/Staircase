"""Workbench close-up renders of a joint (random object colours, ortho). Args: out_prefix config cx cy cz size [hide_names,...]"""
import bpy, sys, types, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
pre, cfg = a[0], a[1]; C = Vector((float(a[2]), float(a[3]), float(a[4]))); size = float(a[5])
hide = set(a[6].split(",")) if len(a) > 6 and a[6] else set()
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline":
                tr.mute = True
m.goto_config(ctx, cfg)
sc = ctx.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.get("unit") != "A" or o.name in hide):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'RANDOM'; sh.show_cavity = True; sh.show_object_outline = True
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
sc.render.film_transparent = False
cam_d = bpy.data.cameras.new("AuditCam"); cam_d.type = 'ORTHO'; cam_d.ortho_scale = size
cam = bpy.data.objects.new("AuditCam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.clip_start, cam_d.clip_end = 0.001, 50
views = {"from_out": Vector((0, -1, 0)), "from_top": Vector((0, 0, 1)), "iso": Vector((-0.6, -1, 0.7)), "from_back": Vector((-1, 0, 0)), "from_in": Vector((0, 1, 0.0001))}
for nm, d in views.items():
    d = d.normalized()
    cam.location = C + d * 3.0
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < 0.99 else 'X').to_euler()
    sc.render.filepath = f"{pre}_{nm}.png"
    bpy.ops.render.render(write_still=True)
print("RENDERED")
