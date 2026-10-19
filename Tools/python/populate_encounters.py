"""Populate M_Blockout01 with the encounter layout: enemies, pickups, weapon spawns.

Run:  UnrealEditor-Cmd.exe TheCommander.uproject -run=pythonscript -script=Tools/python/populate_encounters.py -unattended -nosplash
Meshes come from /Game/Weapons (leg B import). Each mesh is auto-normalized to a
per-type target height in uu so Blender-meter imports never land at 1uu.
"""
import unreal
import json

MAP = '/Game/Maps/M_Blockout01'
LINES = []

def L(m):
    t = '[POPULATE] ' + str(m)
    unreal.log(t); LINES.append(t)

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
L('loaded ' + MAP)

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def target_height(label):
    # NOTE: prefixes must match the ACTUAL label prefixes (ENC_/PU_/WP_),
    # not the asset prefixes (E_/P_/W_) — that mismatch made every spawn fall
    # through to the 100uu default in populate_run4.
    if label.startswith('ENC_NorEaster'): return 300.0
    if label.startswith('ENC_Brute'): return 160.0
    if label.startswith('ENC_Golem'): return 150.0
    if label.startswith('ENC_Drone'): return 60.0
    if label.startswith('ENC_'): return 180.0
    if label.startswith('PU_'): return 40.0
    if label.startswith('WP_'): return 60.0
    return 100.0

def spawn_mesh(mesh_path, loc, label):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        L('MISSING ' + mesh_path)
        return None
    # NOTE (probe_run1): spawn_actor_from_object returns NULL for every input in this
    # engine build (even engine cubes on a fresh level). Proven path = class-spawn
    # StaticMeshActor then assign the mesh directly.
    a = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator())
    if not a:
        L('SPAWN FAILED (class) ' + label)
        return None
    try:
        a.static_mesh_component.set_static_mesh(mesh)
    except Exception as e:
        L('ASSIGN FAILED %s: %r' % (label, e))
        return None
    want = target_height(label)
    try:
        b = mesh.get_bounds()
        extent_z = float(b.box_extent.z) * 2.0
        s = want / extent_z if extent_z > 0.001 else 1.0
        # guard against garbage bounds
        if s > 500 or s < 0.001: s = 1.0
        a.set_actor_scale3d(unreal.Vector(s, s, s))
        L('spawn %s loc=%s extent_z=%.1f -> scale %.2f' % (label, loc, extent_z, s))
    except Exception as e:
        L('bounds/scale issue for %s: %r (scale=1)' % (label, e))
    a.set_actor_label(label)
    return a

# ---- encounters (enemy proxies = spatial markers for the real AI) ----
ENCOUNTERS = [
    ('/Game/Weapons/E_BarnacleDrone',  ( 800, -400, 150), 'ENC_Drone_01'),
    ('/Game/Weapons/E_BarnacleDrone',  (-900,  300, 150), 'ENC_Drone_02'),
    ('/Game/Weapons/E_BarnacleDrone',  (   0,  600, 180), 'ENC_Drone_03'),
    ('/Game/Weapons/E_PilgrimZealot',  (1500, -800,   0), 'ENC_Zealot_01'),
    ('/Game/Weapons/E_PilgrimZealot',  (-1500, 700,   0), 'ENC_Zealot_02'),
    ('/Game/Weapons/E_MayflowerPhantom', (-700, -1400, 0), 'ENC_Phantom_01'),
    ('/Game/Weapons/E_LobsterBrute',    (-1200, -1200, 50), 'ENC_Brute_Pit'),
    ('/Game/Weapons/E_RockGolem',       (1200, 1200, 510), 'ENC_Golem_Platform'),
    ('/Game/Weapons/E_NorEasterTitan',  (0, 1600, 0), 'ENC_Boss_NorEaster'),
]

# ---- pickups (classic: no regen, no stamina — design contract) ----
PICKUPS = [
    ('/Game/Weapons/P_HealthCross',  (-1150, -1150, 60), 'PU_Health_Pit'),
    ('/Game/Weapons/P_ArmorShard',   (1300, 1300, 520), 'PU_Armor_Platform'),
    ('/Game/Weapons/P_AmmoBox',      (500, 100, 30), 'PU_Ammo_01'),
    ('/Game/Weapons/P_AmmoBox',      (-500, -100, 30), 'PU_Ammo_02'),
    ('/Game/Weapons/P_KeycardGreen', (0, 0, 620), 'PU_KeyGreen_PillarTop'),
    ('/Game/Weapons/P_KeycardRed',   (-1250, -1250, 60), 'PU_KeyRed_Pit'),
]

