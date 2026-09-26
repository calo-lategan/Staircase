"""Plane cuts of the final model (no rig). Job JSON {"cuts": [{"id","co","no","objects": "*"|[..]}]} -> segments per object."""
import bpy, bmesh, sys, json
from mathutils import Vector
job_p, out_p = sys.argv[sys.argv.index("--") + 1:][:2]
job = json.load(open(job_p)); out = {}; bms = {}
cands = [o for o in bpy.data.objects if o.type == 'MESH']
for c in job["cuts"]:
    co, no = Vector(c["co"]), Vector(c["no"]).normalized(); res = {}
    objs = cands if c.get("objects", "*") == "*" else [bpy.data.objects[n] for n in c["objects"]]
    for o in objs:
        if o.name not in bms:
            bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bms[o.name] = bm
        bm = bms[o.name]
        d = [(v.co - co).dot(no) for v in bm.verts]
        if not d or min(d) > 0 or max(d) < 0: continue
        b2 = bm.copy()
        r = bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=co, plane_no=no)
        segs = [[list(v.co) for v in g.verts] for g in r["geom_cut"] if isinstance(g, bmesh.types.BMEdge)]
        b2.free()
        if segs: res[o.name] = segs
    out[c["id"]] = res
json.dump(out, open(out_p, "w")); print("CUTS", len(out))
