"""Re-save the final model (FINAL_standard.blend, the owner's 26 Sep clean-up) as IFC.

The .blend was built from the 25 Sep IFC by build_blend.py: one object per IFC element, same vertices, and each object carries
the element's GlobalId. The clean-up only deleted objects (no object was moved, rotated, scaled or reshaped; checked below),
so the faithful IFC is the 25 Sep IFC with exactly those elements removed. That keeps every IFC entity, material, type and
GlobalId as the owner's SketchUp export wrote them. Elements whose IFC geometry can't be meshed (zero-thickness faces) were
never in the .blend and are kept unchanged.

Run with Blender's Python module (bpy >= 5.0, the .blend was saved by Blender 5.1) and ifcopenshell:
    python3 blend_to_ifc.py
Output: FINAL_standard.ifc and blend_to_ifc.json (what was removed and the checks)."""
import json, os
import numpy as np
import bpy
import ifcopenshell, ifcopenshell.api, ifcopenshell.geom

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "out", "Latest 21-09-2026", "25.9.2026 final STEP LADDER-standard.ifc")
BLEND = os.path.join(HERE, "FINAL_standard.blend")
OUT = os.path.join(HERE, "FINAL_standard.ifc")

bpy.ops.wm.open_mainfile(filepath=BLEND)
M = json.load(open(os.path.join(HERE, "final_meshes.json"))); Z = np.load(os.path.join(HERE, "final_meshes.npz"))
by_guid = {m["guid"]: k for k, m in M.items()}
kept, reshaped, moved = set(), [], []
for o in bpy.data.objects:
    if o.type != "MESH": continue
    g = o["guid"]; k = by_guid[g]; kept.add(g)
    v = np.array([p.co[:] for p in o.data.vertices]); v0 = Z[k + "_v"]
    if v.shape != v0.shape or np.abs(v - v0).max() > 1e-6: reshaped.append(o.name)
    if any(abs(x) > 1e-9 for x in o.location) or any(abs(x) > 1e-9 for x in o.rotation_euler) or any(abs(s - 1) > 1e-9 for s in o.scale):
        moved.append(o.name)
if reshaped or moved:
    raise SystemExit(f"blend has edited geometry ({len(reshaped)} reshaped, {len(moved)} moved): export the meshes instead")
removed = sorted(m["guid"] for m in M.values() if m["guid"] not in kept)

f = ifcopenshell.open(SRC)
before = [p for p in f.by_type("IfcProduct") if p.Representation]
log = []
for g in removed:
    e = f.by_guid(g)
    log.append(dict(guid=g, id=e.id(), name=e.Name, material=M[by_guid[g]]["material"], lo=M[by_guid[g]]["lo"], hi=M[by_guid[g]]["hi"]))
    ifcopenshell.api.run("root.remove_product", f, product=e)
f.write(OUT)

g2 = ifcopenshell.open(OUT)
after = [p for p in g2.by_type("IfcProduct") if p.Representation]
mesh_guids = {m["guid"] for m in M.values()}
unmeshable = [p.GlobalId for p in after if p.GlobalId not in mesh_guids]
check = dict(source=os.path.basename(SRC), blend=os.path.basename(BLEND), out=os.path.basename(OUT),
             products_before=len(before), removed=len(removed), products_after=len(after),
             blend_objects=len(kept), unmeshable_kept=len(unmeshable),
             matches_blend=len(after) == len(kept) + len(unmeshable) and set(p.GlobalId for p in after) - set(unmeshable) == kept,
             reshaped=len(reshaped), moved=len(moved), removed_elements=log)
json.dump(check, open(os.path.join(HERE, "blend_to_ifc.json"), "w"), indent=1)
print({k: v for k, v in check.items() if k != "removed_elements"})
