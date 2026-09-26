"""Datasheet stills (EEVEE, same look as the storyline): 11 configurations from one consistent 3/4 view
+ connection close-ups taken from the storyline camera.
blender -b "STEP LADDER RIGGED3.blend" --factory-startup --python render_datasheet_stills.py -- <out_dir>"""
import bpy, sys, types, os, math
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
out_dir = args[0]
ONLY = set(args[1].split(",")) if len(args) > 1 else None
os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene
ctx = bpy.context
for lc in ctx.view_layer.layer_collection.children:
    if lc.name in ("IfcProject/Undefined", "MainStaircase_Source", "Collection"):
        lc.exclude = True
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
R = sc.render
R.image_settings.file_format = 'PNG'
R.image_settings.color_mode = 'RGB'


def story(on):
    for o in bpy.data.objects:
        ad = o.animation_data
        if ad:
            for tr in ad.nla_tracks:
                if tr.name == "Storyline":
                    tr.mute = not on


# ---- 1. configurations (interactive rig state, consistent camera)
story(False)
cd = bpy.data.cameras.new("DS_Cam"); cd.lens = 50; cd.clip_start = 0.05; cd.clip_end = 300
cd.dof.use_dof = False
cam = bpy.data.objects.new("DS_Cam", cd); sc.collection.objects.link(cam)
sc.camera = cam
R.resolution_x, R.resolution_y, R.resolution_percentage = 1600, 1000, 100
VF = 2 * math.atan((36 * 1000 / 1600) / 2 / cd.lens)
import json
dims = {}
for key, lab, grp, deg, lay in m.CONFIGS:
    m.goto_config(ctx, key)
    dg = ctx.evaluated_depsgraph_get()
    pts = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.get("unit") and not o.hide_render:
            mw = o.evaluated_get(dg).matrix_world
            pts += [mw @ v.co for i, v in enumerate(o.data.vertices) if i % 7 == 0]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    full = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.get("unit") and not o.hide_render:
            mw = o.evaluated_get(dg).matrix_world
            full += [mw @ v.co for v in o.data.vertices]
    flo = Vector((min(p.x for p in full), min(p.y for p in full), min(p.z for p in full)))
    fhi = Vector((max(p.x for p in full), max(p.y for p in full), max(p.z for p in full)))
    dims[key] = dict(label=lab, group=grp, deg=deg, layout=lay,
                     parts=sum(1 for o in bpy.data.objects if o.type == 'MESH' and o.get("unit") and not o.hide_render),
                     L=round((fhi.x - flo.x) * 1000), W=round((fhi.y - flo.y) * 1000), zmin=round(flo.z, 4), zmax=round(fhi.z, 4))
    if ONLY and key not in ONLY:
        continue
    c = (lo + hi) / 2
    r = (hi - lo).length / 2
    cabin = key in m.CABIN_STATES
    az, el = math.radians(-52 if not cabin else -40), math.radians(24 if not cabin else 16)
    d = r / math.sin(VF / 2) * (0.95 if not cabin else 1.9)
    if cabin:
        c = c + Vector((-0.6, 0.0, 0.35))
    cam.location = c + d * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    R.filepath = os.path.join(out_dir, f"{key}.png")
    bpy.ops.render.render(write_still=True)
    print("STILL", key, flush=True)

json.dump(dims, open(os.path.join(os.path.dirname(out_dir), "state_dims.json"), "w"), indent=1)
# ---- 2. connection close-ups from the storyline camera
story(True)
sc.camera = bpy.data.objects["StoryCam"]
R.resolution_x, R.resolution_y = 1600, 900
for name, fr in (("detail_side_join", 1256), ("detail_end_hook", 200), ("detail_pole_insert", 1300),
                 ("detail_bar_cabin", 728), ("detail_fold_rails", 1445), ("detail_lift_out", 858)):
    if ONLY and name not in ONLY:
        continue
    sc.frame_set(fr)
    R.filepath = os.path.join(out_dir, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("STILL", name, flush=True)
print("STILLS_DONE")
