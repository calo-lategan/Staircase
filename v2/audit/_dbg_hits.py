import bpy, bmesh, sys, types
from mathutils import Vector
from mathutils.bvhtree import BVHTree
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
m.goto_config(bpy.context, "SINGLE_CATWALK")
dg = bpy.context.evaluated_depsgraph_get()
o = bpy.data.objects["MainRig_061"]
bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.evaluated_get(dg).matrix_world); bm.normal_update()
print("faces", len(bm.faces), "verts", len(bm.verts), "manifold edges", sum(e.is_manifold for e in bm.edges), "/", len(bm.edges),
      "boundary", sum(e.is_boundary for e in bm.edges))
T = BVHTree.FromBMesh(bm)
for z in [5.0025, 5.020, 5.0475]:
    start = Vector((9.49, 45.60972, z)); d = Vector((1, 0, 0)); hits = []
    for _ in range(50):
        loc, nrm, idx, dist = T.ray_cast(start, d, 0.4)
        if loc is None: break
        hits.append((round((loc.x - 9.50879) * 1000, 3), round(nrm.x, 3)))
        start = loc + d * 1e-7
    print("z", z, hits)
