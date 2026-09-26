p = "build_story_v3.py"
s = open(p, encoding="utf-8").read()
R = []
R.append(("HOLD0, HOLD, LIFT, LIFT_SLOW, MOVE, DOCK, INS, INS_FAST, FINAL = 72, 80, 40, 24, 90, 48, 56, 18, 168",
          "HOLD0, HOLD, LIFT, LIFT_SLOW, MOVE, DOCK, INS, INS_FAST, FINAL = 60, 64, 30, 18, 72, 40, 48, 16, 120\n"
          "DOCK_LEN = {\"wide\": 60, \"double\": DOCK, \"bar\": DOCK}   # the nesting slide gets the most time"))
R.append(('''    if both and lP == "WIDE" and lN == "DOUBLE":
        pts = [pP, pP - Y * DY, Vector((pN.x, pP.y - DY, pN.z + HOOK)), pN + Z * HOOK]
        dock = "double"
    elif both and lP == "DOUBLE" and lN == "WIDE":
        pts = [pP, pP + Z * HOOK, Vector((pP.x, pN.y - DY, pP.z + HOOK)), pN - Y * DY]
        dock = "wide"
    elif both:
        pts = None
    elif arrive:
        if lN == "WIDE":
            pts, dock = [pN - Y * AWAY, pN - Y * DY], "wide"
        else:
            pts, dock = [pN - Y * AWAY + Z * HOOK, pN + Z * HOOK], "double"
    elif leave:
        pts = [pP, pP - Y * DY, pP - Y * AWAY] if lP == "WIDE" else [pP, pP + Z * HOOK, pP - Y * AWAY + Z * HOOK]
    else:''',
 '''    # side-by-side = NESTED: unit B's right rails (25 mm inverted channels) run inside unit A's left 25 mm
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
    else:'''))
R.append(('''    b_delay = 0.4 if cab_out else 0.0            # unit B waits until the cabin has been craned away
    for i in range(MOVE + 1):
        t = i / MOVE
        fr = f1 + i
        a = aP + (aN - aP) * ease(t)''',
 '''    b_delay = 0.4 if cab_out else 0.0            # unit B waits until the cabin has been craned away
    slide_out = leave and lP == "WIDE"           # B must leave A's channels before A may fold or lift
    for i in range(MOVE + 1):
        t = i / MOVE
        fr = f1 + i
        tf = clamp01((t - 0.4) / 0.5) if slide_out else t
        a = aP + (aN - aP) * ease(tf)'''))
R.append(('''        if pts is None:
            bpos = pos_b(N, a) if lN == "DOUBLE" else pos_b(N)
        else:
            bpos = poly(pts, clamp01((t - b_delay) / (1 - b_delay)))''',
 '''        if pts is None:
            bpos = pos_b(N, a) if lN == "DOUBLE" else pos_b(N)
        elif slide_out:                          # 40 % of the move sliding out, the rest carrying B away
            bpos = pts[0].lerp(pts[1], ease(t / 0.4)) if t < 0.4 else pts[1].lerp(pts[2], ease((t - 0.4) / 0.6))
        else:
            bpos = poly(pts, clamp01((t - b_delay) / (1 - b_delay)))'''))
R.append(('''        if lN == "BAR":
            key_loc(A, fr, A0 + Z * HOOK * ease(t))
        if cab_in:
            key_cab(fr, CAB_UP * (1 - ease((t - 0.5) / 0.5)), lN == "BAR")''',
 '''        if lN == "BAR":
            key_loc(A, fr, A0 + Z * HOOK * ease(tf))
        if cab_in:
            key_cab(fr, CAB_UP * (1 - ease((t - 0.55) / 0.45)), lN == "BAR")'''))
R.append(("        set_vis_at(f1 + MOVE // 2, {cab.name: True, tube.name: lN == \"BAR\"})",
          "        set_vis_at(f1 + int(0.55 * MOVE), {cab.name: True, tube.name: lN == \"BAR\"})"))
R.append(('''    if dock:
        pre = {"wide": pN - Y * DY, "double": pN + Z * HOOK}.get(dock)
        for i in range(DOCK + 1):
            t = i / DOCK''',
 '''    if dock:
        DK = DOCK_LEN[dock]
        pre = {"wide": pN + D_N, "double": pN + Z * HOOK}.get(dock)
        for i in range(DK + 1):
            t = i / DK'''))
R.append(('''        key_arm(f2 + DOCK, "A", aN)
        key_arm(f2 + DOCK, "B", angB)
        f3 = f2 + DOCK''',
 '''        key_arm(f2 + DK, "A", aN)
        key_arm(f2 + DK, "B", angB)
        f3 = f2 + DK'''))
