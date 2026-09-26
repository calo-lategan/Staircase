"""Member axis lines (PCA end points, world mm) of every visible unit-A part per state, with role/variant/side/bone.
blender -b ... --python member_axes.py -- out.json CONFIG ..."""
import bpy, bmesh, sys, types, json
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
out_p, cfgs = a[0], a[1:]
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
for o in bpy.data.objects:
    if o.animation_data:
        for tr in o.animation_data.nla_tracks:
            if tr.name == "Storyline": tr.mute = True
res = {}
for cfg in cfgs:
    m.goto_config(bpy.context, cfg)
    dg = bpy.context.evaluated_depsgraph_get()
    res[cfg] = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.get("unit") != "A" or o.hide_render:
            continue
        mw = o.evaluated_get(dg).matrix_world
        P = np.array([(mw @ v.co)[:] for v in o.data.vertices]) * 1000
        c = P.mean(0); w_, V_ = np.linalg.eigh(np.cov((P - c).T)); U = V_[:, np.argmax(w_)]
        s = (P - c) @ U
        res[cfg][o.name] = dict(role=o.get("role"), variant=o.get("hr_variant"), side=o.get("side"),
                                p0=(c + U * s.min()).tolist(), p1=(c + U * s.max()).tolist(), lo=P.min(0).tolist(), hi=P.max(0).tolist())
json.dump(res, open(out_p, "w"))
print("AXES", {k: len(v) for k, v in res.items()})
