"""EEVEE stills of the final IFC model for the datasheet (IFC colours), and close-ups."""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
try:
    sc.eevee.taa_render_samples = 16
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
w = bpy.data.worlds.new("W") if not sc.world else sc.world
sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get("Background"); bg.inputs[0].default_value = (0.55, 0.6, 0.66, 1); bg.inputs[1].default_value = 0.55
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 4.5; so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (0.8, 0.2, -0.9)
try:
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    try: sc.view_settings.view_transform = 'Filmic'; sc.view_settings.look = 'Medium High Contrast'
    except Exception: pass
for o in bpy.data.objects:
    if o.name.endswith("_none") and o.type == 'MESH': o.hide_render = True        # zero-thickness leftover planes
for m in bpy.data.materials:
    if m.name.startswith("IFC_"):
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        if b: b.inputs["Base Color"].default_value = m.diffuse_color; b.inputs["Base Color"].default_value = tuple(c ** 1.6 for c in m.diffuse_color[:3]) + (1,); b.inputs["Roughness"].default_value = 0.5; b.inputs["Metallic"].default_value = 0.1
cam_d = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, target, direction, dist, lens=50, ortho=None):
    t = Vector(target); d = Vector(direction).normalized()
    cam.location = t + d * dist; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    if ortho: cam_d.type = 'ORTHO'; cam_d.ortho_scale = ortho
    else: cam_d.type = 'PERSP'; cam_d.lens = lens
    cam_d.clip_start = 0.005; cam_d.clip_end = 100
    sc.render.filepath = os.path.join(out, name); bpy.ops.render.render(write_still=True)
shot("final_hero.jpg", (9.02, -17.72, 0.85), (1.0, -1.35, 0.75), 4.6, 40)
shot("final_side.jpg", (9.02, -17.72, 0.95), (0, -1, 0.0001), 10, ortho=2.6)
shot("final_tread_end.jpg", (9.62, -18.25, 0.02), (0.9, -1.0, 0.9), 0.75, 45)
shot("final_tread_under.jpg", (9.62, -17.72, 0.02), (0.45, -0.35, -1.0), 1.1, 45)
shot("final_lock.jpg", (9.40, -18.33, 0.18), (0.8, -1.0, 0.45), 0.8, 45)
shot("final_base.jpg", (9.75, -18.33, -0.06), (0.6, -1.0, 0.45), 0.9, 45)
shot("final_top.jpg", (8.13, -18.33, 0.96), (-0.7, -1.0, 0.5), 0.8, 45)
shot("final_pole_top.jpg", (9.40, -18.33, 1.26), (0.8, -1.0, 0.35), 0.6, 45)
print("RENDERS done")
