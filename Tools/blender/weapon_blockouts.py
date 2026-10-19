"""Weapon blockout meshes for The Commander — pure-primitive low-poly, no downloads.

Run headless:
  blender -b -P weapon_blockouts.py -- --out C:/path/to/Tools/blender/out
Exports FBX per weapon. Units: meters (UE import scale handles uu).
"""
import bpy, sys, os, math

argv = sys.argv
out_dir = (argv[argv.index('--out') + 1] if '--out' in argv
           else argv[argv.index('--') + 1] if '--' in argv and argv[argv.index('--') + 1] != '--out'
           else os.path.dirname(os.path.abspath(__file__)) if '--out' not in argv else os.path.dirname(os.path.abspath(__file__)))
os.makedirs(out_dir, exist_ok=True)

# clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

def mat(name, rgba, metallic=0.6, rough=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    return m

M_STEEL = mat('M_Steel', (0.35, 0.36, 0.38, 1))
M_RED = mat('M_CommanderRed', (0.55, 0.03, 0.03, 1), 0.2, 0.5)
M_BRASS = mat('M_Brass', (0.55, 0.42, 0.12, 1), 0.9, 0.3)
M_WOOD = mat('M_DarkWood', (0.16, 0.09, 0.05, 1), 0.0, 0.8)

def join_selected(name, material):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    ob.data.name = name + '_Mesh'
    ob.data.materials.clear()
    ob.data.materials.append(material)
    return ob

def export_fbx(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True,
                             apply_scale_options='FBX_SCALE_ALL',
                             axis_forward='-Z', axis_up='Y',
                             add_leaf_bones=False)
    print('[WEAPON_EXPORT]', path, os.path.getsize(path), 'bytes')

# ---------------- w_01 Pilgrim Puckle — blocky sidearm ----------------
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
barrel = bpy.context.active_object; barrel.scale = (0.18, 0.05, 0.05)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.02, 0, -0.08))
grip = bpy.context.active_object; grip.scale = (0.07, 0.04, 0.12); grip.rotation_euler = (0, math.radians(15), 0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.12, location=(0.12, 0, 0.01), rotation=(0, math.radians(90), 0))
muzzle = bpy.context.active_object
w1 = join_selected('W_PilgrimPuckle', M_BRASS)
export_fbx(w1, os.path.join(out_dir, 'W_PilgrimPuckle.fbx'))

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()

# ---------------- w_03 Mayflower Cannon — fat shotgun ----------------
bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.7, location=(0, 0, 0), rotation=(0, math.radians(90), 0))
body = bpy.context.active_object
bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.35, location=(0.4, 0, 0.03), rotation=(0, math.radians(90), 0))
bar2 = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.15, 0, -0.09))
grip2 = bpy.context.active_object; grip2.scale = (0.1, 0.05, 0.14); grip2.rotation_euler = (0, math.radians(20), 0)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.38, 0, 0))
stock = bpy.context.active_object; stock.scale = (0.12, 0.05, 0.09)
w3 = join_selected('W_MayflowerCannon', M_WOOD)
export_fbx(w3, os.path.join(out_dir, 'W_MayflowerCannon.fbx'))

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()

# ---------------- w_06 Harbor Wreck Rocket — the big one ----------------
bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=1.1, location=(0, 0, 0), rotation=(0, math.radians(90), 0))
tube = bpy.context.active_object
bpy.ops.mesh.primitive_cone_add(radius1=0.11, radius2=0.02, depth=0.25, location=(0.65, 0, 0), rotation=(0, math.radians(90), 0))
nose = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.1, 0, -0.14))
grip3 = bpy.context.active_object; grip3.scale = (0.1, 0.06, 0.16); grip3.rotation_euler = (0, math.radians(12), 0)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.6, 0, 0.1))
sight = bpy.context.active_object; sight.scale = (0.08, 0.03, 0.05)
for i, ang in enumerate((0, 120, 240)):
    a = math.radians(ang)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.55, 0.1 * math.cos(a), 0.1 * math.sin(a)))
    fin = bpy.context.active_object; fin.scale = (0.15, 0.02, 0.1)
    fin.rotation_euler = (a, 0, 0)
w6 = join_selected('W_HarborWreckRocket', M_RED)
export_fbx(w6, os.path.join(out_dir, 'W_HarborWreckRocket.fbx'))

print('[WEAPON_BLOCKOUTS_DONE] out_dir=' + out_dir)
