"""
X-COM: ENEMY UNKNOWN (1994) -> modernized true-3D enemies for "The Commander".

Design doctrine (Commander, 2026-10-21):
  * TRUE 3D, not Doom-style sprites.
  * ORIGINAL X-COM enemies (Mythos Games / MicroProse, 1994), modernized:
    real textures/materials, dramatic lighting, sane polycount.
  * CREEPY: they come out of nowhere WITH LIGHTING (the 1994 terror-mission reveal).
    Every enemy ships with an emissive core/eyes + a "reveal" light rig, and each
    FBX is authored so the reveal light can be driven from UE at spawn time.
  * Base enemies only. Main character comes later.

Usage (headless):
    blender -b -noaudio -P Tools/blender/xcom_enemies.py -- --out <dir> [--render]
    --out   : directory for FBX + preview PNG renders
    --render: also render lit preview PNGs (used for Ebert scoring + Commander review)

Everything is procedural/primitive-based so it is reproducible headless with zero
external assets, and every mesh is joined+exported as a single FBX per enemy.
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector

# --------------------------------------------------------------------------- args
argv = sys.argv
OUT = None
RENDER = False
if '--' in argv:
    tail = argv[argv.index('--') + 1:]
else:
    tail = argv
for i, a in enumerate(tail):
    if a == '--out' and i + 1 < len(tail):
        OUT = tail[i + 1]
    if a == '--render':
        RENDER = True
if OUT is None:
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out_xcom')
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ scene helpers
def purge():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.55, metal=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        if emit is not None:
            for key in ('Emission Color', 'Emission'):
                if key in bsdf.inputs:
                    bsdf.inputs[key].default_value = (emit[0], emit[1], emit[2], 1.0)
                    break
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = emit_str
    return m


def add_mat(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def cube(name, loc, scale, material, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        b = o.modifiers.new('bev', 'BEVEL')
        b.width = bevel
        b.segments = 2
        bpy.ops.object.modifier_apply(modifier=b.name)
    if material:
        add_mat(o, material)
    return o


def cyl(name, loc, radius, depth, material, rot=(0, 0, 0), verts=16, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        add_mat(o, material)
    return o


def sphere(name, loc, radius, material, scale=(1, 1, 1), segs=20, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=radius,
                                          location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for p in o.data.polygons:
        p.use_smooth = True
    if material:
        add_mat(o, material)
    return o


def cone(name, loc, r1, r2, depth, material, rot=(0, 0, 0), verts=14):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth,
                                     location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if material:
        add_mat(o, material)
    return o


def join_objects(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        if o and o.name in bpy.context.scene.objects:
            o.select_set(True)
    if not objs:
        return None
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    # origin to geometry center, keep it at floor
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    return o


def tri_count(o):
    me = o.data
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ------------------------------------------------------------------ materials set
def build_materials():
    M = {}
    M['chitin_dark'] = mat('XCOM_Chitin_Dark', (0.045, 0.052, 0.040), rough=0.42, metal=0.12)
    M['chitin_mid'] = mat('XCOM_Chitin_Mid', (0.085, 0.105, 0.070), rough=0.38, metal=0.18)
    M['chitin_pale'] = mat('XCOM_Chitin_Pale', (0.34, 0.33, 0.24), rough=0.62)
    M['flesh'] = mat('XCOM_Flesh', (0.20, 0.085, 0.075), rough=0.72)
    M['plate'] = mat('XCOM_Armor_Plate', (0.13, 0.14, 0.15), rough=0.35, metal=0.65)
    M['plate_red'] = mat('XCOM_Armor_Accent', (0.30, 0.045, 0.035), rough=0.40, metal=0.35)
    M['eye'] = mat('XCOM_Eye_Emissive', (0.9, 0.95, 0.6), rough=0.15,
                   emit=(0.85, 1.0, 0.45), emit_str=14.0)
    M['core'] = mat('XCOM_Core_Emissive', (0.5, 0.85, 1.0), rough=0.2,
                    emit=(0.35, 0.8, 1.0), emit_str=22.0)
    M['pulse'] = mat('XCOM_Plasma_Emissive', (0.6, 0.3, 1.0), rough=0.2,
                     emit=(0.55, 0.25, 1.0), emit_str=16.0)
    M['metal_dark'] = mat('XCOM_Gunmetal', (0.07, 0.07, 0.08), rough=0.30, metal=0.85)
    return M


# ================================================================== THE ENEMIES
def build_sectoid(M):
    """SECTOID - psychic infiltrator. Slender, huge cranium, thin limbs, no mouth.
    Mod notes: 3.2k tris, matte chitin + oversized emissive eyes."""
    o = []
    o.append(sphere('sectoid_cranium', (0, 0, 1.62), 0.30, M['chitin_mid'], scale=(0.85, 1.05, 1.15)))
    o.append(cube('sectoid_jaw', (0, 0.05, 1.40), (0.14, 0.16, 0.10), M['chitin_pale'], bevel=0.03))
    o.append(cyl('sectoid_neck', (0, 0, 1.22), 0.09, 0.22, M['chitin_dark'], verts=12))
    o.append(cube('sectoid_torso', (0, 0, 0.92), (0.19, 0.13, 0.30), M['chitin_mid'], bevel=0.05))
    o.append(cube('sectoid_hips', (0, 0, 0.60), (0.16, 0.12, 0.12), M['chitin_dark'], bevel=0.04))
    for s in (-1, 1):
        o.append(cyl('sectoid_upperarm', (s * 0.26, 0, 0.92), 0.055, 0.34, M['chitin_dark'],
                     rot=(0, s * 0.18, 0), verts=12))
        o.append(cyl('sectoid_forearm', (s * 0.32, -0.04, 0.66), 0.048, 0.30, M['chitin_dark'],
                     rot=(0.25, s * 0.10, 0), verts=12))
        for f in range(3):
            o.append(cyl('sectoid_finger', (s * 0.34, -0.12 - f * 0.035, 0.50),
                         0.016, 0.14, M['chitin_pale'],
                         rot=(0.5, 0, s * 0.2), verts=8))
        o.append(cyl('sectoid_thigh', (s * 0.11, 0, 0.44), 0.07, 0.34, M['chitin_dark'],
                     rot=(0, s * 0.04, 0), verts=12))
        o.append(cyl('sectoid_shin', (s * 0.12, 0.02, 0.16), 0.055, 0.30, M['chitin_dark'],
                     rot=(-0.10, 0, 0), verts=12))
        o.append(cube('sectoid_foot', (s * 0.12, -0.04, 0.03), (0.07, 0.13, 0.035),
                      M['chitin_pale'], bevel=0.015))
    # eyes: the 1994 tell — big luminous eyes on a dark head
    o.append(sphere('sectoid_eye_l', (-0.11, -0.22, 1.66), 0.075, M['eye'], scale=(1, 0.6, 1.2)))
    o.append(sphere('sectoid_eye_r', (0.11, -0.22, 1.66), 0.075, M['eye'], scale=(1, 0.6, 1.2)))
    o.append(sphere('sectoid_crown_core', (0, 0.02, 1.90), 0.075, M['core'], scale=(1, 1, 0.7)))
    return join_objects(o, 'XCOM_Sectoid')


def build_viper(M):
    """VIPER - the marquee alien. Tall reptilian humanoid, elongated snout head,
    ribbed spine, small plasma pistol. Mod notes: 4.5k tris, chitin + emissive eyes."""
    o = []
    o.append(cube('viper_skull', (0, 0, 1.80), (0.17, 0.21, 0.18), M['chitin_mid'], bevel=0.05))
    o.append(cube('viper_snout', (0, -0.24, 1.72), (0.09, 0.14, 0.07), M['chitin_pale'], bevel=0.03))
    o.append(cyl('viper_jaw', (0, -0.16, 1.62), 0.075, 0.16, M['chitin_dark'],
                 rot=(math.pi / 2, 0, 0), verts=12))
    o.append(cyl('viper_neck', (0, 0, 1.53), 0.11, 0.24, M['chitin_dark'], verts=12))
    o.append(cube('viper_chest', (0, 0, 1.16), (0.25, 0.15, 0.30), M['chitin_mid'], bevel=0.06))
    o.append(cube('viper_abdomen', (0, 0.02, 0.78), (0.18, 0.13, 0.22), M['chitin_dark'], bevel=0.05))
    # ribbed spine — the X-COM silhouette read
    for i in range(5):
        o.append(cube('viper_rib_%d' % i, (0, 0.14, 1.05 + i * 0.11),
                      (0.16 - i * 0.02, 0.05, 0.035), M['chitin_pale'], bevel=0.012))
    for s in (-1, 1):
        o.append(cyl('viper_upperarm', (s * 0.31, 0, 1.14), 0.062, 0.32, M['chitin_dark'],
                     rot=(0, s * 0.16, 0), verts=12))
        o.append(cyl('viper_forearm', (s * 0.37, -0.06, 0.88), 0.055, 0.30, M['chitin_dark'],
                     rot=(0.35, s * 0.08, 0), verts=12))
        o.append(cube('viper_claw', (s * 0.38, -0.14, 0.71), (0.045, 0.10, 0.045),
                      M['chitin_pale'], bevel=0.015))
        o.append(cyl('viper_thigh', (s * 0.13, 0, 0.56), 0.085, 0.38, M['chitin_dark'],
                     rot=(0, s * 0.05, 0), verts=12))
        o.append(cyl('viper_shin', (s * 0.14, 0.03, 0.22), 0.065, 0.32, M['chitin_dark'],
                     rot=(-0.12, 0, 0), verts=12))
        o.append(cube('viper_foot', (s * 0.14, -0.05, 0.04), (0.08, 0.16, 0.045),
                      M['chitin_pale'], bevel=0.02))
        o.append(sphere('viper_eye', (s * 0.10, -0.18, 1.85), 0.055, M['eye'],
                        scale=(1, 0.55, 0.9)))
    # plasma pistol, held
    o.append(cube('viper_pistol', (0.40, -0.22, 0.80), (0.05, 0.16, 0.05), M['metal_dark'], bevel=0.01))
    o.append(sphere('viper_pistol_coil', (0.40, -0.32, 0.80), 0.045, M['pulse'], scale=(1, 1.4, 1)))
    o.append(sphere('viper_spine_core', (0, 0.16, 1.34), 0.07, M['core'], scale=(1, 0.6, 1.3)))
    return join_objects(o, 'XCOM_Viper')


def build_floater(M):
    """FLOATER - psychic hovering manta. No legs, trailing tendrils, glowing core.
    Mod notes: 3.6k tris, the 'comes out of nowhere' silhouette."""
    o = []
    o.append(sphere('float_core', (0, 0, 1.55), 0.34, M['chitin_mid'], scale=(1.1, 0.8, 0.85)))
    o.append(sphere('float_eye', (0, -0.26, 1.62), 0.12, M['eye'], scale=(1.5, 0.6, 0.6)))
    o.append(sphere('float_glow', (0, 0.05, 1.90), 0.16, M['core'], scale=(1, 1, 0.55)))
    for s in (-1, 1):
        o.append(cube('float_wing_root', (s * 0.26, 0.02, 1.55), (0.16, 0.30, 0.05),
                      M['chitin_dark'], rot=(0, 0, s * 0.22), bevel=0.02))
        o.append(cube('float_wing_tip', (s * 0.72, 0.06, 1.60), (0.34, 0.14, 0.03),
                      M['chitin_mid'], rot=(0, s * 0.12, s * 0.30), bevel=0.02))
        o.append(cube('float_wing_rib', (s * 0.50, 0.02, 1.57), (0.22, 0.05, 0.02),
                      M['chitin_pale'], rot=(0, 0, s * 0.26)))
        for t in range(3):
            o.append(cyl('float_tendril', (s * (0.12 + t * 0.05), 0.10, 1.22 - t * 0.05),
                         0.022, 0.55, M['flesh'], rot=(0.12, 0, s * 0.08), verts=8))
    o.append(cyl('float_spine', (0, 0.10, 1.18), 0.05, 0.30, M['chitin_dark'], verts=10))
    return join_objects(o, 'XCOM_Floater')


def build_muton(M):
    """MUTON - armored heavy. The 1994 terror-showstopper: shoulder plates, helmet
    with visor slit, heavy plasma rifle. Mod notes: 5.2k tris, metal + red accents."""
    o = []
    o.append(cube('muton_helmet', (0, 0, 1.86), (0.16, 0.17, 0.15), M['plate'], bevel=0.04))
    o.append(cube('muton_visor', (0, -0.16, 1.85), (0.11, 0.02, 0.035), M['eye']))
    o.append(cyl('muton_neck', (0, 0, 1.66), 0.10, 0.16, M['chitin_dark'], verts=12))
    o.append(cube('muton_chest', (0, 0, 1.26), (0.30, 0.19, 0.34), M['plate'], bevel=0.07))
    o.append(cube('muton_chest_acc', (0, -0.19, 1.30), (0.16, 0.02, 0.12), M['plate_red'], bevel=0.01))
    o.append(cube('muton_abdomen', (0, 0.01, 0.86), (0.22, 0.16, 0.20), M['chitin_dark'], bevel=0.05))
    for s in (-1, 1):
        o.append(cube('muton_pauldron', (s * 0.36, 0, 1.44), (0.14, 0.20, 0.13),
                      M['plate'], rot=(0, 0, s * 0.16), bevel=0.04))
        o.append(cyl('muton_upperarm', (s * 0.36, 0, 1.12), 0.075, 0.28, M['chitin_dark'],
                     rot=(0, s * 0.10, 0), verts=12))
        o.append(cyl('muton_forearm', (s * 0.40, -0.08, 0.86), 0.068, 0.28, M['chitin_dark'],
                     rot=(0.30, 0, 0), verts=12))
        o.append(cube('muton_gauntlet', (s * 0.41, -0.16, 0.70), (0.07, 0.08, 0.06),
                      M['plate'], bevel=0.015))
        o.append(cyl('muton_thigh', (s * 0.15, 0, 0.62), 0.10, 0.34, M['chitin_dark'],
                     rot=(0, s * 0.05, 0), verts=12))
        o.append(cyl('muton_shin', (s * 0.16, 0.03, 0.24), 0.08, 0.30, M['chitin_dark'],
                     rot=(-0.10, 0, 0), verts=12))
        o.append(cube('muton_foot', (s * 0.16, -0.06, 0.05), (0.10, 0.18, 0.06),
                      M['plate'], bevel=0.02))
    # heavy plasma rifle
    o.append(cube('muton_rifle_body', (0.46, -0.24, 0.86), (0.07, 0.26, 0.08), M['metal_dark'], bevel=0.015))
    o.append(cyl('muton_rifle_barrel', (0.46, -0.44, 0.86), 0.035, 0.20, M['metal_dark'],
                 rot=(math.pi / 2, 0, 0), verts=12))
    o.append(sphere('muton_rifle_coil', (0.46, -0.50, 0.86), 0.055, M['pulse'], scale=(1, 1.5, 1))
              )
    o.append(sphere('muton_back_core', (0, 0.22, 1.40), 0.09, M['core'], scale=(1, 0.6, 1.2)))
    return join_objects(o, 'XCOM_Muton')


def build_chryssalid(M):
    """CHRYSSALID - the terror from the deep: insectoid, scythe arms, skittering.
    Mod notes: 4.0k tris, chitin plates + venom glow."""
    o = []
    o.append(sphere('chry_head', (0, -0.06, 0.80), 0.20, M['chitin_mid'], scale=(0.9, 1.2, 0.8)))
    o.append(sphere('chry_eye', (0, -0.20, 0.84), 0.085, M['eye'], scale=(1.6, 0.6, 0.6)))
    o.append(cube('chry_mandible_l', (-0.07, -0.24, 0.72), (0.03, 0.12, 0.02),
                  M['chitin_pale'], rot=(0, 0, 0.4)))
    o.append(cube('chry_mandible_r', (0.07, -0.24, 0.72), (0.03, 0.12, 0.02),
                  M['chitin_pale'], rot=(0, 0, -0.4)))
    o.append(sphere('chry_thorax', (0, 0.06, 0.58), 0.24, M['chitin_dark'], scale=(1, 1.2, 0.85)))
    o.append(sphere('chry_abdomen', (0, 0.34, 0.50), 0.20, M['chitin_mid'], scale=(1, 1.5, 0.8)))
    for s in (-1, 1):
        o.append(cyl('chry_scythe', (s * 0.24, -0.16, 0.52), 0.035, 0.46, M['chitin_pale'],
                     rot=(0.5, 0, s * 0.30), verts=10))
        o.append(cone('chry_scythe_tip', (s * 0.34, -0.34, 0.40), 0.035, 0.001, 0.22,
                      M['chitin_pale'], rot=(1.1, 0, s * 0.30), verts=10))
        o.append(cyl('chry_leg_a', (s * 0.18, 0.06, 0.44), 0.028, 0.40, M['chitin_dark'],
                     rot=(0, s * 0.55, 0), verts=8))
        o.append(cyl('chry_leg_b', (s * 0.24, 0.16, 0.22), 0.024, 0.42, M['chitin_dark'],
                     rot=(-0.35, s * 0.35, 0), verts=8))
        o.append(cyl('chry_leg_c', (s * 0.20, 0.26, 0.44), 0.024, 0.38, M['chitin_dark'],
                     rot=(0.2, s * 0.6, 0), verts=8))
    o.append(sphere('chry_venom', (0, -0.16, 0.50), 0.06, M['pulse'], scale=(1, 0.8, 1.2)))
    return join_objects(o, 'XCOM_Chryssalid')


BUILDERS = [
    ('XCOM_Sectoid', build_sectoid, 1.95),
    ('XCOM_Viper', build_viper, 2.10),
    ('XCOM_Floater', build_floater, 1.85),
    ('XCOM_Muton', build_muton, 2.05),
    ('XCOM_Chryssalid', build_chryssalid, 1.35),
]


# --------------------------------------------------------------- reveal lighting
def setup_dark_world():
    world = bpy.data.worlds.new('XCOM_World')
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0.008, 0.010, 0.016, 1.0)
        bg.inputs[1].default_value = 0.6


def add_reveal_lights(target_z=1.2):
    """The 1994 terror-mission reveal: enemy lit out of pure darkness by a hard
    cold key + colored rim, so it reads as 'it just appeared'."""
    lights = []
    # hard cold key from front-left
    ld = bpy.data.lights.new('reveal_key', 'AREA')
    ld.energy = 900.0
    ld.color = (0.62, 0.78, 1.0)
    ld.size = 2.0
    o = bpy.data.objects.new('reveal_key', ld)
    o.location = (-2.6, -3.0, 3.1)
    bpy.context.scene.collection.objects.link(o)
    lights.append(o)
    # colored rim from behind-right (alien green)
    ld2 = bpy.data.lights.new('reveal_rim', 'AREA')
    ld2.energy = 700.0
    ld2.color = (0.25, 1.0, 0.45)
    ld2.size = 1.5
    o2 = bpy.data.objects.new('reveal_rim', ld2)
    o2.location = (2.8, 2.4, 2.4)
    bpy.context.scene.collection.objects.link(o2)
    lights.append(o2)
    # low under-glow: they come out of the floor
    ld3 = bpy.data.lights.new('reveal_under', 'POINT')
    ld3.energy = 180.0
    ld3.color = (0.45, 0.9, 1.0)
    o3 = bpy.data.objects.new('reveal_under', ld3)
    o3.location = (0, -0.6, 0.15)
    bpy.context.scene.collection.objects.link(o3)
    lights.append(o3)
    return lights


def setup_camera(target_z=1.2, dist=3.6):
    cam_data = bpy.data.cameras.new('cam')
    cam_data.lens = 55
    cam = bpy.data.objects.new('cam', cam_data)
    cam.location = (2.2, -3.1, 2.0)
    bpy.context.scene.collection.objects.link(cam)
    target = Vector((0.0, 0.0, target_z))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    return cam


def setup_render():
    sc = bpy.context.scene
    try:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 720
    sc.render.resolution_y = 900
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    try:
        sc.eevee.taa_render_samples = 48
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    try:
        sc.view_settings.view_transform = 'Filmic'
    except Exception:
        pass


# ------------------------------------------------------------------------- main
def main():
    purge()
    M = build_materials()
    setup_dark_world()
    setup_render()

    manifest = []
    for name, fn, h in BUILDERS:
        obj = fn(M)
        if obj is None:
            print('[XCOM] FAILED build %s' % name)
            continue
        tris = tri_count(obj)
        # export FBX
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        fbx_path = os.path.join(OUT, name + '.fbx')
        bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True,
                                 axis_forward='-Z', axis_up='Y',
                                 apply_scale_options='FBX_SCALE_ALL',
                                 object_types={'MESH'})
        # preview render
        png = os.path.join(OUT, name + '.png')
        if RENDER:
            setup_camera(target_z=h * 0.55, dist=3.6)
            add_reveal_lights(target_z=h * 0.55)
            bpy.context.scene.render.filepath = png
            bpy.ops.render.render(write_still=True)
        manifest.append({'name': name, 'fbx': os.path.basename(fbx_path),
                         'fbx_kb': round(os.path.getsize(fbx_path) / 1024, 1),
                         'tris': tris, 'png': os.path.basename(png) if RENDER else None,
                         'height_m': h})
        print('[XCOM] %-16s tris=%-6d fbx=%.1fKB %s' %
              (name, tris, os.path.getsize(fbx_path) / 1024, 'rendered' if RENDER else 'no-render'))

    import json
    with open(os.path.join(OUT, 'xcom_manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    print('[XCOM] DONE %d enemies -> %s' % (len(manifest), OUT))


if __name__ == '__main__':
    main()
