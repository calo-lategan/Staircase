import bpy, sys, types
t = bpy.data.texts["staircase_ui.py"]
m = types.ModuleType("staircase_ui_live"); sys.modules["staircase_ui_live"] = m
exec(compile(t.as_string(), "staircase_ui.py", "exec"), m.__dict__)
ctx = bpy.context
o = bpy.data.objects["HRS_B_040"]; c = bpy.data.objects["HRC_B_015"] if "HRC_B_015" in bpy.data.objects else None
for ob in (o, c):
    if not ob: continue
    ad = ob.animation_data
    print("OBJ", ob.name, "action", ad.action.name if ad and ad.action else None, "tracks", [(t.name, t.mute, [s.name for s in t.strips]) for t in ad.nla_tracks] if ad else None,
          "drivers", [d.data_path for d in ad.drivers] if ad else None, "hide", ob.hide_render, ob.hide_viewport, "cons", [x.type for x in ob.constraints])
for tr in [t for ob in bpy.data.objects if ob.animation_data for t in ob.animation_data.nla_tracks if t.name == "Storyline"]:
    tr.mute = True
m.goto_config(ctx, "DOUBLE_CATWALK")
print("after goto", o.hide_render, c.hide_render if c else None, "cfg", ctx.scene.staircase_config, "hr_on", ctx.scene.staircase_handrail_on)
ctx.evaluated_depsgraph_get()
print("after dg", o.hide_render, c.hide_render if c else None)
print("B side modes", [m.side_mode(ctx.scene, "B", s, "DOUBLE") for s in "RL"], "lock", m.lock_of(m.current_angle("B")))
