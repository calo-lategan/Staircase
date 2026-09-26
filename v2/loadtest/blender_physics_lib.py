"""STEP 2 - Blender rigid-body physics tests. HEADLESS ONLY (never inside the live session):
    blender -b --factory-startup --python v2/loadtest/blender_physics.py -- <out_dir>
Builds physics proxies of the MEASURED members (see loadtest_latest.py) in a blank scene and runs:
  A  mechanism        : side girders unlocked (pure parallelogram) vs locked (bottom-mini lock pin)
  B  reaction          : top-support force measured by breaking-threshold bisection vs hand statics
  C  hook ULS          : hooks as breakable joints at their hand-calc capacity under ULS crowd load,
                         then the recommended hook (t10 x w16)
  D  catwalk stability : lateral push at guardrail height via a force-limited motor -> start of motion
                         (mu 0.30 -> sliding governs; mu 0.90 -> tipping governs)
Units m, kg, N, s. Constraint impulse threshold = force / physics steps per second.
Writes <out_dir>/results_physics.json and a still per test.
"""
import bpy, bmesh, math, json, os, sys, time
from mathutils import Vector, Matrix, Euler

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
FPS, SUB, ITER = 24, 30, 100
STEP_HZ = FPS * SUB
G = 9.81
LINK = Vector((0.1999, 0.0, 0.0246))
Y_SIDE = 0.6205
LOCKS = {"CATWALK": (0.0, [0.0590, 0.3642, 0.6693, 0.9745, 1.2797, 1.5848]),
         "STANDARD": (35.0, [0.0814, 0.3865, 0.6917, 0.9969, 1.3020, 1.6072]),
         "STEEP": (49.4, [0.1036, 0.4087, 0.7139, 1.0191, 1.3242, 1.6294])}
SPAN, P_FRAME, L_TREAD = 1.831, 0.3052, 1.241
RHO_S, RHO_A = 7850.0, 2700.0
M_TREAD = 2124.8e-6 * 1.236 * RHO_A
M_BAR_LO = 275.0e-6 * 1.7787 * RHO_S
M_BAR_UP = 274.7e-6 * 1.8451 * RHO_S
M_HR_SIDE = 22.4                       # handrail per side, loadtest_latest.self_weight basis A
M_UNIT = 127.0                         # unit self weight, basis A
sc = bpy.context.scene


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    if sc.rigidbody_world:
        bpy.ops.rigidbody.world_remove()
    bpy.ops.rigidbody.world_add()
    w = sc.rigidbody_world
    w.substeps_per_frame = SUB
    w.solver_iterations = ITER
    w.point_cache.frame_start = 1
    w.point_cache.frame_end = 200
    sc.frame_start, sc.frame_end = 1, 200
    sc.render.fps = FPS


