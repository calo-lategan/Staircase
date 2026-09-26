"""Storyline v6 - fixes from the frame QA: handrails lift out of frame (no pop), bar extends into place, unit B
arrives from further away, camera pulls back before handrails drop (only T5 is a handrail close-up), T5 close-up
on a middle pole, slower camera approaches, ground edge hidden."""
p = "build_story_v3.py"
s = open(p, encoding="utf-8").read()
R = []
R.append(("RAISE, PIN, HOOK, AWAY, DY, CAB_UP = 1.5, 0.15, 0.25, 3.0, 0.30, 7.0",
          "RAISE, PIN, HOOK, AWAY, DY, CAB_UP = 4.0, 0.15, 0.25, 5.0, 0.30, 7.0\nPULL = 26                 # camera pulls back after a joint closes, before the handrails come down"))
# ground: bigger plane, world ground colour = paving colour
R.append(("        s = 400.0\n", "        s = 2500.0\n"))
R.append(("    cr.elements[0].position, cr.elements[0].color = 0.0, (0.25, 0.23, 0.21, 1)",
          "    cr.elements[0].position, cr.elements[0].color = 0.0, (0.36, 0.33, 0.29, 1)"))
R.append(("(0.495, (0.30, 0.30, 0.29, 1)), (0.505,", "(0.495, (0.36, 0.33, 0.29, 1)), (0.505,"))
# bar: extends into place / retracts (object scale along its length) instead of popping
R.append(("key_loc(tube, f, TUBE0)", "key_loc(tube, f, TUBE0)\ntube.scale = (1, 1, 0.001)\ntube.keyframe_insert(\"scale\", frame=f)"))
R.append(('''    mv[tube.name] = lP == "BAR" or lN == "BAR"   # the hook bar is static; it is simply there for the bar state''',
          '''    mv[tube.name] = lP == "BAR" or lN == "BAR"   # the hook bar is static; it is simply there for the bar state
    if lN == "BAR":                              # the bar extends into place while the handrails come out
        set_vis_at(T, {tube.name: True})
        tube.scale = (1, 1, 0.001); tube.keyframe_insert("scale", frame=T)
        tube.scale = (1, 1, 1.0); tube.keyframe_insert("scale", frame=T + 28)'''))
R.append(('''    if lP == "BAR":
        set_vis_at(f1 + int(0.2 * MOVE), {tube.name: False, "MainRig_010": True})''',
          '''    if lP == "BAR":                              # the stair lifts off, the bar retracts, the stair's own axle goes back in
        tube.scale = (1, 1, 1.0); tube.keyframe_insert("scale", frame=f1 + int(0.2 * MOVE))
        tube.scale = (1, 1, 0.001); tube.keyframe_insert("scale", frame=f1 + int(0.2 * MOVE) + 22)
        set_vis_at(f1 + int(0.2 * MOVE) + 22, {tube.name: False})
        set_vis_at(f1 + int(0.2 * MOVE), {"MainRig_010": True})'''))
# pause after a joint closes (camera pulls back), then the handrails drop
R.append(('''    # ---- INSERT: handrails of N drop in (fast to 150 mm, then slow into the guide rails)
    set_vis_at(f3, VIS[N])
    for i in range(INS + 1):
        for u in "AB":
            for s in "RL":
                key_lift(f3 + i, u, s, base(N, u, s) + drop_profile(i / INS))
    f4 = f3 + INS''',
          '''    # ---- INSERT: handrails of N drop in (fast to 150 mm, then slow into the guide rails)
    f3d = f3                                     # joint closed
    f3 = f3 + (PULL if dock else 12)             # camera settles before the handrails come down
    key_arm(f3, "A", aN)
    key_arm(f3, "B", angB)
    set_vis_at(f3, VIS[N])
    for i in range(INS + 1):
        for u in "AB":
            for s in "RL":
                key_lift(f3 + i, u, s, base(N, u, s) + drop_profile(i / INS))
    f4 = f3 + INS'''))
