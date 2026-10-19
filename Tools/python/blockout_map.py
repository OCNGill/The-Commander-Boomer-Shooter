"""M_Blockout01 — headless arena blockout for The Commander.

Run:  UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript -script=Tools/python/blockout_map.py -unattended -nosplash
Design anchors (Docs/DESIGN.md): verticality, cover-as-geometry, secrets, 600 UU/s floor.
Defensive: falls back from EditorLevelLibrary to WorldFactory if the level API is gone.
"""
import unreal
import json

MAP = '/Game/Maps/M_Blockout01'
LINES = []

def L(msg):
    text = '[BLOCKOUT] ' + str(msg)
    unreal.log(text)
    LINES.append(text)

# ---- 1. create or open the map ----
world = None
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    L('loaded existing ' + MAP)
else:
    try:
        unreal.EditorLevelLibrary.new_level(MAP)
        L('created level via EditorLevelLibrary: ' + MAP)
    except Exception as e:
        L('EditorLevelLibrary.new_level failed: %r' % e)
        ft = unreal.AssetToolsHelpers.get_asset_tools()
        world = ft.create_asset('M_Blockout01', '/Game/Maps', unreal.World, unreal.WorldFactory())
        L('WorldFactory create_asset -> %r' % world)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
COUNT = [0]

def spawn(mesh_path, loc, scale, rot=(0.0, 0.0, 0.0), label=''):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        L('MISSING ENGINE MESH: ' + mesh_path)
        return None
    COUNT[0] += 1
    rotator = unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2])
    a = actor_sub.spawn_actor_from_object(mesh, unreal.Vector(*loc), rotator)
    if a:
        a.set_actor_scale3d(unreal.Vector(*scale))
        a.set_actor_label(label or ('BO_%03d' % COUNT[0]))
    L('spawn %s | loc=%s scale=%s rot=%s' % (label or COUNT[0], loc, scale, rot))
    return a

def spawn_class(cls, loc, rot=(0.0, 0.0, 0.0), label=''):
    COUNT[0] += 1
    a = actor_sub.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    if a and label:
        a.set_actor_label(label)
    L('spawn class %s | loc=%s' % (cls.__name__, loc))
    return a

CUBE = '/Engine/BasicShapes/Cube.Cube'        # 100 uu
PLANE = '/Engine/BasicShapes/Plane.Plane'      # 100 uu
CYLINDER = '/Engine/BasicShapes/Cylinder.Cylinder'

# ---- 2. arena geometry (units: 1 uu = 1 cm; arena 40 m x 40 m) ----
HALF = 2000.0
spawn(PLANE, (0, 0, 0), (40, 40, 1), label='BO_Floor')

# perimeter walls (cube = 100uu -> scale 40 wide, 0.5 thick, 4 tall)
spawn(CUBE, (0,  HALF, 200), (40, 0.5, 4), label='BO_Wall_N')
spawn(CUBE, (0, -HALF, 200), (40, 0.5, 4), label='BO_Wall_S')
spawn(CUBE, ( HALF, 0, 200), (0.5, 40, 4), label='BO_Wall_E')
spawn(CUBE, (-HALF, 0, 200), (0.5, 40, 4), label='BO_Wall_W')

# central pillar (verticality anchor)
spawn(CYLINDER, (0, 0, 300), (4, 4, 6), label='BO_Pillar_Center')

# cover field — cover is GEOMETRY ONLY (design contract: never a mechanic)
COVER = [
    (( 600,   600, 50), (3, 3, 1), 0.0),
    ((-600,   600, 50), (3, 3, 1), 45.0),
    (( 600,  -600, 50), (3, 3, 1), 90.0),
    ((-600,  -600, 50), (4, 2, 1), 30.0),
    ((   0,  1200, 50), (6, 1, 1), 0.0),
    ((   0, -1200, 50), (6, 1, 1), 0.0),
    ((1400,     0, 50), (1, 6, 1), 0.0),
    ((-1400,    0, 50), (1, 6, 1), 0.0),
]
for i, (loc, sc, yaw) in enumerate(COVER):
    spawn(CUBE, loc, sc, (0.0, 0.0, yaw), label='BO_Cover_%02d' % i)

# raised platform + ramp (verticality)
spawn(CUBE, (1200, 1200, 250), (8, 8, 5), label='BO_Platform_NE')
spawn(CUBE, (950, 950, 120), (5, 3, 0.6), (0.0, -14.0, 45.0), label='BO_Ramp_NE')

# hazard pit ring (Pitfall/Tomb Raider spirit — geometry placeholder)
spawn(CUBE, (-1200, -1200, -25), (10, 10, 0.5), label='BO_PitFloor')
spawn(CUBE, (-1100, -1200, 25), (0.5, 20, 0.5), label='BO_PitRim_E')
spawn(CUBE, (-1300, -1200, 25), (0.5, 20, 0.5), label='BO_PitRim_W')
spawn(CUBE, (-1200, -1100, 25), (20, 0.5, 0.5), label='BO_PitRim_N')
spawn(CUBE, (-1200, -1300, 25), (20, 0.5, 0.5), label='BO_PitRim_S')

# ---- 3. gameplay anchors ----
spawn_class(unreal.PlayerStart, (0, -1500, 100), (0.0, 0.0, 0.0), label='BO_PlayerStart')
spawn_class(unreal.DirectionalLight, (0, 0, 3000), (0.0, -50.0, 30.0), label='BO_Sun')

# ---- 4. save ----
try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    L('save_dirty_packages OK')
except Exception as e:
    L('save failed: %r' % e)

exists = unreal.EditorAssetLibrary.does_asset_exist(MAP)
L('RESULT map=%s exists=%s actors=%d lines=%d' % (MAP, exists, COUNT[0], len(LINES)))
unreal.log('[BLOCKOUT_SUMMARY] ' + json.dumps({'map': MAP, 'exists': bool(exists), 'actors': COUNT[0]}))