def box(name, size, loc, rot=(0, 0, 0), color=(0.7, 0.7, 0.7, 1)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    mt = bpy.data.materials.new(name + "_m"); mt.diffuse_color = color
    me.materials.append(mt)
    return o


def _activate(o):
    for x in sc.objects:
        x.select_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def rb(o, kind='ACTIVE', mass=1.0, coll=(0,), friction=0.5):
    _activate(o)
    bpy.ops.rigidbody.object_add(type=kind)
    r = o.rigid_body
    r.mass = mass; r.collision_shape = 'BOX'; r.friction = friction
    r.use_margin = True; r.collision_margin = 0.0005
    r.linear_damping = 0.0; r.angular_damping = 0.0
    cc = [False] * 20
    for c in coll:
        cc[c] = True
    r.collision_collections = cc
    return o


def joint(name, a, b, loc, kind='HINGE', threshold_N=None):
    """HINGE about world Y | FIXED | ROLLER (vertical-only: free slide along world X, free rot about Y)."""
    e = bpy.data.objects.new(name, None)
    sc.collection.objects.link(e)
    e.location = loc
    roller = kind == 'ROLLER'
    e.rotation_euler = {'HINGE': (-math.pi / 2, 0, 0), 'HINGE_X': (0, math.pi / 2, 0)}.get(kind, (0, 0, 0))
    _activate(e)
    bpy.ops.rigidbody.constraint_add(type='GENERIC' if roller else ('HINGE' if kind == 'HINGE_X' else kind))
    c = e.rigid_body_constraint
    if roller:
        c.use_limit_lin_x = False
        c.use_limit_lin_y = c.use_limit_lin_z = True
        c.limit_lin_y_lower = c.limit_lin_y_upper = 0.0
        c.limit_lin_z_lower = c.limit_lin_z_upper = 0.0
        c.use_limit_ang_x = c.use_limit_ang_y = c.use_limit_ang_z = False
    c.object1, c.object2 = a, b
    c.disable_collisions = True
    c.use_override_solver_iterations = True
    c.solver_iterations = 2 * ITER
    if threshold_N is not None:
        c.use_breaking = True
        c.breaking_threshold = threshold_N / STEP_HZ
    return e


def girder_system(lock, locked=True, q_kN=7.5, factor=1.0, top_threshold_N=None):
    th, st = LOCKS[lock]
    t = math.radians(th)
    u = Vector((-math.cos(t), 0, math.sin(t)))
    o0 = Vector((0, 0, 1.0))
    ground = rb(box("BaseSupport", (0.2, 1.6, 0.05), o0 + Vector((0, 0, -0.05)), color=(0.2, 0.2, 0.22, 1)), 'PASSIVE', coll=(1,))
    top = rb(box("TopBar", (0.05, 1.6, 0.05), o0 + u * SPAN + Vector((0, 0, 0.06)), color=(0.85, 0.85, 0.88, 1)), 'PASSIVE', coll=(1,))
    q_mass = q_kN * 1000.0 * P_FRAME * math.cos(t) * L_TREAD / G * factor
    bodies = {}
    for side, ys in (("R", Y_SIDE), ("L", -Y_SIDE)):
        lo = rb(box(f"BarLo_{side}", (SPAN, 0.025, 0.02), o0 + u * (SPAN / 2) + Vector((0, ys, 0)), rot=(0, t, 0),
                    color=(0.55, 0.5, 0.78, 1)), mass=M_BAR_LO * factor if factor > 1 else M_BAR_LO, coll=(2,))
        up = rb(box(f"BarUp_{side}", (1.845, 0.025, 0.02), o0 + u * ((st[0] + st[-1]) / 2) + LINK + Vector((0, ys, 0)),
                    rot=(0, t, 0), color=(0.88, 0.55, 0.62, 1)), mass=M_BAR_UP + M_HR_SIDE, coll=(3,))
        bodies[f"lo_{side}"], bodies[f"up_{side}"] = lo, up
        joint(f"J_base_{side}", ground, lo, o0 + Vector((0, ys, 0)), kind='HINGE')
    # full-width top axle (part 010, 1.98 kg) joins both bars and sits on ONE roller -> the TOTAL top
    # reaction is statically determinate (moment about the base-hinge line); each side carries half.
    axle = rb(box("TopAxle010", (0.025, 1.305, 0.025), o0 + u * SPAN, color=(0.9, 0.8, 0.2, 1)), mass=1.98, coll=(6,))
    for side, ys in (("R", Y_SIDE), ("L", -Y_SIDE)):
        joint(f"J_axle_{side}", bodies[f"lo_{side}"], axle, o0 + u * SPAN + Vector((0, ys, 0)), kind='HINGE')
    joint("J_top_roller", top, axle, o0 + u * SPAN, kind='ROLLER', threshold_N=top_threshold_N)
    bodies["axle"] = axle
    for i, s in enumerate(st):
        p_lo = o0 + u * s
        p_up = p_lo + LINK
        tr = rb(box(f"Tread{i}", (0.28, 1.2, 0.05), (p_lo + p_up) / 2, color=(0.66, 0.58, 0.42, 1)),
                mass=M_TREAD + q_mass, coll=(4 + i % 2,))
        bodies[f"tread{i}"] = tr
        for side, ys in (("R", Y_SIDE), ("L", -Y_SIDE)):
            # lock = mini pin: stops the parallelogram (rot about Y) but the tread stays simply supported (rot about X free)
            joint(f"J_lo{i}_{side}", bodies[f"lo_{side}"], tr, p_lo + Vector((0, ys, 0)), kind='HINGE_X' if locked else 'POINT')
            joint(f"J_up{i}_{side}", bodies[f"up_{side}"], tr, p_up + Vector((0, ys, 0)), kind='POINT')
    return bodies


def ramp_gravity(n=15):
    """quasi-static loading: gravity 0 -> g over n frames (removes the sudden-load impulse spike)"""
    sc.gravity = (0.0, 0.0, 0.0)
    sc.keyframe_insert("gravity", frame=1)
    sc.gravity = (0.0, 0.0, -G)
    sc.keyframe_insert("gravity", frame=1 + n)


def clear_ramp():
    if sc.animation_data:
        sc.animation_data_clear()
    sc.gravity = (0.0, 0.0, -G)


def simulate(frames):
    sc.rigidbody_world.point_cache.frame_end = frames + 1
    bpy.ops.ptcache.free_bake_all()
    sc.frame_set(1)
    for f in range(1, frames + 1):
        sc.frame_set(f)
    bpy.context.view_layer.update()


def motion(bodies):
    dt, dr = 0.0, 0.0
    for o in bodies.values():
        m0 = Matrix.LocRotScale(o.location, Euler(o.rotation_euler), None)
        m1 = o.matrix_world
        dt = max(dt, (m1.translation - m0.translation).length * 1000)
        dr = max(dr, math.degrees(abs(m0.to_quaternion().rotation_difference(m1.to_quaternion()).angle)))
    return round(dt, 1), round(dr, 2)


def still(name, target=Vector((-0.75, 0, 1.5)), eye=(0.9, -1.3, 0.55), scale=3.2):
    cam = bpy.data.objects.get("Cam")
    if not cam:
        cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam)
    d = Vector(eye).normalized()
    cam.location = target + d * 12
    cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = scale; cam.data.clip_end = 50
    sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.color_type = 'MATERIAL'
    sc.render.resolution_x, sc.render.resolution_y = 900, 600
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath

