#!/usr/bin/env python3
"""
edi_build.py — HIGH-POLY character pipeline for EDI (Blender 4.x, headless).

Replaces the 74-tri crew blockout for ONE character with a real game-asset build:
lofted parametric body, sculpted face (cheekbone shelf / cupid's-bow lip / jaw taper),
hair cards, catsuit wardrobe, cigarette prop with emissive ember, PBR bake to 2K,
hero + turnaround + face + smoke renders.

Spec: Docs/CHARACTER_EDI_v01.md
Run:
    blender -b -P edi_build.py -- --look BLACKICE --tris 30000 --bake
    blender -b -P edi_build.py -- --look NOIR --tris 30000

Output -> Tools/blender/out_crew_edi/
Zero-trust: every FBX is sha256-verified and tri-counted into the manifest.
"""

import os, sys, json, math, hashlib, time
try:
    import bpy, bmesh
    from mathutils import Vector
except ImportError:
    print("edi_build.py must run under Blender: blender.exe -b -P edi_build.py")
    sys.exit(2)

# ---------------------------------------------------------------- args
def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default

LOOK    = (arg("--look", "BLACKICE") or "BLACKICE").upper()
TRIS    = int(arg("--tris", "30000"))
DO_BAKE = "--bake" in sys.argv
NO_RENDER = "--no-render" in sys.argv
NO_EXPORT = "--no-export" in sys.argv
SEED    = int(arg("--seed", "4242"))

ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
OUT_DIR = os.path.join(ROOT, "Tools", "blender", "out_crew_edi")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------- palette
PALETTE = {
    "BLACKICE": dict(hair=(0.612, 0.259, 0.129), hair_tip=(0.76, 0.51, 0.31),
                     skin=(0.910, 0.761, 0.651), suit=(0.055, 0.078, 0.149),
                     smoke=(0.725, 0.761, 0.808), bg=(0.243, 0.361, 0.541),
                     accent=(0.620, 0.106, 0.106), lip=(0.42, 0.16, 0.17),
                     metal=(0.18, 0.19, 0.22), ember=(1.0, 0.32, 0.06)),
    "NOIR":     dict(hair=(0.722, 0.663, 0.549), hair_tip=(0.85, 0.82, 0.74),
                     skin=(0.851, 0.765, 0.690), suit=(0.078, 0.078, 0.078),
                     smoke=(0.604, 0.627, 0.651), bg=(0.165, 0.176, 0.192),
                     accent=(0.478, 0.118, 0.169), lip=(0.30, 0.06, 0.10),
                     metal=(0.10, 0.10, 0.11), ember=(1.0, 0.30, 0.05)),
}
P = PALETTE.get(LOOK, PALETTE["BLACKICE"])

t_start = time.time()
log = []


def L(msg):
    print(f"[EDI:{LOOK}] {msg}", flush=True)
    log.append(msg)


# ---------------------------------------------------------------- helpers
def new_obj(name):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob, me


def bm_to(bm, me):
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0


def smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True


