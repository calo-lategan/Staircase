"""Pictures for the brief's "25 Sep model check": an overview with every change highlighted plus projected marker
positions (percent of the image) for clickable numbers, and per-change 'where' + close-up renders.
Orange = change or add, red = remove / not in the load path. The blend file is only read, never saved.
blender -b v2/final/FINAL_standard.blend --factory-startup --python render_final_check_refs.py -- <out_dir>"""
import bpy, sys, os, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
OBJ = bpy.data.objects
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
try: sc.eevee.taa_render_samples = 16
except Exception: pass
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get("Background"); bg.inputs[0].default_value = (0.55, 0.6, 0.66, 1); bg.inputs[1].default_value = 0.55
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 4.5; so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (0.8, 0.2, -0.9)
try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
for o in OBJ:
    if o.name.endswith("_none") and o.type == 'MESH': o.hide_render = True
# grey-down the IFC colours so the highlights read clearly
for m in bpy.data.materials:
    if m.name.startswith("IFC_"):
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        if b:
            c = m.diffuse_color[:3]; g = sum(c) / 3
            b.inputs["Base Color"].default_value = tuple((0.55 * g + 0.45 * v) ** 1.6 for v in c) + (1,)
            b.inputs["Roughness"].default_value = 0.55; b.inputs["Metallic"].default_value = 0.1

def mat(name, col, em):
    mt = bpy.data.materials.new(name); mt.use_nodes = True
    bs = mt.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*col, 1); bs.inputs["Roughness"].default_value = 0.45
    bs.inputs["Emission Color"].default_value = (*col, 1); bs.inputs["Emission Strength"].default_value = em
    return mt
HL = mat("HL_change", (1.0, 0.34, 0.04), 0.8)
RM = mat("HL_remove", (0.9, 0.06, 0.06), 0.8)
MS = mat("HL_missing", (1.0, 0.86, 0.08), 1.2)
saved = {}
def paint(names, mt):
    for n in names:
        o = OBJ.get(n)
        if not o or o.type != 'MESH': continue
        if n not in saved:
            if not o.material_slots: o.data.materials.append(None)
            saved[n] = [(s.link, s.material) for s in o.material_slots]
        for s in o.material_slots: s.link = 'OBJECT'; s.material = mt
def unpaint():
    for n, lst in saved.items():
        for s, (lk, mt) in zip(OBJ[n].material_slots, lst): s.link = lk; s.material = mt
    saved.clear()

def dims(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return bb
def cen(n):
    bb = dims(OBJ[n]); return sum(bb, Vector()) / 8
def code(o): return o.name.split("_")[-1]
def sz(o): return sorted(o.dimensions * 1000, reverse=True)
MESH = [o for o in OBJ if o.type == 'MESH' and not o.name.endswith("_none")]
def pick(c, test): return [o.name for o in MESH if code(o) == c and test(sz(o), o)]

DUP = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath), "duplicates_final.json")))
dup_second = [b for a, b in DUP]
treads = pick("D03", lambda d, o: d[0] > 1200) + pick("D03", lambda d, o: 260 < d[0] < 280) + pick("D03", lambda d, o: 1170 < d[0] < 1185)
rails = ["E8505_I02", "E9366_A02", "E11379_J04", "E9226_I02"]
pin_hw = [o.name for o in MESH if code(o) in ("1008948", "1069272", "F07", "I03")]
lockpins = pick("F04", lambda d, o: 160 < d[0] < 250)
poles = pick("F04", lambda d, o: d[0] > 1000)
axle_base = [n for n in ["E5232_E08", "E6998_E08"] if n in OBJ]; axle_top = [n for n in ["E7258_E08", "E7326_E08"] if n in OBJ]; axle_2nd = [n for n in ["E2559_E08", "E5326_E08"] if n in OBJ]
hooks = ["E11170_L07", "E8541_L07", "E11386_L07", "E8522_L07", "E2485_L07", "E153_L07"]
jack_parts = [o.name for o in MESH if code(o) == "E08" and 9.55 < cen(o.name).x < 9.72 and cen(o.name).z < -0.01 and sz(o)[0] < 200]
jack_2nd = [o.name for o in MESH if code(o) == "E08" and 9.85 < cen(o.name).x < 10.0 and cen(o.name).z < 0.0 and sz(o)[0] < 200]
brackets_top = ["E7216_E08", "E7284_E08"]
toprail = pick("K05", lambda d, o: True); handrail = pick("H04", lambda d, o: True); hbrk = pick("C04", lambda d, o: True)
print("counts", len(treads), len(pin_hw), len(lockpins), len(poles), len(jack_parts), len(jack_2nd))

