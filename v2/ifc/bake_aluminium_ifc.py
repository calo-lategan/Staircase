"""Bake the aluminium material into the staircase IFC (all staircase parts = EN AW-6082-T6).

Input : v2/out/Latest 21-09-2026/final STEP LADDER 22-9-2026.ifc          (left untouched)
Output: v2/out/Latest 21-09-2026/final STEP LADDER 22-9-2026 - ALUMINIUM.ifc

For every staircase element (everything except the toilet cabin, which keeps its own finishes):
  * one IfcMaterial "Aluminium EN AW-6082-T6" replaces the SketchUp colour materials
    (IfcRelAssociatesMaterial), with material property sets:
      Pset_MaterialCommon      MassDensity 2700 kg/m3
      Pset_MaterialMechanical  YoungModulus 70 GPa, ShearModulus 27 GPa, PoissonRatio 0.3, alpha 23e-6 /K
      Pset_MaterialThermal     ThermalConductivity 170 W/mK, SpecificHeatCapacity 900 J/kgK
      Pset_AluminiumAlloy_EN   EN 573-3 designation, temper, f0 / fu (EN 1999-1-1 Tab. 3.2b), gamma_M1, finish
  * an aluminium IfcSurfaceStyle (METAL reflectance) is attached to the material
    (IfcMaterialDefinitionRepresentation) AND to every body item of the element (IfcStyledItem),
    so viewers show aluminium and BIM tools read the grade.
Run: uvx --with ifcopenshell python v2/ifc/bake_aluminium_ifc.py
"""
import os, json, collections, multiprocessing
import ifcopenshell, ifcopenshell.api, ifcopenshell.geom, ifcopenshell.util.element as E

SRC = r"C:\Users\USER\Desktop\Staircases\idea one\v2\out\Latest 21-09-2026\final STEP LADDER 22-9-2026.ifc"
DST = SRC.replace(".ifc", " - ALUMINIUM.ifc")
HERE = os.path.dirname(os.path.abspath(__file__))
f = ifcopenshell.open(SRC)
run = ifcopenshell.api.run

# ---------------------------------------------------------------- 1. classify: staircase vs cabin (by world position)
st = ifcopenshell.geom.settings()
st.set("use-world-coords", True)
centre = {}
it = ifcopenshell.geom.iterator(st, f, multiprocessing.cpu_count())
if it.initialize():
    while True:
        sh = it.get()
        v = sh.geometry.verts
        if v:
            xs = v[0::3]
            centre[sh.id] = (min(xs) + max(xs)) / 2
        if not it.next():
            break


def cls(e):
    if e.id() in centre:
        x = centre[e.id()]
        return "cabin" if x < -50 else "stair" if x > 4 else "other"
    kids = [c for r in getattr(e, "IsDecomposedBy", []) for c in r.RelatedObjects]
    ks = {cls(k) for k in kids}
    return "stair" if "stair" in ks else "cabin" if "cabin" in ks else "other"


prods = f.by_type("IfcBuildingElementProxy")
groups = collections.defaultdict(list)
for e in prods:
    groups[cls(e)].append(e)
stair = groups["stair"]

# ---------------------------------------------------------------- 2. material + properties + style
mat = run("material.add_material", f, name="Aluminium EN AW-6082-T6", category="aluminium")
mat.Description = "Wrought aluminium alloy EN AW-6082 (AlSi1MgMn), temper T6, EN 573-3 / EN 755-2; design to EN 1999-1-1"
psets = {
    "Pset_MaterialCommon": {"MassDensity": 2700.0},
    "Pset_MaterialMechanical": {"YoungModulus": 70.0e9, "ShearModulus": 27.0e9, "PoissonRatio": 0.3,
                                "ThermalExpansionCoefficient": 23.0e-6},
    "Pset_MaterialThermal": {"ThermalConductivity": 170.0, "SpecificHeatCapacity": 900.0},
    "Pset_AluminiumAlloy_EN": {
        "Designation": "EN AW-6082", "ChemicalDesignation": "EN AW-AlSi1MgMn", "Temper": "T6",
        "ProductStandard": "EN 755-2 extrusions / EN 485-2 plate", "DesignStandard": "EN 1999-1-1",
        "ProofStrength_f0_t_le_5mm_MPa": 260.0, "UltimateStrength_fu_t_le_5mm_MPa": 310.0,
        "ProofStrength_f0_t_gt_5mm_MPa": 250.0, "UltimateStrength_fu_t_gt_5mm_MPa": 290.0,
        "HAZ_Factor_rho_o_haz": 0.48, "PartialFactor_gamma_M1": 1.10, "PartialFactor_gamma_M2": 1.25,
        "BucklingClass": "A", "Finish": "Clear anodised 20 um (EN ISO 7599 AA20); treads mill finish, serrated",
        "Recyclable": True},
}
for name, props in psets.items():
    ps = run("pset.add_pset", f, product=mat, name=name)
    run("pset.edit_pset", f, pset=ps, properties=props)

