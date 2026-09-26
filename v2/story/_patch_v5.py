"""Storyline v5 edits (user feedback 23 Sep): vertical nesting drop, hooks drop onto the ONE static axle / bar (the
moving unit's own axle is left out), static bar without the cabin, one handrail close-up only, calmer camera,
design colours instead of plain aluminium, brighter environment."""
p = "build_story_v3.py"
s = open(p, encoding="utf-8").read()
R = []

# ---------------------------------------------------------------- colours: the model's own design colours, satin finish
a = s.index("def apply_aluminium():")
b = s.index("def setup_look():")
R.append((s[a:b], '''def apply_colours():
    """the model's own (SketchUp / IFC) part colours, given a satin painted-aluminium finish (object-level copies,
    so the imported materials stay untouched)"""
    made, cnt = {}, 0
    for o in bpy.data.objects:
        if o.type != 'MESH' or not (o.get("unit") in ("A", "B") or o.get("static_bar")):
            continue
        if not o.material_slots:
            continue
        tread = bone_of(o).startswith("Tread") and max(o.dimensions) > 1.0
        for i, sl in enumerate(o.material_slots):
            src = o.data.materials[i] if i < len(o.data.materials) else None
            col = (0.75, 0.76, 0.78)
            if src is not None:
                bs = src.node_tree.nodes.get("Principled BSDF") if src.node_tree else None
                col = tuple(bs.inputs["Base Color"].default_value[:3]) if bs else tuple(src.diffuse_color[:3])
            if o.get("static_bar"):
                col = (0.55, 0.57, 0.58)
            key = (tuple(round(c, 3) for c in col), tread)
            if key not in made:
                made[key] = mat(f"SC paint {len(made):02d}{' tread' if tread else ''}", col, 0.25, 0.42 if tread else 0.34,
                                bump=0.3 if tread else 0.0)
            sl.link = 'OBJECT'
            sl.material = made[key]
        cnt += 1
    return {"objects": cnt, "paints": len(made)}


'''))
R.append(("mat_counts = apply_aluminium()", "mat_counts = apply_colours()"))
# brighter sky, warm paving, warm sun
R.append(("    cr.elements[0].position, cr.elements[0].color = 0.0, (0.20, 0.20, 0.20, 1)\n    cr.elements[1].position, cr.elements[1].color = 1.0, (0.50, 0.58, 0.72, 1)",
          "    cr.elements[0].position, cr.elements[0].color = 0.0, (0.25, 0.23, 0.21, 1)\n    cr.elements[1].position, cr.elements[1].color = 1.0, (0.28, 0.46, 0.78, 1)"))
R.append(("(0.505, (0.88, 0.89, 0.90, 1)), (0.62, (0.72, 0.76, 0.82, 1))", "(0.505, (0.90, 0.91, 0.92, 1)), (0.62, (0.55, 0.68, 0.88, 1))"))
R.append(("    sun.data.energy = 4.0\n    sun.data.color = (1.0, 0.97, 0.92)", "    sun.data.energy = 4.2\n    sun.data.color = (1.0, 0.95, 0.88)"))
R.append(('gm = mat("Site ground (paving)", (0.20, 0.20, 0.19), 0.0, 0.92, bump=0.25, bump_scale=60.0)',
          'gm = mat("Site ground (paving)", (0.36, 0.33, 0.29), 0.0, 0.9, bump=0.25, bump_scale=60.0)'))
# faster EEVEE: no screen-space GI
R.append(("    ee.use_raytracing = True\n    ee.ray_tracing_method = 'PROBE'\n    ee.use_fast_gi = True\n    ee.fast_gi_method = 'GLOBAL_ILLUMINATION'\n    ee.fast_gi_distance = 0.5\n",
          "    ee.use_raytracing = False\n"))
R.append(("    ee.taa_render_samples = 16", "    ee.taa_render_samples = 8"))
R.append(("        gm = mat(", "        gm = mat("))

# ---------------------------------------------------------------- timing / constants
R.append(('DOCK_LEN = {"wide": 60, "double": DOCK, "bar": DOCK}   # the nesting slide gets the most time',
          'DOCK_LEN = {"wide": 48, "double": DOCK, "bar": DOCK}\nNEST_UP = 0.35            # unit B is lowered into the nest from this height'))
# tube is static: never craned; reset at frame 1
R.append(("key_cab(f, 0.0 if k0 in m.CABIN_STATES else CAB_UP, True)",
          "key_cab(f, 0.0 if k0 in m.CABIN_STATES else CAB_UP, False)\nkey_loc(tube, f, TUBE0)"))