# ---------------------------------------------------------------- items: (id, orange, red, anchor point)
def lerp(n, t):                     # point along the long axis of an object's bounding box (t 0..1 from min-x end)
    o = OBJ[n]; bb = dims(o); lo = min(bb, key=lambda v: v.x); hi = max(bb, key=lambda v: v.x)
    c = cen(n); ax = (hi - lo)
    return Vector((lo.x + ax.x * t, c.y, lo.z + ax.z * t))
def mm(x, y, z): return Vector((x / 1000, y / 1000, z / 1000))
def on(a_, b_, t, y): return mm(a_[0] + (b_[0] - a_[0]) * t, y, a_[1] + (b_[1] - a_[1]) * t)
FG = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath), "frame_geometry_final.json")))
L = FG["L"]; Rr = FG["R"]
dup_pole = [n for n in dup_second if n.endswith("_F04") and OBJ[n].dimensions.x * 1000 > 1000 or (n.endswith("_F04") and max(OBJ[n].dimensions) * 1000 > 1000)]
ITEMS = [
    ("f1", treads, [], mm(8900, -17900, 575)),                                                  # tread 3 walking surface
    ("f2", rails + pin_hw, [], on(L["rail_lo"]["a"], L["rail_lo"]["b"], 0.30, -18350)),       # left lower rail
    ("f3", lockpins + poles, [], cen("E639_F04")),                                           # one piece: pole + its locking end                                                     # a left lock pin
    ("f4", poles, [], mm(L["poles"][1]["x"], -18360, L["poles"][1]["zlo"] + 0.70 * (L["poles"][1]["zhi"] - L["poles"][1]["zlo"]))),
    ("f5", axle_base + axle_top + hooks + jack_parts + brackets_top, axle_2nd + jack_2nd, cen("E6956_E08")),
    ("f6", toprail, [], on(L["hand_rails"][1]["a"], L["hand_rails"][1]["b"], 0.78, L["hand_rails"][1]["y"])),
    ("f7", handrail, [], on(L["hand_rails"][0]["a"], L["hand_rails"][0]["b"], 0.30, L["hand_rails"][0]["y"])),
    ("f8", hbrk, [], cen(sorted(hbrk, key=lambda n: (round(cen(n).y, 1), -cen(n).x))[1])),
    ("f9", [], dup_second + [a for a, b in DUP], mm(Rr["poles"][0]["x"], -17100, Rr["poles"][0]["zlo"] + 0.85 * (Rr["poles"][0]["zhi"] - Rr["poles"][0]["zlo"]))),
]

def stand_in(name, p0, p1, r):
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=(p1 - p0).length)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(MS)
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.location = (p0 + p1) / 2; o.rotation_euler = (p1 - p0).to_track_quat('Z', 'Y').to_euler(); o.hide_render = True
    return o.name
PROXY_F5 = []
for ax, cx, cz in (("E6998_E08", 9.6359, -0.0893), ("E7326_E08", 8.1358, 0.9607)):
    if ax in OBJ:
        ys_ = [(OBJ[ax].matrix_world @ v.co).y for v in OBJ[ax].data.vertices]
        PROXY_F5.append(stand_in("AxleExtension_" + ax, Vector((cx, max(ys_), cz)), Vector((cx, -17.019, cz)), 0.0125))
cam_d = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
def place(target, direction, dist, lens=40):
    t = Vector(target); d = Vector(direction).normalized()
    cam.location = t + d * dist; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam_d.type = 'PERSP'; cam_d.lens = lens; cam_d.clip_start = 0.005; cam_d.clip_end = 100