# ---- weapon spawns ----
WEAPONS = [
    ('/Game/Weapons/W_PilgrimPuckle',      (0, -1450, 40), 'WP_PilgrimPuckle_Spawn'),
    ('/Game/Weapons/W_MayflowerCannon',    (-300, 0, 40), 'WP_MayflowerCannon_Mid'),
    ('/Game/Weapons/W_HarborWreckRocket',  (1400, 1400, 570), 'WP_Rocket_Platform'),
]

# dedup: clear any actors from a previous populate run (label prefix match)
# API NOTE (apilist_run1): the actor lister is EDITORACTORSUBSYSTEM.get_all_level_actors()
# (also EditorLevelLibrary.get_all_level_actors) — get_all_actors_of_class does NOT exist
# on any of these classes, and World.persistent_level is not python-exposed in this 5.8
# build. spawn_actor_from_object exists but returns NULL for everything (probe_run1),
# so always class-spawn + set_static_mesh.
cleared = 0
_all = []
for getter in (
    lambda: unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors(),
    lambda: unreal.EditorLevelLibrary.get_all_level_actors(),
):
    try:
        _all = list(getter())
        if _all:
            break
    except Exception as e:
        L('actor getter failed: %r' % e)
L('actor getter returned %d actors' % len(_all))
for a in _all:
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    try:
        lab = a.get_actor_label()
    except Exception:
        continue
    if lab.startswith(('ENC_', 'PU_', 'WP_')):
        a.destroy(); cleared += 1
L('cleared %d previously placed encounter actors' % cleared)

placed = 0
for path, loc, label in ENCOUNTERS + PICKUPS + WEAPONS:
    if spawn_mesh(path, loc, label): placed += 1

# ---- lighting beats (horror tier per level1_bible.md) ----
def spawn_light(cls, loc, color_rgba, intensity, label, radius=None):
    try:
        a = actor_sub.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator())
        if not a:
            L('LIGHT SPAWN FAILED ' + label)
            return
        a.set_actor_label(label)
        lc = getattr(a, 'light_component', None)
        if lc is not None:
            try:
                lc.set_light_color(unreal.LinearColor(*color_rgba))
                lc.set_intensity(float(intensity))
                if radius is not None and hasattr(lc, 'set_attenuation_radius'):
                    lc.set_attenuation_radius(float(radius))
            except Exception as e:
                L('light props partial for %s: %r' % (label, e))
        L('light %s at %s intensity=%s' % (label, loc, intensity))
    except Exception as e:
        L('light %s EXC %r' % (label, e))

spawn_light(unreal.PointLight, (-1200, -1200, 220), (1.0, 0.25, 0.15, 1.0), 4000, 'LGT_PitRed', 900)
spawn_light(unreal.PointLight, (0, 0, 750), (0.3, 1.0, 0.45, 1.0), 2500, 'LGT_KeyGreen', 600)
spawn_light(unreal.PointLight, (0, 1600, 260), (0.4, 0.55, 1.0, 1.0), 5000, 'LGT_BossCold', 1200)
spawn_light(unreal.PointLight, (0, -1450, 220), (1.0, 0.85, 0.6, 1.0), 3000, 'LGT_SpawnWarm', 800)
try:
    fog = actor_sub.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 100), unreal.Rotator())
    if fog:
        fog.set_actor_label('LGT_Fog')
        # fog_density is read-only from python in this build; default 0.02 is fine
        L('fog actor placed (default density 0.02)')
except Exception as e:
    L('fog EXC %r' % e)

try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    L('save_dirty_packages OK')
except Exception as e:
    L('save failed: %r' % e)

L('RESULT placed=%d expected=%d map_exists=%s' % (placed, len(ENCOUNTERS)+len(PICKUPS)+len(WEAPONS),
   unreal.EditorAssetLibrary.does_asset_exist(MAP)))
unreal.log('[POPULATE_SUMMARY] ' + json.dumps({'placed': placed, 'total': len(ENCOUNTERS)+len(PICKUPS)+len(WEAPONS)}))
