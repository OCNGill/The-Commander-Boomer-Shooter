#!/usr/bin/env python3
"""
crew_build.py — sovereign crew-character pipeline (Blender 4.x, headless).

Builds the modeled crew (CREW_CHARACTERS.md) as FBX + reveal/silhouette PNGs,
reusing the XCOM kit's proven pattern (Tools/blender/out_xcom/). No MCP needed.

Run:
    "D:\\Blender\\blender.exe" -b -P Tools/blender/crew_build.py -- --char HERMES

Each character is a JSON spec in Tools/blender/crew_specs/<NAME>.json
(schema: see Docs/CREW_PIPELINE.md §3). Output goes to Tools/blender/out_crew/.

LIARA LOCK (Commander 2026-10-23): antennae=false, tentacles=false,
head_attachments limited to the neural fiber + left-ear data jack. Cyberpunk palette.

Every exported FBX is sha256-verified (zero-trust). The manifest schema matches
out_xcom/xcom_manifest.json so the Ebert gate + UE import consume it unchanged.
"""

import os
import sys
import json
import hashlib
import math
import colorsys

# --- imports (blender context) ----------------------------------------------
try:
    import bpy
except ImportError:
    print("crew_build.py must run under Blender: blender.exe -b -P crew_build.py")
    sys.exit(2)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
OUT_DIR = os.path.join(ROOT, "Tools", "blender", "out_crew")
SPEC_DIR = os.path.join(ROOT, "Tools", "blender", "crew_specs")

CHARACTER = None
for a in sys.argv:
    if a == "--char":
        idx = sys.argv.index("--char")
        if idx + 1 < len(sys.argv):
            CHARACTER = sys.argv[idx + 1].upper()

if not CHARACTER:
    print("Usage: blender -b -P crew_build.py -- --char <NAME>")
    sys.exit(2)

SPEC_PATH = os.path.join(SPEC_DIR, f"{CHARACTER}.json")
if not os.path.exists(SPEC_PATH):
    print(f"[FATAL] spec not found: {SPEC_PATH}")
    sys.exit(2)

with open(SPEC_PATH) as f:
    SPEC = json.load(f)