def shot(name, rx=1000, ry=625):
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.filepath = os.path.join(out, name); bpy.ops.render.render(write_still=True)

ALL = [OBJ[n] for n in treads + rails + poles + toprail + handrail + axle_2nd + jack_2nd + brackets_top + jack_parts if n in OBJ]
CORNERS = [o.matrix_world @ Vector(c) for o in ALL for c in o.bound_box]
DIRV = (0.62, -1.3, 0.52)
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
tgt = sum(CORNERS, Vector()) / len(CORNERS); dist = 5.0
dv = Vector(DIRV).normalized()
for it in range(12):                                       # centre the projected extents, then scale to fill ~88 %
    place(tuple(tgt), DIRV, dist); bpy.context.view_layer.update()
    ps = [world_to_camera_view(sc, cam, c) for c in CORNERS]
    x0, x1 = min(q.x for q in ps), max(q.x for q in ps); y0, y1 = min(q.y for q in ps), max(q.y for q in ps)
    rx = cam.matrix_world.to_3x3() @ Vector((1, 0, 0)); ry = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
    width_m = 2 * dist * math.tan(math.atan(36 / 2 / 40)); height_m = width_m * 1000 / 1600
    tgt = tgt + rx * ((x0 + x1) / 2 - 0.5) * width_m + ry * ((y0 + y1) / 2 - 0.5) * height_m
    dist *= max(x1 - x0, y1 - y0) / 0.88
OV = (tuple(tgt), DIRV, dist, 40)
ONLY = [x for x in os.environ.get("ONLY", "").split(",") if x]
print("OVERVIEW dist", round(dist, 2))
marks = {}
for iid, _, _, a in ITEMS:
    q = world_to_camera_view(sc, cam, a)
    marks[iid] = [round(q.x * 100, 2), round((1 - q.y) * 100, 2)]
if not ONLY: shot("f_overview.jpg", 1600, 1000)
if not ONLY: json.dump(marks, open(os.path.join(out, "f_markers.json"), "w"), indent=1)
print("MARKERS", marks)

CLOSE = {
    "f1": [((9.45, -17.72, 0.20), (0.9, -0.55, 0.85), 1.35, 45), ((9.62, -17.72, 0.02), (0.45, -0.35, -1.0), 1.1, 45)],
    "f2": [((9.62, -18.25, 0.02), (0.9, -1.0, 0.9), 0.75, 45)],
    "f3": [(tuple(cen("E639_F04")), (0.5, -1.0, 0.3), 0.5, 45)],
    "f4": [((9.02, -18.10, 0.95), (0.35, -1.0, 0.25), 3.2, 40)],
    "f5": [((9.75, -18.33, -0.06), (0.6, -1.0, 0.45), 0.9, 45), ((8.13, -18.33, 0.96), (-0.7, -1.0, 0.5), 0.8, 45), ((9.636, -17.06, -0.08), (0.55, 1.0, 0.55), 0.42, 45)],
    "f6": [((9.40, -18.33, 1.26), (0.8, -1.0, 0.35), 0.6, 45)],
    "f7": [((9.40, -18.33, 1.26), (0.8, -1.0, 0.35), 0.6, 45)],
    "f8": [(tuple(cen(sorted(hbrk, key=lambda n: (round(cen(n).y, 1), -cen(n).x))[1])), (0.35, -1.0, -0.35), 0.42, 45)],
    "f9": [((9.40, -17.10, 0.60), (0.9, 1.0, 0.45), 1.5, 40), ((9.6466, -17.101, -0.094), (0.6, 1.0, 0.5), 0.45, 45)],
}
for iid, o_, r_, a in ITEMS:
    if ONLY and iid not in ONLY: continue
    paint(o_, HL); paint(r_, RM)
    for n in PROXY_F5: OBJ[n].hide_render = (iid != "f5")
    place(*OV); shot(f"{iid}_where.jpg")
    for k, v in enumerate(CLOSE[iid]):
        place(*v); shot(f"{iid}_close{k + 1}.jpg")
    unpaint()
print("RENDERS done")
