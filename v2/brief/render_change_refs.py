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


# 1 treads + lips
paint(T, HL)
for tr in T:
    n = nosing(tr)
    box(Vector((n.x - 0.001, n.y, n.z - 0.040 - 0.0175)), (0.004, 1.176, 0.035))
overview_std(); shot("c1_where")
mid = (nosing(T[2]) + nosing(T[3])) / 2
aim(mid + Vector((0, 0, -0.08)), 10, 16, 1.5); shot("c1_close")
unpaint(); clear_proxies()

# 2 right-hand rails
paint([OBJ["MainRig_179"], OBJ["MainRig_118"]], HL)
overview_std(); shot("c2_where")
p = pts("MainRig_179"); xb = max(v.x for v in p)
tgt = sum((v for v in p if v.x > xb - 0.5), Vector()) / len([v for v in p if v.x > xb - 0.5])
aim(tgt + Vector((0, 0, 0.05)), 78, 8, 0.9); shot("c2_close")
unpaint()

# 3 left-hand channels (end view of the U profiles + from outside)
paint([OBJ["MainRig_037"], OBJ["MainRig_026"]], HL)
aim((cen("MainRig_006") + cen("MainRig_010")) / 2 + Vector((0, 0, 0.15)), -58, 22, 6.4); shot("c3_where")
p = pts("MainRig_037"); xb = max(v.x for v in p)
end = sum((v for v in p if v.x > xb - 0.012), Vector()) / len([v for v in p if v.x > xb - 0.012])
aim(end + Vector((0, 0, 0.02)), -25, 28, 0.42); shot("c3_close")
unpaint()

# 4 posts: remove flats at steps 2,4,5 (red); new 60x60 outside the rails at steps 1,3,6 (orange stand-ins)
for s, y in (("R", POST_R), ("L", POST_L)):
    for i in (1, 3, 4):
        paint([poles[s][i], tops[s][i]], RM)
    for i in (0, 2, 5):
        hidden([poles[s][i], tops[s][i]])
        c = cen(poles[s][i].name)
        zb = min(v.z for v in pts(minis[s][i].name))
        box(Vector((c.x, y, (zb + top_z[s]) / 2)), (0.06, 0.06, top_z[s] - zb))
overview_std(); shot("c4_where")
c = cen(poles["R"][2].name)
aim(Vector((c.x, POST_R, c.z - 0.25)), 52, 14, 1.9); shot("c4_close")
for s in "RL":
    for i in (0, 2, 5):
        hidden([poles[s][i], tops[s][i]], False)
unpaint(); clear_proxies()

# 5 lock pins at steps 2,4,5
for s in "RL":
    paint([minis[s][i] for i in (1, 3, 4)], HL)
overview_std(); shot("c5_where")
mc = cen(minis["R"][1].name)
aim(mc + Vector((0, 0, 0.05)), 72, 16, 0.55); shot("c5_close")
unpaint()

# 6 top rail
paint([guard["R"], guard["L"]], HL)
overview_std(); shot("c6_where")
aim(cen(guard["R"].name), 62, 24, 1.5); shot("c6_close")
unpaint()

# 7 handrail + 300 mm level extensions
paint([hand["R"], hand["L"]], HL)
for s in "RL":
    p = pts(hand[s].name)
    lo_end = max(p, key=lambda v: v.x); hi_end = min(p, key=lambda v: v.x)
    yc = sum(v.y for v in p) / len(p)
    a = Vector((lo_end.x, yc, lo_end.z - 0.0125)); b = Vector((hi_end.x, yc, hi_end.z - 0.0125))
    cyl(a, a + Vector((0.30, 0, 0)), 0.024)
    cyl(b, b + Vector((-0.30, 0, 0)), 0.024)
overview_std(); shot("c7_where")
p = pts(hand["R"].name); lo_end = max(p, key=lambda v: v.x)
aim(lo_end + Vector((0.12, 0, -0.05)), 45, 14, 1.25); shot("c7_close")
unpaint(); clear_proxies()

# 8 middle rail at 575 above the step line (stand-in)
for y in (POST_R - 0.045, POST_L + 0.045):
    a = Vector((N0.x, y, step_line(N0.x) + 0.575)); b = Vector((N5.x, y, step_line(N5.x) + 0.575))
    cyl(a, b, 0.015)
overview_std(); shot("c8_where")
aim(Vector(((N0.x + N5.x) / 2, POST_R, step_line((N0.x + N5.x) / 2) + 0.45)), 80, 10, 2.4); shot("c8_close")
clear_proxies()

# 9 toe board 150 high on the step line (stand-in)
L = (N5.x - N0.x) / math.cos(math.radians(35)) + 0.3
for y in (POST_R - 0.048, POST_L + 0.048):
    xm = (N0.x + N5.x) / 2
    box(Vector((xm, y, step_line(xm) + 0.075)), (L, 0.006, 0.15), along=U)