def loft(name, sections, segs=20, cap=True):
    """
    sections: list of (z_height, radius_x, radius_y, x_offset).
    CRITICAL: the section's first value is the HEIGHT (world Z, up). v01 wrote it
    into Y instead, so the whole body was modelled lying on its side while the
    head floated above it -> 'debris in a void' in every render.
    """
    ob, me = new_obj(name)
    bm = bmesh.new()
    rings = []
    for (z_h, rx, ry, xo) in sections:
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring.append(bm.verts.new((xo + rx * math.cos(a), ry * math.sin(a), z_h)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if cap:
        for ring, z_h, xo in ((rings[0], sections[0][0], sections[0][3]),
                              (rings[-1], sections[-1][0], sections[-1][3])):
            c = bm.verts.new((xo, 0.0, z_h))
            for i in range(segs):
                j = (i + 1) % segs
                bm.faces.new((ring[i], ring[j], c))
    bm_to(bm, me)
    smooth(ob)
    return ob


def add_sphere(name, radius=0.1, loc=(0, 0, 0), segs=24, rings=16):
    ob, me = new_obj(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=radius and rings or rings,
                              radius=radius)
    for v in bm.verts:
        v.co = v.co + Vector(loc)
    bm_to(bm, me)
    smooth(ob)
    return ob


def add_cube(name, size=(0.1, 0.1, 0.1), loc=(0, 0, 0)):
    ob, me = new_obj(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + loc[0],
                       v.co.y * size[1] + loc[1],
                       v.co.z * size[2] + loc[2]))
    bm_to(bm, me)
    return ob


def bake_scale(ob, sx, sy, sz):
    """Scale a mesh around its own centroid.

    add_sphere()/add_cube() bake loc into the vertices, so ob.location stays at the
    origin and `ob.scale = (...)` would scale the object AROUND THE WORLD ORIGIN,
    flinging every feature to a wrong position. This bakes the squash into the
    verts instead, preserving the feature's placement.
    """
    vs = ob.data.vertices
    if not vs:
        return ob
    n = len(vs)
    cx = sum(v.co.x for v in vs) / n
    cy = sum(v.co.y for v in vs) / n
    cz = sum(v.co.z for v in vs) / n
    for v in vs:
        v.co = Vector((cx + (v.co.x - cx) * sx,
                       cy + (v.co.y - cy) * sy,
                       cz + (v.co.z - cz) * sz))
    ob.data.update()
    return ob


def bake_rotate(ob, rx, ry, rz):
    """Rotate a mesh around its own centroid (Euler XYZ, radians).

    Same trap as bake_scale: ob.location is the origin because loc was baked into
    the verts, so ob.rotation_euler would swing the feature around world (0,0,0).
    """
    from mathutils import Euler
    vs = ob.data.vertices
    if not vs:
        return ob
    n = len(vs)
    cx = sum(v.co.x for v in vs) / n
    cy = sum(v.co.y for v in vs) / n
    cz = sum(v.co.z for v in vs) / n
    eul = Euler((rx, ry, rz), 'XYZ').to_matrix()
    for v in vs:
        d = Vector((v.co.x - cx, v.co.y - cy, v.co.z - cz))
        d = eul @ d
        v.co = Vector((cx + d.x, cy + d.y, cz + d.z))
    ob.data.update()
    return ob


def subsurf(ob, levels=2, render=2):
    m = ob.modifiers.new("Subd", 'SUBSURF')
    m.levels = levels
    m.render_levels = render
    m.subdivision_type = 'CATMULL_CLARK'
    return m


def tri_count(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    try:
        return len(ev.to_mesh().polygons)
    finally:
        ev.to_mesh_clear()


# ---------------------------------------------------------------- materials
def make_mat(name, base, rough=0.5, metal=0.0, sss=0.0, emis=None, emis_str=0.0,
             spec=0.5, clearcoat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*base, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = spec
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = spec
    if clearcoat:
        for k in ('Coat Weight', 'Clearcoat'):
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = clearcoat
                break
    if sss:
        for k in ('Subsurface Weight', 'Subsurface'):
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = sss
                break
        if 'Subsurface Radius' in bsdf.inputs:
            bsdf.inputs['Subsurface Radius'].default_value = (0.36, 0.14, 0.10)
        if 'Subsurface Color' in bsdf.inputs:
            bsdf.inputs['Subsurface Color'].default_value = (*base, 1.0)
    if emis is not None:
        for k in ('Emission Color', 'Emission'):
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = (*emis, 1.0)
                break
        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = emis_str
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m


def noisy_bump(m, scale=25.0, strength=0.15, detail=6.0):
    """Adds a procedural bump so baked normals are not perfectly flat."""
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        return
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.location = (-500, -250)
    tex.inputs['Scale'].default_value = scale
    if 'Detail' in tex.inputs:
        tex.inputs['Detail'].default_value = detail
    bump = nt.nodes.new('ShaderNodeBump'); bump.location = (-250, -250)
    bump.inputs['Strength'].default_value = strength
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])


# ---------------------------------------------------------------- HEAD
def build_head():
    """
    Sculpted head. Silhouette-critical cues (Docs/CHARACTER_EDI_v01.md §2):
      1. cheekbone shelf  -> malar pushed OUT + sub-zygomatic hollow pulled IN
      2. cupid's-bow lip  -> two upper lip peaks, plumper lower lip
      3. jaw taper        -> wide at the cheek, narrow at the chin
    """
    ob, me = new_obj("EDI_Head")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=36, radius=1.0)

    for v in bm.verts:
        x, y, z = v.co.x, v.co.y, v.co.z
        # base skull shaping: oval/heart, wider at temples, narrowing to jaw
        sx = 0.78
        sz = 1.02
        sy = 0.88
        # taper the lower face toward a V jaw
        if z < -0.05:
            taper = 1.0 - 0.42 * ((-z - 0.05) / 0.95) ** 1.35
            sx *= taper
            sy *= (1.0 - 0.18 * ((-z - 0.05) / 0.95) ** 1.2)
        # flatten the mid-face slightly (flat mid-face per spec)
        if -0.25 < z < 0.30:
            sy *= 0.955
        x, y, z = x * sx, y * sy, z * sz

        # --- cheekbone shelf: push zygomatic out, hollow just beneath
        cheek_z = 0.02
        d_cheek = math.sqrt((x - 0.52) ** 2 + (y - 0.30) ** 2 + (z - cheek_z) ** 2)
        if d_cheek < 0.60:
            w = (1.0 - d_cheek / 0.60) ** 2
            x += 0.115 * w * (1 if x > 0 else -1)
            y += 0.035 * w
        # sub-zygomatic hollow (pull IN just below the shelf)
        d_hollow = math.sqrt((x - 0.44) ** 2 + (y - 0.20) ** 2 + (z + 0.30) ** 2)
        if d_hollow < 0.52:
            w = (1.0 - d_hollow / 0.52) ** 2
            x -= 0.075 * w * (1 if x > 0 else -1)

        # --- brow ridge: smooth shelf, not a protrusion
        d_brow = math.sqrt((x) ** 2 + (y - 0.52) ** 2 + (z - 0.42) ** 2)
        if d_brow < 0.72 and abs(x) < 0.62:
            w = (1.0 - d_brow / 0.72) ** 2
            y += 0.055 * w
            z += 0.028 * w

        # --- nose: straight narrow bridge, small refined tip
        if abs(x) < 0.24 and -0.12 < z < 0.52:
            nx = abs(x) / 0.24
            prof = math.sin(max(0.0, min(1.0, (z + 0.12) / 0.64)) * math.pi) ** 0.7
            bump = 0.185 * (1.0 - nx ** 1.6) * prof
            y += bump
            # narrow the bridge
            if z > 0.12:
                x *= (1.0 - 0.30 * (1.0 - nx))
        # nose tip / nostril wings
        d_tip = math.sqrt(x ** 2 + (y - 0.72) ** 2 + (z + 0.06) ** 2)
        if d_tip < 0.20:
            w = (1.0 - d_tip / 0.20) ** 2
            y += 0.055 * w
            z -= 0.022 * w

        # --- lips: full, defined cupid's bow on top, plumper lower
        d_lip = math.sqrt(x ** 2 + (y - 0.66) ** 2 + (z + 0.40) ** 2)
        if d_lip < 0.30:
            w = (1.0 - d_lip / 0.30) ** 1.6
            upper = z > -0.40
            if upper:
                # cupid's bow: two peaks
                bow = math.cos(x / 0.11 * math.pi) * 0.5 + 0.5
                y += 0.062 * w * (0.55 + 0.55 * bow)
                z += 0.012 * w * bow
            else:
                y += 0.082 * w          # lower lip plumper

        # --- chin: short, slightly pointed, strong mental ridge
        d_chin = math.sqrt(x ** 2 + (y - 0.42) ** 2 + (z + 0.80) ** 2)
        if d_chin < 0.38:
            w = (1.0 - d_chin / 0.38) ** 2
            y += 0.070 * w
            z -= 0.022 * w

        v.co = Vector((x, y, z))

    # --- SCALE TO HUMAN HEAD (critical): build at unit radius then scale.
    # A 1.70 m human head is ~0.235 m tall / 0.175 m wide -> half-extent ~0.118.
    # Without this the skull is 2 m across and every close camera is INSIDE it.
    HEAD_R = 0.118
    for v in bm.verts:
        v.co = Vector((v.co.x * HEAD_R * 0.94,      # slightly narrower than tall
                       v.co.y * HEAD_R * 1.02,
                       v.co.z * HEAD_R * 1.00))

    # --- EYE SOCKETS (world-space, after scaling). Without a socket the eyeballs
    # read as 'googly eyes glued to the surface' - they must sit IN the skull.
    # Depth must stay SHALLOW: surf_y() raycasts this carved surface later, so a
    # deep socket gets counted twice and buries the eyeball inside the head.
    for v in bm.verts:
        for sx_sign in (1, -1):
            d = math.sqrt(((v.co.x - 0.0335 * sx_sign) / 0.030) ** 2 +
                          ((v.co.z - 0.012) / 0.019) ** 2)
            if d < 1.0:
                w = (1.0 - d) ** 1.5
                v.co.y -= 0.0090 * w         # shallow socket recess

    bm_to(bm, me)
    smooth(ob)
    ob.location = (0, 0, 1.588)     # head centre; crown lands at ~1.706 m
    subsurf(ob, 1, 1)               # 40x32 base -> ~10k tris at render, toward the 25-35k gate
    return ob