AXB, AXA = "UnitB_006", "MainRig_010"
# ---------------------------------------------------------------- MOVE visibility
R.append(('''    mv[tube.name] = lP == "BAR"                 # the hook bar leaves with the cabin
    mv[cab.name] = P in m.CABIN_STATES''',
          '''    mv[tube.name] = lP == "BAR" or lN == "BAR"   # the hook bar is static; it is simply there for the bar state
    mv[cab.name] = P in m.CABIN_STATES
    if lN == "DOUBLE":
        mv["UnitB_006"] = False                  # unit B hooks on with its hooks only: its own bottom axle stays out
    if lN == "BAR":
        mv["MainRig_010"] = False                # the stair hooks on the bar: its own top axle stays out'''))
# ---------------------------------------------------------------- paths: vertical nesting
R.append(('''    # side-by-side = NESTED: unit B's right rails (25 mm inverted channels) run inside unit A's left 25 mm
    # U-channels. Upper and lower channels are stacked, so the only way in or out is lengthwise, along the frame.
    D_P = Matrix.Rotation(math.radians(aP), 3, 'Y') @ m.D_END      # one frame length toward the top end
    D_N = Matrix.Rotation(math.radians(aN), 3, 'Y') @ m.D_END
    W = Y * m.W_SIDE
    if both and lP == "WIDE" and lN == "DOUBLE":
        pts = [pP, pP + D_P, pP + D_P + Z * HOOK, pN + Z * HOOK]   # slide out, lift, shift over the top axle
        dock = "double"
    elif both and lP == "DOUBLE" and lN == "WIDE":
        pts = [pP, pP + Z * HOOK, pP + Z * HOOK - W, pP - W]       # lift off, shift sideways, line up the rails
        dock = "wide"
    elif both:
        pts = None
    elif arrive:
        if lN == "WIDE":
            pts, dock = [pN + D_N - Y * AWAY, pN + D_N], "wide"
        else:
            pts, dock = [pN - Y * AWAY + Z * HOOK, pN + Z * HOOK], "double"
    elif leave:
        pts = [pP, pP + D_P, pP + D_P - Y * AWAY] if lP == "WIDE" else [pP, pP + Z * HOOK, pP - Y * AWAY + Z * HOOK]
    else:''',
          '''    # side-by-side = NESTED: unit B's right rails sit inside unit A's left 25 mm U-channels. B goes in and out
    # vertically (top to bottom), never sliding along the channels.
    W = Y * m.W_SIDE
    if both and lP == "WIDE" and lN == "DOUBLE":
        pts = [pP, pP + Z * NEST_UP, pN - W + Z * HOOK, pN + Z * HOOK]    # lift out, up to the top end, over the axle
        dock = "double"
    elif both and lP == "DOUBLE" and lN == "WIDE":
        pts = [pP, pP + Z * HOOK, pP + Z * HOOK - W, pN + Z * NEST_UP]    # lift off the axle, sideways, above the nest
        dock = "wide"
    elif both:
        pts = None
    elif arrive:
        if lN == "WIDE":
            pts, dock = [pN - Y * AWAY + Z * NEST_UP, pN + Z * NEST_UP], "wide"
        else:
            pts, dock = [pN - Y * AWAY + Z * HOOK, pN + Z * HOOK], "double"
    elif leave:
        pts = [pP, pP + Z * NEST_UP, pP + Z * NEST_UP - Y * AWAY] if lP == "WIDE" else [pP, pP + Z * HOOK, pP - Y * AWAY + Z * HOOK]
    else:'''))
R.append(('''    b_delay = 0.4 if cab_out else 0.0            # unit B waits until the cabin has been craned away
    slide_out = leave and lP == "WIDE"           # B must leave A's channels before A may fold or lift''',
          '''    b_delay = 0.35 if lP == "BAR" else 0.0      # unit B waits until the stair is off the bar
    slide_out = leave and lP == "WIDE"           # B must leave A's channels before A may fold or lift'''))
R.append(('''        tf = clamp01((t - 0.4) / 0.5) if slide_out else t''',
          '''        tf = clamp01((t - 0.45) / 0.4) if (slide_out and lN == "BAR") else clamp01((t - 0.4) / 0.5) if slide_out else t'''))
