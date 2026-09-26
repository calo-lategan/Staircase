"""Per-element display colour from the geometry iterator's styles (diffuse RGB), keyed like final_meshes (E<id>)."""
import sys, json, multiprocessing, collections
import ifcopenshell, ifcopenshell.geom
f = ifcopenshell.open(sys.argv[1])
st = ifcopenshell.geom.settings(); st.set("use-world-coords", True)
it = ifcopenshell.geom.iterator(st, f, multiprocessing.cpu_count())
out = {}
if it.initialize():
    while True:
        s = it.get(); g = s.geometry
        ids = list(g.material_ids); mats = g.materials
        if ids and mats:
            k = collections.Counter(ids).most_common(1)[0][0]
            m = mats[k]
            d = m.diffuse
            try:
                rgb = [d.r(), d.g(), d.b()]
            except Exception:
                rgb = list(d)[:3]
            out[f"E{s.id}"] = dict(rgb=rgb, style=m.name, transparency=getattr(m, "transparency", 0.0) or 0.0)
        if not it.next(): break
json.dump(out, open(sys.argv[2], "w"), indent=0)
print("COLOURS", len(out), collections.Counter(tuple(round(c, 2) for c in v["rgb"]) for v in out.values()).most_common(20))
