"""Restore the M_Blockout01 base arena geometry (BO_* actors) if it is missing.

Why this exists: Tools/python/blockout_map.py created the 23 base actors with
spawn_actor_from_object(), which is documented in this repo (populate_encounters.py
note, probe_run1) to return NULL for every input in this UE 5.8 build. The base
arena therefore never made it into the saved .umap -- only the 18 ENC_/PU_/WP_
encounters and the horror lights did. This script re-creates the base actors with
the PROVEN path (spawn_actor_from_class + static_mesh_component.set_static_mesh),
saves the map, and then runs the read-only transform dump so the JSON reflects
the real, complete level.

Run:
  UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript \
      -script=Tools/python/ensure_base_geometry.py -unattended -nosplash -NoSound
"""
import unreal
import os
import runpy

MAP = '/Game/Maps/M_Blockout01'
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DUMP = os.path.join(ROOT, 'Tools', 'python', 'dump_level_transforms.py')


def L(m):
    t = '[ENSURE] ' + str(m)
    try:
        unreal.log(t)
    except Exception:
        pass
    try:
        print(t)
    except Exception:
        pass


unreal.EditorLoadingAndSavingUtils.load_map(MAP)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

existing = {}
for a in sub.get_all_level_actors():
    try:
        existing[a.get_actor_label()] = a
    except Exception:
        pass
L('existing actors in map: %d' % len(existing))

CUBE = '/Engine/BasicShapes/Cube.Cube'
PLANE = '/Engine/BasicShapes/Plane.Plane'
CYL = '/Engine/BasicShapes/Cylinder.Cylinder'


def spawn(mesh_path, loc, scale, rot, label):
    if label in existing:
        L('skip (already present) ' + label)
        return existing[label]
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        L('MISSING MESH ' + mesh_path)
        return None
    a = sub.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*loc),
        unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    if not a:
        L('SPAWN FAILED ' + label)
        return None
    try:
        a.static_mesh_component.set_static_mesh(mesh)
    except Exception as exc:
        L('ASSIGN FAILED %s: %r' % (label, exc))
        return None
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.set_actor_label(label)
    L('placed %s loc=%s scale=%s' % (label, loc, scale))
    return a


HALF = 2000.0
spawn(PLANE, (0, 0, 0), (40, 40, 1), (0.0, 0.0, 0.0), 'BO_Floor')
spawn(CUBE, (0, HALF, 200), (40, 0.5, 4), (0.0, 0.0, 0.0), 'BO_Wall_N')
spawn(CUBE, (0, -HALF, 200), (40, 0.5, 4), (0.0, 0.0, 0.0), 'BO_Wall_S')
spawn(CUBE, (HALF, 0, 200), (0.5, 40, 4), (0.0, 0.0, 0.0), 'BO_Wall_E')
spawn(CUBE, (-HALF, 0, 200), (0.5, 40, 4), (0.0, 0.0, 0.0), 'BO_Wall_W')
spawn(CYL, (0, 0, 300), (4, 4, 6), (0.0, 0.0, 0.0), 'BO_Pillar_Center')

COVER = [
    ((600, 600, 50), (3, 3, 1), 0.0),
    ((-600, 600, 50), (3, 3, 1), 45.0),
    ((600, -600, 50), (3, 3, 1), 90.0),
    ((-600, -600, 50), (4, 2, 1), 30.0),
    ((0, 1200, 50), (6, 1, 1), 0.0),
    ((0, -1200, 50), (6, 1, 1), 0.0),
    ((1400, 0, 50), (1, 6, 1), 0.0),
    ((-1400, 0, 50), (1, 6, 1), 0.0),
]
for i, (loc, sc, yaw) in enumerate(COVER):
    spawn(CUBE, loc, sc, (0.0, 0.0, yaw), 'BO_Cover_%02d' % i)

spawn(CUBE, (1200, 1200, 250), (8, 8, 5), (0.0, 0.0, 0.0), 'BO_Platform_NE')
spawn(CUBE, (950, 950, 120), (5, 3, 0.6), (0.0, -14.0, 45.0), 'BO_Ramp_NE')

spawn(CUBE, (-1200, -1200, -25), (10, 10, 0.5), (0.0, 0.0, 0.0), 'BO_PitFloor')
spawn(CUBE, (-1100, -1200, 25), (0.5, 20, 0.5), (0.0, 0.0, 0.0), 'BO_PitRim_E')
spawn(CUBE, (-1300, -1200, 25), (0.5, 20, 0.5), (0.0, 0.0, 0.0), 'BO_PitRim_W')
spawn(CUBE, (-1200, -1100, 25), (20, 0.5, 0.5), (0.0, 0.0, 0.0), 'BO_PitRim_N')
spawn(CUBE, (-1200, -1300, 25), (20, 0.5, 0.5), (0.0, 0.0, 0.0), 'BO_PitRim_S')

if 'BO_PlayerStart' not in existing:
    a = sub.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -1500, 100), unreal.Rotator())
    if a:
        a.set_actor_label('BO_PlayerStart')
        L('placed BO_PlayerStart')
if 'BO_Sun' not in existing:
    a = sub.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 3000),
                                   unreal.Rotator(roll=0.0, pitch=-50.0, yaw=30.0))
    if a:
        a.set_actor_label('BO_Sun')
        L('placed BO_Sun')

L('actor count now: %d' % len(list(sub.get_all_level_actors())))

for fn, desc in ((lambda: unreal.EditorLoadingAndSavingUtils.save_map(MAP), 'save_map'),
                 (lambda: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True), 'save_dirty_packages'),
                 (lambda: unreal.EditorAssetLibrary.save_asset(MAP, only_if_is_dirty=False), 'save_asset')):
    try:
        fn()
        L('save OK via ' + desc)
        break
    except Exception as exc:
        L('save via %s failed: %r' % (desc, exc))

L('running transform dump')
runpy.run_path(DUMP, run_name='__main__')
L('done')
