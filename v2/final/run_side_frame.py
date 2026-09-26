import json, math, sys
import numpy as np
import openseespy.opensees as ops
import side_frame as SF
C = json.load(open("tread2_cases.json"))
def pf(case, side, only=None):
    p = C[case]["pins"]; r, f = p[f"{side}_rear"], p[f"{side}_front"]
    return {i: ({"rear": (-r[0], -r[2]), "front": (-f[0], -f[2])} if (only is None or i in only) else {"rear": (0, 0), "front": (0, 0)}) for i in range(6)}
def summary(out, applied_fz):
    Rx = out["reactions"]["base"][0] + out["reactions"]["top"][0]; Rz = out["reactions"]["base"][1] + out["reactions"]["top"][1]
    s = f"ok={out['ok']} base {[round(v) for v in out['reactions']['base']]} top {[round(v) for v in out['reactions']['top']]} | sumRx {Rx:.1f} sumRz {Rz:.0f} (applied {applied_fz:.0f}) | max|uz| {out['disp_max'][0]:.2f} mm"
    return s
if __name__ == "__main__":
    for side in ("L", "R"):
        for rig in (True, False):
            forces = pf("ULS crowd", side)
            out = SF.run(side, forces, bracket_rigid=rig, label="ULS crowd")
            app = -sum(f["rear"][1] + f["front"][1] for f in forces.values())
            print(f"\n=== side {side}, brackets {'rigid' if rig else 'pinned'}: {summary(out, app)}")
            for key in ("lo", "up"):
                rows = out[f"rail_{key}"]; Mm = max(rows, key=lambda r: max(abs(r[2]), abs(r[3])))
                print(f"   rail {key}: |M|max {max(abs(Mm[2]), abs(Mm[3])):8.0f} Nmm at s={Mm[0]:.0f} (N {Mm[1]:7.0f}) | N {min(r[1] for r in rows):7.0f}..{max(r[1] for r in rows):7.0f}")
            print("   links:", {k: round(v) for k, v in out["links"].items()})
            pm = out["pole_forces"]
            print("   poles max |M|", round(max(max(abs(p[4]), abs(p[5])) for p in pm)), "max |V|", round(max(abs(p[3]) for p in pm)), "max |N|", round(max(abs(p[2]) for p in pm)))
