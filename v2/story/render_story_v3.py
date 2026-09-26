"""Render the v3 storyline (EEVEE) - frames to PNG.
blender -b "STEP LADDER RIGGED3.blend" --factory-startup --python render_story_v3.py -- <out_dir> <frames>
<frames>: "a-b" (range), "a-b:s" (step) or "f1,f2,..." ; optional 3rd arg: resolution percentage
"""
import bpy, sys, os, time
argv = sys.argv[sys.argv.index("--") + 1:]
out_dir, spec = argv[0], argv[1]
pct = int(argv[2]) if len(argv) > 2 else 100
sc = bpy.context.scene
vl = bpy.context.view_layer
for lc in vl.layer_collection.children:              # the IFC import + source copy are not in shot
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
R.resolution_percentage = pct
R.image_settings.file_format = 'PNG'
R.image_settings.color_mode = 'RGB'
R.image_settings.compression = 15
R.use_persistent_data = True
if "-" in spec and "," not in spec:
    rng, _, step = spec.partition(":")
    a, b = map(int, rng.split("-"))
    frames = list(range(a, b + 1, int(step or 1)))
else:
    frames = [int(x) for x in spec.split(",")]
os.makedirs(out_dir, exist_ok=True)
t0 = time.time()
for i, fr in enumerate(frames):
    p = os.path.join(out_dir, f"{fr:04d}.png")
    if os.path.exists(p) and os.path.getsize(p) > 0:
        continue
    sc.frame_set(fr)
    R.filepath = p
    bpy.ops.render.render(write_still=True)
    if i % 25 == 0:
        print(f"RENDERED {fr} ({i + 1}/{len(frames)}) {time.time() - t0:.1f}s", flush=True)
print("RENDER_DONE", len(frames), f"{time.time() - t0:.1f}s")