overview_std(); shot("c9_where")
xm = N0.x - 0.35
aim(Vector((xm, POST_R, step_line(xm) + 0.05)), 70, 14, 1.4); shot("c9_close")
clear_proxies()

# 10 hook plates at the rail ends
hooks = [OBJ[n] for n in ("MainRig_000", "MainRig_001", "MainRig_177", "MainRig_178")]
paint(hooks, HL)
overview_std(); shot("c10_where")
aim(cen("MainRig_178"), 72, 22, 0.55); shot("c10_close")
unpaint()

# 13 ID plate on the right-hand lower rail
p = pts("MainRig_179"); xb = max(v.x for v in p)
low = sum((v for v in p if v.x > xb - 0.3), Vector()) / len([v for v in p if v.x > xb - 0.3])
box(Vector((low.x - 0.15, Y_R_OUT + 0.003, low.z + 0.07)), (0.10, 0.004, 0.06), along=U)
overview_std(); shot("c13_where")
aim(Vector((low.x - 0.15, Y_R_OUT, low.z + 0.07)), 80, 12, 0.6); shot("c13_close")
clear_proxies()

# ================================================================== 11 feet (catwalk)
config("SINGLE_CATWALK")
feet = [OBJ[n] for n in ("MainRig_002", "MainRig_003", "MainRig_004", "MainRig_009")]
paint(feet, HL)
ground = 4.90
for f in feet:
    c = cen(f.name)
    box(Vector((c.x, c.y, ground - 0.005)), (0.15, 0.15, 0.01))
for n in ("MainRig_179", "MainRig_037"):
    p = pts(n)
    xm = (min(v.x for v in p) + max(v.x for v in p)) / 2
    zb = min(v.z for v in p if abs(v.x - xm) < 0.1)
    yc = sum(v.y for v in p) / len(p)
    box(Vector((xm, yc, (zb + ground) / 2)), (0.04, 0.035, zb - ground))
    box(Vector((xm, yc, ground - 0.005)), (0.15, 0.15, 0.01))
c = (cen("MainRig_006") + cen("MainRig_010")) / 2
aim(c + Vector((0, 0, 0.1)), 55, 26, 5.2); shot("c11_where")
aim(Vector((c.x, Y_R_OUT, ground + 0.12)), 86, 5, 3.0); shot("c11_close")
unpaint(); clear_proxies()

# ================================================================== 12 side-by-side: pins through both rails + end-held centre rail
config("WIDE_STANDARD")
T = treads()
N0, N5 = nosing(T[0]), nosing(T[5])
pins = hrs("A", "L", "STANDARD", "mini")
paint(pins, HL)
paint([OBJ["MainRig_037"], OBJ["MainRig_026"], OBJ["UnitB_179"], OBJ["UnitB_118"]], HL)
inner = [o for o in OBJ if o.get("unit") == "A" and o.get("side") == "L" and o.get("hr_variant") == "STANDARD"
         and o.get("role") != "mini" and o.type == 'MESH']
paint(inner, RM)
yj = 45.005
a = Vector((N0.x + 0.30, yj, step_line(N0.x) + 1.0)); b = Vector((N5.x - 0.30, yj, step_line(N5.x) + 1.0))
cyl(Vector((N0.x, yj, step_line(N0.x) + 1.0)), Vector((N5.x, yj, step_line(N5.x) + 1.0)), 0.024)
cyl(Vector((N0.x, yj, step_line(N0.x) + 1.0)), Vector((N0.x + 0.30, yj, step_line(N0.x) + 1.0)), 0.024)
cyl(Vector((N5.x, yj, step_line(N5.x) + 1.0)), Vector((N5.x - 0.30, yj, step_line(N5.x) + 1.0)), 0.024)
box(Vector((N0.x + 0.30, yj, (4.875 + step_line(N0.x) + 1.0) / 2)), (0.06, 0.06, step_line(N0.x) + 1.0 - 4.875))
axt = cen("MainRig_010")
box(Vector((N5.x - 0.30, yj, (axt.z + step_line(N5.x) + 1.0) / 2)), (0.06, 0.06, step_line(N5.x) + 1.0 - axt.z))
c = (cen("MainRig_006") + cen("MainRig_010")) / 2
aim(Vector((c.x, yj - 0.3, c.z + 0.3)), -40, 26, 7.0); shot("c12_where")
aim(Vector((N0.x - 0.1, yj, step_line(N0.x) + 0.25)), -12, 22, 1.6); shot("c12_close")
unpaint(); clear_proxies()
print("CHANGE_REFS_DONE")
