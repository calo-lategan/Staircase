"""IFC -> per-element triangulated meshes (world metres) + metadata (guid, colour material, aggregate path)."""
import sys, json, multiprocessing
import numpy as np
import ifcopenshell, ifcopenshell.geom, ifcopenshell.util.element as E
src, out = sys.argv[1], sys.argv[2]
f = ifcopenshell.open(src)
st = ifcopenshell.geom.settings(); st.set("use-world-coords", True)
parent = {}
for r in f.by_type("IfcRelAggregates"):
    for o in r.RelatedObjects: parent[o.id()] = r.RelatingObject.id()
def path(eid):
    p = []
    while eid in parent:
        eid = parent[eid]; p.append(eid)
    return p
mat = {}
for r in f.by_type("IfcRelAssociatesMaterial"):
    for o in r.RelatedObjects: mat[o.id()] = getattr(r.RelatingMaterial, "Name", None)
it = ifcopenshell.geom.iterator(st, f, multiprocessing.cpu_count())
arrays, meta = {}, {}
if it.initialize():
    while True:
        s = it.get(); e = f.by_id(s.id)
        v = np.array(s.geometry.verts, float).reshape(-1, 3); fa = np.array(s.geometry.faces, int).reshape(-1, 3)
        if len(v):
            k = f"E{s.id}"
            arrays[k + "_v"] = v; arrays[k + "_f"] = fa
            m = mat.get(s.id)
            if m is None:
                for a in path(s.id):
                    if a in mat: m = mat[a]; break
            meta[k] = dict(id=s.id, guid=e.GlobalId, type=e.is_a(), name=e.Name, material=m, path=path(s.id),
                           nv=len(v), nf=len(fa), lo=v.min(0).tolist(), hi=v.max(0).tolist())
        if not it.next(): break
np.savez_compressed(out, **arrays)
json.dump(meta, open(out.replace(".npz", ".json"), "w"), indent=1)
print("MESHES", len(meta))
