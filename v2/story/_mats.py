import bpy, collections
c = collections.Counter()
for o in bpy.data.objects:
    if o.type == 'MESH' and o.get("unit") == "A":
        for m in o.data.materials:
            if m is None: continue
            bs = m.node_tree.nodes.get("Principled BSDF") if m.node_tree else None
            base = tuple(round(x, 2) for x in bs.inputs["Base Color"].default_value[:3]) if bs else None
            c[(m.name, base, tuple(round(x, 2) for x in m.diffuse_color[:3]), o.get("role") or "-")] += 1
for k, v in sorted(c.items(), key=lambda kv: -kv[1])[:30]: print("MAT", k, v)