R.append(('''        if lN == "BAR":
            key_loc(A, fr, A0 + Z * HOOK * ease(tf))''',
          '''        if lN == "BAR":      # step clear of the static bar, fold, lift above it, come back over it
            dx = 0.45 * (ease((t - 0.4) / 0.15) - ease((t - 0.85) / 0.15))
            key_loc(A, fr, A0 + X * dx + Z * HOOK * ease((t - 0.6) / 0.25))
        elif lP == "BAR":    # lift the hooks off the bar, bar goes, lower back
            key_loc(A, fr, A0 + Z * HOOK * (ease(t / 0.2) - ease((t - 0.2) / 0.15)))'''))
R.append(('''    if cab_out:
        set_vis_at(f1 + int(0.4 * MOVE) + 1, {cab.name: False, tube.name: False})
    f2 = f1 + MOVE''',
          '''    if cab_out:
        set_vis_at(f1 + int(0.4 * MOVE) + 1, {cab.name: False})
    if lP == "BAR":
        set_vis_at(f1 + int(0.2 * MOVE), {tube.name: False, "MainRig_010": True})
    if lP == "DOUBLE":                           # B has lifted off: its own bottom axle is back
        set_vis_at(f1 + MOVE // 3, {"UnitB_006": True})
    f2 = f1 + MOVE'''))
R.append(('''        pre = {"wide": pN + D_N, "double": pN + Z * HOOK}.get(dock)''',
          '''        pre = {"wide": pN + Z * NEST_UP, "double": pN + Z * HOOK}.get(dock)'''))
# ---------------------------------------------------------------- captions
R.append(('''        mtxt = ("Unit B slides out along unit A's channels and moves over the top axle" if lP == "WIDE"
                else "Unit B lifts off the top axle and lines its right rails up with unit A's left channels")''',
          '''        mtxt = ("Unit B lifts out of unit A's channels and moves over the top axle" if lP == "WIDE"
                else "Unit B lifts off the top axle and moves over unit A's left channels")'''))
R.append(('''        if cab_out:
            mtxt = "Cabin craned away \\u2013 " + mtxt[0].lower() + mtxt[1:]''',
          '''        if lP == "BAR":
            mtxt = "Stair lifts its hooks off the bar \\u2013 " + mtxt[0].lower() + mtxt[1:]'''))
R.append(('''        mtxt = ("Unit B slides out of unit A's channels and is removed" if lP == "WIDE" else "Unit B removed") \\
            + (f" \\u2013 unit A folds {aP:g}\\u00b0 \\u2192 {aN:g}\\u00b0" if aP != aN else "")''',
          '''        mtxt = ("Unit B lifts out of unit A's channels and is removed" if lP == "WIDE" else "Unit B removed") \\
            + (f" \\u2013 unit A folds {aP:g}\\u00b0 \\u2192 {aN:g}\\u00b0" if aP != aN else "") \\
            + (" and moves over the static bar" if lN == "BAR" else "")'''))
R.append(('''        cap(f2 + 2, f3 + 2, {"wide": "Side-by-side join \\u2013 unit B's right guide rails slide inside unit A's left 25 mm channels",
                             "double": "End-to-end join \\u2013 unit B's guide plates hook over unit A's top axle",
                             "bar": "Top axle hooks onto the cabin's static bar under the door sill"}[dock])''',
          '''        cap(f2 + 2, f3 + 2, {"wide": "Side-by-side join \\u2013 unit B drops in from above: its right guide rails sit inside unit A's left channels",
                             "double": "End-to-end join \\u2013 unit B's hooks drop onto unit A's top axle (unit B's own bottom axle stays out)",
                             "bar": "Top hooks drop onto the static bar (the stair's own top axle stays out)"}[dock])'''))
