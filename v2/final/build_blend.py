"""Build a .blend from the IFC meshes (one object per IFC element, world coords in metres, custom props)."""
import bpy, sys, json
import numpy as np
npz, js, out = sys.argv[sys.argv.index("--") + 1:][:3]
Z = np.load(npz); M = json.load(open(js))
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
col = bpy.data.collections.new("FINAL"); bpy.context.scene.collection.children.link(col)
SHORT = {}
for k, m in M.items():
    v = Z[k + "_v"]; f = Z[k + "_f"]
    me = bpy.data.meshes.new(k)
    me.from_pydata(v.tolist(), [], f.tolist()); me.update()
    mat = (m["material"] or "none").split("_")[0]
    o = bpy.data.objects.new(f"{k}_{mat}", me); col.objects.link(o)
    o["ifc_id"] = m["id"]; o["guid"] = m["guid"]; o["material"] = m["material"] or ""; o["parents"] = json.dumps(m["path"])
bpy.ops.wm.save_as_mainfile(filepath=out)
print("BLEND", len(M))
