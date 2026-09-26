import codecs
p = "build_brief.py"
s = open(p, encoding="utf-8").read()
a = s.index("COMPLY = [")
b = s.index("\n]\n", a) + 3
new = '''COMPLY = [
    ("R3", "Clear width 1,100 (industry anchor)", "1,023 between handrails, unchanged: confirm by crowd-flow calculation", "open"),
    ("R4 R5", "Going \\u2265 250 with riser \\u2264 175", "Unchanged 250 / 175 on the standard stair (at the limit)", "pass"),
    ("R6", "Closed risers preferred", "Lip part-closes each riser (#1); preferred, not required", "part"),
    ("R7", "Open gap between steps \\u2264 120 (100 rec)", "100 mm with the 35 mm lip (#1)", "pass"),
    ("R8", "2 \\u00d7 rise + going 540\\u2013660 (guidance only)", "600", "pass"),
    ("R9", "Pitch \\u2264 35\\u00b0", "Standard 35\\u00b0; steep 49.4\\u00b0 is crew-only", "part"),
    ("R10 R13 R14 R15", "Landings sized by the flow calculation, \\u2265 gangway width", "Where flights join or the catwalk is used as a landing: set on the site layout", "site"),
    ("R11", "Headroom \\u2265 2,100", "Site layout", "site"),
    ("R12", "Uniform risers, also with connecting stairs", "Walking surface kept at the same height (#1); check the step at the end-to-end joint", "part"),
    ("R16 R94", "Slip PTV \\u2265 36 (40 events)", "Serrated top; pendulum test on the finished step", "test"),
    ("R17", "55 mm contrasting nosings, both edges", "#1", "pass"),
    ("R18 R109", "Centre rail preferred over 28\\u00b0 and 1,800 wide", "Not fitted by decision (#12): accept through the venue risk assessment", "part"),
    ("R19 R64 R71 R72", "Handrail: grip 25\\u201350, 300 past ends, closed, continuous", "Change 7 is still to be decided", "open"),
    ("R48", "Deck gap \\u2264 25", "20 mm (#1)", "pass"),
    ("R63 R69", "Top rail \\u2265 1,100, both sides, full length", "1,127 both sides, unchanged; circular padding added on top", "pass"),
    ("R65 R68", "No gap in the side over 470 (\\u2264 100 mesh for the public)", "About 1,000 mm below the handrail without a middle rail (#8); the scaffold edge protection or \\u2264 100 mm mesh must cover it", "site"),
    ("R66", "Toe board 150", "Not fitted (#9): cover on site where the edge is open", "site"),
    ("R67", "Handrail clear of objects \\u2265 50", "About 95 mm off the poles, unchanged", "pass"),
    ("R70", "Child rail about 600", "Not fitted (#8): site / scaffold", "site"),
    ("R73 R74\\u2013R77", "Footplates, base jacks, plumb 1:100, bracing, bearing", "Scaffold scope (#11); the engineer gives the unit\\u2019s support reactions", "site"),
    ("R78 R104", "Positive, captive locking, no unintended release", "Pins are the pole ends (#5); a latch so a handrail can\\u2019t lift out is still to design", "open"),
    ("R90", "Effective going: going + 15 mm nosing", "285 step on a 250 going: 35 mm overlap", "pass"),
    ("R93", "ID and rating plate", "After finalisation (#13)", "open"),
    ("R95", "No finger traps in moving joints", "The 20 mm gap between steps closes while folding: procedure, or 298-deep steps", "open"),
    ("R96", "Instruction manual and method statement", "To write with the final design", "open"),
    ("R103 R108", "Module joins: gap \\u2264 25, level within 4", "Nested join 5 mm, same level; double join 19 mm", "pass"),
    ("R106", "Post spacing (1.2 m for class C)", "305 mm: a pole at every step", "pass"),
    ("R113 R128 R115 R180", "Crowd 7.5 kN/m\\u00b2 (stairs and platforms), span/250, < 10 mm under one person, pattern loads", "Checked for #1\\u2013#3 with load patterns; holds if those changes are adopted and the flat catwalk has a middle support", "cond"),
    ("R114", "4 kN on one step", "0.83 (#1)", "pass"),
    ("R116 R176", "Sideways crowd load and 10 % sway on the whole stair", "Into the hooks and the scaffold: engineer to check", "open"),
    ("R142 R179 R143", "Barrier 3.0 kN/m, post 1.5 kN, rail point 1.25 kN", "Only with the pole thickness in #4 and a pin section that carries it", "part"),
    ("R142", "Barrier 5.0 kN/m where people gather to watch", "Not covered", "open"),
    ("R150 R170", "Connections: crowd uplift and tie-down", "Top hooks 10 mm (#10); hooks resting on the axle need a keeper against lifting; pole-pin holes in the 25 mm rail to check", "part"),
    ("R153 R169", "Partial factors 1.35 G + 1.5 Q", "All utilisations in this brief are factored this way", "pass"),
    ("R163", "Aluminium EN AW-6082-T6", "All parts", "pass"),
    ("R165 R166", "Independent design check; load test 1.2\\u00d7", "For the final design", "test"),
    ("R173 R98", "Edge protection class", "Class C for the 35\\u00b0 stair, class A for the flat catwalk; the 49.4\\u00b0 steep setting is outside EN 13374 (crew only)", "test"),
    ("R177", "f\\u2081 \\u2265 6 Hz vertical, \\u2265 1.5 Hz sway", "Stiffer rails raise f\\u2081; confirm both on the scaffold", "open"),
    ("R178", "1.0 kN/m downwards on the top rail", "Top rail unchanged, 305 mm between poles: passes easily; matters more because the padding invites sitting", "pass"),
    ("R181", "Storm overturning (no people)", "Site wind check with the scaffold ties", "site"),
]
'''
s = s[:a] + new + s[b:]
R = [
    ('why=[("R113", "Stairs and platforms must carry 7.5 kN/m\\u00b2 of crowd."), ("R115", "Deflection no more than span/250 (7.3 mm) under the crowd.")],',
     'why=[("R113 R128", "Stairs and platforms (the catwalk) must carry 7.5 kN/m\\u00b2 of crowd."), ("R115", "Deflection no more than span/250 (7.3 mm) under the crowd, under 10 mm for one person."), ("R180", "Uneven crowds: one part loaded, the rest empty.")],'),
    ('("R64", "Graspable rail 25\\u201350 mm (a round profile)."),', '("R64", "Grip size 25\\u201350 mm (40 target)."),'),
    ('"R65/R68 (no gap over 470 mm) and R70 (child rail ~600) are then not met by the unit: the side needs another answer, e.g. mesh infill or the scaffold\\u2019s edge protection."',
     '"R65/R68 (no gap over 470 mm; mesh \\u2264 100 mm for the public) and R70 (child rail ~600) are then not met by the unit: the scaffold\\u2019s edge protection or \\u2264 100 mm mesh must cover the side."'),
    ('"R109 only prefers a centre rail on stairs over 28\\u00b0 and 1.8 m wide: accept via the venue risk assessment."',
     '"R109 prefers a centre rail (and assist elements) on stairs over 28\\u00b0 and 1.8 m wide, which a side-by-side pair is: accept through the venue risk assessment."'),
    ('"R78 R104 met by the pole-pins; add a latch so a handrail can\\u2019t lift out by accident."',
     '"R78 R104: the pole-pins lock the steps; a latch so a handrail can\\u2019t lift out by accident is still to design."'),
    ('ST_LBL = {"pass": "Pass", "part": "Partly", "test": "Test", "open": "Open"}',
     'ST_LBL = {"pass": "Pass", "part": "Partly", "test": "Test", "open": "Open", "site": "Site / scaffold", "cond": "If adopted"}'),
    (".st.none {{ color:var(--ink2); background:var(--soft); }}",
     ".st.none, .st.site {{ color:var(--ink2); background:var(--soft); }}\n.st.cond {{ color:var(--accent); background:var(--accentbg); }}"),
]
for x, y in R:
    x = codecs.decode(x, "unicode_escape") if chr(92) + "u" in x else x
    assert x in s, "MISSING " + x[:80]
    s = s.replace(x, y)
open(p, "w", encoding="utf-8").write(s)
print("audit fixes applied")
