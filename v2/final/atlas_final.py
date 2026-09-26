"""Aligned orthographic atlas: each family representative is placed in its own PCA frame (u along x, w along y,
v along z) and rendered: END (looking along u = true cross-section), SIDE (along w), TOP (along v)."""
import bpy, sys, json, os
import numpy as np
from mathutils import Vector, Matrix
fam_p, parts_p, out_dir = sys.argv[sys.argv.index("--") + 1:][:3]
F = json.load(open(fam_p)); P = json.load(open(parts_p))
os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.78, 0.80, 0.84)
sh.show_cavity = True; sh.show_object_outline = True
sc.render.resolution_x, sc.render.resolution_y = 900, 600
for o in bpy.data.objects: o.hide_render = True
cam_d = bpy.data.cameras.new("AtlasCam"); cam_d.type = 'ORTHO'
cam = bpy.data.objects.new("AtlasCam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
meta = []
for k, f in enumerate(F):
    n = f["members"][0]; o = bpy.data.objects[n]; p = P[n]
    U, W, V = [np.array(p[a]) for a in ("U", "W", "V")]; c = np.array(p["centre"]) / 1000
    R = np.array([U, W, V])
    M = Matrix(((*R[0], -R[0] @ c), (*R[1], -R[1] @ c), (*R[2], -R[2] @ c), (0, 0, 0, 1)))
    tmp = bpy.data.objects.new("ATLAS_TMP", o.data); sc.collection.objects.link(tmp)
    tmp.matrix_world = M @ o.matrix_world; tmp.hide_render = False
    bpy.context.view_layer.update()
    vs = [tmp.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    cc = (lo + hi) / 2; d = hi - lo
    for nm, ax, up in (("END", Vector((1, 0, 0)), 'Z'), ("SIDE", Vector((0, -1, 0)), 'Z'), ("TOP", Vector((0, 0, 1)), 'Y')):
        cam.location = cc + ax * (max(d) * 2 + 1)
        cam.rotation_euler = (-ax).to_track_quat('-Z', 'Y' if up == 'Y' else 'Z').to_euler() if nm != "TOP" else (0, 0, 0)
        if nm == "END":
            cam.rotation_euler = (1.5708, 0, 1.5708)
        oth = {"END": (1, 2), "SIDE": (0, 2), "TOP": (0, 1)}[nm]
        cam_d.ortho_scale = max(d[oth[0]] * 1.25, d[oth[1]] * 1.25 * 900 / 600, 0.002)
        cam_d.clip_start, cam_d.clip_end = 0.0001, max(d) * 5 + 3
        sc.render.filepath = os.path.join(out_dir, f"f{k:03d}_{nm}.png")
        bpy.ops.render.render(write_still=True)
    meta.append(dict(k=k, rep=n, count=len(f["members"]), material=f["material"], dims=[round(x * 1000, 1) for x in d], scale_m=cam_d.ortho_scale))
    bpy.data.objects.remove(tmp)
json.dump(meta, open(os.path.join(out_dir, "atlas.json"), "w"), indent=1)
print("ATLAS", len(meta))
