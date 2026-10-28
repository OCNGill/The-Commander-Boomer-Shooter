"""
edi_audit.py — deterministic scene audit. No vision model, no opinions.
Prints every object's world-space bounding box, tri count, material, and
checks the assembled figure for gaps/overlaps. Run:
    blender -b -P edi_audit.py
"""
import bpy, os, sys, json

print("=" * 100)
print("EDI SCENE AUDIT — deterministic")
print("=" * 100)

rows = []
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data
    # world-space bbox
    corners = [ob.matrix_world @ v.co for v in me.vertices] if me.vertices else []
    if not corners:
        rows.append((ob.name, 0, 0, None, None, []))
        continue
    xs = [c.x for c in corners]; ys = [c.y for c in corners]; zs = [c.z for c in corners]
    bb = (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    mats = [m.name for m in me.materials if m]
    rows.append((ob.name, len(me.vertices), tris, bb, mats, corners))

rows.sort(key=lambda r: r[0])
print(f"{'OBJECT':26s} {'VERTS':>7} {'TRIS':>7}  {'XMIN':>7} {'YMIN':>7} {'ZMIN':>7}  {'XMAX':>7} {'YMAX':>7} {'ZMAX':>7}  MATERIALS")
for name, nv, tris, bb, mats, _ in rows:
    if bb:
        print(f"{name:26s} {nv:7d} {tris:7d}  {bb[0]:7.3f} {bb[1]:7.3f} {bb[2]:7.3f}  "
              f"{bb[3]:7.3f} {bb[4]:7.3f} {bb[5]:7.3f}  {','.join(mats) or 'NONE'}")
    else:
        print(f"{name:26s} {nv:7d} {tris:7d}  {'-- empty --':^52s}")

tot_tris = sum(r[2] for r in rows)
print(f"\nTOTAL MESHES: {len(rows)}   TOTAL BASE TRIS: {tot_tris}")

# ---- expected anatomy landmarks for a 1.70 m figure
print("\n" + "=" * 100)
print("ANATOMY SANITY CHECK (expected world Z for a 1.70 m build)")
print("=" * 100)
expect = {
    "EDI_Head":      (1.47, 1.71),
    "EDI_Neck":      (1.49, 1.62),
    "EDI_Torso":     (0.90, 1.51),
    "EDI_Palm_R":    (0.88, 0.98),
    "EDI_Foot_L":    (0.03, 0.10),
}
for name, (zlo, zhi) in expect.items():
    hit = next((r for r in rows if r[0] == name), None)
    if not hit or not hit[3]:
        print(f"  {name:16s} MISSING")
        continue
    bb = hit[3]
    ok = (bb[2] >= zlo - 0.06) and (bb[5] <= zhi + 0.06)
    print(f"  {name:16s} z {bb[2]:.3f}..{bb[5]:.3f}   expected {zlo:.2f}..{zhi:.2f}   {'PASS' if ok else 'FAIL'}")
    # width sanity
    w = bb[3] - bb[0]
    print(f"  {'':16s} width(X) = {w:.3f} m")

# ---- head size check (the v01 bug: 2 m skull)
head = next((r for r in rows if r[0] == "EDI_Head"), None)
if head and head[3]:
    bb = head[3]
    hw, hh = bb[3] - bb[0], bb[5] - bb[2]
    verdict = "PASS" if (0.14 < hw < 0.22 and 0.20 < hh < 0.30) else "FAIL"
    print(f"\n  HEAD SIZE: {hw*1000:.0f} mm wide x {hh*1000:.0f} mm tall -> {verdict} "
          f"(human head ~175 x 235 mm)")

# ---- body connectivity: every part must touch SOME other part (transitive)
print("\n" + "=" * 100)
print("ASSEMBLY OVERLAP CHECK (each part must intersect at least one other)")
print("=" * 100)
BODY = {"EDI_Torso", "EDI_Neck", "EDI_Head", "EDI_Hair"}
parts = [(r[0], r[3]) for r in rows if r[3] and not r[0].startswith(("EDI_Smoke", "EDI_Cigarette",
                                                                    "EDI_Ember", "EDI_Ash",
                                                                    "EDI_ZipPull", "EDI_Ring"))]
def bbs_overlap(a, b, pad=0.035):
    return not (a[3] < b[0]-pad or a[0] > b[3]+pad or
                a[4] < b[1]-pad or a[1] > b[4]+pad or
                a[5] < b[2]-pad or a[2] > b[5]+pad)

# transitive closure over the body
adj = {n: set() for n, _ in parts}
for i, (na, ba) in enumerate(parts):
    for nb, bb in parts[i+1:]:
        if bbs_overlap(ba, bb):
            adj[na].add(nb); adj[nb].add(na)

seen, comps = set(), []
for n in adj:
    if n in seen: continue
    stack, comp = [n], []
    while stack:
        c = stack.pop()
        if c in seen: continue
        seen.add(c); comp.append(c)
        stack.extend(adj[c] - seen)
    comps.append(sorted(comp))

for i, c in enumerate(comps):
    tag = "MAIN BODY" if any(x in BODY for x in c) else f"CLUSTER {i}"
    print(f"  [{tag}] {len(c)} parts")
    if tag != "MAIN BODY":
        print(f"      -> {c}")
main = max(comps, key=len)
print(f"\n  MAIN BODY = {len(main)} parts   DETACHED CLUSTERS = {len(comps)-1}  "
      f"-> {'PASS' if len(comps)==1 else 'REVIEW'}")

print("\n" + "=" * 100)
print("AUDIT COMPLETE")
print("=" * 100)
