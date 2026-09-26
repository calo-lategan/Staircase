"""Orthographic atlas of part families: each representative rendered alone along its 3 principal axes (object-local
bbox frame), with scale bar data. blender -b ... --python atlas.py -- families.json out_dir"""
import bpy, sys, json, os, math
from mathutils import Vector, Matrix
fam_p, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
F = json.load(open(fam_p))
os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.78, 0.82)
sh.show_cavity = True; sh.show_object_outline = True; sh.show_xray = False
sc.render.resolution_x, sc.render.resolution_y = 900, 600
for o in bpy.data.objects:
    o.hide_render = True
cam_d = bpy.data.cameras.new("AtlasCam"); cam_d.type = 'ORTHO'
cam = bpy.data.objects.new("AtlasCam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
meta = []
for k, f in enumerate(F):
    n = f["members"][0]["name"]; o = bpy.data.objects.get(n)
    if o is None or o.type != 'MESH': continue
    me = o.data
    vs = [v.co for v in me.vertices]
    if not vs: continue
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    # render in object-local frame: place a temp copy at origin with identity rotation
    tmp = bpy.data.objects.new("ATLAS_TMP", me); sc.collection.objects.link(tmp)
    tmp.matrix_world = Matrix.Identity(4); tmp.hide_render = False
    c = (lo + hi) / 2; d = hi - lo
    for nm, ax in (("X", Vector((1, 0, 0))), ("Y", Vector((0, -1, 0))), ("Z", Vector((0, 0, 1)))):
        cam.location = c + ax * (max(d) * 2 + 1)
        up = Vector((0, 0, 1)) if nm != "Z" else Vector((0, 1, 0))
        cam.rotation_euler = (-ax).to_track_quat('-Z', 'Y').to_euler() if nm != "Z" else (0, 0, 0)
        other = [i for i in range(3) if abs(ax[i]) < 0.5]
        w, h = d[other[0]], d[other[1]]
        cam_d.ortho_scale = max(w * 1.5, h * 1.5 * 900 / 600, 0.002) * 1.08
        cam_d.clip_start, cam_d.clip_end = 0.0001, max(d) * 5 + 3
        fn = os.path.join(out_dir, f"fam{k:02d}_{n}_{nm}.png"); sc.render.filepath = fn
        bpy.ops.render.render(write_still=True)
    meta.append(dict(k=k, rep=n, count=len(f["members"]), dims_local_mm=[round(x * 1000, 2) for x in d], ortho_scale_m=cam_d.ortho_scale))
    bpy.data.objects.remove(tmp)
json.dump(meta, open(os.path.join(out_dir, "atlas.json"), "w"), indent=1)
print("ATLAS", len(meta))
