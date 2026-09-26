"""Per-change visual references for the SketchUp brief: for every change a 'where on the unit' overview and a
close-up, with the affected parts highlighted (orange = change / new, red = remove) and simple stand-in shapes
for parts that don't exist yet (middle rail, toe board, new posts, extensions, feet, centre rail, ID plate).
Nothing is saved: the blend file is only read.
blender -b "STEP LADDER RIGGED3.blend" --factory-startup --python render_change_refs.py -- <out_dir>
"""
import bpy, bmesh, sys, types, os, math, json
from mathutils import Vector, Matrix
out_dir = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene
ctx = bpy.context
OBJ = bpy.data.objects
for lc in ctx.view_layer.layer_collection.children:
    if lc.name in ("IfcProject/Undefined", "MainStaircase_Source", "Collection"):
        lc.exclude = True
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
for o in OBJ:
    ad = o.animation_data
    if ad:
        for tr in ad.nla_tracks:
            if tr.name == "Storyline":
                tr.mute = True
cab = OBJ.get("Showcase_Cabin")
R = sc.render
R.image_settings.file_format = 'JPEG'
R.image_settings.quality = 88
R.resolution_x, R.resolution_y, R.resolution_percentage = 1000, 625, 100
sc.eevee.taa_render_samples = 16
U = Vector((-math.cos(math.radians(35)), 0, math.sin(math.radians(35))))   # up the stair, standard


def mat(name, col, em):
    mt = bpy.data.materials.new(name)
    nt = mt.node_tree
    bs = nt.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*col, 1)
    bs.inputs["Roughness"].default_value = 0.45
    bs.inputs["Emission Color"].default_value = (*col, 1)
    bs.inputs["Emission Strength"].default_value = em
    return mt


HL = mat("HL_change", (1.0, 0.34, 0.04), 0.9)
RM = mat("HL_remove", (0.9, 0.06, 0.06), 0.9)
saved = {}


def paint(objs, mt):
    for o in objs:
        if o.name not in saved:
            if not o.material_slots:
                o.data.materials.append(None)
            saved[o.name] = [(s.link, s.material) for s in o.material_slots]
        for s in o.material_slots:
            s.link = 'OBJECT'
            s.material = mt


def unpaint():
    for n, lst in saved.items():
        o = OBJ[n]
        for s, (lk, mt) in zip(o.material_slots, lst):
            s.link = lk
            s.material = mt
    saved.clear()


PROXY = []
col = bpy.data.collections.new("BriefProxies")
sc.collection.children.link(col)


def _obj(bm, name, mt=HL):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.materials.append(mt)
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    PROXY.append(o)
    return o


def cyl(p0, p1, r, mt=HL):
    bm = bmesh.new()
    L = (p1 - p0).length
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r, radius2=r, depth=L)
    o = _obj(bm, "px_cyl", mt)
    o.location = (p0 + p1) / 2
    o.rotation_euler = (p1 - p0).to_track_quat('Z', 'Y').to_euler()
    return o


def box(center, size, along=None, mt=HL):
    """size = (length along `along`, width in y, height); along = direction of the long side (default x)"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = _obj(bm, "px_box", mt)
    o.location = center
    if along is not None:
        o.rotation_euler = along.to_track_quat('X', 'Z').to_euler()
    return o


def clear_proxies():
    for o in PROXY:
        bpy.data.objects.remove(o, do_unlink=True)
    PROXY.clear()


def pts(n):
    o = OBJ[n]
    mw = o.evaluated_get(ctx.evaluated_depsgraph_get()).matrix_world
    return [mw @ v.co for v in o.data.vertices]


def cen(n):
    p = pts(n)
    return sum(p, Vector()) / len(p)


def bone_of(o):
    if o.parent_type == 'BONE':
        return o.parent_bone
    for c in o.constraints:
        if c.type == 'CHILD_OF' and getattr(c, "subtarget", ""):
            return c.subtarget
    return ""


def hrs(unit, side, lock, role):
    ns = [o for o in OBJ if o.get("unit") == unit and o.get("side") == side and o.get("hr_variant") == lock
          and o.get("role") == role and o.type == 'MESH']
    return sorted(ns, key=lambda o: -cen(o.name).x)          # index 0 = bottom step


def treads(unit="A"):
    pre = "MainRig_" if unit == "A" else "UnitB_"
    out = []
    for o in OBJ:
        if o.type == 'MESH' and o.name.startswith(pre) and bone_of(o).startswith("Tread") and max(o.dimensions) > 1.0:
            out.append(o)
    return sorted(out, key=lambda o: -cen(o.name).x)


def nosing(o):
    p = pts(o.name)
    return Vector((max(v.x for v in p), sum(v.y for v in p) / len(p), max(v.z for v in p)))


cam = bpy.data.objects.new("CR_Cam", bpy.data.cameras.new("CR_Cam"))
cam.data.lens = 50; cam.data.clip_start = 0.02; cam.data.clip_end = 300
sc.collection.objects.link(cam)
sc.camera = cam


def aim(target, az, el, d):
    az, el = math.radians(az), math.radians(el)
    cam.location = target + d * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()


def shot(name):
    ctx.view_layer.update()
    R.filepath = os.path.join(out_dir, name + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)


def overview_std():
    c = (cen("MainRig_006") + cen("MainRig_010")) / 2 + Vector((0, 0, 0.15))
    aim(c, 58, 22, 6.4)


def config(k):
    m.goto_config(ctx, k)
    if cab:
        cab.hide_render = True
    ctx.view_layer.update()


def hidden(objs, flag=True):
    for o in objs:
        o.hide_render = flag


Y_R_OUT, Y_L_OUT = 46.2587, 44.9877          # outer faces of the right rail / left channel
POST_R, POST_L = Y_R_OUT + 0.045, Y_L_OUT - 0.045   # 60 posts, 15 mm clear outside the rails

# ================================================================== standard stair changes
config("SINGLE_STANDARD")
T = treads()
N0, N5 = nosing(T[0]), nosing(T[5])
guard = {s: max(hrs("A", s, "STANDARD", "guardrail"), key=lambda o: o.dimensions.length) for s in "RL"}
hand = {s: max(hrs("A", s, "STANDARD", "handrail"), key=lambda o: o.dimensions.length) for s in "RL"}
poles = {s: hrs("A", s, "STANDARD", "pole") for s in "RL"}
tops = {s: hrs("A", s, "STANDARD", "toppost") for s in "RL"}
minis = {s: hrs("A", s, "STANDARD", "mini") for s in "RL"}
top_z = {s: max(v.z for v in pts(guard[s].name)) for s in "RL"}


def step_line(x):             # height of the nosing line at x
    return N0.z + (N0.x - x) * math.tan(math.radians(35))



# 4 (revised): keep all 12 flat poles, pin = bottom of the pole; make them thicker -> highlight every pole, pin and top post
allp = []
for s_ in "RL":
    allp += poles[s_] + minis[s_] + tops[s_]
paint(allp, HL)
overview_std(); shot("c4_where")
c = cen(poles["R"][2].name)
aim(Vector((c.x, 46.25, c.z - 0.35)), 60, 14, 1.3); shot("c4_close")
unpaint()
print("CHANGE_REFS_DONE")
