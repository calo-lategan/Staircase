import bpy, json, collections
d = json.load(open(r"C:\Users\USER\Desktop\Staircases\idea one\v2\story\story_v3.json"))
def hide_at(o, fr):
    ad = o.animation_data
    if ad:
        for tr in ad.nla_tracks:
            if tr.name == "Storyline":
                for st in tr.strips:
                    cb = None
                    for layer in st.action.layers:
                        for s2 in layer.strips:
                            cb = s2.channelbag(st.action_slot)
                    if cb:
                        for fc in cb.fcurves:
                            if fc.data_path == "hide_render":
                                return fc.evaluate(fr) > 0.5
    return o.hide_render
for name, fr in d["markers"]:
    c = collections.Counter(f'{o.get("unit")}:{o.get("hr_variant")[:3]}:{o.get("side")}' for o in bpy.data.objects
                            if o.type == 'MESH' and o.get("hr_variant") and not hide_at(o, fr + 10))
    print("VIS", name, dict(sorted(c.items())))