# ---------------------------------------------------------------- camera: calmer, one handrail close-up
R.append(('''    camkeys += [(T - 2, pole_shot(P, T, close=False)), (T + LIFT_SLOW + 6, pole_shot(P, T, close=False)),
                (f1 + 26, ms), (f2 - (22 if dock else 16), ms)]
    if dock:
        if dock == "wide":      # follow the slide from above, then look straight down the channel mouths
            sw = S(("chan", "MainRig_026", "mid", f3), -34, 38, 1.5)
            se = S(("chan", "MainRig_037", "end", f3), -9, 16, 0.5)
            camkeys += [(f2 + 8, sw), (f2 + int(0.45 * DK), sw), (f3 - 12, se), (f3, se)]
        else:
            ds = {"double": S(("axle", "MainRig_010", "ymin", f3), -76, 16, 0.7),
                  "bar": S(("axle", "MainRig_010", "ymin", f3), -60, 30, 0.95)}[dock]
            camkeys += [(f2 + 8, ds), (f3, ds)]
    camkeys += [(f3 + INS_FAST, pole_shot(N, f4)), (f4, pole_shot(N, f4)), (f4 + 24, wide_shot(N, az=-58))]
    if last:
        camkeys += [(f4 + 56, wide_shot(N, az=-50)), (f - 6, S(("site",), 24, 12, 8.0))]
    else:
        camkeys += [(f - 24, wide_shot(N, az=-52))]''',
          '''    close_ins = (P, N) == ("DOUBLE_STANDARD", "WIDE_STANDARD")     # the one handrail close-up of the film
    camkeys += [(T + 6, wide_shot(P, az=-52)), (f1 + 22, ms), (f2 - (18 if dock else 10), ms)]
    if dock:
        if dock == "wide":      # look along the channel mouths while unit B is lowered in
            camkeys += [(f2 + 10, S(("chan", "MainRig_037", "end", f3), -14, 20, 0.95)),
                        (f3 - 8, S(("chan", "MainRig_037", "end", f3), -10, 17, 0.6)), (f3, S(("chan", "MainRig_037", "end", f3), -10, 17, 0.6))]
        else:
            ds = {"double": S(("axle", "MainRig_010", "ymin", f3), -76, 16, 0.75),
                  "bar": S(("fixed", (TUBE0.x, 45.0, TUBE0.z)), -60, 28, 1.0)}[dock]
            camkeys += [(f2 + 10, ds), (f3, ds)]
    if close_ins:
        camkeys += [(f3 + INS_FAST, pole_shot(N, f4)), (f4, pole_shot(N, f4)), (f4 + 26, wide_shot(N, az=-58))]
    else:
        camkeys += [(f3 + 28, wide_shot(N, az=-58))]
    if last:
        camkeys += [(f4 + 56, wide_shot(N, az=-50)), (f - 6, S(("site",), 24, 12, 8.0))]
    else:
        camkeys += [(f - 20, wide_shot(N, az=-52))]'''))
# ---------------------------------------------------------------- anchors: rails (always visible) instead of axles
R.append(('''AX = {"A": ("MainRig_006", "MainRig_010"), "B": ("UnitB_006", "UnitB_010")}''',
          '''AX = {"A": ("MainRig_006", "MainRig_010"), "B": ("UnitB_006", "UnitB_010")}
RAILS = {"A": ("MainRig_179", "MainRig_037"), "B": ("UnitB_179", "UnitB_037")}'''))
R.append(('''    if kind == "fold":
        e0, e1 = (axle_end(n, "ymin") for n in AX[a[1]])
        return (e0 + e1) / 2 + Z * 0.35, 0.0''',
          '''    if kind == "fixed":
        return Vector(a[1]), 0.0
    if kind == "fold":
        p = wpts(RAILS[a[1]][1])
        c = sum(p, Vector()) / len(p)
        return Vector((c.x, min(q.y for q in p), c.z)) + Z * 0.35, 0.0'''))
R.append(('''        for u in a[1]:
            if bpy.data.objects[AX[u][0]].hide_render:
                continue
            for n in AX[u]:
                for w in ("ymin", "ymax"):
                    q = axle_end(n, w)
                    pts += [q, q + Z * 1.2]''',
          '''        for u in a[1]:
            if bpy.data.objects[RAILS[u][0]].hide_render:
                continue
            for n in RAILS[u]:
                p = wpts(n)
                for q in (min(p, key=lambda v: v.x), max(p, key=lambda v: v.x)):
                    pts += [q, q + Z * 1.2]'''))
for x, y in R:
    assert x in s, "MISSING: " + x[:100]
    s = s.replace(x, y)
open(p, "w", encoding="utf-8").write(s)

u = "staircase_ui.py"
t = open(u, encoding="utf-8").read()
t = t.replace('CABIN_STATES = {"SINGLE_STANDARD", "SINGLE_BAR"}', 'CABIN_STATES = {"SINGLE_STANDARD"}')
a = '''    if cab:
        set_vis(cab, sc.staircase_config in CABIN_STATES)'''
assert a in t
t = t.replace(a, a + '''
    # hooking on uses the ONE static axle / bar: the hooking unit's own axle is left out
    axb, axa = bpy.data.objects.get("UnitB_006"), bpy.data.objects.get("MainRig_010")
    if axb and layout == "DOUBLE":
        set_vis(axb, False)
    if axa and layout == "BAR":
        set_vis(axa, False)''')
open(u, "w", encoding="utf-8").write(t)
print("v5 patched")
