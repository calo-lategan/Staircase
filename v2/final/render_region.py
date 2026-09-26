"""Workbench close-ups of a region of the final model (random colours). Args: out_prefix cx cy cz size views(comma) [hide_substrings]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
pre = a[0]; C = Vector((float(a[1]), float(a[2]), float(a[3]))); size = float(a[4]); views = a[5].split(",")
hide = a[6].split(",") if len(a) > 6 and a[6] else []
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and any(h and h in o.name for h in hide): o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'RANDOM'; sh.show_cavity = True; sh.show_object_outline = True
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
cam_d = bpy.data.cameras.new("C"); cam_d.type = 'ORTHO'; cam_d.ortho_scale = size; cam_d.clip_start, cam_d.clip_end = 0.001, 60
cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
V = {"from_left": Vector((0, -1, 0)), "from_right": Vector((0, 1, 0)), "from_top": Vector((0, 0, 1)), "from_front": Vector((1, 0, 0)),
     "iso": Vector((1, -1, 0.8)), "iso2": Vector((1, 1, 0.8)), "from_below": Vector((0.3, -0.3, -1))}
for nm in views:
    d = V[nm].normalized(); cam.location = C + d * 4.0
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < 0.95 else 'X').to_euler()
    sc.render.filepath = f"{pre}_{nm}.png"; bpy.ops.render.render(write_still=True)
print("RENDERED")