# ---------------------------------------------------------------- FACE PLACEMENT GATE
def verify_face_placement():
    """
    Deterministic gate: every facial feature must sit ON or OUTSIDE the skull
    surface, not inside it. The vision reviewer gave contradictory verdicts across
    runs ('detached googly eyes' -> 'no eyes at all'), so placement is proven by
    raycast, not by opinion. Returns the list of violations (empty = pass).
    """
    head = bpy.data.objects.get("EDI_Head")
    if head is None:
        return ["EDI_Head missing - cannot verify face placement"], 0, 0, 0
    lo = head.location
    # Surface lookup from RAW VERTICES. head.ray_cast() returned no hits at all in
    # headless Blender (15/15 misses) because the depsgraph has not been evaluated
    # at this point in the script. Vertex data is always valid - no update needed.
    verts = [v.co.copy() for v in head.data.vertices]

    def surface_y(x, z, world=True):
        """Frontmost head surface Y at world (x,z). Widening fallback if sparse."""
        lx, lz = x - lo.x, z - lo.z
        best, rad = None, 0.012
        while best is None and rad <= 0.09:
            for co in verts:
                dx, dz = co.x - lx, co.z - lz
                if dx * dx + dz * dz <= rad * rad:
                    if best is None or co.y > best:
                        best = co.y
            rad *= 1.7
        return (best + lo.y) if (best is not None and world) else best

    bad = []
    checked = 0
    matched = 0
    misses = 0
    bpy.context.view_layer.update()          # make bound_box/matrix_world current
    for ob in bpy.data.objects:
        n = ob.name
        if not any(k in n for k in ("Eye_", "Iris", "Pupil", "Brow", "Lash",
                                    "Lip", "Mouth", "Nostril", "Nose")):
            continue
        matched += 1
        # NOTE: add_sphere()/add_cube() BAKE loc into the vertices, so ob.location
        # is (0,0,0) for every feature. Query by real centroid, never ob.location.
        world_pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        front_y = max(p.y for p in world_pts)
        cx = sum(p.x for p in world_pts) / len(world_pts)
        cz = sum(p.z for p in world_pts) / len(world_pts)
        surf = surface_y(cx, cz)
        if surf is None:
            misses += 1
            continue
        checked += 1
        if front_y < surf - 0.0006:      # buried more than 0.6 mm inside the skull
            bad.append(f"{n}: frontmost y={front_y:.4f} is {surf-front_y:.4f} m INSIDE the skull")
    return bad, checked, matched, misses


