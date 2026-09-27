import json, sys
for P in ("box80","plate55"):
    d=json.load(open(f"rail_design_{P}.json")); pr=d['params']
    print("=====",P,"W_B",pr['W_B'],"W_A",pr['W_A'],"DEPTH",pr['DEPTH'],"TAB_R",pr['TAB_R'],"NOTCH",pr['NOTCH_DEPTH'],pr['NOTCH_W'])
    print(" IN",{k:(v['util'],v['section'],v['case'][:34]) for k,v in d['frame']['worst_inplane'].items()})
    print(" COMB",{k:(v['util'],v['tau_torsion'],v['util_with_torsion'],v['section'],v['combo']) for k,v in d['combined'].items()})
    print(" SLS",{k:(v['sag'],v['f1']) for k,v in d['frame']['sls'].items()}, "pin",d['frame']['pin_force_max']['N'],"tip",d['frame']['pin_force_toward_tip_max'],"lock",d['frame']['fold_lock_Fz_max_kN'],d['frame']['fold_lock_Fx_max_kN'],"lower-only",{k:v['max_displacement_mm'] for k,v in d['frame']['lock_lower_only'].items()})
    print(" LOC",{k[:45]:(v['util'] if isinstance(v,dict) else v) for k,v in d['local'].items()})
    c=d['caps']; print(" CAP",c['design_pull_kN'],c['governing_case'],{k[:20]:{q:w for q,w in v.items() if q!='note'} for k,v in c.items() if isinstance(v,dict)}, {k:v for k,v in c.items() if not isinstance(v,dict) and k not in ('design_pull_kN','governing_case')})
    print(" PIN",{k:v for k,v in d['pins'].items()}, "EDGE",d['edges'])
    print(" MASS",d['mass'])
    print(" CLASS",{k:{e:(r['beta'],r['cls'],r['rho']) for e,r in v.items()} for k,v in d['classes'].items()})
    g=d['geometry']; print(" GEO cap",g['cap_pole_min_gap'],"notch/slot",g['tab']['notch_to_slot_min']['gap'],g['tab']['notch_to_own_hole_min'],"fold",g['fold_out'],"base",{k:(v['end_cut_s'],v['end_cut_x_far'],v['end_cut_x_tip'],v['z_far_corner_at_cut'],v['clear_far_corner_to_footplate']) for k,v in g['base_end'].items()},"ext",g['rail_extent_s'])
    for side in ("L","R"): print(" SLOTS",side,[(r['x'],r['up_std_cw'],r['up_steep'],r['lo_std_steep'],r['lo_catwalk'],r['upper_slots_web_between'],r['lower_slots_web_between'],r['vert_between_webs_catwalk'],r['vert_between_webs_standard'],r['vert_between_webs_steep'], min(r[k] for k in r if k.startswith('cap_gap'))) for r in g['slots'][side]])
    for k,v in d['barrier'].items():
        if "5.0" in k or "R143" in k: print(" BAR",k,{z:(v[z]['pin_pull_max_kN'],v[z]['pin_push_max_kN'],v[z]['T_pin_max_kNmm'],v[z]['cap_tension_max_kN'],v[z]['pad_force_max_kN'],v[z]['M_lat_max_kNm'],v[z]['defl_lat_mm']) for z in ('up','lo')}, v['torsion_up'], v['torsion_lo'], [(p['F_up'],p['F_lo'],p['s_vert'],p['L1']) for p in v['poles']][:1])
    print(" NEST", d['nesting'])
