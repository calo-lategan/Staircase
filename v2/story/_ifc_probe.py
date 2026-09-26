import ifcopenshell, ifcopenshell.util.placement as P, collections, sys
f = ifcopenshell.open(r"C:\Users\USER\Desktop\Staircases\idea one\v2\out\Latest 21-09-2026\final STEP LADDER 22-9-2026.ifc")
print(f.schema, "entities", len(list(f)))
c = collections.Counter(e.is_a() for e in f.by_type("IfcProduct"))
print(c.most_common(30))
print("materials", [(m.id(), m.Name) for m in f.by_type("IfcMaterial")][:30])
print("styles", len(f.by_type("IfcSurfaceStyle")), [s.Name for s in f.by_type("IfcSurfaceStyle")][:20])
print("relmat", len(f.by_type("IfcRelAssociatesMaterial")))
for t in ("IfcBuildingElementProxy","IfcElementAssembly","IfcBuilding","IfcSpace","IfcDoor","IfcWall","IfcSlab","IfcRoof","IfcWindow","IfcStair","IfcMember","IfcPlate","IfcRailing","IfcBeam","IfcColumn","IfcCovering"):
    try: es = f.by_type(t)
    except: continue
    if es: print(t, len(es), [e.Name for e in es[:8]])
