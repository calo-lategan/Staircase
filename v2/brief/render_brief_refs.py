"""Reference images for the SketchUp change brief + projected callout positions (percent of image).
blender -b "STEP LADDER RIGGED3.blend" --factory-startup --python render_brief_refs.py -- <out_dir>
"""
import bpy, sys, types, os, math, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
out_dir = sys.argv[sys.argv.index("--") + 1]
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
R.image_settings.file_format = 'JPEG'
R.image_settings.quality = 90
sc.eevee.taa_render_samples = 16
OBJ = bpy.data.objects


def story(on):
    for o in OBJ:
        ad = o.animation_data
        if ad:
            for tr in ad.nla_tracks:
                if tr.name == "Storyline":
                    tr.mute = not on


def pts(n):
    o = OBJ[n]
    mw = o.evaluated_get(ctx.evaluated_depsgraph_get()).matrix_world
    return [mw @ v.co for v in o.data.vertices]


def cen(n):
    p = pts(n)
    return sum(p, Vector()) / len(p)


def hr(unit, side, lock, role, pick="mid", biggest=False):
    ns = [o.name for o in OBJ if o.get("unit") == unit and o.get("side") == side and o.get("hr_variant") == lock
          and o.get("role") == role and o.type == 'MESH']
    if biggest:
        return max(ns, key=lambda n: (max(p.x for p in pts(n)) - min(p.x for p in pts(n))))
    ns.sort(key=lambda n: cen(n).x)
    return ns[-1] if pick == "max_x" else ns[0] if pick == "min_x" else ns[len(ns) // 2]


def end_pt(n, key):
    p = pts(n)
    q = max(p, key=key)
    near = [v for v in p if (v - q).length < 0.02]
    return sum(near, Vector()) / len(near)


cd = bpy.data.cameras.new("REF_Cam"); cd.lens = 50; cd.clip_start = 0.02; cd.clip_end = 300
cd.dof.use_dof = False
cam = bpy.data.objects.new("REF_Cam", cd); sc.collection.objects.link(cam)


def aim(target, az, el, d):
    az, el = math.radians(az), math.radians(el)
    cam.location = target + d * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    ctx.view_layer.update()


def shoot(name, camobj, calls, W=1600, H=1000):
    sc.camera = camobj
    R.resolution_x, R.resolution_y, R.resolution_percentage = W, H, 100
    ctx.view_layer.update()
    res = []
    for num, p in calls:
        v = world_to_camera_view(sc, camobj, p)
        res.append(dict(n=num, x=round(v.x * 100, 2), y=round((1 - v.y) * 100, 2), ok=bool(v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1)))
    R.filepath = os.path.join(out_dir, name + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("REF", name, flush=True)
    return {"file": name + ".jpg", "w": W, "h": H, "calls": res}


OUT = {}
story(False)
# ---- R1 overview: standard stair from the right-hand side (box-tube rails, posts, rails, hooks, feet)
m.goto_config(ctx, "SINGLE_STANDARD")
cab = OBJ.get("Showcase_Cabin")
if cab:
    cab.hide_render = True
lo_r, up_r = cen("MainRig_179"), cen("MainRig_118")
post = hr("A", "R", "STANDARD", "pole")
guard = hr("A", "R", "STANDARD", "guardrail", biggest=True)
hand = hr("A", "R", "STANDARD", "handrail", biggest=True)
mini = hr("A", "R", "STANDARD", "mini")
c = (cen("MainRig_006") + cen("MainRig_010")) / 2 + Vector((0, 0, 0.45))
aim(c - Vector((0, 0, 0.3)), 58, 22, 6.4)
OUT["overview"] = shoot("ref_overview", cam, [
    (1, cen("MainRig_019")), (2, lo_r), (3, up_r), (4, cen(post)), (5, cen(guard)), (6, cen(hand)),
    (7, lo_r.lerp(cen(guard), 0.5)), (8, lo_r + Vector((0, 0.03, 0.09))), (9, end_pt("MainRig_010", lambda v: v.y)),
    (10, cen("MainRig_003"))])
# ---- R2 tread front edge + gap under it (right-hand end of step 3)
t2, t1 = pts("MainRig_096"), pts("MainRig_079")
fx, yc = max(v.x for v in t2), 45.628
z2lo, z2hi, z1hi = min(v.z for v in t2), max(v.z for v in t2), max(v.z for v in t1)
aim(Vector((fx, yc, (z1hi + z2hi) / 2)), 8, 6, 1.05)
OUT["tread"] = shoot("ref_tread_edge", cam, [(1, Vector((fx, yc, (z2lo + z2hi) / 2))), (2, Vector((fx, yc + 0.18, z2lo))),
                                             (3, Vector((fx - 0.015, yc - 0.18, (z1hi + z2lo) / 2)))])
# ---- R5 catwalk side elevation (feet, lower rail, mid-foot position)
m.goto_config(ctx, "SINGLE_CATWALK")
lo = pts("MainRig_179")
mid_bot = Vector(((min(v.x for v in lo) + max(v.x for v in lo)) / 2, max(v.y for v in lo), min(v.z for v in lo)))
aim(mid_bot + Vector((0, 0, 0.2)), 88, 5, 3.4)
OUT["catwalk"] = shoot("ref_catwalk_side", cam, [(1, cen("MainRig_003")), (2, cen("MainRig_009")), (3, mid_bot - Vector((0, 0, 0.02))),
                                                 (4, cen("MainRig_179"))], 1600, 700)
# ---- R6 post base on the right-hand side (flat post, lock pin, rail)
m.goto_config(ctx, "SINGLE_STANDARD")
mc = cen(mini)
aim(mc + Vector((0, 0, 0.06)), 72, 16, 0.55)
OUT["post"] = shoot("ref_post_base", cam, [(1, mc + Vector((0, 0, 0.16))), (2, mc), (3, min(pts("MainRig_118"), key=lambda v: (v - mc).length))])
# ---- storyline close-ups: nested join and end-to-end hook
story(True)
scam = OBJ["StoryCam"]
for o in OBJ:                      # hidden-in-viewport objects are not evaluated: let the storyline decide
    if o.get("unit") or o.get("hr_variant"):
        o.hide_viewport = False
sc.frame_set(1256)
sc.frame_set(1256)
A_ch = end_pt("MainRig_037", lambda v: v.x)
A_up = end_pt("MainRig_026", lambda v: v.x)
OUT["nested"] = shoot("ref_nested_join", scam, [(1, A_ch + Vector((0, 0.0145, 0.004))), (2, A_ch + Vector((0, 0, 0.006))),
                                                (3, A_up + Vector((0, 0, 0.006)))], 1600, 900)
sc.frame_set(1300)
sc.frame_set(1300)
pin = cen(hr("A", "L", "STANDARD", "mini", "max_x"))
OUT["pin"] = shoot("ref_centre_pin", scam, [(1, pin), (2, end_pt("MainRig_037", lambda v: v.x))], 1600, 900)
sc.frame_set(200)
OUT["hook"] = shoot("ref_end_hook", scam, [(1, end_pt("MainRig_010", lambda v: -v.y)), (2, end_pt("UnitB_037", lambda v: v.x))], 1600, 900)
json.dump(OUT, open(os.path.join(out_dir, "callouts.json"), "w"), indent=1)
print("REFS_DONE")
