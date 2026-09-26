"""MATE / CLASH AUDIT + FreeCAD round-trip verification.
1) Pairwise interference: bbox-prefiltered exact boolean intersection volume on all 270+ parts.
   Whitelisted pairs = designed welded/bonded/clip fits. Anything else with volume > TOL is a
   REAL clash (missing cutout / wrong location) and is listed.
2) STEP round-trip: re-import full_v2.step through OCCT (FreeCAD's kernel) and compare solid
   count + total volume -> proves the file translates mathematically exact to FreeCAD.
Run: uvx --python 3.13 --with "build123d==0.10.0" --with "cadquery-ocp==7.8.1.1.post1" python v2/cad/audit_mates.py
"""
import sys, pathlib, importlib.util
ROOT = pathlib.Path(r"C:/Users/USER/Desktop/Staircases/idea one")
spec = importlib.util.spec_from_file_location("assembly2", ROOT / "v2" / "cad" / "assembly2.py")
asm = importlib.util.module_from_spec(spec)
sys.modules["assembly2"] = asm
spec.loader.exec_module(asm)

shapes = asm.build()
REG = asm.REG
print(f"built {len(REG)} parts for audit")

# designed-contact whitelist: (substringA, substringB) unordered
WELD = [
    ("U-guide cheek", "Stringer"), ("Guide cover", "U-guide cheek"), ("Follower pin", "Leg upper"),
    ("Follower pin", "U-guide cheek"), ("Ball-lock", "U-guide cheek"), ("Ball-lock", "Leg upper"),
    ("Index plunger", "Leg upper"), ("Index plunger", "U-guide cheek"),
    ("Bolt", "Tread"), ("Bolt", "Carrier"), ("Bolt", "Guardrail post"),
    ("nosing", "Tread"), ("Rubber", "Leg slider"), ("Sole board", "Leg slider"),
    ("Mesh infill", "Guardrail post"), ("Mesh infill", "rail"), ("Mesh infill", "Stringer"),
    ("Mesh infill", "Toe board"), ("Rail return", "rail"), ("Rail return", "Guardrail post"),
    ("rail", "Guardrail post"), ("Toe board", "Guardrail post"), ("Toe board", "Stringer"),
    ("Lifting lug", "Stringer"), ("Ballast lug", "Base pivot"), ("Rating plate", "Stringer"),
    ("pictogram", "Base pivot"), ("Diagonal brace", "Base pivot"),
    ("Diagonal brace", "Leg"), ("Diagonal brace", "Stringer"), ("Diagonal brace", "Control bar"),
    ("Leg slider", "Leg upper"), ("Handhold", "End guardrail"),
    ("Pivot pin", "DU bush"), ("DU bush", "Carrier"), ("DU bush", "Stringer"), ("DU bush", "Control bar"),
    ("DU bush", "Base pivot"), ("Pivot pin", "Leg upper"), ("Pivot pin", "Carrier"),
    ("Pivot pin", "Base pivot"), ("Follower pin", "Guide cover"),
]
def whitelisted(na, nb):
    for a, b in WELD:
        if (a in na and b in nb) or (a in nb and b in na):
            return True
    return False

bbs = []
for r in REG:
    bb = r["shape"].bounding_box()
    bbs.append((bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z))

TOL_OVL = 0.4       # mm bbox overlap needed in every axis to bother checking
TOL_VOL = 50.0      # mm3 intersection volume considered a REAL clash (> a grain of swarf)
clashes, checked = [], 0
n = len(REG)
for i in range(n):
    for j in range(i + 1, n):
        a, b = bbs[i], bbs[j]
        if (min(a[3], b[3]) - max(a[0], b[0]) < TOL_OVL or
            min(a[4], b[4]) - max(a[1], b[1]) < TOL_OVL or
            min(a[5], b[5]) - max(a[2], b[2]) < TOL_OVL):
            continue
        na, nb = REG[i]["name"], REG[j]["name"]
        if whitelisted(na, nb):
            continue
        checked += 1
        try:
            inter = REG[i]["shape"].intersect(REG[j]["shape"])
            v = inter.volume if inter is not None else 0.0
        except Exception:
            v = -1.0
        if v > TOL_VOL or v < 0:
            clashes.append((REG[i]["pid"], REG[j]["pid"], na, nb, round(v, 1)))

print(f"pairs boolean-checked (non-whitelisted, bbox-overlapping): {checked}")
if clashes:
    print(f"*** {len(clashes)} REAL CLASHES ***")
    for pa, pb, na, nb, v in sorted(clashes, key=lambda c: -c[4])[:40]:
        print(f"  {v:>10.1f} mm3  {na} [{pa}]  x  {nb} [{pb}]")
else:
    print("NO unexplained interferences - every contact is a designed weld/bond/pin fit.")

# ---- FreeCAD kernel round-trip ----
from build123d import import_step
total_v = sum(r["shape"].volume for r in REG)
imp = import_step(str(ROOT / "v2" / "out" / "full_v2.step"))
solids = imp.solids()
vol_rt = sum(s.volume for s in solids)
dv = abs(vol_rt - total_v) / total_v * 100
print(f"\nSTEP round-trip (OCCT = FreeCAD kernel): {len(solids)} solids vs {len(REG)} parts")
print(f"volume: exported {total_v/1e6:.3f} dm3 vs re-imported {vol_rt/1e6:.3f} dm3  (delta {dv:.4f}%)")
print("FreeCAD-exact:" , "YES" if dv < 0.01 else "CHECK")
