import bpy
from mathutils import Vector
out = []
def walk(c, d=0):
    objs = c.objects
    lo = [1e9]*3; hi = [-1e9]*3
    for o in objs:
        if o.type == 'MESH':
            for v in o.bound_box:
                w = o.matrix_world @ Vector(v)
                for i in range(3): lo[i] = min(lo[i], w[i]); hi[i] = max(hi[i], w[i])
    out.append("  "*d + f"{c.name}: {len(objs)} objs hide_render={getattr(c,'hide_render',None)} bb={[round(x,2) for x in lo]}..{[round(x,2) for x in hi]}")
    for ch in c.children: walk(ch, d+1)
walk(bpy.context.scene.collection)
lc = bpy.context.view_layer.layer_collection
def lwalk(l, d=0):
    out.append("  "*d + f"[LC] {l.name} exclude={l.exclude} hide_vp={l.hide_viewport}")
    for ch in l.children: lwalk(ch, d+1)
lwalk(lc)
out.append("scenes: " + ", ".join(s.name for s in bpy.data.scenes))
out.append("materials: %d %s" % (len(bpy.data.materials), [m.name for m in bpy.data.materials][:40]))
out.append("orphan-ish objects not in scene: %d" % len([o for o in bpy.data.objects if not o.users_scene]))
open("_probe4.txt","w").write("\n".join(out))
