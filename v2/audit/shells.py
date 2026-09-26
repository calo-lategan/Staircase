"""Split objects into connected shells: bbox (local to a ref), signed volume, closed?, face count.
blender ... --python shells.py -- CONFIG refx refy refz name1 name2 ..."""
import bpy, bmesh, sys, types, json
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
cfg = a[0]; REF = Vector((float(a[1]), float(a[2]), float(a[3]))); names = a[4:]
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
m.goto_config(bpy.context, cfg)
dg = bpy.context.evaluated_depsgraph_get()
out = {}
for n in names:
    o = bpy.data.objects[n]
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(Matrix.Translation(-REF) @ o.evaluated_get(dg).matrix_world)
    bm.faces.ensure_lookup_table()
    seen, shells = set(), []
    for f in bm.faces:
        if f.index in seen: continue
        stack, sh = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); sh.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        shells.append(sh)
    res = []
    for sh in shells:
        vs = {v for f in sh for v in f.verts}
        lo = [min(v.co[k] for v in vs) * 1000 for k in range(3)]; hi = [max(v.co[k] for v in vs) * 1000 for k in range(3)]
        vol = 0.0
        for f in sh:
            vv = [v.co for v in f.verts]
            for i in range(1, len(vv) - 1):
                vol += vv[0].dot(vv[i].cross(vv[i + 1])) / 6.0
        edges = {e for f in sh for e in f.edges}
        closed = all(len([h for h in e.link_faces if h in set(sh)]) == 2 for e in edges)
        res.append(dict(faces=len(sh), lo=[round(x, 2) for x in lo], hi=[round(x, 2) for x in hi], vol_mm3=round(vol * 1e9, 1), closed=closed))
    out[n] = res
    print("OBJ", n, len(res), "shells")
    for r in sorted(res, key=lambda r: r["lo"][1]):
        print("   ", r)
json.dump(out, open(f"shells_{cfg}.json", "w"), indent=1)