R.append(('''        mtxt = ("Unit B slides off the axle pins and moves to the top end" if lP == "WIDE"
                else "Unit B lifts off the top axle and moves alongside")''',
 '''        mtxt = ("Unit B slides out along unit A's channels and moves over the top axle" if lP == "WIDE"
                else "Unit B lifts off the top axle and lines its right rails up with unit A's left channels")'''))
R.append(('''        mtxt = "Unit B removed" + (f" \\u2013 unit A folds {aP:g}\\u00b0 \\u2192 {aN:g}\\u00b0" if aP != aN else "")''',
 '''        mtxt = ("Unit B slides out of unit A's channels and is removed" if lP == "WIDE" else "Unit B removed") \\
            + (f" \\u2013 unit A folds {aP:g}\\u00b0 \\u2192 {aN:g}\\u00b0" if aP != aN else "")'''))
R.append(('''        cap(f2 + 2, f3 + 2, {"wide": "Side-by-side join \\u2013 axle pins engage the neighbouring guide plates",''',
 '''        cap(f2 + 2, f3 + 2, {"wide": "Side-by-side join \\u2013 unit B's right guide rails slide inside unit A's left 25 mm channels",'''))
R.append(('''    cap(f3 + 2, f4 + 6, f"Handrail poles drop into the guide rails \\u2013 steps {lock_txt}")''',
 '''    cap(f3 + 2, f4 + 6, f"One handrail drops through both nested guide rails \\u2013 both units {lock_txt}" if lN == "WIDE"
        else f"Handrail poles drop into the guide rails \\u2013 steps {lock_txt}")'''))
R.append(('''        ds = {"wide": S(("axle", "MainRig_006", "ymin", f3), -12, 20, 0.6),
              "double": S(("axle", "MainRig_010", "ymin", f3), -76, 16, 0.7),
              "bar": S(("axle", "MainRig_010", "ymin", f3), -60, 30, 0.95)}[dock]
        camkeys += [(f2 + 8, ds), (f3, ds)]''',
 '''        if dock == "wide":      # follow the slide from above, then look straight down the channel mouths
            sw = S(("chan", "MainRig_026", "mid", f3), -34, 38, 1.5)
            se = S(("chan", "MainRig_037", "end", f3), -9, 16, 0.5)
            camkeys += [(f2 + 8, sw), (f2 + int(0.45 * DK), sw), (f3 - 12, se), (f3, se)]
        else:
            ds = {"double": S(("axle", "MainRig_010", "ymin", f3), -76, 16, 0.7),
                  "bar": S(("axle", "MainRig_010", "ymin", f3), -60, 30, 0.95)}[dock]
            camkeys += [(f2 + 8, ds), (f3, ds)]'''))
R.append(('''    camkeys += [(f3 + INS_FAST, pole_shot(N, f4)), (f4, pole_shot(N, f4)), (f4 + 30, wide_shot(N, az=-60))]
    if last:
        camkeys += [(f4 + 70, wide_shot(N, az=-50)), (f - 6, S(("site",), 24, 12, 8.0))]
    else:
        camkeys += [(f - 28, wide_shot(N, az=-50))]''',
 '''    camkeys += [(f3 + INS_FAST, pole_shot(N, f4)), (f4, pole_shot(N, f4)), (f4 + 24, wide_shot(N, az=-58))]
    if last:
        camkeys += [(f4 + 56, wide_shot(N, az=-50)), (f - 6, S(("site",), 24, 12, 8.0))]
    else:
        camkeys += [(f - 24, wide_shot(N, az=-52))]'''))
R.append(('''    if kind == "axle":
        return axle_end(a[1], a[2]), 0.0''',
 '''    if kind == "axle":
        return axle_end(a[1], a[2]), 0.0
    if kind == "chan":
        p = wpts(a[1])
        if a[2] == "end":
            xm = max(q.x for q in p)
            p = [q for q in p if q.x > xm - 0.012]
        return sum(p, Vector()) / len(p), 0.0'''))
R.append(('need = sorted({sh["a"][-1] for _, sh in camkeys if sh["a"][0] in ("axle", "pole")})',
          'need = sorted({sh["a"][-1] for _, sh in camkeys if sh["a"][0] in ("axle", "pole", "chan")})'))
R.append(('''        if sh["a"][0] in ("axle", "pole") and sh["a"][-1] == fr:''',
          '''        if sh["a"][0] in ("axle", "pole", "chan") and sh["a"][-1] == fr:'''))
R.append(('''    T, r = frozen[a] if a[0] in ("axle", "pole") else anchor(a)''',
          '''    T, r = frozen[a] if a[0] in ("axle", "pole", "chan") else anchor(a)'''))
R.append(('camkeys += [(1, wide_shot(k0, az=-64)), (HOLD0 - 26, wide_shot(k0, az=-54))]',
          'camkeys += [(1, wide_shot(k0, az=-64)), (HOLD0 - 24, wide_shot(k0, az=-56))]'))
for a, b in R:
    assert a in s, "MISSING: " + a[:90]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("story ok")
