"""Arbitrary plane cuts through the posed model (read-only). Job JSON: {"config": "...", "cuts": [{"id", "co": [x,y,z],
"no": [nx,ny,nz], "objects": [...] or "*"}]}. Writes {id: {obj: [[p0, p1], ...]}} in world metres.
blender -b RIGGED3.blend --factory-startup --python cut_planes.py -- job.json out.json"""
import bpy, bmesh, sys, types, json
from mathutils import Vector
job_p, out_p = sys.argv[sys.argv.index("--") + 1:][:2]
job = json.load(open(job_p))
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline":
                tr.mute = True
m.goto_config(ctx, job["config"])
dg = ctx.evaluated_depsgraph_get()
unit = job.get("unit", "A")
cands = [o for o in bpy.data.objects if o.type == 'MESH' and o.get("unit") == unit and not o.hide_render]
bms = {}
def bm_of(o):
    if o.name not in bms:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.evaluated_get(dg).matrix_world)
        bms[o.name] = bm
    return bms[o.name]
out = {}
for c in job["cuts"]:
    co, no = Vector(c["co"]), Vector(c["no"]).normalized()
    objs = cands if c.get("objects", "*") == "*" else [bpy.data.objects[n] for n in c["objects"]]
    res = {}
    for o in objs:
        bm = bm_of(o)
        d = [(v.co - co).dot(no) for v in bm.verts]
        if min(d) > 0 or max(d) < 0:
            continue
        b2 = bm.copy()
        r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=co, plane_no=no)
        segs = [[list(v.co) for v in g.verts] for g in r["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]
        b2.free()
        if segs:
            res[o.name] = segs
    out[c["id"]] = res
json.dump(out, open(out_p, "w"))
print("CUTS", len(out), sum(len(v) for v in out.values()))