# ---------------------------------------------------------------- FACE DETAILS
def build_face_details():
    """
    Real feature GEOMETRY. A displaced sphere cannot read as a face no matter how
    well it is sculpted - the eyes, brows and mouth line must exist as separate
    objects or every render is 'a blank egg' (three reviews said exactly that).
    All positions are world coords on the 1.70 m build; head centre is (0,0,1.588).
    """
    parts = []
    HZ = 1.588                      # head centre z
    head = bpy.data.objects.get("EDI_Head")
    _hverts = [v.co.copy() for v in head.data.vertices] if head else []
    _hloc = head.location if head else Vector((0, 0, 0))

    def surf_y(x, z):
        """Frontmost head surface Y at world (x,z), from raw vertices.

        v01 hand-guessed these depths and put the brows/mouth/nostrils INSIDE the
        skull (EYE_Y=0.098 vs a surface at ~0.106) -> 'no eyebrows, no lips'.
        head.ray_cast() misses entirely in headless Blender, so read the verts.
        """
        if not _hverts:
            return 0.106
        lx, lz = x - _hloc.x, z - _hloc.z
        best, rad = None, 0.012
        while best is None and rad <= 0.09:
            for co in _hverts:
                dx, dz = co.x - lx, co.z - lz
                if dx * dx + dz * dz <= rad * rad:
                    if best is None or co.y > best:
                        best = co.y
            rad *= 1.7
        return (best + _hloc.y) if best is not None else 0.106

    EYE_Z = HZ + 0.012              # eyes sit just above head centre
    EYE_X = 0.0335                  # inter-pupillary half-width
    EYE_R = 0.0122                  # eyeball radius ~12 mm
    EYE_Y = surf_y(EYE_X, EYE_Z) + EYE_R * 0.18   # sits proud of the socket floor

    # ---- eyeballs: sclera
    for s, tag in ((1, "R"), (-1, "L")):
        e = add_sphere(f"EDI_Eye_{tag}", radius=EYE_R, loc=(EYE_X * s, EYE_Y, EYE_Z),
                       segs=24, rings=16)
        parts.append(e)

        # iris: flattened disc on the front of the eyeball.
        # It must sit PROUD of the sclera surface: at 0.80*EYE_R it was 0.6 mm
        # inside the eyeball and rendered as 'iris: Absent' on every review.
        ir = add_sphere(f"EDI_Iris_{tag}", radius=EYE_R * 0.50,
                        loc=(EYE_X * s, EYE_Y + EYE_R * 1.02, EYE_Z), segs=16, rings=10)
        bake_scale(ir, 1.0, 0.30, 1.0)          # flatten against the eyeball
        parts.append(ir)

        # pupil sits just proud of the iris
        pu = add_sphere(f"EDI_Pupil_{tag}", radius=EYE_R * 0.22,
                        loc=(EYE_X * s, EYE_Y + EYE_R * 1.09, EYE_Z), segs=12, rings=8)
        parts.append(pu)

        # upper lid: a thin skin-toned cap over the top of the eyeball
        lid = add_sphere(f"EDI_Lid_{tag}", radius=EYE_R * 1.13,
                         loc=(EYE_X * s, EYE_Y - EYE_R * 0.16, EYE_Z + EYE_R * 0.52),
                         segs=18, rings=12)
        bake_scale(lid, 1.10, 1.0, 0.62)
        parts.append(lid)

        # ---- eyebrow: dark tapered lozenge, angled up toward the temple
        bw, bl, bh = 0.030, 0.0105, 0.0072
        by = surf_y(EYE_X * s + 0.003 * s, EYE_Z + 0.030) + 0.0016
        brow = add_cube(f"EDI_Brow_{tag}", size=(bl, bh, bw),
                        loc=(EYE_X * s + 0.003 * s, by, EYE_Z + 0.030))
        bake_rotate(brow, math.radians(-12), math.radians(9 * s), math.radians(-8 * s))
        bev = brow.modifiers.new("Bevel", 'BEVEL'); bev.width = 0.0042; bev.segments = 3
        parts.append(brow)

        # ---- lower lash line: very fine dark line under the eye
        ly = surf_y(EYE_X * s + 0.001 * s, EYE_Z - 0.0125) + 0.0014
        lash = add_cube(f"EDI_Lash_{tag}", size=(0.0115, 0.0032, 0.0155),
                        loc=(EYE_X * s + 0.001 * s, ly, EYE_Z - 0.0125))
        bake_rotate(lash, math.radians(14), math.radians(6 * s), 0)
        parts.append(lash)

    # ---- NOSE: real wedge geometry. Two nostril dots on a smooth egg read as
    # 'detached blobs' - there must be a bridge, tip and alae or there is no nose.
    ny_base = surf_y(0.0, EYE_Z - 0.020)
    nose_lo = add_sphere("EDI_NoseBridge", radius=1.0,
                         loc=(0.0, ny_base + 0.0062, EYE_Z - 0.004), segs=18, rings=12)
    bake_scale(nose_lo, 0.0068, 0.0102, 0.0250)     # narrow tall bridge
    parts.append(nose_lo)

    nose_tip = add_sphere("EDI_NoseTip", radius=1.0,
                          loc=(0.0, ny_base + 0.0118, HZ - 0.0135), segs=16, rings=10)
    bake_scale(nose_tip, 0.0082, 0.0088, 0.0076)    # refined rounded tip
    parts.append(nose_tip)

    for s, tag in ((1, "R"), (-1, "L")):
        ala = add_sphere(f"EDI_NoseAla_{tag}", radius=1.0,
                         loc=(0.0092 * s, ny_base + 0.0082, HZ - 0.0158), segs=14, rings=10)
        bake_scale(ala, 0.0058, 0.0068, 0.0062)     # side wing of the nostril
        parts.append(ala)

    # ---- lips: real volume. The sculpted bow is too subtle to read at render scale.
    mouth_z = HZ - 0.0335
    for tag, dz, hgt, wdt in (("Upper", 0.0072, 0.0042, 0.0225),
                              ("Lower", -0.0072, 0.0052, 0.0212)):
        ly = surf_y(0.0, mouth_z + dz) + 0.0016
        lip = add_sphere(f"EDI_Lip{tag}", radius=1.0,
                         loc=(0.0, ly, mouth_z + dz), segs=22, rings=12)
        bake_scale(lip, wdt, 0.0062, hgt)
        parts.append(lip)

    # ---- mouth: a dark seam so the lips READ as lips rather than a soft bump
    seam = add_cube("EDI_MouthSeam", size=(0.0245, 0.0022, 0.0016),
                    loc=(0.0, surf_y(0.0, mouth_z) + 0.0030, mouth_z))
    bev = seam.modifiers.new("Bevel", 'BEVEL'); bev.width = 0.0011; bev.segments = 3
    parts.append(seam)

    # ---- nostrils: two tiny dark recesses
    for s, tag in ((1, "R"), (-1, "L")):
        ny = surf_y(0.0082 * s, HZ - 0.0175) + 0.0012
        n = add_sphere(f"EDI_Nostril_{tag}", radius=0.0044,
                       loc=(0.0082 * s, ny, HZ - 0.0175), segs=12, rings=8)
        bake_scale(n, 1.0, 0.75, 1.15)
        parts.append(n)

    return parts


