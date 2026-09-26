import sys, collections, json
import ifcopenshell, ifcopenshell.util.element as E, ifcopenshell.util.unit as U
f = ifcopenshell.open(sys.argv[1])
print("schema", f.schema, "length unit scale to metres:", U.calculate_unit_scale(f))
ua = f.by_type("IfcUnitAssignment")[0]
print("units:", [(u.UnitType, getattr(u, "Name", None)) for u in ua.Units][:8])
els = f.by_type("IfcProduct")
c = collections.Counter(e.is_a() for e in els)
print(c.most_common())
names = collections.Counter((e.is_a(), e.Name) for e in els if e.is_a() not in ("IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcProject"))
for (t, n), k in sorted(names.items(), key=lambda kv: -kv[1])[:120]:
    print(f"{k:4d}  {t:<28} {n}")
# hierarchy: aggregates / nesting
agg = f.by_type("IfcRelAggregates")
print("aggregates:", len(agg))
for r in agg[:30]:
    print("  ", r.RelatingObject.is_a(), r.RelatingObject.Name, "->", len(r.RelatedObjects), [o.Name for o in r.RelatedObjects[:6]])
mats = collections.Counter()
for r in f.by_type("IfcRelAssociatesMaterial"):
    m = r.RelatingMaterial
    mats[(m.is_a(), getattr(m, "Name", None))] += len(r.RelatedObjects)
print("materials:", mats.most_common(20))