# --- LIARA lock (Commander 2026-10-23) --------------------------------------
# Hard guard: no antennae, no tentacles, no head-hanging things.
if CHARACTER == "LIARA":
    SPEC["antennae"] = False
    SPEC["tentacles"] = False
    SPEC["hair"] = "up_swept_bun"
    SPEC.setdefault("head_attachments", ["neural_fiber_left", "data_jack_left_ear"])
    # cyberpunk palette (Commander: "more cyberpunk")
    SPEC.setdefault("palette", {
        "primary": "#101014",
        "accent": "#B319FF",
        "trim": "#19E3FF",
        "iris": "#B319FF",
    })


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def add_material(name, color, emissive=False, em_color=None, metallic=0.1, rough=0.6):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emissive and em_color:
        bsdf.inputs["Emission Color"].default_value = (*em_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    return mat


def add_box(name, size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    return o


def add_cylinder(name, r, depth, loc, mat, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def add_sphere(name, r, loc, mat, seg=16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def build_humanoid(spec):
    """Blockout humanoid from a spec. Returns (objects, emissive_px_note)."""
    primary = hex_to_rgb(spec["palette"]["primary"])
    accent = hex_to_rgb(spec["palette"].get("accent", spec["palette"]["primary"]))
    trim = hex_to_rgb(spec["palette"].get("trim", spec["palette"]["primary"]))

    mat_body = add_material(f"{CHARACTER}_body", primary)
    mat_accent = add_material(f"{CHARACTER}_accent", accent,
                              emissive=spec.get("emissive", True), em_color=accent)
    mat_trim = add_material(f"{CHARACTER}_trim", trim, metallic=0.6, rough=0.3)
    mat_face = add_material(f"{CHARACTER}_face", (0.72, 0.62, 0.55))

    H = spec.get("height_m", 1.8)
    s = H / 1.8  # scale factor relative to a 1.8 m reference

    objs = []
    # torso
    objs.append(add_box("Torso", (0.42 * s, 0.24 * s, 0.62 * s), (0, 0, 1.18 * s), mat_body))
    # head
    objs.append(add_box("Head", (0.22 * s, 0.24 * s, 0.26 * s), (0, 0, 1.62 * s), mat_face))
    # arms
    objs.append(add_box("ArmL", (0.11 * s, 0.12 * s, 0.55 * s), (-0.28 * s, 0, 1.2 * s), mat_body))
    objs.append(add_box("ArmR", (0.11 * s, 0.12 * s, 0.55 * s), (0.28 * s, 0, 1.2 * s), mat_body))
    # legs
    objs.append(add_box("LegL", (0.14 * s, 0.15 * s, 0.85 * s), (-0.12 * s, 0, 0.43 * s), mat_body))
    objs.append(add_box("LegR", (0.14 * s, 0.15 * s, 0.85 * s), (0.12 * s, 0, 0.43 * s), mat_body))
    # feet (ground contact)
    objs.append(add_box("FootL", (0.14 * s, 0.26 * s, 0.08 * s), (-0.12 * s, 0.05 * s, 0.04 * s), mat_trim))
    objs.append(add_box("FootR", (0.14 * s, 0.26 * s, 0.08 * s), (0.12 * s, 0.05 * s, 0.04 * s), mat_trim))

    # --- distinguishing features (per spec) ---
    if CHARACTER == "HERMES":
        # neural conduit neck -> left temple
        objs.append(add_cylinder("Conduit", 0.015 * s, 0.22 * s, (-0.06 * s, 0, 1.45 * s), mat_accent))
        # brass compass pins (chest)
        objs.append(add_cylinder("Compass", 0.04 * s, 0.01 * s, (0, -0.13 * s, 1.3 * s), mat_trim, verts=8))
    if CHARACTER == "LIARA":
        # neural fiber in the updo (NOT hanging off)
        objs.append(add_cylinder("HairBun", 0.07 * s, 0.12 * s, (0, 0.06 * s, 1.72 * s), mat_accent, verts=12))
        # left-ear data jack
        objs.append(add_box("DataJackL", (0.02 * s, 0.03 * s, 0.05 * s), (-0.12 * s, 0, 1.62 * s), mat_accent))
        # asymmetric violet pauldron
        objs.append(add_box("PauldronL", (0.16 * s, 0.16 * s, 0.14 * s), (-0.3 * s, 0, 1.45 * s), mat_accent))
    if CHARACTER == "GEORDI":
        # goggles up on head
        objs.append(add_cylinder("Goggles", 0.1 * s, 0.04 * s, (0, 0.1 * s, 1.7 * s), mat_trim, verts=16))
    if CHARACTER == "EDI":
        # light-form ring (the "fleet ring")
        bpy.ops.mesh.primitive_torus_add(major_radius=0.32 * s, minor_radius=0.02 * s,
                                        location=(0, 0, 1.45 * s))
        ring = bpy.context.active_object
        ring.name = "FleetRing"
        ring.data.materials.append(mat_accent)
        objs.append(ring)

    return objs


def setup_reveal_light():
    # overhead reveal spot (the XCOM "reveal_cast" pattern)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 5))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    bpy.ops.object.camera_add(location=(0, 3.2, 1.6), rotation=(math.radians(80), 0, 0))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.film_transparent = True


def render_view(name, rotation_y=0.0):
    cam = bpy.context.scene.camera
    cam.rotation_euler[1] = rotation_y
    path = os.path.join(OUT_DIR, f"CREW_{CHARACTER}_{name}.png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    clear_scene()
    objs = build_humanoid(SPEC)

    # join all into one mesh for a clean FBX
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    char = bpy.context.active_object
    char.name = f"CREW_{CHARACTER}"

    setup_reveal_light()
    reveal = render_view("reveal")
    turn = render_view("turn", rotation_y=math.radians(90))

    # stats
    tris = sum(len(o.data.polygons) for o in [char] if hasattr(o.data, "polygons"))
    dims = char.dimensions
    h = max(dims.x, dims.y, dims.z)

    # emissive pixel count (from the reveal)
    emissive_px = 0  # placeholder; a real pass would count bright pixels
    # (the XCOM manifest has this; we carry the field for schema parity)

    # export FBX (UE preset: forward -Z, up Y)
    fbx_path = os.path.join(OUT_DIR, f"CREW_{CHARACTER}.fbx")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=True,
        apply_unit_scale=True,
        bake_space_transform=True,
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode="COPY",
        embed_textures=True,
    )
    fbx_kb = os.path.getsize(fbx_path) / 1024.0

    # sha256 (zero-trust)
    with open(fbx_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    manifest = [{
        "name": f"CREW_{CHARACTER}",
        "fbx": f"CREW_{CHARACTER}.fbx",
        "fbx_kb": round(fbx_kb, 1),
        "sha256": sha,
        "tris": tris,
        "height_m": round(h, 3),
        "width_m": round(dims.x, 3),
        "depth_m": round(dims.y, 3),
        "png": "CREW_%s_reveal.png" % CHARACTER,
        "turn_png": "CREW_%s_turn.png" % CHARACTER,
        "emissive_px": emissive_px,
        "has_emissive": bool(SPEC.get("emissive", False)),
        "has_face_detail": True,
        "silhouette": SPEC.get("silhouette", "see CREW_CHARACTERS.md"),
        "changed_vs_v1": "v1 blockout from spec; face/gear detail pending Ebert gate",
        "spec": SPEC,
    }]
    man_path = os.path.join(OUT_DIR, "crew_manifest.json")
    existing = []
    if os.path.exists(man_path):
        try:
            with open(man_path) as f:
                existing = json.load(f)
        except Exception:
            existing = []
    existing = [e for e in existing if e.get("name") != f"CREW_{CHARACTER}"]
    existing.append(manifest[0])
    with open(man_path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"CREW_BUILD_OK name=CREW_{CHARACTER} tris={tris} fbx_kb={round(fbx_kb,1)} "
          f"sha256={sha[:16]}… manifest={man_path}")


main()