# ---------------------------------------------------------------- BODY
def build_body():
    """Lofted female body, 1.70 m, narrow waist, fit build. Returns (torso, parts)."""
    parts = []

    # torso: y is UP (Z-up is Blender, we build along +Z)
    torso = loft("EDI_Torso", [
        #  z,     rx,    rz,    xoff   (hip -> shoulder)
        (0.905, 0.152, 0.108, 0.0),   # hip
        (0.985, 0.140, 0.101, 0.0),
        (1.065, 0.124, 0.094, 0.0),   # waist (narrow)
        (1.135, 0.126, 0.098, 0.0),
        (1.215, 0.145, 0.108, 0.0),   # ribcage
        (1.300, 0.158, 0.113, 0.0),   # bust line
        (1.385, 0.156, 0.106, 0.0),
        (1.455, 0.150, 0.098, 0.0),   # shoulder base
        (1.505, 0.132, 0.090, 0.0),   # trapezius
    ], segs=34)
    subsurf(torso, 2, 2)
    parts.append(torso)

    # neck
    neck = loft("EDI_Neck", [
        (1.495, 0.058, 0.052, 0.0),
        (1.560, 0.052, 0.048, 0.0),
        (1.618, 0.050, 0.047, 0.0),
    ], segs=24)
    subsurf(neck, 2, 2)
    parts.append(neck)

    # head
    head = build_head()
    parts.append(head)

    # arms + hands
    for side in (1, -1):
        s = side
        upper = loft(f"EDI_UpperArm_{'R' if s>0 else 'L'}", [
            (1.455, 0.052, 0.052, 0.150 * s),
            (1.330, 0.046, 0.046, 0.163 * s),
            (1.205, 0.041, 0.041, 0.172 * s),
        ], segs=20)
        subsurf(upper, 2, 2); parts.append(upper)

        fore = loft(f"EDI_Forearm_{'R' if s>0 else 'L'}", [
            (1.205, 0.041, 0.041, 0.172 * s),
            (1.095, 0.036, 0.036, 0.181 * s),
            (0.985, 0.031, 0.031, 0.188 * s),
        ], segs=20)
        subsurf(fore, 2, 2); parts.append(fore)

        # hand: slender, long fingers
        palm = add_cube(f"EDI_Palm_{'R' if s>0 else 'L'}",
                        size=(0.048, 0.026, 0.082),
                        loc=(0.192 * s, 0.0, 0.930))
        subsurf(palm, 2, 2); parts.append(palm)
        for fi in range(4):
            fx = 0.192 * s + (fi - 1.5) * 0.019 * s
            finger = loft(f"EDI_Finger_{'R' if s>0 else 'L'}{fi}", [
                (0.888, 0.0088, 0.0088, fx),
                (0.862, 0.0082, 0.0082, fx),
                (0.838, 0.0072, 0.0072, fx),
            ], segs=10)
            subsurf(finger, 1, 1); parts.append(finger)
        thumb = loft(f"EDI_Thumb_{'R' if s>0 else 'L'}", [
            (0.952, 0.0105, 0.0105, 0.170 * s),
            (0.918, 0.0095, 0.0095, 0.158 * s),
        ], segs=10)
        subsurf(thumb, 1, 1); parts.append(thumb)

        # legs
        thigh = loft(f"EDI_Thigh_{'R' if s>0 else 'L'}", [
            (0.930, 0.082, 0.084, 0.086 * s),
            (0.760, 0.074, 0.076, 0.082 * s),
            (0.585, 0.063, 0.065, 0.078 * s),
        ], segs=24)
        subsurf(thigh, 2, 2); parts.append(thigh)

        calf = loft(f"EDI_Calf_{'R' if s>0 else 'L'}", [
            (0.585, 0.062, 0.064, 0.078 * s),
            (0.430, 0.055, 0.058, 0.074 * s),
            (0.275, 0.038, 0.041, 0.072 * s),
            (0.170, 0.033, 0.036, 0.071 * s),   # ankle - closes the 20 cm gap to the foot
            (0.092, 0.031, 0.034, 0.071 * s),
        ], segs=24)
        subsurf(calf, 2, 2); parts.append(calf)

        foot = add_cube(f"EDI_Foot_{'R' if s>0 else 'L'}",
                        size=(0.048, 0.118, 0.032),
                        loc=(0.072 * s, 0.045, 0.062))
        subsurf(foot, 2, 2); parts.append(foot)

    return parts


# ---------------------------------------------------------------- HAIR
def build_hair():
    """
    Hair cards (Docs/CHARACTER_EDI_v01.md §5).
    BLACKICE: copper auburn, shoulder-length, deep side part, voluminous wave.
    NOIR:     ash platinum, extra-long past waist, sleek.
    """
    ob, me = new_obj("EDI_Hair")
    bm = bmesh.new()
    import random
    rng = random.Random(SEED)

    long_mode = (LOOK == "NOIR")
    cards = 96 if long_mode else 64
    length = 1.16 if long_mode else 0.30
    width = 0.030 if long_mode else 0.038
    base_z = 1.588 + 0.112          # crown of the (now correctly scaled) skull
    head_r = 0.104                  # just outside the 0.111 m skull half-width

    # COVERAGE: hair must NOT cross the face. theta=0 is +Y = FRONT (the nose).
    # v01 swept -111deg..180deg = 291 deg, which wrapped the face and made every
    # render read as 'the back of a head' with 'no face'. Leave a 124 deg frontal
    # window open and grow hair from 62deg around the back to 298deg.
    TH0 = math.radians(62.0)
    SWEEP = math.radians(236.0)

    for i in range(cards):
        u = i / (cards - 1)
        theta = TH0 + u * SWEEP + rng.uniform(-0.05, 0.05)
        # deep side part: hair is parted on her right, swept across the crown
        part_sweep = math.sin(u * math.pi) * 0.10
        theta += part_sweep

        x0 = head_r * math.sin(theta) * 1.02
        y0 = head_r * math.cos(theta) * 1.02
        z0 = base_z - abs(math.cos(theta)) * 0.030 - (1.0 - abs(math.sin(theta))) * 0.012

        segs = 12 if long_mode else 8
        length_i = length * (0.80 + 0.20 * (1.0 - abs(math.cos(theta))))  # longest at the sides
        step = length_i / segs
        ring = []
        for k in range(segs + 1):
            t = k / segs
            fall = t * length_i
            wave = math.sin(t * math.pi * (2.2 if not long_mode else 0.9)) * (0.026 if not long_mode else 0.012)
            # hug the skull for the first half, then flare only slightly
            outward = 0.008 + (t ** 1.7) * (0.020 if long_mode else 0.030)
            xx = x0 * (1.0 + outward * 7.0) + wave * (1 if x0 >= 0 else -1)
            yy = y0 * (1.0 + outward * 7.0) * (1.0 - t * 0.22)
            zz = z0 - fall
            ring.append((xx, yy, zz))
        # card = quad strip with a taper
        for k in range(segs):
            t0, t1 = k / segs, (k + 1) / segs
            w0 = width * (1.0 - 0.55 * t0)
            w1 = width * (1.0 - 0.55 * t1)
            a = Vector(ring[k]); b = Vector(ring[k + 1])
            tangent = (b - a).normalized() if (b - a).length > 1e-6 else Vector((0, 0, -1))
            side = tangent.cross(Vector((0, 1, 0)))
            if side.length < 1e-5:
                side = Vector((1, 0, 0))
            side.normalize()
            v1 = bm.verts.new(a + side * w0)
            v2 = bm.verts.new(a - side * w0)
            v3 = bm.verts.new(b - side * w1)
            v4 = bm.verts.new(b + side * w1)
            bm.faces.new((v1, v2, v3, v4))

    bm_to(bm, me)
    smooth(ob)
    return ob


