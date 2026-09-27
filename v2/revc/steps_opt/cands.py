"""Full-case FE of the candidate steps (all 8 load cases).  python3 cands.py NAME"""
import sys, json, os
import stepfe as s
BASE = {"slot_dir": "x", "rib_through_box": True, "ws": 10.0, "wsol": 8.0, "Ls": 40.0, "Lbx": 10.0, "b_r": 12.0}
C = {
 "C1 optimum (greedy, tight)": {**BASE, "tb": 3.0, "tb_bot": 3.0, "tb_top": 2.5, "ts": 2.0, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0,
                                 "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [8.0, 3.0], "t_cap": 6.0},
 "C2 recommended (margin)": {**BASE, "tb": 3.0, "tb_bot": 3.5, "tb_top": 3.0, "ts": 2.0, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0,
                              "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [10.0, 3.0], "t_cap": 6.0},
 "C3 flat ribs 3 mm (no bulb)": {**BASE, "tb": 3.0, "tb_bot": 3.5, "tb_top": 3.0, "ts": 2.0, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0,
                              "nose_type": "box", "p_r": 50.0, "tr": 3.0, "bulb": None, "t_cap": 6.0},
 "C4 T-bar grating 20 pitch": {"mode": "grating", "rib_through_box": True, "tb": 3.0, "tb_bot": 3.5, "tb_top": 3.0, "ts": 2.0, "tn": 2.0,
                              "tn_bot": 2.0, "tn_top": 2.0, "nose_type": "box", "p_r": 20.0, "tr": 2.0, "bulb": [6.0, 2.0],
                              "bar_top": [10.0, 2.0], "rods": [100.0, 150.0, 200.0], "rod_d": 5.0, "t_cap": 6.0},
 "C6 extruded box with diagonal web (no diaphragms)": {**BASE, "rib_through_box": False, "box_diag": 2.5, "tb": 2.5, "tb_front": 4.0, "tb_bot": 3.5, "tb_top": 3.0,
                              "ts": 2.0, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0, "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [10.0, 3.0], "t_cap": 6.0},
 "C8 recommended production: closed box + diagonal, bulb 12": {**BASE, "rib_through_box": False, "box_diag": 2.5, "tb": 2.5, "tb_front": 4.0, "tb_bot": 3.5, "tb_top": 3.0,
                              "ts": 2.0, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0, "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [12.0, 3.0], "t_cap": 6.0},
 "C9 as C8 with 2.5 mm skin (extruder-safe)": {**BASE, "rib_through_box": False, "box_diag": 2.5, "tb": 2.5, "tb_front": 4.0, "tb_bot": 3.5, "tb_top": 3.0,
                              "ts": 2.5, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0, "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [12.0, 3.0], "t_cap": 6.0},
 "C7 owner option: 30 mm lip, 3 mm nosing walls, 2.5 box": {**BASE, "tb": 2.5, "tb_bot": 2.5, "tb_top": 2.5, "ts": 2.0, "tn": 3.0, "tn_bot": 2.0, "tn_top": 2.0,
                              "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [8.0, 3.0], "t_cap": 6.0, "lip": 30.0},
 "C5 owner option: 30 mm nosing lip, lighter box": {**BASE, "tb": 2.5, "tb_bot": 2.5, "tb_top": 2.5, "ts": 2.0, "tn": 2.0, "tn_bot": 2.0, "tn_top": 2.0,
                              "nose_type": "box", "p_r": 50.0, "tr": 2.0, "bulb": [8.0, 3.0], "t_cap": 6.0, "lip": 30.0},
}
if __name__ == "__main__":
    name = [k for k in C if k.startswith(sys.argv[1])][0]
    cases = sys.argv[2:] or list(s.CASES)
    r = s.run({**s.DEFAULT, **C[name]}, cases)
    fn = "cands.json"
    out = {}
    tag = name.split()[0]
    json.dump(dict(name=name, D=C[name], cases=r), open(f"cand_{tag}.json", "w"), indent=1, default=str)