# the dock camera anchors are frozen at the moment the joint is closed
R.append(('''            camkeys += [(f2 + 10, S(("chan", "MainRig_037", "end", f3), -14, 20, 0.95)),
                        (f3 - 8, S(("chan", "MainRig_037", "end", f3), -10, 17, 0.6)), (f3, S(("chan", "MainRig_037", "end", f3), -10, 17, 0.6))]''',
          '''            camkeys += [(f2 + 16, S(("chan", "MainRig_037", "end", f3d), -14, 20, 0.95)),
                        (f3d - 6, S(("chan", "MainRig_037", "end", f3d), -10, 17, 0.62)), (f3d, S(("chan", "MainRig_037", "end", f3d), -10, 17, 0.62))]'''))
R.append(('''            ds = {"double": S(("axle", "MainRig_010", "ymin", f3), -76, 16, 0.75),
                  "bar": S(("fixed", (TUBE0.x, 45.0, TUBE0.z)), -60, 28, 1.0)}[dock]
            camkeys += [(f2 + 10, ds), (f3, ds)]''',
          '''            ds = {"double": S(("axle", "MainRig_010", "ymin", f3d), -76, 16, 0.75),
                  "bar": S(("fixed", (TUBE0.x, 45.0, TUBE0.z)), -60, 28, 1.0)}[dock]
            camkeys += [(f2 + 16, ds), (f3d, ds)]'''))
R.append(('''    camkeys += [(T + 6, wide_shot(P, az=-52)), (f1 + 22, ms), (f2 - (18 if dock else 10), ms)]''',
          '''    camkeys += [(T + 6, wide_shot(P, az=-52)), (f1 + 22, ms), (f2 - (30 if dock else 10), ms)]'''))
R.append(('''    if close_ins:
        camkeys += [(f3 + INS_FAST, pole_shot(N, f4)), (f4, pole_shot(N, f4)), (f4 + 26, wide_shot(N, az=-58))]
    else:
        camkeys += [(f3 + 28, wide_shot(N, az=-58))]
    if last:
        camkeys += [(f4 + 56, wide_shot(N, az=-50)), (f - 6, S(("site",), 24, 12, 8.0))]
    else:
        camkeys += [(f - 20, wide_shot(N, az=-52))]''',
          '''    if close_ins:            # the one handrail close-up: a pole in the middle of the flight, through both nested rails
        camkeys += [(f3 + INS_FAST, pole_shot(N, f4)), (f4, pole_shot(N, f4)), (f4 + 46, wide_shot(N, az=-58))]
    else:
        camkeys += [(f3 - 2, wide_shot(N, az=-58))]
    if last:
        camkeys += [(f4 + 56, wide_shot(N, az=-50)), (f - 6, S(("site",), 24, 12, 8.0))]
    elif not close_ins:
        camkeys += [(f - 20, wide_shot(N, az=-52))]'''))
R.append(('''    if lay(k) == "WIDE":           # inner side between the units, seen from the bottom end
        role = "toppost" if k == "WIDE_CATWALK_MINI" else "mini"
        return S(("pole", "A", "L", lock, role, "max_x", at), -16, 30 if close else 28, 0.75 if close else 1.35)''',
          '''    if lay(k) == "WIDE":           # a pole in the middle of the flight at the nested join, from the front, above the steps
        role = "toppost" if k == "WIDE_CATWALK_MINI" else "mini"
        return S(("pole", "A", "L", lock, role, "mid", at), -24, 32 if close else 28, 1.15 if close else 1.35)'''))
# the hold after the T5 close-up is a little longer so the pull-out is gentle
R.append(('''    f = f4 + (FINAL if last else HOLD)''', '''    f = f4 + (FINAL if last else HOLD + (16 if (P, N) == ("DOUBLE_STANDARD", "WIDE_STANDARD") else 0))'''))
# fold shots a little higher (keeps the horizon out)
R.append(('''        ms = S(("fold", "B"), -78, 12, 2.2)''', '''        ms = S(("fold", "B"), -78, 20, 2.3)'''))
R.append(('''        ms = S(("fold", "A"), -76, 12, 2.2)''', '''        ms = S(("fold", "A"), -76, 20, 2.3)'''))
for x, y in R:
    assert x in s, "MISSING: " + x[:90]
    s = s.replace(x, y)
# tube scale keys: keep them LINEAR like the rest (push_to_nla handles it)
open(p, "w", encoding="utf-8").write(s)
print("v6 patched")
