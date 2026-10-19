"""Pickup + keycard + enemy-proxy blockouts for The Commander.

Run headless:
  blender -b -noaudio -P pickups_enemies_blockouts.py -- --out <dir>
Pickups are the ONLY health system (classic pickups, no regen — design contract).
Enemy proxies are primitive stand-ins for tomorrow's rig work, one per enemy in
Docs/generated/weapons_enemies_v1.json themes.
"""
import bpy, sys, os, math

argv = sys.argv
out_dir = (argv[argv.index('--out') + 1] if '--out' in argv
           else argv[argv.index('--') + 1] if '--' in argv and argv[argv.index('--') + 1] != '--out'
           else os.path.dirname(os.path.abspath(__file__)) if '--out' not in argv else os.path.dirname(os.path.abspath(__file__)))
os.makedirs(out_dir, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

def mat(name, rgba, metallic=0.3, rough=0.5, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    if emit and 'Emission Strength' in b.inputs:
        b.inputs['Emission Strength'].default_value = emit
        b.inputs['Emission Color'].default_value = rgba
    return m

M_RED = mat('M_HealthRed', (0.7, 0.02, 0.02, 1), 0.1, 0.4, 2.0)
M_BLUE = mat('M_ArmorBlue', (0.05, 0.2, 0.7, 1), 0.7, 0.3, 1.0)
M_YELLOW = mat('M_AmmoYellow', (0.8, 0.65, 0.05, 1), 0.5, 0.4)
M_GREEN = mat('M_KeyGreen', (0.05, 0.7, 0.1, 1), 0.2, 0.3, 3.0)
M_REDKEY = mat('M_KeyRed', (0.75, 0.05, 0.05, 1), 0.2, 0.3, 3.0)
M_FLESH = mat('M_EnemyFlesh', (0.45, 0.2, 0.15, 1), 0.0, 0.8)
M_SHELL = mat('M_LobsterShell', (0.6, 0.08, 0.05, 1), 0.4, 0.35)
M_STONE = mat('M_Rock', (0.35, 0.34, 0.32, 1), 0.0, 0.95)
M_STORM = mat('M_StormCloud', (0.15, 0.18, 0.25, 1), 0.1, 0.9, 0.5)

def finalize(name, material):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name; ob.data.name = name + '_Mesh'
    ob.data.materials.clear(); ob.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out_dir, name + '.fbx'), use_selection=True,
                             apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
                             add_leaf_bones=False)
    print('[EXPORT]', name, os.path.getsize(os.path.join(out_dir, name + '.fbx')), 'bytes')
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()

def cube(loc, sc, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = sc; o.rotation_euler = [math.radians(a) for a in rot]; return o

def sphere(loc, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=16, ring_count=8)
    return bpy.context.active_object

def cyl(loc, r, d, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=[math.radians(a) for a in rot], vertices=16)
    return bpy.context.active_object

# ---- PICKUPS (classic, no regen mechanics) ----
# Health cross
cube((0,0,0), (0.3,0.1,0.1)); cube((0,0,0), (0.1,0.1,0.3))
finalize('P_HealthCross', M_RED)

# Armor shard
cube((0,0,0), (0.25,0.08,0.35), (0,0,45))
finalize('P_ArmorShard', M_BLUE)

# Ammo box
cube((0,0,0), (0.3,0.2,0.15)); cube((0,0,0.12), (0.32,0.22,0.04))
finalize('P_AmmoBox', M_YELLOW)

# Keycards (green + red)
cube((0,0,0), (0.2,0.12,0.01))
finalize('P_KeycardGreen', M_GREEN)
cube((0,0,0), (0.2,0.12,0.01))
finalize('P_KeycardRed', M_REDKEY)

# ---- ENEMY PROXIES (one per weapons_enemies_v1.json enemy) ----
# e_01 Barnacle Drone — squat sphere + spit nozzle
sphere((0,0,0.3), 0.3); cyl((0.3,0,0.3), 0.08, 0.25, (0,90,0))
finalize('E_BarnacleDrone', M_SHELL)

# e_02 Pilgrim Zealot — capsule body + wide-brim cone hat + musket
cyl((0,0,0.45), 0.22, 0.9)
bpy.ops.mesh.primitive_cone_add(radius1=0.34, radius2=0.05, depth=0.18, location=(0,0,1.0))
cyl((0.28,0,0.5), 0.03, 0.8, (0,80,0))
finalize('E_PilgrimZealot', M_FLESH)

# e_03 Mayflower Phantom — hooded wedge (ghost hull)
cube((0,0,0.6), (0.5,0.3,1.1)); cube((0,0,1.25), (0.3,0.2,0.35), (0,0,45))
finalize('E_MayflowerPhantom', M_STORM)

# e_04 Lobster Brute — wide shell body + two claw boxes
cube((0,0,0.7), (0.9,0.6,0.8)); cube((0.7,0.45,0.7), (0.3,0.25,0.2)); cube((0.7,-0.45,0.7), (0.3,0.25,0.2))
finalize('E_LobsterBrute', M_SHELL)

# e_05 Rock Golem — stacked boulders
sphere((0,0,0.5), 0.55); sphere((0.5,0.3,0.35), 0.3); sphere((-0.5,-0.3,0.35), 0.3); sphere((0,0,1.2), 0.35)
finalize('E_RockGolem', M_STONE)

# e_06 Nor-Easter Titan — tall storm column + shoulder mass
cyl((0,0,1.4), 0.55, 2.8); sphere((0.65,0,2.4), 0.35); sphere((-0.65,0,2.4), 0.35)
finalize('E_NorEasterTitan', M_STORM)

print('[PICKUP_ENEMY_BATCH_DONE] out_dir=' + out_dir)