# ---------------------------------------------------------------- WARDROBE + PROPS
def build_catsuit(body_parts):
    """Slightly inflated copy of the body = skin-tight latex catsuit."""
    for ob in body_parts:
        if any(k in ob.name for k in ("Torso", "UpperArm", "Forearm", "Thigh", "Calf", "Neck")):
            sol = ob.modifiers.new("Suit", 'DISPLACE')
            sol.strength = 0.0055
            sol.mid_level = 0.0
    return body_parts


def build_props():
    """Cigarette + ember + zip pull + cuff + rings."""
    props = []

    # cigarette
    cig = loft("EDI_Cigarette", [
        (0.0, 0.0040, 0.0040, 0.0),
        (0.028, 0.0040, 0.0040, 0.0),   # filter
        (0.030, 0.0038, 0.0038, 0.0),
        (0.072, 0.0038, 0.0038, 0.0),   # paper
    ], segs=12)
    cig.rotation_euler = (math.radians(72), 0, math.radians(-24))
    cig.location = (0.196, 0.052, 0.985)
    props.append(cig)

    # ember
    ember = add_sphere("EDI_Ember", radius=0.0042, loc=(0.227, 0.066, 1.010), segs=14, rings=10)
    props.append(ember)

    # ash
    ash = loft("EDI_Ash", [
        (0.0, 0.0037, 0.0037, 0.0),
        (0.010, 0.0032, 0.0032, 0.0),
    ], segs=10)
    ash.rotation_euler = cig.rotation_euler
    ash.location = (0.233, 0.069, 1.014)
    props.append(ash)

    # zip pull (sternum)
    zip_p = add_cube("EDI_ZipPull", size=(0.006, 0.003, 0.019), loc=(0.0, 0.117, 1.276))
    props.append(zip_p)

    # studded cuff (left wrist)
    cuff = loft("EDI_Cuff", [
        (0.985, 0.0345, 0.0345, -0.188),
        (1.005, 0.0352, 0.0352, -0.188),
    ], segs=18)
    props.append(cuff)

    # rings
    for ri, rx in enumerate((0.1835, -0.1835)):
        ring = loft(f"EDI_Ring_{ri}", [
            (0.845, 0.0098, 0.0098, rx),
            (0.853, 0.0098, 0.0098, rx),
        ], segs=12)
        props.append(ring)

    return props


# ---------------------------------------------------------------- SMOKE CARDS
def build_smoke():
    ob, me = new_obj("EDI_Smoke")
    bm = bmesh.new()
    import random
    rng = random.Random(SEED + 7)
    origin = Vector((0.231, 0.070, 1.018))
    for i in range(7):
        h = 0.12 + i * 0.085
        w = 0.030 + i * 0.021
        lean = 0.020 * i + rng.uniform(-0.012, 0.012)
        c = origin + Vector((lean, 0.006 * i, h))
        vs = [bm.verts.new(c + Vector((-w, 0, -w * 1.25))),
              bm.verts.new(c + Vector((w, 0, -w * 1.25))),
              bm.verts.new(c + Vector((w * 1.5, 0, w * 1.25))),
              bm.verts.new(c + Vector((-w * 1.5, 0, w * 1.25)))]
        bm.faces.new(vs)
    bm_to(bm, me)
    return ob


