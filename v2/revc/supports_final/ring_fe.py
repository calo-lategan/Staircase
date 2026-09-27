"""Local crushing (ring bending) of the D48.3 x 4 axle tube between the rail hook (6 mm pin leg, saddle over the top of
the tube) and the fork jaws of the jack / landing bracket (notch R 24.5 under the tube, both sides of the hook).
2D ring of 144 beam elements (OpenSees), mean radius 22.15, wall 4, effective length L_eff along the tube.
Top: the contact forces from hook_fe.json (angle, force) applied radially inward at the outer surface.
Bottom: fork seat (U-notch R 24.5, clearance 0.35) as stiff radial springs over +-35 deg about the direction of the
resultant hook load (kept inside 180..360 deg), compression-only (active set).
Check (EN 1993-1-1 / EN 1999-1-1, class 1 rectangle strip): N/N_Rd + M/M_pl,Rd <= 1 with M_pl = f t^2 L / 4.
L_eff = 30 mm (hook 6 + jaws 2 x 8 + gaps, i.e. the tube length between the outer faces of the fork jaws; the
longitudinal spreading beyond the jaws is ignored, conservative). Sensitivity at 20 mm is reported too.
insert=True: solid D40 bar inside (bore 40.3) as a free rigid disc with compression-only radial springs to the wall."""
import json, math, os
import numpy as np
import openseespy.opensees as ops
HERE = os.path.dirname(os.path.abspath(__file__))
RM, T = 22.15, 4.0
MATS = {"steel S355 (EN 10219)": dict(E=210000.0, f=355.0 / 1.0), "6082-T6": dict(E=70000.0, f=250.0 / 1.1)}


def ring(contacts, mat, Leff, nseg=144, seat=None, insert=False):
    """linear ring; fork seat = radial springs over `seat` (deg), compression-only by active-set iteration
    (clearance 0.35 mm concentrates the seat contact: +-35 deg about the bottom is assumed)"""
    E, f = MATS[mat]["E"], MATS[mat]["f"]
    A, I = Leff * T, Leff * T ** 3 / 12
    ang = [2 * math.pi * k / nseg for k in range(nseg)]
    if seat is None:                          # seat centred opposite the resultant hook load, +-35 deg, inside the notch (180..360 deg)
        fx = sum(-F * math.cos(math.radians(a)) for a, F in contacts); fz = sum(-F * math.sin(math.radians(a)) for a, F in contacts)
        c = math.degrees(math.atan2(fz, fx)) % 360; c = min(max(c, 215.0), 325.0); seat = (c - 35.0, c + 35.0)
    active = [k for k, a in enumerate(ang) if seat[0] <= math.degrees(a) <= seat[1]]
    inner = list(range(nseg)) if insert else []
    for it in range(60):
        ops.wipe(); ops.model("basic", "-ndm", 2, "-ndf", 3); ops.geomTransf("Linear", 1)
        for k, a in enumerate(ang): ops.node(k + 1, RM * math.cos(a), RM * math.sin(a))
        for k in range(nseg): ops.element("elasticBeamColumn", k + 1, k + 1, (k + 1) % nseg + 1, A, E, I, 1)
        ops.node(9001, 0.0, 0.0); ops.fix(9001, 1, 1, 1)
        ops.uniaxialMaterial("Elastic", 11, 5.0e4 * 30.0)
        for k in active:                      # seat spring from a fixed point outside the tube to the ring node (compression = bearing)
            ops.node(20000 + k, (RM + 30.0) * math.cos(ang[k]), (RM + 30.0) * math.sin(ang[k])); ops.fix(20000 + k, 1, 1, 1)
            ops.element("Truss", 1000 + k, 20000 + k, k + 1, 1.0, 11)
        if insert:                            # solid D40 insert: rigid disc (free node) with compression-only radial springs to the wall
            ops.node(9004, 0.0, 0.0); ops.fix(9004, 0, 0, 1); ops.uniaxialMaterial("Elastic", 12, 5.0e4 * RM)
            for k in inner: ops.element("Truss", 3000 + k, 9004, k + 1, 1.0, 12)
        ops.node(9002, RM + 50.0, 0.0); ops.fix(9002, 1, 1, 1); ops.uniaxialMaterial("Elastic", 5, 1.0)
        ops.element("Truss", 5000, 1, 9002, 1.0, 5)
        ops.node(9003, 0.0, RM + 50.0); ops.fix(9003, 1, 1, 1); ops.element("Truss", 5001, int(nseg / 4) + 1, 9003, 1.0, 5)
        ops.timeSeries("Linear", 1); ops.pattern("Plain", 1, 1)
        for a_deg, F in contacts:            # F acts on the tube radially inward at angle a_deg (force from the hook)
            k = int(round(math.radians(a_deg) / (2 * math.pi) * nseg)) % nseg; a = ang[k]
            ops.load(k + 1, -F * math.cos(a), -F * math.sin(a), 0.0)
        ops.constraints("Plain"); ops.numberer("RCM"); ops.system("UmfPack"); ops.algorithm("Linear")
        ops.integrator("LoadControl", 1.0); ops.analysis("Static"); ok = ops.analyze(1)
        tens = [k for k in active if ops.eleResponse(1000 + k, "axialForce")[0] > 1e-3]
        tin = [k for k in inner if ops.eleResponse(3000 + k, "axialForce")[0] > 1e-3]
        if not tens and not tin: break
        active = [k for k in active if k not in tens]; inner = [k for k in inner if k not in tin]
    worst = (0, None)
    for k in range(nseg):
        fr = ops.eleResponse(k + 1, "localForce")
        for N, M in ((fr[0], fr[2]), (fr[3], fr[5])):
            u = abs(N) / (A * f) + abs(M) / (f * T * T * Leff / 4)
            s_el = abs(N) / A + abs(M) / (Leff * T * T / 6)
            if u > worst[0]: worst = (u, dict(N=round(N, 1), M=round(M, 1), sigma_elastic=round(s_el, 1), angle=round(math.degrees(ang[k]), 1)))
    ov = ops.nodeDisp(int(nseg / 4) + 1)[1] - ops.nodeDisp(int(3 * nseg / 4) + 1)[1]
    seat_arc = [round(math.degrees(ang[k]), 1) for k in active]
    return dict(ok=ok, util_plastic=round(worst[0], 3), util_elastic=round(worst[1]["sigma_elastic"] / f, 3), at=worst[1],
                ovalisation_mm=round(ov, 3), load=round(sum(F for a, F in contacts), 1), seat_arc=[min(seat_arc), max(seat_arc)], iterations=it + 1, insert=insert)


if __name__ == "__main__":
    H = json.load(open(os.path.join(HERE, "hook_fe.json")))
    out = []
    for h in H:
        if not h["contact"]: continue
        for mat in MATS:
            if h["end"] == "top" and mat.startswith("steel"): continue
            for ins in (False, True):
                for Leff in (30.0, 20.0):
                    r = ring(h["contact"], mat, Leff, insert=ins); r.update(side=h["side"], end=h["end"], case=h["tag"], material=mat, L_eff=Leff)
                    out.append(r)
                    print(f"{h['side']} {h['end']:4s} {mat:22s} insert {ins!s:5s} L {Leff:4.0f} load {r['load']:7.0f} util_pl {r['util_plastic']:.2f} util_el {r['util_elastic']:.2f} oval {r['ovalisation_mm']:.3f} it {r['iterations']} | {h['tag'][:50]}")
    json.dump(out, open(os.path.join(HERE, "ring_fe.json"), "w"), indent=1)