body = [c for c in f.by_type("IfcGeometricRepresentationSubContext") if c.ContextIdentifier == "Body"][0]
style = run("style.add_style", f, name="Aluminium EN AW-6082-T6 clear anodised")
run("style.add_surface_style", f, style=style, ifc_class="IfcSurfaceStyleShading",
    attributes={"SurfaceColour": {"Name": None, "Red": 0.80, "Green": 0.81, "Blue": 0.83}, "Transparency": 0.0})
run("style.add_surface_style", f, style=style, ifc_class="IfcSurfaceStyleRendering",
    attributes={"SurfaceColour": {"Name": None, "Red": 0.80, "Green": 0.81, "Blue": 0.83}, "Transparency": 0.0,
                "ReflectanceMethod": "METAL",
                "SpecularColour": {"Name": None, "Red": 0.9, "Green": 0.9, "Blue": 0.92},
                "SpecularHighlight": {"IfcSpecularRoughness": 0.3}})
run("style.assign_material_style", f, material=mat, style=style, context=body)

# ---------------------------------------------------------------- 3. assign to every staircase element
run("material.unassign_material", f, products=stair)
run("material.assign_material", f, products=stair, type="IfcMaterial", material=mat)
styled = {si.Item.id(): si for si in f.by_type("IfcStyledItem") if si.Item}
n_restyle = n_new = 0
for e in stair:
    if not e.Representation:
        continue
    for rep in e.Representation.Representations:
        if rep.RepresentationIdentifier != "Body":
            continue
        for item in rep.Items:
            si = styled.get(item.id())
            if si:
                si.Styles = (style,)
                n_restyle += 1
            else:
                f.createIfcStyledItem(item, (style,), None)
                n_new += 1

# remove IfcMaterials that no element uses any more (the old SketchUp colours on the stair)
n_rm = 0
for m in list(f.by_type("IfcMaterial")):
    if m == mat:
        continue
    if not any(r.is_a("IfcRelAssociatesMaterial") for r in f.get_inverse(m)):
        for inv in list(f.get_inverse(m)):
            if inv.is_a("IfcMaterialDefinitionRepresentation") or inv.is_a("IfcMaterialProperties"):
                f.remove(inv)
        f.remove(m)
        n_rm += 1

f.write(DST)

# ---------------------------------------------------------------- 4. verify by re-reading the written file
g = ifcopenshell.open(DST)
chk = collections.Counter()
for e in g.by_type("IfcBuildingElementProxy"):
    ms = E.get_material(e)
    chk[ms.Name if ms else None] += 1
m2 = [m for m in g.by_type("IfcMaterial") if m.Name == "Aluminium EN AW-6082-T6"][0]
props = {p.Name: {q.Name: q.NominalValue.wrappedValue for q in p.Properties} for p in m2.HasProperties}
out = dict(src=SRC, dst=DST, elements=len(prods), classes={k: len(v) for k, v in groups.items()},
           restyled_items=n_restyle, new_styled_items=n_new, removed_unused_materials=n_rm,
           material_count_after=dict(chk.most_common(6)), material_psets=props,
           material_has_style=bool(m2.HasRepresentation))
json.dump(out, open(os.path.join(HERE, "bake_aluminium_ifc.json"), "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != "material_psets"}, indent=1, default=str))