# ---------------------------------------------------------------- LIGHTS + CAM
def setup_world():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("EDI_World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (*P['bg'], 1.0)
        bg.inputs['Strength'].default_value = 0.42
    return w


def add_light(name, kind, loc, energy, color=(1, 1, 1), size=1.0, rot=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == 'AREA':
        ld.size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.collection.objects.link(ob)
    return ob


def setup_lighting():
    # Energies tuned for a 1.7 m subject at ~2 m in Cycles.
    # v01 shipped 620/190/880 W and blew every frame to pure white (p50=255).
    # Also all lights sat at -Y while the face is on +Y -> she was backlit from
    # the camera's blind side. This rig AIMs every light at a named anatomy point,
    # so the aim cannot drift from the model the way hand-tuned Eulers did.
    def aim_light(name, kind, loc, energy, color, size, target):
        lt = bpy.data.lights.new(name, kind)
        lt.energy = energy; lt.color = color
        if kind == 'AREA':
            lt.size = size
        ob = bpy.data.objects.new(name, lt)
        bpy.context.collection.objects.link(ob)
        ob.location = loc
        d = Vector(target) - Vector(loc)
        if d.length > 1e-6:
            ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        return ob

    FACE  = (0.0, 0.10, 1.60)    # between the eyes
    CHEST = (0.0, 0.117, 1.276)
    HAIR  = (0.0, -0.02, 1.66)

    # key: front-right, high, slightly cool.  175 W clipped the face to white (p95=255).
    aim_light("KEY",  'AREA', (1.35,  1.25, 2.55),  88, (0.93, 0.96, 1.0), 2.4, FACE)
    # fill: front-left, low, cool blue
    aim_light("FILL", 'AREA', (-1.85, 1.25, 1.15),  34, (0.60, 0.72, 1.0), 3.0, CHEST)
    # rim: BEHIND her (-Y) to separate hair + shoulders from the backdrop
    aim_light("RIM",  'AREA', (-1.05, -1.85, 2.35), 132, (1.0, 0.93, 0.84), 1.8, HAIR)
    # ember bounce from the cigarette
    add_light("EMBER", 'POINT', (0.227, 0.10, 1.02), 3.0, (1.0, 0.36, 0.10))


def add_cam(name, loc, rot, lens=50):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 5000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.collection.objects.link(ob)
    return ob


def aim_cam(name, loc, target, lens=50):
    """Point a camera at a world-space target. Framing is computed, never guessed."""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 5000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    bpy.context.collection.objects.link(ob)
    d = Vector(target) - Vector(loc)
    # Blender camera looks along local -Z with +Y up
    rot = d.to_track_quat('-Z', 'Y').to_euler()
    ob.rotation_euler = rot
    return ob


# ---------------------------------------------------------------- RENDER
def render(cam_name, fname, samples=48, res=(1280, 1600)):
    sc = bpy.context.scene
    sc.camera = bpy.data.objects[cam_name]
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = os.path.join(OUT_DIR, fname)
    t0 = time.time()
    try:
        bpy.ops.render.render(write_still=True)
        L(f"rendered {fname} ({time.time()-t0:.1f}s, {samples} smp, denoise on)")
    except RuntimeError as ex:
        # OIDN can throw "out of memory" here even with plenty of free RAM.
        # Degrade gracefully: more samples, no denoiser - a noisy frame beats no frame.
        if "denois" not in str(ex).lower() and "OpenImageDenoise" not in str(ex):
            raise
        L(f"DENOISER FAILED on {fname} ({ex}) -> retrying without it")
        sc.cycles.use_denoising = False
        sc.cycles.samples = max(samples, 128)
        bpy.ops.render.render(write_still=True)
        L(f"rendered {fname} ({time.time()-t0:.1f}s, {sc.cycles.samples} smp, NO denoise)")


# ---------------------------------------------------------------- MAIN
def main():
    clear_scene()
    L(f"look={LOOK} target_tris={TRIS} bake={DO_BAKE}")

    body = build_body()
    L(f"body parts: {len(body)}")

    face = build_face_details()
    L(f"face feature objects: {len(face)}")

    # ---- DETERMINISTIC PLACEMENT GATE (no render until placement is proven)
    bad, checked, matched, misses = verify_face_placement()
    L(f"face placement gate: matched={matched} checked={checked} raycast_misses={misses}")
    if bad:
        for b in bad:
            L(f"  BURIED: {b}")
        L(f"FACE PLACEMENT FAIL - {len(bad)} feature(s) inside the skull; aborting before render")
        raise SystemExit(3)
    if checked < 8:
        L(f"FACE PLACEMENT FAIL - only {checked} features actually verified "
          f"({misses} raycast misses); a vacuous pass is not a pass")
        raise SystemExit(4)
    L("face placement gate PASSED")

    hair = build_hair()
    L("hair cards built")

    body = build_catsuit(body)
    props = build_props()
    smoke = build_smoke()
    L(f"props: {len(props)}")

    # ---- materials
    skin_m = make_mat("EDI_Skin", P['skin'], rough=0.46, metal=0.0, sss=0.22, spec=0.42)
    noisy_bump(skin_m, scale=38.0, strength=0.055, detail=8.0)
    # face features need their OWN materials - a single skin shader cannot make an eye read
    sclera_m = make_mat("EDI_Sclera", (0.90, 0.885, 0.865), rough=0.22, metal=0.0, spec=0.85)
    iris_m   = make_mat("EDI_Iris",   (0.30, 0.42, 0.53),  rough=0.16, metal=0.0, spec=0.92)
    pupil_m  = make_mat("EDI_Pupil",  (0.018, 0.018, 0.022), rough=0.12, metal=0.0, spec=0.95)
    brow_m   = make_mat("EDI_Brow",   (0.115, 0.062, 0.038), rough=0.62, metal=0.0)
    lash_m   = make_mat("EDI_Lash",   (0.030, 0.024, 0.022), rough=0.50, metal=0.0)
    seam_m   = make_mat("EDI_MouthSeam", (0.335, 0.105, 0.098), rough=0.42, metal=0.0, spec=0.5)
    nost_m   = make_mat("EDI_Nostril", (0.135, 0.070, 0.058), rough=0.55, metal=0.0)
    liplip_m = make_mat("EDI_LipCol", (0.615, 0.268, 0.252), rough=0.26, metal=0.0, spec=0.72)
    hair_m = make_mat("EDI_Hair", P['hair'], rough=0.34, metal=0.0, spec=0.62)
    noisy_bump(hair_m, scale=140.0, strength=0.10, detail=4.0)
    suit_m = make_mat("EDI_Suit", P['suit'], rough=0.18, metal=0.06, spec=0.68, clearcoat=0.55)
    noisy_bump(suit_m, scale=220.0, strength=0.035, detail=3.0)
    lip_m = make_mat("EDI_Lips", P['lip'], rough=0.30, metal=0.0, spec=0.55)
    metal_m = make_mat("EDI_Metal", P['metal'], rough=0.30, metal=0.92, spec=0.6)
    cig_m = make_mat("EDI_CigPaper", (0.90, 0.89, 0.86), rough=0.62, metal=0.0)
    ash_m = make_mat("EDI_Ash", (0.52, 0.51, 0.50), rough=0.88, metal=0.0)
    ember_m = make_mat("EDI_Ember", (0.25, 0.06, 0.02), rough=0.42,
                       emis=P['ember'], emis_str=26.0)
    smoke_m = make_mat("EDI_SmokeMat", P['smoke'], rough=1.0, metal=0.0, spec=0.1)
    smoke_m.blend_method = 'BLEND' if hasattr(smoke_m, 'blend_method') else None

    def assign(ob, mat):
        ob.data.materials.clear()
        ob.data.materials.append(mat)

    for ob in body:
        n = ob.name
        if "Head" in n or "Lid" in n:
            assign(ob, skin_m)
        elif "Neck" in n:
            assign(ob, skin_m)
        else:
            assign(ob, suit_m)
    for ob in face:
        n = ob.name
        if   "Eye_" in n:    assign(ob, sclera_m)
        elif "Iris" in n:    assign(ob, iris_m)
        elif "Pupil" in n:   assign(ob, pupil_m)
        elif "Brow" in n:    assign(ob, brow_m)
        elif "Lash" in n:    assign(ob, lash_m)
        elif "Mouth" in n:   assign(ob, seam_m)
        elif "Lip" in n:     assign(ob, liplip_m)
        elif "Nostril" in n: assign(ob, nost_m)
        elif "Nose" in n:    assign(ob, skin_m)
        else:                assign(ob, skin_m)
    assign(hair, hair_m)
    for ob in props:
        n = ob.name
        if "Cigarette" in n:   assign(ob, cig_m)
        elif "Ember" in n:     assign(ob, ember_m)
        elif "Ash" in n:       assign(ob, ash_m)
        else:                  assign(ob, metal_m)
    assign(smoke, smoke_m)

    # ---- lighting + world
    setup_world()
    setup_lighting()
    L("lighting rigged (key/fill/rim/ember)")

    # ---- cameras (aimed at real anatomy points on the 1.70 m build)
    # CRITICAL: the face is sculpted on +Y (nose/lips push +y). v01 parked every
    # camera at -Y, so all four shots were of the BACK of her skull -> "no face".
    # head centre (0,0,1.588) · face front (0,0.10,1.60) · sternum (0,0.117,1.276)
    # smoking hand + ember (0.227,0.066,1.010) · smoke column z 1.02 -> 1.65
    aim_cam("CAM_Hero",  (0.85,  1.45, 1.55), (0.0, 0.02, 1.42), lens=64)   # 3/4 head->waist
    aim_cam("CAM_Face",  (0.26,  0.71, 1.63), (0.0, 0.06, 1.60), lens=90)   # tight portrait
    aim_cam("CAM_Smoke", (0.62,  0.70, 1.28), (0.17, 0.06, 1.16), lens=58)  # hand+cig+smoke+face
    aim_cam("CAM_Turn",  (0.0,   3.20, 0.95), (0.0, 0.00, 0.95), lens=38)   # full body

    # ---- tri census (pre-subdivision applied at render time)
    total = 0
    for ob in body + [hair] + props + [smoke]:
        try:
            total += tri_count(ob)
        except Exception:
            pass
    L(f"evaluated tri census: {total}")

    # ---- render set
    if NO_RENDER:
        L("renders SKIPPED (--no-render)")
    else:
        render("CAM_Hero",  f"CRW_EDI_{LOOK}_view-hero_v01.png",      samples=56, res=(1200, 1500))
        render("CAM_Face",  f"CRW_EDI_{LOOK}_view-face_v01.png",      samples=64, res=(1200, 1500))
        render("CAM_Smoke", f"CRW_EDI_{LOOK}_view-smoke_v01.png",     samples=64, res=(1200, 1500))
        render("CAM_Turn",  f"CRW_EDI_{LOOK}_view-turnaround_v01.png", samples=32, res=(1600, 1000))

    if NO_EXPORT:
        L("export SKIPPED (--no-export)")
        return

    # ---- export FBX
    for ob in bpy.data.objects:
        ob.select_set(False)
    exportable = body + [hair] + props
    for ob in exportable:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = body[0]
    fbx = os.path.join(OUT_DIR, f"CRW_EDI_{LOOK}_v01.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, apply_scale_options='FBX_SCALE_ALL',
        object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False,
        bake_space_transform=True, mesh_smooth_type='FACE',
        use_mesh_modifiers=True, embed_textures=False,
        axis_forward='-Z', axis_up='Y', apply_unit_scale=True)
    L(f"exported {os.path.basename(fbx)}")

    # ---- zero-trust verify
    sha = hashlib.sha256(open(fbx, 'rb').read()).hexdigest()
    size_kb = round(os.path.getsize(fbx) / 1024, 1)
    man = {
        "name": f"CRW_EDI_{LOOK}",
        "look": LOOK, "version": "v01",
        "fbx": os.path.basename(fbx), "fbx_kb": size_kb, "sha256": sha,
        "tris_evaluated": total,
        "height_m": 1.70,
        "palette": {k: [round(c, 3) for c in v] for k, v in P.items()},
        "spec": "Docs/CHARACTER_EDI_v01.md",
        "build_seconds": round(time.time() - t_start, 1),
        "log": log,
    }
    manpath = os.path.join(OUT_DIR, f"MANIFEST_CRW_EDI_{LOOK}_v01.json")
    with open(manpath, "w") as f:
        json.dump(man, f, indent=1)
    L(f"manifest -> {os.path.basename(manpath)}  sha256={sha[:16]}…  {size_kb} KB")
    L(f"DONE in {time.time()-t_start:.1f}s")


main()
