"""STEP 2 - Blender CLOTH cross-check (HEADLESS):
    blender -b --factory-startup --python v2/loadtest/blender_cloth.py -- <out_dir>
Cloth stiffness has no physical units, so it is CALIBRATED once, then used to PREDICT other cases:
  1. calibrate bending stiffness so a single catwalk girder ribbon (span 1.831 m, SLS load of one side)
     sags exactly the FE 'locked' deflection (loadtest_latest.py, 45.6 mm)
  2. linearity: same ribbon at the ULS load (x1.48) -> linear theory predicts x1.48 sag
  3. double catwalk WITH a support under the hinged joint -> each span should sag like the single span
  4. double catwalk WITHOUT a support under the joint -> hinged mechanism, cloth shows the collapse
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
L = 1.831
W_SIDE_SLS = 9096.9          # N, one side girder, characteristic (loadtest_latest hand statics)
ULS_RATIO = 1.48             # (1.5*Q + 1.35*G) / (Q + G) for this load mix
DEFL_TARGET = 45.558         # mm, FE locked Vierendeel catwalk (SLS)
DX = 0.025
LOAD_SCALE = 1000.0


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def ribbon(n_spans, pins, hinges):
    """grid along X (n_spans*L long, 0.1 wide); pin columns at x in pins; zero bending at hinge columns."""
    length = n_spans * L
    nx = int(round(length / DX)) + 1
    me = bpy.data.meshes.new("rib"); bm = bmesh.new()
    rows = []
    for j in range(3):
        rows.append([bm.verts.new((-i * DX, (j - 1) * 0.05, 0.0)) for i in range(nx)])
    for j in range(2):
        for i in range(nx - 1):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Ribbon", me); sc.collection.objects.link(o)
    pin = o.vertex_groups.new(name="pin"); bend = o.vertex_groups.new(name="bend")
    for v in me.vertices:
        x = -v.co.x
        if any(abs(x - p) < DX / 2 for p in pins):
            pin.add([v.index], 1.0, 'REPLACE')
        w = 0.0 if any(abs(x - h) < DX * 1.01 for h in hinges) else 1.0
        bend.add([v.index], w, 'REPLACE')
    return o, nx


def roller_pad(x):
    """frictionless collision pad under the ribbon at x: vertical support, horizontal slide free (a roller)"""
    me = bpy.data.meshes.new("pad"); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.08, v.co.y * 0.3, v.co.z * 0.10))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Pad", me); sc.collection.objects.link(o)
    o.location = (-x, 0.0, -0.0515)
    m = o.modifiers.new("Collision", 'COLLISION')
    o.collision.cloth_friction = 0.0
    o.collision.thickness_outer = 0.001
    o.collision.damping = 0.0
    return o


def run(n_spans, pins, hinges, weight_N, bending, frames=120, rollers=()):
    clear()
    for x in rollers:
        roller_pad(x)
    o, nx = ribbon(n_spans, pins, hinges)
    mod = o.modifiers.new("Cloth", 'CLOTH')
    s = mod.settings
    s.quality = 12
    s.mass = (weight_N * n_spans / 9.81) / len(o.data.vertices) / LOAD_SCALE   # unitless solver: scale load, calibrate stiffness
    s.tension_stiffness = s.compression_stiffness = s.shear_stiffness = 20000.0
    s.bending_stiffness = 1e-4
    s.bending_stiffness_max = bending
    s.vertex_group_bending = "bend"
    s.vertex_group_mass = "pin"
    s.air_damping = 30.0
    mod.collision_settings.use_collision = True
    mod.collision_settings.distance_min = 0.001
    mod.collision_settings.collision_quality = 8
    mod.point_cache.frame_start = 1
    mod.point_cache.frame_end = frames
    sc.frame_start, sc.frame_end = 1, frames
    for f in range(1, frames + 1):
        sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    zs = {}
    for v, v0 in zip(ev.data.vertices, o.data.vertices):     # bin by REST position
        x = round(-v0.co.x, 3)
        zs[x] = min(zs.get(x, 0.0), v.co.z)
    sag = -min(zs.values()) * 1000
    spans = []
    for k in range(n_spans):
        seg = [z for x, z in zs.items() if k * L <= x <= (k + 1) * L]
        spans.append(round(-min(seg) * 1000, 1))
    return round(sag, 1), spans, o


R = {}
# 1. calibrate (log bisection)
lo_b, hi_b = 1e-5, 1e5
for _ in range(26):
    b = math.sqrt(lo_b * hi_b)
    sag, _, _ = run(1, [0.0], [], W_SIDE_SLS, b, rollers=(L,))
    if sag > DEFL_TARGET:
        lo_b = b
    else:
        hi_b = b
B = math.sqrt(lo_b * hi_b)
sag1, _, _ = run(1, [0.0], [], W_SIDE_SLS, B, rollers=(L,))
R["calibration"] = dict(bending_stiffness=B, sag_mm=sag1, target_mm=DEFL_TARGET)
# 2. linearity at ULS
sagU, _, _ = run(1, [0.0], [], W_SIDE_SLS * ULS_RATIO, B, rollers=(L,))
R["linearity_ULS"] = dict(sag_mm=sagU, linear_prediction_mm=round(sag1 * ULS_RATIO, 1),
                          ratio=round(sagU / sag1, 3), expected_ratio=ULS_RATIO)
# 3. double catwalk, joint supported (hinge over the support)
sag2, spans2, _ = run(2, [0.0], [L], W_SIDE_SLS, B, rollers=(L, 2 * L))
R["double_supported"] = dict(max_sag_mm=sag2, per_span_mm=spans2, single_span_mm=sag1)
# 4. double catwalk, joint UNSUPPORTED (hinge, no support) -> mechanism
sag3, spans3, o = run(2, [0.0], [L], W_SIDE_SLS, B, frames=150, rollers=(2 * L,))
R["double_unsupported"] = dict(max_sag_mm=sag3, per_span_mm=spans3)
# still of case 4
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
cam.location = (-L, -6, 0.0); cam.rotation_euler = (math.pi / 2, 0, 0)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 4.2; sc.camera = cam
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x, sc.render.resolution_y = 1000, 500
sc.render.filepath = os.path.join(OUT, "E_cloth_double_unsupported.png")
bpy.ops.render.render(write_still=True)
with open(os.path.join(OUT, "results_cloth.json"), "w") as f:
    json.dump(R, f, indent=1)
print("CLOTH_DONE", json.dumps(R))
