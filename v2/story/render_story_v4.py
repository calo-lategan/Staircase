"""Fast render of the v3 storyline (EEVEE) - JPEG frames, animation render (engine stays warm between frames).
blender -b "STEP LADDER RIGGED3.blend" --factory-startup --python render_story_v4.py -- <out_dir> <frames> [pct] [samples]
<frames>: "a-b" range (resumable: existing frames are skipped) or "f1,f2,..." list of stills
"""
import bpy, sys, os, time
argv = sys.argv[sys.argv.index("--") + 1:]
out_dir, spec = argv[0], argv[1]
res = argv[2] if len(argv) > 2 else "1600x900"
samples = int(argv[3]) if len(argv) > 3 else 16
sc = bpy.context.scene
for lc in bpy.context.view_layer.layer_collection.children:     # IFC import + source copy are never in shot
    if lc.name in ("IfcProject/Undefined", "MainStaircase_Source", "Collection"):
        lc.exclude = True
for o in bpy.data.objects:
    ad = o.animation_data
    if ad:
        for tr in ad.nla_tracks:
            if tr.name == "Storyline":
                tr.mute = False
sc.camera = bpy.data.objects["StoryCam"]
R = sc.render
R.engine = 'BLENDER_EEVEE'
R.resolution_x, R.resolution_y = map(int, res.split("x")); R.resolution_percentage = 100
sc.eevee.taa_render_samples = samples
R.image_settings.file_format = 'JPEG'
R.image_settings.quality = 92
R.use_overwrite = False            # resume: frames already on disk are skipped
R.use_placeholder = False
os.makedirs(out_dir, exist_ok=True)
t0 = time.time()
if "-" in spec and "," not in spec:
    a, b = map(int, spec.split("-"))
    sc.frame_start, sc.frame_end = a, b
    R.filepath = os.path.join(out_dir, "")
    bpy.ops.render.render(animation=True)
    n = b - a + 1
else:
    fr = [int(x) for x in spec.split(",")]
    for f in fr:
        sc.frame_set(f)
        R.filepath = os.path.join(out_dir, f"{f:04d}.jpg")
        bpy.ops.render.render(write_still=True)
    n = len(fr)
print("RENDER_DONE", n, f"{time.time() - t0:.1f}s", f"{(time.time() - t0) / n:.2f}s/frame")
